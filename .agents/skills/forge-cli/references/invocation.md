# invocation.md

Global install, auth, and runtime conventions shared by all `forge` commands. Load this when the user asks about installation, upgrade, authentication, global flags, or output formats.

## Install and upgrade

```bash
# Install or upgrade: download the installer, then run it
curl -fsSL -o /tmp/forge-install.sh https://luban-source.byted.org/repository/forge/install.sh
sh /tmp/forge-install.sh

# Check installed version
forge version

# Upgrade in place to the latest release; also re-syncs the bundled skill
forge upgrade
```

- `forge upgrade` replaces the binary and then transparently runs `forge skill update` to re-sync the skill shipped inside the new binary into all detected agent directories.
- If the user reports skill drift (CLI upgraded but the skill seems stale), run `forge skill status` to compare marker `content_hash` with the embedded skill.

### Auto-upgrade

When a newer release exists, the first stale-release `forge` invocation per machine blocks for ~7-15s while the new binary self-installs in the background (skill bundle resyncs as part of the same step). Subsequent invocations no-op via version comparison — no slowdown. Non-release builds (dev / dirty / commit-hash) never auto-upgrade.

Two env vars opt out:

| Env | Effect |
|---|---|
| `FORGE_NO_AUTO_UPGRADE=1` | Skip the blocking upgrade. Every command still prints `Notice: forge vX is available...` to stderr until the user manually runs `forge upgrade`. |
| `FORGE_NO_UPDATE_NOTIFIER=1` | Silences the passive notice. Only effective in combination with `FORGE_NO_AUTO_UPGRADE=1` — on its own the auto-upgrade path runs and the notice never fires. |

CI / unattended scripts that must not have an unexpected 15s pause should set `FORGE_NO_AUTO_UPGRADE=1`. Full silence (no auto-upgrade and no notice) needs both vars set.

Failures roll back to a notice automatically: a failed auto-upgrade prints `Auto-upgrade failed: <reason>` followed by the same `Notice: forge vX is available...` line, records a 1-hour backoff on disk, and lets the user's actual command proceed against the current binary. The next stale-release invocation retries.

## Authentication

```bash
forge auth status
forge auth login --begin --site <site>           # agent-friendly: returns immediately
forge auth login --complete <token>              # one-shot; call after user signals scan/click complete
forge auth login --site <site>                   # blocking; for human terminals only
forge auth logout
```

Rules:

- On a missing / invalid auth result, recover the identity that the command actually selected. If the error names an injected-JWT variable, repair or unset that injection first because it remains authoritative. With `--bytecloud-user-jwt-file`, supply a fresh user JWT for the explicit site or remove the flag; never fall back to another login automatically. With `BYTECLOUD_AUTH_AS=app`, do **not** start a user login: run `forge auth status --site <site>`, repair the selected site's global or site-specific AK/SK pair and suffix, keep `BYTECLOUD_AUTH_AS=app`, and treat a valid application identity that receives 403 as an application-permission problem. Only when user identity is intended should an agent run the **two-phase begin/complete** flow described in [Auth login from an agent](#auth-login-from-an-agent). **Never** invoke the bare `forge auth login` from inside an agent — it is a blocking command (it drives the interactive ByteCloud auth flow to completion) and will deadlock your tool harness.
- The `--begin` envelope always carries a `user_action` object whose `method` field is either `browser` (ByteCloud auth login) or `qr_scan` (cn QR session login). **Always read `user_action.method` first** and pick the corresponding fields — the two flows look superficially similar but require different user actions.
- After the user signals they've scanned / clicked, call `auth login --complete <token>` **once**. Treat `login_status=success` as "credentials persisted, retry the original command", `expired` as "run `recovery.command` then start over", `pending` as "the server may lag the user's confirmation by a moment — wait 3–5 seconds and call `--complete` one more time; if still pending, the pending envelope re-emits `user_action` so re-show it and ask the user to confirm before retrying." Do **not** run a polling loop in the background.
- Avoid touching `internal/auth/*` or the auth commands unless the task explicitly requires auth work.

### Headless application identity

For a workload with no user interaction, have the runtime securely inject both
SDK-native variables `BYTECLOUD_AUTH_ACCESS_KEY_ID` and
`BYTECLOUD_AUTH_SECRET_ACCESS_KEY` (do not place their values in commands or
logs), select application identity explicitly, then validate the selected site:

```bash
export BYTECLOUD_AUTH_AS=app
forge auth status --site <site>
```

After the injected-JWT seam, unset/`auto` and `BYTECLOUD_AUTH_AS=user` select
user identity only. A missing, expired, site-incompatible, network-failing, or
refresh-failing user credential never switches the command to AK/SK.
`BYTECLOUD_AUTH_AS=app` strictly selects application identity; Forge
intentionally has no `--as` flag. When auto mode sees a complete AK/SK pair but
cannot authenticate the user, its recovery hint tells the operator to set that
environment variable explicitly.

Site-specific AK/SK pairs append `CN`, `I18N_TT`, `US_TTP`, or `EU_TTP`, for
example `BYTECLOUD_AUTH_ACCESS_KEY_ID_I18N_TT` and
`BYTECLOUD_AUTH_SECRET_ACCESS_KEY_I18N_TT`. Existing pre-issued JWT injection
continues to take precedence through `BYTECLOUD_CLI_API_JWT_TOKEN` or
`BYTECLOUD_CLI_API_JWT_TOKEN_<SITE>`.

Application identity is the application/service-account principal in the JWT,
not a delegated user. It must be granted the Forge API/resource permissions
needed by the command. There is no supported `AK/SK + username -> user JWT`
flow; `--owner`, `--user`, or `--creator` only supplies an attribution field
where supported and never bypasses authorization. Actor fields inferred by
Forge use the application account as owner/operator/creator; backend-authored
audit fields remain backend-defined. If the application JWT has no usable
principal claim and the command needs an implicit actor, pass that command's
explicit actor flag when available or use a user login.

Real-environment validation covers AK/SK exchange, JWT refresh, identity and
principal resolution, and read-only API access on all four sites. Do not infer
that every write is enabled: each Forge/Reckon/BPM backend must authorize the
application account for the specific operation and resource.

Git-managed US-TTP commit creation is not supported with application identity.
Forge rejects it before `code update` or Git push. Set
`BYTECLOUD_AUTH_AS=user` and log the same user in to `us-ttp` and `i18n` before
running `forge code commit create`. A Git-managed `forge code compile create`
without `--commit-id` auto-creates that commit and has the same restriction;
when an existing commit is suitable, pass its `--commit-id` explicitly and
ensure the application principal has compile permission.

Forge-managed US-TTP changes may use application identity, but `us-ttp` and
the auxiliary `i18n` site must resolve to the same SDK-reported AccessKeyID.
Mixed identities or different application credentials fail before code update.

`forge job webshell exec` is not authorized by AK/SK alone; it requires a
separate CN browser SSO session. Prefer `forge job webshell list` or ordinary
job-log commands for sessionless inspection, or establish that session
explicitly when exec is required.

### Auth login from an agent

The bare `forge auth login` is a **blocking command** that runs the interactive auth flow until the user authorizes or it times out (the ByteCloud auth flow for the default path; a 2-minute QR window for `--session`). Synchronous bash tools return output only on exit, so a foreground call from inside an agent hangs and the user never sees the URL/QR. Always use the **two-phase agent flow**; the only exception is the blocking browser fallback for a [rejected QR scan](#qr-scan-rejected-login-method-isnt-allowed):

1. **Begin** — non-blocking; emits a JSON envelope with `complete_token` and `user_action`.
   - ByteCloud auth (default): `forge auth login --begin --site <site>`
   - QR session (cn only, required for `forge job webshell exec`): `forge auth login --begin --session --site cn`

2. **Render `user_action.prompt_body` verbatim** to the user-facing surface (AskUserQuestion body, printed message, etc.). The cmd ships it as a fully-substituted, multi-line, plain-text string with real newlines — URL, Feishu PC AppLink for session QR, or QR path on its own line, all alternatives surfaced when present, no markdown, no fenced code block. Pass it through; do not paraphrase, do not selectively drop fields (e.g. surfacing only `open_in_browser` while skipping `phone_qr_image`, or surfacing only `scan_qr_image` while skipping `lark_applink_url`, deprives the user of their preferred path). Localize the prose only when the user's request language is non-English; keep the line breaks, field order, and "path on its own line" structure intact.

   The structured fields (`open_in_browser`, `phone_qr_image`, `lark_applink_url`, `scan_qr_image`, etc.) remain in the envelope for debugging and for agents that genuinely need to recompose; under normal flow, `prompt_body` is the canonical surface.

   | `method` | Load-bearing fields surfaced in `prompt_body` |
   |---|---|
   | `browser` | `open_in_browser` (always); `phone_qr_image` (PNG path) when present, framed as an alternative path |
   | `qr_scan`  | `lark_applink_url` (Feishu PC) when present, or `scan_qr_image` (PNG path) for the Lark mobile app; `qr_payload` deliberately omitted (SSO-rejected URL) |

3. **Call complete after the user's signal** — `forge auth login --complete <token>` returns immediately each call (one-shot, never blocks). The user's "done" reply (or `AskUserQuestion` confirmation) is the trigger; do **not** run a background polling loop. On `success` → credentials persisted, retry the original command. On `pending` → wait 3–5 seconds and call `--complete` once more in the foreground (the server occasionally lags the user's confirmation); if still `pending`, re-show the prompt (the envelope re-emits `user_action` verbatim) and ask the user to confirm before another attempt. On `expired` → run the `recovery.command` literal from the envelope (carries `recovery.reason`: `bytecloud_challenge_expired` / `bytecloud_challenge_denied` for the default flow, or `qr_window_expired_2min` for `--session`) and start over — unless the user reported a rejected QR scan; then follow [QR scan rejected](#qr-scan-rejected-login-method-isnt-allowed).

#### Hard rules

These exist because the typical agent failure is asking the user to "open this link and scan with Lark" — a contradiction SSO rejects.

- **Pass `user_action.prompt_body` verbatim.** That field is the cmd-rendered, ready-to-display body — URL / Feishu PC link / path on its own line, all alternatives surfaced when present, real newlines, no markdown. Reaching into method-specific fields and composing your own prompt is the failure mode that drops `phone_qr_image` or session `lark_applink_url`, or that escapes newlines into literal `\n\n` characters.
- **Read `user_action.method` first** when you DO need to branch (e.g. for `--complete` retry logic). Never reach into method-specific fields without branching on the discriminator.
- **`browser` mode has two equivalent paths.** `open_in_browser` and `phone_qr_image` (when present) end at the same SSO approval page. `prompt_body` already shows both as alternatives — when composing custom prompts, mirror that: surface both, frame as "or" / "either", never tell the user to do both, never silently drop one.
- **In `qr_scan` mode, only the embedded URL is Lark-only — not the file or AppLink.** `qr_payload` (the URL inside the QR) fails in desktop browsers with "Please open it by Lark client"; never present `qr_payload` as a clickable link. `lark_applink_url` is the safe Feishu PC wrapper when present. `scan_qr_image` is just a PNG file — opening its path in any image viewer (Preview, Chrome via `file://`, etc.) just renders the image, and that is a perfectly fine way to show the QR to the user. Do **not** discourage the user from opening the PNG; the browser ban applies to `qr_payload`, not the PNG path.
- **Never `Read` / `cat` / multimodal-load the QR PNG into your own context.** The file's only intended viewer is the user's phone camera. Loading the bytes into the agent burns context for zero value: the agent does not need to "see" the QR to relay its file path, and seeing it does not let the agent complete the auth on the user's behalf. Forward `scan_qr_image` / `phone_qr_image` as a path string only.
- **Do not paraphrase the action.** The CLI ships `user_action.instruction` precisely so agents do not have to synthesize their own (often-wrong) prose. If you localize, base the localized prose on the structured fields, not on free-text reading of the envelope.
- **Put the URL or PNG path on its own line** in the user-facing prompt — no surrounding text on the same line, no markdown decoration like `[link](...)` or backticks. Most terminals auto-detect URLs and resolve `file://` paths only when the URL/path is the only content on the line; embedding it inside a sentence breaks the auto-linker.
- **Skip markdown decoration in the user-facing prompt.** Agent question UIs do not always render markdown; `**bold**` and `\n\n` paragraph breaks frequently land as literal characters in the user's view. Use plain text with real newlines. This includes section-header bolds like `**Step 1:**` — agents tend to add these when bundling multiple actions; don't.
- **Match the user's request language.** Templates below are in English; if the user clearly typed in another language (e.g. zh-CN), translate the prose while keeping the structure intact: same line breaks, same field order, URL / path still on its own line, no markdown.
- **Don't call `--complete` before the user signals they've scanned / clicked, and don't run a polling loop afterward.** The user's reply IS the trigger. After surfacing the prompt body, **end your turn** — wait for the user's "done" reply (or for an `AskUserQuestion`-style blocking primitive to return) before calling `--complete` once. On `pending`, retry once after a 3–5 second pause in the foreground; do **not** spawn a background `until` / `while` loop. This rule is harness-agnostic: agents with a blocking question primitive should use it; agents without one should print the prompt and stop, not chain straight into `--complete`.

#### Reference templates

`user_action.prompt_body` is the canonical surface — pass it verbatim. The strings below mirror what the cmd builds, useful as a reference when translating to the user's language (keep the structure: line breaks, field order, path on its own line).

Browser flow (`method=browser`), with `phone_qr_image`:

```text
Open the URL in any desktop browser, or scan the QR image with your phone — either path reaches the same approve page:

URL: {open_in_browser}
QR:  {phone_qr_image}

Reply "done" once authorized.
```

Browser flow (`method=browser`), without `phone_qr_image` (user passed `--qr-image=-`):

```text
Open the URL in any desktop browser to authorize:

{open_in_browser}

Reply "done" once authorized.
```

QR scan flow (`method=qr_scan`):

```text
Scan the QR image with the Lark mobile app to authorize:

{scan_qr_image}

(Cmd+click the path, or paste it into Chrome's address bar, to view the image.) Reply "done" once authorized.

If Lark shows "Login method isn't allowed" (不允许使用此登录方式) after scanning, reply "blocked" instead; this account must sign in with password or passkey in a browser.
```

QR scan flow (`method=qr_scan`), with `lark_applink_url`:

```text
Open the Feishu PC link to authorize, or scan the QR image with the Lark mobile app:

Feishu PC: {lark_applink_url}
QR image: {scan_qr_image}

(Cmd+click the path, or paste it into Chrome's address bar, to view the image.) Reply "done" once authorized.

If Lark shows "Login method isn't allowed" (不允许使用此登录方式) after scanning, reply "blocked" instead; this account must sign in with password or passkey in a browser.
```

#### Outcomes

- `success` persists credentials (the ByteCloud auth SDK's own per-site store for the default flow; an SSO session jar for `qr_scan` mode); retry the original command.
- `expired` — run `recovery.command` from the envelope, then loop again. For a session QR the envelope also carries `recovery.fallback_command`; use it instead when the user reported a rejected scan.
- `pending` — wait 3-5s, retry `--complete <token>`.

#### QR scan rejected ("Login method isn't allowed")

Some accounts may not use QR sign-in on ByteDance SSO: after scanning, Lark shows "Login method isn't allowed" (不允许使用此登录方式) and asks for account + password or passkey instead. The rejection is visible only in Lark; the CLI keeps reporting `pending` until the window expires, so retrying QR never succeeds for that account.

- When the user replies "blocked" or reports that message, stop the QR flow: do not call `--complete` again and do not start another `--begin --session`.
- Run `user_action.fallback_command` (also `recovery.fallback_command` on an expired envelope), which is `forge auth login --session --site cn --session-method interactive-browser`. It launches a local Chrome / Chromium window on the SSO sign-in page where the user signs in with password or passkey, and the command returns once the session is captured.
- It is a blocking command: it waits up to 5 minutes for the user, so run it in the foreground with a timeout of at least that long, and tell the user a browser window will open. If your harness cannot keep a foreground command alive that long, ask the user to run the command in their own terminal instead.
- It needs a desktop: macOS or Linux with Chrome / Chromium (set `FORGE_BROWSER_EXECUTABLE_PATH` for a non-standard install); Windows is not supported.
- The session is saved only on the machine that runs the command, and forge cannot copy it to another machine. When you run on a remote host without a display (devbox, ForgeIDE, an agent sandbox), this environment cannot complete the fallback: tell the user so, and ask them to run both the fallback login and the target forge command (`job webshell exec`, `job sdp exec`, or the Primus log query/download) in a terminal on their own desktop. Do not start another QR login on the remote host.

#### Misc

- `--begin --session --session-method=interactive-browser` is rejected (the local-Chrome flow needs a long-lived process to hold the CDP session); use the blocking form for that path on a TTY.
- `--qr-image=-` is rejected with `--begin --session` — the saved PNG is the load-bearing artifact, suppressing it would leave the agent with nothing concrete to surface.
- Challenge files live under `~/.forge/cache/auth_login_challenges/<token>.json` (0600 in a 0700 dir) and are swept after 30 min. PNGs live under `<tmp>/forge/auth-qr-*.png` and are wiped by `auth logout`.

#### Hand-off to human

Last resort, only when the user has no browser at all (e.g. headless CI box): ask them to run `forge auth login --site <site>` on a machine where they can act on the QR / URL. Credentials persist on disk (the ByteCloud auth SDK's store) and are shared across processes, so once they confirm, `auth status --site <site>` lights up everywhere.

### Multi-site login

You can be authenticated to multiple sites at once. User credentials are keyed by site in the ByteCloud auth SDK's store, and `auth status` (no flag) lists the sessions forge has seen locally. A Global ByteCloud user-login application can return per-site user JWTs backed by the same refresh token, so logging into one site can populate tokens for other sites; non-Global login applications remain site-bound. This login application is not AK/SK application identity. AK/SK is resolved for the command's selected site from its global or site-specific environment pair.

- Log in: `forge auth login --site us-ttp`
- Recreate the local ByteCloud service account app, e.g. to switch an old non-Global app_id to Global: `forge auth logout --reset-service-account`, then log in again and choose Global on the creation page.
- Switch site for one command: `forge --site us-ttp job meta get <id>`
- Log out (all sites at once): `forge auth logout`
- Per-site status: `forge auth status --site us-ttp`

If `--site` is omitted, commands use the config default (currently `cn`).

### Shared credential store (BYTECLOUD_CLI_CONFIG_DIR)

Managed containers and CI images often pre-provision one ByteCloud credential store for every ByteCloud auth SDK consumer and export the SDK's `BYTECLOUD_CLI_CONFIG_DIR` with that directory. Forge honors it: when the value is non-blank, the credential store is exactly that directory — nothing is appended — instead of the default `$HOME/.forge/bytecloud-auth/`.

- **Check the store before proposing a login.** When it already holds a valid credential for the target site, no `forge auth login` is needed; starting the begin/complete flow anyway costs the user a pointless round-trip. Run the per-site check first: `forge auth status --site <site>`.
- **Read `auth_source` to know what answered.** `"auth_source": "bytecloud-sdk"` means the credential store or AK/SK application exchange served it; `"auth_source": "env:<VARIABLE>"` means an injected JWT answered and the store was never consulted. The target-specific `BYTECLOUD_CLI_API_JWT_TOKEN_<SITE>` (`CN`, `I18N_TT`, `US_TTP`, or `EU_TTP`) comes first, followed by `BYTECLOUD_CLI_API_JWT_TOKEN` → `AIME_USER_CLOUD_JWT` → legacy `BYTECLOUD_CLI_JWT_TOKEN`. To validate the store itself, unset the applicable target-specific variable and all three global variables.
- **The site-less `forge auth status` summary never reads the store.** It checks the effective runtime site's target-specific injected JWT before the three global variables and reports the highest-priority active one even when invalid. Only when none applies does it reflect forge's local login inventory / AK/SK configuration. On a freshly provisioned environment that inventory can be empty, so its text output reports the active `BYTECLOUD_CLI_CONFIG_DIR` redirect and defers to `forge auth status --site <site>`. Do not read that empty summary as "not logged in".
- **Every store-backed operation follows the redirect**: login, logout (including `--reset-service-account`), per-site status, and JWT lookup. Forge's own state (`config.json`, SSO session jars, caches) stays under `$HOME/.forge` either way.
- Unset the variable — or export it blank, since a blank / whitespace-only value counts as unset — to return to `$HOME/.forge/bytecloud-auth/`.
- The browser SSO session used by `forge job webshell exec` is a separate credential path and is **not** covered by this variable; see [webshell.md](webshell.md).

### Site inference before command assembly

Before running any Forge command, resolve the intended site from the user's text, then carry it explicitly as `--site <site>` on every command in the same workflow. Do not drop this flag when switching from a global instruction to a task-specific reference such as `job.md`, `quota.md`, or `compile.md`.

Signals:

- Existing `--site <site>` in a user-provided command is authoritative unless it conflicts with an explicit user correction.
- Use explicit control-plane wording: `row`, `i18n`, and `us 控制面` / US control-plane wording mean `--site i18n`; `us-ttp` / USTTP wording means `--site us-ttp`.
- Only treat `us` as `--site i18n` when it is clearly a site/control-plane signal, not any unrelated occurrence of the word.

If two text signals disagree, ask for confirmation before running a command. For mutating commands (`code update`, `code meta update`, `code version create`, `code commit create`, `code compile create`, `job create`, `job kill`, `job checkpoint save`, `job checkpoint delete`), do not guess.

## CLI input contract

- Ordinary Forge commands are flag-only and reject stray positional arguments. The only intentional positional surfaces are `forge completion <shell>` and the transparent `forge localrun ...` passthrough.
- Unknown flags, invalid flag values, missing required groups, incompatible flags, and extra arguments are structured `validation` errors (exit code 2). Treat them as command-construction mistakes and correct the invocation; do not retry the same malformed command.
- Help, examples, completion, and this skill use canonical flag names. Hidden deprecated aliases remain accepted for existing scripts, but never generate them in a new command; supplying a canonical flag and its legacy alias together is an error.
- `--mine` is not global. It exists only on actor-scoped collection lists and resolves the current authenticated user into that resource's actual relation (`owner`, `user`, `admin`, `operator`, or `applicant`).
- Never emit an empty actor filter (`--owner=`, `--user=`, etc.) or a non-positive exact-ID list filter. Forge rejects both as validation errors so a malformed narrowing filter cannot silently become a broad list. Mutually exclusive selector groups use effective values, so explicit compatibility defaults such as `--mine=false` or `--job-id=0` are treated as omitted.

## Runtime flags

Applied to most commands that hit Reckon:

| Flag | Values | Notes |
|---|---|---|
| `--network` | `office` / `prod` | Selects the network environment. |
| `--site` | `cn` / `i18n` / `eu-ttp` / `us-ttp` | Global user-login applications may populate target-site user JWTs for multiple sites from one login. With `BYTECLOUD_AUTH_AS=app`, AK/SK application identity is selected independently for this site from its global or `_<SITE>` pair. Auto/user mode may refresh/discover a target-site user token but never switches to AK/SK; Reckon requests are always sent with a target-compatible JWT. The `(network, site)` pair selects a ByteCloud control plane — see the next section. |

Inside an AIME agent sandbox (non-blank `AIME_CURRENT_USER`), the auto-detected network defaults to `office` for every site; an explicit `--network` or user pin still overrides that default.

Production gateways are region-pinned: a `--network prod` request whose `--site` does not match the caller's region will fail with a raw network error (TLS / dial timeout, no route), not a friendly pre-flight message — there is no client-side cross-region guard. To read another region's data, use `--network office` (reachable across all regions). See `troubleshooting.md` → "Cross-region prod request fails with a raw network error".

Exception: `forge code compile create --compile-mode local` has its own preflight. It reads `FORGE_REGION`, allows only `cn` / `us`, rejects when the container region does not match the target code region (`cn` for `--site cn`, `us` for `--site i18n`; `--site us-ttp` and `--site eu-ttp` are unsupported for local compile), and requires `FORGE_IDE=1`, `FORGE_COMPILER_VERSION`, and the version-selected compiler command in `PATH` (`< 1.0.0.1940` uses `fd`; `>= 1.0.0.1940` uses `forge_dev`). On `forge_dev`, workspace local compile infers model/Sail/Torch, graphs, device, and image-appropriate Python defaults; non-official Sail still asks for TensorFlow when needed. See `compile.md` for the full capability gate.

### Control planes

There are four ByteCloud control planes, one per `--site`. The colloquial naming is messy — `--site i18n` has **three** aliases because the same site's host domain contains different substrings in different networks (office: `tiktok-row.net` → "row"; prod: `cloud-i18n.bytedance.net` → "i18n") and the backend also runs out of US infra ("us"). Map口语 names to `--site` using this table (case-insensitive; the hyphen in `us-ttp` / `eu-ttp` is optional):

| 口语名 | `--site` |
|---|---|
| **cn 控制面** | `cn` |
| **i18n 控制面** / **row 控制面** / **us 控制面** | `i18n` |
| **us-ttp 控制面** (usttp / US-TTP / USTTP) | `us-ttp` |
| **eu-ttp 控制面** (euttp / EU-TTP / EUTTP) | `eu-ttp` |

The single biggest trap: **"us 控制面" is NOT "us-ttp 控制面"**. "us" (without `-ttp`) is an alias for `--site i18n`; "us-ttp" is its own distinct site. When a user says just "us" without `-ttp`, they mean `i18n`. Bare `ttp` / `TTP 区域` is ambiguous between `eu-ttp` and `us-ttp`; ask for the exact TTP site instead of defaulting to either one.

Forge2/Reckon console URLs are also site signals. Infer `--site` from the hostname before extracting ids, then carry that site through every command in the workflow:

| Hostname | `--site` |
|---|---|
| `reckon.bytedance.net` | `cn` |
| `reckon-us.tiktok-row.net` | `i18n` |
| `reckon-eu.tiktok-row.net` | `eu-ttp` |
| `reckon-ttp.tiktok-row.net` | `us-ttp` |

If the URL host and user text imply different sites, ask for confirmation before running. Do not silently retry the same job/version on another site after a lookup or resource-group query fails.

#### Control-plane confirmation

Before the first site-relevant `forge` command in a workflow, including any prerequisite `forge auth status --site <site>` check, resolve the intended site. If neither the user's text nor any URL yields a site and no `--site` is already sticky in the conversation, first check the ForgeIDE signal: when the ForgeIDE precondition holds and `FORGE_IDE_DEPLOY_REGION` maps to `cn` or `i18n`, use that deployment environment as the sticky site and skip the question. Otherwise, run `forge config show` and read `runtime_source.site`.

If `forge config show` output has no `runtime_source` key, the binary predates this field: run `forge upgrade`; if upgrading is not possible, treat it as `default`.

- `flag` or `pinned`: use `runtime.site` as the sticky site for the conversation without asking.
- `default`: stop and ask which control plane to use, offering exactly `cn` (CN control plane), `i18n` (RoW / "us control plane"), `eu-ttp` (EU-TTP), and `us-ttp` (US-TTP). In the same question, ask whether to persist it with `forge config set --site <site>` so future conversations skip the question; run that command only after an explicit yes. Ask only when a person can answer in an interactive conversation. In a non-interactive or unattended run (a scheduled or cron-triggered routine, batch or CI execution, no user present, or the agent was told not to ask), do not ask: proceed with `runtime.site` as before, and state in the output that the site was not specified and `<site>` was used, together with the fix (`--site <site>` in the prompt, or `forge config set --site <site>` on that machine).
- Never infer candidates from `auth`; Global accounts commonly populate all four sites, so that inventory does not identify the user's control plane.

Ask at most once per conversation. After the user chooses, keep the site sticky and pass `--site <site>` explicitly on every site-relevant command. Do not ask when the user already named a site, when a site is already sticky, or for `forge localrun`, `forge config`, `forge version`, or `forge upgrade`, where the site is irrelevant. `forge auth` is site-scoped and is not on this list; the explicit fixed-site exception is browser-session repair with `forge auth login --begin --session --site cn`.

In ForgeIDE, apply the existing ForgeIDE access guard to URL-derived sites. Read `FORGE_IDE_DEPLOY_REGION`: `i18n` ForgeIDE can run only `--site i18n` targets, and `cn` ForgeIDE can run only `--site cn` targets. TTP targets (`--site eu-ttp` / `--site us-ttp`) do not have a ForgeIDE environment; use an office-network environment instead.

Keep target site separate from auxiliary auth:

- URL or user intent chooses the command's target `--site`.
- For `--site us-ttp` code workflows, keep the target as `--site us-ttp`; recover bridge auth according to the selected identity instead of changing the target or automatically starting a user login.
- For `job webshell exec`, keep the target `--site` from the URL/job; if the browser session is missing, repair only the session with `forge auth login --begin --session --site cn`.

The actual ByteCloud host each `(--network, --site)` pair reaches is resolved by the bundled `bytecloud-auth-go-sdk` — forge no longer maintains its own host table; it just maps `--network` (office/prod) onto the SDK's `AuthNetwork`. The control-plane identity (i.e. `--site`) does not change with network: "row 控制面" and "i18n 控制面" are the same control plane (`--site i18n`) even though the underlying host differs by network. Escape hatch for a single invocation: `BYTECLOUD_CLI_CLOUD_HOST=<url>` overrides the SDK's host resolution.

For code workflows on `--site us-ttp`, users still pass only `--site us-ttp`.
The CLI internally uses i18n credentials for global compliance and git-token
lookups, then uses us-ttp credentials for the final TTP commit/compile/job calls.
The SDK can reuse compatible credentials inside the `i18n` / `us-ttp` /
`eu-ttp` auth fallback group. If user identity is selected and bridge auth
still fails, refresh the target `us-ttp` user login through the agent-safe
begin/complete flow; if the error names the auxiliary i18n path, refresh that
user login too. With `BYTECLOUD_AUTH_AS=app`, do not run user login: a
Forge-managed flow must resolve the same AK/SK application on both sites, while
a Git-managed commit/auto-commit is unsupported and must use user identity (or
an existing `--commit-id` where compile can skip commit creation).

## Workspace metadata model

Workflow stages read and update `<workspace>/.forge/forge_meta.json`. The CLI resolves the workspace from the current working directory using its bounded parent lookup.

Stored views include:

- workspace metadata from `code fetch`
- commit artifacts from `code commit create`
- compile artifacts from `code compile create`
- job defaults such as `job.resource_group`

Implications:

- Run context-driven commands from the fetched workspace root or a nearby child directory.
- Do not pass `--dir`; `code commit create`, `code compile create`, and `job create` do not accept it.
- If `.forge/forge_meta.json` is missing, run `forge code fetch` or use explicit no-workspace flags where supported.
- Never edit `.forge/forge_meta.json` by hand in normal usage; re-run the earliest missing workflow stage instead.

## Output contract

- Default structured output for most commands is JSON on stdout.
- Commands that produce tabular data (for example `job deepinsight query`) default to CSV and expose `--json` to switch to JSON.
- Many commands accept `--output <file>` to write the formatted result to disk; when `--output` is used, stdout prints only `wrote output to <path>`.
- Errors use the standard CLI error envelope on stderr and return non-zero exit codes.

## Command naming conventions (repo invariant)

- Two-level `forge <resource> <action>` for simple operations (`code fetch`, `job create`).
- Three-level `forge <resource> <domain> <action>` when a resource has stable sub-domains (`code commit create`, `job metrics query`).
- Action verbs: `create`, `get`, `get-meta`, `query`, `list`, `diff`, `diagnose`, `update`. Lifecycle verbs `start` / `stop` are allowed only for explicit runtime lifecycle resources such as `serving deployment`; avoid other novel verbs. There is no `status` verb — use `get` (e.g., `code compile get`).
- `commit` and `compile` live only under `code`; there is **no** top-level `commit` or `compile` alias.
- Flags use kebab-case; underlying JSON fields may be snake_case — the mapping is at the Cobra binding layer, not the user surface.

## Agent stance

- Never ask the user for information the workspace metadata already has; always resolve derived flags (framework, commit ids, owner, …) from context first.
- When a derived flag is missing, trace back to the earliest failing stage (e.g., missing `framework` → rerun `code fetch`) rather than asking the user to supply it manually.
- For one-shot observation tasks, prefer `--json` so follow-up analysis is machine-readable.


### Borrow a user JWT for one invocation

Use `forge --bytecloud-user-jwt-file <path|-> --site <site> <command>`.
`-` reads non-interactive stdin; a file must be a regular non-symlink file and
owner-only on POSIX (`0600` or `0400`). Supply one JWT, no more than 64 KiB,
with readable claims and a future expiry. A present region must match the site.
Never put the JWT itself in argv. File/stdin input overrides environment and
stored credentials, stays in memory, and never changes login inventory.
`auth status --json` reports `auth_source: bytecloud-user-jwt-file`; validation
is local, and `--force-refresh` cannot renew this token. An expired or rejected
token requires a fresh input, not another identity.

Always specify `--site`; a configured default is insufficient. Auth reads
support `auth status` and `auth jwt get-bytecloud` (which explicitly prints the
token). Remove this flag for login/logout/session management or
`BYTECLOUD_AUTH_AS=app`. Another credential site is never used implicitly;
US-TTP `code commit create` therefore rejects it before side effects. Use a
protected file when the command also needs stdin for prompts.
