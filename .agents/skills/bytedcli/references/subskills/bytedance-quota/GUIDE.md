---
name: bytedance-quota
description: "Use bytedcli quota to query and manage ByteQuota storage quota. Trigger when users mention ByteQuota quota items, quota checks, quota requests or transfers, or storage quota bypasses."
---

# ByteQuota

Use `bytedcli quota` to query and manage ByteQuota storage quota through the direct control-plane endpoint for CN or BOE. Commands return stable public DTOs and keep ByteQuota's internal transfer protocol out of the CLI contract.

Scope is CN storage quota only. It excludes compute and every `resource_pool` workflow. BOE is reserved for pre-release validation; overseas sites return `UNSUPPORTED_SITE_CAPABILITY`.

## Commands

- `bytedcli quota meta capability get`: Get supported ByteQuota capabilities for the selected site.

- `bytedcli quota meta platform list`: List storage quota platforms.

- `bytedcli quota meta sales-area list`: List storage quota sales areas.

- `bytedcli quota meta flavor list`: List storage quota flavors.

- `bytedcli quota get`: Get one quota item.

- `bytedcli quota list`: List quota items.

- `bytedcli quota operation get`: Get one quota operation.

- `bytedcli quota operation list`: List quota operations.

- `bytedcli quota request`: Request quota from the direct parent business.

- `bytedcli quota borrow`: Borrow quota between businesses.

- `bytedcli quota allocate`: Allocate quota from a parent to a direct child business.

- `bytedcli quota reclaim`: Reclaim quota from a direct child business.

- `bytedcli quota check`: Check quota for a planned resource request.

- `bytedcli quota bypass get`: Get one quota bypass.

- `bytedcli quota bypass list`: List quota bypasses.

- `bytedcli quota bypass monthly create`: Create a monthly quota bypass.

- `bytedcli quota bypass urgent create`: Create an urgent quota bypass.

## References

- [Command guide](references/quota.md)
- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)

## Safety

- Read and preview commands do not create quota operations or bypass records.
- Mutations default to preview. Add `--yes` only after the user approves the exact preview.
- `--force` is available only for bypass creation, requires `--yes`, and never overrides authorization, ambiguous business resolution, or unsupported site capability.
- Do not retry writes automatically. Preserve the operation or bypass ID returned by a successful submission and query it before considering another submission.
