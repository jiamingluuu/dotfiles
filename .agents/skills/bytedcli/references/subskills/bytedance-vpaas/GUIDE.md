---
name: bytedance-vpaas
description: "Operate VPAAS billing push batch detail queries through bytedcli. Use when users mention VPAAS 推量、计费推量、billing push、batchId、批次失败明细、ChargeItemCode invalid/empty/未生效/预算计费项，or need to query CN/BOE/MYA/SG/VA push batch summary and failed records with attribution."
author: yangyang.36
---

# bytedcli VPAAS

## When to use

Use this skill when the user needs to inspect VPAAS billing push batches or diagnose push failures from a batch ID. Typical requests include querying failed batch details, comparing batch summary counts, checking `ChargeItemCode` errors, or validating VPAAS push tasks across CN/BOE/MYA/SG/VA.

## Command

The VPAAS query command is implemented as a native bytedcli command under `src/api/vpaas`, `src/cli/commands/vpaas`, and `src/cli/handlers/vpaas`. The command tree follows the standard resource + verb shape:

```bash
bytedcli vpaas batch get  --batch-id <batch_id> --psm <psm> --region <region> [--start <YYYY-MM-DD>] [--end <YYYY-MM-DD>]
bytedcli vpaas batch list --psm <psm> --region <region> [--batch-id <batch_id>] [--status <status>] [--page <n>] [--page-size <n>] [--start <YYYY-MM-DD>] [--end <YYYY-MM-DD>]
```

Supported `--region` values (VPAAS data-center region; independent from the global ByteCloud `--site`):

- `cn`
- `boe`
- `mya`
- `sg`
- `va`

`--psm` is required — the DevSRE consul proxy target PSM is intentionally not shipped as a hardcoded default. Pass it via `--psm <psm>` or set the environment variable `BYTEDCLI_VPAAS_PSM=<psm>`.

`--consul-tags` overrides the DevSRE proxy consul tags (`x-devsre-proxy-consul-tags`). CN, MYA, and SG use their verified console routing by default. BOE and VA remain unset unless you pass `--consul-tags` or set `BYTEDCLI_VPAAS_CONSUL_TAGS`.

Useful examples (note: `--json` is a **global** flag and must appear before the subcommand):

```bash
bytedcli vpaas batch get --batch-id <batch_id> --psm <psm> --region cn
bytedcli --json vpaas batch get --batch-id <batch_id> --psm <psm> --region cn
bytedcli vpaas batch list --psm <psm> --region sg --page 1 --page-size 100
bytedcli --json vpaas batch list --batch-id <batch_id> --psm <psm> --region cn --status failed --page 1 --page-size 20
```

## Output interpretation

`vpaas batch get` (text mode) prints a single key-value summary line for the batch (total/success/failed + summary fields like Status/Product/MeasureCategory/BillingDate).

`vpaas batch list` (text mode) prints a paged table of detail rows. The key row fields are `BatchID`, `Status`, `Product`, `Measure`, `Value`, `Instance`, `Customer`, `errorCode`, `errorMsg`, and `归因`.

If the list command prints `No records found`, there are no matching rows for the selected filters.

If `--json` is used:

- `batch get` returns `{ summary, summaryCounts }`
- `batch list` returns `{ rows, page, pageSize, total, warnings }`

## Attribution labels

The plugin maps common backend errors to operator-facing causes:

- `ChargeItemCode is invalid` → `计费项配置无效`
- `ChargeItemCode is empty` → `计费项为空`
- `budget charge item` / `预算计费项` → `预算计费项不允许推量`
- `ChargeItemCode not activated` / `未生效` → `计费项未生效`
- `RequestInvalid` + `InvalidParameter` → `请求参数无效`
- Other messages → `未知错误`

## Region notes

The verified plugin configuration is documented in [invocation.md](../../invocation.md). If an environment request fails with service discovery, ROW gateway, or no endpoint errors, first compare the environment config against that reference before changing code.

For MYA queries, use the global `--site i18n-tt` to obtain the VPAAS gateway JWT while keeping `--region mya` for backend routing. Using `--site i18n-bd` currently returns HTTP 401.

## Safety

This command is read-only. It must not trigger reruns, state changes, notifications, or any production write operation.
