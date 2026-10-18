class_name ProductProbe
extends RefCounted
## 仅 dev 且显式指定新工作产物目录时启用。只读状态；不提供状态注入。

var capture_requested: bool = false
var _scene: StarterMain
var _directory: String = ""
var _sequence: int = 0
var _captures: int = 0
var _seconds: float = 0.0
var _capturing: bool = false


func _init(scene: StarterMain) -> void:
	_scene = scene
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var index: int = args.find("--probe-directory")
	if index < 0:
		return
	if not OS.is_debug_build() or index + 1 >= args.size():
		return
	var path: String = args[index + 1].replace("\\", "/")
	if not path.is_absolute_path() or not path.contains("/artifacts/") or not DirAccess.dir_exists_absolute(path):
		push_error("PROBE_PATH_INVALID")
		return
	_directory = path


func advance(delta: float) -> void:
	if _directory.is_empty():
		return
	_seconds += delta
	if _seconds > 60.0 or _sequence >= 10000:
		_scene.get_tree().quit(3)
		return
	_sequence += 1
	var snapshot: Dictionary = _scene.diagnostic_snapshot()
	snapshot["sequence"] = _sequence
	snapshot["focused"] = DisplayServer.window_is_focused()
	snapshot["captures"] = _captures
	var file: FileAccess = FileAccess.open(_directory.path_join("state.tmp"), FileAccess.WRITE)
	if file == null:
		_scene.get_tree().quit(3)
		return
	file.store_string(JSON.stringify(snapshot))
	file.close()
	DirAccess.rename_absolute(_directory.path_join("state.tmp"), _directory.path_join("state.json"))
	if capture_requested and not _capturing and _captures < 8:
		capture_requested = false
		_capture()


func _capture() -> void:
	_capturing = true
	await RenderingServer.frame_post_draw
	var camera: Camera3D = _scene.get_node("World/Camera") as Camera3D
	var actor: Vector2 = camera.unproject_position(_scene.player.global_position)
	var target: Vector2 = camera.unproject_position(_scene.target.global_position)
	var image: Image = _scene.get_viewport().get_texture().get_image()
	_captures += 1
	var stem: String = _directory.path_join("frame-%d" % _captures)
	if image.save_png(stem + ".png") != OK:
		_scene.get_tree().quit(3)
	var record: Dictionary = _scene.diagnostic_snapshot()
	record["actor_pixel"] = [actor.x, actor.y]
	record["target_pixel"] = [target.x, target.y]
	record["sequence"] = _sequence
	var file: FileAccess = FileAccess.open(stem + ".json", FileAccess.WRITE)
	file.store_string(JSON.stringify(record))
	file.close()
	_capturing = false
