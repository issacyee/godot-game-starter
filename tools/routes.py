"""模板示例的显式入口及产品验收基线；派生玩法后须同步替换，不能从探针推导预期。"""
import math
import json
from pathlib import Path

ROUTES = {
    "2d": {"scene": "res://scenes/main_2d.tscn", "unit": "px", "origin": [0, 0],
           "move_range": (90.0, 120.0), "speed": 200.0, "reach": 75.0,
           "baseline": "res://tuning/baseline_2d.tres", "package": "package"},
    "3d": {"scene": "res://scenes/main.tscn", "unit": "m", "origin": [0, 0.5, 0],
           "move_range": (1.8, 4.0), "speed": 4.0, "reach": 1.5,
           "baseline": "res://tuning/baseline.tres", "package": "package-3d"},
}


def configured_routes(root: Path) -> tuple[str, ...]:
    config = json.loads((root / "starter-project.json").read_text(encoding="utf8"))
    if config.get("schema") != 1 or config.get("route") not in ["template", "2d", "3d"]:
        raise RuntimeError("starter-project.json: 必须显式选择 template、2d 或 3d")
    return tuple(ROUTES) if config["route"] == "template" else (config["route"],)


def validate_sample(state: dict, route: str) -> None:
    spec = ROUTES[route]
    if (state.get("schema") != 2 or state.get("route") != route
            or state.get("position_space") != "world_local" or state.get("distance_unit") != spec["unit"]):
        raise RuntimeError("路线、单位或采样格式不符")
    position = state.get("position")
    if (not isinstance(position, list) or len(position) != len(spec["origin"])
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in position)):
        raise RuntimeError("位置分量无效")
    expected = {"diagnostic_capacity": 32, "direction_deadzone": 0.15, "interaction_reach": spec["reach"],
                "move_speed": spec["speed"], "text_size": 22}
    if state.get("parameters") != expected or state.get("parameter_source") != spec["baseline"]:
        raise RuntimeError("实际有效参数或来源与路线基线不符")
