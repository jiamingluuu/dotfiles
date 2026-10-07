# 法人主体 / Legal Entity (`md-legal-entity`)

This model represents companies or organizations with registration, tax, legal-status, and
financial information. It is distinct from virtual entities such as trust plans or consolidation
adjustments. Business attributes do not imply that this CLI returns or accepts those attributes.
For an unspecified `主体`, `公司`, or `组织`, follow the domain Skill's entity model selection rules before querying.

Only `search` is exposed for this model.

The command searches these fixed fields together:

- `name`
- `en_name`
- `official_name`
- `ebs_code`
- `ebs_short_name`

```bash
bytedcli --json cis-master-data md-legal-entity search --keyword <name-fragment>
bytedcli --json cis-master-data md-legal-entity search --keyword <legal-entity-name> --page 1 --page-size 20
```

Do not attempt `get`, `batch-get`, `multi-get`, `query`, or `list` for this model.
