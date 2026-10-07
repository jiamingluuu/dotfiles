# Footprint Viewlog API

> The officially maintained way to drive this API is the
> `bytedcli log footprint search` command (see `SKILL.md` →
> "Footprint Search (`log footprint search`)"). It validates the
> `log_type` / `region` (backend `idc`) enums, auto-resolves the ByteCloud
> JWT, picks the host via `--network`, and never prints the JWT. Prefer it
> over the raw `curl` / Python calls below. This reference documents the
> underlying HTTP contract for debugging and for environments where the CLI
> is unavailable.

Reference for retrieving logs from Footprint through the raw
`POST /v1/open/bytedcli/viewlog` HTTP API, using an SSO-derived ByteCloud
JWT. This is a different mechanism from the `log footprint get` /
`log footprint download` CLI subcommands documented in `SKILL.md`:

- `log footprint get` → TCE Sync, reads pod-local files via the CLI.
- `log footprint download` → downloads a concrete log file URL via the CLI.
- `log footprint search` → the officially maintained command wrapping this
  same open API (auto JWT, enum validation, `--network` host selection).
- **This reference** → drives the `viewlog` open API directly with
  `curl` / Python `requests` and a manually fetched JWT.

## When to use this

Use the `viewlog` API when the user wants to:

- Fetch / view / download Footprint logs for any supported `log_type`
  (e.g. "get me argos logs for trace abc from Footprint", "pull dorado
  job output from Footprint", "tail the tce logs for this pod via
  Footprint"). See the log-type enum below for the full supported set.
- Drive Footprint programmatically without opening the Footprint UI for
  one of the supported log types.

Do **not** use it for:

- Configuration / admin work in Footprint (release notes, redact lists,
  exemption requests).
- Any `log_type` not listed (or listed with value `false`) in the
  log-type enum below. Reject the request and tell the user the type
  isn't supported yet rather than calling the API.

## Authentication (ByteCloud JWT)

The API requires the `x-Footprint-JWT` header set to a raw ByteCloud
JWT. Obtain it via `bytedcli` (general invocation in
`references/invocation.md`):

```bash
# 1. Make sure the i18n-tt site is authenticated (Footprint uses TikTok SSO)
bytedcli --site i18n-tt auth status

# 2. Log in if needed (opens browser SSO; must run from a network that can
#    reach the login host — see Troubleshooting if you hit 403 [Segregator])
bytedcli --site i18n-tt auth login

# 3. Export the raw ByteCloud JWT into the environment (in-memory only)
export FOOTPRINT_JWT="$(bytedcli --site i18n-tt auth get-bytecloud-jwt-token)"
```

- Never write the JWT to disk or echo it into logs; keep it in the shell
  session env only. Treat a pasted JWT as exposed and let it expire
  (~1 hour).
- If `auth login` cannot complete from the current network (common in a
  prod-network IDE workspace), supply a JWT obtained elsewhere directly
  into `FOOTPRINT_JWT`.

## Endpoint

- Host — pick the one reachable from the current network:
  - **Server / on-cluster (FaaS, ByteCloud, internal pod, IDE workspace, no OG):**
    `https://gkypl7ix.sg-fn.bytedance.net`
  - **OG / office network (user's local laptop, BOE, BOE-VPN):**
    `https://gkypl7ix.sg-fn.tiktok-row.net`
- Path: `POST /v1/open/bytedcli/viewlog`
- Content type: `application/json`
- Required auth header: `x-Footprint-JWT: <jwt>`

> Quick rule of thumb:
>
> - `*.sg-fn.bytedance.net` → reachable only from inside the server /
>   prod-network mesh. Office IPs get `403 [Segregator] ... not allowed
to connect to OG from Prod Network`.
> - `*.sg-fn.tiktok-row.net` → goes through the ROW Operations Gateway,
>   reachable from office / laptop networks.
>
> If a request returns `403 [Segregator] ...`, retry against the other
> host (see Troubleshooting below).

For convenience, set the host once per shell:

```bash
# Server-side / on-cluster
export FOOTPRINT_HOST="https://gkypl7ix.sg-fn.bytedance.net"

# OR: laptop / office network
export FOOTPRINT_HOST="https://gkypl7ix.sg-fn.tiktok-row.net"
```

## Invocation examples

```bash
# curl: argos log by log_id within a time window
curl -sS -X POST "${FOOTPRINT_HOST}/v1/open/bytedcli/viewlog" \
  -H 'Content-Type: application/json' \
  -H "x-Footprint-JWT: ${FOOTPRINT_JWT}" \
  -d '{
        "log_type": "argos",
        "log_id": "20260609221616XXXXXXXXXXXXXXXXXXXX",
        "idc": "ttp",
        "start_time": 1781042400,
        "end_time": 1781044200,
        "unique_search_id": "FP_FE_example_0001"
      }'
```

```python
import os, requests

resp = requests.post(
    f"{os.environ['FOOTPRINT_HOST']}/v1/open/bytedcli/viewlog",
    headers={
        "Content-Type": "application/json",
        "x-Footprint-JWT": os.environ["FOOTPRINT_JWT"],
    },
    json={
        "log_type": "argos",
        "log_id": "20260609221616XXXXXXXXXXXXXXXXXXXX",
        "idc": "ttp",
        "start_time": 1781042400,
        "end_time": 1781044200,
        "unique_search_id": "FP_FE_example_0001",
    },
    timeout=180,
)
resp.raise_for_status()
print(resp.json()["completed"], len(resp.json().get("data", [])))
```

## Common request fields

The endpoint accepts a `ViewlogParams` JSON body. The exact field set
varies per `log_type`.

| Field                     | Required                     | Notes                                                                |
| ------------------------- | ---------------------------- | -------------------------------------------------------------------- |
| `log_type`                | yes                          | A truthy key in the log-type enum below (e.g. `argos`, `dorado`)     |
| `idc`                     | usually                      | One of the keys in the idc map below (defaults to `ttp` server-side) |
| `log_id`                  | depends on log_type          | The trace id / job id / case id specific to the log_type             |
| `unique_search_id`        | yes for async log types      | A unique key for this query, conventionally `FP_FE_<hash>`           |
| `start_time` / `end_time` | for time-bounded log types   | Unix epoch seconds                                                   |
| `psm_list` / `psm`        | for service-scoped log types | List of PSMs                                                         |

Common per-log-type usage:

- `argos` — fetch an argos trace by `log_id` within a `start_time` /
  `end_time` window.
- `argos_keyword` — keyword search across argos logs; pass the keyword
  via the log-type-specific query field the user mentions.
- `dorado` — fetch dorado job output by `log_id`.
- Other supported types (`rpc`, `ftf` / `ftf2`, `tce`, `faas`,
  `primus`, `slardar`, `clickhouse`, `physical`, `yarn`, `hdfs`, etc.)
  follow the same shape — supply the `log_id` / `psm` / time window the
  type expects, plus any extra log-type-specific fields the user
  mentions (e.g. `query_params`, `method`, `response_slice_mode`,
  `response_index` for ftf2; `physical_host_info` for physical;
  `tce_search_*` for tce).

Only send fields for log types that are truthy in the enum below; reject
anything not listed there.

## Optional polling overrides (headers)

The endpoint polls bytedoc for up to a configured timeout when the sync
call falls back to polling, or when the log_type is async. Defaults are
controlled server-side via TCC. Per-request overrides:

- `X-Bytedcli-Poll-Timeout-Seconds: <int>`
- `X-Bytedcli-Poll-Interval-Seconds: <int>`

Use these when the user explicitly wants a faster poll or shorter wait.

## Rate limiting

Requests are rate-limited per JWT department (`organization` claim).
A `429 Too Many Requests` response means the dept-level rate has been
hit; back off and retry with exponential delay rather than spamming.

## Response shape

Successful response:

```json
{
  "status": 200,
  "unique_search_id": "FP_FE_...",
  "completed": true,
  "expected_total": 42,
  "data": [
    /* list of log entries */
  ]
}
```

- `completed: false` means the polling timeout elapsed before all logs
  arrived; `data` may be partial. The user can retry with a higher
  `X-Bytedcli-Poll-Timeout-Seconds` or call `/v1/open/isPollingComplete`
  later with the same `unique_search_id`.
- `expected_total: -1` means the backend has not yet recorded the total
  count for this query.

## Validation rules to enforce before calling

1. `log_type` must be a truthy entry in the log-type enum below. Reject
   otherwise.
2. If `idc` is supplied, it must be a key in the idc map below.
3. For async log types (anything not in the server's
   `bytedcli_sync_log_types` TCC), require `unique_search_id`. If the
   user did not supply one, generate `FP_FE_<sha1(payload)[0:32]>`
   deterministically so retries hit the same bytedoc bucket.
4. When the user supplies a `log_id` whose embedded timestamp prefix
   (e.g. `20260609221616...` → 2026-06-09 22:16:16) falls outside the
   requested `start_time` / `end_time` window, widen the window to cover
   the log's actual time before calling, or `data` may come back empty.
5. Always send `Content-Type: application/json`.
6. Never log the raw JWT.

## Enums

These enums are the source of truth for what may be passed to
`POST /v1/open/bytedcli/viewlog`. Any value not listed here, or listed
with value `false`, must be rejected before the request is made.

### Supported `log_type`

The following log types are officially supported and may be sent. Any
`log_type` not listed here (or listed with value `false`) must be
rejected before sending the request, even if Footprint itself would
accept it. As coverage expands, add the new type with value `true`.

```json
{
  "log_types": {
    "argos": true,
    "argos_keyword": true,
    "dorado": true,
    "rpc": true,
    "ftf": true,
    "ftf2": true,
    "tce": true,
    "tracelog": true,
    "faas": true,
    "ark": true,
    "arnold": true,
    "bernard": true,
    "spark": true,
    "flink": true,
    "primus": true,
    "slardar": true,
    "clickhouse": true,
    "physical": true,
    "rtc": true,
    "rds_slowlog": true,
    "pastebin": true,
    "megatron": true,
    "tesla": true,
    "yarn": true,
    "hdfs": true,
    "redis": true,
    "abase2": true,
    "tlb": true,
    "kubelet": true,
    "lambda": true,
    "mongos": true,
    "forge": true,
    "arnold_tenant": true,
    "baremetal_instance": true,
    "ttat_tos": true,
    "triangle": true
  }
}
```

### Supported `idc`

Pass one of the **keys** below as `idc` in the request body. The values
on the right are the underlying region codes — they are informational
only and must not be sent to the API.

```json
{
  "ttp": "useast5",
  "ttp2": "useast5",
  "ttp_usswdt": "useast5",
  "ttp_uswest6": "useast5",
  "eu_ttp_gcp": "no1a",
  "eu_ttp_ie": "no1a",
  "eu_ttp_de": "no1a",
  "eu_ttp_ie2": "no1a",
  "eu_ttp_iedt": "no1a",
  "eu_ttp_no1a": "no1a",
  "eu_ttp_useast2a": "no1a",
  "eu_ttp_useast2b": "no1a"
}
```

Default when `idc` is omitted: `ttp` (server-side default).

## Troubleshooting

- **`403 [Segregator] ... not allowed to connect to OG from Prod Network`**
  — the host/network combination is wrong. From a prod-network workspace
  use `*.sg-fn.bytedance.net`; from an office/laptop network use
  `*.sg-fn.tiktok-row.net`. Switch `FOOTPRINT_HOST` and retry.
- **`auth login` fails with `403 [Segregator]`** — the ByteCloud login
  for `i18n-tt` routes through an OG host that must be reached from an
  OG-allowed network. Run `auth login` from a laptop/office network, or
  supply a JWT obtained elsewhere into `FOOTPRINT_JWT`.
- **`401` / `获取字节云 JWT 失败`** — the `i18n-tt` site is not
  authenticated. See `references/troubleshooting.md` §3–4 for the
  per-site `auth status` → `auth login` flow.
- **`429 Too Many Requests`** — department-level rate limit; back off and
  retry with exponential delay.
- **Empty `data`** — usually the time window doesn't cover the
  `log_id`'s embedded timestamp; widen `start_time` / `end_time`. If
  `completed: false`, raise `X-Bytedcli-Poll-Timeout-Seconds` and retry.
- **Unsupported `log_type`** — only types that are truthy in the
  log-type enum above are allowed; reject anything not listed there
  before calling.
