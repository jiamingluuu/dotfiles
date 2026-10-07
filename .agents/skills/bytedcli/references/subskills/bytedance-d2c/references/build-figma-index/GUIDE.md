---
name: build-figma-index
description: 根据 Figma URL 获取对应的 Figma 元信息。适用于首次获取 Figma 元信息，也适用于存量页面迭代时获取新的 Figma 信息。
---

# 获取 Figma 元信息

使用 `bytedcli d2c figma get` 根据 Figma URL 获取对应的 Figma 元信息。该命令调用 `buildFigmaIndex`，会优先复用服务端缓存；缓存未命中时拉取 Figma 原始树、建立节点索引，并返回根节点、节点数、整稿截图 URL 和 `origin_json`。

## 用法

```bash
bytedcli --json d2c figma get \
  --figma-url "https://www.figma.com/design/<fileKey>/<name>?node-id=1-2" \
  --repo-name "owner/repo" \
  --creator "user.name"

# 存量页面迭代且需要新的 / 最新 Figma 信息时，必须刷新远端索引
bytedcli --json d2c figma get \
  --figma-url "https://www.figma.com/design/<fileKey>/<name>?node-id=1-2" \
  --repo-name "owner/repo" \
  --creator "user.name" \
  --refresh
```

可选参数：

- `--no-origin`：主动省略体积较大的完整 `origin_json`；默认会返回原始树。
- `--refresh`：删除已有远端索引并重新构建。首次获取或普通读取默认复用缓存；修改 / 迭代存量页面且需要新的、最新 Figma 信息时必须使用 `--refresh`，避免只命中旧缓存。
- `--figma-token` / `--figma-auth-token`：显式凭证。通常不需要传，命令会依次从环境变量和 `creator` 的服务端存储中解析。

返回字段包括 `cached`、`root`、`node_count`、`root_image_url`、`origin_json`、`timestamp`。只有显式传 `--no-origin` 时才省略原始树。

## 约束

- 这不是纯只读操作：缓存未命中或使用 `--refresh` 时会写入服务端索引。
- Figma 凭证只在内存中使用，不写盘、不打印、不进入命令结果。
- 若显式参数、环境变量和 `creator` 名下的服务端凭证均不存在，命令会以 `D2C_INPUT_ERROR` 失败；此时需传 `--figma-token` / `--figma-auth-token` 或先存储凭证。
- 后续 `d2c figma-graph get` 必须使用与本命令完全相同的 `--figma-url`，因为完整 URL 是索引键。
- 不要绕过 bytedcli 直接调用 HTTP 接口。
