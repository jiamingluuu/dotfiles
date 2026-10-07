# Lynx UI Popup SKILL.md

The Popup component is a powerful modal container that supports gesture dragging, multi-stage height stops, and nested scroll views. **Note: When nesting scrollable components within the Popup, you MUST pass Popup render-prop options into the nested content and bind `main-thread:gesture` to the inner scroll container.** This document details the advanced usage and best practices for the Popup component.

## 1. Prerequisites

To ensure that Popup's gesture interactions (especially the coordination with internal scroll components) work correctly, you **MUST** enable the new gesture system in your Lynx project configuration.

Please ensure your `lynx.config.ts` or relevant configuration file includes the following setting:

```typescript
// lynx.config.ts
export default {
  // ... other configs
  enableNewGesture: true,
}
```

## 2. Basic Usage

Popup is typically used as a panel that slides up from the bottom of the screen. You can control its opening and closing via a `ref`.

For D2C output, use the guide's ref + render-prop shape. Do not use `visible` / `placement` or a direct primitive body.

`heightPercent.bottom` defaults to `0`. Do not set it unless the design requires a real collapsed stop; never duplicate `top` or `init` into `bottom`.

```tsx
import { useRef } from '@byted-lynx/react'
import { Popup, type PopupRef } from '@byted-lynx/lynx-ui'

function App() {
  const popupRef = useRef<PopupRef>(null)

  const openPopup = () => {
    // Open the popup, defaults to center position (0)
    // Optional values: top (1), bottom (-1)
    popupRef.current?.open()
  }

  return (
    <view>
      <text bindtap={openPopup}>Open Popup</text>

      <Popup
        ref={popupRef}
        heightPercent={{
          top: 90, // Top stop position (percentage)
          init: 60, // Initial opening position (percentage)
        }}
      >
        {(popupOptions) => <PopupContent {...popupOptions} />}
      </Popup>
    </view>
  )
}

function PopupContent() {
  return (
    <view style={{ height: '100%', backgroundColor: 'white' }}>
      <text>Popup Content</text>
    </view>
  )
}
```

## 3. Nested Scrolling (Critical)

When a Popup contains scrollable components (such as `ScrollView`, `List`, `FoldView`, etc.), special configuration is required to resolve gesture conflicts (e.g., distinguishing between scrolling content and dragging to close the Popup when the user pulls down).

Popup uses the **Render Prop** pattern to pass a gesture object to its children. You need to bind this gesture object to the **outermost scroll container**.

### Step-by-Step Guide:

1. **Popup Layer**: Use a function as `children` to receive `popupOptions`.
2. **Popup Scroll ID**: Set `scrollContainerId` to the nested scroll container id. For `List`, this must match `listId`; for `ScrollView`, this must match `scrollviewId`.
3. **Child Component Layer**: Pass `popupOptions` into a dedicated content component.
4. **Binding**: In that content component, receive `main-thread:gesture` from props and bind it to the nested `List`, `ScrollView`, or `FoldView`.

### Code Example:

**Popup Parent Component:**

```tsx
// Parent.tsx
<Popup
  ref={popupRef}
  scrollContainerId='my-scroll-view'
  // ...other props
>
  {/* Use Render Prop to receive options */}
  {(popupOptions) => <MyContent {...popupOptions} />}
</Popup>
```

**Internal ScrollView Child Component:**

```tsx
// MyContent.tsx
import { ScrollView } from '@byted-lynx/lynx-ui'
import type { BaseGesture } from '@byted-lynx/gesture-runtime'

interface MyContentProps {
  // Receive gesture object from Popup
  'main-thread:gesture'?: BaseGesture
  [key: string]: any
}

const MyContent = (props: MyContentProps) => {
  // Destructure the gesture object
  const { 'main-thread:gesture': nativeGesture } = props

  return (
    <ScrollView
      // CRITICAL: Bind gesture to ScrollView
      main-thread:gesture={nativeGesture}
      scrollviewId='my-scroll-view'
      style={{ width: '100%', height: '100%' }}
      scrollY
    >
      {/* Scrollable Content */}
      <view style={{ height: '2000px', backgroundColor: '#f0f0f0' }}>
        <text>Long Scroll Content...</text>
      </view>
    </ScrollView>
  )
}
```

**Internal List Child Component:**

```tsx
import { List } from '@byted-lynx/lynx-ui'
import type { BaseGesture } from '@byted-lynx/gesture-runtime'

interface MyListProps {
  'main-thread:gesture'?: BaseGesture
}

const MyList = ({ 'main-thread:gesture': nativeGesture }: MyListProps) => (
  <List
    main-thread:gesture={nativeGesture}
    listId='list'
    listType='single'
    spanCount={1}
    style={{ width: '100%', height: '100%' }}
  >
    {items.map(item => (
      <list-item item-key={item.id} key={item.id}>
        <Row item={item} />
      </list-item>
    ))}
  </List>
)
```

### Notes:

- **List**: `Popup scrollContainerId` must match `List listId`, and `List` must bind `main-thread:gesture={nativeGesture}`.
- **ScrollView**: `Popup scrollContainerId` must match `ScrollView scrollviewId`, and `ScrollView` must bind `main-thread:gesture={nativeGesture}`.
- **FoldView**: If nesting a `<FoldView>`, bind `main-thread:gesture={nativeGesture}` on the `<FoldView>` tag.
- **Deep Nesting**: Ensure the gesture is bound to the outermost scroll container.
- **Nested Scroll Containers**: Internally nested scroll containers **MUST** bind the gesture.

## 4. FAQ

**Q: Why does scrolling the List or ScrollView inside the Popup not work?**
A: It is likely that `main-thread:gesture` is not bound correctly, or `Popup scrollContainerId` does not match the nested scroll container id. Please check the render-prop handoff and the `listId` / `scrollviewId` pairing.

**Q: Gestures are not working?**
A: Please check if `enableNewGesture: true` is enabled in `lynx.config.ts`.
