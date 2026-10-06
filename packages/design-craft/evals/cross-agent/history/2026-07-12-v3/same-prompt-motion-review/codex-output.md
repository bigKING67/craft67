## 1. 证据级别与设计解读

- **使用模式**：`design-craft / critique`，只读动效与交互物理审查。
- **证据级别**：仅有静态源码证据。可以确认事件处理路径、显式 CSS/WAAPI 参数以及片段中缺失的分支；不能证明实际延迟、掉帧、触摸手感、浏览器合成行为或响应式表现。
- **Design read**：这是一个供运营人员全天高频使用的 Web 工作面板，气质应克制、稳定、可预测；动效只用于保持拖拽因果、当前位置与三档状态之间的连续性。
- **结论：Block。** Sheet 的位移动效有存在理由，但当前实现不应进入实现批准阶段。问题不只是“参数不够顺滑”，而是直接操控、动画所有权、中断和无障碍合同均未成立。

## 2. 哪些 motion 应存在

**应保留：**

- Pointer-down 时，drag handle 上立即出现轻量反馈。
- 拖拽过程中，sheet 由用户输入直接驱动；这是 **1:1 movement，不是带 easing 的动画**。
- 松手后，从当前屏幕位置和释放速度开始，短促、可中断地落到合法 snap point。
- 超过 `full` / `collapsed` 边界时，可有有限阻力，用于说明“已经到边界”。
- 状态落定后，应明确反馈 `collapsed`、`half` 或 `full`。

**不应动画：**

- Pointermove 驱动的位置不能经过 `transition`。
- 不应使用 `transition: all`。
- 不应在高频路径上动画 `top`。
- 不应把整个内容丰富的 sheet 缩放到 `0.96`；这会让任务上下文一起晃动。
- Settling 期间不应锁死重新抓取。
- Reduced Motion 下不应保留长距离自动滑行、惯性拖尾或弹性 overshoot。

## 3. 阻塞性发现，按优先级排序

### B1 — 当前不是有效的直接操控

- `pointermove` 没有检查 active drag；光标只要在 sheet 上移动，就可能执行 `sheet.style.top = ...`。
- `startY` 被记录但完全未使用。
- `event.clientY` 被直接当作 `top`，没有 `startSheetY` 或 grab offset；第一次移动可能把 sheet 顶边跳到指针位置。
- 未见 `pointerId`、pointer capture、`pointercancel` 或 `lostpointercapture`。
- `clientY` 是 viewport 坐标，而 `top` 的参考坐标取决于 containing block；两者是否一致尚未建立。

这破坏“物体始终黏在手指下面”的基本因果关系，并可能影响 sheet 内部原有的点击、选择和滚动任务。

### B2 — CSS 与 WAAPI 同时争夺位置，且位于 layout 热路径

- `transition: all 300ms` 会尝试过渡每次 pointermove 写入的 `top`，从机制上制造拖尾，而不是 1:1 tracking。
- WAAPI 同样动画 `top`；这是 layout/paint 风险，而不是稳定的 compositor transform 路径。
- `fill: "forwards"` 完成后没有提交并释放动画所有权；持续存在的 animation effect 可能与下一次 inline `top` 写入冲突。
- `.finished` 只翻转布尔值，没有提交最终逻辑位置或清理动画实例。

实际是否表现为卡顿、第二次拖动冻结或样式竞争仍需运行态验证，但源码中的所有权冲突已经成立。

### B3 — 中断模型自相矛盾

- Settling 时，`pointerdown` 被 `animating` 拒绝，因此用户不能在运动途中重新抓住 sheet。
- 但 `pointermove` 和 `pointerup` 没有同样的 guard；所谓 lockout 并不完整。
- 未见从当前屏幕 presentation value 开始的取消/重定向。
- 连续 `pointerup` 可能创建重叠动画，而较早的 `.finished` 回调可能提前把 `animating` 设回 `false`。

直接操控对象必须能随时被重新接管，而不是等待固定动画结束。

### B4 — Release physics 与手势输入脱节

- 固定 `480ms` 对全天高频操作偏慢。
- `ease-in` 在起点最慢，用户松手后会先看到迟疑，再看到加速；这与释放速度的因果方向相反。
- 未记录位置时间序列，也没有 CSS px/s 的 release velocity。
- Settling 从零速度启动，无法继承快速 flick 或缓慢放手的差异。
- `nearestSnapPoint(sheet.offsetTop)` 只使用松手位置。是否应改成 momentum-based target 尚无产品证据，不能直接替换，但至少应测量并传递速度。

### B5 — Pointer-down 反馈和 Reduced Motion 均不合格

- `scale(0.96)` 作用于整个 sheet，幅度对大型运营面板过大，会让内容、文字和任务上下文一起收缩。
- 未见 `prefers-reduced-motion` 分支。
- 未见落定后的显式状态反馈；减少空间运动后，用户可能更难确认最终落在哪一档。
- 未见 press feedback 与 positional transform 的独立所有权设计。

## 4. 八项具体设计动作

| # | 设计动作 | 具体合同 |
|---|---|---|
| 1 | **局部 pointer-down 反馈** | 只让 drag handle/header 立即改变颜色、粗细或明暗，并切换 `cursor: grabbing`；响应约 `80–120ms`。移除整张 sheet 的 `scale(0.96)`。若保留 scale，只作用于独立 handle 层且控制在约 `0.97–0.99`。 |
| 2 | **建立真实的 1:1 tracking** | 记录 `activePointerId`、`startPointerY`、`startPresentationY`；位置计算为 `startPresentationY + (clientY - startPointerY)`，而不是直接使用 `clientY`。通过专用 handle 启动，排除按钮、输入框和可滚动内容。 |
| 3 | **明确唯一位置所有者** | 使用外层 position wrapper 独占 `translateY(...)`；handle 子层独占 press feedback。删除 positional `transition`、`transition: all` 和逐帧 `top` 更新。坐标转换和几何读取在 pointerdown 时完成，pointermove 热路径只写 transform。 |
| 4 | **支持 presentation-value interruption** | Settling 过程中再次 pointerdown 时，读取当前屏幕 `y` 和当前速度，停止旧 controller，并从该位置无跳变进入 drag；不要用 `animating` 拒绝输入。Settling 完成后提交逻辑状态并释放动画所有权，不能留下永久 `fill: forwards` effect。 |
| 5 | **测量并交接 velocity** | 保存最近约 `80–120ms` 的位置与单调时间戳，用多个样本计算 release velocity，单位明确为 CSS px/s；对异常速度限幅。用接近临界阻尼的可中断 spring 接收初速度，建议从 damping ratio `1.0`、response `0.24–0.30s`、无可见 bounce 开始实测。 |
| 6 | **把 projected endpoint 作为有条件的产品决定** | 候选计算可为 `projection = (v / 1000) * 0.99 / (1 - 0.99)`，再令 `projectedY = currentY + projection`；endpoint 必须限制在合法边界，并建议最多跨一个 snap interval，除非产品明确允许 `collapsed ↔ full` flick。只有确认“快速甩动应改变目标档位”后，才用它选择 snap；否则继续使用当前 nearest-position 规则，但 settling 仍继承 velocity。 |
| 7 | **增加 intent threshold 与 soft boundaries** | 移动约 `8–12 CSS px` 后才确认 drag，并执行 `setPointerCapture(pointerId)`；处理 `pointercancel`、`lostpointercapture` 和额外触点。超过 `full`/`collapsed` 时使用渐进阻力，例如以 `0.55` 为初始 rubber-band constant，而不是无限移动或突然硬停；half 是 snap point，不是物理边界。 |
| 8 | **设计 Reduced Motion 等价路径** | 用户主动拖动仍保持 1:1，因为它由用户直接控制；松手后的自动 travel 改为立即落定或最多约 `80–120ms` 的无 overshoot settle。保持相同 target-selection 语义，通过 handle 颜色、边缘强调、静态状态文本及相应 ARIA 状态反馈 `collapsed/half/full`，而不是依靠长距离滑行来表达状态。 |

补充：drag handle 的 `touch-action` 必须与页面滚动合同共同决定。通常只在 handle 上阻止浏览器接管纵向手势，不能粗暴地让整个 sheet 内容失去正常滚动。

## 5. 已验证与未验证

### 由给定源码可以确认

- `startY` 在片段中未被使用。
- `pointermove` 没有 active-drag guard。
- Pointer 位置被直接写为 `top`。
- 未见 pointer capture、pointer ID、intent threshold、cancel cleanup 或 velocity history。
- Settling 使用 `top`、`480ms`、`ease-in` 和 `fill: forwards`。
- `animating` 只阻止 `pointerdown`。
- CSS 使用 `transition: all 300ms` 和整张 sheet 的 `scale(0.96)`。
- 未见 Reduced Motion 分支。

### 尚未验证，不能当作事实宣称

- 第一次拖动的实际跳变距离。
- `transition: all` 造成的可感知跟手延迟程度。
- `top` 动画是否在目标设备上掉帧、layout thrash 或产生明显 paint。
- `fill: forwards` 是否在目标浏览器中具体表现为下一次 drag 被遮蔽。
- Containing block、scroll offset、snap point 几何及响应式安全范围。
- Sheet 内容滚动与拖动手势如何竞争。
- 产品是否希望 quick flick 改变目标状态，或始终按松手位置选择。
- 60/120 Hz、鼠标、触控板及真实触屏上的实际手感。
- Reduced Motion 下的实际表现。

## 6. 实现批准前的最小浏览器／设备验证计划

1. **桌面主支持浏览器，60 Hz**
   - 测试无按键 hover、从 handle 不同高度抓取、慢拖、快速 flick、方向反转、越界、移出元素后释放。
   - 记录 `pointerY`、presentation `y`、velocity CSS px/s、projected endpoint、chosen target。
   - 验收：未按下绝不移动；越过 threshold 后无初始跳变，sheet delta 与 pointer delta 1:1，误差不出现持续累积。

2. **中断专项**
   - 在 `collapsed→half`、`half→full` 运动的约 25%、50%、75% 位置重新抓取。
   - 验收：没有可见跳跃，没有等待旧动画结束，没有残留 animation effect，释放后只有一个有效 settle controller。

3. **目标选择与边界**
   - 对同一松手位置分别进行慢速释放和双向快速 flick。
   - 明确验证 nearest-position 与 projected-target 两套候选；由产品合同决定采用哪一套。
   - 验收：日志中的单位、限幅、projection、最终状态可解释；越界阻力连续且不会进入非法位置。

4. **Reduced Motion 与窄视口**
   - 打开系统或浏览器 Reduced Motion，覆盖三档状态、重新抓取、快速释放和边界。
   - 验收：功能结果与普通模式一致；无长距离自主滑行或 overshoot；最终状态仍通过非空间反馈清楚可辨。
   - 同时检查窄视口、动态 viewport 高度及内容滚动交接。

5. **真实触屏与性能**
   - 至少使用一台真实 touch device；理想最小组合是桌面 60 Hz 加一台 120 Hz 触屏设备。
   - 在代表性运营数据负载下录制 Performance/frame timeline。
   - 验收：pointer capture、页面滚动竞争和取消路径正确；拖动帧内没有重复 layout read/write；position 主要由 compositor-friendly transform 驱动。

交互批准证据应至少包含短视频或 pointer/frame trace；单张截图不能证明 gesture physics。此次未编辑任何文件，也未执行浏览器、响应式或真实设备验证。