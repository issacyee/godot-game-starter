class_name StarterPresentation2D
extends StarterUI
## 2D 表现只借用显示节点，不持有规则、玩家或协调器。

var _world: Node2D
var _target: Node2D


func _init(world: Node2D, target: Node2D, status: Label,
		start_button: Button, pause_button: Button, restart_button: Button) -> void:
	super(status, start_button, pause_button, restart_button, "Godot 2D 起步模板")
	_world = world
	_target = target


func present(view: Dictionary) -> void:
	_world.visible = view.running
	_target.visible = not view.activated
	super.present(view)
