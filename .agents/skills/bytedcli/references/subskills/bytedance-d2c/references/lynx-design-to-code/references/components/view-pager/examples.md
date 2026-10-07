## Examples

### AutoHeight

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_viewpager_autoheight.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const pagerItem = [
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Scream.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/dune.webp',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/The Social Network.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Rocketeer.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Halloween.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Batman.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/47 Lord of War.jpg',
  ]
  return (
    <ViewPager
      style={{
        width: '100%', // unspecified the height of the ViewPager
      }}
    >
      {pagerItem.map((item, index) => (
        <view
          key={index}
          style={{
            width: '100%',
            padding: '20px',
            backgroundColor: `${colorArray[index % 5]}`,
          }}
        >
          <text
            style={{
              fontSize: '50px',
              padding: '50px',
            }}
          >
            {index.toString()}
          </text>
          <image
            style={{
              width: '100%',
              height: '300px',
            }}
            src={item.toString()}
          />
        </view>
      ))}
    </ViewPager>
  )
}

root.render(<App />)

export default App
```

### Basic

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_viewpager_basic.webp}
 */
function App() {
  const pagerItem = [
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Scream.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/dune.webp',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/The Social Network.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Rocketeer.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Halloween.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/Batman.jpg',
    'https://lf3-static.bytednsdoc.com/obj/eden-cn/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/posters/47 Lord of War.jpg',
  ]

  return (
    <ViewPager
      style={{
        width: '100%',
        height: '400px', // specify the height of the ViewPager
      }}
    >
      {pagerItem.map((item, index) => (
        <image
          key={index}
          style={{
            width: '100%',
            height: '100%',
            padding: '20px',
          }}
          src={item.toString()}
        />
      ))}
    </ViewPager>
  )
}

root.render(<App />)

export default App
```

### DynamicHeight

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { DynamicHeight } from './DynamicHeight'

function App() {
  return (
    <view>
      <DynamicHeight />
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

import { root } from '@byted-lynx/react'

import { List } from '@lynx-js/lynx-ui-list'

import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_viewpager_list.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const pagerItem = ['1', '2', '3', '4', '5']
  const listData = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
  ]
  return (
    <ViewPager
      style={{
        width: '100%',
        height: '100%', // specify the height of the ViewPager
      }}
    >
      {pagerItem.map((_item, index) => (
        <List
          key={index}
          style={{ width: '100%', height: '100%' }}
          listId='listBasic'
          name='listBasic'
          listType='single'
          spanCount={1}
          scrollOrientation={'vertical'}
          useRefactorList={true}
        >
          {listData.map((value: number) => (
            <list-item
              item-key={value.toString()}
              id={value.toString()}
              key={value.toString()}
            >
              <view
                style={{
                  width: '100%',
                  height: '400px',
                  borderWidth: '2px',
                  borderColor: `${colorArray[index % 5]}`,
                }}
              >
                <text style={{ fontSize: '30px' }}>
                  {'list-item-' + value.toString()}
                </text>
                <view
                  style={{
                    width: '100%',
                    height: '200px',
                    backgroundColor: `${colorArray[index % 5]}`,
                  }}
                  id={`inner${value.toString()}`}
                />
              </view>
            </list-item>
          ))}
        </List>
      ))}
    </ViewPager>
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

import {
  root,
  runOnMainThread,
  useEffect,
  useMainThreadRef,
  useMemo,
  useRef,
} from '@byted-lynx/react'

import { mix, springValue } from '@lynx-js/motion'
import type { MotionValue } from '@lynx-js/motion'

import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'
import type {
  ViewPagerOffsetChangeEvent,
  ViewPagerRef,
} from '@byted-lynx/lynx-ui-view-pager'

import { RectangleCard } from './RectangleCard'
import { ViewPagerContext } from './ViewPagerContext'

import './index.scss'

function App() {
  const viewPagerRef = useRef<ViewPagerRef>(null)
  const data: { height: number, letter: string }[] = [
    { height: 600, letter: 'V' },
    { height: 460, letter: 'I' },
    { height: 600, letter: 'E' },
    { height: 400, letter: 'W' },
    { height: 500, letter: 'P' },
    { height: 600, letter: 'A' },
    { height: 500, letter: 'G' },
    { height: 400, letter: 'E' },
    { height: 500, letter: 'R' },
  ]

  const heights = useMainThreadRef<Record<string, number>>({})
  const springValueRef = useMainThreadRef<MotionValue<number>>()

  const updateItemHeight = (key: string, height: number) => {
    'main thread'
    console.info('updateItemHeight before', key, height, heights.current)
    heights.current[key] = height
    console.info('updateItemHeight after', key, height, heights.current)
  }

  const viewPagerValue = useMemo(() => {
    return {
      updateItemHeight,
    }
  }, [updateItemHeight])

  function bindSpringValue() {
    'main thread'
    springValueRef.current ??= springValue<number>(0, {
      duration: 0.1,
      bounce: 0,
    })

    springValueRef.current.on('change', value => {
      console.log('spring bounce', value)
      lynx.querySelector('#viewpager')?.setStyleProperty(
        'height',
        `${value}px`,
      )
    })
  }

  useEffect(() => {
    runOnMainThread(bindSpringValue)()
  }, [])

  const handleOffsetChange = (e: { detail: ViewPagerOffsetChangeEvent }) => {
    'main thread'

    const index = Math.floor(e.detail.offset)
    const progress = e.detail.offset - index

    if (index >= data.length - 1 || index < 0) {
      return
    }

    const heightMixer = mix(
      heights.current[`${index}`],
      heights.current[`${index + 1}`],
    )

    springValueRef.current?.set(heightMixer(progress))
  }

  return (
    <view className='lunaris-dark view-pager-container'>
      <ViewPagerContext.Provider value={viewPagerValue}>
        <ViewPager
          lazyOptions={{
            enableLazy: false,
          }}
          ref={viewPagerRef}
          style={{ width: '100%', height: '720px' }}
          className='view-pager'
          MTOnOffsetChange={handleOffsetChange}
        >
          {data.map(({ height, letter }, index) => (
            <RectangleCard
              key={`${index}`}
              cardKey={`${index}`}
              letter={letter}
              height={height}
            />
          ))}
        </ViewPager>
      </ViewPagerContext.Provider>
    </view>
  )
}

root.render(<App />)
```
