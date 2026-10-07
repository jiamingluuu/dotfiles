# People Hire CLI Reference

`people hire` commands wrap Hire web APIs on `people.bytedance.net` and `people-cn.bytedance.com`.
Authentication reuses the Feishu Web session saved by `bytedcli auth login --session --feishu`; a plain `bytedcli auth login` (ByteCloud Auth) does not cover these commands. When the session is missing, commands fail with `PEOPLE_AUTH_REQUIRED` and the fix command `bytedcli auth login --session --feishu`.

## people hire task status

Read current-user Hire task counts.

```bash
bytedcli people hire task status
bytedcli --json people hire task status
```

Text output shows pending evaluation, written-exam, uncommitted interview-feedback, ByteDance offer-approval, visible-interview, and today-finished-interview counts, followed by the interview activity counts. JSON output returns these stable fields under `task_status`:

- `pending_evaluation_count`
- `pending_exam_count`
- `uncommitted_interview_count`
- `bytedance_offer_approval_count`
- `visible_interview_count`
- `today_finished_interview_count`
- `interview_activity_counts[]`

The four scene-derived fields always exist. They are `null` when the backend omits an area for the current account, while an explicit backend zero remains `0`. Each interview activity count contains the backend `activity_status` number and its `count`; the CLI does not assign unverified labels to those numeric values.

The command is read-only and follows the current account's Hire task visibility.

## people hire overview get

Read the current user's Hire backlog and the recruitment progress visible to the current account.

```bash
bytedcli people hire overview get
bytedcli --json people hire overview get
```

The command is read-only and sends no user-provided identifiers. Text output renders separate backlog and recruitment-progress tables. JSON output has this stable shape:

```json
{
  "hire_overview": {
    "backlog_areas": [
      {
        "key": "backlog_interview",
        "name": "My Interviews",
        "count": 2,
        "sub_areas": []
      }
    ],
    "recruitment_progress": []
  }
}
```

Every area and sub-area contains only `key`, `name`, `count`, and, for areas, `sub_areas`. A missing or backend-null count remains `null`; it is not converted to zero. The output omits people, creator fields, stage IDs, URLs, URL parameters, and raw responses.

## people hire calendar status

Read the current interviewer's Hire calendar availability summary.

```bash
bytedcli people hire calendar status
bytedcli --json people hire calendar status
```

Text output shows appointment tasks being arranged, the total available time-slot count, and whether the current interviewer has any calendar time. JSON output returns these stable fields under `calendar_status`:

- `arranging_appointment_task_count`
- `total_available_time_count`
- `has_any_calendar_time`

The command resolves the current People user automatically. It does not accept the user ID as CLI input, persist it, or include it in output.

## people hire job-process list

List recruitment processes and their ordered stages visible to the current Hire account.

```bash
bytedcli people hire job-process list
bytedcli people hire job-process list --page 2 --page-size 20
bytedcli --json people hire job-process list
```

The command retrieves the complete process list once and paginates processes locally. `--page` is 1-based and defaults to `1`; `--page-size` defaults to `20`. Text output shows the current page as one row per stage with the full process ID, process name, backend process type/status, full stage ID, stage name, sequence, and backend stage type.

JSON output returns `job_processes`, `current_count`, `total`, `page`, and `page_size`. Each process contains `id`, localized `name`, `name_en`, `active_status`, `type`, and `stages`; each stage contains `id`, localized `name`, `name_en`, `sequence`, and `type`. `active_status`, process/stage `type`, and `sequence` are a backend number when present or `null` when absent; text output displays those missing values as `-`.

The command is read-only. Numeric type/status values are preserved without unverified labels. The output omits creator identity and raw response fields.

## people hire referral-code get

Read the current Hire account's referral code without refreshing it.

```bash
bytedcli people hire referral-code get
bytedcli --json people hire referral-code get
```

Text output shows the code and its last refresh time. JSON output returns `referral_code.code` and `referral_code.last_refresh_time`. A backend value of `0` for `last_refresh_time` is preserved in JSON and shown as `-` in text mode.

This command is read-only. It calls the referral page's code-read endpoint and never calls the separate code-refresh endpoint. The result follows the current account's Hire referral access.

## people hire referral-policy get

Read the current Hire referral policy visibility and link configuration.

```bash
bytedcli people hire referral-policy get
bytedcli --json people hire referral-policy get
```

Text output shows whether the policy is displayed and its link. JSON output returns `referral_policy.is_display` and `referral_policy.policy_link`. A backend `is_display=false` value or an empty `policy_link` is preserved as a valid state and does not cause an error.

## people hire referral-position list

Search open referral positions on the referral storefront (内推职位).

```bash
bytedcli people hire referral-position list --type social
bytedcli people hire referral-position list --type campus --recruit intern --keyword "<kw>"
bytedcli people hire referral-position list --type social --city CT_128,CT_11 --category <category-id>
bytedcli --json people hire referral-position list --type social --page 1 --page-size 30
```

| Option             | Meaning                                                                 | Default    |
| ------------------ | ----------------------------------------------------------------------- | ---------- |
| `--type <type>`    | `campus` (校招) or `social` (社招).                                     | `social`   |
| `--recruit <kind>` | Campus sub-type: `intern` (实习) / `regular` (正式). Campus only.       | none       |
| `--keyword <kw>`   | Keyword search (department / keyword / HR), maps to web `key_words`.    | none       |
| `--city <codes>`   | Comma-separated location codes (`location_code_list`).                  | none       |
| `--category <ids>` | Comma-separated job-category ids (`job_category_id_list`).              | none       |
| `--department-id`  | Single department id.                                                   | none       |
| `--page <n>`       | 1-based page number.                                                    | `1`        |
| `--page-size <n>`  | Rows per page (backend `limit`).                                        | `20`       |

Backend channel mapping: social sends `recruit_type_id_list=["1","3"]`; campus sends `["2"]`, or `["201"]` (正式) / `["202"]` (实习) when `--recruit` is set. Pagination is offset/limit. JSON returns `positions`, `total`, `current_count`, `page`, `page_size`, `offset`, and `has_more`; text mode renders a paged table. Location codes and category ids come from `referral-position filter list`.

## people hire referral-position filter list

List valid filter options for one channel.

```bash
bytedcli people hire referral-position filter list --type campus
bytedcli --json people hire referral-position filter list --type social
```

Returns `categories` (job categories), `recruit_types` (recruit types; campus exposes 实习/正式), and `locations` (city/country nodes with codes). Each option has `id`, `name`, `name_en`, and optional `parent`. Campus reads the campus config endpoint; social reads the experienced-hire config endpoint.

## people hire referral-position get

Get one referral position's full detail by job post id.

```bash
bytedcli people hire referral-position get --id <job-post-id>
bytedcli --json people hire referral-position get --id <job-post-id>
```

Returns the position name, code, department, category chain, city/cities, recruit type, HR, description, requirement, `job_id`, and (when the backend provides it) the external `share_host` / `share_token` used to build a candidate share link.

## people hire referral-position share

Build an external candidate-facing share short link for one position or a filtered set, with an optional locally-rendered QR code.

```bash
bytedcli people hire referral-position share --type campus --id <job-post-id>
bytedcli people hire referral-position share --type social --keyword "<kw>" --city <code>
bytedcli people hire referral-position share --id <job-post-id> --qr
bytedcli --json people hire referral-position share --id <job-post-id> --qr-image
```

| Option           | Meaning                                                        | Default |
| ---------------- | -------------------------------------------------------------- | ------- |
| `--id <id>`      | Share a single position; omit to share the filtered list.      | none    |
| `--type`         | `campus` / `social`. Filtered-list share only.                 | `social`|
| `--keyword/--city/--category/--department-id/--recruit` | Same filters as `list` for filtered-list share. | none |
| `--qr`           | Render the short link as a terminal QR code (TTY text mode).   | off     |
| `--qr-image [p]` | Write a PNG QR; without a value a temp-file path is used.      | off     |

With `--id`, the CLI calls the single-position share-token endpoint; otherwise it calls the filtered-jobs share-token endpoint with the current filter body. It then exchanges the `host`+`token` share URL for a `job.toutiao.com/s/<code>` short link via the short-path endpoint. The short link is returned as `share_url` with `scope` of `position` or `filtered`. The QR code is generated locally from the short link (no backend QR endpoint); in JSON mode the PNG path is returned as `qr_image_path` and terminal QR is suppressed.
