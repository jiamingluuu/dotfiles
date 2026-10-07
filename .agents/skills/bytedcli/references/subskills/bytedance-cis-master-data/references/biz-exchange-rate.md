# 汇率 / Exchange Rate (`biz-exchange-rate`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- Exact lookup field: `mdm_code`
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `x_currency`
  - `x_currency,y_currency`
  - `x_currency,y_currency,date`
  - `x_currency,y_currency,date,rate_type`
  - `date`
  - `date,rate_type`
- `search` and `list` are not exposed for this model.

## Examples

```bash
bytedcli --json cis-master-data biz-exchange-rate get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-exchange-rate query \
  --criterion 'x_currency=<base-currency-code>' \
  --criterion 'y_currency=<quote-currency-code>' \
  --criterion 'date=<effective-date>' \
  --criterion 'rate_type=<rate-type>'
```

Use exactly one documented criterion field set. Do not substitute `list` for a missing or incomplete
documented query criterion.
