# Dataset 导入 / 导出 / 关联 Agent 执行

用于数据集创建、搜索、数据条目查询、导入、导出，以及在 Dataset 上批量运行 Agent。详细命令字段见
[Dataset 查询](../commands/dataset-query.md)、[Dataset 传输](../commands/dataset-transfer.md)
和 [Dataset 运行与状态](../commands/dataset-run-status.md)。

## 快速导航

- 创建、修复元信息和查询数据集：`dataset init/update/list/items`。
- 导入数据：`dataset import csv/json/jsonl/hdfs/hive/aeolus/lark`。
- 导出数据：`dataset export csv/json/jsonl/lark/hdfs/hive/dataset`。
- 轮询进度：`dataset status --process-id`。
- 关联 Agent 执行：`dataset run` + `dataset status --task-id`。

## 核心原则

- 认证启动前自检由主 `SKILL.md` 统一完成；需要目标 Space 时在业务命令上显式传 `--space-id <SPACE_ID>`，不要切换默认 Space。
- `DATASET_ID` 是数据集 ID；`PROCESS_ID` 来自 `dataset import/export`；`TASK_ID` 来自 `dataset run`；`AGENT_ID` 是 Agent ID。
- `dataset import/export/run` 都是异步提交，不等待终态，也没有内置等待 flag。
- `dataset status --process-id` 查询导入/导出 process；`dataset status --task-id` 查询 Dataset 上 Agent 批量任务。
- 直接 UUID 调用 Agent 不属于本场景，使用 `agent_task_result_inspect.md` 的 `agent task --send/--status`。

## 创建和查询数据集

```bash
bytedcli labelgpt dataset init --name <DATASET_NAME> --sensitivity-level 2 --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset update --id <DATASET_ID> --sensitivity-level 2 --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset list --name <KEYWORD> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset list --id <DATASET_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset items --id <DATASET_ID> --space-id <SPACE_ID> --page-size 50 --format raw
bytedcli labelgpt dataset items --id <DATASET_ID> --space-id <SPACE_ID> --field prompt --field answer --format raw
```

`dataset init/update/list/items` 是同步创建、更新或查询，不产生 `process_id`。创建时敏感级别无默认值；历史数据集可用 `dataset update` 补齐后再导出。

## 导入数据

文件导入：

```bash
bytedcli labelgpt dataset import csv --id <DATASET_ID> --space-id <SPACE_ID> --file ./data.csv --format raw
bytedcli labelgpt dataset import json --id <DATASET_ID> --space-id <SPACE_ID> --file ./data.json --format raw
bytedcli labelgpt dataset import jsonl --id <DATASET_ID> --space-id <SPACE_ID> --file ./data.jsonl --format raw
```

外部源导入：

```bash
bytedcli labelgpt dataset import hdfs --id <DATASET_ID> --space-id <SPACE_ID> \
  --hdfs-path <HDFS_PATH> --hdfs-file-type jsonl --format raw
bytedcli labelgpt dataset import hive --id <DATASET_ID> --space-id <SPACE_ID> \
  --hive-table <DB.TABLE> --hive-sql '<SQL>' --format raw
bytedcli labelgpt dataset import aeolus --id <DATASET_ID> --space-id <SPACE_ID> \
  --aeolus-dataset-id <AEOLUS_DATASET_ID> \
  --aeolus-client-id <CLIENT_ID> \
  --aeolus-secret <SECRET> \
  --aeolus-sql '<SQL>' --format raw
bytedcli labelgpt dataset import lark --id <DATASET_ID> --space-id <SPACE_ID> --lark-url <LARK_URL> --format raw
```

导入成功只表示 process 已提交。记录输出里的 `process_id`。

## 导出数据

文件或表格导出：

```bash
bytedcli labelgpt dataset export csv --id <DATASET_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset export json --id <DATASET_ID> --space-id <SPACE_ID> --fields prompt,answer --format raw
bytedcli labelgpt dataset export jsonl --id <DATASET_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset export lark --id <DATASET_ID> --space-id <SPACE_ID> --format raw
```

导出可以在提交前筛选数据行；列表参数支持重复传入或逗号分隔，时间使用 Unix 毫秒：

```bash
bytedcli labelgpt dataset export json \
  --id <DATASET_ID> --space-id <SPACE_ID> \
  --data-item-id <ITEM_1> --data-item-id <ITEM_2> \
  --data-tag eval --create-time-start 1783413650000 --create-time-end 1783595894000 \
  --format raw
```

复杂条件使用 version 1 的 `.json` / `.yaml` / `.yml` `--filter-file`。文件支持
`feature_filter` 的 and/or 条件组、全部 1-23 算子，以及严格的
`sampling: {type: quantity|ratio, value: ...}`；quantity value 为正整数，
ratio value 为 1–100 的整数。relation 省略或空白时默认为 `and`。flags 与文件按
AND 组合，抽样在条件命中后执行。`--fields` 只控制导出字段，不是筛选条件。未知字段、
旧 sampling 结构、旧缩写 operator、非法关系/算子/正则/数值/时间/抽样会在认证和网络
请求前失败。

外部目标导出：

```bash
bytedcli labelgpt dataset export hdfs --id <DATASET_ID> --space-id <SPACE_ID> \
  --hdfs-path <HDFS_PATH> --hdfs-file-type jsonl --format raw
bytedcli labelgpt dataset export hive --id <DATASET_ID> --space-id <SPACE_ID> \
  --hive-table <DB.TABLE> --format raw
bytedcli labelgpt dataset export dataset --id <DATASET_ID> --space-id <SPACE_ID> \
  --target-dataset-id <TARGET_DATASET_ID> --format raw
```

导出成功只表示 process 已提交。完成后从 `dataset status` 的 `processes[].send_groups[].export_url` 读取下载链接。
无筛选时 CLI 保持旧请求形态，不发送嵌套 `ListDatasetDataRequest`；有筛选时才发送带源
Dataset ID 的顶层筛选请求。Magnus HDFS/Hive 直导路径可能绕过服务端顶层筛选，CLI 会
发送筛选但不承诺该路径一定应用，也不会因此阻断提交。

## 轮询导入 / 导出进度

单次查询：

```bash
bytedcli labelgpt dataset status --process-id <PROCESS_ID> --format raw
bytedcli labelgpt dataset status --process-id <P1> --process-id <P2> --format raw
```

需要等待终态时，由调用侧循环执行 `dataset status`，直到顶层 `stop == true` 或目标 `processes[].finished == true`。成功/失败用 `processes[].failed` 判定。

```bash
PROCESS_ID=<PROCESS_ID>
for i in $(seq 1 120); do
  STATUS_JSON=$(bytedcli labelgpt dataset status --process-id "$PROCESS_ID" --format raw)
  echo "$STATUS_JSON"
  if echo "$STATUS_JSON" | jq -e '.stop == true' >/dev/null; then
    echo "$STATUS_JSON" | jq -e 'all(.processes[]; .failed == false)' >/dev/null
    break
  fi
  sleep 5
done
```

## 在数据集上运行 Agent

```bash
bytedcli labelgpt dataset run \
  --id <DATASET_ID> \
  --agent-id <AGENT_ID> \
  --space-id <SPACE_ID> \
  --format raw
```

只运行指定数据项：

```bash
bytedcli labelgpt dataset run \
  --id <DATASET_ID> \
  --agent-id <AGENT_ID> \
  --space-id <SPACE_ID> \
  --data-item-id <ITEM_ID_1> \
  --data-item-id <ITEM_ID_2> \
  --format raw
```

记录输出里的 `task_id`，用 Dataset Task 模式查询：

```bash
bytedcli labelgpt dataset status --task-id <TASK_ID> --format raw
```

不要用 `agent task --status` 查询 `dataset run` 的 `task_id`；它只接受直接 Agent UUID。

## 常见错误

- `--space-id is required`：在当前业务命令中显式追加 `--space-id <SPACE_ID>`。
- `--sensitivity-level is required`：所有站点创建 Dataset 都必须显式选择 `1|2|3|4`；历史 Dataset 用 `dataset update --id ... --sensitivity-level ...` 修复。
- 把 `PROCESS_ID` 当 `TASK_ID`：导入/导出只用 `--process-id`，Dataset 上跑 Agent 才用 `--task-id`。
- 想等待任务完成：CLI 不内置等待；必须循环调用 `dataset status` 并设置最大轮询次数。
- `aeolus-secret` 不会在输出里回显；避免在不必要时开启 `--debug`。
