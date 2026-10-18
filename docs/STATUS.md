# 范围与限制

## 模板范围

- 小型 3D 示例：进入、物理移动、近距激活、暂停／继续、重开。
- 静态类型 GDScript、Resource 调参、Godot 默认字体、有界内存诊断。
- Godot AI 结构化编辑、独立 GdUnit4 测试、负向检查、Windows dev 导出与只读复核。

能力入口见 [CAPABILITIES](CAPABILITIES.md)，运行命令见 [README](../README.md)。

## 验证记录

验证结果由使用者在自己的环境生成，不在共享文档中维护机器配置或历史通过记录。`artifacts/` 不入库，也不随模板复制。

- `artifacts/latest-test.json`、`latest-negative.json`、`latest-export.json` 定位相应输出目录；文件仅在对应命令成功时更新，可能仍指向旧结果。
- 完整导出目录含 `result.json`、`delivery.json`、GdUnit4 报告、日志、dev 包和平台检查文件。
- 仅 `passed=true` 且 `python tools/dev.py verify <export目录>` 通过的完整目录可对应当前源码；源码变化后必须重新验证。

## 限制

- 导出与 OS 输入自动化仅提供 Windows x86_64 路径，需要交互桌面；不代表全部 Windows 设备兼容。其他 OS、Web、移动、手柄及完整窗口／DPI 矩阵需另行适配和验证。
- 无头测试不证明像素、音频或 GPU 性能；局部 PNG 判据不等于完整视觉、字形或遮挡检测。默认字体的中文覆盖需在目标设备检查。
- 无存档／完整恢复、失焦自动暂停、休眠恢复、持久日志或崩溃符号化；不承诺物理跨端位级一致。
- dev 包未签名，构建身份与哈希不是防篡改签名或可复现二进制证明。
- CI 的实际结果以对应提交的工作流报告为准，配置存在不代表通过。
- 首次依赖安装需要网络；Python 依赖是版本锁，不是全平台 wheel 哈希锁。
- 资源编辑约定和局部拦截不是 OS 沙箱，不能阻止 Shell 或其他客户端绕过。

## 新项目交接

先更新 [项目简报](BRIEF.md)，选择平台与能力，再按 [模板定制](CUSTOMIZATION.md) 替换示例。后续项目可在本文件记录自身阻塞与下一步；不要将旧产物视为新项目的验证结果。
