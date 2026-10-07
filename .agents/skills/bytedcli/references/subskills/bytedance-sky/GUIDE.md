---
name: bytedance-sky
description: "Use when users ask about Sky marketing coupons, direct-discount coupon batches, or a coupon batch whitelist / allow-list (营销批次白名单) on sky-myp.byteintl.net. Read the current whitelist and add or delete members through bytedcli instead of opening the Sky admin console."
---

# Sky Marketing Coupon Whitelist

Use `bytedcli sky marketing-coupon whitelist` to manage the allow-list (whitelist) of a Sky marketing coupon batch. `get` reads the current members; `add` and `delete` change membership.

The Sky backend `UpdateBatchControlInfo` **overwrites** the entire `allow_list` rather than appending, so `add` / `delete` are implemented as read-modify-write: the CLI reads the current whitelist, applies your change in memory, and writes back the full member set (preserving other `batch_control_info` fields). You do not need to pass the existing members.

## Auth

Sky uses the browser site session on `sky-myp.byteintl.net`, not a JWT flag. bytedcli reads Chromium cookies for that host (plus the `bytedance.com` apex for BD SSO). Sign in to the Sky admin console in Chrome once, then retry the CLI. If the session cookie is missing the command fails fast with `SKY_AUTH_REQUIRED`.

The operator identity written with each change (`updater_name` / `updater_email`) is taken from the logged-in user; there is no flag to override it.

## Commands

```bash
bytedcli sky marketing-coupon whitelist get --batch-id demo-batch-id
bytedcli --json sky marketing-coupon whitelist get --batch-id demo-batch-id
bytedcli sky marketing-coupon whitelist add --batch-id demo-batch-id --members demo-uid
bytedcli sky marketing-coupon whitelist add --batch-id demo-batch-id --members demo-uid,demo-uid-2 --yes
bytedcli sky marketing-coupon whitelist delete --batch-id demo-batch-id --members demo-uid --yes
```

`--members` is comma-separated. `add` / `delete` preview the computed diff by default (dry-run) and only submit the overwrite when you pass `--yes`.

## Result handling

- `get` JSON returns `marketing_batch_id`, `allow_list` (array), and `count`. Text mode prints the batch id, member count, and the members.
- `add` / `delete` JSON returns `marketing_batch_id`, `action`, `applied`, `dry_run`, `before`, `after`, `added`, `removed`, `noop`, and `changed`. Without `--yes`, `dry_run` is true and `applied` is false — nothing is written.
- `noop` lists requested members that had no effect (already present for `add`, already absent for `delete`). When `changed` is false the whitelist already satisfies the request and no write happens even with `--yes`.
- Use placeholder values such as `demo-batch-id` and `demo-uid` in examples; do not copy real batch ids, uids, or cookies from browser curls.

## Agent Guidance

- Always pass `--batch-id`. Find it on the direct-discount coupon list/detail page (the id in the batch detail URL).
- To change a whitelist, do not read-then-overwrite manually: just run `add` / `delete` with the members to change — the CLI handles the read-modify-write and preserves other members.
- Run without `--yes` first to preview `before` / `after`, then re-run with `--yes` to apply.

## References

- Read `../../invocation.md` for installation, global options, and JSON invocation rules.
- Read `../../troubleshooting.md` when authentication, network access, or command execution fails.
