# inspection_whitelist.md — resource-inspection kill whitelist

Use this reference for the Forge **resource-inspection kill whitelist** (强杀白名单) — exempting a job or a user within a resource group from inspection-driven automatic kill behavior. For the inspection **tasks / rules** surface (巡检规则 / 巡检任务) see [inspection.md](inspection.md).

**Whitelist management is a platform operation — never a local file edit.** Wording like "把 alice 加入(强杀)白名单", "对某个用户做白名单管理", or "add user X to the kill whitelist" always maps to `forge inspection kill-whitelist create|list|update` against the backend. Do not search for or edit local config files, YAML, or an inspection task's `task_config` to manage whitelist entries, and do not treat a username as a file path or config key. A username target is `--target <username> --target-type user` and requires `--resource-group`. When the resource group is missing, **ask the user for it — and say why**: one user can run jobs in multiple resource groups, so the backend cannot infer which group to exempt (unlike job targets, where the backend derives the resource group from the job id). **Never guess or derive it yourself**: do not resolve the group from membership lookups such as `quota resource-group list --user <name>`, and never substitute a similar-looking username for the one the user gave — at most present lookup results as candidates for the user to confirm before creating anything.

For install / auth / `--site` basics see [invocation.md](invocation.md); these commands take the usual `--network` / `--site` runtime flags.

**Whitelist data is per control plane — the site is never irrelevant here.** An entry lives on exactly one site, and every list/query returns only the site you asked. If the user names a site (or gives a Reckon URL), pass `--site`; if they don't, the command runs against a single default site (`cn`) — say which site you queried, and don't present one site's result as the whole picture. All commands emit JSON by default; do not add `--json`.

Not every control plane supports resource inspection yet. If a command fails with a `method not found` error, or a create returns no `id`, the target site does not have it enabled — tell the user the operation did not take effect instead of reporting success.

Implemented commands:

- `forge inspection kill-whitelist create | list | update`

---

## Create kill whitelist entry

Use `create` when the user asks to add a job or user to the resource-inspection kill whitelist.

**Whitelist entries expire — surface the duration to the user; don't silently take the default.** With no `--duration-hours` the backend applies its default (about 24 hours); once it expires the job is no longer exempt. Whitelisted rounds reset the consecutive-hit streak; automatic kill becomes eligible again after subsequent qualifying scheduled hits reach the rule threshold. Duration is optional — never block the create on it. When the user names a duration, convert it to `--duration-hours N` (`0` = permanent when permitted). When they don't, proceed with the create using the backend default and state explicitly that the entry expires in about 24 hours — do not stop to ask for a duration when everything required is already known. The create output includes `expiry_time` (unix seconds) when the entry is active; report when protection ends, and mention `kill-whitelist update --whitelist-id <id> --action renew --duration-hours N` to extend. Stop and ask only for missing **required** parameters, e.g. `--resource-group` for user targets.

```bash
# Add a job by job id. The backend can infer the resource group.
forge inspection kill-whitelist create \
  --target 123456 \
  --reason "offline evaluation"

# Add a user in one resource group.
forge inspection kill-whitelist create \
  --target alice \
  --target-type user \
  --resource-group aml-forgeide \
  --duration-hours 24 \
  --reason "incident mitigation"

# Request a permanent entry when permitted.
forge inspection kill-whitelist create \
  --target 123456 \
  --duration-hours 0 \
  --reason "long-running benchmark"
```

Flags:

| Flag | Notes |
|---|---|
| `--target` | Required. Job id when `--target-type job`; username when `--target-type user` |
| `--target-type` | `job` (default) or `user` |
| `--resource-group` | Required for `--target-type user`; omit for job targets unless the user explicitly provides it |
| `--duration-hours` | How long the exemption lasts. Omit → backend default (~24h, then the entry expires and the job is killable again); `0` → permanent when permitted. Surface this to the user rather than defaulting silently |
| `--reason` | Optional but recommended for auditability |
| `--approver` | Optional payoff-unit admin to notify when approval is required |

Natural-language extraction:

| User wording | Command shape |
|---|---|
| Pure numeric job id, e.g. "把 123456 加白" | `--target 123456 --target-type job`; leave `--resource-group` empty unless provided |
| Username / SSO, e.g. "把 alice 加白" | Ask for `--resource-group` if missing and explain why user targets need it (multi-group ambiguity; job targets don't — the backend infers from the job). Never guess the group from membership lookups or rewrite the username; then use `--target alice --target-type user --resource-group <group>` |
| User gives a reason | Put the concise reason in `--reason` |
| User says how long, e.g. "加白 3 天" / "48 小时" | Convert to hours: `--duration-hours 72` / `--duration-hours 48` |
| User asks for permanent / never expire | Use `--duration-hours 0` |
| User doesn't say a duration | Create with the ~24h backend default and explicitly report the expiry plus how to renew — never stall the create waiting for a duration, and never default silently |

Output includes:

```json
{
  "ok": true,
  "id": 7,
  "status": "approved",
  "expiry_time": 1782999999,
  "notified_approvers": ["admin_a"],
  "detail_url": "https://..."
}
```

If `status` is `pending`, tell the user which approvers were notified when `notified_approvers` is present. If `status` is `approved`, the entry is already active — and when `expiry_time` (unix seconds) is present, **tell the user when the exemption ends**, since the job becomes killable again after it.

---

## List kill whitelist entries

Use `list` to check current entries, approval status, or entries waiting for the current user.

```bash
# Recent entries
forge inspection kill-whitelist list

# Entries waiting for current user's approval
forge inspection kill-whitelist list --pending-my-approval

# Entries submitted by the current authenticated user
forge inspection kill-whitelist list --mine

# One exact target with status filter
forge inspection kill-whitelist list --target 123456 --status approved

# Deep link / exact entry lookup by id
forge inspection kill-whitelist list --whitelist-id 7
```

Filters:

| Flag | Notes |
|---|---|
| `--whitelist-id` | Exact whitelist entry id (`--id` is a deprecated compatibility alias) |
| `--target` | Exact target job id or username |
| `--mine` | Entries submitted by the current authenticated applicant; mutually exclusive with `--applicant` |
| `--applicant` | Applicant username |
| `--payoff-unit` | Owning payoff unit |
| `--resource-group` | Resource group |
| `--status` | `pending`, `approved`, `rejected`, `expired`, or `revoked` |
| `--pending-my-approval` | Only entries pending current user's approval |
| `--page`, `--page-size` | Pagination; defaults are page 1 and page size 20 |

Output includes `total`, `page`, `page_size`, and `entries`. Entry fields use user-facing labels:

```json
{
  "id": 9,
  "target": "123456",
  "target_type": "job",
  "resource_group": "aml-forgeide",
  "payoff_unit": "reckon_payoff",
  "status": "pending",
  "applicant": "alice",
  "renew_pending": true,
  "can_approve": true,
  "duration_hours": 24
}
```

When summarizing entries, lead with `id`, `target`, `target_type`, `resource_group`, `status`, and whether `can_approve` is true. The `id` is the handle for approval, rejection, renewal, or revocation.

`duration_hours` is only meaningful while `status` is `pending` — it is the requested exemption length (`0`/negative means the applicant asked for permanent) before an approver has acted, so it's how you answer "how long was this requested for?" for an entry that has no `expiry_time` yet. Once an entry is approved it carries a real `expiry_time` instead and `duration_hours` on it should not be quoted as the active exemption length.

---

## Update kill whitelist entry

Use `update --action` to approve, reject, renew, or revoke one entry. Do not invent separate CLI verbs for these operations.

```bash
# Approve an entry
forge inspection kill-whitelist update --whitelist-id 7 --action approve

# Reject an entry
forge inspection kill-whitelist update --whitelist-id 7 --action reject --reject-reason duplicate

# Renew for 24 hours
forge inspection kill-whitelist update --whitelist-id 7 --action renew --duration-hours 24

# Revoke an approved entry
forge inspection kill-whitelist update --whitelist-id 7 --action revoke
```

Flags:

| Flag | Notes |
|---|---|
| `--whitelist-id` | Required whitelist entry id (`--id` is a deprecated compatibility alias) |
| `--action` | Required: `approve`, `reject`, `renew`, or `revoke` |
| `--reject-reason` | Use with `--action reject`; include the user's reason when provided |
| `--duration-hours` | Use with `--action renew`; pass it explicitly when the user requests a specific renewal duration |

If the user asks to approve/reject/renew/revoke but does not provide an `id`, **always run `list` first to locate the entry** — filter with `--pending-my-approval` for approval/rejection requests ("待我审批" / "my pending approvals"), or with `--target` / `--applicant` / `--status` as the wording suggests. Only ask the user for an id when the filtered list still cannot pin down a single entry. Do not ask for an id before listing, and do not answer with approve/reject prose alone (e.g. drafting a rejection reason) without locating the entry and running the update.

Output includes `ok` and, when the backend returns it, the updated `entry`. Summarize the updated status and id.

---

## Error handling

- Permission denied means the caller is not allowed to act on that payoff unit / resource group. Do not retry blindly; tell the user to ask an eligible admin or approver.
- User-target whitelist entries require `--resource-group` because one user can run jobs in multiple resource groups.
- Job-target entries can usually omit `--resource-group`; the backend derives the job's resource group.
- These commands emit JSON by default. Do not add `--json`.
- Mutating commands (`create` / `update`) should only be run when the user's intent is clear. Listing is read-only.

---

## Common workflows

### Add a job to the whitelist

```bash
forge inspection kill-whitelist create --target <job_id> --reason "<reason>"
```

Report the returned `id`, `status`, and `detail_url` if present.

### Add a user to the whitelist

If `resource_group` is missing, ask for it (explain the multi-group ambiguity; do not derive it from membership lookups). Then:

```bash
forge inspection kill-whitelist create \
  --target <username> \
  --target-type user \
  --resource-group <resource_group> \
  --reason "<reason>"
```

### Approve everything waiting for me

First list:

```bash
forge inspection kill-whitelist list --pending-my-approval
```

Show the entries and ask which `id` values to approve unless the user already clearly requested all listed entries. Then run one update per selected id:

```bash
forge inspection kill-whitelist update --whitelist-id <id> --action approve
```

### Check whether a target is already approved

```bash
forge inspection kill-whitelist list --target <job_id_or_username> --status approved
```

If no approved entry appears, check all statuses before concluding there is no request:

```bash
forge inspection kill-whitelist list --target <job_id_or_username>
```
