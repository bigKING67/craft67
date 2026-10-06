# CLI 输入前置校验

当前整文件审查已于 2026-09-19 收口，见[统一回执](../acceptance/core-closeout-20260919.json)。以下分项是历史验证证据，不是待办队列。最终补齐凭据 HTTP 头编码/控制字符准入、最大日期范围及 JSON 孤立 surrogate 的 capture 前拒绝。

2026-09-19。data 的操作/证券/期间参数先由 prepare_operation 校验，再检查 capture-dir/source-id 配对与来源ID格式，之后才读取凭据或构造Provider。错误输入不应触发数据请求；这项检查不保证目录可写，也不代替 capture 发布时的文件系统检查。

所有调用 parse_iso_date 的入口仅接受规范 YYYY-MM-DD 日历日期。Python 可解析的紧凑日期与ISO周日期也拒绝，防止原串流入Provider参数或字典序日期比较。闰日按真实日历解析。

退出码沿用 usage_error/2，不改变合法参数路径。证据见[回执](../acceptance/cli-preflight-review-20260919.json)。

## Provider 标识冲突

2026-09-19：yfinance 路由显式拒绝 Fuyao 专用 thscode/thscodes，即使其值为空字符串也拒绝，不静默忽略。五个支持 symbol 的市场数据入口保留原有效行为。Provider/凭据尚未访问时返回 usage_error/2；证据见[冲突验收](../acceptance/cli-provider-conflicts-review-20260919.json)。

## 显式空日期

2026-09-19：可选 start/end/as-known-on 用 None 判断是否省略，不用真假值判断。显式空字符串仍进入规范日期校验并返回 usage_error/2；省略参数才保留默认范围/当前时点行为。适用于FRED series/observations/vintages、calendar与corporate-actions。证据见[空日期验收](../acceptance/cli-empty-dates-review-20260919.json)。

## 显式数据运行环境

2026-09-19：MONEY_CRAFT_DATA_PYTHON 显式配置必须指向可执行文件；缺失、目录、不可执行或启动失败返回配置错误3，不能静默使用当前Python。启动入口将路由配置错误输出为结构化JSON。默认候选不存在仍可保留当前解释器，处于已激活venv时原默认优先级保留。实际正向launcher测试验证重启guard防循环。此处不校验任意可执行程序是否为Python，也不修复既有环境；详见[运行路由验收](../acceptance/cli-runtime-review-20260919.json)。

2026-09-19 依赖探测进程输出无法解码，或当前解释器find_spec抛ImportError/ValueError时，返回全False与错误类型，不暴露原异常文本。doctor仍可输出诊断；模块可发现不等于可成功导入或原生库就绪。 见[依赖探测验收](../acceptance/cli-probe-review-20260919.json)。

2026-09-19 yfinance诊断调用方：doctor的configured仅表示当前解释器可发现模块，不保证import/原生库/网络可用；dependency_probe_error记录探测失败。研究计划与采集使用同一探测入口，异常转invalid_configuration/CONFIG3；普通缺包保留auto降级、required报missing_optional_dependency，disabled或不支持证券不探测。见[调用方验收](../acceptance/cli-yfinance-probe-review-20260919.json)。

## Fuyao 凭据与错误消息

2026-09-19：凭据文件通过初始属性检查后，以 NOFOLLOW/NONBLOCK 打开，再检查实际文件的 dev/inode、常规文件类型、所有者和权限；实际读取不超过 MAX_API_KEY_BYTES+1，超长拒绝。检查/读取失败返回配置错误，错误消息不包含原始读取异常。消息脱敏在换行归一化和500字符截断之前执行。证据见[凭据验收](../acceptance/fuyao-credential-review-20260919.json)。

此处是 POSIX 临时文件验证，不保证父目录不受替换、同一 inode 内容不被并发改写或 Windows/NFS 行为。文件读取安全不证明凭据有效；本轮未使用真实凭据或请求 Fuyao。

## CLI 剩余验收范围

以下是范围清单，不是新增覆盖声明。各历史回执只证明其记录的版本与输入。

| 范围 | 当前证据与下一步 |
|---|---|
| data 参数、Provider 错误映射 | 已有前置校验及错误码回执；继续核对其余参数组合与顶层返回语义。 |
| 运行环境与依赖诊断 | 已验启动失败、探测异常及 yfinance 调用方；可发现不等于导入/原生库/网络就绪。 |
| Fuyao 凭据 | 本轮校验文件替换、FIFO、增长及错误脱敏；环境值格式、平台差异仍待集中核对。 |
| Fuyao 传输与响应 | 已验重定向、HTTP错误关闭、截断响应、JSON异常及重试边界；整体封口仍需完整响应语义与其余异常分支；成功null及重复JSON键准入已有后续回执。 |
| capture、research、track | 有既有生命周期回执；不能替代各模块剩余分支及恢复边界的整体验收。 |
| audit、earnings、thesis、report 与 main | 各核心模块测试不等于全部CLI分流、错误传播和退出码已审；报告真实PDF验收另列。 |

## Fuyao 传输与响应边界

2026-09-19：重定向必须保持原scheme及netloc，拒绝userinfo；生产默认HTTPS不可降级到HTTP。显式base_url原有HTTP能力保留用于本地HTTP夹具，不将其声明为HTTPS强制策略。urllib默认跳转体读取限制为MAX_RESPONSE_BYTES+1，并检查声明长度，跳转响应在finally关闭。

HTTPError响应关闭后按原状态分类；关闭发生OSError时保留HTTP错误码并附通用cleanup诊断，不泄露底层异常。最终响应实际长度与Content-Length核对，短读按网络错误最多3次，超量矛盾按schema错误。缺失Content-Length仍按实际字节上限读取。

JSON业务code必须为int且不能是bool；Decimal指数无法表示及过深嵌套转schema错误，解析消息不包含响应片段。Retry-After的NaN/Infinity不参与重试延时；既有有限数值0至10秒裁剪保留。证据见[传输验收](../acceptance/fuyao-transport-review-20260919.json)。

本轮使用默认urllib opener与临时自签证书、本地HTTPS服务器验证；没有真实Fuyao请求。尚未证明全部远端响应语义、数据字段真实性、任意I/O异常或所有平台行为；CLI仍PARTIAL。

独立复核补充：redirect handler的finally关闭失败不得覆盖已存在的HTTP拒绝、schema或transport异常；HTTP/schema错误仅追加通用cleanup诊断。urllib正常drain阶段及无原始异常时的关闭失败转local_io_error/4，不暴露底层异常，也不进入网络重试。降级拒绝与超限拒绝叠加close失败、正常drain后close失败均有回归。

## Fuyao 成功信封与重复 JSON 键

2026-09-19：依据本轮重新读取的[官方聚合文档](https://fuyao.aicubes.cn/llms-full.txt)响应信封章节，保留合法成功空列表，非零业务错误仍可携带data:null。客户端对code=0且data:null采取schema错误拒绝策略，避免生成ok:true且没有业务数据容器的capture。它不是对所有endpoint字段的完整验证；空对象、行身份和数值真实性仍需后续按接口合同核查。

解析器拒绝任何层级的重复JSON对象键，包括重复业务码或重复数据字段；错误消息不输出键名或值。上述两类错误返回malformed_response/6，不重试，在capture创建之前停止。真实CLI子进程使用合成opener响应验证，未请求真实API。见[响应准入验收](../acceptance/fuyao-response-review-20260919.json)。

成功null拒绝属于Money Craft准入策略；上述官方文档没有逐接口明确禁止该组合，不能将此客户端规则写成官方保证。

## Fuyao 批量标的绑定

2026-09-19：CLI的snapshot/valuations在成功响应解析后、capture前核对data.item为数组及行对象；thscode必须属于请求集合且不能重复，ticker须与thscode六位前缀一致。缺失、错配、重复标识返回malformed_response/6；不通过重试掩盖响应合同错误。

[官方聚合文档](https://fuyao.aicubes.cn/llms-full.txt)的估值接口明确允许未返回股票被省略以及空列表。因此合法部分/空结果仍成功，CLI warnings按请求顺序列出没有返回行的标的，不补零、不生成占位行。snapshot也保留合法空列表。警告不等于研究证据完整；需要下游对缺失数据作明确处置。

此处仅约束两个CLI入口（以及通过该CLI执行的采集），直接调用FuyaoClient不自动获得该校验。未验证数值、时间戳、total、顺序或其他接口标的绑定，也不保证响应中自报的证券身份真实。20个真实CLI子进程合成响应案例覆盖14个非法及6个完整/部分/空结果；见[标的绑定验收](../acceptance/fuyao-identity-review-20260919.json)。
