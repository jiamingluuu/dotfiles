# Agent 提交任务、获取结果与运行诊断

用于直接提交 Agent 任务、按 UUID 查询结果、查看 AgentData 状态，以及通过唯一的 `agent monitor` 入口检查总体指标和节点运行明细。详细字段见 [Agent 任务](../commands/agent-task.md) 与 [Agent 运行监控](../commands/agent-monitor.md)。

## 命令选择

- 提交任务：`agent task --send --id --param [--uuid]`。
- 查询结果：`agent task --status --uuid ...`。
- AgentData 状态、重试次数和 LogID：`agent task --detail`。
- 总体积压、吞吐和限流：`agent monitor overview --id`。
- 分页运行记录及节点明细：`agent monitor runs --id`。
- 单个 Data Item 的全部节点：`agent monitor item --id --data-item-id`。

`agent task --detail` 和 `agent monitor item` 不是同一个查询：前者按 UUID 或 Dataset 数据定位 AgentData 任务记录，不返回节点输入输出；后者按 Agent ID + Data Item ID 获取完整节点链路。

## 提交并查询结果

```bash
bytedcli labelgpt agent task --send --id <AGENT_ID> --uuid <UUID> \
  --param '{"text":"case 1"}' --format raw
bytedcli labelgpt agent task --status --uuid <UUID> --format raw
```

`--send` 提交后立即返回，`--status` 只做单次查询。批量查询时重复传 `--uuid`；`results[]` 按输入 UUID 顺序返回，`found=false` 表示暂未查到结果或节点日志。

## 查看 AgentData 状态

```bash
bytedcli labelgpt agent task --detail --uuid <UUID> --format raw
bytedcli labelgpt agent task --detail \
  --dataset-id <DATASET_ID> --dataset-data-id <DATASET_DATA_ID> \
  --id <AGENT_ID> --task-status 5 --format raw
```

`--detail` 必须选择单个 UUID，或同时提供 Dataset ID + Dataset Data ID；两种方式互斥。`--id` 只用于收窄 Dataset 查询。

## 查看总体指标与运行明细

`agent monitor` 的六个叶子只接受正整数 Agent ID，不接受 Agent 名称。只有名称时，在目标 Space 获取完整列表并按完整名称匹配：

```bash
bytedcli labelgpt agent list --all-pages --space-id <SPACE_ID> --format raw
```

从列表取得精确 ID 后再查询；存在重名时先请用户确认，不能猜测。

```bash
bytedcli labelgpt agent monitor overview --id <AGENT_ID> --format raw
bytedcli labelgpt agent monitor runs --id <AGENT_ID> --uuid <UUID> \
  --node-detail full --format raw
bytedcli labelgpt agent monitor runs --id <AGENT_ID> --status abnormal \
  --node-detail summary --page-num 1 --page-size 10 --format raw
bytedcli labelgpt agent monitor item --id <AGENT_ID> --data-item-id <DATA_ITEM_ID> \
  --process-id <PROCESS_ID> --node-detail full --format raw
```

- `runs` 可组合 Process ID、UUID、Channel、数据 ID、时间和状态筛选，同时提供时取交集。
- `runs --node-detail full` 返回节点输入输出；`summary` 只保留 `has_input/has_output`；`none` 完全省略节点明细。
- `item` 自动读取指定 Data Item 的全部节点分页，支持 `full|summary`；Process ID 可选，默认 `0`。
- `overview`、`tasks`、`health`、`runs`、`item`、`summary` 的其它约束和字段见 monitor 参考。

## 输出落盘

- task：`agent_task_<AGENT_ID>.json`、`agent_task_status_<TIMESTAMP>.json`、`agent_task_detail_<TIMESTAMP>.json`。
- monitor：`agent_monitor_<LEAF>_<AGENT_ID>.json`，例如 `agent_monitor_overview_123.json`、`agent_monitor_runs_123.json`、`agent_monitor_item_123.json`。
- 目标文件重名时会追加时间戳，避免静默覆盖。

## 常见错误

- 只有 UUID 且要节点输入输出：先执行 `agent task --status --uuid <UUID>`，再向用户索要 Agent ID；拿到 ID 后用 `agent monitor runs --id <AGENT_ID> --uuid <UUID> --node-detail full`。
- 只有 Agent 名称：用 `agent list --all-pages` 获取精确 ID；名称不唯一时请用户确认。
- 把 `detail` 当节点详情：它只返回 AgentData 状态、重试和 LogID。
- 把 Dataset `task_id` 当 UUID：`dataset run` 的进度只能用 `dataset status --task-id <TASK_ID>`。
