# 职场 / Workplace (`md-workplace`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`
- `batch-get` fields: `mdm_code`, `name`
- `multi-get` fields: `mdm_code`, `name`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `name`, `address`
- Fixed `search` fields: `name`, `address`

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-workplace get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-workplace batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-workplace multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-workplace query --criterion 'address=demo-value'
bytedcli --json cis-master-data md-workplace search --keyword demo-fragment
bytedcli --json cis-master-data md-workplace list --page-size 16
```

`name` is multilingual. `get --field name` is not supported. In `batch-get`, `name` is valid
only when every repeated criterion uses `name`; do not mix `name` with `mdm_code` in one batch.
Use `multi-get --field name` for several names, or a single-field `query` for one exact name.
When the user requests independent `name` and `mdm_code` lookups in one batch, explain the batch restriction
and provide separate exact `query --criterion 'name=<name>'` and `get --field mdm_code --value <code>`
commands directly. Preserve both supplied values; do not turn independent lookups into an AND query.
Name lookups may return multiple rows and do not guarantee the input-name order. `code` supports
`query` only. `address` supports `query` and `search`, not exact-lookup commands.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
