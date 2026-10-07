# CIS业务线 / CIS Business Line (`md-cis-business-line`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `parent_mdm_code`, `name`, `description`
- Fixed `search` fields: `name`, `description`
- All methods, including fuzzy `search`, require access to this model. If access is denied, surface the returned application link instead of changing the model or query.

## Examples

```bash
bytedcli --json cis-master-data md-cis-business-line get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-cis-business-line query \
  --criterion 'parent_mdm_code=<parent-master-data-code>'
bytedcli --json cis-master-data md-cis-business-line query \
  --criterion 'name=<exact-business-line-name>'
bytedcli --json cis-master-data md-cis-business-line search \
  --keyword <business-line-name-or-description-fragment>
bytedcli --json cis-master-data md-cis-business-line list --page-size <bounded-page-size>
```

`name` and `description` are exact single-field `query` criteria, not exact lookup fields. Do not use either with `get`, `batch-get`, or `multi-get`, and do not combine them with another `query` criterion.

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
