# 多账套会计科目 / Multi-Ledger Accounting Subject (`md-inter-account-subject`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- `get` fields: `mdm_code`, `code`
- `batch-get` and `multi-get` fields: `mdm_code`, `code`, `name`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `parent_mdm_code`, `name`. Choose exactly one per query; do not combine these fields.
- Fixed `search` fields: `name`. Supply `--keyword` only; search does not cover other fields.

For `batch-get`, `name` require every criterion in the call to use the same field. Do not mix one of these fields with another field. Other permitted exact fields can be mixed in independent criteria.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Search and Detail Permissions

Name search returns discovery summaries containing `mdm_code` and `name` (including available language variants) without requiring the model query permission. Search success does not authorize detail access. Use the returned `mdm_code` for a detail query; that query still checks the signed-in account’s row and field permissions.

## Basic and Extended Information

多账套会计科目 and [多账套会计科目扩展](biz-inter-account-subject.md) describe the same business object and share its detail query permission. Use the same returned `mdm_code` to read the other entry. When only a basic-information name is known, locate the basic information first and reuse its returned code.

Business-key values can match several stored records. Do not assume that one result proves no other match exists. Use `query` for a collection and select the returned `mdm_code` when the user needs a specific record.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

To narrow a `code` lookup to an accounting area, use `query --criterion 'code=<code>' --filter 'area_code=equal:<area>'`. `area_code` is an additional filter, not a driving criterion.

This model does not expose `list`. Ask for a documented lookup value when the request lacks one.

If the accounting area code is unknown, first use [the area directory](md-inter-account-subject-area.md). Its code is an additional `area_code` filter, not an independent query criterion.

## Examples

```bash
bytedcli --json cis-master-data md-inter-account-subject get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-inter-account-subject batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data md-inter-account-subject multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data md-inter-account-subject query --criterion 'name=<exact-value>'
bytedcli --json cis-master-data md-inter-account-subject search --keyword <keyword>
```
