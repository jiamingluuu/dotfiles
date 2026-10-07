## Examples

### Basic

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { ScrollView } from '@lynx-js/lynx-ui-scroll-view'

import { Button } from '@byted-lynx/lynx-ui-button'
import { VideoEngine } from '@byted-lynx/lynx-ui-video-engine'
import type { VideoEngineRef } from '@byted-lynx/lynx-ui-video-engine'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_video_engine_basic.webp}
 */
function App() {
  const videoRef = useRef<VideoEngineRef>(null)
  const [url, setUrl] = useState<string>(
    'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4',
  )
  return (
    <view style={{ width: '100%', height: '100%' }}>
      <VideoEngine
        ref={videoRef}
        style={{ width: '100%', height: '200px' }}
        autoPlay={true}
        autoPrepare={true}
        skipRedirection
        fullscreenMode='landscape'
        poster={'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/230px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'}
        playUrl={url}
      />
      <ScrollView
        style={{ width: '100%', height: '80px' }}
        scrollOrientation='horizontal'
        scene='button'
        estimatedItemStyle={{ width: '100px', height: '100%' }}
      >
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'play'}
          onClick={() => {
            videoRef.current?.play()
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'pause'}
          onClick={() => {
            videoRef.current?.pause()
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'stop'}
          onClick={() => {
            videoRef.current?.stop()
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'replay'}
          onClick={() => {
            videoRef.current?.seek(0, true)
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'seekTo 5000'}
          onClick={() => {
            videoRef.current?.seek(5000, true)
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'changeSrc'}
          onClick={() => {
            if (url === 'https://media.w3.org/2010/05/sintel/trailer.mp4') {
              setUrl(
                'https://v-akamai-boei18n.bytedance.net/video/tos/boei18n/tos-boei18n-o-0000/675f95d6eb9f4e9d8391402ee1d8cc2f/?br=1504&a=1180&l=02162104232217000000000000000000000ffff0ae70a6e642b68&rc=amY7dG5zOTZ2NDMzZzw2M0ApOHd5ZGQ0a2s3ZjMzaDRoeWcycXNeXi5lZTFgLS1iLmJzc2RgNW5obTMwcC4tLWE2MC06Yw%3D%3D',
              )
            } else {
              setUrl('https://media.w3.org/2010/05/sintel/trailer.mp4')
            }
          }}
        />
      </ScrollView>
    </view>
  )
}

root.render(<App />)

export default App
```

### Marquee

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef } from '@byted-lynx/react'

import { VideoEngine } from '@byted-lynx/lynx-ui-video-engine'
import type { VideoEngineRef } from '@byted-lynx/lynx-ui-video-engine'
import { ViewPager } from '@byted-lynx/lynx-ui-view-pager'
import type { ViewPagerChangeEvent } from '@byted-lynx/lynx-ui-view-pager'
/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_video_engine_marquee.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const pagerItem = ['1', '2', '3']
  const videoRefs = useRef<(VideoEngineRef | null)[]>([])

  return (
    <view style={{ width: '100%', height: '100%' }}>
      <ViewPager
        style={{ width: '100%', height: '500px' }}
        scene='viewpager'
        onPageWillChange={(e: { detail: ViewPagerChangeEvent }) => {
          videoRefs.current.map((videoRef, index) => {
            if (index === e.detail.index) {
              videoRef?.play()
            } else {
              videoRef?.pause()
            }
          })
        }}
      >
        {pagerItem.map((_item, index) => (
          <view
            key={index}
            style={{
              width: '100%',
              height: '100%',
              padding: '20px',
              backgroundColor: `${colorArray[index % 5]}`,
            }}
          >
            <VideoEngine
              ref={ele => {
                videoRefs.current[index] = ele
              }}
              style={{ width: '100%', height: '100%' }}
              autoPlay={false}
              autoPrepare={true}
              skipRedirection
              fullscreenMode='landscape'
              poster={'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/230px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'}
              playUrl={index % 2
                ? 'https://media.w3.org/2010/05/sintel/trailer.mp4'
                : 'https://v-akamai-boei18n.bytedance.net/video/tos/boei18n/tos-boei18n-o-0000/675f95d6eb9f4e9d8391402ee1d8cc2f/?br=1504&a=1180&l=02162104232217000000000000000000000ffff0ae70a6e642b68&rc=amY7dG5zOTZ2NDMzZzw2M0ApOHd5ZGQ0a2s3ZjMzaDRoeWcycXNeXi5lZTFgLS1iLmJzc2RgNW5obTMwcC4tLWE2MC06Yw%3D%3D'}
            />
          </view>
        ))}
      </ViewPager>
    </view>
  )
}

root.render(<App />)

export default App
```

### Pagination

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useEffect, useRef, useState } from '@byted-lynx/react'

import { VideoEngine } from '@byted-lynx/lynx-ui-video-engine'
import type { VideoEngineRef } from '@byted-lynx/lynx-ui-video-engine'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_video_engine_paginatioin.webp}
 */
function App() {
  const colorArray = ['red', 'purple', 'orange', 'green', 'yellow']
  const pagerItem = [
    'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4',
    'http://www.w3school.com.cn/example/html5/mov_bbb.mp4',
    'https://www.w3schools.com/html/movie.mp4',
    'https://media.w3.org/2010/05/sintel/trailer.mp4',
    'https://v-akamai-boei18n.bytedance.net/video/tos/boei18n/tos-boei18n-o-0000/675f95d6eb9f4e9d8391402ee1d8cc2f/?br=1504&a=1180&l=02162104232217000000000000000000000ffff0ae70a6e642b68&rc=amY7dG5zOTZ2NDMzZzw2M0ApOHd5ZGQ0a2s3ZjMzaDRoeWcycXNeXi5lZTFgLS1iLmJzc2RgNW5obTMwcC4tLWE2MC06Yw%3D%3D',
  ]
  const videoRefs = useRef<(VideoEngineRef | null)[]>([])

  const [position, setPosition] = useState<number>(0)

  useEffect(() => {
    // videoRefs.current[position]?.play()
  }, [position])

  return (
    <view style={{ width: '100%', height: '100%' }}>
      <list
        style={{ width: '100%', height: '700px' }}
        vertical-orientation
        experimental-disable-platform-implementation={true}
        preload-buffer-count={1}
        custom-list-name={'list-container'}
        item-snap={{ factor: 0.0, offset: 0 }}
        // @ts-expect-error expected
        bindsnap={e => {
          // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
          let { position } = e.detail
          if (position >= pagerItem.length) {
            position = pagerItem.length - 1
          }
          // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
          setPosition(position)
          videoRefs.current.map((_videoRef, index) => {
            if (index === position) {
              // videoRefs.current[index]?.play()

              // videoRef?.play(() => {
              //   // videoRef?.operatePoster(false)
              // })
            } else {
              // videoRef?.pause(() => {
              //   videoRef?.reset()
              // })
              // videoRef?.operatePoster(true)
            }
          })
        }}
      >
        {pagerItem.map((item, index) => (
          <list-item
            key={index}
            item-key={item}
            style={{
              width: '100%',
              height: '300px',
              padding: '2px',
              backgroundColor: `${colorArray[index % 5]}`,
            }}
            bindtap={() => [videoRefs.current[index]?.play()]}
          >
            <VideoEngine
              ref={ele => {
                videoRefs.current[index] = ele
              }}
              style={{ width: '100%', height: '100%' }}
              autoPlay={true}
              focusedInList={index === position}
              autoPrepare={true}
              skipRedirection
              objectfit='aspectFill'
              fullscreenMode='landscape'
              poster={'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/230px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'}
              playUrl={item}
            />
          </list-item>
        ))}
      </list>
    </view>
  )
}

root.render(<App />)

export default App
```

### TikTok

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root } from '@byted-lynx/react'

import { TikTok } from './TikTok'

function App() {
  return <TikTok />
}

root.render(<App />)

export default App
```

### VideoModel

```tsx
// Copyright 2025 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

import { root, useRef, useState } from '@byted-lynx/react'

import { ScrollView } from '@lynx-js/lynx-ui-scroll-view'

import { Button } from '@byted-lynx/lynx-ui-button'
import { VideoEngine } from '@byted-lynx/lynx-ui-video-engine'
import type { VideoEngineRef } from '@byted-lynx/lynx-ui-video-engine'

/**
 * preview {@link https://lf0-fast-deliver-inner.bytedance.net/obj/eden-internal/zalzzh-ukj-lapzild-shpjpmmv-eufs/ljhwZthlaukjlkulzlp/lynx_ui_video_engine_basic.webp}
 */
function App() {
  const videoRef = useRef<VideoEngineRef>(null)
  const [_url, _setUrl] = useState<string>(
    'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4',
  )
  return (
    <view style={{ width: '100%', height: '100%' }}>
      <VideoEngine
        ref={videoRef}
        style={{ width: '100%', height: '200px' }}
        autoPlay={true}
        autoPrepare={true}
        skipRedirection
        fullscreenMode='landscape'
        videoModel='{"status":10,"message":"success","video_id":"demo-video-id","video_list":{"video_1":{"definition":"720p","vtype":"mp4","main_url":"https://example.com/demo-video.mp4"}}}'
        poster={'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/230px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'}
      />
      <ScrollView
        style={{ width: '100%', height: '80px' }}
        scrollOrientation='horizontal'
        scene='button'
        estimatedItemStyle={{ width: '100px', height: '100%' }}
      >
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'play'}
          onClick={() => {
            videoRef.current?.play()
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'pause'}
          onClick={() => {
            videoRef.current?.pause()
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'stop'}
          onClick={() => {
            videoRef.current?.stop()
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'replay'}
          onClick={() => {
            videoRef.current?.seek(0, true)
          }}
        />
        <Button
          normalStyle={{ width: '100px', height: '100%' }}
          activedStyle={{ background: 'red' }}
          text={'seekTo 5000'}
          onClick={() => {
            videoRef.current?.seek(5000, true)
          }}
        />
      </ScrollView>
    </view>
  )
}

root.render(<App />)

export default App
```
