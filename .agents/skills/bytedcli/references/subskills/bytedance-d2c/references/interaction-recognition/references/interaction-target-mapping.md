# Interaction Target Mapping

本文是 `Interaction` IR class 到各 target 组件的选择指引。组件选择打分以 `packages/aiden-d2c/src/modules/shotEval/componentSelection.ts` 为代码 SOT；组件用法正确性以 `packages/aiden-d2c/src/modules/shotEval/usageContracts.ts` 为代码 SOT。本文只做索引，不复述具体契约规则，也不注入 interaction recognition prompt。

## Lynx

| IR class | Lynx 组件选择指引 | 打分/用法 SOT |
|---|---|---|
| `SCROLL` | `ScrollView` / `List` / `FeedList` / `scroll-view` / `list` | `componentSelection.ts` 类映射；`usageContracts.ts` 边界契约 |
| `PAGED` | `Swiper` / `SwiperItem` / `ViewPager` / `x-viewpager-ng` | `componentSelection.ts` 类映射 |
| `TABBED` | `Tabs` / `TabBar` / `TabGroup` | `componentSelection.ts` 类映射 |
| `INPUT` | `Input` / `x-input-ng` / `input` / `textarea` | `componentSelection.ts` 类映射 |
| `ACTION` | `Button` / `button` | `componentSelection.ts` 类映射；`usageContracts.ts` 用法契约 |
| `OVERLAY` | `Popup` / `Sheet` / `Popover` / `DialogRoot` / `Dialog*` / `x-overlay-ng` | `componentSelection.ts` 类映射；`usageContracts.ts` 用法契约 |
| `FOLD` | `FoldView` | `componentSelection.ts` 类映射 |

## Browser (h5 / web)

| IR class | Browser 组件/DOM 选择指引 | 说明 |
|---|---|---|
| `SCROLL` | `div` / `section` with `overflow: auto|scroll`，或数据驱动的 repeated card/row group | 保留真实滚动容器和重复数据结构，不要只生成静态截断内容 |
| `PAGED` | carousel/pager 组件；无组件时用 React state 或 CSS scroll-snap 表达单页切换 | 分页区域应有 peer pages，不要退化成普通横向静态排布 |
| `TABBED` | tablist buttons + active panel；可用业务 Tabs 组件时优先使用 | 互斥标题和内容面板必须保持绑定关系 |
| `INPUT` | `input` / `textarea` / 业务输入组件 | 不要用 `div` + placeholder 文本伪装可输入区域 |
| `ACTION` | `button` / 业务 Button 组件 | 主命令必须是可点击语义节点，不要只用静态文本 |
| `OVERLAY` | modal/dialog/sheet/popover 组件；无组件时用 fixed overlay + panel 结构 | 设计中已打开的弹层要保留独立层级和遮挡关系 |
| `FOLD` | collapse/fold 组件；无组件时用 button + controlled content region | 仅在识别结果明确为折叠展开语义时使用 |
