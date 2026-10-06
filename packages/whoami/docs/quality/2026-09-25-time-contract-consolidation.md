# Skill 时间契约与模块接口收敛审计

日期：2026-09-25。结论：时间规则已从 Skill 超长段落和报告契约的重复副本收敛到单一权威文件。默认 Skill 上下文更短，详细规则按任务加载；报告 schema、错误优先级、运行行为和既有冻结验收均保持不变。

## 现场问题与处理

改动前，[SKILL.md](../../SKILL.md)只有 43 行却达到 11,070 字节，其中一整行同时描述冻结日期、历法年界、细分时间、IANA/DST、offset、绝对时刻、区间、时长、重复日程、模糊范围、多年范围及 timingChain。相同细节又存在于原报告契约，任何规则调整都要修改至少两份长文本，且默认加载 Skill 时会携带大量只在时间问题中需要的例子。

新增[时间表达与 evidence 粒度契约](../../references/time.md)，集中规定模块接口、总校验顺序、冻结基准、相对年份、历法、年度以下粒度、日期与时区合法性、DST、绝对时刻、区间、时长、重复日程、模糊范围和多年闭区间。[报告契约](../../references/report.md)继续负责 schema、正文、论证、引用与渲染，只链接时间权威；Skill 保留必须加载时间契约的触发条件、不可绕过的总顺序和年度 evidence 边界。

结果：Skill 从 11,070 字节降至 7,580 字节，减少 3,490 字节、约 31.5%；报告契约从 25,980 字节降至 16,808 字节，时间细节进入 11,914 字节、带章节的按需文档。这里优化的是默认加载和单一权威，并未用删减强制程度换取长度。

## 程序接口与等价证据

[report-time.ts](../../src/report-time.ts)仍只向报告层提供 `validIsoDate`、`referencedRelativeYears`、`validateReportTemporalText`。新增[接口合同测试](../../tests/report-time.test.ts)，锁定这三个导出，防止解析内部实现重新渗回报告层。静态审计从实现提取 30 个 `InputError.code`，时间契约逐项覆盖 30/30；`report.ts` 继续只调用上述接口，没有重新引入 `Temporal` 或出生时间解析器。

本轮没有新增 semantic-forward 套件。合同重排没有增加或改变用户行为；创建新套件只会复制现有 001—023 的语义样例。现有时间模块、完整报告和 23 份冻结 manifest 已覆盖行为保持，历史 Skill 快照继续保留原字节与原哈希，不随当前 Skill 改写。

## 验证结果

- `npm run check`：173/173 PASS；TypeScript strict 与 build PASS。
- 23 份 semantic-forward manifest 由当前构建版全部重放成功；所有验收仍因缺可信 runtime receipt 保持 partial，历史内容 review 状态不改写。
- Skill quick_validate PASS。
- 时间实现错误码 30 个，权威契约覆盖 30/30。
- AGENTS/README/SKILL/references/docs 共 80 个现行 Markdown、401 个本地链接无缺失；不读取 private，private 与 node_modules 之外 175 个 JSON 均可解析。
- `openspec/` 与 `.git/` 均不存在；没有全局安装、发布、推送或外部动作。

这项 PASS 只证明文档权威收敛、模块公开接口和现有工程行为可回归。它不证明宿主模型已实际加载某个引用文件，也不证明传统规则、解释质量或现实预测有效。
