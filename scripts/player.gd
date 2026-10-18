class_name StarterPlayer
extends CharacterBody3D

var move_speed: float = 4.0
var direction: Vector2 = Vector2.ZERO


func _physics_process(_delta: float) -> void:
	velocity = Vector3(direction.x, 0.0, direction.y) * move_speed
	move_and_slide()


func reset() -> void:
	position = Vector3(0.0, 0.5, 0.0)
	velocity = Vector3.ZERO
	direction = Vector2.ZERO
