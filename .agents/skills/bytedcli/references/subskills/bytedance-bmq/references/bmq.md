# BMQ

```bash
# Topic 列表
bytedcli bmq topic list --vregion "US-BOE" --page 1 --page-size 20
bytedcli bmq topic list --vregion "Singapore-Central" --search "demo" --all

# Topic 详情
bytedcli bmq topic get --topic-id 12345 --vregion "US-BOE"

# Topic 官方流量监控链接（BMQ 平台同款 Grafana 监控 URL）
bytedcli --site us-ttp bmq topic metrics get --search "demo-topic"
bytedcli --site us-ttp bmq topic metrics get --topic-id 12345 --type iframe

# Cluster 列表
bytedcli bmq cluster list --vregion "US-BOE" --all
bytedcli bmq cluster list --vregion "Singapore-Central" --search "public"

# Consumer Group 列表
bytedcli bmq consumer list --vregion "US-BOE" --page 1 --page-size 20
bytedcli bmq consumer list --vregion "Singapore-Central" --search "demo-consumer" --all

# Mirror 列表
bytedcli bmq mirror list --vregion "Singapore-Central" --status RUNNING --all
bytedcli bmq mirror list --vregion "Singapore-Central" --search "topic_name" --page-size 10

# 多站点（TikTok ROW）
bytedcli --site i18n-tt bmq topic list --vregion "Singapore-Central" --all

# TTP 站点
bytedcli --site us-ttp bmq topic list
bytedcli --site eu-ttp bmq topic list --vregion eu-ttp2
```

## Mirror search and hash strategy

`bmq mirror list --search <topic>` filters by **target topic** in the selected
`--vregion` (the mirror's target region). `--all` includes mirrors not owned by you;
`--page` and `--page-size` select one page, not an automatic full scan.

JSON mirror records include `partitionAlign` and `kafkaHashPolicy`. Text output
shows `Partition Align` and `Kafka Hash Policy`. These are separate upstream
fields: `false` is preserved, missing/null values are JSON `null` (text `-`), and
policy strings such as `PARTITION_ALIGN` or `KAFKA_DEFAULT` are returned unchanged.
Do not infer a policy from partition counts or substitute one field for the other.


## Topic creation orders

`bmq topic create` submits a ByteCloud approval order. Select the control plane with global `--site` and the target virtual region with `--vregion`. Supply `--workflow-config-id` from that site's current ByteCloud BMQ console CreateTopic workflow; IDs are not inferred from region aliases, reused across sites or taken from a standalone BMQ OpenAPI endpoint. The example ID is a placeholder. Creation supports `cn`, `boe`, `i18n-bd` (alias `i18n`), `i18n-tt`, `us-ttp` and `eu-ttp`; other global profiles are rejected before authentication.

```bash
bytedcli --site cn bmq topic create \
  --vregion China-North --cluster-name demo-cluster --topic-name demo-topic \
  --owner demo-owner --service-tree '|Demo|Messaging' \
  --workflow-config-id 12345 --message-qps 100 --message-size-kb 64 \
  --partition-num 3 --replica-num 2 \
  --read-psm example.app.reader --write-psm example.app.writer --dry-run
```

Required inputs: virtual region, cluster name, topic name, owner, workflow ID, message QPS, message size in KB and partition count. All numeric options accept only positive safe integers. A 64 MiB message is `--message-size-kb 65536`; per-partition production flow uses `--partition-max-flow-kb` in KB/s. Retention accepts either `--retention-hours` or `--retention-days`, not both.

Defaults: replicas 2, security level L3, topic usage `others`, retention size 256 GB, maximum consumers 20, lane topic false and user personal information false. Override the latter fields with `--retention-size-gb`, `--max-consumer-num`, `--create-lane` and `--contain-user-personal-info`; `--allowed-dc-list` accepts comma-separated data centers. Use `--member` for an additional owner, `--psm` for the primary service, and repeatable/comma-separated `--read-psm` / `--write-psm` for service permissions. Security level accepts L1-L4 or P0-P3; data sensitivity accepts L1-L4, and priority accepts P0-P3.

`--extra-json` appends JSON form fields that have no dedicated mapping. It rejects overrides of managed fields, including identity, region, cluster, topic, workflow ID, permissions, security and retention settings. Use dedicated options for those fields.

Without `--yes`, the command performs an offline preview: no authentication, preflight or order submission. Text and JSON output both contain the complete request and selected endpoints. After checking the preview, repeat with the same fields and `--yes`; `--dry-run --yes` still previews. `--skip-check` skips only the permission preflight and retains local validation and normal approval. Missing or unrecognized preflight decisions stop submission; `preflight_skipped` is true whenever the preview or `--skip-check` skips that call.

A successful submission reports `status: submitted`, the order ID/URL and `topic_verified: false`. Track that order through approval, then query the exact cluster/topic on the same site and region:

```bash
bytedcli --site cn bmq topic list --vregion China-North --search demo-topic --all
bytedcli --site cn bmq topic get --vregion China-North --topic-id 12345
```

Verify the returned cluster, topic identity and resource status before use. An accepted order is not evidence of an effective Topic. If the submission response cannot identify the order, the command returns `BMQ_CREATE_RESULT_UNCONFIRMED`; inspect existing orders before retrying to avoid duplicates. The CLI does not automatically retry the submission request.
