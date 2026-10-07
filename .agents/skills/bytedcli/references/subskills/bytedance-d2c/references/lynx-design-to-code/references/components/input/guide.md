# Lynx UI Input SKILL.md

The `input` route maps to the `x-input-ng` element for single-line editable text fields. Use it for real user text entry. Do not simulate editable input with `view` + `text` placeholders.

## 1. Core Capabilities

- **Single-line text entry**: Use `x-input-ng` for editable username, search, phone, email, password, code, and short form fields.
- **Keyboard type control**: Use `type` to hint the correct keyboard, such as `text`, `number`, `digit`, `password`, `tel`, or `email`.
- **Placeholder and confirm behavior**: Use `placeholder` and `confirm-type` to control the displayed hint and IME enter action.
- **Editable state control**: Use `readonly`, `maxlength`, `disabled`, `focus`, `show-soft-input-onfocus`, and `smart-scroll` for interaction and keyboard behavior.
- **Keyboard avoidance controls**: Use `adjust-mode`, `auto-fit`, and `bottom-inset` when the field must stay visible above the soft keyboard.
- **Input lifecycle events**: Listen with `bindinput`, `bindfocus`, `bindblur`, and `bindconfirm`.

## 2. Routing Guidance

- **Choose the `input` route when**: The design shows a real editable single-line field, search bar, OTP slot row, login field, or any control that should invoke the keyboard.
- **Implement that route with**: `x-input-ng`.
- **Do not use `view` + `text` when**: The user can type, edit, select, focus, or submit text.
- **Use another route when**:
  - The field is multi-line: use `<textarea>`.
  - The region is only a static label or fake mock text: use `<text>`.
  - The node is a button-like chip or segmented control: use the corresponding component instead.

## 3. Basic Usage

`x-input-ng` is used as a raw element here, so you do not import it from `@byted-lynx/lynx-ui`.

```tsx
import { useState } from '@byted-lynx/react'

export function SearchField() {
  const [value, setValue] = useState('')

  return (
    <view className='search-shell'>
      <x-input-ng
        className='search-input'
        value={value}
        placeholder='Search'
        type='text'
        confirm-type='search'
        smart-scroll={true}
        bindinput={(e) => setValue(e.detail.value)}
      />
    </view>
  )
}
```

## 4. Critical Development Advice

- **MUST**: Use `x-input-ng` for true editable single-line entry in this skill route.
- **MUST**: Keep the route name as `input` in routing docs and skill lookup, but use `x-input-ng` in the rendered element.
- **MUST**: Preserve the x-element prop names from the API, including hyphenated names such as `confirm-type`, `show-soft-input-onfocus`, and `placeholder-color`.
- **MUST**: Style the field shell and spacing with surrounding layout primitives as needed, but keep the editable node itself as `x-input-ng`.
- **MUST NOT**: Fake an input with `view`, `text`, and icons when the design implies focus, caret, keyboard entry, or confirm action.
- **MUST NOT**: Fall back to the older built-in `<input>` element for this skill.
- **MUST NOT**: Use `x-input-ng` for multi-line paragraph entry.
- **Notice**: `x-input-ng` exposes keyboard-handling props directly, including `smart-scroll`, `auto-fit`, and `adjust-mode`.
- **Notice**: The local bundled examples still come from `src/examples/Input`, which demonstrate higher-level `@byted-lynx/lynx-ui-input` wrappers around the same input domain.

## 5. Useful Attributes

- `value`: Current text value.
- `placeholder`: Placeholder hint text.
- `type`: Keyboard/input mode, such as `text`, `number`, `digit`, `password`, `tel`, or `email`.
- `confirm-type`: IME action label such as `search`, `done`, `go`, `next`, or `send`.
- `maxlength`: Maximum character count.
- `disabled`: Whether the field is interactive.
- `focus`: Whether the field should be focused.
- `readonly`: Whether the field is editable.
- `show-soft-input-onfocus`: Whether focusing the field opens the software keyboard.
- `smart-scroll`: Whether the field scrolls above the keyboard automatically.
- `adjust-mode`: Keyboard lift behavior, `end` or `center`.
- `auto-fit`: Whether extra bottom padding is added when the container lacks space above the keyboard.
- `bottom-inset`: Target inset from the keyboard top when using end mode.
- `placeholder-color`: Placeholder text color.
- `placeholder-font-size`: Placeholder font size.
- `placeholder-font-weight`: Placeholder font weight.

## 6. Useful Events

- `bindinput`: Fired when the text changes.
- `bindfocus`: Fired when the field gains focus.
- `bindblur`: Fired when the field loses focus.
- `bindconfirm`: Fired when the IME confirm action is triggered.

## 7. Methods

`x-input-ng` exposes common input methods including:

- `addText`
- `controlKeyBoard`
- `focus`
- `blur`
- `setValue`
- `select`
- `setSelectionRange`
- `setInputFilter`
- `sendDelEvent`
