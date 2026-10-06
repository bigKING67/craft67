# 旧 bazi-ziwei：保留什么、修正什么

最初核验来源：`~/.codex/skills/bazi-ziwei`。安装副本无 .git，选定文件哈希已记录在 source-manifest.json。完成独立实现和替换审查后，该原样副本于 2026-09-26 移出 Skill 发现目录，归档到 `~/.codex/skill-backups/bazi-ziwei-20260926T151453`；归档动作没有改写其中内容。

## 现场问题

| 观察 | 影响 | whoami 对应 |
|---|---|---|
| SKILL.md 要求钟表时间且不做经度修正；bazi-prompt.md 的报告项却写真太阳时 | 报告口径可能与实际算法输入不一致 | 双时间记录与明确校时来源 |
| run-chart.ts 对非 male/female 且非“男”的字符串归为 female | 非法值会静默变成另一性别 | 严格枚举，非法输入失败 |
| 数字参数直接强转，未在入口验证日期、数值范围、时区语义 | 错误资料可能传入排盘层 | 输入边界校验与结构化错误 |
| timeZone 是数字，默认 8；无出生地点输入 | 无法从该入口正确表达历史地区时区/DST | IANA 时区与出生地经度 |
| TEST-GUIDE 主要为人工 smoke/报告关键词检查 | 输出包含关键字不代表命盘、时序或解读一致 | 固定样例、边界回归、引用校验与真实长文试用 |

原有“确定性排盘→单体系解释→综合报告”思想保留。whoami 不继承旧报告为金标准，也不沿用旧快照中的用户命盘值。

## 来源与复用限制

原地址 https://github.com/dzcmemory-web/bazi-ziwei-skill 当前返回 HTTP 451；GitHub API 指出 dmca，封锁记录为 2026-08-25T21:02:35Z。通知地址：https://github.com/github/dmca/blob/master/2026/08/2026-08-24-astrology-code.md 。投诉人的上传授权陈述只作为投诉内容，不视为独立查明事实。

本地 LICENSE/NOTICE 标注 MIT 不足以解决该争议。whoami 不整包复制提示词、enrichment、模板或内置核心；改用许可明确的直接依赖，并原创接口、规则流程和报告组织。历史本地使用副本仅作为 repo 外的回滚与审计归档保留，不随 whoami 公开仓库分发。
