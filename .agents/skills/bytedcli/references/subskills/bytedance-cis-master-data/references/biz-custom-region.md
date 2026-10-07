# 自定义区域 / Custom Region (`biz-custom-region`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data biz-custom-region get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-custom-region query --criterion 'mdm_code=<master-data-code>'
bytedcli --json cis-master-data biz-custom-region search --keyword <region-name-fragment>
bytedcli --json cis-master-data biz-custom-region list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
