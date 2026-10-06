# 宿主报告入口

用户已选择停止使用 Kami。新报告以本仓库 DESIGN.md 与 Design Craft 为设计依据，复用 [report-rendering.md](report-rendering.md) 的渲染合同，不再安装或调用 Kami 插件。宿主正式路由为 `report-full` / `report-summary`；摘要需由研究阶段提供，renderer 不自动删减全文。宿主 `investment_report_render.py` 调用本项目 renderer，`investment_archive_report.py` 使用 `--report-python` 指定独立运行时。旧档案内部 `report-kami.*` 仅为快照格式兼容；用户阅读副本仍为 `report.html` / `report.pdf`。研究证据是否完整与报告呈现是否通过必须分别报告。

仅当宿主已提供 `~/.codex/tools/investment_render_gate.py` 且使用正式投资运行账本时，在当前 `render` 阶段运行期间，先生成 HTML/PDF 并完成实际视觉检查，再生成 v2 回执：

```bash
python3 ~/.codex/tools/investment_render_gate.py \
  --run-dir <run-dir> --markdown <report.md> \
  --html <report.html> --pdf <report.pdf> \
  --visual-review <visual-review.json> \
  --skill-root "$MONEY_CRAFT_SKILL_DIR" --python "$REPORT_PYTHON" \
  --output-dir <new-validation-directory>
python3 ~/.codex/tools/investment_run.py complete \
  --run-dir <run-dir> --stage render \
  --render-validation <new-validation-directory>/validation.json
```

`visual-review.json` 至少包含 `status`、实际检查者 `reviewer` 和本次 PDF 的 `pdf_sha256`，仅在已检查实际文件且通过时填 `PASS`；自动生成文件、计划截图或其他版本的检查不能代替实际审查。失败或输入变化后使用新的验证目录。宿主 renderer 通过环境变量 `MONEY_CRAFT_SKILL_DIR` 选择当前固定的 Skill；冻结候选验收时必须传该目录，避免归档时切回其他源码。

阶段完成回执的 `--output` 应登记不会再改写的阶段结果 JSON；后续证据导入、封存仍会更新的工作态 `manifest.json` 不应作为不可变阶段输出。完成 seal 操作后仍需 complete 对应账本阶段，并执行 `investment_run.py verify --run-dir <run-dir> --artifacts` 和独立归档根的 `verify-all`。这些宿主要求不适用于仅生成阅读预览的任务。

`investment_archive_report.py --audit` 只接受 ai-berkshire 抽检结果数组，Money Craft 的 `audit report/financial` 回执不能替代，格式不兼容会在 archive 阶段失败。研究 finalize 后立即准备，不要等到 archive：

```bash
AB=~/Documents/sixseven/codeproject/ai-berkshire/tools/report_audit.py
python3 "$AB" extract --report <report.md> --seed <n> > report.audit.json   # 抽样数据点数组
# 逐项填写 fetched_value/fetched_source（必要时 fetched_value2/fetched_source2）
# 与 evidence_refs（source_id、相对证据路径、locator），数值取自本轮已采集原件
python3 "$AB" verdict --results report.audit.json --require-evidence-refs --output-json   # 必须 PASS
```

`extract` 的 stdout 在 JSON 数组前可能有说明文字，保存前只保留数组。

正式 archive 阶段应给 `investment_archive_report.py` 传入 `--render-validation <已完成render阶段的v2回执>`，收录刚才实际验证的 HTML/PDF 原始字节，不再重渲染。预览与默认归档可能使用不同的 audit/manifest 输入，省略此参数可能产生哈希不一致并被 seal 拒绝。回执的 run_id 必须与 `--run-id` 一致，源 Markdown 必须匹配；宿主仍在 seal 前验证完成回执与实际档案。没有此宿主工具时继续使用 Skill 自有 rendition 流程。
