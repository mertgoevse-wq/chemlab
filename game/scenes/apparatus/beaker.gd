# Beaker (400 mL) - Interactive Laboratory Glassware (Godot 4)
# Cylindrical borosilicate glass beaker with spout and graduation marks (100, 200, 300, 400 mL).
#
# Features:
# 1. 400 mL calibrated capacity with cylindrical body and molded pour spout
# 2. Visual graduation ring markings at 100 mL, 200 mL, 300 mL, and 400 mL
# 3. Physics-based pouring with 35° tilt threshold detection and PourRay recipient transfer
# 4. Dynamic liquid volume shader integration (Beer-Lambert, turbidity, meniscus sloshing)
# 5. Rigorous chemical stoichiometric tracking and thermal equilibrium integration
# 6. Full interoperability with PlayerController, InputManager, AnalyticalBalance, and TitrationBuret

extends RigidBody3D
class_name Beaker

# =============================================================================
# SIGNALS
# =============================================================================
signal volume_changed(current_volume_ml: float, capacity_ml: float)
signal contents_changed(contents: Dictionary)
signal temperature_changed(temperature_c: float)
signal liquid_poured(amount_ml: float, recipient: Node)
signal liquid_received(data: Dictionary)
signal reaction_occurred(reaction_name: String)

# =============================================================================
# EXPORTED PROPERTIES
# =============================================================================
@export_group("Apparatus Identity")
@export var vessel_name: String = "400 mL Beaker"
@export var capacity_ml: float = 400.0
@export var current_volume_ml: float = 0.0
@export var temperature_c: float = 21.0
@export var empty_mass_g: float = 135.0
@export var is_sealed: bool = false

@export_group("Liquid Visual State")
@export var color_rgba: Color = Color(0.9, 0.95, 1.0, 0.2)
@export var turbidity: float = 0.0
@export var ph: float = 7.0

@export_group("Pour Dynamics")
@export var pour_flow_rate_ml_per_sec: float = 35.0
@export var pour_angle_threshold_deg: float = 35.0
@export var pour_ray_length: float = 0.45

# Contents dictionary: species_id -> {"name": String, "volume_ml": float, "moles": float, "color": Color}
@export var contents: Dictionary = {}

# =============================================================================
# NODE REFERENCES
# =============================================================================
@onready var liquid_volume: MeshInstance3D = get_node_or_null("LiquidVolume")
@onready var pour_mouth: Marker3D = get_node_or_null("PourMouth")
@onready var pour_ray: RayCast3D = get_node_or_null("PourMouth/PourRay")
@onready var recipient_area: Area3D = get_node_or_null("RecipientArea")
@onready var pour_particles: CPUParticles3D = get_node_or_null("PourMouth/PourStream")
@onready var audio_pour: AudioStreamPlayer3D = get_node_or_null("AudioPour")

# =============================================================================
# RUNTIME STATE
# =============================================================================
var is_pouring: bool = false
var is_swirling: bool = false
var current_swirl_rpm: float = 0.0
var has_phenolphthalein: bool = false

# =============================================================================
# LIFECYCLE
# =============================================================================
func _ready() -> void:
	add_to_group("interactive_apparatus")
	add_to_group("glassware")
	add_to_group("apparatus")
	add_to_group("interactable")
	set_meta("is_apparatus", true)

	if pour_ray:
		pour_ray.enabled = true
		pour_ray.collide_with_areas = true
		pour_ray.collide_with_bodies = true

	if recipient_area:
		recipient_area.add_to_group("recipient_vessel")
		recipient_area.add_to_group("liquid_receiver")
		recipient_area.set_meta("vessel_owner", self)

	# Register with SimulationBridge autoload if active
	if Engine.has_singleton("SimulationBridge") or has_node("/root/SimulationBridge"):
		var bridge = get_node_or_null("/root/SimulationBridge")
		if bridge and bridge.has_method("register_vessel"):
			bridge.register_vessel(name, capacity_ml)

	_recalculate_physical_state()


func _physics_process(delta: float) -> void:
	_check_pour_physics(delta)


# =============================================================================
# POUR DYNAMICS & PHYSICS TRIGGER (> 35° TILT)
# =============================================================================
func _check_pour_physics(delta: float) -> void:
	# Measure 3D spatial tilt angle relative to world Vector3.UP
	var tilt_rad: float = global_transform.basis.y.angle_to(Vector3.UP)
	var tilt_deg: float = rad_to_deg(tilt_rad)

	# Pouring condition: tilted past 35° threshold, liquid present, not sealed
	if tilt_deg > pour_angle_threshold_deg and current_volume_ml > 0.001 and not is_sealed:
		is_pouring = true
		var pour_factor: float = clampf((tilt_deg - pour_angle_threshold_deg) / 45.0, 0.15, 1.0)
		var delta_pour_ml: float = pour_flow_rate_ml_per_sec * pour_factor * delta

		var recipient: Node = null

		if pour_mouth and pour_ray:
			var mouth_pos = pour_mouth.global_position
			pour_ray.global_position = mouth_pos
			# Cast ray directly downward in world gravity direction
			pour_ray.target_position = pour_ray.to_local(mouth_pos + Vector3.DOWN * pour_ray_length)
			pour_ray.force_raycast_update()

			if pour_ray.is_colliding():
				var collider = pour_ray.get_collider()
				recipient = _resolve_recipient_vessel(collider)

		var transferred = pour_out(delta_pour_ml)
		if not transferred.is_empty():
			if recipient != null and recipient.has_method("receive_liquid"):
				recipient.receive_liquid(transferred)
				liquid_poured.emit(transferred["volume_ml"], recipient)
			else:
				# Poured onto bench or floor (spill)
				liquid_poured.emit(transferred["volume_ml"], null)

		_update_pour_stream_effects(true)
	else:
		if is_pouring:
			is_pouring = false
			_update_pour_stream_effects(false)


func _resolve_recipient_vessel(node: Node) -> Node:
	var curr: Node = node
	while curr != null:
		if curr != self:
			if curr.has_meta("vessel_owner"):
				return curr.get_meta("vessel_owner") as Node
			if curr.has_method("receive_liquid") or curr.has_method("add_reagent"):
				return curr
		curr = curr.get_parent()
	return null


func _update_pour_stream_effects(active: bool) -> void:
	if pour_particles:
		pour_particles.emitting = active
		if active:
			pour_particles.color = color_rgba

	if audio_pour:
		if active and not audio_pour.playing:
			audio_pour.play()
		elif not active and audio_pour.playing:
			audio_pour.stop()


# =============================================================================
# SCIENTIFIC STATE API & REAGENT DISPENSING
# =============================================================================

# Adds reagent with species ID, volume in mL, and moles
func add_reagent(id: String, ml: float, moles: float = 0.0, reagent_color: Color = Color.WHITE) -> bool:
	if current_volume_ml >= capacity_ml:
		return false

	var available_ml: float = capacity_ml - current_volume_ml
	var actual_ml: float = minf(ml, available_ml)
	if actual_ml <= 0.0:
		return false

	var actual_moles: float = moles
	if actual_moles <= 0.0:
		actual_moles = _estimate_moles(id, actual_ml)

	if id == "phenolphthalein" or id == "phenolphthalein_indicator":
		has_phenolphthalein = true

	var final_color = reagent_color
	if reagent_color == Color.WHITE:
		final_color = _lookup_species_color(id)

	if contents.has(id):
		contents[id]["volume_ml"] = float(contents[id]["volume_ml"]) + actual_ml
		contents[id]["moles"] = float(contents[id]["moles"]) + actual_moles
	else:
		contents[id] = {
			"name": id.capitalize(),
			"volume_ml": actual_ml,
			"moles": actual_moles,
			"color": final_color
		}

	current_volume_ml += actual_ml
	_recalculate_physical_state()
	volume_changed.emit(current_volume_ml, capacity_ml)
	contents_changed.emit(contents)
	return true


# Pours out delta_ml and returns Dictionary of transferred liquid
func pour_out(delta_ml: float) -> Dictionary:
	if current_volume_ml <= 0.0001:
		return {}

	var actual_pour: float = minf(delta_ml, current_volume_ml)
	var fraction: float = actual_pour / current_volume_ml

	var transferred: Dictionary = {
		"source_vessel": vessel_name,
		"volume_ml": actual_pour,
		"temperature_c": temperature_c,
		"color": color_rgba,
		"turbidity": turbidity,
		"ph": ph,
		"species": {}
	}

	for s_id in contents.keys():
		var s_data: Dictionary = contents[s_id]
		var s_moles: float = float(s_data["moles"]) * fraction
		var s_vol: float = float(s_data["volume_ml"]) * fraction
		transferred["species"][s_id] = {
			"moles": s_moles,
			"volume_ml": s_vol,
			"color": s_data.get("color", color_rgba)
		}
		s_data["moles"] = float(s_data["moles"]) - s_moles
		s_data["volume_ml"] = float(s_data["volume_ml"]) - s_vol

	current_volume_ml -= actual_pour
	if current_volume_ml <= 0.001:
		current_volume_ml = 0.0
		contents.clear()
		ph = 7.0
		turbidity = 0.0
		has_phenolphthalein = false

	_recalculate_physical_state()
	volume_changed.emit(current_volume_ml, capacity_ml)
	contents_changed.emit(contents)
	return transferred


# Flexible receiver for liquid transfers
func receive_liquid(arg1, arg2 = null, arg3 = null, arg4 = null, arg5 = null, arg6 = null) -> float:
	var incoming_vol: float = 0.0
	var incoming_temp: float = 21.0

	if arg1 is Dictionary:
		var data: Dictionary = arg1
		incoming_vol = float(data.get("volume_ml", 0.0))
		incoming_temp = float(data.get("temperature_c", 21.0))
		var incoming_species: Dictionary = data.get("species", {})

		if incoming_species.is_empty():
			var s_id: String = String(data.get("id", "water"))
			var s_moles: float = float(data.get("moles", 0.0))
			var s_color: Color = data.get("color", Color(0.9, 0.95, 1.0, 0.2))
			add_reagent(s_id, incoming_vol, s_moles, s_color)
		else:
			for s_id in incoming_species.keys():
				var sp: Dictionary = incoming_species[s_id]
				var s_vol: float = float(sp.get("volume_ml", 0.0))
				var s_moles: float = float(sp.get("moles", 0.0))
				var s_col: Color = sp.get("color", Color.WHITE)
				add_reagent(s_id, s_vol, s_moles, s_col)

	elif arg1 is String:
		var s_id: String = String(arg1)
		incoming_vol = float(arg2) if arg2 != null else 1.0
		var s_moles: float = float(arg3) if arg3 != null else 0.0
		var s_color = arg5 if (arg5 is Color) else Color.WHITE
		add_reagent(s_id, incoming_vol, s_moles, s_color)

	# Thermal equilibrium mixing: (m1*T1 + m2*T2)/(m1+m2)
	if current_volume_ml > 0.0 and incoming_vol > 0.0:
		var prev_vol = current_volume_ml - incoming_vol
		temperature_c = (prev_vol * temperature_c + incoming_vol * incoming_temp) / current_volume_ml
		temperature_changed.emit(temperature_c)

	liquid_received.emit({"volume_ml": incoming_vol})
	return incoming_vol


# Sets visual liquid shader parameters
func set_liquid_state(color: Color, fill_ratio: float, turb: float) -> void:
	color_rgba = color
	turbidity = turb

	if liquid_volume:
		if fill_ratio <= 0.001 or current_volume_ml <= 0.001:
			liquid_volume.visible = false
		else:
			liquid_volume.visible = true
			var mat = liquid_volume.get_surface_override_material(0)
			if mat == null:
				mat = liquid_volume.material_override
			if mat is ShaderMaterial:
				var sm = mat as ShaderMaterial
				sm.set_shader_parameter("fill_amount", clampf(fill_ratio, 0.0, 1.0))
				sm.set_shader_parameter("liquid_color", color)
				sm.set_shader_parameter("turbidity", turb)


# Returns interaction info dictionary for PlayerController HUD
func get_interaction_info() -> Dictionary:
	var prompt := "[E] Pick Up"
	if current_volume_ml > 0.0:
		prompt = "[E] Pick Up | [Left Click] Pour | [Right Click] Swirl"

	return {
		"can_pickup": true,
		"can_interact": true,
		"can_pour": can_pour(),
		"can_swirl": can_swirl(),
		"vessel_name": vessel_name,
		"current_volume_ml": current_volume_ml,
		"capacity_ml": capacity_ml,
		"temperature_c": temperature_c,
		"ph": ph,
		"prompt_text": prompt
	}


# Mass query for Analytical Balance
func get_total_mass() -> float:
	return empty_mass_g + current_volume_ml * 1.0


# Interoperability helpers with PlayerController & InputManager
func can_pour() -> bool:
	return current_volume_ml > 0.001 and not is_sealed


func on_pour(pour_rate: float, _is_positive: bool = true) -> void:
	if pour_rate > (pour_angle_threshold_deg / 85.0) and current_volume_ml > 0.001:
		_update_pour_stream_effects(true)
	else:
		if not is_pouring:
			_update_pour_stream_effects(false)


func can_swirl() -> bool:
	return current_volume_ml > 0.001


func on_swirl_start(rpm: float) -> void:
	is_swirling = true
	current_swirl_rpm = rpm
	if liquid_volume:
		var mat = liquid_volume.material_override
		if mat is ShaderMaterial:
			mat.set_shader_parameter("wave_speed", clampf(rpm / 15.0, 3.0, 12.0))
			mat.set_shader_parameter("wave_amplitude", 0.012)


func on_swirl_stop() -> void:
	is_swirling = false
	current_swirl_rpm = 0.0
	if liquid_volume:
		var mat = liquid_volume.material_override
		if mat is ShaderMaterial:
			mat.set_shader_parameter("wave_speed", 3.5)
			mat.set_shader_parameter("wave_amplitude", 0.008)


# =============================================================================
# INTERNAL PHYSICAL & CHEMICAL CALCULATIONS
# =============================================================================
func _recalculate_physical_state() -> void:
	if current_volume_ml <= 0.0001:
		ph = 7.0
		color_rgba = Color(0.9, 0.95, 1.0, 0.2)
		turbidity = 0.0
		set_liquid_state(color_rgba, 0.0, 0.0)
		return

	# 1. Acid-Base Stoichiometry (HCl + NaOH -> NaCl + H2O)
	_step_neutralization_reaction()

	# 2. pH Calculation
	_update_solution_ph()

	# 3. Color Blending
	_update_solution_color()

	# 4. Update 3D Liquid Volume Visual
	var fill_ratio = current_volume_ml / capacity_ml
	set_liquid_state(color_rgba, fill_ratio, turbidity)


func _step_neutralization_reaction() -> void:
	var hcl_moles = contents["hcl"]["moles"] if contents.has("hcl") else 0.0
	var naoh_moles = contents["naoh"]["moles"] if contents.has("naoh") else 0.0

	if hcl_moles > 0.000001 and naoh_moles > 0.000001:
		var limit = minf(hcl_moles, naoh_moles)
		contents["hcl"]["moles"] = float(contents["hcl"]["moles"]) - limit
		contents["naoh"]["moles"] = float(contents["naoh"]["moles"]) - limit

		if not contents.has("nacl"):
			contents["nacl"] = {
				"name": "Sodium Chloride",
				"volume_ml": 0.0,
				"moles": 0.0,
				"color": Color(0.95, 0.98, 1.0, 0.12)
			}
		contents["nacl"]["moles"] = float(contents["nacl"]["moles"]) + limit

		# Exothermic reaction enthalpy: Delta H = -57.1 kJ/mol
		var q_joules: float = 57100.0 * limit
		var total_mass_g: float = current_volume_ml * 1.0
		if total_mass_g > 0.1:
			var delta_t = q_joules / (total_mass_g * 4.184)
			temperature_c += delta_t
			temperature_changed.emit(temperature_c)

		reaction_occurred.emit("Neutralization")


func _update_solution_ph() -> void:
	var vol_l = current_volume_ml / 1000.0
	var hcl_moles = contents["hcl"]["moles"] if contents.has("hcl") else 0.0
	var naoh_moles = contents["naoh"]["moles"] if contents.has("naoh") else 0.0

	if hcl_moles > naoh_moles:
		var excess_h = (hcl_moles - naoh_moles) / vol_l
		ph = clampf(-log(excess_h) / log(10.0), 0.0, 7.0)
	elif naoh_moles > hcl_moles:
		var excess_oh = (naoh_moles - hcl_moles) / vol_l
		var poh = -log(excess_oh) / log(10.0)
		ph = clampf(14.0 - poh, 7.0, 14.0)
	else:
		ph = 7.0


func _update_solution_color() -> void:
	if has_phenolphthalein and ph >= 8.2:
		var pink_factor = clampf((ph - 8.2) / 1.5, 0.0, 1.0)
		var base_pink = Color(0.95, 0.10, 0.55, 0.85)
		color_rgba = Color(0.92, 0.96, 1.0, 0.2).lerp(base_pink, pink_factor)
		return

	var total_r: float = 0.0
	var total_g: float = 0.0
	var total_b: float = 0.0
	var total_a: float = 0.0

	for s_id in contents.keys():
		var sp: Dictionary = contents[s_id]
		var weight: float = float(sp["volume_ml"]) / maxf(current_volume_ml, 0.001)
		var col: Color = sp.get("color", Color(0.9, 0.95, 1.0, 0.2))
		total_r += col.r * weight
		total_g += col.g * weight
		total_b += col.b * weight
		total_a += col.a * weight

	color_rgba = Color(total_r, total_g, total_b, clampf(total_a, 0.15, 0.95))


func _lookup_species_color(id: String) -> Color:
	match id.to_lower():
		"hcl", "hydrochloric_acid":
			return Color(0.95, 0.98, 1.0, 0.15)
		"naoh", "sodium_hydroxide":
			return Color(0.95, 0.98, 1.0, 0.15)
		"coppersulfate", "cuso4":
			return Color(0.05, 0.65, 0.95, 0.85)
		"permanganate", "kmno4":
			return Color(0.55, 0.05, 0.65, 0.90)
		"nickel", "nicl2":
			return Color(0.15, 0.92, 0.25, 0.85)
		"phenolphthalein":
			return Color(0.95, 0.98, 1.0, 0.10)
		_:
			return Color(0.90, 0.95, 1.0, 0.20)


func _estimate_moles(id: String, ml: float) -> float:
	match id.to_lower():
		"water", "h2o", "distilled_water":
			return (ml * 1.0) / 18.015
		"hcl", "naoh":
			return (ml / 1000.0) * 0.10
		_:
			return (ml / 1000.0) * 1.00
