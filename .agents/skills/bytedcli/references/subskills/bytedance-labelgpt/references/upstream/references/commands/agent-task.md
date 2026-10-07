# bytedcli labelgpt agent task

异步提交 Agent 送标任务、按 UUID 查询或停止任务，或查看 AgentData 执行细节。运行监控统一使用 [agent-monitor.md](agent-monitor.md)。

## 用法与模式

```bash
bytedcli labelgpt agent task --send --id <AGENT_ID> --param <JSON> [--uuid <UUID>] [选项]
bytedcli labelgpt agent task --status --uuid <UUID> [--uuid <UUID>...] [选项]
bytedcli labelgpt agent task --stop --uuid <UUID> [选项]
bytedcli labelgpt agent task --detail (--uuid <UUID> | --dataset-id <DATASET_ID> --dataset-data-id <DATASET_DATA_ID>) [选项]
```

四种模式互斥：

- `--send`：提交任务并立即返回。
- `--status`：按一个或多个 UUID 单次查询结果。
- `--stop`：停止一个排队中或运行中的 UUID 任务。
- `--detail`：查询 AgentData 当前执行状态、重试次数、LogID 和时间信息。

```bash
bytedcli labelgpt agent task --send --id <AGENT_ID> --param '{"foo":"bar"}' --format raw
bytedcli labelgpt agent task --send --id <AGENT_ID> --param '{"foo":"bar"}' --uuid <UUID> --format raw
bytedcli labelgpt agent task --status --uuid <UUID> --uuid <UUID2> --format raw
bytedcli labelgpt agent task --stop --uuid <UUID> --format raw
bytedcli labelgpt agent task --detail --uuid <UUID> --format raw
bytedcli labelgpt agent task --detail --dataset-id <DATASET_ID> --dataset-data-id <DATASET_DATA_ID> --id <AGENT_ID> --format raw
```

## 参数说明

- `--id <AGENT_ID>`：`--send` 必填；`--detail` 可用于收窄 Dataset 记录。
- `--param <JSON>`：`--send` 必填，必须是 JSON object 或 array。
- `--uuid <UUID>`：`--send` 可选且最多一个，未提供时 CLI 自动生成；`--status` 必填且可重复；`--stop` 必填且只接受一个；`--detail` 可选且最多一个。
- `--dataset-id` 与 `--dataset-data-id`：`--detail` 的 Dataset 查询条件，必须同时提供，且不能和 `--uuid` 同时提供。
- `--task-status <STATUS>`：`--detail` 可选状态筛选，常见值为 `0` 待处理、`1` 处理中、`2` 处理成功、`3` 处理失败、`4` 已拉取、`5` 重试中。
- `--page-num/--page-size`：`--detail` 的分页参数，必须大于 0，默认 `1/10`。

如提交提示登录信息无效或不完整，先执行 `bytedcli labelgpt auth logout`，再执行 `bytedcli labelgpt auth login`。

## 输出

### Send

`raw/json` 输出 `mode=send`、`plan_id`、`uuid`、`async=true`、`send` 和 `submitted`。

### Status

输出 `mode=status`、输入 `uuids` 和按输入顺序返回的 `results`。`results[]` 包含 `uuid`、`found`，以及存在时的 `result` 和 `node_execute_log`。CLI 只查询一次；需要等待终态时由调用侧按平台约束轮询，不要假定固定间隔或上限。

### Stop

`raw/json` 输出 `mode=stop`、`uuid`、`stopped=true` 和 `discarded=true`。停止操作不可逆。

### Detail

输出 `mode=detail`、查询条件 `query`、当前页 `records`、`total`、`page_num`、`page_size`。空结果固定为 `[]`。`records[]` 包含：

- AgentData/Agent：`agent_data_id`、`agent_id`、`agent_name`、`version_id`。
- 数据：`data_id`、`dataset_id`、`dataset_data_id`。
- 链路：`uuid`、`trace_uuid`、`branch_trace_uuid`、`channel`、`queue_id`、`batch_id`。
- 状态：`status`、`status_text`、`retry_count`。
- 日志和环境：`log_id`、`argo_log_link`、`env`、`tag`、`ip`、`email`。
- 时间：创建、修改、首次执行、触发、过期和预计过期时间，以及秒级 `execution_duration`。
- 送标：`send_label_platform`、`need_send_label`。

`detail` 不返回工作流节点输入输出，也不等价于 `agent monitor item`。已知 UUID 且要查看每个节点的输入输出时，还需要精确 Agent ID：

```bash
bytedcli labelgpt agent monitor runs --id <AGENT_ID> --uuid <UUID> --node-detail full --format raw
```

## 输出文件与注意事项

- `--send -o <DIR>`：`agent_task_<AGENT_ID>.json`。
- `--status -o <DIR>`：`agent_task_status_<TIMESTAMP>.json`。
- `--stop -o <DIR>`：`agent_task_stop_<TIMESTAMP>.json`。
- `--detail -o <DIR>`：`agent_task_detail_<TIMESTAMP>.json`。

各模式按 Agent ID、UUID 或数据 ID 定位，不强制要求 `space-id`。未选择模式或同时选择多个模式都会报错。

## Schema 查询索引

```bash
bytedcli labelgpt schema agent task --format raw
```
