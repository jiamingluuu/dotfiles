# 收单地址 / Acquiring address (`biz-acquiring-address`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`
- `batch-get` fields: `mdm_code`
- `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `office_address`, `acquiring_address`
- Fixed `search` fields: `office_address`, `acquiring_address`

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data biz-acquiring-address get --field mdm_code --value demo-code
bytedcli --json cis-master-data biz-acquiring-address batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data biz-acquiring-address multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data biz-acquiring-address query --criterion 'acquiring_address=demo-value'
bytedcli --json cis-master-data biz-acquiring-address search --keyword demo-fragment
bytedcli --json cis-master-data biz-acquiring-address list --page-size 16
```

Use `query` for one complete office or acquiring address and `search` for a fragment.
`office_address` and `acquiring_address` are not `get`, `batch-get`, or `multi-get` fields.
`wp_code` is not a supported query criterion. Do not substitute the workplace model for this model.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
