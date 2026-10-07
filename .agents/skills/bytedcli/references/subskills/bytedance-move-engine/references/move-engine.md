# Move Engine command reference

## Project

```bash
bytedcli --site cn move-engine project list [--src-region sample-region] [--dst-region sample-region] [--src-vdc sample-vdc] [--dst-vdc sample-vdc] [--keyword sample-project] [--move-type sample-type] [--label sample-key=sample-value]
bytedcli --site cn move-engine project get --project-id 1
bytedcli --site cn move-engine project search --psm example.service.api [--product-type tce]
```

## Item

```bash
bytedcli --site cn move-engine item list --project-id 1 --page 1 --page-size 20
bytedcli --site cn move-engine item list --project-id 1 --after-id sample-cursor --product-type tce --status sample-status
bytedcli --site cn move-engine item list --project-id 1 --filters-json '[{"key":"labels.sample-key","values":["sample-value"]}]'
bytedcli --site cn move-engine item projection list --project-id 1 --product-type tce --pipeline-id sample-pipeline-id --field deploy_status
bytedcli --json --site cn move-engine item deployment get --project-id 1 --product-type tce --job-id 2 --psm example.service.api
```

`item list` 常用过滤参数均可重复或使用逗号分隔：`--psm`、`--product-type`、`--item-type`、`--owner`、`--status`、`--migrate-tag`、`--pipeline-id`。`--label` 使用 `key=value`。

高级过滤器是 `FieldFilter[]` JSON，每项至少包含 `key`，并通过 `values`、`ne_values` 或 `range_value` 表达条件。支持固定字段以及 `labels.<key>`、`upgrade_item_meego.<key>` 动态字段；重复或未知 key 会在请求前报错。

`item projection list --field` 可重复传入，只接受：`deploy_status`、`is_consumer`、`consumer_filter_status`、`consumer_migration_mark`、`consumer_config`。

`item deployment get` 映射只读接口 `/api/item/get/byteladder/meta`。四个参数均必填；文本模式展示迁移状态、源/目标 region、部署时间和 BPM 信息，JSON 模式在 `deployment` 中返回不含凭据的安全字段投影。

## Consumer

```bash
bytedcli --site cn move-engine consumer group list --project-id 1 --product-type tce --psm example.consumer.service
bytedcli --site cn move-engine consumer group list --project-id 1 --product-type faas --psm example.function.service --no-current-filter-config
bytedcli --site i18n-tt move-engine consumer mq-cluster list --region sample-region
```

默认会查询当前消费组过滤配置；只需要消费组列表时加 `--no-current-filter-config`。

## Pipeline

```bash
bytedcli --site cn move-engine pipeline get --project-id 1 --pipeline-id sample-pipeline-id
bytedcli --site cn move-engine pipeline list --project-id 1
bytedcli --site cn move-engine pipeline search --project-id 1 --keyword sample-pipeline
bytedcli --site cn move-engine pipeline search --project-id 1 --psm example.service.api --product-type tce
```

`pipeline search` 要求提供 `--keyword`，或同时提供 `--psm` 与 `--product-type`。pipeline ID 按字符串处理。
