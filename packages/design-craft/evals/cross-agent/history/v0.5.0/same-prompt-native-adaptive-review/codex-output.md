## 1. 证据等级、平台与设计解读

- **模式 / Skill**：`critique`；实际使用 `design-craft` 的产品语境、iOS、Android、adaptive、motion 与 validation 规则。
- **证据等级**：**L0 static / prose-only**。输入包含明确产品语境，但没有源码或截图，因此不能提升为 L1 contextual，更不能形成运行态结论。
- **Resolved platform**：`adaptive`。
  - 来源：提示中转述的 `PRODUCT.md: platform=adaptive`。
  - 置信度：对本次评审范围为高；但未读取真实 `PRODUCT.md`、原生 target 或商店构建配置，故未独立确认仓库交付形态。
- **设计 authority**：提示中转述的 `DESIGN.md` 要求共享语义角色，并明确允许原生导航、控件、图标、材质与动效；因此“同一产品”不要求“像素与组件完全相同”。
- **Design read**：把它读作一个面向现场操作员与复核经理的高可信任务工具，气质冷静、原生、可恢复，优先保障单手完成、快速核验和中断后无损续做。

**一句话诊断：** 当前实现把共享代码误当成共享界面，用固定手机画布、非原生导航、固定字体和同款控件牺牲了系统行为、无障碍与平板工作效率；**iOS 和 Android 均不具备发布级平台一致性。**

## 2. 分平台结论

| 平台 | Verdict | 决定性原因 |
|---|---|---|
| **iOS / iPadOS** | **Block / 不符合** | 自定义 JS 返回替代导航栈和边缘返回；`40x40` 小于 `44x44pt` 基准且无有效命中区扩展证据；禁用 Dynamic Type；iPad/Split View 仍是居中的 390 宽手机画布；未响应 Reduce Motion。 |
| **Android** | **Block / 不符合** | 空 `BackHandler` 吞掉系统 Back，破坏 predictive Back；`40x40` 小于 `48x48dp` 基准且无扩展证据；禁用字体缩放；Cupertino 控件和 Web 图标破坏 Material 语义；平板/多窗口无 adaptive navigation；未响应 Remove animations。 |

这不是“需要一些视觉润色”，而是导航、无障碍和窗口适配合同被破坏，属于发布阻断。

## 3. 优先发现：最多五项阻断

### P0-1 — 导航、返回与中断恢复

**静态证据：** 自定义 top bar 和 JS Back 替代 iOS navigation stack；空 `BackHandler` 消费 Android Back。

**影响：**
- iOS 用户失去可信的层级导航和左边缘返回手势。
- Android 系统 Back、手势 Back 与 predictive Back 被截断。
- 返回、后台切换或进程恢复时是否保存草稿完全没有证据，直接触及“不中断丢进度”的核心承诺。

**通过条件：** 两端恢复系统导航合同；仅在确有未保存且不可自动恢复的数据时拦截退出，并证明后台、进程终止和返回后的任务状态可恢复。

### P0-2 — 基础无障碍合同失败

**静态证据：** 所有主要操作为 `40x40`；正文固定 `fontSize: 14` 且禁用 font scaling。

**影响：**
- 视觉尺寸低于 iOS `44x44pt` 和 Android `48x48dp` 基准；没有 `hitSlop`、非重叠命中区或语义合并证据。
- Dynamic Type 与 Android font scaling 被明确关闭，而二者是发布要求。
- 放大字体后重排、焦点顺序、VoiceOver/TalkBack 朗读和外接键盘遍历均无可交付证据。

**通过条件：** 有效命中区达到平台基准；核心文本允许系统缩放并能重排；主要流程通过屏幕阅读器和键盘完整完成。

### P0-3 — 没有真正的 adaptive 结构

**静态证据：** React Native 屏幕固定 `width: 390` 并在平板居中；bottom tab 在手机、iPad 和 Android tablet 上保持不变。

**影响：**
- 操作员手机场景尚可被强行装入，但经理的 Split View / multi-window 复核场景没有利用可用空间。
- 固定宽度不能处理方向、窗口尺寸、IME、iPad size class、Android window class 或 fold posture。
- 不变的 bottom tab 单独未必错误，但与固定手机画布共同证明目前没有结构性适配。

**通过条件：** 由实际窗口宽度、size/window class、姿态和输入方式驱动单栏、双栏、sidebar、rail 或 drawer，而不是由设备型号驱动。

### P1-4 — 控件与主题同时失去平台可信度

**静态证据：** 两端共用 Cupertino-shaped switch 和 Web icon set；两种 appearance 都直接使用 `#777777`、`#FFFFFF`。

**影响：**
- Android 明显呈现为 iOS/Web 移植；iOS 上“长得像 UISwitch”也不能证明具备系统语义、状态、焦点和可访问性。
- 硬编码色值绕过 `DESIGN.md` 的语义色角色，无法可靠处理 dark mode、高对比度、disabled/pressed/focus/error 等状态。
- 因缺少实际前景、背景和状态组合，**不能声称已经测得对比度失败**；能确认的是 token 合同已被绕过且存在高风险。

**通过条件：** 共享语义 API，但分别渲染平台原生控件、图标与材质；所有颜色经语义 token 映射并覆盖明暗、高对比度及交互状态。

### P1-5 — 完成动效违反无障碍与产品气质

**静态证据：** 完成转换为 `500ms` overshoot spring，且没有 Reduce Motion / Remove animations 分支。

**影响：**
- 缺少系统动效设置响应本身就是发布要求失败。
- 500ms 弹性过冲与“冷静、可信、快速”的高频操作语境不匹配。
- 尚无证据表明状态提交是否错误地等待动画结束；若如此，中断或快速连操作还会产生一致性风险。

**通过条件：** 业务完成状态立即提交且不依赖动画 callback；默认反馈短促、无夸张过冲；Reduce Motion / Remove animations 下改为短 cross-fade 或即时切换。

## 4. 八项具体设计动作

1. **恢复原生导航合同**：采用能接入 iOS navigation stack 与 Android system/predictive Back 的导航实现；删除全局吞 Back 的空 handler，自定义顶部内容只做样式层而不接管系统语义。
2. **建立中断恢复模型**：按字段或步骤自动保存 task draft、当前步骤和必要附件状态；覆盖 background、进程被杀、返回、网络中断与重进，并向用户显示明确的“已保存/待同步/同步失败”状态。
3. **补齐交互无障碍**：iOS 有效目标至少 `44x44pt`，Android 至少 `48x48dp`；补 label、role/trait、value/state、disabled/loading 语义、完成公告、逻辑焦点顺序及外接键盘焦点环。
4. **改为语义排版**：使用 iOS Dynamic Type text styles 与 Android Material type roles/`sp`；允许系统字体缩放，核心内容不设阻断性上限，并让 action、表单和错误信息在大字号下换行重排。
5. **落实语义主题**：把 `#777777`、`#FFFFFF` 替换成 `textSecondary`、`surface`、`onSurface`、`divider` 等共享角色，再分别映射到 iOS semantic colors/materials 与 Android Material color scheme。
6. **拆分平台呈现层**：共享 switch 的 value、disabled、validation 和 analytics 语义；iOS 渲染系统 switch 与合适的 SF Symbols，Android 渲染 Material switch 与 Material Symbols；品牌/领域专属图标才跨平台共享。
7. **用窗口能力重构布局**：compact 保持单栏单手流；iPad expanded/Split View 使用 sidebar 或 list-detail；Android medium/expanded 使用 navigation rail/drawer 与 list-detail；同时处理 safe area、system bars、IME、hinge 和 resize。
8. **重写完成反馈**：先原子提交状态，再给约 `120–200ms` 的 restrained feedback；避免 500ms overshoot。iOS Reduce Motion 与 Android Remove animations 下使用即时状态更新或短淡入淡出，且不延迟朗读、触觉或导航。

## 5. Intentional parity matrix

| 能力 | 保持共享 | iOS / iPadOS 适配 | Android 适配 |
|---|---|---|---|
| 任务模型 | 字段、步骤、校验、草稿版本、同步状态、完成规则 | 同一业务结果 | 同一业务结果 |
| 内容层级 | 任务标题、状态、关键证据、主要动作优先级 | 按 Dynamic Type 与系统导航语义呈现 | 按 Material type roles 与 app bar 语义呈现 |
| 导航意图 | 顶级目的地、详情层级、退出/恢复规则 | Navigation stack、edge Back、iPad sidebar/split structure | Navigation component、system/predictive Back、rail/drawer |
| 控件语义 | value、label、error、disabled、analytics event | 原生 iOS controls、SF Symbols、system materials | Material controls、Material Symbols、tonal elevation |
| Adaptive 布局 | compact/medium/expanded 的信息优先级 | size class、Split View、pointer/keyboard | window size class、multi-window、fold posture、D-pad/keyboard |
| 主题 | 语义 color roles、状态含义、品牌色意图 | semantic system colors、light/dark/increased contrast | Material color roles、light/dark/high contrast、可选 Dynamic Color |
| 无障碍结果 | 同一任务可完整操作、同一状态可理解 | VoiceOver、Dynamic Type、Switch Control/keyboard | TalkBack、font scaling、Switch Access/D-pad/keyboard |
| 动效与反馈 | 同一因果状态、不得用动效阻塞提交 | Reduce Motion、克制 haptic、平台 transition | Remove animations、Material transition、snackbar/haptic |

这里追求的是**任务结果与语义一致**，不是控件形状、图标、导航结构和动效像素一致。

## 6. 已确认与未确认

### 本轮输入直接支持的结论

仅在“所给静态描述准确”的前提下，可以确认：
- 产品声明为 `adaptive`，且 `DESIGN.md` 允许平台原生差异。
- 存在固定 `390` 宽度、自定义返回、吞 Android Back、`40x40` pressable、禁用字体缩放、硬编码色值、跨平台同款控件/图标、固定 tab 和无减弱分支的 500ms spring。
- 这些属性足以给出上述**静态平台合同不符合**结论。

它们不是源码现场核验、构建结果或运行时观察。

### 明确未确认

- 实际 iOS/Android target、React Native/导航库版本、store build configuration。
- `hitSlop`、accessibility props、焦点管理或原生组件桥接是否存在于未提供的代码中。
- VoiceOver/TalkBack 的标签、状态公告、custom actions 与真实 traversal。
- Dynamic Type/font scaling 后的裁切、换行、滚动和动作可达性。
- safe area、IME、旋转、Split View、multi-window、foldable 与窗口实时 resize。
- 色彩的实际前景/背景组合、对比度数值和高对比度模式。
- 系统 Back、predictive Back、iOS edge gesture 的真实运行行为。
- 草稿持久化、离线同步、进程终止恢复和冲突处理。
- 动效流畅度、帧率、可中断性、触觉、OEM 差异或硬件手感。

## 7. 最小源码、构建与运行态验证计划

1. **源码核对**：读取真实 `PRODUCT.md`、`DESIGN.md`、`package.json`、iOS/Android manifests 和导航入口；定向搜索 `BackHandler`、`width: 390`、`allowFontScaling`、`fontSize: 14`、硬编码颜色、switch/icon 实现、animation duration、Reduce Motion hooks、window-size 分支及持久化 lifecycle。
2. **静态测试**：补导航/返回分支、draft 恢复、主题映射、字体缩放、accessibility props 与 reduced-motion 分支测试；先运行仓库已有 typecheck、lint、unit/integration scripts，不凭空发明脚本名。
3. **平台构建**：用发现到的 workspace/scheme 执行 `xcodebuild` compile/test；用真实 Gradle variant 执行 assemble、unit test 和 lint。两端构建在本轮均未执行。
4. **iOS Simulator：unverified locally**。至少验证 iPhone compact、iPad 全屏与 Split View；覆盖 edge Back、后台/终止恢复、明暗模式、Dynamic Type accessibility sizes、Reduce Motion、VoiceOver 和外接键盘 traversal。
5. **Android Emulator：unverified locally**。至少验证 gesture-nav phone、tablet/可调整窗口及 foldable profile；覆盖 predictive Back、multi-window、字体放大、Remove animations、TalkBack、IME 与键盘/D-pad traversal。
6. **Real-device evidence：全部缺失**。尚无 iPhone、iPad、Android phone 或 Android tablet/foldable 真机证据；发布前应在代表性硬件上复核返回手势、触觉、触摸命中、后台/进程恢复、OEM 行为和持续性能。

本轮未编辑任何文件，也未执行 iOS Simulator、Android Emulator 或任何真机验证。