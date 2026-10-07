# Lynx UI List SKILL

## 1. Core Capabilities

- **Virtual Scrolling**: **List** and **FeedList** is the **only two** scroll container that can only renders visible items, ensuring smooth scrolling performance even with **massive** amounts of data. If the count of children has more than 10 items, you **MUST** use **List** or **FeedList**.
- **Multiple Layouts**: Supports three layout modes: `single` (single-column list), `flow` (multi-column grid layout), and `waterfall` (multi-column waterfall layout). **FeedList** is the **only** scroll container that supports multi-column layout.
- **Required Height**: `List` **MUST** have an explicit measurable height on the component itself. Use `style.height` with fixed, viewport, or percentage units, or use `listMaxHeight`. Do not rely on `flex: 1` alone.
- **No Descendant Z-Index**: Descendants of `List`, including `<list-item>` content and custom item components, **MUST NOT** set `z-index` / `zIndex`. It can detach children from native list rendering.

## 2. AI Coding Guide

### Minimal Usable Example

When using `List`, you must provide a unique `listId`, specify the `listType`, and use `<list-item>` as the direct child. Each `<list-item>` **MUST** have a unique `item-key` and **MUST** also set a `key` prop. These two keys serve different purposes and both are required.

Runtime constraints:

- Set `style.height` directly on `List`, for example `height: '400px'`, `height: '100vh'`, or `height: '100%'` when the parent already has a concrete height.
- Use `listMaxHeight` when the API should own the maximum height.
- Do not use `flex: 1` as the only boundary for `List`.
- Do not set `z-index` / `zIndex` anywhere inside the list item subtree.
- Keep fixed page-level bottom actions outside `List`. Only actions that belong to every repeated item should be rendered inside `<list-item>`.
- When `List` is nested inside `Popup`, set `Popup scrollContainerId` to the same value as `List listId`, pass Popup render-prop options into the list component, and bind `main-thread:gesture` to the `List`.

```tsx
import { List } from '@byted-lynx/lynx-ui'

function BasicList() {
  const items = Array.from({ length: 100 }, (_, i) => `Item ${i + 1}`)

  return (
    <List
      listId='my-unique-list'
      listType='single'
      spanCount={1}
      style={{ width: '100%', height: '400px' }}
    >
      {items.map(item => (
        <list-item item-key={item} key={item}>
          <view style={{ height: '50px', borderBottom: '1px solid #eee' }}>
            <text>{item}</text>
          </view>
        </list-item>
      ))}
    </List>
  )
}
```

### Recommended Prompt Formula

> **Scenario Description** + **Layout Type and Configuration** + **Data and Item Content** + **Interaction Requirement**

**Example Prompt:**

- "Create a single-column virtual list to display 1000 data items. Each item has a height of 60px."
- "Implement a two-column grid layout using `List`. The data items are images."
- "Create a waterfall layout `List`. When the list is scrolled to the bottom, trigger a ‘load more’ function."

## 3. Use Cases & Best Practices

### Single-column List (single)

The most basic list form.

```tsx
import { List } from '@byted-lynx/lynx-ui';

function SingleColumnList() {
  const data = [...];
  return (
    <List listId="single-list" listType="single" style={{ width: '100%', height: '400px' }}>
      {data.map(item => (
        <list-item item-key={item.id} key={item.id}>
          <MyListItem data={item} />
        </list-item>
      ))}
    </List>
  );
}
```

**Example Path**: `apps/examples/src/List/Layouts/index.tsx`

### Grid Layout (flow)

Set `listType` to `flow` and specify `spanCount` to create a grid layout.

```tsx
import { List } from '@byted-lynx/lynx-ui';

function GridLayout() {
  const data = [...];
  return (
    <List
      listId="grid-list"
      listType="flow"
      spanCount={3} // 3 columns
      mainAxisGap={10} // Vertical gap
      crossAxisGap={10} // Horizontal gap
      style={{ width: '100%', height: '400px' }}
    >
      {/* ... list-items ... */}
    </List>
  );
}
```

**Example Path**: `apps/examples/src/List/Layouts/index.tsx`

### Waterfall Layout (waterfall)

Set `listType` to `waterfall` for an unequal-height column layout.

```tsx
import { List } from '@byted-lynx/lynx-ui';

function WaterfallList() {
  const data = [...]; // Data items usually have different heights
  return (
    <List
      listId="waterfall-list"
      listType="waterfall"
      spanCount={2} // 2 columns
      style={{ width: '100%', height: '400px' }}
    >
      {/* ... list-items ... */}
    </List>
  );
}
```

**Example Path**: `apps/examples/src/List/Layouts/index.tsx`

### 4. FAQ

**Q: Do I need to set `listId`, and does it have to be unique?**

A: Yes. `listId` is the unique identifier used by the native layer to track a `List` instance. You must ensure every `List` on the same page has a different `listId`.

**Q: Why does my `List` warn about children or reuse keys?**

A: The direct child of `List` must be `<list-item>`, and each `<list-item>` must have a unique `item-key`. The virtual list mechanism and reuse strategy depend on `item-key` to correctly recycle and render items.

**Q: Do I need both React `key` and `item-key`?**

A: Yes. `item-key` is consumed by the native virtualization engine to identify and recycle items; React’s `key` is used by React’s reconciliation to track element identity. They may share the same value, but you must provide both.

**Q: Why can’t my `List` scroll or render correctly?**

A: `List` needs an explicit measurable height on the component itself to calculate visible items. Provide `style.height`, such as `height: '400px'`, `height: '100vh'`, or `height: '100%'` when the parent already has a concrete height. `flex: 1` alone is not sufficient.

**Q: How do `listType` and `spanCount` relate?**

A: `single` ignores `spanCount` (single column). `flow` and `waterfall` require `spanCount` ≥ 1 to define the number of columns. `flow` assumes relatively equal item heights; `waterfall` supports uneven heights (masonry-style).

**Q: What do `mainAxisGap` and `crossAxisGap` control?**

A: They control spacing between items. For vertical lists, `mainAxisGap` is the vertical gap and `crossAxisGap` is the horizontal gap. These are most relevant for multi-column layouts (`flow`, `waterfall`).

**Q: How should I implement “load more” correctly?**

A: Use `onScrollToLower` to trigger pagination. Keep `item-key` stable when appending data, avoid heavy computations in scroll callbacks, and debounce network requests to prevent jank.

**Q: My `onScroll` feels laggy—how to optimize?**

A: Avoid expensive work in `onScroll`. Throttle the handler, move heavy logic off the UI thread, and prefer `onScrollToLower`/`onScrollToUpper` for coarse-grained triggers.

**Q: Can I set CSS `max-height` directly?**

A: Use the `listMaxHeight` prop to set max height. Do not rely on CSS `max-height` alone, as the native measuring logic reads from the prop.

**Q: When should I use `FeedList` instead of `List`?**

A: Use `FeedList` if you need refresh or loadmore footer. Otherwise, use `List` for simple virtual lists.

**Q: How do I make `List` fill remaining space in a flex layout?**

A: Give the parent a concrete height, then set `style={{ height: '100%' }}` on `List`. Do not rely on `flex: 1` on `List` or its wrapper as the only boundary.

**Q: Can list item content use `z-index` for badges or overlays?**

A: No. Do not set `z-index` / `zIndex` on descendants of `List`, including content rendered by custom item components. Reorder children or use normal positioned layout without `z-index`; otherwise the item subtree may detach from native list rendering.

**Q: Why can’t my `List` scroll inside a `Popup`?**

A: The Popup gesture must be passed to the nested List. Use `<Popup scrollContainerId="list">` with `<List listId="list" main-thread:gesture={nativeGesture}>`, where `nativeGesture` comes from the Popup render-prop options.

**Q: Where should bottom CTA buttons live when the page also has a `List`?**

A: If the CTA is a fixed page action, render it as a sibling outside `List` and anchor it to the page/container bottom. Put a Button inside `<list-item>` only when it is part of each repeated row or card.

## 5. Sub components

- **`<list-item>`**: This is a built-in tag, not a React component provided by `lynx-ui`. It must be the direct child of `List` and must have a unique `item-key` property. All content for a list item should be placed inside this tag and must not use `z-index` / `zIndex`.
