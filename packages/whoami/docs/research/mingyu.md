# Mingyu：固定版本研究与吸收记录

核验日期：2026-09-23。仓库 [Brhiza/mingyu](https://github.com/Brhiza/mingyu)，本轮固定提交 `de2bac7814d1f0a133c5457cd356553e477cf018`。八份实际读取文件的 URL、字节数和 SHA-256 见 [source-manifest.json](source-manifest.json)。未安装或运行其核心，不是全仓审查或正确性认证。

## OBSERVED：源码能力

- `packages/core/src/bazi/baziAnalysisPipeline.ts`：编排根气、成局、扶助、制约、季节、日主强弱、格局和用神。说明它有可读的分析链；函数存在不证明判定正确。
- `packages/core/src/bazi/baziRootAdjudication.ts`：将藏干根事实与受冲后的作用裁定分层，区分部分墓库土及季节情形。注释引用传统典籍，但本轮未完成原文与所有条件逐条校勘。
- `packages/core/src/ziwei/iztro/build-evidence-pool.ts`：组织宫星、四化、运限落宫、三方四正、缺口与限制；数值 priority 用于证据排序，不应作为现实事件概率。
- `packages/core/src/synthesis/corroboration.ts`：可见羊刃/煞曜、天乙/贵人星的条件化合参结构。本轮仅抽查部分源码，未验证全部分支；不认定为完整双盘合参标准。
- `skills/mingyu/references/reasoning-checks.md`：复核问题主体、时空、取用、支持与反证、时间窗口和输出资料。
- `benchmarks/fortune-contest/README.md`：声明 2022—2026 共 40 命例、200 题；2022—2025 导入 MingLi-Bench，2026 根据比赛原题/答案整理。本轮只核对说明，未核对新增题目与官方原卷一致性。不可把旧年份重复计算为独立测试集。

## 许可与使用方式

`packages/core/package.json` 的 version 为 `0.4.0`，license 为 `AGPL-3.0-only`，并有对应 LICENSE。当前 whoami 未新增该依赖、未复制其源码或提示词。直接采用代码的许可方案须单独明确；本轮仅记录来源与机制，并基于 whoami 已有藏干、柱位与六冲数据独立实现事实联结。未来实现传统裁定前仍应核验传统来源和适用边界。

## 本轮已吸收

“结构事实与作用判断分层”用于通根证据：保留原 roots，新增 rootDetails，列具体藏干、同干/同五行区别及直接六冲来源。无旺衰评分、无自动冲毁/从格/用神判断。运行时规则引导宿主说明支持、反证、缺口，避免将同源标签当成多份证据。

没有照搬 Mingyu 的受冲裁定、调候表、用神策略、合参结论或数值优先级。本轮行为回归验证的是事实联结，不是命理预测。

## 后续取舍

优先研究旺衰候选的必要条件、格局/调候/扶抑的分歧裁决、紫微限运四化、双盘冲突。每项需形成来源—前提—反例—输出限制，再进入代码；仅凭函数名或典籍标题不升级为已验证规则。完整差距见 [分析层路线](analysis-roadmap.md)。
