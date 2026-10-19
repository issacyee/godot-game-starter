class_name StarterPresentation
extends StarterUI
## 3D 表现只借用显示节点，不持有规则、玩家或协调器。

var _world: Node3D
var _target: MeshInstance3D


func _init(world: Node3D, target: MeshInstance3D, status: Label,
		start_button: Button, pause_button: Button, restart_button: Button) -> void:
	super(status, start_button, pause_button, restart_button, "Godot 3D 起步模板")
	_world = world
	_target = target


func present(view: Dictionary) -> void:
	_world.visible = view.running
	_target.visible = not view.activated
	super.present(view)
