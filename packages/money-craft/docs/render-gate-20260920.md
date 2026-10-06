# 渲染完成与封存门禁修复

2026-09-20。修复完整宿主测试中“阅读版检查失败，但render已完成并继续封存”的流程缺口。结果为 **PASS_BOUNDED_RENDER_GATE_REGRESSION**，不是将原完整E2E改判通过。[验收回执](../acceptance/render-gate-20260920.json)。

## 实现

新增宿主工具 `~/.codex/tools/investment_render_gate.py`。在render运行期间实际执行Kami的content schema、HTML内容覆盖、PDF markdown、占位符、视觉结构、字体、样式、密度及数学残留九项检查；每项单独捕获退出码和日志，错误不再被同一shell中的后续成功命令掩盖。每次使用新的输出目录，保留失败。

回执绑定run ID、render attempt、canonical Markdown、content IR、HTML、PDF、检查日志及视觉复核文件的SHA-256。视觉复核需有reviewer、status=PASS和实际PDF哈希；自动检查不代替人的页面检查。任意失败、缺项、不确定状态、非零退出码、错误日志或资产变更均阻断完成。

`investment_run.py complete --stage render` 现在必须提供 `--render-validation`。校验在修改账本之前执行；通过后，将回执和全部绑定文件写入完成事件的产物记录。非render阶段不能误用该参数。

`investment_archive_revision.py seal` 在准备封存及锁内修改前重新验证已完成render事件中的绑定，且比对工作档案的report.md、report-kami.html和report-kami.pdf。这防止用一个阅读版的通过回执封存另一个输出。旧sealed档案只读verify仍兼容；没有绑定的新封存请求被拒绝，不为旧账本补造通过证明。

这是防止遗漏、忽略失败和陈旧结果的流程校验，不是对有任意文件写入/代码执行权的恶意调用者的密码学证明。视觉评价质量及研究语义仍需实际审查。

## 使用合同

先完成实际PDF页面检查并写视觉记录，例如：

```json
{"status":"PASS","reviewer":"actual reviewer identity","pdf_sha256":"actual PDF SHA-256"}
```

随后在运行中的render阶段执行（路径按本次工作区设置，output-dir必须新建）：

```sh
python3 ~/.codex/tools/investment_render_gate.py \
  --run-dir RUN_DIR --markdown REPORT_MD --content CONTENT_JSON \
  --html REPORT_HTML --pdf REPORT_PDF --visual-review VISUAL_REVIEW_JSON \
  --kami-root KAMI_SKILL_ROOT --python RENDER_PYTHON --output-dir CHECK_ATTEMPT_DIR

python3 ~/.codex/tools/investment_run.py complete \
  --run-dir RUN_DIR --stage render \
  --render-validation CHECK_ATTEMPT_DIR/validation.json
```

只有第一条实际返回PASS，第二条才可成功。失败时保留检查目录，按现有fail/retry流程修复并重检；不得编辑失败日志或回执凑PASS。绑定输入和日志应保持不可变；修订输出后生成新检查尝试。

## 验证

11项单测通过：PASS完成并登记证据；缺回执；明确失败/不确定；缺检查；四类输入变更；非零退出码/错误日志；错误attempt和失效视觉绑定；档案输出不一致；完成后回执变更；实际collect子进程记录失败；真实seal入口在产物不一致时零持久修改。

既有investment_run、archive_revision、archive_sources三套shell回归通过。账本回归的render fixture升级为显式合成PASS回执，原有链、失败重试及完整性覆盖保留；合成fixture不充当真实Kami通过证据。旧失败案例sealed revision的只读verify-current仍ok=true。

上轮真实8页PDF及content IR执行九项检查，七项通过，content与markdown失败。complete明确返回1，错误为render validation is not PASS，run.json字节未变，阶段停留render，未启动archive。负例集成使用标明用途的视觉fixture以隔离自动门禁；不宣称本轮重新完成该PDF视觉验收。

原文件、diff、11项测试、三套回归、真实失败日志和零修改核对位于 `local/acceptance/20260920-render-gate/`。本轮没有修复旧PDF标点或HTML静态覆盖的不确定，也没有重跑完整公司研究E2E；接下来应单独解决这两项兼容问题，再用新门禁验收，不能用本轮门禁修复替代其通过结果。未改全局Skill安装、用户money档案或旧封存文件，未commit/push/发布。
