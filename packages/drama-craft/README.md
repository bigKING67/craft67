# Drama Craft

电商短视频的 AI 剧情设计与迭代 Skill：把"这条剧情怎么排、下一轮改什么"变成可生产的分镜和可对照的实验。

正式包名与 Skill 调用名为 `drama-craft`。

## 解决什么问题

剧情带货最常见的浪费不是没人写脚本，而是写了没法判断对错：结构靠感觉、改版靠重写、复盘靠点赞。本包提供三层确定性：

1. **结构确定**：11 个已归类原型（证据等级 C，见下方状态说明），每个都有固定思路、情绪路径、爽点与适配条件；真实爆款基本是"钩子 × 主原型 × 转化镜 × 机制"的四段拼接。主原型与组件（P9 钩子、P10 转化镜）分两层，一个项目只选一个主原型。
2. **可拍性确定**：场景、人像、服化道、上妆手法、剪辑方式写成硬约束，并附生成交接表（画幅与安全区、单镜生成档位、口型、参考资产编号、素材来源）；写脚本时就知道哪些画面 AI 做不出来。
3. **迭代确定**：掉点诊断按播放进度百分比分段，配基线口径、最小判读条件、单变量矩阵、冻结不变量与停止条件，让每轮改动可归因。

## 何时用

- 给产品、卖点和机制，要 2–3 个不同机制的剧情方向，各带 beat 与分镜。
- 已有脚本数据不好，要定位掉点并给出单变量改法。
- 有成片要复盘归类，抽成可复用模板。
- 要建原型库、批量产能和迭代记录。

不用于投放排期、达人筛选与佣金、账号运营 SOP、品牌战略，也不用于产品 UI 或工程审查。商业与投放判断用 commerce 系列 Skill；品类功效与价格宣称的合规结论以 commerce 的 claim/currentness 为上游；纯创意概念与图像 Brief 的通用方法用 creative-craft。

## 三条铁律

来自真实爆款抽样，先遵守再谈创新（**适用范围：主原型 P1–P5 与 P11**；P6–P8 用 [SKILL.md](skills/drama-craft/SKILL.md) 的等价硬约束，不要给无冲突原型硬塞施压者）：

1. 施压者永远不是主角——顾客、婆婆、孩子、未婚夫、老公、皇帝。
2. 主角几乎不反驳——反击靠一个动作（试用、上妆、擦唇）或第三方一句真话。
3. 机制压最后 2–4 秒，且必须带具体数字。

## 安装与使用

Skill 内容在 `skills/drama-craft/`。本机多宿主共用 `~/.agents/skills` 一处 canonical 安装，不要向 `~/.codex/skills`、`~/.claude/skills`、`~/.pi/agent/skills` 另复制副本：

```sh
rsync -a --delete skills/drama-craft/ ~/.agents/skills/drama-craft/
diff -r skills/drama-craft ~/.agents/skills/drama-craft
```

安装副本与源码是两种状态：文件一致不等于正在运行的宿主会话已加载新版本，需在新会话验证。各宿主的发现方式、限制与验证状态见 [adapters/README.md](adapters/README.md)；本包尚未打 tag、未发 Release，任何按分支或路径安装的方式都不构成不可变版本。

## 内容索引

| 文件 | 内容 |
| --- | --- |
| [SKILL.md](skills/drama-craft/SKILL.md) | 交付判断、三条铁律与适用范围、beat 架构、时长预算、工作流、生产硬约束、路由 |
| [story-patterns.md](skills/drama-craft/references/story-patterns.md) | P1–P11 原型库（主原型与组件两层）、证据等级与复核、观察池、组合规则、采集字段 |
| [production-craft.md](skills/drama-craft/references/production-craft.md) | 场景、人像、服化道、上妆手法、剪辑方式、生成交接、跨镜一致性 |
| [iteration-loop.md](skills/drama-craft/references/iteration-loop.md) | 百分比分段掉点诊断、基线口径、最小判读条件、变量矩阵、停止条件、分类验收 |
| [output-templates.md](skills/drama-craft/references/output-templates.md) | beat sheet、分镜表（含素材来源与参考资产）、变量矩阵、复盘卡、机制话术结构 |
| [worked-example.md](skills/drama-craft/references/worked-example.md) | 一份填完的 P1 20s 端到端交付：输入到验收全流程 |

宿主安装与发现见 [adapters/README.md](adapters/README.md)。

## 验证

```sh
cd packages/drama-craft
python3 scripts/check.py
python3 -m unittest discover -s tests -p 'test_*.py'

# 从仓库根
python3 scripts/check.py --package drama-craft
```

`check.py` 校验 frontmatter、链接可达、reference 无孤儿、原型编号连续、每个原型的必填字段（主原型额外要求情绪路径与爽点）、铁律必须在"三条铁律"节内且写明适用范围、主原型/组件/观察池的分类存在、生成交接与素材来源字段在位、示例数字不得直接当宣称，并与包文档对比（原型数量与区间、源码版本、CHANGELOG 版本节、README 不得自称"已验证"）。它不评价创意质量。

## 当前状态

源码 0.2.0。原型库与生产约束来自内容团队的两份内部采集文档（爆款 AI 剧情采集分类、AI 剧情方向分析），属于 2026 年抖音抽样归类：**证据等级 C**（单条样本量与采集起止日未逐条留档，未经真实投放 A/B 复核），因此称"已归类"而不称"已验证"。文档中的商品名、价格与数据仅用于说明结构，不代表当前在售状态、效果或转化承诺；机制示例数字不得直接写进成片当宣称。真实投放结论需按 [迭代方法](skills/drama-craft/references/iteration-loop.md) 自行积累，并在 90 天复核周期内重新定级。
