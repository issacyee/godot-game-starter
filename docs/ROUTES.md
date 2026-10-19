# 选择 2D／3D 路线

模板维护两条路线，直接运行默认进入 2D。**派生游戏必须先确认路线；默认体验不替代设计选择。** 选择发生在开发开始时，不是游戏内模式菜单，也不是运行期无缝切换。

## 入口与边界

| 项目 | 2D（默认体验） | 3D |
| --- | --- | --- |
| 示例场景 | `scenes/main_2d.tscn` | `scenes/main.tscn` |
| 协调／空间观测 | `scripts/main_2d.gd` | `scripts/main.gd` |
| 物理位置所有者 | `StarterPlayer2D`／CharacterBody2D | `StarterPlayer`／CharacterBody3D |
| 运动 | XY 俯视、FLOATING、无重力 | XZ 平面、无重力 |
| 空间单位 | 像素，速度为像素/秒 | 米，速度为米/秒 |
| 表现适配 | `scripts/starter_presentation_2d.gd` | `scripts/starter_presentation.gd` |
| 参数基线／实验 | `tuning/baseline_2d.tres`／`slow_2d.tres` | `tuning/baseline.tres`／`slow.tres` |
| 场景测试 | `tests/scene/main_2d_scene_test.gd` | `tests/scene/main_scene_test.gd` |
| 导出包目录 | `package/` | `package-3d/` |

两者都演示进入、键盘移动、墙碰撞、靠近激活、暂停／继续与重开。共享 `RoundRules`、`StarterSession` 生命周期、`StarterUI`、诊断和工具；各路线独立承担物理、空间观测与投影，不统一 Vector2／Vector3 或复制引擎物理。该接法只是两个示例的局部复用，不是所有派生游戏必须继承的公共框架。

## 体验不改变派生选择

```powershell
python tools/dev.py run             # 使用 project.godot 主场景，模板默认 2D
python tools/dev.py run --route 2d   # 显式体验 2D，不改项目
python tools/dev.py run --route 3d   # 显式体验 3D，不改项目
```

也可在编辑器打开相应场景运行当前场景。原始引擎命令为 `Godot --path . res://scenes/main.tscn`（3D）；导出包不需要运行期选择参数，每个包已有独立主场景。

## 派生时的必要步骤

1. 先与设计者确认 2D 或 3D、视角、移动模型、目标设备和范围；写入 [BRIEF](BRIEF.md)。不要仅因模板默认 2D 就默认确认。
2. 将根目录 `starter-project.json` 的 `route` 从 `template` 改为 `2d` 或 `3d`，保留 `schema: 1`。这是开发工具的路线登记，不是玩家设置或运行状态。
3. 在 Godot 项目设置中把主场景设为所选示例；用 Godot AI 时使用 `project_manage set_main_scene`。同步主场景与路线登记，测试拒绝不一致。
4. 按上表替换所选路线玩法；共用部分可继续复用，另一条路线可保留作参考，不要求继续适配。默认不自动删除、移动文件或改 UID；需要移除时先检查引用并另行确认。
5. 运行 [验证命令](../README.md)。`template` 会测试并导出两条路线；`2d`／`3d` 只运行所选示例场景测试及公共测试，只导出所选路线。未知或缺失路线显式失败，不能静默回退。`--route` 仅供 run 体验，不能临时缩减 test／export 的验收范围。

`project_route_test.gd` 是公共场景测试；新增公共测试继续自动发现。替换示例后须同步改测试及 `tools/routes.py`、平台动作、探针和像素判据，它们仍然是示例验收，不会自动理解新游戏。保留另一条示例文件意味着引擎可能仍导入／打包它们；单路线选择不承诺物理剔除全部无关资产。

之后变更维度属于迁移：重新确认设计、物理、内容、参数单位、镜头与验收，而不是给现有坐标换类型。完整阶段顺序见 [从零构建游戏](deriving-a-game.md)。

## 首期不包含

默认 2D 不预设像素风，不强制整数缩放或最近邻过滤；基准视口为 960×640，完整窗口／DPI 矩阵未覆盖。横版跳跃、TileMapLayer／TileSet、美术动画、导航、2D 光照与复杂镜头按游戏需求接入，不因支持 2D 就预装。
