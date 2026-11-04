# Athanor Ascension — Interactive Genome Archive
# Zoomable karyotype -> locus -> base-pair browser with live mutation consequences.
#
# Design intent (Assassin's Creed-style "memory as genome" overview): the whole
# karyotype is a navigable map; every curated gene is a landmark; mutations appear
# in real time as lollipops on the chromosome and as genotype/phenotype readouts.
#
# The browser never invents a protein effect: uncurated loci are reported as VUS.

extends Control

const ASSEMBLY_PATH: String = "res://data/genomics/human_grch38_curated.json"
const SIDE_WIDTH: float = 372.0
const HEADER_H: float = 54.0

const BG: Color = Color(0.035, 0.05, 0.07, 1.0)
const PANEL_BG: Color = Color(0.055, 0.072, 0.098, 0.94)
const GRID: Color = Color(0.18, 0.24, 0.3, 0.55)
const TEXT: Color = Color(0.82, 0.88, 0.93)
const DIM: Color = Color(0.52, 0.61, 0.7)
const CYAN: Color = Color(0.2, 0.85, 0.95)
const AMBER: Color = Color(1.0, 0.72, 0.28)
const MAGENTA: Color = Color(0.92, 0.42, 0.72)
const GENE_COLOR: Color = Color(0.45, 0.62, 0.72)

var _assembly: Dictionary = {}
var _selected_chr: String = "21"
var _selected_gene: String = "APP"
var _zoom: float = 1.0
var _center_bp: float = 0.0
var _mutations: Array = []
var _dosage: Array = []
var _karyotype: Dictionary = {}
var _last_exposure: Dictionary = {}
var _status: String = "Scroll to zoom · drag to pan · click a chromosome"
var _dragging: bool = false
var _last_mouse_x: float = 0.0
var _pulse: float = 0.0

var _gene_list: ItemList
var _gene_info: RichTextLabel
var _hotspot_opt: OptionButton
var _zygosity_opt: OptionButton
var _mutagen_opt: OptionButton
var _dose_slider: HSlider
var _dose_label: Label
var _phenotype_panel: RichTextLabel
var _karyotype_label: Label
var _assembly_label: Label
var _status_label: Label
var _exposure_panel: RichTextLabel
var _trisomy21: CheckButton
var _monosomy_x: CheckButton


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_assembly = GenomeSimulation.load_assembly(ASSEMBLY_PATH)
	_build_ui()
	_select_chromosome("21")
	_refresh()
	set_process(true)


func _process(delta: float) -> void:
	_pulse += delta
	queue_redraw()


# =============================================================================
# UI CONSTRUCTION
# =============================================================================

func _build_ui() -> void:
	var font := ThemeDB.fallback_font
	var title := Label.new()
	title.text = "GENOME ARCHIVE  ·  HELIX INSTITUTE"
	title.position = Vector2(22.0, 14.0)
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", TEXT)
	add_child(title)

	_assembly_label = Label.new()
	_assembly_label.position = Vector2(22.0, 36.0)
	_assembly_label.add_theme_font_size_override("font_size", 11)
	_assembly_label.add_theme_color_override("font_color", DIM)
	_assembly_label.text = "%s · %s" % [_assembly.get("assembly", "?"), _assembly.get("organism", "?")]
	add_child(_assembly_label)

	var back := Button.new()
	back.text = "← Return to Athanor"
	back.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	back.offset_left = -206.0
	back.offset_right = -22.0
	back.offset_top = 14.0
	back.offset_bottom = 44.0
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/main_menu/main_menu.tscn"))
	add_child(back)

	_karyotype_label = Label.new()
	_karyotype_label.position = Vector2(22.0, HEADER_H - 4.0)
	_karyotype_label.add_theme_font_size_override("font_size", 12)
	_karyotype_label.add_theme_color_override("font_color", CYAN)
	add_child(_karyotype_label)

	_build_side_panel()

	_status_label = Label.new()
	_status_label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_status_label.offset_top = -26.0
	_status_label.offset_bottom = -6.0
	_status_label.offset_left = 22.0
	_status_label.offset_right = -(SIDE_WIDTH + 16.0)
	_status_label.add_theme_font_size_override("font_size", 11)
	_status_label.add_theme_color_override("font_color", DIM)
	_status_label.text = _status
	add_child(_status_label)

	var disclaimer := Label.new()
	disclaimer.text = "Educational model · not a diagnostic device"
	disclaimer.position = Vector2(22.0, size.y - 46.0)
	disclaimer.add_theme_font_size_override("font_size", 10)
	disclaimer.add_theme_color_override("font_color", Color(0.45, 0.5, 0.56))
	add_child(disclaimer)


func _build_side_panel() -> void:
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	scroll.offset_left = -SIDE_WIDTH
	scroll.offset_right = -12.0
	scroll.offset_top = HEADER_H + 8.0
	scroll.offset_bottom = -12.0
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	add_child(scroll)

	var panel := VBoxContainer.new()
	panel.custom_minimum_size = Vector2(SIDE_WIDTH - 24.0, 0)
	panel.add_theme_constant_override("separation", 8)
	scroll.add_child(panel)

	panel.add_child(_section_label("CHROMOSOME GENES"))
	_gene_list = ItemList.new()
	_gene_list.custom_minimum_size = Vector2(0, 118)
	_gene_list.item_selected.connect(_on_gene_selected)
	panel.add_child(_gene_list)

	panel.add_child(_section_label("LOCUS DOSSIER"))
	_gene_info = RichTextLabel.new()
	_gene_info.bbcode_enabled = true
	_gene_info.fit_content = true
	_gene_info.custom_minimum_size = Vector2(0, 104)
	_gene_info.add_theme_font_size_override("normal_font_size", 11)
	panel.add_child(_gene_info)

	panel.add_child(_section_label("CURATED VARIANT"))
	_hotspot_opt = OptionButton.new()
	panel.add_child(_hotspot_opt)

	var zyg_row := HBoxContainer.new()
	zyg_row.add_theme_constant_override("separation", 6)
	var zyg_label := Label.new()
	zyg_label.text = "Zygosity"
	zyg_label.add_theme_font_size_override("font_size", 11)
	zyg_label.add_theme_color_override("font_color", DIM)
	zyg_row.add_child(zyg_label)
	_zygosity_opt = OptionButton.new()
	_zygosity_opt.add_item("Heterozygous", 0)
	_zygosity_opt.add_item("Homozygous", 1)
	_zygosity_opt.add_item("Hemizygous", 2)
	_zygosity_opt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	zyg_row.add_child(_zygosity_opt)
	panel.add_child(zyg_row)

	panel.add_child(_action_button("Apply curated variant", _on_apply_hotspot))

	panel.add_child(_section_label("CHEMICAL MUTAGEN EXPOSURE"))
	var mut_row := HBoxContainer.new()
	_mutagen_opt = OptionButton.new()
	for m in GenomeSimulation.mutagens(_assembly):
		_mutagen_opt.add_item(str(m.get("name", m.get("id", "?"))))
	_mutagen_opt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_mutagen_opt.item_selected.connect(func(_i): _refresh_mutagen_hint())
	mut_row.add_child(_mutagen_opt)
	panel.add_child(mut_row)

	var dose_row := HBoxContainer.new()
	var dose_title := Label.new()
	dose_title.text = "Dose"
	dose_title.add_theme_font_size_override("font_size", 11)
	dose_title.add_theme_color_override("font_color", DIM)
	dose_row.add_child(dose_title)
	_dose_slider = HSlider.new()
	_dose_slider.min_value = 0.2
	_dose_slider.max_value = 8.0
	_dose_slider.step = 0.2
	_dose_slider.value = 2.0
	_dose_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_dose_slider.value_changed.connect(func(v): _dose_label.text = _dose_text(v))
	dose_row.add_child(_dose_slider)
	_dose_label = Label.new()
	_dose_label.add_theme_font_size_override("font_size", 11)
	_dose_label.add_theme_color_override("font_color", TEXT)
	dose_row.add_child(_dose_label)
	panel.add_child(dose_row)

	panel.add_child(_action_button("Expose cell culture", _on_expose))

	_exposure_panel = RichTextLabel.new()
	_exposure_panel.bbcode_enabled = true
	_exposure_panel.fit_content = true
	_exposure_panel.custom_minimum_size = Vector2(0, 64)
	_exposure_panel.add_theme_font_size_override("normal_font_size", 10)
	panel.add_child(_exposure_panel)

	panel.add_child(_section_label("CHROMOSOME DOSAGE"))
	_trisomy21 = CheckButton.new()
	_trisomy21.text = "Trisomy 21 (+chr21)"
	_trisomy21.toggled.connect(_on_dosage_toggled)
	panel.add_child(_trisomy21)
	_monosomy_x = CheckButton.new()
	_monosomy_x.text = "Monosomy X (45,X)"
	_monosomy_x.toggled.connect(_on_dosage_toggled)
	panel.add_child(_monosomy_x)

	panel.add_child(_section_label("PHENOTYPE REPORT"))
	_phenotype_panel = RichTextLabel.new()
	_phenotype_panel.bbcode_enabled = true
	_phenotype_panel.fit_content = true
	_phenotype_panel.custom_minimum_size = Vector2(0, 96)
	_phenotype_panel.add_theme_font_size_override("normal_font_size", 11)
	panel.add_child(_phenotype_panel)

	panel.add_child(_action_button("Reset subject", _on_reset))


func _section_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 10)
	label.add_theme_color_override("font_color", DIM)
	return label


func _action_button(text: String, handler: Callable) -> Button:
	var btn := Button.new()
	btn.text = text
	btn.custom_minimum_size = Vector2(0, 30)
	btn.pressed.connect(handler)
	return btn


# =============================================================================
# DATA & STATE
# =============================================================================

func _chromosome() -> Dictionary:
	return GenomeSimulation.chromosome(_assembly, _selected_chr)


func _chrom_length() -> int:
	return maxi(1, int(_chromosome().get("length_bp", 1)))


func _span_bp() -> float:
	return float(_chrom_length()) / _zoom


func _left_bp() -> float:
	var span := _span_bp()
	return clampf(_center_bp - span * 0.5, 0.0, maxf(float(_chrom_length()) - span, 0.0))


func _select_chromosome(name: String) -> void:
	if GenomeSimulation.chromosome(_assembly, name).is_empty():
		return
	_selected_chr = name
	_zoom = 1.0
	_center_bp = float(_chrom_length()) * 0.5
	var on_chr := GenomeSimulation.genes_on(_assembly, name)
	if not on_chr.is_empty():
		_selected_gene = str(on_chr[0].get("symbol", ""))
	else:
		_selected_gene = ""
	_zoom = 6.0
	if _selected_gene != "":
		_center_bp = float(GenomeSimulation.gene(_assembly, _selected_gene).get("start", _center_bp))
	if _zygosity_opt != null:
		_restore_zygosity()


func _select_gene(symbol: String, focus: bool = false) -> void:
	var g := GenomeSimulation.gene(_assembly, symbol)
	if g.is_empty():
		return
	_selected_gene = symbol
	_selected_chr = str(g.get("chromosome", _selected_chr))
	if _zygosity_opt != null:
		_restore_zygosity()
	if focus:
		var length := float(g.get("end", 0)) - float(g.get("start", 0))
		if length <= 0.0:
			length = 5000.0
		_zoom = clampf(float(_chrom_length()) / (length * 8.0), 1.0, 200000.0)
		_center_bp = (float(g.get("start", 0)) + float(g.get("end", 0))) * 0.5


func _recompute_dosage() -> void:
	_dosage = GenomeSimulation.dosage_effects(_assembly, _karyotype)


func _refresh() -> void:
	_karotype_label_update()
	_rebuild_gene_list()
	_rebuild_hotspots()
	_refresh_mutagen_hint()
	_update_gene_info()
	_update_phenotypes()
	_queue()


func _queue() -> void:
	_status_label.text = _status
	queue_redraw()


func _karotype_label_update() -> void:
	_karyotype_label.text = "KARYOTYPE  %s   ·   %d curated loci   ·   %d recorded variants" % [
		GenomeSimulation.karyotype_label(_karyotype),
		GenomeSimulation.genes(_assembly).size(),
		_mutations.size()
	]


func _rebuild_gene_list() -> void:
	_gene_list.clear()
	var on_chr := GenomeSimulation.genes_on(_assembly, _selected_chr)
	for g in on_chr:
		var idx := _gene_list.add_item("%s  ·  %s" % [str(g.get("symbol", "")), GenomeSimulation.format_bp(int(g.get("start", 0)))])
		_gene_list.set_item_metadata(idx, str(g.get("symbol", "")))
		if str(g.get("symbol", "")) == _selected_gene:
			_gene_list.select(idx)


func _rebuild_hotspots() -> void:
	var previous := _hotspot_opt.selected
	_hotspot_opt.clear()
	var g := GenomeSimulation.gene(_assembly, _selected_gene)
	for hs in g.get("hotspots", []):
		_hotspot_opt.add_item("%s  %s" % [str(hs.get("c", "")), str(hs.get("protein", ""))])
	if _hotspot_opt.item_count == 0:
		_hotspot_opt.add_item("No curated hotspot at this locus")
		_hotspot_opt.disabled = true
	else:
		_hotspot_opt.disabled = false
		_hotspot_opt.select(clampi(previous, 0, _hotspot_opt.item_count - 1))


func _restore_zygosity() -> void:
	var g := GenomeSimulation.gene(_assembly, _selected_gene)
	var inheritance := str(g.get("inheritance", "")).to_lower()
	if inheritance.contains("x-linked"):
		_zygosity_opt.select(2)
	elif inheritance.contains("recessive") and not inheritance.contains("dominant"):
		_zygosity_opt.select(1)
	else:
		_zygosity_opt.select(0)


func _current_zygosity() -> String:
	match _zygosity_opt.selected:
		1: return "homozygous"
		2: return "hemizygous"
		_: return "heterozygous"


func _dose_text(value: float) -> String:
	var m := GenomeSimulation.mutagen(_assembly, _current_mutagen_id())
	return "%.1f %s" % [value, str(m.get("unit", "units"))]


func _current_mutagen_id() -> String:
	var list := GenomeSimulation.mutagens(_assembly)
	var idx := _mutagen_opt.selected
	if idx < 0 or idx >= list.size():
		return ""
	return str(list[idx].get("id", ""))


func _refresh_mutagen_hint() -> void:
	if _dose_label == null:
		return
	_dose_label.text = _dose_text(_dose_slider.value)
	_exposure_panel.text = "[color=#7f8c9b]%s[/color]" % str(GenomeSimulation.mutagen(_assembly, _current_mutagen_id()).get("mechanism", ""))


func _update_gene_info() -> void:
	var g := GenomeSimulation.gene(_assembly, _selected_gene)
	if g.is_empty():
		_gene_info.text = "[color=#7f8c9b]No gene selected.[/color]"
		return
	var phenotype_lines: Array[String] = []
	for ph in g.get("phenotypes", []):
		phenotype_lines.append("• %s (%s)" % [str(ph.get("label", "")), str(ph.get("zygosity", ""))])
	_gene_info.text = "[b]%s[/b] · chr%s:%s-%s (%s)\n%s\n[color=#7f8c9b]%s\n%s[/color]" % [
		str(g.get("symbol", "")),
		str(g.get("chromosome", "")),
		GenomeSimulation.format_bp(int(g.get("start", 0))),
		GenomeSimulation.format_bp(int(g.get("end", 0))),
		str(g.get("strand", "+")),
		str(g.get("summary", "")),
		str(g.get("inheritance", "")),
		"\n".join(phenotype_lines)
	]


func _update_phenotypes() -> void:
	var aggregated := GenomeSimulation.aggregate_phenotypes({"mutations": _mutations, "dosage": _dosage})
	if aggregated.is_empty():
		_phenotype_panel.text = "[color=#6f8590]No pathogenic findings in the curated model. Add a curated variant or chromosome-dosage change.[/color]"
		return
	var lines: Array[String] = []
	for entry in aggregated:
		var severity := str(entry.get("severity", "uncertain"))
		var color := GenomeSimulation.severity_color(severity)
		lines.append("[color=#%s]■ %s[/color]  [color=#7f8c9b]%s[/color]\n   [color=#aab6c2]%s[/color]" % [
			color.to_html(false), str(entry.get("label", "")), severity, str(entry.get("source", ""))
		])
	_phenotype_panel.text = "\n".join(lines)


# =============================================================================
# ACTIONS
# =============================================================================

func _on_gene_selected(index: int) -> void:
	var symbol := str(_gene_list.get_item_metadata(index))
	_select_gene(symbol, true)
	_refresh()


func _on_apply_hotspot() -> void:
	var g := GenomeSimulation.gene(_assembly, _selected_gene)
	var hotspots: Array = g.get("hotspots", [])
	if hotspots.is_empty():
		_status = "This locus has no curated hotspot. Arbitrary edits are reported as VUS."
		_queue()
		return
	var idx := clampi(_hotspot_opt.selected, 0, hotspots.size() - 1)
	var hs: Dictionary = hotspots[idx]
	var position := GenomeSimulation.hotpot_genomic_bp(g, hs)
	var alt := str(hs.get("alt", "T"))
	var result := GenomeSimulation.apply_point_mutation(_assembly, _selected_gene, position, alt, _current_zygosity())
	if bool(result.get("ok", false)):
		_mutations.append(result)
		_status = "%s %s applied (%s). %s" % [str(g.get("symbol", "")), str(hs.get("c", "")), _current_zygosity(), str(result.get("phenotype", ""))]
	_center_bp = float(position)
	_refresh()


func _on_expose() -> void:
	var mutagen_id := _current_mutagen_id()
	if mutagen_id == "":
		return
	var seed_value := int(Time.get_unix_time_from_system()) % 100000
	var result := GenomeSimulation.expose_to_mutagen(_assembly, mutagen_id, _dose_slider.value, seed_value, 0.32)
	_last_exposure = result
	if bool(result.get("nondisjunction", false)):
		var chr_name := str(result.get("affected_chromosome", "21"))
		var copies := int(_karyotype.get(chr_name, 2))
		_karyotype[chr_name] = copies + 1 if copies < 4 else copies
		_recompute_dosage()
		_status = "Spindle poison: nondisjunction in chromosome %s. Karyotype is now %s." % [chr_name, GenomeSimulation.karyotype_label(_karyotype)]
	else:
		var added := 0
		for entry in result.get("mutations", []):
			if bool(entry.get("ok", false)):
				_mutations.append(entry)
				added += 1
		var counts := []
		var summary: Dictionary = result.get("summary", {})
		for key in summary.keys():
			if str(key) == "total":
				continue
			counts.append("%s ×%d" % [str(key), int(summary[key])])
		_status = "%s: %d point events (%s)." % [str(result.get("mutagen", mutagen_id)), added, ", ".join(counts)]
		_exposure_panel.text = "[color=#7f8c9b]%s[/color]" % str(result.get("note", ""))
	var applied_count := 0
	for entry in result.get("mutations", []):
		if bool(entry.get("ok", false)):
			applied_count += 1
	if applied_count > 0:
		var skill_manager := get_node_or_null("/root/SkillManager")
		if skill_manager != null:
			skill_manager.add_xp("biology", mini(12 + applied_count * 4, 40), "Mutagen exposure series: %s" % mutagen_id)
	_refresh()


func _on_dosage_toggled(_pressed: bool) -> void:
	_karyotype.clear()
	if _trisomy21.button_pressed:
		_karyotype["21"] = 3
	if _monosomy_x.button_pressed:
		_karyotype["X"] = 1
	_recompute_dosage()
	_status = "Karyotype set to %s." % GenomeSimulation.karyotype_label(_karyotype)
	_refresh()


func _on_reset() -> void:
	_mutations.clear()
	_karyotype.clear()
	_dosage.clear()
	_last_exposure.clear()
	_trisomy21.set_pressed_no_signal(false)
	_monosomy_x.set_pressed_no_signal(false)
	_status = "Subject reset to the reference diploid model."
	_refresh()


# =============================================================================
# INPUT
# =============================================================================

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP or event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			if _track_rect().has_point(event.position):
				_zoom_at(event.position, 1.18 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.18)
				accept_event()
		elif event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
			if _karyotype_rect().has_point(event.position):
				var hit := _chromosome_at(event.position)
				if hit != "":
					_select_chromosome(hit)
					_refresh()
					accept_event()
			elif _track_rect().has_point(event.position):
				_dragging = true
				_last_mouse_x = event.position.x
				var gene := _gene_at_screen(event.position)
				if gene != "":
					_select_gene(gene)
					_refresh()
				accept_event()
		elif event.button_index == MOUSE_BUTTON_LEFT and not event.pressed:
			_dragging = false
	elif event is InputEventMouseMotion and _dragging:
		var span := _span_bp()
		var delta_bp := (event.position.x - _last_mouse_x) / maxf(_track_rect().size.x, 1.0) * span
		_center_bp = clampf(_center_bp - delta_bp, span * 0.5, maxf(float(_chrom_length()) - span * 0.5, span * 0.5))
		_last_mouse_x = event.position.x
		queue_redraw()
		accept_event()


func _zoom_at(mouse_pos: Vector2, factor: float) -> void:
	var track := _track_rect()
	var before_span := _span_bp()
	var fraction := clampf((mouse_pos.x - track.position.x) / maxf(track.size.x, 1.0), 0.0, 1.0)
	var anchor_bp := _left_bp() + fraction * before_span
	_zoom = clampf(_zoom * factor, 1.0, 300000.0)
	var after_span := _span_bp()
	_center_bp = anchor_bp + (0.5 - fraction) * after_span
	_center_bp = clampf(_center_bp, after_span * 0.5, maxf(float(_chrom_length()) - after_span * 0.5, after_span * 0.5))
	_status = "Locus view: %s across %.0f bp of chromosome %s" % [GenomeSimulation.format_bp(int(after_span)), after_span, _selected_chr]
	_queue()


# =============================================================================
# GEOMETRY
# =============================================================================

func _karyotype_rect() -> Rect2:
	return Rect2(18.0, HEADER_H + 20.0, size.x - SIDE_WIDTH - 34.0, maxf(size.y * 0.42, 120.0))


func _track_rect() -> Rect2:
	var top := _karyotype_rect().end.y + 12.0
	return Rect2(18.0, top, size.x - SIDE_WIDTH - 34.0, maxf(size.y - top - 34.0, 100.0))


func _gene_at_screen(pos: Vector2) -> String:
	var track := _track_rect()
	var span := _span_bp()
	var bp := _left_bp() + (pos.x - track.position.x) / maxf(track.size.x, 1.0) * span
	var candidates := GenomeSimulation.genes_overlapping(_assembly, _selected_chr, int(bp - span * 0.01), int(bp + span * 0.01))
	if candidates.is_empty():
		var exact := GenomeSimulation.gene_at(_assembly, _selected_chr, int(bp))
		if not exact.is_empty():
			return str(exact.get("symbol", ""))
		return ""
	return str(candidates[0].get("symbol", ""))


func _chromosome_at(pos: Vector2) -> String:
	var rect := _karyotype_rect()
	var cols := 9
	var rows := 3
	var cell := Vector2(rect.size.x / cols, rect.size.y / rows)
	var idx := int((pos.y - rect.position.y) / cell.y) * cols + int((pos.x - rect.position.x) / cell.x)
	var list := GenomeSimulation.chromosomes(_assembly)
	if idx >= 0 and idx < list.size():
		return str(list[idx].get("name", ""))
	return ""


# =============================================================================
# DRAWING
# =============================================================================

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BG, true)

	# Panel column.
	draw_rect(Rect2(size.x - SIDE_WIDTH - 4.0, HEADER_H, SIDE_WIDTH + 4.0, size.y - HEADER_H), PANEL_BG, true)
	draw_line(Vector2(0, HEADER_H), Vector2(size.x, HEADER_H), GRID, 1.0)
	draw_line(Vector2(size.x - SIDE_WIDTH - 4.0, HEADER_H), Vector2(size.x - SIDE_WIDTH - 4.0, size.y), GRID, 1.0)

	_draw_karyotype()
	_draw_track()
	_draw_legend()


func _draw_karyotype() -> void:
	var area := _karyotype_rect()
	var font := ThemeDB.fallback_font
	draw_string(font, area.position + Vector2(0, -6), "KARYOTYPE MAP · GRCh38 · 25 chromosomes",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)

	var list := GenomeSimulation.chromosomes(_assembly)
	var cols := 9
	var rows := 3
	var cell := Vector2(area.size.x / cols, area.size.y / rows)
	var max_len := 1
	for chr in list:
		max_len = maxi(max_len, int(chr.get("length_bp", 1)))

	for i in range(list.size()):
		var chr: Dictionary = list[i]
		var col := i % cols
		var row := i / cols
		var cell_origin := area.position + Vector2(col * cell.x, row * cell.y)
		var chr_name := str(chr.get("name", ""))
		var length := int(chr.get("length_bp", 1))
		var max_h := cell.y * 0.66
		var min_h := 18.0
		var h := maxf(min_h, max_h * float(length) / float(max_len))
		var w := 9.0
		var x := cell_origin.x + cell.x * 0.5 - w * 0.5
		var y := cell_origin.y + (cell.y - h) * 0.5

		var selected := chr_name == _selected_chr
		var base_color := Color(0.42, 0.62, 0.7, 0.85)
		if selected:
			base_color = CYAN
		var centromere_ratio := float(chr.get("centromere_bp", 0)) / float(maxf(length, 1))
		var cen_y := y + h * centromere_ratio

		# p arm and q arm, with a schematic band pattern.
		draw_rect(Rect2(x, y, w, maxf(cen_y - y, 1.0)), Color(base_color.r, base_color.g, base_color.b, 0.42), true)
		draw_rect(Rect2(x, cen_y, w, maxf(y + h - cen_y, 1.0)), Color(base_color.r, base_color.g, base_color.b, 0.3), true)
		for b in range(1, 9):
			var by := y + h * float(b) / 9.0
			if absf(by - cen_y) < 4.0:
				continue
			draw_line(Vector2(x, by), Vector2(x + w, by), Color(0.15, 0.22, 0.26, 0.55), 1.0)
		draw_rect(Rect2(x - 2.0, cen_y - 2.5, w + 4.0, 5.0), Color(0.1, 0.12, 0.15, 0.9), true)
		draw_rect(Rect2(x, y, w, h), base_color, false, 1.2)

		if selected:
			draw_rect(Rect2(x - 7.0, y - 7.0, w + 14.0, h + 14.0), Color(CYAN.r, CYAN.g, CYAN.b, 0.25), false, 1.5)

		# Curated genes as ticks along the chromosome.
		for g in GenomeSimulation.genes_on(_assembly, chr_name):
			var gene_ratio := (float(g.get("start", 0)) + float(g.get("end", 0))) * 0.5 / float(maxf(length, 1))
			var gy := y + h * gene_ratio
			draw_circle(Vector2(x + w + 4.0, gy), 1.6, Color(0.75, 0.82, 0.88, 0.75 if selected else 0.4))

		# Mutation markers.
		for m in _mutations:
			if str(m.get("chromosome", "")) != chr_name:
				continue
			var ratio := float(m.get("position", 0)) / float(maxf(length, 1))
			var my := y + h * ratio
			draw_circle(Vector2(x - 6.0, my), 2.2, GenomeSimulation.severity_color(str(m.get("severity", "uncertain"))))

		var label_color := CYAN if selected else DIM
		draw_string(font, Vector2(cell_origin.x + 4.0, cell_origin.y + cell.y - 4.0), chr_name,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 11, label_color)

	# Dosage badges.
	for entry in _dosage:
		var chr_name := str(entry.get("chromosome", ""))
		for i in range(list.size()):
			if str(list[i].get("name", "")) != chr_name:
				continue
			var col := i % cols
			var row := i / cols
			var badge_pos := area.position + Vector2(col * cell.x + cell.x * 0.5, row * cell.y + 4.0)
			draw_circle(badge_pos, 6.0, MAGENTA)
			draw_string(font, badge_pos + Vector2(-3.0, 4.0), "+", HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.1, 0.05, 0.1))


func _draw_track() -> void:
	var track := _track_rect()
	var font := ThemeDB.fallback_font
	draw_rect(track, Color(0.045, 0.062, 0.085, 0.9), true)
	draw_rect(track, GRID, false, 1.0)

	var chr := _chromosome()
	var length := _chrom_length()
	var span := _span_bp()
	var left := _left_bp()

	# Ruler.
	var tick_step := _nice_step(span / 8.0)
	var tick_bp := ceilf(left / tick_step) * tick_step
	while tick_bp <= left + span:
		var x := track.position.x + (tick_bp - left) / span * track.size.x
		draw_line(Vector2(x, track.position.y), Vector2(x, track.position.y + track.size.y), Color(0.2, 0.27, 0.32, 0.4), 1.0)
		draw_string(font, Vector2(x + 3.0, track.position.y + 12.0), _format_tick(tick_bp),
			HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)
		tick_bp += tick_step

	draw_string(font, track.position + Vector2(6.0, track.size.y - 8.0),
		"CHR %s  ·  %s–%s  ·  %s  ·  zoom %.0fx" % [
			_selected_chr,
			GenomeSimulation.format_bp(int(left)),
			GenomeSimulation.format_bp(int(left + span)),
			GenomeSimulation.karyotype_label(_karyotype),
			_zoom
		], HORIZONTAL_ALIGNMENT_LEFT, -1, 10, DIM)

	# Genes as lanes.
	var lanes: Array[float] = [0.0, 0.0, 0.0]
	var lane_height := 13.0
	var lane_top := track.position.y + 30.0
	for g in GenomeSimulation.genes_on(_assembly, _selected_chr):
		var gs := float(g.get("start", 0))
		var ge := float(g.get("end", 0))
		if ge < left or gs > left + span:
			continue
		var x1 := track.position.x + (clampf(gs, left, left + span) - left) / span * track.size.x
		var x2 := track.position.x + (clampf(ge, left, left + span) - left) / span * track.size.x
		var width := maxf(x2 - x1, 2.0)
		var lane := 0
		for i in range(lanes.size()):
			if x1 > lanes[i]:
				lane = i
				break
		lanes[lane] = x2
		var y := lane_top + lane * (lane_height + 3.0)
		var is_selected := str(g.get("symbol", "")) == _selected_gene
		var color := AMBER if is_selected else GENE_COLOR
		draw_rect(Rect2(x1, y, width, lane_height), Color(color.r, color.g, color.b, 0.75 if is_selected else 0.4), true)
		draw_rect(Rect2(x1, y, width, lane_height), color, false, 1.0)
		if span < 8_000_000.0 or is_selected:
			draw_string(font, Vector2(x1 + 2.0, y - 2.0), str(g.get("symbol", "")),
				HORIZONTAL_ALIGNMENT_LEFT, -1, 10, color)

	# Curated hotspots of the selected gene.
	var selected_gene := GenomeSimulation.gene(_assembly, _selected_gene)
	if not selected_gene.is_empty() and str(selected_gene.get("chromosome", "")) == _selected_chr:
		for hs in selected_gene.get("hotspots", []):
			var pos := float(GenomeSimulation.hotpot_genomic_bp(selected_gene, hs))
			if pos < left or pos > left + span:
				continue
			var x := track.position.x + (pos - left) / span * track.size.x
			var y := track.position.y + track.size.y - 26.0
			draw_line(Vector2(x, track.position.y + 18.0), Vector2(x, y), Color(0.95, 0.6, 0.3, 0.55), 1.2)
			draw_circle(Vector2(x, y), 3.2, AMBER)
			draw_string(font, Vector2(x + 5.0, y + 3.0), str(hs.get("c", "")), HORIZONTAL_ALIGNMENT_LEFT, -1, 9, AMBER)

	# Recorded mutations.
	for m in _mutations:
		if str(m.get("chromosome", "")) != _selected_chr:
			continue
		var pos := float(m.get("position", 0))
		if pos < left or pos > left + span:
			continue
		var x := track.position.x + (pos - left) / span * track.size.x
		var color := GenomeSimulation.severity_color(str(m.get("severity", "uncertain")))
		var pulse := 1.0 + 0.2 * sin(_pulse * 3.0)
		draw_line(Vector2(x, track.position.y + 20.0), Vector2(x, track.position.y + track.size.y - 34.0), Color(color.r, color.g, color.b, 0.5), 1.4)
		draw_circle(Vector2(x, track.position.y + 20.0), 3.6 * pulse, color)

	# Base-resolution hint.
	if span < 1200.0:
		draw_string(font, track.position + Vector2(6.0, track.size.y - 24.0),
			"Base-resolution view. Reference sequence is only asserted at curated hotspots; elsewhere the model reports VUS.",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 9, AMBER)


func _draw_legend() -> void:
	var font := ThemeDB.fallback_font
	var x := 20.0
	var y := size.y - 64.0
	draw_circle(Vector2(x, y), 3.0, AMBER)
	draw_string(font, Vector2(x + 9.0, y + 3.0), "curated hotspot", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)
	draw_circle(Vector2(x + 104.0, y), 3.0, GenomeSimulation.severity_color("severe"))
	draw_string(font, Vector2(x + 113.0, y + 3.0), "recorded variant", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)
	draw_circle(Vector2(x + 212.0, y), 3.0, MAGENTA)
	draw_string(font, Vector2(x + 221.0, y + 3.0), "copy-number change", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, DIM)


func _nice_step(raw: float) -> float:
	if raw <= 0.0:
		return 1.0
	var exponent := floor(log(raw) / log(10.0))
	var base := pow(10.0, exponent)
	var fraction := raw / base
	var nice := 1.0
	if fraction > 5.0:
		nice = 10.0
	elif fraction > 2.0:
		nice = 5.0
	elif fraction > 1.0:
		nice = 2.0
	return nice * base


func _format_tick(bp_value: float) -> String:
	if bp_value >= 1_000_000.0:
		return "%.1fMb" % (bp_value / 1_000_000.0)
	if bp_value >= 1000.0:
		return "%.0fkb" % (bp_value / 1000.0)
	return "%dbp" % int(bp_value)
