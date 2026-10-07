---
name: bytedance-logifier
description: "Retrieve and query Logifier logs with bytedcli. Use when the user explicitly mentions Logifier, asks to retrieve logs by business line and device ID, provides a Logifier batch, or supplies Logifier DSL. Do not use for ordinary PSM, LogID, instance, Pod, or Footprint log queries; use bytedance-log for those."
---

# bytedcli Logifier

Use `bytedcli logifier` to create a Logifier retrieval task from a business line and device ID, then inspect the resulting batch and query its logs with the platform's DSL. It does not upload local logs, edit batches, or download raw archives.

## When to use

- The user explicitly says `Logifier` or asks for a Logifier batch.
- The user asks to retrieve logs and provides, or can provide, a business line and device ID.
- The user has a Logifier `batch_id` and wants batch metadata or filtered logs.
- The user provides a Logifier DSL expression.

Do not route ordinary PSM, LogID, instance, Pod, or Footprint logs here. Those remain `bytedcli log ...`.

## Authentication

Logifier reuses the current bytedcli CN user login. The user signs in through the standard QR-code flow; do not ask for a JWT, Cookie, browser data, or a long-lived token.

```bash
bytedcli --site cn auth status
bytedcli --site cn auth login
```

When a Logifier command returns `LOGIFIER_AUTH_REQUIRED`, complete the login and retry the same read-only command.

## Commands

```bash
# Inspect batch metadata first
bytedcli --json logifier batch get --batch-id sample-batch-001

# Preview a retrieval. This reads the business-line defaults but creates nothing.
bytedcli --json logifier retrieval create \
  --party coze \
  --device-id demo-device-001 \
  --range 4h

# Create and wait for the retrieval task.
bytedcli --json logifier retrieval create \
  --party coze \
  --device-id demo-device-001 \
  --range 4h \
  --yes \
  --wait

# Create, wait, then query the completed batch automatically.
bytedcli --json logifier retrieval create \
  --party coze \
  --device-id demo-device-001 \
  --range 4h \
  --yes \
  --query 'error || exception' \
  --page-size 100

# Query one batch with Logifier DSL
bytedcli --json logifier batch query \
  --batch-id sample-batch-001 \
  --query 'error || exception' \
  --page-size 100

# Query the latest logs without a DSL filter
bytedcli --json logifier batch query --batch-id sample-batch-001 --reverse --page-size 100

# Continue from a returned nextIndex
bytedcli --json logifier batch query \
  --batch-id sample-batch-001 \
  --query 'logid:sample-logid' \
  --start-index 100 \
  --page-size 100

# Query a batch hosted on the Logifier endpoint returned by retrieval
bytedcli --json logifier batch query \
  --batch-id sample-batch-001 \
  --api-base-url https://logifier-example.bytedance.net/v2/ \
  --query 'error'
```

`--query` is optional: omit it to query all logs in the batch. `--page-size` accepts 1 through 1000 and defaults to 100. With `--reverse`, an omitted `--start-index` starts from the newest log; otherwise it starts from index 0. The JSON result has `logs`, `nextIndex`, `pageSize`, and `truncated`; when `truncated` is true, continue with `--start-index <nextIndex>` or narrow the query. A just-finished retrieval can need a few seconds before its batch index is readable: bytedcli retries short timeout and temporary server failures automatically. If it still returns `LOGIFIER_BATCH_NOT_READY`, wait briefly and rerun the same batch query.

`retrieval create` requires a Logifier business line (`--party`), a device ID, and a time range. Ask the user only for missing inputs. `--range` defaults to `4h`; alternatively use `--start` and `--end`. It is a write action: without `--yes`, bytedcli only displays the dynamic defaults and the final request preview. `--wait` waits for completion; `--query` implies waiting and automatically queries the completed batch. Use `retrieval get --task-id <id>` to inspect a task later, or `retrieval wait --task-id <id>` to continue waiting without creating another task.

The default API endpoint is the online Logifier service. Pass `--api-base-url` only when a completed retrieval gives another Logifier endpoint. bytedcli accepts only approved HTTPS Logifier hosts and never sends the user JWT to an arbitrary URL.

## References

- [Command invocation](../../invocation.md)
- [Authentication](references/authentication.md)
- [Errors](references/errors.md)
