# troubleshooting.md

Common failure modes across the Forge workflow and how to recover. Load this when a command fails with an auth, endpoint, context, or region-related error.

---

## Auth failures

Symptoms: `auth status` reports invalid session, Reckon returns `401`, or any command exits with an auth-related error envelope.

```bash
forge auth status
forge auth login --begin --site <site>           # agent-friendly: returns immediately
forge auth login --complete <token>              # one-shot; call after user signals scan/click complete
```

Rules:

- Recover the identity the failed command actually selected. If the error names an injected-JWT variable, repair or unset that injection first because it outranks the SDK store. With `BYTECLOUD_AUTH_AS=app`, do not run user login: verify `forge auth status --site <site>`, repair the target site's global or site-specific AK/SK pair/suffix, and treat 403 with a valid app identity as an application-permission problem. Only when user identity is intended should an agent run `forge auth login --begin --site <site>` and follow the [Auth login from an agent](invocation.md#auth-login-from-an-agent) flow (the bare blocking `auth login` deadlocks synchronous bash tools).
- The `--begin` JSON envelope carries `user_action` (with `method`, `prompt_body` — the cmd-rendered ready-to-display body — plus the structured fields and an `instruction` string) and a `complete_token`. Pass `user_action.prompt_body` to the user-facing surface verbatim — plain text, no fenced code block, no markdown decoration; the cmd has already substituted every load-bearing field with the URL / PNG path on its own line. The `--begin` command also draws an ASCII QR on TTY for human terminals; ignore that on the agent path.
- After the user signals they've scanned / clicked, call `auth login --complete <token>` **once** (no polling loop). `success` → credentials persisted, retry the original command; `pending` → wait 3–5 seconds and call once more (the server occasionally lags the user's confirmation); if still pending, re-show the prompt and ask the user to confirm; `expired` → restart with `--begin`.
- If `auth login --complete` itself fails repeatedly with a non-interactive error, check clock skew, corporate proxy settings, or whether the user is behind a VPN restriction that blocks the SSO callback URL.

## Workspace metadata missing or stale

Symptoms:

- `code update`, `code commit create`, `code compile create`, or `job create` says `.forge/forge_meta.json` is missing.
- The CLI reports missing framework, `code_version_id`, commit artifact, or compile artifact.

Root cause: the command is not running from a fetched Forge workspace, or the workspace metadata exists but is missing artifacts from an earlier workflow stage.

Rules:

- `code update` and `code commit create` require a fetched workspace.
- `code compile create` requires a fetched workspace unless the user passes `--commit-id`.
- `job create` requires a fetched workspace unless the user passes both `--model-commit-id` and `--norbert-commit-id`.
- Do not keep searching broad local directories from an unrelated repo. If no workspace can be identified from the current directory, a user-provided path, or the latest `code fetch` result in the conversation, stop and use the recovery path below.

Recovery:

1. Confirm you are in the fetched workspace root or a nearby child directory.
2. Verify `<workspace>/.forge/forge_meta.json` exists.
3. If missing, run `forge code fetch --version-id <id> [--output-dir <parent>]`.
4. If commit or compile artifacts are missing, rerun the earliest missing stage: `code commit create`, then `code compile create`.
5. For explicit no-workspace execution, use the command-specific flags: `code compile create --commit-id <id>` or `job create --model-commit-id <id> --norbert-commit-id <id>`.

## `code fetch` / `commit get` fails with "case-insensitive name collision"

Symptoms: `code fetch`, `code commit get`, or `code commit diff` exits with `decode code_snippet: case-insensitive name collision: "X" and "Y" ... this filesystem ... is case-insensitive (e.g. macOS/Windows)`.

Root cause: the Forge version/commit holds two files in the same directory whose names differ only by letter case (e.g. `models/din.py` and `models/DIN.py`). The local volume is case-insensitive (the macOS/APFS and Windows default), so both cannot coexist on disk — writing them would silently drop one. forge refuses rather than lose a file (the git / Mercurial behavior). The check is filesystem-aware: on a case-sensitive volume the same fetch succeeds and writes both files.

Recovery:

- For `code fetch` / `code commit get`: fetch onto a **case-sensitive volume**. On macOS create one with a disk image, e.g. `hdiutil create -size 2g -fs 'Case-sensitive APFS' -volname forge ~/forge.dmg && hdiutil attach ~/forge.dmg`, then `forge code fetch --version-id <id> --output-dir /Volumes/forge` (these commands probe the `--output-dir` volume). Both files materialize with their real names.
- For `code commit diff`: there is **no `--output-dir`** — it decodes snapshots under the OS temp dir, so point `TMPDIR` at a case-sensitive volume for the run, e.g. `TMPDIR=/Volumes/forge forge code commit diff --commit-id <id>` (`os.MkdirTemp` honors `$TMPDIR`). Otherwise the only fix is renaming at the source.
- Or fix the source: rename one colliding file in the workspace and re-create the Forge commit / version.
- There is intentionally **no "overwrite anyway" flag** — on a case-insensitive volume that could only mean silently dropping a file, which is exactly the data loss this guard prevents.

Encode side (`code update` / `code commit create`): these are permissive — they will upload a workspace that contains case-colliding files (the snippet faithfully carries both), but the JSON result includes a `warnings` entry stating that consumers on case-insensitive filesystems cannot fetch both. Relay that warning when teammates are on macOS / Windows.

## Cross-region prod request fails with a raw network error

Symptoms: a `--network prod` command hangs or fails with a low-level network error — `net/http: TLS handshake timeout`, `dial tcp ... i/o timeout`, `no route to host`, `connection refused` — while auth is valid and the same command works for someone in another region. Most common when the `--site` does not match the region the caller is actually in.

If `AIME_CURRENT_USER` is set, first follow [AIME agent sandbox auto-detected as prod](#aime-agent-sandbox-auto-detected-as-prod); an older Forge binary can select prod before this cross-region diagnosis applies.

Root cause: production gateways are region-pinned. By default a prod Reckon or Tracing request goes straight to the target `--site`'s own gateway, which is generally unreachable from a different region. There is **no** client-side guard that pre-checks this, so the request goes out and fails at the transport layer. The most common failure is therefore a transport error, or an auth error naming the target site, when the caller is not in the target region.

Cross-region relaying is off unless the operator opted in (`FORGE_RECKON_REGION_GATEWAY`), and it applies only to `--network prod`: office-network runs never relay. With it on, a prod request enters through the caller region's gateway and is forwarded to the target site instead, so the failures below change shape. Check the variable and the network before applying the relay-only branches.

A relayed request can instead fail with a structured gateway error. Its envelope carries `error.detail.cross_region_gateway` with `code`, `reason`, `target_outcome` (`not_reached` or `unknown`), `transient`, and `logid`. Branch on these fields, not on the message text. **This envelope appears only when relaying is enabled**; on the default route there is no such detail and a missing one says nothing about the target's state. Even with relaying enabled, some training observation reads -- for example events, metrics, and stage lookups -- do not produce this detail: a gateway rejection there surfaces as a plain API error whose message carries the gateway text, so treat it as `target_outcome=unknown` and do not assume the target was not reached.

Agent rules:

- Treat a prod + cross-region transport failure as a **region/site mismatch first**, not a service outage. Confirm the caller's region and the targeted `--site` before escalating.
- On the default route, Reckon and Tracing requests authenticate with the **target** site's login. For an auth failure there, run `forge auth login --begin --site <target-site>` and follow [Auth login from an agent](invocation.md#auth-login-from-an-agent); a credential from the caller's own region is rejected before the request is sent, so logging in to the caller's region does not help.
- Relay-only (`FORGE_RECKON_REGION_GATEWAY` enabled, prod network): Reckon and Tracing requests authenticate with the **caller region's** login instead, so an auth failure there needs that region's site (a CN host needs `forge auth login --begin --site cn`), not the target `--site`. A prod host whose region Forge cannot map keeps the target site's entry and login, so the default-route rule above applies to it. Services that are not relayed still need the **target** site's login and a route to its region: Primus log content and downloads, `job log query --am`, and BPM work orders (TTP global_site calls likewise keep using the i18n login). For an auth failure on one of those, run `forge auth login --begin --site <target-site>` (`--site i18n` for global_site); if the target region is unreachable from this host, rerun from a host in that region or with `--network office`.
- Relay-only, `reason=request_blocked_at_border` (`target_outcome=not_reached`, usually an API not approved for cross-border access): do not retry over prod; rerun with `--network office` if the host reaches office entrypoints, otherwise from a host in the target region.
- Relay-only, `target_outcome=unknown` on a write command: never resubmit automatically; verify the resource state first. Retry a read-only command once only when `transient=true`.
- Any other reason: relay `logid` to the user for escalation. Webshell exec, BPM, and artifact downloads are never relayed and always need a host that can reach the target region; Primus read-only metadata rides the Reckon route and follows whichever mode is in effect.
- Recovery options to relay to the user:
  - `--network office` — office gateways are reachable across all regions; use this when you just need to read data from another region's site.
  - Correct the `--site` to the one matching the caller's region.
  - Run from a host in the target region (or a jump box / dedicated line that can reach it) if you genuinely need that site's **prod** gateway.
- Do not interpret this as a forge bug or a broken job. If the same command also fails over office network, fall through to [Auth failures](#auth-failures) or [Control-plane / ByteCloud host issues](#control-plane--bytecloud-host-issues).

## AIME agent sandbox auto-detected as prod

Symptoms: inside an AIME agent sandbox, `forge config show` reports `runtime.network=prod`, the environment contains `IS_PROD_RUNTIME=1`, and a command such as `forge auth login --begin --site us-ttp` times out while dialing `paas-gw-tx.tiktokd.org`.

Root cause: older Forge binaries let the injected production-runtime marker trigger generic prod-host detection before recognizing the AIME sandbox. The sandbox proxy can reach office entrypoints for every site, while region-pinned production gateways may be unreachable.

Recovery:

- Run `forge upgrade`; current Forge defaults to `office` whenever `AIME_CURRENT_USER` is non-blank.
- Until upgraded, pass `--network office` explicitly on every command, including `forge auth login --begin`.
- To pin one container, run `forge config set --network office`. The pin lives in `~/.forge/config.json` and is lost when the container is rebuilt.
- For any dial / TLS / lookup timeout from `auth login --begin` or a Reckon command on a non-`cn` site, retry once with `--network office` before offering another explanation.

## Network detected as office on a prod host

Symptoms: a command prints to stderr:

```
detected network=office, but this host looks like prod (tiger account, region lookup unavailable). If that's wrong, rerun with --network prod, or pin it via `forge config set --network prod`.
```

Root cause: `network` is auto-detected. On an interactive `tiger` production host, detection needs a resolvable region (read from `/opt/tiger/chadc/region.json`, which itself needs an IDC). When the IDC / region lookup fails, the prod-host detection layer falls through and the CLI defaults to `office` — even though the host is almost certainly on the prod network. This hint only appears when the network was resolved by detection (no `--network` flag and no pinned config).

Agent rules:

- **Relay the hint to the user and let them decide.** Do not run `forge config set --network prod` on your own — pinning network is a persistent, user-owned choice.
- Suggest the two corrections verbatim: rerun the command with `--network prod` for a one-off, or `forge config set --network prod` to pin it for this host.
- If the user confirms they are *not* on prod (e.g. a local laptop logged in as a `tiger` account), the office default is correct and the hint can be ignored.

## Switching sites

Symptoms: user runs a command with `--site <non-default>` and it fails with a per-site missing/invalid credential error.

First preserve the selected identity:

- With `BYTECLOUD_AUTH_AS=app`, do not start user login. Configure a complete global AK/SK pair or the target site's suffixed pair, keep `BYTECLOUD_AUTH_AS=app`, and verify with `forge auth status --site <site>`. A valid application identity that the backend rejects needs application API/resource permission, not login.
- With user identity, a Global ByteCloud user-login application can return per-site JWTs backed by the same refresh token, so one login may populate credentials for other sites. The SDK still stores each site separately; non-Global login applications remain site-bound. If no target-compatible user credential resolves, use the agent-safe begin/complete flow for that exact site and retry the original command.
- If the error names an injected-JWT variable, repair or unset that injection before either SDK path because login or AK/SK cannot override it while it remains applicable.

For user identity, newer SDK credentials may include `site_tokens` for multiple sites; older, non-Global, or incomplete local state may still require an explicit login to the target site. If the user already has an old local user-login application that was created before Global was selected, reset it and recreate it as Global from a human terminal:

```
forge auth logout --reset-service-account
forge auth login --site us-ttp
forge --site us-ttp job meta get <id>
```

Use the same target site that produced the original auth error when repairing either identity and retrying the command.

If the environment pre-provisions a shared ByteCloud credential store (managed containers, CI), the missing credential may just be forge reading a different directory: export the ByteCloud SDK's `BYTECLOUD_CLI_CONFIG_DIR` with that directory and forge reads and writes credentials there instead of the default `$HOME/.forge/bytecloud-auth/` — no separate `forge auth login` is needed when the store already holds a valid credential for the target site. Verify with `forge auth status --site <site>` and read its `auth_source` field; the full precedence rules (injected JWTs outrank the store, and the site-less summary never reads it) are in [`invocation.md` → Shared credential store](invocation.md#shared-credential-store-bytecloud_cli_config_dir). Unset the variable to return to forge's own store.

If `auth login --site <tiktok-row-site>` repeatedly fails the ByteCloud auth flow, verify the user's account has access to that site (TikTok email / passkey vs ByteDance one) and that there is no VPN / corporate proxy in the way.

## Control-plane / ByteCloud host issues

Symptoms: `auth login --site <x>` succeeds but `get-bytecloud` or any Reckon call returns a network/auth error. Or the user says "**row 控制面** / **us 控制面** / **i18n 控制面** / **us-ttp 控制面** 连不上 / 401".

First disambiguate the site. Control-plane口语 names do **not** map 1:1 to `--site` — "us" and "us-ttp" in particular are different sites. See [`invocation.md` → Control planes](invocation.md#control-planes) for the full alias table. Quick summary:

- "cn 控制面" → `--site cn`
- "i18n / row / us 控制面" → `--site i18n` (three aliases for the same site)
- "us-ttp / usttp / US-TTP 控制面" → `--site us-ttp` (**different from "us"!**)
- "eu-ttp / euttp / EU-TTP 控制面" → `--site eu-ttp`

The ByteCloud host is no longer forge-cli's to resolve — the `bytecloud-auth-go-sdk` owns the `(auth-network, site)` → host table, and forge maps `--network` (office/prod) onto the SDK's `AuthNetwork` at client construction. If the environment routes differently, override per-invocation with the SDK's env var:

```
BYTECLOUD_CLI_CLOUD_HOST=https://cloud-custom.internal forge auth login --site us-ttp --network prod
```

Report the working host back to the forge team so it can be raised with the ByteCloud SDK owners.

## Sandbox DNS / resolver failures

Symptoms: a Forge observation command fails with `no such host`, `Could not resolve host`, `EAI_NONAME`, or resolver errors against `127.0.0.1:53` / `::1`. Auth status is valid. Affects `forge job meta|event|log|metrics|deepinsight|wandb|tensorboard ...`, `forge job webshell ...`, and direct Primus / Primus History / Reckon Tracing probes.

Root cause: these surfaces depend on corp-internal DNS and control-plane routing. Sandboxed execution often cannot resolve internal hostnames even when the user's host network can.

Recovery:

- Rerun the same command outside the sandbox. Do not continue debugging inside the sandbox once a resolver error is confirmed.
- Treat a sandbox-only resolver error as an environment artifact, not as evidence that the Forge service or training job is broken — do not raise it as a service incident.
- If the same command also fails outside sandbox, fall through to [Auth failures](#auth-failures) or [Control-plane / ByteCloud host issues](#control-plane--bytecloud-host-issues) depending on the actual error class.

## Skill / CLI version drift

Symptoms: the skill warns that the installed version requires a newer `forge` than what is currently on PATH; or `forge skill status` reports `content_hash` drift between the marker and the embedded skill.

Recovery:

```bash
# Upgrade the CLI (this also re-syncs the bundled skill)
forge upgrade

# Confirm current skill deployment
forge skill status

# Force resync if the marker looks stale
forge skill update --force
```

If the skill came from AgentBuddy or another marketplace, Forge treats that directory as externally managed and does not overwrite it, even with `--force`. Refresh or migrate a Global AgentBuddy installation with:

```bash
npm_config_registry=https://bnpm.byted.org npx agentbuddy@latest skill update --migrate -g
```

For a Project install, omit `-g` and run the command from the project root.

## Compile log redaction seems to hide something important

`code compile get` automatically redacts token / jwt / secret / cookie / authorization-like keys from the build log. This is intentional and must not be disabled. If the redaction hides a value the user needs to debug:

- Re-run the compile locally in a controlled environment if you need to inspect secrets.
- For build-log troubleshooting, focus on non-secret fields (status, timestamps, step messages).

## Rate limiting / gateway errors

Rate limiting is handled by the `paas-gw` gateway, not the client. Symptoms include `429` or gateway-specific envelopes. Recovery:

- Back off and retry. Do not reintroduce a client-side limiter.
- If the error persists, check whether the user is inadvertently running many parallel invocations (CI loop, watch script, etc.).

## Unexpected `runtime.GOOS == "windows"` behavior

The skill bundle distribution (canonical + symlink) is macOS / Linux only in the first release. On Windows, `forge skill install` / `update` will fail fast with an unsupported-platform error.
