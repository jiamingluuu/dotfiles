## API Definition

```typescript
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import type { ForwardedRef, ReactElement } from '@byted-lynx/react'

import type { BaseGesture } from '@byted-lynx/gesture-runtime'

export type FoldView = (props: FoldViewProps) => ReactElement

export interface FoldViewRef {
  /**
   * Stop refreshing animation and reset the pull-down refresh effect.
   * @zh 停止刷新动画并重置下拉刷新效果。
   * @Android
   * @iOS
   */
  stopRefresh: (
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    success?: (res: any) => void,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    fail?: (res: any) => void,
  ) => void
  /**
   * Scroll to top position.
   * @zh 滚动到顶部位置。
   * @Android
   * @iOS
   */
  scrollToTop: (
    /**
     * Scroll with animation
     * @zh 滚动动画
     * @Android
     * @iOS
     */
    animated: boolean,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    success?: (res: any) => void,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    fail?: (res: any) => void,
  ) => void
  /**
   * Scroll to folding position, the header will be invisible.
   * @zh 滚动到折叠位置，头部将不可见。
   * @Android
   * @iOS
   */
  scrollToSticky: (
    /**
     * Scroll with animation
     * @zh 滚动动画
     * @Android
     * @iOS
     */
    animated: boolean,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    success?: (res: any) => void,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    fail?: (res: any) => void,
  ) => void
  /**
   * Scroll to any position
   * @zh 滚动到任意位置
   * @Android
   * @iOS
   */
  scrollTo: (
    /**
     * Scroll to offset
     * @zh 滚动到偏移量
     * @Android
     * @iOS
     */
    offset: `${number}px` | `${number}rpx`,
    /**
     * Scroll with animation
     * @zh 滚动动画
     * @Android
     * @iOS
     */
    animated: boolean,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    success?: (res: any) => void,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    fail?: (res: any) => void,
  ) => void

  /**
   * Scroll to the element in headers with the specified id.
   * @zh 滚动到 headers 中指定 ID 的元素。
   * @Android
   * @iOS
   */
  scrollIntoView: (
    /**
     * The id of the element to scroll to. In headers.
     * @zh 要滚动到的元素的 ID。需要在 headers 中。
     * @Android
     * @iOS
     */
    id: string,
    /**
     * Scroll with animation
     * @zh 滚动动画
     * @Android
     * @iOS
     */
    animated: boolean,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    success?: (res: any) => void,
    // biome-ignore lint/suspicious/noExplicitAny:type-lynx should upgrade
    fail?: (res: any) => void,
  ) => void
}

export interface FoldViewProps {
  ref?: ForwardedRef<FoldViewRef>
  /**
   * The id of the foldview.
   * @zh 折叠视图的 ID。
   * @defaultValue "foldview"
   * @Android
   * @iOS
   */
  foldviewId?: string
  /**
   * The nodes in headers
   * @zh 头部的节点
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  headers?: ReactElement[]
  /**
   * The node in toolbar
   * @zh 工具栏的节点
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  toolbar?: ReactElement
  /**
   * The node in slot
   * @zh 插槽的节点
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  slot?: ReactElement
  /**
   * The refresh header, it is necessary to set it only when the FoldView needs to be refreshed by pulling down actions. Notice, when a pull-down refresh is required in the slot, `x-refresh-view` needs to be added inside the slot, and `refreshInSlot` should be set to true.
   * @zh 刷新头部，仅在需要通过下拉动作刷新 FoldView 时设置。注意，当插槽中需要下拉刷新时，需要在插槽中添加 `x-refresh-view`，并设置 `refreshInSlot` 为 true。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  refreshHeader?: ReactElement
  /**
   * Enable iOS bounces spring effect
   * @zh 启用 iOS 弹性弹跳效果
   * @defaultValue true
   * @iOS
   */
  bounces?: boolean
  /**
   * Enable vertical scroll.
   * @zh 启用垂直滚动。
   * @defaultValue true
   * @Android
   * @iOS
   */
  enableScroll?: boolean
  /**
   * This attribute controls the z-index relationship between the header and the slot when overflow support is required. When it's true, the header's z-index is higher than the slot's, and when it's false, the header's z-index is lower than the slot's.
   * @zh 控制溢出支持时头部和插槽之间的 z-index 关系。当为 true 时，头部的 z-index 高于插槽，当为 false 时，头部的 z-index 低于插槽。
   * @defaultValue false
   * @Android
   * @iOS
   * @since 2.11
   */
  headerOverSlot?: boolean

  /**
   * Enable FoldView Header and Slot overflow HitTest fallback.
   * @zh 启用FoldView Header和Slot 溢出HitTest回退。
   * @defaultValue false
   * @Android
   * @iOS
   * @since 3.6
   */
  experimentalOverflowHitTestFallback?: boolean
  /**
   * It is necessary to be true only when a pull-down refresh is required in the slot, works together with the `x-refresh-view` inside the slot.
   * @zh 仅当插槽中需要下拉刷新时需要为 true，与插槽内的 `x-refresh-view` 一起使用。
   * @defaultValue false
   * @Android
   * @iOS
   */
  refreshInSlot?: boolean
  /**
   * Display the scroll bar.
   * @zh 显示滚动条。
   * @defaultValue false
   * @iOS
   */
  scrollBarEnable?: boolean
  /**
   * The granularity of the event response for `onOffsetChange`, which triggers when the scroll distance exceeds the scrollable distance's granularity.
   * @zh 在滚动距离超过可滚动距离的粒度时，触发 `onOffsetChange` 事件响应的粒度。
   * @defaultValue 0.01
   * @Android
   * @iOS
   */
  granularity?: number
  /**
   * Some options are required while the FoldView is in a bullet/spark popup.
   * @zh 在 FoldView 位于子弹/火花弹窗中时需要的某些选项。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  popupOptions?: {
    /**
     * Name is required while the FoldView is in a bullet/spark popup.
     * @zh 在 FoldView 位于子弹/火花弹窗中时需要的名称。
     * @Android
     * @iOS
     */
    name: string
    /**
     * If the bullet/spark popup could transform between half-screen and full-screen, the value need to be true.
     * @zh 如果子弹/火花弹窗可以在半屏和全屏之间转换，则需要将值设置为 true。
     * @Android
     * @iOS
     */
    enableHalfToFullScreen: boolean
  }
  /**
   * On Android, if the FoldView is put in an Native scroll container, this value should be true.
   * @zh 在 Android 上，如果 FoldView 被放置在原生滚动容器中，应该设置此值为 true。
   * @defaultValue false
   * @Android
   */
  scrollWithNative?: boolean

  /**
   * If you want to use gesture, pass it here.
   * @zh 如果想使用 gesture api，请传入该属性。
   * @iOS
   * @Android
   */
  'main-thread:gesture'?: BaseGesture
  /**
   * The pull-down action triggered.
   * @zh 下拉动作触发。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onRefresh?: () => void
  /**
   * Triggered when this Refresh is pulling down
   * @zh 在下拉刷新期间触发。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onPullToRefresh?: (
    /**
     * Is it being dragged.
     * @zh 是否正在拖动。
     * @Android
     * @iOS
     */
    dragging: boolean,
    /**
     * Pulling percent.
     * @zh 拉动百分比。
     * @Android
     * @iOS
     * @deprecated Use `percent` instead.
     */
    precent: number,
    /**
     * Pulling percent.
     * @zh 拉动百分比。
     * @Android
     * @iOS
     */
    percent: number,
  ) => void
  /**
   * Being triggered when the folding action happens.
   * @zh 在折叠动作发生时触发。
   * @eventProperty
   * @Android
   * @iOS
   */
  onOffsetChange?: (e: {
    /**
     * Represents the total folding distance, which is header.height - toolbar.height, in px
     * @zh 代表总折叠距离，为 header.height - toolbar.height，单位 px。
     * @Android
     * @iOS
     */
    height: number
    /**
     * Represents the absolute folding offset value, in px
     * @zh 代表绝对折叠偏移值，单位 px。
     * @Android
     * @iOS
     */
    offset: number
  }) => void
  /**
   * Being triggered when the folding action happens.
   * @zh 在折叠动作发生时触发。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */

  /**
   * Being triggered when the folding action happens. Accepts main-thread function only.
   * @zh 在折叠动作发生时触发。
   * @eventProperty
   * @Android
   * @iOS
   */
  'main-thread:onOffsetChange'?: (e: {
    /**
     * Represents the total folding distance, which is header.height - toolbar.height, in px
     * @zh 代表总折叠距离，为 header.height - toolbar.height，单位 px。
     * @Android
     * @iOS
     */
    height: number
    /**
     * Represents the absolute folding offset value, in px
     * @zh 代表绝对折叠偏移值，单位 px。
     * @Android
     * @iOS
     */
    offset: number
  }) => void
  /**
   * Being triggered when the header is completely invisible.
   * @zh 当头部完全不可见时触发。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  onSticky?: () => void
  /**
   * Being triggered when the header is visible.
   * @zh 当头部可见时触发。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  onLeaveSticky?: () => void
}
```
