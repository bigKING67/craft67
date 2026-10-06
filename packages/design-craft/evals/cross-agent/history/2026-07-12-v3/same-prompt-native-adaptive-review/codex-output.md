## 1. 证据级别、平台解析与设计读法

- **评审模式**：`design-craft / critique`，只读静态评审。
- **证据级别**：**prompt-only 静态描述**。足以判定明确写出的尺寸、配置和架构反模式；不足以证明实际渲染、手势、无障碍树、性能或设备体验。
- **Resolved platform**：`adaptive`。
  - 来源：明确的 `PRODUCT.md platform: adaptive`
  - 置信度：**高**
  - React Native 同时面向 iOS / Android，与该平台定义一致。
- **Style authority**：`DESIGN.md` 要求共享语义角色和内容层级，同时明确允许平台原生适配；因此当前“像素级统一”的做法不是设计系统要求，而是实现偏离。
- **Design read**：这是一个面向单手现场操作员、同时服务平板管理者复核的任务界面；气质应可信、克制、可恢复，优先保证快速完成、原生导航和中断后续做。

**一句话诊断**：当前概念是“固定宽度的统一皮肤”，不是“共享产品语义、分别遵守 iOS 与 Android 合同”的 adaptive 产品，两个平台都不具备发布级 conformance。

## 2. 分平台结论

| 平台 | 结论 | 主要原因 |
|---|---|---|
| **iOS / iPadOS** | **BLOCK：不符合发布级平台规范** | 替换原生 navigation stack、40×40 目标、禁用 Dynamic Type、iPad 无结构适配、非系统图标、缺少 Reduce Motion 路径 |
| **Android** | **BLOCK：不符合发布级平台规范** | 消费 system Back 并破坏 predictive Back、40×40 目标、禁用字体缩放、Cupertino 控件、平板仍用底部栏、缺少 Remove animations 路径 |

这不是“需要少量 polish”的状态；导航、字体缩放、触控目标和减弱动画都是 release-blocking contract。

## 3. 最多五项阻断问题

### P0-1 无障碍基础合同直接失败

- 固定 `fontSize: 14` 且关闭字体缩放，直接违反 Dynamic Type / Android font scaling 要求。
- 若 `40×40` 是实际可点击边界且没有外层命中区域：
  - iOS 低于 `44×44pt`
  - Android 低于 `48×48dp`
- 对单手、戴手套、运动中操作或运动能力受限的现场用户，误触和不可读风险尤其高。
- VoiceOver、TalkBack、外接键盘遍历没有任何静态证据，不能视为通过。

**接受条件**：字体按语义角色缩放至项目规定上限仍可重排；所有主操作满足平台最小目标，且屏幕阅读器、键盘遍历不丢失功能。

### P0-2 导航和系统 Back 被自定义实现破坏

- iOS：自定义顶栏和 JavaScript Back 替代 navigation stack，无法静态证明保留原生返回层级、交互式左缘返回、焦点恢复及系统转场。
- Android：空 `BackHandler` 消费 Back 是明确缺陷，会拦截系统 Back，并与 predictive Back 合同冲突。
- 对“中断后不丢进度”的任务产品，吞掉 Back 既不是保护进度，也不是可预测导航。

**接受条件**：恢复平台导航栈；Android system/predictive Back 可正常预览和完成；iOS 保留原生返回手势；只有明确的未保存风险才进入可理解的离开保护流程。

### P0-3 Phone-to-tablet 没有发生结构适配

- 强制 `width: 390` 并居中，只是把手机画布放进平板，不是 adaptive layout。
- 底部 tab 在手机、iPad、Android 平板完全不变，忽略 window size、Split View、multi-window 和输入模式。
- 管理者复核任务需要利用扩展宽度展示上下文、证据和验证状态，而不是永久窄列。

**接受条件**：由可用窗口和 size class 驱动结构；compact 保持单栏，expanded 提供适合复核的双栏/侧栏/详情结构，并在窄分屏时可靠退回 compact。

### P0-4 控件、图标和主题采用了错误的“视觉一致”

- 同一个 Cupertino-shaped switch 在 Android 上不符合 Material 行为和状态表达。
- 同一套 web icons 无法保证 SF Symbols / Material Symbols 的字重、基线、RTL、无障碍名称和系统熟悉度。
- `#777777`、`#FFFFFF` 绕过 `DESIGN.md` 的语义颜色角色，并在两种 appearance 中复用，无法建立可靠的亮色、暗色和高对比主题合同。
- 具体对比度是否失败无法仅凭颜色出现位置判断，但**主题语义合同已确定失败**。

**接受条件**：共享语义 token，平台分别映射到系统颜色、材料和控件；实际前景/背景组合完成对比度验证。

### P0-5 完成动画不符合运营产品及减弱动画要求

- `500ms` overshooting spring 对高频任务完成反馈偏慢且过于弹跳，不符合“trustworthy, calm”。
- 缺少 iOS Reduce Motion 和 Android Remove animations 分支，是明确的无障碍发布阻断。
- 未知业务提交、成功公告或下一步焦点是否等待动画结束；若等待，会进一步增加状态不确定性。

**接受条件**：数据提交与视觉动画解耦；默认反馈更短、更克制；Reduce Motion 使用短 cross-fade，Remove animations 可直接更新状态；动画不延迟成功语义、公告或继续操作。

## 4. 八项具体设计动作

1. **恢复原生导航合同**  
   使用 React Navigation native stack 或等效原生集成；移除吞掉 Back 的空 `BackHandler`；接入 Android predictive Back，并保留 iOS interactive pop。

2. **按窗口能力重构布局**  
   使用 window/size classes、可用宽度和输入模式，而不是设备名：compact 单栏；expanded 使用任务列表/详情或任务内容/验证面板双栏。

3. **重新设计单手操作区**  
   主完成动作优先位于安全、可达的下部区域；iOS 至少 `44×44pt`，Android 至少 `48×48dp`，同时保留合理间距和明确按下状态。

4. **采用可缩放的语义排版**  
   开启 `allowFontScaling`；将共享的标题、正文、标签等语义映射到 iOS Dynamic Type styles 和 Android Material type roles/`sp`；大字号时允许换行和纵向扩展。

5. **把原始颜色替换为语义角色**  
   例如 `surface`、`onSurface`、`primaryAction`、`success`、`warning`、`divider`；分别映射 light/dark，必要时覆盖 increased-contrast/high-contrast 环境。

6. **平台化控件和图标**  
   共享业务 props 与状态机，但 iOS 使用原生 switch/SF Symbols，Android 使用 Material switch/Material Symbols；不要用视觉 look-alike 隐藏平台分支。

7. **建立双平台 motion policy**  
   默认完成反馈控制在约 `150–250ms`、无明显 overshoot；iOS Reduce Motion 使用低位移 cross-fade，Android Remove animations 使用立即切换或极短淡变；不依赖 animation-end 提交状态。

8. **把可恢复任务状态纳入界面合同**  
   草稿自动保存、幂等完成、后台/进程重建后恢复；完成时发送 VoiceOver/TalkBack announcement，焦点移动到逻辑下一步，同时保持键盘遍历顺序。

## 5. Intentional parity matrix

| 能力 | 保持共享 | iOS / iPadOS 必须适配 | Android 必须适配 |
|---|---|---|---|
| 任务模型 | 字段、校验、草稿、完成状态、错误恢复、分析事件语义 | 同一业务结果 | 同一业务结果 |
| 内容层级 | 任务标题、步骤、证据、状态、主次动作 | 按 iOS typography/layout 表达 | 按 Material typography/layout 表达 |
| 导航 | 目的地和层级关系 | Navigation stack、interactive Back、iPad sidebar/split 选择 | System/predictive Back、navigation bar/rail/drawer |
| 自适应结构 | compact/expanded 的信息优先级 | Size classes、Split View、键盘输入 | Window size classes、multi-window、fold posture |
| 控件与图标 | 共享业务 API、状态和可访问名称 | Native controls、SF Symbols、system materials | Material components、Material Symbols、tonal elevation |
| 主题 | `surface/onSurface/action/status` 等语义角色 | Dynamic system colors、iOS appearance | Material color roles、可选 Dynamic Color 和静态 fallback |
| 无障碍结果 | 同样的任务可完成性、焦点逻辑和状态公告 | VoiceOver、Dynamic Type、Reduce Motion、Switch Control | TalkBack、font scaling、Remove animations、D-pad |
| 动效反馈 | 同一因果状态和完成含义 | iOS 转场、克制 haptics | Material motion、Android feedback/snackbar 语法 |

**应追求结果和业务语义 parity，而不是像素、控件形状或导航外壳 parity。**

## 6. 已验证与未验证

### 可由给定静态描述确认

以下内容仅表示“按题面作为事实接受”，不是我独立读取源码后确认：

- 产品目标平台明确为 `adaptive`。
- `DESIGN.md` 允许平台原生导航、控件、图标、材料和动效。
- 存在固定 `390` 宽度、自定义 Back、消费 Android Back、`40×40` pressable、固定且禁缩放字体、原始颜色、统一 Cupertino switch/web icons、统一底部栏和无减弱动画分支。
- 基于这些事实，可以静态判定两个平台当前均未满足发布级设计合同。

### 完全未验证

- 实际源码位置、依赖版本、导航库配置和构建是否成功。
- `hitSlop`、父容器或无障碍 delegate 是否扩大了有效触控区域。
- VoiceOver/TalkBack labels、roles、values、state descriptions、focus/traversal、announcements。
- 外接键盘、D-pad、Switch Control 的实际遍历和激活。
- safe area、IME、cutout、home indicator、hinge、RTL、横竖屏和本地化扩展。
- 实际颜色配对、对比度、暗色主题及系统高对比模式。
- 草稿持久化、后台恢复、进程死亡恢复、离线和重复提交行为。
- 动画流畅度、可中断性、触感、帧率、性能和实际视觉质量。
- iOS 返回手势、Android predictive Back、平板分屏和 multi-window 的运行表现。

## 7. 最小源码、构建与运行时验证计划

1. **源码审计**
   - 先确认 `package.json`、导航库、iOS/Android targets 和现有测试脚本。
   - 定位 `width: 390`、`BackHandler`、`allowFontScaling`、`fontSize: 14`、硬编码颜色、switch/icon 封装、spring 配置、window dimensions 和 reduced-motion 分支。
   - 检查任务草稿持久化、导航状态恢复、无障碍 props、focus management 和完成状态机。

2. **最小静态/构建门禁**
   - 使用仓库已有的 type-check、lint 和相关单元测试，不臆造包管理器脚本。
   - iOS：先用 `xcodebuild -list` 解析真实 workspace/project 与 scheme，再执行 Simulator 目标的 build/test。
   - Android：执行真实模块的 Gradle compile/assemble、unit test 和 lint，例如确认模块后运行对应 `assembleDebug`、`testDebugUnitTest`、`lintDebug`。

3. **最小运行矩阵**
   - iOS：一台 compact iPhone Simulator，加一个 iPad Split View 状态；覆盖大号 Dynamic Type、VoiceOver、Reduce Motion、亮/暗色、键盘和返回手势。
   - Android：一个手机 Emulator，加一个 tablet/multi-window 或 foldable profile；覆盖 gesture navigation/predictive Back、200% font scale、TalkBack、Remove animations、亮/暗色和键盘/D-pad。
   - 两端都执行：开始任务 → 输入部分内容 → 后台/中断 → 恢复 → 完成 → 重复触发/返回，确认进度、焦点和公告一致。

4. **真实设备发布前门禁**
   - 至少一台代表性 iOS 设备和一台代表性 Android 设备，并让其中至少一个覆盖平板/扩展窗口场景。
   - 验证单手可达性、边缘/预测返回、haptics、OEM/insets、后台与进程恢复、持续性能和真实触控手感。

**当前证据状态：**

- `iOS Simulator: unverified locally`
- `Android Emulator: unverified locally`
- `iOS real device: unverified`
- `Android real device: unverified`
- `iPad Split View: unverified`
- `Android tablet/foldable multi-window: unverified`
- 未执行源码扫描、type-check、lint、build、截图或 accessibility-tree 检查。