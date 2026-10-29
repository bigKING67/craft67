# 成员身份与归属

首次接入只需要名字或团队称呼，例如“67”或“小王”，不要求提供邮箱。先运行 `doctor --local`，它读取当前项目生效的 Git `user.name`（可继承已有全局配置），在 `member.name` 中显示；已有名字不重复询问。缺失或空白时返回 `attention_required` 和 `configure_member_name`，Agent 据此询问称呼。只读阅读、分析可以继续，身份设置列为待办。

日常入口 `resume` 同样返回当前 `member`；尚未选择任务、任务记录缺失和正常接手时都检查名字，缺失时在 `next_actions` 中提示 `configure_member_name`。它保留原任务状态与查看能力，不因缺名字阻塞只读操作，也不联网或写配置。

下面的 `git config --local` 会写当前 clone 的本地配置，在首次身份配置已获授权时执行。只保存用户提供的名字，不替其他成员设置，不修改全局配置；TWC 不另建成员名单，也不在安装时自动修改身份。

```sh
# 在成员自己的 clone 内执行，使用本人提供的名字或称呼。
git config --local user.name "67"
python3 <skill>/scripts/twc.py --project <repo> doctor --local
```

首次称呼核对不证明 Git 提交身份完整或平台账号已认证。实际提交或正式交接时才核对完整身份，优先使用已有 Git 配置；必要的只读查询为 `git config --get user.name` 和 `git config --get user.email`。缺失或不符时报告现状，将修正列为写入待办，不编造邮箱，也不将邮箱补齐前置到首次使用。

每位成员使用个人平台账号，显示名可用真实姓名或团队认识的中文名；账号 ID 和当前 login 用于关联平台记录。CNB 原始字段 username/nickname 在 TWC 中显示为 login/full_name。组织名、个人账号和人名分别记录；例如组织 bql_huayue、负责人 sixseven 与该负责人的平台账号可以有不同名称。Token 属于个人，不能共用负责人账号。

TWC 只读取身份，不修改 Git 配置。在平台读取已获授权时运行 `doctor --online`，核对 `actor.platform.data.login` 是本人、`actor.git.author/committer` 符合预期；Git 姓名可以是中文，不要求与 login 相同。完整诊断读取有效的 Git author/committer（含环境变量覆盖），拒绝用操作系统名/主机名猜测缺失身份。首次预检的 `member.name` 只是配置的称呼，不替代这些有效提交身份。它们是后续提交的默认身份，实际提交作者仍以 Git 提交对象为准。[Git var](https://git-scm.com/docs/git-var)

| 事实 | 来源与用途 |
| --- | --- |
| 任务负责人 | 平台 Issue 分配；准备或执行任务不自动取得负责人身份 |
| 当前执行者 | 本次 `/user` 返回的实例、账号 ID、login、显示名与观察时间 |
| 提交作者 / committer | Git 提交对象；本地有效身份只能说明当前配置，不能替代历史作者 |
| PR 创建者 / 实际合并者 | 平台 PR 与合并记录，不能从分支名或 Git author 推断 |
| 集成负责人 | 任务契约 `integrator` 指定平台账号（可附人名）；实际合并权限由服务器控制 |

## 命令副作用与准备示例

| 命令 | 本地写入 | TWC 发起的平台请求 |
| --- | --- | --- |
| `resume`、`check`、`doctor --local` | 无 | 无 |
| `doctor --online` | 无，不写 packet 或绑定 | 读取平台身份、仓库等诊断信息 |
| `prepare --task …`（含 `--rebind`） | 任务记录、packet 与绑定 | 默认读取平台任务与当前身份；没有 `--online` 参数 |
| `prepare --task … --offline`（可加 `--rebind`） | 同上 | 无；平台事实保留未知 |
| `verify` | 无，仅预览 | 无 |
| `verify --execute --approved-policy …` | 验证记录与证据摘要；项目命令还可能写其他资源 | 加 `--online` 才读取当前平台身份；项目命令自身可能联网，不受此开关限制 |
| `handoff --draft …` | 交接文件 | 加 `--online` 才刷新平台事实与当前身份 |

仅在准备或重绑已获授权时使用下列示例；用实际任务编号和契约路径替换占位值。离线准备仍是写操作，`--offline` 不提供只读模式。

```sh
# 已审阅任务切换，仅在本地重绑；不读取平台。
python3 <skill>/scripts/twc.py --project <repo> prepare --task pr:N --contract <path> --rebind --offline
# 已获平台读取及本地准备授权；默认联网，不添加 --online。
python3 <skill>/scripts/twc.py --project <repo> prepare --task pr:N --contract <path>
```

交接保留准备者、每份证据的执行者和当前交接者，换人接手不会沿用上一人的身份。联网身份读取只保留账号 ID、login 和显示名，不复制 `/user` 其他私密资料。

新身份快照用 `member` 保存当时的名字、来源和 `self_asserted` 标记；任务记录的 `recorded_by`、验证记录的 `actor`、交接的 `prepared_by`/`actor` 分别保留各自称呼。只有名字、没有邮箱时仍能记录。离线交接会显示 `67 (self-reported name; platform identity unverified)`；平台已核验时同时显示账号 login 与自报称呼。旧记录没有称呼时保持未知，不从接手者配置补写；未变的任务契约不因重新 prepare 改写原准备者。检查执行中称呼发生变化会令证据变为 `incomplete`，需要核对后重验。

离线或身份读取失败仍可记录真实检查结果，但平台身份为未知，不借用旧缓存、任务 assignee、分支前缀或 Git 姓名补全。旧证据缺少 actor 时也标未知；缺当前交接者或验证执行者时不会给出 `advisory_ready`。本地身份观察、JSON 和哈希都不是防伪证明；正式审查仍依据平台账号、推送/PR 记录与受控 CI。

Git HTTPS 推送凭据与 TWC 的只读 Token 是两套凭据，都应属于本人；读取 `/user` 不能证明随后一次 Git push 使用了同一个账号。若两个身份不符，先修正个人凭据配置，不共享管理员 Token。TWC 不保存另一份成员名单或 owner 数据库。

建议短分支如 `feat/alice/42-material-search`：前缀便于识别，不构成权限或归属证明。成员将自己的任务分支推到团队仓库并提 PR，指定负责人核对最新基线、独立审批和验证后串行合并。负责人自己开发的 PR 同样需要另一位合适成员审查，不通过自批或管理员跳过替代。
