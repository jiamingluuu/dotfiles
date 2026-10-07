---
name: download-icon
description: 按 Figma 节点 id 下载图片（图标 / 切图）。适用于已知要出图的节点 id、需要按指定层级出图，或需要把图标落到本地目录的场景。
---

# 下载 Figma 节点图片

使用 `bytedcli d2c figma download-icon` 按节点 id 直接取图。该命令调用 `downloadIcon`，
返回 Figma 官方的临时图片链接；传 `--output-dir` 时会顺带把图片下载到本地。

## 何时用它，而不是 `d2c figma get`

两者出图层级的决定权不同：

- `d2c figma get`（`buildFigmaIndex`）经转换管线出图，层级由全局 `transformerOptions`
  （`mergeChildImage` 等）决定，**无法按节点控制**。
- `download-icon` 不走管线，**传哪个节点 id 就出那一层的图**。

所以要拿图标的画框尺寸时用本命令：例如 12×12 的图标按画框出图是 36×36 @3x，
而管线会下沉到内部 VECTOR，只得到 26×33。

先用 `d2c figma get` 拿到节点树、挑出要出图的节点 id，再用本命令出图。

## 用法

```bash
# 取图片链接（不落盘）
bytedcli --json d2c figma download-icon \
  --figma-url "https://www.figma.com/design/<fileKey>/<name>?node-id=2345-11996" \
  --node-ids "2345-11996,2345-12588" \
  --creator "user.name"

# 出 svg 并保存到本地目录
bytedcli d2c figma download-icon \
  --figma-url "https://www.figma.com/design/<fileKey>/<name>" \
  --node-ids "2345-11996" \
  --creator "user.name" \
  --format svg \
  --output-dir ./icons
```

参数：

- `--figma-url`（必填）：Figma 设计稿链接，用于解析 fileKey。
- `--node-ids`（必填）：逗号分隔的节点 id，最多 500 个。支持 URL 里的 `2345-11996`
  短横线形式，也支持 `2345:11996`；重复项会自动去重。
- `--creator`（必填）：用于解析该用户名下已存储的 Figma 凭证。
- `--format`：`png`（默认）或 `svg`。
- `--scale`：位图倍率 1~4，默认 3；`format=svg` 时 Figma 侧忽略。
- `--output-dir`：把图片下载到该目录；省略时只返回链接。
- `--figma-token` / `--figma-auth-token`：显式凭证。通常不需要传，命令会依次从显式参数、
  环境变量（`FIGMA_ACCESS_TOKEN` 等）和 `creator` 的服务端存储中解析。

返回字段：`file_key`、`format`、`scale`、`requested_count`、`resolved_count`、
`failed_count`、`images[{node_id, url}]`、`failed[]`、`output_dir`、
`saved[{node_id, file_path, bytes}]`。

## 约束

- **链接是临时的**：Figma 侧约 30 天有效且不保证；需要长期引用就传 `--output-dir` 当场保存，
  或自行落库。命令不转存、不落库。
- **部分节点取不到图不算失败**：Figma 对取不到图的节点返回空，这些 id 归入 `failed`，
  其余节点照常返回；命令同时在 stderr 提示未出图的节点，不要只看 `resolved_count`。
- 出图层级由传入的节点 id 决定，别指望它和 `d2c figma get` 的图一致。
- Figma 凭证只在内存中使用，不写盘、不打印、不进入命令结果。
- 单次最多 500 个节点 id；更多请拆成多次调用。
- 不要绕过 bytedcli 直接调用 HTTP 接口。

## 调用量归因

该命令的调用会由服务端按调用人与部门记入统一的 D2C 调用量看板
（能力类型 `download-icon`，子维度为出图格式）。身份由你的 ByteCloud SSO 凭证解析，
命令不发送自报身份；重试会复用同一请求 ID，因此一次调用只计一次。
