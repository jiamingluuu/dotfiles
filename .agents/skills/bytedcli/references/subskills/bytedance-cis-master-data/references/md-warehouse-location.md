# IT库房位置 / IT warehouse location (`md-warehouse-location`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`
- `batch-get` fields: `mdm_code`
- `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `name`, `address`
- Fixed `search` fields: `name`, `address`

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-warehouse-location get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-warehouse-location batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-warehouse-location multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-warehouse-location query --criterion 'address=demo-value'
bytedcli --json cis-master-data md-warehouse-location search --keyword demo-fragment
bytedcli --json cis-master-data md-warehouse-location list --page-size 16
```

Use `query` for one complete name or address and `search` for a fragment. `name` and `address`
are not `get`, `batch-get`, or `multi-get` fields. Geographic fields such as `city_mdm_code`
are not supported query criteria. This model describes IT warehouse locations, not stock quantities.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
