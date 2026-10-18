"""项目本地引导；显式联网，不装全局依赖，不覆盖已有插件。"""
import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".tools"


def download(url: str, destination: Path, sha256: str) -> None:
    if not destination.exists():
        urllib.request.urlretrieve(url, destination)
    if hashlib.sha256(destination.read_bytes()).hexdigest() != sha256:
        raise RuntimeError(f"下载校验失败，保留检查，不覆盖: {destination}")


def main():
    parser = argparse.ArgumentParser(description="只安装至 .tools；首次需网络")
    parser.add_argument("component", choices=["ai", "templates"])
    args = parser.parse_args()
    TOOLS.mkdir(exist_ok=True)
    lock = json.loads((ROOT / "dependencies.lock.json").read_text(encoding="utf8"))
    if args.component == "ai":
        env = TOOLS / "venv"
        if not env.exists():
            venv.EnvBuilder(with_pip=True).create(env)
        python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--index-url", "https://pypi.org/simple", "-r", str(ROOT / "tools/requirements-ai.lock.txt")], check=True)
        subprocess.run([str(python), "-m", "pip", "check"], check=True)
    else:
        archive = TOOLS / "templates.tpz"
        download("https://github.com/godotengine/godot-builds/releases/download/4.7-stable/Godot_v4.7-stable_export_templates.tpz", archive, lock["godot"]["templates_sha256"])
        with zipfile.ZipFile(archive) as zipped:
            for relative in ["templates/windows_debug_x86_64.exe", "templates/windows_release_x86_64.exe", "templates/version.txt"]:
                target = TOOLS / "templates" / relative
                raw = zipped.read(relative)
                if target.exists() and target.read_bytes() != raw:
                    raise RuntimeError(f"不覆盖已有不同文件: {target}")
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_bytes(raw)
    print("项目内依赖就绪；没有安装全局包或改系统策略。")


if __name__ == "__main__":
    main()
