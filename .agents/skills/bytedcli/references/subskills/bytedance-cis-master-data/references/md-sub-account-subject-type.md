# 会计子目类型 / Accounting Subsubject Types (`md-sub-account-subject-type`)

## Methods and Fields

- Methods: `list` only. Do not use `get`, `batch-get`, `multi-get`, `query`, or `search`.
- Returns accessible type codes and names, subject to the same permissions as 主数据平台. Access reuses the existing 会计子目类型 directory query permission; a 会计子目 role must include that permission to access this directory. On permission denial, follow only the application link returned by the CLI.
- Use `code` from a returned type as the `type` criterion of `md-sub-account-subject query`; do not substitute its `mdm_code`.
- Returned directory fields (not an exact lookup or filter allow-list): `mdm_code`, `code`, `name`, `status`, `priority`. Names may appear as language-specific keys.
- Filtering: use `--filter status=equal:1` only when the user requests effective types; do not apply it by default.
- Sorting: keep the default order; do not infer a sort option from the returned fields.
- Follow normal list pagination. A page is not a promise of the complete directory.

## Examples

```bash
bytedcli --json cis-master-data md-sub-account-subject-type list --page-size 32
# Read the returned type name and code before querying the requested category.
bytedcli --json cis-master-data md-sub-account-subject query --criterion 'type=<returned-type-code>'
```

If the requested type is not visible, report that result; do not guess its code or bypass permissions.
