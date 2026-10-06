# 共用核心审查覆盖状态

> 当前版本及待办以 [验收总表（2026-09-21）](current-acceptance-status.md) 为入口；下文保留分阶段证据与历史边界。

2026-09-20 [归档解释器与默认证据文案已修复](delivery-runtime-fix-20260920.md)：两套回归及Apple原报告隔离归档生成通过，宿主兼容工具4文件有界变更；没有修改全局Python链接或Skill安装，尚未完成正式封存及新宿主重跑。[美的主张范围复核](midea-research-scope-20260920.md)明确已有披露可继续研究，正常化未知不应被表述为无法分析公司；核心门禁本轮未放松。

2026-09-20 最新候选宿主验收：[Apple历史案例](apple-candidate-e2e-20260920.md)完成：核心及78项计算通过，7份响应/账本重放通过，候选与全局安装未变。全链路因兼容归档固定Python失效、渲染/视觉门禁仍失败；研究语义覆盖另保留PARTIAL。源码/核心通过与正式归档失败分开判定。

2026-09-20 最新：[汇兑后续核查](fx-followup-review-20260920.md)已收窄缺口：取得港交所中期报告，汇兑列报拆分与A股披露对齐；表内/文字差异找到与OCI附注相符的精确算术关系，解释保持INFERRED。10项计算、局部账本通过；正常化与结算桥仍UNVERIFIED。原始失败、全局安装和核心门禁不变。

2026-09-20 最新研究补证：[汇兑与金融工具核查](fx-bridge-review-20260920.md)已完成局部核查：2份原件哈希、3页PDF视觉核对、13项计算及局部账本通过。发现衍生品投资表、文字与财务附注间尚未解释的口径差异；正常化盈利及结算桥仍UNVERIFIED。未改核心门禁或全局安装，原完整链路仍未通过。

2026-09-20 最新增量：[附加证据及输出合同修复](additional-evidence-20260920.md)已在源码/候选和主代理材料重放中通过：525项测试（497通过、28跳过）、19项源码检查、7项包检查、75文件源码/候选一致。新工作区报告与论文审计及50项计算通过；封存仍由经济解释UNVERIFIED阻断。全局安装未更新，4文件与源码不同；未自主重跑或正式归档。下方记录保留各阶段时点，不能当作本次安装一致证明。

2026-09-20 [新版安装与美的宿主重跑](midea-installed-e2e-20260920.md)已完成：75文件源码/候选/安装一致，9项安装版自检通过；同一冻结提示下宿主自行使用 `import-public` 成功，原行情阻塞已关闭。全链路仍失败：S23较早季报未获计划声明、经济解释UNVERIFIED及两处文档合同问题阻断封存。主代理重放50项计算、10来源本地完整性及账本校验通过，不代表正式归档通过。

2026-09-20 公开行情登记缺口已在源码和候选包修复，见[整改回执](../acceptance/public-source-admission-20260920.json)。新增 `import-public`，公开行情与正式披露分列，保留 URL/哈希、时间、封存和中断门禁。美的原报告/论文/勾稽输入未改，在新工作区导入原8项披露及2份行情后，87项计算与核心封存通过。518项测试中490通过、28项可选依赖跳过；19项源码检查、7项包检查及75文件源码/候选一致。全局安装未变，完整宿主重跑和正式归档仍未验收；不能把主代理材料重放计为自主全链通过。

2026-09-20 [美的集团首次完整链路验收](midea-e2e-20260920.md)已执行，结果为 **FAIL_E2E_SOURCE_ADMISSION**：宿主自行取证及研究，87项计算与账本完整性通过，但公开行情S31/S32无法登记进核心证据清单，引用审计拒绝封存；渲染/正式归档尚未执行。旧失败保留，下一项明确整改是公开补充来源登记，不能放松引用门禁。此结果取代“尚未运行新公司案例”的状态，不等于完整链路已通过。

2026-09-20 当前版本的证据衔接及下一阶段门禁见[准出清单](readiness-20260920.md)：现场源码/安装75文件一致，16个运行时与综合基线一致；保留全文、增量和宿主验收的不同范围。新公司自主取证到归档仍需专门验收，不能把历史分离流程合并宣称通过。

2026-09-20 商业化证据规则新增[真实披露摘录验收](../acceptance/real-commercial-review-20260920.json)：全局安装版解读TI 2024年报收入政策与Microchip截至2024-09-30季度10-Q订单条款，机器路由/引用/哈希检查及6项主代理语义标准通过。未发现需要修改规则的缺口；普通分销与寄售、合同版本与履约风险均区分。原PDF下载均返回403，实际使用工具提取文本；不宣称原件完整性、历史版本一致性、独立客户核验或当前投资研究已完成。

2026-09-20 最新研究语义增量已完成下列有界验收并进入全局安装；不改变历史全仓审查或封存报告的证据范围：

| 增量 | 最新证据 | 当前结论 |
|---|---|---|
| 分项与披露合计核对 | [三类跨案例验收](../acceptance/tie-transfer-review-20260920.json) | 一致、舍入兼容、期间/单位不同比较三个冻结合成样本通过；数学审计不自动证明舍入原因 |
| 离线材料与本地路由边界 | [路由收口](../acceptance/offline-routing-closeout-20260920.json) | 修正事实输入限制与文件读取限制的冲突后，安装版路由通过；旧提示词失败保留，不宣称无条件稳定 |
| 框架/定点/订单/交付/收入/利润 | [安装版验收](../acceptance/commercial-evidence-installed-20260920.json) | 一个混合状态合成样本通过，10条计算及6项主代理语义标准通过；不等于真实合同或会计确认核验 |

验收器补充识别路由包装脚本实际调用的Python核心入口，仍核验退出码及有效JSON；33项回归通过，原始误拒记录与重审结果分别保留。当前源码与全局安装75文件一致；版本仍为0.3.0未发布候选，没有commit/push/Release，应用未启动。

按用户明确要求，三个旧Money Craft安装备份已全部清理，见[清理回执](../acceptance/backup-cleanup-20260920-final.json)。当前安装、源码、候选包和验收记录保留。下方历史条目中的“备份保留”只描述当时状态，不代表当前仍可从旧目录回滚。

剩余边界：本轮语义验收由主代理人工复核，非独立审稿；没有对全市场、所有合同或会计政策建立泛化保证。后续若继续扩展商业化判断能力，优先选真实正式披露核对可取消订单、寄售和收入政策；只有新材料暴露实际缺口才修改规则，不继续围绕相同合成案例反复调参。

2026-09-20 组合日常安装阶段已完成[收口](../acceptance/portfolio-daily-baseline-20260920.json)：独立有界审查发现并修复大持仓C10000回执兼容缺陷，共享合同统一为2–7位且独立复验通过；493项候选测试（23项在报告运行时补齐）、8项包检查及75文件源码/候选/安装一致。新自然语言宿主自动读取并执行全局安装版，46项结果核对、80项回执、8项语义标准通过。stdout回执兼容修复经24项测试及独立复审；首次失败与旧安装备份保留。应用未启动，无commit/push/Release。

2026-09-20 原始资料到组合核心链已完成[有界验收](../acceptance/skill-tasks/portfolio-extraction-20260920.json)：宿主仅获3份PDF及自然语言约束，自行生成输入并执行核心；主代理50项核对、独立CLI重放、71项计算及8项语义标准通过。首次机器验收未识别原生JSON回执，修复验收工具后对原答案重验通过，23项验收器回归及旧Markdown案例重验通过。Skill/core和全局安装均未改；指定格式和LOCAL身份边界保留，不扩展为任意PDF或全市场穿透能力。

2026-09-19 组合核心宿主验收已收口：[显式源码端到端回执](../acceptance/skill-tasks/portfolio-core-host-20260919.json)。隔离宿主238.286秒完成，路由READY，正常输入成功、来源摘要错误输入拒绝；回答13项计算与主代理8项语义标准通过。源码和安装摘要均保持不变。此证据覆盖已结构化输入的源码版调用，不代表隐式发现、自主转录或新版安装验收；应用仍后置。

2026-09-19 组合核心增量：新增 `portfolio_audit.py`、CLI 入口与输入合同，已做主代理代码复核、正负向回归及官方资料重放，见[验收回执](../acceptance/portfolio-core-20260919.json)。此增量不在原15文件冻结审查内，不能借用历史独立审查或安装宿主成绩；新模块未作独立代理审查。

2026-09-19后续：真实五年论文研究新增历史年报来源S21/S22，变更了research_workflow及CLI self-test。原全文审查哈希保留；当前差异由[历史来源增量审查](../acceptance/historical-source-intake-20260919.json)覆盖，不能将旧台账哈希称为新版本全文重审。481项测试、源码及包检查通过。随后[公司研究收口](amazon-company-research-closeout-20260919.md)已同步全局安装，72文件一致，完整自然语言任务与安装版研究封存有界通过。

当前收口顺序与完成条件见[验收收口清单](acceptance-closeout.md)。2026-09-19 已复核全部 15 个运行时文件与台账哈希一致；历史宿主套件不自动覆盖当前版本。

下表及逐日条目保留当时审查范围；当前结论以顶部收口链接及文末后续记录为准。

更新：2026-09-19。此表登记已有证据与剩余范围，不是逐文件全仓审查完成证明，也不提供评分。历史记录的测试数量只代表各自运行时版本。

| 范围 | 已有证据 | 当前结论与边界 |
|---|---|---|
| 金融计算与报表勾稽 | [本轮复核](../acceptance/financial-core-review-20260917.json) | 修复收据漏审、精度与异常边界、期间绑定；不证明原始摘录或单位已核验 |
| 研究计划与论文合同 | [本轮复核](../acceptance/research-workflow-review-20260917.json) | 计划期间一致性、事实/source变更、重复合同章节；research_run 全路径仍未完成 |
| 报告审计 | [本轮复核](../acceptance/report-audit-review-20260917.json) | 日期规范、来源定义及索引后引用；不证明原始来源真实或 Markdown 全语法兼容 |
| research 收据、证据路径与公开引用 | [收据](../acceptance/core-receipt-20260916.json)、[路径](../acceptance/official-evidence-path-20260916.json)、[引用](../acceptance/public-citation-20260916.json) | 三项已复现问题修复；不证明发行人身份、报告期和论点支持 |
| research CLI 生命周期 | [生命周期](../acceptance/research-lifecycle-20260916.json) | 源码/安装各21步，本地合成材料；不是正式 money 档案或内核断网验证 |
| tracking 旧基线与封存 | [本轮复核](../acceptance/tracking-base-20260917.json) | 两个工作区基于旧论文准备时，后提交的过期候选须拒绝；保护工作区与当前历史，支持重新初始化恢复 |
| tracking 历史连续性 | [本轮复核](../acceptance/tracking-history-20260917.json) | 编号从首版连续、相邻论文哈希衔接；缺版或错误前驱拒绝，验证不改写历史 |
| tracking 封存异常清理 | [本轮复核](../acceptance/tracking-publication-20260917.json) | CLI 故障注入覆盖目录权限、指针替换与替换后同步失败；保留已被引用的版本与工作区，不等于断电恢复 |
| tracking 并发读取快照 | [本轮复核](../acceptance/tracking-snapshot-20260917.json) | verify/status 与写入共用锁；真实 CLI 交错验证，不覆盖绕过锁的外部写入 |
| tracking 强制终止后重试 | [本轮复核](../acceptance/tracking-kill-20260917.json) | current 替换前后 SIGKILL 实测；无效历史禁止扩展，保留现场；未实现自动恢复 |
| 财报计算与跟踪交接 | [既有验证](../openspec/changes/add-earnings-update-core/validation.md) | [本轮合同复核](../acceptance/earnings-contract-review-20260917.json)完成；未重新做真实财报语义提取审查 |
| 前瞻、复盘、数值交叉核验 | [既有验证](../openspec/changes/add-earnings-preview-replay/validation.md) | 有基线封存及捕获数据对账；历史实测不代表当前Provider连通性，未来预测表现未验证 |
| 驱动模型与归因 | [既有验证](../openspec/changes/add-earnings-driver-model/validation.md) | [本轮整文件复核](../acceptance/earnings-math-review-20260917.json)及12项回归通过；假设质量及未来实际结果仍未证实 |
| Skill 宿主行为 | [六类及自然触发](../acceptance/skill-tasks/final-convergence-20260916.json) | 固定版本有界通过；之后核心修复不自动继承为该新版本全套宿主复验 |
| 上游治理 | [既有验证](../openspec/changes/add-upstream-reference-governance/validation.md) | 有目录/捕获/变更治理证据；不能由历史文档推断所有上游当前已刷新 |

## 尚未完成的集中审查范围

- 已建立[15 个运行时文件的覆盖台账](core-review-coverage.md)：9 个有界已审、5 个局部、1 个待审；这不是全部自有源码或全仓覆盖。
- tracking 本轮验证的是确定性的先后提交与锁内基线检查，不宣称覆盖系统崩溃、任意并发调度、损坏指针恢复或恶意重写整套哈希。
- Provider、发行人原文提取、渲染/导出有既有测试和历史资料，但本轮没有重新验证最新网络数据、多市场多公司语义及所有运行环境。
- 正式 money 档案协议与 `.research`/tracking 共用核心是不同完成边界；不合并准出结论。

下一步按逐文件台账核对证据流程及报告输出；tracking 自动恢复与真实断电耐久性仍为明确缺口。已通过的固定聊天案例不继续无目的重复。应用建设后置，commit、push、发布仍分别授权。

2026-09-17 研究证据生命周期增量见[验收记录](../acceptance/research-evidence-lifecycle-20260917.json)：拒绝封存后采集/导入；首次封存核对 capture 身份、原始哈希和字节数；新 manifest 绑定 capture 元数据；旧 manifest 重复 finalize 保持文件字节不变。研究生命周期仍 PARTIAL，已复现并发 no-clobber 竞争，跨文件中断与恢复待闭环。

2026-09-17 单文件并发不覆盖缺口已修，见[验收记录](../acceptance/research-no-clobber-20260917.json)。两个真实 finalize CLI 进程在收据发布前同步竞争，一方成功、一方 existing_artifact；赢家收据保留，重试不改写。此证据仅覆盖单文件发布窗口，不关闭 collect/import/finalize 的工作区级竞争或跨文件中断恢复。

2026-09-17 四个研究入口的工作区共用锁已接入，见[验收记录](../acceptance/research-workspace-lock-20260917.json)。真实 CLI 交错验证忙碌拒绝、不改工作区、完成后重试；异常和强杀验证 OS 锁释放。collect 配置预检查也持锁。此结果不等于多文件崩溃恢复；初始化、外部直接写入、Windows 与网络文件系统仍在边界之外。

2026-09-17 官方导入中断保护见[验收记录](../acceptance/research-import-interruption-20260917.json)：清单发布后异常保留证据，缺失完成事件阻止状态准出与封存；真实 CLI 在清单发布后强杀验证。此轮未实现原地自动恢复，清单发布前强杀造成的孤儿文件仍待处理。

2026-09-17 官方导入清单发布前的孤儿检测见[验收记录](../acceptance/research-orphan-import-20260917.json)：已登记待导入来源的 PDF/HTML 及标准 UUID 暂存名阻止准出，可选来源同样适用。真实 CLI 在可选来源证据发布后、清单发布后分别强杀，后续不改文件且拒绝封存。原地自动恢复与其他事务仍未实现。

2026-09-17 封存缺完成事件的恢复见[验收记录](../acceptance/research-finalize-recovery-20260917.json)：收据已发布但事件缺失时 status 不报完整；retry finalize 重新核验后仅补 run-state 完成事件，重复执行不变，漂移则拒绝。真实 CLI 强杀已验证；收据暂存硬链接保留，其他事务恢复仍未闭环。

2026-09-17 采集中断检查见[验收记录](../acceptance/research-collection-interruption-20260917.json)：已登记capture无标准化结果或标准暂存目录残留时拒绝继续；完整结果在事件失败后resume零请求复用。离线合成Provider的真实采集进程强杀后，真实CLI collect/status/finalize拒绝且文件不变。未使用真实网络Provider，未重建缺失结果或清理残留。

2026-09-17 初始化并发见[验收记录](../acceptance/research-init-lock-20260917.json)：构建与发布期间持共用锁，真实 CLI 竞争返回 busy；发布前强杀后新 init 成功，已有目标不改写。旧暂存目录保留；外部绕锁、残留清理、其他事务与跨平台仍未闭环。

2026-09-17 生命周期范围集中说明见[验收边界](research-lifecycle-boundaries.md)，本轮修复采集事件容量预检，见[验收记录](../acceptance/research-lifecycle-boundaries-20260917.json)。未将不支持项或环境缺口改判通过；接下来按文件台账继续报告输出及其余核心审查。

2026-09-17 报告输出路径保护见[验收记录](../acceptance/report-render-paths-20260917.json)：写入前拒绝输出与源文件/模板/证据等输入的路径别名，以及HTML/PDF同文件；覆盖软/硬链接。真实CLI拒绝覆盖源文件，独立HTML正常生成与校验。report_renderer进入PARTIAL，未完成转义、图表、PDF或视觉验收。

2026-09-17 报告模板递归展开修复见[验收记录](../acceptance/report-template-expansion-20260917.json)：仅替换模板原文标记，内容带入的未解析标记在写出前拒绝，不再按字段顺序展开。真实CLI验证源文件与旧HTML保持不变；原始HTML、SVG、PDF和失败发布仍未闭环。

2026-09-17 资源属性校验见[验收记录](../acceptance/report-resource-attributes-20260917.json)：HTMLParser 识别无引号/实体编码及更多资源属性，替换原URL正则；页内锚点和内嵌栅格图允许，纯文本来源不误判。真实CLI外部img拒绝且文件不变。CSS、脚本、嵌套文档及完整浏览器离线语义仍未闭环。

2026-09-17 报告正文主动内容限制见[验收记录](../acceptance/report-body-audit-20260917.json)：Markdown输出在嵌入可信模板前检查标签/属性，拒绝脚本/事件/嵌套页面等，保留普通排版、表格和转义代码。模板CSS/JS及程序图表不受此正文检查覆盖；不是任意HTML安全验收，renderer仍PARTIAL。

2026-09-17 生成失败输出保护见[验收记录](../acceptance/report-render-staging-20260917.json)：HTML/PDF先暂存，PDF或源哈希复核失败时不改正式输出，正常异常清理临时目录。PDF使用模拟写入与故障注入；不代表实际PDF排版验收，双输出最终替换仍非原子事务。

2026-09-17 图表完整数值准入见[验收记录](../acceptance/report-chart-scalars-20260917.json)：不再从范围、来源编号或括号负数中截取数字；按调用方限制后缀，拒绝浮点溢出/下溢。真实CLI保留原始表格并省略无法确定的财务趋势图，正常估值图仍可生成。极大有限数的后续运算、表头单位推断及完整SVG几何仍未闭环。

2026-09-17 图表极值运算保护见[验收记录](../acceptance/report-chart-overflow-20260917.json)：不可表示的量程/FCF差额不画图，变化率溢出明确标注，坐标和柱宽先算比例。真实CLI极值输入保留正文且不生成四类失效图表。单位推断、标签精度、完整SVG几何和真实PDF仍未闭环。

2026-09-17 图表标签与柱宽修复见[验收记录](../acceptance/report-chart-labels-20260917.json)：非零微小值/超大值用科学计数法，负零归零；估值/同比柱条取消最小宽度。真实CLI验证零条宽、非零微小价格及来源不变。仍不代表单位推断、十进制精度、完整几何或真实PDF验收。

2026-09-17 估值图单位准入见[验收记录](../acceptance/report-scenario-units-20260917.json)：完整值列标题及元单位合同，外币/总价值/无单位不画估值图。真实CLI保留美元表和正常财务图。财务/同比单位及完整几何、真实PDF仍未闭环。

2026-09-17 同比图百分比准入见[验收记录](../acceptance/report-yoy-units-20260917.json)：百分点/金额/基点和无单位裸数不当作百分比。真实CLI保留百分点表且省略同比图，正常财务图继续生成。财务单位、候选列择优、完整几何和PDF仍未闭环。

2026-09-17 财务图金额单位准入见[验收记录](../acceptance/report-financial-units-20260917.json)：行末金额单位必需、首列头单位冲突拒绝，趋势各项显式单位，现金流相同金额单位才派生。真实CLI拒绝将百分比财务行画作金额，原表及估值图保留。任意单位声明与完整SVG/PDF未闭环。

2026-09-17 年份顺序/间隔修复见[验收记录](../acceptance/report-year-order-20260917.json)：财务/现金流按年升序重排、重复年份拒绝、横坐标按实际年差。真实CLI倒序表图形与正序一致且source不变。图表选择、证据展示、完整SVG/PDF待审。

2026-09-17 证据计数展示修复见[验收记录](../acceptance/report-evidence-display-20260917.json)：不再将失败零或空组登记标为完整/已捕获；严格计数、保留零、缺失明确。真实CLI部分清单展示2/15并保持输入不变，不证明证据质量或清单真实性。

2026-09-17 图表候选表筛选见[验收记录](../acceptance/report-table-selection-20260917.json)：代码围栏/缩进代码不作数据，分隔行逐列校验。真实CLI代码财务表保留但不生成趋势图，正常估值表仍出图；非完整Markdown语法等价及全选表策略验收。

2026-09-19 runtime_paths整文件闭环见[验收记录](../acceptance/runtime-paths-review-20260919.json)：路径优先级、显式env及常量调用有界已审，修复末级symlink绕过、半加载和空变量优先级；10专项/354全量通过。核心9已审/4局部/2待审，下一项Provider适配器。

2026-09-19 FRED观测响应准入见[验收记录](../acceptance/fred-response-review-20260919.json)：默认观测格式逐行日期/数值验证，错误信封不作为成功；CLI离线注入异常不写capture。FRED转PARTIAL，其他端点、修订语义、transport/credential与真实Provider未闭环；9已审/5局部/1待审。

2026-09-19 FRED传输/脱敏见[验收记录](../acceptance/fred-transport-review-20260919.json)：拒绝HTTP降级/跨主机重定向及不合规基础URL，完整已知凭据先脱敏后截断。离线handler与真实CLI main注入验证，无实时网络声明。FRED仍PARTIAL。

2026-09-19 FRED凭据读取见[验收记录](../acceptance/fred-credential-review-20260919.json)：同fd身份/权限复核与限量读取，检查后替换/放宽权限/增长拒绝；真实CLI在网络与capture之前退出。父目录、同inode外部并发、Windows/NFS不保证，FRED仍PARTIAL。

2026-09-19 FRED身份/历史单日绑定见[验收记录](../acceptance/fred-binding-review-20260919.json)：series唯一身份与请求匹配，search行身份/vintage日期检查，历史单日顶层日期及逐行有效区间校验。CLI注入错序列/错时点拒绝且不写capture；全量368项通过。无独立代理复审或真实Provider声明，FRED仍PARTIAL。

2026-09-19 FRED网络失败路径见[验收记录](../acceptance/fred-network-review-20260919.json)：HTTP错误体显式释放，读/关闭失败保留状态和通用诊断，协议读取中断转结构化重试，非有限Retry-After回退；CLI三次后EXIT_TRANSIENT且无capture。30项FRED/375项全量通过，FRED仍PARTIAL，无独立代理或真实网络声明。

2026-09-19 FRED分页/口径见[验收记录](../acceptance/fred-pagination-review-20260919.json)：分页元数据与条数自洽、请求范围/转换标识绑定；合法部分页保留且CLI提示，缺元数据提示完整性未验证。33项FRED/378项全量通过。未自动翻页或验证上游转换算术，FRED仍PARTIAL。

2026-09-19 FRED整文件有界审查见[回执](../acceptance/fred-closeout-review-20260919.json)和[边界清单](fred-review-boundaries.md)：源码全文已读，修复Content-Length与实际长度不一致准入。36项FRED/381项全量通过；vintages范围绑定、独立生命周期复核和默认HTTPS证据未闭环，保持PARTIAL。

2026-09-19 vintages范围绑定见[回执](../acceptance/fred-vintage-range-review-20260919.json)：显式边界回显与逐项闭区间校验完成，空结果/单边/倒序保留；CLI越界不写capture。38项FRED/383项全量通过，独立生命周期复核与默认HTTPS仍待验。

2026-09-19 FRED独立复核和默认HTTPS验收见[回执](../acceptance/fred-https-review-20260919.json)：两项发现修复并按最终hash独立复验，44项FRED/389项全量通过。FRED转REVIEWED_BOUNDED，累计10已审/4局部/1待审；真实Provider和跨平台仍未验证，下一模块yfinance。

2026-09-19 yfinance缺失准入见[回执](../acceptance/yfinance-admission-review-20260919.json)：坏搜索行整批拒绝、全缺失行情/必需表形成gap、非有限Decimal统一为缺失，零及空公司行动保留。12项target/393项全量与独立复验通过；转PARTIAL，当前10已审/5局部/0待审，数值/表结构/日期/真实Provider未闭环。

2026-09-19 yfinance表结构见[回执](../acceptance/yfinance-frame-review-20260919.json)：按位置导出避免重复标签重选、完整维度先验再截列；独立发现零列pandas夹具差异并修复。15项target/396项全量通过；真实pandas runtime、数值/日期仍未闭环。

2026-09-19 yfinance快照数值类型见[回执](../acceptance/yfinance-numeric-review-20260919.json)：九个行情字段归一化后拒绝bool/字符串/容器，保留有限数字/零/缺失。17项target/398项全量通过，独立99项边界矩阵通过；表内数值/日期另待审，仍PARTIAL。

2026-09-19 yfinance表内数值见[回执](../acceptance/yfinance-cells-review-20260919.json)：完整行归一化后校验数值类型再截列，corporate-actions的Dividends FX有显式文本例外。独立发现误拒合法币种列并修复，20项target/401项全量通过；真实pandas、NA/NaT及日期未闭环。

2026-09-19 yfinance日期见[回执](../acceptance/yfinance-dates-review-20260919.json)：history请求闭区间拒绝越界，actions先验日期再过滤，时间戳按自身日历日判断。23项target/404项全量通过，独立复核与CLI不capture验证完成；真实pandas、序列化及整文件收口仍待验。

2026-09-19 yfinance真实pandas见[回执](../acceptance/yfinance-pandas-review-20260919.json)：独立临时环境pandas3.0.6/yfinance1.7.0复现并修复NA/NaT字符串化，27项target/408项全量无跳过通过，独立验证导出精度与null。原失效data环境未改、真实Provider未验，模块仍PARTIAL。

2026-09-19 yfinance整文件收口见[回执](../acceptance/yfinance-closeout-review-20260919.json)：补连接超时分类、修复损坏Unicode导出逃逸；29项target/410项全量无跳过，最终hash独立复核无剩余已验证阻断。转REVIEWED_BOUNDED，当前11已审/4局部/0待审；真实Yahoo和原data环境另列限制。

2026-09-19 CLI错误分类见[回执](../acceptance/cli-provider-errors-review-20260919.json)：yfinance缺依赖3、格式错误6、暂时故障5、其他Provider4，历史4码格式测试按新合同更新。25项target/411项全量通过，四类子进程无capture与独立复核通过；CLI仍PARTIAL。

2026-09-19 CLI前置校验见[回执](../acceptance/cli-preflight-review-20260919.json)：规范日期解析、capture参数在凭据/Provider之前拒绝；跨3Provider共9项子进程及独立3项非法日期CLI验证通过。全量413项通过；CLI仍PARTIAL。

2026-09-19 Provider参数冲突见[回执](../acceptance/cli-provider-conflicts-review-20260919.json)：yfinance不再静默忽略thscode/thscodes（含空串），五条symbol路由验证；全量414项通过，独立复核Fuyao和search未受影响。CLI仍PARTIAL。

2026-09-19 可选空日期见[回执](../acceptance/cli-empty-dates-review-20260919.json)：start/end/as-known-on显式空串拒绝，None才表示省略，单边/双边有效参数保留。全量415项与独立37项日期矩阵通过；CLI仍PARTIAL。

2026-09-19 CLI运行环境见[回执](../acceptance/cli-runtime-review-20260919.json)：显式解释器失效/启动失败转配置错误，默认fallback保留；实际launcher与跨venv正例独立验证。全量418项通过，未修改全局/用户失效环境，CLI仍PARTIAL。

2026-09-19 CLI依赖探测修复：UnicodeError及本进程find_spec的ImportError/ValueError转结构化诊断；全量420项、源码19项、打包8项通过，独立复核KEEP，安装71文件一致。CLI仍PARTIAL。 见[依赖探测验收](../acceptance/cli-probe-review-20260919.json)。

2026-09-19 doctor/研究计划/采集三处yfinance探测接入共用错误处理；423项全量、19项源码、8项打包通过，独立复核KEEP，71文件安装一致。真实doctor子进程及main collect夹具分别验证，CLI仍PARTIAL。见[验收](../acceptance/cli-yfinance-probe-review-20260919.json)。

2026-09-19 Fuyao凭据替换窗口、读取上限与截断前脱敏已修复并独立复核；428项全量、19项源码、8项打包通过，71文件安装一致。真实CLI验证regular/FIFO替换在请求前拒绝；POSIX本地边界，未用真实凭据或联网。CLI仍PARTIAL，剩余分支见cli-input-boundaries.md。见[回执](../acceptance/fuyao-credential-review-20260919.json)。

2026-09-19 Fuyao传输与响应有界整改：跳转限制/有界drain/关闭/长度核对/JSON异常/有限Retry-After；独立复核发现的cleanup覆盖P2已修复并复验。442项全量、19项源码、8项打包通过，71文件安装一致。默认opener本地TLS验收，不代表真实服务数据语义或全CLI封口。见[回执](../acceptance/fuyao-transport-review-20260919.json)。

2026-09-19 Fuyao重复JSON键及成功null准入已修复并独立复核，合法空列表与错误null保留；成功null拒绝是本适配器策略，非官方逐接口明文禁止。445项全量、19项源码、8项打包通过，71文件安装一致；真实CLI合成响应证明capture前拒绝。CLI仍PARTIAL。见[回执](../acceptance/fuyao-response-review-20260919.json)。

2026-09-19 Fuyao snapshot/valuations CLI标的绑定和缺项提示已验，非法响应capture前失败；20个真实CLI合成案例，447项全量、19项源码、8项打包通过，独立复核KEEP，71文件安装一致。不证明Provider自报身份或数值真实，不覆盖直接client全部接口；CLI仍PARTIAL。见[回执](../acceptance/fuyao-identity-review-20260919.json)。

2026-09-19 批量缺失标的由研究层按请求/返回行识别为gap，capture完整性、resume、status、引用排除与finalize PARTIAL贯通。449项全量、49项research、19项源码、8项打包通过；独立复核KEEP，71文件安装一致。临时真实工作区+合成runner，不是联网研究验收；research_run仍PARTIAL。见[回执](../acceptance/research-missing-rows-review-20260919.json)。

2026-09-19 Fuyao raw capture与normalized数据/来源时间戳绑定已验，保留Decimal字符串与calendar过滤；真实CLI合成产物及status/resume篡改回归。452项全量、19项源码、8项打包通过，独立复核50项KEEP，71文件安装一致。仅本地一致性，非远端真实性；research_run仍PARTIAL。见[回执](../acceptance/research-capture-content-review-20260919.json)。

2026-09-19 Fuyao case/request.json/normalized参数三方绑定及manifest请求哈希已验。独立复核发现None默认值不一致并已修复复验；456项全量、19项源码、8项打包通过，71文件安装一致。旧缺request档案拒绝，非远端执行真实性证明；research_run仍PARTIAL。见[回执](../acceptance/research-request-binding-review-20260919.json)。

2026-09-19 yfinance case/request/normalized/export绑定及manifest request哈希已验；11步实际CLI+adapter export合成链路通过。459项全量、19项源码、8项打包通过，独立复核10项KEEP，71文件安装一致。未联网或验证远端真实性；research_run仍PARTIAL。见[回执](../acceptance/research-yfinance-binding-review-20260919.json)。

2026-09-19 manifest覆盖与case/证据清单完整比对已验；6种更新receipt哈希后的遗漏/改写拒绝，普通内容漂移保留STALE，缺绑定旧manifest拒绝且封存字节不变。460项全量、19项源码、8项打包通过，独立复核48项KEEP，71文件安装一致。research_run仍PARTIAL，非外部签名保证。见[回执](../acceptance/research-manifest-coverage-review-20260919.json)。

2026-09-19 finalized事件必须唯一末尾并绑定当前manifest/gap且有verified receipt；拒绝反向重建收据，保留先收据后事件的正常恢复。7变种及已有进程恢复通过；461项全量、19项源码、8项打包通过，独立复核48项KEEP，71文件安装一致。research_run仍PARTIAL。见[回执](../acceptance/research-finalization-binding-review-20260919.json)。

2026-09-19 state运行时输入合同补齐字段/严格整数/修订事件数/日期时区，16畸形CLI场景拒绝且无写入；独立发现24:00宽容解析并显式封堵。463项全量、19项源码、8项打包通过，独立复核KEEP，71文件安装一致，原进程恢复保留；research_run仍PARTIAL。见[回执](../acceptance/research-state-contract-review-20260919.json)。

## 2026-09-19 有限集中收口

15 个顶层运行时文件全部 REVIEWED_BOUNDED，0 PARTIAL/0 PENDING；CLI、research、tracking 与 renderer 完成独立复核及必要修复，473 项回归、源码19项、打包8项验证。真实 WeasyPrint 三页 PDF 和 browser67 宽/窄、明/暗 HTML 检查完成。非运行时合同与宿主验收单列，详见 core-closeout-20260919.json 及 acceptance-closeout.md。无全仓评分、commit、push、发布或应用建设。
