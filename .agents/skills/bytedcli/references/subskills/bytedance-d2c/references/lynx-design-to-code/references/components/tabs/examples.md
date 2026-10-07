## Examples

### Basic

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import type { TabsRef } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'
/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_tabs_basic.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const tabsRef = useRef<TabsRef>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const pagerItem = ['1', '2', '3', '4', '5', '6', '7', '8']

  return (
    <view
      style={{
        width: '100%',
      }}
    >
      <Tabs
        ref={tabsRef}
        viewpagerId='viewpager'
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((_item, index) => (
          <text
            key={index}
            style={{
              margin: '0px 10px 0px 10px',
              padding: '10px',
              border: '1px black',
              borderRadius: '10px',
              background: selectedIndex === index ? '#12345678' : 'white',
            }}
          >
            {`tabs-${index}`}
          </text>
        ))}
        linkBarHeight='10px'
        linkBar={
          <view
            style={{
              width: '100%',
              height: '5px',
              background: 'yellow',
              borderRadius: '5px',
              display: 'flex',
              justifyContent: 'center',
            }}
          >
            <view
              style={{
                width: '18px',
                height: '5px',
                background: 'black',
                borderRadius: '2px',
              }}
            />
          </view>
        }
      />
      <ViewPager style={{ width: '100%', height: '400px' }}>
        {pagerItem.map((_item, index) => (
          <view
            key={index}
            style={`width:100%;height:580rpx;background:${
              colorArray[index % 5]
            }`}
          >
            <text>{`pager-${index}`}</text>
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```

### JSTabs

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import type { TabsRef } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_tabs_spacing.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const tabsRef = useRef<TabsRef>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(2)
  const pagerItem = [
    'home',
    'X',
    'bytedance',
    'vlog',
    'Is Lynx easy to use?',
    'Not bad',
    'graphic',
    'chill',
  ]

  return (
    <view style={{ width: '100%' }}>
      <Tabs
        ref={tabsRef}
        viewpagerId='viewpager'
        tabSpacing={20}
        enableMTS={false}
        firstScreenSelectIndex={2}
        legacyCompatible
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((item, index) => (
          <text
            key={index}
            style={{
              padding: '10px 0px 10px 0px',
              background: selectedIndex === index ? '#12345678' : 'white',
            }}
          >
            {item}
          </text>
        ))}
        linkBarHeight='10px'
        linkBar={
          <view
            style={{
              width: '100%',
              height: '5px',
              background: 'black',
              borderRadius: '5px',
            }}
          />
        }
      />
      <ViewPager
        viewpagerId='viewpager'
        initialSelectIndex={2}
        style={{ width: '100%', height: '400px' }}
        onOffsetChange={(e: unknown) => {
          tabsRef.current?.legacySDKViewPagerOffsetChange(e)
        }}
        onPageChange={(e: unknown) => {
          tabsRef.current?.legacySDKViewPagerChange(e)
        }}
      >
        {pagerItem.map((_item, index) => (
          <view
            key={index}
            style={`width:100%;height:580rpx;background:${
              colorArray[index % 5]
            }`}
          >
            <text>{`pager-${index}`}</text>
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```

### Multiple

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useState } from '@byted-lynx/react'

import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_tabs_multiple.webp}
 */

function App() {
  const colorArray = ['orange', 'red', 'purple', 'green', 'yellow']
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const [innerSelectedIndex, setInnerSelectedIndex] = useState<number>(0)

  const pagerItem = [
    'home',
    'X',
    'bytedance',
    'vlog',
    'Is Lynx easy to use?',
    'Not bad',
    'graphic',
    'chill',
  ]

  return (
    <view style={{ width: '100%' }}>
      <Tabs
        viewpagerId='outer'
        scene='outer'
        tabSpacing={20}
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((item, index) => (
          <text
            key={index}
            style={{
              padding: '10px 0px 10px 0px',
              background: selectedIndex === index ? '#12345678' : 'white',
            }}
          >
            {item}
          </text>
        ))}
        linkBarHeight='10px'
        linkBar={
          <view
            style={{
              width: '100%',
              height: '5px',
              background: 'black',
              borderRadius: '5px',
            }}
          />
        }
      />
      <ViewPager
        viewpagerId='outer'
        style={{ width: '100%', height: '400px' }}
        bounces={false}
      >
        {pagerItem.map((_itemOuter, indexOuter) => (
          <view
            key={indexOuter}
            style={`width:100%;height:580rpx;padding:10px;background:${
              colorArray[indexOuter % 5]
            }`}
          >
            <text>{`outer-pager-${indexOuter}`}</text>
            {indexOuter === 0 && (
              <view>
                <Tabs
                  viewpagerId='inner'
                  scene='inner'
                  onTabChanged={(index: number) => {
                    setInnerSelectedIndex(index)
                  }}
                  tabs={pagerItem.map((_itemInner, index) => (
                    <text
                      key={index}
                      style={{
                        margin: '0px 10px 0px 10px',
                        padding: '10px',
                        border: '1px black',
                        borderRadius: '10px',
                        background: innerSelectedIndex === index
                          ? '#12345678'
                          : 'white',
                      }}
                    >
                      {`tabs-${index}`}
                    </text>
                  ))}
                  linkBarHeight='10px'
                  linkBar={
                    <view
                      style={{
                        width: '100%',
                        height: '5px',
                        background: 'black',
                        borderRadius: '5px',
                      }}
                    />
                  }
                />
                <ViewPager
                  viewpagerId='inner'
                  style={{ width: '100%', height: '400px' }}
                  bounces={false}
                >
                  {pagerItem.map((_itemInner, index) => (
                    <view
                      key={index}
                      style={`width:100%;height:580rpx;border:20px ${
                        colorArray[(9 - index) % 5]
                      };background:white`}
                    >
                      <text>{`inner-pager-${index}`}</text>
                    </view>
                  ))}
                </ViewPager>
              </view>
            )}
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```

### PosterGallery

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { PosterGallery } from './PosterGallery'

function App() {
  return (
    <view>
      <PosterGallery />
    </view>
  )
}

root.render(<App />)

export default App
```

### Presentation

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import type { TabsRef } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'
import './styles.css'
/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_tabs_basic.webp}
 */
function App() {
  // const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const tabs = [
    'Full Moon',
    'Waning Gibbous',
    'Waning Crescent',
    'Waxing Gibbous',
    'First Quarter',
    'Waxing Crescent',
    'New Moon',
  ]
  const tabsRef = useRef<TabsRef>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const pagerItem = ['1', '2', '3', '4', '5', '6', '7']

  return (
    <view class='container lunaris-dark'>
      <Tabs
        ref={tabsRef}
        viewpagerId='viewpager'
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((_item, index) => (
          <text
            key={index}
            class={`tab-item ${
              selectedIndex === index ? 'tab-item-selected' : ''
            }`}
          >
            {tabs[index]}
          </text>
        ))}
        linkBarHeight='0px'
        linkBar={
          <view class='link-bar'>
            <view class='link-bar-inner' />
          </view>
        }
      />
      <view className='gap' />
      <ViewPager
        className='view-pager'
        style={{ marginTop: '20px', height: '600px' }}
      >
        {pagerItem.map((_item, index) => (
          <view class='pager-item-wrapper' key={index + ''}>
            <view
              key={index}
              className='pager-item'
            >
              <text className='pager-item-text-tab'>
                Tabs
              </text>
              <text className='pager-item-text-package'>
                @lynx-js/lynx-ui
              </text>
            </view>
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```

### RTL

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useState } from '@byted-lynx/react'

import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_tabs_multiple.webp}
 */

function App() {
  const colorArray = ['orange', 'red', 'purple', 'green', 'yellow']
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const [innerSelectedIndex, setInnerSelectedIndex] = useState<number>(0)

  const pagerItem = [
    'home',
    'X',
    'bytedance',
    'vlog',
    'Is Lynx easy to use?',
    'Not bad',
    'graphic',
    'chill',
  ]

  return (
    <view style={{ width: '100%', direction: 'rtl' }}>
      <Tabs
        viewpagerId='outer'
        scene='outer'
        tabSpacing={20}
        enableRTL={true}
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((item, index) => (
          <text
            key={index}
            style={{
              padding: '10px 0px 10px 0px',
              background: selectedIndex === index ? '#12345678' : 'white',
            }}
          >
            {item}
          </text>
        ))}
        linkBarHeight='10px'
        linkBar={
          <view
            style={{
              width: '100%',
              height: '5px',
              background: 'black',
              borderRadius: '5px',
            }}
          />
        }
      />
      <ViewPager
        viewpagerId='outer'
        style={{ width: '100%', height: '400px' }}
        bounces={false}
      >
        {pagerItem.map((_itemOuter, indexOuter) => (
          <view
            key={indexOuter}
            style={`width:100%;height:580rpx;padding:10px;background:${
              colorArray[indexOuter % 5]
            }`}
          >
            <text>{`outer-pager-${indexOuter}`}</text>
            {indexOuter === 0 && (
              <view>
                <Tabs
                  viewpagerId='inner'
                  scene='inner'
                  enableRTL={true}
                  onTabChanged={(index: number) => {
                    setInnerSelectedIndex(index)
                  }}
                  tabs={pagerItem.map((_itemInner, index) => (
                    <text
                      key={index}
                      style={{
                        margin: '0px 10px 0px 10px',
                        padding: '10px',
                        border: '1px black',
                        borderRadius: '10px',
                        background: innerSelectedIndex === index
                          ? '#12345678'
                          : 'white',
                      }}
                    >
                      {`tabs-${index}`}
                    </text>
                  ))}
                  linkBarHeight='10px'
                  linkBar={
                    <view
                      style={{
                        width: '100%',
                        height: '5px',
                        background: 'black',
                        borderRadius: '5px',
                      }}
                    />
                  }
                />
                <ViewPager
                  viewpagerId='inner'
                  style={{ width: '100%', height: '400px' }}
                  bounces={false}
                >
                  {pagerItem.map((_itemInner, index) => (
                    <view
                      key={index}
                      style={`width:100%;height:580rpx;border:20px ${
                        colorArray[(9 - index) % 5]
                      };background:white`}
                    >
                      <text>{`inner-pager-${index}`}</text>
                    </view>
                  ))}
                </ViewPager>
              </view>
            )}
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```

### Spacing

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import type { TabsRef } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_tabs_spacing.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const tabsRef = useRef<TabsRef>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(0)
  const pagerItem = [
    'home',
    'X',
    'bytedance',
    'vlog',
    'Is Lynx easy to use?',
    'Not bad',
    'graphic',
    'chill',
  ]

  return (
    <view style={{ width: '100%' }}>
      <Tabs
        ref={tabsRef}
        viewpagerId='viewpager'
        tabSpacing={20}
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((item, index) => (
          <text
            key={index}
            style={{
              padding: '10px 0px 10px 0px',
              background: selectedIndex === index ? '#12345678' : 'white',
            }}
          >
            {item}
          </text>
        ))}
        linkBarHeight='10px'
        linkBar={
          <view
            style={{
              width: '100%',
              height: '5px',
              background: 'black',
              borderRadius: '5px',
            }}
          />
        }
      />
      <ViewPager style={{ width: '100%', height: '400px' }}>
        {pagerItem.map((_item, index) => (
          <view
            key={index}
            style={`width:100%;height:580rpx;background:${
              colorArray[index % 5]
            }`}
          >
            <text>{`pager-${index}`}</text>
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```
