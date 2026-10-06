## 1. 证据等级与设计判断

- **证据等级：静态源码片段级，source-only。** 可确认事件处理、属性所有权、显式时长/缓动以及提供片段中缺失的分支；不能证明实际手感、帧率、浏览器最终合成行为或设备触控表现。
- **审查模式：** `design-craft / critique`，平台按 **Web** 处理；采用 `motion-quality`、`interaction-physics` 和静态证据边界。
- **Design read：** Reading this as: 面向高频运营人员的 Web 任务底部面板，气质克制、工具化，以拖拽时保持任务上下文、输入与位移直接对应、最终状态可预测为首要目标。
- **结论：暂不批准当前实现。** 阻断原因是源码中存在明确的直接操控、可中断性和 Reduced Motion 合同缺口，不是因为已经观察到卡顿——本轮没有运行浏览器或设备。

## 2. 哪些运动应该存在

**应该存在：**

- Pointer-down 时，拖拽手柄立即给出克制的输入反馈。
- 越过意图阈值后，面板位置与指针保持 **1:1 映射**；这不是延迟播放的“动画”，而是直接操控。
- 松手后，用短促、无装饰性弹跳的 settle 将面板归入 `collapsed`、`half` 或 `full`，以解释离散状态变化。
- 状态标签、手柄或 scrim 可以使用轻微颜色/透明度变化帮助确认状态。

**不应该动画：**

- 不应给拖拽跟踪附加 `300ms` tween。
- 不应使用 `transition: all`。
- 不应逐帧动画或更新布局属性 `top`。
- 不应缩放整个任务面板及其内容；内容应保持视觉尺度和上下文稳定。
- 不应使用 `480ms ease-in` 作为高频操作的固定 settle。
- calm utility UI 不需要装饰性 bounce、连续弹性振荡或多层内容视差。
- Reduced Motion 下不应保留大幅自动位移、rubber-band 或 overshoot。

## 3. 五个阻断发现

1. **B1 — 手势生命周期不成立。**  
   `pointermove` 和 `pointerup` 没有 active-drag、`pointerId` 或按键检查；因此提供代码中，未按下时的鼠标移动也能写入 `top`，任意 `pointerup` 都能触发 settle。没有 pointer capture、`pointercancel` 或 `lostpointercapture` 收口，指针离开元素后可能丢失跟踪或结束事件。

2. **B2 — 无法保持抓取偏移和 1:1 跟踪。**  
   `startY` 在片段中记录后未使用，`event.clientY` 被直接当成 `sheet.style.top`。这既会把面板顶部吸到指针位置，也可能把 viewport 坐标错误地用于 offset-container 坐标；抓取点不会稳定留在手指下方。

3. **B3 — 动画管线主动制造跟手延迟和布局风险。**  
   `transition: all 300ms` 会让可动画的 `top` 写入不断从当前插值值重新追赶指针；同时拖拽和 WAAPI settle 都修改布局属性 `top`，`offsetTop` 读取还可能触发布局同步。实际卡顿/FPS 尚未测量，但这套属性与时序选择不满足直接操控合同。

4. **B4 — settle 不可中断，且 presentation state 没有统一所有者。**  
   `animating` 在约 `480ms` 内拒绝新的 `pointerdown`，违反“飞行途中可重新抓取”；但 `pointermove` 又没有同样的锁，状态互相矛盾。`fill: "forwards"` 将最终值留在动画 effect 层，代码没有提交最终样式、取消旧动画或从当前屏幕值继续，后续 inline `top` 与持久化 effect 可能竞争。

5. **B5 — 速度连续性和无障碍路径缺失。**  
   没有采样释放速度，也没有把速度交给 settle；`ease-in` 从接近零速度开始、向终点加速后突然停止，与手指释放速度不连续。提供证据中也没有 `prefers-reduced-motion` 分支；整张 sheet 的 `scale(0.96)` 加上 `300ms` broad transition，既不是即时反馈，也会扰动任务内容和抓取几何。

## 4. 八个具体设计动作

1. **Pointer-down 所有权与反馈**  
   只让明确的 drag handle 启动拖拽，记录主指针 `pointerId`、当前屏幕位置和 `grabOffsetY = pointerY - sheetY`。立即将 handle 的颜色、描边或 grip 强度切到 pressed 状态，最多 `100–120ms ease-out`；不要缩放整个 sheet。不要对可滚动内容整体设置 `touch-action: none`。

2. **建立显式状态机和 1:1 不变量**  
   使用 `idle → pending → dragging → settling`。在约 `8–12 CSS px` 意图阈值后进入 dragging、调用 `setPointerCapture`，只处理当前 `pointerId`；位置始终满足 `sheetY = pointerY - grabOffsetY`。用单一 `translate3d(0, y, 0)` motion value，拖拽期间关闭位置 transition，并完整处理 `pointerup`、`pointercancel` 和 `lostpointercapture`。

3. **从 presentation value 中断**  
   删除 `if (animating) return`。保留当前 settle animation/spring 的句柄；重新按下时读取当前屏幕 `y` 和当前速度，先以该值建立新抓取偏移，再取消旧动画。第一帧不得回跳到旧逻辑状态或旧 inline 值。若 press feedback 仍使用 `transform`，让 handle 内层和位移外层分别拥有 transform。

4. **测量并交接释放速度**  
   保存最近约 `80–120ms`、至少 `4–6` 个带 monotonic timestamp 的位置样本，计算 **CSS px/s** 的释放速度并对异常值限幅。目标选择完成后，把该速度作为 settle 的 initial velocity；若动画 API 要求相对速度，使用 `relativeVelocity = velocityPxPerSec / (targetY - currentY)` 并按 API 单位转换。速度交接和目标选择是两个独立决策。

5. **把 projected endpoint 作为需授权的产品语义**  
   在没有产品证据前，保留 `nearestSnapPoint(currentPresentationY)`；不能因为“更物理”就静默改变状态选择。若确认允许 flick/momentum，可从以下可审计起点试验：

   ```text
   delta = clamp((velocityPxPerSec / 1000) * 0.99 / (1 - 0.99),
                 -adjacentSnapGap, adjacentSnapGap)
   projectedY = clamp(currentY + delta, fullY, collapsedY)
   target = nearestSnapPoint(projectedY)
   ```

   `0.99/ms`、限幅和最多跨一个状态只是初始假设；应根据 trace 调整，并在当前状态附近加入约一个 snap gap 的 `10%` hysteresis，防止阈值抖动。

6. **使用连续的软边界**  
   在 `full` 和 `collapsed` 之外不要无限跟随，也不要硬截断。令 `overshoot` 为越界距离、`D` 为有效拖拽跨度，可从以下阻力函数开始：

   ```text
   resisted = (overshoot * D * 0.55) /
              (D + 0.55 * abs(overshoot))
   ```

   展示位置为 `boundary + resisted`；松手后回到合法端点。阻力必须单调、无断点，且不能改变最终状态语义。

7. **统一 settle 与最终状态提交**  
   用可读取位置和速度的 spring/motion primitive；calm utility 可从 damping ratio 约 `1.0`、response `0.28–0.35s` 开始，不做 bounce。只移动外层 transform，内部任务内容保持挂载且不缩放。完成后明确提交 canonical state、最终 transform 和可访问状态，再清除 animation effect；不要依赖永久 `fill: forwards`。

8. **设计独立的 Reduced Motion 路径**  
   读取 `matchMedia("(prefers-reduced-motion: reduce)")`。可以保留用户主动控制的边界内 1:1 拖动，但取消 rubber-band、overshoot 和大幅自动 settle；松手时直接提交目标位置，使用约 `80–120ms` 的 handle 颜色/状态文字 cross-fade 确认 `collapsed`、`half`、`full`。同时提供键盘可操作的离散状态控制，并在状态提交后更新可访问状态文本。

## 5. 已验证与未验证

**已由静态片段确认：**

- `pointerdown` 只在 `animating` 时提前返回；`startY` 在所示代码中没有后续用途。
- `pointermove` 无条件把 `clientY` 写入 `top`。
- `pointerup` 使用 `offsetTop` 选择最近 snap，并启动 `480ms ease-in`、`fill: forwards` 的 WAAPI 动画。
- CSS 声明了 `transition: all 300ms` 和整张 sheet 的 `scale(0.96)`。
- 提供代码中未出现 active-pointer 状态、capture/cancel、速度采样、presentation-value interruption 或 Reduced Motion 分支。

**尚未验证：**

- 完整组件中是否另有事件门禁、touch-action、状态管理或 Reduced Motion 补偿代码。
- `position`、offset parent、transform origin、computed transition 及 snap-point 的实际坐标系。
- 浏览器中的真实跳变、跟手误差、动画优先级、强制布局、FPS、掉帧或输入延迟。
- sheet 内部滚动与拖拽之间的手势仲裁。
- 用户是否期望 flick 跳转、是否允许跨越一个以上状态，以及 nearest/current 与 projected endpoint 哪个更符合产品语义。
- 不同 viewport、浏览器、60/120Hz 触控设备和真实 Reduced Motion 的表现。

## 6. 实现批准前的最小验证计划

1. 在一个受支持的桌面 Chromium 浏览器中记录 `pointerY`、presentation `sheetY`、grab offset、速度、projected endpoint 和最终 target，同时采集 Performance trace；覆盖无移动点击、慢拖和三个状态间双向拖拽。
2. 验收 1:1：越过阈值后，除软边界区外 `sheetY - pointerY` 应保持常量，建议逐帧误差不超过 `2 CSS px`；gesture handler 中不得出现每帧强制同步布局。
3. 在 settle 的约 `25% / 50% / 75%` 处重新抓取并立即反向；同时测试移出 handle 后释放、`pointercancel`、窗口失焦、第二根手指。要求视觉跳变不超过约 `2 CSS px`、无卡死状态、无旧 animation effect 残留。
4. 从每个 snap 两侧以慢速和快速释放，验证“当前位置最近点”或已授权的 projection 规则；确认 hysteresis 不抖动、projection 有界、未经授权时不会跨越多个状态。
5. 在边界外缓慢和快速拖动，逐帧确认阻力连续、单调，释放后稳定回到合法 snap；内部滚动内容不得被手柄之外的区域无条件劫持。
6. 在窄/宽 viewport、resize/orientation change 后复测 snap；开启系统 Reduced Motion，确认没有大幅自主位移、弹性或整面板缩放，同时状态文字、视觉反馈和键盘控制仍然明确。
7. 最少设备覆盖为桌面 mouse/trackpad 加一个真实受支持的触控设备；若产品实际覆盖 60Hz 与 120Hz，应各测一台，并按真实支持矩阵补 WebKit/Chromium。保存 trace 和慢动作视频作为批准证据。

以上均为**待执行验证计划**；本轮没有进行浏览器、响应式或真实设备验证，也没有修改文件。