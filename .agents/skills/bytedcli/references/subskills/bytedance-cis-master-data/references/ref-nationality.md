# 国籍 / Nationality (`ref-nationality`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `code`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-nationality get --field code --value <nationality-code>
bytedcli --json cis-master-data ref-nationality query --criterion 'code=<nationality-code>'
bytedcli --json cis-master-data ref-nationality search --keyword <nationality-name-fragment>
bytedcli --json cis-master-data ref-nationality list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
