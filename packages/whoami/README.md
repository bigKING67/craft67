# whoami

八字与紫微斗数的本地计算核心和 Codex Skill。核心负责可复算的命盘、时间口径与证据，宿主模型负责有条件、有依据的传统解读。它不承诺现实事件预测准确，也不会用模型自行补造时辰、四柱或星曜。

## 快速使用

```sh
npm ci --ignore-scripts
npm run build
node dist/cli.js chart --input examples/birth.json --years 2024,2025,2026,2027,2028
node dist/cli.js context --input examples/birth.json --years 2024,2025,2026,2027,2028
```

在支持 Skill 的宿主里可以直接说：**“使用 `whoami`，为我做八字＋紫微综合长文分析。”** 宿主会先核对出生资料，再调用本地核心，不需要另配模型密钥。本仓库是 `whoami` Skill 的唯一维护源；安装动作必须显式执行，开发机可将 `~/.codex/skills/whoami` 链接到本目录。旧的 `bazi-ziwei` 不应与它同时留在 Skill 发现目录，避免两个入口给出冲突的资料要求和分析合同。安装或更新后需要新开 Codex 会话，已有会话不会自动刷新 Skill 列表。

日常流程只需按[输入与 CLI](references/input-and-cli.md)准备资料，按[分析契约](references/analysis.md)形成判断，再按[报告契约](references/report.md)校验和渲染；涉及年份、日期、时区、区间或日程时同时遵守[时间表达与 evidence 粒度契约](references/time.md)。报告模板不是自动断语；宿主必须依据实际命盘填写正文，并核对旺衰、格局、调候、扶抑、用神取舍和紫微四化的适用条件。

可直接查看已经跑通的[合成样例完整报告](examples/report.md)和[自然追问示例](examples/followups.md)。对应输入为 `examples/birth.json`，年份为 2024—2028。

## 日常工作流

1. 收集历法、日期、时间或时间范围、性别、地点、经度和历史 IANA 时区。未知时辰保持 `null`，不能填中午。
2. 使用同一输入和年份运行 `chart` 与 `context`。出现多个候选时逐一比较，不替用户选择出生时辰。
3. 具体问题走快速档：基于 context 直接作答，答复经 `answer-check` 检查后交付。要求完整报告时走完整档：分别完成八字与紫微分析，再作范围一致的对照；报告通过 `report-check` 后用 `render` 生成 Markdown。
4. 用户更正出生资料时重新计算，并用 `compare` 区分改变与未变的事实；旧报告不能只替换标识后继续使用。

需要查看已实现的财格规则线索，可运行：

```sh
node dist/cli.js rule-review --input examples/acceptance/officer-branch/birth.json --years 2026
```

它只输出已见条件、反例和待核条件，不代替完整命理解读。参考[单候选样例](examples/acceptance/officer-branch/rule-review.md)和[边界双候选样例](examples/acceptance/boundary/rule-review.md)。

更正出生时间后的事实对照：

```sh
node dist/cli.js compare --before examples/acceptance/full-1996/birth.json --after examples/acceptance/full-1996/birth-1010.json --years 2026,2027,2028
```

[实算对照输出](examples/acceptance/full-1996/compare-output.json)会区分本例中保持不变的四柱、已经变化的起运，以及失效的旧报告绑定。

## 项目边界

- `src/`：输入校验、时间处理、八字/紫微适配、规则证据、报告和 CLI。
- `SKILL.md`、`references/`：资料采集、分析、追问和交付合同。
- `tests/`、`examples/`：合成输入、公开样例和离线验证，不存真人命盘。
- `docs/research/`：研究来源与吸收决策，不是日常运行时提示词。
- `docs/quality/`：维护和验收记录，不进入普通算命上下文。

## 维护与验证

```sh
npm run check
```

GitHub Actions 的 [CI 工作流](.github/workflows/ci.yml) 在 push、PR 或手动触发时，使用 Ubuntu + Node 24.18.0，从锁文件安装依赖并执行同一检查入口，覆盖类型检查、测试和构建。实际运行状态见 [Actions](https://github.com/bigKING67/whoami/actions/workflows/ci.yml)；工作流文件存在不代表远端检查已通过。固定验收样例的命盘 ID 包含完整 Node 和 tzdata 版本，因此 CI 固定 Node 24.18.0；`engines.node >=22` 是运行要求，不表示这些固定证据可跨版本直接复用。升级验证环境时应同步复核样例，不能跳过证据绑定检查。

自然语言回归、benchmark、运行回执、Ed25519 外部签发和 Codex runtime audit 都属于维护流程，完整命令和信任边界集中在[维护与验收契约](references/acceptance.md)。历史结果见[验证记录](docs/validation.md)。这些机制验证文件、计算和回答之间的绑定，不能证明传统命理或现实预测有效。

2026-09-26 的时间文本修复、完整报告生成与定向整改，见[本轮质量与验收记录](docs/quality/2026-09-26-time-text-and-live-eval.md#审阅结论)。该记录分别列出工程检查、初轮问题、修正版内容复核及未取得可信宿主回执的限制；原始模型产物保存在本地 gitignored `private/`，不随仓库提交。

## 明确限制

出生年份支持 1901—2098，流年支持 1901—2099。真太阳时采用 NOAA 近似均时差；边界筛查和分钟采样不代表秒级精度或连续区间完备证明。项目不自动地理编码，不猜经度和历史时区，来源元数据也不会自动证明来源真实。

当前规则层能列出通根、透干、财格条件、反例和部分四化位置，但不是完整自动命理专家系统。调候资料目前只核验了[丙火申月](references/climate.md)这一窄条目；旺衰、格局、调候和喜用仍需宿主依据事实说明支持、反证与未决条件。报告的安全门禁只拦截部分高置信危险措辞，不等于完整自然语言语义认证。

首版没有 Web UI、海报、账号、远端存储或独立模型 API。真人输入和报告默认不持久化；需要保存时使用仓库外路径或 gitignored `private/`，不要上传或提交私人资料。

## 安装与更新

开发机使用符号链接，让 Skill 入口始终跟随当前仓库：

```sh
ln -s /absolute/path/to/whoami ~/.codex/skills/whoami
```

分发给其他机器时不必复制整个仓库：先 `npm run build`，再用 `npm run pack:skill -- <新目录>` 导出只含运行与重建所需文件的分发目录（约 1MB，不含测试、验收样例、质量记录与研究扫描件），在目标目录执行 `npm ci --omit=dev` 后即可使用。目标目录已存在时脚本拒绝覆盖。

如果发现目录中已有同名路径，先检查并备份，不能用上述命令直接覆盖。旧 `bazi-ziwei` 应移到 `~/.codex/skills/` 之外的备份目录；回滚时删除 `whoami` 链接并把备份移回原位。安装后可运行 Skill 校验，并在新会话中确认选择器只显示 `whoami`。

## 来源与授权

原创代码、测试、合同和项目文档采用 [MIT License](LICENSE)。依赖 `lunar-typescript`、`iztro` 和 Temporal polyfill，版本固定在锁文件。研究来源见[研究索引](docs/research/README.md)；第三方扫描、转录、引文和测试来源不由本项目重新授权，具体边界见[第三方材料说明](THIRD_PARTY_NOTICES.md)。
