# Reverse Craft

Reverse Craft 是面向逆向工程、CTI/OSINT、CTF 和授权安全研究的证据优先 Agent Skill。
它把 43 条专业路线统一为一个可发现的 `$reverse-craft`，并提供确定性路由、
案例状态机、证据链、Finding/Path 追溯、可复现报告、安全工具引导和真实宿主验收。

## 核心能力

- **一个入口，43 条路线**：二进制、移动端、Web/API、云与身份、取证与恶意样本、
  CTI/公开来源 OSINT、硬件/无线、攻防研究、报告/证据治理。
- **Evidence-first**：Evidence -> Finding -> Path -> Report；所有关键结论可回溯。
- **原件保护**：证据默认复制到 case artifact store，记录 SHA-256、size、时间和来源。
- **可恢复写入**：原子 JSON 写入、带 snapshot 对账与尾锚的 hash-chain 事件流、锁、seal receipt。
- **安全引导**：`doctor` 与 `setup plan` 只读；`setup apply` 需要固定计划哈希和显式确认。
- **browser67 协作**：JS 逆向复用 browser67 的 `js-reverse` 运行时，不创建第二套
  browser/session truth。
- **Agent 原生**：Codex 与 Pi 都可以直接从仓库安装/加载，不依赖 npm 发布。

## 安装

### Codex

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/reverse-craft" ~/.agents/skills/reverse-craft
```

也可以把 `skills/reverse-craft` 复制到项目 `.agents/skills/` 或用户 Skill 根目录。

### Pi

```bash
pi install .
```

也可以在一次任务中直接指定：

```bash
pi --skill ./skills/reverse-craft
```

## CLI 快速开始

CLI 仅使用 Python 标准库；仓库内和安装后的 Skill 都可直接运行。

```bash
RC="python3 skills/reverse-craft/scripts/reverse_craft.py"

$RC doctor --json
$RC route --hint "分析 APK 的证书校验和 native so" --json
$RC route --hint "使用公开来源富化 IOC 并准备 CTI 交接" --json
$RC case init --title "sample-01" --scope "local CTF fixture"
$RC evidence add --case <case-id> --file ./sample.bin --kind binary
$RC finding add --case <case-id> --title "Parser trusts length field" \
  --severity high --evidence E-0001 --status confirmed
$RC path add --case <case-id> --title "Input to controlled write" --finding F-0001
$RC report render --case <case-id>
$RC case validate --case <case-id> --json
$RC case seal --case <case-id>
```

`REVERSE_CRAFT_HOME` 可覆盖默认运行根目录 `~/.reverse-craft`。案例数据不会默认写入源码树。

CLI 校验失败返回退出码 `1`；可预期的用户/数据错误以 `reverse-craft.error.v1` 写入 stderr 并返回
退出码 `2`；未预期异常只输出脱敏的 `reverse-craft.crash.v1`（异常类型，不含原始消息或 traceback）
并返回退出码 `3`。

## 工具安装计划

```bash
$RC setup plan --profile android --output /tmp/reverse-craft-plan.json
$RC setup apply --plan /tmp/reverse-craft-plan.json --sha256 <printed-sha256> --yes
```

计划文件固定平台、命令、目标和哈希。`apply` 拒绝未知命令、被修改的计划、过期计划和
缺少 `--yes` 的调用。工具安装仍应只在当前任务授权范围内执行。

## 验证

```bash
npm run check:all
npm run test:hosts          # 真实 Codex + Pi，可用时运行
npm run test:hosts:cti      # 真实 Codex + Pi 的 R44/CTI 发现与边界探针
npm run test:hosts:r0       # 真实 Codex + Pi 的 R0 停滞阈值与可行性重规划探针
python3 scripts/check_browser67_mcp.py --surface-only  # 只读 MCP surface + health
npm run check:browser67     # 完整 managed fixture/evidence/rebuild/finalize
```

R0 Host gate 对比两个停滞阈值前后的决策，并检查 R0 保持 primary、重规划前记录、可行性门和计划维度
变化；它不证明真实目标一定能继续推进，也不证明某个具体工具在目标环境中可用。

`--surface-only` 不创建、采用、清理或关闭 tab，也不写 evidence/rebuild artifacts。完整 browser67 gate
只操作自己创建的 localhost fixture，并以 scoped `finalize_task` 收口。基础门禁不把真实宿主或真实
browser67 结果冒充为已验证；三类证据单独报告。

## 项目状态

当前版本 `0.2.0`。npm package 仍保持私有；`v0.2.0` Git tag 是可复现 Skill 安装源，本次不创建
GitHub Release。

架构、验证层级和上游更新流程见 [`docs/architecture.md`](docs/architecture.md)、
[`docs/verification.md`](docs/verification.md) 与 [`docs/upstream-audit.md`](docs/upstream-audit.md)。
