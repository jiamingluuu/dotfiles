## API Definition

```typescript
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import type { ForwardedRef, ReactElement } from '@byted-lynx/react'

import type { BaseGesture } from '@byted-lynx/gesture-runtime'
import type { CSSProperties, XOverlayNGProps } from '@byted-lynx/type-lynx'

import type { PopupStatus } from '../src/index'

export interface RenderFunction {
  /**
   * The gesture that needs to be bound to the scroll container inside the popup. After binding, the scroll container inside the popup follows the rule that when it is not at the top, it will drag the popup first, and when it is at the top, it can scroll the inner scroll container.
   * @zh Popup内滚动容器需要绑定的手势，绑定后弹窗内的滚动容器遵循未到达顶部时，优先拖拽Popup，到达顶部后可以滚动内部滚动容器
   * @Android
   * @iOS
   * @Harmony
   */
  'main-thread:gesture': BaseGesture
  /**
   * The gesture that needs to be bound to the non-scrollable container inside the popup. After binding, the non-scrollable container inside the popup will only respond to dragging.
   * @zh Popup内非滚动容器当需要拖拽时需要绑定的手势，绑定后该节点仅响应拖拽
   * @Android
   * @iOS
   * @Harmony
   */
  'draggableGesture': BaseGesture
}
export type Popup = (props: PopupProps) => ReactElement

export interface PopupRef {
  /**
   * Open the popup. Popup position: 0 (center), 1 (top), -1 (bottom). Default is center.
   * @zh 打开弹窗, 弹窗位置 0（中心）1（顶部）-1（底部）,默认是中心
   * @defaultValue 0
   * @Android
   * @iOS
   * @Harmony
   */
  open: (position?: PopupStatus) => void

  /**
   * Close popup
   * @zh 关闭弹窗
   * @Android
   * @iOS
   * @Harmony
   */
  close: () => void

  /**
   * Translate popup to specified position, 0(center) 1(top) -1(bottom) | "px" | "%" | "rpx"
   * @zh 移动弹窗到指定位置，0（中心）1（顶部）-1（底部）
   * @Android
   * @iOS
   * @Harmony
   */
  translateTo: (position: PopupStatus | string) => void
}

export interface TouchEvent {
  detail: {
    /**
     * x coordinate of touch event
     * @zh 触摸事件的 x 坐标
     */
    y: number
    /**
     * y coordinate of touch event
     * @zh 触摸事件的 y 坐标
     */
    x: number
  }
}

export interface OnDragCallback {
  /**
   * 0 - begin 1 - drag 2 - end
   * @zh 0 - 开始 1 - 拖动 2 - 结束
   */
  state: number
  /**
   * x and y coordinate
   * @zh x 和 y 坐标
   */
  touchEvent: TouchEvent
  /**
   * The top of popup
   * @zh 弹窗的顶部位置
   */
  top: number
}

export interface HeightPercent {
  /**
   * The init offset percentage or absolute value (e.g. "200px") that the popup, base line is maxHeight
   * @zh 弹窗的初始偏移百分比或绝对值（例如 "200px"），基准线是 maxHeight   * @defaultValue 60
   * @Android
   * @iOS
   * @Harmony
   */
  init: number | `${number}px` | `${number}%` | `${number}rpx`

  /**
   * The maximum offset percentage or absolute value (e.g. "400px") that the popup can drag, base line is maxHeight
   * @zh 弹窗可拖动的最大偏移百分比或绝对值（例如 "400px"），基准线是 maxHeight
   * @defaultValue 100
   * @Android
   * @iOS
   * @Harmony
   */
  top: number | `${number}px` | `${number}%` | `${number}rpx`

  /**
   * The minimum offset percentage or absolute value (e.g. "0px") that the popup can drag, base line is maxHeight
   * @zh 弹窗可拖动的最小偏移百分比或绝对值（例如 "0px"），基准线是 maxHeight
   * @defaultValue 0
   * @Android
   * @iOS
   * @Harmony
   */
  bottom?: number | `${number}px` | `${number}%` | `${number}rpx`

  /**
   * The boundary offset percentage or absolute value (e.g., "20px") for the popup's non-inertial slide release rebound. When the non-inertial slide release rebound area is within position - boundaryArea to + boundaryArea, it will trigger a rebound back to the current position; otherwise, it will move to the next position. The baseline is maxHeight.
   * @zh 弹窗无惯性滑动的松手回弹的边界偏移百分比或绝对值（例如 "20px"），当无惯性滑动松手回弹的区域在position - boundaryArea / + boundaryArea 之间时，会触发回弹到当前的position为止，否则会进入下一个位置，基准线是 maxHeight
   * @defaultValue 10
   * @Android
   * @iOS
   * @Harmony
   */
  boundaryArea?: number | `${number}px` | `${number}%` | `${number}rpx`

  /**
   * The speed threshold for inertial sliding rebound. When the release speed is greater than this value, it will slide to the next position; when less than this value, it will rebound to the current position
   * @zh 惯性滑动回弹阈值：弹窗有惯性滑动时的速度阈值，当松手大于该速度时会滑动到下一个position，当小于该速度时会回弹至当前的position
   * @defaultValue 5(px/s)
   * @Android
   * @iOS
   * @Harmony
   */
  flingThreshold?: number
}

export interface PopupProps {
  ref?: ForwardedRef<PopupRef>

  /**
   * The id of root scroll container(required)
   * @zh 根节点滚动容器的 ID（必需）
   * @Android
   * @iOS
   * @Harmony
   */
  scrollContainerId: string

  /**
   * children of popup.
   * @zh 弹窗的子元素
   * @Android
   * @iOS
   * @Harmony
   */
  children: (prop: RenderFunction) => ReactElement

  /**
   * The ID of the popup content, which needs to be set when autoHeight is true, to get the content height
   * @zh 弹窗内容的 ID, 在 autoHeight 为 true 时需要设置，用于获取内容高度
   * @Android
   * @iOS
   * @Harmony
   */
  contentId?: string

  /**
   * Auto height of popup, when set to true, you need to specified contentId prop, the height of popup will be the height of content, The drag area is between bottom and the current height, initHeight and maxHeight are no longer valid
   * @zh 自动弹窗高度，设置为 true 时，需要指定 contentId 属性，弹窗高度会根据内容高度动态变化，拖动区域在底部和当前高度之间，initHeight 和 maxHeight 不再有效
   * @Android
   * @iOS
   * @Harmony
   */
  autoHeight?: boolean

  /**
   * Style for mask
   * @zh 遮罩的样式
   * @Android
   * @iOS
   * @Harmony
   */
  maskStyle?: CSSProperties

  /**
   * Style for popup content
   * @zh 弹窗内容的样式
   * @Android
   * @iOS
   * @Harmony
   */
  contentStyle?: CSSProperties

  /**
   * Preload when popup is create, it will speed up shown when visible is true
   * @zh 弹窗创建时预加载，这样在 visible 为 true 时会加快显示速度
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  preload?: boolean

  /**
   * When set to true, click mask will dismiss popup.
   * @zh 设置为 true 时，点击遮罩会关闭弹窗
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  closeOnMaskClick?: boolean

  /**
   * When set to true, mask event will through to children
   * @zh 当设置为true的时候，遮罩事件会传递到子元素
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  maskEventThrough?: boolean

  /**
   * if enable drag or not
   * @zh 是否启用拖动
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  enableDrag?: boolean

  /**
   * if enable bounces or not when touch up
   * @zh 是否需要松手回弹
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  enableBounces?: boolean

  /**
   * If true, allows the component to overflow the bottom boundary when dragged.
   * @zh 如果为 true，则允许组件在拖动时超出底部边界。
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  allowDragBeyondBottom?: boolean

  /**
   * Stops the propagation of gesture events when the scroll container is at the top.
   * @zh 当滚动容器滚动到顶部时，停止滚动容器的手势事件传播。
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  stopGesturePropagationWhenScrollAtTop?: boolean

  /**
   * Dynamically adjusts the exit animation based on the content height. When enabled, the on-screen animation duration remains constant. As a result, the greater the content height, the faster the exit velocity to ensure the animation completes within the fixed time
   * @zh 根据内容高度动态调整退出动画。启用后，屏幕上的动画持续时间保持不变。因此，内容高度越大，退出速度越快，以确保动画在固定时间内完成。
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  adjustExitTransitionByContentHeight?: boolean

  /**
   * Theoretically, this is the maximum height that can be dragged to. When using overlayMode, the screen height needs to be passed in. When not using overlayMode, the height of the current LynxView needs to be passed in.
   * @zh 理论上能拖拽到的最大高度，当使用overlayMode时需要传入屏幕高度，当不使用overlayMode时，需要传入当前LynxView的高度
   * @defaultValue screenHeight
   * @Android
   * @iOS
   * @Harmony
   */
  maxHeight: number

  /**
   * Nodes fixed at the bottom of the popup will not be affected by dragging
   * @zh 固定在弹窗底部的节点，不会受到拖动影响
   * @Android
   * @iOS
   * @Harmony
   */
  bottomNode?: ReactElement

  /**
   * Whether to allow dragging the Popup when touching the internal scroll container area
   * @zh 是否允许触摸在内部滚动容器区域时可拖拽Popup
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  enableScrollContainerDraggable?: boolean

  /**
   * It is recommended to use a full-screen transparent container for the popup, as it offers better performance. Alternatively, you can also choose to use the popup through an overlay
   * @zh 建议为弹窗使用全屏透明容器，因为这样性能更好。或者，你也可以选择通过overlay使用弹窗，请参考overlay-ng mode官网描述
   * @Android
   * @iOS
   * @Harmony
   * @docTypeFallback 'spark' | 'bullet' | 'bulletPopup' | (string & {})
   */
  bytedanceOverlayMode?: 'spark' | 'bullet' | 'bulletPopup' | (string & {})

  /**
   * Whether to enable the debug log
   * @zh 是否启用调试日志
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  internalDebugLog?: boolean

  /**
   * show animation transition
   * @zh 显示动画过渡效果
   * @defaultValue 'all ease-out'
   * @Android
   * @iOS
   * @Harmony
   */
  enterEasingFunction?: string

  /**
   * hide animation transition
   * @zh 隐藏动画过渡效果
   * @defaultValue 'all ease-out'
   * @Android
   * @iOS
   * @Harmony
   */
  exitEasingFunction?: string

  /**
   * enter animation duration(ms)
   * @zh 进入动画持续时间（毫秒）
   * @defaultValue 300
   * @Android
   * @iOS
   * @Harmony
   */
  enterDuration?: number

  /**
   * exit animation duration(ms)
   * @zh 退出动画持续时间（毫秒）
   * @defaultValue 300
   * @Android
   * @iOS
   * @Harmony
   */
  exitDuration?: number
  /**
   * If you want to use gesture, pass it here.
   * @zh 如果你想使用手势，请使用这个属性
   * @Android
   * @iOS
   * @Harmony
   */
  'main-thread:gesture'?: BaseGesture

  /**
   * height percentage of Popup
   * @zh 弹窗的高度百分比
   * @Android
   * @iOS
   * @Harmony
   */
  heightPercent?: HeightPercent

  /**
   * bounces transition
   * @zh 松手回弹效果动画
   * @defaultValue 'all 0.1s ease-out'
   * @Android
   * @iOS
   * @Harmony
   */
  bouncesTransition?: string

  /**
   * mask transition timing function, e.g. cubic-bezier(0.25, 0.1, 0.25, 1)
   * @zh 遮罩的过渡动画时间函数，例如 cubic-bezier(0.25, 0.1, 0.25, 1)
   * @Android
   * @iOS
   * @Harmony
   */
  maskTransitionTimingFunction?: string

  /**
   * x-overlay-ng props for the popup
   * @zh 在弹窗的overlay id, 用于在设置bytedanceOverlayMode下指定弹窗的overlay props
   * @defaultValue {}
   * @Android
   * @iOS
   * @Harmony
   */
  overlayProps?: Partial<XOverlayNGProps>

  /**
   * drag callback
   * @zh 拖动回调
   * @Android
   * @iOS
   * @Harmony
   */
  onDrag?: (eventParam: OnDragCallback) => void

  /**
   * popup position callback
   * @zh 弹窗位置回调
   * @Android
   * @iOS
   * @Harmony
   */
  onPopupPositionChange?: (
    /**
     * 0(center) 1(top) -1(bottom) 4(close)
     * @zh 0(中间) 1(顶部) -1(底部) 4(关闭)
     * @Android
     * @iOS
     * @Harmony
     */
    position: number,
  ) => void

  /**
   * 弹窗高度变化回调
   * @param height 弹窗的高度
   * @returns
   */
  onPopupTopChange?: (height: number) => void

  /**
   * clicking the back button or sliding back
   * @zh 是否左滑或者点击返回键
   * @Android
   */
  onRequestClose?: () => void
}
```
