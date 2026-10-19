"""项目内 Godot AI MCP 客户端；不改全局客户端配置，不保存凭据。"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / ".tools/profile"
ENV = dict(os.environ, APPDATA=str(PROFILE / "roaming"), LOCALAPPDATA=str(PROFILE / "local"), GODOT_AI_DISABLE_TELEMETRY="true", GODOT_AI_VENV_PYTHON=str(ROOT / ".tools/venv/Scripts/python.exe"))


async def main():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    command = str(ROOT / ".tools/venv/Scripts/godot-ai.exe")
    config = json.loads((ROOT / "tools/ai-config.json").read_text(encoding="utf8"))
    exclusions = sorted(set(config["exclude_domains"]) | {"testing"})
    args = ["attach", "--port", str(config["http_port"]), "--ws-port", str(config["ws_port"]), "--exclude-domains", ",".join(exclusions), "--disable-telemetry"]
    async with stdio_client(StdioServerParameters(command=command, args=args, env=ENV)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if sys.argv[1] == "list":
                result = await session.list_tools()
            else:
                params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
                listing = await session.call_tool("session_manage", {"op": "list"})
                sessions = (listing.structured_content or {}).get("sessions", [])
                matching = [s for s in sessions if Path(s["project_path"]).resolve() == ROOT]
                selected = params.get("session_id", "")
                if len(matching) != 1 or (selected and selected != matching[0]["session_id"]):
                    raise RuntimeError("目标项目会话缺失、不唯一或与固定 session_id 不符；不自动重试")
                params["session_id"] = matching[0]["session_id"]
                if sys.argv[1] in ["test_run", "test_manage"]:
                    raise RuntimeError("唯一测试入口是独立进程 GdUnit4")
                if sys.argv[1] == "editor_manage" and params.get("op") == "game_eval":
                    raise RuntimeError("任意脚本执行需要单独审查授权；默认客户端不提供")
                result = await session.call_tool(sys.argv[1], params)
            print(result.model_dump_json(indent=2))
            if getattr(result, "is_error", False):
                raise RuntimeError("Godot AI 操作失败，详情见返回值")


if __name__ == "__main__":
    asyncio.run(main())
