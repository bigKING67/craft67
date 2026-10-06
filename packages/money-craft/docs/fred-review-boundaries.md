# FRED 整文件有界审查

2026-09-19，Review Craft bounded fast path；无评分、非 canonical 全仓审查。源码全文已读，直接 CLI 映射和 capture 调用边界已核对；既有测试加本轮回归为证据，不以测试数量代表分支全覆盖。精确源码哈希见 [本轮回执](../acceptance/fred-closeout-review-20260919.json)。

| 范围 | 决定与证据 |
| --- | --- |
| 凭据、路径、文件身份 | KEEP：环境变量优先，安全文件身份/权限/限量读取，已有竞态回归；父目录信任、同 inode 并发内容与 Windows/NFS 保留限制。 |
| 请求与重定向 | KEEP：CLI 负责参数准入；适配器固定端点、HTTPS、同主机跳转；自定义 opener 属可信调用方，不保证任意参数字典。 |
| 响应字节与解析 | FIX：实际长度与 Content-Length 核对；不足转网络重试，超出拒绝。标准库 HTTPResponse 的截断回归通过；深层 JSON 在当前 Python 已结构化拒绝，KEEP。 |
| HTTP 错误、重试、释放 | KEEP：三次上限、退避、状态保留及显式错误响应释放已有离线证据；独立 diff review 和默认 opener 真实网络生命周期证据仍缺。 |
| 身份、日期、转换 | KEEP：series 唯一身份、历史单日有效区间、观测日期范围和显式 units 绑定；不证明经济含义或上游转换算术。 |
| 分页 | DOCUMENT：合法部分页明确提示，缺元数据提示 unverified；保留原始 capture，不自动翻页。 |
| 输出与调用方 | KEEP：原始字节不改写，CLI 区分配置/格式/暂时失败；无自动交易能力。 |

## 保留的收口条件

FRED 继续 PARTIAL。源码全文阅读不等于生命周期高保障验收：仍需独立复核近期 credential/transport/network 改动，以及默认 opener 的受控 HTTPS/重定向/异常关闭证据。真实 FRED/ALFRED 数据连通性单列，不能用测试替代。

任意 realtime 区间、vintages 请求范围响应绑定、自动分页、HTTP 日期型 Retry-After、跨平台/网络文件系统不在已完成行为保证内。当前 CLI 暴露的 vintages start/end 仍需补范围绑定验收；不是把现有入口移出范围。

下一步先完成该现有入口的范围绑定，再做独立复核；不继续用零散补测替代模块收口。yfinance 随后处理，应用仍后置。

## 后续范围绑定结果

2026-09-19：上述 vintages start/end 已完成显式边界回显及逐日期闭区间验证，证据见[范围验收](../acceptance/fred-vintage-range-review-20260919.json)。该项从待办关闭；下一步为独立生命周期复核与默认 HTTPS 路径验收，模块仍 PARTIAL。前述清单保留为整文件审查时点的记录。

## 有界收口结果

2026-09-19：独立复核与默认opener受控TLS验收完成，见[最终回执](../acceptance/fred-https-review-20260919.json)。Decimal解析和重定向体读取/关闭两项发现均已修复，并按最终hash复验无剩余已验证阻断。模块转REVIEWED_BOUNDED，前述PARTIAL属于历史审查时点。真实FRED、其他Python/平台及来源语义不在本次通过声明内。

## 适配器行为明细（自 provider reference 迁出）

### 观测响应准入（2026-09-19）

当前 CLI 使用默认 `output_type=1`；适配器对该格式逐行核对对象、规范 ISO 日期及字符串数值，数值须可解析为有限 Decimal，缺失标记 `.` 原样保留，不转零。其他输出形态拒绝为 malformed_response，不假装已支持。响应出现错误字段时先核对错误信封，非法/缺失错误码不会因同时存在数据数组而当作成功；这些错误不写入成功 capture。

官方格式依据：[observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)、[errors](https://fred.stlouisfed.org/docs/api/fred/errors.html)。本轮仅验证离线注入及 CLI 错误传播，未请求真实 Provider 数据；不证明序列身份、单位、实时修订区间或经济含义已核验，其他端点及 transport/credential 边界仍待审。

### 传输与错误文本（2026-09-19）

FRED client 基础 URL 须为带主机的 HTTPS，不接受用户信息、查询串、fragment 或非法端口；默认重定向处理器只允许 HTTPS 且相同主机/端口，不允许降级。显式注入的 opener 属于调用方信任边界，不以这些检查保证其行为。错误信息先替换完整已知凭据再截断至 500 字符，避免截断留下凭据前缀；不声称识别任意变形、编码或上游已截断的秘密。离线注入与 CLI 传播测试不等于真实网络重定向验收。

### 凭据文件读取（2026-09-19）

安全文件在原路径检查后，以禁止跟随末级符号链接及非阻塞方式打开（平台支持时），通过同一文件描述符复核设备/inode、普通文件类型、所有者与权限，再最多读取上限加一个字节并校验实际长度。检查后替换、权限放宽或超限增长会返回 invalid_configuration，在网络与capture之前停止。文件缺失仍为missing_configuration；环境变量优先逻辑不变。不保证父目录可信性、同inode同时改写字节的一致快照或Windows/NFS语义。

### 序列身份与历史单日响应（2026-09-19）

`series` 必须返回唯一记录，且 id 与请求完全一致；`search` 每条记录必须为对象并有非空字符串 id，允许空结果。`vintages` 逐项校验规范 ISO 日期，不假设升序。`series`/`observations` 的单日 realtime 请求（CLI `--as-known-on`）要求响应顶层两个日期与请求一致，逐行有效区间包含该日；不要求逐行区间端点相等。异常作为 malformed_response 在成功 capture 前拒绝，保留合法原始响应字节。

依据：[series](https://fred.stlouisfed.org/docs/api/fred/series.html)、[vintagedates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html)、[Real-Time Periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)。observations/vintages 响应自身没有序列 id，本检查不能独立证明这些数值来自请求序列；仍依赖请求、传输与采集关联。任意 realtime 区间、观测日期范围、单位转换、分页完整性与真实 Provider 数据语义尚未闭环。

### 网络失败与响应释放（2026-09-19）

HTTP 错误体只做有界读取，读失败不覆盖已知 HTTP 状态；在重试前显式关闭错误响应。读失败或关闭失败会在结构化错误消息中保留通用诊断，不回显底层秘密。429/5xx 仍按原策略最多尝试三次，400 等不可重试状态直接失败。正常响应读取阶段的 HTTP 协议异常（包括 IncompleteRead）转换为可重试 network_error，context manager 负责退出释放。非有限 Retry-After 值回退默认退避；有限秒数继续限制在 0..10。

离线回归覆盖读取中断、关闭失败、三次重试耗尽及真实 CLI 入口错误传播；失败返回 EXIT_TRANSIENT，不写成功 capture。此处三次上限是尝试次数，不是总耗时保证；不声称真实网络、HTTP 日期形式 Retry-After 或全部协议状态已验收。

### 分页、观测范围与转换口径（2026-09-19）

观测日期须落在请求的 observation_start/end 闭区间内；显式请求 units 时，响应转换标识须完全一致。此处 units 表示 lin/pch 等转换，不是币种，也不证明上游计算正确。分页 count/offset/limit 如出现任一字段，须全部为合法整数、与请求匹配且条数自洽；返回条数不得超过请求 limit。完全缺少分页元数据时保留响应，但 CLI 警告完整性 unverified；合法非完整页则提示 partial page。不会自动遍历分页，不把一次成功采集等同于完整数据集；原始 capture 保留上游分页字段，CLI 警告不另写入原始响应。依据：[FRED observations](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)。

### 响应长度（2026-09-19）

存在 Content-Length 时，读到的字节数须一致；不足视为可重试读取中断，超过则拒绝为 malformed_response。无长度头时仍受响应体大小上限与 JSON 准入约束。已用标准库 HTTPResponse 的截断消息做离线回归，不代表默认 opener 或真实 HTTPS 网络已验收。

### 修订日期查询范围（2026-09-19）

`vintages --start/--end` 映射到 realtime_start/end。显式边界必须由响应顶层原样回显，返回日期不得越过请求闭区间；只指定一侧时只绑定该侧。允许空结果、边界当天及倒序结果，不额外推断未指定边界。异常在成功 capture 前以 malformed_response 拒绝。依据：[vintagedates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html)。这是请求/响应范围核验，不证明修订历史完整或来源内容真实。

### 默认 HTTPS 路径验收（2026-09-19）

默认 urllib opener 已通过当前 Python/macOS 的本地 TLS 服务验证：同主机跳转成功，跨主机与 HTTPS 降级在目标访问前拒绝；503、最终响应截断和跳转响应截断有界重试，400 不重试。跳转响应体单独有界读取，301/302/303/307/308 复用标准库跳转策略并在异常时关闭原响应。极端 JSON 指数导致的 Decimal InvalidOperation 转为 malformed_response。测试采用临时自签证书与进程内临时 CA 信任，不更改系统信任或用户凭据；不等于真实 FRED/ALFRED 连通性验收。
