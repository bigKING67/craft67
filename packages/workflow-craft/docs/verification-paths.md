# Workflow Craft 关键验证路径

这是本包已有测试的操作索引，不是第二份功能规格。命令从包目录执行；测试使用临时 Git 仓库、本地模拟服务和固定安装产物，不触碰实际成员项目或付费模型。代码改变这些入口或结果时，同步维护对应测试和本表。

| 路径 | 操作与可观察结果 | 自动证据与容易误判之处 |
| --- | --- | --- |
| 首次启用 | 未配置项目 → doctor/resume 要求选择 → 显式 init personal → 子目录复用；另一个项目重新选择 | `test_modes.py`：没有选择不写配置；名字可复用，不要求邮箱。脚本返回 selection_required 不等于模型实际主动询问 |
| 个人本地任务 | prepare local → verify 预览/执行 → handoff → resume；修改代码后旧证据 stale | `test_modes.py`：无平台/邮箱也可本地接续；local_task 就绪不等于平台审批；纯文字 AC 保持 needs_review |
| 团队及切换 | 预览模式切换 → 当前策略哈希应用 → 旧证据失效 → 重验；历史任务/署名/集成要求保留 | `test_modes.py`：并发改配置拒绝覆盖；已有团队任务切到个人仍需原评审，不因模式名绕过 |
| 延后与部分重验 | 已有两项通过 → 改代码 → resume 只读报告 stale → 只重验 unit → full 仍 stale、交接未就绪 → 补齐 full | `test_task_boundaries.py`：不重建任务，不因部分通过而放行其他必要检查；不能通过删契约/检查来省略验收 |
| 本地生命周期 | create → start → verify → complete → archive → reopen；finish 只清绑定；父任务等待全部子任务 | `test_lifecycle.py`：保留历史，代码/评审/子任务变化使完成依据过期；文字验收不可替代失败检查，本地完成不等于平台审批 |
| 会话与工作区 | 两会话各绑一任务、结束一个、换分支、独立 worktree 接续、两个进程争用锁 | `test_lifecycle.py`：指针不串线；没有绑定不猜任务；锁只覆盖工具写入，不能当编辑器/数据库沙箱 |
| 模式显示 | 子目录/linked worktree → solo；更改配置 → team；嵌套项目/坏配置/读取失败给出对应状态 | `test_statusline.py`：不写文件、不联网、不执行检查；显示不证明工具链锁、任务或宿主加载 |
| Claude 输入 | 工作区 JSON → 当前目录优先于启动目录；坏输入及解码深度异常显示不可用 | `test_statusline.py`：真实命令 stdin/stdout 合同，含 Python 3.11 深层 JSON 回归；不能代替 Claude 原生 TUI 显示验收 |
| Pi 状态项 | session_start → solo；agent_end → 更新；切换时 shutdown/start → 新状态；shutdown → 清除自己的项 | `test_statusline.py` 调用 `statusline.test.mjs`：真实适配器、模拟事件、真实 Python 读取；保留其他状态并拒绝过期回调。需要 Node 22.18+，缺失会明确 skip；另需原生宿主加载验收 |
| 固定产物安装 | 构建 → 三类宿主项目安装目录 → 删除临时源码 → 执行安装副本；旧名迁移/漂移拒绝 | `test_cli.py`、`test_packaging.py`：自包含、幂等、受控升级；安装文件存在不是宿主自动发现 |
| Trellis 只读盘点 | 读取任务/计划/spec → 核对目录引用、来源哈希和扫描漂移 → 输出待核对项 | `test_trellis_inventory.py`：重复标识、归档差异、坏数据、符号链接和并发变化；退出 0 仍为 migration_ready=false，不代表完整备份或迁移成功 |
| 宿主遵循项目规则 | 无持久任务的多文件修改；已有任务的 stale 接续；已有合并队列的只读接手 | 在临时项目装固定包，配置独立项目规则并显式调用 Skill；核对真实命令顺序、检查次数、文件差异与状态，不只看最终回答。具体观察见 [0.4.1 兼容验收](compatibility.md#041-project-rule-cooperation-acceptance-2026-10-30)，不纳入离线门禁或自动调用模型 |

```sh
# 状态栏改动的定向检查
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_statusline.py -v
# 模式与本地任务
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_modes.py
# 完整离线发布前门禁（含安装产物）
python3 scripts/check.py
```

实际宿主验收使用临时项目和显式安装路径，核对载入版本、输出与前后文件差异；无模型调用的扩展加载测试不能证明模型遵循 Skill。真实宿主、人工体验、远端平台与正式发布的范围按 [兼容性记录](compatibility.md) 分别报告。测试目录由临时目录管理器清理；持久验收记录只保留去敏结论与必要 artifact，不归入安装产物。
