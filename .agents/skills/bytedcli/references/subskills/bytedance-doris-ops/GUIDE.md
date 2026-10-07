---
name: bytedance-doris-ops
description: "Run SQL directly through Doris Ops, or list Doris Ops clusters, when a task provides a known Doris cluster id (SG or CN), needs to discover cluster ids, or explicitly requests the Doris Ops backend. Do not use for DataLeap asset/schema/lineage or managed DorisTable DDL, an existing Aeolus datasource, or an existing Dorado carrier task."
---

# bytedcli Doris Ops

Use `bytedcli doris-ops query run` to execute SQL on a specified Doris cluster, and `bytedcli doris-ops cluster list` to discover the numeric cluster ids visible to you. Both commands support two regions: `sg` (SG Doris Ops, `i18n-tt` auth) and `cn` (`data.bytedance.net`, `cn` auth); `sg` is the default. The CLI exchanges the region's ByteCloud JWT for a Titan Passport Cookie automatically; do not scrape browser cookies or hand-copy tokens.

## When to use

- The user supplies a Doris cluster id and SQL to execute.
- The user knows only a cluster name/namespace and needs its numeric id: use `doris-ops cluster list` to look it up.
- SQL for that known cluster comes from a local `.sql` file.
- An agent or script needs structured columns and rows directly from Doris Ops for that cluster.
- The task explicitly needs the Doris Ops query path without browser-cookie dependencies.

For DataLeap asset discovery, schema, lineage, partitions, managed DorisTable creation, or managed DorisTable metadata changes, use `bytedance-hive`. For ByteHouse cluster discovery or ByteHouse SQL, use `bytedance-bytehouse`.

This command complements, rather than replaces, the existing Doris-capable workflows:

- If the caller already has an Aeolus Query Editor datasource id/name, use `bytedance-aeolus` with `--engine datasource`.
- If the caller already has a Dorado carrier task id and needs ad-hoc execution in that task context, use `bytedance-dorado` with `--engine-type doris_sql`.
- Use this skill when the stable selector is the Doris cluster id and the desired backend is Doris Ops. Do not create an Aeolus datasource or a Dorado task merely to call this command.
- Use `bytedance-hive` for DataLeap-managed DorisTable DDL or metadata operations. Only use this direct command for DDL/DML when the user explicitly asks to execute it through Doris Ops and confirms the target and write impact.

## Prerequisites

- Use the common invocation guidance in `../../invocation.md`.
- If the region login is missing or expired, run `bytedcli --site <sg|cn> auth login` once (`i18n-tt` for `sg`, `cn` for `cn`). The `DORIS_OPS_AUTH_REQUIRED` error reports the exact `auth_command` for the region you used.
- Do not run `auth login --session` for these commands. Doris authentication does not read a browser Cookie.

## Quick start

```bash
# Run inline SQL. sg is the default region; pass --region cn for CN Doris Ops.
bytedcli doris-ops query run --region sg --cluster-id 1001 --sql "SELECT 1"
bytedcli doris-ops query run --region cn --cluster-id 90 --sql "SELECT 1"

# Discover cluster ids by name/namespace before querying.
bytedcli --json doris-ops cluster list --region cn --query "leads" --limit 20

# Stable JSON for agents and scripts. Global --json goes before the domain.
bytedcli --json doris-ops query run --cluster-id 1001 --sql "SELECT * FROM demo_db.sample_table LIMIT 10"

# Read SQL from a file and return at most 20 rows in the command output.
bytedcli --json doris-ops query run --cluster-id 1001 --file ./query.sql --rows 20
```

## Commands

### `doris-ops query run`

```bash
bytedcli doris-ops query run --cluster-id <id> (--sql <sql> | --file <path>) [--region sg|cn] [--rows <n>] [--yes]
```

- `--cluster-id <id>`: required positive Doris cluster id. There is no implicit project or cluster default. Use `doris-ops cluster list` if you only know the cluster name.
- `--sql <sql>`: inline SQL.
- `--file <path>`: read SQL from a regular local file of at most 1 MiB; use exactly one of `--sql` and `--file`.
- `--region <sg|cn>`: endpoint region; defaults to `sg`. `sg` targets SG Doris Ops (`i18n-tt` auth); `cn` targets `data.bytedance.net` (`cn` auth).
- `--rows <n>`: truncate rows emitted by the command. Structured output keeps the total in `row_count` and flags a cut result with `truncated: true` and `rows_limit`. `--rows 0` returns the columns and `row_count` with no rows, which is a cheap way to probe the shape and size of a result first.
- `--yes`: confirm SQL that is not one single clearly read-only `SELECT`, `SHOW`, `DESC`, or `DESCRIBE` statement. Comments, dollar-quoted strings, mode-dependent escapes, CTEs, multiple statements, DDL, and DML are treated as ambiguous and rejected without it. `SELECT ... INTO OUTFILE`, `SELECT ... INTO DUMPFILE`, and `SELECT ... FOR UPDATE` are treated as writes despite starting with `SELECT`.
- `--json`: global option for structured output; place it before `doris-ops`.

### `doris-ops cluster list`

```bash
bytedcli doris-ops cluster list [--region sg|cn] [--query <text>] [--limit <n>]
```

- `--region <sg|cn>`: endpoint region; defaults to `sg`.
- `--query <text>`: case-insensitive substring filter over cluster name, PSM, description, and id. Omit it to list every cluster the region returns.
- `--limit <n>`: cap the clusters printed/emitted after filtering. Structured output keeps `total_count`, `matched_count`, `returned_count`, and flags a cut result with `truncated: true`. `--limit 0` returns counts with no cluster rows.
- Each returned cluster includes at least `id` (the numeric id `query run` needs), `name`, `region`, and `owner`.

## Authentication

The commands use this non-browser flow:

1. Obtain a ByteCloud JWT for the region's site (`i18n-tt` for `sg`, `cn` for `cn`).
2. Exchange it for a Titan Passport id.
3. Send that id as the Doris Ops request Cookie.
4. On the exact Doris authentication-failed response, force-refresh the exchange once and retry once.

Users do not need to pass global `--site` to these commands; `--region` selects the Doris endpoint and the CLI fixes the corresponding auth site internally. If login is required, follow the returned `auth_command` (`bytedcli --site i18n-tt auth login` for `sg`, `bytedcli --site cn auth login` for `cn`).

## Agent guidance

- Never guess a cluster id and never assume a project-specific cluster. Ask for `--cluster-id`, or resolve it with `doris-ops cluster list`, when it is unavailable.
- Never interpolate user-provided or dynamic SQL into a shell command: backticks, `$()`, quotes, and expansions may execute before bytedcli starts. Pass an argv array without a shell, or write the exact SQL through a structured file API to a regular `.sql` file and use `--file`.
- Prefer `--json` for automation. Preserve `columns`, row order, and total/returned row counts when summarizing results.
- `--rows` limits only emitted rows; it does not change the SQL or add a server-side `LIMIT`.
- Do not route DataLeap-managed DorisTable creation or metadata changes here; use `bytedance-hive`.
- For direct Doris Ops DDL/DML, require an explicit user request and confirm the target database, table, statement, and write impact before adding `--yes`. Never add `--yes` merely to bypass conservative classification.
- `DORIS_OPS_AUTH_REQUIRED`: run the reported `auth_command`, then retry once. Do not switch to browser-cookie extraction.
- `DORIS_OPS_WRITE_CONFIRMATION_REQUIRED`: the SQL is not one single clearly read-only statement. Show the user the exact SQL and target cluster and obtain explicit approval before retrying with `--yes`. Never add `--yes` merely to silence this error.
- `CLI_ARGS_MISSING` / `CLI_ARGS_INVALID` / `CLI_PARSE_ERROR`: generic CLI codes for a missing `--cluster-id`, for passing both `--sql` and `--file`, and for a non-integer option value.
- `DORIS_OPS_INPUT_ERROR`: domain-level input validation, such as empty SQL or a negative `--rows`.
- `DORIS_OPS_FILE_ERROR`: `--file` is not a regular file, exceeds 1 MiB, changed while being read, or is unreadable.
- `DORIS_OPS_HTTP_ERROR`: non-2xx transport failure; report the status and request id.
- `DORIS_OPS_RESPONSE_TOO_LARGE` / `DORIS_OPS_RESPONSE_TIMEOUT` / `DORIS_OPS_RESPONSE_READ_ERROR`: the response exceeded 64 MiB, timed out, or failed mid-read. Narrow the SQL or retry once; report the status and request id if it persists.
- `DORIS_OPS_EMPTY_RESPONSE`: retry once; if it persists, report the HTTP status and request id returned by the CLI.
- `DORIS_OPS_API_ERROR`: inspect the business error and report the request id or log id when present; do not expose cookies or JWTs.
- `DORIS_OPS_INVALID_RESPONSE`: upgrade bytedcli and retry; if it persists, report the response shape without credentials or row data that the user did not ask to share.

## References

- `../../invocation.md`
- `../../troubleshooting.md` for generic CLI errors only. Its multi-site selection advice does not apply to these commands: Doris auth is fixed per region (`sg`→`i18n-tt`, `cn`→`cn`), and the commands do not inherit global `--site`.
