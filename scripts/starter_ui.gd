class_name StarterUI
extends RefCounted
## 只读值视图到通用 UI；世界可见性由各路线表现适配。

var _status: Label
var _start_button: Button
var _pause_button: Button
var _restart_button: Button
var _title: String


func _init(status: Label, start_button: Button, pause_button: Button,
		restart_button: Button, title: String) -> void:
	_status = status
	_start_button = start_button
	_pause_button = pause_button
	_restart_button = restart_button
	_title = title


func present(view: Dictionary) -> void:
	_start_button.visible = not view.running
	_pause_button.visible = view.running
	_restart_button.visible = view.running
	_pause_button.text = "继续（Esc）" if view.paused else "暂停（Esc）"
	_status.text = _title + "\n点击进入或按 Enter"
	if view.running:
		_status.text = "方向键 / WASD 移动，靠近金色目标后按 Enter\nR 重开；Esc 暂停 / 继续"
	if view.activated:
		_status.text = "交互成功：目标已激活\nR 重开；Esc 暂停 / 继续"
	if view.paused:
		_status.text = "已暂停：物理和规则时间均冻结\nEsc 继续；R 重开"
