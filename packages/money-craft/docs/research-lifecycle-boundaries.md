# 研究生命周期验收边界

当前结论（2026-09-19）：research_run.py 与 tracking_workflow.py 已完成声明范围整文件及独立复核，状态为 `REVIEWED_BOUNDED`，见[统一收口记录](../acceptance/core-closeout-20260919.json)。本页保留历史机制证据；旧快照中的待审不代表当前仍有同一缺口。支持范围仍仅为本机受控工作区，不扩展为正式 money 档案、任意平台或自动恢复。

## 已验证的行为

| 场景 | 当前行为与证据 |
|---|---|
| 参与协议的并发操作 | init/collect/import/status/finalize 共用非阻塞锁；获取锁冲突返回 busy。已有 root 的 init 直接拒绝；目标尚未发布时，其他入口可返回 missing_workspace。见[初始化](../acceptance/research-init-lock-20260917.json)和[工作区锁](../acceptance/research-workspace-lock-20260917.json)。 |
| 单文件不覆盖 | `atomic_bytes(replace=False)` 的完整 staging 通过硬链接发布，已有目标拒绝；不支持硬链接时不降级为覆盖。其他替换写入及目录发布不属于此项。见[不覆盖发布](../acceptance/research-no-clobber-20260917.json)。 |
| 官方导入中断 | 清单发布后的异常保留被引用证据；缺事件、已登记待导入来源的 canonical 文件或标准暂存名阻止准出。见[导入中断](../acceptance/research-import-interruption-20260917.json)、[孤儿检测](../acceptance/research-orphan-import-20260917.json)。 |
| 采集中断 | 已登记 capture 缺标准化结果或标准暂存名残留时拒绝再次请求。结果齐全而仅采集事件失败时，可零请求 resume。见[采集中断](../acceptance/research-collection-interruption-20260917.json)。 |
| 封存后写入及证据漂移 | 收据存在后禁止采集/导入；校验 capture 身份、哈希与字节数；旧版正常封存重复 finalize 不改文件。见[证据生命周期](../acceptance/research-evidence-lifecycle-20260917.json)。 |
| 完成事件恢复 | 收据有效而缺 finalized 事件时不报完整；重试核验后仅补事件。漂移则拒绝。见[封存恢复](../acceptance/research-finalize-recovery-20260917.json)。 |
| 事件容量耗尽 | collect/import/首次或恢复 finalize 在相关写入前拒绝；已完整封存仍可幂等核验。本轮补齐 collect 首次与 resume 的零请求、零写入检查。见[收口检查](../acceptance/research-lifecycle-boundaries-20260917.json)。 |

## 收口范围与单列证据

输入、状态/事件、异常 JSON 与初始化 I/O 已在集中收口中核验；源码整文件读取不等于逐分支动态覆盖。Skill 合同、报告产物与固定版本自然语言验收各有独立记录，当前进度以[统一说明](acceptance-closeout.md)为准。

## 当前不提供的恢复能力

- 不根据孤儿 raw capture 自动重建标准化结果，不自动补造官方导入完成事件。
- 不自动删除或接纳未知残留、旧 staging 或强杀留下的收据硬链接。
- 不提供跨多文件的通用事务 journal、回滚或重放。

处置路径：`incomplete_import` / `incomplete_collection` 时保留旧工作区，另建运行并重新采集、导入原始材料。仅已有完整结果的采集 resume、缺 finalized 事件的核验后补记属于已验证恢复。初始化重试重新构建 staging，不恢复旧 staging。禁止为了让检查通过而手改事件或收据。

以上限制必须保留在使用说明中；若后续需求需要原地恢复或清理，应先明确可恢复输入、数据归属、冲突处置和验证标准，再实现相应能力。

## 环境与证据限制

- 并发/强杀证据来自本机 POSIX 与离线合成材料。Windows、网络文件系统、真实不支持硬链接的卷和断电耐久性尚未验收。
- 锁只协调使用同一协议的入口；外部直接写入、删除或替换锁文件不在保证范围内。
- 本地完整性、事件存在和离线测试不证明外部来源真实性、论点支持、来源时效或预测表现。
- 应用仍后置；本文件不授予 commit、push、发布、交易或账户操作授权。

## 批量缺失标的的证据状态

2026-09-19：Fuyao snapshot/valuations 的研究操作按case请求标的与normalized data.item实际返回标识核对，不以warnings文本作判断。成功但缺项进入provider_gap（missing_requested_securities），collection valid=false；resume和status重复核对，provider_evidence显示complete_with_gaps。

成功缺项响应仍保留原始capture并验证哈希，manifest记录normalized-response/raw-response/capture-metadata，不误记为无响应的normalized-error。缺项来源整体不进入passed/imported引用集合；若将来需要引用其中已返回行，应新增明确的细粒度证据合同，当前不自动放行。

既有finalize允许在官方证据及报告等门禁通过后完成带缺口档案，但收据evidence_coverage必须PARTIAL且列出provider_gaps；complete表示流程产物完整，不代表证据齐全。旧的batch normalized成功输出缺少item或身份错配时拒绝读取，不静默升级为通过。回归使用临时工作区与合成Provider runner，非真实联网采集，见[缺项链路验收](../acceptance/research-missing-rows-review-20260919.json)。

## Fuyao 原始响应与规范化内容一致性

2026-09-19：validate_provider_capture在capture元数据及原始文件哈希检查后，重建Fuyao的CLI内容投影并比较normalized data与source_timestamp_ms，同时核对原始code=0、request_id及data对象。JSON小数按Decimal字符串化；calendar按case的start/end重放本地过滤。比较保留类型区别，True不能冒充1。原始重复JSON键、异常数值及超限输入被拒绝，诊断不包含响应内容。

此门禁随capture校验覆盖collect/resume/status、引用源检查和manifest生成。它证明保留的两种表示内容一致，不证明远端原始数据真实、完整或新鲜；规范化parameters与原始请求参数绑定、其他Provider投影仍未在本轮封口。合法日历过滤及Decimal转换通过真实CLI子进程合成响应产物复验，见[内容一致性验收](../acceptance/research-capture-content-review-20260919.json)。

## Fuyao 研究请求的三方绑定

2026-09-19：Fuyao capture要求request.json存在且为可读常规JSON文件。研究层从case中的operation/arguments重建预期路径及CLI的sanitized参数，分别与request.json和normalized.parameters比较；同时检查request schema/provider/operation/GET/path。比较保留类型差异。覆盖search、snapshot、valuations、history、三类financials、indicators、corporate-actions及calendar；支持CLI的上海时区日期转毫秒、默认值与本地过滤参数表达。

manifest为成功Fuyao响应（含成功但数据缺项）加入sanitized-request的文件哈希。只改其中一份或同时改request与normalized参数而不符合case均拒绝；旧capture缺request.json不能静默通过。预期投影与真实CLI prepare_operation对比验证，测试夹具通过真实CLI生成参数而非复用验证器逻辑。

本轮只证明本地请求记录和研究case一致，不证明Provider实际执行了请求、case研究意图正确或整套文件未被协同重写。其他Provider请求绑定仍单列。见[请求绑定验收](../acceptance/research-request-binding-review-20260919.json)。

独立复核修正：operation_command会跳过值为None的选项，因此请求投影对search.limit、history.interval/adjust、financials.period同样使用CLI默认值；仅None触发回退，不把0或空字符串当作省略。新增真实CLI对照覆盖此边界。

## yfinance 请求与适配器导出绑定

2026-09-19：yfinance复用请求记录/case/normalized参数三方绑定，覆盖search、snapshot、valuations、history、financials、corporate-actions；按CLI默认值处理None、symbol大写及forward→auto。request.json参数保留可选None，而adapter export参数按适配器规则移除None，两者分别与各自预期比较。

adapter-export额外核对schema/provider/operation/symbol/parameters/fetched_at/data及source_timestamp_ms，禁止重复JSON键、非有限JSON常量及超限导出；数据以类型敏感的JSON比较。request_id须为None。manifest加入sanitized-request哈希；Fuyao原有绑定继续生效。

临时工作区的完整yfinance研究操作链通过实际CLI子进程和真实适配器request/export流程运行，只有_execute的数据获取替换为合成夹具，不访问Yahoo。验证collect/status/resume/manifest和内容篡改拒绝，不等于外部来源真实性、真实宿主自然语言注入或真实网络验收。yfinance_version是被保留的导出元信息，不与当前安装版本强制相等。见[yfinance绑定验收](../acceptance/research-yfinance-binding-review-20260919.json)。

## 完成收据的证据清单覆盖

2026-09-19：receipt_status不再只遍历manifest自行声明的文件集合。先验证收据绑定文件及manifest所列证据文件的安全路径与哈希，保留内容漂移的STALE分类；再从当前plan/case和已经验证的Provider/官方证据重新生成预期manifest，按类型敏感的JSON比较确认完整一致。来源、文件、角色、研究身份、数量或重复项不匹配时receipt_integrity为INVALID，complete=false，已封存工作区不可再次finalize覆盖。

回归在真实临时已完成工作区中同时修改manifest与receipt中的manifest哈希，覆盖清空来源、删文件、改角色、改身份、错误数量和重复来源；均不能仅凭新的自洽哈希通过。此检查不提供外部签名，不保证抵抗plan/case/证据/全部元数据同时协调改写；它确保本地manifest覆盖当前工作区应绑定的集合。旧收据可省略assessment的兼容规则保留，但旧manifest若缺当前要求的证据绑定，不自动迁移或默认为有效。见[manifest覆盖验收](../acceptance/research-manifest-coverage-review-20260919.json)。

## 封存事件与当前档案绑定

2026-09-19：状态检查不再仅凭存在名为finalized的事件认定封存完成。该事件必须唯一、位于events末尾，details.manifest_sha256须等于当前manifest哈希，provider_gap_count必须为严格整数且等于当前缺口数（bool不算整数）。不一致时complete=false并输出事件诊断；finalize拒绝追加或覆盖，封存文件保持不变。

完全没有finalized事件仍属于既有可恢复窗口：先复核已写收据/manifest/证据，满足原门禁后才补事件；新规则不取消该恢复路径。新测试覆盖错误哈希、错误计数、bool计数、缺details、重复finalized和finalized后追加事件。这里只验证本地事件一致性，不提供外部签名、不可篡改时间线或抵抗整套文件协同重写的保证。见[封存事件验收](../acceptance/research-finalization-binding-review-20260919.json)。

独立复核补充：已有finalized事件必须同时有可验证的completion receipt。事件存在但收据丢失/无效属于发布顺序不可能产生的反向状态，不允许重建收据或重写审计产物；finalize写入前拒绝，新增第7类缺收据回归保留全部现存文件。只有收据有效且事件缺失仍可按原流程补记事件。

## run-state 输入合同

2026-09-19：运行时按state schema要求检查顶层及event字段集合，拒绝缺项和额外项；校验run_id/plan hash、严格整数revision/sequence（bool不通过），要求revision等于事件数量且sequence连续。事件type为非空字符串、details为对象；created_at及event.at必须为可解析且带时区的ISO日期时间，并约束时区偏移范围。不依赖可选jsonschema包。

不会要求时间戳单调递增：系统时钟回拨不应破坏合法顺序，事件顺序由sequence表达。合法既有中断恢复继续适用；错误state在读取入口返回invalid_state，不自动迁移或修复。真实CLI回归验证畸形状态不产生traceback且文件不被改写。见[state合同验收](../acceptance/research-state-contract-review-20260919.json)。

时间合同限定常规非闰秒RFC3339表达：小时00..23、分秒00..59，不接受24:00自动归次日。独立复核发现Python3.14会宽容解析24:00，现用显式范围消除此跨版本差异；16个畸形状态CLI案例覆盖该边界。

## 运行时完整性细节（自 company-research reference 迁出）

封存收据存在后，`collect`（含 `--resume`）与 `import-official` 拒绝修改该工作区，补充证据须新建研究运行。成功采集必须保留 `capture.json`：采集、恢复、状态检查和封存核对来源编号、Provider、操作、时间、request ID，以及原始响应的 SHA-256 与字节数。元数据缺失或不匹配、响应发生漂移时返回结构化错误；不会重新计算哈希来接纳已改变的响应。新封存的 manifest 同时绑定 capture 元数据，额外字段被改动也会令收据失效。旧工作区缺少采集元数据时应重新采集到新运行，不自动补造历史哈希。官方导入若在清单发布后、事件记录完成前中断，保留已发布证据并返回 `incomplete_import`，拒绝继续状态准出或封存；保留现场并新建研究运行，不自行补造完成事件。清单发布前的失败仅在确认原清单未变且文件属于本次导入时清理。清单发布前中断留下的官方文件（已登记且仍待导入的来源）或标准命名的导入暂存文件也返回 `incomplete_import`，包括可选来源；检查不读取、接纳或删除这些文件。保留旧工作区，新建运行后重新采集与导入原始材料；原地自动恢复及其他类型的孤儿文件仍未闭环。这些是本地完整性校验，不能证明外部来源真实性；禁止覆盖的单文件写入通过同目录硬链接原子发布，竞争者返回 `existing_artifact`，不支持硬链接的文件系统直接报错，不回退到可能覆盖的写法。`collect`（含 CLI 的 Provider 预检查）、`import-official`、`status` 和 `finalize` 在读取工作区前取得共用非阻塞锁，占用时返回 `workspace_busy`，待当前操作结束后重试。锁文件位于工作区旁的 `.<workspace-name>.research.lock`，不进入封存目录；释放后保留文件，不能在操作进行中删除或替换它，否则会破坏互斥。正常退出、异常退出和进程终止会释放操作系统锁。此锁只协调这些入口，不保护外部编辑器直接改文件；初始化也使用同一把锁，在构建暂存目录前加锁并在锁内再次检查目标；竞争者返回 `workspace_busy`，已有目标返回 `existing_workspace`。发布前进程终止后可重新初始化，原暂存目录保留在旁，不自动复用或删除。外部绕过锁创建/替换目录、多文件提交中断恢复、Windows 和网络文件系统运行验收仍待补齐。

采集若已发布已登记来源的 capture 目录、尚未写入对应标准化结果，或留下标准 UUID 命名的 capture 暂存目录，后续入口返回 `incomplete_collection`；不重复请求 Provider、不从残留数据推造标准化结果、不清理现场。应保留原运行并新建运行重新采集。若所有标准化结果及对应 capture 完整，仅汇总/采集事件写入中断，可用 `collect --resume` 重新校验并复用已有结果，补写汇总和事件；结果中的 `network_requests_attempted` 应为 0。部分来源尚未采集时，resume 仍可能请求那些缺失来源。

采集在调用 Provider 或更新汇总前检查事件容量；达到上限返回 `state_limit`，首次与 resume 均不请求数据、不改写工作区。

若收据已发布但 `finalized` 完成事件未记入，`status` 返回 `complete=false`、`stages.finalization_event=pending`，并提示重试 `finalize`。重试在锁内重新验证收据绑定、证据及报告；仅在全部通过后补记当前时间的完成事件，不改写原收据、manifest 或审计文件。已有事件不重复追加；证据漂移或事件容量耗尽时拒绝恢复。此路径只恢复完成事件，不修复其他中断、不清理强杀遗留暂存文件，也不证明断电耐久性。
