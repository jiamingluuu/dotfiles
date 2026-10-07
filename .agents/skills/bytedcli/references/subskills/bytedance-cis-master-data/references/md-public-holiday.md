# 公共假期 / Public Holiday (`md-public-holiday`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `holiday_item_id`
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `holiday_item_id`
  - `holiday_year`
  - `holiday_year,holiday_mdm_code`
  - `holiday_item_name`
- Fixed `search` field: `holiday_item_name`

## Examples

```bash
bytedcli --json cis-master-data md-public-holiday get \
  --field holiday_item_id --value <holiday-item-id>
bytedcli --json cis-master-data md-public-holiday query \
  --criterion 'holiday_year=<holiday-year>' \
  --criterion 'holiday_mdm_code=<holiday-master-data-code>'
bytedcli --json cis-master-data md-public-holiday search --keyword <holiday-name-fragment>
bytedcli --json cis-master-data md-public-holiday list --page-size <bounded-page-size>
```

Use exactly one documented query field set. Use `list` only after exact, bounded, and fuzzy lookup.
