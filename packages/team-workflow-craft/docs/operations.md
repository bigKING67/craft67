# 团队试点与运维验收

首版软件提供本地协作工具，不部署公司平台。先用一个低风险功能、一个集成负责人、两位成员跑通，再扩大范围。配置、工具链产物与检查策略由负责人审阅；普通贡献者不能靠修改门禁为自己生成“通过”。

成员准备与日常动作见 [接入指南](member-onboarding.md)。真人试点之前可选运行 [隔离分支保护验收](gitea-policy-probe.md)，确认实际 Gitea 版本的行为；该测试不会进入普通离线门禁，也不能替代真人和真实产品验证。

已建立的 CNB 合成演练仓库、首条真实 CI 和待验收边界见 [CNB 首轮演练记录](cnb-pilot.md)。该记录是带日期的证据快照，不是第二套平台状态。

## CNB 0.2.2 验收（2026-10-26）

本节记录当日的合成试点结果。源码来源、安装产物、宿主会话、服务器 CI 和合并后本地复验分别核对；后续平台状态以 CNB 为准。

- **源码与固定产物**：候选从 craft67 已合并提交 [`e189bbce70508a9567e9cb3afe3fcdb6794ff6fa`](https://github.com/bigKING67/craft67/commit/e189bbce70508a9567e9cb3afe3fcdb6794ff6fa) 的本包重建。[该源码的 GitHub CI](https://github.com/bigKING67/craft67/actions/runs/40260385162) 中，本包 127 项测试通过。`team-workflow-craft-0.2.2.zip` 的 SHA-256 为 `e3b6b51fde137205bec2f565145da99d04ae3fd3517624dab010c71002e8358c`；29 个载荷文件与清单匹配，含安装标记共 30 个文件。
- **升级与安装**：未经修改的 0.2.1 安装在未加 `--allow-upgrade` 时拒绝替换，显式预览后升级到 0.2.2 成功；另一份全新 clone 直接安装成功。`doctor --local` 核对安装内容与工具链锁一致。旧固定产物、历史契约、验证者和执行证据保持原样。
- **Codex 接手**：一份全新分支 clone 在新 Codex 会话中接受普通只读接手提示，实际读取项目 0.2.2 Skill，查询当前任务与证据，将重验和重绑列为待办。该样本的执行轨迹与文件快照说明见 [宿主兼容性](compatibility.md)。
- **PR 与普通合并**：[CNB PR #6](https://cnb.cool/bql_huayue/twc-pilot/-/pulls/6) 的源提交为 `60fa7741678eba594e51859a35154c646c57b9c7`，目标基线为 `008bd37814a883edee71854c5d95386b9efbba92`。负责人账号完成评审并普通合并，平台回读 `is_merged=true`、`is_force_merged=false`。实际 main 合并提交为 `aec310d1d4e9493d7f543fda4c5bb649c9eb3348`，父提交为上述目标与源提交，代码树与已评审分支一致。
- **试点的 9 项测试**：[CNB PR 构建](https://cnb.cool/bql_huayue/twc-pilot/-/build/logs/cnb-505-1k5r2br4p#001) 实际 checkout 为 `60fa7741`，Python 3.12.15 下 9 项通过；状态接口 SHA `3529e4d7accec39ae839c890acb023fbe001cb47` 单独记录。合并后另从 main 全新 clone，安装同一固定产物，在 Python 3.12.10 下本地重验 9 项通过。两次均为失败、错误、跳过 0，退出码 0。该流水线只触发 PR，合并后的本地结果不算新增 CNB main 构建。

合并后 main 默认 `resume` 返回 `no_task`，不自动绑定历史任务；显式查询 PR #6、Issue #1 和 PR #3 时，旧 unit 证据均为 `stale`，PR #6 的 AC-1 为 `pending`，文字 AC 为 `needs_review`。顶层 `status=ok` 仅说明任务记录可读取，检查结果看 `checks.unit.status`，验收看 `acceptance`。本轮 main 的测试回执单独留存，没有回写历史任务证据或交接快照。

本轮由同一操作者使用用户控制的两个平台账号完成，证明角色流程，不构成独立真人审批或跨机器验收。0.2.2 的 Claude Code/Pi 会话、独立成员与跨机器接手仍未覆盖。合并后新 clone 的安装文件与上述 Codex 样本逐文件一致，但未另开宿主会话。本轮未进行正式 tag/Release 或全局安装；原工作区 WIP、此前试点安装和全局 Codex 配置保持原样。

## 三人试点

1. CNB 使用公司批准的组织/私有仓库、个人最小权限和恢复渠道；自托管 Gitea 另需固定平台/数据库版本与隔离 Runner。真实平台 OpenAPI 和权限返回是最终依据。
2. 负责人选一个功能，平台明确目标/验收/分配；接口/Schema 在代码仓库。建立测试数据库/端口/资源前缀的隔离约定。
3. 三人安装同一批准 ZIP，核对产物与工具链锁，在各自宿主新会话显式调用。记录宿主/OS 版本、加载路径、doctor/prepare/verify/handoff 的真实结果。
4. Claude 开始 → 授权推送与发布去敏交接 → Codex 在另一 clone 接手 → Pi 复核。接手只用平台资料，不能借用发起者绝对路径或聊天。
5. 集成负责人刷新基线、串行合并；每个 PR 基线变动后重验，最后跑组合功能与错误/重试路径。记录平台精确 head/base、CI 和批准身份。

## 验收矩阵

| 项目 | 本包离线门禁 | 公司试点所需证据 |
| --- | --- | --- |
| 小任务轻量 | Skill 独立场景评估；CLI 无 claim/spawn/merge/deploy | 同任务对比原生/Trellis 精简/TWC；模型测评另行授权 |
| 任务读取 | 模拟 CNB/Gitea 权限/分页/网络/畸形响应 | 实例版本/OpenAPI、真实账户权限、Issue/PR/review/status 读取 |
| WIP 保护 | 临时仓库 dirty、跨目录、路径保护 | 实际产品 worktree 与服务资源隔离 |
| 验证真实性 | 未运行/失败/超时/漂移不能通过 | 受控 CI、身份与必要独立审查 |
| 独立安装 | 构建清单/安装防护/源码副本移走后运行 | 三宿主当前会话加载；Windows 与目标平台 |
| 交接 | 独立 clone 接手、历史与当前身份区分、草稿和过期检测 | 真正跨机器访问已推送代码/规格/证据 |
| 集成 | 新基线/接口使旧材料过期；组合失败、修复和重验；local advisory 永远不授予 merge | 最新主分支、审批、组合测试、保护分支 |
| 运维 | 不属于本地 Skill 验证 | 备份含 DB/仓库/附件/配置，一次异机恢复、第二管理员恢复渠道 |

2026-10-16 已在 macOS 27.0.1 arm64 用固定 v0.1.3 产物完成三宿主原生发现检查，见 [兼容性记录](compatibility.md)。该检查未发起模型任务，只确认入口被宿主识别，不替代上表的当前会话正文调用、真实接手或多人集成验收。

## 可重复的跨 clone 验收

[安装产物验收用例](../tests/test_handoff_acceptance.py) 从当前源码构建 ZIP，分别装入 Claude、Codex、Pi 的项目入口，之后只运行各安装副本的 CLI。三份独立 clone 使用 Alice、Bob、sixseven 三个合成 Git 身份，共用临时本地 bare 仓库；不会联系 CNB，也不创建真实账号或调用模型。

在本包目录可单独运行：

```sh
python3 -m unittest discover -s tests -p test_handoff_acceptance.py -v
```

用例通过 `doctor → inspect → prepare → verify → handoff` 检查以下行为：

- Bob 从共享分支接手时没有 Alice 的 ignored local 任务绑定或证据，必须重新准备。显式传入历史证据后，验证者仍为 Alice，当前操作者为 Bob。
- 接手后提交变化、主分支前进或接口文件变化都会使相应旧证据/快照失效，不能直接用于当前交付。
- 主分支和功能分支分别通过测试，合并后因公共协议变更而失败；失败证据阻止就绪。修复组合行为并重验后，才由 sixseven 的独立 clone 再次验证并串行集成到本地测试远端。
- Alice 原工作区里的无关 WIP 和提交位置保持不变。全程不把离线身份当成平台认证；最终交接仍为 `unknown`，`merge_authorized=false`。

这是确定性工具与真实 Git 的组合验收。测试脚本执行本地 Git 提交/推送/合并，TWC 本身没有获得这些权限；它也不证明三种 Agent 执行了 Skill 正文、不同机器环境一致或 CNB 保护规则生效。

## 平台与 CI

按实际版本配置并验收：保护主分支、禁止强推与非授权直推、必要审批/状态检查、过期审批处理、最新基线和受限合并身份。Gitea PR head 测试不能单独证明合并组合；官方 [Actions FAQ](https://docs.gitea.com/usage/actions/faq/) 说明相关行为。以公司部署版本实测为准。

Runner 执行待审查代码，隔离于平台 DB、备份及生产权限。Actions、镜像、依赖与 Skill ZIP 使用批准来源；自托管 Gitea 不等于 CI 不访问 GitHub。

CNB 的权限和合并预览差异见 [CNB 接入](../skills/team-workflow-craft/references/cnb.md)；仅管理员批准并不直接证明普通开发者无法点击合并。

代码托管和云模型的数据边界独立。模型账号、端点、网络与政策由公司管理，TWC 不新增模型连接，也不承诺仅靠 Skill 阻止宿主发送上下文。

## 后续版本

当前源码 v0.2.2 提供随分支提交的任务记录、`resume`、`check` 和本地交接；`--publish` 仍不支持。下一步优先完成真实多人试点、平台门禁和故障演练，分别记录当前版本与证据。评论发布仅在出现明确需求、另行授权并验收去重及写超时回读后评估，不是本版本承诺。客户端去重不保证 exactly-once；自动抢单、分布式锁、合并队列及更多平台抽象仍无当前需求。
