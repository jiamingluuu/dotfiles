## API Definition

````typescript
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import type { ForwardedRef, ReactElement } from '@byted-lynx/react'

import type { BaseScrollEvents } from '@lynx-js/lynx-ui-common'

import type { CSSProperties } from '@byted-lynx/type-lynx'

export type Tabs = (props: TabsProps) => ReactElement

type ScrollPropagationBehavior =
  | 'native' // Follows platform default behavior
  | 'propagate' // Always allow scroll propagation
  // | 'propagateAtEdge' // @todo Child scrolls first; parent scrolls on next touch at edge
  | 'preventPropagate' // Never allow scroll propagation

export interface TabsRef {
  /**
   * Slide to the specified tab.
   * @zh 滑动到指定的标签页。
   * @Android
   * @iOS
   */
  selectTab: (
    /**
     * The index to be selected.
     * @zh 要选择的索引。
     * @Android
     * @iOS
     */
    index: number,
    /**
     * If a animation effect needed.
     * @zh 是否需要动画效果。
     * @Android
     * @iOS
     */
    smooth: boolean,
    success?: (res: unknown) => void,
    fail?: (res: unknown) => void,
  ) => void

  /**
   * Scroll the specified tab to the centered position manually.
   * @zh 将指定的 tab 滚动到居中的位置
   * @Android
   * @iOS
   */
  scrollToCenter: (
    /**
     * The index to be selected.
     * @zh 要选择的索引。
     * @Android
     * @iOS
     */
    index: number,
  ) => void

  /**
   * When the version of Lynx SDK in the app is lower than 2.13, manually pass in the 'offsetchange' event and 'change' event to avoid stability issues.
   * @zh 当应用程序中的 Lynx SDK 版本低于 2.13 时，手动传入 'offsetchange' 事件和 'change' 事件以避免稳定性问题。
   * @Android
   * @iOS
   * @example
   * ```tsx
   *  <ViewPager
        scene="viewpager"
        bindoffsetchange={(e: unknown) => {
          tabsRef.current?.legacySDKViewPagerOffsetChange(e)
        }}
        bindchange={(e: unknown) => {
          tabsRef.current?.legacySDKViewPagerChange(e)
        }}
  * ```
  */
  legacySDKViewPagerOffsetChange: (res: unknown) => void
  /**
   * When the version of Lynx SDK in the app is lower than 2.13, manually pass in the 'offsetchange' event and 'change' event to avoid stability issues.
   * @zh 当应用程序中的 Lynx SDK 版本低于 2.13 时，手动传入 'offsetchange' 事件和 'change' 事件以避免稳定性问题。
   * @Android
   * @iOS
   * @example
   * ```tsx
   *  <ViewPager
        scene="viewpager"
        bindoffsetchange={(e:unknown) => {
          tabsRef.current?.legacySDKViewPagerOffsetChange(e)
        }}
        bindchange={(e:unknown) => {
          tabsRef.current?.legacySDKViewPagerChange(e)
        }}
  * ```
  */
  legacySDKViewPagerChange: (res: unknown) => void
}

export interface TabsProps {
  ref?: ForwardedRef<TabsRef>
  /**
 * Inject your tab items.
 * @zh 注入你的标签项。
 * @defaultValue undefined
 * @Android
 * @iOS
 * @example
 * ```tsx
 * <Tabs
      tabs={scollview.map((item1, index1) => (
        <view
          style={{
            width: `${100 + index1 * 10}px`,
            height: '80px',
            background: colorArray[index1 % 5],
            margin: '2px',
            borderRadius: '2px 2px 2px 2px',
            borderColor: 'purple',
          }}
        >
          <text>{`tabs-${index1}`}</text>
        </view>
      ))}
   />
 * ```
 */
  tabs: ReactElement[]
  /**
   * The class apply to the internal container of child view inside scroll-view.
   * @zh 应用于 scroll-view 内子视图的内部容器的类名。
   * @Android
   * @iOS
   */
  containerClass?: string
  /**
 * Inject your linkbar, its width should be set to 100%, Tabs will calculate its width automatically.
 * @zh 注入你的linkbar，它的宽度应设置为100%，Tabs将自动计算其宽度。
 * @defaultValue undefined
 * @Android
 * @iOS
 * @example
 * ```tsx
 * <Tabs
    linkBarHeight="10px"
    linkBar={
      <view
        style={{
          width: '100%',
          height: '10px',
          marginLeft: '5px',
          marginRight: '5px',
          background: 'purple',
        }}
      />
    }
  />
 * ```
 */
  linkBar?: ReactElement
  /**
   * Style for root view
   * @zh 根视图的样式
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  style?: CSSProperties
  /**
   * Style for internal scrollview, be used for RTL and paddings.
   * @zh 内部滚动视图的样式，用于RTL和填充。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  scrollViewStyle?: CSSProperties
  /**
   * The height of the linkBar need to be specified, could be a estimated value.
   * @zh linkBar的高度需要指定，可以是一个估计值。
   * @defaultValue 0
   * @Android
   * @iOS
   */
  linkBarHeight: `${number}px` | `${number}rpx`
  /**
   * The id of the viewpager needs to be specified. Used for global-bind.
   * @zh 需要指定viewpager的id。用于全局绑定。
   * @Android
   * @iOS
   */
  viewpagerId: string

  /**
   * Scroll to the clicked tab smoothly.
   * @zh 平滑地滚动到点击的标签页。
   * @defaultValue 'smooth'
   * @Android
   * @iOS
   */
  selectBehavior?: 'smooth' | 'unsmooth' | 'disable'

  /**
   * Specify the first screen index. Use `selectTab` for updates.
   * @zh 指定第一个屏幕索引。使用 `selectTab` 进行更新。
   * @defaultValue 0
   * @Android
   * @iOS
   */
  firstScreenSelectIndex?: number

  /**
   * Specify enable mts or not, better performance when enable mts
   * @zh 指定是否启用mts，启用mts时性能更好
   * @defaultValue true
   * @Android
   * @iOS
   */
  enableMTS?: boolean

  /**
   * Specify enable rtl or not
   * @zh 指定是否启用 rtl
   * @defaultValue false
   * @Android
   * @iOS
   */
  enableRTL?: boolean

  /**
   * Be used to mark the exposure timing of lazy loading. Please ensure that it is unique throughout the page.
   * @zh 用于标记懒加载的曝光时间。请确保它在整个页面中是唯一的。
   * @defaultValue 'Tabs'
   * @Android
   * @iOS
   * @Harmony
   */
  scene?: string

  /**
   * Specify lazy render or not, better performance when enable lazy
   * @zh 指定是否懒渲染，启用懒渲染时性能更好
   * @defaultValue false
   * @Android
   * @iOS
   */
  lazy?: boolean

  /**
   * Specify spacing between each tab, in pixels
   * @zh 指定每个标签之间的间距，以像素为单位
   * @defaultValue 0
   * @Android
   * @iOS
   * @Harmony
   */
  tabSpacing?: number

  /**
   * show debug log or not
   * @zh 是否显示调试日志
   * @defaultValue false
   * @Android
   * @iOS
   */
  debugLog?: boolean
  /**
   * Controls whether scroll events propagate to parent containers. For now, 'preventPropagate' needs to be used together with temporaryBlockScrollClass and temporaryBlockScrollTag on iOS.
   * @zh 控制滚动事件是否向父级容器传递. 'preventPropagate' 在 iOS 上暂时需与 temporaryBlockScrollClass 和 temporaryBlockScrollTag 配合使用。
   * @experimental Currently, this property has its limits because the full ability has dependency on higher native SDK version. On iOS the 'propagate' only works when the both parent component and this component are set to 'propagate'. And useRefactorList={true} don't support 'propagate'. On Android, the 'preventPropagate' can only works when its parent element is x-swiper and x-viewpager-ng.
   * @defaultValue 'native'
   * @iOS
   * @Android
   */
  scrollPropagationBehavior?: ScrollPropagationBehavior
  /**
   * The specific class name of the container that is blocked when 'scrollPropagationBehavior' is set to be 'preventPropagate', must be informed by the container provider. For now, 'preventPropagate' needs to be used together with temporaryBlockScrollClass and temporaryBlockScrollTag on iOS.
   * This is a temporary props and will be deprecated on new Lynx SDK version.
   * @zh 当 'scrollPropagationBehavior' 设置为 'preventPropagate' 时，指定被阻止的容器类名，必须由容器提供者告知。目前，'preventPropagate' 需要与 temporaryBlockScrollClass 和 temporaryBlockScrollTag 一起使用。
   * @defaultValue 'BDXLynxViewPager'
   * @iOS
   */
  temporaryBlockScrollClass?: string
  /**
   * Used to specify the native container tag that is blocked when 'scrollPropagationBehavior' is set to be 'preventPropagate', corresponding to the Tag attribute of UIView. Needs to be specified by the native container provider. For now, 'preventPropagate' needs to be used together with temporaryBlockScrollClass and temporaryBlockScrollTag on iOS.
   * This is a temporary props and will be deprecated on new Lynx SDK version.
   * @zh 用于指定当 scrollPropagationBehavior 设为 'preventPropagate' 时被阻止滚动的原生容器标签（对应 UIView 的 Tag 属性）。该值需由原生容器提供方指定，且 'preventPropagate' 在 iOS 上暂时需与 temporaryBlockScrollClass 和 temporaryBlockScrollTag 配合使用。
   * @defaultValue 0
   * @iOS
   */
  temporaryBlockScrollTag?: number

  /**
   * Being triggered when scrolling stops.
   * @zh 当滚动tab结束时触发
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onScrollEnd?: (info: { detail: BaseScrollEvents }) => void

  /**
   * Click callback
   * @zh 点击回调
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onClickItem?: (
    /**
     * Clicked index
     * @zh 点击的索引
     * @Android
     * @iOS
     */
    index: number,
  ) => void
  /**
   * Tab change callback
   * @zh 标签页更改回调
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onTabChanged?: (
    /**
     * Changed index
     * @zh 更改的索引
     * @Android
     * @iOS
     */
    index: number,
  ) => void

  /**
   * callback when tab will change, mts tabs only
   * @zh 标签页将更改时执行的回调，仅限mts标签页
   * @eventProperty
   * @param index - the index to be changed
   * @Android
   * @iOS
   * @since 2.16
   */
  onTabWillChange?: (
    /**
     * The index to be changed
     * @zh 将要更改的索引
     * @Android
     * @iOS
     */
    index: number,
  ) => void

  /**
   * When the version of Lynx SDK in the app is lower than 2.16, manually pass in the 'offsetchange' event and 'change' event to avoid stability issues.
   * @zh 当应用程序中的 Lynx SDK 版本低于 2.16 时，手动传入 'offsetchange' 事件和 'change' 事件以避免稳定性问题。
   * @defaultValue false
   * @Android
   * @iOS
   * @example
   * ```tsx
   *  <ViewPager
        scene="viewpager"
        bindoffsetchange={(e:unknown) => {
          tabsRef.current?.legacySDKViewPagerOffsetChange(e)
        }}
        bindchange={(e:unknown) => {
          tabsRef.current?.legacySDKViewPagerChange(e)
        }}/>
   * ```
   */
  legacyCompatible?: boolean

  /**
  * When the version of Lynx SDK in the app is lower than 2.16, manually pass in the 'offsetchange' event and 'change' event to avoid stability issues.
  * @zh 当应用程序中的 Lynx SDK 版本低于 2.16 时，手动传入 'offsetchange' 事件和 'change' 事件以避免稳定性问题。
  * @defaultValue false
  * @deprecated use `legacyCompatible` instead
  * @Android
  * @iOS
  * @example
  * ```tsx
  *  <ViewPager
       scene="viewpager"
       bindoffsetchange={(e:unknown) => {
         tabsRef.current?.legacySDKViewPagerOffsetChange(e)
       }}
       bindchange={(e:unknown) => {
         tabsRef.current?.legacySDKViewPagerChange(e)
       }}/>
  * ```
  */
  legacyCompatiable?: boolean
}
````
