# 币种 / Currency (`ref-currency`)

## Model Selection

“币种” and “货币代码” are distinct data objects. This command queries 币种, including its `code` field;
it does not query the separate 货币代码 model used by interest rates. That model has no independent CLI
query. Do not substitute `ref-currency list` for a request to list 货币代码 records. If the user only says
“currency codes” and the intended object is unclear, clarify whether they mean 币种 codes or 货币代码.

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Single-record `get` fields: `mdm_code`, `code`
- `batch-get` / `multi-get` fields: `mdm_code`, `code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted single-field `query` criteria: `mdm_code`, `code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-currency get --field code --value <currency-code>
bytedcli --json cis-master-data ref-currency query --criterion 'name=<currency-name>'
bytedcli --json cis-master-data ref-currency search --keyword <currency-name-fragment>
bytedcli --json cis-master-data ref-currency list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
