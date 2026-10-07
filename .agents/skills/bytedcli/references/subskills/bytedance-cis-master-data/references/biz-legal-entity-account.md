# 主体账户 / Legal-Entity Account (`biz-legal-entity-account`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- Unique fields: `mdm_code`, `account_id`, `ap_info_id`
- Fixed `search` field: `account_name`
- Accepted single-field `query` criteria: `mdm_code`, `account_id`, `ap_info_id`, `bank_number`

## Examples

```bash
bytedcli --json cis-master-data biz-legal-entity-account search --keyword <account-name>
bytedcli --json cis-master-data biz-legal-entity-account get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-legal-entity-account query \
  --criterion 'bank_number=<bank-number>' --page-size 32
```

Use `search` for an account name. Prefer `mdm_code` for stable exact lookup; use `account_id` or
`ap_info_id` only when the caller already has that identifier. Use `query` for an exact indexed bank
number or lookup field.
