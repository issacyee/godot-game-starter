@tool
class_name StarterTuning
extends Resource
## 定义不是实例状态；加载后复制有效值，不写回此 Resource。

@export_group("玩法")
## 移动速度，米/秒；每次进程启动读取。
@export_range(1.0, 10.0, 0.1) var move_speed: float = 4.0
## 交互距离，米；必须小于起点到目标的三米距离。
@export_range(0.5, 2.0, 0.1) var interaction_reach: float = 1.5

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
	if not is_finite(move_speed) or move_speed < 1.0 or move_speed > 10.0:
		errors.append("move_speed: 必须在 [1, 10] 米/秒")
	if not is_finite(interaction_reach) or interaction_reach < 0.5 or interaction_reach > 2.0:
		errors.append("interaction_reach: 必须在 [0.5, 2] 米，且小于起点目标距离")
	if not is_finite(direction_deadzone) or direction_deadzone < 0.0 or direction_deadzone > 0.5:
		errors.append("direction_deadzone: 必须在 [0, 0.5]")
	if text_size < 16 or text_size > 32:
		errors.append("text_size: 必须在 [16, 32] 像素")
	if diagnostic_capacity < 8 or diagnostic_capacity > 128:
		errors.append("diagnostic_capacity: 必须在 [8, 128]")
	return errors


func effective_values() -> Dictionary:
	return {"move_speed": move_speed, "interaction_reach": interaction_reach,
		"direction_deadzone": direction_deadzone, "text_size": text_size,
		"diagnostic_capacity": diagnostic_capacity}
