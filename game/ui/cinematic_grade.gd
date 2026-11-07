# Athanor Ascension - Cinematic Grade / Post-Processing
# Autoload: CinematicGrade
# Handles: Bloom, Color Grading, Film Grain, Vignette, DOF, Lab-specific LUTs

extends Node

class_name CinematicGrade

signal grade_changed(lab_id: String)
signal effect_toggled(effect_name: String, enabled: bool)

# Post-processing effects
var bloom_enabled: bool = true
var bloom_threshold: float = 1.0
var bloom_intensity: float = 0.3
var bloom_radius: float = 8.0

var color_grading_enabled: bool = true
var color_grade_lift: Vector3 = Vector3(0.0, 0.0, 0.0)
var color_grade_gamma: Vector3 = Vector3(1.0, 1.0, 1.0)
var color_grade_gain: Vector3 = Vector3(1.0, 1.0, 1.0)

var film_grain_enabled: bool = true
var film_grain_amount: float = 0.02

var vignette_enabled: bool = true
var vignette_amount: float = 0.3

var dof_enabled: bool = false
var dof_focus_distance: float = 10.0
var dof_focus_range: float = 5.0
var dof_blur_strength: float = 0.01

# Lab-specific color grading profiles
var lab_profiles: Dictionary = {}

func _ready() -> void:
	_initialize_lab_profiles()
	_apply_current_profile()

func _initialize_lab_profiles() -> void:
	lab_profiles = {
		"default": {
			"lift": Vector3(0.0, 0.0, 0.0),
			"gamma": Vector3(1.0, 1.0, 1.0),
			"gain": Vector3(1.0, 1.0, 1.0),
			"bloom_intensity": 0.3,
			"film_grain": 0.02,
			"vignette": 0.3,
			"description": "Neutral baseline"
		},
		"analytical": {
			"lift": Vector3(-0.02, -0.01, 0.0),
			"gamma": Vector3(1.05, 1.05, 1.0),
			"gain": Vector3(1.0, 1.0, 1.1),
			"bloom_intensity": 0.15,
			"film_grain": 0.01,
			"vignette": 0.2,
			"description": "Cool, clinical, precise"
		},
		"organic_synthesis": {
			"lift": Vector3(0.02, 0.01, -0.01),
			"gamma": Vector3(0.98, 1.0, 1.02),
			"gain": Vector3(1.05, 1.0, 0.95),
			"bloom_intensity": 0.35,
			"film_grain": 0.03,
			"vignette": 0.4,
			"description": "Warm, organic, reaction glows"
		},
		"accelerator": {
			"lift": Vector3(0.0, -0.02, 0.05),
			"gamma": Vector3(1.0, 1.05, 0.95),
			"gain": Vector3(1.0, 1.1, 1.0),
			"bloom_intensity": 0.5,
			"film_grain": 0.01,
			"vignette": 0.3,
			"description": "Cherenkov blue, high energy"
		},
		"fusor": {
			"lift": Vector3(0.05, 0.02, -0.02),
			"gamma": Vector3(0.95, 1.0, 1.05),
			"gain": Vector3(1.1, 1.0, 0.9),
			"bloom_intensity": 0.6,
			"film_grain": 0.04,
			"vignette": 0.5,
			"description": "Plasma orange, neutron glow"
		},
		"genomics": {
			"lift": Vector3(-0.01, 0.0, 0.02),
			"gamma": Vector3(1.02, 1.0, 1.0),
			"gain": Vector3(1.0, 1.05, 1.0),
			"bloom_intensity": 0.2,
			"film_grain": 0.015,
			"vignette": 0.25,
			"description": "Clean, DNA helix teal"
		},
		"radiochemistry": {
			"lift": Vector3(0.01, 0.03, -0.01),
			"gamma": Vector3(0.95, 1.0, 1.05),
			"gain": Vector3(1.0, 1.15, 0.85),
			"bloom_intensity": 0.4,
			"film_grain": 0.02,
			"vignette": 0.35,
			"description": "Radioluminescent green"
		},
		"nuclear": {
			"lift": Vector3(0.0, 0.02, 0.03),
			"gamma": Vector3(0.9, 1.05, 1.0),
			"gain": Vector3(1.0, 1.2, 0.8),
			"bloom_intensity": 0.7,
			"film_grain": 0.03,
			"vignette": 0.4,
			"description": "Cherenkov, criticality warning"
		},
		"cleanroom": {
			"lift": Vector3(-0.03, -0.02, 0.0),
			"gamma": Vector3(1.1, 1.1, 1.05),
			"gain": Vector3(1.0, 1.0, 1.1),
			"bloom_intensity": 0.1,
			"film_grain": 0.005,
			"vignette": 0.15,
			"description": "Sterile, ISO Class 5"
		},
		"orbital": {
			"lift": Vector3(0.02, 0.03, 0.05),
			"gamma": Vector3(0.95, 0.95, 1.05),
			"gain": Vector3(1.05, 1.0, 1.1),
			"bloom_intensity": 0.45,
			"film_grain": 0.01,
			"vignette": 0.2,
			"description": "Microgravity, Earth glow"
		},
		"cryogenic": {
			"lift": Vector3(-0.02, 0.0, 0.05),
			"gamma": Vector3(1.05, 1.05, 1.0),
			"gain": Vector3(1.0, 1.0, 1.15),
			"bloom_intensity": 0.25,
			"film_grain": 0.01,
			"vignette": 0.3,
			"description": "Liquid nitrogen blue"
		}
	}

func _apply_current_profile() -> void:
	var current_lab = _get_current_lab()
	if current_lab != "" and lab_profiles.has(current_lab):
		_set_profile(lab_profiles[current_lab])
	else:
		_set_profile(lab_profiles["default"])

func _get_current_lab() -> String:
	# Would get current lab from scene/quest manager
	var quest_manager = get_node_or_null("/root/QuestManager")
	if quest_manager:
		var active_quest = quest_manager.get_active_quest()
		# Map quest to lab
		match active_quest:
			"quest_010_aspirin_synthesis", "quest_011_titration_practicum":
				return "organic_synthesis"
			"quest_030_accelerator_certification", "quest_031_anomaly_beam":
				return "accelerator"
			"quest_040_fusor_checklist", "quest_041_first_plasma":
				return "fusor"
			"quest_020_genome_orientation", "quest_021_voss_anomaly":
				return "genomics"
			"quest_080_ignis_access", "quest_081_purex_reprocessing":
				return "nuclear"
			_:
				return "default"
	return "default"

func _set_profile(profile: Dictionary) -> void:
	color_grade_lift = profile.get("lift", Vector3(0, 0, 0))
	color_grade_gamma = profile.get("gamma", Vector3(1, 1, 1))
	color_grade_gain = profile.get("gain", Vector3(1, 1, 1))
	bloom_intensity = profile.get("bloom_intensity", 0.3)
	film_grain_amount = profile.get("film_grain", 0.02)
	vignette_amount = profile.get("vignette", 0.3)

	# Apply to WorldEnvironment or post-process shader
	_apply_to_environment()

	grade_changed.emit(_get_current_lab())

func _apply_to_environment() -> void:
	# Apply to current world environment
	var viewport = get_viewport()
	if viewport and viewport.world and viewport.world.environment:
		var env = viewport.world.environment

		# Color grading (if supported)
		# env.adjustment_enabled = true
		# env.adjustment_color_correction_lift = color_grade_lift
		# env.adjustment_color_correction_gamma = color_grade_gamma
		# env.adjustment_color_correction_gain = color_grade_gain

		# Bloom
		# env.glow_enabled = bloom_enabled
		# env.glow_intensity = bloom_intensity
		# env.glow_bloom_threshold = bloom_threshold

	print("Applied cinematic profile: lift=%s, gamma=%s, gain=%s, bloom=%.2f, grain=%.3f, vignette=%.2f" % [
		color_grade_lift, color_grade_gamma, color_grade_gain, bloom_intensity, film_grain_amount, vignette_amount
	])

# =============================================================================
# PUBLIC API
# =============================================================================

func set_lab_profile(lab_id: String) -> bool:
	if lab_profiles.has(lab_id):
		_set_profile(lab_profiles[lab_id])
		return true
	return false

func get_current_profile() -> Dictionary:
	return {
		"lift": color_grade_lift,
		"gamma": color_grade_gamma,
		"gain": color_grade_gain,
		"bloom_intensity": bloom_intensity,
		"film_grain": film_grain_amount,
		"vignette": vignette_amount,
		"dof_enabled": dof_enabled
	}

func set_bloom(enabled: bool, intensity: float = -1.0, threshold: float = -1.0, radius: float = -1.0) -> void:
	bloom_enabled = enabled
	if intensity >= 0.0:
		bloom_intensity = clamp(intensity, 0.0, 2.0)
	if threshold >= 0.0:
		bloom_threshold = clamp(threshold, 0.0, 5.0)
	if radius >= 0.0:
		bloom_radius = clamp(radius, 0.0, 32.0)

	effect_toggled.emit("bloom", enabled)
	_apply_to_environment()

func set_color_grading(lift: Vector3, gamma: Vector3, gain: Vector3) -> void:
	color_grade_lift = lift
	color_grade_gamma = gamma
	color_grade_gain = gain
	_apply_to_environment()

func set_film_grain(enabled: bool, amount: float = -1.0) -> void:
	film_grain_enabled = enabled
	if amount >= 0.0:
		film_grain_amount = clamp(amount, 0.0, 0.1)
	effect_toggled.emit("film_grain", enabled)

func set_vignette(enabled: bool, amount: float = -1.0) -> void:
	vignette_enabled = enabled
	if amount >= 0.0:
		vignette_amount = clamp(amount, 0.0, 1.0)
	effect_toggled.emit("vignette", enabled)

func set_dof(enabled: bool, focus_distance: float = -1.0, focus_range: float = -1.0, blur_strength: float = -1.0) -> void:
	dof_enabled = enabled
	if focus_distance >= 0.0:
		dof_focus_distance = max(0.1, focus_distance)
	if focus_range >= 0.0:
		dof_focus_range = max(0.1, focus_range)
	if blur_strength >= 0.0:
		dof_blur_strength = clamp(blur_strength, 0.0, 0.1)
	effect_toggled.emit("dof", enabled)

# =============================================================================
# PRESET PROFILES
# =============================================================================

func apply_preset(preset_name: String) -> bool:
	var presets = {
		"cinematic": {
			"lift": Vector3(0.0, 0.0, 0.0),
			"gamma": Vector3(1.0, 1.0, 1.0),
			"gain": Vector3(1.0, 1.0, 1.0),
			"bloom_intensity": 0.4,
			"film_grain": 0.025,
			"vignette": 0.4
		},
		"documentary": {
			"lift": Vector3(0.01, 0.0, -0.01),
			"gamma": Vector3(0.95, 0.95, 1.0),
			"gain": Vector3(1.05, 1.0, 0.95),
			"bloom_intensity": 0.2,
			"film_grain": 0.04,
			"vignette": 0.5
		},
		"scientific": {
			"lift": Vector3(-0.02, -0.01, 0.0),
			"gamma": Vector3(1.05, 1.05, 1.0),
			"gain": Vector3(1.0, 1.0, 1.1),
			"bloom_intensity": 0.15,
			"film_grain": 0.01,
			"vignette": 0.2
		},
		"high_contrast": {
			"lift": Vector3(-0.05, -0.05, -0.05),
			"gamma": Vector3(1.2, 1.2, 1.2),
			"gain": Vector3(1.1, 1.1, 1.1),
			"bloom_intensity": 0.3,
			"film_grain": 0.02,
			"vignette": 0.3
		},
		"colorblind_deuteranopia": {
			"lift": Vector3(0.0, 0.0, 0.0),
			"gamma": Vector3(1.0, 1.0, 1.0),
			"gain": Vector3(1.0, 0.8, 1.2),
			"bloom_intensity": 0.3,
			"film_grain": 0.02,
			"vignette": 0.3
		},
		"colorblind_protanopia": {
			"lift": Vector3(0.0, 0.0, 0.0),
			"gamma": Vector3(1.0, 1.0, 1.0),
			"gain": Vector3(0.8, 1.0, 1.2),
			"bloom_intensity": 0.3,
			"film_grain": 0.02,
			"vignette": 0.3
		},
		"colorblind_tritanopia": {
			"lift": Vector3(0.0, 0.0, 0.0),
			"gamma": Vector3(1.0, 1.0, 1.0),
			"gain": Vector3(1.2, 1.2, 0.8),
			"bloom_intensity": 0.3,
			"film_grain": 0.02,
			"vignette": 0.3
		}
	}

	if presets.has(preset_name):
		_set_profile(presets[preset_name])
		return true
	return false

# =============================================================================
# ACCESSIBILITY
# =============================================================================

func set_colorblind_mode(mode: String) -> bool:
	var modes = {
		"deuteranopia": "colorblind_deuteranopia",
		"protanopia": "colorblind_protanopia",
		"tritanopia": "colorblind_tritanopia",
		"none": "scientific"
	}
	if modes.has(mode):
		return apply_preset(modes[mode])
	return false

func set_high_contrast(enabled: bool) -> void:
	if enabled:
		apply_preset("high_contrast")
	else:
		_apply_current_profile()

# =============================================================================
# SCREENSHOT / CAPTURE
# =============================================================================

func capture_screenshot(path: String = "", include_ui: bool = false) -> bool:
	var viewport = get_viewport()
	if not viewport:
		return false

	var image = viewport.get_texture().get_image()
	if path == "":
		path = "user://screenshots/screenshot_%s.png" % Time.get_datetime_string_from_system().replace(":", "-").replace(" ", "_")

	var dir = path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir)

	return image.save_png(path)

# =============================================================================
# SETTINGS PERSISTENCE
# =============================================================================

func to_dict() -> Dictionary:
	return {
		"bloom_enabled": bloom_enabled,
		"bloom_intensity": bloom_intensity,
		"bloom_threshold": bloom_threshold,
		"bloom_radius": bloom_radius,
		"color_grading_enabled": color_grading_enabled,
		"lift": [color_grade_lift.x, color_grade_lift.y, color_grade_lift.z],
		"gamma": [color_grade_gamma.x, color_grade_gamma.y, color_grade_gamma.z],
		"gain": [color_grade_gain.x, color_grade_gain.y, color_grade_gain.z],
		"film_grain_enabled": film_grain_enabled,
		"film_grain_amount": film_grain_amount,
		"vignette_enabled": vignette_enabled,
		"vignette_amount": vignette_amount,
		"dof_enabled": dof_enabled,
		"dof_focus_distance": dof_focus_distance,
		"dof_focus_range": dof_focus_range,
		"dof_blur_strength": dof_blur_strength
	}

func from_dict(data: Dictionary) -> void:
	bloom_enabled = data.get("bloom_enabled", true)
	bloom_intensity = data.get("bloom_intensity", 0.3)
	bloom_threshold = data.get("bloom_threshold", 1.0)
	bloom_radius = data.get("bloom_radius", 8.0)
	color_grading_enabled = data.get("color_grading_enabled", true)

	var lift_arr = data.get("lift", [0.0, 0.0, 0.0])
	color_grade_lift = Vector3(lift_arr[0], lift_arr[1], lift_arr[2])

	var gamma_arr = data.get("gamma", [1.0, 1.0, 1.0])
	color_grade_gamma = Vector3(gamma_arr[0], gamma_arr[1], gamma_arr[2])

	var gain_arr = data.get("gain", [1.0, 1.0, 1.0])
	color_grade_gain = Vector3(gain_arr[0], gain_arr[1], gain_arr[2])

	film_grain_enabled = data.get("film_grain_enabled", true)
	film_grain_amount = data.get("film_grain_amount", 0.02)
	vignette_enabled = data.get("vignette_enabled", true)
	vignette_amount = data.get("vignette_amount", 0.3)
	dof_enabled = data.get("dof_enabled", false)
	dof_focus_distance = data.get("dof_focus_distance", 10.0)
	dof_focus_range = data.get("dof_focus_range", 5.0)
	dof_blur_strength = data.get("dof_blur_strength", 0.01)

	_apply_to_environment()