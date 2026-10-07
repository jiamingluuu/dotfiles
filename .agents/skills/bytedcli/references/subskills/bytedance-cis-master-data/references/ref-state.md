# 省/州 / State/Province (`ref-state`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Single-record `get` field: `mdm_code`
- `batch-get` / `multi-get` fields: `mdm_code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted single-field `query` criteria: `mdm_code`, `country_mdm_code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-state get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data ref-state query \
  --criterion 'country_mdm_code=<country-master-data-code>'
bytedcli --json cis-master-data ref-state search --keyword <state-name-fragment>
bytedcli --json cis-master-data ref-state list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
