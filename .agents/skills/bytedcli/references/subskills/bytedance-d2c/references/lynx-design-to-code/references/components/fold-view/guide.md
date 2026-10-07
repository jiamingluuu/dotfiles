# Lynx UI FoldView SKILL.md

The FoldView component is a specialized scroll container that implements a "collapsible header" effect. It consists of a header area (which folds/scrolls away), a toolbar (which sticks to the top), and a scrollable content slot. This document details the advanced usage and best practices for the FoldView component.

## 1. Prerequisites

To ensure smooth gesture handling and nested scrolling behaviors, especially when combining with other scroll containers, please ensure your project enables the new gesture system.

```typescript
// lynx.config.ts
export default {
  // ... other configs
  enableNewGesture: true,
}
```

## 2. Basic Usage

FoldView divides the view into three parts:

- **Headers**: The top area that scrolls away.
- **Toolbar**: The area that sticks to the top after the headers scroll off-screen.
- **Slot**: The main scrollable content (e.g., List, ScrollView).

```tsx
import { FoldView } from '@byted-lynx/lynx-ui'

function MyPage() {
  return (
    <FoldView
      style={{ width: '100%', height: '100%' }}
      headers={[
        <view style={{ height: '200px', backgroundColor: 'blue' }}>
          <text>Header Area</text>
        </view>,
      ]}
      toolbar={
        <view style={{ height: '50px', backgroundColor: 'red' }}>
          <text>Sticky Toolbar</text>
        </view>
      }
      slot={
        <scroll-view scroll-y style={{ height: '100%' }}>
          {/* Your long list content */}
          <text>List Content 1</text>
          <text>List Content 2</text>
          {/* ... */}
        </scroll-view>
      }
    />
  )
}
```

## 3. Pull-to-Refresh

FoldView supports pull-down refreshing. You need to provide a `refreshHeader` and handle the `onRefresh` event.

### Standard Refresh

```tsx
<FoldView
  refreshHeader={<MyLoadingSpinner />}
  onRefresh={() => {
    // Perform data fetching
    console.log('Refreshing...')
  }}
  // ... other props
/>
```

### Refresh in Slot (Advanced)

If you need the refresh trigger to be inside the slot (e.g., specialized list behavior), use `refreshInSlot`.

```tsx
<FoldView
  refreshInSlot={true}
  slot={
    <scroll-view>
      <x-refresh-view>
        <text>Loading...</text>
      </x-refresh-view>
      {/* content */}
    </scroll-view>
  }
/>
```

## 4. Nested in Popup (Critical)

When using `FoldView` inside a `Popup`, you **MUST** forward the gesture from the Popup to the FoldView to ensure the drag-to-close gesture works correctly when the FoldView is at the top.

```tsx
// Inside Popup's render prop
<Popup>
  {(popupOptions) => {
    const { 'main-thread:gesture': nativeGesture } = popupOptions
    return (
      <FoldView
        // Bind the gesture from Popup to FoldView
        main-thread:gesture={nativeGesture}
        headers={[/*...*/]}
        slot={[/*...*/]}
      />
    )
  }}
</Popup>
```

## 5. Controlling Scroll Position

You can programmatically control the scroll position using the `ref`.

```tsx
import { useRef } from '@byted-lynx/react'
import type { FoldViewRef } from '@byted-lynx/lynx-ui'

// ...
const foldViewRef = useRef<FoldViewRef>(null)

// Scroll to top (expand header)
foldViewRef.current?.scrollToTop(true)

// Scroll to sticky position (collapse header, show toolbar)
foldViewRef.current?.scrollToSticky(true)
```

## 6. FAQ

**Q: Why is my header covering the list content?**
A: Check the `headerOverSlot` property. If set to `true`, the header will have a higher z-index than the slot. Default is `false`.

**Q: My list inside the slot isn't scrolling?**
A: Ensure the component inside `slot` (like `ScrollView` or `List`) has a defined height (usually `100%`) and is scrollable.

**Q: Can I use multiple items in headers?**
A: Yes, `headers` prop accepts an array of ReactElements (`ReactElement[]`).
