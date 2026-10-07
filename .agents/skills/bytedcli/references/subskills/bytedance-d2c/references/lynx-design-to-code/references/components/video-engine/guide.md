# Lynx UI VideoEngine SKILL.md

`<VideoEngine>` is a component that plays media and controls the playback of it.

## 1. Common Use Cases

- **Play media**: Play media such as video, audio, etc.

## 2. Basic Usage

`<VideoEngine>` is used to play media and controls the playback of it.

```tsx
import { VideoEngine } from '@byted-lynx/lynx-ui'

function App() {
  return (
    <VideoEngine
      style={{ width: '100%', height: '200px' }}
      autoPlay={true}
      autoPrepare={true}
      skipRedirection
      poster={'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/230px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'}
      playUrl={'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4'}
    />
  )
}
```

## 3. Example for playback controls

You can control the playback of `<VideoEngine>` by calling the methods of the ref.

```tsx
import { VideoEngine } from '@byted-lynx/lynx-ui'
import type { VideoEngineRef } from '@byted-lynx/lynx-ui'
import { useRef, useEffect } from '@byted-lynx/react'

function App() {
  const videoRef = useRef<VideoEngineRef>(null)

  useEffect(() => {
    videoRef.current?.play()
  }, [])

  return (
    <VideoEngine
      style={{ width: '100%', height: '200px' }}
      autoPlay={false}
      autoPrepare={true}
      skipRedirection
      poster={'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/230px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'}
      playUrl={'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-360p.mp4'}
    />
  )
}
```

## 4. Critical Development Advices

- **NOTICE**: The `skipRedirection` prop is used to specify whether to skip redirection. It is recommended to set it to `true` explicitly.
- **NOTICE**: If you are trying to play audio-only media, you should set `as` prop to `Audio` explicitly.
