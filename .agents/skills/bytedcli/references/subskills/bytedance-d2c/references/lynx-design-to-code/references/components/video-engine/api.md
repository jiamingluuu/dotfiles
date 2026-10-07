## API Definition

```typescript
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import type { ForwardedRef, ReactElement } from '@byted-lynx/react'

import type { CSSProperties } from '@byted-lynx/type-lynx'

export type VideoEngine = (props: VideoEngineProps) => ReactElement

export type VideoEnginePlaybackCallback = (
  success: boolean,
  errCode?: number,
  errMsg?: string,
) => void

export interface VideoEngineRef {
  /**
   * Start playing. You should start play after resource redirect (after `onRedirected`)
   * @zh 开始播放。你应该在资源重定向后（`onRedirected`）开始播放
   * @remarks When this operation is successful, it only means that the operation was successfully submitted to the player, and does not mean that the player status has changed.
   * @Android
   * @iOS
   * @Harmony
   */
  play: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     * @Harmony
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Pause playing
   * @zh 暂停播放
   * @remarks When this operation is successful, it only means that the operation was successfully submitted to the player, and does not mean that the player status has changed.
   * @Android
   * @iOS
   * @Harmony
   */
  pause: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Stop playing
   * @zh 停止播放
   * @remarks When this operation is successful, it only means that the operation was successfully submitted to the player, and does not mean that the player status has changed.
   * @Android
   * @iOS
   * @Harmony
   */
  stop: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Seek
   * @zh 定位播放位置
   * @remarks When this operation is successful, it only means that the operation was successfully submitted to the player, and does not mean that the player status has changed.
   * @Android
   * @iOS
   */
  seek: (
    position: number,
    play: boolean,
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Replay, it is recommended to call it after the playback ends.
   * @zh 重新播放，建议在播放结束后调用
   * @remarks When this operation is successful, it only means that the operation was successfully submitted to the player, and does not mean that the player status has changed.
   * @Android
   * @iOS
   */
  replay: (
    /**
     * Whether to play after replay. If not, it will be stopped at the first frame.
     * @zh 是否在重新播放后开始播放。如果为 false，则会在第一帧停止。
     * @Android
     * @iOS
     */
    play: boolean,
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Prepare manually.
   * @zh 手动准备。
   * @Android
   * @iOS
   * @Harmony
   */
  prepare: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Get playback duration.
   * @zh 获取播放时长。
   * @Android
   * @iOS
   * @Harmony
   */
  getDuration: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: (
      success: boolean,
      /**
       * Duration, in ms.
       * @zh 时长，以毫秒为单位
       * @Android
       * @iOS
       */
      duration: number,
      errCode?: number,
      errMsg?: string,
    ) => void,
  ) => void
  /**
   * Enter full screen. It need client impl, {@link https://lynx.bytedance.net/docs/frontend/components/x-video-engine | see more}.
   * @zh 进入全屏。需要客户端实现，{@link https://lynx.bytedance.net/docs/frontend/components/x-video-engine | 了解更多}.
   * @Android
   * @iOS
   */
  enterFullScreen: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Exit full screen. It need client impl, {@link https://lynx.bytedance.net/docs/frontend/components/x-video-engine | see more}.
   * @zh 退出全屏。需要客户端实现，{@link https://lynx.bytedance.net/docs/frontend/components/x-video-engine | 了解更多}.
   * @Android
   * @iOS
   */
  exitFullScreen: (
    /**
     * Invocation callback，errCode refer to {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @zh 调用回调，errCode 参考 {@link https://lynx.bytedance.net/docs/frontend/lynx-api/selector-query/selector-query | SelectorQuery}
     * @Android
     * @iOS
     */
    callback?: VideoEnginePlaybackCallback,
  ) => void
  /**
   * Reset the Video. It is required to reset the Video if it is reused. Will be deprecated after being refactored by MTS.
   * @zh 重置视频。如果要重复使用视频，则需要重置视频。重构后将弃用。
   * @Android
   * @iOS
   * @Harmony
   */
  reset: () => void

  /**
   * Handle the poster manually
   * @zh 手动处理海报
   * @Android
   * @iOS
   * @Harmony
   */
  operatePoster: (display: boolean) => void
}

export enum VideoEngineOption {
  // add video engine option by requirement
  // @zh 根据要求添加视频引擎选项
  PLAYER_OPTION_ENABLE_DASH = '17',
}

export interface VideoEngineProps {
  ref?: ForwardedRef<VideoEngineRef>
  /**
   * Style for wrapper, especially for border-radius
   * @zh 包装器的样式，特别用于设置圆角
   * @defaultValue undefined
   * @Android
   * @iOS
   * @Harmony
   */
  style?: CSSProperties
  /**
   * Be used to select the `x-video-engine`. Please ensure that it is unique throughout the page.
   * @zh 用于选择 `x-video-engine`。请确保在整个页面中唯一。
   * @defaultValue 'videoengine'
   * @Android
   * @iOS
   * @Harmony
   */
  videoEngineId?: string
  /**
   * Be used to mark the exposure timing. Please ensure that it is unique throughout the page.
   * @zh 用于标记曝光时间点。请确保在整个页面中唯一。
   * @defaultValue 'videoengine'
   * @Android
   * @iOS
   * @Harmony
   */
  scene?: string
  /**
   * The specified video playback source uses the videoModel data structure recommended by the company to play the resource and is expressed by JSONString.
   * @zh 指定视频播放源，使用公司推荐的视频模型数据结构播放资源，表现为 JSON 字符串。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  videoModel?: string
  /**
   * Use vid to specify the video playback source. Most hosts use vid to play. You need to pass in token and domain at the same time. Toutiao can support only passing in vid.
   * @zh 使用 vid 指定视频播放源。大多数主机会使用 vid 来播放。你需要同时传入 token 和 domain。头条支持仅传入 vid。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  videoId?: string
  /**
   * To play with vid, you need to pass in both token and domain. Toutiao can support passing in only vid
   * @zh 使用 vid 播放视频需要同时传入 token 和 domain。头条支持仅传入 vid。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  token?: string
  /**
   * To play with vid, you need to pass in both token and domain. Toutiao can support passing in only vid. {@link https://lynx.bytedance.net/docs/frontend/components/x-video-engine | see more}.
   * @zh 使用 vid 播放视频需要同时传入 token 和 domain。头条支持仅传入 vid。{@link https://lynx.bytedance.net/docs/frontend/components/x-video-engine | 查看更多}.
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  domain?: string
  /**
   * For the specified video playback source, once play-url is set, the player will try to load the resource asynchronously. Before bindredirect, all playback control logic will not take effect.
   * @zh 指定视频播放源，一旦设置 play-url，播放器将尝试异步加载资源。在绑定重定向之前，所有播放控制逻辑将无效。
   * @defaultValue undefined
   * @Android
   * @iOS
   * @Harmony
   */
  playUrl?: string
  /**
   * Poster. Will be dismissed after playing.
   * @zh 海报。播放后将被取消显示。
   * @defaultValue undefined
   * @Android
   * @iOS
   * @Harmony
   */
  poster?: string
  /**
   * Play automatically after stream data changes.
   * @zh 流数据变化后自动播放。
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  autoPlay?: boolean
  /**
   * Specifies the video cropping/scaling mode.
   * @zh 指定视频裁剪/缩放模式。
   * @defaultValue 'aspectFit'
   * @Android
   * @iOS
   * @Harmony
   */
  objectfit?: 'aspectFit' | 'aspectFill' | 'scaleToFill'
  /**
   * Rotate or not in full-screen mode
   * @zh 全屏模式下是否旋转
   * @defaultValue 'landscape'
   * @Android
   * @iOS
   * @since 2.18
   */
  fullscreenMode?: 'landscape' | 'portrait'
  /**
   * Live player should muted.
   * @zh 是否静音实时播放器。
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  mute?: boolean
  /**
   * Loop play. After the video starts playing, loop changes will not change the current play/pause status of the video.
   * @zh 循环播放。视频开始播放后，循环状态变化不会改变视频的当前播放/暂停状态。
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  loop?: boolean
  /**
   * Automatically pre-render the player (showing the first frame) after resource preparation is completed
   * @zh 在资源准备完成后自动预渲染播放器（显示首帧）
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  autoPrepare?: boolean
  /**
   * Automatically pre-render the player (showing the first frame) after resource preparation is completed
   * @zh 在资源准备完成后自动预渲染播放器（显示首帧）
   * @defaultValue false
   * @Android
   * @iOS
   * @Harmony
   */
  initTime?: number
  /**
   * The key specified by video preloading(not work for playerType === 'light'). If not filled in, it is the md5 of the URL for iOS and the hashcode for Android. {@link https://bytedance.larkoffice.com/wiki/ZS89weXVcijlHRkuVBzclMOznOg | Video preloading solution }
   * @zh 指定视频预加载的键（不支持 playerType === 'light'）。如果未填写，则为 iOS 的 URL 的 md5 和 Android 的 hashcode。{@link https://bytedance.larkoffice.com/wiki/ZS89weXVcijlHRkuVBzclMOznOg | 视频预加载方案 }
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  preloadKey?: string
  /**
   * Video prefetch cache size. {@link https://bytedance.larkoffice.com/wiki/ZS89weXVcijlHRkuVBzclMOznOg | Video preloading solution }
   * @zh 视频预取缓存大小。{@link https://bytedance.larkoffice.com/wiki/ZS89weXVcijlHRkuVBzclMOznOg | 视频预加载方案 }
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  cacheSize?: number
  /**
   * For player monitoring.
   * @zh 用于播放器监控。
   * @defaultValue undefined
   * @Android
   * @iOS
   * @Harmony
   */
  tag?: string
  /**
   * For player monitoring.
   * @zh 用于播放器监控。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  subTag?: string
  /**
   * Specify whether to pause the video when the LynxView exits the background or moves out of the screen to prevent sound leakage
   * @zh 指定当 LynxView 退出背景或移出屏幕后是否暂停视频，以防止声音泄漏
   * @defaultValue false
   * @Android
   * @iOS
   */
  pauseOnHide?: boolean
  /**
   * To customize engine parameters, you need to refer to TTVideoEngine key definition and pass in the correct value type. The client needs to pay attention to it.
   * @zh 要自定义引擎参数，需要参考 TTVideoEngine 键定义并传入正确的值类型。客户端需要注意。
   * @defaultValue undefined
   * @Android
   * @iOS
   */
  playerOption?: Record<
    VideoEngineOption,
    `@encode(${string | number | boolean}, ${
      | '[c]'
      | 'i'
      | 'l'
      | 'f'
      | 'd'
      | 'b'})`
  >
  /**
   * Specify the playback speed.
   * @zh 指定播放速度
   * @defaultValue 1.0
   * @Android
   * @iOS
   */
  playbackSpeed?: number
  /**
   * Specify the volume, range: [0.0, 1.0]
   * @zh 指定音量，范围：[0.0, 1.0]
   * @defaultValue 1.0
   * @Android
   * @iOS
   * @Harmony
   */
  volume?: number
  /**
   * Whether to use the default resource loader (Forest、Gecko) to download resources
   * @zh 是否使用默认资源加载器（Forest、Gecko）下载资源
   * @defaultValue true
   * @Android
   * @iOS
   */
  skipRedirection?: boolean
  /**
   * Execute pending ops automatically
   * @zh 自动执行待处理的操作
   * @defaultValue true
   * @Android
   * @iOS
   * @Harmony
   */
  cachingPendingOps?: boolean
  /**
   * Custom player backend. The host can inject its own player. `preloadKey` is not supported for playerType === 'light'.
   * @zh 自定义播放器后端。宿主可注入其自己的播放器。playerType === 'light' 不支持 `preloadKey`。
   * @defaultValue 'default'
   * @Android
   * @iOS
   * @docTypeFallback 'default' | 'light' | (string & {})
   */
  playerType?: 'default' | 'light' | (string & {})
  /**
   * Whether to load player instances on demand for performance optimization, commonly used in list scenarios, no need to set in other cases
   * @zh 是否按需加载播放器实例，用于性能优化，常用于列表场景，其他情况无需设置
   * @Android
   * @iOS
   * @Harmony
   */
  attached?: boolean
  /**
   * Specify the playback resolution.
   * @zh 指定播放分辨率。
   * @defaultValue 'auto'
   * @Android
   * @iOS
   * @since 3.3
   */
  resolution?:
    | 'auto'
    | '240p'
    | '360p'
    | '480p'
    | '540p'
    | '720p'
    | '1080p'
    | '4k'
    | 'hdr'
    | '2k'
    | '1080p 50fps'
    | '2k 50fps'
    | '4k 50fps'
    | '1080p 60fps'
    | '2k 60fps'
    | '4k 60fps'
    | '1080p 120fps'
    | '2k 120fps'
    | '4k 120fps'
  /**
   * The type of the media
   * @zh 媒体的类型
   * @defaultValue 'Video'
   * @Android
   * @iOS
   * @Harmony
   */
  as?: 'Video' | 'Audio'
  /**
   * The player starts playing.
   * @zh 播放器开始播放。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onPlay?: () => void
  /**
   * The player is paused.
   * @zh 播放器暂停。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onPause?: () => void
  /**
   * The player is stopped.
   * @zh 播放器停止。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onStop?: () => void
  /**
   * The player is seek.
   * @zh 播放器搜索。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onSeek?: (willPlay: boolean) => void
  /**
   * The player finish playing.
   * @zh 播放器播放结束。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onEnded?: () => void
  /**
   * The src is changed
   * @zh 源文件发生变化
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onSrcChanged?: () => void
  /**
   * The player receives an error.
   * @zh 播放器接收到错误信息。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onError?: (e: { errorCode: number, errorMsg: string }) => void
  /**
   * The player's progress is updated
   * @zh 播放器进度更新
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onTimeUpdate?: (e: { detail: { current: number, total: number } }) => void
  /**
   * If you access gecko resources, the loading is asynchronous
   * @zh 如果访问 gecko 资源，加载是异步的
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onRedirected?: () => void
  /**
   * Triggered when the video starts rendering the first frame
   * @zh 视频开始渲染首帧时触发
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   * @Harmony
   */
  onFirstFrame?: () => void
  /**
   * The player is ready to play.
   * @zh 播放器准备好播放。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onPrepared?: () => void
  /**
   * The player is visible. `scene` and `videoengineId` should be specified.
   * @zh 播放器可见。应该指定 `scene` 和 `videoengineId`。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onAppear?: () => void
  /**
   * The player is invisible. `scene` and `videoengineId` should be specified.
   * @zh 播放器不可见。应该指定 `scene` 和 `videoengineId`。
   * @defaultValue undefined
   * @eventProperty
   * @Android
   * @iOS
   */
  onDisappear?: () => void
}
```
