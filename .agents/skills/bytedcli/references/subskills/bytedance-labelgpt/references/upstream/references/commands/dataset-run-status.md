# bytedcli labelgpt dataset 运行与状态

查询导入/导出 Process 或 Dataset Agent Task 进度，停止 Dataset Agent Task，并在数据集上提交 Agent 批量运行任务。`dataset status` 和 `dataset stop` 按 ID 操作，不强制要求 `space-id`；`dataset run` 依赖目标 Space。

## 快速导航

- [dataset status](#dataset-status)：查询 Process 或 Task 进度。
- [dataset stop](#dataset-stop)：终止 `dataset run` 启动的 Dataset Agent Task。
- [dataset run](#dataset-run)：在整个数据集或指定数据项上运行 Agent。
- 数据集创建和查询见 [dataset-query.md](dataset-query.md)。
- 导入和导出提交见 [dataset-transfer.md](dataset-transfer.md)。

## dataset status

支持两种互斥模式：

- **Process 模式**：查询一个或多个导入/导出 Process。
- **Task 模式**：查询 `dataset run` 返回的一个或多个 Agent 批量 Task。

### 用法

```bash
bytedcli labelgpt dataset status (--process-id <PROCESS_ID>... | <PROCESS_ID>...) [选项]
bytedcli labelgpt dataset status --task-id <TASK_ID>... [选项]
```

Process ID 或 Task ID 都可通过重复 flag 与位置参数传入。所有 ID 必须是正 int64；重复值按 canonical 十进制字符串去重并保留首次出现顺序。

### 示例

```bash
# Process 模式
bytedcli labelgpt dataset status --process-id <PROCESS_ID>
bytedcli labelgpt dataset status <PROCESS_ID_1> <PROCESS_ID_2> --format raw
bytedcli labelgpt dataset status --process-id <PROCESS_ID_1> --process-id <PROCESS_ID_2> -o ./out

# Task 模式
bytedcli labelgpt dataset status --task-id <TASK_ID>
bytedcli labelgpt dataset status --task-id <T1> --task-id <T2> --format raw
bytedcli labelgpt dataset status --task-id <TASK_ID> <TASK_ID_2> -o ./out
```

### 参数说明

- `--process-id <PROCESS_ID>`：导入或导出 Process ID，可重复传；默认模式下位置参数也归属 Process。与 `--task-id` 互斥。
- `--task-id <TASK_ID>`：Agent 批量 Task ID，可重复传；Task 模式下位置参数也归属 Task。与 `--process-id` 互斥。

### 输出

Process 模式输出：

- `processes[]`：包含 Process ID、总体状态、导入/执行计数、导入/Agent/导出阶段状态、`send_groups`、`finished` 和 `failed`。
- `send_groups[]`：包含 task group、发送计数、导出类型、文件类型和 `export_url`。
- `stop`：所有 Process 都不在 wait_processing/processing 时为 true。
- `found`、`missing`。

Task 模式输出：

- `tasks[]`：包含 Task ID、状态、完成量/总量、`agent_groups`、时间字段、`finished` 和 `failed`。
- `agent_groups[]`：包含 group 标识、模式、子节点、完成状态、计数、进度比例和模型离线类型。
- `stop`、`found`、`missing`。

`pretty` 下 Process 模式展示导出 URL，Task 模式展示任务进度和 Group 数量。

### 输出文件

- `-o <DIR>`：两种模式都写入 `dataset_status_<timestamp>.json`；存在时追加时间戳。

### 注意事项

- 按 Process ID 或 Task ID 查询，不强制要求 `space-id`；显式传入时仍作为请求头发送。
- 两种模式互斥。
- 命令不会自动轮询。需要等待终态时，在调用侧固定间隔重复查询，直到 `stop == true` 或所有目标 `finished == true`，再用 `failed` 判断成功/失败。
- 机器调用优先使用 `--format raw`。

## dataset stop

终止一个仍在排队、执行或暂停中的 Dataset Agent Task。

```bash
bytedcli labelgpt dataset stop --task-id <TASK_ID> --format raw
```

- `--task-id` 必填，只接受一个正 int64。
- Task ID 来自 `dataset run`，即底层批量运行返回的任务标识。
- 操作不可逆；服务端拒绝停止已经完成、失败或终止的 Task。
- 服务端终止整个批量 Task，并级联终止正在运行的 Agent 数据。
- `raw/json` 输出 `task_id` 和 `stopped`。
- 按 Task ID 定位，不强制要求 `space-id`。
- 导入/导出产生的 Process 不支持通过此命令停止。

## dataset run

在数据集上运行 Agent 编排方案。

### 用法

```bash
bytedcli labelgpt dataset run --id <DATASET_ID> --agent-id <AGENT_ID> --space-id <SPACE_ID> [--data-item-id <ID>... | <ID>...]
```

### 示例

```bash
bytedcli labelgpt dataset run --id <DATASET_ID> --agent-id <AGENT_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset run --id <DATASET_ID> --agent-id <AGENT_ID> --space-id <SPACE_ID> --data-item-id <DATA_ITEM_ID_1>
bytedcli labelgpt dataset run --id <DATASET_ID> --agent-id <AGENT_ID> --space-id <SPACE_ID> <DATA_ITEM_ID_1> <DATA_ITEM_ID_2> --format raw
bytedcli labelgpt dataset run --id <DATASET_ID> --agent-id <AGENT_ID> --space-id <SPACE_ID> --dry-run --format raw
```

不传数据项 ID 时处理整个数据集；提交后立即返回 `task_id`，不等待执行完成。

### 参数说明

- `--id <DATASET_ID>`：目标数据集 ID，必填。
- `--agent-id <AGENT_ID>`：Agent ID，必填。
- `--data-item-id <ID>`：可选且可重复；位置参数也作为数据项 ID。不传时处理整个数据集。
- `--dry-run`：只校验数据集列名与 Agent 的数据集输入字段绑定，输出报告但不提交任务。

### 输出

`raw/json` 输出 `id`、`task_id`、`agent_id`、`agent_name`、输出 `fields`、`data_item_count` 和 `submitted`。

`--dry-run` 改为输出校验报告：`id`、`agent_id`、`agent_name`、`dry_run`、`valid`、`dataset_columns`、`bindings`（每项含 `column`、`field_key`、`node_key`、`required`、`present`）、`unused`、`errors`、`warnings` 和 `data_item_count`。存在必填绑定列缺失时 `valid=false`，命令返回非零退出码。

### 输出文件

- `-o <DIR>`：写入 `dataset_run_<timestamp>.json`；`--dry-run` 写入 `dataset_run_dry_run_<timestamp>.json`。

### 注意事项

- 必须显式传 `--space-id <SPACE_ID>`；`--dry-run` 同样读取受 Space 约束的资源，仍需 `--space-id`。
- Fire-and-forget，不轮询任务状态。`task_id` 与导入/导出的 `process_id` 是不同概念；使用 `dataset status --task-id` 查询。
- `--dry-run` 只做本地列名与输入绑定校验，不提交任务，不返回 `task_id`；建议在正式提交前先跑一次。
- 数据项 ID 支持 flag 和位置参数混用，自动去重、去空。
- 机器调用优先使用 `--format raw`。

## Schema 查询索引

```bash
bytedcli labelgpt schema dataset status --format raw
bytedcli labelgpt schema dataset stop --format raw
bytedcli labelgpt schema dataset run --format raw
```
