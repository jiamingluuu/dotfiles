# 支出类型 / Expense Type (`md-expense-type`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`, `name`
- Accepted single-field `query` criteria: `mdm_code`, `parent_mdm_code`, `source_code`, `name`, `remark`. Choose exactly one per query; do not combine these fields.
- Fixed `search` fields: `name`, `remark`. Supply `--keyword` only; search does not cover other fields.

For `batch-get`, `name` require every criterion in the call to use the same field. Do not mix one of these fields with another field. Other permitted exact fields can be mixed in independent criteria.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

This model does not expose `list`. Ask for a documented lookup value when the request lacks one.

## Examples

```bash
bytedcli --json cis-master-data md-expense-type get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-expense-type batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data md-expense-type multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data md-expense-type query --criterion 'remark=<exact-value>'
bytedcli --json cis-master-data md-expense-type search --keyword <keyword>
```
