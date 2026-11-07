extends SceneTree

func _init() -> void:
	_run.call_deferred()

func _run() -> void:
	var packed := load("res://scenes/laboratories/analytical_lab.tscn")
	var node = packed.instantiate()
	root.add_child(node)
	for _i in range(6):
		await process_frame
	# Add an explicit cinematic camera above the bench looking down.
	var cam := Camera3D.new()
	cam.fov = 62.0
	node.add_child(cam)
	cam.global_position = Vector3(3.8, 2.55, 3.6)
	cam.look_at(Vector3(-0.4, 0.9, -0.2), Vector3.UP)
	cam.current = true
	print("CAMPOS ", cam.global_position, " meshes=", _count_meshes(node))
	await process_frame
	RenderingServer.force_draw()
	await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(ProjectSettings.globalize_path("res://").path_join("..").path_join("docs/screenshots/audit_lab_overview.png"))
	quit(0)

func _count_meshes(n: Node) -> int:
	var c := 0
	if n is MeshInstance3D:
		c += 1
	for ch in n.get_children():
		c += _count_meshes(ch)
	return c
