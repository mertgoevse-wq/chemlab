// Athanor Ascension — full-screen cinematic grade.
// A restrained vignette, film grain and a faint warm/cool split. No scanlines,
// no heavy aberration: the goal is a photographed laboratory, not a filter.

shader_type canvas_item;
render_mode unshaded;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.45;
uniform float vignette_softness : hint_range(0.05, 1.0) = 0.55;
uniform float grain_strength : hint_range(0.0, 0.2) = 0.03;
uniform float warm_shift : hint_range(-0.1, 0.1) = 0.010;
uniform float letterbox : hint_range(0.0, 0.15) = 0.0;

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 uv = UV;
	vec2 centered = uv * 2.0 - 1.0;
	float radius = length(centered * vec2(1.0, 0.92));
	float vignette = smoothstep(1.35, vignette_softness, radius);
	vec4 tex = texture(screen_tex, uv);

	// Grain is animated per frame and strongest in the shadows, like film.
	float grain = hash(uv * vec2(1920.0, 1080.0) + TIME * 60.0) - 0.5;
	float luma = dot(tex.rgb, vec3(0.299, 0.587, 0.114));
	float grain_weight = mix(1.0, 0.35, luma);
	vec3 graded = tex.rgb + grain * grain_strength * grain_weight;

	// Split-tone: warm highlights, slightly cool midtones.
	graded.r += warm_shift * luma;
	graded.b -= warm_shift * luma * 0.6;

	float mask = smoothstep(0.0, 1.0, 1.0 - vignette_strength * (1.0 - vignette));
	graded *= mask;

	// Optional letterbox for cutscenes (0 by default).
	float lb = step(letterbox, uv.y) * step(uv.y, 1.0 - letterbox);
	graded *= lb;

	COLOR = vec4(graded, lb);
}
