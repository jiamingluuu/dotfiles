---
name: bytedance-kelemetry
description: "Query Kelemetry Kubernetes object lifecycle traces via bytedcli. Use when tasks mention Kelemetry, K8s object trace, object lifecycle, traceID, pods/deployments/statefulsets events, or Kubernetes resource history."
---

# bytedcli Kelemetry

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 用户明确提到 Kelemetry。
- 需要按 Kubernetes resource/name/namespace 查询对象生命周期 trace；`--cluster` 只是可选 operation 过滤。
- 已有 traceID，需要拉取单条 trace 详情。

## 前置条件

- Kelemetry 使用 ByteCloud JWT，先执行 `bytedcli auth login`。
- 支持全局 `--site`：`cn`、`i18n`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`；`us-ttp-bdee`、`us-ttp-usts` 按 `us-ttp` 处理。
- 查询窗口建议保持在 1-2 小时内；默认 `--range 1h`。

> 示例省略 invocation 前缀。

## Quick start

```bash
# 查某个 Kubernetes 对象最近 1 小时的 trace 列表
bytedcli --json kelemetry search --name demo-pod --range 1h

# 指定 service 和时间窗口
bytedcli --json kelemetry search --resource deployments --name demo-deploy --namespace demo-namespace --service tracing --range 30m --limit 20

# 用绝对时间和 operation 查询
bytedcli --json kelemetry search --cluster demo-cluster --resource statefulsets --name demo-statefulset --namespace demo-namespace --start 2026-07-06T10:00:00+08:00 --end 2026-07-06T11:00:00+08:00

# 查看单条 trace
bytedcli --json kelemetry get --trace-id demo-trace-id
```

## 命令速查

```bash
kelemetry search [--cluster <cluster>] [--resource <resource>] [--name <name>] [--namespace <namespace>] [--service <service>] [--start <time>] [--end <time>] [--range <duration>] [--limit <n>]
kelemetry get --trace-id <traceID>
```

## 字段映射

- `--cluster` 映射 Kelemetry OpenAPI 的 `operation`；不传时省略该参数，由后端按 all 处理。
- `--resource`、`--name`、`--namespace` 组装为 Jaeger `tags` JSON，至少传一个。
- 未传 `--start/--end` 时，`--range` 映射为 Jaeger `lookback`；传绝对时间时转换为微秒 `start/end`。
- `--limit` 默认 1；需要批量浏览时显式调大。
- 文本输出只展示摘要；JSON 输出保留完整 trace payload。

## 结果读取

- `search` JSON 输出从 `data.traces[]` 读取 `traceID`、`spans`、`processes` 等原始 Jaeger trace 字段。
- `get` JSON 输出从 `data.trace` 读取单条 trace。
- 若 envelope 返回 `errors`，CLI 会抛 `KELEMETRY_API_ERROR`，先根据错误信息修正 traceID、时间窗口或对象过滤条件。
