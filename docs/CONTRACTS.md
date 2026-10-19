# 模块契约与验证

原则见 [架构指南](guides/game-architecture.md)，新模块可按 [契约模板](contracts/module-template.md) 记录；此处登记当前默认接法，不重复通用规范。

## 模块与依赖

| 模块 | 所有权／输入输出 | 允许依赖 |
| --- | --- | --- |
| `RoundRules` | 回合规则、显式秒数／距离请求、Result／值视图／激活事实 | RefCounted、标量与容器；不读 Node、Input、文件或墙钟 |
| `StarterSession`／`StarterMain2D`／`StarterMain` | 共用参数投影、语义请求、生命周期；具体 main 负责对应空间观测和接线 | 规则、物理、表现、Resource 与平台适配；不统一两种物理 |
| `StarterPlayer2D`／`StarterPlayer` | CharacterBody2D／CharacterBody3D 位置和速度，消费方向与速度 | Godot 物理；不实现交互规则或 UI |
| `StarterUI`／两路线 Presentation | 借用显示节点，将值视图映射为可见性／文案 | Label、Button；路线适配另借用 Node2D 或 Node3D／Mesh；无规则、玩家或协调器引用 |
| `StarterTuning`／`DiagnosticJournal` | 共享定义与有效值／有界事件副本 | Resource／RefCounted；不保存玩家进度 |
| `ProductProbe` | 显式 dev 探针、只读采样与截图 | 平台／渲染边界；不提供状态写入 |

规则与表现互不引用。表现适配器由协调器创建和持有，借用节点的有效期不超过当前场景，不释放节点、不订阅全局信号；不把协调器作为万能上下文传入。

## 路线与派生

[路线表](ROUTES.md) 是场景和脚本发现入口。`starter-project.json` schema=1、route=template 表示维护双示例，主场景为 2D；派生时须先确认 route=2d／3d，并在编辑器设置对应主场景。它只决定开发工具测试／导出范围，不在运行中改变物理维度；`run --route` 仅临时体验，不更改登记。缺失、未知配置或登记与主场景不一致显式失败。模板验证两路，派生后仅所选路线及公共测试必需；不会自动删除另一条资源。

## 规则／协调／物理

- `RoundRules` 拥有 running、paused、activated 和 elapsed。`interact(distance)` 是请求，Result 表达接受／拒绝，`activated` 信号仅在真实成功时一次发出。越界、重复、暂停与未开始拒绝不改规则状态；负数／非有限时间拒绝；零时间合法。
- `RoundRules.view()` 每次返回独立的标量 Dictionary；修改它不回写规则。字段为 running、paused、activated、elapsed，仅供调用时读取，不是完整保存／恢复载荷。
- 请求返回后协调层记录结果，再向表现投影完整视图。`activated` 在规则提交状态后同步发出，每次成功激活仅一次；表现不依赖事件历史恢复可见性。将来接入一次性反馈时由局部事实驱动，订阅者不得重入规则写入口。
- `StarterSession.request()` 是两个具体 main 继承的玩家、UI、AI 输入与测试共享语义入口。离散动作每帧消费 just_pressed；移动由 InputMap 持续状态驱动。场景只计算观测距离，不重复决定激活规则。
- 所选路线的 `CharacterBody2D`／`CharacterBody3D` 唯一拥有物理位置，Godot `move_and_slide()` 与对应 StaticBody 拥有碰撞；2D 使用 FLOATING、XY 像素，3D 使用 XZ 米，两者均无重力。2D 玩家为碰撞层 1／掩码 2，边界为层 2／掩码 1；目标只显示，不维护第二套区域交互状态。规则不保存坐标。`_physics_process(delta)` 使用引擎时间，不另造固定步累加器。
- 初始标题隐藏世界且不推进规则；进入／重开重置回合和物理对象。暂停令 SceneTree.paused=true；主协调与 UI ALWAYS，世界 PAUSABLE，规则时间不推进。继续不补暂停时间。重开复用同一个世界，不堆旧实例。失焦自动暂停／休眠策略后置，不能声称已覆盖。

## 表现边界与时序

两路线的 `present(view)` 委托 `StarterUI` 投影通用 UI，只读取值视图，设置世界／目标／按钮可见性和提示文字。不修改输入、SceneTree.paused、物理位置／速度、规则时间、参数或诊断，也不读取文件。相同视图重复调用得到相同显示；隐藏目标依据 activated 状态，不依赖曾经收到激活事件。显示节点是输出，不是玩法真值。

离散输入在 `_process` 中按 start／interact、pause／continue、restart 的既有次序消费；UI 持久信号直接调用同一请求入口。交互读取调用当时两个节点的本地距离（同父节点），不等待后续物理步。`_physics_process` 更新持续方向并传递显式 delta，玩家物理回调负责运动；不声称离散输入与同帧物理结果同步。表现仅在初始化及请求结果之后刷新，不另设规则时钟。

扩展时先明确输入、物理观测和规则结果的顺序，不引入第二套调度。改变回调时机或规则入口须同步测试，不用可见性反推业务状态。

## 参数与诊断

随包自定义 Resource 是定义，route 必须与场景匹配，单位不隐式换算；启动一次校验、投影独立 Dictionary。重开沿用本次有效值，不修改共享 Resource；Theme 为每实例副本，只调整字号，字体不覆盖，直接由 Godot 内置默认字体（ThemeDB.fallback_font）提供。无需额外字体文件、下载或剪裁；缺字使用引擎原生回退，跨设备覆盖未验证。基线和 slow 实验预设分离，玩家设置没有实现。具体单位／范围／时机见 [tuning](../tuning/README.md)。

诊断投影 schema=2，含 route、position_space=world_local、distance_unit=px／m 及 2／3 分量 position；仅供观测，不是存档。截图点为 viewport 像素，2D 通过 `get_global_transform_with_canvas()`，3D 通过 `Camera3D.unproject_position()`；探针不再猜测维度。构建身份含路线与主场景，平台预期来自 `tools/routes.py`，不以产品自报值决定验收范围。

诊断仅白名单 code/result/sequence 的有界内存事件；snapshot 深复制，记录丢弃计数、有效参数、来源和 SHA-256。无路径／账号／自由文本上传，无落盘轮转或崩溃留存。dev 显式 `--probe-directory` 才采样工作产物；不开放任意状态注入，最多 60 秒／8 张图。

## 分层验证

1. **unit**：RefCounted 规则、参数校验、有界诊断；Godot 无头，仍依赖 Godot 引擎，不创建窗口／音频。无随机规则，随机测试当前不适用。
2. **scene**：两路线各自 GdUnit4 scene_runner 及公共路线／主场景一致性；磁盘加载、owner、脚本／资源、持久信号、引擎帧推进、真实规则状态、物理墙、重复呈现无玩法副作用及值视图隔离。保存至隔离 user:// 后 CACHE_MODE_IGNORE 重载。语义动作模拟不是 OS／物理设备证明。
3. **negative**：隔离项目构造失败、解析、加载、挂起、零测／零筛选、跳过和报告故障，以及未知登记、路线／位置形状／非有限值／参数错配；必须拒绝，保留正例。无重试、无放宽容差。
4. **product**：所选每条路线独立的实际 Windows 导出 dev 包（模板两包）；Win32 SendInput 前台句柄确认、只读探针、进入／移动／激活／暂停／继续／三次重开／正常关闭。PNG 与同帧状态核对局部角色、目标和交互反馈；截图编码不作为性能测量。

统一入口 `python tools/dev.py test|negative|export`。新输出目录、超时终止进程树；JUnit 核对退出码、日志错误、测试清单与数量、失败／错误／跳过／flaky 和新报告。`verify` 只读复核当前源码、证据哈希、重新解析 JUnit 并执行像素判据。必需测试不能跳过；修改预期必须来自新契约或独立推导。测试写法和证据边界见 [测试指南](guides/testing.md)。

`export` 是 dev 闭环，不是防篡改签名／可复现二进制证明／完整自主验证。缺性能目标设备、GPU 预算、长跑、崩溃符号和托管执行；这些不能由无头测试通过推导。无存档与完整恢复；以后启用须版本信封、校验、失败显式与逐步恢复对照，不承诺物理跨端位级一致。
