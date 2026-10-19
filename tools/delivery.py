"""双路线实际导出与只读复核；只在隔离副本选择主场景，不改原资源。"""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from dev import ROOT, digest, inventory, isolated_env, execute, stage_project, test, validate_report, write_json
from routes import ROUTES, configured_routes


def export(out: Path, godot: str) -> dict:
    from negatives import check
    from verify_ai import check as check_ai
    ai = check_ai(out)
    subprocess.run(["python", str(ROOT / "tools/check_docs.py")], check=True)
    testing = out / "testing"; testing.mkdir()
    tests = test(testing, godot)
    negative = out / "negative"; negative.mkdir()
    faults = check(negative, godot)
    products = {route: export_route(out, godot, route) for route in configured_routes(ROOT)}
    evidence = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(out.rglob("*")) if p.is_file()
                and (p.suffix in [".png", ".xml", ".log"] or p.name.startswith("ai-")
                     or any(part in ["package", "package-3d"] for part in p.relative_to(out).parts)
                     or p.name in ["platform.json", "negative-summary.json", "build_identity.json"]
                     or (p.parent.name.startswith("platform-") and p.suffix == ".json"))}
    result = {"ai": ai, "tests": tests, "negative": faults, "routes": products,
              "evidence": evidence, "release_ready": False}
    write_json(out / "delivery.json", result)
    return result


def export_route(out: Path, godot: str, route: str) -> dict:
    from platform_windows import exercise
    from visual import verify_frames
    spec = ROUTES[route]
    project = out / f"product-project-{route}"
    stage_project(project, route)
    shutil.rmtree(project / "tests")
    shutil.rmtree(project / "addons")
    shutil.copytree(ROOT / "licenses", project / "licenses")
    source = inventory()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    identity = {"schema": 2, "channel": "dev", "version": "0.1.0-dev", "route": route,
                "main_scene": spec["scene"], "source_hash": digest(source),
                "git_commit": commit.stdout.strip() if commit.returncode == 0 else None,
                "engine": "4.7.stable.official.5b4e0cb0f",
                "built_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "dependencies": json.loads((ROOT / "dependencies.lock.json").read_text(encoding="utf8"))}
    write_json(project / "build_identity.json", identity)
    templates = ROOT / ".tools/templates/templates"
    for name in ["windows_debug_x86_64.exe", "windows_release_x86_64.exe"]:
        if not (templates / name).is_file():
            raise RuntimeError("匹配的 Windows 标准导出模板缺失；先执行 tools/setup.py templates")
        key = "windows_debug_sha256" if "debug" in name else "windows_release_sha256"
        if hashlib.sha256((templates / name).read_bytes()).hexdigest() != identity["dependencies"]["godot"][key]:
            raise RuntimeError("展开的导出模板与锁定发行字节不一致")
    preset = '''[preset.0]
name="Windows Desktop"
platform="Windows Desktop"
runnable=true
advanced_options=false
custom_features=""
export_filter="all_resources"
include_filter="build_identity.json,licenses/*.txt"
exclude_filter=""
export_path=""
script_export_mode=1

[preset.0.options]
custom_template/debug="%s"
custom_template/release="%s"
binary_format/architecture="x86_64"
binary_format/embed_pck=false
application/modify_resources=false
debug/export_console_wrapper=0
''' % ((templates / "windows_debug_x86_64.exe").as_posix(), (templates / "windows_release_x86_64.exe").as_posix())
    (project / "export_presets.cfg").write_text(preset, encoding="utf8")
    env = isolated_env(out / f"export-profile-{route}")
    import_log = out / f"import-product-{route}.log"
    code = execute([godot, "--headless", "--path", str(project), "--editor", "--import"], import_log, env)
    if code != 0 or re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", import_log.read_text(encoding="utf8"), re.M):
        raise RuntimeError(f"{route} 导出副本导入失败")
    product = out / spec["package"]; product.mkdir(); exe = product / "starter.exe"
    export_log = out / f"export-{route}.log"
    code = execute([godot, "--headless", "--path", str(project), "--export-debug", "Windows Desktop", str(exe)], export_log, env)
    if (code != 0 or re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", export_log.read_text(encoding="utf8"), re.M)
            or not exe.is_file() or not exe.with_suffix(".pck").is_file()):
        raise RuntimeError(f"{route} 实际导出失败")
    write_json(product / "build_identity.json", identity)
    shutil.copytree(ROOT / "licenses", product / "licenses")
    platform_dir = out / f"platform-{route}"
    platform = exercise(exe, platform_dir, route)
    if re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", (platform_dir / "product.log").read_text(encoding="utf8"), re.M):
        raise RuntimeError(f"{route} 实际产品日志存在错误")
    visual = verify_frames(platform_dir, route)
    for action in platform["actions"]:
        if action["state"]["build"] != identity:
            raise RuntimeError("实际产品嵌入身份不匹配")
    return {"platform": platform, "visual": visual, "identity": identity, "package": spec["package"]}


def verify(out: Path) -> None:
    from visual import verify_frames
    from platform_windows import validate_platform
    from negatives import REQUIRED_NEGATIVE
    record = json.loads((out / "result.json").read_text(encoding="utf8"))
    if not record["passed"] or record["source"] != inventory() or record["source_hash"] != digest(inventory()):
        raise RuntimeError("失败报告或当前源码已漂移，需重新验证")
    if record["command"] != "export":
        raise RuntimeError("只读交付复核要求 export 报告")
    delivery = json.loads((out / "delivery.json").read_text(encoding="utf8"))
    if delivery != record["result"]:
        raise RuntimeError("交付总报告不一致")
    for relative, expected in delivery["evidence"].items():
        path = out / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"证据损坏或缺失: {relative}")
    for layer, value in delivery["tests"].items():
        validate_report(out / "testing" / layer / "reports", record["started"], set(value["expected"]), 0,
                        out / "testing" / layer / "process.log")
    if set(delivery["negative"]) != REQUIRED_NEGATIVE or not all(x["rejected"] for x in delivery["negative"].values()):
        raise RuntimeError("负向自证不完整")
    if delivery["ai"]["telemetry_enabled"] is not False or "testing" not in delivery["ai"]["exclude_domains"]:
        raise RuntimeError("AI 实际配置证据不足")
    routes = configured_routes(ROOT)
    if set(delivery["routes"]) != set(routes) or record["routes"] != list(routes):
        raise RuntimeError("所选路线交付证据不完整")
    for route in routes:
        spec = ROUTES[route]
        product = delivery["routes"][route]
        identity = product["identity"]
        if identity["route"] != route or identity["main_scene"] != spec["scene"] or identity["source_hash"] != record["source_hash"]:
            raise RuntimeError("路线构建身份不符")
        validate_platform(product["platform"], route)
        if verify_frames(out / f"platform-{route}", route) != product["visual"]:
            raise RuntimeError("像素重执行不一致")
        package = out / spec["package"]
        for name in ["starter.exe", "starter.pck", "build_identity.json"]:
            if not (package / name).is_file():
                raise RuntimeError("实际包缺失")
        if json.loads((package / "build_identity.json").read_text(encoding="utf8")) != identity:
            raise RuntimeError("包身份不符")
        for action in product["platform"]["actions"]:
            if action["state"]["build"] != identity:
                raise RuntimeError("产品身份与源码不符")
    print("只读复核通过：当前源码、GdUnit4、负向检查、所选路线实际包、OS 输入和局部像素证据一致。")
