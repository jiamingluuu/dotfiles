# bytedcli labelgpt agent monitor

只读查看 Agent 的运行指标、任务积压、节点健康度和运行记录。这是运行监控的唯一入口。所有叶子都要求正整数 `--id`，按 Agent ID 定位，不强制要求 `space-id`。

`agent monitor` 不支持 `--name`。只有 Agent 名称时，先在目标 Space 执行 `agent list --all-pages --format raw`，按完整名称匹配并取得精确 Agent ID；如果名称不唯一，先请用户确认，不能猜测。

## 快速导航

```bash
bytedcli labelgpt agent monitor overview --id <AGENT_ID> --format raw
bytedcli labelgpt agent monitor tasks --id <AGENT_ID> --format raw
bytedcli labelgpt agent monitor health --id <AGENT_ID> --format raw
bytedcli labelgpt agent monitor runs --id <AGENT_ID> --format raw
bytedcli labelgpt agent monitor item --id <AGENT_ID> --data-item-id <DATA_ITEM_ID> --format raw
bytedcli labelgpt agent monitor summary --id <AGENT_ID> --format raw
```

### overview

返回总体积压、吞吐、运行量、处理耗时、限流、首次执行耗时和模型限流指标，包括可选的自适应 QPM/并发上限。

### tasks

返回 `channel_tasks` 和 `process_tasks`。每项含 Dataset、Process、来源与状态文本、处理/排队/重试数量、耗时、Channel 和 QPM；空列表固定为 `[]`。

### health

```bash
bytedcli labelgpt agent monitor health --id <AGENT_ID> \
  --start-time "2026-08-26 10:00" --end-time "2026-08-26 10:30:00" --format raw
```

- `--start-time` 与 `--end-time` 必须成对提供，接受 `YYYY-MM-DD HH:mm` 或 `YYYY-MM-DD HH:mm:ss`。开始时间不得晚于结束时间。
- 两者都省略时使用最近五分钟窗口。
- 返回节点状态、错误率、平均响应耗时和执行量，以及健康、预警、异常计数。

### runs

```bash
bytedcli labelgpt agent monitor runs --id <AGENT_ID> \
  --status abnormal --node-detail summary --page-num 1 --page-size 10 --format raw
```

- 可组合 `--process-id`、`--uuid`、`--channel`、`--data-id`、起止时间过滤；同时提供时取交集。
- `--status` 为 `all|success|abnormal`，默认 `all`。
- `--node-detail` 为 `full|summary|none`，默认 `full`。`full` 包含节点输入输出；`summary` 只保留是否存在输入输出；`none` 不查询节点明细。无需查看业务 payload 时优先用 `summary` 或 `none`。
- 分页默认 `1/10`，页码和页大小必须大于 0。任何节点明细查询失败都会使命令整体失败，不返回静默截断结果。

### item

```bash
bytedcli labelgpt agent monitor item --id <AGENT_ID> --data-item-id <DATA_ITEM_ID> \
  --process-id <PROCESS_ID> --node-detail summary --format raw
```

- `--data-item-id` 必填；`--process-id` 可选且必须为非负整数，默认 0。
- 自动读取该数据项的全部节点分页。`--node-detail` 支持 `full|summary`，默认 `full`。
- 任一分页失败则整体失败，不输出不完整节点列表。

### summary

```bash
bytedcli labelgpt agent monitor summary --id <AGENT_ID> --top 5 --format raw
```

- 并行汇总总体指标、任务和节点健康度；任一来源失败则整体失败，不输出部分摘要。
- `--top` 控制积压任务和慢节点数量，范围 `1..50`，默认 5。
- 时间规则与 `health` 相同。无节点健康样本时 `health_status=unknown`。
- 摘要不包含节点输入输出、邮箱、IP、日志链接、Owner 或模型账号。

## 输出文件与 Schema

`raw/json` 的稳定顶层输出分别为：

- `overview`：Agent 标识及积压、吞吐、耗时、限流和模型调用指标。
- `tasks`：`agent_id`、`channel_tasks[]`、`process_tasks[]`。
- `health`：`agent_id`、`window`、`nodes[]` 和三类健康计数。
- `runs`：`agent_id`、筛选状态、节点明细级别、`runs[]`、`total` 和分页信息。
- `item`：Agent/Data Item/Process 标识、节点明细级别、Agent 版本、`total` 和 `nodes[]`。
- `summary`：Agent 标识、时间窗口、吞吐与任务计数、健康状态、积压榜和慢节点榜。

`-o <DIR>` 分别写入 `agent_monitor_<LEAF>_<AGENT_ID>.json`，例如 `agent_monitor_overview_123.json`、`agent_monitor_runs_123.json` 和 `agent_monitor_item_123.json`；同名文件已存在时追加时间戳。详细输入输出以对应 Schema V2 为准：

```bash
bytedcli labelgpt schema agent monitor runs --format raw
```
