# Athanor Ascension — Vitals HUD
# Thin, readable overlay: health, injuries, cumulative chemical and radiation dose.
# Deliberately sparse: the lab should stay the focus, the numbers just refuse to lie.

extends Control

const BAR_WIDTH: float = 210.0
const BAR_HEIGHT: float = 8.0
const MARGIN: Vector2 = Vector2(22.0, 18.0)

const COLOR_OK: Color = Color(0.36, 0.84, 0.66)
const COLOR_WARN: Color = Color(1.0, 0.72, 0.28)
const COLOR_CRIT: Color = Color(1.0, 0.36, 0.34)
const COLOR_TRACK: Color = Color(0.08, 0.1, 0.14, 0.82)
const COLOR_TEXT: Color = Color(0.82, 0.87, 0.92)
const COLOR_DIM: Color = Color(0.55, 0.62, 0.7)

var _pulse: float = 0.0


func _process(delta: float) -> void:
	_pulse += delta
	queue_redraw()


func _draw() -> void:
	var vitals := get_node_or_null("/root/PlayerVitals")
	var font := ThemeDB.fallback_font
	if vitals == null:
		return

	var hp: float = float(vitals.health)
	var max_hp: float = 100.0
	var ratio: float = clampf(hp / max_hp, 0.0, 1.0)
	var hp_color := COLOR_OK
	if ratio <= 0.25:
		hp_color = COLOR_CRIT
	elif ratio <= 0.55:
		hp_color = COLOR_WARN

	draw_rect(Rect2(MARGIN, Vector2(BAR_WIDTH + 130.0, 22.0)), COLOR_TRACK, true)
	draw_rect(Rect2(MARGIN + Vector2(0, 6), Vector2(BAR_WIDTH, BAR_HEIGHT)), Color(0.16, 0.19, 0.24, 0.9), true)
	var filled := Rect2(MARGIN + Vector2(0, 6), Vector2(BAR_WIDTH * ratio, BAR_HEIGHT))
	draw_rect(filled, hp_color, true)
	draw_string(font, MARGIN + Vector2(BAR_WIDTH + 14.0, 15.0), "VITALS", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, COLOR_DIM)
	draw_string(font, MARGIN + Vector2(BAR_WIDTH + 62.0, 16.0), "%d / %d" % [int(round(hp)), int(max_hp)],
		HORIZONTAL_ALIGNMENT_LEFT, -1, 13, COLOR_TEXT)

	var y := MARGIN.y + 30.0
	for injury in vitals.injuries:
		var severity := float(injury.get("severity", 1.0))
		var color := COLOR_WARN.lerp(COLOR_CRIT, clampf(severity / 3.0, 0.0, 1.0))
		draw_circle(Vector2(MARGIN.x + 5.0, y - 4.0), 3.0, color)
		draw_string(font, Vector2(MARGIN.x + 16.0, y), "%s  %ds" % [str(injury.get("label", "Injury")), int(ceil(float(injury.get("remaining_s", 0.0))))],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)
		y += 16.0

	if float(vitals.radiation_msv) > 0.01:
		var rad_color := COLOR_WARN if float(vitals.radiation_msv) < 20.0 else COLOR_CRIT
		draw_string(font, Vector2(MARGIN.x, y), "Dose %.2f mSv  (ICRP annual 20 mSv)" % float(vitals.radiation_msv),
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, rad_color)
		y += 16.0

	var exposure_total := 0.0
	for value in vitals.chemical_exposure.values():
		exposure_total += float(value)
	if exposure_total > 0.0:
		draw_string(font, Vector2(MARGIN.x, y), "Chemical load %.0f ppm·min" % exposure_total,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, COLOR_DIM)

	if vitals.is_incapacitated:
		var alpha := 0.35 + 0.25 * sin(_pulse * 4.0)
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.4, 0.02, 0.02, alpha * 0.35), true)
		draw_string(font, Vector2(size.x * 0.5 - 150.0, size.y * 0.5), "INCAPACITATED — stabilising",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(1, 0.7, 0.68))
