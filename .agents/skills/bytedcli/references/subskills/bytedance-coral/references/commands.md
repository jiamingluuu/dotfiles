# Coral command cheat sheet

Run `bytedcli coral <subcommand> --help` for exact options. Use `--json` for machine-readable output.

## Top-level

```bash
bytedcli coral --help
bytedcli coral search --help
bytedcli coral hive table --help
bytedcli coral permission --help
```

## Metadata

```bash
# Broad entity search
bytedcli --json coral search --region sg --query "example_table" --type-name HiveTable --limit 10

# DB and table metadata
bytedcli --json coral hive db get --region sg --db-name example_db
bytedcli --json coral hive table list --region sg --db-name example_db --query "example" --limit 10
bytedcli --json coral hive table get --region sg --db-name example_db --table-name example_table

# Table extras
bytedcli --json coral hive table ddl --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table latest-partition --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table partitions --region sg --db-name example_db --table-name example_table --limit 20
bytedcli --json coral hive table preview --region sg --db-name example_db --table-name example_table --limit 10
bytedcli --json coral hive table replicas --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table lineage --region sg --db-name example_db --table-name example_table --direction BOTH
bytedcli --json coral hive table quality --region sg --db-name example_db --table-name example_table
bytedcli --json coral hive table dorado-tasks --region sg --db-name example_db --table-name example_table
```

## Permission

```bash
# Sensitive field update: dry-run previews both two-stage PUT payloads; --dry-run overrides --yes
bytedcli --json coral field set-sensitive --table example_db/example_table --field sample_col --level 4
bytedcli --json coral field set-sensitive --table example_db/example_table --field sample_col --level 4 --yes

# Direct owner grant: preview by default, then rerun with --yes only after explicit confirmation
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --auth-object demo-group --auth-type user_group --permission read --ttl 180
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --auth-object demo-group --auth-type user_group --permission read --ttl 180 --yes

# Modify TTL by existing permission identity (not application id); preview by default
bytedcli --json coral permission modify-ttl --region cn --resource-type table --name example_db/example_table \
  --auth-type person --auth-object demo-user --permission read --ttl 180 --reason "Extend table access"
bytedcli --json coral permission modify-ttl --region cn --resource-type database --name example_db \
  --auth-type psm --auth-object demo.psm --permission read --ttl 90 --reason "Extend database access"
bytedcli --json coral permission modify-ttl --region cn --resource-type column --name example_db/example_table/sample_col \
  --auth-type person --auth-object demo-user --permission read --ttl 30 --reason "Extend column access" --yes

# Table-level read permission
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --permission read --ttl 365 --reason "Need read access for analysis."

# Column-level read permission; repeat --column or comma-separate values (auto-merges partition columns by default)
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --column sample_date --auth-object demo-user --permission read --ttl 365

# Disable partition columns auto-filling when applying for specific columns
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --no-auto-partition --auth-object demo-user --permission read --ttl 365

# Row/partition-scoped read permission; repeat --row-filter for multiple exact values
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --row-filter app=sample-app-lite \
  --auth-object demo-user --permission read --ttl 365

# Advanced: override Coral permission group/cluster when region default is not enough
bytedcli --json coral permission apply --region cn --cluster sample_cluster --db-name example_db \
  --table-name example_table --auth-object demo-user --permission read --ttl 365

# Preserve notice confirmation in the submitted payload (ignore_notice=false)
bytedcli --json coral permission apply --region uspipo --db-name example_db \
  --table-name example_table \
  --auth-type psm --auth-object demo.psm \
  --permission read --ttl 0 --no-ignore-notice

# Answer draft questions; chain from latest draft output
bytedcli --json coral permission answer --draft-file /tmp/coral-draft.json \
  --question-id <question_id> --answer <user_answer> > /tmp/coral-answered.json

# Cross-region multi-select draft questions; use option ids from crossRegionQuestions
bytedcli --json coral permission answer --draft-file /tmp/coral-draft.json \
  --question-id 1 --answer 4 --answer 1 --answer 2 > /tmp/coral-answered-q1.json

# Submit answered draft
bytedcli --json coral permission create --region sg --draft-file /tmp/coral-answered.json

# Withdraw an existing application
bytedcli --json coral permission withdraw --region sg --id <application_id> --description "Withdraw test application"
```

## Notes

- Supported Coral regions shown by current help are generated from the site registry: `cn`, `sg`, `gcp`, `va`, `us-eastred`, `eu-ttp2`, `us`, `mycis`, `sglark`, `jplark`, `uspipo`, plus official-name alias `eu-compliance2` for the legacy `gcp` key. `gcp` / `eu-compliance2` is EU-Compliance2 (cid 31); `us-eastred` is a separate control plane (cid 5). The default follows `--site` / `BYTEDCLI_CLOUD_SITE`: `eu-ttp` uses `us-eastred`, US-TTP sites use `us`, `i18n` uses `va`, `i18n-bd` uses `mycis`, and unspecified or `i18n-tt` uses `sg`.
- For Hive table search, `HiveTable` works as the entity type.
- `permission modify-ttl` uses resource identity (`resource_type` plus `name`, authorization fields, and permission), not an application id. It previews endpoint + payload by default and sends only with `--yes`; use `--object`/`--objects-file` for batches.
- `permission grant` is an immediate owner write: it previews endpoint + complete payload by default and sends only with `--yes`; explicit `--dry-run` overrides `--yes`. It supports table- and column-level grants, with `user_group` (default) or `person` recipients.
- `permission apply` returns either a submitted/existing/unknown result or `status: draft`; see `permission-workflow.md` for draft handling.
- `permission apply --cluster <cluster>` is an advanced Coral group override. CN permission apply defaults to Coral group `default`; omit it for normal flows.
- `permission apply` sends `ignore_notice=true` by default. Pass `--no-ignore-notice` when the product flow explicitly requires `ignore_notice=false`.
- `permission apply --row-filter column=value` accepts exact values only. The CLI validates the column and each value against Coral resource settings and rejects unsupported or closed values before generating the draft.
- Cross-region drafts expose `crossRegionQuestions`; answer them through `permission answer`, not by manually editing `cross_region_questions_answers`.

## Global table lifecycle

Use `coral global-table create`, `modify field`, `add-region`, `get` and `wait`. See [global-table.md](global-table.md) for Hive-compatible schema inputs, the dedicated i18n-tt region mapping, default preview and operation recovery.
