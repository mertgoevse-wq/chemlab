// Athanor Ascension — night city backdrop for the laboratory window.
// Unshaded, cheap (no loops), designed for the Compatibility renderer.
// A skyline with lit windows, sodium haze and rain streaks is cheaper and more
// atmospheric than a 4K photo, and it matches the offline-first constraint.

shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

uniform vec3 sky_top : source_color = vec3(0.015, 0.03, 0.06);
uniform vec3 sky_horizon : source_color = vec3(0.10, 0.14, 0.22);
uniform vec3 city_haze : source_color = vec3(0.55, 0.36, 0.18);
uniform vec3 window_warm : source_color = vec3(1.0, 0.72, 0.38);
uniform vec3 window_cool : source_color = vec3(0.55, 0.78, 1.0);
uniform float rain_strength : hint_range(0.0, 1.0) = 0.55;
uniform float city_speed = 0.02;

float hash11(float n) {
	return fract(sin(n * 127.1) * 43758.5453);
}

float hash21(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void fragment() {
	vec2 uv = UV;

	// Sky gradient, slightly darker at the top of the frame.
	vec3 col = mix(sky_horizon, sky_top, smoothstep(0.0, 0.85, uv.y));

	// Distant haze band just above the rooftops.
	col += city_haze * 0.34 * smoothstep(0.66, 0.38, uv.y) * smoothstep(0.06, 0.40, uv.y);

	// Two skyline layers: far silhouette and near buildings with windows.
	float far_id = floor(uv.x * 22.0);
	float far_h = 0.18 + 0.20 * hash11(far_id + 3.0);
	float far_building = step(uv.y, far_h);
	col = mix(col, vec3(0.035, 0.045, 0.065), far_building * 0.85);

	float id = floor(uv.x * 9.0);
	float h = 0.16 + 0.38 * hash11(id);
	float building = step(uv.y, h);

	// Lit window grid on the near buildings.
	vec2 grid = vec2(uv.x * 9.0 * 4.0, uv.y * 30.0);
	vec2 cell = floor(grid);
	vec2 f = fract(grid);
	float lit = step(0.52, hash21(cell));
	float pane = step(0.28, f.x) * step(f.x, 0.78) * step(0.24, f.y) * step(f.y, 0.70);
	float w = lit * pane * building;

	// A few cold fluorescent floors break up the warm blocks.
	float cold = step(0.82, hash21(cell + 7.0));
	vec3 window_col = mix(window_warm, window_cool, cold);
	col = mix(col, vec3(0.02, 0.025, 0.035), building * 0.9);
	col += window_col * w * 2.1;

	// Rain on the glass: thin vertical streaks drifting sideways.
	float streak_x = uv.x * 90.0 + hash11(floor(uv.y * 6.0)) * 4.0;
	float streak = smoothstep(0.86, 1.0, fract(streak_x)) *
		smoothstep(0.0, 0.7, fract(uv.y * 1.3 - TIME * (0.25 + city_speed)));
	col += vec3(0.35, 0.45, 0.55) * streak * rain_strength * 0.12;

	// Condensation bloom at the bottom edge of the glass.
	col += vec3(0.12, 0.16, 0.18) * smoothstep(0.30, 0.0, uv.y) * 0.5;

	ALBEDO = col;
	EMISSION = col * 1.55;
}
