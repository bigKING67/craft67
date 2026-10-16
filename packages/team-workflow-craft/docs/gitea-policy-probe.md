# Gitea 保护规则的隔离行为验收

[gitea_policy_probe.py](../tests/live/gitea_policy_probe.py) 是手动选择的测试工具，不属于安装后的 Skill，也不会由离线门禁启动。它会在一次性恢复副本内创建临时成员、合成 Git 提交、PR 和审批，验证真实 Git/REST 行为；它不是生产部署、公司代码迁移或真人协作测试。

## 运行边界

先按 [恢复方案](gitea-vps.md#备份与恢复) 建立新本机恢复项目。当前探针要求一个空私有仓库及已经配置的 main 规则：禁止 push/force push，至少一次审批，内容变化后撤销审批，阻止被拒审和落后分支合并，管理员不可绕过，指定 owner 合并，没有 CI 状态门禁。

探针只接受本机 Unix-socket Docker context、`twc-gitea-restore-<8 位 hex>` 项目、restore.example.invalid、无 host port/Traefik、仅 internal 网络，以及属于新项目的卷；拒绝可写宿主 bind。Python helper 使用已有本地 image ID，不自动拉镜像，不挂 Docker socket。Token 不进入参数/日志，收尾撤销后再验证拒绝访问。

```sh
python3 tests/live/gitea_policy_probe.py \
  --context <local-context> --project twc-gitea-restore-<8hex> \
  --repository <org/repo> --owner <fixture-owner> \
  --python-image sha256:<local-python-image-id> \
  --output <protected-directory>/policy-receipt.json
# 核对目标后加 --apply；此操作会改变一次性副本。
```

无 `--apply` 只返回计划。`--apply` 的初始种子仅为测试暂时允许 fixture owner 首次 push，随后恢复 main 禁止 push。探针拒绝向已有内容的仓库写测试提交。成功或失败后都要按该恢复项目的准确命名空间清理容器、卷和网络；不删除原始备份。

## 验收内容与已知语义

覆盖开发者 main 直推/非快进强推/删除拒绝、任务分支和 PR、作者自批拒绝、缺审批时 owner 普通/force merge 拒绝、非名单成员合并拒绝、代码变化后旧审批失效、基线落后拦截、请求修改拦截，以及重新验证/确认后的串行合并。TWC 以只读权限真实读取 task/change/reviews/statuses，并验证写入拒绝；空 statuses 记为未运行，不是通过。

首次样本曾假定“只更新基线也必须由服务器撤销审批”，该断言失败，样本保留为 incomplete。现场观察与 [Gitea 官方语义](https://docs.gitea.com/usage/access-control/protected-branches/) 一致：PR 内容不变时可保留原审批。因此测试明确检查这一行为，再由审查者针对新 head 确认后合并。团队合同仍要求 head/base 变化后重新验证组合，不声称平台独立强制了全部流程。

本工具不执行真实产品测试或 CI，不证明 CI 身份可信，不覆盖所有竞态/权限组合、AGit、跨仓 fork、生产系统或三宿主加载。报告中的 passed 仅针对列出的固定场景。普通包门禁额外验证探针拒绝非隔离环境，不调用 Docker daemon 启动此流程。
