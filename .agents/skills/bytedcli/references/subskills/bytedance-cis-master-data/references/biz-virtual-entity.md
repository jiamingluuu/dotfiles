# 虚拟主体 / Virtual entity (`biz-virtual-entity`)

This model includes trust plans, funds, consolidation adjustments, and consolidation entities
maintained as subjects for business and financial management. It is distinct from the company or
organization records in the legal-entity model. Financial terminology or a fund-like name alone
does not establish the model; follow the domain Skill's entity model selection rules when unclear.

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`, `ebs_code`, `name`, `en_name`, `official_name`, `ebs_short_name`
- `batch-get` fields: `mdm_code`, `ebs_code`, `name`, `en_name`, `official_name`, `ebs_short_name`
- `multi-get` fields: `mdm_code`, `ebs_code`, `name`, `en_name`, `official_name`, `ebs_short_name`
- Accepted single-field `query` criteria: `mdm_code`, `ebs_code`, `name`, `en_name`, `official_name`, `ebs_short_name`
- Fixed `search` fields: `name`, `en_name`, `official_name`, `ebs_code`, `ebs_short_name`

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data biz-virtual-entity get --field mdm_code --value demo-code
bytedcli --json cis-master-data biz-virtual-entity batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data biz-virtual-entity multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data biz-virtual-entity query --criterion 'ebs_short_name=demo-value'
bytedcli --json cis-master-data biz-virtual-entity search --keyword demo-fragment
bytedcli --json cis-master-data biz-virtual-entity list --page-size 16
```

Prefer `mdm_code` when one stable record is required. Business lookup fields can have duplicate
records, including `en_name`; `get` returns one match and does not establish uniqueness. Use `query`
or `multi-get` when all exact matches must be preserved. `accounting_unit_code` is not a supported
query criterion. Keep virtual entities separate from legal entities and legal-entity accounts.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
