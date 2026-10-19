# 故障排查

- **路线不一致／TUNING_INVALID**：核对 `starter-project.json`、项目主场景和所选路线 Resource 的 route／单位。派生选择按 [路线步骤](ROUTES.md)；不能用 `run --route` 代替登记，也不能把 3D 米制参数赋给 2D。
- **引擎版本不匹配**：将 `STARTER_GODOT` 指向锁定版本的标准版 console exe，不使用 Mono 版。工具检查真实 `--version`；环境变量优先于 `.tools/local.json`，不读取 `GODOT_PATH`。
- **AI 无工具／断连**：先运行 `python tools/setup.py ai`，再运行 `python tools/dev.py editor`。等待插件就绪后，用 `.tools/venv/Scripts/python.exe tools/ai.py list` 和 `editor_state` 查询。会话必须指向当前项目，插件与后端版本一致；端口见 `tools/ai-config.json`。不要随意结束其他项目进程，也不要用 Configure all 写全局配置。
- **AI testing 未排除**：实际工具列表不能有 `test_run`／`test_manage`，会话的 `exclude_domains` 必须含 `testing`。配置文件存在不等于已生效。
- **新脚本资源未注册**：调用 `filesystem_manage scan`，检查写操作诊断，再运行新进程测试；没有错误日志不能单独证明脚本有效。
- **资源修改未生效**：核对项目、场景、owner、共享引用和未保存状态，结构化修改并保存后运行 `test`。避免多个进程同时写同一资源。
- **测试失败**：查看输出目录中的 `result.json`、unit／scene 的 `process.log` 和 `reports/report_1/results.xml`。先建立回归再修复，不重试刷绿。negative 的故意失败应由总报告明确判定为拒绝。
- **导出缺模板**：运行 `python tools/setup.py templates`，下载并校验约 1.28 GB 标准归档，仅展开 Windows x86_64 模板。导出使用独立副本，不读取编辑器缓存。
- **OS 验证聚焦失败**：需要未锁屏的 Windows 交互桌面与相同权限；检查时不要同时操作。工具核对前台窗口后才发送按键，不能用 Input.action_press 替代 OS 输入验证。
- **包缺字／画面异常**：检查默认 Theme 与实际包截图。中文缺字可能依赖系统回退字体，需在目标设备复核；有明确需求时再添加经许可的字体。无头结果不证明画面，`platform-2d/`／`platform-3d/` 的截图也不是 GPU 性能证据。
- **报告过期**：文档、工具或其他被盘点源码变化都会使 `verify` 拒绝。重新运行 `export`，不要修改旧报告；SHA-256 关联不是签名。
- **自动化数据混淆**：隔离 profile 位于 `.tools/` 或 `artifacts/`。不要将测试数据当作玩家恢复材料；本模板没有存档、玩家设置或持久日志。

`.pi/extensions/resource-guard.ts` 在受信任的项目会话加载后，拦截直接 write/edit 到 `.tscn`／`.tres`。它不阻止 Shell、任意脚本或其他客户端，只是局部防误写措施，不是安全沙箱。
