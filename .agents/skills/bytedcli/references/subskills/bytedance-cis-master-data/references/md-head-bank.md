# 银行总行 / Head Bank (`md-head-bank`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `bank_code`
- Accepted single-field `query` criteria: `mdm_code`, `bank_code`, `bank_name`
- Fixed `search` field: `bank_name`

## Examples

```bash
bytedcli --json cis-master-data md-head-bank get --field bank_code --value <bank-code>
bytedcli --json cis-master-data md-head-bank query --criterion 'bank_code=<bank-code>'
bytedcli --json cis-master-data md-head-bank search --keyword <bank-name-fragment>
bytedcli --json cis-master-data md-head-bank list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
