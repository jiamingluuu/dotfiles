# Forge webshell — explicit, confirmed supplemental access

Use this reference only when the user explicitly asks for
`forge job webshell list/exec` (or provides an already-confirmed Forge webshell
target) and the target environment is known to permit that access. For ordinary
training pod discovery, executor state/attempt selection, container diagnosis,
or kill operations, use [primus_pods.md](primus_pods.md) first.

## Hard routing gate

- `forge job webshell list` is **not** the Source of Truth for Primus pod
  inventory, executor attempt identity, or lifecycle state. Primus History is
  authoritative.
- `forge job webshell exec` is **not** the default entrypoint for training
  container operations.
- A logical executor such as `executor_stream_395` must be expanded in Primus
  History to concrete attempts such as `_0`, `_1`, `_2`; select the current
  `RUNNING` attempt before considering any live operation.
- RoW/i18n container diagnosis and pod/process kill operations use SDP + Primus.
  EU/TTP defaults to Primus History, Primus log, and Footprint-backed logs.
- Do not run `webshell list` as a cheap lifecycle preflight and then
  automatically feed its output to `webshell exec`. In an explicit Forge
  webshell request, `list` may enumerate supplemental target candidates, but
  only an executor target (`--role + --executor-id`) requires the authoritative
  attempt resolution described below.

## Prerequisites

1. The user explicitly requested Forge webshell and the environment/access
   path is confirmed usable.
2. Apply the prerequisite for the selected target shape:
   - **`webshell list`**: no pre-resolved pod is required. Its result is
     supplemental target data only and must not be used to establish pod
     inventory, attempt identity, or lifecycle state. The command has no
     `--stage-id`; its rows cannot represent a selected historical stage.
   - **`webshell exec --role <r> --executor-id <id>`**: resolve the concrete
     current `RUNNING` attempt through Primus History and make sure its mapping
     to the CLI's executor target is unambiguous, as described in
     [primus_pods.md](primus_pods.md). The command also has no `--stage-id`;
     compare the selected `stage_id` with the default/latest-stage metadata
     before exec. If they differ, stop instead of executing against the
     job-level target.
   - **`webshell exec --am`**: no executor-attempt expansion applies. Confirm
     the intended job/stage and use its AM target; do not derive executor
     lifecycle conclusions from that target. This job-level target also has no
     stage selector, so stop when the intended stage is not the current stage.
   - **`webshell exec --webshell-url <url>`**: no Primus target lookup is
     required when the user supplied or already confirmed the exact URL. Treat
     it as opaque and do not cite it as lifecycle evidence.
3. `forge auth status --site <site>` authenticated. The CLI surface accepts all
   four sites (`cn` / `i18n` / `eu-ttp` / `us-ttp`), but support in the command
   surface does not make webshell the recommended regional workflow.
4. **For `webshell exec` only** — a **cn** SSO browser session, even
   when targeting i18n / eu-ttp / us-ttp jobs. Every region's
   webshellauth host delegates OAuth2 to ByteDance SSO
   (`sso.bytedance.com`), so the cn jar is the universally valid
   credential. Run `forge auth session status --site cn`; if
   `validated` is false or `cookie_count` is 0, run
   `forge auth login --begin --session --site cn`. The envelope's
   `user_action.method` will be `qr_scan`; pass `user_action.prompt_body`
   to the user verbatim (it already has the path on its own line and
   asks the user to scan with Lark mobile). End your turn. Once the
   user signals done, call `forge auth login --complete <token>`
   **once** (one-shot, no polling loop). The QR window is 2 minutes;
   on `pending`, wait 3–5 seconds and call once more (the server may
   lag the user's confirmation); on `expired`, the envelope carries
   `recovery.command` for a fresh begin. If the user reports that Lark
   rejected the scan ("Login method isn't allowed"), stop retrying QR and
   run `user_action.fallback_command` (browser sign-in with password or
   passkey; needs the user's desktop with Chrome). Same agent-flow contract as
   the ByteCloud auth flow — see
   [`invocation.md` → Auth login from an agent](invocation.md#auth-login-from-an-agent)
   for the full Hard rules.
   The runtime `--site` is still used to resolve job metadata and the
   Reckon endpoint that serves Primus metadata — only the SSO session is fixed to cn.

   **Never substitute the ByteCloud auth flow for `webshell exec`.** A
   `forge auth login --begin --site cn` (without `--session`)
   produces a JWT, not a browser session jar; the JWT does not carry
   the `bd_sso_*` cookies the webshell relay requires. If the user is
   already device-flow authenticated but lacks a session, you still
   need to run `--begin --session --site cn` separately.
5. **`webshell list` does NOT need a browser SSO session.** For a
   `--job-id`, it uses the read-only Primus metadata path with the compatible
   job-derived fallback when needed; neither path requires a browser cookie
   jar. The returned targets remain supplemental and non-authoritative.

## List supplemental webshell targets

```text
forge job webshell list --job-id <id> [--role <name>] [--include-finished]
```

- This output is only supplemental target data for an explicit Forge webshell
  request. Do not cite it as evidence of pod inventory, attempt identity, or
  lifecycle state.
- Running an explicitly requested `webshell list` does not require a
  pre-resolved attempt. Before using one of its executor rows for
  `webshell exec`, inspect the role's complete pod rows for the selected stage
  at the site-resolved History access URL from
  [primus_pods.md](primus_pods.md), filter to `RUNNING`, and resolve the current
  concrete attempt there. Preserve the original `primus_history_url` for audit
  and handoff. If Primus History cannot be read, the list may still be returned
  as explicitly requested supplemental data, but label it non-authoritative and
  stop before executor exec or any lifecycle conclusion.
- Default view only returns `state == RUNNING` executors (plus the AM).
- `--role base-runner` filters executors to one role.
- `--include-finished` returns non-RUNNING rows too.
- With `--job-id`, targets come from the job's current Primus metadata for
  the selected `--site`; pass the job's own site.
- Output JSON shape: `ok`, `primus_url`, `application_id`, `final_status`,
  `user`, `dc`, `am: {pod_name, webshell_url, log_url}`,
  `executors: [{role, executor_id, id, pod_name, node, state, launch_time, release_time, exit_code, diag, webshell_url}]`.
  Pre-terminal executors (`state` RUNNING or STARTING) report `release_time`
  and `exit_code` as `null`, and `diag` as an empty string, because Primus
  echoes the previous attempt's terminal diagnostics onto these rows.

## Exec one command

```text
forge job webshell exec --job-id <id> {--am | --role <r> --executor-id <executor_id>} \
    --command "<cmd>" [--timeout-ms 30000] [--output-file /tmp/out.txt] [--raw]
```

- Target is exactly one of: `--am`, `--role+--executor-id`, or `--webshell-url`.
- The concrete-attempt prerequisite applies only to
  `--role+--executor-id`. `--am` has no executor attempt to expand, while an
  exact user-supplied or already-confirmed `--webshell-url` bypasses target
  discovery; neither exception turns the target into lifecycle evidence.
- `--executor-id` takes the **`executor_id` string** field from `webshell list`
  output (for example legacy `executor_jaguar-worker_3` or Primus CLI
  `executor_jaguar-worker_3_0`), not the numeric `id` field. That identifier is
  not lifecycle evidence. Use it only after its mapping to the Primus
  History-resolved concrete `RUNNING` attempt is unambiguous. If multiple
  attempts exist and `webshell list` cannot identify the concrete live attempt,
  do not run `webshell exec`.
- Command is exactly one of: `--command` or `--command-file`.
- Exit code semantics: by default the `forge` process exits 0 whenever the
  webshell link succeeded; the remote command's exit code is in the JSON
  envelope's `exit_code` field. Infrastructure failures (timeout, refresh,
  closed) return non-zero forge exit codes. For shell scripts that prefer
  plain exit-code semantics, pass `--exit-with-remote-code` to propagate the
  remote command's exit code as the `forge` process exit code.
- With `--strip-cookies` (default), the JSON envelope redacts sensitive query
  params in `wss_url` and key=value pairs in the echoed `command` field
  (`TOKEN=…` etc). The `output` field is NEVER redacted — see Don'ts.

Use `--output-file` whenever the expected output exceeds ~64 KB; JSON
envelope echoes the full output otherwise and saturates terminals fast.

Use `--timeout-ms 120000` or larger for profiling/tracing (`nsys profile …`).

Routine primus log tailing (e.g. `stderr.log` per role) is already covered by
`forge job log query --log-type primus --role <r> --log-file <f>`. On an
EU/US-TTP office runtime, that command can use the Footprint-backed read path
with the CN browser SSO session. A missing log-proxy path
does not by itself authorize a Forge webshell fallback: use webshell only on
the user's explicit request after the environment and exact target are
confirmed.

ByteCloud AK/SK application identity does not replace this browser session.
`forge job webshell exec` always requires a valid CN SSO session even when the
Forge/Reckon request itself uses `BYTECLOUD_AUTH_AS=app`. For sessionless
inspection, prefer `forge job webshell list` or the normal job-log commands.

## Session management

For webshell, only the **cn** session matters — every region's
webshellauth host delegates OAuth2 to ByteDance SSO. The commands below
include `--site` for completeness (other features may use per-site
sessions), but for webshell `--site cn` is the only one that affects
exec.

```text
forge auth login --begin --session --site cn   # agent-friendly: returns immediately
forge auth login --complete <token>            # one-shot; call after user signals scan complete
forge auth login --session --site cn           # blocking; for human terminals only
forge auth session status --site cn
forge auth session clear  --site cn
```

`--session-method` (advanced; default per site):

- `cn` → `qr` (default) — scan the printed QR with Lark. Accounts that
  Lark answers with "Login method isn't allowed" must use
  `interactive-browser` instead, which signs in with password or passkey
  in a local Chrome window.
- `i18n` / `eu-ttp` / `us-ttp` → `interactive-browser` (default) — launches
  the user's local Chrome / Chromium to complete SSO at TikTok SSO.
  Asking for `qr` on a non-cn site fails fast. **Note**: a non-cn session
  is currently not used by webshell; only run a non-cn session login
  when another feature explicitly needs the TikTok SSO jar.

Each site's session is stored independently as
`~/.forge/sso_session_<site>.json` (0600). Logging in to one site does
not affect another's session.

## Failure recipes

- `AUTH_SESSION_REQUIRED` / `AUTH_SESSION_INVALID` → rerun
  `forge auth login --begin --session --site cn`, end your turn
  while the user scans, then call `--complete <token>` once (always
  cn — see Prerequisites #4). If the scan is rejected with "Login method
  isn't allowed", run `user_action.fallback_command` instead — see
  [QR scan rejected](invocation.md#qr-scan-rejected-login-method-isnt-allowed).
- `WEBSHELL_PERMISSION_DENIED` (or any error message containing a BPM
  apply URL like `bpm.bytedance.net/apply` / `bpm-i18n.tiktok-row.net/apply`
  / `cloud-eu.tiktok-row.net/bpm`) → the authenticated user is not on
  the pod's webshell access list. Open the printed apply URL in a
  browser (or ping the printed `assignee`) to file the BPM workflow.
  Re-running the command is pointless until the workflow is approved.
- "webshell relay denied access by OG compliance policy" /
  `ErrOGDenied` → relay-server compliance gate (e.g.
  `relay-eu.tiktok-row.org` blocks restricted-status employees from
  ROW-prod webshell under GDPR). The error hint includes the relay
  URL — open it in a browser for details. **Hard policy gate, do
  NOT retry.** If the user genuinely needs access, that is an HR /
  compliance workflow, not a CLI workflow.
- `WEBSHELL_TARGET_NOT_RUNNING` → for an executor target, re-open/query the
  selected stage's site-resolved History access URL, inspect all lifecycle
  states for the role, and resolve the current concrete `RUNNING` attempt
  there. Preserve the original URL separately. For `--am` or `--webshell-url`,
  re-confirm the intended current target instead of applying executor-attempt
  rules. Do not retry against another row selected only from `webshell list`.
- `WEBSHELL_REFRESH_ERROR` → 90% of the time, session expired; relogin.
- `WEBSHELL_TIMEOUT` → raise `--timeout-ms`, or break the command into
  smaller pieces; do not wrap in `bash -c "…; …"` when you can just run
  the last line as a separate exec.

## Don'ts (agent stance)

- Do not default `--raw` on. ANSI output contaminates downstream grep/regex.
- Never echo secrets in `--command` (e.g., `echo $TOKEN`); JSON envelope
  mirrors the full output verbatim.
- Do not use `webshell list` for pod enumeration, attempt selection, executor
  health, or lifecycle conclusions.
- Do not use `webshell exec` as the default container path. RoW/i18n uses
  SDP + Primus for container diagnosis and pod/process kill operations;
  EU/TTP defaults to Primus History, Primus log, and Footprint-backed logs.
- Do not proactively suggest `forge auth login --session` for tasks
  that don't actually invoke `webshell exec`. `webshell list` does not
  need a session.
