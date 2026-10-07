# 预算科目 / Budgetary Account (`md-budgetary-account`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`, `budget_subject_name`
- Accepted single-field `query` criteria: `mdm_code`, `budget_subject_parent_code`, `parent_mdm_code`, `budget_subject_name`, `oa_name`. Choose exactly one per query; do not combine these fields.
- Fixed `search` fields: `budget_subject_name`, `oa_name`. Supply `--keyword` only; search does not cover other fields.

For `batch-get`, `budget_subject_name` require every criterion in the call to use the same field. Do not mix one of these fields with another field. Other permitted exact fields can be mixed in independent criteria.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Basic and Extended Information

预算科目 and [预算科目扩展](biz-budgetary-account.md) describe the same business object and share its query permission. Use the same returned `mdm_code` to read the other entry. When only a basic-information name is known, locate the basic information first and reuse its returned code.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

This model does not expose `list`. Ask for a documented lookup value when the request lacks one.

## Examples

```bash
bytedcli --json cis-master-data md-budgetary-account get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-budgetary-account batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data md-budgetary-account multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data md-budgetary-account query --criterion 'oa_name=<exact-value>'
bytedcli --json cis-master-data md-budgetary-account search --keyword <keyword>
```
