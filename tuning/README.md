# 调参导航

唯一设计参数入口：`StarterTuning` 自定义 Resource（[脚本](../scripts/starter_tuning.gd)）。先按 [路线](../docs/ROUTES.md) 选对应资源，在 Godot Inspector 改值，不文本替换已有 `.tres`。来源、单位与有效值见所选场景的 `diagnostic_snapshot()`；dev 探针记录规范 JSON SHA-256。

| 路线 | 权威基线 | 慢速实验 | 空间约定 |
| --- | --- | --- | --- |
| 2D | [baseline_2d.tres](baseline_2d.tres) | [slow_2d.tres](slow_2d.tres) | XY、本地像素；起点到目标 150 px |
| 3D | [baseline.tres](baseline.tres) | [slow.tres](slow.tres) | XZ、本地米；起点到目标 3 m |

| 分组／字段 | 用途与单位 | 合法范围／推荐 | 生效／验证 |
| --- | --- | --- | --- |
| route | 参数适用路线，不是玩家设置 | 2d／3d；必须匹配场景 | 启动；错配拒绝，不自动换算 |
| 2D move_speed | 像素/秒，增大更快 | 50–500／100–250 | 进程启动，重开沿用；四墙、斜向和实验移动 |
| 2D interaction_reach | 像素，增大更远 | 25–100／50–75；小于起点目标距离 | 启动；实际近距交互 |
| 3D move_speed | 米/秒，增大更快 | 1–10／2–5 | 进程启动，重开沿用；场景移动与墙 |
| 3D interaction_reach | 米，增大更远 | 0.5–2／1–1.5；小于起点目标距离 | 启动；规则边界与越界反例 |
| 输入 direction_deadzone | 归一化幅度，小输入过滤 | 0–0.5／0.15 | 启动；语义 InputMap |
| 表现 text_size | 正文 UI 像素 | 16–32／22 | 启动；实例 Theme 副本；需复核实际布局 |
| 工程 diagnostic_capacity | 内存事件最大条数，非平衡参数 | 8–128／32 | 启动；容量和丢弃计数测试 |

3D 旧资源沿用脚本默认 route=3d，2D 资源显式登记 route=2d；不要把米制参数直接赋给像素场景。运行执行完整校验，非法、非有限、错配或缺失配置明确失败，不静默回退。共享 Resource 是定义，不存暂停／分数／位置／冷却等实例状态。读取值投影后本局冻结，不热重载。

体验基线：`python tools/dev.py run`，3D 使用 `python tools/dev.py run --route 3d`。慢速实验：运行对应 dev 导出包 `starter.exe -- --preset slow`，或 Godot `--path . res://scenes/main_2d.tscn -- --preset slow`（3D 改为 `res://scenes/main.tscn`）。每个场景只加载自己路线的 slow；去掉参数恢复基线。未知或非 dev 预设拒绝，不扫描本地覆盖，不改基线、玩家设置或存档。改参数后重启并同步示例验收预期，运行 `test` 和 `export`，不能复用旧报告。

引擎工程选择在 `project.godot`（Compatibility、960×640）。默认 2D 为固定画布，没有跟随镜头、像素风过滤或整数缩放承诺；实体几何为示例结构不变量，不伪装成安全滑杆。性能在确认预算后独立测量，不以截图耗时作 GPU／帧率结论。玩家设置将来独立保存，不能反写设计基线。
