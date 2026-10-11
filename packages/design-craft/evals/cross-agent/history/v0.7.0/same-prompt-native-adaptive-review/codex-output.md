## 1. 证据等级、平台与设计判断

- **证据等级：`L0 static`。** 只有题面与静态实现描述；没有源码、构建、截图、可访问性树或原生运行态。以下“已证实”均只表示由题面直接给出或可从题面数值推导，不代表独立复核。
- **手动路由：** `mobile / reference-only / page / adaptive`；实际使用的 Skill 为 `design-craft`。路由脚本因只读沙箱无法创建临时文件而未执行，不能把手动选择写成 planner 输出。
- **解析平台：`adaptive`，题面来源，高置信。** `PRODUCT.md` 明示双端原生商店交付；`DESIGN.md` 要求共享语义、允许平台原生分化。
- **Design read：** 面向单手现场操作员、同时供经理在平板多窗复核的任务完成界面；应冷静可信，以进度保全、低认知负担和平台原生可预期性为先。
- **文件变更：无。**

## 2. 分平台符合性结论

| 平台 | 静态结论 | 主要原因 |
|---|---|---|
| iOS / iPadOS | **BLOCK — 不符合发布级平台合同** | 非导航栈返回、丢失边缘返回；40pt 目标；禁用 Dynamic Type；固定 390 宽；非语义主题；无 Reduce Motion 路径。 |
| Android | **BLOCK — 不符合发布级平台合同** | 空 `BackHandler` 吞掉系统/预测性返回；40dp 目标；禁用字体缩放；固定手机壳与不变底栏；Cupertino 控件；无 Remove animations 路径。 |

这是基于给定实现事实的合规判断，不是对真实安装包行为的判定。

## 3. 五项发布阻断发现

1. **B1｜导航、返回与恢复。** 自定义 JS 返回取代 iOS 栈，Android Back 被空处理器消费。系统返回合同已被静态证据否定；预测动画、边缘手势及中断后草稿是否保留均未运行验证。对应 M1–M2。
2. **B2｜可访问输入与文字。** RN 的 40×40 逻辑单位低于 iOS 44×44pt 和 Android 48×48dp；固定 14 且禁用缩放直接违背发布要求。VoiceOver/TalkBack 语义、焦点顺序和外接键盘遍历仍无证据。对应 M3–M4、M8。
3. **B3｜自适应结构。** 390 固定画布只能把手机布局居中，并未服务 iPad Split View、Android multi-window、平板经理双栏复核或折叠姿态；可用宽度小于 390 时还存在裁切/溢出风险，实际表现未验证。不变底栏放大了这一问题。对应 M5。
4. **B4｜主题、控件与图标。** 两种外观都写死 `#777777` / `#FFFFFF`，绕开共享语义角色；同一 Cupertino switch 和 Web 图标集使 Android 明确失去原生控件语法。实际对比度、暗色和高对比显示尚未知。对应 M6。
5. **B5｜完成动效。** 500ms overshoot spring 与“冷静、可信”的任务确认不匹配，且没有 Reduce Motion / Remove animations 分支，已违反明确的发布要求。实际流畅度、可中断性和公告时机未知。对应 M7–M8。

## 4. 八个具体设计动作

1. **M1：恢复平台导航所有权。** iOS 使用真实 navigation stack、交互式边缘返回；Android 接入 system/predictive Back dispatcher，并移除无条件消费。
2. **M2：定义可恢复任务状态。** 以任务 ID 持久化草稿、步骤与待同步状态；返回、后台、进程重建和完成提交使用明确且可测试的状态机。若已有实现，补出相同验收证据。
3. **M3：扩大有效命中区。** 图标视觉尺寸可保持，但交互容器至少为 iOS 44pt、Android 48dp，并检查相邻目标间距、单手触达与按下反馈。
4. **M4：恢复语义排版与缩放。** 共享内容角色，iOS 映射 Dynamic Type，Android 映射 Material type/`sp`；允许重排、多行和可滚动内容，不能靠截断主操作兜底。
5. **M5：改为窗口驱动布局。** compact 为单栏操作流；medium/expanded 为列表—详情或任务—证据双栏。iPad 按 size class/Split View 适配；Android 按 window size class、多窗和 fold posture 适配，同时让底栏转为合适的 sidebar/rail/drawer。
6. **M6：建立语义到原生的映射层。** 共享 surface/text/status/action token 名称；iOS 映射 system colors/materials、native switch、SF Symbols，Android 映射 Material color/elevation、Material switch、Material Symbols。
7. **M7：把完成反馈改为因果动效。** 默认使用短、克制、无弹跳的确认；iOS Reduce Motion 用短淡变或静态变化，Android Remove animations 用淡变或立即更新；仅在状态真正提交后反馈。
8. **M8：补齐交互状态合同。** 为按钮、开关、任务状态定义 label/role/value、disabled/loading/error/success、公告、焦点恢复、键盘/D-pad 顺序，并把两端辅助技术纳入发布门禁。

### Intentional parity matrix

| 关注面 | 保持共享 | iOS / iPadOS 必须适配 | Android 必须适配 |
|---|---|---|---|
| 任务与状态 | 领域模型、内容顺序、草稿/同步语义、分析事件 | scene/background 生命周期与栈恢复 | activity/process recreation 与返回状态 |
| 导航 | 目的地、层级、当前位置语义 | navigation stack、edge-back、iPad sidebar/split | predictive Back；compact bar → rail/drawer |
| 布局 | compact/medium/expanded 的内容优先级 | size class、Split View、键盘安全区 | window size class、multi-window、hinge/IME |
| 控件与图标 | 动作含义、标签、状态 | 原生控件、SF Symbols、iOS 菜单/表单习惯 | Material 控件/Symbols、Android 菜单/反馈 |
| 排版与无障碍 | 文本角色、朗读含义、遍历目标 | Dynamic Type、VoiceOver、Switch/键盘 | `sp`/字体缩放、TalkBack、D-pad/键盘 |
| 主题 | 语义 token 名称和状态含义 | system colors/materials/tint | Material roles、tonal elevation、可控的动态色 |
| 动效与反馈 | 完成含义、因果时点、非视觉状态 | iOS 转场、Reduce Motion、克制 haptic | Material 转场、Remove animations、Android feedback |

共享的是产品语义和结果，不是像素、控件外形或导航机制。

## 5. 已证实与未证实

**题面内已证实：** adaptive 目标、用户/任务/无障碍要求，以及列出的九项实现事实；由此可确定 40 小于两端平台下限、禁用缩放和缺少减弱动效分支与明确要求冲突，固定手机画布不满足结构性自适应。

**UNVERIFIED：** 真实源码与条件分支、依赖和原生工程；安全区/IME/旋转/RTL；渲染后的颜色对比与暗色外观；可访问性树、读屏公告、焦点和键盘遍历；草稿持久化与离线恢复；返回手势、预测动画、动效流畅度/中断、触觉；性能、OEM 差异及任何构建结果。

**视觉与原生验收状态：`INCOMPLETE`。** 没有截图可做视觉评审，也没有任一平台运行态。

## 6. 最小验证计划

1. **源码合同：** 读取实际 `PRODUCT.md`/`DESIGN.md`，定位 navigation、`BackHandler`、文字缩放、pressable hit area、主题 token、switch/icon 抽象、window-size 分支、任务草稿与生命周期所有权；添加针对返回、恢复和完成状态机的单元/集成测试。
2. **构建门禁：** 先发现并使用项目自有 typecheck/lint/test；再对实际 Xcode scheme 做 compile/test，对实际 Gradle app module 做 assemble/lint/test。因无源码，scheme、module 和精确命令目前均 **UNVERIFIED**，本次未运行。
3. **iOS Simulator：`unverified locally`。** 至少覆盖 iPhone compact 与 iPad Split View、多方向、明暗/高对比、最大支持 Dynamic Type、VoiceOver、外接键盘、Reduce Motion、边缘返回，以及编辑中断—恢复—完成。
4. **Android Emulator：`unverified locally`。** 覆盖手机、平板及折叠/多窗 profile，手势导航与 predictive Back、旋转/IME、字体缩放、TalkBack、键盘/D-pad、Remove animations，以及进程重建后的草稿恢复。
5. **真实设备：两端均无证据。** 发布前至少在代表性 iPhone/iPad 与 Android 手机/平板或折叠机复核单手触达、系统返回、后台/来电/进程终止恢复、读屏、触觉、60/120Hz 动效和 OEM 差异；保存设备/OS、场景和截图或录屏 artifact。