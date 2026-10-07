# 时区 / Time Zone (`ref-time-zone`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `time_zone_id`
- Accepted single-field `query` criteria: `mdm_code`, `time_zone_id`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-time-zone get \
  --field time_zone_id --value <time-zone-id>
bytedcli --json cis-master-data ref-time-zone query --criterion 'time_zone_id=<time-zone-id>'
bytedcli --json cis-master-data ref-time-zone search --keyword <time-zone-name-fragment>
bytedcli --json cis-master-data ref-time-zone list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
