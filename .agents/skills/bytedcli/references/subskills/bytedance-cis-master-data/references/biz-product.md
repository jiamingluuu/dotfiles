# 业务线扩展 / Business Line Extension (`biz-product`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `level_info`, `explanation`, `mission`, `vision`. Choose exactly one per query; do not combine these fields.
- Fixed `search` fields: `explanation`. Supply `--keyword` only; search does not cover other fields.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Basic and Extended Information

业务线扩展 and [业务线](md-product.md) describe the same business object and share its query permission. Use the same returned `mdm_code` to read the other entry. When only a basic-information name is known, locate the basic information first and reuse its returned code. An extension search only searches the extension fields listed above.

Search the business introduction to discover candidates. Mission and vision are detail fields, not fuzzy-search fields. Use the returned `mdm_code` to read the basic business-line information and confirm the match.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

This model does not expose `list`. Ask for a documented lookup value when the request lacks one.

## Examples

```bash
bytedcli --json cis-master-data biz-product get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-product batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data biz-product multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data biz-product query --criterion 'vision=<exact-value>'
bytedcli --json cis-master-data biz-product search --keyword <keyword>
```
