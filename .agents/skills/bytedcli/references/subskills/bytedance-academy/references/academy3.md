# Academy 3.0 Commands

Academy 3.0 remains part of the existing Academy domain. These commands are
additive and do not replace legacy `source_v2` or raw feature set commands.

Use `--site i18n-tt`. Set `BYTEDCLI_NETWORK_PROFILE=prod` on the production
network. All requests use the MLDP API origins documented in
[the Academy reference](academy.md#api-origin-and-authentication), including direct HTTP
requests for endpoints not exposed by the CLI. Console links are resource
references, never API base URLs.

## ID terminology

`fe_config_id` is the FFE `graphVersionId` for one concrete graph version. It
is not the logical FFE graph id, the Academy `featureModuleGraphId`, or the
Feature Module id. Use `--fe-config-id` whenever the user supplies this value.
The backend field `ffeGraphId` and compatibility flag `--ffe-graph-id` carry
the same graph version id.

## FE Sources

```bash
bytedcli --site i18n-tt academy source-registry schema list
bytedcli --site i18n-tt academy source-registry schema get \
  --op-name long_seq_featurebank_source
bytedcli --site i18n-tt academy source-registry scope list
bytedcli --site i18n-tt academy source-registry search \
  --name sample-source --op-name long_seq_featurebank_source
bytedcli --site i18n-tt academy source-registry get --source-id 123

bytedcli --site i18n-tt academy source-registry create \
  --payload-file source.json
bytedcli --site i18n-tt academy source-registry update \
  --source-id 123 --payload-file source-update.json
bytedcli --site i18n-tt academy source-registry validation start \
  --source-id 123
bytedcli --site i18n-tt academy source-registry validation get \
  --source-id 123 --refresh-graph true
```

Create/update/validation defaults an omitted SCM version to the newest build-ok
version and reports it. Create/update payloads are checked against the live
template and graph/physical-region scope map.

Each `scopeConfigs` row uses:

- `graphName`;
- physical `region` from `source-registry scope list`;
- `draftEnabled`;
- `draftConfigJson`;
- `draftExcludedFields`.

Every enabled scope must contain every live-template field unless that field is
explicitly excludable and listed in `draftExcludedFields`. Unknown config keys
and non-excludable exclusions are rejected. For
`long_seq_featurebank_source`, `feature_view` must be non-empty.

After `validation start --yes`, poll `validation get --refresh-graph true`
until the validation reaches a terminal status. Do not continue to module
compile when source validation failed or is still running.

## FE Modules

```bash
bytedcli --site i18n-tt academy feature-module scm-version list
bytedcli --site i18n-tt academy feature-module scm-code-tree get \
  --scm-version 1.0.0.1
bytedcli --site i18n-tt academy feature-module search --keyword sample
bytedcli --site i18n-tt academy feature-module search --fe-config-id 123
bytedcli --site i18n-tt academy feature-module graph analysis get --fe-config-id 123
bytedcli --site i18n-tt academy feature-module get --feature-module-id 456

bytedcli --site i18n-tt academy feature-module access get \
  --feature-module-id 456
bytedcli --site i18n-tt academy feature-module access-audit list \
  --feature-module-id 456
bytedcli --site i18n-tt academy feature-module collaborator create \
  --feature-module-id 456 --username demo-user

bytedcli --site i18n-tt academy feature-module create \
  --payload-file create.json
bytedcli --site i18n-tt academy feature-module fork \
  --payload-file fork.json
bytedcli --site i18n-tt academy feature-module rebase \
  --payload-file rebase.json

bytedcli --site i18n-tt academy feature-module version list \
  --feature-module-id 456
bytedcli --site i18n-tt academy feature-module draft get \
  --feature-module-id 456 --version -1
bytedcli --site i18n-tt academy feature-module draft save \
  --feature-module-id 456 --payload-file draft.json
bytedcli --site i18n-tt academy feature-module code-diff get \
  --feature-module-id 456 --base-version 0 --test-version -1
```

Fork uses `sourceFeatureModuleId` plus a committed non-draft `sourceCommitId`
returned by `feature-module version list`. Create, fork, and rebase scopes are
checked against the live graph and logical-region allowlists. Draft save first
reads the current version and rejects payloads that omit existing files; always
submit the complete code tree.

### Access control

Use `access get` before editing or compiling an existing FE Module. It returns
the owner, collaborators, current caller, and the backend permission flags.
Use `access-audit list` to inspect newest-first collaborator and ownership
changes.

Map natural-language requests to add a collaborator or grant FE Module access to
`collaborator create`. It is the only access mutation exposed by bytedcli. It
previews the request by default and requires `--yes` to submit. If the target
username is already the owner or a collaborator, report that access already
exists. After adding a collaborator, read access again and show the updated
list.

Do not remove collaborators or transfer ownership through bytedcli, MCP, or an
AI skill, including through generic HTTP commands. Those actions remain in the
Studio Access page for the FE Module owner or an Academy admin.

Before generating or changing DSL, fetch the module's exact `scmVersion` and
resolve its `baseCommitHash` with `scm-version list`. The complete
`feature_engine_core/academy/**` package at that commit is the Academy Python
runtime authority. Inspect exact files with the existing Codebase commands:

```bash
bytedcli --json codebase repo directory list \
  -R academy/feature_engine_i18n \
  --revision <baseCommitHash> \
  --path feature_engine_core/academy

bytedcli --json codebase repo file \
  feature_engine_core/academy/core/op/offline_meta.py \
  -R academy/feature_engine_i18n \
  --revision <baseCommitHash>
```

`scm-code-tree get` returns the compiled `feature_graph` code/example snapshot;
it does not contain the full Academy runtime and must not be used as an
`academy.*` allowlist. Rebase is the only normal action that changes the module
SCM.

### Exact-SCM Academy runtime rules

- Inventory every imported or referenced `academy.*` symbol. Verify top-level
  exports, generated `academy.ops`, `academy.aux`, `academy.core`, and supported
  deeper imports against the complete exact-commit runtime.
- Use an op catalog only to discover generated `ops.*` candidates. For those
  ops, verify the exact OpDef/wrapper signature. For other runtime helpers,
  inspect the Python signature, implementation, re-exports, and same-revision
  Feature Module usage when needed.
- Do not reject, delete, or replace an API because it is outside `academy.ops`,
  absent from an op catalog, or imported through `academy.core`. For example,
  preserve `academy.core.op.offline_meta.add_fountain_offline_meta(...)` when
  the selected SCM exposes it; it mutates graph offline metadata and is not
  inherently Academy 2.0-only.
- Distinguish supported DSL helpers from graph-build internals by exact source
  semantics and exact-revision usage, not directory names. If compatibility or
  an equivalent cannot be proven, report it as unresolved instead of deleting
  behavior or inventing a replacement.
- Preserve helper side effects, metadata, callbacks, and ownership in every
  create, edit, repair, fork, and migration workflow—not only returned feature
  values.
- Keep `academy.aux.ue` config creation/registration inside the originating
  current FE Module. `UidConf` and `FidConf` capture the active
  `module_stack[-1]` as `from_module`; do not move them into another FE Module
  or manually substitute a different owner. Subgraph pruning happens later and
  does not repair incorrect ownership.

For an exact historical FFE-version feature list, use graph analysis with
`--fe-config-id`. The command reads the Fountain graph-version record, where an
Academy 3.0 record's `commitId` is the compiled `featureModuleGraphId`, then
returns that artifact's `features`, `rawFeatures`, and `sources`. Do not infer a
historical version's features from the owning module's current draft or latest
code version.

## Academy 2.0 migration

For Online Extraction migration:

1. Fetch the requested commit diff and identify every changed `feature_defs`
   file. Ignore unrelated files.
2. For modified files, fetch the complete post-commit file; never translate
   diff hunks without full context.
3. Produce one Academy 3.0 module/DSL per changed `feature_defs` file. Do not
   merge multiple source modules into one DSL.
4. Preserve feature logic, names, runtime-helper side effects, metadata,
   callbacks, and current-module ownership. Read the migration guide and the
   complete exact-SCM Academy runtime before translating. Remove a lifecycle or
   framework API only when exact source proves it is incompatible, and replace
   it only with a semantics-equivalent API that can also be proven.
5. Prefer the source compilation's graph and region. Map legacy `va` to logical
   `ROW`.
6. Save complete code trees, then resolve/create/compile each module separately
   unless the user explicitly requests one multi-module compilation.

## Compile and inspect

Resolve exact module versions, create the graph, then compile:

```bash
bytedcli --site i18n-tt academy feature-module selection resolve \
  --payload-file selection.json
bytedcli --site i18n-tt academy feature-module graph create \
  --payload-file graph.json

bytedcli --site i18n-tt academy feature-module graph compile \
  --feature-module-graph-id 789 \
  --graph-name tiktok --graph-name search \
  --graph-region ROW --graph-region EU
bytedcli --site i18n-tt academy feature-module graph refresh \
  --feature-module-graph-id 789
bytedcli --site i18n-tt academy feature-module graph get \
  --feature-module-graph-id 789
```

Repeated graph and region values are sent as one compile matrix request. If no
graph or region options are supplied, compile defaults to the primary module's
stored graph and logical-region scope. Explicit values must remain within that
scope.

Poll `graph refresh` followed by `graph get` until status is terminal. Read
`extra.buildLog`; for safely attributable DSL errors, update the complete draft,
resolve/create a new graph, and retry a bounded number of times. Stop on repeated
errors, unavailable SCM ops, missing business semantics, source/config failures,
or non-DSL infrastructure failures.

```bash
bytedcli --site i18n-tt academy feature-module graph dc list \
  --feature-module-graph-id 789
bytedcli --site i18n-tt academy feature-module graph content get \
  --feature-module-graph-id 789 --graph-name tiktok --graph-region sg
bytedcli --site i18n-tt academy feature-module graph analysis get \
  --feature-module-graph-id 789
bytedcli --site i18n-tt academy feature-module graph diff get \
  --base-id 700 --test-id 789
```

## Optional debug and FFE

Debug is explicit and limited to compiled TikTok ROW graphs:

```bash
bytedcli --site i18n-tt academy feature-module debug sample get
bytedcli --site i18n-tt academy feature-module debug start \
  --feature-module-graph-id 789 --feature-name fc_sample
bytedcli --site i18n-tt academy feature-module debug list \
  --feature-module-id 456 --page 1 --page-size 20
bytedcli --site i18n-tt academy feature-module debug run-log get \
  --feature-module-graph-id 789
bytedcli --site i18n-tt academy feature-module debug run-log get \
  --debug-log-id 1001
bytedcli --site i18n-tt academy feature-module debug op-log list \
  --debug-log-id 1001
bytedcli --site i18n-tt academy feature-module debug op-log get \
  --debug-log-id 1001 --file-name output.json
```

Use the returned sample request unless the user supplied one. `debug list`
returns debug history for a Feature Module with standard pagination. For
`debug run-log get`, provide exactly one selector: `--feature-module-graph-id`
reads the latest run for that graph, while `--debug-log-id` reads that exact
historical run. A debug log id can come from either `debug start` or `debug
list`, and the same IDs select `op-log list` / `op-log get`. After debug, inspect
run/op logs and emitted feature values. Missing values for requested outputs
indicate a likely source, sample, or DSL issue; report it rather than claiming
debug success.

FFE sync is also explicit. Content and FFE use a compiled physical DC from
`graph dc list` (`sg`, `gcp`, or `ttp`), not a logical compile region:

```bash
bytedcli --site i18n-tt academy feature-module graph sync-ffe \
  --feature-module-graph-id 789 --graph-name tiktok --graph-region sg
```

After a successful sync, the command re-reads the graph and returns the FFE
`graphVersionId` as both `graphVersionId` and `fe_config_id`.

Preview every mutation first, then rerun with `--yes` after review.
