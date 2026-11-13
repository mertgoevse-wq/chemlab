# Athanor Ascension — Performance Profile
# Applies a conservative render profile on startup so the game holds 60 FPS on
# the target Dell Latitude 5530 (i5-1240U, Intel Iris Xe, 16 GB RAM).
# The profile is chosen from the adapter name, not from a hard-coded assumption.
extends Node

const TARGET_FPS: int = 60

var adapter_name: String = ""
var profile: String = "balanced"


func _ready() -> void:
	adapter_name = str(RenderingServer.get_video_adapter_name())
	profile = "iris_xe" if "intel" in adapter_name.to_lower() else "balanced"
	Engine.max_fps = TARGET_FPS
	Engine.physics_ticks_per_second = 60
	_apply_viewport_settings()
	print("[PerformanceProfile] %s · %s · cap %d FPS" % [profile, adapter_name, TARGET_FPS])


func _apply_viewport_settings() -> void:
	var tree := get_tree()
	if tree == null or tree.root == null:
		return
	var viewport := tree.root
	var rid := viewport.get_viewport_rid()

	if profile == "iris_xe":
		RenderingServer.viewport_set_msaa_3d(rid, RenderingServer.VIEWPORT_MSAA_DISABLED)
		RenderingServer.viewport_set_screen_space_aa(rid, RenderingServer.VIEWPORT_SCREEN_SPACE_AA_DISABLED)
		RenderingServer.directional_shadow_atlas_set_size(2048, true)
	else:
		RenderingServer.viewport_set_msaa_3d(rid, RenderingServer.VIEWPORT_MSAA_2X)
		RenderingServer.directional_shadow_atlas_set_size(4096, true)

	# 0.5 disables mesh LOD bias inflation; 1.0 keeps full quality.
	viewport.mesh_lod_threshold = 1.0 if profile == "iris_xe" else 0.5
