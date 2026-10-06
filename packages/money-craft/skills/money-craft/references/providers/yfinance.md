# yfinance 港美股 Provider

官方项目与 API 参考：

- https://pypi.org/project/yfinance/
- https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html
- https://ranaroussi.github.io/yfinance/reference/api/yfinance.Search.html

Money Craft 将 `yfinance==1.7.0` 作为可选的港股和美股二级数据适配器。它不属于核心标准库运行时，也不替代 SEC、港交所、发行人 IR、法定财报或其他正式披露。PyPI 页面明确说明：yfinance 与 Yahoo 无隶属或背书关系，使用公开 API，面向研究和教育用途；Yahoo Finance 数据的实际使用权需服从 Yahoo 条款，接口面向 personal use（个人使用）。不得将它当成可自由再分发的数据授权。

在专用 Python 环境中安装：

```bash
MONEY_CRAFT_DATA_HOME="${MONEY_CRAFT_DATA_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/money-craft}"
python3 -m venv "$MONEY_CRAFT_DATA_HOME/venvs/data"
"$MONEY_CRAFT_DATA_HOME/venvs/data/bin/python" -m pip install \
  -r "$MONEY_CRAFT_SKILL_DIR/requirements-yfinance.txt"
"$MONEY_CRAFT_DATA_HOME/venvs/data/bin/python" \
  "$MONEY_CRAFT_SKILL_DIR/scripts/money_craft.py" doctor --json
```

不要因为当前宿主的系统 Python 未安装 yfinance 就改写全局环境；使用同一专用解释器执行 `research plan/init/collect`。`doctor` 只检查包是否可导入和版本，不联网。

数据运行时的自动切换、`MONEY_CRAFT_DATA_PYTHON` 覆盖和旧 data-venv 迁移兼容回退，以及共享 XDG、显式 dotenv、Provider gap 和当前来源边界，见 [财务数据与证据](../financial-data-and-evidence.md)。

## 身份映射

Money Craft 的 `security_id` 仍是研究身份真源，Yahoo symbol 只是 Provider identifier：

| `security_id` | yfinance symbol | 规则 |
|---|---|---|
| `HK:00700` | `0700.HK` | 去除多余前导零后至少保留四位，并追加 `.HK` |
| `US-NASDAQ:NVDA` | `NVDA` | 美股使用 ticker；类别股的 `.` 转为 Yahoo 的 `-` |
| `US-NYSE:BRK.B` | `BRK-B` | 只改变 Provider identifier，不改 canonical identity |

检索必须唯一命中该 Provider symbol；返回币种若与计划基础币种冲突，或资产类型不是 equity/stock，采集失败。公司法定名称、share class、财政期和证券权利仍以交易所、监管披露和发行人文件确认。

## 有界能力

使用 `--provider yfinance`：

| CLI | yfinance 调用 | 约束 |
|---|---|---|
| `data search` | `Search(...).quotes` | 只作 symbol 消歧，不采纳新闻或研究报告 |
| `data snapshot` | `Ticker.fast_info` | 行情/市值为二级快照；允许缺失字段 |
| `data history` | `Ticker.history` | 当前只开放 `1d`、最长 10 年；`auto` 为 yfinance 自动调整，Money Craft 的 inclusive end 会转换为 yfinance exclusive end + 1 日 |
| `data valuations` | `Ticker.get_valuation_measures` | 固定季度频率、当前值加最多 5 个期间 |
| `data financials` | `get_income_stmt` / `get_balance_sheet` / `get_cash_flow` | 年度或季度，最多保留请求的列数；字段、币种和财政期必须与正式报告对账 |
| `data corporate-actions` | `Ticker.get_actions` | 本地按日期过滤；只作拆股/分红交叉核对 |

`calendar`、Fuyao `indicators`、盘中流式行情、期权、分析师评级、新闻、筛选器和自动交易不在本适配器范围内。接口存在不等于 Money Craft 应暴露。

## 输出与证据边界

yfinance 返回 pandas 对象而不是稳定的 REST wire envelope。Money Craft 将表格转成 `index + columns + rows` 的版本化 `money-craft.yfinance-adapter-export.v1`，Decimal 字符串化后写入私有 capture；该文件必须标为 `adapter-export`，不得谎称 Yahoo 原始 HTTP 响应。

所有 yfinance normalized response、adapter export 和 capture receipt 只保存在 repo 外或已忽略的 `local/evidence/`。公开产物只能包含来源元数据、哈希、派生计算和正式披露链接，不分发抓取的数据集。缺字段、空表、限流、接口变化或标的冲突都形成 Provider gap；不能用旧缓存或模型记忆补齐。

## 调用方须知

- 必需数据全部缺失时返回 `transient_provider_error`；空 `corporate-actions` 只表示该次结果无事件，不证明上游无漏数。
- 非有限值归缺失、零值保留；字符串数字、布尔值等不会被当作金融数值，异常整条拒绝为 `malformed_response`。
- `history` 与 `corporate-actions` 的日期越过请求闭区间即拒绝，不静默裁剪；时区与交易日完整性未验证。
- CLI 退出码：缺可选依赖 3、Provider 故障 4、可重试故障 5、`malformed_response` 6；失败不写成功 capture。
- 通过准入不代表字段、币种、财政期或单位已与正式报告对账。适配器实现细节与未闭环项见源码仓库的 `docs/yfinance-review-boundaries.md`（安装包不含，维护时查阅）。
