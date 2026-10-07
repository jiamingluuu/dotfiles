# 金融分支机构 / Financial-Institution Branch (`md-bank`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- Exact lookup fields: `mdm_code`, `code`; prefer `mdm_code` for stable single-record lookup
- Fixed `search` fields: `name`, `bank_branch_name`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `bank_code`, `name`,
  `bank_branch_name`

## Examples

```bash
bytedcli --json cis-master-data md-bank search --keyword <institution-name>
bytedcli --json cis-master-data md-bank get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-bank multi-get \
  --field mdm_code --value <master-data-code-1> --value <master-data-code-2>
bytedcli --json cis-master-data md-bank query \
  --criterion 'code=<branch-code>' --filter 'status=equal:1'
```

Use `search` for partial institution or branch names. `query --criterion name=<value>` performs an
exact indexed name lookup, not fuzzy search. Historical rows can share the same `code`; use
`mdm_code` when one stable record is required. A `multi-get --field code` can therefore return more
than one row for a value.

`code` identifies a branch; `bank_code` identifies its bank grouping; `mdm_code` identifies a
specific record. Do not substitute these fields or turn a partial code into an exact lookup.
