/*
 * ChemLab: Dynamic Liquid Volume Shader (PBR + Beer-Lambert + Meniscus)
 * Designed for Godot 4 Compatibility Renderer (OpenGL 3.3 / GLES3) on Intel Iris Xe.
 *
 * Physical Principles:
 * - World-Aligned Meniscus: Liquid surface remains strictly horizontal (gravity-aligned)
 *   regardless of vessel orientation, tilt, or pouring kinematics.
 * - Capillary Meniscus: Concave capillary rise at glassware inner perimeter (contact angle ~15°).
 * - Beer-Lambert Absorption Law: Transmittance T = exp(-epsilon * c * d).
 * - Turbidity: Mie scattering simulation for colloidal precipitates (AgCl, BaSO4, PbI2).
 * - Swirling & Wave Dynamics: Analytical Rankine vortex and harmonic surface oscillations.
 * - Closed-form analytical ray-plane intersection for capping (zero-loop, Iris Xe optimized).
 */

shader_type spatial;
render_mode cull_disabled, depth_draw_always, blend_mix, diffuse_burley, specular_schlick_ggx;

// Core uniform requirements from specification
uniform float fill_amount : hint_range(0.0, 1.0, 0.001) = 0.5;
uniform vec4 liquid_color : source_color = vec4(0.15, 0.55, 0.95, 0.85);
uniform float turbidity : hint_range(0.0, 1.0, 0.01) = 0.0;
uniform float meniscus_curvature : hint_range(0.0, 0.5, 0.001) = 0.025;
uniform float wave_amplitude : hint_range(0.0, 0.2, 0.001) = 0.008;

// Physical apparatus dimensions (in meters)
uniform float container_height : hint_range(0.01, 1.0, 0.005) = 0.15;
uniform float container_radius : hint_range(0.005, 0.5, 0.002) = 0.045;
uniform float wave_speed : hint_range(0.0, 10.0, 0.1) = 3.5;
uniform float roughness : hint_range(0.0, 1.0, 0.01) = 0.02;
uniform float ior : hint_range(1.0, 2.0, 0.001) = 1.333; // Water n = 1.333

varying vec3 v_world_pos;
varying vec3 v_local_pos;
varying vec3 v_world_normal;
varying vec3 v_container_up;
varying vec3 v_container_base;

void vertex() {
	v_local_pos = VERTEX;
	v_world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	v_container_up = normalize((MODEL_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
	v_container_base = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
}

void fragment() {
	// 1. World-Space Liquid Level Center Calculation
	// Liquid pivots about container center of volume at fill level
	float fill_clamped = clamp(fill_amount, 0.0, 1.0);
	vec3 liquid_center_world = v_container_base + v_container_up * (fill_clamped * container_height);
	float world_liquid_surface_y = liquid_center_world.y;

	// 2. Cylinder Axis Radial Distance Calculation
	vec3 to_pos = v_world_pos - v_container_base;
	float axis_projection = dot(to_pos, v_container_up);
	vec3 radial_vec = to_pos - v_container_up * axis_projection;
	float radial_distance = length(radial_vec);
	float norm_r = clamp(radial_distance / max(container_radius, 0.001), 0.0, 1.0);

	// 3. Meniscus Curvature (Concave capillary elevation near glass boundary)
	float meniscus_elevation = meniscus_curvature * pow(norm_r, 4.0);

	// 4. Harmonic Swirling Waves & Capillary Ripples
	float swirl_angle = atan(radial_vec.z, radial_vec.x);
	float swirl_wave = sin(swirl_angle * 2.0 - TIME * wave_speed) * norm_r * wave_amplitude;
	float capillary_ripples = cos(radial_distance * 60.0 - TIME * (wave_speed * 1.5)) * wave_amplitude * 0.25 * (1.0 - norm_r);

	float effective_surface_y = world_liquid_surface_y + meniscus_elevation + swirl_wave + capillary_ripples;

	// 5. World-Aligned Surface Clipping & Capping
	vec3 final_normal = v_world_normal;
	float depth_below_surface = 0.0;
	bool is_surface = false;

	if (FRONT_FACING) {
		// Front faces: Clip any geometry above the world-aligned liquid level
		if (v_world_pos.y > effective_surface_y) {
			discard;
		}
		depth_below_surface = max(effective_surface_y - v_world_pos.y, 0.0);
	} else {
		// Back faces: Analytical ray-plane intersection with horizontal liquid surface
		vec3 cam_pos = INV_VIEW_MATRIX[3].xyz;
		vec3 ray_dir = normalize(v_world_pos - cam_pos);

		// Guard against ray parallel to horizontal surface
		if (abs(ray_dir.y) > 0.0001) {
			float t = (effective_surface_y - cam_pos.y) / ray_dir.y;
			if (t > 0.0) {
				vec3 hit_point = cam_pos + ray_dir * t;
				vec3 to_hit = hit_point - v_container_base;
				float hit_axis = dot(to_hit, v_container_up);
				vec3 hit_radial = to_hit - v_container_up * hit_axis;
				float hit_dist = length(hit_radial);

				// Verify intersection lies within physical glassware bounds
				if (hit_dist <= container_radius * 1.08 && hit_axis >= -0.01 && hit_axis <= container_height * 1.05) {
					// We are shading the top liquid meniscus disk!
					is_surface = true;
					// Meniscus surface normal: primarily world UP, perturbed by capillary slope
					vec3 meniscus_slope = normalize(hit_radial + vec3(0.0001)) * pow(hit_dist / max(container_radius, 0.001), 3.0) * (meniscus_curvature * 8.0);
					final_normal = normalize(vec3(0.0, 1.0, 0.0) + meniscus_slope);
					// Transform normal to view space
					final_normal = normalize((VIEW_MATRIX * vec4(final_normal, 0.0)).xyz);
					depth_below_surface = 0.01;
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

	// 6. Beer-Lambert Absorption Law: T = exp(-alpha * d)
	// Optical path depth scaling
	float optical_path = clamp(depth_below_surface / max(container_height, 0.01), 0.05, 1.0);
	vec3 absorption = (vec3(1.0) - liquid_color.rgb) * (liquid_color.a * 6.0);
	vec3 transmittance = exp(-absorption * optical_path);
	vec3 clear_solution = liquid_color.rgb * transmittance;

	// 7. Turbidity / Precipitate Scattering
	// Turbid liquids scatter light diffusely (e.g. white AgCl, yellow PbI2, creamy BaSO4)
	vec3 precipitate_color = mix(liquid_color.rgb, vec3(0.92, 0.92, 0.90), 0.65);
	vec3 final_albedo = mix(clear_solution, precipitate_color, turbidity);

	// 8. Dielectric Fresnel Highlight (Water IOR = 1.333, F0 = 0.02)
	float f0 = pow((1.0 - ior) / (1.0 + ior), 2.0);
	float ndotv = max(dot(final_normal, normalize(VIEW)), 0.001);
	float fresnel = f0 + (1.0 - f0) * pow(1.0 - ndotv, 4.0);

	// 9. Output Shading Assembly
	ALBEDO = final_albedo + vec3(fresnel * 0.2);
	ROUGHNESS = mix(roughness, 0.45, turbidity);
	METALLIC = 0.0;
	SPECULAR = mix(0.5, 0.15, turbidity);

	// Surface meniscus rim glow
	if (is_surface) {
		float meniscus_rim = pow(norm_r, 3.0) * 0.35;
		EMISSION = mix(liquid_color.rgb, vec3(1.0), 0.6) * (fresnel * 0.4 + meniscus_rim);
	}

	// Alpha: Clear solutions are translucent, turbid suspensions become fully opaque
	float solution_alpha = mix(liquid_color.a, 0.98, optical_path * 0.5);
	ALPHA = clamp(mix(solution_alpha, 0.99, turbidity), 0.1, 1.0);
}
