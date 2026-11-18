# 宿主适配说明

`skills/drama-craft/` 是唯一运行时。适配层只写安装目标、发现方式与限制，不得复制或改写专业规则（铁律、原型库、生成交接）。

## 单一安装原则

- 本机多宿主共用 `~/.agents/skills`，只保留一份 canonical 安装。这与同仓 commerce pack 的 `default_install_root` 一致。
- **不要**再向 `~/.codex/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 复制第二份：副本会漂移，同名 Skill 在不同宿主有不同优先级，出问题时无法判断哪一份生效。
- 统一安装与核对：

```sh
rsync -a --delete packages/drama-craft/skills/drama-craft/ ~/.agents/skills/drama-craft/
diff -r packages/drama-craft/skills/drama-craft ~/.agents/skills/drama-craft
```

- `diff` 为空只说明副本与源码一致，**不说明宿主已加载新内容**。宿主缓存、会话与 project resource 优先级都要另查。
- 本包没有 install provenance、备份目录或自检入口；回退方式是在重装前把目标目录复制到仓库外的临时位置。需要事务化安装时，参照 commerce pack 的 installer，不在这里重造。

## 各宿主的安装与发现

以下全部是**文档级说明**，除 `~/.agents/skills` 的文件一致性做过本机核对，其余宿主的发现与生成质量尚未验证。

| 宿主 | 目标 | 说明 | 验证状态 |
| --- | --- | --- | --- |
| Pi | `~/.agents/skills/drama-craft/` | 用户级 Skill 根自动发现；启动新会话才生效；可 `/skill:drama-craft` 显式调用，或直接提任务 | 发现已验证（2026-11-18 会话技能清单含该路径，用户级）；生成质量未验证 |
| Codex | `~/.agents/skills/drama-craft/` | Codex 发现共享 Agents Skill root 时直接可用；不要另装一份到 `~/.codex/skills` | 发现已验证（2026-11-18，见下方探针记录）；生成质量未验证 |
| Claude Code | `~/.agents/skills/` 或 `~/.claude/skills/` | 取决于宿主版本配置的 Skill 目录；只选一个，不要双装 | 未验证 |
| Cursor | 无原生 Skill 发现 | 把 `SKILL.md` 与本任务需要的 `references/` 作为规则或上下文引入；引用时保留文件路径，避免只贴片段导致铁律与适用范围脱节 | 未验证 |
| 通用（无 Skill 机制的模型） | 任意 | 把 `SKILL.md` 作为系统或任务上下文，按需追加一个 `references/` 文件；references 之间不互相引用，必须显式带上 | 未验证 |

## 已验证的部分（2026-11-18）

只证明"宿主能发现这个 Skill 文件"，不证明生成质量：

- **Codex**：`codex-cli 0.169.1` 的 `app-server` 走 JSON-RPC，`initialize` → `initialized` → `skills/list`（`forceReload: true`）。返回条目为 `name=drama-craft`、`path=/Users/gaoqian/.agents/skills/drama-craft/SKILL.md`、`scope=user`、`enabled=true`、`pluginId=null`。全程零模型调用，不写任何配置。
- **Pi**：本次会话的 Skill 清单里直接出现 `drama-craft` 及上述用户级路径，说明 `~/.agents/skills` 已被发现；是否被任务选中、生成质量如何仍需真实新会话验证。
- **文件一致性**：`diff -r` 源码与安装副本为空。

复验方式：Codex 用同一组 JSON-RPC 方法重新取一次 `skills/list` 并核对 path 与 scope；Pi 开新会话看 Skill 清单。两者都不替代一次真实任务的生成质量对照。

## 未发布状态

- 本包尚未打 tag、未发 Release，也没有 npm 包。任何按分支或本地路径安装的方式都不构成不可变版本，不能写进对外安装文档。
- 发布前需要：打 `<catalog 包名>/v<版本>` 标签、确认宿主安装方式、在真实会话里跑一次生成质量对照（同一 brief 与裸模型对比是否产出 beat、分镜、变量矩阵）。
- 在完成上述步骤前，不得对外声称「已在某宿主验证可用」；静态检查通过只代表结构合规。
