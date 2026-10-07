---
name: bytedance-magibook
description: "Operate Magibook SQL queries, books, cells, prisms, workspaces, assets, and MagiTeam agent sessions through bytedcli. Use when a request mentions Magibook, MagiTeam, a Magibook/MagiTeam Prism, a Magibook book/cell, published-book inputs, agent-driven data analysis inside Magibook, or standalone Hive/ClickHouse/Doris SQL execution without another named platform, platform URL, or platform-specific resource ID."
---

# Magibook

Use the native `bytedcli magibook` domain. Prefer `--json` for automation and place it before the domain:

```bash
bytedcli --json magibook --region cn book list
```

## Authentication

The CLI chooses exactly one authentication channel in this order:

1. `MAGIBOOK_USR_TOKEN` as a bearer token.
2. `POD_USER_TOKEN` as a bearer token.
3. The CN ByteCloud user JWT from bytedcli as `X-Jwt-Token`.

Do not print, log, or return any of these token values. A Magibook pod normally has `POD_USER_TOKEN`, so no separate login is needed there. Otherwise, check or establish the CN login with:

```bash
bytedcli --site cn auth status
bytedcli --site cn auth login
```

When neither bearer token is available, every Magibook region falls back to the CN ByteCloud user JWT. `--region` selects the Magibook data/request host only; it does not select the JWT partition.

## Region

```bash
bytedcli --json magibook --region cn|va|sg|boe <group> <command> [options]
```

- A book and all of its cells exist in exactly one region.
- Region selection priority is `--region`, then `MAGIBOOK_REGION`, then `cn`.
- A wrong `--region` often returns an empty list or "not found" instead of an authentication error.
- If `book list`, `cell list`, or `book execute` cannot find the expected resource, retry with the book's actual region.
- Keep the same region on all later commands in one workflow, including execute, task status, cell get, and agent polling.
- On a production-network VA/SG host, set `BYTEDCLI_NETWORK_PROFILE=prod`. Office/corp-network calls omit it.
- `boe` requires `MAGIBOOK_CLI_OVERRIDE_HOST`. The override is rejected for `cn`, `va`, and `sg`, and accepts only a trusted ByteDance HTTPS origin or loopback HTTP origin. Set it only for the BOE command that needs it, then unset it.

## Command Map

All resource identifiers are named options. Use command help instead of guessing optional fields:

```bash
bytedcli magibook --help
bytedcli magibook book --help
bytedcli magibook cell create --help
```

### SQL

Use `bytedcli magibook sql execute` when the user asks to execute standalone Hive, ClickHouse, or Doris SQL without naming another SQL platform, platform URL, or platform-specific resource ID. If the user explicitly names Aeolus, Dorado, TQS, ByteHouse, Doris Ops, or a resource from one of those platforms, preserve that platform's existing route instead of switching to Magibook.

```bash
bytedcli --json magibook --region cn sql get --sql-uuid <uuid>
bytedcli --json magibook --region cn sql update --sql-uuid <uuid> --title <title>
bytedcli --json magibook --region cn sql history list --sql-uuid <uuid> [--limit 20]
bytedcli --json magibook --region cn sql execute (--sql <text> | --file <path>) [--engine hive|clickhouse|doris] [--title <title>] [--prism-uuid <uuid>] [--query-region <region>] [--queue <queue>] [--cluster <cluster>] [--rows 100] [--timeout 600] [--no-wait]
bytedcli --json magibook --region cn sql rerun --sql-uuid <uuid> [--variables-json <json> | --variables-file <path>] [--queue <queue>] [--rows 100] [--timeout 600] [--no-wait]
bytedcli --json magibook --region cn sql status --sql-uuid <uuid> --history-id <id>
bytedcli --json magibook --region cn sql result --sql-uuid <uuid> --history-id <id> [--rows 100]
bytedcli --json magibook --region cn sql cancel --sql-uuid <uuid> --history-id <id>
```

`sql execute` creates and preserves one Magibook SQL asset and one initial History. Submit it once. By default, the command polls every 2 seconds until `success`, `failed`, or `cancelled`, and fetches a result preview after success. `--no-wait` returns immediately. `--timeout` limits only the local wait; timeout or Ctrl-C does not cancel or resubmit the query. Always preserve `prism_uuid`, `sql_uuid`, `history_id`, `url`, and `status_command` so the same History can be resumed.

- `sql get` returns the current SQL text and persisted configuration. `sql update` changes only the persisted title; the server trims it and accepts 1 through 256 characters. `sql history list` returns the newest histories first and accepts `--limit` from 1 through 200, defaulting to 20.
- `sql execute`, `sql get`, and `sql update` may also return `embed_url`, a file-scoped embedded link that identifies no execution. See [Embedded URLs](#embedded-urls).
- `sql rerun` executes the existing asset as one new History without changing its persisted SQL or configuration. Submit it once. It uses the same polling, result preview, timeout, Ctrl-C, rate-limit, and resume behavior as `sql execute`.
- Rerun variables are optional, but when supplied they must be the complete JSON array shaped as `[{"key":"name","value":["start","end"]}]`; `--variables-json` and `--variables-file` are mutually exclusive. These variables apply only to the new History.
- Rerun `--queue` is a runtime-only override for Hive assets. It does not update the asset, and it is rejected for ClickHouse or Doris assets.
- `--engine` defaults to `hive`. Hive alone accepts `--queue`; Doris requires `--cluster`; ClickHouse accepts neither flag.
- Without `--prism-uuid`, the service creates or reuses the caller's default "Magibook OAPI SQL" Prism. When it is provided, the query is created in that Prism.
- Prefer `--file` for SQL containing literal shell-style templates such as `${date}` or `${date-1}` so the shell cannot expand them before bytedcli reads the query. If inline SQL is unavoidable, use expansion-safe single-quoted shell input and escape any embedded single quotes correctly; never place template SQL in double quotes.
- `--rows` defaults to 100 and accepts 1 through 1000. The preview contains column headers. This command does not download full results; open the returned `url` to reach the SQL file in Magibook and inspect the complete result there. Both `url` and `embed_url` are file-scoped, so neither opens one specific run — see [Embedded URLs](#embedded-urls).
- Hive supports cancel. ClickHouse and Doris report `supported: false` with reason `engine_cancel_unavailable`; do not simulate cancellation.
- A `failed` or `cancelled` query returns a non-success CLI status with the same identifiers and exact follow-up status command. A local timeout returns a resumable controlled result instead.
- During `sql execute` or `sql rerun` waiting, status/result reads retry only the explicit business rate-limit code `magibook/podOAPI/rateLimitExceed`, at most 3 retries per read with jittered 2–3, 4–6, and 8–12 second delays. All polling, result reads, and backoff share the post-submit `--timeout` budget and stop on Ctrl-C; same-account CLIs share the backend quota.
- If a post-submit request fails or rate-limit retries are exhausted, the command exits nonzero with `MAGIBOOK_SQL_WAIT_FAILED` or `MAGIBOOK_SQL_RESULT_FAILED`. `data` and `error.details` preserve the identifiers, URL, last known SQL `status`, and `status_command`; `data.wait_status` is `error`. This is a waiting/result-fetch failure, not evidence that the SQL failed. Resume that History with `status_command`, then `sql result` after success; never resubmit `sql execute` to recover. Timeout remains a controlled `wait_status: timeout` result (exit 0), and Ctrl-C returns `wait_status: interrupted` (exit 130).
- `--region` chooses the Magibook deployment. `--query-region` chooses the SQL engine region; keep the two meanings distinct.

### Books

```bash
bytedcli --json magibook --region cn book list [--workspace-uuid <uuid>] [--mine] [--page 1] [--page-size 20]
bytedcli --json magibook --region cn book url get --book-uuid <uuid>
bytedcli --json magibook --region cn book create --title <title> [--workspace-uuid <uuid>] [--prism-uuid <uuid>] [--description <text>]
bytedcli --json magibook --region cn book copy --book-uuid <uuid> [--title <title>] [--from-published] [--lifetime-hours <n>]
bytedcli --json magibook --region cn book publish --book-uuid <uuid> --run-as BOOK_OWNER|BOOK_RUNNER
bytedcli --json magibook --region cn book schedule --book-uuid <uuid> --action enable|disable [--cron <expression>]
bytedcli --json magibook --region cn book execute --book-uuid <uuid> [--latest-publication]
bytedcli --json magibook --region cn book snippet execute --book-uuid <uuid> (--snippet <code> | --file <path>) [--timeout-ms <milliseconds>]
bytedcli --json magibook --region cn book variable update --book-uuid <uuid> --key <name> (--value <text> | --value-json <json>)
```

`book execute` normally returns a `batch_task_id`. When it is non-null, poll it with `cell task status --task-id <id>`. When it is null, do not poll; inspect the returned payload and book state instead.

Before publishing, determine the execution identity with the user and always pass `--run-as`: `BOOK_OWNER` runs a publication with the owner's permissions, while `BOOK_RUNNER` uses each runner's permissions.

To run the latest publication with input-cell values, add `--latest-publication` and repeat any input option as needed:

```bash
bytedcli --json magibook --region cn book execute \
  --book-uuid <uuid> \
  --latest-publication \
  --input product_id=12345 \
  --input-json quantity=42 \
  --input-cell-json <cell_uuid>='["US","JP"]'
```

- `--input` and `--input-json` address an input cell by variable name.
- `--input-cell` and `--input-cell-json` address it by cell UUID.
- Use the JSON variants for numbers, booleans, arrays, objects, dates, and date ranges.
- `--inputs-file` accepts either an input array or `{ "inputs": [...] }`.
- Input values are only valid with `--latest-publication`.

`book variable update` changes only an existing draft variable value. Use `--value` for text/date values and `--value-json '["2026-09-01","2026-09-02"]'` for ranges such as `${date}`.

### Cells

```bash
bytedcli --json magibook --region cn cell list --book-uuid <uuid>
bytedcli --json magibook --region cn cell get --cell-id <id> [--show-output]
bytedcli --json magibook --region cn cell search --book-uuid <uuid> --pattern <regex> [--ignore-case]
bytedcli --json magibook --region cn cell create --book-uuid <uuid> --cell-type <type> [--title <title>] [--content <text> | --content-file <path>]
bytedcli --json magibook --region cn cell link --book-uuid <uuid> --url <url> [--title <title>]
bytedcli --json magibook --region cn cell update --cell-id <id> --old <text> --new <text> [--replace-all]
bytedcli --json magibook --region cn cell update --cell-id <id> --title <title>
bytedcli --json magibook --region cn cell move --cell-id <id> --target-cell-id <id> --position before|after
bytedcli --json magibook --region cn cell delete --cell-id <id>
bytedcli --json magibook --region cn cell execute --book-uuid <uuid> --cell-id <id> [--cell-id <id> ...]
bytedcli --json magibook --region cn cell task status --task-id <id>
bytedcli --json magibook --region cn cell download --cell-id <id> --output <path>
```

Cell types are `python`, `sql_hive`, `sql_clickhouse`, `sql_dataframe`, `markdown`, and `dynamic_text`. Prefer `--content-file`, `--old-file`, and `--new-file` for multiline content. An empty `--old ''` performs a full replacement.

`cell get --show-output` is a bounded preview. When `is_truncated` is true, use `cell download` for the complete result. SQL/vquery results download as CSV; Python multipart results download as ZIP. `view` and `edit` remain hidden migration aliases for standalone CLI users; new instructions should use `get` and `update`.

`cell execute` follows the same asynchronous task flow as `book execute`: if it returns a non-null `batch_task_id`, poll `cell task status` until `status` is `success` or `failed`. A null ID with `No runnable cells` is a successful no-op; report the message and do not poll or retry.

### Prisms and Workspaces

```bash
bytedcli --json magibook --region cn prism list [--workspace-uuid <uuid>] [--source self|mine|shared|workspace|all] [--keyword <text>]
bytedcli --json magibook --region cn prism create --title <title> [--workspace-uuid <uuid>] [--description <text>]
bytedcli --json magibook --region cn prism book list --prism-uuid <uuid>
bytedcli --json magibook --region cn workspace create --name <name> [--description <text>]
bytedcli --json magibook --region cn workspace grant --workspace-uuid <uuid> --user <origin-id> [--role admin|write|read]
```

The hierarchy is workspace, prism, then book. An agent session must belong to a prism. `workspace grant` is a permission mutation and must target the exact workspace, user origin ID, and role requested by the user.

Prism source scopes are distinct: `self` returns all prisms in the selected workspace, `mine` only prisms created by the caller, `shared` prisms shared with the caller, and `workspace` other readable workspace prisms. `all` is a deprecated API alias for `self`; use `self` in new workflows.

### Assets

```bash
bytedcli --json magibook --region cn asset upload --scope-uuid <uuid> --file <path> [--scope prism|workspace] [--name <name>]
bytedcli --json magibook --region cn asset list --scope-uuid <uuid> [--scope prism|workspace] [--keyword <text>]
bytedcli --json magibook --region cn asset download --asset-uuid <uuid> --output <path>
bytedcli --json magibook --region cn asset delete --asset-uuid <uuid>
```

Asset preprocessing is asynchronous. After upload, poll `asset list` until `preprocess_status` is `success`, `failed`, `timeout`, or `not_supported` before relying on the asset as agent context.

### Agent

```bash
bytedcli --json magibook --region cn agent session create --prism-uuid <uuid> [--no-all-assets]
bytedcli --json magibook --region cn agent session send --session-uuid <uuid> --prompt <text> [--no-web-search] [--language auto|zh|en]
bytedcli --json magibook --region cn agent session status --session-uuid <uuid>
bytedcli --json magibook --region cn agent session get --session-uuid <uuid>
bytedcli --json magibook --region cn agent session cancel --session-uuid <uuid>
```

`agent session send` is asynchronous. Create a fresh session unless the user explicitly asks to continue an existing one, submit one prompt, poll status until completion, then fetch the result.

Creating a session selects every asset visible in the prism, including parent-workspace assets, unless `--no-all-assets` is passed. Sending a prompt enables web search unless `--no-web-search` is passed. Confirm both scopes with the user; when broader asset access or web search was not requested, pass the corresponding `--no-*` flag.

For book/cell tasks, asset preprocessing, and agent sessions, poll no faster than every 3 seconds and stop after 10 minutes unless the user chose another deadline. Stop early on the terminal state reported by the command (`success`/`failed` for tasks; `success`/`failed`/`timeout`/`not_supported` for assets; `is_complete=true` for agents). On timeout, report that work is still pending and return the exact status command so polling can resume; do not report success or resubmit the operation.

## Write Safety

- Treat an explicit user request as authorization for that exact mutation. Otherwise confirm the region, target resource, and payload before `create`, `copy`, `publish`, `schedule`, `link`, `update`, `move`, `delete`, `grant`, `upload`, `execute`, `send`, or `cancel`.
- Submit each mutation once. If a timeout or network error leaves the result unknown, inspect the resource or task/session status before retrying; never blindly duplicate a write or prompt.
- `cell create`, `cell update`, and `book snippet execute` (including existing hidden aliases) accept `--allow-high-risk`. Omit it by default; use it only after the user explicitly authorizes the reported high-risk scopes. The initial operation request is not that authorization. Follow the CLI error's review instructions before submitting a new request.
- Download commands require a new destination path and refuse to overwrite an existing file.

## Compatibility

For standalone Magibook CLI migration, the paths `book run`, `book snippet-run`, `cell view`, `cell edit`, `cell run`, `cell task-status`, `prism books`, and the flat `agent` actions are accepted as hidden aliases. New workflows must use the primary commands shown above.

## Output

With `--json`, bytedcli returns the standard `{status,data,error,context}` envelope. Read business payloads from `data`. Preserve IDs and region from each response for later commands. Errors include a Magibook code and hint when available.

## Embedded URLs

Some responses carry an `embed_url` alongside the ordinary `url`. They serve different presentation targets:

- Use `embed_url` when a Feishu document, acceptance report, or another host needs to render the Magibook resource inline.
- Use `url` to open the complete Magibook page.
- When you provide an `embed_url` and the same response also contains `url`, preserve both values and label their purposes. Do not substitute one for the other.

Commands that can return `embed_url`:

- `sql execute`, `sql get`, `sql update`.
- `book create`, `book copy`, `book url get`, `book publish`, `book list`, `prism book list`.
- `cell create`, `cell link`, `cell list`, `cell search`, `cell get`, `cell get --show-output`, `cell update`.

Rules for consuming it:

- Pass through `url` and `embed_url` exactly as returned. Never assemble either link from a workspace, prism, book, cell, SQL, or history identifier.
- Do not make an extra request solely to obtain a link. A missing `embed_url` means that resource exposes no embedded link, which is a normal outcome. Say so plainly, preserve any returned `url`, and do not retry, publish, execute, submit, create, or call `sql get` just to recover the missing field.
- Some resources genuinely have no project route and therefore no `embed_url`; a Book with `prism_uuid: null` is the usual case. In a list response, some items can have the field while others do not.
- For list commands, the field appears per item, so read it from the item rather than the list wrapper.
- `embed_url` grants no permission beyond the ordinary URL, and generating one creates no publication, execution, or share token.
- A Book's `embed_url` opens the **draft** (`editMode=edit`) everywhere except `book publish`, which returns the published link (`editMode=online`) for the version it just created. Draft links stay behind the review permission gate: a colleague holding only read permission cannot open one and is redirected or denied. So when the link will be read by anyone other than the Book's editors — embedding it in a shared doc, a dashboard, or a wiki page — the draft link is the wrong one. Check `editMode` in the value you received, and when it says `edit`, tell the user the link only works for people who can review the draft, and that a published link requires `book publish` (a real publication — never run it just to obtain a link).

### Acceptance report workflow

Execute each acceptance query once and consume the links from that same response:

```bash
bytedcli --json magibook --region cn sql execute \
  --file ./acceptance.sql \
  --title demo-acceptance
```

1. Preserve `sql_uuid`, `history_id`, and `status_command` for the execution record. Only derive an acceptance conclusion from `data.columns` and `data.rows` when `data.status` is `success` and `data.has_result_set` is true. Check `data.truncated`: when it is true, label the preview as incomplete and use the returned `data.url` to inspect the complete result in Magibook; when no preview is available, do not claim a result conclusion or resubmit the query.
2. If `data.embed_url` is present, use that exact value to create the inline Magibook embed below the corresponding conclusion in the Feishu document or acceptance report.
3. If the same response contains `data.url`, retain it next to the embed and label it **Open the complete Magibook page**.
4. If `data.embed_url` is absent, state that no embedded link is available and retain any returned `data.url`. Do not derive a link, issue `sql get`, or rerun the query just to obtain one.

For example, `sql execute` can return both file-scoped links in its normal result. This excerpt shows the link and resume fields; preview fields and the standard `context` are omitted:

```json
{
  "status": "success",
  "data": {
    "prism_uuid": "demo-prism-uuid",
    "sql_uuid": "demo-sql-uuid",
    "history_id": 12345,
    "engine": "hive",
    "status": "success",
    "url": "https://magibook.example/w/demo-workspace/p/demo-prism/ide/sql/demo-sql-uuid",
    "embed_url": "https://magibook.example/w/demo-workspace/p/demo-prism/ide/sql/demo-sql-uuid?feature=%7B%22embedded%22%3Atrue%7D",
    "status_command": "bytedcli --json magibook --region cn sql status --sql-uuid demo-sql-uuid --history-id 12345"
  },
  "error": null
}
```

An independent `sql get` for an existing SQL asset can return the same pair. This excerpt omits unrelated persisted configuration fields and the standard `context`; it does not imply that `sql get` should be called after `sql execute` merely to obtain a link:

```json
{
  "status": "success",
  "data": {
    "prism_uuid": "demo-prism-uuid",
    "sql_uuid": "demo-sql-uuid",
    "title": "demo-acceptance",
    "sql": "SELECT 1",
    "engine": "hive",
    "url": "https://magibook.example/w/demo-workspace/p/demo-prism/ide/sql/demo-sql-uuid",
    "embed_url": "https://magibook.example/w/demo-workspace/p/demo-prism/ide/sql/demo-sql-uuid?feature=%7B%22embedded%22%3Atrue%7D"
  },
  "error": null
}
```

For SQL, `embed_url` addresses the SQL **file**, not one execution: it carries no history ID. `sql execute` reports the file link for the asset it just created, and `sql get` reports it for an existing asset. Because `sql execute` waits by default and finishes by reporting a result, that file link stays on its final output too — it still identifies the file, not that run. Invoked on their own, `sql rerun`, `sql status`, `sql result`, `sql history list`, and `sql cancel` report no embedded link.

**There is no link to a single SQL execution.** The ordinary `url` is file-scoped as well — it differs from `embed_url` only by the embedded flag, and neither carries a history ID. So never hand either one over as the entry point for a particular run, not even labelled with its `history_id`; opening it shows the file, not that execution. To report one run, give its `sql_uuid` and `history_id` and read it back with `sql result --sql-uuid <uuid> --history-id <id>`, which is also what `status_command` in the payload already spells out.
