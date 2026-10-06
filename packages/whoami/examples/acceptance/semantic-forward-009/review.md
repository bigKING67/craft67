# 维护者复核

状态：PASS（内容合同），运行身份：UNVERIFIED。

任务与量表在两阶段答复和报告前固定。本样例由主代理编写并复核，不是独立模型盲测。baseline context 的 years 只有 2026；178 个非空白字符的第一阶段答复把明年解析为 2027，明确指出当前证据缺年并停止，没有编造 2027 四化、宫职或生成报告。

expanded context 由同一 input 重算，years 精确为 2026/2027。它与 baseline 的 chartId 相同、evidenceId 不同。v6 报告绑定 expanded evidenceId 与 `2026-09-25 / Asia/Shanghai`，事业段保留明年=2027，同时绑定 `ziwei-career` 和 `ziwei-timing`；timingChain.years 精确为 `[2026, 2027]`，现实岗位、考核、权限、组织机会及逐年作用关系缺口仍在，相关段落保持 unresolved。

第二阶段答复为 434 个非空白 Unicode 字符，说明补算只修复年份事实缺失，没有把证据齐全偷换成升职结论。responseClaims 逐段绑定 report claim、论证引用与未决状态。五项 review 计数均为零。

没有可信 runtime receipt，最终 acceptance 状态应保持 partial；PASS 不证明宿主身份、模型普遍表现、紫微传统规则或现实预测有效。
