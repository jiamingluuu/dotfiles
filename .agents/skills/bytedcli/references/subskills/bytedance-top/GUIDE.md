---
name: bytedance-top
description: "Use for TOP platform workflows under 资源管理、新热挖掘、合集管理、榜单管理、热榜入库、批量导入、数据提取、批量操作 or 系列管理, including queries, staged imports, extraction, batch jobs, and dry-run guarded series mutations."
---

# ByteDance TOP

Use `bytedcli top` for TOP's resource and operations workflows. The menu-to-command mapping is:

| TOP menu | bytedcli command |
| -------- | ---------------- |
| 资源管理 | `top entity`     |
| 新热挖掘 | `top discovery`  |
| 合集管理 | `top album`      |
| 榜单管理 | `top ranking`    |
| 热榜入库 | `top warehouse`  |
| 批量导入 | `top import`     |
| 数据提取 | `top extract`    |
| 批量操作 | `top batch`      |
| 系列管理 | `top series`     |

## Authentication

TOP reuses the CN ByteDance SSO browser session and exchanges it for a short-lived TOP JWT in memory. If authentication fails, run:

```bash
bytedcli --site cn auth login --session --auto
```

Do not copy TOP JWTs, cookies, or browser callback URLs into commands, files, logs, or prompts.

## Query entities

Search by title or content, then narrow with semantic filters when needed:

```bash
bytedcli --json top entity list --keyword demo-title --page-size 20
bytedcli --json top entity list --entity-type web-novel --visibility all-app
bytedcli --json top entity list --ids 1000000000000000001
bytedcli --json top entity get --id 1000000000000000001
```

`entity list` supports repeatable or comma-separated `--ids`, `--entity-type`, `--visibility`, `--author`, `--actor`, and `--alias` filters. Use `--exact` only when TOP exact-search semantics match the request; do not silently replace a broad search with exact search.

Entity IDs are opaque decimal strings. Preserve every digit and never convert them through a JavaScript number, spreadsheet numeric cell, or scientific notation.

## Query albums

Albums correspond to 全网实体 → 合集管理:

```bash
bytedcli --json top album list --keyword demo-collection
bytedcli --json top album list --album-type short-drama --binding bound --direction vertical
bytedcli --json top album list --entity-type web-short-drama --video-visibility all-app
bytedcli --json top album get --id 2000000000000000001
```

Use `--created-start` / `--created-end` for album creation time and `--bound-start` / `--bound-end` for entity binding time. Time values accept RFC3339, `YYYY-MM-DD`, Unix timestamps, and relative values:

```bash
bytedcli --json top album list --created-start '7d ago' --binding bound
```

Album list results expose `boundEntityId` without issuing an extra entity lookup for every row. If the user needs the bound entity details, pass that ID explicitly to `top entity get`.

Album direction values are `horizontal`, `vertical`, and `unknown`; `unknown` is a valid legacy value returned by TOP, not a parse failure.

## Query rankings

List the primary/sub-ranking configuration first, then use its complete ranking ID to inspect configured entities:

```bash
bytedcli --json top ranking list --rank-type tv-series --status online
bytedcli --json top ranking list --keyword demo-rank
bytedcli --json top ranking get --id 3000000000000000001
bytedcli --json top ranking entry list --ranking-id 3000000000000000001 --rank-status on-rank
bytedcli --json top ranking entry list --ranking-id 3000000000000000001 --year 2026 --category-id 101
```

`ranking list` uses semantic primary types such as `general`, `novel`, `movie`, `tv-series`, and `short-drama`, plus semantic statuses `offline`, `pending`, and `online`. `ranking entry list` accepts `all`, `on-rank`, or `off-rank`; the returned entry itself may also report `waiting` or `down-rank`.

TOP ignores offset/count when an entry filter is active and returns the filtered set from offset zero. bytedcli paginates that response client-side. Check `truncated`; if it is `true`, narrow `--keyword`, `--year`, `--category-id`, or `--rank-status` before relying on later pages.

## Query new-hot discovery and warehouse candidates

Use discovery types instead of TOP's internal numeric entity/gender codes:

```bash
bytedcli --json top discovery list --type movie --page-size 20
bytedcli --json top discovery list --type novel-female --page-size 50
```

`discovery list` exposes related entity and album IDs, source platforms, scores, new-item state, and intervention count when present.

Use warehouse for 热榜入库 candidates. Filters use semantic supply and publish-status values:

```bash
bytedcli --json top warehouse list --entity-type movie --supply-type ranking-discovery
bytedcli --json top warehouse list --entity-type web-novel --status success,exists
bytedcli --json top warehouse list --entity-type web-short-drama --authority-covered yes --album-covered no
```

Run `bytedcli top warehouse list --help` for the complete status/source vocabulary. Do not pass the backend's numeric status codes.

## Stage and execute batch imports

Topic/post import is a recoverable, two-stage workflow:

```bash
bytedcli --json top import file list --import-type topic
bytedcli --json top import upload --file ./sample-import.xlsx --import-type topic
bytedcli --json top import upload --file ./sample-import.xlsx --import-type topic --yes
bytedcli --json top import item list --file-id sample-file --import-type topic
bytedcli --json top import execute --file-id sample-file --import-type topic
bytedcli --json top import execute --file-id sample-file --import-type topic --yes
```

`upload` and `execute` are dry-run by default. Review the upload payload and every staged item before repeating with `--yes`. Execution imports all staged items and is asynchronous; poll `top import item list` to distinguish `not-confirmed`, `importing`, and `imported`. The upstream file and item queries return complete arrays without server pagination parameters, so bytedcli applies `--page` and `--page-size` after loading the response.

## Extract structured data

Query existing server-side transcoding data without starting a capture:

```bash
bytedcli --json top extract url execute --url https://example.com/sample-content --type movie-detail
bytedcli --json top extract m3u8 get --url https://example.com/sample-playlist.m3u8
```

For capture, choose the source and update behavior explicitly:

```bash
bytedcli --json top extract url execute --url https://example.com/sample-content --type novel-detail --source capture
bytedcli --json top extract url execute --url https://example.com/sample-content --type novel-detail --source both --update incremental --yes
```

`--source server` is read-only. `capture` and `both` keep the capture portion as a dry-run unless `--yes` is present; with `both`, the existing server result is still queried during the preview. Page types are `novel-detail`, `novel-chapter`, `movie-detail`, and `movie-play`.

## Run dynamically configured batch operations

Always discover the current action and template first because the platform controls this list remotely:

```bash
bytedcli --json top batch type list
bytedcli --json top batch type list --keyword resource
bytedcli --json top batch submit --operation SaveSampleResource --sheet-url https://example.com/sample-sheet --user-email demo@example.com
bytedcli --json top batch submit --operation SaveSampleResource --sheet-url https://example.com/sample-sheet --user-email demo@example.com --yes
bytedcli --json top batch execution list --operation SaveSampleResource --user-email demo@example.com
```

Pass the exact `action` returned by `batch type list`. `submit` dynamically resolves that action and previews the payload by default; `--yes` starts an asynchronous operation. A successful submit means accepted, not completed, so query `batch execution list` for the result URL or error state.

## Manage series

List or inspect series with semantic types/statuses:

```bash
bytedcli --json top series list --keyword demo-series --type seasonal --status enabled
bytedcli --json top series get --id 3000000000000000001
```

Create, update, delete, and bind/unbind operations are dry-run guarded:

```bash
bytedcli --json top series create --name demo-series --type seasonal --children-json '[{"resource_id":"1000000000000000001","rank":1,"tab":"season-one"}]'
bytedcli --json top series update --id 3000000000000000001 --name demo-series --type seasonal --status enabled --yes
bytedcli --json top series binding update --series-id 3000000000000000001 --action bind --children-json '[{"resource_id":"1000000000000000001"}]' --operator demo-operator --reason sample-reason
bytedcli --json top series delete --id 3000000000000000001 --operator demo-operator --reason sample-reason
```

`--children-json` accepts an array of objects with a decimal-string `resource_id` and optional positive `rank` and non-empty `tab`. Omitted ranks are assigned from 1 in input order. Review the exact payload, then add `--yes` only when the requested series mutation is confirmed.

## Output guidance

- Put the global `--json` option before `top` for agent or script consumption.
- List results include `total`, `page`, `page_size`, and `has_more`.
- Ranking entry results also include `truncated` to expose incomplete filtered result sets.
- Unknown enum names should be corrected from `--help`; do not pass TOP's internal numeric codes.
- Write-capable commands return `dry_run: true` unless `--yes` is explicit. A dry-run may perform read-only preflight calls, such as loading staged import items or resolving dynamic batch types, but it must not call a write endpoint.
- Entity, album, ranking, discovery, warehouse, import file/item list, batch type/execution, series list/get, extract server query, and m3u8 lookup are read-only.

## Troubleshooting

- `TOP_AUTH_REQUIRED`: run the CN session login command above, then retry.
- Broad entity search timeout: narrow the filters or retry with `--exact` only when exact matching is acceptable.
- Not found: verify that the complete decimal ID was copied without rounding.
- Unknown batch action: rerun `bytedcli --json top batch type list`; the remote operation catalog may have changed.
- Async import/batch result missing: query the corresponding item/execution command rather than treating submit acceptance as completion.
- Permission failure: confirm the signed-in user can open the same TOP view; do not substitute another user's credentials.
