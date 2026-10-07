# Interaction Recognition Playbook

本文是给 LLM 使用和持续维护的交互识别决策手册，适用于后续任意 Figma URL。目标是把人工校正中发现的误判沉淀为可复用规则，使下次遇到同类型交互时能更准确地产出 `interaction-inventory.json`。

文末只保留少量边界样例。样例用于帮助 LLM 理解规则适用边界，不作为全量 case 记录。

## 输入证据

1. Figma 预览图是视觉交互事实来源，用于判断弹层、截断、重复项、位置和主要按钮。
2. Figma JSON 是结构事实来源；`skeleton.html` / `skeleton.rpx.html` 是从 Figma JSON 压缩出的 HTML-like 骨架，用于快速确认 `impl-*`、`overflow-*`、`VirtualList`、`TabBar`、`Dialog`、`input` 等语义。
3. `components` 只能作为候选信号，不能单独决定 `location` 或 `confidence:"high"`。
4. `description` 只用于理解业务语境，不作为交互真值。

## LLM 识别流程

1. 通过 Aiden 提供的 Figma 数据服务准备设计证据。输出目录至少应包含：

- `screenshot.png` 或等价预览图。
- `origin.json`。
- `skeleton.html` 或 `skeleton.rpx.html`。
- `regions-visual.json`、区域 crop 和 region Figma JSON（如果已完成视觉切分）。

2. 先按截图从大到小扫描：Z 轴弹层、固定/吸顶/吸底区域、垂直滚动、横向滚动、分页/轮播、tab、输入区、主要按钮。
3. 再用 Figma JSON 和 skeleton 复核：查 `impl-role`、`impl-web`、`impl-behavior`、节点名、`overflow-y/overflow-x`、`VirtualList`、`ScrollView`、`List`、`TabBar`、`Dialog`、`Button`、`Input`。
4. 只把现行 schema 能表达、且会影响组件选择退化风险的交互写入 `interactions`。
5. 不确定项保留 `confidence:"low"` 或不入库；人工确认后再改为 `high`。
6. 如果截图与结构数据冲突，优先相信截图的交互边界和位置，优先相信 Figma JSON / skeleton 的组件语义。典型例子：截图显示底部半屏弹层，即使组件清单只有 `Slider`，也应标 `OVERLAY`。

## Schema 约定

```json
{
  "class": "SCROLL | PAGED | TABBED | INPUT | ACTION | OVERLAY | FOLD",
  "location": "top | mid | bottom | center | left | right",
  "count": 1,
  "repeated": true,
  "minRepeat": 3,
  "confidence": "high | low"
}
```

`count` 用于叶子控件数量，例如 `INPUT`、`ACTION`。`repeated/minRepeat` 只用于重复内容滚动区域。非重复长内容、被截断弹层正文、说明面板滚动，只标 `SCROLL`，不写 `repeated/minRepeat`。

## Class 判定表

| class | 何时标注 | 强证据 | 不应标注 |
|---|---|---|---|
| `OVERLAY` | 弹窗、半屏面板、抽屉、popover、sheet、dialog | 背景被遮挡或变暗；面板有独立层级；结构数据有 `dialog/modal` | 普通页面卡片 |
| `SCROLL` | 自由滚动容器，包括列表、feed、可滚动正文、被截断面板内容 | 内容被上下/左右裁切；结构数据有 `overflow`、`ScrollView`、`List`、`VirtualList` | 完整展示的普通列表布局；固定数量且无截断的指标卡/任务块 |
| `PAGED` | 分页、轮播、吸附翻页 | 结构数据有 `Swiper/ViewPager` 或 `pageControl`；截图有分页点/单页卡片轮播 | 普通横滑标签或自由滚动列表 |
| `TABBED` | tab、分段切换、tablist/tabbar | 多个互斥标签控制内容面板；结构数据有 `TabBar/TabItem/Tabs` | 筛选 chip、快捷问题、普通横向菜单 |
| `INPUT` | 输入框、搜索框、textarea | 可输入区域；结构数据有 `input/textarea` 或 `impl-role="input"` | 只展示占位样式的静态文本 |
| `ACTION` | 主要命令按钮 | CTA、提交、发送、确认、取消、接受、拒绝等；结构数据有 `Button/button` | 所有可点图标、列表项点击区、普通文本入口 |
| `FOLD` | 折叠展开容器 | 组件或结构数据明确为 `FoldView` | 普通箭头、更多文案、视觉上可展开但无组件证据 |

## 关键判定规则

1. `PAGED` 与 `SCROLL` 不互相替代。同一区域通常二选一；只有「轮播页内还有独立列表」时才同时标。
2. 重复型 `SCROLL` 要有同构项。默认 `minRepeat: 3`；截图只显示 2 个同构项但结构数据明确是列表时可用 `minRepeat: 2`，并保持低置信或等待人工确认。
3. 纯 grid/feed 当前没有独立 `GRID` class。如果风险是滚动容器退化，可先用 `SCROLL` 表达；如果只是静态网格，不写入 `interactions`。
4. `RADIO`、`CHECKBOX`、`SWITCH`、`SLIDER`、`SELECT`、Markdown 富文本当前 schema 暂不表达。它们可以写在未入库原因里，不强行映射到现有 class。
5. `location` 必须来自截图或结构数据坐标：顶部导航/搜索为 `top`，主内容为 `mid`，底部栏/底部弹层为 `bottom`，居中弹窗为 `center`，侧边抽屉为 `left/right`。
6. `confidence:"high"` 的最低门槛是截图强证据；最好同时有 Figma JSON / skeleton 结构证据。仅凭 `components` 或描述推断时不能标 high。
7. 看到被视口或容器裁切的内容时，不要因为没有重复项就忽略滚动。非重复说明正文、空白弹层正文、长文区域都可以标 `SCROLL`，但不要写 `repeated/minRepeat`。
8. 看到底部圆角面板覆盖直播间、页面、列表或背景图时，应优先判断为 `OVERLAY location:"bottom"`。不要只按面板内部控件标注。
9. 弹层内部有主按钮时，通常同时标 `OVERLAY` 和 `ACTION`。按钮数量只统计主命令，不统计关闭图标、帮助图标和普通链接。
10. 横向内容不自动等于 `TABBED`。如果它只是筛选 chip、快捷问题或横滑菜单，应按 `SCROLL` 或不标；只有互斥切换内容面板时才标 `TABBED`。
11. 结构数据里出现 `ScrollView/List` 但截图没有截断、没有继续延伸、只是固定三列指标卡或固定任务块时，不标 `SCROLL`。视觉边界优先于组件名。
12. `OVERLAY` 标的是设计中已打开的弹层状态；如何打开由各 target 的映射和生成流程负责，识别不约束实现。

## 人工校正如何更新本文档

当人工指出 LLM 判断不准时，按以下顺序维护本文档：

1. 抽象出可迁移规则，不只记录当前 case。例如「底部圆角面板覆盖背景」应写成 `OVERLAY bottom` 规则，而不是只写某个 Figma URL。
2. 把规则放入 `关键判定规则` 或 `Class 判定表`。只有当规则需要具体图像帮助理解时，才补充到边界样例库。
3. 标明触发条件和反例。触发条件用于下次自动识别，反例用于避免过拟合。
4. 如果新规则暴露当前 schema 不足，例如 `CHECKBOX`、`SWITCH`、`GRID`，先记录为 schema 缺口，不要强行映射到不相干 class。
5. 如果新规则要求识别新的 class 或新的结构证据信号，更新 `Interaction` schema 及其各 target 的 Target mapping profile。

## LLM 输出候选格式

LLM 给出候选标注时必须包含：

- Figma URL。
- 页面描述。
- 截图证据和 Figma JSON / skeleton 证据。
- 建议写入的 `interactions` JSON。
- 未写入的交互及原因，例如 schema 暂不支持或证据不足。

## 边界样例库

### 非重复滚动不能漏标

触发条件：弹层或正文区域明显被容器底部截断，但没有显示 ≥3 个重复项。

应标：

```json
[
  {"class":"OVERLAY","location":"center","confidence":"high"},
  {"class":"SCROLL","location":"mid","confidence":"high"}
]
```

不要写 `repeated/minRepeat`。该样例覆盖「空白弹层正文被截断」「长说明面板」「非列表长文」。

### 底部半屏面板优先标 OVERLAY

触发条件：直播间、页面或背景图上覆盖一个底部圆角面板，面板遮挡底层内容，底部有主 CTA。

应标：

```json
[
  {"class":"OVERLAY","location":"bottom","confidence":"high"},
  {"class":"ACTION","count":1,"location":"bottom","confidence":"high"}
]
```

即使 `components` 里只有 `Slider`、`Button` 或其他内部控件，也不能忽略外层半屏弹层。

### PAGED 与 SCROLL 不要重复标同一区域

触发条件：同一中部区域是轮播、分页卡片或 `Swiper/ViewPager`。

应标：

```json
[
  {"class":"PAGED","location":"mid","confidence":"high"}
]
```

除非轮播页内部另有独立列表，否则不要因为卡片可横滑或组件清单含 `List` 就同时标 `SCROLL`。

### 完整展示的重复项不等于 SCROLL

触发条件：页面有多个 radio、checkbox、成员行或任务项，但截图完整展示，结构数据没有 `overflow`、`ScrollView`、`VirtualList`。

应只标真实交互：

```json
[
  {"class":"OVERLAY","location":"center","confidence":"high"},
  {"class":"TABBED","location":"top","confidence":"high"},
  {"class":"ACTION","count":1,"location":"bottom","confidence":"high"}
]
```

不要为了重复项本身标 `SCROLL`。`RADIO`、`CHECKBOX` 当前 schema 暂不表达。

### 固定三块视图不是 SCROLL

触发条件：弹层中部是三个固定指标卡、固定任务块或固定配置块；所有内容完整可见，没有上下截断或继续延伸。即使结构数据里出现 `ScrollView/List`，也不能直接判定为滚动。

应只标可确认交互：

```json
[
  {"class":"OVERLAY","location":"center","confidence":"high"},
  {"class":"INPUT","count":3,"location":"mid","confidence":"high"},
  {"class":"ACTION","count":1,"location":"bottom","confidence":"high"}
]
```

`CHECKBOX`、进度条、滑块等当前 schema 暂不表达。

### 筛选弹层不要把底层列表算进当前 case

触发条件：当前 Figma 节点主语义是筛选面板，面板覆盖在列表页上，内部有搜索、tab/chip、checkbox 和底部确认按钮。

应标：

```json
[
  {"class":"OVERLAY","location":"center","confidence":"high"},
  {"class":"INPUT","count":1,"location":"top","confidence":"high"},
  {"class":"TABBED","location":"top","confidence":"high"},
  {"class":"ACTION","count":2,"location":"bottom","confidence":"high"}
]
```

不要把被遮挡的底层瀑布流也标为当前 case 的 `SCROLL`，除非 Figma 节点明确包含并聚焦底层列表。

### 侧边抽屉同时标 OVERLAY 和内部列表

触发条件：右侧或左侧抽屉覆盖在底层页面上，抽屉内部有历史记录、菜单项、会话项等重复列表。

应标：

```json
[
  {"class":"OVERLAY","location":"right","confidence":"high"},
  {"class":"SCROLL","repeated":true,"minRepeat":3,"location":"mid","confidence":"high"}
]
```

外层抽屉和内层列表是两个不同交互语义，可以同时存在。

### Grid/feed 目前用 SCROLL 覆盖滚动退化风险

触发条件：截图是多列卡片网格，内容明显超过视口或结构数据有 `VirtualList`、`lazyLoad`、`feed`、`overflow`。

可标：

```json
[
  {"class":"SCROLL","repeated":true,"minRepeat":3,"location":"mid","confidence":"high"}
]
```

严格说这是 grid/feed，不是普通 list。当前 schema 没有 `GRID`，先用 `SCROLL` 覆盖滚动容器退化风险；如果只是完整展示的静态网格，不写入 `interactions`。

### 快捷问题和横滑菜单不是 TABBED

触发条件：横向区域只是快捷问题、推荐入口、筛选 chip、分类菜单，点击后不体现互斥内容面板。

不要标 `TABBED`。只有结构数据或截图能证明 `TabBar/TabItem/Tabs` 控制内容面板时，才标：

```json
[
  {"class":"TABBED","location":"top","confidence":"high"}
]
```
