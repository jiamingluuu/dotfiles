# ByteBatch commands

All commands accept `--bytebatch-site <cn|i18n|boe|boe-i18n>` (default `cn`) and the global `-j/--json` flag. The site selects both the ByteBatch host and the matching bytedcli ByteCloud user-JWT partition. Formal requests do not send PPE headers.
JSON output schema is `{status, data, error, context}`.

## Discovery

```bash
# Which ByteBatch user does the current login map to?
bytedcli bytebatch whoami

# Deploy regions and the clusters available in each region
bytedcli bytebatch region list

# My services (default), the whole product group, or every service
bytedcli bytebatch service list
bytedcli bytebatch service list --list-type all --keyword demo
bytedcli bytebatch service list --page 2 --page-size 50

# One service: owner, default region/cluster, cron command, permissions
bytedcli bytebatch service get --psm demo.example.batch

# Job types registered for that service in one deploy region
bytedcli bytebatch job-type list --psm demo.example.batch --region China-North
```

`--list-type` accepts `my` (default) / `group` / `all`.

## Jobs

```bash
# Latest jobs of a service in one region
bytedcli bytebatch job list --psm demo.example.batch --region China-North

# Filter by type / status / id / biz key / creator
bytedcli bytebatch job list --psm demo.example.batch --region China-North --status fail
bytedcli bytebatch job list --psm demo.example.batch --region China-North --job-type demo_job_type
bytedcli bytebatch job list --psm demo.example.batch --region China-North --job-id 1234567890123456789
bytedcli bytebatch job list --psm demo.example.batch --region China-North --biz-key demo-key
bytedcli bytebatch job list --psm demo.example.batch --region China-North --creator demo.user

# JSON for automation (each job carries allowedOperations plus file URIs)
bytedcli -j bytebatch job list --psm demo.example.batch --region China-North --page-size 50
```

`--status` accepts `initial|scheduled|cancelled|starting_cron|processing|terminating|success|fail|terminated`.

There is no single-job endpoint; look one job up with `--job-id`.

**Counting semantics**: ByteBatch only reports `total_count` on some responses. When it does, JSON has `total: <n>` and the text summary says `Total`. When it does not, JSON has `total: null` plus `current_count` and `has_more`, and the summary says `This page`. Never treat `current_count` as a total.

The text table's `Files` column only marks which result files exist (`input,success,fail`). Use `-j` to read the full URIs.

## Files

```bash
# Upload a job input file; the printed File URI feeds `job create --input-file-uri`
bytedcli bytebatch file upload --psm demo.example.batch --region China-North --file ./demo-input.csv

# Download by the bare key from `file upload`, or by the full URL from `job list`
bytedcli bytebatch file download --uri 'demo-hash/China-North/input/1234567890123456789.csv'
bytedcli bytebatch file download --uri 'https://music-batch.bytedance.net/api/files/demo-hash/China-North/demo_success.csv' --output ./out.csv --force
```

ByteBatch reports file identifiers in two shapes and `file download --uri` accepts both:

- `file upload` returns a **bare key** like `demo-hash/China-North/input/1234567890123456789.csv` — this is what `job create --input-file-uri` expects. The command also prints the matching full **Download URL**.
- `job list` returns full HTTPS `/api/files/...` URLs, which may use a separate ByteBatch public-file origin.

Same-origin URLs use the selected site's authentication. A recognized ByteBatch public-file URL returned by `job list` is downloaded without JWTs, cookies, command-level headers, or redirects. Other origins and paths outside `/api/files/` are rejected.

Without `--output` the file is written to the current directory using the name from the URI. `--output` also accepts an existing directory. Existing files are never overwritten unless `--force` is passed, and the output directory must already exist.

## Creating jobs (write, requires `--yes`)

```bash
# Dry-run: prints the exact payload that would be POSTed, creates nothing
bytedcli bytebatch job create \
  --psm demo.example.batch \
  --region China-North \
  --cluster demo-cluster \
  --job-type demo_job_type \
  --name demo-backfill

# Submit an immediate job with an uploaded input file (bare key from `file upload`)
bytedcli bytebatch job create \
  --psm demo.example.batch \
  --region China-North \
  --cluster demo-cluster \
  --job-type demo_job_type \
  --name demo-backfill \
  --input-file-uri 'demo-hash/China-North/input/1234567890123456789.csv' \
  --extra-info '{"env":"demo"}' \
  --biz-key demo-key \
  --yes

# Submit a scheduled job
bytedcli bytebatch job create \
  --psm demo.example.batch \
  --region China-North \
  --cluster demo-cluster \
  --job-type demo_job_type \
  --name demo-nightly \
  --execution-type scheduled \
  --scheduled-start-time '2026-07-28 20:00:00' \
  --yes
```

- `--execution-type` accepts `immediate` (default) or `scheduled`. `scheduled` requires `--scheduled-start-time`; `immediate` rejects it.
- `--scheduled-start-time` takes a local time string with an explicit clock part (`'2026-07-28 20:00:00'`) or Unix seconds, and must be in the future. Date-only values are parsed as UTC midnight, so always include the time.
- `--input-file-uri`, `--extra-info` and `--biz-key` are optional; whether the job needs an input file depends on the job type's own implementation.

## Job operations (write, requires `--yes`)

```bash
# Dry-run
bytedcli bytebatch job execute \
  --job-id 1234567890123456789 \
  --psm demo.example.batch \
  --region China-North \
  --operation rerun

# Submit
bytedcli bytebatch job execute \
  --job-id 1234567890123456789 \
  --psm demo.example.batch \
  --region China-North \
  --operation terminate \
  --yes
```

`--operation` accepts `cancel|run|terminate|continue|retry|rerun`. Which ones are valid depends on the job's current state — read `allowedOperations` from `bytedcli -j bytebatch job list`.

## Troubleshooting

| Error code                           | Meaning / fix                                                                                                                                          |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BYTEBATCH_SSO_SESSION_REQUIRED`     | Legacy CAS fallback has no usable browser session. Refresh it with `auth login --session --auto`.                                                      |
| `BYTEBATCH_AUTH_REQUIRED`            | ByteBatch rejected the current JWT or legacy session. Re-login to the matching ByteCloud site, then run `bytebatch whoami`.                            |
| `BYTEBATCH_SESSION_BOOTSTRAP_FAILED` | The CAS exchange did not produce a site session cookie (SSO expired, or the login chain failed). Re-login and retry.                                   |
| `BYTEBATCH_API_ERROR`                | Backend rejected the request; the message carries ByteBatch's `status_code` and `log_id`.                                                              |
| `BYTEBATCH_INPUT_ERROR`              | Bad CLI input; the hint lists the accepted values or a copy-pasteable example.                                                                         |
| `BYTEBATCH_DOWNLOAD_ERROR`           | Download failed or returned an HTML page. Check the URI shape (upload → bare key, `job list` → full URL), then re-login.                               |
| `BYTEBATCH_RESPONSE_ERROR`           | ByteBatch answered with a non-object JSON body, or an upload succeeded without returning a file URI. Retry; if it persists the response shape changed. |
| `BYTEBATCH_SCHEMA_ERROR`             | The response no longer matches the expected schema — upgrade bytedcli, and report it if the newest version still fails.                                |
