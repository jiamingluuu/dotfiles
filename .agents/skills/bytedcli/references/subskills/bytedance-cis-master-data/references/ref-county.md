# 区/县 / County/District (`ref-county`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Single-record `get` field: `mdm_code`
- `batch-get` / `multi-get` fields: `mdm_code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `country_mdm_code`
  - `country_mdm_code,state_mdm_code`
  - `country_mdm_code,state_mdm_code,city_mdm_code`
  - `city_mdm_code`
  - `state_mdm_code`
  - `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-county get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data ref-county query \
  --criterion 'country_mdm_code=<country-master-data-code>' \
  --criterion 'state_mdm_code=<state-master-data-code>' \
  --criterion 'city_mdm_code=<city-master-data-code>'
bytedcli --json cis-master-data ref-county search --keyword <county-name-fragment>
bytedcli --json cis-master-data ref-county list --page-size <bounded-page-size>
```

Use exactly one documented query field set. Do not construct a non-documented field combination.
Use `list` only after exact, bounded, and fuzzy lookup.
