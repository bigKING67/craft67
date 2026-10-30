# 可选宿主状态栏

读取当前 Git 工作树的 `.team-workflow/config.toml`，显示 `Workflow: solo` 或 `Workflow: team`；`solo` 对应配置中的 `personal`。未配置显示“未配置”，无效配置显示“配置错误”，读取失败显示“不可用”。旧 v1 配置仍显示 team。它只说明项目模式，不证明 Skill 加载、验证通过、平台审批或授权。

适配器包含在安装产物里，但不会自动启用、改宿主设置或替换已有状态栏。需要 Python 3.11+、Git；Pi 继续使用宿主自己的 Node。路径中的 `<skill>` 必须换成**实际安装副本**，不要指向开发源码。

先在目标项目验证独立输出：

```sh
python3 -B <skill>/scripts/workflow_status.py --project <repo>
```

子目录自动定位实际 Git 根，linked worktree 读取自己的配置；另一个嵌套 Git 项目不会继承外层模式。读取不联网、不执行 checks、不写任务或缓存，也不运行完整 doctor。修改模式仍走 [开发模式](development-modes.md) 的预览与授权流程。

## Claude Code

官方 [statusline 接口](https://code.claude.com/docs/en/statusline) 把当前工作区 JSON 送入命令 stdin。示例配置片段如下；仅在用户要求启用且没有现有 statusLine 时，把该字段合入选定的项目或用户设置，保留其他字段：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 -B '/absolute/path/to/skill/scripts/workflow_status.py' --claude"
  }
}
```

命令中的路径按实际 shell 正确引用；上例是 POSIX shell，Windows 按对应 shell 调整。已有状态栏时，在原渲染脚本中将同一份 stdin JSON 传给该命令，再把输出追加为一个片段；不能直接覆盖现有配置。不要让两个读取操作争用已经消费完的 stdin。

脚本优先使用 `workspace.current_dir`，兼容 `cwd`。坏 JSON 或缺失目录不会误用启动目录。刷新由 Claude Code 的状态栏生命周期控制，不额外设置轮询。独立 stdin 测试证明接口兼容；最终显示需在目标宿主会话检查。

## Pi

面向 Pi 1.4+，使用官方 [扩展接口](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) 的 `ctx.ui.setStatus` 增加一个独立状态项，**不替换 footer**。临时试用：

```sh
pi -e <skill>/assets/adapters/pi-status.ts
```

确认要长期启用后，将该文件的绝对路径追加到目标项目 `.pi/settings.json` 的 `extensions` 数组，保留原数组与其他配置。不要把适配器单独复制到另一个目录：它按自身位置寻找同一安装副本里的 Python 脚本。若 `python3` 不是 3.11+，可用 `WORKFLOW_CRAFT_PYTHON` 指定解释器可执行文件路径，不能包含 shell 命令或额外参数。

会话开始、切换及 Agent 一轮工作结束时刷新；外部手动编辑配置将在下一次这些事件发生时反映。退出时仅清除自己的 `workflow-craft` 状态项，保留其他扩展状态；后台旧结果不能覆盖新的会话状态。无 UI 时跳过显示，不向模型消息或系统提示词注入内容。

## Codex

当前不提供自定义状态栏脚本适配。使用 `mode`/`resume` 的项目模式信息，在接续开场简短说明即可；不向已有 `tui.status_line` 写入未经支持的自定义字段。宿主支持改变后再评估独立适配，不影响共同工作流。
