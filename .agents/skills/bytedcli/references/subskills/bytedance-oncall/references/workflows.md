# Oncall 常见多步流程

本文仅记录命令之间的衔接关系；执行前仍需读取对应功能说明。示例中的 `<tenant-id>` 和 `<flow-id>` 必须替换为用户提供或上一步返回的真实 ID。

## 先定位租户，再执行租户查询

```bash
bytedcli oncall tenant search --keyword "<tenant-keyword>" --format table
```

拿到唯一的 `<tenant-id>` 后，按用户意图选择下一步，不要默认全部执行：

```bash
TENANT_ID="<tenant-id>"

bytedcli oncall flow list --tenant-id "$TENANT_ID" --format table
bytedcli oncall question-type list --tenant-id "$TENANT_ID" --regions-only --format table
bytedcli oncall document search --tenant-id "$TENANT_ID" --keyword "<search-text>" --format table
```

查值班人时，如果区域未知，先通过 `question-type list --regions-only` 取得可用值，再执行：

```bash
bytedcli oncall duty-user get \
  --tenant-id "$TENANT_ID" \
  --region "<region>" \
  --format table
```

租户搜索返回多个候选时，先请用户确认目标租户。

## 先定位工单，再查关联信息

没有工单 ID 时，根据已知条件使用 `flow list`，例如：

```bash
bytedcli oncall flow list --mine --range 30d --format table
bytedcli oncall flow list --tenant-id "<tenant-id>" --solved=false --format table
```

从唯一候选中取得 `<flow-id>` 后，只执行用户需要的后续查询：

```bash
FLOW_ID="<flow-id>"

bytedcli oncall flow get --id "$FLOW_ID" --format table
bytedcli oncall chat get --flow-id "$FLOW_ID" --format text
bytedcli oncall agent log-list --flow-id "$FLOW_ID" --format table
bytedcli oncall agent summary-get --flow-id "$FLOW_ID" --format table
```

候选工单不唯一时，先请用户确认；不要使用示例 ID 或自行猜测。

## 查当前用户的工单

```bash
# 当前用户发起的工单
bytedcli oncall flow list --mine --range 30d --format table

# 分配给当前用户的未解决人工 Oncall
bytedcli oncall flow list \
  --assigned-to-me \
  --stage launch_oncall \
  --solved=false \
  --format table
```
