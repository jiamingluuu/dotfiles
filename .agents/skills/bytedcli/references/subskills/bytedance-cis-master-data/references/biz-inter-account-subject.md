# 多账套会计科目扩展 / Multi-Ledger Accounting Subject Extension (`biz-inter-account-subject`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `description`. Choose exactly one per query; do not combine these fields.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Basic and Extended Information

多账套会计科目扩展 and [多账套会计科目](md-inter-account-subject.md) describe the same business object and share its query permission. Use the same returned `mdm_code` to read the other entry. When only a basic-information name is known, locate the basic information first and reuse its returned code.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

This model does not expose `search` or `list`. Ask for a documented lookup value when the request lacks one.

## Examples

```bash
bytedcli --json cis-master-data biz-inter-account-subject get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-inter-account-subject batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data biz-inter-account-subject multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data biz-inter-account-subject query --criterion 'description=<exact-value>'
```
