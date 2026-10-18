class_name DiagnosticJournal
extends RefCounted
## 仅内存、白名单字段、有界、无玩家内容与机器路径，默认不上传。

var _capacity: int
var _events: Array[Dictionary] = []
var _sequence: int = 0
var dropped: int = 0


func _init(capacity: int) -> void:
	_capacity = maxi(1, capacity)


func record(code: StringName, result: int) -> void:
	_sequence += 1
	if _events.size() == _capacity:
		_events.pop_front()
		dropped += 1
	_events.append({"sequence": _sequence, "code": str(code), "result": result})


func snapshot() -> Dictionary:
	return {"events": _events.duplicate(true), "dropped": dropped}
