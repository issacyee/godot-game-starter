"""检查本项目 Markdown 相对文件链接；不联网检查外链。"""
import re
from pathlib import Path
from dev import ROOT

errors = []
for path in [ROOT / "AGENTS.md", ROOT / "README.md", *(ROOT / "docs").rglob("*.md"), ROOT / "tuning/README.md"]:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding="utf8")):
        if "://" in target or target.startswith("#"):
            continue
        file = target.split("#")[0]
        if not (path.parent / file).exists():
            errors.append(f"{path.relative_to(ROOT)} -> {target}")
if errors:
    raise SystemExit("\n".join(errors))
print("相对文件链接检查通过（不验证标题锚点与外部网站）")
