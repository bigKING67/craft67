# 同一宿主从零研究到封存验收

2026-09-20。冻结候选75文件、宿主工具哈希、自然语言任务及八项标准后，同一独立Codex CLI宿主从空工作区自行取证、研究、审计、渲染和封存。实际969.462秒，退出0，无超时，运行中无父代理纠正。结论：**FAIL_FULL_E2E_RENDER_GATE_ORDERING**；不是因缺乏确定性投资建议而判失败。详见[回执](../acceptance/full-research-host-review-20260920.json)。

## 已验证的进展

历史对象US-NASDAQ:AAPL，事实截止2025-11-01，实际执行与捕获日期2026-09-20，资料明确post-hoc。自行取得正式2025/2023年报、季度披露、IR与历史价格页；10个捕获对象、7个唯一URL，最终9个引用来源槽位包含同源复用。独立价格第二来源403与财务、股数及预测缺口均保留，不伪造双源。

研究核心首次finalize失败、修正后通过，complete=true；67项计算和3项勾稽通过。报告包含五年财务、商业与资本配置分析、反方、条件估值、证伪及补证要求。未把单一税项调整当完整正常化利润，未把高账面权益回报代理当平均ROE，也未把单源历史价格或异日股数当已验证同日估值。

父代理退出后重新执行verify-snapshot、verify-current、verify-all及运行账本artifact验证，四项均ok=true；核心status再核验complete=true。10个捕获body哈希回读一致；封存报告与核心Markdown逐字节一致；r0001文件只读。候选、全局安装和宿主工具未改变。以上证明研究核心及档案完整性，不证明所有交付门禁通过。

## 失败根因

宿主生成8页classic-paper阅读版，记录实际页面检查及164个内容单元覆盖通过，但两项Kami检查未闭合：

1. PDF markdown checker拒绝四行中的长连接符，涉及年份或来源编号范围；没有证据表明这些诊断对应财务数值错误。
2. 通用HTML内容checker在修正content.json schema后仍返回静态可见性/资源选择不确定，并提示标题、作者未在其认定的可见文本中找到。专用文本覆盖通过不能自动消除此门禁；本轮未证明其底层根因，也没有修改插件规则。

更重要的是检查次序：执行事件第94项命令已经运行PDF markdown checker并产生失败；第115项命令进入封存；第127项命令才创建并检查content IR。渲染阶段先按视觉/字体/占位符检查完成，补充门禁失败未阻断归档。宿主最后将delivery-status修正为PARTIAL_KAMI_ACCEPTANCE，诚实披露问题，但这不回溯修复此前完成事件的语义。

因此E07不通过，整体不能标PASS；E08的哈希链通过只表示被记录文件未变，不表示每个阶段的业务判断正确。原sealed revision只读保留，不篡改或更名为准出成功。

## 冻结标准判定

| 标准 | 判定 |
|---|---|
| E01 冻结Skill与实际路由 | PASS |
| E02 自行正式取证、期间及post-hoc边界 | PASS_WITH_DISCLOSED_GAPS |
| E03 财务输入及可复算计算 | PASS_WITH_DISCLOSED_GAPS |
| E04 商业/现金质量与反方 | PASS_BOUNDED_PARENT_REVIEW；不等于独立投资同行审稿 |
| E05 币种、股份口径及条件估值 | PASS_WITH_DISCLOSED_GAPS；不支持投资决策就绪 |
| E06 同宿主核心完成与失败留存 | PASS |
| E07 同宿主完整交付 | FAIL_REQUIRED_RENDER_CHECKS_NOT_CLOSED_BEFORE_SEAL |
| E08 账本、产物及无父代理代修 | PASS_INTEGRITY_ONLY |

## 下一步整改验收边界

优先处理渲染完成与封存的门禁衔接，而非再换一家股票重复长跑：先识别当前路由实际要求的检查集合，将检查结果及对应Markdown/HTML/PDF哈希绑定到阶段完成；失败、不确定或缺失结果阻断准出；渲染文件改变后旧结果失效。先用“通过、明确失败、不确定、缺失、输出被修改”五类小样本验证，再做必要的端到端复验。具体工具/API改动尚未在本轮实施。

产物与原失败在 `local/skill-evals/20260920-full-research-host/`，父代理只读复核在parent-review。没有修改用户正式money档案、全局Skill、源码或宿主工具，未commit/push/发布。浏览器响应式和Money项目主题不在本次冻结范围内。
