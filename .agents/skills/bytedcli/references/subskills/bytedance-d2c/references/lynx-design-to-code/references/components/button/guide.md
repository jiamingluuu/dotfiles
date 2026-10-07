# Lynx UI Button

`Button` is a headless action root. It renders a Lynx `view`, owns tap and press-state behavior, and leaves its visual design to `className`, `style`, and children.

## Basic usage

```tsx
import { Button } from '@byted-lynx/lynx-ui'

function SubmitButton({
  disabled,
  onSubmit,
}: {
  disabled: boolean
  onSubmit: () => void
}) {
  return (
    <Button
      className='submit-button'
      disabled={disabled}
      onClick={onSubmit}
    >
      <text className='submit-button__label'>Submit</text>
    </Button>
  )
}
```

```css
.submit-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 96rpx;
  border-radius: 48rpx;
  background-color: #2563eb;
}

.submit-button.ui-active {
  opacity: 0.8;
}

.submit-button.ui-disabled {
  opacity: 0.5;
}

.submit-button__label {
  color: #ffffff;
  font-size: 32rpx;
}
```

## Composition rules

- Put the action's width, height, layout, background, and border radius on the `Button` root so its hit area matches the visible control.
- Render labels inside `text`; compose icons and other visual content as children.
- Style pressed and disabled states with same-element selectors such as `.submit-button.ui-active` and `.submit-button.ui-disabled`.
- Pass `disabled` to the Button whenever the action is unavailable. It suppresses `onClick` and adds `ui-disabled` to the root class list.

## Public props

- `onClick?: () => void`: Handle the action.
- `disabled?: boolean`: Disable the action and expose the disabled state class.
- `className?: string`: Style the Button root and its state variants.
- `style?: CSSProperties`: Apply inline styles to the Button root.
- `buttonProps?: ViewProps`: Forward raw Lynx view props when the Button-level props do not cover the required behavior.
