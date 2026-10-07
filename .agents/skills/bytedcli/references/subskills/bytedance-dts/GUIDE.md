---
name: bytedance-dts
description: "Query native ByteDTS task details and complete source-to-destination table mappings through bytedcli. Use when the user mentions a ByteDTS task ID, a /bytedts/datasync/detail URL, DescribeTaskInfo, ByteDTS task status, or asks which tables a ByteDTS task synchronizes. Do not use this for TT-DTS / DES-MQ channel IDs or Dorado DTS metadata."
---

# bytedcli ByteDTS

Use this skill for native ByteDTS data synchronization tasks. It is distinct from:

- `bytedcli tt-dts`: TT-DTS / DES-MQ channels
- `bytedcli dorado dts`: Dorado DTS metadata and task-draft helpers

## Prerequisites

- The command surface is read-only and supports `cn`, `i18n-tt`, `i18n-bd`, `us-ttp`, and `eu-ttp`.
- Authenticate first with `bytedcli --site <site> auth login`.
- Put global `--site` and `--json` options before `dts`.

## Commands

```bash
# Normalized task detail with a table-mapping summary
bytedcli --site cn dts task get --id 123456789

# Complete source-table to destination-table mappings
bytedcli --site cn dts task get --id 123456789 --format tables

# Stable machine-readable output
bytedcli --site cn --json dts task get --id 123456789 --region China-North --format tables

# i18n-tt and i18n-bd use site-specific default VRegions
bytedcli --site i18n-tt --json dts task get --id 123456789 --format tables
bytedcli --site i18n-bd --json dts task get --id 123456789 --format tables
bytedcli --site us-ttp --json dts task get --id 123456789 --format tables
bytedcli --site eu-ttp --json dts task get --id 123456789 --format tables

# SINF control planes are selected by the local region override
bytedcli --site cn --json dts task get --id 123456789 --region sinf
bytedcli --site i18n-bd --json dts task get --id 123456789 --region sinfi18n
```

## Agent guidance

- Pass task IDs through `--id`; both positive safe integers and 32-character hexadecimal ByteDTS IDs are supported.
- Region resolution follows local `--region`, global `--vregion`, then the `--site` default: `cn` -> `China-North`, `i18n-tt` -> `Singapore-Central`, `i18n-bd` -> `Asia-SouthEastBD`, `us-ttp` -> `US-TTP`, and `eu-ttp` -> `EU-TTP2`.
- The special local regions `sinf` and `sinfi18n` select the dedicated SINF ByteDTS routes and use the matching `cn` and `i18n-bd` user identities respectively.
- The `sinf` route automatically sends `x-bcgw-vregion: cn-beijing`; callers should not inject this protected routing header manually.
- Use `task get --format tables` when the user asks which tables are synchronized. It returns `source_database`, `destination_database`, `mapping_count`, `explicit_table_count`, `includes_wildcard`, and every mapping. A `* -> *` row means the task covers all tables rather than one literal table named `*`.
- Use the default `task get --format detail` view for task state, source/destination metadata, and a table-mapping summary. JSON detail output also includes every mapping; in text mode, use `--format tables` to print the complete source-to-destination table map.
- The API projection deliberately excludes raw settings and raw runtime-state blobs.
- If a task belongs to TT-DTS / DES-MQ rather than ByteDTS, route to the `bytedance-tt-dts` skill.
