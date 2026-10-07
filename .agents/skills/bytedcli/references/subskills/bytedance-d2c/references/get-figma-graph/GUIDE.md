---
name: get-figma-graph
description: 调用 searchFigmaGraph，按 NodeID 获取已索引的 Figma 节点信息，并可向上查询父节点或向下 BFS 查询子节点。用于代码生成前读取目标节点结构、组件类型及有限父子上下文。
---

# 按 NodeID 获取 Figma 信息

使用 `bytedcli d2c figma-graph get` 查询已由 `figma get` 建立的 Figma 图索引。

```bash
bytedcli --json d2c figma-graph get \
  --figma-url "https://www.figma.com/design/<fileKey>/<name>?node-id=1-2" \
  --figma-node-id "1-2" \
  --parents-depth 1 \
  --children-depth 2
```

- `--figma-url`：必填，必须与建立索引时的完整 URL 一致。
- `--figma-node-id`：必填，支持 `1-2` 或 `1:2`，命令会统一成冒号形式。
- `--parents-depth`：可选，向上包含多少层父节点，必须是非负整数。
- `--children-depth`：可选，向下 BFS 包含多少层子节点，必须是非负整数。

不传两个 depth 参数时仍返回起始节点。结果中的每个节点包含 `node_id`、`name`、`figma_type`、`pre`、`next` 及服务端保存的其他 Figma 字段。

这是 **read-only** 的 ✅ bytedcli command，不修改索引。若节点不存在，先确认已运行 `bytedcli d2c figma get`，并检查两个命令使用的是同一个完整 Figma URL。

不要绕过 bytedcli 直接调用 HTTP 接口。
