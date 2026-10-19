class_name StarterMain
extends StarterSession
## 保留的 3D 示例，空间单位为米。

const Presentation = preload("res://scripts/starter_presentation.gd")

@onready var player: StarterPlayer = $World/Player
@onready var target: MeshInstance3D = $World/Target
@onready var world: Node3D = $World


func route() -> String:
	return "3d"


func _connect_world() -> void:
	_presentation = Presentation.new(world, target, status, start_button, pause_button, restart_button)
	player.move_speed = float(_values.move_speed)
	world.process_mode = Node.PROCESS_MODE_PAUSABLE


func _move(direction: Vector2) -> void:
	player.direction = direction


func _reset_player() -> void:
	player.reset()


func _interaction_distance() -> float:
	return player.position.distance_to(target.position)


func _position_components() -> Array:
	return [player.position.x, player.position.y, player.position.z]


func capture_points() -> Dictionary:
	var camera: Camera3D = $World/Camera
	return {"actor": camera.unproject_position(player.global_position),
		"target": camera.unproject_position(target.global_position)}
