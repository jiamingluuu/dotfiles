# Anywheredoor / 任意门

Use `bytedcli bits anywhere` for Anywheredoor Android/iOS device enrollment and proxy debugging. The capture flow remains `listen` / `status` / `watch` / `get` / `stop`; additional commands cover device enrollment, share-link resolution, mock inspection/mutation, filters, and black paths.

## Safety

- Prefer `--json` for agent workflows.
- Use `device list` first and pass a real device id to state-changing commands. `did=0` is useful for some readonly list/config checks, but mock create/enable/delete requires a real device id.
- Treat these commands as state-changing when submitted: `device create`, `listen`, `stop`, `mock create-local`, `mock create-remote`, `mock create-rewrite`, `mock update-rewrite`, `mock enable`, `mock disable`, `mock delete`.
- `device create` requires `--yes` before opening the authorization flow. The device may still require visible confirmation in the App.
- Treat the Arena Any-Code as a short-lived secret (Android/iOS: 6 to 10 characters). Prefer `--arena-code-stdin` or the hidden TTY prompt; do not put real codes in shell history, logs, or documents.
- All Mock writes require `--yes`. Rewrite commands default to previewing the complete request without writing; explicit `--dry-run` produces the same preview. Probe rules must use unique non-business paths and restrictive matching conditions, then be deleted after validation; do not assume creation is disabled.
- Do not put real app ids, device ids, mock ids, PSMs, or internal URLs in public examples. Use placeholders like `1234`, `1234567890123456`, and `/api/demo`.

## Device Selection

```bash
bytedcli --json bits anywhere device list --app-id 1234
```

Pick a real `did` from this list before starting capture or changing mocks.

## Android Device Enrollment

`device create` supports adb-connected Android debug builds where `run-as <package>` can read the App's Anywheredoor SharedPreferences. The default package is Douyin; use `--package <application-id>` for another debuggable package.

The command reads the App-side DID, checks whether the backend already has `auth=true`, and skips the authorization flow when the device is already authorized. Otherwise it submits the Arena Any-Code and polls the backend for the same DID. Device UI progress alone is not success: only backend `auth=true` produces a passed verification.

```bash
# Read-only preflight plus code validation; does not open the authorization UI.
printf '%s\n' 'SAMPLECODE' | bytedcli --json bits anywhere device create \
  --app-id 1234 \
  --adb-serial sample-device \
  --arena-code-stdin \
  --dry-run

# Open the authorization UI, complete visible confirmation, and wait for readback.
printf '%s\n' 'SAMPLECODE' | bytedcli --json bits anywhere device create \
  --app-id 1234 \
  --adb-serial sample-device \
  --arena-code-stdin \
  --wait-seconds 120 \
  --yes
```

The default wait is 60 seconds; `--wait-seconds` accepts `0` through `300`. DID output is masked by default. Use `--show-did` only when the full identifier is explicitly required. Dry-run can succeed while returning `verification.status=not-run`; a non-dry-run only returns `passed` after backend `auth=true`. If `auth=true` is not observed after a successful readback, the command returns structured pending data and `BITS_ANYWHEREDOOR_AUTH_PENDING`; check visible confirmation, code validity, and network state before using `device list` to read back.

## iOS Device Enrollment

`device create --platform ios` supports debuggable iOS Apps with AppUse and `AWEAnywhereArena`. The command reads the SDK DID through `BDTrackerProtocol.deviceID`, opens the SDK-provided Any-Code dialog, and polls the backend for the same DID. Use `--airbuild` when AppUse runs in the current AirBuild space.

```bash
# Local AppUse dry-run.
printf '%s\n' 'SAMPLE' | bytedcli --json bits anywhere device create \
  --platform ios \
  --app-id 1234 \
  --appuse-port 20100 \
  --arena-code-stdin \
  --dry-run

# AirBuild authorization and backend readback.
printf '%s\n' 'SAMPLE' | bytedcli --json bits anywhere device create \
  --platform ios \
  --app-id 1234 \
  --appuse-port 20100 \
  --airbuild \
  --arena-code-stdin \
  --wait-seconds 120 \
  --yes
```

The target App must be foreground and AppUse must report the selected port. The command initializes the official Arena window, verifies its `UIAlertController`, targets that dialog's input/action views, and uses the SDK submission flow. It does not call private grant/bind APIs directly.

## Original Capture Flow

```bash

bytedcli --json bits anywhere listen \
  --app-id 1234 --did 1234567890123456

bytedcli --json bits anywhere status \
  --app-id 1234 --did 1234567890123456

bytedcli bits anywhere watch \
  --app-id 1234 --did 1234567890123456 \
  --url-path /api/demo \
  --show-curl

bytedcli bits anywhere watch \
  --app-id 1234 --did 1234567890123456 \
  --window-sec 1800 \
  --include-snapshot \
  --url-path /api/demo

bytedcli bits anywhere get \
  --app-id 1234 --did 1234567890123456 \
  --history-id 1447858190 --env 8 --curl

bytedcli --json bits anywhere stop \
  --app-id 1234 --did 1234567890123456
```

`watch` defaults to HTTP polling mode and prints `id`, `path`, `log_id`, and `env`. Use `--window-sec` with `--include-snapshot` to dump recent captures; use `--show-curl` to render each matched capture as a curl command. `get --history-id <id> --env <env> --curl` converts one captured record into curl.

Advanced compatibility options from the original flow are still available:

- `--skip-listen`: watch without calling `listen` first.
- `--mode ws`: Arena WebSocket research escape hatch. It is usually silent for non-browser clients, so prefer default poll mode for real debugging.
- `--interval-ms`: polling interval, default `1500`.
- `--url-path`: client-side substring filter plus backend path hint.

The curl renderer removes headers that curl manages itself, such as `Host`, `Content-Length`, and `Accept-Encoding`.

## Share Links

Use `share get --url <url>` when the user only has an Anywheredoor share link. Single-item links contain `_proxy_share_item_id` and `appId`; bulk links contain `_proxy_share_items_id` and `appId`. Add `--curl` only for single-item links.

```bash
bytedcli --json bits anywhere share get \
  --url 'https://example.com/anywheredoor/proxy/share?appId=1234&_proxy_share_item_id=1447858190&env=8'

bytedcli bits anywhere share get \
  --url 'https://example.com/anywheredoor/proxy/share?appId=1234&_proxy_share_item_id=1447858190&env=8' \
  --curl

bytedcli --json bits anywhere share get \
  --url 'https://example.com/anywheredoor/proxy/share?appId=1234&_proxy_share_items_id=sample-share-id'
```

`share` is readonly. It calls the backend share APIs directly and returns the captured request/response envelope; it does not open a browser or scrape the share page.

## Mock

```bash
bytedcli --json bits anywhere mock list \
  --app-id 1234 --did 1234567890123456 \
  --type local --page-size 20

bytedcli --json bits anywhere mock get \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --type local

bytedcli --json bits anywhere mock create-local \
  --app-id 1234 --did 1234567890123456 \
  --name sample-local-mock \
  --method GET \
  --url-path /api/demo \
  --query-filter app=1 \
  --query-filter version_code=123456 \
  --body '{"ok":true}' \
  --serializer json \
  --yes

bytedcli --json bits anywhere mock create-remote \
  --app-id 1234 --did 1234567890123456 \
  --name sample-remote-mock \
  --method POST \
  --url-path /api/stream \
  --query-filter mode=demo \
  --target-url 'https://example.com/mock/stream?session=sample' \
  --yes

bytedcli --json bits anywhere mock enable \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --yes

bytedcli --json bits anywhere mock disable \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --yes

bytedcli --json bits anywhere mock delete \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --yes
```

Supported mock type names: `local`, `remote`, `status-code`, `throttling`, `idl`, `rewrite`.

### Creation And Enabled State

`mock create-local`, `mock create-remote`, and `mock create-rewrite` all accept the
same optional `--enable` flag. It controls the request field sent to the server:

| CLI option | Create request | Observed created state |
| --- | --- | --- |
| Omit `--enable` | `enabled: false` | Enabled |
| Pass `--enable` | `enabled: true` | Enabled |

**The current backend creates all three Mock types enabled, including when
`enabled: false` is sent. Omitting `--enable` does not create a disabled rule.**
The flag does not replace `--yes`, which confirms the write. To stop a created rule,
use `mock disable --app-id <id> --did <id> --mock-id <id> --yes`; that separate
enabled-state operation is effective. Creation commands do not automatically disable
rules after creating them.

Rewrite preview/results distinguish `requestedEnabled` (the requested value) from
`enabled` (the expected state in a preview, or the verified state after submission).
For example, the default is `requestedEnabled: false` with `enabled: true`.

Supported serializer names for `create-local`: `json`, `text`, `html`, `javascript`, `protobuf`, `webcast-packer`, `webcast-im`, `stream-forecast`, `script`.

`mock create-local` can narrow matching beyond path/method with Anywheredoor `extra_filter`. Prefer repeatable `--query-filter key=value` for query equality checks; the CLI writes the backend `content[0].extra_filter` JSON string. For advanced backend-supported shapes, pass raw JSON with `--extra-filter '<json-object>'`. Do not combine `--query-filter` and `--extra-filter`.

`mock create-remote` uses the same source matching flags and rewrites matching requests to `--target-url`. Query values in `--query-filter` match the source request; query values inside `--target-url` are sent to the target. The target must be an absolute HTTP(S) URL without credentials, fragments, or duplicate query keys.

## Full Rewrite Rules

Use `mock create-rewrite` / `mock update-rewrite` for Rewrite rules that modify headers,
query parameters, host/path/URL, request or response bodies, and response status codes.
Only the new Rewrite creation and update use the v2 Mock API. Existing
`mock list/get`, including `--type rewrite`, retain v1; new write preflight and readback
also reuse those v1 readers. Common `mock enable`, `mock disable` and `mock delete`
retain their v1 APIs and accept the same Rewrite mock ID. The backend rejects editing these rules through v1 with a
message asking to edit in Bits. The CLI selects the required route automatically. Rewrite rules use type `rewrite`
and structured matching/replacement rules; `create-remote` uses type `remote` for
target-URL forwarding.

Both commands require `--app-id`, a real positive `--did` (not `0`), `--name`, and
exactly one of `--config '<json>'` or `--config-file <path>`. Inline and file input use
the same configuration schema and cannot be combined. Update also requires `--mock-id` and verifies that the selected ID is
a Rewrite rule before writing. Authentication reuses `bytedcli auth login` and the
BITS user JWT; a BITS OpenAPI token is not needed for this workflow.

By default, both commands validate the configuration and preview the complete request
and activation behavior without writing. Explicit `--dry-run` produces the same preview;
it cannot be combined with `--yes`. Use `--yes` to submit. Update previews read the existing
rule to verify the target and show its current configuration and enabled state.
Creation accepts the same `--enable` flag as Local/Remote and sends the same boolean
request field. **Creating with `--yes` immediately enables the new rule even when
`--enable` is omitted**, as explained in Creation And Enabled State.
Update replaces the complete name, locations and ordered rules, preserving the current
enabled state; omitted locations/rules are not merged with the existing configuration.
Preview the full replacement before submitting. Concurrent external edits are not
protected by an atomic version check.

Create `rewrite.json` with this structured configuration:

```json
{
  "locations": [
    { "host": "example.com", "path": "/api/demo", "query": "mode=demo" }
  ],
  "rules": [
    {
      "type": "add-header",
      "scope": "request",
      "replace": { "key": "X-Demo", "value": "sample" }
    },
    {
      "type": "body",
      "scope": "response",
      "match": { "value": "old-value" },
      "replace": { "value": "new-value" }
    }
  ]
}
```

```bash
# Preview by default; --dry-run is optional
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 \
  --name sample-rewrite --config-file ./rewrite.json

# The same configuration can be supplied inline without creating a file
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 --name sample-rewrite \
  --config '{"locations":[{"host":"example.com","path":"/api/demo"}],"rules":[{"type":"body","scope":"response","match":{"value":"old-value"},"replace":{"value":"new-value"}}]}' \
  --dry-run

# Submit once, create enabled, and verify by readback
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 \
  --name sample-rewrite --config-file ./rewrite.json --yes

# Explicitly request enabled creation; the observed state is also enabled
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 \
  --name sample-rewrite --config-file ./rewrite.json --enable --yes

# Inspect an existing Rewrite and preview a complete replacement
bytedcli --json bits anywhere mock list \
  --app-id 1234 --did 1234567890123456 --type rewrite
bytedcli --json bits anywhere mock get \
  --app-id 1234 --did 1234567890123456 --mock-id 987654321 --type rewrite
bytedcli --json bits anywhere mock update-rewrite \
  --app-id 1234 --did 1234567890123456 --mock-id 987654321 \
  --name sample-rewrite --config-file ./rewrite.json --dry-run

# Submit the replacement after reviewing it
bytedcli --json bits anywhere mock update-rewrite \
  --app-id 1234 --did 1234567890123456 --mock-id 987654321 \
  --name sample-rewrite --config-file ./rewrite.json --yes
```

`locations` and `rules` must both be non-empty arrays. The same ordered rules apply to
every location, matching the console form. Unknown configuration keys and numeric rule
type codes are rejected. This input is a CLI configuration, not raw `mock get` output.

| Location field | Meaning / default |
| --- | --- |
| `path` | Required non-empty request path |
| `host` | Optional host; empty means any host |
| `hostMatch` | `exact` (default) or `regex` |
| `pathMatch` | `exact` (default) or `prefix` |
| `query` | Optional query matching string, e.g. `mode=demo&lang=en`; empty means any query |
| `psm` | Optional source PSM; empty by default, as when typing a custom path in the console |
| `xCommand` | Optional source `x-command` header equality filter |

| Rule `type` | `scope` |
| --- | --- |
| `add-header`, `modify-header`, `remove-header`, `add-or-modify-header`, `body` | Explicit `request`, `response`, or `both` required |
| `host`, `path`, `url`, `add-query`, `modify-query`, `remove-query`, `add-or-modify-query` | `request`; defaults to this value |
| `response-status-code` | `response`; defaults to this value |

`match` accepts `key`, `value`, `full`, `caseSensitive`, `keyRegex`, `valueRegex`.
Strings default to empty (match all) and booleans to `false`. Host/path/URL/body/status
rules operate on values and do not accept key matching. Status-code matching takes an
empty string or a complete HTTP status string (`100` through `599`), without regex options.
Regex is interpreted by the backend; use its supported syntax and `$1` capture references.
Body rewriting is textual matching/replacement, not a JSON patch operation.

`replace` accepts `key`, `value`, and `firstOnly` (`false` by default: replace all matches).
Non-removal rules require `replace.value`; an explicit empty string clears the matched
value. Add/add-or-modify rules additionally require a non-empty `replace.key` and do not
accept `match` or `firstOnly: true`. Remove rules do not accept `replace`. Status-code
replacement requires an HTTP status string (`100` through `599`).

Success requires name, content (including rule order) and enabled-state readback to match.
`verification: passed` confirms the saved configuration. Traffic changes may propagate
after that readback; exercise a matching request and allow for propagation when checking
the actual rewrite effect.
`BITS_ANYWHEREDOOR_REWRITE_PARTIAL_SUCCESS` means the write was submitted but verification
failed; the error includes the mock ID. `BITS_ANYWHEREDOOR_REWRITE_OUTCOME_UNKNOWN` means
the server may have accepted a write whose response failed. Inspect `mock list/get` before
retrying either case. Write requests are not automatically retried. Existing
`mock enable`, `mock disable`, and `mock delete` manage the resulting rule.

## Filter And Black Path

```bash
bytedcli --json bits anywhere filter get \
  --app-id 1234 --did 1234567890123456

bytedcli --json bits anywhere black-path get --app-id 1234
```

These are readonly inspection commands.
