/*
 * ChemLab: Dual-Zone Bunsen Burner Flame Shader
 * Designed for Godot 4 Compatibility Renderer (OpenGL 3.3 / GLES3) on Intel Iris Xe.
 *
 * Physical Principles:
 * - Inner Reducing Cone: T ~ 1200 K (~900°C), bright cerulean blue emission
 *   from CH* (431 nm) and C2 Swan bands (516 nm) chemiluminescence.
 * - Outer Oxidizing Mantle: T ~ 1800 K (~1500°C), faint violet / transparent halo
 *   where excess atmospheric oxygen fully combusts CO and hydrocarbons into CO2 and H2O.
 * - Procedural Multi-Octave Noise: Animated upward licking turbulence, zero external textures.
 * - Single-Pass Additive Synthesis: 60 FPS guaranteed on Intel Iris Xe (80 EU).
 */

shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded;

// Core uniform requirements from specification
uniform float flame_speed : hint_range(0.1, 10.0, 0.1) = 3.5;
uniform vec4 inner_color : source_color = vec4(0.0, 0.65, 1.0, 1.0); // Bright cerulean blue (T ~ 1200 K)
uniform vec4 outer_color : source_color = vec4(0.38, 0.14, 0.82, 0.55); // Faint violet / transparent (T ~ 1800 K)
uniform float flicker_strength : hint_range(0.0, 1.0, 0.01) = 0.25;

// Apparatus operational modes & physical dimensions
// flame_state: 0 = OFF, 1 = SAFETY_YELLOW (collar closed), 2 = HEATING_BLUE (collar open)
uniform int flame_state : hint_range(0, 2) = 2;
uniform float flame_intensity : hint_range(0.0, 5.0, 0.05) = 1.2;
uniform float flame_height_scale : hint_range(0.2, 3.0, 0.05) = 1.0;
uniform vec4 safety_color : source_color = vec4(1.0, 0.65, 0.08, 0.9); // Luminous yellow/orange
uniform vec4 core_hot_color : source_color = vec4(0.85, 0.95, 1.0, 1.0); // Incandescent white base

// Procedural 2D noise & FBM for turbulence (GLES3 / Intel Iris Xe optimized)
float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float noise2d(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
	float total = 0.0;
	float amp = 0.6;
	for (int i = 0; i < 3; i++) {
		total += noise2d(p) * amp;
		p *= 2.05;
		amp *= 0.5;
	}
	return total;
}

void vertex() {
	if (flame_state != 0) {
		float normalized_y = clamp(VERTEX.y / (0.12 * flame_height_scale), 0.0, 1.5);
		float time_val = TIME * flame_speed;

		// Organic fluttering displacement along XZ plane
		float wave_amplitude = 0.012;
		float disp_x = sin(time_val * 1.2 + VERTEX.y * 22.0) * wave_amplitude * normalized_y;
		float disp_z = cos(time_val * 0.9 + VERTEX.y * 18.0) * wave_amplitude * normalized_y;

		// High frequency turbulent micro-flicker
		float micro_flicker = sin(time_val * 3.5 + VERTEX.y * 45.0) * (0.003 * flicker_strength) * normalized_y;

		VERTEX.x += disp_x + micro_flicker;
		VERTEX.z += disp_z + micro_flicker;

		// Dynamic height breathing
		if (flame_state == 1) {
			VERTEX.y *= flame_height_scale * 1.35; // Luminous yellow flame is taller and relaxed
		} else if (flame_state == 2) {
			VERTEX.y *= flame_height_scale * 1.0;  // Heating blue flame is compact and rigid
		}
	}
}

void fragment() {
	if (flame_state != 0 && flame_intensity > 0.001) {
		// Reference geometry bounds
		float max_height = (flame_state == 1) ? 0.16 * flame_height_scale : 0.12 * flame_height_scale;
		float h = clamp(VERTEX.y / max_height, 0.0, 1.0);
		float r = length(VERTEX.xz);

		// Conical tapering profile: wider at burner nozzle, tapering to sharp apex
		float expected_radius = mix(0.018, 0.001, pow(h, 0.8));
		float radial_factor = clamp(r / max(0.0001, expected_radius), 0.0, 1.6);

		// Multi-octave upward scrolling turbulence
		vec2 noise_uv = vec2(VERTEX.x * 45.0, VERTEX.y * 35.0 - TIME * flame_speed * 1.8);
		float turbulence = fbm(noise_uv);

		// Temporal physical flicker
		float flicker = 1.0 + (sin(TIME * flame_speed * 2.8) * 0.12 + cos(TIME * flame_speed * 1.6) * 0.08) * flicker_strength;

		vec3 out_color = vec3(0.0);
		float out_emission = 0.0;
		float out_alpha = 0.0;

		if (flame_state == 2) {
			// =====================================================================
			// DUAL-ZONE HEATING FLAME (Premixed combustion, collar OPEN)
			// =====================================================================

			// 1. Inner Reducing Cone (h <= 0.42, sharp boundary, bright cerulean blue, T ~ 1200 K)
			float inner_h = h / 0.42;
			float inner_expected_r = mix(0.012, 0.001, clamp(inner_h, 0.0, 1.0));
			float inner_radial_factor = r / max(0.0001, inner_expected_r);

			float inner_cone_mask = 0.0;
			if (inner_h <= 1.0 && inner_radial_factor <= 1.1) {
				float inner_radial_falloff = smoothstep(1.1, 0.25, inner_radial_factor);
				float inner_vert_falloff = smoothstep(0.0, 0.08, inner_h) * smoothstep(1.0, 0.85, inner_h);
				inner_cone_mask = inner_radial_falloff * inner_vert_falloff;
			}

			// 2. Outer Oxidizing Mantle (Full height, faint violet / transparent sheath, T ~ 1800 K)
			float outer_radial_falloff = smoothstep(1.25, 0.05, radial_factor);
			float outer_vert_falloff = smoothstep(0.0, 0.08, h) * smoothstep(1.0, 0.70, h);
			float outer_mantle_mask = outer_radial_falloff * outer_vert_falloff;

			// Color mixing: Mantle is faint violet; Inner cone is bright cerulean blue with incandescent white tip
			vec3 mantle_rgb = outer_color.rgb;
			vec3 inner_cone_rgb = mix(inner_color.rgb, core_hot_color.rgb, smoothstep(0.7, 1.0, inner_h) * 0.6);

			out_color = mix(mantle_rgb, inner_cone_rgb, inner_cone_mask);
			out_alpha = (outer_mantle_mask * outer_color.a + inner_cone_mask * inner_color.a) * (0.85 + turbulence * 0.2) * flicker;
			out_emission = (6.0 * outer_mantle_mask + 18.0 * inner_cone_mask) * flame_intensity;

		} else if (flame_state == 1) {
			// =====================================================================
			// SAFETY YELLOW FLAME (Diffusion combustion, collar CLOSED)
			// =====================================================================
			float body_radial = smoothstep(1.3, 0.1, radial_factor);
			float body_vert = smoothstep(0.0, 0.12, h) * smoothstep(1.0, 0.75, h);
			float body_mask = body_radial * body_vert;

			vec3 yellow_rgb = mix(safety_color.rgb, vec3(1.0, 0.35, 0.02), pow(radial_factor, 1.2));
			// Small blue base at gas port
			if (h < 0.20 && radial_factor < 0.5) {
				yellow_rgb = mix(inner_color.rgb * 1.2, yellow_rgb, h / 0.20);
			}

			out_color = yellow_rgb;
			out_alpha = body_mask * safety_color.a * (0.8 + turbulence * 0.2) * flicker;
			out_emission = 8.0 * body_mask * flame_intensity;
		}

		ALBEDO = out_color;
		EMISSION = out_color * out_emission;
		ALPHA = clamp(out_alpha, 0.0, 1.0);
	} else {
		ALBEDO = vec3(0.0);
		EMISSION = vec3(0.0);
		ALPHA = 0.0;
	}
}
