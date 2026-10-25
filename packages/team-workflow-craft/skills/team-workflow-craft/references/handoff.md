# 接手续交

```sh
python3 <skill>/scripts/twc.py --project <repo> handoff --draft --online \
  --done "完成接口和错误分支" --next "负责人核对组合测试和审批"
git add -- .team-workflow/tasks/pr-8
git commit -m "twc: hand off pr-8" -- .team-workflow/tasks/pr-8
```

`handoff` 在任务目录写入 `handoff.json` 和 `handoff.md`。内容包括：任务和契约版本、分支、base/head、代码内容哈希、完成/剩余/下一步、每条 AC 和每项检查的状态及执行者、阻碍和未知项。检查状态中 `stale` 表示有过记录但对应的是旧代码、旧契约或旧策略，需要重跑；`missing` 表示从未记录；`not_run` 表示最新尝试未能启动，不可沿用旧通过。目录里只保留最新一份交接，历史由 Git 保存。

- remaining：手写的未完成项，加上所有未 verified 的 AC（自动推导，不靠自报）。
- 输入里的 TODO、TBD、待补充、`...` 等占位文本会被拒绝。
- `--online` 重新读取 PR，核对平台上的 head/base。
- `--publish` 明确不支持，不发任何请求。

## 状态含义

| readiness | 条件 |
| --- | --- |
| `not_ready` | 缺契约、契约或接口漂移、验证失败、证据全部过期、AC 未验证、有未提交代码、基线未集成，或仍有未完成工作 |
| `unknown` | 缺必要证据、有需人工判断的 AC、平台未刷新，或没有可核对的交付 PR |
| `advisory_ready` | 本地材料齐全且 PR base/head 一致；只表示可以进入人工集成审查，不代表审批、CI 完整或合并许可 |

## 交给下一个人

提交任务目录并推送任务分支，就完成了交接材料的传递；需要平台可见时，由获授权的人把 `handoff.md` 发到 PR。本地绝对路径、未推送的提交和 `.team-workflow/local/` 都不能当作对方可用的交付。

接手者 fetch 后切到该分支，先 `resume`：它读取已提交的任务目录，报告哪些证据对当前代码仍然有效、上次交接的下一步、交接之后又有哪些提交。然后用自己的身份 `prepare`，按需重跑 `verify`。旧证据保留原执行者；不同 Agent 的加载证明分别记录。
