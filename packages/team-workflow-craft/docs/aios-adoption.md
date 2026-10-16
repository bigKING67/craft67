# AIOS 接入 CNB：协作主仓库、镜像与发布来源

状态：已转向 CNB，创建私有空仓库 `bql_huayue/aios`；原 VPS Gitea 已停用并保留 Mac 加密备份。用户明确选择暂缓 AIOS 历史导入，生产发布来源尚未切换。本文件不覆盖 AIOS 当前 AGENTS、Trellis 和部署规范；实施由 AIOS 的 `10-15-gitea-team-adoption` Full 任务和运行手册承接，避免形成第二份运行权威。

## 推荐关系

```text
成员独立 clone / 任务分支
    → CNB 私有仓库：Issue → PR → 审查/检查 → main
        ├→ 发布负责人选择完整 commit SHA
        │    → 构建与验证 → 批准部署 → VPS 运行指定镜像
        └→ 负责人单向同步到现有 GitHub 私有仓库
             → 沿用受控 public-export → GitHub aios-public
```

CNB 是团队唯一协作主仓库；Issue、负责人、PR 与审查只在这里维护。GitHub 私有仓库保留分发/镜像作用，不接受另一条独立开发主线。公开仓库继续走已有脱敏导出，不接收私有 Git 历史。镜像故障应可见，但不成为 CNB 开发和从 CNB 发布的前置依赖。

每位成员使用自己的账号和分支，例如 `feat/alice/42-asset-search`。用户已确认集成负责人是 `sixseven`；主分支只经 PR 由 sixseven 串行合并，任务契约的 integrator 写负责人 sixseven，平台权限绑定其实际 CNB username/ID；人名不冒充登录标识。姓名与角色记录见 [成员接入](member-onboarding.md)。普通开发者不需要 VPS 密码、平台管理员账号或部署凭据。选定一次发布不等于把发布权限交给所有能够 push 的人。

当前组织为 `bql_huayue`（百雀羚花悦），目标私有仓库 `bql_huayue/aios` 已创建，目前为空。历史 Gitea 的 `baiqueling/aios` 不再是团队入口。初期不用长期 develop 分支，短任务分支配合 main 即可。

## 2026-10-15 的现场依据

- 本机 AIOS 的 `origin` 仍为 GitHub，另有只读审计使用的 `vps` remote；当前有多个任务的未提交内容，必须保留。
- GitHub API 确认 `bigKING67/aios` 为 PRIVATE。仓库内已有 `public-export` 政策与 `aios-public` 发布链路，不能用全量镜像替代它。
- VPS AIOS 的 origin 仍指向 GitHub，工作树干净，health 正常。VPS Git HEAD 与运行容器的镜像标签不同；这两种事实不能互相替代，不据此单独判定部署异常。
- 现有 `scripts/ops/vps-up.sh` 依赖名为 origin 的 upstream，在 VPS 使用 Compose 构建镜像；已有 frontend manifest 与 API image/source proof 应保留。
- `.github/workflows/deploy-vps.yml` 手动触发，但内部显式从 GitHub fetch。仅修改 remote 不会消除这条旧发布来源。
- 现有 `vps-prepush-guard.sh`、Git 状态库、热修复回流及 Prefect 发布都采用原来的 MacBook/origin/VPS 合同，需要共同审查。

导入准备只读取干净临时 bare clone 的已发布 main，未复制本机 WIP；该快照没有 submodule 或 LFS 属性。历史扫描命中包含大量哈希、字段名和示例，但旧部署文档另有 Kimi/DeepSeek Key 格式的明文值，未验证失效。用户选择先保留空仓库；不能把删除当前文件当作清理 Git 历史，也不擅自改写历史或轮换生产凭据。

CNB 的 `main` 保护规则已通过登录页面保存并重新打开核对：需至少一位评审人批准、需管理员批准、存在的状态检查需通过、禁止创建/直推/强推/删除保护分支，负责人和管理员均无绕过项。未配置自动合并、NPC 审批或 CI 作业。规则页面说明修改只影响新 PR；目前尚无提交，首次导入需要由负责人针对批准 SHA 安排一次初始化，不得给成员长期开放保护分支创建/推送。

原 Gitea 的分支保护、隔离验证和恢复证据只适用于已停用的平台，不能移作 CNB 的完成证明。CNB 的保护规则保存、普通成员真实推送/审批/合并、CI 与跨宿主接手须分别验收；只有单一账号时无法证明独立审批和合并权限隔离。

TWC v0.1.3 已从独立安装产物验证当前 CNB 账号与私有仓库读取，doctor 正常；账号专用 Token 无私有仓库读取权限。两类凭据分开配置，未扩大仓库授权范围。真实仓库当前没有 Issue/PR/提交；此处测试的本地 Git 是未上传的合成夹具，不是 AIOS 代码验证。PR 设置已启用自动添加仓库管理员为评审人，并通过重新进入页面确认保存；处理人及双账号合并约束仍待真实 PR 验收。

2026-10-16 按 sixseven 的明确要求，将本人的两枚 TWC 只读凭据替换为永久有效令牌：仓库令牌仍仅限 `bql_huayue/aios`，身份令牌仍仅有 `account-profile:r`。新凭据通过打包产物的在线 doctor 与身份令牌私库访问拒绝验证；旧 7 天令牌已撤销，实际请求返回 `auth_required`。凭据只保存在 Mac 的仓库外受保护目录，不进入 Skill、资料包或项目配置。负责人角色本身没有 7 天期限。

## Docker 的版本应该怎样固定

Docker 运行构建产物。发布记录至少关联：CNB 仓库与完整源码 SHA、检查证据、目标架构、各服务镜像 ID/registry digest、非敏感配置版本、迁移状态、部署者、时间与前一版恢复点。镜像中的 revision 标签帮助追踪，但必须同时检查实际镜像身份。

Git `main` 是会前进的分支，`:latest` 和普通镜像 tag 也可被移动。选定 SHA 后，后续 fetch/pull 不能悄悄把部署目标换成更新提交。若流程要求部署当时最新 main，发现基线前进时应停止并重新验证，不能复用旧证据发布新提交。

本机 Docker image ID 与 registry manifest digest 是不同对象；本地构建时记录实际 image ID，有 registry 时按目标平台和 digest 部署。固定源码 SHA 不保证两次独立构建字节相同，因此后续推荐构建一次、验证同一产物、部署同一 digest。[Docker digest 文档](https://docs.docker.com/dhi/explore/security-concepts/digests/)

AIOS 还有 ETL、Prefect 和数据库迁移，不能只记 web/API 两个镜像就宣布整套产品版本一致。每次发布明确受影响组件；共享卷、数据库与生产环境配置保持独立。数据库迁移的回退另定策略，换回旧镜像不等于回滚数据库。

## 分两步切换

第一步复用现有部署方式，降低迁移范围：

1. 完成公司对 CNB SaaS 的使用认可、个人账号和恢复渠道、组织负责人权限。代码镜像不包含平台的 Issue、PR、审批和账号；按公司需要配置元数据导出和代码异地备份。
2. 确定公司组织和成员权限；在干净的临时 checkout 中清点批准迁移的分支/标签、LFS、submodule 和历史敏感内容。导入固定 Git 对象，不打包当前脏工作区，不批量提交 WIP。
3. 暂时保留原 origin，新增明确的 CNB 目标完成克隆、权限、分支/标签 SHA 对照。不要立即对正在开发的所有 clone 批量改 remote。
4. 验证普通成员可推任务分支、不可直接推 main/强推、作者不能自批；配置审批与过期审批处理、受限合并身份、最新基线以及真实存在的必需检查。尚未接 CI 时明确作为人工试点，不填虚假成功状态。[CNB 代码仓库设置](https://cloud.tencent.com/document/product/1785/116271)
5. 在 AIOS 范围内更新 AGENTS/运行手册、push guard、Git sync、部署与 Prefect/热修复调用方及测试。日常提交/PR 不依赖生产 VPS 可用，也不给实习生复制 VPS 认证；生产协调检查移到获授权的集成/发布路径。最终 `origin` 指向 CNB，原 GitHub 保存为 `github`。
6. 关闭旧 GitHub 独立生产部署入口，或将其改为只接收并验证同一 CNB 发布记录；不保留可绕过 CNB 选择任意 GitHub 分支上线的通道。公开导出工作流保持独立。
7. 首次生产切换先部署与现有运行版本对应的已验证代码，固定完整 SHA、构建/核验镜像和组件版本，执行健康检查及回滚演练；再接受下一次功能发布。切换本身仍需明确部署授权。

第二步再改为产物发布：隔离 Linux builder/Runner 拉取 CNB 代码，执行检查并构建目标平台镜像，保存到批准的 registry；生产 VPS 只拉指定 digest 并执行部署/健康检查。保存前一版可用镜像与部署清单，调整现有镜像清理策略，避免回滚产物刚被删除。

当前 CNB 构建与制品发布尚未接入 AIOS。启用构建、私有镜像和生产拉取身份是独立实施项；不要让不受信任的 PR job 获得生产 Docker socket、数据库/备份或部署身份。第一步仅从 CNB 获取已批准代码后受控构建，不在共享生产 VPS 上增加任意 PR 的自动执行。

## GitHub 怎么保留

开始时由负责人从干净镜像 checkout 正常 fast-forward 推送已批准的 main 和明确选中的标签。GitHub 出现额外提交、分叉或标签冲突时停止，先带回 CNB 审查，不强推覆盖。无需让每个成员配置两个推送目标。

暂不启用双向镜像或强制覆盖。后续需要自动化时，使用受限身份与明确分支/标签清单，并验证失败、冲突和告警。

私有 GitHub 镜像可以继续触发原有的 public-export 审查与导出。公开 `aios-public` 只有经过策略允许、扫描和构建验收的投影；其 commit SHA 与私有源码不同，按 `PUBLIC_SOURCE.json` 的 source SHA 追踪，不要求两者 SHA 相等。不得把私有仓库直接 `push --mirror` 到公开仓库。

## TWC 在 AIOS 中的位置

保留 AIOS 已有 Trellis 流程控制权，先采用 TWC 的工具模式：读取 CNB 任务和既有规格、全仓工作区检查、版本绑定验证、交接草稿。Trellis 本地执行阶段不另建一套可独立修改的共享负责人/完成状态。三种宿主使用同一批准产物，每位成员从自己的 clone 接手。

验收需要一条真实链路：成员 A 推任务分支 → 成员 B 只凭平台资料接手 → PR 审查与最新基线验证 → 负责人合并 → 选择 SHA 发布 → 运行镜像可追溯 → GitHub 单向同步仍通过原公开导出门禁。方案文件、成功 push 或 main 合并各自都不等于该链路已验收。
