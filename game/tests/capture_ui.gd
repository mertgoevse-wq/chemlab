# Athanor Ascension — UI capture helper (development only)
# Usage: tools/bin/godot --path game --script res://tests/capture_ui.gd -- <scene> <out.png>
extends SceneTree


func _init() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 2:
		printerr("usage: -- <scene path> <output png>")
		quit(2)
		return
	var scene_path := str(args[0])
	var output := str(args[1])
	var packed := load(scene_path)
	if packed == null:
		printerr("cannot load %s" % scene_path)
		quit(3)
		return
	var node = packed.instantiate()
	root.add_child(node)
	if args.size() > 2:
		var mode := str(args[2])
		if mode.begins_with("stage") and node.has_method("_set_stage"):
			node._set_stage(int(mode.substr(5)))
		elif mode == "briefing":
			# Re-fire quest_started so the transmission card animates in.
			var qm = root.get_node_or_null("QuestManager")
			if qm and qm.has_method("start_quest"):
				qm.start_quest("quest_01_orientation")
			await create_timer(0.9).timeout
		elif mode == "submitted" and node.has_method("submit_batch"):
			node._ppe = {"goggles": true, "gloves": true, "coat": true}
			node._hood = true
			node._reflux_done = true
			node.submit_batch()
	for _i in range(6):
		await process_frame
	RenderingServer.force_draw()
	await process_frame
	var image := root.get_viewport().get_texture().get_image()
	# Relative paths are repo-relative (docs/screenshots/...), not game/-relative.
	var output_path := output
	if not output.begins_with("res://") and not output.is_absolute_path():
		output_path = ProjectSettings.globalize_path("res://").path_join("..").path_join(output).simplify_path()
	DirAccess.make_dir_recursive_absolute(output_path.get_base_dir())
	var error := image.save_png(output_path)
	print("CAPTURE %s -> %s (err %d, %dx%d)" % [scene_path, output_path, error, image.get_width(), image.get_height()])
	quit(0 if error == OK else 4)
