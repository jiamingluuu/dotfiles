# Goofy Deploy

---

## Quick Preview / 快速预览部署

```bash
# Deploy current directory to a quick preview
bytedcli goofy preview deploy ./ --alias <alias>

# Update an existing alias
bytedcli goofy preview deploy ./dist --alias <alias> --override

# List previews
bytedcli goofy preview list --page 1 --page-size 20

# Remove a preview
bytedcli goofy preview remove --preview-id <preview_id>
bytedcli goofy preview remove --alias <alias>

# Open preview dashboard
bytedcli goofy preview dashboard
```

自动识别目录结构（`deploy.yml` / Next.js / 静态站点 / 构建产物），详见 `preview-directory.md`。

---

## Normal Project Deploy / 普通项目部署

### Sites

```bash
# List supported sites
bytedcli goofy deploy list-sites
```

### Common

```bash
# Get Region Name By Region Id (such as: 2001 -> China-North)
bytedcli goofy deploy region-to-region-name --region <region_id>

# Get Region ID By Region Name (such as:  China-North -> 2001)
bytedcli goofy deploy region-name-to-region --region <region_name>
```

### Search Projects

```bash
# Search projects by name
bytedcli goofy deploy project search --mode by-name --query example-app
# Search projects by Scm Name
bytedcli goofy deploy project search --mode by-scm --query example/app
# Search projects by Git Repo
bytedcli goofy deploy project search --mode by-git --query example-repo
# Search projects by route
bytedcli goofy deploy project search --mode by-route --query deploy.example.com

# Search uses the new OpenGlobalSearchV3 API by default.
# Exception: --mode by-route always uses the legacy API for now (known V3 issues).
# Switch back to the legacy global search API if needed:
bytedcli goofy deploy project search --mode by-name --query example-app --legacy-search
# or via env var (flag wins over env; accepted values: legacy | v3):
BYTEDCLI_GOOFY_SEARCH_API=legacy bytedcli goofy deploy project search --mode by-name --query example-app
```

### Teams

```bash
# List teams visible to the current account
bytedcli goofy deploy team list

# Get team details
bytedcli goofy deploy get-team --team-id <team_id>
```

`team list` accepts `--include-memberships-via-departments` and `--force-refresh-cache` to include inherited memberships and refresh the membership cache.

### Projects

`project list` requires exactly one of `--team-id` and `--psm`. Project, Region and Channel list JSON includes `page`, `page_size`, `page_count` (items on this page), and `has_more` (the server value, or `null` when unavailable). Pagination options require positive integers.

```bash
# List projects in a team
bytedcli goofy deploy project list --team-id <team_id> --page 1 --page-size 20

# List projects by FaaS PSM
bytedcli goofy deploy project list --psm <psm>

# Create a Web or Node app
bytedcli goofy deploy project create \
  --team-id <team_id> \
  --english-name <english_name> \
  --name <name> \
  --app-type web \
  --scm-name <scm_name> \
  --framework web-default \
  --artifact-source scm

bytedcli goofy deploy project create \
  --team-id <team_id> \
  --english-name <english_name> \
  --name <name> \
  --app-type node \
  --scm-name <scm_name> \
  --framework node-default \
  --psm <psm>

# Get project details
bytedcli goofy deploy get-project --app-id <app_id>

# Get project build configuration (app type, SCM, build/deploy platform)
bytedcli goofy deploy get-build-config --app-id <app_id>
```

### Regions & Channels

`region update` previews `{dry_run, region_id, body}` by default without an API call. Pass `--yes` to PATCH exactly that body. Channel `page_count` counts rows after local Region filtering; `has_more` remains the server value.

Compatibility: six old flat Channel names remain hidden for published scripts. `list-regions`, `list-projects-in-team` and its `list-projects` alias remain hidden and share the grouped actions. `--page-num` remains hidden in five list families (project, region, channel, deployment, preview); use `--page` in new calls. No removal date is scheduled.

```bash
# List deployment regions for a project
bytedcli goofy deploy region list --app-id <app_id>

# Create a region with a main channel
bytedcli goofy deploy region create \
  --app-id <app_id> \
  --region-name <region_name> \
  --app-type web \
  --deploy-config-source config-file \
  --deploy-service csr \
  --config-file <config_file> \
  --domain-prefix <domain_prefix>

bytedcli goofy deploy region create \
  --app-id <app_id> \
  --region-name <region_name> \
  --app-type node \
  --deploy-config-source direct \
  --runtime nodejs22

# Update region domain prefixes
bytedcli goofy deploy region update --region-id <region_id> --app-type web --domain-prefix <domain_prefix>

# Apply the previewed domain update
bytedcli goofy deploy region update --region-id <region_id> --app-type web --domain-prefix <domain_prefix> --yes

# Create a deployment channel (requires region-id) with env-name based traffic matching
bytedcli goofy deploy channel create \
  --region-id <region_id> \
  --name <channel_name> \
  --env-name <env_name>

# Create a deployment channel with header-based traffic matching
# Header mode does not require --env-name; --header-key and --header-value must be provided together; --header-op defaults to 1 (= equals)
bytedcli goofy deploy channel create \
  --region-id <region_id> \
  --name <channel_name> \
  --header-key fe-env \
  --header-value <header_value>

# Create a deployment channel with URL query based traffic matching
# Query matching is a distinct Goofy rule type. Do not pass --env-name with it, or Goofy may parse the request as a PPE rule and discard the query condition.
# --query-key and --query-value must be provided together.
# --query-op supports equals, includes, and regex, and defaults to equals.
# Environment-name, header, and query matching cannot be combined.
bytedcli goofy deploy channel create \
  --region-id <region_id> \
  --name <channel_name> \
  --query-key x-tt-env \
  --query-value <query_value> \
  --query-op equals

# Delete a non-main channel. The first command is a dry-run; --yes applies.
# Main channels are always rejected.
bytedcli goofy deploy channel delete --channel-id <channel_id>
bytedcli goofy deploy channel delete --channel-id <channel_id> --yes

# List deployment channels for a project
bytedcli goofy deploy channel list --app-id <app_id>
bytedcli goofy deploy channel list --app-id <app_id> --env-name <env_name>
bytedcli goofy deploy channel list --app-id <app_id> --keyword <name_substring>
# Filter channels by deploy unit (region) ID; applies to the current page
bytedcli goofy deploy channel list --app-id <app_id> --region-id <region_id>

# Get channel details
bytedcli goofy deploy channel get --channel-id <channel_id>

# Merge Web BFF or Node runtime environment variables before the first deployment.
# The command detects the channel type and selects the matching PATCH payload automatically.
# Use a protected KEY=VALUE file for sensitive values. The first command is a dry-run.
bytedcli goofy deploy channel update-bff-env \
  --channel-id <channel_id> \
  --bff-env-file <path_to_env_file>
bytedcli goofy deploy channel update-bff-env \
  --channel-id <channel_id> \
  --bff-env-file <path_to_env_file> \
  --yes
```

The file contains one `KEY=VALUE` entry per line; protect sensitive files with mode `0600` and delete
them after use. For non-sensitive values, repeat `--bff-env KEY=VALUE` instead; the two input forms are
mutually exclusive. `channel update-bff-env` detects Web BFF versus Node channel configuration,
preserves variables not provided by the caller, verifies the complete saved target with a readback,
reports `appType` as `web` or `node`, and omits values from its result. Run it after channel
creation and before the first `deploy-new` or `deploy-version`, so the first runtime instance starts
with the intended configuration.

```bash
# Reorder channel traffic priority for a deploy unit.
# --channel-ids is a comma-separated ordered list: the array order is the priority
# order (highest first). Submit every non-baseline channel of the deploy unit in
# that order, matching the deploy console behavior (the catch-all "全流量" channel
# is excluded). The first command is a dry-run; add --yes to apply.
bytedcli goofy deploy channel update-priority --channel-ids <channel_id_1>,<channel_id_2>
bytedcli goofy deploy channel update-priority --channel-ids <channel_id_1>,<channel_id_2> --yes
```

### Deployments

```bash
# List deployment history for a project
bytedcli goofy deploy list-deployments --app-id <app_id> --page 1 --page-size 20

# List deployment history for a specific channel (app-id is not required)
bytedcli goofy deploy list-deployments --channel-id <channel_id>

# Provide both flags; --channel-id takes precedence and --app-id is ignored
# (a note is emitted in text mode; JSON output includes ignored_app_id: true)
bytedcli goofy deploy list-deployments --app-id <app_id> --channel-id <channel_id>

# Get deployment details (by ID or URL)
bytedcli goofy deploy get-deployment <deploy_url_or_id>
bytedcli goofy deploy get-deployment --deploy-id <deploy_id>

# Diagnose a deployment failure (by ID or URL)
bytedcli goofy deploy diagnose <deploy_url_or_id>
bytedcli -j goofy deploy diagnose <deploy_url_or_id>
# Also fetch and render the latest pipeline node log (last 300 lines)
bytedcli goofy deploy diagnose <deploy_url_or_id> --show-deployment-log
```

### Triggering Deployments

#### Deploy New Version (from git branch + commit)

```bash
bytedcli goofy deploy deploy-new \
  --channel-id <channel_id> \
  --git-branch <branch_name> \
  --commit-hash <commit_hash>

# US-TTP also requires an explicit reviewer type and reviewer username
bytedcli --site us-ttp goofy deploy deploy-new \
  --channel-id <channel_id> \
  --git-branch <branch_name> \
  --commit-hash <commit_hash> \
  --reviewer-type organization \
  --reviewer sample-reviewer

# Deploy and wait for completion
bytedcli goofy deploy deploy-new \
  --channel-id <channel_id> \
  --git-branch <branch_name> \
  --commit-hash <commit_hash> \
  --wait --wait-timeout-sec 900 --poll-interval-sec 15
```

### Deploy Existing Version (from existed scm version)

```bash
bytedcli goofy deploy deploy-version \
  --channel-id <channel_id> \
  --scm-version <version>

# Deploy and wait
bytedcli goofy deploy deploy-version \
  --channel-id <channel_id> \
  --scm-version <version> \
  --wait --poll-interval-sec 10
```

US-TTP deployment commands require both `--reviewer-type` and `--reviewer`. Supported reviewer
types are `person` (USTS individual), `organization` (NOC group), and `custom-group` (USTS group).
The reviewer value is the username returned by Goofy's candidate list for the selected type. This
applies to `deploy-new`, `deploy-version`, `deploy-tar`, `publish`, and `retry`.

### Deploy a TAR Artifact (quick TAR deployment, Web apps only)

```bash
# Deploy from a project root (auto-detects dist/build/out) or a build directory
bytedcli goofy deploy deploy-tar --channel-id <channel_id> .
bytedcli goofy deploy deploy-tar --channel-id <channel_id> ./dist

# Or a prebuilt tarball, with description and wait-for-completion
bytedcli goofy deploy deploy-tar --channel-id <channel_id> ./build.tar.gz \
  --description "hotfix" --wait
```

Uploads the tarball for the channel, then creates the deployment with
`enableQuickTarDeployment` (TAR served from TOS). Directory detection finds the
deployable directory (deploy.yml at root → as-is; project root → dist/build/out)
but, unlike `goofy preview deploy`, never generates a deploy.yml — the tarball
must already match the app's own deployment configuration.

### Deployment Lifecycle

```bash
# Cancel a running/pending deployment (by ID or URL)
bytedcli goofy deploy cancel <deploy_url_or_id>
bytedcli goofy deploy cancel --deploy-id <deploy_id>

# Retry a failed deployment with the same parameters (by ID or URL)
bytedcli goofy deploy retry <deploy_url_or_id>
bytedcli goofy deploy retry --deploy-id <deploy_id> --wait --poll-interval-sec 10

# Rollback channel to previous online version
bytedcli goofy deploy rollback --channel-id <channel_id>
bytedcli goofy deploy rollback --channel-id <channel_id> --wait --poll-interval-sec 10
```

## Bulk Deploy / Clone Deployments & Regions Across Regions

Bulk deploy is a Goofy Deploy platform capability. Get the latest bulk
deploy instructions from the Goofy Deploy platform team; do not invoke any
external CLI for it.

Typical use cases: bringing an app up in a new region by cloning its existing
regions/channels/deployments from a source region, or keeping a secondary
region in sync with the primary.

## Relay / DevServer Request Relay

Use this command for day-to-day local Request Relay / DevServer debugging. bytedcli reuses
the current login session to provide the ByteCloud JWT to the relay runtime; do
not ask users to paste JWTs into commands, logs, docs, or scripts.

```bash
# Agent workflow: explicitly create/reuse the channel and get its channel_id.
# --env-name is required. Pass a stable logical name; bytedcli resolves the
# final ppe_ or boe_ prefix from the selected Goofy Deploy region.
# The first setup waits for the route-config deployment to finish. The default
# timeout is 600 seconds with a 10-second polling interval.
bytedcli --json goofy relay setup \
  --app-id <app_id> \
  --region China-North \
  --env-name my_feature

# Read .data.channel_id and .data.traffic_match from the JSON result, then
# start a managed background relay. Success is reported only after server_info.
bytedcli --json goofy relay start \
  --channel-id <channel_id> \
  --target <local_devserver_url> \
  --detach \
  --preflight

# Inspect and stop the managed relay.
bytedcli --json goofy relay status --channel-id <channel_id>
bytedcli goofy relay logs --channel-id <channel_id> --tail 100
bytedcli goofy relay logs --channel-id <channel_id> --tail 100 --follow
bytedcli --json goofy relay stop --channel-id <channel_id>

# Foreground compatibility path against an existing channel.
bytedcli goofy relay start \
  --channel-id <relay_channel_id> \
  --target <local_devserver_url>

# One-command compatibility path. This performs channel/deployment writes before
# starting Relay, so agents should prefer the explicit setup workflow above.
bytedcli goofy relay start \
  --app-id <app_id> \
  --region China-North \
  --env-name my_feature \
  --target <local_devserver_url>

# Full Web Server/GGW -> local devserver verification
bytedcli --json goofy relay doctor \
  --channel-id <channel_id> \
  --env-name <resolved_env_name> \
  --target <local_devserver_url> \
  --url <public_web_server_url>
```

Relay command options:

| Option                     | Use                                                                                                                                                       |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--channel-id <id>`        | Relay channel ID returned as `.data.channel_id` by `relay setup --json`.                                                                                  |
| `--env-name <name>`        | Required for setup. A logical suffix such as `my_feature`, or a complete matching `ppe_` / `boe_` name.                                                   |
| `--target <url>`           | Local devserver endpoint. The relay client only accepts local addresses such as `http://127.0.0.1:3000`, `http://localhost:5173`, or `http://[::1]:3000`. |
| `--detach`                 | Run as a managed background process and return after the Relay protocol is ready.                                                                         |
| `--duration-ms <ms>`       | Optional run duration. Omit or pass `0` to run until interrupted.                                                                                         |
| `--schedule-vdc <vdc>`     | Optional `x-schedule-vdc` header for WebSocket upgrade when a TLB URL needs VDC routing.                                                                  |
| `--log-level <level>`      | `debug`, `info`, `warn`, or `error`.                                                                                                                      |
| `--log-format <format>`    | `text` or `json`. Use `json` when an outer agent needs structured relay logs.                                                                             |
| `--preflight`              | Check that the local target is reachable before connecting to relay-server.                                                                               |
| `--diagnostic-file <path>` | Write bounded redacted Relay diagnostics to a JSONL file.                                                                                                 |
| `--no-ui`                  | Disable the interactive status display for foreground runs.                                                                                               |

Relay diagnostics:

`relay setup --json` returns `channel_id`, `resolved_env_name`, and the exact
`traffic_match` (`x-tt-env: <resolved_env_name>`). Use `relay doctor` for the
complete Web Server/GGW to local devserver round trip. bytedcli obtains a fresh
ByteCloud JWT from the current login state; never write JWTs into scripts,
tickets, logs, or shared docs.

When setup creates a new DevServer channel, it also waits for the initial
route-config deployment to reach a terminal state. The default maximum wait is
600 seconds and the default poll interval is 10 seconds; customize them with
`--wait-timeout-sec` and `--poll-interval-sec`. In JSON mode, progress is emitted
as JSONL events on stderr while stdout remains a single final result envelope:

```json
{
  "event": "goofy_relay_setup_progress",
  "data": {
    "phase": "deployment_poll",
    "deployment_id": "123456",
    "deployment_status": 2,
    "wait_timeout_sec": 600,
    "poll_interval_sec": 10,
    "message": "Deployment 123456 status: 2."
  }
}
```

Stable phases are `region_resolved`, `channel_created`, `channel_reused`,
`deployment_discovery`, `deployment_created`, `deployment_poll`, and
`route_published`.

### Maintainer Live E2E

Repository maintainers can run the real Relay lifecycle against the repository's
fixed shared Web test project:

```bash
integration/goofy/run-e2e.sh
```

Run it from the bytedcli repository root after `bytedcli auth status` confirms a
usable CN login. By default the runner executes `npm run build:code` before any
live API call so the E2E uses the latest `dist/bytedcli.js`. Use `--skip-build`
only after explicitly confirming that `dist` is fresh. The process must be able
to write the normal bytedcli user data directory because detached Relay state
and logs are stored there. In a filesystem-sandboxed agent, grant access to that
directory or run the command outside the sandbox.

The default run sequentially covers `China-North` and `China-BOE`. It validates
the read APIs, creates a uniquely named DevServer channel, waits for the first
route deployment, runs the complete Relay doctor, starts/stops a managed Relay,
and deletes the channel. This is a real write test and is intentionally not part
of `npm test` or CI. Private sanitized reports are written under
`integration/goofy/.runs/`.

Use `--keep-resources` only for debugging. A kept-resource run exits non-zero and
prints the exact resources that require manual cleanup.

Exit code `0` means both Regions and cleanup passed, `1` means a functional or
cleanup failure, and `2` means a build/auth/runtime-directory prerequisite was
not satisfied.

Relay runtime behavior notes (`bytedcli goofy relay`):

- Requires Node.js >= 20.0.0.
- Does not accept `--region`; the relay-server endpoint is selected from the control-plane token API's `deployUnitRegion`.
- Supports region IDs `1001` (`China-BOE`), `1002` (`US-BOE`), `1005` (`China-BOE2`), `2001` (`China-North`), `2003` (`ChinaSinf-North`), `2004` (`China-East`), `3001` (`Singapore-Central`), and `3007` (`Asia-SouthEastBD`).
- Uses Relay Protocol V2: request/response bodies are streamed end-to-end over WebSocket binary frames, not JSON base64.
- Applies backpressure with a 4 MB credit window per request per direction and returns credit in 512 KB batches.
- Applies WebSocket send-queue backpressure with a 16 MB high watermark, 4 MB low watermark, and 30 second drain timeout.
- One relay connection allows up to 256 concurrent requests. If `RELAY_CLIENT_BUSY` appears, wait, reduce concurrency, or split traffic across channels/clients.
- Keeps request/response size protections and metadata limits. Large uploads/downloads should use another debug path.
- Logs use stable `code`, `message`, and `action` fields; sensitive values such as JWTs, cookies, authorization headers, tokens, secrets, credentials, and sessions are masked.
- In interactive TTYs with text logs, shows a two-line terminal status summary after `server_info` confirms the relay connection. It reports connection state, active requests, recent success rate, P50/P95, reconnects, and cumulative request/response bytes. Use `--log-format json`, CI/non-TTY output, or pass `--no-ui` when an outer agent needs plain logs only.
- `--diagnostic-file` writes bounded redacted JSONL diagnostics with phases, memory snapshots, active requests, termination reasons, and WebSocket queue snapshots. Files are `0600`, each event is capped at 64 KB, the file is capped at 8 MB, and bodies are not written.
- `--doctor` checks Node.js, local target, RelayConnectionToken, region endpoint, WSS auth/upgrade, `client_hello`, and a real Webserver/GGW -> relay-server -> relay runtime -> local devserver round trip. It uses a random `x-gf-relay-doctor-nonce`, fixed `x-tt-trace: 1`, and `get-svc: 1`; success requires the returned nonce to match.
- `client_hello` includes a local environment summary for relay-status diagnostics: human-readable OS names derive from native system metadata (`sw_vers` on macOS and `/etc/os-release` on Linux), fall back to OS type/release when unavailable, and service-container VDC/vregion detection is improved when platform environment variables are incomplete.
- Resource guidance: reserve about 1 GB memory for relay sessions. For Node.js, `NODE_OPTIONS=--max-old-space-size=768` leaves room for native buffers and sockets.
- Keep bytedcli up to date so `bytedcli goofy relay` reports the current endpoint/region support, native OS-name diagnostics, and service-container region metadata.

Relay runtime version notes:

| Version  | Notes                                                                                                                                                            |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| recent   | Relays derive service-container vregion/region metadata from VDC information as a fallback when direct environment variables are unavailable.                    |
| `0.4.10` | Uses native OS metadata for `client_hello` environment names instead of the `os-name` package, avoiding stale OS version mappings.                               |
| `0.4.9`  | Reports relay runtime environment metadata, including host/user/OS/Node/cwd and service-container or Devbox signals, for control-plane relay-status diagnostics. |
| `0.4.8`  | Adds text-frame body fallback and response body ACK diagnostics for WebSocket paths where binary frames are unreliable.                                          |
| `0.4.7`  | Raises the local response body budget to 100 MB and the single-client concurrency limit to 256 requests.                                                         |

Troubleshooting signals:

| Code or symptom                                                      | Meaning / action                                                                                                |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Node.js version too low                                              | Switch to Node.js >= 20.0.0.                                                                                    |
| `relay_connection_token_failed`                                      | Check that the channel exists and the current user can access it; prefer bytedcli login reuse over manual JWTs. |
| `TARGET_DEVSERVER_UNREACHABLE` / `relay_target_request_failed`       | Start the local devserver and verify `--target`; add `--preflight` for early failure.                           |
| `RELAY_CLIENT_BUSY` / `TOO_MANY_CONCURRENT_REQUESTS`                 | The client hit its 256-request concurrency limit; reduce load or split clients/channels.                        |
| `RELAY_SERVER_BUSY`                                                  | The relay-server instance hit its concurrency limit; retry, switch instance, or ask the platform to scale.      |
| `RELAY_REQUEST_TIMEOUT`                                              | The full relay request timed out; inspect relay-server, relay runtime, and local devserver latency.             |
| `RELAY_REQUEST_TOO_LARGE` / `RELAY_RESPONSE_TOO_LARGE`               | The relay request/response body exceeded the supported budget; reduce body size or use another debug path.      |
| `TARGET_REQUEST_BUDGET_EXCEEDED` / `TARGET_RESPONSE_BUDGET_EXCEEDED` | Buffered request or response data exceeded the connection budget; lower concurrency or reduce body size.        |
| `RELAY_REQUEST_METADATA_TOO_LARGE`                                   | Path, query, or headers are too large; reduce request metadata.                                                 |
| `RELAY_REQUEST_ASSEMBLY_TIMEOUT`                                     | relay-server did not finish sending the request within 30 seconds; retry and inspect relay-server/client logs.  |
| `REPLACED_BY_NEW_CONNECTION`                                         | Another relay client connected to the same channel; the older connection exits.                                 |
| `Unsupported deployUnitRegion`                                       | The channel's region is not configured for relay; ask the Goofy Deploy platform to add endpoint support.        |

When normal start connects but traffic still does not reach the local target, run doctor with the exact
Webserver URL and channel `envName`. Doctor stage output includes `name`, `status`, `message`, `action`,
`durationMs`, and `details`; use stage duration to locate whether time is spent in local devserver,
token API, DNS/TLS/WSS, protocol activation, Webserver/GGW owner lookup, or relay round trip.

## Example Workflow

```bash
# 1. List regions
bytedcli goofy deploy region list --app-id 131716
# Output shows region IDs like 224335

# 2. (Optional) create channel
bytedcli goofy deploy channel create \
  --region-id 224335 \
  --name demo-test \
  --env-name ppe_demo_test

# 3. Get project channels
bytedcli goofy deploy channel list --app-id 131716
# Output shows channel IDs like 3520795

# 4. Configure Web BFF or Node runtime variables before the first deployment (dry-run, then apply)
bytedcli goofy deploy channel update-bff-env \
  --channel-id <channel_id> \
  --bff-env-file <path_to_env_file>
bytedcli goofy deploy channel update-bff-env \
  --channel-id <channel_id> \
  --bff-env-file <path_to_env_file> \
  --yes

# 5. Check recent deployments
bytedcli goofy deploy list-deployments --app-id 131716
# Output shows versions like 1.0.0.47

# 6a. Deploy by git branch + commit
bytedcli goofy deploy deploy-new \
  --channel-id 3520795 \
  --git-branch main \
  --commit-hash abc123def456 \
  --wait

# 6b. Or deploy by existed scm version
bytedcli goofy deploy deploy-version \
  --channel-id 3520795 \
  --scm-version 1.0.0.47

# 7. If deployment fails, diagnose it (paste the URL directly)
bytedcli goofy deploy diagnose "https://cloud.bytedance.net/goofy/channel/3520795/deploy?deploymentId=12345678"
#   optionally include the pipeline node log for deeper debugging
bytedcli goofy deploy diagnose 12345678 --show-deployment-log

# 8. Retry the failed deployment
bytedcli goofy deploy retry 12345678 --wait --poll-interval-sec 10

# 9. Or rollback to previous version
bytedcli goofy deploy rollback --channel-id 3520795 --wait --poll-interval-sec 10
```

## Aliases

- 主入口：`goofy deploy *` / `goofy preview *` / `goofy relay *`
- 可用别名：`gd` = `goofy-deploy`

## Vmok 生产者发布

```bash
bytedcli goofy deploy publish --channel-id <channel_id> --version <scm_version> --tag <tag>
bytedcli goofy deploy publish --channel-id <channel_id> \
  --git-branch <branch> --commit-hash <commit> --tag <tag> --wait \
  --wait-timeout-sec 900 --poll-interval-sec 15
```

`--version` 与 `--git-branch` + `--commit-hash` 二选一，`--tag` 必填。Tag 不存在时自动创建，
已存在时移动到新版本。版本升级固定为 patch，只发布 Channel 配置的生产者模块，
消费者版本保持不变。发布后继续使用现有的 `get-deployment`、`cancel` 和 `retry`
命令管理工单。

## Vmok 消费者按 Tag 部署

```bash
bytedcli goofy deploy deploy-version --channel-id <consumer_channel_id> \
  --scm-version <consumer_scm_version> --vmok-remote '@example/module-a=preview'
bytedcli goofy deploy deploy-new --channel-id <consumer_channel_id> \
  --git-branch <consumer_branch> --commit-hash <consumer_commit> \
  --vmok-remote '@example/module-a=preview' --vmok-remote '@example/module-b=stable' --wait
```

根据制品来源选择 `deploy-version` 或 `deploy-new`。`--vmok-remote <module=tag>` 可重复；
消费者有多个需要固定 Tag 的直接依赖时，分别传入该参数。命令会把这些依赖写入
`configForVmokAutomation.overrides`，覆盖消费者制品中的同名直接依赖。深层依赖不在
本命令范围内。
