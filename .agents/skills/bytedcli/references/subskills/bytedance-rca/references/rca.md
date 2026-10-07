# RCA

RCA（Root Cause Analysis）—— 业务错误归因 / 不可用事件批量归因，底层走 general-rca service。

```bash
# 已知错误码，直接归因（PERCENT 可选；PERCENT 必须是 0-100 数字）
bytedcli rca biz execute \
  --psm example.demo.svc \
  --method ExampleMethod \
  --codes 60001:80,60002:20

# 显式指定接口类型（仅 --codes 模式生效）
bytedcli rca biz execute --psm xxx --method yyy --codes 60001 --type http
bytedcli rca biz execute --psm xxx --method yyy --codes 60001 --type rpc

# 按时间窗批量归因（不传时间默认昨天 CST/UTC+8；只传一端时另一端自动对齐为同一天）
bytedcli rca biz execute \
  --psm example.demo.svc \
  --method ExampleMethod \
  --start 2026-06-01 \
  --end 2026-06-10

# 调试时关闭 eops 上报
bytedcli rca biz execute --psm xxx --method yyy --codes 60001 --no-push-eops

# Agent 调用统一加 --json
bytedcli --json rca biz execute --psm xxx --method yyy --start 2026-06-01
```

Options（`rca biz execute`）：

- `--psm <psm>`、`--method <method>`：必填
- `--codes <codes>`：错误码归因模式，逗号分隔；与 `--start/--end` 互斥；三者至少传一项
- `--start <YYYY-MM-DD>` / `--end <YYYY-MM-DD>`：时间窗模式；只传一端时另一端自动对齐为同一天；都不传时默认为昨天（CST/UTC+8）
- `--type <http|rpc>`：仅 `--codes` 模式生效
- `--no-push-eops`：调试时关闭 eops 回写

Service endpoint：

- 默认 `https://eofwxqpn.fn.bytedance.net`
- 覆盖优先级：`BYTEDCLI_RCA_BASE_URL` env > `~/.bytedcli/config.json` 的 `rcaBaseUrl` > 默认

Notes：

- service invoke timeout 默认 60s，时间窗 1~3 天以上易触发 `function_invoke_timeout`，建议分段拉取
- `RCA_INPUT_ERROR`：参数错误（缺必填、`--codes` 解析空、PERCENT 缺失/非数字/越界）
- `RCA_SCHEMA_ERROR`：日期格式错或 service 返回字段不符
