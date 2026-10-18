# 调参导航

唯一设计参数入口：`StarterTuning` 自定义 Resource（[脚本](../scripts/starter_tuning.gd)），权威基线 [baseline.tres](baseline.tres)，实验 [slow.tres](slow.tres)。在 Godot Inspector 选资源改值，不文本替换已有 `.tres`。来源与有效值见 `StarterMain.diagnostic_snapshot()`；dev 产品探针记录规范 JSON SHA-256。

| 分组／字段 | 用途与单位 | 合法范围／推荐 | 生效／验证 |
| --- | --- | --- | --- |
| 玩法 move_speed | 水平米/秒，增大更快 | 1–10／2–5 | 进程启动，重开沿用；场景移动与墙 |
| 玩法 interaction_reach | 激活距离，米，增大更远 | 0.5–2／1–1.5；必须小于起点目标距离 3 米 | 启动；边界 1.5 与越界反例 |
| 输入 direction_deadzone | 归一化幅度，小输入过滤 | 0–0.5／0.15 | 启动；语义 InputMap |
| 表现 text_size | 正文 UI 像素，增大更易读但占空间 | 16–32／22 | 启动；实例 Theme 副本；需复核实际布局 |
| 工程 diagnostic_capacity | 内存事件最大条数，非平衡参数 | 8–128／32 | 启动；容量和丢弃计数测试 |

Resource 导出范围只是 Inspector 提示，运行仍执行完整校验；非法、非有限或缺失配置明确失败，不静默回退。共享 Resource 是定义，不存暂停／分数／位置／冷却等实例状态。读取值投影后本局冻结，不热重载。

体验基线：`python tools/dev.py run`。慢速实验：直接运行 dev 导出包 `starter.exe -- --preset slow`，或用 Godot `--path . -- --preset slow`；去掉参数恢复基线。只支持显式 slow，不扫描未知本地覆盖，未知或非 dev 预设拒绝。实验不改基线、无玩家设置或存档写入。改参数后重启、`test` 和 `export`，不能复用旧报告。

引擎工程选择在 `project.godot`（Compatibility、960×640）；实体几何为示例结构不变量，不伪装成安全滑杆。未来确认性能预算后独立测量，不以截图耗时作 GPU／帧率结论。玩家设置将来独立保存，不能反写设计基线。
