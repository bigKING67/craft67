# 项目配置与 Gitea

```sh
python3 <skill>/scripts/twc.py --project <repo> init --dry-run \
  --base-url https://git.company.example --repository company/product --base-ref origin/main
# 核对后用同一命令的 --apply 创建配置、固定工具链锁和 local ignore。
python3 <skill>/scripts/twc.py --project <repo> doctor --online
```

域名/仓库须替换成真实批准实例；已有 `.team-workflow` 不覆盖。默认不创建或修改 AGENTS.md/CLAUDE.md，不猜测试命令。Trellis 管流程时 init 加 `--workflow-owner trellis`。

Token 仅从 `coordination.token_env` 指定的环境变量读取，默认 `TWC_GITEA_TOKEN`；通过公司批准的秘密管理方式提供，不写配置、URL或日志。申请所需最小只读身份/仓库/Issue 权限，具体以实例版本为准。工具不管理模型 Key、宿主登录、账号权限或服务器部署。

HTTPS 必需，验证 TLS，不跟随重定向。GET 有限重试，列表翻到空页或达到上限报 incomplete。`auth_required/forbidden/not_found/unavailable/unsupported/invalid_response/incomplete` 分别保留；404 不擅自断言不存在，可能权限隐藏。doctor 默认离线，`--online` 仅请求当前身份、仓库和版本，其他能力仍需相应路径实测。

PR 读取 reviews 与 commit statuses；statuses 不是所有 Actions/check-run 的完整集合，空列表不表示通过。开发依据 [Gitea API Usage](https://docs.gitea.com/development/api-usage/)；上线须核对公司实例 `/swagger.v1.json` 和真实权限/字段语义。

doctor 核对项目级同名入口和安装清单，而不只检查文件存在；当前宿主会话加载及全局同名入口仍明确未核验。配置与同实例 Git remote 的仓库路径不一致时拒绝 prepare；SSH alias/缺 remote 无法从本地确证时保留 unverified，交接不会据此给出 advisory_ready。

`toolchain.lock.json` 固定 version/protocol/runtime_tree_sha256，不自动更新 latest。这个内容哈希覆盖 Skill 源文件，来源真实性仍由批准的构建产物 SHA256 和分发渠道负责。源码、ZIP、安装副本和宿主会话加载分开验收。
