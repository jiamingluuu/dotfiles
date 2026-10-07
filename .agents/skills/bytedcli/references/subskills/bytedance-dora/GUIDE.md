---
name: bytedance-dora
description: "Use when tasks mention Dora, 云真机, 云手机, cloud device, device occupation/reservation/release/renewal, native Android screenshots/recordings/tap/swipe/text/key control or PNG/JPEG upload without ADB, Android/adb cloud devices, iOS/bdc cloud devices, Harmony/鸿蒙/HDC remote addresses, ADB/BDC/HDC connection addresses, semantic Android UI actions on occupied Dora cloud devices, or installing APK/IPA packages on occupied cloud devices."
---

# bytedcli Dora

Use this skill for Dora cloud-device work. The command domain is top-level `dora`; do not use `bits dora`.

## Invocation

Prefer globally installed `bytedcli`:

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

Use JSON mode for machine-readable output by placing `--json` before `dora`:

```bash
bytedcli --json dora device list
```

Requires bytedcli authentication; if not logged in, run `bytedcli auth login` first.

## When to use

- 查询 Dora 公有云真机 / 云手机列表。
- 按 Dora 分组 ID 查询真实分组设备列表。
- 查询当前用户已占用设备列表。
- 获取单台设备详情。
- 占用一台空闲设备用于远程调试。
- 申请预约设备。
- 按用户输入的 `安卓/adb`、`iOS/bdc` 或 `鸿蒙/harmony/hdc` 精确占用对应平台设备。
- 占用云真机后做二次验证、续期，并在长时间任务中启动到期前自动续期守护。
- 用户明确要求安装指定 APK/IPA 时，占用、续期和连接验证完成后安装。
- 释放、续期当前占用的设备。
- 获取设备 ADB、BDC 或 Harmony HDC 远端调试地址。
- 不依赖 ADB，通过 Dora 原生 WebSocket 控制已占用的 Android 设备：点击、滑动、文本输入和按键。
- 不依赖 ADB，通过 Dora 原生 WebSocket 将已占用 Android 设备的当前画面截为 PNG，或录制为 MP4。
- 不依赖 ADB，将本地 PNG/JPEG 写入已占用 Android 设备的受限图片目录。

## Quick start

```bash
# 查询公有空闲设备；默认筛选 public / idle / Android / physical / CN
bytedcli dora device list
bytedcli --json dora device list

# 常用筛选
bytedcli --json dora device list --os ios --device-type physical --usage idle --connect-state online
bytedcli --json dora device list --os android --device-type physical --usage idle --connect-state online
bytedcli --json dora device list --os harmony --device-type physical --usage idle --connect-state online
bytedcli dora device list --keyword "pixel"
bytedcli dora device list --connect-state online --country SG
bytedcli dora device list --level high --version "14" --manufacturer "Google"

# 查询当前用户已占用设备
bytedcli --json dora device list --scope occupied

# 查询指定 Dora 分组；group scope 必须显式提供 group ID
bytedcli dora device list --scope group --group-id <group-id>
bytedcli --json dora device list --scope group --group-id <group-id>

# 获取设备详情
bytedcli --json dora device get --serial <device-serial>

# 占用设备用于远程调试；默认 1800 秒，最大 14400 秒
bytedcli --json dora device occupy --serial <device-serial> --time-sec 3600

# 申请预约设备
bytedcli --json dora device apply --serial <device-serial> --hours 2
bytedcli --json dora device apply --serial <model-key> --reservation-type model --hours 2

# 续期 / 释放
bytedcli --json dora device renew --serial <device-serial> --time-sec 14400
bytedcli --json dora device release --serial <device-serial>

# 获取连接地址
bytedcli --json dora device adb --serial <device-serial>
bytedcli --json dora device bdc --serial <device-serial>
bytedcli --json dora device hdc --serial <device-serial>

# Dora 原生 Android 控制，不依赖本机 ADB
bytedcli --json dora device control tap --serial <device-serial> --x 540 --y 1170
bytedcli --json dora device control swipe --serial <device-serial> --from-x 540 --from-y 1800 --to-x 540 --to-y 600 --duration-ms 300 --steps 8
bytedcli --json dora device control text --serial <device-serial> --text 'hello'
bytedcli --json dora device control key --serial <device-serial> --key back

# Dora 原生 Android 截图与录屏，不依赖本机 ADB；本机需安装 ffmpeg
bytedcli --json dora device screen export --serial <device-serial> --format png --output ./screen.png
bytedcli --json dora device screen export --serial <device-serial> --format mp4 --duration-sec 10 --output ./screen.mp4

# Dora 原生 Android 文件写入，不依赖本机 ADB；单文件必须小于 4 MiB
bytedcli --json dora device file upload --serial <device-serial> --file ./qr.png
bytedcli --json dora device file upload --serial <device-serial> --file ./qr.jpg --remote-path /sdcard/Pictures/bytedcli/codes/qr.jpg

# Android：按当前 UI hierarchy 精确查找、点击、长按
bytedcli --json dora device ui get --serial <device-serial> --resource-id example.app:id/action --package example.app
bytedcli --json dora device ui execute --action tap --serial <device-serial> --text "Open" --package example.app
bytedcli --json dora device ui execute --action long-press --serial <device-serial> --content-desc "Account" --duration-ms 5000 --package example.app

# Android：默认 ADB 安装路径保持兼容
bytedcli --json dora device app deploy --serial <device-serial> --apk ./demo.apk

# Android：Dora 原生远程安装，不需要本机 ADB 连接或端口
printf '%s' "$APK_DOWNLOAD_URL" | \
  bytedcli --json dora device app deploy \
    --transport native \
    --serial <device-serial> \
    --url-file -

# Android：保留原有 ADB 设备侧下载与 SHA-256 校验路径
printf '%s' "$APK_DOWNLOAD_URL" | \
  bytedcli --json dora device app deploy \
    --transport adb \
    --serial <device-serial> \
    --url-file - \
    --sha256 <expected-sha256>
```

## 远端调试地址（ADB / BDC / HDC）

三个命令都通过 `--serial` 获取当前用户已占用设备的远端调试地址，仅取址，不执行本机客户端、不验证连通性，也不自动占用或续期。已有占用可用 `device get` 和 `device list --scope occupied` 复核；需要新占用时，按下方通用占用流程选择对应平台。JSON 模式保留服务端返回的地址字段；Dora serial 与返回的调试地址是不同标识。

| 平台    | 取址命令                                            | 文本提示                |
| ------- | --------------------------------------------------- | ----------------------- |
| Android | `bytedcli dora device adb --serial <device-serial>` | `adb connect <address>` |
| iOS     | `bytedcli dora device bdc --serial <device-serial>` | `bdc connect <address>` |
| Harmony | `bytedcli dora device hdc --serial <device-serial>` | `hdc -s <address>`      |

ADB/HDC 文本模式分别展示存在的 `address` 和 `address_v6`；BDC 文本模式展示 `address`。HDC 返回远端 HDC Server 地址，文本提示是命令前缀，实际使用时追加所需命令，例如 `hdc -s <address> list targets`。HDC 接口若返回 `Device Occupied By Other`，先核实目标设备仍由当前用户占用。

HDC 的 `address` 格式为 `IPv4:端口`；`address_v6` 格式为不带方括号的 `IPv6:端口`，例如 `2001:db8:0:1:0:0:0:1:8710`，末尾的 `8710` 是端口。将返回值完整传给 `hdc -s`，保留服务端地址格式。设备可能只有 IPv4、只有 IPv6 或同时提供两者；某个字段缺省或为空字符串时，使用另一个非空地址。JSON 保留服务端字段，文本模式只输出非空地址。可用 `hdc -s <address> list targets` 验证连接，并用返回的 connect key 作为 `-t` 参数选择设备。

## Dora 原生 Android 控制（无需 ADB）

`device control` 直接连接 Dora 的控制 WebSocket，不会启动、调用或依赖本机 `adb`。控制前设备必须由当前用户占用，且设备详情必须包含有效 Session 与屏幕分辨率。

**授权边界**：执行 `dora device control`（tap、swipe、text、key）前，必须确认用户已明确授权目标设备（serial）和具体动作序列；不要在用户仅描述高层业务目标时静默执行破坏性点击、表单提交、支付或后退/Home 导航。

**控制与 UI 方式选择规则**：

- **原生 Dora 控制 (`dora device control tap|swipe|text|key`)**：已知目标像素坐标、滑动轨迹、整段文本输入或标准硬件按键（home、back、enter 等）时优先使用。直接走 Dora 原生 WebSocket，低延迟，不依赖本机 ADB 环境。
- **ADB 语义 UI (`dora device ui get|execute`)**：需要按 `text`、`resource-id`、`content-desc` 查找定位元素，需要断言页面唯一匹配或检查 UI hierarchy，或需要校验 package/readback 状态时使用（底层依赖 ADB 与 UIAutomator）。

```bash
# 点击：x / y 是设备屏幕内的零基像素坐标
bytedcli --json dora device control tap --serial <device-serial> --x 540 --y 1170

# 滑动：起点、终点是像素坐标；默认 300 ms、8 个中间移动帧；--duration-ms 最大 10000 ms，--steps 最大 120
bytedcli --json dora device control swipe --serial <device-serial> --from-x 540 --from-y 1800 --to-x 540 --to-y 600
bytedcli --json dora device control swipe --serial <device-serial> --from-x 100 --from-y 100 --to-x 900 --to-y 1800 --duration-ms 500 --steps 12

# 文本：通过 Dora 原生整段文本粘贴事件输入，支持 Unicode 和换行
bytedcli --json dora device control text --serial <device-serial> --text 'hello 世界'
bytedcli --json dora device control text --serial <device-serial> --text $'第一行\n第二行'

# 按键：支持别名或非负 Android 数字 keycode
bytedcli --json dora device control key --serial <device-serial> --key home
bytedcli --json dora device control key --serial <device-serial> --key back
bytedcli --json dora device control key --serial <device-serial> --key 66
```

按键别名：`home`、`back`、`enter`、`menu`、`recent` / `app-switch`、`volume-up`、`volume-down`、`power`。

控制结果中的 `delivery_status: "sent"` 表示 WebSocket 已连接且控制帧已提交给连接。Dora 协议没有逐操作 ACK，因此不能把该字段解释为设备端已确认执行。需要确认界面结果时，可通过 Dora Web 控制台（`https://dora.bytedance.net` 或 `https://bits.bytedance.net/quality/dora/`）观察实时画面，或使用 `dora device screen export --format png` 获取当前画面。

## Dora 原生 Android 截图与录屏（无需 ADB）

`device screen export` 复用 Dora 原生 `screen.io` WebSocket 下行画面流，不会获取 ADB 地址，也不会启动或调用本机 `adb`。命令仅支持当前用户已占用的 Android 设备，并要求本机 `PATH` 中存在 `ffmpeg`。

```bash
# 截取当前画面为 PNG；默认最多等待关键帧 15000 ms
bytedcli --json dora device screen export \
  --serial <device-serial> \
  --format png \
  --output ./screen.png

# 录制无音频 MP4；默认 10 秒，范围 1-300 秒
bytedcli --json dora device screen export \
  --serial <device-serial> \
  --format mp4 \
  --duration-sec 10 \
  --output ./screen.mp4

# 设备休眠或首个关键帧较慢时，可调大等待时间，最大 60000 ms
bytedcli --json dora device screen export \
  --serial <device-serial> \
  --format png \
  --output ./screen.png \
  --timeout-ms 30000
```

- `--format` 支持 `png|mp4`，默认 `png`；PNG 的 `--output` 必须以 `.png` 结尾，MP4 必须以 `.mp4` 结尾。
- `--output` 的父目录必须已经存在且不能是符号链接；命令拒绝覆盖已有文件。
- MP4 的 `--duration-sec` 默认 10 秒，范围为 1-300 秒；PNG 不接受该参数。当前只录视频，不包含设备音频。
- `--timeout-ms` 是等待首个 H.264 配置帧与关键帧的时间，默认 15000 ms，范围为 1-60000 ms；录屏开始后还会额外等待指定录制时长。
- 两条命令都会先校验当前用户占用关系和 Android 平台，再连接 Dora 原生画面流。原始 H.264 与未完成产物使用 owner-only 临时文件；只有 `ffmpeg` 成功后才原子写入目标路径，失败时清理临时文件。
- 成功 JSON 返回 `serial`、绝对 `output_path`、`format`、`codec`、`frame_count` 和 `bytes`；录屏额外返回 `duration_ms` 与 `frame_rate`。
- `DORA_SCREEN_FFMPEG_NOT_FOUND` 表示本机没有可执行的 `ffmpeg`；安装 FFmpeg 并确保其位于 `PATH` 后重试。
- `DORA_SCREEN_KEYFRAME_TIMEOUT` 通常表示设备休眠、画面流尚未就绪或关键帧等待时间不足；唤醒设备或调大 `--timeout-ms` 后重试。
- 单次捕获最多接收 256 MiB 原始 H.264 数据与 36001 个视频帧；`DORA_SCREEN_CAPTURE_TOO_LARGE` 或 `DORA_SCREEN_CAPTURE_TOO_MANY_FRAMES` 时缩短 `--duration-sec` 后重试。

## Dora 原生 Android 文件写入（无需 ADB）

`dora device file upload` 将一个本地 PNG/JPEG 先上传到 Dora 用户文件库，再通过官方 `file.push` 事件写入当前用户已占用的 Android 设备。该命令不获取 ADB 地址，也不调用本机 `adb`。

**授权边界**：仅当用户明确要求把指定本地 PNG/JPEG 写入指定 Dora 设备时执行。执行前确认目标 serial、源文件和设备目标路径；使用默认路径时也要明确告知 `/sdcard/Pictures/bytedcli/<本地文件名>`。用户只提供图片、询问能力或描述后续验收目标时，先确认这些写入参数，不执行上传。

```bash
bytedcli --json dora device file upload \
  --serial <device-serial> \
  --file ./qr.png

bytedcli --json dora device file upload \
  --serial <device-serial> \
  --file ./qr.jpg \
  --remote-path /sdcard/Pictures/bytedcli/codes/qr.jpg \
  --timeout-ms 120000
```

- 当前只接受字节签名与扩展名一致的 `.png`、`.jpg`、`.jpeg` 普通文件；拒绝符号链接、空文件和大于等于 4 MiB 的文件。4 MiB 起需要的分片上传尚未接入。
- 默认设备路径是 `/sdcard/Pictures/bytedcli/<本地文件名>`。显式 `--remote-path` 必须位于 `/sdcard/Pictures/bytedcli/` 下，路径穿越与反斜杠会被拒绝；以 `/` 结尾时自动追加本地文件名。
- 命令计算本地 SHA-256 用于结果校验，并按 Dora 官方协议计算 MD5 `file_hash`；随后用 `check_file` 复用已上传文件，或通过 `upload/file` 上传，再发送 `file.push {file_path,file_hash}` 并等待成功/失败终态。
- 成功结果中的 `status: "device file written"`、`confirmed: true` 只确认 Dora `file.push` 成功终态。该命令不会声称 MediaStore 已索引，也不保证相册应用立即可见；需要确认界面时另行导出屏幕或打开目标应用检查。
- JSON 返回 `serial`、`session_id`、`device_path`、`source_sha256`、`file_size`、`mime_type`、`transport`、`confirmed` 与 `status`。文件内容不会写入 argv、日志或错误。

### Markdown 多行换行（必读）

Shell 中需要输入真实换行时使用 `$'...'`，例如 `--text $'第一行\n第二行'`。不要写成 `--text "第一行\n第二行"`，bash / zsh 双引号不会把 `\n` 转换为换行，设备会收到字面量反斜杠和字母 `n`。

## Android 语义 UI 操作

`dora device ui get` 与 `dora device ui execute --action tap|long-press` 只支持当前用户已占用且在线的 Android 设备。调用方传 Dora serial；bytedcli 每次重新获取 Dora ADB 地址，按有效 IPv4、IPv6 target 的顺序执行完整在线校验，并为所有后续 ADB 命令显式传 `-s <resolved-target>`。

- `get` 是只读查询。执行 `execute --action tap|long-press` 前，必须确认用户已明确授权目标设备与具体动作；不要把仅提供 selector 视为点击授权。
- `--resource-id`、`--text`、`--content-desc` 必须三选一，均为精确匹配。
- 建议自动化流程显式传 `--package`。传入后会在动作前校验 resumed package，并将节点限定到同一 package；点击或长按后再次读取 resumed package。
- 每次查询或动作都重新执行 UIAutomator dump，只接受 `enabled=true` 且 bounds 有效的节点，不缓存旧 hierarchy 或旧坐标。
- 匹配结果必须恰好一个。零匹配返回 `DORA_UI_NODE_NOT_FOUND`，多匹配返回 `DORA_UI_NODE_AMBIGUOUS`；命令不会降级到 OCR、截图识别或 Computer Use。
- Lynx、WebView、Canvas 和系统 IME 可能不暴露 UIAutomator 节点。遇到结构化未找到错误时，检查页面节点可见性或改用 App 提供的稳定 resource-id。
- 成功 JSON 返回 `serial`、`adb_target`、selector 类型与脱敏指纹、`package`、`bounds`、动作、`duration_ms` 和 readback 状态；不输出 selector 原文或完整 hierarchy。
- `execute --action long-press` 的 `--duration-ms` 接受 500–10000 毫秒，默认 1200 毫秒。

## Android APK 安装

`dora device app deploy` 要求 `--apk` 与 `--url-file` 二选一。`--transport` 支持 `adb|native`，默认 `adb`，因此未传该参数的现有命令保持原行为。

- 安装前必须确认用户已明确授权目标设备和指定 APK；仅收到包路径或 URL 不代表已经授权安装。用户已明确要求安装该 APK 时，PackageInstaller 的精确确认动作可视为同一授权范围。
- `--transport native --url-file <path-or-dash>` 直接连接 Dora `event.io` WebSocket 并发送 `app.install`。该路径不获取 ADB 地址，不需要本机 ADB 端口，且只支持当前用户已占用的 Android 设备。命令等待 Dora 返回成功或失败终态；文本模式显示进度，JSON 只输出终态结果。默认超时为 1800000 毫秒，可用 `--timeout-ms` 调整，最大 14400000 毫秒。
- 原生 URL 安装仅使用 Dora 官方直链契约；该契约没有 SHA-256 字段，因此 `--transport native` 不接受 `--sha256`。需要客户端校验制品摘要时继续使用默认 ADB URL 路径。
- `--transport adb --apk <path>` 接受本地普通 `.apk` 文件，通过参数数组执行 `adb install -r -d`。大文件仍会经过远程 ADB tunnel。
- `--transport adb --url-file <path-or-dash>` 由设备通过 `curl` 或 `wget` 直接下载，避免本机通过远程 ADB tunnel 传输整个文件。只接受最终 HTTPS 制品 URL，不跟随重定向，下载上限为 2 GiB。URL 文件在 POSIX 上必须是 owner-only（如 `0600`/`0400`）；`-` 只读取非 TTY stdin。
- 共享 MCP 调用不能使用 `--url-file -`，以免读取 MCP 协议 stdin；此时改用 owner-only URL 文件。直接运行 CLI 时仍可通过管道传入。
- ADB URL 下载必须同时提供可信的 `--sha256`。bytedcli 在安装前读取设备端 `sha256sum` 结果并精确比对，不一致时停止安装。
- URL 不进入进程 argv、普通日志、JSON 输出或错误摘要。不要把带签名 URL 直接写进命令行参数或文档。
- `--transport adb --url-file` 在设备侧优先使用禁用启动配置与 URL glob 的 `curl`；仅当 `wget` 支持禁用启动配置、netrc 和 cookies 时才使用其 fallback，否则需要先在设备上安装 `curl`。
- 每次 ADB URL 安装只创建一个 `/data/local/tmp/bytedcli-dora-*.apk`，所有终态都会尝试精确清理该文件，不扫描或删除设备上的其他临时文件。清理失败时返回 `DORA_APP_CLEANUP_FAILED` 和精确路径；释放设备前按该路径手动删除。
- ADB URL 安装要求设备具备 `stat`、`sha256sum`、`head` 和 `wc`。设备缺少必要工具，或 package manager 未返回独立的 `Success` 行时，命令结构化失败；不会静默改走远程 ADB 大文件传输。
- Native URL 安装只把受保护的 HTTPS URL 交给 Dora `app.install` 并等待终态，不创建 bytedcli ADB 临时文件，也不要求设备存在上述 shell 工具。
- 结果中的 `transport` 表示实际传输方式。为保持既有 JSON 契约，默认 ADB URL 路径返回 `device-download`；本地 ADB 安装返回 `adb`，原生 URL 安装返回 `native`。

## 稳定占用云真机

以下设备占用与维护流程适用于 Android、iOS 和 Harmony。核心原则：**先明确平台，再只筛对应平台；占用后必须二次验证并续期；长时间占用要启动自动续期守护**。已占用的目标设备直接复核并取址，不重复选机和占用。仅需地址时使用前文取址命令；Android/iOS 的连接与可选安装见下一节。

### 输入到设备类型映射

| 用户输入 / 物料                               | 目标平台 | 连接方式                     | 安装方式                                                     |
| --------------------------------------------- | -------- | ---------------------------- | ------------------------------------------------------------ |
| `安卓` / `android` / `adb` / `.apk` / `.apks` | Android  | ADB 或 Dora native WebSocket | `dora device app deploy`（`.apks` 需 bundletool 或平台支持） |
| `iOS` / `ios` / `iphone` / `bdc` / `.ipa`     | iOS      | BDC                          | `bdc install --resign`                                       |
| `鸿蒙` / `harmony` / `hdc`                    | Harmony  | HDC                          | 当前支持设备管理与取址，不支持应用安装                       |

- 用户显式说 `adb` 就按 Android；显式说 `bdc` 就按 iOS；显式说 `鸿蒙`、`harmony` 或 `hdc` 就按 Harmony。
- 用户只给安装包时，从后缀推断：`.apk`/`.apks` => Android，`.ipa` => iOS。
- 显式平台与安装包后缀冲突时先停下说明冲突，不要跨平台安装或随机占设备。
- 没有平台线索且没有安装包时，先询问 Android、iOS 还是 Harmony；不要默认占 Android。

### 通用占用流程

1. **确认平台**：按上表确定 Android、iOS 或 Harmony，以及对应的 ADB、BDC 或 HDC 取址命令。
2. **只查对应平台候选设备**：

   ```bash
   # iOS / BDC
   bytedcli --json dora device list --os ios --device-type physical --usage idle --connect-state online

   # Android / ADB
   bytedcli --json dora device list --os android --device-type physical --usage idle --connect-state online

   # Harmony / HDC
   bytedcli --json dora device list --os harmony --device-type physical --usage idle --connect-state online
   ```

3. **占用候选设备**：

   ```bash
   bytedcli --json dora device occupy --serial <device-serial> --time-sec 3600
   ```

4. **占用后必须验证**：

   ```bash
   bytedcli --json dora device get --serial <device-serial>
   bytedcli --json dora device list --scope occupied
   ```

   验证点：目标 serial 出现在“我已占用”列表；平台与预期的 `android`、`ios` 或 `harmony` 一致；连接状态为 online；用途变为远程调试/已占用。任一不满足，不要继续取址、连接或安装，换一台重试。

5. **占用确认后立即续期，并再次确认**：

   ```bash
   bytedcli --json dora device renew --serial <device-serial> --time-sec 14400
   bytedcli --json dora device get --serial <device-serial>
   bytedcli --json dora device list --scope occupied
   ```

   续期策略：未指定时续到 Dora 允许的最大远程调试时长（当前最大 14400 秒）；如果用户指定占用时长，按用户时长续期但不能超过平台上限。续期失败时不要继续后续设备操作，先说明设备可能很快过期并重新占用或重试续期。

6. **长时间任务启动自动续期守护**：

   如果任务可能超过当前占用时长，或用户明确要求“别让设备过期 / 快到期自动续期”，占用验证和首次续期成功后立即启动后台续期守护。默认策略：到期前 10 分钟触发续期；如果当前 Dora JSON 字段不好稳定解析到期时间，则使用保守轮询，每 50 分钟续到 14400 秒，并把每次 `get / renew / occupied` 结果写日志。

   ```bash
   DORA_SERIAL=<device-serial>
   DORA_RENEW_SEC=14400
   DORA_RENEW_INTERVAL_SEC=3000   # 50 分钟；必须短于当前租约剩余时长
   DORA_RENEW_LOG="/tmp/dora-renew-${DORA_SERIAL}.log"
   DORA_RENEW_PID="/tmp/dora-renew-${DORA_SERIAL}.pid"

   (
     while true; do
       date '+%Y-%m-%d %H:%M:%S %z'
       bytedcli --json dora device get --serial "$DORA_SERIAL"
       bytedcli --json dora device renew --serial "$DORA_SERIAL" --time-sec "$DORA_RENEW_SEC"
       bytedcli --json dora device list --scope occupied
       sleep "$DORA_RENEW_INTERVAL_SEC"
     done
   ) >> "$DORA_RENEW_LOG" 2>&1 &
   echo $! > "$DORA_RENEW_PID"
   ```

   启动后要说明 PID 和日志路径。任务结束或释放设备前必须停止守护，避免无人使用时继续续期：

   ```bash
   kill "$(cat /tmp/dora-renew-<device-serial>.pid)"
   rm -f "/tmp/dora-renew-<device-serial>.pid"
   bytedcli --json dora device release --serial <device-serial>
   ```

   自动续期守护失败时，优先看日志里的 `renew` 返回和续期后的 `device get` / `--scope occupied`；连续失败不要继续声称设备安全，重新占用或提醒用户。

只释放本轮创建且已不再使用的占用；用户原有占用保持不变。Harmony 当前提供设备管理和远端取址，应用安装、控制与截图尚未接入。

## Android/iOS 连接与可选安装

以下步骤用于用户明确要求连接设备或安装指定 APK/IPA 的任务；仅查询远端调试地址不需要执行这些步骤。

1. **按 transport 验证安装前置条件**：
   - Android native：不获取 ADB 地址，也不执行 `adb connect`。保持设备由当前用户占用且在线；`dora device app deploy --transport native` 会再次校验 Android 平台、占用关系和有效 Dora session。
   - Android ADB：

     ```bash
     bytedcli --json dora device adb --serial <device-serial>
     adb connect <host:port>
     adb -s <host:port-or-serial> get-state
     ```

   - iOS：

     ```bash
     bytedcli --json dora device bdc --serial <device-serial>
     bdc connect <bdc-address-or-command-from-dora>
     bdc devices
     ```

   ADB / BDC 连接验证不通过时不要走对应 transport 安装；Android native 不以本机 ADB 连接作为前置条件。

2. **可选安装包**：仅当用户明确要求在目标设备安装指定包路径，或明确要求查找并安装指定安装包时执行；仅提供包路径、URL 或安装包物料时，先确认目标设备与安装动作。未授权安装时只占用、续期、按需启动自动续期守护并连接验证。
   - Android APK：

     ```bash
     bytedcli --json dora device app deploy --serial <device-serial> --apk <package.apk>
     ```

     用户已明确授权安装且有受保护 HTTPS APK URL 时，优先使用 `--transport native --url-file -`，避免本机 ADB 连接和端口要求。需要客户端 SHA-256 校验时使用 `--transport adb --url-file - --sha256 <digest>`。`app.install` 只发起安装并等待终态，不执行任何 UI 点击。若云真机弹出 PackageInstaller 二次确认，无 ADB 流程先用 `dora device screen export --format png` 观察画面，再在用户已授权且坐标精确时使用 `dora device control tap`；不要点击未知 OEM 弹窗。只有必须按 resource-id / text 做语义定位时才使用 `dora device ui get|execute`，该分支会重新引入 ADB。

   - iOS IPA：

     ```bash
     bdc install --resign -u <ios-udid-or-bdc-id> <package.ipa>
     ```

     iOS 真机常见证书不匹配；默认加 `--resign`，不要先尝试无重签安装再失败。

3. **安装后验证**：Android native 以 `app.install` 成功终态作为安装结果；完全无 ADB 的验收可用 `device screen export` 观察画面，并在坐标明确时用 `device control key|tap|swipe|text` 完成启动与交互。需要按包名执行 `pm list packages`、启动 activity 或语义 UI 定位时才切到 ADB。Android ADB 使用 `pm list packages` 或启动 activity；iOS 使用 `bdc` 的 app list/info/launch 能力验证 bundle 存在并可启动。没有包名 / bundle id 时，先从安装包元信息解析，不凭文件名猜。

## Notes

- `device list` 的主要筛选值使用语义化输入：`--usage idle|remote-debug|automation|ops|reserve|all`，`--connect-state online|offline|all`，`--os android|ios|windows|macos|linux|harmony|all`，`--device-type physical|vm|emulator|baymax|all`，`--level low|medium|high|all`。
- 查询分组设备必须同时传 `--scope group --group-id <id>`，且不要附加 public 专用筛选或分页参数。该模式一次返回完整分组并只调用 Dora 分组接口；分组不存在、无权限、空列表、归属不一致或接口失败都会明确报错，绝不降级查询公有池。
- `--version` 按 Dora 页面设备系统版本过滤，`--manufacturer` 按品牌过滤。
- 文本输出会渲染关键字段；JSON 输出保留结构化结果，适合脚本继续解析。
- `adb` / `bdc` / `hdc` 文本模式输出连接提示；需要原始地址字段时使用 JSON 模式。`hdc` 使用 `-s` 指定远端 HDC Server，实际使用时需追加具体命令。
- 设备操作按 Dora 页面接口执行，`occupy` 固定用于远程调试占用，`apply` 用于预约申请。
- `device ui` 与 `device app deploy` 为 Android-only，且只操作当前用户已经占用的设备；不会自动占用或续期。`device app deploy --transport native` 直接使用 Dora WebSocket，默认 `adb` transport 保持原有 ADB 行为。
- `device control tap|swipe|text|key` 仅支持当前用户已占用的 Android 设备，直接走 Dora 原生 WebSocket，不需要本机 ADB；iOS 设备继续使用 BDC 能力。
- `device screen export --format png|mp4` 仅支持当前用户已占用的 Android 设备，直接读取 Dora 原生 H.264 画面流，不需要本机 ADB；需要本机 `ffmpeg` 生成 PNG / MP4。
- `device file upload` 仅支持当前用户已占用的 Android 设备，通过 Dora 用户文件库与原生 `file.push` 写入受限图片目录，不需要本机 ADB。
- 控制坐标使用零基像素值，必须落在 Dora 返回的屏幕宽高范围内。不要传 `0..1` 比例，bytedcli 会在发送前自动归一化。
- 文本控制不会在结果中回显输入内容，只返回字符数和发送帧数。

## 常见错误

- 不要使用 `bits dora ...` 或猜测 `dora device connect`；Dora 是顶层 `dora` 域，连接地址分别通过 `device adb` / `device bdc` / `device hdc` 获取。
- 不要把 `--group-id` 传给默认的 public 查询来判断分组归属；bytedcli 会拒绝这种组合，因为公有池接口不接受分组归属语义。必须使用 `--scope group --group-id <id>`。
- `DORA_GROUP_EMPTY` 表示分组接口请求成功、但该分组当前没有设备；它不同于 `DORA_GROUP_NOT_FOUND`。应停止依赖设备的后续步骤，等待分组补充设备或改为显式查询另一个已知分组，不要降级到公有池。
- 不要把 `adb` 当成 iOS 连接方式，也不要把 `bdc` 当成 Android 连接方式。
- 不要为了点击、滑动、文本输入或 Android 按键先获取 ADB 地址；优先使用 `dora device control ...` 原生控制命令。
- 不要把 `delivery_status: "sent"` 当成设备端 ACK；需要确认操作效果时使用 `dora device screen export --format png` 或 Dora Web 控制台实时画面核对。
- 不要猜测 `dora device screenshot` / `record` / `stream` / `screenrecord`；标准命令是 `dora device screen export --format png|mp4`。
- 不要把 `dora device file upload` 的成功解释为图片已进入 MediaStore 或相册；它只确认指定设备文件路径写入成功。
- 不要只看 `occupy` 命令返回成功；必须用 `device get` + `--scope occupied` 验证确实占到当前用户名下，然后执行 `device renew` 续期并再次确认。
- 不要为长时间占用只续期一次；用户要求保持占用或任务可能超过租约时，要启动自动续期守护，并记录 PID 与日志路径。
- 不要在释放设备后留下自动续期守护；释放前先 kill 对应 PID，否则可能无人使用时继续续期占住设备。
- 不要在多设备连接时省略 `adb -s` / `bdc -u`；安装必须指向刚才验证过的目标设备。
- 不要在用户未提供安装包、也未指定包来源时主动找包或猜包；这种场景不进入安装流程，仅查询地址时不执行客户端连接验证。
- 不要猜测 `dora device ui find` / `search`；标准查询命令是 `dora device ui get`。
- 不要把 Dora serial 直接传给 `adb -s`；`device ui` 和默认 ADB transport 的 `device app deploy` 会在每次调用时解析并验证当前 ADB target。原生安装使用 `--transport native`。
- 不要把签名 URL 放进 `--url-file` 的参数值；该参数接收文件路径或 `-`，URL 内容通过 owner-only 文件或非 TTY stdin 读取。
- 不要给 `--transport native` 传 `--apk`、`--sha256` 或 ADB 地址；该路径只接收 `--url-file` 并等待 Dora 原生安装终态。
