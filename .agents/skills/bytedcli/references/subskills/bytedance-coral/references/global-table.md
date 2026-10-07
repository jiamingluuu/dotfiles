# Global Hive tables

Use `bytedcli --site i18n-tt coral global-table` to create a Global table and publish its physical tables, append regions, replace ordinary fields, or observe a publication. This command uses a personal user identity and the office network profile. Explicit non-i18n-tt sites and service identities fail before HTTP. It defaults to i18n-tt only when no site is explicitly selected.

## Regions and transport

| CLI region             | Oceanus region | cid |
| ---------------------- | -------------- | --- |
| va                     | US-East        | 1   |
| sg                     | Singapore      | 6   |
| gcp                    | US-EastRed     | 5   |
| eu-ttp2 (alias euttp2) | EU-TTP2        | 39  |
| us-ttp (alias usttp)   | US-TTP         | 9   |
| eu-compliance2        | EU-Compliance2 | 31  |

Global metadata uses cid=100. `eu-compliance2` is a distinct target (cid=31), not an alias for Global `gcp` (cid=5). This Global-specific `gcp` means US-EastRed; ordinary Coral commands retain their existing region meanings. `eu2` is not an alias. Schema, metadata and publication use the Oceanus personal OpenAPI gateway. Optional `get/wait --verify-ddl` uses the existing regional Hive DDL routes and authentication.

## Create

The Global project must map to all targets, all databases must exist, and the table must be absent globally and locally. A same-table publication that is active or has uncertain completion blocks create even when metadata is still absent; this check runs in preview and again before submission. One Oceanus version PUT with `autoRelease=true` creates the Global definition and starts regional publication. The CLI does not invoke five separate `hive ddl create` commands.

```bash
# Preview; performs read-only preflight and server schema parsing
bytedcli --site i18n-tt coral global-table create \
  --project-id 123 --database example_db --table demo_table \
  --fields '[{"name":"id","dataType":"bigint"}]' \
  --partition-keys '[{"name":"date","dataType":"string"}]' \
  --ttl 1 --ttl-column date --region va,sg,gcp,eu-ttp2,us-ttp \
  --region-owner va=demo-owner-a --region-owner sg=demo-owner-a \
  --region-owner gcp=demo-owner-b --region-owner eu-ttp2=demo-owner-b \
  --region-owner us-ttp=demo-owner-c

# SQL input: database/table may be taken from the qualified statement
bytedcli --site i18n-tt coral global-table create \
  --project-id 123 --region va,sg --ttl 1 --ttl-column date \
  --ddl 'CREATE TABLE example_db.demo_table (id BIGINT) PARTITIONED BY (date STRING)'

# File alternative: the same command submits only with --yes
bytedcli --site i18n-tt coral global-table create \
  --project-id 123 --region va,sg --ttl 1 --ttl-column date \
  --file ./demo.sql --yes --wait
```

Inputs follow `hive ddl create`: `--fields` and `--partition-keys` JSON, or `--ddl`, or `--file`. SQL must contain one fully consumed `CREATE TABLE (...) PARTITIONED BY (...)` statement. If flags also identify the table, they must match SQL. Unknown clauses, extra statements and constraints are rejected. Ordinary fields support primitive Hive types, `decimal(p,s)` with p=1..38 and s<=p, and nested `array<T>`, `map<K,V>`, `struct<name:T,...>` and `uniontype<T,...>`. Map keys and partition keys must be primitive types; nesting is limited to 64 levels. Struct field names use letters, digits and underscores (starting with a letter or underscore), optionally backtick-quoted. Duplicate struct names are rejected case-insensitively. For example, use `--fields '[{"name":"tags","dataType":"array<string>"},{"name":"attributes","dataType":"map<string,array<bigint>>"}]'`; the same types work in `--ddl` / `--file` and `modify field`. Create still requires the server-parsed schema to match before submission; backend storage/region restrictions remain authoritative. The field object accepts `name`, `dataType`, `comment` and optional `typeName: HiveColumn`; omitted comments become empty strings.

TTL is an explicit positive integer in days. `--ttl-column` must be a STRING partition, with `--ttl-extension-type pname` and `--ttl-pattern yyyyMMdd`. The initial storage template is managed parquet/zstd, security level 2, non-core. Unsupported policies/formats are rejected. Global metadata TTL may be -1; the requested TTL applies to physical tables.

Owner/contact/admin rules:

- `--owner` provides default regional owners; `--region-owner region=user` overrides an individual target. Repeat for multiple owners. Without an owner flag the current user owns the target.
- `--global-owner` defaults to the current user independently of local owners.
- `--business-contact` defaults to the current user. `--specified-real-user` supplies the authority admin; otherwise it is the first regional owner.
- `--region-config-file` accepts `{ "schemaVersion": 1, "regions": { "va": { "owners": ["demo-owner"], "businessContacts": ["demo-contact"], "authorityAdmins": ["demo-admin"] } } }`. Only requested regions are allowed. A config owner and `--region-owner` for the same target conflict.
- Notifications default off; `--notify` enables platform publication notifications.

## Add regions and change fields

```bash
# Append missing regional tables; inherit the existing Global schema and bindings
bytedcli --site i18n-tt coral global-table add-region \
  --project-id 123 --database example_db --table demo_table \
  --region gcp,eu-ttp2 --owner demo-owner-b --ttl 1 --ttl-column date

# Complete ordinary field list; publish only to selected regions
bytedcli --site i18n-tt coral global-table modify field \
  --project-id 123 --database example_db --table demo_table --region va,sg \
  --fields '[{"name":"id","dataType":"bigint"},{"name":"sample_value","dataType":"string"}]'

# Full target list: remove sample_value by omitting it (preview)
bytedcli --site i18n-tt coral global-table modify field \
  --project-id 123 \
  --ddl 'ALTER TABLE example_db.demo_table REPLACE COLUMNS (id BIGINT)'

# SQL file alternative
bytedcli --site i18n-tt coral global-table modify field \
  --project-id 123 --file ./demo-alter.sql
```

`modify field` follows `hive modify field`: supply the complete resulting ordinary field list. Omitted old fields are removed; append additions after retained fields. Retained names, types, comments and relative order must remain unchanged. Partition edits, type migrations, reorders, renames, CASCADE/RESTRICT and removing all fields are unsupported. Dropping a field does not physically erase historical file contents. Both JSON and SQL inputs run the existing regional Hive schema Explain before publication; any preflight failure stops submission.

For field updates, `--region` selects a subset of the intended regions; omit it to select all, including regions from an unfinished initial publication. Selected regions must have a successful stored regional version and an existing physical table. The backend automatically cancels an earlier unfinished publication when a new version is submitted, including its unselected pending regions. Therefore the default command blocks while any prior publication is pending. Use `--supersede-pending` only with explicit authorization for this effect; the preview lists `pendingPublications`, and `--yes` is still required. Unselected canceled targets are not republished. A never-created target requires a later `add-region`, not a field update. Regional owners, TTL, partitions and storage settings are preserved. The Global schema changes to the requested schema; unselected regions keep their current schema and may lag until explicitly updated. Reuse the same complete field list with `--region` to bring lagging regions into agreement after their pending publication finishes. A schema equal to Global is accepted when a selected region still needs changes. `add-region` creates only new local tables; it does not adopt an already existing local table.

Update previews include `preservationNotes`: writable attributes absent from current metadata are retained from successful per-region version snapshots. Metadata and version history are checked again before submission. The endpoint provides no atomic compare-and-swap, so concurrent edits from another process or machine cannot be fully excluded. A four-region field addition has been verified through the live version API and physical DDL. The backend canceled the prior publication's unselected pending region; preserving that old publication is not supported by the verified route. A two-region field removal has also been verified through the CLI and physical DDL; unselected regional tables retained the removed field. Completing deferred regions remains a separate live acceptance case.

## Submission and recovery

All three writes default to a full payload preview. `--yes` submits once; `--dry-run` takes precedence. User authorization already present in the conversation is sufficient; do not repeatedly ask for the same permission. Local records contain the plan, hashes, baseline IDs, receipt and observed associations in the active auth profile. Records are private files and contain no credentials. A resource lock prevents uncertain or concurrent submissions. An accepted predecessor with one exact matching version can hand over the lock only after selected regions have a verified successful source and any earlier pending-publication cancellation is explicitly authorized; predecessor and successor records remain linked. Attempting, indeterminate or ambiguously associated predecessors block another submission.

```bash
# Read the current Global table and every currently bound regional table
bytedcli --site i18n-tt coral global-table get --database example_db --table demo_table

# Observe the saved operation; never submits another version
bytedcli --site i18n-tt coral global-table wait \
  --operation-id 11111111-1111-4111-8111-111111111111 \
  --timeout-ms 300000 --poll-interval-ms 10000 --verify-ddl

# Recover on another machine/profile using an explicit release and project
bytedcli --site i18n-tt coral global-table get \
  --release-id demo-release --project-id 123 --verify-ddl
```

`get/wait --release-id` requires `--project-id` because release detail does not contain a project ID. For a multi-table release, provide both `--database` and `--table`; completion remains conservative when package counts cannot be attributed to this table. `--operation-id` cannot be combined with other table/release selectors. `--region` filtering is supported only by table-only `get`.

`wait` defaults to a total 300000 ms deadline and 10000 ms polling (minimum 5000). Timeout or Ctrl-C stops local observation; it does not cancel publication. Continue with the same ID. A write timeout produces `CORAL_GLOBAL_SUBMISSION_INDETERMINATE` and an operation ID, never an automatic write retry. Do not delete a lock and repeat an uncertain write.

`workflow.complete` refers to this operation's selected targets: it requires one matching finished release, every target's success state, matching Global/local schema, owners, TTL, storage and bidirectional bindings. Complete prior bindings and pending expected targets are retained. `deferredRegions` reports other regions separately and does not affect selected-target completion. `workflow.releaseComplete` and `workflow.metadataMatches` distinguish historical release completion from current table verification; a superseded operation points to its successor rather than requesting restoration of an older schema. `--verify-ddl` also checks physical field/partition definitions and TTL; null DDL is not success. Table-only `get` verifies current metadata but does not claim publication completion.

`association=candidate` means actor/payload/baseline evidence identifies a unique candidate but not proven request ownership. `operationConfirmed` is separate from `workflow.complete`. Ambiguous/truncated discovery blocks completion. `get` returns a snapshot even when pending; `wait` exits nonzero on timeout, failure or ambiguity. Approval status stays `unknown` without machine-readable evidence: USTTP `RELEASING` alone does not prove a particular approval ticket or rejection.

Importing/binding existing tables, cross-region data replication, Global ETL and approval handling are outside this command set. Do not invent `import`, `bind`, `add-column` or `drop-column` commands.
