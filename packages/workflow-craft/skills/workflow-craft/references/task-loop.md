# 任务循环

`<skill>` 是本次实际加载的目录，不是开发源码路径。需要 Python 3.11+ 和 Git。命令输出 JSON；无需 Hook、子 Agent 或模型凭据。以下 `twc` 指 `python3 <skill>/scripts/twc.py --project <repo>`；Windows 原生可用 `py -3` 或已确认的 `python`，并使用本机虚拟环境的 `Scripts/python.exe`。命令 argv 由项目按实际解释器配置，不把其他机器的绝对路径提交进仓库。

仅查看任务、已有证据或解释状态时，使用 `resume` 和必要的本地只读查询；需要本机预检时用 `doctor --local`。`next_actions` 中的重验、准备或重绑只列为待办，不执行项目检查或写任务记录，也不为核对本地材料自动调用 `--online`。用户要求核对平台时，在已有授权内读取；未刷新平台事实时保留未知。

建议中的命令也按实际副作用区分：`git config --get user.name` 是查询；`git config --local user.name …` 或设置 `user.email` 会写本地配置，`prepare`（含 `--rebind`）会写任务记录与本地绑定，不能列为只读步骤。只读接手时报告身份或绑定问题，将修正列为待办；后续执行沿用已有授权判断。

以下步骤用于已经选择由本工具记录的任务，按当前需要执行；不要求已有其他工作流的项目完整重走。

## 独立任务生命周期（0.5.0+）

仅 `workflow_owner=workflow-craft` 或旧名所有者可用；Trellis 托管项目拒绝生命周期写入。已有 `prepare` 契约不自动加入生命周期，用 `task start --task …` 显式接续即可保留契约与证据。

本节所有命令在 `twc` 后、子命令前加 `--session <稳定会话ID>`，或为当前会话设置 `TWC_SESSION_ID`。可用宿主已有的稳定 ID；没有时生成一次短 ID 并在本会话复用，不要每条命令重建或让多个会话共用。不同 worktree 的绑定独立。新会话先 `task list` 或 `resume --task …` 只读定位；确定接续后 `task start --task …`。显式会话不会继承旧工作区绑定或猜测别的会话正在做哪个任务。普通问答无需创建会话状态。

| 命令 | 行为 |
| --- | --- |
| `task create --task local:<slug> --contract <path> [--parent local:<parent>]` | 从现有契约建立 planning 执行记录并绑定当前会话；父任务必须存在且未完成。平台任务沿用 prepare 的联网语义，可加 --offline |
| `task list` / `resume --task …` | 只读查看关系、契约、证据和历史完成是否仍有效；无需 session |
| `task start [--task …]` | 显式绑定并进入 in_progress；可从暂停/旧契约接续。换分支后需显式 --task 重绑，不改契约、不自动重验 |
| `task pause` | 保存 paused 并清除当前会话绑定，其他会话指针保留；同任务的其他会话会读到暂停状态 |
| `task finish` | 只清除当前会话绑定，不完成、归档或暂停任务 |
| `task complete` | 核对当前契约、全部登记检查、验收和子任务完成依据；有缺口返回未应用，不运行检查、不提交代码 |
| `task archive` | 仅当前完成依据仍有效的 completed 任务可归档；保留目录和记录，不删除文件，同时解除本会话绑定 |
| `task reopen --task …` | 显式重开 completed/archived 任务，保留历史完成依据并建立当前绑定；再按实际变化补验证 |

只有文字验收需要人工判断时，完成命令可带 `--reviewed AC-2 --review-evidence <repo-relative-file>`，多个 ID/材料可重复。材料必须是已有、非空、可提交的实际评审依据；命令记录当前称呼、内容哈希和代码上下文，不认证人类或平台审批。不能用它覆盖失败/过期的自动检查；没有实际评审材料时保留未完成。`resume` 的原始 AC 自动状态仍保留 needs_review，执行记录另显示这份本地评审声明及来源，不称自动验证通过。

父子关系只在子任务保存 parent，父任务子列表从记录派生；不维护两份可冲突的关系。任务记录的 `execution.state` 是历史进度，`execution.completion` 展示当前依据是否仍有效：代码、契约、策略、工具链、评审材料或子任务变化会使完成依据 stale。查看不偷偷改历史状态；重开后再验收。执行完成不要求先 commit，也不表示代码已经可供他人 clone 或允许合并；交接、集成仍走项目门禁。

同工作区的 prepare、生命周期写入、verify 执行和 handoff 通过本地锁串行化，忙时明确拒绝。它不锁编辑器、Git、端口或数据库，也不是任务认领租约；真正并行开发用独立 worktree 和服务资源。写入锁使用 POSIX flock 或 Windows 原生字节锁；Windows 验证命令先加入 Job Object 再执行，残留子进程、超时与取消均不能算通过。Job Object 和 POSIX 进程组都不是恶意代码沙箱，也不跟踪通过外部服务启动的进程。文件以原子替换写入，跨文件创建/绑定不是数据库事务；写入失败后先只读核对已有契约与绑定，再显式接续，不删除历史重来。

## 契约、验证与交接

1. **接续已有记录先 `twc resume`**。它只读，给出当前任务、每条验收条件（AC）的状态、证据是否仍对应当前代码、上次交接的 next、交接之后的提交，以及 `next_actions`。它也读取当前称呼；出现 `configure_member_name` 时只询问名字，不要求邮箱，仍可继续只读查看。`next_actions` 是缺口清单，不是强制执行顺序。接续实现已获授权时，按当前目标和项目规则安排；看到 `verify: …` 保留这些检查为待验，不据此开工前全量重跑。确需定位故障或建立基线时，先做相关检查；否则完成相应修改后再验证。未重验的证据保持 stale/missing，不能当作通过或据此宣布完成。需要切换绑定时，先核对当前任务，再在授权范围内 `prepare --rebind`。
2. **`twc prepare --task local:<slug>|issue:N|pr:N --contract <path>`** 写任务记录与本地绑定。`local:<slug>` 不读取平台；Issue/PR 默认联网，无平台读取授权或需要离线准备时加 `--offline`，仍会写本地文件。`prepare` 没有 `--online` 参数，`--rebind` 不改变联网规则。契约记录位于 `.team-workflow/tasks/local-<slug>/task.json` 或 `<type>-<N>/task.json`，AC 自动编号。契约或其引用文件变了，`prepare` 会拒绝；审阅变化后加 `--update-contract`，旧证据随之失效。
3. **`twc verify --check <name>`** 选择当前所需检查后先预览，授权覆盖时加 `--execute --approved-policy <hash>`；多个检查可重复 `--check`，省略会选择全部登记检查，只有当前验收确需全部时才省略。每次执行在任务目录写一份可提交的证据摘要。证据绑定代码内容、基线、策略、契约版本和工具链，任一变化即失效；提交任务目录本身不会使它失效。
4. **`twc handoff --draft --done … --next …`** 在任务目录写 `handoff.json/md`。没有证据的 AC 自动进入 remaining；拒绝 TODO、待补充之类的占位文本。
5. **只提交自己的路径**：`git add -- <paths>`，再 `git commit -m … -- <paths>`。任务目录也这样提交，推送分支即完成交接材料。`resume` 报告 `staged_outside_scope` 时，先确认暂存区里没有别的会话或成员的文件。

AC 写成 `{"text": "…", "checks": ["unit"]}`，所列检查在当前代码上都有新鲜的通过证据时才算 verified。纯文字的 AC 是 `needs_review`，留给人判断，工具永远不会自动判它通过。CI 可运行 `twc check`，它只做确定性的结构检查：契约是否被绕过 prepare 修改过、记录结构与检查状态是否有效、旧命令摘要是否含绝对路径、交接是否含占位文本。

未使用显式会话的旧契约流程仍可直接 `resume`：跨 clone 切到任务分支后，由本分支自 base 以来改动过的唯一任务目录推导，不需要对方本地文件。生命周期任务按上节显式选择并 start；原始证据保留执行者，不改名，项目要求新成员独立重验时仍执行。新任务、验证和交接在 actor（契约为 recorded_by）保留当时称呼并标记平台身份是否核验；本地就绪不等于平台审批。

```sh
python3 <skill>/scripts/twc.py --project <repo> doctor --local
python3 <skill>/scripts/twc.py --project <repo> resume
```

首次接入 TWC 协作流程时先运行 `doctor --local`；可在 init 前运行，只读检查名字、本机配置、版本锁和项目安装入口，不联网、不执行项目检查。出现 `configure_member_name` 时，只询问用户希望使用的名字或称呼（例如“67”），不索要邮箱；已有 `member.name` 不重复询问。获准配置身份后，仅在当前 clone 设置 `user.name`，不改全局配置；只读接手可继续阅读和分析，将设置列为待办。`ok` 不代表宿主已加载 Skill 或提交/平台身份已经核验。并行尝试使用独立 clone、分支或 `workspace create` 创建的 worktree，见 [collaboration.md](collaboration.md)。任务记录与契约字段见 [context.md](context.md)。

需要连接平台、处理平台权限或联网失败时按 provider 读取 [CNB](cnb.md) 或 [Gitea](gitea.md)，只读本次平台的说明。命令的本地写入、平台请求及离线重绑示例见 [身份与命令副作用](identity.md#命令副作用与准备示例)；参数不确定时查询当前安装副本的 `<command> --help`，不要把一个子命令的选项套到另一个子命令。`init`/`workspace create` 默认预览，已有授权覆盖后才加 `--apply`；不修改宿主全局配置。只扫描当前项目的宿主入口，发现同名目录还需核对所选宿主实际加载路径。

验证命令会执行项目代码，可能写文件、访问网络和数据库。先读取 `verify` 预览，核对命令、工作目录和副作用；已有授权覆盖当前命令时直接使用对应策略哈希执行，不重复询问。策略有实质变化时重新判断授权，哈希参数本身不是人的批准证明。具体证据合同见 [verification.md](verification.md)。

交接或排障尝试不再产生新证据时读 [handoff.md](handoff.md)，保留已验证事实、尝试结果和下一步取证目标。工具只写本地文件；提交、推送、发布到平台、合并、部署各自依据用户授权。禁止把 `advisory_ready` 当成合并许可。

