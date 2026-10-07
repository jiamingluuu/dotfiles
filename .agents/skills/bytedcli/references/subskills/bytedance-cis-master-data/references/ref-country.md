# 国家/地区 / Country/Region (`ref-country`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Single-record `get` fields: `mdm_code`, `code`, `three_character_code`
- `batch-get` / `multi-get` fields: `mdm_code`, `code`, `three_character_code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted single-field `query` criteria: `mdm_code`, `code`, `three_character_code`, `name`, `full_name`
- Fixed `search` fields: `name`, `full_name`

## Examples

```bash
bytedcli --json cis-master-data ref-country get --field code --value <country-code>
bytedcli --json cis-master-data ref-country query \
  --criterion 'three_character_code=<three-character-code>'
bytedcli --json cis-master-data ref-country search --keyword <country-name-fragment>
bytedcli --json cis-master-data ref-country list --page-size <bounded-page-size>
```

Use `list` only when exact lookup, bounded query, and fuzzy search do not express the request.
