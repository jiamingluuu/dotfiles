## Examples

### BankCard

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import './index.scss'
import './BankCardScrollView.scss'

import { root, useEffect, useRef } from '@byted-lynx/react'

import { Popup } from '@byted-lynx/lynx-ui-popup'
import type { PopupRef } from '@byted-lynx/lynx-ui-popup'
import type { OnDragCallback } from '@byted-lynx/lynx-ui-popup/types'

import BankCardScrollView from './BankCardScrollView'

/**
 * preview {@link https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/popup_bankcard.gif}
 */
function App() {
  const popupRef = useRef<PopupRef>(null)
  const infoIcon =
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/website_sheild _1.svg'

  useEffect(() => {
    popupRef.current?.open()
  }, [])
  const onPopupStateChange = (state: number) => {
    console.log('onPopupStateChange', state)
  }

  const onDrag = (e: OnDragCallback) => {
    console.log('onDrag', e)
  }

  return (
    <view style='width:100%;height:100%;'>
      <view
        style={{ flexDirection: 'column', alignItems: 'center' }}
        className='payment-info'
      >
        <text className='total-amount-header'>Total amount</text>
        <text className='total-amount'>$120.76</text>
        <view
          style={{ flexDirection: 'row', alignItems: 'center' }}
          className='secure-payment'
        >
          <svg
            className='secure-icon'
            src='https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/website_lock_1.svg'
          />
          <text className='secure-payment-text'>Secure Payment</text>
        </view>
      </view>
      <Popup
        ref={popupRef}
        scrollContainerId='scrollview'
        maxHeight={680}
        heightPercent={{
          top: 70,
          init: 50,
          boundaryArea: 10,
        }}
        preload={true}
        internalDebugLog={true}
        onPopupPositionChange={onPopupStateChange}
        onDrag={onDrag}
        maskStyle={{
          background: 'black',
          opacity: 0.8,
        }}
        bottomNode={
          <view className='payment-bottom-node'>
            <view className='add-card'>
              <text className='add-card-text'>+ Add new card</text>
            </view>
            <view className='info-banner'>
              <svg className='info-icon' src={infoIcon} />
              <text className='info-text'>
                We adhere entirely to the data security standards of the payment
                card industry.
              </text>
            </view>
            <view className='footer'>
              <view className='continue-button'>
                <text className='continue-text'>Continue</text>
              </view>
            </view>
          </view>
        }
      >
        {(popupOptions) => <BankCardScrollView {...popupOptions} />}
      </Popup>
    </view>
  )
}

root.render(<App />)

export default App
```

### FoldView

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import './index.scss'
import './foldview.scss'
import { root, useEffect, useRef, useState } from '@byted-lynx/react'

import { Popup, PopupStatus } from '@byted-lynx/lynx-ui-popup'
import type { PopupRef } from '@byted-lynx/lynx-ui-popup'
import type { OnDragCallback } from '@byted-lynx/lynx-ui-popup/types'

import FoldView from './foldview'

/**
 * preview {@link https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/popup_foldview.gif}
 */
function App() {
  const popupRef = useRef<PopupRef>(null)
  const [backgroundColor, setBackgroundColor] = useState('blue')
  const [_initHeight, setInitHeight] = useState(15)

  const onTap = () => {
    console.log('onTap')
    popupRef.current?.open(PopupStatus.AT_TOP)
  }

  useEffect(() => {
    setInitHeight(60)
    popupRef.current?.open()
  }, [])

  const onPopupStateChange = (state: number) => {
    console.log('onPopupStateChange', state)
  }

  const onDrag = (e: OnDragCallback) => {
    console.log('onDrag', e)
  }

  const _headers = ['1', '2', '3', '4']

  const handleChangeColor = () => {
    setBackgroundColor(backgroundColor === 'blue' ? 'yellow' : 'blue')
    popupRef?.current?.translateTo('90%')
  }

  return (
    <view style='width:100%;height:100%;z-index:0'>
      <text
        style='width:100px;height:100px;background:red;text-align: center;line-height: 100px;'
        bindtap={onTap}
      >
        open popup
      </text>

      <text
        style={{
          width: '100px',
          height: '100px',
          backgroundColor,
          textAlign: 'center',
          lineHeight: '100px',
        }}
        bindtap={handleChangeColor}
      >
        bindtap
      </text>

      <Popup
        ref={popupRef}
        // bytedanceOverlayMode='window'
        scrollContainerId='foldview'
        internalDebugLog={true}
        onRequestClose={() => {
          console.log('onRequestClose')
          popupRef.current?.close()
        }}
        maxHeight={914}
        closeOnMaskClick={true}
        heightPercent={{
          top: 90,
          init: 60,
          bottom: 30,
          boundaryArea: 10,
        }}
        maskTransitionTimingFunction='all ease-out'
        enterDuration={3000}
        exitDuration={3000}
        preload={true}
        onPopupTopChange={(top) => {
          console.log('onPopupTopChange', top)
        }}
        onPopupPositionChange={onPopupStateChange}
        onDrag={onDrag}
        maskStyle={{
          background: 'rgba(0, 0, 0, 0.5)',
        }}
      >
        {(popupOptions) => <FoldView {...popupOptions} />}
      </Popup>
    </view>
  )
}

root.render(<App />)

export default App
```

### List

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import './index.scss'
import { root, useRef } from '@byted-lynx/react'

import { Popup } from '@byted-lynx/lynx-ui-popup'
import type { PopupRef } from '@byted-lynx/lynx-ui-popup'
import type { OnDragCallback } from '@byted-lynx/lynx-ui-popup/types'

import MyList from './list'

/**
 * preview {@link https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/popup_list.gif}
 */
function App() {
  const popupRef = useRef<PopupRef>(null)

  const onTap = () => {
    console.log('onTap')
    popupRef.current?.open(1)
  }

  const onPopupStateChange = (state: number) => {
    console.log('onPopupStateChange', state)
  }

  const onDrag = (e: OnDragCallback) => {
    console.log('onDrag', e)
  }

  return (
    <view style='width:100%;height:100%;'>
      <text
        style='width:100px;height:100px;background:red;text-align: center;	line-height: 100px;'
        bindtap={onTap}
      >
        open popup
      </text>
      <Popup
        ref={popupRef}
        scrollContainerId='list'
        heightPercent={{
          top: 100,
          init: 60,
          boundaryArea: 10,
        }}
        preload={true}
        onPopupPositionChange={onPopupStateChange}
        onDrag={onDrag}
        maskStyle={{
          background: 'gray',
          opacity: 0.5,
        }}
      >
        {(popupOptions) => <MyList {...popupOptions} />}
      </Popup>
    </view>
  )
}

root.render(<App />)

export default App
```

### Pad

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import './index.scss'
import { root, useRef } from '@byted-lynx/react'

import { Popup } from '@byted-lynx/lynx-ui-popup'
import type { PopupRef } from '@byted-lynx/lynx-ui-popup'
import type { OnDragCallback } from '@byted-lynx/lynx-ui-popup/types'

import MyScrollView from './scrollview'

/**
 * preview {@link https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/popup_scrollview.gif}
 */
function App() {
  const popupRef = useRef<PopupRef>(null)

  const onTap = () => {
    console.log('onTap')
    popupRef.current?.open()
  }

  const onPopupStateChange = (state: number) => {
    console.log('onPopupStateChange', state)
  }

  const onDrag = (e: OnDragCallback) => {
    console.log('onDrag', e)
  }

  return (
    <view style='width:100%;height:100%;'>
      <text
        style='width:100px;height:100px;background:red;text-align: center;	line-height: 100px;'
        bindtap={onTap}
      >
        open popup
      </text>
      <Popup
        ref={popupRef}
        scrollContainerId='scrollview'
        heightPercent={{
          top: 80,
          init: 40,
          boundaryArea: 10,
        }}
        preload={true}
        internalDebugLog={true}
        contentStyle={{
          maxWidth: '400px',
          alignSelf: 'center',
        }}
        onPopupPositionChange={onPopupStateChange}
        onDrag={onDrag}
        maskStyle={{
          background: 'gray',
          opacity: 0.5,
        }}
      >
        {(popupOptions) => <MyScrollView {...popupOptions} />}
      </Popup>
    </view>
  )
}

root.render(<App />)

export default App
```

### ScrollView

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import './index.scss'
import { root, useRef } from '@byted-lynx/react'

import { Popup } from '@byted-lynx/lynx-ui-popup'
import type { PopupRef } from '@byted-lynx/lynx-ui-popup'
import type { OnDragCallback } from '@byted-lynx/lynx-ui-popup/types'

import MyScrollView from './scrollview'

/**
 * preview {@link https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/popup_scrollview.gif}
 */
function App() {
  const popupRef = useRef<PopupRef>(null)

  const onTap = () => {
    console.log('onTap')
    popupRef.current?.open()
  }

  const onPopupStateChange = (state: number) => {
    console.log('onPopupStateChange', state)
  }

  const onDrag = (e: OnDragCallback) => {
    console.log('onDrag', e)
  }

  return (
    <view style='width:100%;height:100%;'>
      <text
        style='width:100px;height:100px;background:red;text-align: center;	line-height: 100px;'
        bindtap={onTap}
      >
        open popup
      </text>
      <Popup
        ref={popupRef}
        scrollContainerId='scrollview'
        heightPercent={{
          top: 80,
          init: 40,
          boundaryArea: 10,
        }}
        preload={true}
        internalDebugLog={true}
        onPopupPositionChange={onPopupStateChange}
        onDrag={onDrag}
        maskStyle={{
          background: 'gray',
          opacity: 0.5,
        }}
      >
        {(popupOptions) => <MyScrollView {...popupOptions} />}
      </Popup>
    </view>
  )
}

root.render(<App />)

export default App
```

### SpendSave

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useEffect, useRef } from '@byted-lynx/react'

import { Popup } from '@byted-lynx/lynx-ui-popup'
import type { PopupRef } from '@byted-lynx/lynx-ui-popup'

import { ActionButtons } from './components/ActionButtons'
import { BalanceCards } from './components/BalanceCards'
import { SpendSave } from './components/SpendSave'
import './index.scss'

/**
 * preview {@link https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/popup_spendsave.gif}
 */
function App() {
  const popupRef = useRef<PopupRef>(null)
  useEffect(() => {
    popupRef.current?.open()
  }, [])

  return (
    <view className='spend-save'>
      <image
        className='spend-save-img'
        src='https://lf3-static.bytednsdoc.com/obj/eden-cn/uhpykheh7uhnuhojvbs/website_spend_bg.png'
      />
      <BalanceCards />
      <ActionButtons />

      <Popup
        ref={popupRef}
        scrollContainerId='foldview'
        maxHeight={680}
        preload={true}
        enterEasingFunction='all ease-in-out'
        enterDuration={1200}
        exitEasingFunction='all ease-in'
        exitDuration={300}
        heightPercent={{
          top: 70,
          init: 30,
          boundaryArea: 10,
        }}
        maskStyle={{
          background: 'black',
          opacity: 0.2,
        }}
      >
        {(popupOptions) => <SpendSave {...popupOptions} />}
      </Popup>
    </view>
  )
}

root.render(<App />)

export default App
```
