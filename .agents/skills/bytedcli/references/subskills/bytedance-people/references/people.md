# People Commands

People commands are grouped under `people` and backed by People web APIs on `people.bytedance.net`.
Authentication reuses the Feishu Web session saved by `bytedcli auth login --session --feishu`.

## Contents

- [`people approval status`](#people-approval-status)
- [`people approval list`](#people-approval-list)
- [`people approval category list`](#people-approval-category-list)
- [`people approval flow list`](#people-approval-flow-list)
- [`people overview get`](#people-overview-get)
- [`people shortcut list`](#people-shortcut-list)
- [`people app list`](#people-app-list)
- [`people calendar workday get`](#people-calendar-workday-get)
- [`people leave list`](#people-leave-list)
- [`people leave apply`](#people-leave-apply)

## people approval status

Read approval dashboard counts for the current account.

```bash
bytedcli people approval status
bytedcli --json people approval status
```

Text output shows pending, finished, CC, and applied counts. JSON output returns `approval_status` with `pending_count`, `finished_count`, `cc_count`, and `applicant_count`. The command is read-only and does not perform approval actions.

## people approval list

List approval instances visible to the current account.

```bash
bytedcli people approval list
bytedcli people approval list --status finished --category-ids 1,52
bytedcli people approval list --keyword "sample keyword" --page-size 20
bytedcli people approval list --status finished --page-token sample-page-token
bytedcli --json people approval list --status pending
```

Options:

- `--status <status>`: `pending`, `finished`, `cc`, `applicant`, or `other`; defaults to `pending`.
- `--keyword <keyword>`: search approval names and summaries.
- `--category-ids <ids>`: comma-separated positive category IDs.
- `--flow-id <id>`: exact approval flow ID.
- `--page-size <n>`: backend page size from `1` to `100`; defaults to `20`.
- `--page-token <token>`: opaque token returned by the previous page.

Text output shows the process ID, approval name, normalized process status, initiator, summary, relevant timestamp, and urged flag. JSON output returns `approvals`, `current_count`, `page_size`, `has_more`, `next_page_token`, and the normalized filters. Each approval contains only the reviewed field allowlist; raw form data and the raw backend response are never returned. Pagination is cursor-based, so the command does not invent a numeric page or `total`.

## people approval category list

List approval categories available to the current account.

```bash
bytedcli people approval category list
bytedcli --json people approval category list
```

Text output shows category ID, name, and optional flow ID. JSON output returns `categories` and `current_count`. Use these IDs with `people approval list --category-ids`.

## people approval flow list

List approval flows available to the current account.

```bash
bytedcli people approval flow list
bytedcli --json people approval flow list
```

Text output shows flow ID, category ID (`biz_type`), and name. JSON output returns `flows` and `current_count`. Use a returned flow ID with `people approval list --flow-id`.

## people overview get

Read the current account's People home overview counts.

```bash
bytedcli people overview get
bytedcli --json people overview get
```

Text output shows the aggregate total plus talent plan, feedback, performance, written exam, resume, and interview counts. JSON output returns `overview.total_count` and `overview.todo_counts` with the same six normalized categories. This is a count summary, not an actual todo-item list.

## people shortcut list

List the People home shortcut links visible to the current account.

```bash
bytedcli people shortcut list
bytedcli people shortcut list --page 2 --page-size 10
bytedcli --json people shortcut list
```

Options:

- `--page <n>`: 1-based local page number, defaults to `1`.
- `--page-size <n>`: local page size, defaults to `20`.

Text output shows shortcut ID, name, type, description, and full URL. JSON output returns `shortcuts`, `current_count`, `total`, `page`, and `page_size`; each shortcut contains `id`, `name`, `logo`, `description`, `url`, and `type`. These are People home navigation shortcuts, not actual approval or task records.

## people app list

List the People home application directory visible to the current account.

```bash
bytedcli people app list
bytedcli people app list --page 2 --page-size 10
bytedcli --json people app list
```

Options:

- `--page <n>`: 1-based local page number, defaults to `1`.
- `--page-size <n>`: local page size, defaults to `20`.

Text output shows app ID (`id`), name, group, favorite state, and full URL. JSON output returns `apps`, `groups`, `favorite_ids`, `current_count`, `total`, `page`, and `page_size`. Each app contains the stable application identifiers, localized names, descriptions, group metadata, icon, order, URL, and normalized `favorite` flag. The command is read-only and does not launch or mutate an application.

## people calendar workday get

Check whether one mainland date is a workday.

```bash
bytedcli people calendar workday get --date 2026-06-03
bytedcli --json people calendar workday get --date 2026-06-03
```

Options:

- `--date <YYYY-MM-DD>`: required date to check.

The command reads the ByteDance public mainland calendar and combines Monday-Friday weekday rules with public-calendar holiday and statutory working-day events. It is read-only and does not read or mutate personal leave records.

Text output shows the date, workday result, reason, day of week, holiday / makeup / activity flags, pre-holiday flag, calendar source, and matched events. JSON output returns `workday` with:

- `date`
- `day_of_week`: JavaScript weekday number, where `0` is Sunday and `6` is Saturday.
- `is_workday`
- `reason`: `weekday`, `weekend`, `holiday`, or `makeup_workday`.
- `holiday`
- `makeup_workday`
- `activity_day`
- `pre_holiday`
- `events`
- `source`

## people leave list

Query self leave records for a date range.

```bash
bytedcli people leave list --start-date 2026-06-03 --end-date 2026-06-03
bytedcli --json people leave list --start-date 2026-06-03 --page-size 100
```

Options:

- `--start-date <YYYY-MM-DD>`: required start date.
- `--end-date <YYYY-MM-DD>`: optional end date, defaults to `--start-date`.
- `--page <n>`: 1-based page number.
- `--page-size <n>`: page size.

Text output shows record ID, leave type, time, duration, status, and notes. JSON output returns `records`, `page`, `page_size`, and backend `total` when present.

## people leave apply

Apply for a single same-day leave record. The default mode is preflight only.

```bash
bytedcli people leave apply \
  --date 2026-06-03 \
  --full-day \
  --leave-type "Annual Leave"

bytedcli people leave apply \
  --date 2026-06-03 \
  --full-day \
  --leave-type "Annual Leave" \
  --yes

bytedcli people leave apply \
  --date 2026-06-03 \
  --half-day pm \
  --leave-type fully-paid-sick \
  --comment "身体不适"

bytedcli people leave apply \
  --date 2026-06-03 \
  --half-day pm \
  --leave-type fully-paid-sick \
  --comment "身体不适" \
  --yes
```

Options:

- `--date <YYYY-MM-DD>`: leave date.
- `--full-day`: one full-day record from AM to PM.
- `--half-day <am|pm>`: one half-day record, morning or afternoon.
- `--leave-type <type>`: People leave type ID, display name, or alias such as `Annual Leave`, `fully-paid-sick`, `sick`, or `病假`.
- `--comment <text>`: leave application comment.
- `--applicant-user-id <id>`: People applicant user id; inferred from self leave records when omitted.
- `--yes`: submit the live People leave application.
- `--allow-conflict`: submit despite People time validation warnings; use only after explicit user confirmation.

Pass exactly one of `--full-day` or `--half-day <am|pm>`. Without `--yes`, the command validates the request and prints `next_command`. With `--yes`, the command submits and then refreshes the day's records to show matching leave records.
