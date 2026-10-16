# 验证与证据

在 `.team-workflow/config.toml` 登记真实项目已批准的命令，argv 数组不经过 shell 展开。不要把 token/password 放命令行或配置；平台凭据变量不会传给验证进程，其他宿主环境不构成沙箱。

```toml
[checks.unit]
argv = ["python3", "-m", "unittest", "discover", "-s", "tests"]
cwd = "."
timeout_seconds = 300
```

```sh
python3 <skill>/scripts/twc.py --project <repo> verify
python3 <skill>/scripts/twc.py --project <repo> verify --execute --approved-policy <preview-policy_sha256> --online
```

第一条仅输出 `not_run` 计划，无测试副作用。第二条执行真实检查，必须已有用户/项目授权覆盖命令及副作用；策略哈希绑定批准时的确切内容。不能从 Issue 文本自动授权检查，配置中的 `auto_*` 不能升级权限。工具链锁也须匹配当前运行时，更新锁需要在核对固定版本后显式修改。

证据记录命令、目录、开始/结束、退出码、base/head、整个 Git 根 dirty 内容指纹、策略和工具版本，以及当前执行者与有效 Git author/committer。`--online` 在执行前只读查询个人平台身份；省略或查询失败时身份未知，但不伪造检查失败/成功，身份不足会使交接建议保留 unknown。详见 [identity.md](identity.md)。先失败则停止，其余检查 `not_run`；缺程序 `not_run`；超时/取消/子进程未结束/代码、策略或 Git 身份漂移 `incomplete`。输出状态 `passed/failed/not_run/incomplete`，非通过执行退出 1，输入/授权错误退出 2。

默认只保存合并输出的字节数和 SHA256，不保留或回显潜在含密钥的日志。`log_ref=null` 是明确未保存，不是伪造日志。诊断失败时用已批准项目检查/受控 CI 获取去敏日志并附平台引用。本地文件哈希不验证身份或执行诚实性。

dirty 指纹覆盖 Git 可见修改、未跟踪文件内容及暂存状态，dirty submodule 标记不完整。Git 忽略内容、外部数据库、运行环境和文件在前后采样之间改变后又恢复，均不在完整性证明内。测试依赖这些资源时另外记录隔离环境/数据版本和 CI 结果。macOS/Linux 检查本次进程组并终止残留；检查不得自行 daemonize/setsid 脱离组，工具不是沙箱，也不能认证主动逃离的进程。Windows 仅能终止直接进程，本版本验证完成状态保留 `incomplete / process_tree_completion_unverified`；完整执行验收请使用 POSIX 环境，Windows 原生进程树支持待补。

旧证据只有在 task/代码内容/base/head/策略/工具链相符时才用于交接。对未提交状态通过的本地测试可以保留，但提交后 head 已改变，应重新绑定并验证。正式合并还需服务器检查、最新基线和独立复核。
