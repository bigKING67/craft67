# FRED / ALFRED 宏观数据 Provider

官方合同：

- https://fred.stlouisfed.org/docs/api/api_key.html
- https://fred.stlouisfed.org/docs/api/fred/series_search.html
- https://fred.stlouisfed.org/docs/api/fred/series.html
- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
- https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- https://fred.stlouisfed.org/docs/api/terms_of_use.html

FRED 用于宏观、利率、通胀、就业、增长、流动性和信用环境的结构化时间序列；ALFRED 用于读取历史时点当时已知的版本。它们是宏观研究基础设施，不是公司法定披露、证券行情或交易信号 Provider。

> This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.

## 凭据与运行边界

每个请求都需要 32 位小写字母数字 API key。运行时依次读取 `FRED_API_KEY` 和权限为 `0600` 或更严格的 `~/.config/money-craft/fred-api-key`；密钥文件必须由当前用户拥有、是普通文件且不能是符号链接。FRED 把 key 放在查询参数中，因此客户端不得记录完整请求 URL、把 key 写进 capture、错误文本、报告或 shell 参数。配置路径覆盖、显式 dotenv 与数据运行时见 [财务数据与证据](../financial-data-and-evidence.md)。

如果 key 曾出现在聊天、截图、日志或命令历史中，先在 FRED Account 撤销并创建新 key，再通过无回显输入保存：

```bash
install -d -m 700 ~/.config/money-craft
read -rs 'FRED_API_KEY?FRED API key: '; printf '%s\n' "$FRED_API_KEY" > ~/.config/money-craft/fred-api-key; unset FRED_API_KEY
chmod 600 ~/.config/money-craft/fred-api-key
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" doctor --json
```

## 有界 CLI

```bash
# 搜索 series id，不把自然语言搜索结果直接写进投资结论
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" data search \
  --provider fred --query "10-year breakeven inflation" --limit 10

# 读取 series 元数据：标题、来源、单位、频率、季调、更新时间和 notes
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" data series \
  --series-id T10YIE

# 当前最新修订口径
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" data observations \
  --series-id T10YIE --start 2020-01-01 --end 2026-09-01 --units lin

# 2024-12-31 当时能够看到的历史版本，防止未来信息污染
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" data observations \
  --series-id GDPC1 --start 2019-01-01 --end 2024-12-31 \
  --as-known-on 2024-12-31 --units lin

# 列出发生新增或修订的 vintage dates
python3 "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" data vintages \
  --series-id GDPC1 --start 2020-01-01 --end 2026-09-01
```

`--units` 只开放官方的 `lin`、`chg`、`ch1`、`pch`、`pc1`、`pca`、`cch`、`cca`、`log` 变换。若投资论文依赖变换值，必须保留原始 series id、原单位、变换代码、观测区间与 real-time/as-known-on 日期。返回值 `.` 表示缺失，不能补零。

## 建议的宏观仪表盘

| 研究维度 | 常用 series id | 能回答什么 | 不能直接推出什么 |
|---|---|---|---|
| 政策与短端利率 | `DFF`、`FEDFUNDS`、`SOFR` | 实际政策约束和美元短端资金价格 | 下一次会议必然加息或降息 |
| 国债曲线 | `DGS2`、`DGS10`、`DGS30`、`T10Y2Y`、`T10Y3M` | 无风险利率、期限结构、曲线倒挂 | 单独预测衰退日期或股市方向 |
| 已实现通胀 | `CPIAUCSL`、`CPILFESL`、`PCEPI`、`PCEPILFE` | 总体/核心 CPI 与 PCE 的变化 | 市场未来通胀定价 |
| 通胀预期/补偿 | `T5YIE`、`T10YIE`、`T5YIFR`、`MICH` | 市场隐含和调查型通胀预期的方向 | 纯粹、无风险溢价的真实预期 |
| 增长与生产 | `GDPC1`、`INDPRO` | 实际增长和工业周期 | 高频实时增长结论 |
| 就业 | `UNRATE`、`PAYEMS`、`ICSA` | 失业、非农和初请的趋势 | 未经修订的实时劳动力全貌 |
| 美联储与财政流动性 | `WALCL`、`RRPONTSYD`、`WTREGEN` | 美联储资产负债表、逆回购和财政部现金余额 | 机械等同于股票市场净流动性 |
| 信用与金融条件 | `BAMLH0A0HYM2`、`NFCI` | 高收益利差和综合金融条件 | 单指标择时或信用事件概率 |

series id 只是入口。任何正式使用都先读取 `data series` 元数据，确认来源、单位、频率、季调、更新时间和 notes；同名指标不得仅凭 ticker 猜口径。通胀保值债券 breakeven 同时包含通胀预期、风险溢价和流动性影响，流动性代理也不是可直接加减得到的“股市资金净流入”。这些解释属于 `INFERRED`，不是 FRED 原始观测。

## FRED 与 ALFRED 的选择

- 回答“截至今天最新修订后的历史是多少”：不传 `--as-known-on`，使用 FRED mode。
- 回答“在某个历史决策日，当时能看到什么”：传 `--as-known-on YYYY-MM-DD`，使用同日闭区间 real-time period。
- 判断修订风险：先用 `data vintages` 找修订日期，再比较两个或更多 as-known-on capture。
- 回测、历史论文复盘和预测评估默认使用 ALFRED vintage；不得拿今天修订后的 GDP/CPI 历史回填过去模型并称为实时结果。

观测日期不是发布日期。月度或季度 series 的 `date` 是观测期标签，是否在决策时已发布由 real-time period、vintage 和 series 更新时间共同判断。

## 证据、权利与失败语义

FRED 汇集许多来源，部分 series 由第三方拥有并带有版权或使用限制；FRED API 的可访问性不覆盖原数据所有者的权利。正式报告保留 series 元数据、原来源/notes、抓取时间、查询口径和 capture 哈希，不批量再分发原始数据集。

官方条款没有承诺固定不变的速率上限，只说明可能限流和调整额度。客户端对 `429`、`5xx` 和短暂网络错误最多尝试三次，尊重并限制 `Retry-After`；仍失败就形成 `PROVIDER_GAP`，不能用旧值或模型记忆补齐。没有适用于结论的当前正式或可追溯来源时停止事实型判断；FRED 的可用性不能替代公司正式披露。

### 调用方须知

- 缺失值 `.` 原样保留，不能补零；非法响应、错误信封或越界日期都以 `malformed_response` 拒绝，不写成功 capture。
- `--as-known-on` 与 `vintages --start/--end` 的响应必须回显请求的 realtime 边界；这只证明请求/响应范围一致，不证明修订历史完整。
- 分页不会自动遍历：CLI 提示 `partial page` 或完整性 unverified 时，不能把一次采集当作完整数据集。
- 可重试失败（429/5xx/网络中断）最多尝试三次，仍失败即 `PROVIDER_GAP`；不用旧值或模型记忆补齐。
- 适配器边界的测试证据与未闭环项见源码仓库的 `docs/fred-review-boundaries.md`（安装包不含，维护时查阅）；本轮测试不等于真实 FRED/ALFRED 连通性验收。
