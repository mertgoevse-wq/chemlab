/*
 * Athanor Ascension: Dynamic Chemical Liquid Shader
 * File: game/shaders/liquid_shader.gdshader
 *
 * Physical Principles:
 * - Young-Laplace Capillary Meniscus (contact angle ~15°, lambda_c = 2.7 mm)
 * - Closed-Form Rankine Stirring Vortex (conical depression + centrifugal wall climb)
 * - Rigorous Beer-Lambert Law Transmittance: T = exp(-alpha * c * l)
 * - Mie/Rayleigh Colloidal Turbidity (Tyndall effect opalescence for precipitates)
 * - Analytical Ray-Plane Intersection Capping (zero-loop, 60 FPS on Iris Xe)
 */

shader_type spatial;
render_mode cull_disabled, depth_draw_always, blend_mix, diffuse_burley, specular_schlick_ggx;

group_uniforms meniscus_and_geometry;
uniform float fill_amount : hint_range(0.0, 1.0, 0.001) = 0.5;
uniform float container_height : hint_range(0.01, 0.5, 0.002) = 0.11;
uniform float container_radius : hint_range(0.005, 0.2, 0.001) = 0.038;
uniform float meniscus_height : hint_range(0.0, 0.015, 0.0005) = 0.0035; // ~2.7-3.5 mm
uniform float capillary_decay : hint_range(50.0, 600.0, 10.0) = 320.0; // 1 / lambda_c

group_uniforms chemical_spectrophotometry;
uniform vec4 liquid_color : source_color = vec4(0.92, 0.15, 0.55, 0.85); // Phenolphthalein pink
uniform float solute_concentration : hint_range(0.0, 5.0, 0.01) = 1.0; // mol / L
uniform vec3 molar_extinction : source_color = vec3(0.08, 1.25, 0.45); // eps(R, G, B)
uniform float turbidity : hint_range(0.0, 1.0, 0.01) = 0.0; // AgCl / BaSO4 colloidal suspension
uniform vec3 precipitate_tint : source_color = vec3(0.94, 0.94, 0.91);

group_uniforms agitation_and_vortex;
uniform float swirl_rpm : hint_range(0.0, 1500.0, 10.0) = 0.0; // Magnetic stirrer RPM
uniform float wave_amplitude : hint_range(0.0, 0.05, 0.0005) = 0.003;
uniform float wave_speed : hint_range(0.0, 12.0, 0.1) = 4.0;
uniform float roughness : hint_range(0.0, 0.5, 0.005) = 0.02;
uniform float ior : hint_range(1.0, 1.6, 0.001) = 1.333; // Water n = 1.333

varying vec3 v_world_pos;
varying vec3 v_world_normal;
varying vec3 v_container_up;
varying vec3 v_container_base;

void vertex() {
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	v_container_up = normalize((MODEL_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	v_container_base = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
}

void fragment() {
	// 1. World-Space Liquid Level Center Calculation
	float fill_clamped = clamp(fill_amount, 0.0, 1.0);
	vec3 liquid_center_world = v_container_base + v_container_up * (fill_clamped * container_height);
	float world_liquid_surface_y = liquid_center_world.y;

	// 2. Cylinder Axis Radial Distance Calculation
	vec3 to_pos = v_world_pos - v_container_base;
	float axis_projection = dot(to_pos, v_container_up);
	vec3 radial_vec = to_pos - v_container_up * axis_projection;
	float radial_distance = length(radial_vec);
	float norm_r = clamp(radial_distance / max(container_radius, 0.0001), 0.0, 1.0);

	// 3. Young-Laplace Capillary Meniscus Profile
	// Exponential rise near inner glass wall: h = h0 * exp(-(R - r) / lambda)
	float wall_dist = max(container_radius - radial_distance, 0.0);
	float meniscus_elevation = meniscus_height * exp(-wall_dist * capillary_decay);

	// 4. Closed-Form Rankine Stirring Vortex & Swirl Oscillations
	float norm_rpm = clamp(swirl_rpm / 1200.0, 0.0, 1.0);
	float vortex_depth = norm_rpm * (container_height * 0.45);
	// Parabolic core depression transitioning to outer free-surface swirl
	float vortex_depression = -vortex_depth * exp(-pow(norm_r / 0.35, 2.0));
	float centrifugal_climb = vortex_depth * 0.40 * pow(norm_r, 3.0);

	// Harmonic sloshing ripples
	float swirl_angle = atan(radial_vec.z, radial_vec.x);
	float wave_phase = swirl_angle * 2.0 - TIME * wave_speed;
	float slosh_ripples = sin(wave_phase) * norm_r * (wave_amplitude * (1.0 + norm_rpm * 2.0));
	float micro_ripples = cos(radial_distance * 95.0 - TIME * (wave_speed * 1.8)) * (wave_amplitude * 0.18);

	float effective_surface_y = world_liquid_surface_y + meniscus_elevation + vortex_depression + centrifugal_climb + slosh_ripples + micro_ripples;

	// 5. World-Aligned Surface Clipping & Analytical Disk Capping
	vec3 final_normal = v_world_normal;
	float depth_below_surface = 0.0;
	bool is_surface = false;

	if (FRONT_FACING) {
		if (v_world_pos.y > effective_surface_y) {
			discard;
		}
		depth_below_surface = max(effective_surface_y - v_world_pos.y, 0.0);
	} else {
		// Back faces: Analytical ray-plane intersection with horizontal liquid surface disk
		vec3 cam_pos = INV_VIEW_MATRIX[3].xyz;
		vec3 ray_dir = normalize(v_world_pos - cam_pos);

		if (abs(ray_dir.y) > 0.0001) {
			float t = (effective_surface_y - cam_pos.y) / ray_dir.y;
			if (t > 0.0) {
				vec3 hit_pos = cam_pos + ray_dir * t;
				vec3 to_hit = hit_pos - v_container_base;
				float hit_axis = dot(to_hit, v_container_up);
				vec3 hit_radial = to_hit - v_container_up * hit_axis;
				float hit_dist = length(hit_radial);

				if (hit_dist <= container_radius * 1.06 && hit_axis >= -0.01 && hit_axis <= container_height * 1.05) {
					is_surface = true;
					float hit_norm_r = clamp(hit_dist / max(container_radius, 0.001), 0.0, 1.0);
					// Capillary slope perturbation on meniscus surface normal
					float slope_magnitude = meniscus_height * capillary_decay * exp(-(container_radius - hit_dist) * capillary_decay);
					vec3 meniscus_slope = normalize(hit_radial + vec3(0.0001)) * clamp(slope_magnitude, 0.0, 2.0);
					final_normal = normalize(vec3(0.0, 1.0, 0.0) + meniscus_slope);
					final_normal = normalize((VIEW_MATRIX * vec4(final_normal, 0.0)).xyz);
					depth_below_surface = 0.008;
				} else if (v_world_pos.y > effective_surface_y) {
					discard;
				}
			} else if (v_world_pos.y > effective_surface_y) {
				discard;
			}
		} else if (v_world_pos.y > effective_surface_y) {
			discard;
		}
	}

	// 6. Rigorous Beer-Lambert Law Transmittance: T = exp(-alpha * c * l)
	float optical_path = clamp(depth_below_surface / max(container_height * 0.5, 0.005), 0.04, 2.0);
	vec3 spectral_alpha = molar_extinction * solute_concentration * 4.5;
	vec3 transmittance = exp(-spectral_alpha * optical_path);
	vec3 solution_color = liquid_color.rgb * transmittance;

	// 7. Colloidal Turbidity & Tyndall Opalescence
	// Forward light transmits dilute color; transverse/back light scatters milky precipitate
	float cos_view = abs(dot(final_normal, normalize(VIEW)));
	float tyndall_scatter = pow(1.0 - cos_view, 2.5) * turbidity;
	vec3 turbid_color = mix(solution_color, precipitate_tint, clamp(turbidity * 0.85 + tyndall_scatter * 0.35, 0.0, 1.0));

	// 8. Dielectric Fresnel Highlight (Water IOR = 1.333, F0 = 0.020)
	float f0 = pow((1.0 - ior) / (1.0 + ior), 2.0);
	float fresnel = f0 + (1.0 - f0) * pow(1.0 - cos_view, 5.0);

	// 9. Surface Output Assembly
	ALBEDO = turbid_color + vec3(fresnel * 0.22);
	ROUGHNESS = mix(roughness, 0.42, turbidity);
	METALLIC = 0.0;
	SPECULAR = mix(0.55, 0.12, turbidity);

	if (is_surface) {
		float meniscus_rim = pow(norm_r, 4.0) * 0.45;
		EMISSION = mix(solution_color, vec3(1.0), 0.5) * (fresnel * 0.35 + meniscus_rim);
	}

	float base_alpha = mix(liquid_color.a, 0.98, optical_path * 0.4);
	ALPHA = clamp(mix(base_alpha, 0.99, turbidity), 0.15, 1.0);
}
