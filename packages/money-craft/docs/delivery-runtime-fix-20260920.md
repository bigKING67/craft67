# 兼容归档与证据文案修复

2026-09-20，按用户继续修复的指令，对宿主兼容工具作局部修改，见[回执](../acceptance/delivery-runtime-fix-20260920.json)。文件位于宿主 `.codex/tools`，不是Money Craft候选包内容；未修改全局Python链接或Skill安装。

归档命令新增 `--kami-python`，计划回显选定解释器；正式写入前检查可执行文件及markdown/weasyprint依赖。保留venv调用路径，不能resolve到基础Python后丢失环境。默认路径仍兼容旧行为，不再等复制报告后才发现解释器不可用。

渲染器缺少结论元数据时，改用中性的“研究范围、证据状态与限制请见正文”，删除无依据的双源核验默认宣称。已有明确结论仍保留。不宣称此次已修好所有YAML、章节解析或字体规则问题。

两套既有shell回归及新增缺失解释器零写入、显式参数回显、中性回退与明确结论保留测试通过。使用Apple原Markdown与audit在独立working目录实际生成HTML/PDF和manifest，audit_verdict=PASS，Markdown逐字节不变。该操作为父代理隔离重放，不是原宿主自主结果，也没有完成来源提升、受保护离线验证、revision/current封存或完整视觉验收。没有写用户正式money档案、commit/push或发布。
