# FTF Noise-Template Rule Management

## Use Cases

Use this workflow to list, query, create, or update field-level rules under
`ftf assertion noise-template-rule`.

Do not use it for one-off DIFF annotations, full SchemaConfig replacement, template deletion, or
PSM/Method metadata. The first release intentionally has no `delete` command.

## Inputs

`list` is an inbound-only discovery command. It requires:

- `--psm <psm>` and `--method <method>`
- optional `--scene <scene>`, defaulting to `default`
- optional `--page` and `--page-size`, defaulting to `1` and `10`; page size is limited to 100

The remaining commands require:

- `--direction inbound|outbound`
- `--psm <psm>` and `--method <method>` for the upstream request
- `--mode system|sandbox`
- `--scene <scene>`, defaulting to `default`

Inbound selectors must not include outbound options. Outbound selectors use exactly one locator:

- RPC/HTTP: `--outbound-method`; `--outbound-psm` and `--outbound-protocol` are optional metadata.
- DB: both `--outbound-table` and `--outbound-table-operation`; `--outbound-method` is forbidden.

`get` additionally requires `--path`. `create` and `update` require `--details-file` containing a
JSON array with 1 to 20 entries. Create entries are new rule objects where only `path` is required.
Update entries are shallow
patches with a required `path`; omitted fields are preserved, arrays and
`schemaConfigDetailMap` are replaced as a whole, and `[]` or `{}` clears a collection. Explicit
`null` is not supported in update patches.

Example create file:

```json
[
  {
    "path": "data->items->[*]->request_id",
    "needDiff": 0,
    "noiseTag": "dynamic identifier"
  }
]
```

Example update file:

```json
[
  {
    "path": "rows->[*]->updated_at",
    "schemaConfigDetailMap": {},
    "noiseTag": "updated timestamp"
  }
]
```

## Quick Start

Choose the leaf from the information already available:

| Need | Command | Minimum input | Writes data |
| --- | --- | --- | --- |
| Discover inbound rules and the actual parent mode | `list` | PSM + Method | No |
| Read one known path | `get` | Full selector + path | No |
| Add new paths | `create` | Full selector + details file | Preview by default; only with `--yes` |
| Change existing paths | `update` | Full selector + details file | Preview by default; only changed rules with `--yes` |

When only PSM and Method are known, start with `list`, then reuse one returned path and the actual
parent mode for `get`:

```bash
bytedcli --site cn --json ftf assertion noise-template-rule list \
  --psm example.psm \
  --method GetDemo

bytedcli --site cn --json ftf assertion noise-template-rule get \
  --direction inbound \
  --psm example.psm \
  --method GetDemo \
  --mode sandbox \
  --path 'data->items->[*]->request_id'
```

Read `data.parent.mode` from the list response instead of guessing `system` or `sandbox`. For
pagination, increment `--page` while `data.has_more=true`; `--page-size` defaults to 10 and cannot
exceed 100. Put global flags such as `--site`, `--json`, and `--as` before `ftf`.

## Workflow

### List inbound rules from PSM and Method

Use `list` when the path or parent mode is not known. Validate the leaf, then request one page:

```bash
bytedcli --json ftf assertion noise-template-rule list --help
bytedcli --json ftf assertion noise-template-rule list \
  --psm example.psm \
  --method GetDemo
```

The command fixes `direction=inbound` and strict mode internally. Read `data.rules[].path` to
choose a path for `get` or `update`. Use `data.has_more` and increment `--page` when more rules
are available. `data.parent.exists=false` means the parent configuration does not exist;
`data.parent.exists=true` with an empty `rules` array means the parent exists but has no active
noise-template rules.

### Get one inbound rule

Validate the exact leaf first when command availability is uncertain, then run the read:

```bash
bytedcli --json ftf assertion noise-template-rule get --help
bytedcli --json ftf assertion noise-template-rule get \
  --direction inbound \
  --psm example.psm \
  --method GetDemo \
  --mode system \
  --path "data->items->[*]->request_id"
```

Trust `data.exists`, not the returned rule defaults, when deciding whether the path exists.
`data.context.configLastModifyTime` is the parent version used internally by update.

### Create outbound method rules

Create previews locally by default and performs no GET or write. Review the exact request in JSON,
then repeat the same command with `--yes`:

```bash
bytedcli --json ftf assertion noise-template-rule create \
  --direction outbound \
  --psm example.psm \
  --method GetDemo \
  --mode system \
  --outbound-psm downstream.example \
  --outbound-method GetDownstream \
  --outbound-protocol thrift \
  --details-file ./noise-template-create.json

bytedcli --json ftf assertion noise-template-rule create \
  --direction outbound \
  --psm example.psm \
  --method GetDemo \
  --mode system \
  --outbound-psm downstream.example \
  --outbound-method GetDownstream \
  --outbound-protocol thrift \
  --details-file ./noise-template-create.json \
  --yes
```

Create is strict ADD, not upsert. If any path already exists, stop and use update for that path.

### Update outbound table rules

Update performs one strict GET per path with fixed concurrency 4, requires one consistent parent
version, shallow-merges each patch, and previews before/after values. Without `--yes` it sends no
write. Repeat the complete command with `--yes` only after reviewing the preview:

```bash
bytedcli --json ftf assertion noise-template-rule update \
  --direction outbound \
  --psm example.psm \
  --method QueryRows \
  --mode system \
  --outbound-psm mysql.example \
  --outbound-protocol mysql \
  --outbound-table orders \
  --outbound-table-operation SELECT \
  --details-file ./noise-template-update.json

bytedcli --json ftf assertion noise-template-rule update \
  --direction outbound \
  --psm example.psm \
  --method QueryRows \
  --mode system \
  --outbound-psm mysql.example \
  --outbound-protocol mysql \
  --outbound-table orders \
  --outbound-table-operation SELECT \
  --details-file ./noise-template-update.json \
  --yes
```

If one GET fails, the CLI stops scheduling requests that have not started. Already-issued
read-only GETs may finish, but their results are discarded and no merge or write follows.

## Write Constraints

- Create and update are preview-only unless `--yes` is present on the FTF parent or leaf.
- Create submits one strict ADD and does not pre-query paths.
- Update writes only changed rules and sends the parent version obtained by its preparation GETs.
- A no-op update sends no write even with `--yes`.
- Writes do not automatically replay after authentication, timeout, connection, version, or CAS
  failures.
- Success means the configuration was persisted and asynchronous synchronization was triggered;
  it does not prove downstream consumption completed.

## Results

- List JSON returns `rules`, `page`, `page_size`, `total`, `has_more`, and parent context with
  `exists`, `schema_id`, actual `mode`, and `config_last_modify_time`.
- Get JSON returns `exists`, the complete `rule`, and strict parent `context`.
- Preview JSON returns the selector, exact request, path/change summaries, write count, and
  `confirmation_required`.
- Mutation JSON returns the backend receipt including paths, affected count, conflicts, operator,
  parent modification time, and concurrency flags.

Recovery rules:

| Error                                      | Required action                                                                                                                                            |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FTF_NOISE_TEMPLATE_PRECONDITION_CONFLICT` | Correct a selector mismatch, or rerun the complete update to GET a fresh version, review the new preview, and confirm again. Never replay the old request. |
| `FTF_NOISE_TEMPLATE_CONCURRENT_CONFLICT`   | Rerun the complete command; do not directly retry the previous write payload.                                                                              |
| `FTF_NOISE_TEMPLATE_CONFLICT`              | Remove existing paths from create or move them to an update file.                                                                                          |
| `FTF_NOISE_TEMPLATE_NOT_FOUND`             | Verify each path with get, then create missing rules or correct the update file.                                                                           |
| `FTF_NOISE_TEMPLATE_UNSUPPORTED_FIELDS`    | Upgrade bytedcli before updating; the CLI refuses to drop fields introduced by a newer server contract.                                                    |
| `FTF_NOISE_TEMPLATE_WRITE_UNCERTAIN`       | Stop writes and use get to read back every target path before deciding whether another write is safe.                                                      |
