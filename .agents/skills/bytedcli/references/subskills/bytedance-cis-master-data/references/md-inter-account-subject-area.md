# 多账套会计科目COA / Accounting Areas (`md-inter-account-subject-area`)

## Methods and Fields

- Methods: `list`, `get`.
- `get` field: `code` only. Other exact fields and `batch-get`, `multi-get`, `query`, `search` are not exposed.
- Returns accessible accounting areas, subject to the same permissions as 主数据平台. Access reuses the existing 多账套会计科目COA directory query permission; a 多账套会计科目 role must include that permission to access this directory. On permission denial, follow only the application link returned by the CLI.
- Returned directory fields (not an exact lookup or filter allow-list): `mdm_code`, `code`, `name`, `status`, `country_code`, `country_mdm_codes`.
- Filtering: use `--filter status=equal:1` only when the user requests effective areas.
- Sorting: keep the default order; do not infer a sort option from the returned fields.
- Follow normal list pagination. A page is not a promise of the complete directory.

## Choosing an Area

Discover the area by its returned name and code; distinguish old and current areas instead of guessing. Ask the user when several candidates match their intent.

Use the returned `code` as an `area_code` filter when querying multi-ledger subjects with a documented driving criterion. The subject model does not support `area_code` as a driving criterion or `list`; knowing only an area is insufficient to enumerate all subjects. Ask for a subject code or another documented lookup value.

## Examples

```bash
bytedcli --json cis-master-data md-inter-account-subject-area list --page-size 32
bytedcli --json cis-master-data md-inter-account-subject-area get --field code --value <area-code>
bytedcli --json cis-master-data md-inter-account-subject query --criterion 'code=<subject-code>' --filter 'area_code=equal:<returned-area-code>'
```

Directory access does not grant access to every subject in that area. Follow permission errors returned by the subject query.
