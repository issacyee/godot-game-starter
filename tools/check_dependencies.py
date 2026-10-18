"""第三方完整树锁校验；许可与省略项另见 dependencies.lock.json。"""
import hashlib
import json
from pathlib import Path
from dev import ROOT


def check() -> None:
    expected = json.loads((ROOT / "third-party-inventory.json").read_text(encoding="utf8"))
    actual = {}
    for folder in [ROOT / "addons/godot_ai", ROOT / "addons/gdUnit4"]:
        for path in folder.rglob("*"):
            if path.is_file():
                actual[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected != actual:
        raise RuntimeError("第三方树变化；复核发行、许可与有意省略项后显式更新锁，不自动修复")
    print(f"第三方树锁一致：{len(actual)} 个文件")


if __name__ == "__main__":
    check()
