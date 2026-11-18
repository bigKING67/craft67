# Drama Craft 包级规则

本包只交付一个可安装产品：`skills/drama-craft/`。根目录文件（README、CHANGELOG、tests、scripts）属于源码治理与校验，不得成为已安装 Skill 的运行时依赖。

## 能力边界

- 负责：AI 剧情短视频/短剧的剧情设计、beat 拆解、分镜交付、变量迭代与复盘归类。
- 不负责：投放排期与预算、达人筛选与佣金、账号运营 SOP、品牌战略、产品 UI，以及投资或工程审查。
- 商业与投放判断交给 commerce 系列 Skill；创意概念与图像 Brief 的通用方法交给 creative-craft。本包只回答"这条剧情怎么排、怎么改"。

## 目录职责

| 路径 | 职责 |
| --- | --- |
| `skills/drama-craft/SKILL.md` | 入口：三条铁律与适用范围、等价硬约束、beat 架构、工作流、生成交接、生产硬约束、路由表 |
| `skills/drama-craft/references/story-patterns.md` | 主原型与组件两层、P1–P11 原型库 + 证据等级与复核 + 观察池 + 采集字段 |
| `skills/drama-craft/references/production-craft.md` | 场景、人像、服化道、上妆手法、剪辑、生成交接、一致性 |
| `skills/drama-craft/references/iteration-loop.md` | 百分比分段诊断、基线口径、最小判读条件、变量矩阵、停止条件、分类型验收 |
| `skills/drama-craft/references/output-templates.md` | beat sheet、分镜表（含素材来源与参考资产）、变量矩阵、复盘卡、机制三种结构 |
| `skills/drama-craft/references/worked-example.md` | 填完的 P1 20s 端到端范例：输入 → beat → 分镜 → 生成交接 → 矩阵 → 复盘 → 验收 |
| `scripts/check.py` | Skill 结构、链接、原型编号与逐原型字段、铁律位置与适用范围、关键约束与占位声明；包文档与版本一致性 |
| `adapters/README.md` | 各宿主安装目标、发现方式与验证状态；只写安装与限制，不复制专业规则 |
| `tests/` | 校验器的正向与反向回归 |

## 修改规则

- 新增主原型时同步五处：`story-patterns.md` 加编号小节（P1–P11 连续，新增则顺延编号并更新 `MAIN_PROTOTYPES`）、`scripts/check.py` 的 `PROTOTYPE` 期望区间、`README.md` 与 `CHANGELOG.md` 的原型区间与数量（检查器会比对）、必要时补 `worked-example.md` 或新范例。
- 原型只允许一主标签；把"观察池"条目转正需要 ≥5 条同结构样本台账，并在 CHANGELOG 写明来源与日期。
- 铁律（施压者非主角、主角几乎不反驳、机制带数字）及其**适用范围／等价硬约束**改动属于行为变更，必须升 minor 版本并更新 CHANGELOG。P6–P8 与组件 P9、P10 不适用三条铁律，禁止为了让剧本"符合铁律"回写施压者。
- 出稿验收分"通用项"与分原型追加项：向验收清单新增条款时，先判断它适用于全部原型还是仅 P1–P5、P11，不要写成无差别硬要求。
- 诊断与迭代口径以播放进度百分比为准，不回到固定秒数；基线口径与最小判读条件改动同样算行为变更。
- 新增或修改镜头字段时，保证 `素材来源`（AI / 实拍 / 图库）与 `参考资产`（CH/SC/PD 编号）两列在各模板中同时存在，否则跨镜一致性检查不可执行。
- 原型库只能标"已归类"并附证据等级；不得写"已验证"。台账不足 5 条的结构只能进观察池，90 天未复核的降级回观察池。
- 原型库、模板与范例里的数字（价格、时长、比例）都是结构占位，必须保留"不得直接作为宣称"的说明；不得把真实品牌、账号或未授权素材写成资产清单，引用样例只保留品类与结构。
- 修改后运行 `python3 scripts/check.py`（含包文档与版本一致性）与 `python3 -m unittest discover -s tests -p 'test_*.py'`；从仓库根再跑 `python3 scripts/check.py --package drama-craft`。改 Skill 内容后同步本机安装副本 `~/.agents/skills/drama-craft` 并核对差异。

## 数据来源

原型库与生产约束来自内容团队的两份内部文档（爆款 AI 剧情采集分类、AI 剧情方向分析），属于**抽样归类**（证据等级 C）而非平台规则或转化承诺。文档里的商品名、价格只为说明结构，不代表当前在售状态或效果；引用前需按当期实际机制核对，功效与价格宣称的合规结论以 commerce 系列 claim/currentness 为上游。
