class_name StarterMain2D
extends StarterSession
## 默认俯视 2D 示例；同父 World 下测量距离，单位为像素。

const Presentation = preload("res://scripts/starter_presentation_2d.gd")

@onready var player: StarterPlayer2D = $World/Player
@onready var target: Node2D = $World/Target
@onready var world: Node2D = $World


func route() -> String:
	return "2d"


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
	return [player.position.x, player.position.y]


func capture_points() -> Dictionary:
	return {"actor": player.get_global_transform_with_canvas().origin,
		"target": target.get_global_transform_with_canvas().origin}
