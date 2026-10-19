"""测试入口负向自证；真实 GdUnit4 故障进程 + 独立报告篡改检查。"""
import os
from pathlib import Path
import shutil
import time
from dev import execute, isolated_env, stage_project, run_layer, validate_report, write_json, selected_test_files, ROOT
from routes import ROUTES, validate_sample, configured_routes

REQUIRED_NEGATIVE = {"assertion", "parse", "script_load", "resource", "hang", "zero", "skip", "zero_filter",
                     "missing", "stale", "incomplete", "exit_code", "skipped_report", "count_mismatch", "missing_fields",
                     "route_mismatch", "position_shape", "position_nonfinite", "parameter_mismatch", "unknown_route", "project_route", "route_scene_mismatch", "route_test_missing"}


FIXTURES = {
    "assertion": 'extends GdUnitTestSuite\nfunc test_bad() -> void:\n\tassert_int(1).is_equal(2)\n',
    "parse": 'extends GdUnitTestSuite\nfunc test_bad( -> void:\n\tpass\n',
    "script_load": 'extends GdUnitTestSuite\nconst Missing = preload("res://does_not_exist.gd")\nfunc test_bad() -> void:\n\tpass\n',
    "resource": 'extends GdUnitTestSuite\nfunc test_bad() -> void:\n\tvar resource: Resource = load("res://missing.tres")\n\tassert_object(resource).is_not_null()\n',
    "hang": 'extends GdUnitTestSuite\nfunc test_bad() -> void:\n\twhile true:\n\t\tpass\n',
    "zero": 'extends GdUnitTestSuite\nfunc helper() -> void:\n\tpass\n',
    "skip": 'extends GdUnitTestSuite\nfunc test_bad(_do_skip := true) -> void:\n\tassert_int(1).is_equal(1)\n',
}


def check(out: Path, godot: str) -> dict:
    project = out / "project"
    stage_project(project)
    shutil.rmtree(project / "tests")
    (project / "tests/unit").mkdir(parents=True)
    result = {}
    env = isolated_env(out / "profile")
    if execute([godot, "--headless", "--path", str(project), "--editor", "--import"], out / "import.log", env) != 0:
        raise RuntimeError("故障夹具初始化失败")
    fixture = project / "tests/unit/fault_test.gd"
    reasons = {"assertion":"退出码 100", "parse":"退出码 105", "script_load":"退出码 105", "resource":"退出码 100", "hang":"超时", "zero":"报告", "skip":"skipped"}
    for name, script in FIXTURES.items():
        fixture.write_text(script, encoding="utf8")
        try:
            run_layer(project, "unit", out / name, godot, timeout=8 if name == "hang" else 30)
        except Exception as exc:
            if reasons[name] not in str(exc):
                raise RuntimeError(f"故障夹具并非因预期原因拒绝: {name}: {exc}") from exc
            result[name] = {"rejected": True, "reason": str(exc)}
        else:
            raise RuntimeError(f"未拒绝故障: {name}")
    # 过滤零匹配：明确不存在的筛选目录，而不是没有调用测试入口。
    log = out / "zero-filter.log"
    code = execute([godot, "--headless", "--path", str(project), "-s", "addons/gdUnit4/bin/GdUnitCmdTool.gd", "-a", "res://tests/nonexistent", "--ignoreHeadlessMode", "-rd", str(out / "zero-filter")], log, env, 30)
    try:
        validate_report(out / "zero-filter", time.time() - 60, {"required:test"}, code, log)
    except Exception as exc:
        result["zero_filter"] = {"rejected": True, "reason": str(exc)}
    else:
        raise RuntimeError("筛选零匹配被接受")
    clean = out / "report-fixtures"
    clean.mkdir()
    log = clean / "process.log"
    log.write_text("", encoding="utf8")
    good = '<testsuites tests="1" failures="0" skipped="0" flaky="0"><testsuite tests="1" failures="0" errors="0" skipped="0" flaky="0"><testcase classname="proof" name="test_ok" /></testsuite></testsuites>'
    report = clean / "results.xml"
    report.write_text(good, encoding="utf8")
    validate_report(clean, time.time(), {"proof:test_ok"}, 0, log)  # 对照正例
    for name in ["missing", "stale", "incomplete", "exit_code", "skipped_report", "count_mismatch", "missing_fields"]:
        report.write_text(good, encoding="utf8")
        code = 0
        if name == "missing":
            report.unlink()
        elif name == "stale":
            os.utime(report, (1, 1))
        elif name == "incomplete":
            report.write_text(good[:-15], encoding="utf8")
        elif name == "exit_code":
            code = 1
        elif name == "skipped_report":
            report.write_text(good.replace('<testcase classname="proof" name="test_ok" />', '<testcase classname="proof" name="test_ok"><skipped /></testcase>'), encoding="utf8")
        elif name == "missing_fields":
            report.write_text(good.replace('failures="0"', ''), encoding="utf8")
        elif name == "count_mismatch":
            report.write_text(good.replace('tests="1"', 'tests="2"'), encoding="utf8")
        try:
            validate_report(clean, time.time(), {"proof:test_ok"}, code, log)
        except Exception as exc:
            result[name] = {"rejected": True, "reason": str(exc)}
        else:
            raise RuntimeError(f"报告故障被接受: {name}")
    # 两路线的正例和删字段／错单位反例，预期来自显式基线，不读取产品自报值。
    import copy
    for route, spec in ROUTES.items():
        good_sample = {"schema": 2, "route": route, "position_space": "world_local", "distance_unit": spec["unit"],
                       "position": spec["origin"], "parameter_source": spec["baseline"],
                       "parameters": {"diagnostic_capacity": 32, "direction_deadzone": 0.15,
                                      "interaction_reach": spec["reach"], "move_speed": spec["speed"], "text_size": 22}}
        validate_sample(good_sample, route)
        mutations = {"route_mismatch": {"route": "3d" if route == "2d" else "2d"},
                     "position_shape": {"position": [0]}, "position_nonfinite": {"position": [float("nan")] * len(spec["origin"])},
                     "parameter_mismatch": {"parameters": {}}, "unknown_route": {"route": "unknown"}}
        for name, changes in mutations.items():
            sample = copy.deepcopy(good_sample)
            sample.update(changes)
            try:
                validate_sample(sample, route)
            except RuntimeError as exc:
                result.setdefault(name, {"rejected": True, "routes": {}})["routes"][route] = str(exc)
            else:
                raise RuntimeError(f"路线故障被接受: {route}/{name}")
    # 在隔离项目中保留真实公共路线测试，错误登记须由新 Godot 进程拒绝。
    (project / "tests/scene").mkdir()
    shutil.copy2(ROOT / "tests/scene/project_route_test.gd", project / "tests/scene/project_route_test.gd")
    for name in ["main_scene_test.gd", "main_2d_scene_test.gd"]:
        (project / "tests/scene" / name).write_text('extends GdUnitTestSuite\nfunc test_control() -> void:\n\tassert_bool(true).is_true()\n', encoding="utf8")
    import re
    main = re.search(r'^run/main_scene="([^"]+)"', (project / "project.godot").read_text(encoding="utf8"), re.M).group(1)
    wrong = "3d" if main == ROUTES["2d"]["scene"] else "2d"
    write_json(project / "starter-project.json", {"schema": 1, "route": wrong})
    try:
        run_layer(project, "scene", out / "route-scene-mismatch", godot)
    except RuntimeError as exc:
        if "退出码 100" not in str(exc):
            raise RuntimeError(f"路线不一致并非断言拒绝: {exc}") from exc
        result["route_scene_mismatch"] = {"rejected": True, "reason": str(exc)}
    else:
        raise RuntimeError("登记与主场景不一致被接受")
    selection = out / "route-selection"; (selection / "tests/scene").mkdir(parents=True)
    for name in ["main_scene_test.gd", "main_2d_scene_test.gd", "project_route_test.gd"]:
        (selection / "tests/scene" / name).touch()
    for route, expected in [("template", 3), ("2d", 2), ("3d", 2)]:
        write_json(selection / "starter-project.json", {"schema": 1, "route": route})
        if len(selected_test_files(selection, "scene")) != expected:
            raise RuntimeError("路线测试选择未生效")
    write_json(selection / "starter-project.json", {"schema": 1, "route": "unknown"})
    try:
        configured_routes(selection)
    except RuntimeError as exc:
        result["project_route"] = {"rejected": True, "reason": str(exc)}
    else:
        raise RuntimeError("未知派生路线未被拒绝")
    missing = out / "missing-route-suite"; (missing / "tests/scene").mkdir(parents=True)
    write_json(missing / "starter-project.json", {"schema": 1, "route": "2d"})
    try:
        selected_test_files(missing, "scene")
    except RuntimeError as exc:
        result["route_test_missing"] = {"rejected": True, "reason": str(exc)}
    else:
        raise RuntimeError("缺少所选路线测试被接受")
    if set(result) != REQUIRED_NEGATIVE:
        raise RuntimeError("负向清单不完整")
    write_json(out / "negative-summary.json", result)
    return result
