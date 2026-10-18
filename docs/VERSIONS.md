# 版本与兼容约束

依赖固定到明确版本，不追踪 master/latest。完整来源和哈希见 [dependencies.lock.json](../dependencies.lock.json)。

| 组件 | 版本／依据 | 检查方式 |
| --- | --- | --- |
| Godot 标准版 | `4.7.stable.official.5b4e0cb0f`；[发行页](https://github.com/godotengine/godot-builds/releases/tag/4.7-stable) | 工具运行 `--version`，要求精确匹配 |
| Godot AI | `4.3.0`；[兼容说明](https://github.com/hi-godot/godot-ai/blob/v4.3.0/README.md) 要求 Godot 4.7+ | 插件与后端同版，查询实际会话和工具列表 |
| GdUnit4 | `6.2.2`；[兼容表](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.2/README.md) 的 6.2.x 支持 Godot 4.7 | 独立进程 unit／scene 与负向检查 |
| Python | 推荐 3.13；Godot AI 要求 3.11–3.14 | 项目虚拟环境、锁定依赖、`pip check` |

## 插件与开发依赖

- Godot AI 随库保留 v4 签名发行树；上游签名信任 SPKI 指纹为 `84ebbd811f3a12c09ff4e236bbbbb9310fc23e03fcfc3717ba546747d0d21072`。不修改插件内部文件，使用配置排除 testing、关闭遥测。
- GdUnit4 仅携带 addon，省略可选的 `GdUnit4CSharpApi.cs` 桥；标准引擎无 CSharpScript 时，GDScript loader 会直接返回。
- `python tools/check_dependencies.py` 校验随库插件的完整文件树；升级时需审查发行、许可、省略项及兼容性，再显式更新锁文件。
- Python 后端版本见 [requirements-ai.lock.txt](../tools/requirements-ai.lock.txt)。这是版本锁，不是全平台 wheel 哈希锁；插件签名也不证明全部上游行为安全。

## 导出模板

`python tools/setup.py templates` 下载同版标准发行归档并校验 SHA-256，仅展开 Windows x86_64 的 debug／release 模板至 `.tools/`，不安装全局模板。导出时再次校验模板字节。游戏包不携带 Python、MCP 或 GdUnit4。
