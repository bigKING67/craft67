# Money Craft 日常运行与真实数据链路

2026-09-19 本机验收完成：专用 data/report 环境已重建，旧环境完整保留。真实读取及边界见 [验收回执](../acceptance/live-runtime-20260919.json)。这份说明不包含凭据，也不代表研究结论或收益保证。

## 日常入口

```sh
MONEY_CRAFT_SKILL_DIR="$HOME/.agents/skills/money-craft"
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" doctor --json
```

系统 `python3` 启动主入口会选择有效的专用 data 环境。`doctor` 仅检查本地配置、依赖和解释器，不能替代真实网络读取。当前 data/report 均使用 Python 3.14.7，yfinance 固定为1.7.0；本轮具体依赖版本保存在本地验收 freeze 文件中。

报告须显式使用 report 解释器，避免 data 环境因没有 Markdown 而拒绝渲染：

```sh
MONEY_CRAFT_REPORT_PYTHON="$HOME/.local/share/money-craft/venvs/report/bin/python"
"$MONEY_CRAFT_REPORT_PYTHON" "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" report render \
  --source <已审计Markdown文件> --output-dir <独立派生目录> --json
```

`<...>` 是待替换路径。不能用正式封存 revision 作为派生输出目录。此次用已有合成样张生成3页PDF并通过静态离线验证；没有重做浏览器/逐页视觉验收。

## 已验证的真实读取

- Fuyao：指定A股证券搜索及一份年度利润表响应。
- yfinance：AAPL与0700.HK各一个明确历史窗口的日线，均7行；日期范围和表格维度已核对。
- FRED：DGS10元数据及一个历史观测窗口。
- ALFRED：同一窗口按2024-01-31历史可得版本读取，响应real-time绑定已核对。

以上调用通过实际安装的Skill和日常data环境执行。capture只保存在已忽略的 `local/evidence/20260919-live-runtime/`，包含请求、响应与摘要，8份成功capture的响应哈希已核验。公开回执不包含原始数据集。

这证明指定接口本次可用，不代表所有Provider能力、实时行情时效、财务字段口径或完整研究已验收。Fuyao利润表尚未与发行人原文逐字段对账；yfinance导出不是Yahoo原始HTTP响应；FRED元数据、观测与历史版本也不构成投资判断。

## 失败与恢复

两个旧venv指向不存在的Python 3.13。重建时原目录分别重命名为 `data.backup-20260919T125916Z` 和 `report.backup-20260919T125916Z`，位于同一专用venvs目录；没有删除旧环境、修改凭据或系统Python。备份保留旧内容，但仍含失效解释器链接，不能称为可直接运行的回滚环境。

第一次并发yfinance读取出现 `OperationalError: database is locked`。适配器只将两种明确SQLite锁消息纳入既有三次有界重试；持续锁冲突仍失败，其他数据库错误不重试。修复后美股/港股并发读取通过。由于缓存已初始化，复验不等于重新复现了冷缓存锁竞争；瞬时恢复、耗尽和非锁错误分流另有确定性回归测试。

没有清除Yahoo缓存/cookie、更换凭据或放宽来源、计算、路由门禁。当前仍不执行交易或账户操作。
