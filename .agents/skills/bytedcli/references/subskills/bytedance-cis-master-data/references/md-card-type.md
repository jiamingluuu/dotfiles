# 证件类型 / Identity-Document Type (`md-card-type`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `name`, `description`
- Fixed `search` fields: `name`. Description is available in details and exact `query`; fuzzy search does not match description.

## Examples

```bash
bytedcli --json cis-master-data md-card-type get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-card-type query --criterion 'mdm_code=<master-data-code>'
bytedcli --json cis-master-data md-card-type search --keyword <document-type-fragment>
bytedcli --json cis-master-data md-card-type list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
