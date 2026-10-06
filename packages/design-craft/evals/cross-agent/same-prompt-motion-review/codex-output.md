结论：**暂不批准实现。** 动效有必要，但只应服务于因果关系与直接操控。当前静态代码已暴露出手势所有权、1:1 跟手、可中断性和 Reduced Motion 合同缺口；实际是否“卡顿”或“手感差”仍未经过运行态验证。

## 1. 证据级别与设计读法

- **证据级别：静态源码级。** 可确认事件绑定、属性选择、时长、缓动及缺失分支；不能确认帧率、实际延迟、触摸手感、响应式几何或浏览器动画叠加结果。
- **设计读法：**这是高频 Web 运营工作台里的任务上下文容器，气质应平静、克制、工具化，以连续直接操控、可预测停靠和不中断任务为第一优先。
- **评审状态：`BLOCK / incomplete`。** 不是因为已经观察到运行态失败，而是源码中的交互合同本身尚不成立。

## 2. 哪些动效应该存在

应该存在：

- Pointer-down 的即时、轻量反馈。
- 用户控制的 1:1 拖动；这属于直接操控，不是补间动画。
- 松手后到合法 snap point 的短促、可中断 settle。
- 越界时轻微阻力，以及状态已经落在 `collapsed / half / full` 的明确反馈。

不应动画化：

- 拖动中的每一次位置更新，不应套 CSS transition。
- 不应动画化 `top` 等布局属性，也不应使用 `transition: all`。
- 不应把整张 sheet 缩放到 `0.96`；任务内容、滚动位置和内部控件应保持稳定。
- 不应以固定 480ms 锁住下一次输入，也不需要装饰性弹跳。
- Reduced Motion 下不应保留大距离自动滑行、橡皮筋或整面缩放。

## 3. 阻断项

- **B1 — P0，手势所有权缺失。** `pointermove`、`pointerup` 没有 active-drag 或 pointer-ID 守卫；`startY` 在所示代码中未使用；位置直接设为 `clientY`。因此该路径允许没有合法 pointer-down 的移动或松手改变 sheet，首次移动也不会保留抓取偏移。

- **B2 — P1，1:1 跟手合同被破坏。** `transition: all 300ms` 覆盖 `top` 和 `transform`；连续写入 `top` 会成为可补间的布局更新，而非指针与 sheet 的等量位移。源码证明存在该结构风险，但实际拖尾幅度和掉帧情况未验证。

- **B3 — P1，settle 不可中断。** `animating` 在 480ms 内拒绝新的 pointer-down；代码没有从当前屏幕 presentation value 接管，也没有携带当前速度。`fill: "forwards"` 后未显式提交最终状态并取消动画，未来底层样式写入与动画效果的所有权也不清晰。

- **B4 — P1，释放物理与输入不连续。** settle 使用固定 `480ms + ease-in`，开始阶段推进较慢，并从零速度重新启动。代码没有速度采样或 velocity handoff。`nearestSnapPoint(current)` 可以是合法产品规则；是否改成 projected endpoint 属于单独的行为决策，不能作为“润色”静默替换。

- **B5 — P1，反馈与无障碍方向不符。** 整张 sheet 的 `scale(0.96)` 会移动视觉锚点、压缩任务内容，并受 300ms broad transition 影响。所给证据中没有 `prefers-reduced-motion` 分支，无法满足“保留状态反馈但移除大空间位移”的要求。

## 4. 八个具体设计动作

1. **Pointer-down 反馈：**只反馈 drag handle，例如立即切换 handle 颜色/粗细、`cursor: grabbing`，或对 handle 做约 `0.98` 的轻微压感；建议 `80–140ms`，不要缩放整张 sheet。

2. **建立合法拖动：**记录 active pointer ID，约 `8–12px` 意图阈值后进入 drag，调用 pointer capture；保存 `grabOffset = pointerY - presentationY`，之后仅处理该 pointer。把 `touch-action` 限定在 handle，避免破坏 sheet 内部滚动内容。

3. **恢复 1:1 跟手：**固定 sheet 的布局锚点，以 `translate3d(0, y, 0)` 表达三个状态；drag active 时关闭位置 transition，每帧令 `ΔsheetY = ΔpointerY`。位移层与 handle 压感层分开，避免两个行为争用同一 `transform`。

4. **按 presentation value 中断：**移除 `animating` 输入锁。重新抓取时读取受控 motion value 的当前屏幕位置与速度，取消旧 settle，并以该位置作为新 drag 原点；结束时提交逻辑状态并清理旧动画，`pointercancel`/取消路径也必须收口。

5. **Velocity handoff：**保存最近约 `80–120ms` 的位置与单调时间戳样本，以 CSS px/s 计算并限幅 `vY`；settle 从当前 presentation position 和该初速度开始，不从零速度重新播放。

6. **Projected endpoint：**仅当产品确认“快速甩动可改变目标状态”时启用。可从  
   `projectedY = clamp(currentY + (vY / 1000) × d / (1-d), fullY, collapsedY)`  
   开始试验，`d≈0.99` 作为偏利落的初值，再选最近 snap point。若仍采用位置语义，则保留 `nearest(currentY)`，但 settle 仍应继承速度。

7. **软边界与 settle：**在 `full`/`collapsed` 外使用递增阻力而非立即硬停；可从 rubber-band 常数约 `0.55` 开始。合法区间内采用近临界阻尼、约 `0.3s` 响应的 settle，不制造装饰性 bounce，最终参数由真实触摸证据校准。

8. **Reduced Motion：**保留用户直接控制的 1:1 拖动；越界改为直接限制，松手后对同一目标立即或近乎立即提交，不播放大距离 spring、弹性或整面 scale。用 handle/chevron、scrim 色值、静态状态文字及语义状态更新表明 `collapsed / half / full`。

## 5. 已验证与未验证

**静态代码已验证：**

- `pointermove` 和 `pointerup` 没有合法拖动守卫。
- `clientY` 被直接写入 `top`，所示 `startY` 未参与计算。
- settle 为固定 480ms、`ease-in`、`fill: forwards`，并在完成前锁住 pointer-down。
- CSS 使用 `transition: all 300ms` 和整面 `scale(0.96)`。
- 所给代码没有展示 pointer capture、grab offset、velocity、projection、soft boundary、取消路径或 Reduced Motion 分支。

**未验证：**

- 实际视觉跳跃、拖尾、卡顿、帧率和强制布局成本。
- CSS transition 与 WAAPI 在目标浏览器中的最终 presentation-value 行为。
- snap point 几何、响应式安全区、内部滚动与页面滚动冲突。
- 速度阈值、投影语义和三个目标状态是否符合既有产品合同。
- Reduced Motion、键盘替代、触摸设备、60/120Hz 及任务上下文保持情况。

## 6. 实现批准前的最小验证计划

1. 在代表性桌面 Chromium、真实业务内容下覆盖三个状态及双向拖动；确认首次移动无跳跃、指针离开 handle 后仍持续跟踪、内部焦点/滚动/表单值不丢失。

2. 记录 `pointerY`、presentation `sheetY`、时间、release velocity、projected endpoint 和最终 target；覆盖慢拖、短拖、快速甩动、反向、边界越界、`pointercancel`、额外触点和 settle 中重新抓取。

3. 用 Performance trace 检查代表性高负载页面：拖动热路径不应重复触发由位置更新造成的 Layout，且 presentation delta 应在意图阈值后与 pointer delta 等量；不要仅凭肉眼或截图判断。

4. 开启系统/浏览器 Reduced Motion 重跑同一状态矩阵：目标状态语义一致，但没有大距离自动滑行、弹性或整面缩放；状态仍能从视觉和语义反馈中辨认。

5. 至少在一台真实触摸设备上验证窄视口、浏览器安全区、页面滚动与 sheet 内滚动仲裁，以及 settle 中重新抓取。截图不是决定性证据；最小交付证据应包含短录屏、输入/位置 trace、Performance trace 和 Reduced Motion 结果。

路线记录：`L1-F / normal / web`；实际使用 `design-craft` 的 motion、interaction-physics 与 validation 合同。路由 preflight 返回 `RUNTIME_ERROR`，实际 browser lifecycle 为 `not_started`；未改文件、未运行浏览器或设备、未生成截图/录屏/trace artifact。