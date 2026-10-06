---
schema: money-craft.fuyao-acceptance.v1
security: 贵州茅台
thscode: 600519.SH
as_of: 2026-08-23
data_cutoff: 2026-08-23T19:40:16+08:00
---

# 600519.SH Fuyao 只读验收

## 结论

- 主能力矩阵 `10/10` 通过：搜索、快照、估值、行情历史、三张年度报表、年度指标、公司行动和交易日历均返回规范化结果。
- 最新季度三张报表 `3/3` 通过，2026 年半年度关键字段与公司正式半年度报告逐字段一致。
- 最新期间指标 `2026-2` 在有界重试后仍返回 Provider `5003/result empty`。客户端正确保留了可重试错误、Provider code 和请求关联信息；这是当前数据可用性限制，不是已发现的客户端合同缺陷。
- 凭据来自 repo 外 secure file；验收 artifact 不记录 API key。

## 能力矩阵

| 范围 | 用例 | 结果 | 证据 |
|---|---:|---|---|
| 主矩阵 | S01-S10 | 10/10 passed | `evidence-manifest.json` 的 S01-S10 哈希绑定；底层响应仅保存在本地私有 evidence |
| 最新报表 | S14-S16 | 3/3 passed | `evidence-manifest.json` 的 S14-S16 哈希绑定；底层响应不公开分发 |
| 最新指标 | S17 | provider unavailable | `evidence-manifest.json` 的 S17 错误 envelope 哈希绑定 |

`S10` 的成功结果带一个预期 warning：交易日历的请求区间由客户端在本地过滤。`S08` 和 `S09` 没有 Provider 顶层 source timestamp，但均保留 fetch timestamp 与返回数据；这不会被伪装成交易日时间。

## 关键交叉核验

| 字段 | 公司正式报告（CNY） | Fuyao（CNY） | 差异 |
|---|---:|---:|---:|
| 2025 营业收入 | 168,838,102,514.79 | 168,838,102,514.79 | 0.00 |
| 2025 归母净利润 | 82,320,067,101.68 | 82,320,067,101.68 | 0.00 |
| 2026 H1 营业收入 | 90,703,260,964.48 | 90,703,260,964.48 | 0.00 |
| 2026 H1 归母净利润 | 44,516,880,421.86 | 44,516,880,421.86 | 0.00 |

正式来源的 URL、抓取日期和内容 SHA-256 记录在 `evidence-manifest.json`；下载文件和运行账本保存在已忽略的 `local/evidence/600519/`，不进入公开 Git 历史。

## 公开数据边界

- 公开内容：研究报告、投资论文、确定性审计结果、验收摘要和证据 manifest。
- 私有内容：Fuyao 原始/规范化响应、capture receipt、下载的 PDF 与网页快照、逐宿主 smoke 原始输出。
- `tests/fixtures/fuyao/` 全部是手工合成的合同数据，不来自真实 Provider 响应。

## 时间边界

验收 `as_of` 是 2026-08-23（周日）。快照的 timestamp 是请求/服务时间，不应冒充成交时间；行情历史的最后一根日线是 2026-08-21，因此 Golden Case 使用 `2026-08-21 close` 作为股价时点。

## 未覆盖

- 没有交易、账户、写入或生产变更。
- 没有用推测值填补 `2026-2` 指标；后续应重试 Provider 或直接从正式报告计算并明确标为派生值。
- 本次只验证 600519.SH，不外推为所有 A 股标的都具有相同数据完整性。

## 完整性验证

- 本地私有 `captures/S01-S10` 与 `captures/S14-S16` 的 `response.json` 共 13 份，SHA-256 均与公开 manifest 绑定值一致。
- repo、安装 Skill 与验收 artifact 的 Fuyao key 模式扫描无命中。
- source validation、单元测试与 package check 均通过；正式报告和财务计算另由 report audit 与 financial audit 校验。
