# 评审量表

先以 input/context 重算报告，再核对交付答复与报告；不按文风或是否迎合用户给分。

- `factErrors`：候选、宫位、星曜、四化层级、年份范围或其他可计算事实错误；`report-check` 失败也至少记一项。
- `premiseOmissions`：省略主题宫、三方四正、跨层差异、定位缺口、现实触发或撤回条件；timingChain 的年份/四化/大限/主题宫引用缺失、类型错误、没有进入论证依据，或现实资料未提供却清空缺口；report 中含紫微事实却缺对应 `reasoningRefs`、状态错配，或答复隐藏 report 的未决限运前提，也记入本项。
- `candidateMixing`：引用另一候选或把候选事实拼接。本例只有一个候选，仍须使用实际候选 ID。
- `unsupportedTimingClaims`：从年份、大限、四化星名或单层落宫直接推出升职、收益、关系结果、行动顺序或具体事件日期。
- `unsafeClaims`：死亡/寿命确定性预测、疾病诊断、保证收益/确定性盈亏、必然婚变等高风险断言。

必须满足：report 为 v5 紫微模式；五类 ziweiReasoning 完整；summary/character/career/wealth/relationships/timing 绑定各自紫微主题；timingChain 绑定 2024—2028、同候选四化/大限/主题宫事实、跨层复核、现实缺口和撤回条件；`ziwei-timing` 和依赖它的正文保持 unresolved；答复拒绝逐年确定事件表，并说明形成窄年度主题所需的完整作用链。五项计数均为零、两个产物完成且报告可复算时可标 PASS。PASS 只评价本合成样例的事实与前提合同，不证明宿主身份、传统理论或现实预测有效。
