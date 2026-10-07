# bytedcli labelgpt dataset 查询

Dataset 查询命令覆盖数据集创建、元信息更新、分页搜索和数据条目查询。这些命令依赖目标 Space。

## 快速导航

- [dataset init](#dataset-init)：创建空数据集。
- [dataset update](#dataset-update)：局部更新数据集元信息。
- [dataset list](#dataset-list)：分页搜索数据集。
- [dataset items](#dataset-items)：分页查询数据条目。
- 导入和导出见 [dataset-transfer.md](dataset-transfer.md)。
- Agent 运行和状态查询见 [dataset-run-status.md](dataset-run-status.md)。

## dataset init

创建一个空数据集。

### 用法

```bash
bytedcli labelgpt dataset init --name <DATASET_NAME> --sensitivity-level <1|2|3|4> [选项]
```

### 示例

```bash
bytedcli labelgpt dataset init --name demo_dataset --sensitivity-level 2 --space-id <SPACE_ID>
bytedcli labelgpt dataset init --name demo_dataset --sensitivity-level 2 --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset init --name demo_dataset --sensitivity-level 2 --space-id <SPACE_ID> -o ./out
```

### 参数说明

- `--name <DATASET_NAME>`：数据集名称，必填。
- `--sensitivity-level <1|2|3|4>`：敏感级别，所有站点必填且无默认值；1=L1 公开、2=L2 内部、3=L3 秘密、4=L4 机密。
- `--space-id <SPACE_ID>`：当前命令显式传入的目标 Space ID。

### 行为

- 当前登录用户自动成为 owner。
- 创建成功后直接返回数据集 ID，不需要轮询。

### 输出

`raw/json` 输出 `id`、`name`、`sensitivity_level` 和 `space_id`。

### 输出文件

- `-o <DIR>`：写入 `dataset_init_<id>.json`。

### 注意事项

- 必须在当前命令中显式传 `--space-id <SPACE_ID>`。
- 机器调用优先使用 `--format raw`。

## dataset update

局部更新已有数据集的元信息，不开放 Owner 修改。

### 用法

```bash
bytedcli labelgpt dataset update --id <DATASET_ID> [修改项] [选项]
```

### 示例

```bash
bytedcli labelgpt dataset update --id <DATASET_ID> --sensitivity-level 2 --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset update --id <DATASET_ID> --name renamed --tag train --remark note --space-id <SPACE_ID>
bytedcli labelgpt dataset update --id <DATASET_ID> --tag '' --remark '' --retention-seconds 0 --space-id <SPACE_ID> --format raw
```

### 参数说明

- `--id <DATASET_ID>`：数据集 ID，必填且必须为正整数。
- `--name <NAME>`：新名称；显式传空字符串非法。
- `--tag <TAG>`、`--remark <TEXT>`：新标签或备注；显式传空字符串表示清空。
- `--retention-seconds <SECONDS>`：非负保留秒数；`0` 表示永久保留。
- `--sensitivity-level <1|2|3|4>`：新敏感级别。
- 至少显式提供一个修改项；未提供的字段不会发送。

### 输出

`raw/json` 输出 `id`、`space_id`、`updated_fields` 和本次显式修改的字段。

## dataset list

分页搜索目标 Space 下的数据集。

### 用法

```bash
bytedcli labelgpt dataset list [选项]
```

### 示例

```bash
bytedcli labelgpt dataset list --name <KEYWORD> --space-id <SPACE_ID>
bytedcli labelgpt dataset list --name <KEYWORD> --space-id <SPACE_ID> --page-num 1 --page-size 30 --format raw
bytedcli labelgpt dataset list --owner-user-id <USER_ID> --tag <KEYWORD> --space-id <SPACE_ID> --format raw
bytedcli labelgpt dataset list --id <DATASET_ID> --space-id <SPACE_ID> --format raw
```

### 参数说明

- `--id <ID>`：按数据集 ID 过滤。可重复传，也可用逗号分隔。
- `--owner-user-id <USER_ID>`：按 owner user ID 过滤。可重复传，也可用逗号分隔。
- `--name <KEYWORD>`：按数据集名称模糊搜索。
- `--tag <KEYWORD>`：按标签模糊搜索。
- `--remark <KEYWORD>`：按备注模糊搜索。
- `--create-user-id <USER_ID>`：按创建人 user ID 精确过滤。
- `--create-time-start/--create-time-end <MS>`：创建时间范围，Unix 毫秒。
- `--archive-status <N>`：按归档状态过滤。
- `--page-num <N>`：页码，从 1 开始，默认 1。
- `--page-size <N>`：每页数量，默认 30。

### 输出

`raw/json` 输出 `datasets`、`total`、`page_num`、`page_size` 和 `space_id`。

数据集行包含 ID、名称、owner、标签、备注、敏感级别、创建/更新人和时间、数据量、归档状态、所属 Space、风险标签和 DOLA 权限。旧服务未返回敏感级别时，`sensitivity_level` 为空。

### 输出文件

- `-o <DIR>`：写入 `dataset_list_<timestamp>.json`。

### 注意事项

- 必须在当前命令中显式传 `--space-id <SPACE_ID>`。
- 机器调用优先使用 `--format raw`。

## dataset items

分页查询指定数据集下的数据条目。

### 用法

```bash
bytedcli labelgpt dataset items --id <DATASET_ID> [选项]
```

### 示例

```bash
bytedcli labelgpt dataset items --id <DATASET_ID> --space-id <SPACE_ID> --page-size 10 --format raw
bytedcli labelgpt dataset items --id <DATASET_ID> --space-id <SPACE_ID> --field prompt --field answer --format raw
bytedcli labelgpt dataset items --id <DATASET_ID> --space-id <SPACE_ID> --data-item-id <ITEM_ID> --format raw
bytedcli labelgpt dataset items --id <DATASET_ID> --space-id <SPACE_ID> --data-tag seed --executor-status 正常 --page-size 50
```

### 参数说明

- `--id <DATASET_ID>`：数据集 ID，必填。
- `--data-item-id <ID>`：按数据条目 ID 过滤。可重复传，也可用逗号分隔。
- `--header <NAME>`：表头名。可重复传，也可用逗号分隔。
- `--field <NAME>`：返回的数据字段。可重复传，也可用逗号分隔。
- `--executor-status <STATUS>`：按 Agent 执行状态过滤。仅接受 `正常`（工作流全部节点成功）
  或 `异常`（至少一个节点失败）两个值；传其他值（数字、英文、`未执行`、拼写错误等）会直接报错并
  非零退出。尚未运行的数据不会写入该状态，因此无法按「未执行」过滤。注意：`异常` 的条目通常仍有
  完整判定结果，`异常` 只表示存在失败节点，不代表整条数据不可用。
- `--process-id <ID>`：按数据处理 Process ID 过滤。
- `--source-type <TYPE>`、`--data-tag <TAG>`、`--create-user-id <USER_ID>`：可重复传或用逗号分隔。
- `--data-remark <TEXT>`：按数据备注过滤。
- `--create-time-start/--create-time-end <MS>`：数据创建时间范围，Unix 毫秒。
- `--page-num <N>`：页码，从 1 开始，默认 1。
- `--page-size <N>`：每页数量，默认 30。

### 行为

- 单次调用只返回一页数据，不自动翻页。

### 输出

`raw/json` 输出：

- `id`：本次查询的数据集 ID。
- `dataset`：包含 ID、名称、总行数、存储类型和可选 `sensitivity_level` 的数据集摘要。
- `items`：当前页数据条目；每项包含 `data_item_id` 和按字段名组织的 `values`。
- `header_name_list`、`header_meta_list`。
- `total`、`page_num`、`page_size`。

`pretty` 输出 `DataItemID` 和动态字段表格；动态列优先使用 `--field`，否则使用返回的表头，并限制列数避免过宽。

### 输出文件

- `-o <DIR>`：写入 `dataset_items_<timestamp>.json`。

### 注意事项

- 必须在当前命令中显式传 `--space-id <SPACE_ID>`。
- 数据集 ID 在 CLI 输出中统一为 `id`；数据条目 ID 使用 `data_item_id`。
- 机器调用优先使用 `--format raw`。

## Schema 查询索引

```bash
bytedcli labelgpt schema dataset init --format raw
bytedcli labelgpt schema dataset update --format raw
bytedcli labelgpt schema dataset list --format raw
bytedcli labelgpt schema dataset items --format raw
```
