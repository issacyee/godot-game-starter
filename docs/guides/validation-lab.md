# 本地派生验证沙盒

用于在完整派生项目中验证骨架的实际效果，并把通用修复、特性和测试回流到骨架。工具和流程随骨架共享；具体测试项目及原始记录留在本机，不入库。

## 共享与本地

| 内容 | 位置 | 是否入库 |
| --- | --- | --- |
| 派生工具 | `tools/lab.py` | 是 |
| 工作流文档 | `docs/guides/validation-lab.md` | 是 |
| 派生项目 | `.tools/sandbox/games/<name>/` | 否 |
| 基线元数据 | `.tools/sandbox/baselines/<name>.json` | 否 |
| 问题记录 | `.tools/sandbox/findings/` | 否 |
| 回流补丁 | `.tools/sandbox/patches/` | 否 |
| 本机 Godot 路径 | 派生项目的 `.tools/local.json` | 否 |

骨架只知道一个通用的本地沙盒目录，不知道其中有哪些项目。项目名、业务内容、玩家数据、本机路径和验收记录不得写进共享文件。

## 目录

```text
.tools/sandbox/
├─ games/<name>/       # 完整骨架副本，可在其中独立运行工具和测试
├─ baselines/          # 派生时的骨架 commit、源码摘要和未跟踪文件清单
├─ findings/           # 本地问题记录
└─ patches/            # 从派生项目导出的补丁
```

`.tools/` 已被 Git 忽略，并被 `tools/dev.py` 的源码哈希、测试 staging、build 和导出流程排除。`tools/lab.py` 在写盘前会再次检查这些边界；任何一项不成立都会拒绝创建。

## 创建项目

在骨架根目录执行：

```powershell
python tools/lab.py new --name <name> --godot "<Godot 4.7 console exe>"
```

- `--name` 使用小写 slug（如 `sample`、`arena-test`），不能重复。
- 默认复制当前工作树中所有已跟踪文件，加上未跟踪但未被忽略的文件；未提交的骨架修改也会进入副本。
- `--tracked-only` 只复制已跟踪文件，用于更干净的基线。
- `--godot` 校验版本为 `4.7.stable.official.5b4e0cb0f` 后，写入派生项目的 `.tools/local.json`；该文件被派生项目自身 `.gitignore` 忽略。不传时请在派生项目中设置 `STARTER_GODOT`。
- 复制通过临时目录和原子重命名完成；失败会回滚，不留下半成品。
- 基线与项目分开保存；重复名称会被拒绝。

## 首次定制

每个真实游戏项目至少先做：

1. 修改 Godot 项目设置中的 `application/config/name` 和 `application/config/custom_user_dir_name`，避免多个测试项目共用 `user://`。
2. 更新项目自己的 `docs/BRIEF.md`、`docs/STATUS.md` 和 `README.md`。
3. 按 [模板定制](../CUSTOMIZATION.md) 替换示例玩法、场景、资源、调参和测试。
4. 需要版本历史时在派生项目内自行 `git init`；`tools/lab.py` 不自动提交。

未修改的派生项目适合做对照基线，不代表真实游戏。

## 验证

在派生项目根目录执行：

```powershell
python tools/check_docs.py
python tools/check_dependencies.py
python tools/dev.py test
```

涉及实际产物时再按范围运行 `build`、`prove`、`export`，并用 `verify <目录>` 只读复核。失败、过期、必需跳过、零测试或证据缺失都不能算完成。

## 回流

1. 在派生项目中复现问题，留下失败回归或最小复现，记录基线 commit 和源码摘要。
2. 把改动拆成 `core:`（通用骨架修复/特性）和 `game:`（仅属于该游戏）两类提交。
3. 从派生项目导出补丁：

```powershell
git -C .tools/sandbox/games/<name> format-patch -1 <sha> -o "$PWD/.tools/sandbox/patches"
# 或按路径导出
git -C .tools/sandbox/games/<name> diff --output=".tools/sandbox/patches/<date>-<slug>.patch" skeleton-base..HEAD -- <paths>
```

4. 在骨架中先只读检查补丁：

```powershell
git apply --check .tools/sandbox/patches/<file>
git apply --stat .tools/sandbox/patches/<file>
```

   逐块审查，确认没有项目名、玩家数据、本机路径、密码或只对某个游戏成立的常量。无法确认通用性时不用补丁，改为手工重写。

5. 应用到骨架并验证：

```powershell
git apply --3way .tools/sandbox/patches/<file>
python tools/check_docs.py
python tools/dev.py test
python tools/dev.py negative
```

   按改动范围补跑 `build`、`prove` 或 `export`。冲突手工解决，不强制覆盖。

6. 把同一补丁同步到其他派生项目并重跑其测试；至少一个派生项目重新验证后，回流才算闭环。
7. 在 `.tools/sandbox/findings/YYYY-MM-DD-<slug>.md` 记录项目、基线、复现、根因、骨架修复、派生验证、其他项目回归和未覆盖风险。

只属于某个游戏的内容留在该游戏项目内，不进入骨架。通用修复以代码、测试和文档进入骨架后，才会随 Git 共享。

## 换机器与恢复

新机器只需克隆骨架并重新创建本地沙盒：

```powershell
git clone <repo>
cd <repo>
python tools/setup.py ai          # 使用 Godot AI 时按需
python tools/lab.py new --name <name>
```

- 工具和流程来自 Git，不需要重写。
- 派生项目、baseline 和原始 findings／patches 不在 Git 中；需要保留时另行备份 `.tools/sandbox/` 的对应内容，或把通用结论固化为骨架代码、测试和文档。
- 本机 Godot 路径由 `--godot` 或 `STARTER_GODOT` 重新提供，不写入共享文件。
- 未修改的派生项目可以按当前骨架重新创建；项目专属改动应从备份恢复或重新应用。

## 边界与风险

- `.tools/` 是本机可丢弃目录；`git clean -xfd`、删除 `.tools` 或重装依赖可能连带删除沙盒。重要项目需另行备份。
- 派生项目完整复制 addons，会占用额外磁盘；不共享 Git 对象库。
- 补丁和 findings 可能含游戏数据或本机信息，只留本地，应用前审查。
- `.tools/local.json` 含本机路径，但位于派生项目忽略目录；禁止 `git add -f` 强制加入。
- 本沙盒不是骨架的测试数据、发布内容或 CI 输入；骨架工具不应扫描或引用具体项目。
- 并发执行按单用户处理；工具使用临时目录和原子重命名，不做跨进程锁。

## 相关文档

- [测试与验证](testing.md)：分层证据和失败判定。
- [模板定制](../CUSTOMIZATION.md)：派生项目要改哪些入口。
- [工作流](../workflow.md)：任务、验证和交付顺序。
- [范围与限制](../STATUS.md)：当前平台和能力边界。
- [tools/lab.py](../../tools/lab.py)：实际派生工具。
