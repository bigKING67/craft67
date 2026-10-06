# 本地测试与资料存储

研究报告、来源 PDF/音频、case、manifest 和验收回执是资料；venv、依赖缓存和
临时渲染文件是执行环境。不要将整个 `local/` 或某次验收工作区作为缓存删除。

## 新验收任务使用临时环境

在仓库根目录运行，输出目录必须尚不存在：

```bash
python3 scripts/test_environment.py --runtime report \
  --output-dir local/acceptance/report-storage-check -- \
  '{python}' scripts/report_smoke.py
```

`report` 根据 `requirements-report.txt` 创建临时 venv 并安装依赖；`data` 使用
`requirements-yfinance.txt`。安装会联网，版本范围沿用现有 requirements，不声称
锁定版本的完全复现。`empty` 只创建 venv；默认 `none` 使用当前解释器，不安装依赖。
日常反复开发继续复用已有用户专用环境，无须每次新建或下载。

被运行的命令通过 `MONEY_CRAFT_TEST_OUTPUT` 或参数中的 `{output}` 获取永久输出目录，
通过 `{python}` 使用选定解释器。需要留下的报告/来源/结果必须写到该输出目录。
包装器不自动复制研究资料，也不是文件系统沙箱，不能阻止命令主动写其他位置。

包装器将 `MONEY_CRAFT_DATA_HOME`、`MONEY_CRAFT_CACHE_HOME`、pip 缓存和 `TMPDIR`
指向本次系统临时目录。成功、非零退出、超时、SIGINT/SIGTERM 都会先停止命令的
进程组，再清理临时目录。默认总时限 900 秒，包含安装，可用 `--timeout` 调整。
不允许任务用 daemon/新会话脱离受管理进程组。SIGKILL、断电、宿主崩溃无法保证收尾；
残留需先核对运行情况，不能按前缀批量删除。目前支持 macOS/Linux。

输出目录保留 `test-environment-receipt.json`，只记录退出状态、环境清理结果等，
不记录参数、环境变量或原始日志。`COMMAND_SUCCEEDED` 仅代表进程成功，
不表示研究或验收语义通过。stdout/stderr 继续由调用方/CI 管理。

报告 CI 已使用此入口，测试断言与 report smoke 保持不变。其他已有 smoke 使用
`TemporaryDirectory`，不再重复增加清理层。手工验收需使用此入口才有这些保证；
已有用户 venv、已安装 Skill 和历史研究归档不受影响。

## 只读盘点与历史保留

```bash
python3 scripts/storage_check.py
```

统计 `local/` 各类别占用，不跟随目录符号链接；只将 `skill-evals/` 和
`acceptance/` 中名称日期超过 30 天的目录列为人工复核项。日期不代表最后使用时间，
复核项不等于可删除项。研究目录不参与按时间列候选。

- 正式报告、关键来源和正式验收结论继续保留。
- 旧调试资料先核对文档/验收引用，再确定精确清理范围。
- 运行中任务、`.keep`、未知目录应保留；此工具不提供历史自动删除。
- 不根据 `pyvenv.cfg` 扫描并删除存量环境；只清理由新入口本次创建的临时目录。
- 不增加后台服务，不改 Pi 的打包保留机制或 Server 编译缓存策略。

## 重复证据去重

同一份来源常在 `raw/`、宿主运行账本、`.research/<run>/evidence/` 和归档 revision 中各存一份。可用写时复制克隆（APFS `clonefile`、Linux `FICLONE`）合并字节相同的副本：

```bash
python3 skills/money-craft/scripts/money_craft.py storage dedupe --root local --json          # 只报告
python3 skills/money-craft/scripts/money_craft.py storage dedupe --root local --apply --json  # 执行
```

- 默认 dry-run；只处理 ≥64 KiB、SHA-256 相同、同一设备上的普通文件。克隆后每个路径保留独立 inode、原权限与 mtime，改写其中一份不影响其他副本。
- sealed revision（只读目录或只读文件）只作为克隆源，从不被替换；非当前用户所有或当前用户不可写的文件、已有硬链接的文件、`.working/` 和 `*.staging.*` 进行中目录也不替换。以 root 运行时同样按权限位判断，不因 root 可写而替换只读目录中的文件。
- 替换前复核源与目标未变化，并校验克隆内容的 SHA-256；不一致时记为 `changed_during_scan` 并保留原文件。文件系统不支持克隆时回执 `error_kinds` 含 `clone_unsupported` 并立即停止，不退回硬链接或复制。
- 克隆替换保留目标的权限与 mtime，但扩展属性/ACL 来自克隆源（macOS 会带上源文件的 `com.apple.quarantine` 等），属组按新建文件规则确定；证据文件不依赖这些属性时才适用。Linux `FICLONE` 常量仅适用于 x86/arm。
- 克隆共享的块对 `stat`/`du` 不可见：节省的空间用 `df` 观察；再次运行会把已克隆的副本重新计入 `duplicate_bytes`（上限值，重复执行无害）。
- 不要与正在运行的 `research`/`track` 命令并发执行。回执不含绝对路径和文件内容。
