---
name: bytedance-app-info
description: "Use bytedcli app-info for AppInfo application metadata queries. Trigger when users mention AppInfo, App ID, application code, Chinese name or alias, account group, product line, Android/iPhone/iPad package name, or application search, detail, or batch lookup."
---

# AppInfo

Use `bytedcli app-info` for AppInfo application metadata queries.

## Commands

- `bytedcli app-info search`: List applications without a filter. Pagination defaults to `--page 1 --page-size 20`.
- `bytedcli app-info search --keyword <value>`: Automatically identify the input by App ID, application code, Android/iPhone/iPad package, then Chinese name or alias. Results are merged and de-duplicated by App ID.
- `bytedcli app-info search --keyword <value> --by <dimension>`: Search one explicit dimension. Supported dimensions are `app-id` (unique App ID), `code` (application identifier), `cn-name` (Chinese name or alias), `account-group-id`, `product-line-id`, `android-package`, `iphone-package`, and `ipad-package`.
- `bytedcli app-info get --app-id <app-id>`: Get one application by its unique App ID.
- `bytedcli app-info batch-get --app-id <app-id>...`: Batch get applications by App ID. Repeat `--app-id` or pass comma-separated IDs. The CLI uses independent detail requests with a concurrency limit of 10 and returns per-input `input`, `ok`, `item`, and `error`.

## References

- [Command guide](references/app-info.md)
- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
