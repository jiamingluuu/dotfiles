---
name: bytedance-rca
description: "Operate RCA (Root Cause Analysis) via bytedcli: analyze biz error codes, batch-analyze unavailable events in a time window, route through the general-rca service. Use when tasks mention RCA, 业务错误归因, 错误码归因, 不可用事件分析, biz error analysis, or 风险归因."
---

# RCA

RCA（Root Cause Analysis）平台的 CLI 操作工具，底层走 general-rca service（默认 `https://eofwxqpn.fn.bytedance.net`）。

通用调用方式（`npx` / 全局安装、`--site` 站点切换、`--json` 输出、`--http-debug` 等调试 flag）见 [../../invocation.md](../../invocation.md)。命令报错排查见 [../../troubleshooting.md](../../troubleshooting.md)。

## Capabilities

- 业务错误归因（指定错误码）：已知 PSM + Method + 错误码列表，直接归因
- 业务错误归因（时间窗）：按 PSM + Method + 时间窗，拉取该窗口内所有不可用事件批量归因，HTTP/RPC 自动按 `--type` 透传
- 知识库联动：归因结果可回写到 eops 与知识库（默认开启，可用 `--no-push-eops` 关闭）

## Usage

```bash
# 已知错误码，直接归因（PERCENT 可选）
bytedcli rca biz execute \
  --psm example.demo.svc \
  --method ExampleMethod \
  --codes 60001:80,60002:20

# 已知错误码，显式指定接口类型（http 或 rpc）
bytedcli rca biz execute \
  --psm example.demo.svc \
  --method ExampleMethod \
  --codes 60001 \
  --type http

# 按时间窗批量归因（不传时间默认昨天 CST/UTC+8；只传一端时另一端自动对齐成同一天）
bytedcli rca biz execute \
  --psm example.demo.svc \
  --method ExampleMethod \
  --start 2026-06-01 \
  --end 2026-06-10

# 调试时关闭 eops 上报
bytedcli rca biz execute --psm xxx --method yyy --codes 60001 --no-push-eops

# Agent 调用必须加上 --json
bytedcli --json rca biz execute --psm xxx --method yyy --start 2026-06-01
```

## Options

### `rca biz execute`

模式选择规则：

- `--codes` 与 `--start/--end` 互斥（不能同时传）。
- `--codes` 与 `--start/--end` 至少传一项；三者都不传会以 `RCA_INPUT_ERROR` 拒绝。
- 时间窗模式（mode B）下，只传 `--start` 或 `--end` 任一端均合法，另一端自动对齐为同一天；都不传时默认为昨天（CST / UTC+8 口径）。

| Option                 | Required | 说明                                                                                 |
| ---------------------- | -------- | ------------------------------------------------------------------------------------ |
| `--psm <psm>`          | yes      | 服务 PSM，例如 `example.demo.svc`                                                    |
| `--method <method>`    | yes      | RPC method 或 HTTP path                                                              |
| `--codes <codes>`      | mode A   | 指定错误码归因模式：错误码列表，逗号分隔；支持 `KEY:PERCENT`，如 `60001:80,60002:20` |
| `--start <YYYY-MM-DD>` | mode B   | 时间窗起始日期；进入 mode B 后若省略，默认昨天（CST/UTC+8）                          |
| `--end <YYYY-MM-DD>`   | mode B   | 时间窗结束日期；进入 mode B 后若省略，与 `--start` 同日；只传一端时另一端自动对齐    |
| `--type <type>`        | no       | 接口类型 `http\|rpc`，仅 `--codes` 模式生效                                          |
| `--no-push-eops`       | no       | 不将分析结果上报 eops（调试用）                                                      |

`--codes KEY:PERCENT` 中 PERCENT 必须是 0-100 的数字；裸错误码（如 `60001`）原样保留为字符串，不会自动补 100。

## Service Endpoint

默认调用 service `https://eofwxqpn.fn.bytedance.net`。如需指向私有部署或本地开发：

```bash
export BYTEDCLI_RCA_BASE_URL=http://127.0.0.1:8181
bytedcli rca biz execute --psm xxx --method yyy --start 2026-06-01
```

也可以在 `~/.bytedcli/config.json` 设置 `rcaBaseUrl`。

## 已知约束

- service invoke timeout 默认 60s，时间窗超过 1~3 天的时间窗模式调用容易触发 `function_invoke_timeout`，建议分段拉取，或在控制台调高 invoke timeout。
- `--no-push-eops` 仅影响 eops 上报，不影响归因结果返回。

## Troubleshooting

详见 [../../troubleshooting.md](../../troubleshooting.md)。RCA 相关常见错误：

- `RCA_INPUT_ERROR`：参数格式问题（缺 `--psm/--method`、`--codes` 解析为空、`--codes 60001:` 缺 PERCENT、PERCENT 越界等）。按错误 `hint` 修正即可。
- `RCA_SCHEMA_ERROR`：非法日期格式（`--start/--end` 必须是 `YYYY-MM-DD`）或 service 返回的字段不符合预期。
- `function_invoke_timeout`：时间窗过大，分段拉取或调大 service invoke timeout。
