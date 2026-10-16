# CNB 接入

用于公司批准的 CNB SaaS 私有仓库。`base_url` 固定 `https://cnb.cool`，工具只向官方 `https://api.cnb.cool` 发送只读请求；不从任意主机名推导 API 地址。不支持未经验证的私有化 CNB 端点。

```sh
python3 <skill>/scripts/twc.py --project <repo> init --dry-run \
  --provider cnb --base-url https://cnb.cool \
  --repository organization/product --base-ref origin/main
```

已有配置不能用 init 覆盖；显式核对并更新 provider、base_url、repository、token_env、base_ref，以及获批准产物的工具链锁。旧平台的 packet/binding/evidence 不可直接当作新平台证据，需重新 prepare/verify。已有 Trellis 项目加 `--workflow-owner trellis`。

CNB 最小权限采用两枚个人只读 Token，不写入 TOML、Git、URL 或日志：

- `TWC_CNB_TOKEN`：资源仅指定目标私有仓库，授予下表五项 repo 读取权限。
- `TWC_CNB_IDENTITY_TOKEN`：只授予 `account-profile:r`，不授予任何 repo/group/registry 权限。资源类型需允许账号 API；不因此开放其他私有仓库。

2026-10-15 实测指定仓库的 Token 保存后未保留 account-profile 权限，账户接口返回 403；不要将仓库 Token 改成全资源并保留 repo-code 等权限来绕过。`init --provider cnb` 默认生成 `identity_token_env = "TWC_CNB_IDENTITY_TOKEN"`；已有获批准且可读账号的 Token 可以省略此字段，但不建议为此扩大授权。两枚 Token 都应属于操作本人；读取账户 Token 不能认证另一枚仓库 Token 或 Git push 使用同一账号，actor 会明确记录这一边界。Git push 的个人凭据单独配置。所需读取合同如下：

| 读取 | 官方端点 | Token 权限 |
| --- | --- | --- |
| 当前账号 | `/user` | `account-profile:r` |
| 仓库信息 | `/{repo}` | `repo-basic-info:r` |
| Issue | `/{repo}/-/issues/{number}` | `repo-issue:r` |
| PR | `/{repo}/-/pulls/{number}` | `repo-pr:r` |
| PR 审查 | `/{repo}/-/pulls/{number}/reviews` | `repo-notes:r` |
| 指定提交状态 | `/{repo}/-/git/commit-statuses/{sha}` | `repo-code:r` |

依据 [CNB OpenAPI](https://docs.cnb.cool/zh/develops/openapi.html) 与 [官方 Swagger](https://api.cnb.cool/swagger.json)，2026-10-15 核对。身份将原始 `username/nickname` 映射为通用 `login/full_name`，账号 ID 保留字符串，避免大整数精度损失；Issue/PR 编号按 CNB 字符串合同检查。PR 直接读取 PR 端点，不把同号 Issue 当成 PR。审查分页使用 `page_size`；达到上限返回 incomplete。

`doctor --online` 检查账号和仓库；CNB 没有公开服务器版本端点，version 明确为 unsupported，不伪造版本，也不因此把其他成功读取判失败。401/403/404/网络/畸形响应分别保留真实状态；404 也可能表示没有私有资源访问权。

`get_checks` 只读取完整 head SHA 对应的 commit statuses，空列表不是通过；没有读取 PR 合并预览、完整构建作业或分支保护，所以不能用它声称服务器门禁通过。CNB 的 `pull_request` 构建针对合并预览，验收时另核对实际构建 SHA、当前 base/head 与策略。[构建触发规则](https://docs.cnb.cool/zh/build/trigger-rule.html)

开发者角色本身包含合并权限。仅在任务契约填写 integrator、要求管理员审批或给团队起名，都不能证明只有指定人能合并。需在实际仓库配置保护规则，并以不同账号验证直推/强推/自批/拒审/陈旧审批/普通成员合并和管理员路径；未经实测保持 unverified。[角色权限](https://docs.cnb.cool/zh/guide/role-permissions.html)

TWC 不创建账号/仓库/Token、不发评论、不推送/合并/部署；授权的平台配置仍由管理员通过原生界面完成。
