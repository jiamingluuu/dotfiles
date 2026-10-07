---
name: bytedance-quality-data
description: Use bytedcli obric quality-data commands to query Quality Data feedback records. Invoke for Quality Data feedback lists, feedback details, or search-condition metadata.
---

# bytedcli obric quality-data

Use this subskill for Quality Data feedback queries.

## Commands

```bash
bytedcli obric quality-data list --business ocean --page 1 --page-size 20
bytedcli obric quality-data get --business ocean --id <feedback_id>
bytedcli obric quality-data search-condition get --business ocean
```

Put global options before `obric`:

```bash
bytedcli --json obric quality-data list --business ocean
```

## Authentication

The CLI uses `BYTEDCLI_QUALITY_DATA_TOKEN` when set. Otherwise it reuses a cached token or
silently acquires one from existing CN SSO and Feishu web sessions.

If those shared sessions are unavailable, run:

```bash
bytedcli auth login --session --feishu
```

Quality Data commands never start a QR flow themselves.

## Options

- `--business` is required and accepts `ocean`, `dora`, or `dorag`.
- `list` supports `--page`, `--page-size`, `--id`, and an optional JSON object in `--body`.
- `get` requires `--id`.
- `search-condition get` accepts an optional JSON object in `--body`.

Use `bytedcli --json obric quality-data ...` for structured output.
