class_name StarterPresentation
extends RefCounted
## 只将状态投影到借用的显示节点；不持有规则、玩家或协调器，不推进玩法。

var _world: Node3D
var _target: MeshInstance3D
var _status: Label
var _start_button: Button
var _pause_button: Button
var _restart_button: Button


func _init(world: Node3D, target: MeshInstance3D, status: Label,
		start_button: Button, pause_button: Button, restart_button: Button) -> void:
	_world = world
	_target = target
	_status = status
	_start_button = start_button
	_pause_button = pause_button
	_restart_button = restart_button


func present(view: Dictionary) -> void:
	_world.visible = view.running
	_target.visible = not view.activated
	_start_button.visible = not view.running
	_pause_button.visible = view.running
	_restart_button.visible = view.running
	_pause_button.text = "继续（Esc）" if view.paused else "暂停（Esc）"
	_status.text = "Godot 3D 起步模板\n点击进入或按 Enter"
	if view.running:
		_status.text = "方向键 / WASD 移动，靠近金色目标后按 Enter\nR 重开；Esc 暂停 / 继续"
	if view.activated:
		_status.text = "交互成功：目标已激活\nR 重开；Esc 暂停 / 继续"
	if view.paused:
		_status.text = "已暂停：物理和规则时间均冻结\nEsc 继续；R 重开"
