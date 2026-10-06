# 旧 GitHub 仓库退役检查

删除前盘点时间：2026-10-06T09:47:05.630598+00:00。来源为 GitHub REST repos/releases/branches/tags/issues 接口，逐仓分页查询。该盘点时尚未删除远端内容；最终删除结果见文末。

本地源码快照已迁入 craft67；完整历史、远端分支、PR/Issue 与 Release 不等于已迁移。

| 旧仓库 | Release | 附件 | 分支 | 标签 | 开放 Issue | 开放 PR |
|---|---:|---:|---:|---:|---:|---:|
| [design-craft](https://github.com/bigKING67/design-craft) | 2 | 8 | 21 | 14 | 1 | 5 |
| [creative-craft](https://github.com/bigKING67/creative-craft) | 8 | 24 | 17 | 8 | 0 | 5 |
| [review-craft](https://github.com/bigKING67/review-craft) | 13 | 14 | 1 | 13 | 0 | 0 |
| [money-craft](https://github.com/bigKING67/money-craft) | 0 | 0 | 1 | 0 | 0 | 0 |
| [whoami](https://github.com/bigKING67/whoami) | 0 | 0 | 1 | 0 | 0 | 0 |
| [browser67](https://github.com/bigKING67/browser67) | 9 | 3 | 1 | 10 | 0 | 0 |
| [commerce-growth-os](https://github.com/bigKING67/commerce-growth-os) | 1 | 3 | 4 | 1 | 0 | 3 |
| [3d-craft](https://github.com/bigKING67/3D-Craft) | 0 | 0 | 1 | 0 | 0 | 0 |
| [reverse-craft](https://github.com/bigKING67/reverse-craft) | 0 | 0 | 1 | 1 | 0 | 0 |
| [write-craft](https://github.com/bigKING67/write-craft) | 1 | 0 | 1 | 1 | 0 | 0 |

## 已完成的本地适配

- browser67 更新源改为 craft67；稳定标签隔离为 `browser67/vX.Y.Z`，兼容用户输入 `vX.Y.Z` 简写。其他包 Release、草稿、预发布不作为更新目标。
- 检出 annotated tag 并核对 peeled commit；从 `packages/browser67` 检查 package/lock 并打包，安装前再次核对远端标签。并发锁、恢复回执、WS live 身份校验仍保留。
- browser67 README、手动打包说明及 npm 仓库元数据使用 monorepo 路径；Design、Creative、Review、Write 的 README 活跃安装入口改为 craft67 的包或 Skill 子目录。
- 本地 updater 合同回归不等于新 Release 安装或浏览器运行态验收。新仓库没有 browser67 Release 时明确失败，不使用旧仓库兜底。

## 删除前的迁移建议（后由用户决定直接删除）

1. 发布：为各包采用 `<package>/vX.Y.Z` 标签；先完成该包发布门禁，再对新 commit 创建 annotated tag 和 Release。browser67 需递增当前版本后发布，不能把旧源码的 Release 直接描述为新源码已验证。历史附件可以按原 SHA 保留为历史资产，但不能冒充新版本构建。
2. 历史：逐项决定保留远端分支/标签历史，或明确放弃；当前 monorepo 只含导入快照。尤其 Design、Creative 和 Commerce 的开放 PR 不能因整合自动视为已完成。
3. 外部消费者：旧版已安装 browser67 仍包含旧更新地址；需要过渡升级入口。已只读确认 `pi-67/packages/pi67-cli/src/lib/external-repos.mjs` 与 extension registry 仍引用旧 browser67/design-craft；`pi-67-desktop/eng/capabilities/capability-sources.lock.json` 仍绑定旧远端、旧 commit 及已删除的 `../browser67`、`../design-craft` sibling 路径。已获用户授权并完成这两个仓库的本地适配：Pi CLI 共用 craft67 检出、从子目录调用 runtime；Desktop 的三项一方来源通过 sourceDirectory 绑定已推送的 `502266ef08cde5972efd2948055882cd9e03c1c4`。适配已提交并推送：Pi CLI `b94da54e9cfb01f6a1bebeee24f8de122e974744`，Desktop `5aff465042e53f76415765082afcb0aa57d4e642`。保留用户 WIP；未发布或更新已安装客户端。
4. 文档及来源引用：其他包的 README、npm metadata、发布流程及历史证据中仍有旧地址。区分活跃安装/下载入口与历史来源、schema `$id`；历史证据和稳定 schema 标识不可批量改写。
5. GitHub 状态：附件、Release 说明、PR/Issue 及分支处理完成前，不删除旧仓库。可先在明确授权后将旧仓库标记迁移并归档；归档与删除是不同动作。

## 本轮本地验证

- browser67：包级离线 check 50 步通过；新增 namespaced release、分页、跨包排除和 monorepo 打包回归。
- Design、Creative、Write：对应包级检查通过。Review：安装地址合同同步后 release gate 通过（243 tests，1 skipped），精确安装包 E2E 通过。
- Pi CLI：真实本地 Git fixture 验证共享 clone/pull、dirty 阻断、来源不符拒绝与 legacy 目录保留；CLI 完整检查通过。
- Desktop：resolver/preparation/freshness/reachability 定向测试及 adapter 验证；三个锁定包已从实际 Git 对象解析并确认版本。源码静态检查通过；首次覆盖率阶段因共享临时目录被移除失败，独立目录完整覆盖率复验通过：963 test files passed / 9 skipped，6,456 tests passed / 24 skipped；Statements 84.35%、Branches 78.92%、Functions 86.98%、Lines 87.96%。
- 公开 GitHub API 实测确认 craft67 尚无 browser67 Release，更新器返回预期的明确缺少发布错误，不回退旧源。
- 未执行新 Release 发布/真实全局更新、Windows 或 packaged 宿主验收。

## 发布验收

在新 tag/Release 已发布、构建与版本门禁通过后，先运行 `browser67 update --check --tag browser67/vX.Y.Z --json`，核对仓库、tag object 与 peeled commit。再在明确授权的隔离安装环境验证真实打包、安装、恢复路径及 connected WS 扩展身份。不得用本地 fixture PASS 代替发布或宿主验收。

## 删除结论

2026-10-06：用户在获知 Release、附件、开放 PR/Issue 与旧客户端入口尚未迁移后，明确指示直接删除这 10 个旧仓库，不再迁移旧仓库内容。因此前述保留建议已被用户决定取代；删除执行与核验单独记录。当前 craft67 源码继续保留，旧下载/更新地址将失效；本决定不等于新 Release 或宿主更新已完成。

2026-10-06T10:25:14Z：上述 10 个旧仓库全部删除成功，逐仓 GitHub API 回读均返回 404。删除对象严格限于表内仓库；`craft67`、`pi-67`、`pi-67-desktop` 不在删除范围。逐仓执行回执保存于本地忽略目录 `.migration-local/remote-deletion-result.json`。
