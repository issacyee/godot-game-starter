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
        changed = [relative for relative in expected if actual.get(relative) != expected[relative]]
        line_ending_only = (
            set(expected) == set(actual)
            and bool(changed)
            and all(
                (ROOT / relative).is_file()
                and hashlib.sha256((ROOT / relative).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                == expected[relative]
                for relative in changed
            )
        )
        if line_ending_only:
            raise RuntimeError("第三方树为 CRLF 行尾；请按 .gitattributes 重新检出后再验证")
        raise RuntimeError("第三方树变化；复核发行、许可与有意省略项后显式更新锁，不自动修复")
    print(f"第三方树锁一致：{len(actual)} 个文件")


if __name__ == "__main__":
    check()
