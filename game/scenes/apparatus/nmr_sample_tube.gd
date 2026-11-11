# Athanor Ascension - NMR Sample Tube
# Standard 5mm borosilicate glass sample tube for Nuclear Magnetic Resonance spectrometry.

class_name NMRSampleTube
extends RigidBody3D

@export var compound_name: String = "Ethanol"
@export var sample_type: String = "nmr_sample"
@export var concentration_mM: float = 50.0
@export var solvent: String = "CDCl3"
@export var volume_ml: float = 0.6
@export var liquid_color: Color = Color(0.2, 0.5, 0.8, 0.8)

@onready var tube_mesh: MeshInstance3D = get_node_or_null("TubeMesh")
@onready var liquid_mesh: MeshInstance3D = get_node_or_null("LiquidMesh")

func _ready() -> void:
	# Synchronize metadata for NMR spectrometer detection
	set_meta("sample_type", sample_type)
	set_meta("compound_name", compound_name)
	set_meta("concentration_mM", concentration_mM)
	set_meta("solvent", solvent)
	set_meta("volume_ml", volume_ml)
	_update_liquid_visuals()

func set_sample(p_compound: String, p_concentration: float, p_solvent: String, p_volume: float = 0.6, p_color: Color = Color(0.2, 0.5, 0.8, 0.8)) -> void:
	compound_name = p_compound
	concentration_mM = p_concentration
	solvent = p_solvent
	volume_ml = p_volume
	liquid_color = p_color
	set_meta("compound_name", compound_name)
	set_meta("concentration_mM", concentration_mM)
	set_meta("solvent", solvent)
	set_meta("volume_ml", volume_ml)
	_update_liquid_visuals()

func _update_liquid_visuals() -> void:
	if liquid_mesh and liquid_mesh.material_override:
		var mat = liquid_mesh.material_override as StandardMaterial3D
		if mat:
			mat.albedo_color = liquid_color
