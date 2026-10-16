# Gitea 与 AIOS 共用 VPS 的试点部署

> AIOS 试点状态更新（2026-10-15）：用户选择 CNB，本文对应的 VPS Gitea 已停用并移除；Mac 加密备份保留。以下是可选自托管方案与历史验收记录，不是当前运行入口。

这份伴随运维方案把 Gitea 部署为独立服务，不把服务器加入 TWC Skill 的运行时。本文件提供配置、验证与变更清单；真实 VPS、DNS、账号与备份写入按当次授权执行，部署结果以目标环境的独立验收为准。

## 推荐拓扑

```text
成员本地 Claude / Codex / Pi + TWC
               │ HTTPS + 私有仓库
       独立 Gitea 域名
               │
      现有 Traefik（80/443）
               │ traefik-public
       独立 team-gitea Compose
          server ── private data network ── db
          独立 data/config volumes          独立 postgres volume
```

首批只承担代码、Issue、PR、审查；Git 走 HTTPS，不新增 SSH 端口。Actions、Packages、LFS、邮件、迁移功能默认关闭，不在生产宿主运行待审查代码或 Runner。后续需要这些能力时分别启用和验证。

Gitea 1 GiB/1 CPU、PostgreSQL 512 MiB/0.5 CPU 是试点上限建议，不是官方最低需求或资源预留。共同宿主与代理网络仍是共同故障域，容器不等于虚拟机安全边界。AIOS 渲染高峰、同时 clone/gc 时须观察；不能用一次空闲采样证明容量 SLA。出现持续内存压力或构建需求时，先分离 Runner，再考虑迁走 Gitea。

## 已准备配置

- [compose.yaml](../examples/gitea/compose.yaml)：两个服务、独立数据库和卷，只有 Gitea 连接现有代理网络；数据库没有 host port，不复用 AIOS DB/账号。
- [deployment.env.example](../examples/gitea/deployment.env.example)：只有域名、网络名、resolver 和 secret 路径。
- [restore.override.yaml](../examples/gitea/restore.override.yaml)：恢复演练时移除代理标签与外部网络，只保留内部数据网络；需 Compose 2.24.4+。
- Gitea `28.1.0-rootless` 与 PostgreSQL `17-alpine` 已按 2026-10-15 官方 registry 返回的 OCI index digest 固定；不使用自动更新。实际运行版本/架构以容器验收为准。
- 关闭公开注册、要求登录、强制私有仓库；锁住安装页面。首个管理员通过受控本机 CLI 创建，避免公开安装向导被抢占。

官方 [rootless Docker 安装](https://docs.gitea.com/installation/install-with-docker-rootless/) 规定 `/var/lib/gitea` 与 `/etc/gitea` 的持久化边界；rootless 镜像不等于 Docker daemon 以 rootless 模式运行。`__FILE` secret 配置来自 [Gitea 配置文档](https://docs.gitea.com/administration/config-cheat-sheet/)。

## 生产变更清单

| 新增/使用 | 范围 |
| --- | --- |
| 主机配置 | `/opt/docker/compose/team-gitea/`：固定 compose 与非敏感 env |
| 密钥 | `/etc/team-gitea/secrets/`：仅主机保存，不入 Git、不回显 |
| 容器/卷/私有网络 | 仅 Compose 项目 `team-gitea` 创建的资源 |
| HTTPS | 独立域名 DNS；复用 `traefik-public`、`websecure`、`myresolver` |
| 备份 | 独立 `/var/backups/team-gitea/` 与批准的加密异机目的地 |
| 保护对象 | AIOS 代码/WIP/Compose、运行容器、数据库、Prefect/缓存 timer、其他服务和已有 DNS/路由 |

不需要重建 AIOS、重启 Traefik、更改宿主 SSH 或暴露 Gitea PostgreSQL。Docker provider 应发现新容器标签，实际证书/路由仍须回读验收。

## 执行顺序（获授权后）

1. 再次检查 VPS AIOS health、内存/负载、磁盘和目标资源不存在；如采样已过期或主机有部署/渲染高峰，先重新判断窗口。
2. 固定已审阅 compose 文件哈希与镜像 digest；复制至独立目标。生成数据库密码、SECRET_KEY、INTERNAL_TOKEN，使用独立随机值。secret 目录 root:root 0700，文件在该受保护目录内 0444 以供两个不同 UID 的容器只读挂载；不要把此模式用于可遍历的普通项目目录。
3. 从主机专用配置执行 `docker compose --project-name team-gitea --env-file deployment.env -f compose.yaml config --quiet`；检查只有两个预期服务和三个项目卷。不要打印包含实际 secret 值的 env 或完整 inspect。
4. 拉取固定 digest，启动独立项目，等待数据库及 Gitea health。先用容器内回环确认配置生效、安装锁、注册关闭与匿名受限，再创建管理员；密码/Token 不进 argv、shell history 或回执。
5. DNS 指向批准 VPS；现有证书 resolver 用 HTTP challenge，因此 DNS/代理策略须允许 challenge 到达。检查 TLS、HTTP→HTTPS、登录页、匿名 API/仓库访问拒绝。
6. 管理员设置 2FA、第二恢复管理员/恢复渠道，再建试点组织、仓库和最小权限成员。Git push/pull、Issue/PR、保护分支/审批逐项验收；TWC 用只读 token 跑 doctor/prepare。邮件关闭时依靠批准的账号恢复流程，不能宣称邮件重置可用。
7. 记录 AIOS health 前后对照与容器资源变化；完成一致性备份及隔离恢复，再允许正式公司代码进入。新的账号、策略、CI 和数据导入仍分别依据授权范围。

## 备份与恢复

备份必须包含 Gitea data/config、数据库、部署配置及恢复所需 secrets；存放在本机只防误操作，不防 VPS 丢失。异机目的地未确定时，备份/恢复验收保持未完成。

官方 [备份一致性说明](https://docs.gitea.com/administration/backup-and-restore/) 要求一致地捕获 DB、Git 仓库和文件。小团队初期采用短维护窗口：停止 Gitea 写入 → PostgreSQL 原生 `pg_dump -Fc` → 同窗口打包 data/config 与部署资料 → checksum/`pg_restore --list` → 重新启动 Gitea并检查。失败时恢复原服务可用性并报失败，不把半成品当成功备份。加密复制到批准的另一台机器或对象存储；不与 AIOS 备份目录、保留策略或 timer 共用。

首次恢复必须进入新命名空间/另一台机器，无生产域名、邮件、webhook 或自动任务。仅修改项目名或域名还不够：原配置的 Traefik 路由名固定，同机副本可能覆盖正式路由；恢复的数据库还可能携带 webhook。

同机演练必须叠加 `-f compose.yaml -f restore.override.yaml`，使用新的 `--project-name team-gitea-restore-<run>`、独立恢复配置/secret 目录及全新卷。启动前解析配置，确认 `traefik.enable=false`、没有其他代理标签、没有 host port、两个服务只连接该项目的 `internal: true` 数据网络、没有 external 网络，并核对所有卷名均不等于生产卷。该隔离阻止恢复的 webhook 访问外部网络；不要为方便访问而重连代理网络。

先通过 `docker compose exec -T server` 在容器内回环检查 health、API、权限和仓库读取。需要浏览器验收时，在另一台隔离机器上配置仅回环访问的入口和独立出站限制，另行审阅该变更。校验登录、成员权限、Issue/PR、仓库 clone 和附件后才算恢复完成。不要在生产卷上做恢复演练，也不要自行清理旧备份。

实际恢复时先 `compose up -d --wait --wait-timeout 120 db`，等待数据库完成初始化并稳定健康；初始化临时 PostgreSQL 的一次 `pg_isready` 成功不足以开始恢复。只启动 db 不会创建 server 的 data/config 卷，应先 `compose create server`，回读卷标签和新项目名，再解包到这两个新卷。数据库仅在新空库上执行 `pg_restore --exit-on-error --no-owner --no-acl`，不对已有数据盲目重试。数据库和文件恢复完成后才启动 server。

## 回滚

初次启动失败：只停止 `team-gitea` 的新容器，保留新卷、配置和诊断；不要 `down -v`。如已新增 DNS，只撤销本次记录；其他 DNS、AIOS 和 Traefik 配置不动。镜像升级涉及 DB schema 时不能直接换旧镜像；用升级前完整备份恢复到新空间后切换。

## 验收证据分层

Compose 静态解析、镜像 registry digest、隔离本机启动、实际 VPS 启动、DNS/TLS、身份/权限、备份恢复、TWC 与真实宿主加载分别记录。示例文件可运行不代表已经部署。真实公司环境的 Token 和私人路径不写入源码测试或文档。

2026-10-15 本机 OrbStack 隔离实测：固定镜像启动成功，Gitea API 报告 `28.1.0`；health 为 200，匿名身份/私有仓库访问及注册请求为 403，安装锁/关闭注册/登录限制/强制私有的实际配置均为 true；通过 API 请求创建公开仓库仍得到私有仓库。TWC 只读客户端成功读取实例版本、测试身份、仓库和 Issue。临时容器、网络、卷和 secrets 已清理。此项不覆盖 VPS、Traefik/TLS、Git push/pull、PR/review/status API、备份恢复或三宿主加载；这些仍待目标环境验收。常规包门禁仅解析 Compose，不启动 Docker 服务。

同日另经明确授权完成 Linux VPS 空实例部署：独立 Gitea/PostgreSQL 均健康，资源上限和私有配置生效，仓库数为 0；独立 DNS 记录、Let's Encrypt 证书、HTTPS 登录页/health、HTTP→HTTPS 跳转和匿名身份拒绝通过，真实 Chrome 登录页面可读。原有 18 个运行容器 ID 与部署前一致，AIOS health 正常。管理员首次登录改密、2FA/恢复渠道、异机备份恢复、正式仓库/成员/分支门禁、隔离 CI 与三宿主跨人协作仍未验收。空实例上线不等于公司工作流已完成试点。

后续同日完成管理员首次改密、私有组织和空仓库创建，以及 main 保护配置回读；TWC 通过正式 HTTPS 以只读 Token 读取版本、身份和仓库。两份一致快照分别覆盖空实例、改密后的账号与组织/空仓库/保护规则，使用 AES256 加密保存到获批准的另一台 Mac；传输、解密和四份内部文件的 SHA-256 对照通过。两次恢复均使用本机 OrbStack 新项目、新卷、无 host port 和仅内部网络，Gitea 28.1.0 与 PostgreSQL 17 恢复健康。第二次进一步验证管理员 API 身份、私有组织/仓库、main 保护规则、匿名访问拒绝；临时 Token 撤销后拒绝访问，临时容器/卷/网络已清理。

这验证了当前平台元数据的恢复，不覆盖密码交互登录、已导入 Git 对象、Issue/PR/附件、真实普通成员的 push/合并权限或灾难切换。用户选择暂缓代码导入：来源历史中发现模型服务 Key 格式的明文值，失效状态待确认。2FA、第二恢复渠道、长期自动异机备份、隔离 CI 和三宿主真实协作仍待完成。备份密钥独立保存在批准的 repo 外受保护目录，不写入回执或源码。
