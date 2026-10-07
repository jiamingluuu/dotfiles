# 人员序列 / Personnel sequence (`md-sequence`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get` fields: `mdm_code`, `sequence_id`
- `batch-get` fields: `mdm_code`, `sequence_id`
- `multi-get` fields: `mdm_code`, `sequence_id`
- Accepted single-field `query` criteria: `mdm_code`, `sequence_id`, `parent_mdm_code`, `name`
- Fixed `search` fields: `name`

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-sequence get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-sequence batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-sequence multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-sequence query --criterion 'name=demo-value'
bytedcli --json cis-master-data md-sequence search --keyword demo-fragment
bytedcli --json cis-master-data md-sequence list --page-size 16
```

Use `parent_mdm_code` with `query` for children of a known personnel sequence. `name` supports
exact `query` and fuzzy `search`, but not `get`, `batch-get`, or `multi-get`. `corehr_id`,
`corehr_code`, and `parent_sequence_id` are not supported query criteria. This model describes
personnel sequences, not individual employee records.

Use `list` only when the other documented methods do not express the request. Keep the page size
bounded, use only documented optional fields, and continue with the returned page token when needed.
