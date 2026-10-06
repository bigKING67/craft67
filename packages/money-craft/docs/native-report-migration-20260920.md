# Money Craft 自有报告迁移（2026-09-20）

用户明确停止使用并授权卸载全局 Kami。新报告采用 Money Craft 自有 renderer，Design Craft 为设计基线，仓库 DESIGN.md 为视觉依据；研究 Markdown、计算、来源及证据状态不因排版而改变。

## 已实施

- 使用 Codex CLI 卸载 `kami@kami` 及专属 marketplace，清理专属插件缓存和旧 Python 虚拟环境。其他插件与历史研究档案保留。
- 新建独立 Money Craft report Python 环境，依赖由 `skills/money-craft/requirements-report.txt` 管理。
- 宿主路由改为 `report-full` / `report-summary`，主题 `editorial-ivory`，新入口 `investment_report_render.py` 调用 Money Craft 自有 renderer。summary 只呈现研究阶段提供的摘要，不自动删减原文。
- 宿主 archive 工具采用新入口和 `--report-python`；全局投资规则与 Money 项目 AGENTS 的强制 Kami 条款同步更新。内部 `report-kami.*` 暂留作旧快照格式兼容，不依赖 Kami。对外阅读样张使用 `report.html` / `report.pdf`。
- render-validation v2 使用自有 report verifier、实际视觉审查与文件哈希绑定；非零退出、valid=false、输入变化或审查过期仍阻断完成。v1 仅用于历史回执兼容。
- 打印首屏标题区从 54% 调整为 70%，字号从 28pt 调整为 24pt，修复 Apple 样张“历史”拆行。未改变屏幕主题。

## 验证边界与证据

证据根：`local/acceptance/20260920-native-report/`。

- 使用既有 Apple 历史研究，截止 2025-11-01；不刷新事实。canonical Markdown SHA-256 不变。
- HTML/PDF 164 个可见内容单元均保留；计算注释保留于 Markdown，不要求机器注释可见。报告 6 页、无未替换占位符、静态依赖检查为零；全部 PDF 字体嵌入。
- browser67 宽屏 1440×1000、窄屏 390×844 均无页面横向溢出；实际检查日间与夜间阅读、目录展开，以及最终六页 PDF。任务标签页关闭 1 个、验证关闭 1 个、残留 0、错误 0。
- render gate 12 项回归及 route/archive/run/revision/sources 测试通过；source validate 19 项通过。
- 首次回放把会变更的 manifest 注册为固定输出，账本复核失败，保留原失败证据；最终回放改用不可变阶段回执，证据位于 `final-e2e/`，不覆写失败账本。
- 此为主代理执行的历史资料交付回放；原始响应以本地导入方式复用，明确 post-hoc，不冒充新抓取、独立宿主自然语言验收或完整研究通过。

## 剩余限制

PDF 末页附录留白较多；没有完成全键盘可访问性审计。视觉回执为具名检查记录，不是对抗任意代码伪造的证明。旧内部文件名尚未做格式迁移；旧研究的证据缺口不因此消失。未覆盖全局安装的 Money Craft Skill，其既有差异保留；宿主新入口明确使用本项目源 renderer。没有 commit、push 或发布。
