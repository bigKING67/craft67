# Bottom Sheet 手势动效评审

**评审结论：Block。**
当前实现不应进入实现审批或发布阶段。问题不是“动效不够精致”，而是直接操控、可中断性、吸附物理、Reduced Motion 和输入状态管理均不成立。应保留因果性动效，但重做交互模型。

## 1. 证据等级与设计判断

- **使用方式：**`design-craft` 的只读 `critique` 模式。
- **证据等级：**仅静态源码证据。
- **静态结论置信度：**高，可确认当前代码缺少哪些机制以及使用了哪些不合适的属性。
- **体验结论置信度：**未验证；没有 pointer trace、computed style、frame timeline、Reduced Motion、响应式或真实触屏设备证据。
- **设计判断：**

> Reading this as: 一个供运营人员每天高频使用的 Web 底部操作面板，以克制、稳定的工具感为主，优化目标是在 `collapsed`、`half`、`full` 三个状态间直接操控，同时保持内容、焦点和任务上下文连续。

这里的动效只应承担三件事：

1. 立即确认用户已经抓住面板。
2. 让面板持续贴合手指或指针。
3. 在释放后解释面板为什么落到某个稳定状态。

不应加入装饰性缩放、明显弹跳、迟缓启动或不可中断的固定时长表演。

---

## 2. 哪些动效应该存在，哪些不应动画

### 应保留

- Pointer-down 时对**拖拽手柄**的即时反馈。
- 拖动期间完全由用户驱动的 1:1 位移；这属于直接操控，不是定时动画。
- Pointer-up 后到目标 snap point 的短促、可中断、带释放速度的 settling。
- 到达 `collapsed`、`half`、`full` 后的轻量状态确认，例如手柄颜色、状态文本或遮罩强度变化。
- 用户在 settling 途中重新抓取时，从当前屏幕位置继续。

### 应删除或禁止

- `.sheet { transition: all 300ms; }`
- 拖动期间对 `top` 进行 CSS transition。
- 使用 `top` 作为逐帧移动属性。
- 整个 sheet 的 `scale(0.96)` pointer-down 效果。
- 固定 `480ms ease-in` 的释放动画。
- 默认弹跳、抛物感、视差或内容层独立滑入。
- Sheet 内部任务内容、焦点和滚动位置因 detent 切换而重新动画、重挂载或重置。
- Reduced Motion 模式下的大距离自动滑行、弹性越界和 overshoot。

---

## 3. 优先级问题

### P0 — 拖拽输入模型当前不成立

静态代码表明：

- `pointermove` 没有检查是否已经发生 `pointerdown`。
- `startY` 被记录但从未使用。
- 没有保存 sheet 起始位置或 grab offset。
- `event.clientY` 是 viewport 坐标，却被直接写入 `top`。
- 没有跟踪 `pointerId`。
- 没有 `setPointerCapture()`。
- 没有处理 `pointercancel` 或 `lostpointercapture`。
- `pointerup` 仅监听在 sheet 本身；指针离开元素后释放可能无法被收到。

因此，在提供的代码范围内，普通 pointer move 就可能移动 sheet；真正拖动时，sheet 顶边也会跳到指针位置，而不是保持用户最初抓住的位置。

这违反直接操控的基本要求：

- 物体必须在越过意图阈值后贴合指针。
- 用户抓住哪里，那个抓取偏移就应保持在哪里。
- 指针离开原始元素边界后，拖动仍应继续。
- 只有最初的 active pointer 能驱动当前手势。

**审批影响：阻断。**

---

### P0 — `transition: all` 破坏 1:1 tracking

每次 `pointermove` 都更新 `top`，同时 `.sheet` 又对所有属性执行 `300ms` transition。结果在设计上必然是“指针已经走了，sheet 还在追赶”。

这不是平滑，而是输入延迟。直接操控阶段不能有 duration-based easing：

- Pointer delta 应直接对应 sheet delta。
- 拖动期间应关闭 transition。
- 阻尼只应出现在越过自然边界时，而不是整个合法拖动区间。
- `transition: all` 还会让未来任何无关属性变化被意外动画。

**审批影响：阻断。**

---

### P0 — Settling 不可中断，且逻辑值与 presentation value 可能分离

`animating` 阻止 settling 期间的新 `pointerdown`，但一个可抓取的 sheet 必须允许用户随时重新抓住。

当前实现还存在内部矛盾：

- `pointerdown` 在 `animating` 时被忽略。
- `pointermove` 却没有检查 `animating`，仍可能尝试写入 `top`。
- 没有保存 `Animation` 实例，无法明确 cancel 或 retarget。
- 没有读取当前屏幕上的 presentation value。
- 没有保存 settling 的当前速度。
- `fill: "forwards"` 保留完成后的 WAAPI effect，但没有把最终位置明确提交到持久状态并取消 effect。

这会产生一个高风险模型：逻辑上的 inline `top`、正在填充的 WAAPI effect 和屏幕实际位置可能不是同一个值。具体浏览器表现尚未实测，但当前代码没有安全的中断协议。

**正确原则：**

- Settling 中再次 pointer-down 时，立即读取当前可见位置与当前速度。
- 从这个 presentation value 开始新的 drag。
- 不应先跳回旧 snap point、旧 inline style 或旧逻辑 target。
- 不应等待动画完成后才允许交互。

**审批影响：阻断。**

---

### P0 — 吸附只看释放位置，不看手势意图

当前目标为：

```js
nearestSnapPoint(sheet.offsetTop)
```

它仅使用释放瞬间的位置，没有：

- 短时位置历史。
- Release velocity。
- Velocity handoff。
- Projected endpoint。
- 当前 detent 周围的 hysteresis。
- 高速 flick 与慢速拖动的区分。

直接结果是：

- 两次在同一点释放、但速度方向相反的手势会落到相同状态。
- 一个明确向 `full` 快速 flick 的动作，可能因为释放点稍靠近 `half` 而回到 `half`。
- 用户无法建立稳定的物理预期。

**审批影响：阻断。**

---

### P0 — 显式 Reduced Motion 要求没有对应路径

提供的代码中没有：

- `prefers-reduced-motion` 分支。
- 无弹性 settling 方案。
- 去除大距离自动位移的方案。
- 非空间状态反馈方案。

本产品上下文明确要求 Reduced Motion 保留状态反馈但避免大幅空间移动，因此这不是一般 polish 项，而是明确验收条件。

**审批影响：阻断。**

---

### P1 — `top` 是错误的手势热路径属性

拖动和 settling 都在动画 `top`：

```js
sheet.style.top = ...
sheet.animate([{ top: ... }, { top: ... }])
```

`top` 会参与布局。对大面积 sheet 高频更新时，存在 layout、paint 和主线程竞争风险；`offsetTop` 读取还可能在释放时触发同步样式或布局刷新。

正确方向是：

- 使用 compositor-friendly `transform: translate3d(0, y, 0)`。
- 在 pointer 事件中采样位置和时间。
- 每个 display frame 最多提交一次视觉更新。
- 避免在每帧路径中读取 layout geometry。
- 只在 pointer-down、尺寸变化或 snap point 重算时读取必要几何信息。

这里能静态确认的是属性选择不合适；实际掉帧程度仍需 performance trace。

---

### P1 — Pointer-down 反馈存在，但作用层级和幅度错误

```css
.sheet:active {
  transform: scale(0.96);
}
```

问题不是“没有 feedback”，而是 feedback 施加在整个 sheet 上：

- `0.96` 对大型操作面板是明显的几何收缩。
- Sheet 内所有任务内容都会一起缩放，削弱上下文稳定性。
- 它改变用户正在抓取对象的视觉几何。
- 如果 sheet 改用 `transform` 位移，位移与缩放会竞争同一个 transform 属性。
- 结合 `transition: all 300ms`，反馈启动和恢复都可能过慢。

Pointer-down 反馈应放在 drag handle 或 affordance 层，不应缩放整个工作表面。

---

### P1 — 缺少意图阈值、软边界和手势仲裁

当前实现没有：

- `8–12px` 起始意图阈值。
- 合法上下边界。
- 越界阻力。
- Detent hysteresis。
- 多指过滤。
- Sheet 拖动与内部内容滚动的仲裁。

对于可滚动的 `full` 状态，尤其需要明确：

- 从 drag handle 开始的垂直手势可直接拖 sheet。
- 从内容区域开始时，优先保留内容滚动。
- 只有内容已到顶部且用户继续向下拖动时，才考虑将控制权交给 sheet。
- 不应简单在整个 sheet 上使用会破坏内容滚动的全局手势拦截。

---

## 4. 建议的具体设计动作

### 4.1 Pointer-down feedback

将反馈限制在 drag handle：

- Pointer-down 当帧切换到 `grabbing` 状态。
- 手柄可以轻微加深颜色、提高不透明度或产生极小的局部压感。
- 若使用 scale，只缩放 handle，幅度约 `0.98–0.99`，时长约 `100–140ms`。
- Sheet 容器本身不缩放。
- 使用明确属性 transition，不使用 `transition: all`。
- 同时记录 active `pointerId`、当前 presentation position、pointer 起点和 grab offset。
- 如果 sheet 正在 settling，先中断 settling，再建立新的 drag 基线。

建议状态机：

```text
idle -> dragging -> settling
settling + pointerdown -> dragging
dragging + pointercancel -> settle-or-restore
```

不要再用无法表达中断和 ownership 的单一 `animating` boolean。

---

### 4.2 1:1 tracking

拖动开始后：

1. 设置一个约 `8–12px` 的意图阈值，阈值前仍允许它被识别为 tap。
2. 达到阈值后执行 pointer capture。
3. 保存用户实际抓取点，而不是把 sheet 顶边吸到指针下。
4. 只接受 active `pointerId`。
5. 每次 pointer event 更新位置样本；每个 display frame 最多渲染一次。
6. 合法范围内直接对应 pointer delta，不加 easing、transition 或延迟。
7. 使用 `transform: translate3d(...)`，不使用 `top`。
8. 在 `pointerup`、`pointercancel` 和 `lostpointercapture` 中统一清理状态。

概念关系应为：

```text
nextSheetPosition = pointerPosition - preservedGrabOffset
```

而不是：

```text
nextSheetTop = pointer.clientY
```

如果位移和其他 transform 确实都需要存在，应拆成外层 translation wrapper 和内层视觉反馈层，避免在同一个 `transform` 上互相覆盖。

---

### 4.3 Presentation-value interruption

Settling 必须允许重新抓取：

- 不锁住 pointer-down。
- 动画引擎应持续暴露 `currentPosition` 和 `currentVelocity`。
- 新 pointer-down 发生时，在同一视觉位置停止 settling。
- 新 drag 从当前 presentation position 开始，不从上一个 target 或旧 inline style 开始。
- 原 settling 速度可以作为初始手势状态保留，之后再由用户输入逐渐接管。
- 不产生一帧跳变。

如果继续使用 WAAPI，至少需要显式持有 animation、在中断时读取当前 computed/presentation transform、提交当前样式并 cancel。但 WAAPI 对动态速度继承并不自然；对这种可反复抓取的 sheet，维护独立 motion value 的 spring/rAF primitive 更适合。

---

### 4.4 Velocity handoff

不要根据最后一个 event 猜速度。应保留一个短时间窗口内的位置和时间样本，例如最近约 `60–100ms`：

```text
releaseVelocity = deltaPosition / deltaTime
```

要求：

- 速度方向与 sheet 坐标方向一致。
- 过滤明显过旧或异常的样本。
- 使用 coalesced pointer samples 时，采样与渲染分离。
- Release animation 从测得速度开始，而不是从零速度开始。
- 快速 flick 应比慢速拖动更容易进入相邻 detent。
- 默认无装饰性 bounce；运营工具更适合接近 critically damped 的 settling。

建议初始物理语言：

- damping ratio：接近 `1.0`。
- response：约 `0.25–0.35s`。
- 这是调参起点，不是未经设备验证的最终常量。
- 不使用固定 `480ms ease-in` 作为全部距离和全部速度的统一答案。

---

### 4.5 Projected endpoints

目标状态应根据预测终点选择，而不是只看当前释放位置：

```text
projection(v, d) = (v / 1000) * d / (1 - d)
projectedEndpoint = current + projection(releaseVelocity, d)
target = nearestSnapPoint(projectedEndpoint)
```

对于克制的三段式 sheet，可以从较短的投影开始，例如 `d ≈ 0.99`，然后实测调节；`0.998` 更接近长距离 scroll momentum，可能对本场景过强。

同时需要：

- 将 projected endpoint 限制在 `full...collapsed` 合法范围。
- 在当前 detent 周围增加 hysteresis，防止靠近中点时反复跳目标。
- 慢速释放更依赖位置。
- 明确高速 flick 更依赖速度和方向。
- 是否允许一次跨越两个 detent，应由产品规则决定；高频运营界面通常应要求更强的速度或位移承诺，避免误从 `collapsed` 直接冲到 `full`。

---

### 4.6 Soft boundaries

在 `full` 以上或 `collapsed` 以下继续拖动时，不应：

- 完全自由逃出范围。
- 突然硬停。
- 产生夸张弹簧。

应只对越界部分应用渐进阻力，例如：

```text
displayedOvershoot =
  (overshoot * dimension * 0.55) /
  (dimension + 0.55 * abs(overshoot))
```

其中 `0.55` 只是起点。合法区间仍保持 1:1；只有 overshoot 部分被压缩。

释放后：

- 回到最近合法边界。
- Calm utility 模式默认无明显 overshoot。
- Reduced Motion 下直接取消 rubber-band 和回弹表现。

---

### 4.7 Reduced Motion

建议把 Reduced Motion 分成两段处理：

#### 用户主动拖动期间

可以保留 1:1 tracking，因为位移由用户直接控制并具有明确因果关系，但应：

- 禁止弹性放大和 overshoot。
- 禁止 sheet 缩放、视差或内部内容跟随动画。
- 保持状态边界清晰。

#### 用户释放以后

避免 sheet 自动进行大距离 spring travel：

- 可以立即提交目标 detent。
- 或只允许极短、无 overshoot 的 settling；若距离较大，优先瞬时状态切换。
- 使用约 `80–120ms` 的非空间反馈确认状态，例如 handle 颜色、状态标签或遮罩变化。
- 保持焦点、内容滚动位置和任务状态不变。
- 用与控件语义匹配的可访问状态值表达 `Collapsed`、`Half`、`Full`。
- 提供键盘或离散按钮方式切换 detent，不能把拖拽作为唯一操作方式。

---

## 5. 已确认与未确认

### 静态源码已确认

| 结论 | 静态证据 |
|---|---|
| `pointermove` 未受 drag 状态保护 | Handler 中无 active-drag 条件 |
| Pointer hover 也可能触发位置写入 | `pointermove` 无 button、pointerId 或 dragging 检查 |
| Grab offset 未保留 | `startY` 未使用，sheet 起始位置未记录 |
| 使用了可能不匹配的坐标系 | `clientY` 直接赋给 `top` |
| 没有 pointer capture | 提供代码中没有 `setPointerCapture()` |
| 没有 cancel/lost-capture 清理 | 提供代码中没有对应 handler |
| Settling 期间没有合法的重新抓取路径 | `if (animating) return` |
| Settling 与 pointermove 状态规则互相矛盾 | 只有 `pointerdown` 检查 `animating` |
| Snap target 不考虑速度 | 只调用 `nearestSnapPoint(sheet.offsetTop)` |
| 没有 velocity history 或 projection | 提供代码中不存在相关状态或计算 |
| 使用固定、迟缓启动的 settling | `480ms`、`ease-in` |
| 使用 layout 属性移动 | Pointer tracking 和 WAAPI 都操作 `top` |
| 动画范围过宽 | `transition: all 300ms` |
| 整个 sheet 被明显缩放 | `.sheet:active { transform: scale(0.96) }` |
| 没有提供 Reduced Motion 分支 | 代码中无 `prefers-reduced-motion` 或等价条件 |
| WAAPI effect 未显式提交和取消 | `fill: "forwards"`，且未保存 animation 引用 |

### 尚未验证

以下内容不能从静态代码宣称成立或失败：

- 实际视觉跳变的具体像素量。
- CSS transition、WAAPI 和其他未提供样式之间的最终 cascade 行为。
- Sheet 的 offset containing block，以及 `clientY` 与 `top` 的实际偏差。
- 真实 pointer latency、帧率、掉帧和 layout cost。
- 60 Hz 与 120 Hz 下的手感。
- 鼠标、触控笔和真实触屏的差异。
- 浏览器原生滚动与 sheet 手势是否冲突。
- 快速 flick、慢速释放和反向中断的实际结果。
- Soft boundary 的最终阻尼参数。
- Reduced Motion 下的实际体验。
- `collapsed`、`half`、`full` 的真实尺寸与响应式位置。
- Detent 变化后焦点、内部滚动位置和任务上下文是否保留。
- 屏幕阅读器和键盘操作语义。
- 任何浏览器、设备、截图、视频或 performance trace 结果。

---

## 6. 实现审批前的最小浏览器与设备验证计划

### 最小环境

1. **主支持桌面浏览器**
   - 正常桌面 viewport。
   - 一个窄 viewport。
   - 使用 mouse；若产品支持 pen，再增加 pen。
2. **至少一台真实触屏设备**
   - 使用产品主支持的移动浏览器。
   - 至少覆盖一台 60 Hz 设备。
   - 如果 120 Hz 设备属于正式支持范围或高占比用户设备，再补一次 120 Hz 验证。
3. **Reduced Motion**
   - 在操作系统或浏览器层启用真实 `prefers-reduced-motion: reduce`。
   - 不能只通过临时 CSS 修改模拟最终结果。

### 必测手势

| 场景 | 通过条件 |
|---|---|
| 未 pointer-down 时移动鼠标 | Sheet 完全不移动 |
| 从 handle 左、中、右及不同纵向位置抓取 | 无首次跳变，grab offset 保持 |
| 越过意图阈值前释放 | 仍可作为 tap，不误启动 drag |
| 指针拖出 sheet 边界后释放 | Pointer capture 保持，状态正常结束 |
| 慢速拖到两个 detent 中间 | Hysteresis 稳定，不来回抖动 |
| 快速向上、向下 flick | Target 体现速度方向和 projected endpoint |
| Settling 进行到约 25%、50%、75% 时重新抓取并反向 | 从当前画面位置继续，无视觉跳回、无输入锁 |
| 超过 `full` 或 `collapsed` 边界 | 只有 overshoot 部分出现渐进阻力 |
| 在 `full` 状态滚动内部内容 | 内容滚动与 sheet drag 仲裁明确，不互相抢夺 |
| `pointercancel`、窗口失焦或 capture 丢失 | 手势状态可恢复，不遗留 dragging/animating 状态 |
| Detent 切换 | 焦点、内部滚动位置和任务上下文保持 |
| Reduced Motion | 无大距离自动滑行、弹性或整面缩放；状态仍清楚可辨 |
| 键盘切换 detent | 可到达三个状态，焦点可见且状态可感知 |

### 性能验证

录制一次真实 drag、release 和 interruption 的 Performance trace，确认：

- Pointer hot path 使用 transform，而不是连续动画 `top`。
- 每个 display frame 最多提交一次视觉更新。
- Pointer move 期间没有重复同步 layout measurement。
- 没有由 `transition: all` 引起的额外属性动画。
- 数据视图正常工作负载下没有明显长任务阻塞手势。
- Settling 中重新抓取不会触发整棵内容树重排或重挂载。

### 审批证据

动效不能只靠静态截图审批。最小证据应包含：

- 一段正常动效的 screen recording。
- 一段 Reduced Motion recording。
- 一次包含 drag、release、重新抓取的 performance trace。
- Pointer position 与 sheet presentation position 的简短采样记录，用于确认合法区间内接近 1:1。
- 测试浏览器、设备、操作系统和刷新率记录。

在这些检查完成前，可以确认当前静态实现需要重构，但不能确认新的手势“手感正确”或“运行流畅”。