# Bamboo Hive rule write payloads

`hive-rule create` and `hive-rule update` accept a normalized camelCase JSON object through exactly one of `--payload <json>` or `--payload-file <path>`. File input is recommended for SQL and structured fields.

Both commands are dry-run by default. Review `data.request.body`, then repeat the same command with `--yes` only after explicit confirmation.

## Create template

```json
{
  "uniqueRuleName": "demo-hive-rule",
  "appId": 123,
  "rulesSql": "SELECT 1 AS demo_value",
  "alarmChannel": "lark-group",
  "larkGroupId": "demo-lark-group",
  "ownerIds": [10001],
  "alarmLevel": "notice",
  "expectedValueType": "empty-result",
  "category": "custom",
  "businessLine": "demo-business",
  "schedulingType": "periodic",
  "runFrequency": "daily",
  "crontabExpression": "0 1 * * *",
  "hiveYarn": {
    "queueName": "root.demo_bamboo_queue",
    "clusterName": "demo-cluster"
  },
  "creatorId": 10001,
  "sceneId": "demo-scene",
  "isMqExceptionalDataDelivered": false
}
```

Unconditionally required create fields are `uniqueRuleName`, `appId`, `rulesSql`, `alarmChannel`, `ownerIds`, `alarmLevel`, `expectedValueType`, `category`, `businessLine`, `schedulingType`, `runFrequency`, `crontabExpression`, `hiveYarn`, `creatorId`, `sceneId`, and `isMqExceptionalDataDelivered`. The selected alarm route additionally requires exactly one target: `larkGroupId` for `lark-group`, or `projectName` for `alarm-project`. Optional fields are `dutyPlan`, `spaceId`, `columns`, `countThreshold`, `isAddStandbyDutyPerson`, `isPhoneCall`, `isRepeatAlert`, `comment`, `repeatConfig`, `isEnabled`, `isLlmGenerated`, `partitionInfo`, `llmSource`, `label`, and `byteTree`. `spaceId` must be a positive integer; a decimal string is accepted and normalized to a number.

## Update template

The update endpoint expects a complete rule definition rather than a partial patch. The target ID is supplied separately with `--id` and overrides no JSON field because `id` is not accepted inside the normalized payload.

```json
{
  "uniqueRuleName": "demo-hive-rule",
  "rulesSql": "SELECT 1 AS demo_value",
  "alarmChannel": "lark-group",
  "larkGroupId": "demo-lark-group",
  "ownerIds": [10001],
  "alarmLevel": "notice",
  "expectedValueType": "empty-result",
  "category": "custom",
  "businessLine": "demo-business",
  "schedulingType": "periodic",
  "runFrequency": "daily",
  "crontabExpression": "0 1 * * *",
  "hiveYarn": {
    "queueName": "root.demo_bamboo_queue",
    "clusterName": "demo-cluster"
  },
  "creatorId": 10001,
  "sceneId": "demo-scene",
  "isMqExceptionalDataDelivered": false
}
```

Optional update fields are `dutyPlan`, `columns`, `countThreshold`, `isAddStandbyDutyPerson`, `isPhoneCall`, `isRepeatAlert`, `comment`, `repeatConfig`, `partitionInfo`, and `label`.

## Conditional fields

- Create supports `alarmChannel: "lark-group"` with required `larkGroupId`, or `alarmChannel: "alarm-project"` with required `projectName`; do not send the field for the other route, and keep multiple group IDs in one comma-separated string. Update supports only `"lark-group"` and requires `larkGroupId` because the open edit API does not support alarm-project routing.
- `alarmLevel` accepts `"critical"`, `"warning"`, or `"notice"`.
- `isPhoneCall: true` is valid only with `alarmLevel: "critical"`; `isAddStandbyDutyPerson: true` requires `dutyPlan`.
- `expectedValueType: "empty-result"` accepts neither `columns` nor `countThreshold`.
- `expectedValueType: "scalar"` requires a non-empty `columns` array and accepts no `countThreshold`.
- `expectedValueType: "row-count-threshold"` requires `countThreshold` from `0` through `1000000` and accepts no `columns`.
- `schedulingType` accepts `"periodic"` or `"manual"` for create. Update accepts only `"periodic"` because the open edit API only supports periodic scheduling.
- Create `runFrequency` accepts `"hourly"`, `"daily"`, `"monthly"`, or `"minutely"`. Update accepts only `"hourly"`, `"daily"`, or `"monthly"`. `crontabExpression` must be a valid five-field numeric Cron expression consistent with the selected frequency: use multiple expanded minute values with otherwise unrestricted fields for minutely (for example `*/5 * * * *` or `0,30 * * * *`), one minute across all hours for hourly (`0 * * * *`), one minute and one hour for daily (`0 1 * * *`), or one minute, hour, and day-of-month for monthly (`0 1 1 * *`). Lists, ranges, and steps are accepted only when their expanded values still match that frequency shape.

For `expectedValueType: "scalar"`, each `columns` item uses:

```json
{
  "columnName": "demo_value",
  "method": "eq",
  "expectedValue": "1"
}
```

`method` is `"gt"` (`>`), `"lt"` (`<`), `"gte"` (`>=`), `"lte"` (`<=`), `"eq"` (`==`), or `"neq"` (`!=`).

`category` accepts `"row-count"`, `"duplicate-value"`, `"exception-value"`, `"null-value"`, `"unknown-enum"`, `"field-value"`, `"accuracy"`, `"fluctuation"`, `"delay"`, `"comparison"`, or `"custom"`. Optional `label` accepts `"loss-risk"`, `"config-risk"`, or `null`; optional `llmSource` accepts `"bamboo"`, `"algorithm-batch"`, `"ai-reconciliation"`, `"business-finance-reconciliation"`, `"copy"`, `"ecommerce-eops"`, `"page-selection"`, `"event-tracking"`, or `"sre-reconciliation"`.

Use these semantic strings in input payloads and list filters. Numeric Bamboo enum codes are not accepted as CLI input. They appear in generated dry-run requests and in Hive-rule detail diagnostic fields suffixed with `Code`; the corresponding unsuffixed detail fields use the same semantic strings as write payloads. Upstream `是`/`否` values are exposed as booleans, with the original text preserved only in fields suffixed with `Text`.

Each `partitionInfo` item uses `partitionKey`, `partitionValue`, `qualifiedName`, and `tableName`. Unknown payload keys are rejected so a misspelled field cannot be silently submitted.

## Execution

```bash
# Preview only
bytedcli --json bamboo hive-rule create --payload-file ./demo-bamboo-rule-create.json
bytedcli --json bamboo hive-rule update --id 12345 --payload-file ./demo-bamboo-rule-update.json

# Submit only after reviewing the preview and receiving explicit confirmation
bytedcli --json bamboo hive-rule create --payload-file ./demo-bamboo-rule-create.json --yes
bytedcli --json bamboo hive-rule update --id 12345 --payload-file ./demo-bamboo-rule-update.json --yes
```
