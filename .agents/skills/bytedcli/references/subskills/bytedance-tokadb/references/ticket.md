# TokaDB 变更工单

TokaDB 工单能力都在原 `bytedance-tokadb` skill 内维护，不拆独立 skill。当前只支持两类工单：**创建 CF**（`tokadb ticket cf create`）与**禁用表**（`tokadb ticket table disable`）。

## 支持范围与红线

- 不要提交任何其他类型的工单（建表、删表、启用表、quota 调整等），也不要绕过这两条入口。
- 不要绕过工单直接调用底层 `tables/create_column_family`、`tables/disable` 或 GM 接口。
- 不要手写 curl、复制浏览器 Cookie/JWT，或让用户提供 token。
- 不要在字段未收集完整时提交；缺任一必填字段必须继续询问。
- 不要猜测 `attributes` 或 `storage_attributes`。用户没有高级属性时，也必须明确确认它们为空数组后再提交。
- 不要把 `max_num_version` 用在工单入参里；创建 CF 工单字段是 `max_version`。

## 前置条件

- 需要可用的 ByteCloud 认证；提工单前先执行 `bytedcli auth login`。
- 工单当前只在 CN 生产（`--region cn`，默认）与独立 CN 测试后端（`--region cn_test`）验证过；`cn_test` 不属于默认 `--all-regions` / report，需要显式传入。其余 region 未接入工单提交，不要用于提单。
- 提交人需要目标表的更新权限；创建 CF 工单后端会校验 service/table 存在、表处于 RUNNING、CF 不存在、调用人有 table update 权限。禁用表工单后端会校验目标表存在且调用人有 table update 权限。

## 创建 CF 工单字段清单

后端入口：`POST /api/v1/bytetable/tickets/create_column_family`。

CLI 命令：`bytedcli tokadb ticket cf create`。

必须收集并确认：

| 后端字段                                       | CLI 参数                                   | 说明                                                                        |
| ---------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------- |
| `content.bytetable_cluster`                    | `--cluster <cluster>`                      | TokaDB cluster / ByteTable service 名称                                     |
| `content.database`                             | `--database <database>`                    | 已存在表所在 database                                                       |
| `content.table_name`                           | `--table-name <table>`                     | 已存在表名                                                                  |
| `content.column_families[].name`               | `--cf <name:max_version>` 的 `name`        | 要新建的 CF 名称；可重复传多个 CF                                           |
| `content.column_families[].max_version`        | `--cf <name:max_version>` 的 `max_version` | 正整数；字段名是 `max_version`                                              |
| `content.column_families[].attributes`         | `--cf-attr <cf:key=value>`                 | 可重复；生成 `[key, value]` 数组。没有时必须确认为空数组                    |
| `content.column_families[].storage_attributes` | `--cf-storage-attr <cf:key=value>`         | 可重复；生成 `{ "name": key, "value": value }` 数组。没有时必须确认为空数组 |

CF 名称不能包含 `:`、`=` 或空白字符（`--cf` / `--cf-attr` / `--cf-storage-attr` 用 `:` 与 `=` 作分隔符）。`attributes` 后端校验为 list of `[string, string]`。`storage_attributes` 后续执行节点按 `{name,value}` 读取，因此 CLI 只生成这种形状。

## 创建 CF 标准流程

1. 收集字段：region、cluster、database、table、每个 CF 的 name/max_version、每个 CF 的 attributes、storage_attributes。
2. 如果用户没有提供 attributes 或 storage_attributes，明确询问并确认“为空数组”。
3. 先 dry-run，展示完整 payload，不提交：

```bash
bytedcli tokadb ticket cf create \
  --region cn \
  --cluster demo-cluster \
  --database demo_db \
  --table-name demo_table \
  --cf cf1:1 \
  --dry-run
```

CN 测试环境示例：

```bash
bytedcli tokadb ticket cf create \
  --region cn_test \
  --cluster demo-cluster \
  --database demo_db \
  --table-name demo_table \
  --cf cf1:1 \
  --dry-run
```

4. 用户确认 dry-run payload 后，原命令加 `--yes` 提交：

```bash
bytedcli tokadb ticket cf create \
  --region cn \
  --cluster demo-cluster \
  --database demo_db \
  --table-name demo_table \
  --cf cf1:1 \
  --yes
```

带高级属性示例：

```bash
bytedcli tokadb ticket cf create \
  --region cn \
  --cluster demo-cluster \
  --database demo_db \
  --table-name demo_table \
  --cf cf1:3 \
  --cf-attr cf1:encoding=plain \
  --cf-storage-attr cf1:medium=ssd \
  --dry-run
```

## 禁用表工单字段清单

后端入口：`POST /api/v1/bytetable/tickets/disable_table`。

CLI 命令：`bytedcli tokadb ticket table disable`。

禁用表工单只收下面三个必填字段，后端 serializer 不接受任何其他字段（没有 reason / 备注等）：

| 后端字段                    | CLI 参数                | 说明                            |
| --------------------------- | ----------------------- | ------------------------------- |
| `content.bytetable_cluster` | `--cluster <cluster>`   | TokaDB cluster / ByteTable 服务 |
| `content.database`          | `--database <database>` | 目标表所在 database             |
| `content.table_name`        | `--table-name <table>`  | 要禁用的已存在表名              |

禁用表流程同样默认 dry-run，确认 payload 后再加 `--yes` 提交：

```bash
bytedcli tokadb ticket table disable \
  --region cn \
  --cluster demo-cluster \
  --database demo_db \
  --table-name demo_table \
  --dry-run
```

```bash
bytedcli tokadb ticket table disable \
  --region cn \
  --cluster demo-cluster \
  --database demo_db \
  --table-name demo_table \
  --yes
```

## 输出与后续处理

- `--json` 要放在 `tokadb` 前面：`bytedcli --json tokadb ticket cf create ...`。
- dry-run 输出包含 `dry_run: true`、`endpoint`、`query` 和完整 `request`。
- `--yes` 成功后输出本地 ticket 字段，如 `id`、`workflow`、`flow_record_id`、`status`、`applicant`（`id` / `flow_record_id` 统一为字符串）。
- 需要跟进 BPM 流转时，用 `bytedance-bpm` skill 的 `bpm ticket get/logs/op-keys/update-status/comment` 命令处理 `flow_record_id`。

## Backend Evidence

- 工单 action：`apps/bytetable/ticket/views.py` 中 `create_column_family -> CreateColumnFamilyTicketSerializer`、`disable_table -> DisableTableTicketSerializer`。
- 工单 content serializer：`apps/bytetable/ticket/serializers.py` 中 `CreateColumnFamilyTicketSerializer.content = CreateColumnFamilySerializer()`、`DisableTableTicketSerializer.content = DisableTableSerializer()`（workflow `bytetable_disable_table`）。
- 字段定义：`apps/bytetable/table/serializers.py` 中 `CreateColumnFamilySerializer` / `ColumnFamilySerializer`，以及 `DisableTableSerializer(OperateTableSerializer)`（只含 `bytetable_cluster` / `database` / `table_name`）。
- 权限：`apps/bytetable/ticket/permissions.py` 中 `disable_table` 使用 `TicketHasTableUpdatePermission`。
- BPM 提交：`apps/common/ticket/views.py` 中 `_create_ticket_start_flow()` 会把 `ticket_id` 注入 content，并调用 BPM `start_flow`。
