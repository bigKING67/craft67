# yfinance 有界审查范围

2026-09-19。范围为 yfinance_adapter.py 全文及其直接 CLI 参数/错误映射；普通独立审查，无 canonical 全仓评分。

| 范围 | 处置 |
| --- | --- |
| 可选依赖与版本化导出 | KEEP：核心无强制 pandas 导入，导出保留 Provider/版本/参数与 Decimal 精度；真实 pandas 缺失单例归 null。 |
| search与snapshot | KEEP：坏搜索行整批拒绝，快照类型/缺失准入；请求 symbol 回填不等于独立证券身份验证。 |
| 表格 | KEEP：按位置导出，先验完整维度/类型再截列；公司行动币种列显式文本例外。 |
| 日期 | KEEP：历史闭区间拒绝越界；公司行动先验再过滤，按时间戳自身日历日比较。 |
| 错误重试 | FIX：补连接超时与builtin TimeoutError；证书和数据格式错误不重试。最多三次不等于总耗时上限。 |
| 序列化 | FIX：UTF-8 JSON失败结构化，损坏Unicode不逃逸CLI；不输出损坏内容。 |

验证使用真实 pandas 3.0.6、NumPy 2.5.3、yfinance 1.7.0 与 Python 3.14.7 的临时环境；Provider 返回由离线夹具控制，不请求 Yahoo。原用户 data venv 的失效 Python 链接未修复。

非空表不证明数据真实完整，研究层仍需证券/币种对账与正式披露。未验证真实网络、交易日完整性、重复日线、交易所时区真实性、财报标签经济语义、全部 dtype/依赖版本及跨平台。未提供交易、账户、自动缓存回填或通用数据修复能力。

最终源码hash、独立复核和状态以[收口回执](../acceptance/yfinance-closeout-review-20260919.json)为准。

## 适配器行为明细（自 provider reference 迁出）

### 缺失数据准入（2026-09-19）

search 每条结果须为对象且有非空字符串 symbol，不静默丢弃坏行。snapshot 的行情/市值/股数等字段至少一个非缺失，只有 currency/exchange 等元信息不算行情数据；history、valuations、financials 至少一个非缺失单元格。完全缺失返回 transient_provider_error，最多三次尝试，失败不写成功 capture。非有限 Decimal 与 float 均归缺失，零值保留；其他字段仍允许缺失。

空 corporate-actions 仍允许成功，表示该次结果没有事件；不能由此证明上游没有漏数。此轮只核验缺失和搜索身份形态，非缺失不代表数值类型、表格维度、日期范围、单位或证券真实身份已经校验；这些另待审。

### 表格位置与维度（2026-09-19）

导出直接按原始 itertuples 位置读取，不再用标签列表经 loc 重选，以免重复标签导致行列扩增或取错值。每行宽度先与完整 columns 比较，行数与 index 比较，通过后再按请求限制列数；不靠切片隐藏维度错误。重复标签原样保留，表示位置数组，不宣称标签唯一。空轴也保持 index/columns/rows 对齐；必需表仍受全缺失准入约束。此轮为表接口离线夹具验证，当前验证环境未安装 pandas，真实 pandas 对象行为仍须另验；数值类型和日期范围未因维度通过而视为已验证。

零列且非空 index 的 pandas 表在 index=False 时不产生 tuple；导出按 index 位置保留空行，避免将合法空数据错判为结构损坏。已按本地 pandas 源码提取行为复核；旧数据运行环境解释器链接失效，仍不视作完整 pandas runtime 验收。

### 快照数值类型（2026-09-19）

snapshot 的价格、市值与股数字段在 scalar 归一化后只接受非 bool 的 int/有限 Decimal 或缺失；不把字符串数字、布尔值、列表/对象转成行情数字。非法字段整条拒绝为不可重试 malformed_response，诊断只含字段名不回显异常值。浮点数归 Decimal、非有限值归缺失、零值保留沿用现有规则。此处不检查价格/市值/股数之间的关系、正负范围或币种，财报及历史表数值类型另待审。

### 表内数值类型（2026-09-19）

历史行情、估值、财报和公司行动使用的表导出，在 scalar 归一化后逐单元格检查：数值列只接受非 bool 的 int/有限 Decimal 或缺失。字符串数字、日期对象、布尔值与容器不作为表内金融数值；标签仍独立保留，不对行列标签应用此检查。先检查完整行，再限制输出列数，不用截列掩盖异常值。有限小数精度、负值、零值和现有缺失规则保留。此处未建立真实 pandas 的 NA/NaT 全部类型覆盖，也不证明日期范围、单位或数值间关系。

固定版本 yfinance 1.7.0 的 corporate-actions 包含 `Dividends FX` 币种列；仅此操作的此列明确允许字符串（含空字符串）或缺失，原样保留。其它操作与数值列不因此允许字符串。该例外依据本地固定版本 get_actions 源码及离线回归，不把币种文本存在当作币种语义已验证。

### 历史与公司行动日期（2026-09-19）

日线 history 的 index 须为规范 YYYY-MM-DD 或完整可解析 ISO 时间戳，且逐项落在请求 start/end 闭区间内；越界拒绝，不静默裁掉。时间戳按其自身日历日期比较，不转 UTC 改变市场日期；这不证明其时区与交易所时区匹配。

corporate-actions 返回全历史再本地过滤，所以先校验全部 index 日期（未指定范围也校验），再保留闭区间日期；坏日期不因位于过滤范围外而隐去。缺少可过滤表接口时明确失败。空表沿用已有准入语义。财报期间标签、交易日完整性、重复日线、时区真实性和真实 pandas 运行另待验。

### 真实 pandas 缺失值与导出验收（2026-09-19）

在独立临时环境 Python 3.14.7、yfinance 1.7.0、pandas 3.0.6 上，以真实 DataFrame 验证重复标签、零列、可空 Int64、时区 index 和可空分红币种；不请求 Yahoo 数据。`pd.NA` 与 `pd.NaT` 按已加载 pandas 的单例身份转为 None，避免导出字面量 `<NA>`/`NaT`。缺失日期 index 仍拒绝；普通同名字符串不被视为缺失。导出保留 JSON null、数值零及既有 Decimal 字符串精度合同。

这补充了先前仅夹具/源码提取的证据，不修复原数据环境失效的 Python 链接，也不证明真实 Provider、所有 pandas 版本或所有 dtype 已兼容。

### 超时分类（2026-09-19）

固定依赖 curl_cffi 的 ConnectTimeout、ReadTimeout 与 Python TimeoutError 纳入现有三次尝试和0.5/1秒退避；不以异常继承自 ConnectionError 为由将 SSLError 等证书失败全部当暂时故障。按实际依赖异常对象离线验证，未执行真实网络故障注入；三次限制不代表总耗时上限。

### 导出失败边界（2026-09-19）

adapter-export 必须可编码为 UTF-8 JSON；孤立 Unicode surrogate 等序列化/编码失败转换为不可重试 malformed_response，错误文本不回显损坏内容，不创建成功 capture。JSON 编码显式禁止非有限裸数值；不通过 ASCII 转义将损坏文本留给后续 CLI。

### CLI 退出码（2026-09-19）

yfinance 缺少可选依赖属于配置问题，CLI 返回 3；malformed_response 返回 6；可重试故障返回 5；其余Provider故障返回4。保留JSON error.kind/retryable及无成功capture行为。此前日期越界和损坏Unicode回执中记载的退出码4属于旧映射，新版本同类格式错误使用6；历史回执不回写。

### 本地缓存锁冲突

多进程同时初始化 yfinance 的 SQLite 缓存可能返回 `OperationalError: database is locked`。适配器仅对这一消息和 `database table is locked` 按既有上限重试三次，间隔0.5/1秒；耗尽仍返回 transient_provider_error，不写成功capture。其他数据库错误不自动重试，不删除缓存或cookie来掩盖失败。
