# 成员身份与归属

每位成员使用个人平台账号，显示名可用真实姓名或团队认识的中文名；账号 ID 和当前 login 用于关联平台记录。CNB 原始字段 username/nickname 在 TWC 中显示为 login/full_name。组织名、个人账号和人名分别记录；例如组织 bql_huayue、负责人 sixseven 与该负责人的平台账号可以有不同名称。首次在自己的 clone 配置 Git 身份即可，不必每个任务重新填名字。Token 属于个人，不能共用负责人账号。

```sh
# 在成员自己的 clone 内执行，使用本人姓名和已关联平台的邮箱。
git config --local user.name "成员姓名"
git config --local user.email "成员自己的邮箱"
python3 <skill>/scripts/twc.py --project <repo> doctor --online
```

TWC 只读取身份，不修改 Git 配置。核对 doctor 的 `actor.platform.data.login` 是本人、`actor.git.author/committer` 符合预期；Git 姓名可以是中文，不要求与 login 相同。工具读取有效的 Git author/committer（含环境变量覆盖），拒绝用操作系统名/主机名猜测缺失身份。它们是后续提交的默认身份，实际提交作者仍以 Git 提交对象为准。[Git var](https://git-scm.com/docs/git-var)

| 事实 | 来源与用途 |
| --- | --- |
| 任务负责人 | 平台 Issue 分配；准备或执行任务不自动取得负责人身份 |
| 当前执行者 | 本次 `/user` 返回的实例、账号 ID、login、显示名与观察时间 |
| 提交作者 / committer | Git 提交对象；本地有效身份只能说明当前配置，不能替代历史作者 |
| PR 创建者 / 实际合并者 | 平台 PR 与合并记录，不能从分支名或 Git author 推断 |
| 集成负责人 | 任务契约 `integrator` 指定平台账号（可附人名）；实际合并权限由服务器控制 |

`prepare` 默认联网记录准备者；`verify --execute ... --online` 在检查前读取本次执行者；`handoff --online` 再读取本次交接者。交接保留准备者、每份证据的执行者和当前交接者，换人接手不会沿用上一人的身份。联网读取只保留账号 ID、login 和显示名，不复制 `/user` 其他私密资料。

离线或身份读取失败仍可记录真实检查结果，但平台身份为未知，不借用旧缓存、任务 assignee、分支前缀或 Git 姓名补全。旧证据缺少 actor 时也标未知；缺当前交接者或验证执行者时不会给出 `advisory_ready`。本地身份观察、JSON 和哈希都不是防伪证明；正式审查仍依据平台账号、推送/PR 记录与受控 CI。

Git HTTPS 推送凭据与 TWC 的只读 Token 是两套凭据，都应属于本人；读取 `/user` 不能证明随后一次 Git push 使用了同一个账号。若两个身份不符，先修正个人凭据配置，不共享管理员 Token。TWC 不保存另一份成员名单或 owner 数据库。

建议短分支如 `feat/alice/42-material-search`：前缀便于识别，不构成权限或归属证明。成员将自己的任务分支推到团队仓库并提 PR，指定负责人核对最新基线、独立审批和验证后串行合并。负责人自己开发的 PR 同样需要另一位合适成员审查，不通过自批或管理员跳过替代。
