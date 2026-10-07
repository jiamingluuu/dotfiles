# 语言 / Language (`ref-language`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `code`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-language get --field code --value <language-code>
bytedcli --json cis-master-data ref-language query --criterion 'code=<language-code>'
bytedcli --json cis-master-data ref-language search --keyword <language-name-fragment>
bytedcli --json cis-master-data ref-language list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
