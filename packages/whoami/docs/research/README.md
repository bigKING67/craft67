# 研究索引与吸收决策

初次核验日期：2026-09-23；本轮更新：2026-09-26。精确 commit、文件路径、SHA-256 与大小见 [source-manifest.json](source-manifest.json)。远端 README 不等于完整算法验收。

| 来源 | 定位 | 实际检查 | 决策 |
|---|---|---|---|
| [本地旧 Skill](legacy-bazi.md) | 现状与问题基线 | 入口、CLI、提示词、NOTICE、测试指南 | 保留使用路径思想，独立实现，不复制争议代码 |
| [Yuan](yuan.md) | 统一资料与交付 | 中文 README、八字引擎、紫微领域模型 | 吸收分层和联宫；不吸收隐去分歧或固定权重当真值 |
| [MingLi-Bench](mingli-bench.md) | 评测设计 | 中文 README、LICENSE、160题数据结构 | 按命主拆分，答案隔离，指标分开 |
| [Mingyu](mingyu.md) | 分析规则与证据组织 | 固定提交的八字流程、根气裁定、合参、紫微证据池、复核与评测说明 | 逐项验证后吸收；本轮独立增强根事实，未引入 AGPL 代码 |
| [Fatetell](fatetell.md) | 产品机制与客户端链路 | browser67 页面、公开 JS 与去敏资源路径 | 吸收档案/本命/时序/追问分层，不宣称后台已破解 |

新增基础来源：[lunar-typescript](https://github.com/6tail/lunar-typescript)、[iztro](https://github.com/SylarLong/iztro)、[NOAA 太阳时公式](https://gml.noaa.gov/grad/solcalc/solareqns.PDF)、IANA 时区（运行时版本记录于命盘）。两个排盘依赖均已核验 MIT；仅锁定 npm 依赖，不复制仓库源码。

证据等级：OBSERVED 是直接读到的文件/页面/请求路径；INFERRED 是有依据的机制推断；UNVERIFIED 是未能验证的后台实现或能力。只有完成可复现输入输出验证才能把推断升级。

维护研究文档时只添加影响实现的差异、证据与决策。运行时 Skill 不自动加载全部研究。实际代码边界与当前限制见根 README 与 references，而不是让竞品成为隐式设计权威。

下一阶段差距与本轮状态见 [分析层路线](analysis-roadmap.md)；Fatetell 动态研究按 [有界实验方案](fatetell-experiments.md) 执行，当前尚未开展。

传统规则核验：[月令藏干透出](month-exposure.md)，区分原文转录、校勘/按语与当前独立计算范围。

八字岁运的传统来源、多版本扫描本校勘、反例与吸收边界见[岁运来源审计](bazi-timing.md)；目标章节的段落完整性、实质异文和层次见[整章版本感知校本](bazi-timing-chapter-collation.md)及其[机器可读底稿](bazi-timing-collation.json)，五个扫描见证的逐页字面见[外交转录说明](bazi-timing-diplomatic-transcription.md)与[机器可读转录](bazi-timing-diplomatic-transcription.json)，逐栏回查见[坐标与局部影像定位](bazi-timing-column-locators.md)及其[机器可读坐标](bazi-timing-column-locators.json)，局部版本亲疏信号见[版本关系证据矩阵](bazi-timing-stemma-matrix.md)与[机器矩阵](bazi-timing-stemma-matrix.json)。三个疑难读法已另做[来源隐藏盲审包](bazi-timing-blind-review/README.md)，供两至三位独立审读者逐字复核；当前仅完成材料，不代表已经取得外部意见。运行时按[八字岁运联读](../../references/bazi-timing.md)逐层回配；当前只吸收论证顺序、版本边界和文本层次，不生成固定吉凶、年度评分或事件预测。

财格候选的显干前提与未决条件见 [财格条件研究](wealth-review.md)；正官、七杀、印、食神、伤官五格见 [五格条件研究](pattern-review.md)。

紫微动态依据见 [四化分层与落宫](ziwei-transforms.md)。

普通格的旺衰与扶抑取法见 [来源与范围](strength-balance.md)，运行时流程见 [条件性论证](../../references/strength-balance.md)。

调候目前只吸收一个经扫描本核对的窄条目：[丙火申月的来源边界](climate.md)，运行时按[调候候选复核](../../references/climate.md)执行；它不构成完整调候表或最终用神裁定。

格局、调候与扶抑进入最终取舍时，按[状态形成理由](selection.md)与[运行门槛](../../references/selection.md)区分“候选身份、限定方向、跨口径最终答案”，不按各项 status 投票。

比较如何形成结论的具体示范见 [三类公开命例](classical-strength-cases.md)：原文判断与可计算观察分开，含结构脚本和新例迁移验收。
