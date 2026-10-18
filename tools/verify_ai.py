"""实际核对 Godot AI 工具、版本和目标会话；不调用 testing 域。"""
import json
import os
from pathlib import Path
import subprocess
from dev import ROOT, isolated_env, inventory, write_json


def check(out: Path) -> dict:
    python = ROOT / ".tools/venv/Scripts/python.exe"
    config = json.loads((ROOT / "tools/ai-config.json").read_text(encoding="utf8"))
    port = int(config["http_port"])
    capability = ROOT / f".tools/profile/local/godot-ai/capabilities/http-{port}.json"
    token = json.loads(capability.read_text(encoding="utf8"))["http"]
    import urllib.request
    request = urllib.request.Request(f"http://127.0.0.1:{port}/godot-ai/status", headers={"Authorization": f"Bearer {token}"})
    status = json.load(urllib.request.urlopen(request, timeout=5))
    if status.get("telemetry_enabled") is not False:
        raise RuntimeError("实际后端遥测未关闭")
    # 只记录公开状态，不保存能力令牌。
    write_json(out / "ai-status.json", {"telemetry_enabled":False,"version":status.get("version")})
    results = {}
    for name, args in [("tools", ["list"]), ("sessions", ["session_manage", '{"op":"list"}']), ("editor", ["editor_state"])]:
        process = subprocess.run([str(python), str(ROOT / "tools/ai.py"), *args], cwd=ROOT, capture_output=True, encoding="utf8", timeout=40)
        (out / f"ai-{name}.stderr.log").write_text(process.stderr, encoding="utf8")
        if process.returncode != 0:
            raise RuntimeError(f"Godot AI 实际核对失败: {name}，请看日志，不自动重试")
        result = json.loads(process.stdout)
        write_json(out / f"ai-{name}.json", result)
        results[name] = result
    names = {tool["name"] for tool in results["tools"]["tools"]}
    if {"test_run", "test_manage"} & names or not {"node_create", "resource_manage", "scene_save", "editor_screenshot", "project_run", "logs_read"} <= names:
        raise RuntimeError("testing 未排除或结构化编辑工具缺失")
    sessions = results["sessions"]["structured_content"]
    matching = [s for s in sessions["sessions"] if Path(s["project_path"]).resolve() == ROOT]
    if "testing" not in sessions["exclude_domains"] or len(matching) != 1:
        raise RuntimeError("实际排除项或目标项目会话不符")
    selected = matching[0]
    if selected["plugin_version"] != "4.3.0" or selected["server_version"] != "4.3.0" or selected["godot_version"] != "4.7-stable (official)":
        raise RuntimeError("实际 Godot AI 版本组合不符")
    return {"telemetry_enabled":False,"tool_count":len(names),"exclude_domains":sessions["exclude_domains"],"plugin":"4.3.0","server":"4.3.0","godot":"4.7-stable (official)","project":selected["project_path"]}
