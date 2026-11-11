# ChemLab NMR Spectrometer UI
# Real-time NMR spectrometer interface with spectrum visualization

extends Node3D
class_name NMRUI

# =============================================================================
# SIGNALS
# =============================================================================

signal analyze_requested(sample_id: String)
signal cancel_requested()
signal eject_requested()
signal power_toggled(is_on: bool)

# =============================================================================
# NODE REFERENCES
# =============================================================================

@onready var root_panel: Control = get_node_or_null("RootPanel")
@onready var main_panel: PanelContainer = get_node_or_null("RootPanel/MainPanel")
@onready var vbox: VBoxContainer = get_node_or_null("RootPanel/MainPanel/VBoxContainer")
@onready var title_label: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/HeaderBar/TitleLabel")
@onready var status_dot: Control = get_node_or_null("RootPanel/MainPanel/VBoxContainer/HeaderBar/StatusIndicator/StatusDot")
@onready var status_label: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/HeaderBar/StatusIndicator/StatusLabel")
@onready var power_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/HeaderBar/PowerButton")
@onready var sample_info_card: PanelContainer = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SampleInfoCard")
@onready var sample_name_label: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SampleInfoCard/SampleVBox/SampleHeader/SampleNameLabel")
@onready var compound_value: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SampleInfoCard/SampleVBox/SampleDetails/CompoundValue")
@onready var concentration_value: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SampleInfoCard/SampleVBox/SampleDetails/ConcentrationValue")
@onready var solvent_value: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SampleInfoCard/SampleVBox/SampleDetails/SolventValue")
@onready var temp_value: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SampleInfoCard/SampleVBox/SampleDetails/TempValue")
@onready var spectrum_graph: Control = get_node_or_null("RootPanel/MainPanel/VBoxContainer/SpectrumContainer/SpectrumGraph")
@onready var analyze_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/AnalyzeButton")
@onready var progress_bar: ProgressBar = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/ProgressBar")
@onready var cancel_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/CancelButton")
@onready var eject_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/EjectButton")
@onready var error_panel: PanelContainer = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ErrorPanel")
@onready var error_label: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ErrorPanel/ErrorLabel")
@onready var status_dot: Control = get_node_or_null("RootPanel/MainPanel/VBoxContainer/HeaderBar/StatusIndicator/StatusDot")
@onready var status_label: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/HeaderBar/StatusIndicator/StatusLabel")
@onready var analyze_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/AnalyzeButton")
@onready var progress_bar: ProgressBar = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/ProgressBar")
@onready var cancel_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/CancelButton")
@onready var eject_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/EjectButton")
@onready var error_panel: PanelContainer = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ErrorPanel")
@onready var error_label: Label = get_node_or_null("RootPanel/ErrorPanel/ErrorLabel")
@onready var analyze_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/AnalyzeButton")
@onready var progress_bar: ProgressBar = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/ProgressBar")
@onready var cancel_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/CancelButton")
@onready var eject_button: Button = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ControlBar/EjectButton")
@onready var error_panel: PanelContainer = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ErrorPanel")
@onready var error_label: Label = get_node_or_null("RootPanel/MainPanel/VBoxContainer/ErrorPanel/ErrorLabel")

# =============================================================================
# STATE
# =============================================================================

var _nmr_spectrometer: Node = null
var _current_sample_data: Dictionary = {}
var _is_analyzing: bool = false
var _analysis_progress: float = 0.0
var _spectrum_texture: ImageTexture = null
var _spectrum_material: StandardMaterial3D = null

# =============================================================================
# LIFECYCLE
# =============================================================================

func _ready() -> void:
	_setup_ui()
	_connect_signals()
	_update_ui_state()

	# Create spectrum drawing material
	_setup_spectrum_visualization()

	print(">>> [NMRUI] Initialized")


func _setup_ui() -> void:
	# Hide sample info initially
	sample_info_card.visible = false
	progress_bar.visible = false
	cancel_button.visible = false
	eject_button.visible = false
	error_panel.visible = false
	progress_bar.value = 0

	# Connect button signals
	if power_button:
		power_button.pressed.connect(_on_power_toggled)
	if analyze_button:
		analyze_button.pressed.connect(_on_analyze_pressed)
	if cancel_button:
		cancel_button.pressed.connect(_on_cancel_pressed)
	if eject_button:
		eject_button.pressed.connect(_on_eject_pressed)


func _connect_signals() -> void:
	# Connect to NMR spectrometer if available
	var nmr = get_node_or_null("/root/AnalyticalLab/NMRSpectrometer")
	if not nmr:
		# Try to find NMR in scene
		var tree = get_tree()
		if tree:
			var nmr_nodes = tree.get_nodes_in_group("nmr_spectrometer")
			if nmr_nodes.size() > 0:
				_nmr_spectrometer = nmr_nodes[0]

	if _nmr_spectrometer:
		_nmr_spectrometer.sample_inserted.connect(_on_sample_inserted)
		_nmr_spectrometer.sample_removed.connect(_on_sample_removed)
		_nmr_spectrometer.analysis_started.connect(_on_analysis_started)
		_nmr_spectrometer.analysis_completed.connect(_on_analysis_completed)
		_nmr_spectrometer.analysis_failed.connect(_on_analysis_failed)
		_nmr_spectrometer.spectrum_updated.connect(_on_spectrum_updated)
		_nmr_spectrometer.power_toggled.connect(_on_power_toggled)


# =============================================================================
# SPECTRUM VISUALIZATION
# =============================================================================

func _setup_spectrum_visualization() -> void:
	# Create a shader material for real-time spectrum rendering
	var shader_code = """
	shader_type canvas_item;
	render_mode unshaded;

	uniform sampler2D spectrum_texture : hint_default_white;
	uniform float time : hint_range(0, 10);
	uniform float ppm_min : hint_range(-2, 2);
	uniform float ppm_max : hint_range(10, 14);
	uniform vec4 peak_color : hint_color = vec4(0.2, 0.8, 1.0, 1.0);
	uniform vec4 grid_color : hint_color = vec4(0.15, 0.3, 0.5, 0.5);
	uniform vec4 axis_color : hint_color = vec4(0.4, 0.6, 0.8, 0.8);

	void fragment() {
		vec2 uv = FRAGCOORD.xy / SCREEN_PIXEL_SIZE.xy;

		// Draw grid
		float grid_x = fract(uv.x * 12.0);
		float grid_y = fract(uv.y * 10.0);
		float grid = step(0.98, max(grid_x, grid_y));

		// Draw spectrum from texture
		vec4 spectrum_color = texture(spectrum_texture, uv);

		// Combine
		vec4 color = mix(spectrum_color * peak_color, grid_color * grid, grid);
		color = mix(color, axis_color, step(0.01, abs(uv.y - 0.5)));

		COLOR = color;
	}
	"""

	var shader = ShaderMaterial.new()
	shader.shader = RS.new()
	shader.shader.code = shader_code

	if spectrum_graph:
		spectrum_graph.material_override = shader
		spectrum_graph.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spectrum_graph.size_flags_vertical = Control.SIZE_EXPAND_FILL

	# Also apply shader to 3D DisplayScreen mesh if available
	if _nmr_spectrometer and _nmr_spectrometer.has_node("DisplayScreen"):
		var display_screen = _nmr_spectrometer.get_node("DisplayScreen")
		if display_screen and display_screen.material_override:
			var display_mat = display_screen.material_override.duplicate()
			display_mat.shader = RS.new()
			display_mat.shader.code = """
				shader_type spatial;
				render_mode unshaded;

				uniform sampler2D spectrum_texture : hint_default_white;
				uniform float time : hint_range(0, 10);
				uniform float ppm_min : hint_range(-2, 2);
				uniform float ppm_max : hint_range(10, 14);
				uniform vec4 peak_color : hint_color = vec4(0.2, 0.8, 1.0, 1.0);
				uniform vec4 grid_color : hint_color = vec4(0.15, 0.3, 0.5, 0.5);
				uniform vec4 axis_color : hint_color = vec4(0.4, 0.6, 0.8, 0.8);

				void fragment() {
					vec2 uv = UV;
					// Draw grid
					float grid_x = fract(uv.x * 12.0);
					float grid_y = fract(uv.y * 10.0);
					float grid = step(0.98, max(grid_x, grid_y));

					// Draw spectrum from texture
					vec4 spectrum_color = texture(spectrum_texture, uv);

					// Combine
					vec4 color = mix(spectrum_color * peak_color, grid_color * grid, grid);
					color = mix(color, axis_color, step(0.01, abs(uv.y - 0.5)));

					COLOR = color;
				}
			"""
			display_screen.material_override = display_mat
			_nmr_spectrometer._display_screen_material = display_mat
			print(">>> [NMRUI] Applied spectrum shader to DisplayScreen mesh")


# =============================================================================
# SPECTRUM RENDERING
# =============================================================================

func _render_spectrum(spectrum_data: Dictionary) -> void:
	if not spectrum_data.has("x_ppm") or not spectrum_data.has("y_intensity"):
		return

	var x_ppm = spectrum_data["x_ppm"]
	var y_intensity = spectrum_data["y_intensity"]

	if x_ppm.size() != y_intensity.size() or x_ppm.is_empty():
		return

	# Create image texture from spectrum data
	var img = Image.create(x_ppm.size(), 1, false, Image.FORMAT_RGBA8)

	var max_intensity = 0.0
	for i in range(y_intensity.size()):
		if y_intensity[i] > max_intensity:
			max_intensity = y_intensity[i]

	if max_intensity <= 0.0:
		max_intensity = 1.0

	var ppm_min = spectrum_data.get("x_ppm", []).size() > 0 ? spectrum_data["x_ppm"][0] : -1.0
	var ppm_max = spectrum_data.get("x_ppm", []).size() > 0 ? spectrum_data["x_ppm"][-1] : 11.0
	var ppm_range = ppm_max - ppm_min

	# Lock image for writing
	img.lock()

	for i in range(x_ppm.size()):
		var intensity = y_intensity[i] / max_intensity
		var ppm = x_ppm[i]
		var x = int(float(i) / float(x_ppm.size()) * 1024.0)
		var h = int(intensity * 256.0)

		for y in range(256):
			var alpha = float(y) / 256.0
			var color_val = smoothstep(0.0, float(h) / 256.0, float(y) / 256.0)
			var color = Color(0.2, 0.8, 1.0, color_val * 0.8)
			img.set_pixel(x, 255 - y, color)

	img.unlock()

	var texture = ImageTexture.create_from_image(img)

	if spectrum_graph and spectrum_graph.material_override:
		spectrum_graph.material_override.set_shader_parameter("spectrum_texture", texture)

	# Also update 3D display screen material
	if _nmr_spectrometer and _nmr_spectrometer._display_screen_material:
		_nmr_spectrometer._display_screen_material.set_shader_parameter("spectrum_texture", texture)


# =============================================================================
# UI STATE MANAGEMENT
# =============================================================================

func _update_ui_state() -> void:
	if not _nmr_spectrometer:
		# No NMR found
		title_label.text = "NMR Spectrometer (Not Found)"
		status_label.text = "Disconnected"
		_set_status_color(Color(1, 0.3, 0.3, 1))
		sample_info_card.visible = false
		analyze_button.disabled = true
		power_button.text = "Power"
		progress_bar.visible = false
		cancel_button.visible = false
		eject_button.visible = false
		error_panel.visible = false
		sample_info_card.visible = false
		sample_name_label.text = "NMR Not Found"
		return

	var nmr = _nmr_spectrometer

	# Power button
	power_button.text = "Power: %s" % ("ON" if nmr.is_powered_on else "OFF")

	if nmr.is_powered_on:
		status_label.text = "Ready"
		_set_status_color(Color(0, 1, 0.5, 1))
		power_button.text = "Power: ON"
		analyze_button.disabled = false

		# Check sample status
		if nmr.current_sample:
			_on_sample_inserted(nmr.get_sample_queue()[0] if nmr.get_sample_queue().size() > 0 else {})
		else:
			sample_info_card.visible = false
			analyze_button.text = "Start Analysis"
			analyze_button.disabled = false
			progress_bar.visible = false
			cancel_button.visible = false
			eject_button.visible = false
			error_panel.visible = false

			_update_display_state()
	else:
		status_label.text = "Powered Off"
		_set_status_color(Color(0.5, 0.5, 0.5, 1))
		power_button.text = "Power: OFF"
		sample_info_card.visible = false
		analyze_button.disabled = true
		progress_bar.visible = false
		cancel_button.visible = false
		eject_button.visible = false
		error_panel.visible = false


func _set_status_color(color: Color) -> void:
	if status_dot:
		var mat = status_dot.get_material()
		if not mat:
			mat = CanvasItemMaterial.new()
			status_dot.material = mat
		mat.modulate = color


func _update_display_state() -> void:
	if not _nmr_spectrometer:
		return

	var nmr = _nmr_spectrometer
	var current_spectrum = nmr.get_current_spectrum()

	if current_spectrum.has("y_intensity"):
		# Update spectrum visualization
		_render_spectrum(current_spectrum)

		# Update sample info card
		if _current_sample_data:
			sample_info_card.visible = true
			sample_name_label.text = _current_sample_data.get("compound_name", "Unknown")
			compound_value.text = _current_sample_data.get("compound_name", "—")
			concentration_value.text = "%0.1f mM" % _current_sample_data.get("concentration_mM", 0.0)
			solvent_value.text = _current_sample_data.get("solvent", "—")
			temp_value.text = "%0.1f °C" % _current_sample_data.get("temperature_c", 25.0)
		else
			sample_info_card.visible = false
	else:
		sample_info_card.visible = false


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

func _on_sample_inserted(sample_info: Dictionary) -> void:
	_current_sample_data = sample_info
	_update_display_state()

	analyze_button.text = "Start Analysis"
	analyze_button.disabled = false
	progress_bar.visible = false
	cancel_button.visible = false
	eject_button.visible = true
	error_panel.visible = false

	print("[NMRUI] Sample inserted: ", sample_info.get("sample_id", "unknown"))


func _on_sample_removed(sample_info: Dictionary) -> void:
	_current_sample_data = {}
	_update_ui_state()

	analyze_button.text = "Start Analysis"
	analyze_button.disabled = true
	progress_bar.visible = false
	cancel_button.visible = false
	eject_button.visible = false
	error_panel.visible = false

	print("[NMRUI] Sample removed")


func _on_analysis_started(sample_id: String) -> void:
	_is_analyzing = true

	analyze_button.text = "Analyzing..."
	analyze_button.disabled = true
	progress_bar.visible = true
	progress_bar.value = 0
	cancel_button.visible = true
	eject_button.visible = false
	error_panel.visible = false

	print("[NMRUI] Analysis started: ", sample_id)


func _on_analysis_completed(sample_id: String, spectrum_data: Dictionary) -> void:
	_is_analyzing = false

	analyze_button.text = "Start Analysis"
	analyze_button.disabled = false
	progress_bar.visible = false
	progress_bar.value = 100
	cancel_button.visible = false
	eject_button.visible = true
	error_panel.visible = false

	# Render spectrum
	if spectrum_data:
		_render_spectrum(spectrum_data)

	print("[NMRUI] Analysis completed: ", sample_id)


func _on_analysis_failed(sample_id: String, error: String) -> void:
	_is_analyzing = false

	analyze_button.text = "Start Analysis"
	analyze_button.disabled = false
	progress_bar.visible = false
	cancel_button.visible = false
	eject_button.visible = true
	error_panel.visible = true
	error_label.text = "Error: %s" % error

	print("[NMRUI] Analysis failed: ", error)


func _on_spectrum_updated(spectrum_data: Dictionary) -> void:
	_render_spectrum(spectrum_data)


func _on_power_toggled(is_on: bool) -> void:
	if is_on:
		power_button.text = "Power: ON"
		status_label.text = "Ready"
		_set_status_color(Color(0, 1, 0.5, 1))
		analyze_button.disabled = false
	else:
		power_button.text = "Power: OFF"
		status_label.text = "Powered Off"
		_set_status_color(Color(0.5, 0.5, 0.5, 1))
		analyze_button.disabled = true
		progress_bar.visible = false
		cancel_button.visible = false
		eject_button.visible = false
		error_panel.visible = false
		sample_info_card.visible = false


# =============================================================================
# BUTTON HANDLERS
# =============================================================================

func _on_power_toggled() -> void:
	if _nmr_spectrometer:
		_nmr_spectrometer.toggle_power()
	power_toggled.emit(_nmr_spectrometer.is_powered_on)


func _on_analyze_pressed() -> void:
	if not _nmr_spectrometer:
		return

	var nmr = _nmr_spectrometer
	if nmr.current_sample and not _is_analyzing:
		# Request analysis via SimulationBridge
		var sim_bridge = get_node_or_null("/root/SimulationBridge")
		if sim_bridge and sim_bridge.has_method("request_nmr_analysis"):
			var sample_info = _get_current_sample_info()
			var request = {
				"sample_id": sample_info.get("sample_id", "unknown"),
				"compound_name": sample_info.get("compound_name", "Unknown"),
				"concentration_mM": sample_info.get("concentration_mM", 50.0),
				"solvent": sample_info.get("solvent", "CDCl3"),
				"temperature_c": sample_info.get("temperature_c", 25.0),
				"magnetic_field_t": 9.4,
				"spectral_width_ppm": 12.0,
				"number_of_scans": 16,
				"relaxation_delay_sec": 1.0,
			}
			var result = sim_bridge.request_nmr_analysis(request)
			if result.get("status") == "SUCCESS":
				# Process result
				_on_analysis_completed(sample_info.get("sample_id", "unknown"), result.get("spectrum", {}))
			else:
				_on_analysis_failed(sample_info.get("sample_id", "unknown"), result.get("error", "Unknown error"))
		elif nmr.current_sample:
			# Fallback: use local simulation
			nmr._start_next_analysis()


func _on_cancel_pressed() -> void:
	if _nmr_spectrometer and _is_analyzing:
		_nmr_spectrometer._cancel_analysis()
		cancel_requested.emit()


func _on_eject_pressed() -> void:
	if _nmr_spectrometer and _nmr_spectrometer.current_sample:
		var player = get_tree().get_first_node_in_group("player")
		_nmr_spectrometer._try_remove_sample(player)
		eject_requested.emit()


func _get_current_sample_info() -> Dictionary:
	if _nmr_spectrometer and _nmr_spectrometer.current_sample:
		return _nmr_spectrometer._extract_sample_metadata(_nmr_spectrometer.current_sample)
	return {}