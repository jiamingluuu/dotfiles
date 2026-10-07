---
name: d2c-render-screenshot
description: 把一份组件代码提交到远端，云端 build 并用无头浏览器渲染截图，拿到对应的渲染截图 PNG。
allowed-tools: Bash, Read, Write, Edit, Grep
---

# D2C 远端 Build 与截图

把一份 `tsx` / `css` 组件代码提交到远端流水线，云端 `build` 后得到渲染整页截图，最终产出一张渲染截图 PNG。本 capability 用 `bytedcli d2c` 命令调用该服务，无需本地起服务。


## 快速开始

整体流程：**提交代码 → 轮询状态 → 拿到 downloadUrl → 下载 tar.gz → 解压 → 定位 screenshot.png**。

### Step 1: 提交 tsx/css 发起截图任务

组件代码通常多行，**推荐用 `--tsx-file` / `--css-file` 传文件路径**（命令读文件内容后提交）：

```bash
bytedcli --json d2c render create \
  --tsx-file "./figma2code.tsx" \
  --css-file "./figma2code.css" \
  --package-name "@example/demo-mobile" \
  --creator "your.email.prefix"
```

也支持内联（适合极短片段）：`--tsx "<source>"` / `--css "<source>"`。

**视口优先跟随 Figma 参考截图尺寸**，渲染器本身无预设偏好：

- 若有 visual segmentation 产物，读取 `<figma2codeDir>/input_image.png` 的实际像素 `width` / `height`，并把它们传给 `--width` / `--height`，确保渲染截图与 evaluation 使用的 Figma 参考图同尺寸。
- 若没有 Figma 参考 PNG，再按设计稿判断：移动端设计稿（宽度 ≈ 375 / 750）可不传 `--width` / `--height`，用默认 375×812@2x；桌面端设计稿（宽度明显大于移动端，如 1280 / 1440 / 1920）按设计稿尺寸传 `--width` / `--height`，例如：

```bash
bytedcli --json d2c render create \
  --tsx-file "./figma2code.tsx" \
  --css-file "./figma2code.css" \
  --width 1440 --height 900 \
  --creator "your.email.prefix"
```

渲染容器不会强制 body 宽度（页面撑满所给视口），生成代码需自身保证根元素宽度与设计稿一致。

返回 `{ success, taskId, message }`，记下 `taskId`。

- `--tsx-file`（或 `--tsx`）、`--css-file`（或 `--css`）、`--creator` 为**必填**。
- `--package-name` 可选，**填 tsx 里实际 import 的组件库 npm 包名**——远端会在 `build` 前把它安装进渲染沙箱，缺了对应依赖会导致 `build` 失败（`Failed to resolve import`）。
  - 从 tsx 的 `import ... from '<pkg>'` 里取**裸模块名**（即 npm 包名），多个用逗号 / 空格分隔，例如 `"@example/demo-mobile"` 或 `"@example/demo-mobile pkg-b"`。
  - 只需传**渲染沙箱内置之外**、代码额外依赖的组件库；`react` / `react-dom` 与沙箱已内置的组件库可不传。
  - tsx 只用原生标签 / 内置组件时可省略；相对路径（`./`、`../`）与 `.css` 不是包名，不要传。
  - **必须是能从 bnpm 安装的真实 npm 包名**，不要传页面 / 工程 / 任务名（那类值会 404 导致装包失败）。
- `--width` / `--height` 可选（正整数），渲染视口；只传其一时另一维度取默认（375 / 812）。
- 所有参数都由调用方（agent）从上下文中明确给出，命令不会自动推断。

### Step 2: 轮询任务状态

```bash
bytedcli --json d2c task get \
  --task-id "<taskId>" \
  --kind render-screenshot
```

也可以在提交任务时直接等待终态并落盘产物：

```bash
bytedcli --json d2c render create \
  --tsx-file "./figma2code.tsx" \
  --css-file "./figma2code.css" \
  --creator "your.email.prefix" \
  --wait \
  --output-dir ".aiden_d2c/shot" \
  --poll-interval-ms 60000 \
  --timeout-ms 1200000
```

- `--wait`：命令内部按 `--poll-interval-ms`（毫秒，最小 `30000`，建议 `60000`）轮询，命中 `completed` / `failed` / `cancelled` 时返回；总时限由 `--timeout-ms` 控制（默认 `1200000`，即 20 分钟）。配合 `--output-dir` 时会自动下载并解压产物。
- 不传 `--wait`：只返回 `taskId`，之后用 `d2c task get --kind render-screenshot` 自行查询。
- ⚠️ 用 `Bash` 调用 `--wait` 模式时**必须**把 timeout 设为略大于 `--timeout-ms`（默认至少 **20 分钟**）。

`status === 'completed'` 时返回会带 `downloadUrl`；`failed` / `cancelled` 立即终止并把 message 透传给用户。

### Step 3: 下载并解压拿到截图

`completed` 后从返回里拿到 `downloadUrl`，下载落盘并解压（无需额外 cookie / 鉴权头）：

```bash
mkdir -p .aiden_d2c/shot
curl -L "<downloadUrl>" -o .aiden_d2c/shot.tar.gz
tar -xzf .aiden_d2c/shot.tar.gz -C .aiden_d2c/shot --strip-components 1
```

解压后截图位于 `.aiden_d2c/shot/screenshot.png`（流水线产物根目录下的 `output/screenshot.png`，`--strip-components 1` 去掉顶层目录后即 `screenshot.png`）。用 `Read` 工具打开该 PNG 即可查看 / 对比渲染效果。

> 若解压后未在预期位置找到 `screenshot.png`，用 `find .aiden_d2c/shot -name '*.png'` 定位实际路径后再读取。

## 核心命令概览

| 命令 | 功能 |
|------|------|
| `bytedcli d2c render create` | 提交 tsx/css，发起远端 build+截图任务，返回 `taskId`；带 `--wait --output-dir` 时直接落盘产物 |
| `bytedcli d2c task get --kind render-screenshot` | 查询任务状态，`completed` 时返回 `downloadUrl` |

## ⚠️ 重要注意事项

1. **执行环境**：所有命令调用**必须**用 `Bash` 工具执行，**切勿**通过重复调用 `Skill` 工具来运行命令。
2. **多行代码**：tsx/css 是多行源码，优先用 `--tsx-file` / `--css-file` 传文件路径，避免内联时的 shell 转义问题。
3. **超时设置**：`d2c render create --wait` 耗时长，`Bash` 超时必须 ≥ `--timeout-ms`（默认至少 20 分钟）。
4. **错误透传**：任一接口失败时，响应是 JSON `{ error, message, ... }`，把 `error` / `message` 直接透传给用户并终止，不要静默重试。
5. **任务失败**：状态为 `failed` / `cancelled` 时立即终止，提示用户检查 tsx 源码、css 源码、`creator` 后重试。
