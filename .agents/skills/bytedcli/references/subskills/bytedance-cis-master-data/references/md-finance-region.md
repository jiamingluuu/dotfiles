# 财务区域 / Finance Region (`md-finance-region`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`, `name`
- Accepted single-field `query` criteria: `mdm_code`, `country_mdm_code`, `parent_mdm_code`, `name`. Choose exactly one per query; do not combine these fields.
- Fixed `search` fields: `name`. Supply `--keyword` only; search does not cover other fields.

For `batch-get`, `name` require every criterion in the call to use the same field. Do not mix one of these fields with another field. Other permitted exact fields can be mixed in independent criteria.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

Use `list` for a requested bounded dictionary page when exact lookup, bounded query, and search do not express the request. `current_count` describes this page, not a total count.

## Examples

```bash
bytedcli --json cis-master-data md-finance-region get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-finance-region batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data md-finance-region multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data md-finance-region query --criterion 'name=<exact-value>'
bytedcli --json cis-master-data md-finance-region search --keyword <keyword>
bytedcli --json cis-master-data md-finance-region list --page-size 20
```
