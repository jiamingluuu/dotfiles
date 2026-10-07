## Examples

### List

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { List } from '@lynx-js/lynx-ui-list'

import { FoldView } from '@byted-lynx/lynx-ui-fold-view'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_foldview_list.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const headerItem = ['1', '2', '3', '4', '5']

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
    <FoldView
      style={{
        width: '100%',
        height: '100%',
      }}
      headers={headerItem.map((_item, index) => (
        <view
          key={index}
          style={{
            width: '100%',
            height: '100px',
            backgroundColor: `${colorArray[index % 5]}`,
          }}
        >
          <text style={{ fontSize: '30px' }}>{`header-${index}`}</text>
        </view>
      ))}
      slot={
        <List
          style={{ width: '100%', height: '100%' }}
          listId='listBasic'
          name='listBasic'
          listType='single'
          spanCount={1}
          bounces
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
                  width: '100vw',
                  height: '400px',
                  borderWidth: '2px',
                  borderColor: 'red',
                }}
              >
                <text style={{ fontSize: '30px' }}>
                  {'list-item-' + value.toString()}
                </text>
                <view
                  style='width:100vw; height:200px;background-color:green'
                  id={`inner${value.toString()}`}
                />
              </view>
            </list-item>
          ))}
        </List>
      }
    />
  )
}

root.render(<App />)

export default App
```

### RefreshFold

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { ScrollView } from '@lynx-js/lynx-ui-scroll-view'

import { FoldView } from '@byted-lynx/lynx-ui-fold-view'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_foldview_refresh_fold.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const headerItem = ['1', '2', '3', '4', '5']
  const scrollItem = ['1', '2', '3', '4', '5']

  const _listData = [
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
    <FoldView
      refreshHeader={
        <view style={{ width: '100%', backgroundColor: 'white' }}>
          <text style={{ fontSize: '50px' }}>refreshing...</text>
        </view>
      }
      style={{
        width: '100%',
        height: '100%',
      }}
      headers={headerItem.map((_item, index) => (
        <view
          key={index}
          style={{
            width: '100%',
            height: '100px',
            backgroundColor: `${colorArray[index % 5]}`,
          }}
        >
          <text style={{ fontSize: '30px' }}>{`header-${index}`}</text>
        </view>
      ))}
      slot={
        <ScrollView
          style={{ width: '100%', height: '100%' }}
          scrollOrientation='vertical'
        >
          {scrollItem.map((_item, index) => (
            <view
              key={index}
              style={`width:100%;height:580rpx;background:${
                colorArray[index % 5]
              }`}
            >
              <text style={{ fontSize: '30px' }}>
                {`scroll-item-in-slot-${index}`}
              </text>
            </view>
          ))}
        </ScrollView>
      }
    />
  )
}

root.render(<App />)

export default App
```

### RefreshPage

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { List } from '@lynx-js/lynx-ui-list'

import { FoldView } from '@byted-lynx/lynx-ui-fold-view'
import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import type { TabsRef } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_foldview_refresh_page.webp}
 */
function App() {
  const tabsRef = useRef<TabsRef>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(0)

  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const headerItem = ['1', '2', '3']
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
    <FoldView
      style={{
        width: '100%',
        height: '100%',
      }}
      refreshInSlot
      headers={headerItem.map((_item, index) => (
        <view
          key={index}
          style={{
            width: '100%',
            height: '100px',
            backgroundColor: `${colorArray[index % 5]}`,
          }}
        >
          <text style={{ fontSize: '30px' }}>{`header-${index}`}</text>
        </view>
      ))}
      slot={
        <view
          style={{
            height: '100%',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
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
                  background: 'black',
                  borderRadius: '5px',
                }}
              />
            }
            style={{
              flexShrink: 0,
            }}
          />
          <ViewPager
            style={{
              width: '100%',
              height: '100%', // specify the height of the ViewPager
              flexShrink: 1,
            }}
          >
            {pagerItem.map((_item, index) => (
              <x-refresh-view
                style={{ width: '100%', height: '100%' }}
                key={index}
              >
                <x-refresh-header>
                  <view style={{ width: '100%', backgroundColor: 'white' }}>
                    <text style={{ fontSize: '50px' }}>refreshing...</text>
                  </view>
                </x-refresh-header>
                <List
                  style={{ width: '100%', height: '100%' }}
                  bounces
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
              </x-refresh-view>
            ))}
          </ViewPager>
        </view>
      }
    />
  )
}

root.render(<App />)

export default App
```

### ViewPager

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { List } from '@lynx-js/lynx-ui-list'

import { FoldView } from '@byted-lynx/lynx-ui-fold-view'
import { Tabs } from '@byted-lynx/lynx-ui-tabs'
import type { TabsRef } from '@byted-lynx/lynx-ui-tabs'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_foldview_viewpager.webp}
 */
function App() {
  const tabsRef = useRef<TabsRef>(null)
  const [selectedIndex, setSelectedIndex] = useState<number>(0)

  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const headerItem = ['1', '2', '3', '4', '5']
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
    <FoldView
      style={{
        width: '100%',
        height: '100%',
      }}
      headers={headerItem.map((_item, index) => (
        <view
          key={index}
          style={{
            width: '100%',
            height: '100px',
            backgroundColor: `${colorArray[index % 5]}`,
          }}
        >
          <text style={{ fontSize: '30px' }}>{`header-${index}`}</text>
        </view>
      ))}
      slot={
        <view
          style={{
            height: '100%',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
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
                  background: 'black',
                  borderRadius: '5px',
                }}
              />
            }
            style={{
              flexShrink: 0,
            }}
          />
          <ViewPager
            style={{
              width: '100%',
              height: '100%', // specify the height of the ViewPager
              flexShrink: 1,
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
        </view>
      }
    />
  )
}

root.render(<App />)

export default App
```
