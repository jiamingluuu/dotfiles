---
name: bytedance-hire
description: "Operate retained ByteDance Hire (people.bytedance.net / people-cn.bytedance.com) task counts, recruitment-workbench backlog and progress overview, interviewer calendar status, recruitment processes/stages, referral position search/share, referral policy, and referral code workflows via bytedcli. Use when tasks mention Hire 待办/招聘待办/评估计数/笔试计数/面试计数/面评待提交/Offer 审批/今日面试, 招聘工作台概览/backlog/recruitment progress, 面试官日历/可约时间, 招聘流程/招聘阶段/job process, 内推职位/校招职位/社招职位/内推搜索/职位过滤/内推分享/分享链接/内推二维码/内推政策/内推码/邀请码, hire task status, hire overview, hire calendar, referral position, referral share, referral policy, referral code, people hire, people.bytedance.net, or people-cn.bytedance.com."
---

# bytedcli People Hire

`people hire` CLI wraps `people.bytedance.net/atsx/api` and reuses the Feishu Web session saved by `bytedcli auth login --session --feishu`.

## When to use

- Read current-user Hire task counts.
- Read current-user backlog and account-visible recruitment progress.
- Read the current interviewer's calendar availability summary.
- List recruitment processes and ordered stages visible to the current Hire account.
- Search and filter open referral positions for both 校招 (campus) and 社招 (social).
- Get one referral position's full detail (description, requirement, share token).
- List filter options (job categories, recruit types, locations) for list/share filters.
- Build an external referral share short link (and optional QR code) for one position or a filtered set.
- Read the current user's referral code without refreshing it.
- Read referral policy visibility and link configuration.

## Reference

- Read [the Hire command reference](references/hire.md) when you need complete options, pagination rules, output contracts, or per-command behavior.

## Commands

```bash
# Current-user Hire task counts
bytedcli people hire task status
bytedcli --json people hire task status

# Current-user backlog and account-visible recruitment progress
bytedcli people hire overview get
bytedcli --json people hire overview get

# Current interviewer's calendar availability
bytedcli people hire calendar status
bytedcli --json people hire calendar status

# Recruitment processes and ordered stages
bytedcli people hire job-process list
bytedcli people hire job-process list --page 2 --page-size 20
bytedcli --json people hire job-process list

# Search referral positions (校招 campus / 社招 social)
bytedcli people hire referral-position list --type social --keyword "<kw>"
bytedcli people hire referral-position list --type campus --recruit intern --city CT_128
bytedcli --json people hire referral-position list --type social --page 1 --page-size 30

# List valid filter options (categories, recruit types, location codes) for a channel
bytedcli people hire referral-position filter list --type campus
bytedcli --json people hire referral-position filter list --type social

# Get one position's full detail by job post id
bytedcli people hire referral-position get --id <job-post-id>
bytedcli --json people hire referral-position get --id <job-post-id>

# Build an external share short link for one position or a filtered list (--qr / --qr-image optional)
bytedcli people hire referral-position share --type campus --id <job-post-id>
bytedcli people hire referral-position share --type social --keyword "<kw>" --city <code>
bytedcli people hire referral-position share --id <job-post-id> --qr

# Read the current user's referral code without refreshing it
bytedcli people hire referral-code get
bytedcli --json people hire referral-code get

# Read referral policy visibility and link
bytedcli people hire referral-policy get
bytedcli --json people hire referral-policy get
```

## Notes

- `people hire task status` concurrently reads current-user evaluation, written-exam, uncommitted interview-feedback, ByteDance offer-approval, visible-interview, today-finished-interview, and interview activity counts. A missing account-visible task area is returned as `null` / `unavailable`, while an explicit backend zero remains `0`. Interview `activity_status` values remain numeric because the trace does not prove stable labels for all returned codes.
- `people hire overview get` concurrently reads the current user's backlog areas and account-visible recruitment progress. JSON returns `hire_overview.backlog_areas` and `hire_overview.recruitment_progress`; each sub-area contains `key`, `name`, and `count`, while each top-level area additionally contains `sub_areas`. Missing or backend-null counts remain `null`, and the output omits people, creator fields, stage IDs, URLs, and URL parameters.
- `people hire calendar status` resolves the current People user internally, then returns appointment tasks being arranged, total available time slots, and whether any calendar time exists. It does not accept or expose the user ID.
- `people hire job-process list` is read-only and locally paginates the current account's visible recruitment processes plus ordered stages. JSON includes `page`, `page_size`, `current_count`, and `total`; nullable backend sequence/type/status values stay numeric or `null`, while text output displays missing values as `-`. The output omits creator identity and raw response fields.
- `people hire referral-code get` is read-only and returns the current account's referral code plus the last refresh timestamp. It never calls the separate code-refresh endpoint. A zero refresh timestamp is preserved as `0` in JSON and shown as `-` in text mode.
- `people hire referral-policy get` is read-only and preserves the backend `is_display` flag and `policy_link`. A hidden policy or empty link is a valid result, not an error.
- `people hire referral-position list|get|filter|share` operate the referral storefront (内推职位). Use `--type campus` for 校招 and `--type social` for 社招 (default). Campus additionally accepts `--recruit intern|regular` (实习/正式). `--keyword` maps to the web search box (`key_words`); `--city` takes comma-separated location codes and `--category` comma-separated job-category ids from `referral-position filter list`; `--department-id` narrows to one department. City/category accept either repeated flags or a single comma-separated value.
- `referral-position filter list --type <campus|social>` returns the valid category, recruit-type, and location options for that channel. Campus uses the campus config endpoint; social uses the experienced-hire config endpoint.
- `referral-position get --id <job-post-id>` returns the full position (description, requirement, department, HR, and the position `share_info` token when available).
- `referral-position share` builds an external candidate-facing short link on `job.toutiao.com`. With `--id` it shares one position; without `--id` it shares the current filtered set (same filters as `list`); sharing the whole channel with neither `--id` nor any filter is rejected. The link is produced server-side (share token + short-link); the QR code is rendered locally from the short link. `--qr` draws the QR in the terminal (TTY text mode); `--qr-image [path]` writes a PNG (defaults to a temp file), and in JSON mode the PNG path is returned as `qr_image_path`.
- Authentication reuses the Feishu Web session saved by `bytedcli auth login --session --feishu`; a plain `bytedcli auth login` (ByteCloud Auth) does not cover `people hire`. If an agent receives `PEOPLE_AUTH_REQUIRED`, load the `bytedance-auth` skill and follow its non-blocking Feishu session flow: generate the QR only after the user is ready, present `qr_image_path` for mobile Feishu scanning, and poll `--complete`; do not use `lark_applink_url` as a substitute for scanning.
