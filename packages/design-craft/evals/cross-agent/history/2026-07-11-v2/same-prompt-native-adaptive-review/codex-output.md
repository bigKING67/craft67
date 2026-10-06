# Adaptive Native 静态评审

## 1. 证据等级、平台解析与设计判断

- **评审模式**：`design-craft / critique`，只读原生与 adaptive 一致性评审。
- **证据等级**：`L0 static`。
  - 仅有产品上下文和静态实现描述。
  - 没有源码树、构建结果、截图、可访问性树或任何原生运行态证据。
- **解析平台**：`adaptive`
  - **来源**：提示中明确给出的 `PRODUCT.md`
  - **置信度**：`1.0`，仅指目标平台判断，不代表实现质量已经验证。
- **样式权威**：提示中描述的 `DESIGN.md`
  - 应保持共享语义色彩角色和内容层级。
  - 明确允许导航、控件、图标、材质和动效按平台适配，因此“共享设计系统”不能作为两端像素级复用的理由。
- **核心用户任务**：
  - 操作员在手机上单手快速完成任务。
  - 管理者在平板分屏或多窗口中复核同一任务。
  - 中断后必须恢复，不得丢失进度。

> **Reading this as:** an adaptive native task workflow for one-handed field operators and tablet-reviewing managers, with a calm, trustworthy, platform-native character, optimized for fast completion, verification, and interruption-safe resumption.

**总评：当前概念在 iOS 和 Android 上均不满足发布级平台一致性要求。**
主要问题不是视觉精致度，而是系统导航、可访问性、窗口适配和平台信任合同被共享实现破坏。当前静态证据已经足以形成发布阻断结论，但不足以形成任何模拟器、真机、手势体验或运行时正确性结论。

---

## 2. 分平台一致性结论

### iOS：不通过，存在发布阻断项

| 维度 | 结论 | 理由 |
|---|---|---|
| 导航 | **阻断** | 自定义顶栏和 JavaScript Back 替代 iOS navigation stack，无法从描述中证明原生层级、交互式返回、左边缘返回手势、转场中断和状态恢复得到保留。 |
| 触控 | **阻断** | `40x40` 小于 iOS 最低 `44x44pt` 触控目标。 |
| 字体与缩放 | **阻断** | 固定 `fontSize: 14` 且关闭字体缩放，直接违反 Dynamic Type 发布要求。单一字号同时削弱内容层级。 |
| iPad / Split View | **阻断** | 整屏强制 `width: 390` 并居中，是“平板显示手机画布”，而不是根据可用空间进行结构适配。 |
| 动效可访问性 | **阻断** | 任务完成动效没有 Reduce Motion 替代路径。 |
| 控件和图标 | **高风险** | Cupertino 外形在 iOS 上方向上熟悉，但“看起来像 UISwitch”不等于具有系统语义、动态颜色、焦点和可访问性行为；统一 web icon set 也没有证明符合 SF Symbols 的光学和语义规范。 |
| 主题 | **高风险** | 共享使用 `#777777`、`#FFFFFF` 绕过语义色彩角色，无法证明浅色、深色及系统对比设置的一致性。缺少颜色用途，不能据此直接断言具体对比度数值。 |
| 底部标签栏 | **需重构评估** | iPhone 上的 tab bar 可能合理，但在 iPad 和 Split View 中原样保留、同时整屏锁为 390 宽，不能满足管理者的复核任务。应按 size class 和信息架构决定 tab、sidebar 或 split view。 |
| 完成动效风格 | **不符合定位** | `500ms`、带 overshoot 的完成转场对“冷静、可信、操作型”产品过于显眼。若它阻塞后续操作则问题更严重，但是否阻塞目前未验证。 |

### Android：不通过，系统 Back 为明确发布阻断

| 维度 | 结论 | 理由 |
|---|---|---|
| 系统 Back | **阻断** | 空 `BackHandler` 消耗 Android Back，明确破坏系统返回和 predictive Back 合同，可能困住用户或造成导航预期错乱。 |
| 导航 | **阻断** | JavaScript 自定义返回代替系统导航分发，不能满足预测返回预览、取消、层级退出和系统手势协调。 |
| 触控 | **阻断** | `40x40` 小于 Android 最低 `48x48dp` 触控目标；相邻目标通常还应保留约 `8dp` 分隔。 |
| 字体与缩放 | **阻断** | 固定 `fontSize: 14` 且关闭缩放，违反 Android font scaling 和 TalkBack 相关发布要求。 |
| 平板 / 多窗口 | **阻断** | 固定 390 宽画布不响应 window size class、Android multi-window 或 fold posture，无法支持管理者复核场景。 |
| 动效可访问性 | **阻断** | 没有 Remove animations 替代路径。 |
| 控件和图标 | **高风险** | Cupertino-shaped switch 和 web icon set 是明显的 iOS/web 移植痕迹；应映射到 Material Switch、Material Symbols 及 Android 状态语义。 |
| 主题 | **高风险** | 原始十六进制颜色绕过 Material color roles，无法证明 dark theme、tonal elevation、disabled/pressed/focus 等状态一致。 |
| 自适应导航 | **高风险** | compact phone 可以使用 bottom navigation；medium/expanded 平板通常应评估 navigation rail、drawer 或 list-detail 结构。所有尺寸原样保留底栏不是有意适配。 |
| 完成动效风格 | **不符合定位** | 固定 `500ms` overshoot spring 没有体现 Material 层级关系，也没有适配系统动画比例。应改为克制的 fade-through、shared-axis 或立即状态更新。 |

---

## 3. 优先级发现

| 优先级 | 类别 | 给定证据 | 用户影响 | 最小修正与验收条件 |
|---|---|---|---|---|
| **P0** | Android Back | 空 `BackHandler` 消耗 Back | 用户可能无法按系统习惯退出当前层级；predictive Back 不成立 | 删除无条件消费逻辑，将返回交给平台导航宿主；只有明确处理时才消费。验收：手势和按钮 Back 均展示正确目标、可取消且不困住用户。 |
| **P0** | iOS 导航 | 自定义顶栏和 JS Back 替代 navigation stack | 破坏平台熟悉性，返回手势、转场中断和层级恢复缺乏保证 | 使用 native-stack-capable 导航实现，保留系统返回项和左边缘手势。验收：返回行为、标题、转场和状态恢复符合 iOS 层级。 |
| **P0** | 字体缩放 | 固定 `14`，缩放禁用 | Dynamic Type/font scaling 用户可能无法阅读，放大后层级和操作也无法成立 | 使用语义文字角色；iOS 映射 Dynamic Type，Android 映射 Material type roles/`sp`；不得禁用缩放。验收：目标最大缩放下无裁切、重叠或不可达操作。 |
| **P0** | 触控目标 | 所有主操作均为 `40x40` | 单手、运动中或精细动作受限的用户更容易误触或漏触 | iOS 至少 `44x44pt`；Android 至少 `48x48dp`，并检查目标间距。视觉图标可较小，但命中区域必须合格。 |
| **P0** | Adaptivity | 整屏固定 `width: 390` | 平板复核空间被浪费；Split View、多窗口和横屏无法形成有效工作区 | 由实际窗口宽度、size/window class、姿态和输入模式驱动布局。验收：compact 单栏；expanded 可形成列表—详情或复核辅助面板。 |
| **P0** | 动效可访问性 | 500ms overshoot，无替代路径 | Reduce Motion/Remove animations 用户无法使用符合系统设置的完成流程 | iOS Reduce Motion 使用短 cross-fade/低位移；Android Remove animations 使用 cross-fade 或立即状态更新。验收：关闭动画后仍有明确、即时的完成反馈。 |
| **P0 验证缺口** | 辅助技术 | 没有可访问性树或运行证据 | VoiceOver、TalkBack、外接键盘均是明确发布要求，但当前不能判断是否可用 | 验证 label、role/trait、value/state、阅读顺序、焦点恢复、完成公告和键盘遍历。未通过前不得发布。 |
| **P0 验证缺口** | 中断恢复 | 没有草稿持久化、后台恢复或进程重建证据 | 产品的核心承诺“中断不丢进度”尚未得到任何证明 | 建立共享草稿状态机和显式保存状态；分别验证 iOS/Android 生命周期恢复、进程终止和错误恢复。 |
| **P1** | 主题与设计系统 | `#777777`、`#FFFFFF` 在两种外观中直接使用 | 语义角色、dark theme 和状态颜色容易漂移；具体对比度未知 | 保留共享语义角色名，分别映射到 iOS dynamic system colors/materials 和 Material `ColorScheme`。不得让组件自行判断浅色/深色字面值。 |
| **P1** | 平台控件 | 两端使用同一 Cupertino switch | Android 明显失去平台信任；iOS 也可能只是视觉仿制而非原生行为 | 共享 `Switch` 的业务 API 和状态，不共享像素实现；iOS 使用 native-backed switch，Android 使用 Material switch。 |
| **P1** | 图标 | 两端共用 web icon set | 光学尺寸、笔画、方向语义和平台熟悉性可能不一致 | 共享图标语义键；iOS 映射 SF Symbols，Android 映射 Material Symbols。仅品牌专属图形保持跨平台一致。 |
| **P1** | 平板导航 | phone、iPad、Android tablet 使用同一底栏 | 复核任务没有利用更大宽度；导航和内容仍是手机模式 | compact 保留合适的 bottom navigation/tab bar；expanded 根据平台采用 sidebar、rail、drawer 或 split view。 |
| **P2** | 动效调性 | 固定 500ms overshoot spring | 完成操作可能显得拖沓、庆祝化或难以连续工作 | 将“完成”重点放在即时状态确认；默认无 overshoot，使用平台一致的短转场。只有实测证明有价值时保留轻微弹性。 |

---

## 4. 设计修正与 intentional parity matrix

### 4.1 具体设计修正

1. **先拆除固定手机画布**
   - 不再给整个 screen 设置 `width: 390`。
   - compact 宽度保持单栏、单手优先。
   - medium/expanded 宽度升级为列表—详情、任务—证据或任务—复核面板。
   - 可以为长文本内容设置可读宽度上限，但不能把整个导航和工作区一起锁成手机宽度。

2. **共享路由语义，不共享系统返回实现**
   - 两端可共享 route IDs、任务状态和导航意图。
   - iOS 使用原生栈语义、系统返回项和边缘返回手势。
   - Android 将 Back 交给系统导航宿主并支持 predictive Back。
   - 删除空的 Back 消费器；任何自定义拦截都必须有明确状态和可恢复结果。

3. **重建平台自适应导航**
   - 手机 compact：保留 3–5 个稳定顶级目的地时，iOS tab bar / Android bottom navigation 都可成立。
   - iPad expanded：根据任务复核 IA 使用 sidebar 或 split view。
   - Android medium/expanded：评估 navigation rail、drawer 或 list-detail pane。
   - 尺寸变化不得清空草稿、重置当前任务或丢失滚动/选择状态。

4. **将主操作改为可访问、单手友好的动作区**
   - 扩大命中区域到 iOS `44pt`、Android `48dp`。
   - 主完成操作保持在拇指可达区域，同时避开 home indicator、gesture inset 和 IME。
   - pressed、disabled、loading、success、error 状态必须明确。
   - 完成后立即显示任务对象和结果，而不是只播放动画。

5. **改用语义排版**
   - 共享 `title`、`section`、`body`、`label`、`metadata` 等内容角色。
   - iOS 映射到 Dynamic Type text styles。
   - Android 映射到 Material typography roles 和可缩放 `sp`。
   - 放大文字时允许换行和纵向增长，不通过禁止缩放维持布局。

6. **保留语义色彩，共享角色而非具体颜色**
   - 共享：`surface.primary`、`text.primary`、`text.secondary`、`action.primary`、`state.success`、`divider` 等角色。
   - iOS：映射到动态系统色、系统材质和 tint。
   - Android：映射到 Material `ColorScheme`、tonal elevation，并按产品策略决定是否使用 Dynamic Color。
   - 对浅色、深色、disabled、pressed、selected、error、focus 状态分别验收。

7. **将完成动画改成因果反馈**
   - 先提交或保存状态，再呈现明确的完成反馈。
   - 默认使用克制、无弹跳或接近临界阻尼的转场。
   - iOS 可使用符合栈、sheet 或状态切换关系的原生转场。
   - Android 可使用 fade-through、shared-axis 或立即状态更新。
   - Reduce Motion/Remove animations 路径不得依赖同一空间位移动画。
   - VoiceOver/TalkBack 应在实际状态提交后公告结果；公告不能只绑定到动画结束。

8. **把中断恢复作为共享产品合同**
   - 共享草稿、提交中、成功、失败、冲突和待同步状态机。
   - 表单输入和证据采集应按明确节点保存。
   - 平台生命周期代码分别处理后台、活动重建、窗口变化和进程恢复。
   - 用户恢复时必须知道：当前任务、已保存内容、未完成步骤和是否已同步。

### 4.2 Intentional parity matrix

| 领域 | 保持共享 | iOS 必须适配 | Android 必须适配 |
|---|---|---|---|
| 产品流程 | 任务步骤、验证规则、状态名称、完成条件、错误恢复语义 | 使用 iOS 层级、sheet 和返回模型呈现 | 使用 Android Navigation、Back 和预测返回模型呈现 |
| 草稿与中断恢复 | 草稿状态机、保存时机、同步语义、冲突规则 | 适配 iOS foreground/background、scene 生命周期和状态恢复 | 适配 activity 重建、process death、multi-window 生命周期 |
| 内容层级 | 标题、步骤、证据、状态和操作优先级 | 映射到 Dynamic Type 和 iOS 标题/列表语法 | 映射到 Material typography 和 Android app/list 语法 |
| 颜色系统 | 共享语义角色和状态含义 | 动态系统色、系统材质、tint、iOS appearance | Material `ColorScheme`、tonal elevation、可选 Dynamic Color |
| compact 导航 | 共享顶级目的地、当前选择和深链目标 | 原生 tab bar / navigation stack | bottom navigation / Navigation component |
| expanded 导航 | 共享信息架构和选中任务 | sidebar、split view 或平台适当的 iPad 结构 | navigation rail、drawer 或 list-detail pane |
| 返回行为 | 共享“返回哪个逻辑状态”的规则 | 系统 back item、左边缘交互式返回、可中断转场 | 系统 Back、predictive Back、取消与目标预览 |
| 控件 | 共享业务属性：label、value、disabled、loading、error | native-backed switch、picker、alert、context action | Material switch、picker、dialog、bottom sheet、snackbar |
| 触控目标 | 共享命中区域可达和误触防护要求 | 最低 `44x44pt` | 最低 `48x48dp`，通常保留约 `8dp` 分隔 |
| 图标 | 共享语义名称和品牌专属图形 | SF Symbols 或 iOS 光学规范映射 | Material Symbols 或 Android 光学规范映射 |
| 动效意图 | 共享因果节点：提交、完成、失败、恢复 | iOS 空间关系、Reduce Motion、平台 haptic | Material motion、Remove animations、Android feedback |
| 辅助技术 | 共享标签文本、顺序意图、错误和完成语义 | VoiceOver traits/actions/announcements、Full Keyboard Access | TalkBack roles/state descriptions/actions、键盘/D-pad |
| 外观 | 共享 light/dark 角色覆盖要求 | iOS dynamic appearance 和系统对比设置 | Android light/dark theme、系统颜色和 OEM 差异 |
| 分析与日志 | 共享事件名称、任务 ID 和状态语义 | 平台生命周期事件映射 | 平台生命周期和 Back 事件映射 |

**应追求的是结果与产品语义一致，而不是像素、控件形状或转场参数完全一致。**

---

## 5. 已判定与未验证声明

### 在本基准证据边界内可直接判定

以下内容由提示明确给出，属于 **prompt-attested static facts**，并非对真实源码的独立复核：

- 目标平台明确为 `adaptive`。
- `DESIGN.md` 允许平台原生导航、控件、图标、材质和动效。
- React Native screen 被强制为 `width: 390`。
- 自定义顶栏和 JavaScript Back 替代平台导航。
- 空 `BackHandler` 消耗 Android Back。
- 主操作命中区域为 `40x40`。
- 字体固定为 `14` 且字体缩放被禁用。
- 两种外观中直接使用 `#777777` 和 `#FFFFFF`。
- 两端使用相同 Cupertino-shaped switch 和 web icon set。
- 手机和平板使用相同底部标签栏。
- 完成转场为 `500ms` overshoot spring，且没有 Reduced Motion/Remove animations 替代。
- 数值上，`40` 小于 iOS 的 `44pt` 最低目标，也小于 Android 的 `48dp` 最低目标。
- 禁用字体缩放和缺少减弱/移除动画路径，与明确的发布要求直接冲突。
- 固定 390 宽的整屏实现不满足题设中的平板分屏、多窗口复核目标。

### 未验证，不能表述为已经通过或已经失败的运行行为

- 真实源码是否与描述完全一致。
- iOS 工程是否使用 native stack、是否仍存在任何返回手势桥接。
- Android predictive Back 的实际动画、目标预览和取消行为。
- safe area、状态栏、navigation bar、cutout、hinge 和 IME inset。
- VoiceOver/TalkBack 的 label、role、trait、state、value、reading order、custom action 和 announcement。
- 外接键盘、Full Keyboard Access、Tab/D-pad 顺序及焦点可见性。
- Dynamic Type/font scaling 后是否裁切、重叠、溢出或丢失操作。
- `#777777` 和 `#FFFFFF` 的实际前景/背景组合及具体对比度。
- switch 是否是真正的平台原生控件，还是仅有相同外观的自定义控件。
- iPad Split View、Android multi-window、横竖屏和 foldable posture。
- 底部导航的目的地数量、信息架构是否适合 compact phone。
- 完成动画是否阻塞输入、能否中断、是否掉帧。
- 系统 Reduce Motion/Remove animations 设置是否被底层框架部分自动处理。
- 任务草稿是否持久化，后台、活动重建或进程终止后是否丢失进度。
- 离线、慢网络、提交重试、重复提交和冲突恢复。
- 手势触感、拇指可达性、haptic、OEM 差异、60/120Hz 表现。
- 构建、测试、Simulator、Emulator 或真机结果。

---

## 6. 最小源码、构建与运行验证计划

### 6.1 源码检查

先从真实项目脚本、导航依赖和平台目录确定实现，不假设包管理器或导航框架。最小静态定位可使用：

```bash
rg -n \
  "width\s*:\s*390|BackHandler|allowFontScaling\s*:\s*false|maxFontSizeMultiplier|fontSize\s*:\s*14|#777777|#FFFFFF" \
  <app-source>
```

```bash
rg -n \
  "Pressable|Touchable|hitSlop|Switch|tabBar|bottomNavigation|spring|overshoot|reduceMotion|AccessibilityInfo" \
  <app-source>
```

随后核对：

1. 导航依赖是否支持 iOS native stack 和 Android predictive Back。
2. `BackHandler` 每个 listener 的返回值、注册范围和清理逻辑。
3. `40x40` 是视觉尺寸还是实际命中区域；是否存在 `hitSlop`。
4. 所有文本组件是否允许缩放，是否存在过低的 `maxFontSizeMultiplier`。
5. raw colors 是否用于文本、背景、图标或状态；是否已有语义 token 层。
6. switch 和 icons 是否有 `Platform` 映射，还是统一像素实现。
7. layout 是否根据 window/size class、orientation、split/multi-window 状态重排。
8. 完成动画是否读取系统 Reduce Motion/Remove animations 设置。
9. 草稿状态是否持久化，提交中的中断和恢复如何处理。
10. accessibility props、焦点顺序、完成公告和错误恢复是否存在。

### 6.2 构建与静态测试

使用真实 `package.json` 和 lockfile 对应的既有命令，不凭空替换项目脚本：

1. 运行项目既有的 type-check、lint 和相关单元测试。
2. 为以下逻辑补充或确认静态测试：
   - compact / medium / expanded 布局选择。
   - 未处理的 Android Back 不被消费。
   - 字体缩放保持启用。
   - 交互命中区域满足平台下限。
   - semantic color roles 在 light/dark 中均有映射。
   - Reduced Motion/Remove animations 能选择替代转场。
   - 草稿保存和恢复状态机不依赖当前 screen 实例。

iOS 构建应至少使用实际 workspace/project 和 scheme 执行等价命令：

```bash
xcodebuild \
  -workspace <App>.xcworkspace \
  -scheme <App> \
  -sdk iphonesimulator \
  build
```

Android 构建应按真实 module 调整，最低覆盖：

```bash
./gradlew :app:assembleDebug :app:lintDebug :app:testDebugUnitTest
```

以上均为待执行计划；当前没有构建证据。

### 6.3 iOS Simulator

**iOS Simulator: unverified locally**

最低运行矩阵：

- 一台 compact iPhone。
- 一台 iPad，覆盖全屏和 Split View 窄宽状态。
- light/dark appearance。
- 默认字号及 Dynamic Type accessibility sizes。
- VoiceOver。
- Reduce Motion。
- 外接键盘或 Full Keyboard Access。
- 前台—后台—恢复及终止后重启。

关键验收：

- 系统返回项和左边缘返回手势到达正确目标。
- 返回可取消，转场没有跳变或状态丢失。
- 文字放大后主操作仍可达。
- iPad 从单栏重构为适合复核的 pane/sidebar 结构。
- 完成状态在 Reduce Motion 下仍清楚、及时并得到正确公告。
- 草稿在中断、窗口变化和恢复后保持一致。

### 6.4 Android Emulator

**Android Emulator: unverified locally**

最低运行矩阵：

- 一台 compact phone。
- 一台 tablet 或 expanded-width profile。
- multi-window；若产品支持相关设备，再覆盖 foldable posture。
- 支持 predictive Back 的 Android API level。
- light/dark theme。
- 默认字体及放大 font scale。
- TalkBack。
- Remove animations。
- 外接键盘/D-pad。
- activity recreation、后台恢复和模拟 process death。

关键验收：

- 删除空 Back 消费后，系统 Back 和 predictive Back 目标正确。
- Back 预览、取消及完成过程不丢草稿。
- expanded width 使用 rail/drawer/list-detail 等合理结构，而非居中手机画布。
- TalkBack 顺序、state description、custom action 和完成公告正确。
- Remove animations 下无 overshoot 或大范围位移，状态反馈仍完整。
- activity/process 重建后任务进度恢复。

### 6.5 真机证据

- **iOS real device: unverified**
- **Android real device: unverified**

发布前至少需要各一台代表性真机，验证：

- 系统边缘返回和 predictive Back 的真实触感。
- 单手拇指可达性及误触情况。
- VoiceOver/TalkBack 实际操作效率。
- 外接键盘或硬件输入。
- haptic 和声音反馈的因果时机。
- 后台中断、锁屏、来电/系统中断后的恢复。
- Android OEM 导航和字体差异。
- 60Hz/120Hz 下完成动效和导航手势。
- 真机进程回收后草稿是否仍可恢复。

在 iOS Simulator、Android Emulator 和两端代表性真机证据补齐前，只能给出**静态发布阻断评审**，不能宣称 adaptive 原生体验、辅助技术、手势、动效或中断恢复已经通过。