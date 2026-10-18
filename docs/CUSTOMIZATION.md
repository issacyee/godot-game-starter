# 模板定制

本页列出具体修改入口；从需求到交付的顺序与闸门见 [从零构建游戏](deriving-a-game.md)，日常任务按 [工作流](workflow.md) 进行。

## 1. 建立项目身份

- 复制源码、插件、资源、文档与许可，不携带 `.tools/`、`.godot/` 或 `artifacts/`。
- 在 Godot 项目设置中修改 `application/config/name` 和 `application/config/custom_user_dir_name`，避免多个项目共用用户目录。
- 更新 [BRIEF](BRIEF.md) 的核心体验与目标平台，按 [CAPABILITIES](CAPABILITIES.md) 选择所需能力。
- 按 [README](../README.md) 配置 `STARTER_GODOT`；使用 AI 或导出时安装对应开发依赖。

## 2. 替换示例

| 内容 | 修改入口 |
| --- | --- |
| 激活规则与回合状态 | `scripts/round_rules.gd`、`tests/unit/round_rules_test.gd` |
| 语义动作与生命周期 | `scripts/main.gd`、`tests/scene/main_scene_test.gd` |
| 只读表现投影 | `scripts/starter_presentation.gd`；只借用显示节点，不修改规则／物理 |
| 物理移动 | `scripts/player.gd`；位置保持由 CharacterBody3D 管理 |
| 场景与界面资源 | 在 Godot 编辑器中修改 `scenes/main.tscn`、`assets/interface.tres` |
| 设计参数 | [tuning/README.md](../tuning/README.md)；Inspector 编辑 Resource |
| 输入与显示设置 | Godot 项目设置中的 InputMap 与 Display |
| 导出身份与平台检查 | `tools/delivery.py`、`tools/platform_windows.py`、`tools/visual.py` |

修改场景或资源前检查未保存状态与共享引用；结构化修改、明确保存后用新进程重载。修改玩法、几何、参数或显示时，同步调整对应契约、测试与产品检查，不保留只适用于示例的判据。扩写时沿用 [规则／协调／物理／表现边界](guides/game-architecture.md)，重要模块用 [契约模板](contracts/module-template.md) 明确语义；不要因新增页面再存一份规则状态。

## 3. 验证与交接

```powershell
python tools/check_docs.py
python tools/dev.py test
python tools/dev.py negative
python tools/dev.py export
$delivery = (Get-Content artifacts/latest-export.json | ConvertFrom-Json).directory
python tools/dev.py verify $delivery
```

`export` 需要 Godot AI 编辑器连接、匹配的导出模板与 Windows 交互桌面。新增平台或正式发布流程需建立对应验证，不复用示例的通过记录。

保留 MIT 版权声明和适用的第三方许可；新增素材或依赖时更新 [许可说明](LICENSES.md) 及相应锁文件。
