# Athanor Ascension — Fate Resonance & Tri-Protagonist Narrative Engine (Godot 4)
# Manages the 3 parallel protagonist campaigns (Thorne, Finch, Voss),
# their narrative convergence in Act 4 (The Nexus Catalyst),
# cross-character influence, and dynamic destiny swapping in Acts 5-10.

class_name FateResonanceManager
extends RefCounted

# =============================================================================
# CONSTANTS & PROTAGONIST ENUMS
# =============================================================================

const PROTAGONIST_THORNE := "thorne"   # Academic Prodigy (Analytical / Atrium)
const PROTAGONIST_FINCH  := "finch"    # Basement Alchemist (Synthesis / Underground)
const PROTAGONIST_VOSS   := "voss"     # Ex-Pharma Whistleblower (Pilot Plant / Forensic)

const PROTAGONISTS := [PROTAGONIST_THORNE, PROTAGONIST_FINCH, PROTAGONIST_VOSS]

# =============================================================================
# STATE VARIABLES
# =============================================================================

var active_protagonist: String = PROTAGONIST_THORNE
var nexus_convergence_achieved: bool = false
var destiny_swap_active: bool = false

# Current assigned roles/fates (can be swapped in late game)
# Default: Thorne -> Academic, Finch -> Alchemist, Voss -> Whistleblower
var protagonist_fates: Dictionary = {
	PROTAGONIST_THORNE: "academic_chair",
	PROTAGONIST_FINCH:  "alchemical_underground",
	PROTAGONIST_VOSS:   "regulatory_whistleblower"
}

# Cross-protagonist resonance metrics (0.0 to 100.0)
# Tracks how decisions made by one character influence the worlds of the others
var resonance_matrix: Dictionary = {
	"thorne_to_finch": 0.0,   # Academic data leaked to underground
	"finch_to_voss":   0.0,   # Clandestine catalysts supplied to whistleblowers
	"voss_to_thorne":  0.0,   # Corporate audit files provided to academia
	"finch_to_thorne": 0.0,   # Aetherkin biomimicry shared with university
	"voss_to_finch":   0.0,   # Industrial equipment salvaged for basement lab
	"thorne_to_voss":  0.0    # Forensic certification validating whistleblower claims
}

# Shared narrative flags unlocked across all timelines
var shared_timeline_events: Array[String] = []

# Character profiles and starting metadata
const CHARACTER_PROFILES: Dictionary = {
	PROTAGONIST_THORNE: {
		"name": "Dr. Aris Thorne",
		"title": "Academic Fellow & Senior Theorist",
		"origin": "academic",
		"starting_lab": "analytical_lab",
		"starting_location": "Grand Atrium & Analytical Spectroscopy Wing",
		"primary_apparatus": "NMR_Spectrometer_400MHz",
		"signature_companion": "instrumented_rat",
		"core_philosophy": "Empirical rigor, mathematical thermodynamics, transparent science.",
		"motto": "The spectra never lie; only our interpretations falter."
	},
	PROTAGONIST_FINCH: {
		"name": "Vesper Finch",
		"title": "The Alchemical Underground Prodigy",
		"origin": "hobbyist",
		"starting_lab": "synthesis_lab",
		"starting_location": "Loading Dock & Sub-Level Organic Workshop",
		"primary_apparatus": "Heating_Mantle_Reflux_Rig",
		"signature_companion": "cinderling",
		"core_philosophy": "Chemical intuition, living reaction kinetics, radical access to medicine.",
		"motto": "Nature doesn't ask for peer-review before it reacts."
	},
	PROTAGONIST_VOSS: {
		"name": "Kaelen Voss",
		"title": "Ex-Pharma Toxicologist & Defector",
		"origin": "ex_pharma",
		"starting_lab": "pilot_plant_lab",
		"starting_location": "Wing Delta Industrial Pilot Plant & Forensic Bunker",
		"primary_apparatus": "Continuous_Flow_Reactor",
		"signature_companion": "wall_gecko",
		"core_philosophy": "Industrial scale-up safety, corporate accountability, forensic exposure.",
		"motto": "They called it acceptable loss; I call it evidence."
	}
}

# =============================================================================
# PUBLIC API - PROTAGONIST & TIMELINE MANAGEMENT
# =============================================================================

func set_active_protagonist(protagonist_id: String) -> bool:
	if protagonist_id not in PROTAGONISTS:
		push_warning("FateResonanceManager: Unknown protagonist '%s'" % protagonist_id)
		return false
	active_protagonist = protagonist_id
	return true


func get_active_protagonist() -> String:
	return active_protagonist


func get_character_profile(protagonist_id: String = "") -> Dictionary:
	var target = protagonist_id if protagonist_id != "" else active_protagonist
	return CHARACTER_PROFILES.get(target, {})


func record_resonance_action(source: String, target: String, amount: float, reason: String = "") -> void:
	"""Record a cross-character influence decision."""
	var key = "%s_to_%s" % [source, target]
	if resonance_matrix.has(key):
		resonance_matrix[key] = clamp(resonance_matrix[key] + amount, 0.0, 100.0)

	var event_id = "resonance_%s_%s_%d" % [source, target, int(Time.get_unix_time_from_system())]
	if reason != "" and reason not in shared_timeline_events:
		shared_timeline_events.append(reason)

	_check_convergence_thresholds()


func get_resonance(source: String, target: String) -> float:
	var key = "%s_to_%s" % [source, target]
	return float(resonance_matrix.get(key, 0.0))


func _check_convergence_thresholds() -> void:
	"""Check if cross-character resonance triggers Act 4 Nexus Convergence."""
	var total_resonance = 0.0
	for val in resonance_matrix.values():
		total_resonance += float(val)

	# Once cumulative resonance crosses 150 points or specific shared events occur
	if total_resonance >= 150.0 or "nexus_containment_breach" in shared_timeline_events:
		if not nexus_convergence_achieved:
			nexus_convergence_achieved = true


func trigger_nexus_convergence() -> void:
	nexus_convergence_achieved = true
	if "nexus_containment_breach" not in shared_timeline_events:
		shared_timeline_events.append("nexus_containment_breach")


func swap_destinies(char_a: String, char_b: String, swap_reason: String) -> bool:
	"""Swap the narrative destinies / futures of two protagonists based on player choices."""
	if char_a not in PROTAGONISTS or char_b not in PROTAGONISTS or char_a == char_b:
		return false

	var fate_a = protagonist_fates[char_a]
	var fate_b = protagonist_fates[char_b]

	protagonist_fates[char_a] = fate_b
	protagonist_fates[char_b] = fate_a
	destiny_swap_active = true

	shared_timeline_events.append("destiny_swap_%s_%s: %s" % [char_a, char_b, swap_reason])
	return true


func get_destiny(protagonist_id: String) -> String:
	return str(protagonist_fates.get(protagonist_id, "unknown"))


# =============================================================================
# SERIALIZATION / PERSISTENCE
# =============================================================================

func to_dict() -> Dictionary:
	return {
		"active_protagonist": active_protagonist,
		"nexus_convergence_achieved": nexus_convergence_achieved,
		"destiny_swap_active": destiny_swap_active,
		"protagonist_fates": protagonist_fates.duplicate(true),
		"resonance_matrix": resonance_matrix.duplicate(true),
		"shared_timeline_events": shared_timeline_events.duplicate()
	}


func from_dict(data: Dictionary) -> void:
	active_protagonist = data.get("active_protagonist", PROTAGONIST_THORNE)
	nexus_convergence_achieved = data.get("nexus_convergence_achieved", false)
	destiny_swap_active = data.get("destiny_swap_active", false)
	protagonist_fates = data.get("protagonist_fates", protagonist_fates).duplicate(true)
	resonance_matrix = data.get("resonance_matrix", resonance_matrix).duplicate(true)
	shared_timeline_events = data.get("shared_timeline_events", []).duplicate()
