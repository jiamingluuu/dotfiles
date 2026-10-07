# 楼宇 / Building (`md-building`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`, `building_code`
- `batch-get` fields: `mdm_code`, `building_code`
- `multi-get` fields: `mdm_code`, `building_code`
- Accepted single-field `query` criteria: `mdm_code`, `workplace_mdm_code`, `building_code`, `number`
- Fixed `search` fields: `number`

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-building get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-building batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-building multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-building query --criterion 'number=demo-value'
bytedcli --json cis-master-data md-building search --keyword demo-fragment
bytedcli --json cis-master-data md-building list --page-size 16
```

Prefer `mdm_code` when one stable record is required. Historical rows can share `building_code`;
`get` returns one match and does not establish uniqueness. Use `query` or `multi-get` to preserve
all matches. `workplace_mdm_code` locates buildings under a known workplace through `query`.
`number` supports exact `query` and fuzzy `search`, not `get`, `batch-get`, or `multi-get`.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
