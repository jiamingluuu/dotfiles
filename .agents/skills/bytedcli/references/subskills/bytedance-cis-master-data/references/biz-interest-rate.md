# 利率 / Interest Rate (`biz-interest-rate`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- Exact lookup field: `mdm_code`
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `identifier`
  - `identifier,price_type`
  - `identifier,price_type,value_ts`
- `search` and `list` are not exposed for this model.

## Interpreting Reference Codes

A returned `ir_mdm_code` refers to the separate 货币代码 data object, not 币种 (`ref-currency`).
That object has no independent CLI query. Keep the returned code; do not use it as a currency lookup
or guess a name when no reference summary is returned. Use `identifier` only as documented below.

## Examples

```bash
bytedcli --json cis-master-data biz-interest-rate get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-interest-rate query \
  --criterion 'identifier=<rate-identifier>' \
  --criterion 'price_type=<price-type>' \
  --criterion 'value_ts=<value-timestamp>'
```

Use exactly one documented criterion field set. Do not substitute `list` for a missing or incomplete
documented query criterion.
