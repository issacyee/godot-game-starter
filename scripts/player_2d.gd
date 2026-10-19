class_name StarterPlayer2D
extends CharacterBody2D

var move_speed: float = 200.0
var direction: Vector2 = Vector2.ZERO


func _physics_process(_delta: float) -> void:
	velocity = direction * move_speed
	move_and_slide()


func reset() -> void:
	position = Vector2.ZERO
	velocity = Vector2.ZERO
	direction = Vector2.ZERO
