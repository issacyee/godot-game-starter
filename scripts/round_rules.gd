class_name RoundRules
extends RefCounted
## 只拥有回合规则；物理位置归具体 CharacterBody2D／3D，不在此复制。

signal activated

enum Result { ACCEPTED, INACTIVE, PAUSED, OUT_OF_RANGE, ALREADY_ACTIVATED, INVALID }

var _running: bool = false
var _paused: bool = false
var _activated: bool = false
var _elapsed: float = 0.0
var _reach: float


func _init(reach: float = 1.5) -> void:
	_reach = reach


func start() -> void:
	_running = true
	_paused = false
	_activated = false
	_elapsed = 0.0


func set_paused(value: bool) -> Result:
	if not _running:
		return Result.INACTIVE
	_paused = value
	return Result.ACCEPTED


func interact(distance: float) -> Result:
	if not is_finite(distance) or distance < 0.0 or not is_finite(_reach) or _reach <= 0.0:
		return Result.INVALID
	if not _running:
		return Result.INACTIVE
	if _paused:
		return Result.PAUSED
	if _activated:
		return Result.ALREADY_ACTIVATED
	if distance > _reach:
		return Result.OUT_OF_RANGE
	_activated = true
	activated.emit()
	return Result.ACCEPTED


func advance(seconds: float) -> bool:
	if not is_finite(seconds) or seconds < 0.0:
		return false
	if _running and not _paused:
		_elapsed += seconds
	return true


func view() -> Dictionary:
	return {"running": _running, "paused": _paused, "activated": _activated, "elapsed": _elapsed}
