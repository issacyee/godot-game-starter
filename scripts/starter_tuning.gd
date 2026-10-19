@tool
class_name StarterTuning
extends Resource
## 定义不是实例状态；加载后复制有效值，不写回此 Resource。

@export_enum("2d", "3d") var route: String = "3d"

@export_group("玩法")
## 3D：米/秒；2D：像素/秒。每次进程启动读取。
@export var move_speed: float = 4.0
## 3D：米；2D：像素。必须小于该路线起点到目标的距离。
@export var interaction_reach: float = 1.5

@export_group("输入")
## 语义方向死区，归一化幅度。
@export_range(0.0, 0.5, 0.01) var direction_deadzone: float = 0.15

@export_group("表现")
## UI 正文字号，像素。
@export_range(16, 32, 1) var text_size: int = 22

@export_group("工程预算")
## 诊断环形缓冲最大条数，不是平衡参数。
@export_range(8, 128, 1) var diagnostic_capacity: int = 32


func validate() -> PackedStringArray:
	var errors: PackedStringArray = []
	if route not in ["2d", "3d"]:
		errors.append("route: 必须为 2d 或 3d")
	var speed_min: float = 50.0 if route == "2d" else 1.0
	var speed_max: float = 500.0 if route == "2d" else 10.0
	var reach_min: float = 25.0 if route == "2d" else 0.5
	var reach_max: float = 100.0 if route == "2d" else 2.0
	if not is_finite(move_speed) or move_speed < speed_min or move_speed > speed_max:
		errors.append("move_speed: 超出路线速度范围")
	if not is_finite(interaction_reach) or interaction_reach < reach_min or interaction_reach > reach_max:
		errors.append("interaction_reach: 超出路线距离范围")
	if not is_finite(direction_deadzone) or direction_deadzone < 0.0 or direction_deadzone > 0.5:
		errors.append("direction_deadzone: 必须在 [0, 0.5]")
	if text_size < 16 or text_size > 32:
		errors.append("text_size: 必须在 [16, 32] 像素")
	if diagnostic_capacity < 8 or diagnostic_capacity > 128:
		errors.append("diagnostic_capacity: 必须在 [8, 128]")
	return errors


func validate_for(expected_route: String) -> PackedStringArray:
	var errors: PackedStringArray = validate()
	if route != expected_route:
		errors.append("route: 参数与场景路线不符")
	return errors


func effective_values() -> Dictionary:
	return {"move_speed": move_speed, "interaction_reach": interaction_reach,
		"direction_deadzone": direction_deadzone, "text_size": text_size,
		"diagnostic_capacity": diagnostic_capacity}
