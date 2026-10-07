## API Definition

````typescript
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import type { ReactElement } from '@byted-lynx/react'

import type { CSSProperties } from '@byted-lynx/type-lynx'

export type SVG = (props: SVGProps) => ReactElement

export interface SVGProps {
  /**
   * The content of the SVG
   * @zh SVG 的内容
   * @example
   * ```
   * <SVG
   *   content={`<svg viewBox="0 0 100 100">
   *      <rect x="10" y="20" width="50" height="50" fill="#ccff66" stroke="#ff0000"/>
   *      <rect x="10" y="30" width="50" height="50" fill="none"/>
   *      <circle cx="50" cy="50" r="20" fill="#ff000088" stroke-width="10" stroke="#00ff0088" />
   *      <line x1="0" x2="0" y1="0" y2="100" stroke="black"/>
   *      </svg>`}
   *   width="374px"
   *   height="125px"
   * />
   * ```
   * @Android
   * @iOS
   * @Harmony
   */
  content?: string
  /**
   * The width of the SVG
   * @zh SVG 的宽度
   * @Android
   * @iOS
   * @Harmony
   */
  width: `${number}rpx` | `${number}px` | `${number}ppx` | `${number}%`
  /**
   * The height of the SVG
   * @zh SVG 的高度
   * @Android
   * @iOS
   * @Harmony
   */
  height: `${number}rpx` | `${number}px` | `${number}ppx` | `${number}%`
  /**
   * The src of the SVG
   * @zh SVG 的图片路径
   * @Android
   * @iOS
   * @Harmony
   */
  src?: string
  /**
   * The styles for the SVG
   * @zh SVG 的样式
   * @Android
   * @iOS
   * @Harmony
   */
  style?: CSSProperties
}
````
