# creative-craft

帮助 Agent 直接产出更高质量的 Campaign 概念、商业文案、创意导演、图片/视频制作
Brief 和创意评估；只有项目确实需要时才启用可追溯生产治理。

```text
理解语境 -> 发展路线 -> 锁定导演方案 -> 生产执行 -> 评估迭代 -> 交付复用
```

## 它不是什么

`creative-craft` 不是“提示词大全”，也不是把“高级感、电影感、质感”
堆进提示词里，更不是让 Agent 默认生成一堆 Schema 和流程文件。它解决的是从模糊
想法到可执行创意之间缺失的专业判断：

- 到底要解决什么传播任务；
- 面向谁，抓住什么矛盾、情绪或欲望；
- 创意洞察、核心主张、创意概念和执行形式分别是什么；
- 多条创意路线是否真的不同，而不是只换颜色和风格；
- 图片、视频、文案、声音和渠道版本如何共用同一套创意母体；
- GPT Image 2 与 Seedance 应该怎样接收结构化任务；
- 生成结果哪些是客观观察，哪些只是主观判断或效果假设；
- 哪些内容应该保留、放大、精修、重构、重新生成、重剪、重拍、测试或放弃；
- 最终文件、版权、肖像授权、参考素材、提示词、版本和交付规格如何追溯。

它有两种工作深度：

- **Quick Craft 是默认路径**：直接交付用户要的概念、文案、Prompt、Treatment、
  镜头方案或 Critique，只保留真正改善产出的结构。
- **Traceable Project 按需启用**：多资产、多 Agent、重复 Provider 执行、正式审批、
  来源追溯或交付核验时，再使用 Schema、不可变快照、Receipt、Inspection 和 Gate。

运行时和治理合同用于支撑创意产出，不是默认产出本身。

## 与 design-craft、review-craft 的边界

- `design-craft`：产品 UI/UX、交互、设计系统、动效和前端实现质量。
- `review-craft`：软件工程审查、证据验证、整改决策和项目质量治理。
- `creative-craft`：传播创意、内容创意、视觉与视频导演、生成式媒体生产和创意评估。

内容日历、KOL/KOC 规划、完整品牌战略、媒介投放不应路由到 `creative-craft`。

三者可以串联，但不互相吞并。比如广告落地页的“创意方向”由
`creative-craft` 提供，产品界面体验交给 `design-craft`，代码工程质量再交给
`review-craft`。

## 核心方法：CRAFT

- **C — Context / 语境**：目标、受众、产品、证据、资产、约束、版权和渠道。
- **R — Routes / 路线**：产生真正不同的创意机制，并明确选择理由。
- **A — Art direction / 导演**：锁定信息、视觉、叙事、表演、镜头、声音、
  参考素材角色和不可变项。
- **F — Fabrication / 制作**：生成或编辑图片、视频，检查真实输出并记录。
- **T — Testing / 测试**：比较、精修、适配、交付、测量，并回流到下一轮。

Traceable Project 的完整流程为：

```text
界定任务 -> 盘点事实 -> 补充研究 -> 锁定 Brief -> 创意发散
-> 路线选择 -> 创意导演 -> 图片/视频制作 -> 检查真实结果
-> 定向修改 -> 多渠道适配 -> 交付 -> 复盘沉淀
```

## 主要模式

- `understand`：理解想法、Brief、参考或已有成品。
- `brief`：创建或修复创意权威。
- `concept`：发展、区分、比较和选择创意路线。
- `direct`：创意阐述、视觉导演、Treatment、分镜、镜头、文案层级、
  动效和声音设计。
- `image`：GPT Image 2 图片生成或编辑任务。
- `video`：Seedance 视频生成、参考生成、续写或编辑任务。
- `campaign`：从一个母创意扩展为跨平台、跨规格、跨内容形态的系统。
- `critique`：只读创意评估。
- `refine`：对已授权方向或结果做定向优化。
- `adapt`：尺寸、构图、渠道、语言和版本适配。
- `deliver`：检查文件、规格、版权、来源、命名和交付清单。

## 专业性来自哪些约束

1. **先建立权威，再谈审美。**
2. **先讲传播策略，再讲风格。**
3. **创意路线必须是机制不同，不是换皮。**
4. **模型能力放 Provider 层，避免 Seedance 或 GPT Image 更新后核心失效。**
5. **每份参考素材必须声明控制角色。**
6. **编辑任务必须写清“只改什么”和“绝不改什么”。**
7. **客观观察、创意解读、效果假设和最终决策严格分开。**
8. **迭代默认一次只改变一个主变量。**
9. **评分必须有证据覆盖，缺 Brief、版权或交付规格时不强行打分。**
10. **提示词、输入资产、模型、版本、输出规格和文件校验值可追溯。**

## 可选的 Traceable Project 权威文件

- `BRAND.md`：长期品牌权威。
- `CREATIVE.md`：本次创意任务权威。
- `DELIVERABLES.md`：渠道、规格、版本、文案和交付权威。
- `asset-ledger.json`：素材来源、用途、版权、肖像授权和校验值。

Quick Craft 不需要创建这些文件。Traceable Project 中缺失内容必须标为假设，不能被
Agent 偷偷补成事实。

## 公共内核、私有 Pack、不可变项目快照

不要把任何公司的私有知识、Claims、内部链接或专有素材放进这个公共仓库。正确的
边界是三套独立生命周期：

```text
creative-craft/             公共、通用的方法、Schema 和工具
acme-brand-pack/            私有 Primary Brand 权威：我们是谁
acme-reference-library/     私有参考情报：我们向谁学习什么
campaign-project/           私有项目：我们现在做什么
```

Brand Pack 是一层很薄的品牌权威，不复制 Creative Craft 的方法论、Provider
Profile 或 Schema。它只保存创意执行真正需要的精选内容：品牌、产品、已批准
Claims、视觉系统、语言系统、渠道规则、权利与审批，以及 Asset Ledger。大型素材
继续留在 DAM、团队云盘或对象存储；Ledger 只记录稳定 URI、SHA-256、权利、
授权和允许用途。少量获准且适合 Git 管理的素材可以留在私有 Brand Skill 中。

项目绑定 Brand Pack 时，只会把 manifest、已登记权威文件、Brand Pack Ledger
和安全的本地小素材复制到 `.creative-craft/brand-snapshot/`，把 role=`brand`
的权威文件投影为项目根 `BRAND.md`，将品牌素材合并进项目 Asset Ledger，并在
`brand-binding.json` 中记录来源 ref/commit 和内容摘要。项目不会创建 live
symlink，因此私有 Brand Skill 后续变化不能偷偷改写历史项目。
`update-brand-snapshot` 必须显式执行；它会先备份，写入前后 Binding lineage，
完成全项目校验，失败则回滚。

`draft` Brand Pack 可以用于探索，但会阻止绑定项目中的 Job 进入 `ready`。
只有经过审阅的来源才能把 Pack 改为 `approved`；初始化命令只生成
`TBD/UNVERIFIED` 骨架，绝不编造产品事实、Claims、权利或批准状态。

Reference Pack 是完全独立的**非权威研究层**，可记录多个品牌、公司、团队、
Agency、Creator、Campaign、产品、视觉系统、影片、摄影、包装、编辑系统或社交
账号。它保存分级证据、可迁移原则、不可迁移表达、适用场景、来源身份和素材用途
政策；每个 Entity 都必须声明 `may_override_primary_brand: false`。

因此参考库可以影响创意路线和导演方案，但永远不能重写主品牌的 Identity、产品
事实、Claims、Exact Copy、权利、产品结构或主要视觉/语言权威。一个项目可以绑定
多个 Reference Pack：完整快照分别复制到
`.creative-craft/reference-snapshots/<pack-id>/`，Binding 分别写入
`.creative-craft/reference-bindings/`，旧 Binding 作为不可变历史写入
`.creative-craft/reference-lineage/<pack-id>/`；只有被选 Entity 的素材会合并进
项目 Ledger。`reviewed` Pack 的每个 Source 必须保存本地 Source Snapshot，并验证
SHA-256；只有 URI 或证据标签不算内容绑定。更新其中一个 Pack 不会改写 Primary
Brand Pack 或其他 Reference Pack。

`draft` Reference Pack 只产生“探索性证据”警告，不阻止 Job 进入 `ready`；
`revoked` Pack 会使校验失败；已经绑定的 `superseded` Snapshot 仍可作为历史证据
读取，但不能用于新绑定或更新。公开可见也不等于允许把素材作为生成输入。

## 当前版本

当前工作树是尚未发布的 **`0.3.2` candidate**：增加方向门控的有限精修与 Grok
发现证据，不修改公开工件合同，也不增加 Provider Adapter。`0.3.0` 把 Quick Craft
设为 Agent 默认路径，把证据链运行时收进显式 Traceable Project 模式，收窄自动路由，
并新增仓库内文本 A/B 评测工具。它同时保留一等
`creative-craft.copy-sheet.v1` 文案权威、面向公开交付的具名 Owner 审批门禁、
copy-bound Project Manifest v2、模块化 portable runtime/test、安全原子写入、
索引化的 `uniqueItems` 校验，以及有评测证据支持的 Agent 创意质量提升。当前最新已
发布、可安装的 GitHub 版本仍是不可变 `v0.3.0` tag。

Project Manifest v2 默认 `copy_policy=required`。每个 Image/Video Job 必须绑定一份
Copy Sheet 和明确的 Copy Unit：`draft` 只用于探索，`reviewed` 可进入内部制作就绪，
公开 `ready/delivered` 则必须使用 `approved/public` Copy Sheet，并记录具名 Owner、
时间和审批依据。公开批准的文案不得继续把 `HYPOTHESIZED` 或 `UNVERIFIED` 当作
发布证据。旧 Project Manifest v1 和旧工件仍可读取，但不会被自动升级或自动批准。

`0.2.0` 已建立：

- 可被 Agent 安装的 canonical Skill；
- GPT Image 2、Seedance 2.5 Provider Profile 与执行 Surface Profile；
- `Project Manifest v2 → Brief → Routes → Creative Direction → Copy Sheet → Job → Receipt
  → Inspection → Revision → Evaluation → Delivery` 正式工件链；
- JSON Schema 结构真源、标准库运行时 Schema 校验和跨工件语义校验；
- 文件路径、SHA-256、引用、Provider、Surface、版权和生命周期证据绑定；
- 由 Receipt、真实文件、Inspection 和 Delivery 证据派生的 Job 状态；
- Coverage、Evidence Strength、Confidence、Uncertainty 分离的 Evaluation v2；
- 原子安装、安装来源记录、单元测试、Schema parity 和真实 GitHub CI；
- 明确不冒充真实生成结果的虚构高端洗护案例。

安装后的 Skill/runtime 默认不直接调用 Provider、不产生图片或视频生成费用。仓库级
Agent 质量评测工具会在维护者显式运行时调用 Codex 文本模型，因此独立于 CI 和发布
runtime。虚构案例只证明内部 `reviewed` 文案合同，不代表真实 Provider 输出、真实
Owner 公开批准或 Golden Eval；也不包含 GPT Image 2 或 Seedance 网络 Adapter。

图片/视频的[参考、版本及更新流程](docs/upstream-absorption.md)与
[图片工具](integrations/image-production/README.md)的可编辑海报与验收统一在仓库文档维护。

## 安装到 Pi、Codex 和其他 Agent

这是标准 Agent Skill，canonical runtime 为 `skills/creative-craft/`。当前只通过
GitHub 分发，不发布 npm；`package.json` 只负责 Pi/GitHub package discovery。

Pi 是 Tier 1 Host：

```bash
pi install git:github.com/bigKING67/creative-craft@v0.3.0
pi install -l git:github.com/bigKING67/creative-craft@v0.3.0
```

Codex 是 Tier 1 Host。可以让内置 `skill-installer` 从
`bigKING67/creative-craft` 的 `v0.3.0` tag 安装
`skills/creative-craft`，也可以执行：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo bigKING67/creative-craft \
  --ref v0.3.0 \
  --path skills/creative-craft
```

Codex 会在下一轮或新会话发现该 Skill。其他支持目录式 Skill 的 Agent 可以
clone 仓库后使用原子 installer：

```bash
python3 scripts/install_skill.py --target /path/to/host/skills
```

在 Codex 与 Grok 都发现共享 Agents Skill 根目录的本机环境中，只维护一份安装：

```bash
python3 scripts/install_skill.py --target ~/.agents/skills
```

Grok Build 的发现方式见 `adapters/grok/`。`0.3.2` candidate 已验证不调用模型的
Skill discovery，但尚不声称 Grok Tier 1 运行态行为。

`--force` 不会先删除旧版本：installer 会在目标文件系统 staging、自检、记录
`INSTALL_PROVENANCE.json`，再原子替换并保留旧安装备份。Claude/Cursor 当前仅有
薄适配说明，不属于 Tier 1 运行态验证结论。

维护者从 clean commit 构建候选包时，Release Builder 会先检查 `.tgz` 的全部成员，
拒绝路径越界、symlink 和 hardlink，再对这个实际生成的包运行叶子 Skill 自检以及
Reference bind、update、项目校验和精确树回滚 E2E。该证据只证明包内 runtime，
不等于已经发布到 npm 或完成所有 Agent Host 的真机验证。

## 开始使用

Portable runtime 明确要求 **Python `>=3.10`**。CI 声明覆盖最低版本及 Python
3.11/3.13；安装后的叶子 CLI 只依赖标准库，仓库级 Ruff 与 Schema parity 才使用
`requirements-dev.txt`。

```bash
python3 scripts/validate.py
```

运行 CI 使用的完整 JSON Schema 校验：

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_schemas.py
```

在仓库 checkout 中运行 package self-test：

```bash
python3 skills/creative-craft/scripts/creative_craft.py self-test
```

同一命令从 Pi、Codex 或通用目录式叶子 Skill 中执行时，会自动切换到 runtime
scope，不再要求仓库根目录的 README、LICENSE、plugin metadata 和 source lock。
使用 `--json` 可以记录实际 scope 以及 repository/runtime validity。Release 校验
使用 `self-test --scope runtime --json`，确保即使 `.tgz` 外层含有仓库元数据，
实际被验证的仍是包内叶子 Skill runtime。

需要 Traceable Project 时初始化项目：

```bash
python3 skills/creative-craft/scripts/creative_craft.py seed \
  --target /path/to/project
```

Seed 只创建规划权威骨架、Critique、draft Jobs、Evaluation、planned Delivery
和 Project Manifest；占位骨架不等于已经批准或锁定的权威。它不会创建 Execution
Receipt、Output Inspection 或 Revision Lineage，这些生命周期工件只能在对应的真实
尝试、输出检查或修订发生后创建。Quick Craft 不需要执行 `seed`，也不需要生成任何
JSON 工件。

在独立私有仓库中初始化和校验一个只含占位内容的 Brand Skill：

```bash
python3 skills/creative-craft/scripts/creative_craft.py init-brand-pack \
  --target /path/to/acme-brand-pack/skills/acme-brand \
  --brand-id acme \
  --brand-name "Acme" \
  --owner brand-operations

python3 skills/creative-craft/scripts/creative_craft.py validate-brand-pack \
  --root /path/to/acme-brand-pack/skills/acme-brand
```

真实品牌内容完成审阅后，将当前 Pack 以不可变快照绑定到新项目。团队仓库建议
同时记录来源 ref 和完整 Commit SHA：

```bash
python3 skills/creative-craft/scripts/creative_craft.py seed \
  --target /path/to/campaign-project \
  --brand-pack /path/to/acme-brand-pack/skills/acme-brand \
  --brand-source-uri https://git.example/acme-brand-pack.git \
  --brand-source-ref v1.0.0 \
  --brand-source-commit <full-commit-sha> \
  --imported-by <identity>

python3 skills/creative-craft/scripts/creative_craft.py update-brand-snapshot \
  --target /path/to/campaign-project \
  --brand-pack /path/to/acme-brand-pack/skills/acme-brand \
  --reason "Adopt reviewed brand authority v1.1.0" \
  --brand-source-uri https://git.example/acme-brand-pack.git \
  --brand-source-ref v1.1.0 \
  --brand-source-commit <full-commit-sha> \
  --imported-by <identity>
```

在另一个私有仓库中初始化 Reference Skill，录入经过证据分级的 Entity，并把每个
已审阅来源保存为本地 Source Snapshot，在 `source_references` 中登记
`snapshot_path` 与 SHA-256 后，可将任意数量的参考库绑定到已有项目：

```bash
python3 skills/creative-craft/scripts/creative_craft.py init-reference-pack \
  --target /path/to/acme-reference-library/skills/acme-creative-references \
  --pack-id acme-creative-references \
  --name "Acme Creative References" \
  --owner creative-operations
```

将 Pack 改为 `reviewed` 前，先把每个来源保存到私有 Reference Skill，并登记真实摘要：

```json
{
  "source_id": "source-example",
  "authority": "official",
  "uri": "<原始来源 URI>",
  "captured_at": "2026-08-04T00:00:00Z",
  "snapshot_path": "sources/source-example.md",
  "sha256": "<sources/source-example.md 的 SHA-256>",
  "notes": "已审阅的来源快照。"
}
```

然后再校验和绑定：

```bash

python3 skills/creative-craft/scripts/creative_craft.py validate-reference-pack \
  --root /path/to/acme-reference-library/skills/acme-creative-references

python3 skills/creative-craft/scripts/creative_craft.py bind-reference-pack \
  --target /path/to/campaign-project \
  --reference-pack /path/to/acme-reference-library/skills/acme-creative-references \
  --select reference-entity-a \
  --reference-source-uri https://git.example/acme-reference-library.git \
  --reference-source-ref v0.1.0 \
  --reference-source-commit <full-commit-sha> \
  --imported-by <identity>

python3 skills/creative-craft/scripts/creative_craft.py update-reference-snapshot \
  --target /path/to/campaign-project \
  --reference-pack /path/to/acme-reference-library/skills/acme-creative-references \
  --select reference-entity-a \
  --select reference-entity-b \
  --reason "采用新一版已审阅参考证据"
```

不传 `--select` 时默认选中非空 Pack 的全部 Entity。空的 `draft` Reference Pack
可以先校验和安装，但至少录入一个 Entity 后才能绑定项目。

编译 GPT Image 2 图片任务：

```bash
python3 skills/creative-craft/scripts/creative_craft.py compile-image \
  --file examples/premium-haircare-launch/image-job.json
```

编译 Seedance 视频任务：

```bash
python3 skills/creative-craft/scripts/creative_craft.py compile-video \
  --file examples/premium-haircare-launch/video-job.json
```

查看创意评分与证据覆盖：

```bash
python3 skills/creative-craft/scripts/creative_craft.py score \
  --file examples/premium-haircare-launch/evaluation.json \
  --root examples/premium-haircare-launch
```

校验项目证据图并查看派生状态：

```bash
python3 skills/creative-craft/scripts/creative_craft.py doctor-project \
  --root examples/premium-haircare-launch --json

python3 skills/creative-craft/scripts/creative_craft.py validate-project \
  --root examples/premium-haircare-launch

python3 skills/creative-craft/scripts/creative_craft.py project-status \
  --root examples/premium-haircare-launch --json
```

`doctor-project` 是只读诊断命令。它会报告无效项目图，以及与 Manifest 同目录但未
注册的已知 Creative Craft JSON 工件。与内置模板逐字节一致的文件会被标记为
`seed_template_residue`；该命令不会自动注册或删除文件，因为“文件存在”不能证明
对应的生命周期事件真实发生过。

## Agent 质量评测

仓库提供仅供维护者使用的文本评测工具：在九个真实创意任务上比较不加载 Skill 的
baseline、选定的 committed comparison revision 和 worktree candidate，再做盲评
计分与四个路由用例。内部 `baseline` / `current` evidence key 为兼容旧报告而保留，
不表示本机或 package 中安装了多份 Skill。

```bash
python3 scripts/evaluate_agent_quality.py check --json
python3 scripts/evaluate_agent_quality.py run
python3 scripts/evaluate_agent_quality.py judge --run-dir dist/evals/agent-quality/<run>
python3 scripts/evaluate_agent_quality.py route --run-dir dist/evals/agent-quality/<run>
python3 scripts/evaluate_agent_quality.py report --run-dir dist/evals/agent-quality/<run>
```

工具使用临时 `0700` Codex home 与 user home，同时隔离 `CODEX_HOME`、
`HOME`/`USERPROFILE`、XDG、shell profile 和平台 application-data 根目录；只 symlink
现有 Codex auth 文件且不读取或复制内容，不安装全局 Skill。事件证据必须证明
no-Skill baseline 没有读取 Creative Craft 入口，comparison/candidate 只读取各自
digest 绑定的隔离副本；否则会在继续消耗盲评或路由调用前失败。workspace 为空，
Codex 使用 ephemeral、read-only、ignore-config/rules 参数。若本机使用自定义 model
provider，工具只提取 `name`、
`base_url`、`wire_api`、auth mode 和 WebSocket support 这些非敏感白名单传输字段，
作为 CLI override 传入，不复制用户 config。comparison revision 只导出到临时目录，
生成结束即删除。证据写入已忽略的 `dist/evals/agent-quality/`，并绑定模型、
reasoning、comparison revision 和 candidate Skill digest。

真实模型评测有成本，因此不进入 CI。当前只评测文本 Agent 输出，不调用图片/视频
Provider；盲评模型的比较结论也不能替代真实输出检查或人类创意审批。每个变体在每个
案例中只有一个生成样本和一次盲评，因此重复运行可能波动。选定少数案例的 Canary
可以在没有 routing 结果时生成报告，但状态保持 `PARTIAL`；只有完整 quality 与
routing suite 才能通过面向发布的验收门禁。

另有独立的[中文创意判断力评测材料](evals/creative-quality-zh/README.md)：四个诊断
任务、两个保留任务及人工盲选说明。它们不接入默认评测套件，不改变调用上限；实际
执行情况以绑定题目、Skill 快照和原始输出的独立运行记录为准。材料和离线检查通过
不代表创意质量已经提升。

## 最重要的一条

Job v2 只能声明 `draft`、`ready` 或 `superseded`。最终交付不能只说
“提示词已经写好”，系统必须按证据区分：

- 已计划；
- 已生成；
- 已看到真实输出；
- 已完成定向修改；
- 已按规格检查；
- 已确认版权与授权；
- 已完成最终交付。

没有看到的结果，不得被描述成已经实现。
