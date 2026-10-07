# ByteQuota command guide

## Scope

The first public contract covers CN storage quota only. It excludes compute and `resource_pool`. BOE exists only for pre-release validation; overseas sites are explicitly unsupported.

CN calls `https://quota.byted.org/api/v1/...` directly. BOE pre-release validation calls `https://b-boe.byted.org/api/v1/...` directly with the storage platform selector. Both routes still acquire JWT credentials from the ByteCloud authentication origin resolved by the runtime; API and authentication origins remain separate. The CLI supports only the current quota month for quota reads, capacity checks, transfers, and monthly bypasses; future and historical quota points remain out of scope for v1. Borrow may still include an optional return month.

## Resource identity

Use exactly one business selector when a command targets one business:

```text
--business-id
--bytetree-id
```

Directional commands use role-prefixed selector pairs such as `--from-business-id` / `--from-bytetree-id` and `--parent-business-id` / `--parent-bytetree-id`. Ambiguous ByteTree resolution must fail; never select the first match.

The storage resource identity is:

```text
--platform
--sales-area
--resource-vdc
--flavor
```

`flavor` is the ByteQuota resource flavor. Mapping to a billing item remains a backend concern.
Commands that operate on monthly quota also require `--month YYYY-MM`. Urgent bypasses are time-bounded by `--expires-in` and do not accept `--month`.

For quota `get` and `list`, the CLI resolves `--resource-vdc` against platform metadata. Region-granularity resources ignore the VDC dimension, VRegion-granularity resources query the unique containing VRegion, and VDC-granularity resources query both the containing VRegion and VDC. Unknown or ambiguous VDC metadata fails locally instead of selecting an arbitrary row.

Quota API origins are fixed for CN and BOE and do not use `--vregion`. Host-global `--vregion` and `--vdc` remain routing context and are not part of the ByteQuota resource identity. Use `--resource-vdc` for the quota resource dimension; do not substitute routing flags for `--sales-area` or `--resource-vdc`.

## Commands

| Command | Required command flags | Purpose |
| --- | --- | --- |
| `bytedcli quota meta capability get` | none | Get capability coverage for the selected site |
| `bytedcli quota meta platform list` | none | List storage quota platforms |
| `bytedcli quota meta sales-area list` | `--platform` | List sales areas for a platform |
| `bytedcli quota meta flavor list` | `--platform --sales-area` | List flavors for a platform and sales area |
| `bytedcli quota get` | one business selector, `--platform --sales-area --flavor --month` | Get one exact quota item |
| `bytedcli quota list` | optional filters | List quota items without implicit aggregation |
| `bytedcli quota operation get` | `--id` | Get one request or transfer operation |
| `bytedcli quota operation list` | optional business/type/status filters | List visible quota operations |
| `bytedcli quota request` | child business, resource, `--quantity --reason` | Request quota from the direct parent |
| `bytedcli quota borrow` | one lender and one borrower selector, resource, `--quantity --reason` | Borrow quota, optionally with `--return-month` |
| `bytedcli quota allocate` | one parent and one child selector, resource, `--quantity --reason` | Allocate parent quota to a direct child |
| `bytedcli quota reclaim` | one parent and one child selector, resource, `--quantity --reason` | Reclaim quota from a direct child |
| `bytedcli quota check` | one business selector, resource, `--quantity` | Check a planned resource request |
| `bytedcli quota bypass get` | `--id` | Get one bypass |
| `bytedcli quota bypass list` | optional user/type/status/platform/time filters | List visible bypasses |
| `bytedcli quota bypass monthly create` | one business selector, `--platform --sales-area --flavor --month --buffer-quantity --reason` | Create a monthly business bypass |
| `bytedcli quota bypass urgent create` | one business selector, `--platform --sales-area --flavor --user --expires-in --reason` | Create an urgent user bypass; optional `--resource-vdc`, no `--month` |

Collection reads accept `--page-token`, `--page-size` and `--all`. The default page size is 20, including for `bytedcli quota list --all`; callers may explicitly choose a value up to 200. `--all` cannot be combined with `--page-token`. When more pages remain, the result returns `next_page_token`; pass that value unchanged to the next call. The CLI maps this public pagination contract to each ByteQuota endpoint's native page or cursor wire without changing backend semantics.

For `bytedcli quota list`, omitting both the business selector and `--platform` is a global listing available only to superadmins. An unscoped `--all` is rejected locally for every identity because ByteQuota recomputes the full result for every page. Superadmins who deliberately need a global listing must paginate with `--page-token`; platform admins listing across businesses must pass `--platform`; other callers should pass a business selector.

Operation status filters accept `created`, `submitting`, `approved`, `rejected`, `finished`, or `failed`. Bypass status filters accept `pending`, `active`, `failed`, or `expired`.

## Write safety

Every mutation accepts:

```text
--reason
--dry-run
--yes
```

- Omitting `--yes` means preview.
- `--dry-run` is the explicit form of preview and is mutually exclusive with `--yes`.
- Bypass creation also accepts `--force`; it requires `--yes`. Transfer commands do not expose `--force`.
- Positive quantities are decimal strings; signed values and exponent notation are rejected.
- A borrow may omit `--return-month`, which means no return leg.

JSON context includes the invoked command, site and mode (`read`, `preview`, or `submit`). A request ID is included when the HTTP response provides one.

Successful transfer submissions return an operation ID. Successful bypass submissions return a bypass ID. The CLI does not perform a second read after a write, so a readback failure cannot obscure a mutation that already succeeded.
