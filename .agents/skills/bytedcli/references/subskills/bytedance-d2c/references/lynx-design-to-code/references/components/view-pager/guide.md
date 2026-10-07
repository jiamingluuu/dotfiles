# Lynx UI ViewPager SKILL.md

`<ViewPager>` is a component that lets users swipe between pages of content. It displays one page at a time and navigates horizontally. This document details the advanced usage and best practices for the `<ViewPager>`.

## 1. Common Use Cases

- **Tabbed layouts**: Display horizontally swipeable pages; use `<Tabs>` for titles and `<ViewPager>` for content.
- **Carousels/Galleries(()): Present a collection of images or cards that can be swiped left and right.
- **Content paging**: Split long articles or large lists into multiple pages.
- **Complex scrolling coordination**: Provide localized horizontal switching within vertically scrolling pages: embed it in the slot of `<FoldView>`.
- **Improved render performance**: `<ViewPager>` wraps its children with `<LazyComponent>` by default to lazily load off-screen content, and offers progressive, on-demand loading along the horizontal swipe direction, significantly improving render performance.

## 2. Basic Usage

The children in the `<ViewPager>` will be rendered as horizontal pages.

```tsx
import { ViewPager } from '@byted-lynx/lynx-ui'

function App() {
  const pagerItem = ['1', '2', '3', '4', '5', '6', '7']

  return (
    <ViewPager
      style={{
        width: '100%',
        height: '400px', // specify the height of the ViewPager
      }}
    >
      {pagerItem.map((item, index) => (
        <text
          style={{
            width: '100%',
            height: '100%',
            padding: '20px',
          }}
        >
          {item}
        </text>
      ))}
    </ViewPager>
  )
}
```

## 3. Critical Development Advices

- **MUST**: Specify the width and height of the `<ViewPager>` through the `style` prop explicitly (`100%` or fixed height and width). `<ViewPager>` is designed to have same height and width as its children.
- **MUST**: Specify the height and width of the children in `<ViewPager>` as `100%` through the `style` prop.
- **MUST**: Use `<ViewPager>` together with `<Tabs>` for tabbed or paged peer content. Set the same literal `viewpagerId` on both components; a single default `<ViewPager>` may omit `viewpagerId` only when paired with `<Tabs viewpagerId='viewpager'>`.
- **MUST**: If multiple `<ViewPager>` instances exist, each paired `viewpagerId` must be unique.
- **MUST**: Render one non-empty child page for each tab or inferred peer page. Each child page must have valid visible content and `width: 100%` / `height: 100%`.
- **MUST**: When static Figma evidence only provides the active pane, reuse the active pane's grounded content for the hidden peer pages. Do not create empty pages, opacity-hidden pages, or placeholder-only pages.
- **MUST NOT**: Please do not set `position: absolute` in any children of `<ViewPager>`.
- **MUST NOT**: Please do not set `position: fixed` or `z-index` in any children and grandchildren of `<ViewPager>`, unless you need to make them fix to the root of the Page.
- **Notice**: It is recommended to use Flex layout in the children of `<ViewPager>`.
