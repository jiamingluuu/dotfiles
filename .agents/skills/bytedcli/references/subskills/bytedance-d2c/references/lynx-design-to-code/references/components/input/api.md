## API Definition

### src/apis/develop/element/xelement/xinput.d.ts

```typescript
/**
 * Input Component
 */

 import { StandardProps } from '../../props';

 export interface XInputBlurEvent {
   detail: {
     value: string;
   };
 }
 
 export interface XInputConfirmEvent extends XInputBlurEvent {}
 
 export interface XInputFocusEvent extends XInputBlurEvent {}
 
 export interface XInputEvent {
   detail: {
     value: string;
     cursor: number;
     textLength: number;
   };
 }
 
 export interface XInputProps extends StandardProps {
   /**
    * Position after input is lifted by the keyboard when focused
    * @defaultValue "end"
    * @since 1.6
    */
   'adjust-mode'?: 'end' | 'center';
 
   /**
    * Automatically increase paddingBottom if the ScrollView doesn't have enough space when input is lifted by the keyboard
    * @defaultValue true
    * @since 1.6
    */
   'auto-fit'?: boolean;
 
   /**
    * Height from the top of the keyboard to the input after scrolling in end mode
    * @defaultValue "0"
    * @since 1.6
    */
   'bottom-inset'?: string;
 
   /**
    * Behavior of the Enter key on the keyboard
    * @defaultValue "done"
    */
   'confirm-type'?: 'send' | 'search' | 'go' | 'done' | 'next';
 
   /**
    * Whether the input is disabled
    * @defaultValue false
    */
   disabled?: boolean;
 
   /**
    * Whether the input is focused
    * @defaultValue false
    */
   focus?: boolean;
 
   /**
    * Enter fullscreen input mode in landscape
    * @defaultValue false
    * @since 1.5
    */
   'fullscreen-mode'?: boolean;
 
   /**
    * Maximum input length
    * @defaultValue 140
    */
   maxlength?: number;
 
   /**
    * Placeholder text
    * @defaultValue ""
    */
   placeholder?: string;
 
   /**
    * Placeholder color
    * @defaultValue ""
    */
   'placeholder-color'?: string;
 
   /**
    * Placeholder font size
    * @defaultValue "14px"
    */
   'placeholder-font-size'?: string;
 
   /**
    * Placeholder font weight
    * @defaultValue "normal"
    * @since 2.2
    */
   'placeholder-font-weight'?: string;
 
   /**
    * Whether the input is read-only
    * @defaultValue false
    * @since 2.0
    */
   readonly?: boolean;
 
   /**
    * Show system keyboard when focused, useful for custom keyboards
    * @defaultValue true
    * @since 1.5
    */
   'show-soft-input-onfocus'?: boolean;
 
   /**
    * Automatically scroll the input above the keyboard when focused
    * Not effective with elements having position: fixed
    * @defaultValue true
    * @since 1.6
    */
   'smart-scroll'?: boolean;
 
   /**
    * Input type
    * Android does not support combination of password and other types
    * @defaultValue "text"
    * @since tel and email supported since 1.6
    */
   type?: 'text' | 'number' | 'digit' | 'password' | 'tel' | 'email';
 
   /**
    * Value of the input field
    * @defaultValue ""
    */
   value?: string;
 
   /**
    * Callback when the input loses focus
    */
   bindblur?: (e: XInputBlurEvent) => void;
 
   /**
    * Callback when the user taps the done button on the keyboard
    */
   bindconfirm?: (e: XInputConfirmEvent) => void;
 
   /**
    * Callback when the input gains focus
    */
   bindfocus?: (e: XInputFocusEvent) => void;
 
   /**
    * Callback for input
    */
   bindinput?: (e: XInputEvent) => void;
 }
 
 export type XInputAddTextMethod = {
   method: 'addText';
   params: { text: string };
   success: (data: {}) => void;
   fail: (data: {}) => void;
 };
 
 export type XInputBlurMethod = {
   method: 'blur';
   success: (data: {}) => void;
   fail: (data: {}) => void;
 };
 
 export enum XInputControlKeyBoardAction {
   ShowKeyboard,
   HideKeyboardWithFocus,
   FocusWithoutKeyboard,
   HideKeyboard,
 }
 
 // @support Android
 export type XInputControlKeyBoardMethod = {
   method: 'controlKeyBoard';
   params: { action: XInputControlKeyBoardAction };
   success: (data: {}) => void;
   fail: (data: {}) => void;
 };
 
 export type XInputFocusMethod = {
   method: 'focus';
   success: (data: {}) => void;
   fail: (data: {}) => void;
 };
 
 export type XInputSetValueMethod = {
   method: 'setValue';
   params: { value: string; index?: number };
   success: (data: {}) => void;
   fail: (data: {}) => void;
 };
 
export type XInputSendDelEventMethod = {
  method: 'sendDelEvent';
  params: { action: 0 | 1; length?: number };
  success: (data: {}) => void;
  fail: (data: {}) => void;
};

export type XInputSetInputFilterMethod = {
  method: 'setInputFilter';
  params: { pattern: string };
  success: (data: {}) => void;
  fail: (data: {}) => void;
};

export type XInputSelectMethod = {
  method: 'select';
  success: (data: {}) => void;
  fail: (data: {}) => void;
};

export type XInputSetSelectionRangeMethod = {
  method: 'setSelectionRange';
  params: { selectionStart: number; selectionEnd: number };
  success: (data: {}) => void;
  fail: (data: {}) => void;
};

export type XInputUIMethods =
  | XInputAddTextMethod
  | XInputBlurMethod
  | XInputControlKeyBoardMethod
  | XInputFocusMethod
  | XInputSetValueMethod
  | XInputSendDelEventMethod
  | XInputSetInputFilterMethod
  | XInputSelectMethod
  | XInputSetSelectionRangeMethod;

```
