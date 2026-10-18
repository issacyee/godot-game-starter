"""统一离线验证入口；Python 仅用于开发，不进入游戏运行依赖。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", ".godot", ".tools", "artifacts", "reports", "__pycache__"}


def inventory(root: Path = ROOT) -> dict[str, str]:
    result = {}
    for current, directories, files in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in IGNORED)
        for name in sorted(files):
            path = Path(current) / name
            relative = path.relative_to(root)
            if path.is_symlink():
                raise RuntimeError(f"不接受符号链接: {relative}")
            result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def engine() -> str:
    config = ROOT / ".tools/local.json"
    chosen = os.environ.get("STARTER_GODOT")
    if not chosen and config.exists():
        chosen = json.loads(config.read_text(encoding="utf8"))["godot"]
    if not chosen:
        raise RuntimeError("请设置 STARTER_GODOT 为标准版 Godot 4.7 可执行文件的绝对路径")
    version = subprocess.check_output([chosen, "--version"], text=True).strip()
    if version != "4.7.stable.official.5b4e0cb0f":
        raise RuntimeError(f"引擎版本不匹配: {version}")
    return chosen


def isolated_env(profile: Path) -> dict[str, str]:
    for folder in [profile / "roaming", profile / "local", profile / "home"]:
        folder.mkdir(parents=True, exist_ok=True)
    return dict(os.environ, APPDATA=str(profile / "roaming"), LOCALAPPDATA=str(profile / "local"),
                HOME=str(profile / "home"), XDG_DATA_HOME=str(profile / "home/data"),
                XDG_CONFIG_HOME=str(profile / "home/config"), GODOT_AI_DISABLE_TELEMETRY="true")


def execute(command: list[str], log: Path, env: dict, timeout: float = 90) -> int:
    with log.open("w", encoding="utf8") as output:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT)
        try:
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                proc.kill()
            proc.wait(timeout=10)
            raise RuntimeError("测试进程超时，已终止")


def validate_report(report_dir: Path, started: float, expected: set[str], code: int, log: Path) -> dict:
    if code != 0:
        raise RuntimeError(f"测试进程退出码 {code}")
    text = log.read_text(encoding="utf8", errors="replace")
    if re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", text, re.M):
        raise RuntimeError("引擎报告脚本或资源错误")
    reports = list(report_dir.rglob("results.xml"))
    if len(reports) != 1 or reports[0].stat().st_mtime < started - 1:
        raise RuntimeError("缺失、过期或重复报告")
    xml = ET.parse(reports[0]).getroot()
    if xml.tag != "testsuites":
        raise RuntimeError("报告根无效")
    suites = xml.findall("testsuite")
    cases = xml.findall("./testsuite/testcase")
    names = [f'{case.get("classname")}:{case.get("name")}' for case in cases]
    if not expected or not names or len(set(names)) != len(names) or set(names) != expected:
        raise RuntimeError(f"零测试／测试清单不完整: expected={sorted(expected)}, actual={names}")
    if int(xml.attrib["tests"]) != len(cases) or sum(int(s.attrib["tests"]) for s in suites) != len(cases):
        raise RuntimeError("报告测试数量不一致")
    if not suites or not {"tests", "failures", "skipped", "flaky"} <= xml.attrib.keys():
        raise RuntimeError("报告缺少必需汇总字段")
    if any(not {"tests", "failures", "errors", "skipped", "flaky"} <= suite.attrib.keys() for suite in suites):
        raise RuntimeError("报告缺少必需套件字段")
    for item in [xml, *suites]:
        for key in ["failures", "errors", "skipped", "flaky"]:
            if int(item.get(key, "0")) != 0:
                raise RuntimeError(f"报告包含 {key}")
    if any(list(case) for case in cases):
        raise RuntimeError("必需用例失败、错误、跳过或报告存在未知内容")
    return {"tests": len(cases), "failures": 0, "errors": 0, "skipped": 0,
            "report": str(reports[0]), "sha256": hashlib.sha256(reports[0].read_bytes()).hexdigest()}


def stage_project(destination: Path) -> None:
    destination.mkdir()
    for folder in ["scripts", "scenes", "tuning", "assets", "tests"]:
        shutil.copytree(ROOT / folder, destination / folder)
    shutil.copytree(ROOT / "addons/gdUnit4", destination / "addons/gdUnit4")
    # 只修改隔离副本的引导配置，不改任何 .tscn/.tres；核心链无 Godot AI 或编辑器依赖。
    project = (ROOT / "project.godot").read_text(encoding="utf8")
    project = re.sub(r'^_mcp_game_helper=.*\n', '', project, flags=re.M)
    project = re.sub(r'^enabled=PackedStringArray\(.*\)', 'enabled=PackedStringArray()', project, flags=re.M)
    (destination / "project.godot").write_text(project, encoding="utf8")


def required_tests(project: Path, layer: str) -> set[str]:
    expected = set()
    for path in (project / "tests" / layer).glob("*.gd"):
        for name in re.findall(r'^func (test_\w+)\(', path.read_text(encoding="utf8"), re.M):
            expected.add(f"{path.stem}:{name}")
    return expected


def run_layer(project: Path, layer: str, out: Path, godot: str, timeout: float = 90) -> dict:
    out.mkdir()
    env = isolated_env(out / "profile")
    expected = required_tests(project, layer)
    started = time.time()
    code = execute([godot, "--headless", "--path", str(project), "-s", "addons/gdUnit4/bin/GdUnitCmdTool.gd",
                    "-a", f"res://tests/{layer}", "-c", "--ignoreHeadlessMode", "-rd", str(out / "reports")], out / "process.log", env, timeout)
    result = validate_report(out / "reports", started, expected, code, out / "process.log")
    result["expected"] = sorted(expected)
    result["elapsed_seconds"] = time.time() - started
    return result


def test(out: Path, godot: str) -> dict:
    project = out / "project"
    stage_project(project)
    env = isolated_env(out / "import-profile")
    code = execute([godot, "--headless", "--path", str(project), "--editor", "--import"], out / "import.log", env)
    if code != 0 or re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", (out / "import.log").read_text(encoding="utf8"), re.M):
        raise RuntimeError("独立项目导入失败")
    return {layer: run_layer(project, layer, out / layer, godot) for layer in ["unit", "scene"]}


def new_out(name: str) -> Path:
    out = ROOT / "artifacts" / f"{name}-{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns() % 1000000}"
    out.mkdir(parents=True)
    (ROOT / "artifacts/.gdignore").touch(exist_ok=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="项目内统一验证入口")
    parser.add_argument("command", choices=["test", "negative", "editor", "run", "export", "verify"])
    parser.add_argument("path", nargs="?")
    args = parser.parse_args()
    if args.command == "verify":
        from delivery import verify
        verify(Path(args.path).resolve())
        return
    godot = engine()
    if args.command in ["editor", "run"]:
        env = isolated_env(ROOT / ".tools/profile")
        env["GODOT_AI_VENV_PYTHON"] = str(ROOT / ".tools/venv/Scripts/python.exe")
        # 全新副本先完成资源导入，避免插件 UI 在图标／字体尚未导入时初始化。
        if args.command == "editor" and not (ROOT / ".godot/editor/project_metadata.cfg").is_file():
            code = execute([godot, "--headless", "--path", str(ROOT), "--editor", "--import"], ROOT / ".tools/first-import.log", env)
            if code != 0:
                raise RuntimeError("首次导入失败，请查看 .tools/first-import.log")
        log_path = ROOT / ".tools" / f"{args.command}.log"
        with log_path.open("w", encoding="utf8") as log:
            subprocess.Popen([godot, "--path", str(ROOT), *(["--editor"] if args.command == "editor" else [])], env=env, stdout=log, stderr=subprocess.STDOUT)
        print(f"已启动；日志: {log_path}")
        return
    out = new_out(args.command)
    before = inventory()
    report = {"schema": 1, "command": args.command, "started": time.time(), "source": before, "source_hash": digest(before), "passed": False}
    try:
        from check_dependencies import check as check_dependencies
        check_dependencies()
        if args.command == "test":
            report["result"] = test(out, godot)
        elif args.command == "negative":
            from negatives import check
            report["result"] = check(out, godot)
        elif args.command == "export":
            from delivery import export
            report["result"] = export(out, godot)
        if inventory() != before:
            raise RuntimeError("验证期间源码漂移")
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
        print(f"失败: {exc}", file=sys.stderr)
    finally:
        report["finished"] = time.time()
        write_json(out / "result.json", report)
        if report["passed"]:
            write_json(ROOT / "artifacts" / f"latest-{args.command}.json", {"directory":out.relative_to(ROOT).as_posix(), "source_hash":report["source_hash"]})
        print(out)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
