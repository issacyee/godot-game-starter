# 能力清单

本表描述模板包含的实现，不代表目标设备已通过验证。验证方法见 [CONTRACTS](CONTRACTS.md)，限制见 [STATUS](STATUS.md)。

## 已包含

| 能力 | 实现／入口 |
| --- | --- |
| 开发与审查约定 | [工作流](workflow.md)、[阶段路径](deriving-a-game.md)、[编码](guides/clean-code.md)、[架构](guides/game-architecture.md) |
| 规则与状态所有权 | `RoundRules` 负责规则，`CharacterBody3D` 唯一拥有位置 |
| 逻辑／表现分离 | `StarterMain` 协调，`StarterPresentation` 只读投影；重复呈现／视图隔离回归 |
| 3D、键盘、UI、生命周期 | Camera3D、InputMap、Control/Container、SceneTree 暂停 |
| 结构化资源编辑 | Godot AI；`tools/ai.py`；排除 testing、关闭遥测 |
| 集中调参与实验预设 | Resource、Inspector、独立有效值；[调参导航](../tuning/README.md) |
| 单元与场景测试 | GdUnit4，新进程及隔离用户目录；`tools/dev.py test` |
| 失败判定与产物复核 | `negative`、`export`、`verify`；源码／产品／证据 SHA-256 |
| 简体中文界面 | Godot 内置默认字体与原生回退，不附加字体文件 |
| 有界内存诊断 | `DiagnosticJournal`；白名单事件、深复制、参数身份，不上传 |
| Windows dev 导出 | 嵌入构建身份、许可盘点、OS 键盘与局部像素检查 |
| CI 配置 | `.github/workflows/tests.yml`；无设备测试与负向检查 |

## 按需扩展

其他平台、手柄／触摸／重绑、玩家设置、存档／完整快照、音频、动画、粒子、导航、多语言、性能预算、持久日志、崩溃留存和正式签名发行均未实现。

扩展前明确需求、状态所有权和验证方式；设置与进度分开，字体与素材补充来源和许可，性能在目标设备独立测量。

## 默认不引入

- C#／.NET；测试不使用 McpTestSuite 或 Godot AI testing。
- ECS、服务容器、全局事件总线、对象池或跨游戏框架。
- 没有使用者的字体工具链、随机规则和确定性回放系统。
