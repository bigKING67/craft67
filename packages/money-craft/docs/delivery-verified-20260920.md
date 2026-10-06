# 历史报告隔离交付链路验收

2026-09-20。以原Apple宿主报告和审计输入作父代理本地回放，完成格式兼容修复、PDF检查、来源归集、受保护离线验证及只读revision封存。结论为 **PASS_BOUNDED_PARENT_DELIVERY_REPLAY**，不覆盖原自主宿主端到端结果，也不是完整投资语义审稿。见[回执](../acceptance/delivery-verified-20260920.json)。

## 修复

宿主兼容工具 `investment_kami_render.py` 识别有闭合边界且schema为Money Craft报告的front matter，不再将机器元数据排进正文。未提供独立摘要、且无前言时省略空摘要页及其目录项；已有明确摘要保持。可识别的研究日期加入普通页页脚。源Markdown不变，PDF从12页缩为11页。

`investment_archive_sources.py` 同时接受旧的“主要数据来源”和Money Craft的“来源索引”，支持来源标识同一行URL及旧的下一行URL。重复ID仍拒绝。对应两套shell回归通过，新增解析、重复ID、空摘要和页脚日期回归。

上述变更共四个宿主工具/测试文件，未改变Money Craft核心门禁或全局Skill安装。前一轮解释器显式选择和中性封面回退仍有效。

## 完整回放结果

- format-existing路由，main_serial；研究数据截止2025-11-01，本次排版归档日期2026-09-20，保留事后捕获说明。
- 原核心status仍complete=true。报告逐字节不变；原条件情景和独立核验限制不变。
- PDF全页栅格检查，关键财务表、估值、风险、证伪和来源页放大检查；最终重渲染11页像素与已检版本一致，字体嵌入及日期检查通过。未执行浏览器响应式验收；classic-paper只用于隔离兼容回放，不代表Money项目设计验收。
- 7个source ID、7个URL从原响应离线导入，0失败；S11/S12仍同源，不声称独立双源。原始响应时间写入导入说明，未重新联网刷新。
- guarded verify-snapshot的ok=true；supervisor及snapshot audit hook均有回执，macOS Seatbelt实际限制网络、写入与子进程。
- 只读r0001、current指针、根索引、事务及verify-all全部通过。
- 运行账本completed；20条回执、产物哈希及路径迁移verify通过。

最终测试根：`local/acceptance/20260920-delivery-verified/`。正式用户money目录未写入，未commit/push/发布。

## 保留的失败及修正

`20260920-delivery-replay`误将历史截止日用作format-existing归档日，来源提升正确拒绝；新账本改用真实排版日，未修改原研究截止日。`20260920-delivery-replay-dated`暴露旧来源标题解析缺陷；修复后离线归集成功。其账本又因记录会被后续阶段改写的manifest而发生哈希不一致；最终回放对每个阶段保存不可变manifest快照，原失败回执未篡改。这些均为父代理回放问题，不改写原自主宿主记录。

下一步是候选包和已修复宿主工具下的自主验收，验证不需要父代理纠正命令、材料或账本也能完成；浏览器响应式及Money项目主题验收、完整投资语义覆盖仍需单列，不从本次局部通过外推。
