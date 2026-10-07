---
name: bytedance-dataeyes
description: "Dataeyes data validation and authorization ticket capabilities via bytedcli. Invoke when tasks mention Dataeyes validation, task validation, data tests, project configuration, validation reports, authorization tickets, or ask to get, create, or update a DB-owner authorization ticket."
---

# bytedance-dataeyes

Dataeyes data validation testing capabilities. Refer to the [Dataeyes documentation](https://cloud.tiktok-row.net/docs/product/dataeyes?from=cloud&cdc_fallback=1&region=Singapore-Central&x-bc-region-id=bytedance) for details.

## Commands

### Project Management

- `bytedcli dataeyes project list`: List current-user Dataeyes projects; add `--all` and optional `--keyword <keyword>` to inspect all visible projects.
- `bytedcli dataeyes project get`: Get basic or detailed info about a project.
- `bytedcli dataeyes project create`: Create a new Dataeyes project.
- `bytedcli dataeyes project update-config`: Update a Dataeyes project (supports any API-accepted fields, including QPS shortcuts).
- `bytedcli dataeyes project update-validation-config`: Update validationConfig for a project.

### Authorization Tickets

- `bytedcli dataeyes ticket get`: Get an authorization ticket and its current status.
- `bytedcli dataeyes ticket create --project-id <id> --db-index <index>`: Create a fresh DB-owner ticket after the project has no existing ticket association. The command runs a permission-check preflight, defaults to dry-run, and requires `--yes` to submit.
- `bytedcli dataeyes ticket create --from-ticket-id <id>`: Create a new DB-owner ticket from an existing ticket whose status is `Canceled` or `Rejected`. The command defaults to dry-run and requires `--yes` to submit.
- `bytedcli dataeyes ticket update --ticket-id <id> --status canceled`: Set a pending DB-owner ticket to `Canceled`. The command defaults to dry-run and requires `--yes` to submit.

### Validation & Tasks

- `bytedcli dataeyes validation start`: Start a validation task for a project.
- `bytedcli dataeyes validation list`: List validation tasks associated with a project.
- `bytedcli dataeyes validation get-report`: Get the validation report of a completed task.
- `bytedcli dataeyes task create`: Create tasks (use --validation for small-traffic validation, --fix/--simulate-fix for formal tasks).
- `bytedcli dataeyes task get`: Get detailed info of a task.
- `bytedcli dataeyes task pause`: Pause a running task.
- `bytedcli dataeyes task continue`: Continue a paused task.
- `bytedcli dataeyes task kill`: Kill a running task.
- `bytedcli dataeyes task post-fix`: Continue processing inconsistent data for an existing compare task (UI: "继续处理不一致数据"; supports `--simulate-fix` / `--fix`; dry-run by default, `--yes` to submit).
- `bytedcli dataeyes task export-difflog`: Export the inconsistent-data diff log for a finished compare task to a file (UI: "导出不一致数据"; dry-run by default, `--yes` to trigger).
- `bytedcli dataeyes workflow start`: Start a fix pipeline for a compare task (UI: "发起修复流水线"; takes `--config-file`; dry-run by default, `--yes` to submit).
- `bytedcli dataeyes workflow get`: Get fix pipeline workflow detail (steps, status, config) by `--workflow-id`.
- `bytedcli dataeyes workflow stop`: Stop a running fix pipeline (dry-run by default, `--yes` to submit).

## Agent Guidance

- Read the ticket before any status update or ticket-derived creation. Use `ticket update --status canceled` only for a pending DB-owner authorization ticket; after submission, read the same ticket until its status is `Canceled` before creating from it.
- Use `ticket create --from-ticket-id` only when the source DB-owner ticket is `Canceled` or `Rejected`. After submission, read the returned new ticket ID and confirm that it is pending; do not assume the source ticket ID was reused.
- Ticket-derived creation continues the existing internal ticket chain and does not refresh its DB-owner snapshot. When the owner snapshot is stale, ask DataEyes Oncall to reset/unlink the project ticket association; verify the TaskStart permission check no longer returns `dbOwnerTicketInfo`, then use the fresh `ticket create --project-id ... --db-index ...` form.
- Run `ticket update` and both `ticket create` forms without `--yes` first to inspect the dry-run plan. Add `--yes` only after the target scope, current status, and operator authority have been verified.
- For fresh creation, never submit while the dry-run reports `ready=false`; the command only writes from an explicit `permissionCheckResult=NotPass` plus `initiateStatus=CanInitiate`, and refuses writes while any existing `dbOwnerTicketInfo` remains, including tickets in `Canceled` or `Rejected` status.

## References

- [dataeyes.md](./references/dataeyes.md)
- [invocation.md](./../../invocation.md)
- [troubleshooting.md](./../../troubleshooting.md)
