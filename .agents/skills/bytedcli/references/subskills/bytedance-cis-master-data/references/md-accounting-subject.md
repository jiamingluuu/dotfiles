# 会计科目 / Accounting Subject (`md-accounting-subject`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- `get` fields: `mdm_code`, `code`
- `batch-get` and `multi-get` fields: `mdm_code`, `code`, `name`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `parent_mdm_code`, `name`. Choose exactly one per query; do not combine these fields.
- Fixed `search` fields: `name`. Supply `--keyword` only; search does not cover other fields.

For `batch-get`, `name` require every criterion in the call to use the same field. Do not mix one of these fields with another field. Other permitted exact fields can be mixed in independent criteria.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Basic and Extended Information

会计科目 and [会计科目扩展](biz-accounting-subject.md) describe the same business object and share its query permission. Use the same returned `mdm_code` to read the other entry. When only a basic-information name is known, locate the basic information first and reuse its returned code.

Business-key values can match several stored records. Do not assume that one result proves no other match exists. Use `query` for a collection and select the returned `mdm_code` when the user needs a specific record.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

This model does not expose `list`. Ask for a documented lookup value when the request lacks one.

## Examples

```bash
bytedcli --json cis-master-data md-accounting-subject get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-accounting-subject batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data md-accounting-subject multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data md-accounting-subject query --criterion 'name=<exact-value>'
bytedcli --json cis-master-data md-accounting-subject search --keyword <keyword>
```
