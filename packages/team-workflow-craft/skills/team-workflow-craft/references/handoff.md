# 接手续交

```sh
python3 <skill>/scripts/twc.py --project <repo> handoff --draft --online \
  --packet .team-workflow/local/packets/<run_id>.json \
  --evidence .team-workflow/local/evidence/<run_id>.json \
  --done "完成接口和错误分支" --next "负责人核对组合测试和审批"
```

生成 JSON 和 Markdown 草稿，含任务、分支、base/head、完成/未完成、证据、阻碍和下一步。有未完成工作用 `--remaining`，多个项可重复传；在线刷新 PR 加 `--online`。草稿和快照默认留在 ignored local，不自动评论、上传或提交。`--publish` 在 v0.1 明确报不支持且不发请求。

`not_ready`：缺契约、内容/策略漂移、验证未通过、未提交代码或仍有未完成工作。`unknown`：缺必要证据、平台未刷新或没有可核对交付 PR。`advisory_ready`：当前材料满足本地判断且已核对 PR base/head，仅建议进入人工集成审查，不证明审批、CI 完整或具有合并许可。

跨人交接前，由获授权的人把分支推到公司平台，并发布审核后的 Markdown 和去敏证据/规范链接；明确哪些本地引用已转换成平台可访问位置。不能把本机绝对路径、未推送提交或 ignored local JSON 当作对方可用的交付。上传平台后以平台 URL 交接，不同步全部会话或凭据。

接手者 clone/更新代码，核对实际 Skill 版本与锁、重新 prepare/inspect，阅读目标和剩余步骤。旧证据仅作历史来源；必要检查在自己的环境或受控 CI 重跑。不同 Agent 的加载证明独立记录。
