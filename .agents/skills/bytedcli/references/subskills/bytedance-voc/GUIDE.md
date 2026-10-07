---
name: bytedance-voc
description: "Operate ByteDance VOC (cem.bytedance.net / voc.bytedance.net) — the Douyin CEM user-feedback platform — via bytedcli. Use when tasks mention voc, cem_doubao, 抖音 voc, 用户反馈详情, feedback get, feedback_id, voiceShareId, cem 反馈, voc.bytedance.net, voc auth login, or pasting a `https://voc.bytedance.net/cem/d/<project>/voice/...` URL."
---

# bytedcli VOC

VOC CLI wraps the private `voc.bytedance.net/apin/*` FGW gateway. It is the first ByteDance CLI integration with the CEM user-feedback platform; the platform itself does not yet publish an OpenAPI.

## When to use

- Pull feedback detail(s) by feedback id, share id, or VOC console URL.
- Search VOC feedback-source rows by period, app key, business domain, and origin label ids.
- Render the title, body, channel, sentiment, and three-level issue label for a feedback record.
- Check or refresh the local 6-hour cookie cache.

## Commands

```bash
# Fetch a feedback detail by feedback id (default project: cem_doubao)
bytedcli voc feedback get --id 1234567890

# Fetch feedbacks from a VOC share id
bytedcli voc feedback get --id demoShareA

# Fetch by VOC console URL (auto-resolves project + id from the path)
bytedcli voc feedback get --url "https://voc.bytedance.net/cem/d/<project>/voice/detail/feedback/1234567890"

# Fetch by VOC analysis share URL (resolves voiceShareId, then feedback ids)
bytedcli voc feedback get --url "https://voc.bytedance.net/cem/d/<project>/voice/analysis?voiceShareId=demoShareA"

# Other projects
bytedcli voc feedback get --id 1234567890 --project <project>

# Pull specific client-context columns (CSV or repeatable --column)
bytedcli voc feedback get --id 1234567890 --columns app_version,device_model_general,os_version,network_type
bytedcli voc feedback get --id 1234567890 --column app_version --column channel

# Pull every known client-context column in one shot
bytedcli voc feedback get --id 1234567890 --all-fields

# JSON for agents (passes through eredar_* keys, plus issue_codes_parsed, issue_paths, and share metadata when applicable)
bytedcli --json voc feedback get --id 1234567890

# JSON + full client context (e.g. read app_version straight off the object)
bytedcli --json voc feedback get --id 1234567890 --all-fields

# Search recent feedback-source rows (defaults to the recent 7 days)
bytedcli voc feedback search --busi-domain sample-domain --app-key sample_app_key --range 7d

# Search with origin label ids (repeatable or comma-separated)
bytedcli voc feedback search --busi-domain sample-domain --app-key sample_app_key --origin-label-id 223124 --origin-label-id 223125,223126 --range 7d

# JSON output for downstream analysis / clustering
bytedcli --json voc feedback search --busi-domain sample-domain --app-key sample_app_key --start 2026-07-23 --end 2026-07-30 --page-size 50

# Inspect the local 6h session cache (read-only, no browser launch)
bytedcli voc auth status
bytedcli --json voc auth status
```

## Feedback source search (`voc feedback search`)

`voc feedback search` wraps the VOC console's `FeedbackSource` endpoint and reuses the same Chromium-cookie + FGW auth chain as the detail commands. It is the right entry when the question is "最近 7 天某个 app 主要集中在哪些问题" rather than "看某一条 feedback 的详情".

- Required filters:
  - `--busi-domain <domain>` — business domain, e.g. `sample-domain`
  - `--app-key <appKey>` — target app, e.g. `sample_app_key`
- Time window:
  - `--range <duration>` — relative window; defaults to `7d`
  - `--start <time>` / `--end <time>` — explicit boundaries; accepts date-only, RFC3339, epoch ms, or relative offsets
- Label filter:
  - `--origin-label-id <id>` — repeatable or comma-separated; maps to `origin_label_ids`
- Pagination:
  - `--page` (default `1`)
  - `--page-size` (default `40`)

JSON mode returns a stable contract:

- `busi_domain`, `app_key`, `origin_label_ids`
- `period.{start_ms,end_ms}`
- `page`, `page_size`, `total`, `current_count`
- `word2_splits`
- `items[]` — parsed `FeedbackSource` rows with stable fields like `feedbackId`, `eredarCreateTimestampMs`, `contentTitle`, `issueNames`, `labelNames`, `appVersion`, `osVersion`, plus `raw`

Text mode prints the selected filters plus a compact paged table (`Time / Feedback ID / Version / OS / Issue / Title`) for quick triage.

## Client-context columns (`--columns` / `--all-fields`)

By default `voc feedback get` returns the lightweight list view (title, body, channel, sentiment, issue label, `uid`/`did`). The VOC console's "case detail" panel pulls a richer set from a different route of the same endpoint (`searchType: 1`, which returns a single `detail` object pinned by `eredar_primary_key`). The CLI exposes that route on demand:

- `--columns a,b,c` (CSV, repeatable) or `--column a --column b` — request specific extra columns.
- `--all-fields` — request the full known column set. Mutually exclusive with `--columns`/`--column`.
- Unknown column names fail fast with an error listing the allowed columns (nothing is silently dropped).

In JSON mode the requested columns are surfaced as flat top-level keys on each feedback object (e.g. `data.feedback.app_version`). In text mode they render as a `客户端上下文` block under the feedback body. Empty backend values are normalised to `null`.

**Columns this endpoint actually provides** (non-exhaustive, most useful for triage): `app_version`, `device_model_general` (the device model — note the `_general` suffix), `os_version`, `device_os_general`, `network_type`, `platform`, `channel`, `channel_type`, `app_key`, `app_name`, `aid`, `did`, `uid`, `ip_info`, `city`, `province`, `extra_params` (a JSON string). A large `pc_*` / `owls_*` set also exists but is empty for app feedback.

### Agent Guidance

- For feedback triage that needs `app_version`, run `bytedcli --json voc feedback get --id <id> --all-fields` (or `--columns app_version,device_model_general,os_version,network_type`) instead of asking the user to paste it from the browser.
- **This endpoint does NOT serve `alog_url`/`alog_download_url`, `task_id`/`call_id`/`room_id`, `client_trace_id`/`logid`, or Libra/AB exposure (`ab_groups`/`experiment_group`).** Those live in other systems — do not expect `--all-fields` to surface them. For ALog/Argos/experiment data, drive the dedicated `feedback-*` skills off `device_id`/`user_id`/timestamp rather than VOC.
- `--all-fields` costs one extra request (the base lookup resolves `eredar_primary_key`, then the full-detail route fetches context). For a single known field, `--columns <name>` is just as cheap.

## Viewing Attachments

In JSON output, `image_list` and `video_list` are JSON-encoded arrays of TOS object keys, not directly viewable URLs. Use `voc feedback download-attachment` to download each attachment into a local directory in one shot (the signed CDN URL is short-lived and not usable on its own):

```bash
# Download every image attached to a feedback into a per-feedback temp directory
bytedcli voc feedback download-attachment --id 1234567890

# Same, but write into a chosen directory (created if missing)
bytedcli voc feedback download-attachment --id 1234567890 --out-dir ./voc-attachments

# Download a feedback's videos instead of its images
bytedcli voc feedback download-attachment --id 1234567890 --type video

# Download specific TOS keys directly (no feedback lookup needed)
bytedcli voc feedback download-attachment \
  --uri tos-cn-i-example/sample-image-key \
  --uri tos-cn-i-example/another-image-key

# JSON for agents — each entry has `uri`, `url` (signed CDN), and `saved_to` (local file)
bytedcli --json voc feedback download-attachment --id 1234567890 --out-dir /tmp/voc
```

`--type image` (default) scans `image_list` and falls back to `.jpg` when the URL has no extension; `--type video` scans `video_list` and falls back to `.mp4`. When `--out-dir` is omitted, files land under `${os.tmpdir()}/voc-attachments-<feedbackId|timestamp>/`.

## Authentication

- Cookies are extracted from the local Chromium cookie store (Chrome / Chrome Beta / Chromium / Vivaldi) — `voc.bytedance.net` host-scoped cookies + `.bytedance.net` apex-scoped SSO cookies. Extraction runs automatically on the first VOC call when no fresh cache is available.
- A 6-hour local cache at `~/.local/share/bytedcli/data/voc_session.json` avoids re-decrypting on every call. To force a fresh extraction before the TTL expires, delete that file (the path is printed by `bytedcli voc auth status`).
- The user must be signed into `https://voc.bytedance.net` in Chrome first; the SSO session itself can be established via `bytedcli auth login --session` if it has not been established yet.
- Fixed gateway headers are injected automatically: most VOC endpoints use `x-fgw-app: cem`; `voc feedback search` switches to `x-fgw-app: voc` via `vocPostJson(..., { fgwApp: "voc" })`. `x-fgw-embed-cmw: 1`, `Origin/Referer`, and a modern Chrome UA are always attached so the kani middleware accepts the request.

## Error hints

- `VOC_AUTH_REQUIRED` — user has not signed into VOC in Chrome. Tell them to open https://voc.bytedance.net (running `bytedcli auth login --session` first if there is no SSO session) and then rerun the VOC command.
- `VOC_KANI_FORBIDDEN` — the account lacks the `cem_<project>_overall` kani role. The error payload includes a direct link to the kani application portal.
- `VOC_SHARE_EMPTY` — the share id or URL did not resolve to feedback ids.
- `VOC_NOT_FOUND` — the feedback id or resolved share feedback ids do not exist in the given project (verify the URL or `--project` value).

## Out of scope (first version)

- Label trees, anomaly subscriptions, and write operations are not exposed.
- Only `cem_doubao` is tested as the default project; arbitrary project strings are accepted but not validated.
