#!/usr/bin/env python3
"""在 .tools/sandbox 创建本地派生项目，用于验证骨架；项目数据不入库。"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dev import IGNORED, STAGE_IGNORE, ROOT, digest, inventory  # noqa: E402

LAB = ROOT / ".tools/sandbox"
GAMES = LAB / "games"
BASELINES = LAB / "baselines"
FINDINGS = LAB / "findings"
PATCHES = LAB / "patches"
GODOT_VERSION = "4.7.stable.official.5b4e0cb0f"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
RESERVED = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(1, 10)} | {f"lpt{i}" for i in range(1, 10)}
IGNORED_PARTS = {".tools", ".git", ".godot", "artifacts", "reports", "__pycache__"}


def fail(message: str) -> None:
    print(f"错误: {message}", file=sys.stderr)
    raise SystemExit(2)


def stderr_text(result) -> str:
    return result.stderr.decode("utf8", "replace").strip() or "(无 stderr)"


def git(*args: str):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"git 调用失败: {exc}")


def validate_name(name: str) -> None:
    if not NAME_RE.fullmatch(name):
        fail("--name 必须匹配 ^[a-z0-9][a-z0-9-]{0,63}$")
    if name in RESERVED or name.rstrip(" .") != name:
        fail("--name 是 Windows 保留名或结尾含空格/点")


def validate_lab() -> None:
    if ROOT != Path(__file__).resolve().parents[1]:
        fail("tools/lab.py 位置异常")
    if LAB.parent.name != ".tools":
        fail("沙盒必须位于 .tools/sandbox")
    if ".tools" not in IGNORED or ".tools" not in STAGE_IGNORE:
        fail("骨架工具未排除 .tools；拒绝创建会污染源码哈希/产物的沙盒")
    lab = LAB.resolve()
    for path in (GAMES, BASELINES, FINDINGS, PATCHES):
        if not path.resolve().is_relative_to(lab):
            fail(f"目录不在沙盒内（可能是符号链接）: {path}")


def ensure_dirs() -> None:
    for path in (GAMES, BASELINES, FINDINGS, PATCHES):
        path.mkdir(parents=True, exist_ok=True)


def check_ignored() -> None:
    result = git("check-ignore", "-q", ".tools/sandbox")
    if result.returncode != 0:
        fail(".tools/sandbox 未被 Git 忽略；拒绝在可能被提交的位置创建项目")


def list_files(tracked_only: bool) -> tuple[list[str], list[str]]:
    cached = git("ls-files", "-z", "--cached")
    if cached.returncode != 0:
        fail(f"git ls-files 失败: {stderr_text(cached)}")
    tracked = [os.fsdecode(item) for item in cached.stdout.split(b"\0") if item]
    untracked: list[str] = []
    if not tracked_only:
        others = git("ls-files", "-z", "--others", "--exclude-standard")
        if others.returncode != 0:
            fail(f"git ls-files --others 失败: {stderr_text(others)}")
        untracked = [os.fsdecode(item) for item in others.stdout.split(b"\0") if item]
    if len(set(tracked)) != len(tracked) or len(set(untracked)) != len(untracked) or set(tracked) & set(untracked):
        fail("Git 文件清单存在重复或交叉")
    return tracked, untracked


def validate_paths(entries: list[str]) -> None:
    for entry in entries:
        relative = Path(entry)
        if relative.is_absolute() or not relative.parts:
            fail(f"非法路径: {entry}")
        if any(part in ("", ".", "..") for part in relative.parts):
            fail(f"路径包含空段、. 或 ..: {entry}")
        if any(part in IGNORED_PARTS for part in relative.parts):
            fail(f"路径位于本地排除目录: {entry}")
        source = ROOT / relative
        if source.is_symlink():
            fail(f"拒绝符号链接: {entry}")
        if source.is_dir():
            fail(f"拒绝目录或子模块: {entry}")
        if not source.is_file():
            fail(f"文件缺失或不是普通文件: {entry}")


def validate_godot(value: str) -> Path:
    try:
        path = Path(value).expanduser().absolute()
    except OSError as exc:
        fail(f"无法解析 --godot: {exc}")
    if not path.is_file():
        fail(f"--godot 不存在或不是文件: {path}")
    try:
        result = subprocess.run([str(path), "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"无法执行 --godot: {exc}")
    version = (result.stdout or "").strip() or (result.stderr or "").strip()
    if result.returncode != 0 or version != GODOT_VERSION:
        fail(f"--godot 版本不匹配: {version!r}，要求 {GODOT_VERSION}")
    return path


def write_local_config(target: Path, godot: Path | None) -> bool:
    if godot is None:
        return False
    ignore_file = target / ".gitignore"
    if not ignore_file.is_file():
        print("警告: 目标缺少 .gitignore；不写 .tools/local.json", file=sys.stderr)
        return False
    ignored = {line.strip() for line in ignore_file.read_text(encoding="utf8", errors="replace").splitlines()}
    if not ({".tools/", ".tools", "/.tools/"} & ignored):
        print("警告: 目标 .gitignore 未忽略 .tools/；不写 .tools/local.json", file=sys.stderr)
        return False
    local = target / ".tools/local.json"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps({"godot": str(godot)}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return True


def create(args) -> None:
    validate_name(args.name)
    validate_lab()
    ensure_dirs()
    validate_lab()
    check_ignored()
    godot = validate_godot(args.godot) if args.godot else None

    target = GAMES / args.name
    baseline = BASELINES / f"{args.name}.json"
    if target.exists():
        fail(f"目标已存在: {target.relative_to(ROOT).as_posix()}")
    if baseline.exists():
        fail(f"基线已存在: {baseline.relative_to(ROOT).as_posix()}")

    source_inventory = inventory()
    source_hash = digest(source_inventory)
    status = git("status", "--porcelain")
    if status.returncode != 0:
        fail(f"git status 失败: {stderr_text(status)}")
    dirty = bool(status.stdout.strip())
    commit_result = git("rev-parse", "HEAD")
    commit = commit_result.stdout.decode("utf8", "replace").strip() if commit_result.returncode == 0 else None

    tracked, untracked = list_files(args.tracked_only)
    entries = tracked + untracked
    if not entries:
        fail("文件清单为空")
    validate_paths(entries)

    temp = GAMES / f".tmp-{args.name}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    baseline_temp = BASELINES / f".tmp-baseline-{args.name}-{os.getpid()}-{uuid.uuid4().hex[:8]}.json"
    if temp.exists() or baseline_temp.exists():
        fail("临时路径冲突，请重试")
    renamed = False
    local_written = False
    try:
        temp.mkdir()
        for entry in entries:
            destination = temp / entry
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / entry, destination)
        local_written = write_local_config(temp, godot)
        if inventory() != source_inventory:
            raise RuntimeError("复制期间骨架源码发生变化")
        payload = {
            "schema": 1,
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "skeleton_commit": commit,
            "skeleton_dirty": dirty,
            "skeleton_source_hash": source_hash,
            "tracked_only": bool(args.tracked_only),
            "file_count": len(entries),
            "included_untracked": sorted(untracked),
        }
        baseline_temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        temp.rename(target)
        renamed = True
        baseline_temp.replace(baseline)
    except Exception as exc:
        if renamed and target.exists():
            shutil.rmtree(target, ignore_errors=True)
        shutil.rmtree(temp, ignore_errors=True)
        baseline_temp.unlink(missing_ok=True)
        fail(f"创建失败，已回滚: {exc}")

    print(f"已创建: {target.relative_to(ROOT).as_posix()}")
    print(f"文件: {len(entries)}（tracked {len(tracked)}，untracked {len(untracked)}）")
    print(f"骨架 commit: {commit or 'unknown'}")
    print(f"骨架 dirty: {dirty}")
    print(f"骨架源码摘要: {source_hash}")
    if untracked:
        print("包含未跟踪文件: " + ", ".join(sorted(untracked)))
    print(f"基线: {baseline.relative_to(ROOT).as_posix()}")
    if godot is not None:
        print("Godot: " + ("已写入目标的 .tools/local.json" if local_written else "未写入目标；请设置 STARTER_GODOT"))
    print("下一步:")
    print(f"  cd {target.relative_to(ROOT).as_posix()}")
    print("  python tools/check_docs.py")
    print("  python tools/check_dependencies.py")
    print("  python tools/dev.py test")


def main() -> None:
    parser = argparse.ArgumentParser(description="在 .tools/sandbox 创建本地派生项目；项目数据不入库")
    subparsers = parser.add_subparsers(dest="command", required=True)
    new_parser = subparsers.add_parser("new", help="从骨架当前工作树创建派生项目")
    new_parser.add_argument("--name", required=True, help="小写 slug，例如 sample")
    new_parser.add_argument("--tracked-only", action="store_true", help="只复制 Git 已跟踪文件")
    new_parser.add_argument("--godot", help="Godot 4.7 console 可执行文件；版本匹配后写入目标的 .tools/local.json")
    args = parser.parse_args()
    if args.command == "new":
        create(args)


if __name__ == "__main__":
    main()
