# Fuyao A 股 Provider

官方文档：

- https://fuyao.aicubes.cn/docs/api-reference/overview/
- https://fuyao.aicubes.cn/llms.txt
- https://fuyao.aicubes.cn/llms-full.txt

`llms.txt` 是供 AI Agent 使用的导航索引，按入门、REST API、MCP 接入和
MCP 工具列出具体文档链接；它不是完整字段规范。`llms-full.txt` 是聚合后的
长文档，适合检索完整上下文。实现接口时仍以对应 endpoint 页面、当前错误码
合同和真实响应为准，不能只按索引标题猜测参数或字段。

截至 `sources.lock.json` 当前锁定版本，官方介绍的“跨市场”只出现在元信息描述；`/api/meta/tickers/search` 和 `/list` 的完整 `asset_type` 枚举实际只有 `a-share`、`a-share-index`、`fund-otc`、`fund-etf`、`fund-lof`，已上线行情与财务接口也都位于 `/api/a-share/*`。因此不能从“同花顺产品有全球数据”推断这套 Fuyao API 已开放港股或美股 endpoint；官方文档新增明确路径、参数和响应合同前，港美股必须走其他适配器或正式来源。

索引还包含全市场导出、指数、基金、竞价、龙虎榜、热榜和其他特色数据。
Money Craft v0.3 只把下表中与证据优先基本面研究直接相关的有界能力开放为 A 股适配器；文档
里存在某个接口，不等于本客户端应自动暴露该接口。

Money Craft v0.3 使用固定 HTTPS Base URL `https://fuyao.aicubes.cn`，通过请求头 `X-api-key` 鉴权。该 Provider 的覆盖范围不定义 Money Craft 的全球产品边界。运行时优先读取环境变量 `FUYAO_API_KEY`，否则读取权限必须为 `0600` 或更严格的 `~/.config/money-craft/fuyao-api-key`。密钥文件必须由当前用户拥有、必须是普通文件且不能是符号链接。没有命令行 key 参数或可覆盖的生产 base URL。

共享 XDG 路径、显式 dotenv、Provider gap 和当前来源边界见 [财务数据与证据](../financial-data-and-evidence.md)。`doctor --json` 不联网、不创建目录。

## 支持的 REST 能力

| CLI | REST 路径 | 关键约束 |
|---|---|---|
| `data search` | `/api/meta/tickers/search` | 固定 `asset_type=a-share`，最多 50 条 |
| `data snapshot` | `/api/a-share/prices/snapshot` | 必须显式提供完整 `thscodes`，不开放全市场分页 |
| `data history` | `/api/a-share/prices/historical` | 单标的、当前仅 `1d`、最长 10 年 |
| `data valuations` | `/api/a-share/valuations/snapshot` | 最多 100 个 A 股代码 |
| `data financials` | `/api/a-share/financials/*` | 年度/季度；limit 与时间区间互斥 |
| `data indicators` | `/api/a-share/financials/indicators` | `report` 格式为 `YYYY-1` 至 `YYYY-4` |
| `data corporate-actions` | `/api/a-share/corporate-actions/adjustment-factors` | 单标的；日期为 `YYYY-MM-DD` |
| `data calendar` | `/api/a-share/calendar/trading-days` | 服务端无参数，CLI 日期参数只做本地过滤 |

所有业务响应即使失败也可能是 HTTP 200，必须检查 `code`。`0` 成功；`4001/5002/5003` 可有限重试；认证、权限、参数、标的、未就绪和不支持错误不自动重试。响应中的毫秒时间按 `Asia/Shanghai` 解释。

## 输出与精度

客户端使用 Decimal 解析 JSON 小数，并在规范化 JSON 中输出为字符串，避免二进制浮点漂移。原始响应 bytes 只在显式 capture 时保存。财务指标 `value` 原本就是字符串或 `null`，必须原样保留。

## 数据分发边界

Fuyao 原始响应、规范化完整响应、capture receipt 和批量缓存只保存在 repo 外或仓库已忽略的 `local/evidence/`，不得进入公开 Git 历史。公开案例只提交派生报告、审计结果和 `evidence-manifest.json`；manifest 记录操作、抓取时间和 SHA-256，但不包含响应正文。自动化测试必须使用明确标记的合成 fixture，不得从真实响应裁剪后冒充合成数据。

## MCP

Fuyao 还提供 `/mcp/a-share`、`/mcp/a-share-index`、`/mcp/fund` 和 `/mcp/meta`。Money Craft 不默认生成 MCP 配置，以避免宿主差异和密钥散落；只有用户明确要求并接受对应宿主配置边界时再单独配置。

前瞻案例的实际核验提示：本次 `financials.income` 的 `period=quarterly` Q2/Q3 数字与财报累计栏一致，不能只据频率标签解释为单季。`report_date_ms` 也可能反映后续披露中的旧期比较值；历史报告期不等于历史可得快照。使用前瞻交叉核验入口时，明确累计口径、核对报告日期并保留本次抓取时间；该观察不代替所有标的/接口的字段核验。
