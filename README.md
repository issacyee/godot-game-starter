# Godot 游戏起步模板

面向小团队的小型 3D 项目起点，使用 Godot 4.7 和静态类型 GDScript。游戏运行不依赖 Python、Node 或 .NET。

## 示例体验

进入 → WASD／方向键移动 → 靠近金色目标按 Enter 激活 → Esc 暂停／继续 → R 重开。UI 提供相同操作，关闭窗口退出。

内含规则、物理移动、UI、集中调参、GdUnit4 测试和 Windows dev 导出工具。不包含完整游戏、存档或联网。UI 使用 Godot 内置默认字体，不附带字体文件；中文缺字和跨设备显示需按目标设备检查。

## 环境

| 组件 | 版本 |
| --- | --- |
| Godot 标准版 | `4.7.stable.official.5b4e0cb0f` |
| Godot AI 插件与后端 | `4.3.0`，排除 testing，关闭遥测 |
| GdUnit4 | `6.2.2` |
| 开发脚本 | 推荐 Python 3.13；核心测试仅使用标准库 |

当前工具面向 Windows x86_64、键盘和 Compatibility 渲染。其他平台需另行适配与验证。版本约束见 [VERSIONS](docs/VERSIONS.md)，依赖与哈希见 [dependencies.lock.json](dependencies.lock.json)。

## 首次运行

以下命令在项目根目录的 PowerShell 执行。先安装锁定版本的 Godot 标准版，将环境变量替换为实际路径：

```powershell
$env:STARTER_GODOT = '<Godot 标准版 console.exe 的绝对路径>'
python tools/dev.py run
```

也可用该引擎直接打开 `project.godot`。`STARTER_GODOT` 优先于可选的 `.tools/local.json`（格式：`{"godot":"引擎绝对路径"}`）；工具不读取 `GODOT_PATH`，避免误用其他版本。

需要 Godot AI 或导出时，再显式安装开发依赖：

```powershell
python tools/setup.py ai           # 联网，只安装到 .tools/venv
python tools/setup.py templates    # 联网，下载约 1.28 GB，仅展开 Windows x86_64 标准模板
python tools/dev.py editor         # 使用项目隔离 profile，不改全局客户端配置
```

## 测试与导出

```powershell
python tools/check_docs.py
python tools/dev.py test
python tools/dev.py negative
python tools/dev.py export
$delivery = (Get-Content artifacts/latest-export.json | ConvertFrom-Json).directory
python tools/dev.py verify $delivery
```

- `test`：新 Godot 进程运行 unit／scene 测试，不需要 Godot AI、网络或打开的编辑器。
- `negative`：验证断言、解析、挂起、零测试和报告故障等情况会被拒绝。
- `export`：要求 Godot AI 编辑器已连接；依次执行接入检查、测试、负向检查、实际导出、Windows 键盘和局部像素检查。**需要交互桌面，会暂时聚焦游戏窗口，请勿同时操作。**
- `verify`：只读复核当前源码和完整 export 目录。源码变化后需重新导出，不能沿用旧报告。

产物在 `artifacts/` 的独立目录，失败记录不覆盖。`latest-export.json` 仅用于定位；包内 `package/starter.exe`、`.pck` 和 `licenses/` 应一起保留。当前只生成未签名 dev 包。

## Godot AI

启动编辑器并等待插件连接后：

```powershell
.tools/venv/Scripts/python.exe tools/ai.py list
.tools/venv/Scripts/python.exe tools/ai.py editor_state
```

客户端按项目绝对路径选择唯一会话并固定 `session_id`。修改场景前检查未保存状态，使用结构化工具和明确的 `scene_file`，保存后运行独立测试。端口与排除项在 `tools/ai-config.json`，始终排除 testing；正式测试只使用 GdUnit4。

## 用作新项目

保留源码、插件、资源和许可，不复制 `.tools/`、`.godot/`、`artifacts/`。修改应用名与用户目录，更新简报，替换示例玩法并重新验证。具体修改入口见 [模板定制](docs/CUSTOMIZATION.md)，从目标到交付的阶段路径见 [从零构建游戏](docs/deriving-a-game.md)。

## 开发文档

[文档导航](docs/README.md) · [工作流](docs/workflow.md) · [游戏架构](docs/guides/game-architecture.md) · [编码指南](docs/guides/clean-code.md) · [测试指南](docs/guides/testing.md)

[AI 工作入口](AGENTS.md) · [调参](tuning/README.md) · [模块契约](docs/CONTRACTS.md) · [能力清单](docs/CAPABILITIES.md) · [范围与限制](docs/STATUS.md) · [故障排查](docs/TROUBLESHOOTING.md) · [许可说明](docs/LICENSES.md)
