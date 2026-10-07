# 城市 / City (`ref-city`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`
- Single-record `get` field: `mdm_code`
- `batch-get` / `multi-get` fields: `mdm_code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `state_mdm_code`
  - `country_mdm_code`
  - `country_mdm_code,state_mdm_code`
  - `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-city get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data ref-city query \
  --criterion 'country_mdm_code=<country-master-data-code>' \
  --criterion 'state_mdm_code=<state-master-data-code>'
bytedcli --json cis-master-data ref-city search --keyword <city-name-fragment>
```

Use exactly one documented query field set. `list` is intentionally unavailable because this model has a large data volume.
