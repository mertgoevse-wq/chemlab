// Godot 4.7 Shader Library for Athanor Ascension
// Cinematic shaders for GLES3 Compatibility Renderer (Intel Iris Xe optimized)
// All shaders designed for ≤65 draw calls, 60 FPS on 128 MB VRAM

// ============================================================================
// 1. BOROSILICATE GLASS SHADER (IOR 1.474, Beer-Lambert absorption)
// ============================================================================
shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec4 base_color : source_color = vec4(1.0, 1.0, 1.0, 0.05);
uniform float ior = 1.474;
uniform float roughness = 0.015;
uniform float thickness = 3.0; // mm
uniform vec3 absorption_color = vec3(0.99, 0.99, 0.995); // Slight blue-green tint
uniform float absorption_strength = 0.1;
uniform bool enable_meniscus = true;
uniform float meniscus_height = 0.02;
uniform vec3 liquid_color = vec4(0.2, 0.4, 0.8, 0.6); // For liquid-filled glass

varying vec3 view_dir;
varying vec3 world_normal;
varying vec3 world_pos;

void vertex() {
	view_dir = normalize(VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Fresnel reflection
	float cos_theta = dot(-view_dir, world_normal);
	float r0 = pow((1.0 - ior) / (1.0 + ior), 2.0);
	float fresnel = r0 + (1.0 - r0) * pow(1.0 - cos_theta, 5.0);

	// Refraction
	float eta = cos_theta > 0.0 ? (1.0 / ior) : ior;
	float k = 1.0 - eta * eta * (1.0 - cos_theta * cos_theta);
	vec3 refract_dir = k < 0.0 ? vec3(0.0) : eta * view_dir + (eta * cos_theta - sqrt(max(k, 0.0))) * world_normal;

	// Screen-space refraction (approximation)
	vec2 screen_uv = (VERTEX.xy * 0.5 + 0.5) + refract_dir.xy * 0.02;

	// Beer-Lambert absorption through glass thickness
	float path_length = thickness / max(cos_theta, 0.01);
	vec3 absorption = exp(-absorption_color * absorption_strength * path_length);

	// Meniscus effect (curved liquid surface)
	float meniscus = 0.0;
	if (enable_meniscus) {
		float dist_from_center = length(VERTEX.xz);
		meniscus = sin(dist_from_center * 50.0) * meniscus_height * (1.0 - cos_theta);
	}

	// Base glass color with absorption
	vec3 glass_color = base_color.rgb * absorption;

	// Liquid color if filled (blend based on vertex height)
	float fill_factor = smoothstep(-0.5, 0.5, VERTEX.y + meniscus);
	vec3 final_color = mix(glass_color, liquid_color.rgb * liquid_color.a, fill_factor * liquid_color.a);

	// Reflection contribution
	vec3 reflection = vec3(fresnel * 0.1) * roughness;

	ALBEDO = final_color + reflection;
	ALPHA = base_color.a + fill_factor * liquid_color.a * 0.5;

	// Roughness affects specular
	ROUGHNESS = roughness;
	METALLIC = 0.0;
	SPECULAR = fresnel * 0.5;
}

// ============================================================================
// 2. LIQUID SHADER (Fresnel, Caustics, Bubbles, Meniscus, Color gradients)
// ============================================================================
shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec4 liquid_base_color = vec4(0.1, 0.3, 0.7, 0.8);
uniform float ior_liquid = 1.333; // Water-based
uniform float ior_air = 1.0;
uniform float depth_absorption = 0.3;
uniform vec3 deep_color = vec3(0.05, 0.1, 0.3);
uniform bool enable_caustics = true;
uniform float caustic_speed = 0.5;
uniform float caustic_scale = 10.0;
uniform float caustic_strength = 0.15;
uniform bool enable_bubbles = true;
uniform float bubble_density = 0.02;
uniform float bubble_speed = 0.3;
uniform float meniscus_curve = 0.03;

varying vec3 world_pos;
varying vec3 world_normal;
varying vec3 view_dir;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	view_dir = normalize(VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Depth-based color (Beer-Lambert)
	float depth = (1.0 - VERTEX.y) * 2.0; // Normalized depth
	vec3 color = mix(liquid_base_color.rgb, deep_color, depth * depth_absorption);

	// Meniscus at edges
	float dist_from_center = length(VERTEX.xz);
	float meniscus = sin(dist_from_center * 30.0 + TIME * 2.0) * meniscus_curve * (1.0 - VERTEX.y);
	float meniscus_alpha = smoothstep(0.95, 1.0, dist_from_center) * (1.0 + sin(TIME * 5.0) * 0.1);

	// Caustics (projected texture simulation)
	vec3 caustic = vec3(0.0);
	if (enable_caustics) {
		vec2 caustic_uv = world_pos.xz * caustic_scale + vec2(TIME * caustic_speed);
		float caustic_pattern = sin(caustic_uv.x * 12.0 + sin(caustic_uv.y * 8.0)) * 0.5 + 0.5;
		caustic_pattern = pow(caustic_pattern, 8.0) * caustic_strength;
		caustic = vec3(caustic_pattern) * (1.0 - depth * 0.5);
	}

	// Bubbles (procedural)
	vec3 bubble_effect = vec3(0.0);
	if (enable_bubbles) {
		vec3 bubble_pos = world_pos + vec3(sin(TIME * bubble_speed + world_pos.x * 10.0), TIME * bubble_speed * 0.5, cos(TIME * bubble_speed + world_pos.z * 10.0));
		float bubble_noise = fract(sin(dot(bubble_pos, vec3(12.9898, 78.233, 45.164))) * 43758.5453);
		float bubble_mask = step(1.0 - bubble_density, bubble_noise);
		float bubble_highlight = mask * pow(1.0 - dot(view_dir, world_normal), 3.0);
		bubble_effect = vec3(bubble_highlight) * 0.8;
	}

	// Fresnel
	float cos_theta = abs(dot(view_dir, world_normal));
	float fresnel = pow(1.0 - cos_theta, 3.0) * 0.3;

	ALBEDO = color + caustic + bubble_effect;
	ALPHA = liquid_base_color.a * (1.0 - meniscus_alpha * 0.5);
	EMISSION = caustic * 0.5 + bubble_effect * 0.3 + vec3(fresnel * 0.1);
	ROUGHNESS = 0.02;
	METALLIC = 0.0;
	SPECULAR = 0.9;
}

// ============================================================================
// 3. CHERENKOV RADIATION SHADER (Blue glow, pulsating, particle trails)
// ============================================================================
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled;

uniform vec3 cherenkov_color = vec3(0.2, 0.45, 0.95); // Characteristic blue
uniform float pulse_speed = 2.0;
uniform float pulse_intensity = 1.5;
uniform float cone_angle = 0.75; // cos(41°) ≈ 0.75
uniform bool enable_particles = true;
uniform float particle_count = 50.0;
uniform float particle_speed = 10.0;
uniform float glow_radius = 2.0;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// Distance from center
	float dist = length(world_pos.xz);
	float height = abs(world_pos.y);

	// Cherenkov cone geometry
	float cone_factor = smoothstep(cone_angle - 0.1, cone_angle + 0.1, dist / max(height, 0.01));

	// Pulsating intensity
	float pulse = sin(TIME * pulse_speed) * 0.5 + 0.5;
	float intensity = pulse_intensity * pulse * cone_factor;

	// Radial falloff
	float radial_falloff = exp(-dist * dist / (glow_radius * glow_radius));

	// Particle trails
	vec3 particles = vec3(0.0);
	if (enable_particles) {
		for (int i = 0; i < int(particle_count); i++) {
			float seed = float(i) * 13.7 + TIME * particle_speed;
			vec2 p_pos = vec2(sin(seed + world_pos.x), cos(seed + world_pos.z)) * glow_radius;
			float p_dist = length(world_pos.xz - p_pos);
			float p_alpha = exp(-p_dist * 20.0) * fract(sin(float(i) * 17.3) * 43758.5453);
			particles += vec3(p_alpha * cherenkov_color * pulse);
		}
	}

	vec3 final_color = cherenkov_color * intensity * radial_falloff + particles;

	ALBEDO = vec3(0.0);
	EMISSION = final_color;
	ALPHA = intensity * radial_falloff;
}

// ============================================================================
// 4. RADIOLUMINESCENCE SHADER (Green uranyl glow, alpha particle tracks)
// ============================================================================
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled;

uniform vec3 radio_color = vec3(0.1, 0.8, 0.2); // Uranyl green
uniform float glow_intensity = 1.0;
uniform float pulse_rate = 0.5; // Slow pulse
uniform bool enable_alpha_tracks = true;
uniform float track_count = 20.0;
uniform float track_length = 0.5;
uniform float scintillation_speed = 10.0;

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	// Base scintillation (random flashes)
	float scint = sin(TIME * scintillation_speed + world_pos.x * 50.0 + world_pos.z * 50.0) * 0.5 + 0.5;
	scint = pow(scint, 4.0); // Sharp flashes

	// Slow pulse
	float pulse = sin(TIME * pulse_rate) * 0.3 + 0.7;

	// Alpha particle tracks
	vec3 tracks = vec3(0.0);
	if (enable_alpha_tracks) {
		for (int i = 0; i < int(track_count); i++) {
			float seed = float(i) * 7.3;
			float t = fract(TIME * 2.0 + seed);
			vec3 track_start = vec3(sin(seed * 13.0) * 2.0, -1.0 + t * 3.0, cos(seed * 13.0) * 2.0);
			vec3 track_dir = normalize(vec3(sin(seed * 17.0), 1.0, cos(seed * 17.0))) * track_length;
			vec3 track_end = track_start + track_dir;

			// Distance from track line
			vec3 to_point = world_pos - track_start;
			float proj = dot(to_point, normalize(track_dir));
			proj = clamp(proj, 0.0, track_length);
			vec3 closest = track_start + normalize(track_dir) * proj;
			float dist = length(world_pos - closest);

			float track_alpha = exp(-dist * 50.0) * (1.0 - t) * fract(sin(seed * 23.0) * 43758.5453);
			tracks += radio_color * track_alpha * 0.5;
		}
	}

	vec3 final_color = radio_color * glow_intensity * scint * pulse + tracks;

	ALBEDO = vec3(0.0);
	EMISSION = final_color;
	ALPHA = glow_intensity * scint * pulse * 0.5;
}

// ============================================================================
// 5. VOLUMETRIC FOG / FUME HOOD SHADER (God rays, particle drift)
// ============================================================================
shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled;

uniform vec3 fog_color = vec3(0.9, 0.9, 0.95);
uniform float density = 0.1;
uniform float flow_speed = 0.2;
uniform vec3 flow_direction = vec3(0.0, 0.5, 0.0); // Upward
uniform bool enable_god_rays = true;
uniform float god_ray_intensity = 0.3;
uniform int ray_march_steps = 16;

varying vec3 world_pos;
varying vec3 world_normal;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	// Base fog density with noise
	vec3 noise_pos = world_pos * 2.0 + vec3(TIME * flow_speed * flow_direction.x, TIME * flow_speed * flow_direction.y, TIME * flow_speed * flow_direction.z);
	float noise = sin(noise_pos.x * 3.0 + noise_pos.y * 2.0 + noise_pos.z * 4.0);
	noise += sin(noise_pos.x * 7.0 - TIME * 0.5) * 0.5;
	float fog = density * (0.5 + noise * 0.3);

	// God rays (light shafts)
	vec3 rays = vec3(0.0);
	if (enable_god_rays) {
		vec3 light_dir = normalize(vec3(0.5, -1.0, 0.3)); // From ceiling lights
		vec3 ray_pos = world_pos;
		float ray_density = 0.0;

		for (int i = 0; i < ray_march_steps; i++) {
			ray_pos += light_dir * 0.1;
			vec3 n_pos = ray_pos * 2.0 + vec3(TIME * 0.1);
			float n = sin(n_pos.x + n_pos.y + n_pos.z);
			ray_density += n * 0.5 + 0.5;
		}

		rays = vec3(god_ray_intensity * ray_density / float(ray_march_steps));
	}

	ALBEDO = fog_color * fog + rays;
	ALPHA = fog * 0.5;
	EMISSION = rays;
}

// ============================================================================
// 6. POST-PROCESS COMPOSITOR (Bloom, Color Grading, Film Grain, DOF)
// ============================================================================
shader_type canvas_item;
render_mode blend_mix;

uniform sampler2D screen_texture : hint_screen_texture;
uniform float bloom_threshold = 1.0;
uniform float bloom_intensity = 0.3;
uniform float bloom_radius = 8.0;
uniform vec3 color_grade_lift = vec3(0.0, 0.0, 0.0);
uniform vec3 color_grade_gamma = vec3(1.0, 1.0, 1.0);
uniform vec3 color_grade_gain = vec3(1.0, 1.0, 1.0);
uniform float film_grain = 0.02;
uniform float vignette = 0.3;
uniform bool enable_dof = false;
uniform float dof_focus = 0.5;
uniform float dof_strength = 0.01;

void fragment() {
	vec2 uv = SCREEN_UV;
	vec3 color = texture(screen_texture, uv).rgb;

	// Bloom (simple single-pass)
	vec3 bright = max(color - vec3(bloom_threshold), vec3(0.0));
	vec3 bloom = vec3(0.0);
	for (int i = 0; i < 4; i++) {
		float offset = float(i) * bloom_radius / 4.0;
		vec2 uv_offset = uv + vec2(cos(float(i) * 1.57), sin(float(i) * 1.57)) * offset * 0.001;
		bloom += texture(screen_texture, uv_offset).rgb * (1.0 - float(i) * 0.2);
	}
	bloom *= bloom_intensity * 0.25;
	color += bloom;

	// Color Grading (Lift, Gamma, Gain)
	color = (color + color_grade_lift) * color_grade_gain;
	color = pow(max(color, vec3(0.0001)), color_grade_gamma);

	// Film Grain
	float grain = (fract(sin(dot(uv * 100.0 + TIME * 10.0, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) * film_grain;
	color += vec3(grain);

	// Vignette
	float dist = length(uv - vec2(0.5));
	color *= 1.0 - dist * dist * vignette;

	// Depth of Field (simple)
	if (enable_dof) {
		// Would need depth texture - placeholder
	}

	COLOR = vec4(clamp(color, 0.0, 1.0), 1.0);
}