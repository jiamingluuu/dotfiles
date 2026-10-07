# bytedcli labelgpt dataset 传输

Dataset 传输命令向已有数据集提交导入或导出任务。命令提交后立即返回 `process_id`，不等待完成；进度查询见 [dataset-run-status.md](dataset-run-status.md)。

## 快速导航

- [dataset import](#dataset-import)：从本地文件、HDFS、Hive、Aeolus 或飞书导入。
- [dataset export](#dataset-export)：导出为文件、HDFS、Hive、飞书或其他数据集。
- 数据集创建和查询见 [dataset-query.md](dataset-query.md)。
- Process 状态与 Dataset Agent 运行见 [dataset-run-status.md](dataset-run-status.md)。

## dataset import

### 用法

```bash
bytedcli labelgpt dataset import <csv|json|jsonl|hdfs|hive|aeolus|lark> --id <DATASET_ID> --space-id <SPACE_ID> [选项]
```

### 示例

```bash
bytedcli labelgpt dataset import csv --id <DATASET_ID> --space-id <SPACE_ID> --file ./data.csv
bytedcli labelgpt dataset import json --id <DATASET_ID> --space-id <SPACE_ID> --file ./data.json
bytedcli labelgpt dataset import jsonl --id <DATASET_ID> --space-id <SPACE_ID> --file ./data.jsonl --format raw
bytedcli labelgpt dataset import hdfs --id <DATASET_ID> --space-id <SPACE_ID> --hdfs-path /home/user/data/file.jsonl --hdfs-file-type jsonl
bytedcli labelgpt dataset import hive --id <DATASET_ID> --space-id <SPACE_ID> --hive-table db.table --hive-sql 'select * from db.table'
bytedcli labelgpt dataset import aeolus --id <DATASET_ID> --space-id <SPACE_ID> --aeolus-dataset-id <AEOLUS_DATASET_ID> --aeolus-client-id <CLIENT_ID> --aeolus-secret <SECRET> --aeolus-sql 'select *'
bytedcli labelgpt dataset import lark --id <DATASET_ID> --space-id <SPACE_ID> --lark-url https://...
```

提交后使用：

```bash
bytedcli labelgpt dataset status --process-id <PROCESS_ID> --format raw
```

如需等待终态，在调用侧循环查询，直到 `stop == true` 或 `processes[].finished == true`，再用 `processes[].failed` 判断成功或失败。完整流程见 [Dataset 导入导出与 Agent 运行](../user_case/dataset_import_export_agent_run.md)。

### Source 子命令

| 子命令 | 必填参数 |
| --- | --- |
| `csv` | `--file <local.csv>` |
| `jsonl` | `--file <local.jsonl>` 或 `--file <local.txt>` |
| `json` | `--file <local.json>` |
| `hdfs` | `--hdfs-path`、`--hdfs-file-type <json|jsonl|csv|parquet>` |
| `hive` | `--hive-table`、`--hive-sql` |
| `aeolus` | `--aeolus-dataset-id`、`--aeolus-client-id`、`--aeolus-secret`、`--aeolus-sql` |
| `lark` | `--lark-url` |

`aeolus` 支持 alias `fengshen`；`lark` 支持 alias `feishu`。

### 参数说明

- `--id <DATASET_ID>`：目标数据集 ID，必填。
- `--tag <TAG>`、`--remark <TEXT>`：可选标签和备注。
- `--file <PATH>`：仅用于 csv/json/jsonl。
- `--hdfs-path`、`--hdfs-file-type`：仅用于 HDFS，文件类型支持名称或 `1/2/3/4`。
- `--hive-table`、`--hive-sql`、可选 `--region`：仅用于 Hive。
- `--aeolus-dataset-id`、`--aeolus-client-id`、`--aeolus-secret`、`--aeolus-sql`：仅用于 Aeolus。
- `--lark-url <URL>`：仅用于飞书。

### 输出

`raw/json` 输出 `id`、`process_id`、规范化 `source`、`submitted`，以及文件型导入的 `file_name` / `file_url`。

### 输出文件

- `-o <DIR>`：写入 `dataset_import_<source>_<timestamp>.json`；存在时追加时间戳。

### 注意事项

- 必须显式传 `--space-id <SPACE_ID>`。
- `--aeolus-secret` 不在命令输出中回显；避免不必要的 `--debug`，调试日志可能包含输入内容。

## dataset export

### 用法

```bash
bytedcli labelgpt dataset export <csv|json|jsonl|lark|hdfs|hive|dataset> --id <DATASET_ID> --space-id <SPACE_ID> [选项]
```

### 示例

```bash
bytedcli labelgpt dataset export csv --id <DATASET_ID> --space-id <SPACE_ID>
bytedcli labelgpt dataset export json --id <DATASET_ID> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset export jsonl --id <DATASET_ID> --space-id <SPACE_ID> --fields text,label --format raw
bytedcli labelgpt dataset export json --id <DATASET_ID> --space-id <SPACE_ID> \
  --data-tag eval --create-time-start 1783413650000 --create-time-end 1783595894000 --format raw
bytedcli labelgpt dataset export lark --id <DATASET_ID> --space-id <SPACE_ID>
bytedcli labelgpt dataset export hdfs --id <DATASET_ID> --space-id <SPACE_ID> --hdfs-path /data/export --hdfs-file-type jsonl
bytedcli labelgpt dataset export hive --id <DATASET_ID> --space-id <SPACE_ID> --hive-table db.export_table
bytedcli labelgpt dataset export dataset --id <DATASET_ID> --space-id <SPACE_ID> --target-dataset-id <TARGET_ID>
```

提交后循环 `dataset status --process-id` 等待终态；成功后从 `processes[].send_groups[].export_url` 读取文件下载链接。

### Target 子命令

| 子命令 | 必填参数 |
| --- | --- |
| `csv` | 无 |
| `json` | 无 |
| `jsonl` | 无 |
| `lark` | 无 |
| `hdfs` | `--hdfs-path`、`--hdfs-file-type <json\|jsonl\|csv\|parquet>` |
| `hive` | `--hive-table`（`--region` 可选） |
| `dataset` | `--target-dataset-id` |

`lark` 支持 alias `feishu`。

### 参数说明

- `--id <DATASET_ID>`：源数据集 ID，必填。
- `--fields <FIELDS>`：可重复传或逗号分隔；为空时导出全部字段。
- `--data-item-id`、`--source-type`、`--data-tag`、`--create-user-id`：行筛选参数；支持
  重复传入或逗号分隔，CLI 会 trim、去空、去重并保序。`--executor-status` 和
  `--process-id` 是单值字符串筛选。`--executor-status` 仅接受 `正常` 或 `异常`，传其他值
  会直接报错并非零退出（尚未运行的数据不写入状态，无法按「未执行」过滤）。
- `--data-remark <TEXT>`：数据备注行筛选。
- `--create-time-start <UNIX_MS>`、`--create-time-end <UNIX_MS>`：创建时间行筛选，
  使用 Unix 毫秒且 start <= end。
- `--filter-file <PATH>`：严格解析 `.json`、`.yaml`、`.yml` 的 version 1 筛选文件。
- `--hdfs-path`、`--hdfs-file-type`：仅用于 HDFS。
- `--hive-table <db.table>`、`--region`：仅用于 Hive；表名必须是 `db.table`。
- `--target-dataset-id <ID>`：仅用于导出到其他数据集。

### 筛选文件契约

筛选文件顶层只接受 `version`、`feature_filter` 和 `sampling`，其中 `version` 必须为
`1`。`feature_filter` 使用 `relation: and|or`、`groups` 和每组的
`relation: and|or`、`conditions`；relation 省略或只包含空白时默认为 `and`。
条件字段为 `field`、`operator` 和按算子选择的 `value` 或 `values`。支持
`equals`、`not_equals`、`contains`、`not_contains`、`is_null`、`is_not_null`、
`regex`、`length_greater_than`、`length_greater_than_or_equal`、
`length_less_than`、`length_less_than_or_equal`、`number_greater_than`、
`number_greater_than_or_equal`、`number_less_than`、`number_less_than_or_equal`、
`time_equals`、`time_not_equals`、`time_greater_than`、
`time_greater_than_or_equal`、`time_less_than`、`time_less_than_or_equal`、
`in` 和 `not_in`。`in`/`not_in` 要求非空 `values`，null 算子不得有比较值，
其他算子使用 `value`；不支持字段间比较。`sampling` 必须严格是
`{type: quantity|ratio, value: ...}`：quantity value 为正整数，ratio value
为 1–100 的整数，分别映射后端 `DistributeType=2/3`。JSON/YAML/YML 等价，
未知字段、旧 sampling 结构、非法扩展名、关系、算子、正则、数值、时间或抽样在认证
和 HTTP 请求前拒绝；旧的缩写 operator 名称也会拒绝。

命令行筛选与文件条件按 AND 组合，抽样在全部条件命中后应用。没有筛选参数时不发送
`ListDatasetDataRequest`；有筛选时该嵌套请求带源 `DataSetId`。`--fields` 只写入
`SendGroups[].ExportFields`，而 `SendGroups[].ExtractStrategy.DistributeType` 始终为
`0`。

### 行为与输出

- 提交后立即返回，不表示导出完成。
- `raw/json` 输出 `id`、`process_id`、`target` 和 `submitted`。

### 输出文件

- `-o <DIR>`：写入 `dataset_export_<target>_<timestamp>.json`；存在时追加时间戳。

### 注意事项

- 必须显式传 `--space-id <SPACE_ID>`。
- 导出不支持导入用的 `--tag` / `--remark`；行筛选请使用 `--data-tag` / `--data-remark`。
- 文件类导出链接通过 `dataset status` 的 `send_groups[].export_url` 获取。
- Magnus HDFS/Hive 直导路径可能绕过服务端顶层筛选；CLI 仍发送筛选，但不承诺该路径
  一定应用，也不因此阻断提交。
- DOLA 空间不支持 CSV/JSON/JSONL 导出。
- 机器调用优先使用 `--format raw`。

## Schema 查询索引

```bash
bytedcli labelgpt schema dataset import csv --format raw
bytedcli labelgpt schema dataset import json --format raw
bytedcli labelgpt schema dataset import jsonl --format raw
bytedcli labelgpt schema dataset import hdfs --format raw
bytedcli labelgpt schema dataset import hive --format raw
bytedcli labelgpt schema dataset import aeolus --format raw
bytedcli labelgpt schema dataset import lark --format raw
bytedcli labelgpt schema dataset export csv --format raw
bytedcli labelgpt schema dataset export json --format raw
bytedcli labelgpt schema dataset export jsonl --format raw
bytedcli labelgpt schema dataset export lark --format raw
bytedcli labelgpt schema dataset export hdfs --format raw
bytedcli labelgpt schema dataset export hive --format raw
bytedcli labelgpt schema dataset export dataset --format raw
```
