# Maya invocation

## Authentication and site

Maya uses the ByteDance SSO browser session even though its API host is under `tiktok-row.net`.
Always refresh that session explicitly through the CN site:

```bash
bytedcli --site cn auth login --session
```

The `maya` command itself resolves the fixed Maya API endpoint. Do not switch it to `i18n-tt`, `eu-ttp`, or another cloud site based on the API hostname.

## JSON output

Put the global `--json` flag before the command:

```bash
bytedcli --json maya dashboard get --dashboard-id demo-dashboard-id
```

For `chart get`, inspect `applied_filters` before interpreting the returned rows. It reports whether country and date filters came from the saved dashboard or a CLI override, and whether they were resolved.

## Read-only boundary

The Maya commands only read dashboard configuration and query chart data. They do not save or publish dashboard changes.
