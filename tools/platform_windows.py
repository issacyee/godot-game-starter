"""通过 Win32 SendInput 验证实际导出 dev 包；只读探针，不注入权威状态。"""
import hashlib
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time
from dev import isolated_env, write_json

user32 = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None


def read_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return {}


def wait_state(path: Path, condition, timeout=8) -> dict:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        state = read_state(path)
        if state and condition(state):
            return state
        time.sleep(0.025)  # 仅有界轮询外部进程；游戏测试推进不使用 sleep。
    raise RuntimeError(f"实际产物状态超时: {read_state(path)}")


def key(vk: int, down: bool) -> None:
    pointer = wintypes.WPARAM
    class Mouse(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("data", wintypes.DWORD), ("flags", wintypes.DWORD), ("time", wintypes.DWORD), ("extra", pointer)]
    class Keyboard(ctypes.Structure):
        _fields_ = [("vk", wintypes.WORD), ("scan", wintypes.WORD), ("flags", wintypes.DWORD), ("time", wintypes.DWORD), ("extra", pointer)]
    class Union(ctypes.Union):
        _fields_ = [("mi", Mouse), ("ki", Keyboard)]
    class Input(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", Union)]
    event = Input(type=1, ki=Keyboard(vk=vk, flags=0 if down else 2))
    if user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) != 1:
        raise RuntimeError("OS SendInput 失败；需要交互桌面")


def validate_platform(report: dict) -> None:
    required = {"title", "start", "move", "interact", "pause", "continue", "restart-0", "restart-1", "restart-2"}
    actions = report["actions"]
    if {a["id"] for a in actions} != required or len(actions) != len(required) or report["exit_code"] != 0:
        raise RuntimeError("平台动作或退出证据不完整")
    by_id = {a["id"]: a["state"] for a in actions}
    if by_id["title"]["state"]["running"] or not by_id["start"]["state"]["running"]:
        raise RuntimeError("标题／进入状态错误")
    if not 1.8 <= by_id["move"]["position"][0] < 4.0 or by_id["move"]["state"]["activated"]:
        raise RuntimeError("OS 移动结果错误")
    if not by_id["interact"]["state"]["activated"] or not by_id["pause"]["state"]["paused"] or by_id["continue"]["state"]["paused"]:
        raise RuntimeError("交互／暂停／继续结果错误")
    before, after = report["pause_observation"]
    if after["sequence"] < before["sequence"] + 8 or before["position"] != after["position"] or before["state"]["elapsed"] != after["state"]["elapsed"]:
        raise RuntimeError("暂停冻结证据不足")
    if by_id["continue"]["state"]["elapsed"] <= after["state"]["elapsed"]:
        raise RuntimeError("继续后规则未推进")
    previous = -1
    for action in actions:
        state = action["state"]
        if state["sequence"] <= previous:
            raise RuntimeError("平台证据序号未递增")
        previous = state["sequence"]
        if state["parameters"] != {"diagnostic_capacity":32,"direction_deadzone":0.15,"interaction_reach":1.5,"move_speed":4.0,"text_size":22}:
            raise RuntimeError("实际有效参数与已验证基线不符")
        if state["parameter_source"] != "res://tuning/baseline.tres":
            raise RuntimeError("参数来源不符")
        if action["id"].startswith("restart-") and (state["position"] != [0,0.5,0] or state["state"]["activated"] or state["state"]["paused"]):
            raise RuntimeError("重开未清理旧局")


def exercise(exe: Path, out: Path) -> dict:
    if os.name != "nt":
        raise RuntimeError("当前真实输入适配器只支持 Windows 交互桌面")
    out.mkdir()
    state_file = out / "state.json"
    env = isolated_env(out / "profile")
    log = (out / "product.log").open("w", encoding="utf8")
    proc = subprocess.Popen([str(exe), "--", "--probe-directory", str(out)], cwd=exe.parent, env=env, stdout=log, stderr=subprocess.STDOUT)
    hwnd = None
    actions = []
    held = set()
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    previous = user32.GetForegroundWindow()
    try:
        state = wait_state(state_file, lambda s: s.get("sequence", 0) > 2)
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        windows = []
        @callback_type
        def enum(window, _):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
            if pid.value == proc.pid and user32.IsWindowVisible(window):
                windows.append(window)
            return True
        user32.EnumWindows(enum, 0)
        if not windows:
            raise RuntimeError("找不到实际导出窗口")
        hwnd = windows[0]
        foreground = user32.GetForegroundWindow()
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        current_thread = kernel32.GetCurrentThreadId()
        foreground_thread = user32.GetWindowThreadProcessId(foreground, None)
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
        attached = []
        try:
            for thread in {foreground_thread, target_thread} - {current_thread, 0}:
                if user32.AttachThreadInput(current_thread, thread, True):
                    attached.append(thread)
            user32.ShowWindow(hwnd, 9)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            for thread in attached:
                user32.AttachThreadInput(current_thread, thread, False)
        # 等待真实前台句柄与游戏焦点同时成立，不能信任启动瞬间的旧探针。
        deadline = time.monotonic() + 3
        while user32.GetForegroundWindow() != hwnd and time.monotonic() < deadline:
            time.sleep(0.025)
        if user32.GetForegroundWindow() != hwnd:
            raise RuntimeError(f"Windows 不允许聚焦实际产物: expected={hwnd}, foreground={user32.GetForegroundWindow()}")
        wait_state(state_file, lambda s: s.get("focused") is True)
        def record(name, state):
            actions.append({"id": name, "state": state})
        def press(vk):
            if user32.GetForegroundWindow() != hwnd:
                raise RuntimeError("游戏不是前台；拒绝向其它窗口发键")
            seq = wait_state(state_file, lambda s: isinstance(s.get("sequence"), int))["sequence"]
            key(vk, True); held.add(vk)
            wait_state(state_file, lambda s: s["sequence"] >= seq + 3)
            key(vk, False); held.discard(vk)
        def capture(number):
            press(0x77)  # F8：只读帧缓冲捕获。
            wait_state(state_file, lambda s: s["captures"] >= number)
        record("title", state)
        press(13)
        state = wait_state(state_file, lambda s: s["state"]["running"])
        capture(1)
        record("start", state)
        key(0x44, True); held.add(0x44)
        state = wait_state(state_file, lambda s: 1.8 <= s["position"][0] < 4.0)
        key(0x44, False); held.remove(0x44)
        record("move", state)
        press(13)
        state = wait_state(state_file, lambda s: s["state"]["activated"])
        capture(2)
        record("interact", state)
        press(27)
        paused = wait_state(state_file, lambda s: s["state"]["paused"])
        key(0x44, True); held.add(0x44)
        later = wait_state(state_file, lambda s: s["sequence"] >= paused["sequence"] + 8)
        key(0x44, False); held.remove(0x44)
        if paused["position"] != later["position"] or paused["state"]["elapsed"] != later["state"]["elapsed"]:
            raise RuntimeError("暂停期间状态推进")
        capture(3)
        record("pause", later)
        press(27)
        state = wait_state(state_file, lambda s: not s["state"]["paused"] and s["state"]["elapsed"] > later["state"]["elapsed"])
        record("continue", state)
        for index in range(3):
            press(27)
            wait_state(state_file, lambda s: s["state"]["paused"])
            press(0x52)
            state = wait_state(state_file, lambda s: not s["state"]["paused"] and not s["state"]["activated"] and s["position"] == [0, 0.5, 0])
            record(f"restart-{index}", state)
        # 正常关闭，不把强杀当退出验收。
        user32.PostMessageW(hwnd, 0x0010, 0, 0)
        code = proc.wait(timeout=8)
        if code != 0:
            raise RuntimeError(f"产物异常退出: {code}")
        report = {"passed": True, "input": "Windows SendInput", "actions": actions, "pause_observation": [paused, later], "exit_code": code}
        validate_platform(report)
        write_json(out / "platform.json", report)
        return report
    finally:
        for vk in held:
            key(vk, False)
        if proc.poll() is None:
            proc.terminate(); proc.wait(timeout=8)
        if previous:
            user32.SetForegroundWindow(previous)
        log.close()
