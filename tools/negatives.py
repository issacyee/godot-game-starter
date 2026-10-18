"""测试入口负向自证；真实 GdUnit4 故障进程 + 独立报告篡改检查。"""
import os
from pathlib import Path
import shutil
import time
from dev import execute, isolated_env, stage_project, run_layer, validate_report, write_json


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
    write_json(out / "negative-summary.json", result)
    return result
