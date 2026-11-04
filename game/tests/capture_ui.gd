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
	for _i in range(6):
		await process_frame
	RenderingServer.force_draw()
	await process_frame
	var image := root.get_viewport().get_texture().get_image()
	var error := image.save_png(output)
	print("CAPTURE %s -> %s (err %d, %dx%d)" % [scene_path, output, error, image.get_width(), image.get_height()])
	quit(0 if error == OK else 4)
