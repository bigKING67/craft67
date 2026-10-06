## 1. 证据等级、平台与设计读法

- **证据等级：`L0 static`**——只有产品上下文和实现描述；没有截图、源码、DOM/可访问性树或运行态。虽然上下文充分，但按 `design-craft` 分级，没有截图仍不升级为 L1。
- **Resolved platform：`adaptive`**——来源是题述的 `PRODUCT.md` 摘要和 React Native 双商店目标；在本题范围内置信度高，但实际 `PRODUCT.md` 文件、路径和 revision 未核验。
- **Style authority：**题述 `DESIGN.md` 要求共享语义角色，同时明确允许平台原生差异；因此“同一产品体验”不等于“同一像素、控件和导航”。
- **模式/Skill：**`critique`；实际选择并应用 `design-craft`；main serial，未启动子代理。
- **Route：**未取得有效 route receipt；只读 sandbox 阻止 planner 创建临时文件，因此 route 输出不作为证据。
- **Design read：**将其视为面向单手现场操作员和分屏平板经理的任务完成/复核界面，气质可信、冷静、原生，优化目标是快速完成、明确验证并在中断后无损恢复。

**一句话诊断：**当前实现把应当共享的“产品语义与状态”误做成了“跨平台像素和行为复制”，同时破坏系统导航、文字缩放、触控尺寸和运动偏好；按题述静态事实，两端都不能通过发布门禁。

## 2. 分平台 conformance verdict

| 平台 | 静态门禁结论 | 决定性原因 |
|---|---|---|
| **iOS / iPadOS** | **Block / 不符合** | 非原生导航栈和返回、丢失交互式边缘返回、`40x40` 小于 `44x44pt`、禁用 Dynamic Type、固定手机画布、无 Reduce Motion 路径。 |
| **Android** | **Block / 不符合，且导航风险更直接** | `BackHandler` 吞掉系统/预测性 Back、`40x40` 小于 `48x48dp`、禁用字体缩放、Cupertino 控件、平板导航不适配、无 Remove animations 路径。 |

这是**基于明确静态冲突作出的失败判定**，不是运行态验证；运行测试可能发现更多问题，但不会使这些直接违规自动消失。

## 3. 阻断发现（最多五项）

1. **B1—P0 导航/任务逃生：**自定义顶栏和 JavaScript 返回替换 iOS 导航栈；空 `BackHandler` 又吞掉 Android Back。用户可能无法按系统习惯退出、取消或返回，iOS 边缘手势和 Android predictive Back 均被破坏；修复见 **M1**。
2. **B2—P0 可访问性/控件：**`40x40` 布局边界低于 iOS `44pt`、Android `48dp`；题述没有非重叠 `hitSlop` 证据。固定 `fontSize: 14` 且关闭 scaling 直接违反 Dynamic Type/font scaling 发布要求；修复见 **M2–M3**。
3. **B3—P0 Adaptivity：**强制 `width: 390` 在宽平板浪费空间，在较窄 Split View/multi-window 中可能裁切；不变的底部导航表明没有 window-class 结构适配。问题不是“平板绝不能有 tab”，而是窗口变化时结构从不改变；修复见 **M4–M5**。
4. **B4—P1 原生控件/主题可信度：**Android 使用 Cupertino switch，两端共用 web icon；组件内复用 `#777777`、`#FFFFFF` 绕开语义主题角色。平台熟悉度、暗色/高对比主题及实际对比度均无法签核；具体颜色对比失败尚不能由题述独立证明；修复见 **M6–M7**。
5. **B5—P0 Motion accessibility：**完成态固定为 `500ms` overshooting spring，既不符合“冷静、快速”的高频操作气质，也没有 iOS Reduce Motion 或 Android Remove animations 分支，直接违反发布要求；修复见 **M8**。

另外，**中断后进度是否恢复完全未验证**。这是发布证据缺口，而不是可由当前描述证明的既存缺陷。

## 4. 八个具体设计动作

1. **M1 原生化导航：**恢复平台导航容器；iOS 使用保留 interactive-pop 的 native stack，Android 委托系统 Back dispatcher/predictive Back。删除吞事件的空 handler；返回、取消和恢复草稿使用同一明确状态合同。
2. **M2 建立可访问操作控件：**有效触控区至少 iOS `44x44pt`、Android `48x48dp`，Android 通常保留约 `8dp` 间隔；图标视觉尺寸可更小。统一补齐 label、role、value/state、disabled/loading、焦点顺序及外接键盘/D-pad 路径。
3. **M3 恢复可缩放排版：**启用 `allowFontScaling`；iOS 映射 Dynamic Type text styles，Android 使用 Material type roles/`sp`。避免任意缩放上限，并让标签换行、内容重排、主要动作始终可达。
4. **M4 重构窗口响应布局：**移除固定 `390`；依据实时 window metrics、size class 和 fold posture 适配。compact 为单栏任务流，expanded 为任务列表/详情或验证信息的双栏结构；处理旋转、Split View、multi-window、IME 和 hinge。
5. **M5 让导航形态随空间变化：**共享目的地、选中状态和深链语义；iPhone/compact iOS 可用 tab，iPad expanded 使用 sidebar/split；Android compact 使用 navigation bar，medium/expanded 评估 rail 或 drawer。窗口改变时不丢任务上下文。
6. **M6 平台化控件与图标：**在共享语义 API 后分别实现 iOS 原生 switch、picker、sheet、alert、SF Symbols，以及 Android Material switch、sheet/dialog、Material Symbols；不要靠同一视觉外壳模拟两套系统。
7. **M7 修复主题层：**把字面颜色集中映射为 `surface/text/border/state` 等稳定语义角色，再分别绑定 iOS semantic colors/materials 与 Android Material color roles/tonal elevation；逐主题测量正常、暗色和高对比状态，而不是简单反色。
8. **M8 解耦状态、持久化与动画：**任务状态先原子提交/缓存并可恢复，再发出视觉、触觉和读屏反馈；正常模式采用平台一致的短促、无夸张 overshoot 反馈，Reduce Motion 使用短 cross-fade，Remove animations 使用即时状态切换。不得等动画结束才保存或宣布完成。

## 5. Intentional parity matrix

| 领域 | 必须共享 | iOS / iPadOS 必须适配 | Android 必须适配 |
|---|---|---|---|
| 产品与状态 | 任务模型、校验规则、草稿/完成状态、离线恢复、analytics 语义 | iOS lifecycle 和 restoration 集成 | Android lifecycle、process-death 和 saved-state 集成 |
| 导航 | 目的地、层级含义、选中状态、深链结果 | Native stack、tab/sidebar、interactive Back | System/predictive Back、bar→rail/drawer |
| 布局 | 内容优先级、任务与验证信息关系 | Size classes、Split View、iPad pane/sidebar | Window size classes、multi-window、fold/hinge |
| 控件与图标 | 操作意图、标签、状态和业务结果 | iOS controls、SF Symbols、sheets/alerts | Material controls、Material Symbols、bottom sheets/dialogs |
| 色彩与材质 | `surface/text/border/status` 等语义 token 名称 | Semantic colors、materials、Increase Contrast | Material color roles、tonal elevation、适当的 Dynamic Color/fallback |
| 排版与辅助技术 | 层级、阅读顺序、可访问结果 | Dynamic Type、VoiceOver、Full Keyboard Access | `sp`/font scaling、TalkBack、键盘/D-pad focus |
| Motion/反馈 | 因果状态、完成含义、持久化时点、减少运动结果 | Reduce Motion、原生 transition/haptics | Remove animations、Material motion/snackbar |

## 6. 已验证与未验证

**仅在 L0 范围内由题述建立、未被独立源码核验：**

- `adaptive` 产品意图，以及 `DESIGN.md` 允许平台原生分化。
- 固定 `390` 宽度、自定义返回、吞 Android Back、`40x40` pressable、关闭字体缩放、字面颜色、共用 switch/icon/tab、`500ms` spring 且没有减少运动分支。
- 上述事实若与真实源码一致，足以阻止两端发布 conformance 通过。

**未验证：**

- 实际 `PRODUCT.md`、`DESIGN.md`、Git commit、完整组件树，以及是否存在题述未提及的补偿分支。
- 实际触控边界/`hitSlop`、颜色使用角色与对比度、安全区/insets、旋转、分屏、多窗口、foldable 和键盘/IME 行为。
- VoiceOver/TalkBack 语义、读序、完成公告；Dynamic Type/font scaling 重排；外接键盘焦点遍历。
- 原生返回手感、预测性动画、帧率、触觉、OEM 差异、任务持久化及 background/process-death 恢复。
- **`iOS Simulator: unverified locally`；`Android Emulator: unverified locally`。**
- **iPhone/iPad 和 Android phone/tablet/foldable 的 real-device evidence：全部缺失。**
- 无截图、视频、accessibility tree、构建回执或运行 artifact；本次无文件修改。

## 7. 最小 source / build / runtime 验证计划

1. **Source：**锁定 commit，读取实际 scoped `AGENTS.md`、`PRODUCT.md`、`DESIGN.md` 和 package scripts；定向搜索 `width: 390`、`BackHandler`、`allowFontScaling`、字面颜色、switch/icon、tab、spring、Reduce Motion、window metrics、`hitSlop`、持久化与 app lifecycle。运行 `design_craft_platform_scan.py --platform adaptive`，但只把结果当静态信号。
2. **静态测试：**使用仓库既有 package manager 执行 targeted type-check/lint/unit tests；补测平台 adapter、返回决策、窗口 class、主题映射、完成状态幂等和中断恢复。先发现脚本，不臆造 npm/pnpm/yarn 命令。
3. **Native build：**用 `xcodebuild -list` 发现 workspace/scheme 后执行项目既有 iOS build/test；Android 执行项目既有 Gradle `lint`、unit test 和 debug assemble。编译通过只能证明 build，不等于 Simulator/Emulator 行为通过。
4. **iOS Simulator（当前缺失）：**至少 iPhone 与 iPad；compact/expanded、旋转和可用的 Split View 宽度；验证边缘返回、最大 Dynamic Type、VoiceOver、Reduce Motion、暗色/高对比、外接键盘以及 background/terminate/relaunch 恢复。
5. **Android Emulator（当前缺失）：**覆盖受支持的最低/当前 API，以及 phone/tablet/foldable；验证 gesture navigation、predictive Back、multi-window、TalkBack、最大目标 font scale、Remove animations、键盘/D-pad、IME/hinge 和 process-death 恢复。
6. **真实设备（当前缺失）：**至少代表性 iPhone+iPad、Android phone+large-screen；验证单手可达性、真实系统手势、触觉、OEM/insets、分屏/多窗口、中断恢复及负载下性能。没有这些证据，不宣称 native feel、haptics 或最终商店发布就绪。

**最小放行条件：**两端 build 通过；所有 B1–B5 有源码和运行态证据；触控区、字体缩放、Back、窗口适配、运动偏好、键盘/读屏和中断恢复均通过；artifact 记录 commit、设备/OS、测试状态、截图或视频及日志。

