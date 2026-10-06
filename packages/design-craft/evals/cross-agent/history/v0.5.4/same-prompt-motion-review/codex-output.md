## 1. 证据级别与设计判断

- **模式**：`design-craft` / `critique`
- **平台**：Web
- **证据级别**：**L0 静态源码审查**。只有产品说明和局部 JS/CSS，没有渲染、computed style、事件轨迹或帧时间证据。
- **风格权威**：以题面给出的“calm utility UI、动效只服务因果关系和直接操控”为准。
- **实施批准结论**：**Block**。保留底部面板运动的理由成立，但当前代码没有建立可靠的直接操控模型，也没有满足 Reduced Motion 要求。
- **设计解读**：我把它读作一个供高频日常运营人员使用的 Web 操作面板，气质应克制、稳定，优先保证拖拽因果清晰、随时可接管，并在状态切换时保留任务上下文。

一句话诊断：**当前实现把拖拽当成“不断改 `top` 后播放固定补间”，而不是一个可中断、带速度连续性的直接操控系统。**

## 2. 哪些运动应该存在

**应该存在：**

- pointer-down 时立即出现局部、低幅度的抓取反馈。
- 超过意图阈值后，面板与指针保持 1:1 跟随。
- 松手后，从当前屏幕位置和当前释放速度出发，短促地收敛到合法状态。
- 程序化切换 `collapsed / half / full` 时，可以有简短、可中断的位移，以解释状态空间关系。

**不应该存在：**

- 不应对整个 sheet 做 `scale(0.96)`；它会让内容、边缘和抓取点一起漂移。
- 不应使用 `transition: all`。
- 不应在拖拽热路径或 settle 中动画 `top`。
- 不应使用固定 `480ms ease-in`；它先迟钝、后加速，与释放动作脱节。
- 不应在 settle 期间锁住重新抓取。
- 不应默认加入弹跳、长惯性或跨多个状态的抛掷。
- Reduced Motion 下不应保留投射、橡皮筋、过冲或大距离自动滑行。

## 3. 阻断发现，按优先级排序

### B1 · P0 — 当前事件通道不构成有效的 1:1 拖拽

- `pointermove` 没有检查 active drag、`pointerId` 或 `buttons`，因此源码允许未按下时的移动事件也写入位置。
- `startY` 在所示代码中没有被使用；`event.clientY` 被直接赋给相对布局属性 `top`。
- 这没有保存 grab offset，也没有把 viewport 坐标明确转换到 sheet/container 坐标。
- 没有 pointer capture、`pointercancel` 或 `lostpointercapture` 处理，指针离开 sheet 后不能保证继续跟踪和收尾。
- 没有合法边界；所示逻辑可把 sheet 拖过 `full` 或 `collapsed`。

### B2 · P0 — settle 不可中断，且输入与动画所有权不一致

- `animating` 只拒绝 `pointerdown`，但 `pointermove` 和 `pointerup` 仍可继续写入或启动动画。
- 用户无法在动画中途重新抓住当前屏幕位置；这破坏了直接操控的核心承诺。
- inline `top`、WAAPI `top`、`fill: "forwards"` 与 CSS transition 同时参与状态表达，缺少单一 presentation-value owner。
- 逻辑目标、底层样式值和屏幕当前值可能分离；实际优先级表现仍需浏览器验证。

### B3 · P0 — 没有可见的 Reduced Motion 路径

- 所示 JS/CSS 没有 `prefers-reduced-motion` 分支。
- 该交互包含最长 `480ms` 的明显空间位移，直接触碰题面明确的无障碍要求。
- Reduced Motion 不能只把时长略微缩短；必须取消额外惯性、橡皮筋和大距离自动 travel，同时保留状态确认。

### B4 · P1 — 释放物理量被清零，目标选择与速度没有分层

- 当前只对 `sheet.offsetTop` 做 `nearestSnapPoint`，没有采样或传递释放速度。
- `ease-in` 等价于松手后重新从近似静止开始，再向目标加速；手指运动与面板运动不连续。
- “速度传入 settle”是必须修复的连续性问题。
- “用 projected endpoint 改选目标”则是独立产品决策；现有证据只支持 nearest-current-position 语义，不能静默改成动量选点。

### B5 · P1 — 属性和按压反馈与高频工具场景冲突

- `top` 是布局属性；在 pointermove 热路径和 WAAPI 中持续改变它存在 layout 成本风险。
- `transition: all 300ms` 可能使每个位置更新都追赶前一个目标，也会把无关属性意外纳入动画。
- 整体 `scale(0.96)` 幅度过大，并会缩放任务内容；对全天重复使用的运营界面属于不必要的视觉扰动。
- **这里只能确认源码风险，不能声称已经发生掉帧或卡顿。**

## 4. 八个具体设计动作

1. **把 pointer-down 反馈限制在 drag handle**
   - handle 立即切换为 `cursor: grabbing`，并用约 `80–120ms` 的颜色、明度或轻微 `scaleX` 反馈。
   - 不缩放 sheet 本体，不改变内容尺寸。
   - 只在专用 handle 设置适当的 `touch-action: none`，避免整张 sheet 阻断内容滚动。

2. **建立明确的拖拽会话**
   - pointer-down 记录唯一 `pointerId`、container 坐标系、当前 presentation Y 和 `grabOffset = pointerY - sheetTop`。
   - 以 `8–12 CSS px` 作为初始方向意图阈值；阈值前保持 tap 可能性，阈值后正式进入 drag。
   - 捕获该 pointer，忽略其他指针，并在 `pointerup`、`pointercancel`、`lostpointercapture` 中统一清理。

3. **用单一 transform owner 做 1:1 tracking**
   - sheet 保持稳定布局基线，位置统一由 `translateY(y)` 表示。
   - 每个显示帧应用最新的 `y = pointerY - containerOrigin - grabOffset`；坐标和速度统一使用 CSS px。
   - 删除 `transition: all` 和 `top` 动画。
   - 外层拥有 drag translation，内层 handle 拥有 press feedback，避免两个行为争写同一个 `transform`。

4. **从 presentation value 中断，而不是用 `animating` 锁输入**
   - 动画控制器持续拥有当前屏幕 `y` 和 `velocity`。
   - settle 中再次 pointer-down 时，先在当前 presentation Y 停止 settle，再以该位置计算 grab offset；视觉跳变目标为零。
   - 删除输入锁；重新松手或程序化 retarget 时，从当前 `y/v` 开始新 settle。
   - 收敛完成后明确提交逻辑状态与最终 transform，不依赖永久 `fill: forwards`。

5. **测量并传递释放速度**
   - 保存最近约 `80–120ms` 的单调时间戳和位置样本，输出单位为 **CSS px/s**。
   - 用多个样本而不是最后两个噪声事件计算速度，并从一个待实测的安全范围开始，例如 `±2400px/s`。
   - settle 使用无过冲或近临界阻尼：起点可取 damping ratio `1.0`、response `0.28–0.35s`。
   - 把测得的速度作为 spring 初速度；若 API 接受相对速度，则转换为 `v / (target - current)`。

6. **把 projected endpoint 作为有边界、需授权的目标策略**
   - 可审计候选：`vBound = clamp(v, -2400, 2400) px/s`，`p = clamp(y + vBound * 0.16s, fullY, collapsedY)`。
   - 再把投射距离限制为最多一个相邻 snap gap，避免高频工具中意外跳过任务上下文。
   - 只有产品确认 momentum-based targeting 后，才使用 `nearestSnapPoint(p)`。
   - 未确认前继续使用 `nearestSnapPoint(y)`，但仍把真实释放速度交给 settle；目标选择与速度连续性不得混为一件事。

7. **加入克制的软边界**
   - 在 `fullY…collapsedY` 内保持严格 1:1。
   - 越界量 `o` 可映射为  
     `sign(o) * (abs(o) * D * 0.55) / (D + 0.55 * abs(o))`，再把显示越界限制在约 `24–32px`。
   - 松手后回到边界，默认无弹跳；inner content 可滚动时必须先完成垂直拖 sheet 与滚内容的方向仲裁。

8. **定义真正的 Reduced Motion 状态机**
   - 保留用户主动控制的 1:1 drag，但关闭 endpoint projection、橡皮筋、过冲和长距离惯性 settle。
   - 若剩余距离很小，可用最多约 `80ms` 的克制收敛；距离较大则直接落到目标状态，不播放整张 sheet 的长滑行。
   - 程序化状态变化以立即换位加局部 `80–120ms` handle/state-label 颜色或 opacity 反馈代替大 travel。
   - settle 后更新明确的 `collapsed / half / full` 可见状态和可访问状态文本，避免只靠位置表达结果。

## 5. 已验证与未验证

**由所给源码直接确认：**

- `pointermove` 无拖拽状态或 pointer 身份门禁。
- 所示 `startY` 未参与位置计算。
- `clientY` 被直接写入 `top`。
- settle 使用 `top`、`480ms`、`ease-in` 和 `fill: "forwards"`。
- `animating` 拒绝 pointer-down，但不拒绝 move/up。
- CSS 含 `transition: all 300ms` 和整体 `scale(0.96)`。
- 所示范围内没有 capture、速度采样、软边界、presentation-value interruption 或 Reduced Motion 分支。

**未验证，不能据此断言：**

- 实际是否跳动、滞后、掉帧或触发布局抖动。
- `transition`、WAAPI 和其他未展示样式最终形成的 computed behavior。
- offset parent、滚动容器、snap point 数值及真实可拖范围。
- 其他文件是否补充了 capture、Reduced Motion、键盘控制或状态语义。
- 鼠标、触控板、触屏、多指、浏览器差异和 inner-scroll 仲裁表现。
- 桌面、窄屏、短视口、60Hz/120Hz 或任何真实设备体验。

本次没有修改文件，也没有执行浏览器、响应式或设备验证。

## 6. 实施批准前的最小浏览器/设备验证

1. **桌面主支持浏览器，记录 pointer trace**
   - 记录 `pointerY`、presentation Y、grab offset、时间戳和状态。
   - 验证未按下移动不会移动 sheet；超过阈值后跟踪误差目标为同帧约 `≤2px`，离开 handle 后仍能完成拖拽。

2. **中途接管**
   - 分别在 settle 约 25%、50%、75% 时重新抓取并反向拖动。
   - 验收：不拒绝输入、无可见位置跳变、没有旧动画继续争写位置。

3. **速度、目标与边界矩阵**
   - 在相近释放位置分别用慢拖、快速上甩和快速下甩测试。
   - 分别确认“现有 nearest 语义”和“经授权的 projection 语义”；验证速度被传入 settle，但不会意外跨越未允许的状态。
   - 向两个端点外拉，确认阻力连续、可恢复且没有硬碰撞感。

4. **computed style 与 Performance trace**
   - 确认位置只由指定 transform layer 拥有，`transition-property` 不为 `all`，拖拽期间没有由该控制器反复触发的 Layout 或长任务。
   - 至少检查目标环境的 60Hz；若 120Hz 设备属于支持范围，再补 120Hz。

5. **Reduced Motion 与响应式**
   - 在浏览器媒体模拟和真实 OS Reduced Motion 设置下各跑一次。
   - 覆盖正常桌面、窄视口和短高度视口；验证无投射、弹性或长滑行，同时状态反馈仍清楚。

6. **至少一台主支持的真实触屏设备**
   - 在实际 Safari 或 Chrome 中测试 handle、内容滚动、pointer cancel、快速反向、多指干扰和动态 viewport。
   - 如果产品同时正式支持 iOS 与 Android，则两端都应通过后再批准，而不能用桌面指针测试替代触感结论。