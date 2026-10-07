# 源系统标识 / Source-System Identifier (`biz-source-system`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data biz-source-system get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-source-system query --criterion 'mdm_code=<master-data-code>'
bytedcli --json cis-master-data biz-source-system search --keyword <source-system-name-fragment>
bytedcli --json cis-master-data biz-source-system list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
