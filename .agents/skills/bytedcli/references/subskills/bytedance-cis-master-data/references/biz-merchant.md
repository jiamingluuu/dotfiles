# 商户号 / Merchant number (`biz-merchant`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get` fields: `mdm_code`, `merchant_no`
- `batch-get` fields: `mdm_code`, `merchant_no`
- `multi-get` fields: `mdm_code`, `merchant_no`
- Accepted single-field `query` criteria: `mdm_code`, `merchant_no`
- `search` is not available.

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data biz-merchant get --field mdm_code --value demo-code
bytedcli --json cis-master-data biz-merchant batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data biz-merchant multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data biz-merchant query --criterion 'merchant_no=demo-value'
bytedcli --json cis-master-data biz-merchant list --page-size 16
```

Use `merchant_no` for a known merchant number, or `mdm_code` for its master-data record.
`merchant_name` is not a supported query criterion and this model does not expose `search`.
Ask for a documented exact value when only a name fragment is provided; do not automatically
start a broad list scan. This model does not provide transactions or account balances.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
