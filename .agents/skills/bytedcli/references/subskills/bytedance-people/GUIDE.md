---
name: bytedance-people
description: "Use when a task mentions ByteDance People or people.bytedance.net: approval counts/审批计数, approval instances/审批单据, approval categories or flows/审批分类流程; home overview/首页概览; People home shortcuts/快捷入口; People application directory/应用目录/app list; workday calendar/工作日/节假日/调休/法定工作日/mainland calendar; leave/请假/年假/病假/半天假/全天假; or getting/updating the current user's Feishu profile signature through bytedcli."
---

# bytedance-people

Operate People approval/overview, leave, and current-user profile signature workflows through `bytedcli people ...`. Keep leave applications and signature updates behind their dry-run and explicit-confirmation gates.

## Reference

Read `references/people.md` when you need complete option and output contracts or the guarded leave-application flow.

## Commands

```bash
# Read approvals, filter directories, and People home overview counts
bytedcli people approval status
bytedcli --json people approval status
bytedcli people approval list --status pending
bytedcli people approval list --status finished --category-ids 1,52
bytedcli people approval category list
bytedcli people approval flow list
bytedcli people overview get
bytedcli --json people overview get
bytedcli people app list
bytedcli --json people app list
bytedcli people shortcut list
bytedcli --json people shortcut list

# Query whether a mainland date is a workday
bytedcli people calendar workday get --date 2026-06-03
bytedcli --json people calendar workday get --date 2026-06-03

# Query or update the current user's Feishu profile signature. Update is dry-run unless --yes is passed.
bytedcli people profile signature get
bytedcli people profile signature get --web-fallback --cdp-port 9222
bytedcli people profile signature get --from-web --cdp-port 9222
bytedcli people profile signature get --from-web --cdp-port 9222 --user-id 1234567890
bytedcli people profile signature update --text "Working from Shanghai"
bytedcli people profile signature update --text "Working from Shanghai" --yes
bytedcli --json people profile signature get

# Query self leave records
bytedcli people leave list --start-date 2026-06-03 --end-date 2026-06-03
bytedcli --json people leave list --start-date 2026-06-03 --page-size 100

# Preflight a single full-day leave application. This does not submit.
bytedcli people leave apply \
  --date 2026-06-03 \
  --full-day \
  --leave-type "Annual Leave"

# Submit a full-day leave only after the user explicitly confirms the live action.
bytedcli people leave apply \
  --date 2026-06-03 \
  --full-day \
  --leave-type "Annual Leave" \
  --yes

# Preflight a single half-day leave application. This does not submit.
bytedcli people leave apply \
  --date 2026-06-03 \
  --half-day pm \
  --leave-type fully-paid-sick \
  --comment "身体不适"

# Submit a half-day leave only after the user explicitly confirms the live action.
bytedcli people leave apply \
  --date 2026-06-03 \
  --half-day pm \
  --leave-type fully-paid-sick \
  --comment "身体不适" \
  --yes
```

## Guidance

- `people approval status` is read-only and returns pending, finished, CC, and applicant counts from the current account's approval dashboard.
- `people approval list` is read-only and lists approval instances visible to the current account. `--status` accepts `pending`, `finished`, `cc`, `applicant`, or `other`; use `--keyword`, `--category-ids`, or `--flow-id` for filtering. Pagination is cursor-based: pass the returned `next_page_token` back through `--page-token`; do not infer a numeric page or total. The command returns an explicit allowlist and never exposes the raw approval payload.
- Use `people approval category list` and `people approval flow list` to discover the category IDs and flow IDs accepted by approval-list filters.
- `people overview get` is read-only and returns the six confirmed People home count categories: talent plan, feedback, performance, written exam, resume, and interview.
- `people shortcut list` is read-only and lists People home shortcut links. These shortcuts are navigation entries, not actual approval or task records; use `--page` / `--page-size` for local pagination.
- `people app list` is read-only and lists the People home application directory, including group, favorite state, and application URL. Use `--page` / `--page-size` to page the returned directory locally.
- `people calendar workday get` is read-only and checks one `YYYY-MM-DD` date against the ByteDance public mainland calendar. It combines normal Monday-Friday weekday rules with public-calendar holiday and statutory working-day events. JSON output returns `workday.is_workday`, `reason`, `holiday`, `makeup_workday`, `activity_day`, `pre_holiday`, matched calendar `events`, and `source`.
- `people profile signature get` best-effort reads the current account's Feishu profile signature from the internal Feishu Passport details endpoint. Some accounts/sessions return only `company_information` and `personal_information` without `description`; in that case the CLI returns `PEOPLE_PROFILE_SIGNATURE_UNAVAILABLE` instead of pretending the signature is empty. To read through Web Feishu, launch Chrome with a DevTools port, open `https://bytedance.larkoffice.com/next/messenger/`, then pass `--web-fallback --cdp-port <port>` or force that path with `--from-web --cdp-port <port>`.
- `people profile signature get --from-web --user-id <id>` reads another user's signature only if the current signed-in Web Feishu account can see that user's profile card. It is read-only and does not bypass Feishu profile visibility, privacy, or tenant restrictions. Do not accept a free-form name as a unique selector; resolve or ask for a stable Feishu user ID first.
- Web Feishu signature get uses the signed-in page's `LarkAPI.transport.callSdkApi` command `50100|contact.v2.GetUserProfileRequest|contact.v2.GetUserProfileResponse|1|GET_USER_PROFILE_V2`; the signature is `userInfo.description.text`, and the request must use `syncDataStrategy: 3` (`FORCE_SERVER`). `TRY_LOCAL` is rejected, and `callServerApi` / simple `/im/gateway/` replay are not equivalent.
- `people profile signature update` updates the current account's Feishu profile signature. Without `--yes`, it only prints a dry-run summary and `next_command`; add `--yes` only after the user confirms the final signature text. This command uses the internal Feishu Passport web endpoint documented by the business reference, not public Lark OpenAPI, so it depends on the current Feishu web session and may break if that web endpoint changes.
- `people leave list` reads the current account's leave records for a date range.
- `people leave apply` supports one same-day leave request at a time. Pass exactly one of:
  - `--full-day` for one full-day record from AM to PM.
  - `--half-day am` or `--half-day pm` for one half-day record.
- Write behavior is guarded: without `--yes`, the command validates the leave type/time, prints the planned request, and shows the exact confirmation command.
- Use `--leave-type "Annual Leave"`, `fully-paid-sick`, `sick`, `病假`, the People leave type ID, or the exact display name.
- The applicant user id is normally inferred from existing self leave records. If the account has no readable records, pass `--applicant-user-id <id>`.
- Authentication reuses the Feishu Web session saved by `bytedcli auth login --session --feishu`. If an agent receives `PEOPLE_AUTH_REQUIRED`, load the `bytedance-auth` skill and follow its non-blocking Feishu session flow: generate the QR only after the user is ready, present `qr_image_path` for mobile Feishu scanning, and poll `--complete`; do not use `lark_applink_url` as a substitute for scanning.
- Profile signature update uses `https://internal-api-lark-api.feishu.cn/passport/users/details/`; profile signature get may also use the Web Feishu SDK fallback. Never ask users to paste Cookie values into chat, docs, logs, or command arguments.
- If People reports a time conflict, the command blocks submission by default. Use `--allow-conflict` only when the user explicitly wants to submit despite that validation warning.
