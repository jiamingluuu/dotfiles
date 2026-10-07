# Lynx UI Tabs SKILL.md

`<Tabs>` is a component that display the titles of different pages. Users can click the titles to switch the pages. Usually used with `<ViewPager>` to display the content of each page.

## 1. Common Use Cases

- **Tabbed layouts**: Display the titles of different pages, use `<Tabs>` for titles and `<ViewPager>` for content.

- **Complex scrolling coordination**: Provide localized horizontal switching within vertically scrolling pages, se `<Tabs>` for titles and `<ViewPager>` for content: embed it in the slot of `<FoldView>`.

- **Stage tabs**: Stage or schedule labels can still be `<Tabs>` when the row has an active indicator and switches a peer content pane. Use a normal flex row only when the row is passive metadata with no tab behavior.

## 2. Basic Usage

`<Tabs>` is always used with `<ViewPager>`, while `<ViewPager>` is used to display the content of each page, `<Tabs>` is used to display the titles of different pages.

```tsx
import { useState } from '@byted-lynx/react'
import { Tabs, ViewPager } from '@byted-lynx/lynx-ui'

function App() {
  const pagerItem = ['1', '2', '3', '4', '5', '6', '7']
  const [selectedIndex, setSelectedIndex] = useState(0)

  return (
    <view
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Tabs
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
      />
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
    </view>
  )
}
```

## 3. Example for Linkbar

`linkbar` is the line that indicates the current selected tab. It is usually displayed below the titles.

```tsx
import { useState } from '@byted-lynx/react'
import { Tabs, ViewPager } from '@byted-lynx/lynx-ui'

function App() {
  const pagerItem = ['1', '2', '3', '4', '5', '6', '7']
  const [selectedIndex, setSelectedIndex] = useState(0)

  return (
    <view
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Tabs
        viewpagerId='viewpager'
        tabSpacing={20}
        onTabChanged={(index: number) => {
          setSelectedIndex(index)
        }}
        tabs={pagerItem.map((_item, index) => (
          <text
            key={index}
            style={{
              padding: '10px 0px 10px 0px',
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
      <ViewPager viewpagerId='viewpager' style={{ width: '100%', height: '400px' }}>
        {pagerItem.map(item => (
          <view style={{ width: '100%', height: '100%' }}><text>{item}</text></view>
        ))}
      </ViewPager>
    </view>
  )
}
```

## 4. Critical Development Advices

- **MUST**: The `tabs` prop is required. It is an array of React elements. Each element is a tab title. Their selection state should be controllable by the `onTabWillChange` or `onTabChanged` events.
- **MUST**: Set a literal `viewpagerId` on `<Tabs>`. The paired `<ViewPager>` should use the same explicit `viewpagerId`; a single default `<ViewPager>` may omit it only when `<Tabs viewpagerId='viewpager'>`.
- **MUST**: Every tab title must have a matching non-empty `<ViewPager>` peer page. If static evidence only shows the active pane, reuse the active pane content for hidden peer pages instead of generating blank or opacity-hidden pages.
- **MUST**: Put `<Tabs>` in a width-bounded container, or set `style.width` / a width class on `<Tabs>`.
- **MUST**: Use `tabSpacing`, margin, or padding for tab spacing. Do not force every tab title to the same large width unless the design really has equal-width tabs.
- **MUST NOT**: Do not give tab title elements large equal widths to align static metadata to the left and right edges. Native Tabs measures tab titles for click regions and `linkBar` movement; static status or schedule text should be rendered as a normal layout row.
- **MUST**: Provide `linkBar` for real tabs with an active indicator. Do not remove `linkBar` or draw the active indicator inside each tab title; the native `linkBar` is what follows tab changes.
- **MUST**: The `linkBarHeight` prop only supports px and rpx unit. It reserves bottom space for the native linkbar and can be an estimated value; it does not need to equal the visual bar's CSS height. `0px` is only for intentionally overlaying the indicator without extra padding.
- **MUST**: The CSS property `width` of the `linkBar` slot must be `100%`. If you need to specify the width of the `linkBar` slot, you can set any `width` you want inside the `linkBar` slot (in its children).
- **MUST NOT**: Please do not set `position: fixed` or `z-index` in any children and grandchildren of `<Tabs>`, unless you need to make them fix to the root of the Page.
- **Notice**: The difference between `onTabWillChange` and `onTabChanged` events is that `onTabWillChange` is called before the tab is changed, while `onTabChanged` is called after the tab is changed.
