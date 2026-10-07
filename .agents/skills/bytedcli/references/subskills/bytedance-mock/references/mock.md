# ByteMock CLI Quick Reference

## Rule Management

```bash
# List rules
bytedcli mock rule list --namespace <ns> [--psm <psm>] [--path <path> --http-method GET] [--method <rpcMethod>] [--status all|on|off|1|0]

# Get rule detail
bytedcli mock rule get --id <ruleId>

# Create rule
bytedcli mock rule create \
  --namespace <ns> \
  --callee-psm <psm> \
  --method <method> \
  --name <name> \
  --mock-data '<json>' \        # or --mock-data-file <path>
  [--caller-psm <psm>] \       # default: * (all callers)
  [--protocol thrift|http] \    # default: thrift
  [--status 1|0] \              # default: 1 (enabled)
  [--priority <n>] \            # default: 0
  [--delay <ms>] \              # default: 0
  [--path <path>] \             # HTTP interface path when --protocol http
  [--filter '<json>'] \         # request filter
  [--description '<text>'] \
  [--expire-time '<iso8601>']

# Update rule (覆盖式, 仅传需要更新的字段)
bytedcli mock rule update --id <ruleId> [--mock-data '<json>'] [--name <name>] [--status 1|0]

# Enable / Disable / Delete
bytedcli mock rule enable --id <ruleId>
bytedcli mock rule disable --id <ruleId>
bytedcli mock rule delete --id <ruleId>
```

Notes:

- `mock rule list --psm` is the canonical callee PSM filter. `--callee-psm` remains a compatibility alias.
- For HTTP interface rules, pass `--path` together with `--http-method` when listing so the server filters the exact endpoint.
- Creating HTTP rules through `--protocol http --method GET --path <path>` also writes the HTTP routing fields needed by ByteMock (`http_method`, JSON encoding, and status code 200). When `--status 0` is requested, the CLI creates then disables the rule so it does not become effective.

## Namespace Management

```bash
bytedcli mock namespace list [--namespace <name>] [--keyword <kw>]
bytedcli mock namespace create --name <name> [--description '<text>']
```

## Service Management

```bash
bytedcli mock service list [--namespace <ns>] [--psm <psm>] [--keyword <kw>]
bytedcli mock service create --psm <psm> --namespace <ns> [--protocol thrift|http]
bytedcli mock service sync --psm <psm>
bytedcli mock service prepare --psm <psm1> [--psm <psm2>] [--expired-at '<datetime>']
```

## Dyeing (Traffic Routing)

```bash
# List dyeing rules
bytedcli mock dyeing list --namespace <ns> [--callee <psm>]

# Create/Update dyeing rule
bytedcli mock dyeing update \
  --callee <psm> \
  --caller <psm> \
  --method <method> \           # * for all methods
  --dyeing "ENV:<lane_name>" \
  [--type thrift|http] \        # default: thrift
  [--expired-at '<iso8601>'] \  # default: 7 days
  [--callee-cluster <cluster>] \
  [--caller-cluster <cluster>]

# Enable / Disable
bytedcli mock dyeing enable --id <dyeingId>
bytedcli mock dyeing disable --id <dyeingId>
```

## Domain Mapping

| `--site`  | Office network (OG) domain     | Production network domain      |
| --------- | ------------------------------ | ------------------------------ |
| `prod`    | bytemock.bytedance.net         | bytemock.bytedance.net         |
| `boe`     | bytemock-boe.bytedance.net     | bytemock-boe.bytedance.net     |
| `boei18n` | bytemock-boei18n.bytedance.net | bytemock-boei18n.bytedance.net |
| `i18n`    | bytemock-sg.tiktok-row.net     | bytemock-i18n.bytedance.net    |
| `i18n-tt` | bytemock-sg.tiktok-row.net     | bytemock-i18n.bytedance.net    |
| `i18n-bd` | bytemock-sg.tiktok-row.net     | bytemock-i18n.bytedance.net    |
| `us-ttp`  | bytemock-sg.tiktok-row.net     | bytemock-i18n.bytedance.net    |
| `eu-ttp`  | bytemock-sg.tiktok-row.net     | bytemock-i18n.bytedance.net    |

`eu-ttp-limited` / `eu-ttp-full` normalize to `eu-ttp`. `us-ttp-bdee` / `us-ttp-usts` have no ByteMock mapping yet: commands fail fast with `MOCK_SITE_UNSUPPORTED` (the hint lists the supported sites) instead of silently hitting another control plane.

The I18N control plane (`i18n` / `i18n-tt` / `i18n-bd`; `us-ttp` / `eu-ttp` share it) has two hosts: `bytemock-i18n.bytedance.net` only resolves from ByteDance production networks, and the office network must use the OG gateway `bytemock-sg.tiktok-row.net`. For those sites the CLI picks the host per process:

1. `BYTEDCLI_NETWORK_PROFILE=prod` → production host, `BYTEDCLI_NETWORK_PROFILE=office` → OG host (no probe).
2. Inside a production runtime (AIME workspace, `IS_PROD_RUNTIME` / `SERVICE_ENV` set) → production host (no probe).
3. Otherwise it probes the OG host first (preferred): `GET https://bytemock-sg.tiktok-row.net/` with a 3s timeout. Any gateway response below HTTP 500 (including 401/403/404) counts as reachable; DNS failure, connection refused, TLS errors, timeouts and proxy-side errors (407 / 5xx) count as unreachable and trigger the fallback to the production host. Results are cached per process (success 10 min, failure 30 s). Production-network callers outside an IDC runtime pay that probe once per process — set `BYTEDCLI_NETWORK_PROFILE=prod` to skip it.

`prod` / `boe` / `boei18n` have a single host and never probe. `--debug` prints the chosen host in every mode (plus the probe result when a probe ran).

The I18N control plane validates JWTs per issuing region and rejects the `i18n-bd` partition token (`authentication failed ... not support region: i18nbd`), so `--site i18n-bd` signs requests with the same ByteCloud credential as `--site i18n`; log in for `i18n` if `i18n-bd` reports an auth error.

## Mock Setup Workflow

```bash
# 1. Create namespace (name = BOE lane name for env-mode routing)
bytedcli mock namespace create --name boe_my_lane

# 2. Relate downstream service
bytedcli mock service create --psm downstream.service --namespace boe_my_lane --protocol thrift

# 3. Create mock rule
bytedcli mock rule create --namespace boe_my_lane --callee-psm downstream.service \
  --method TargetMethod --name "my-mock" --mock-data '{"field":"value"}'

# 4. Create dyeing rule (traffic routing)
bytedcli mock dyeing update --callee downstream.service --caller my.service \
  --method TargetMethod --dyeing "ENV:boe_my_lane" --type thrift

# 5. Preload service IDL
bytedcli mock service prepare --psm downstream.service
```
