# 运行回执信任边界加固

日期：2026-09-23。结论：`whoami.runtime-receipt.v1` 继续严格校验声明参数和全部产物哈希，但不再凭仓库内文件自证真实模型运行。v1 完整匹配时只返回 `runtimeBound=true`；`runtimeVerified=false`，最终状态保持 PARTIAL。

## 原缺口

旧实现会在 v1 回执存在、运行字段不含 `UNVERIFIED` 且内容评审 PASS 时返回 `runtimeVerified=true` 和 `status=verified`。但 v1 回执与 manifest 都位于同一目录，没有外部信任根、宿主签名验证或 provider 远端查询；任何人都能手写一组内部一致的 JSON。因此旧状态只能证明文件自洽，不能证明声明的模型实际生成了回答。

## 修复

- 保留 v1 的 schema、模型与采样参数比对，以及 Skill、任务、input、context、response 的逐项 SHA-256 绑定；错绑继续拒绝。
- 新增 `runtimeBound`。只有回执存在、绑定全部通过且所有运行声明字段都不是字面量 `UNVERIFIED` 时为 true；temperature 与 seed 可按合同显式为 null。
- v1 不再设置 `runtimeVerified=true`，也不能把内容 PASS 升级为 `verified`。内容 FAIL 仍返回 failed；其余返回 partial。
- 输出限制明确区分缺回执、文件绑定不完整、文件已绑定但没有受信宿主证明三种情况。
- 不接受清单自带公钥或自行签名作为信任根。未来若要启用 verified，须由仓库外预先信任的宿主身份验证或 provider readback 建立独立证据。
- 独立终审同时发现 `review.status` 曾通过 `String(...)` 接受 `['FAIL']` / `['PASS']` 数组，后续严格比较会绕过 FAIL 与 PASS 问题计数合同；现改为严格字符串枚举并增加两个数组反例。

## 验证与限制

合成回执回归现在明确断言：字段和哈希全部匹配时 `runtimeBound=true`、`runtimeVerified=false`、`status=partial`；合法字符串 `FAIL` 保持 failed；数组状态直接拒绝。原有参数缺失、参数错绑、产物错绑、路径越界和符号链接越界拒绝保持不变。当前改动只收紧证据等级，不改变 input/context 重算或固定前向样例内容。

修复后独立终审重跑 acceptance 定向测试 5/5 PASS，确认 v1 自证升级路径与数组状态绕过均已关闭；本轮范围未发现遗留 blocker、high、P2 或 P3。

## 后续 v2

同日后续新增 `whoami.runtime-receipt.v2` 外置 Ed25519 信任根验证。它没有放宽 v1：v1 仍只能形成文件绑定；v2 必须由调用方显式提供清单目录树外的受信公钥。实现与边界见[外置 attestation 记录](2026-09-23-runtime-attestation-v2.md)。

这项修复仍未提供真实宿主 attestation。它关闭了文件自证升级路径，不等于已经获得可验证的模型运行身份。
