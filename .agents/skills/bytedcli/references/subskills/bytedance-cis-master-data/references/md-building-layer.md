# 楼层 / Building floor (`md-building-layer`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get` fields: `mdm_code`
- `batch-get` fields: `mdm_code`
- `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `building_mdm_code`, `layer_code`
- `search` is not available.

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-building-layer get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-building-layer batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-building-layer multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-building-layer query --criterion 'layer_code=demo-value'
bytedcli --json cis-master-data md-building-layer list --page-size 16
```

Use `building_mdm_code` with `query` for floors of a known building. `layer_code` supports
`query` only and can match multiple records. Do not construct `search` or use `layer_code` as a
`get`, `batch-get`, or `multi-get` field. Ask for a documented criterion when only a name fragment
is provided; do not automatically start a broad list scan.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
