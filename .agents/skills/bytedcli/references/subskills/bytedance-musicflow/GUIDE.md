---
name: bytedance-musicflow
description: "Use when finding MusicFlow workflows, definitions, batches, operators, or executions, inspecting failures, or retrying one execution through bytedcli."
---

# MusicFlow resource queries and execution retry

Use `bytedcli musicflow` to inspect workflows, their ASL definitions, batches, operators, and execution records through the Dashboard BFF.

## Authentication and sites

Use global `--site cn`, `--site i18n-tt`, or `--site boe`. Authentication uses your ByteCloud user JWT; the Dashboard must have JWT support deployed. Unsupported sites fail without falling back to CN. For a CN PPE deployment, add `--lane ppe_<name>` to the MusicFlow leaf command; this sends `x-tt-env` and `x-use-ppe` only to the Dashboard request.

## Commands

- `workflow list [--search <text>] [--owner <user>] [--status init|running|stopped]`: find business workflows.
- `workflow get --id <id>`: inspect one business workflow and its bound definition ID.
- `workflow definition list --workflow-id <id>`: list definitions belonging to a business workflow.
- `workflow definition get --id <id>`: inspect a definition, including its ASL.
- `batch list [--name <name>] [--owner <user>] [--workflow-id <id>] [--status running|stopped]`: find batches before listing executions.
- `batch get --id <id>`: inspect one batch and its configuration.
- `operator list [--search <text>] [--owner <user>]` and `operator get --id <id>`: inspect operator definitions.
- `execution get --id <id>`: inspect one execution, including status, error information and available definition/RDM details.
- `execution retry --id <id>`: preview a single execution retry; add `--yes` to submit with Kani admin permission. Add `--force` to pass Broker ForceRetry; it still previews without `--yes`. Deploy the matching BFF first.
- `execution list --batch-id <id>`: query one page of executions in a known batch. Optional filters: `--status init|running|success|failed`, `--business-key <key>`.
- Add `--start` and `--end` together for a creation-time window, inclusive start and exclusive end. Use ISO timestamps with a timezone and whole seconds (fractional seconds are rejected); the window must be at most 31 days. `--error-like` uses a SQL LIKE pattern (% = any sequence, \_ = one character), requires this window and accepts 1-512 UTF-8 bytes. Matching case sensitivity follows the selected database.

```bash
bytedcli --site boe auth login
bytedcli --site cn -j musicflow workflow list --lane ppe_music_test
bytedcli --site boe -j musicflow workflow list --search demo
bytedcli --site boe -j musicflow workflow definition list --workflow-id 1234567890123456789
bytedcli --site boe -j musicflow workflow definition get --id 1234567890123456791
bytedcli --site boe -j musicflow batch list --workflow-id 1234567890123456789
bytedcli --site boe -j musicflow operator get --id 1234567890123456792
bytedcli --site boe -j musicflow execution get --id 1234567890123456789
bytedcli --site boe -j musicflow execution retry --id 1234567890123456789
# Submit only after the user has authorized retrying this execution.
bytedcli --site boe -j musicflow execution retry --id 1234567890123456789 --yes
bytedcli --site boe -j musicflow execution list --batch-id 1234567890123456790 --status failed --page 1 --page-size 20
bytedcli --site boe -j musicflow execution list --batch-id 1234567890123456790 --business-key demo-key
bytedcli --site boe -j musicflow execution list --batch-id 1234567890123456790 --status failed --start '2026-01-01T00:00:00+08:00' --end '2026-01-02T00:00:00+08:00' --error-like '%timeout%'
```

## Interpreting results

- `status_name` distinguishes `init`, `running`, `success`, `failed`; only success and failed have `is_terminal: true`. Unknown states have `status_name: unknown` and `is_terminal: null`.
- `error_info` is preserved when present. An Init or Running execution is not a successful execution.
- Status/business-key filters are sent to the server before pagination. Lists require a batch ID and never scan all batches.
- Default page size is 20, maximum 100. The backend permits at most 100 pages. `has_more` indicates remaining records; `next_page` is null at the limit, with `page_limit_reached: true` and a hint to narrow filters. One page is not a complete export. An empty later page does not prove the batch has no failures.
- IDs remain decimal strings. Preserve full precision.
- Resource lists return one page with `total`, `has_more`, and `next_page`; use `--page` and `--page-size` (1–100). A page is not a full export.
- Workflow, definition, batch and operator reads require the corresponding Kani read permission. The Dashboard BFF must have JWT access for these exact routes deployed.
- HTTP 200 with `success: false` is a query error, not an empty result.
- Time/error filters run on the server before both counting and pagination. Deploy the matching Manager and BFF first; a missing filter acknowledgement is an error, never an unfiltered fallback.
- Retry completion is not execution success. The Broker may return without retrying a non-failed execution; a stopped batch prevents retry. Check state with `execution get` afterward. No transport retry on timeout/5xx; inspect state before resubmitting after an ambiguous failure.
- Retry preview and submission share `dry_run`, `force`, `lane`, `execution_id`, `method`, `endpoint`, `query`, `result` and `hint`. Preview returns `result: null`; submission puts the BFF response in `result`. List `hint` is null unless the page limit requires narrowing filters.
- ForceRetry retains Broker eligibility checks: successful executions are still skipped, stopped batches are rejected, and non-failed executions must be at least two hours old. It uses the Broker force retry-count ceiling instead of the batch ceiling; it is not unlimited retry.
- Workflow/batch/operator management and node-specific retry are not exposed.

## References

- [Invocation](../../invocation.md): read for CLI setup, authentication, global site selection and JSON invocation. MusicFlow supports only the three sites listed above.
- [Troubleshooting](../../troubleshooting.md): read when authentication, invocation or response handling fails.
