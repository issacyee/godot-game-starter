"""导出与只读复核；不写原场景，不依赖长期编辑器。"""
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from dev import ROOT, digest, inventory, isolated_env, execute, stage_project, test, validate_report, write_json


def export(out: Path, godot: str) -> dict:
    from negatives import check
    from platform_windows import exercise
    from visual import verify_frames
    from verify_ai import check as check_ai
    ai = check_ai(out)
    subprocess.run(["python", str(ROOT / "tools/check_docs.py")], check=True)
    testing = out / "testing"; testing.mkdir()
    tests = test(testing, godot)
    negative = out / "negative"; negative.mkdir()
    faults = check(negative, godot)
    project = out / "product-project"
    stage_project(project)
    shutil.rmtree(project / "tests")
    shutil.rmtree(project / "addons")
    shutil.copytree(ROOT / "licenses", project / "licenses")
    # build_identity.json 只创建于导出副本；不往源码写临时身份。
    source = inventory()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    identity = {"schema":1,"channel":"dev","version":"0.1.0-dev","source_hash":digest(source),
                "git_commit":commit.stdout.strip() if commit.returncode == 0 else None,
                "engine":"4.7.stable.official.5b4e0cb0f", "built_at_utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "dependencies":json.loads((ROOT/"dependencies.lock.json").read_text(encoding="utf8"))}
    write_json(project / "build_identity.json", identity)
    templates = ROOT / ".tools/templates/templates"
    for name in ["windows_debug_x86_64.exe", "windows_release_x86_64.exe"]:
        if not (templates/name).is_file():
            raise RuntimeError("匹配的 Windows 标准导出模板缺失；先执行 tools/setup.py templates")
        key = "windows_debug_sha256" if "debug" in name else "windows_release_sha256"
        if hashlib.sha256((templates/name).read_bytes()).hexdigest() != identity["dependencies"]["godot"][key]:
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
''' % ((templates/"windows_debug_x86_64.exe").as_posix(), (templates/"windows_release_x86_64.exe").as_posix())
    (project/"export_presets.cfg").write_text(preset,encoding="utf8")
    env=isolated_env(out/"export-profile")
    if execute([godot,"--headless","--path",str(project),"--editor","--import"],out/"import-product.log",env)!=0:
        raise RuntimeError("导出副本导入失败")
    import_log = (out/"import-product.log").read_text(encoding="utf8")
    if re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", import_log, re.M):
        raise RuntimeError("导出导入存在脚本／资源错误")
    product=out/"package";product.mkdir();exe=product/"starter.exe"
    code=execute([godot,"--headless","--path",str(project),"--export-debug","Windows Desktop",str(exe)],out/"export.log",env)
    if code!=0 or re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", (out/"export.log").read_text(encoding="utf8"), re.M) or not exe.is_file() or not exe.with_suffix(".pck").is_file():
        raise RuntimeError("实际导出失败")
    write_json(product/"build_identity.json",identity)
    shutil.copytree(ROOT/"licenses",product/"licenses")
    platform=exercise(exe,out/"platform")
    if re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:", (out/"platform/product.log").read_text(encoding="utf8"), re.M):
        raise RuntimeError("实际产品日志存在错误")
    visual=verify_frames(out/"platform")
    for action in platform["actions"]:
        if action["state"]["build"]["source_hash"] != identity["source_hash"]:
            raise RuntimeError("实际产品嵌入身份不匹配")
    evidence={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob("*")) if p.is_file() and (p.suffix in [".png",".xml",".log"] or p.name.startswith("ai-") or "package" in p.relative_to(out).parts or p.name in ["platform.json","negative-summary.json","build_identity.json"] or (p.parent.name=="platform" and p.suffix==".json"))}
    result={"ai":ai,"tests":tests,"negative":faults,"platform":platform,"visual":visual,"identity":identity,"evidence":evidence,"release_ready":False}
    write_json(out/"delivery.json",result)
    return result


def verify(out: Path) -> None:
    from visual import verify_frames
    from platform_windows import validate_platform
    record=json.loads((out/"result.json").read_text(encoding="utf8"))
    if not record["passed"] or record["source"]!=inventory() or record["source_hash"]!=digest(inventory()):
        raise RuntimeError("失败报告或当前源码已漂移，需重新验证")
    if record["command"]!="export":
        raise RuntimeError("只读交付复核要求 export 报告")
    delivery=json.loads((out/"delivery.json").read_text(encoding="utf8"))
    if delivery!=record["result"]:
        raise RuntimeError("交付总报告不一致")
    for relative,expected in delivery["evidence"].items():
        path=out/relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError(f"证据损坏或缺失: {relative}")
    for layer,value in delivery["tests"].items():
        validate_report(out/"testing"/layer/"reports",record["started"],set(value["expected"]),0,out/"testing"/layer/"process.log")
    required_negative={"assertion","parse","script_load","resource","hang","zero","skip","zero_filter","missing","stale","incomplete","exit_code","skipped_report","count_mismatch","missing_fields"}
    if set(delivery["negative"]) != required_negative or not all(x["rejected"] for x in delivery["negative"].values()):
        raise RuntimeError("负向自证不完整")
    if delivery["ai"]["telemetry_enabled"] is not False or "testing" not in delivery["ai"]["exclude_domains"]:
        raise RuntimeError("AI 实际配置证据不足")
    validate_platform(delivery["platform"])
    if verify_frames(out/"platform")!=delivery["visual"]:
        raise RuntimeError("像素重执行不一致")
    required={"title","start","move","interact","pause","continue","restart-0","restart-1","restart-2"}
    actions=delivery["platform"]["actions"]
    if {a["id"] for a in actions}!=required or delivery["platform"]["exit_code"]!=0:
        raise RuntimeError("实际平台流程不完整")
    for action in actions:
        if action["state"]["build"]["source_hash"]!=record["source_hash"]:
            raise RuntimeError("产品身份与源码不符")
    print("只读复核通过：当前源码、GdUnit4、负向检查、实际产品、OS 输入和局部像素证据一致。")
