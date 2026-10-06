# 外置 Ed25519 运行 attestation

日期：2026-09-23，2026-09-24 加固。结论：验收器新增 `whoami.runtime-receipt.v2`。只有核验者显式提供清单目录树之外的受信 Ed25519 公钥，且签名、keyId、运行字段、全部产物、rubric 与 review 绑定通过时，才形成 `runtimeAttested=true`；运行声明完整且受签内容评审为 PASS 时才可返回 verified。v1 仍保持 bound-only。

## 信任与签名合同

- CLI 新增 `acceptance-check --trusted-runtime-key <ed25519-public.pem>`；不从 manifest、receipt 或相邻目录自动发现公钥。
- 公钥必须是 Ed25519 SPKI PEM，实际路径须在 manifest 目录树之外；验收器以 SPKI DER 的 SHA-256 计算 `ed25519:<hex>` keyId。
- v2 attestation 固定 `algorithm=Ed25519`，signature 必须是规范 base64。错误 keyId、错误签名、缺公钥、清单内公钥、非 Ed25519 公钥和无法解析的公钥全部拒绝。
- payload 使用 `whoami.runtime-attestation.v2`，绑定 suiteId、runId、绝对 startedAt、规范 runtime、Skill、任务、rubric、逐 case input/context/response 哈希，以及 review 状态和全部五项计数。
- `runtimeAttestationPayload` 对全部嵌套对象递归按键名词法序生成 canonical JSON；数组顺序保持不变。对象插入顺序不同不会改变签名字节，签发方应复用该 helper。
- v2 回执的 `bindings.rubric` 必须与 manifest 的 rubric 哈希相同。量表、review 或任一受签字段变化都需要重新签发，不能通过只改清单、回执普通字段或 artifact 哈希沿用旧签名。
- `startedAt` 必须可解析为带时区或 Z 的绝对时刻；任意说明文字不能进入可验证回执。

## 状态语义

| 条件 | runtimeBound | runtimeAttested | runtimeVerified | 最终状态 |
|---|---:|---:|---:|---|
| 无回执 | false | false | false | PARTIAL 或 failed |
| 完整 v1 | true | false | false | PARTIAL 或 failed |
| v2 签名通过但运行声明含 `UNVERIFIED` | false | true | false | PARTIAL 或 failed |
| v2 签名通过、运行声明完整、review PASS | true | true | true | verified |
| 任意回执、review PARTIAL | 取决于回执 | 取决于回执 | 取决于回执 | partial |
| 任意回执、review FAIL | 取决于回执 | 取决于回执 | 取决于回执 | failed |

## 验证边界

定向测试使用临时生成的 Ed25519 密钥，私钥只存在于测试进程内存，公钥写入 manifest 目录外的临时目录。测试覆盖直接函数与 CLI 验证成功，受签 PASS/PARTIAL/FAIL 状态矩阵，递归键顺序重排，以及缺公钥、清单内公钥、错误公钥、错误签名、非规范签名、无效 startedAt、未重签篡改 rubric 和未重签篡改 review 的拒绝。临时测试密钥只验证协议实现，不是生产宿主身份，也没有用于任何固定语义套件。

首次独立审查确认两项缺口：旧 payload 未覆盖 rubric 与 review，可把已签失败清单改成 verified；旧 helper 还受嵌套对象插入顺序影响。2026-09-24 的加固将两者纳入 v2 canonical payload，并保留对应攻击反例与顺序互操作回归。此处的工程通过只证明本地协议行为，不证明外部宿主已经签发真实回执。

## 2026-09-24 独立终审

独立复审结论为 PASS，未发现剩余 blocker/high/P2/P3。复审实际确认：已签 FAIL 改为 PASS/0 会因签名无效拒绝；五项 review 计数逐项篡改全部拒绝；替换 rubric 并同步更新 manifest、receipt 普通绑定与文件哈希仍不能沿用旧签名；v2 缺 `bindings.rubric` 拒绝；runtime、bindings、case 与 review 的对象键顺序重排后 payload 字节相同并可验签。完整 v1 仍为 bound-only，受签 PASS/PARTIAL/FAIL 状态矩阵和含 `UNVERIFIED` 的降级行为保持合同。

本地 `npm run check` 为 117/117 PASS，TypeScript strict 与 build PASS；Skill quick_validate 在隔离补入 PyYAML 后 PASS。七份固定前向 manifest 全部可重放且仍为 PARTIAL，因为它们都没有真实 v2 attestation。临时测试密钥和独立探针不构成生产宿主身份或评审内容真实性证明。

该能力提供验证入口，不负责替真实宿主签发回执。公钥是否属于受信宿主仍由调用方依据仓库外渠道确认；随 receipt 一起收到的新公钥不能自动视为可信。
