# 元数据 command guide

| Command | Purpose |
| --- | --- |
| `bytedcli keel service get` | Get one Keel service and its metadata |
| `bytedcli keel service list` | Query services by filters with page or cursor pagination |
| `bytedcli keel deployment get` | Get one deployment and its related service metadata |
| `bytedcli keel deployment list` | List deployments with service-scope filters and pagination |
| `bytedcli keel vdc list` | List VDCs, including Volcengine availability zones |
| `bytedcli keel vregion list` | List logical VRegions, including Volcengine regions, with optional VDC data |
| `bytedcli keel site list` | List global Keel site metadata and optional VRegion/VDC topology |

## Get a service

```bash
bytedcli keel service get \
  --service-urn 'urn:meta:service:default:psm/bytecloud.meta.test:tce:container:CN:boe:prod:entity:<>'

bytedcli --json keel service get \
  --service-urn 'urn:meta:service:default:psm/bytecloud.meta.test:tce:container:CN:boe:prod:entity:<>' \
  --query-meta \
  --accept-language zh-Hans
```

Flags follow the authoritative `GET /keel/v1/service` metadata:

- `--service-urn`: required non-empty service URN query value. The CLI rejects
  the command before any request if it is omitted or empty.
- `--query-meta`: optional boolean query value. When omitted, the CLI does not
  send `query_meta`; when present, it sends `query_meta=true`.
- `--accept-language`: optional `Accept-Language` request header. The API
  examples include `en-US` and `zh-Hans`, but metadata does not declare an enum,
  so the CLI does not invent one.

The JSON result is the documented `Service` object with stable snake_case
fields. Nested objects include `owners_modifier`, `byte_tree_node`, `methods`,
`appendage`, `git_repository`, and the open-ended JSON `fragment`. The result
also preserves `service_urn_v2`, `comment`, and `site`. Nullable documented
collections are normalized to empty arrays.

This read command uses the selected Site/VRegion gateway and the invocation's
ByteCloud JWT. It does not expose routing headers or credentials as flags.
All Keel response envelopes use business `code=0` for success; HTTP status is
handled independently by the shared HTTP layer.

## List services

```bash
bytedcli keel service list --subject bytecloud.meta.test --pid tce --env online --page 1 --page-size 20
bytedcli --json keel service list --subject bytecloud.meta.test --partition CN --lane prod
bytedcli --json keel service list --subject bytecloud.meta.test --last-id '<next-id>' --page-size 100
```

Flags follow the authoritative `GET /keel/v1/services/list` metadata:

- Query pagination: `--last-id`, canonical `--page` (sent as `page_no`), and
  `--page-size`. When both cursor and page are sent, the upstream gives
  `last_id` precedence. `page_size` must not exceed 1000, and `page * page-size`
  must not exceed 200000.
- Required non-empty query filter: `--subject`. Pass the service PSM value, for
  example `--subject bytecloud.meta.test`; the CLI rejects the command before
  any request if it is omitted or empty.
- `--tenant` defaults to `default`, and `--namespace` defaults to `psm`. Both
  defaults are sent to the API when the corresponding flag is omitted.
- Optional scalar query filters: `--partition`, `--lane`, `--env`, and `--pid`.
  Metadata documents `prod` as the lane default; an omitted lane is left to
  the upstream.

Unset query fields are omitted. The JSON result contains
`service_list` and `pagination`; pagination exposes `page_no`, `page_size`,
`total_count`, `next_id`, `prev_id`, and `has_more`. Nullable service arrays
and the service list itself are normalized to empty arrays. This one-request
read uses the invocation's ByteCloud JWT.

## Get a deployment

```bash
bytedcli keel deployment get \
  --deployment-urn 'urn:meta:deployment:default:psm/bytecloud.meta.test:tce:container:CN:online:prod:entity:<>'

bytedcli --json keel deployment get \
  --deployment-urn 'urn:meta:deployment:default:psm/bytecloud.meta.test:tce:container:CN:online:prod:entity:<>' \
  --accept-language zh-Hans
```

Flags follow the authoritative `GET /keel/v1/deployment` metadata:

- `--deployment-urn`: optional deployment URN query value.
- `--accept-language`: optional `Accept-Language` request header. The metadata
  declares no enum, so the CLI does not invent one.

Unset inputs are omitted. The JSON result is the documented `Deployment`
object, including `deployment_urn`, `id`, `service_urn`, `cluster`, `type`,
`framework_list`, `vregion`, `vdcs`, `legacy`, `derived`, `extension`, `tags`,
`fragment`, the nested service core, and appendage audit data. Nullable
`framework_list` and `vdcs` are normalized to empty arrays. Keel envelopes use
business `code=0` for success.

## List deployments

```bash
bytedcli keel deployment list --namespace psm --subject bytecloud.meta.test
bytedcli --json keel deployment list \
  --tenant default --namespace psm --subject bytecloud.meta.test \
  --page 1 --page-size 20
bytedcli --json keel deployment list \
  --partition CN --pid tce --env online --lane prod \
  --last-id '<next-id>'
```

Flags follow the authoritative `GET /keel/v1/deployments/list` metadata:

- Pagination query flags: `--last-id`, canonical `--page` (sent as `page_no`),
  and `--page-size`. `page_size` must not exceed 1000, and
  `page * page-size` must not exceed 200000.
- Optional scalar filters: `--env`, `--lane`, `--tenant`, `--pid`,
  `--partition`, `--namespace`, and `--subject`.

All unset values are omitted; the CLI does not invent defaults where metadata
does not declare a `default_value`. The JSON result contains `deployment_list`
and `pagination`. Each deployment has the same public DTO as `deployment get`;
nullable deployment and nested collections are normalized to empty arrays.

## List VDCs

```bash
bytedcli keel vdc list
bytedcli keel vdc list --vregion China-North --domain bytedance --status operational
bytedcli --json keel vdc list \
  --vdc lf \
  --site cn \
  --partition CN \
  --canonical \
  --accept-language zh-Hans
```

Flags follow the authoritative `GET /keel/v2/vdc/list` metadata:

- Repeatable or comma-separated query filters: `--vregion`, `--domain`,
  `--partition`, `--site`, `--status`, and `--vdc`.
- `--tag`: optional scalar tag filter.
- `--canonical`: optional canonical-state filter; explicit false is preserved
  as `--canonical=false`.
- `--accept-language`: optional `Accept-Language` header. Metadata examples are
  `en-US` and `zh-Hans`, but no enum is declared.

All inputs are optional and omitted when unset. The JSON result is the
documented array of VDC objects with localized names, parent VRegion/site/
partition, domain, status, canonical state, tags, purpose, description, and
extension. The live API emits `extension` as an open-ended JSON object or
`null` despite metadata describing it as a string; the CLI preserves the JSON
shape to avoid type-related parse failures. Nullable tags are normalized to an
empty array. Keel envelopes use business `code=0` for success.

## List VRegions

```bash
bytedcli keel vregion list
bytedcli keel vregion list --domain bytedance --status operational --partition CN
bytedcli --json keel vregion list \
  --vregion China-North \
  --site cn \
  --with-vdc \
  --canonical \
  --accept-language zh-Hans
```

Flags follow the authoritative `GET /keel/v2/vregion/list` metadata:

- Repeatable or comma-separated query filters: `--status`, `--vregion`,
  `--oncall-area`, `--partition`, `--site`, `--sales-area`, and `--domain`.
- `--tag`: optional scalar tag filter.
- `--with-vdc`: optional boolean selecting nested VDC data.
- `--canonical`: optional canonical-state filter.
- `--accept-language`: optional `Accept-Language` header. Metadata examples are
  `en-US` and `zh-Hans`, but no enum is declared.

All inputs are optional and omitted when unset. Explicit false is preserved as
`--with-vdc=false` or `--canonical=false`. The JSON result is the documented
array of `Vregion` objects with names, localized area names, parent site and
partition, domain, status, canonical state, tags, on-call areas, sales area,
purpose, extension, description, and `vdc_list`. The upstream currently emits
`extension` as an open-ended JSON object or `null` despite metadata describing
it as a string, so the CLI preserves its JSON shape. VDCs contain their documented
names, parent site/VRegion/partition, domain, status, tags, purpose, extension,
description, and canonical state. Nullable collections are normalized to empty
arrays. Keel envelopes use business `code=0` for success.

## List sites

```bash
bytedcli keel site list
bytedcli keel site list --domain bytedance --status operational --tag rds
bytedcli --json keel site list \
  --site cn \
  --with-vregion \
  --with-vdc \
  --canonical \
  --accept-language zh-Hans
```

Flags follow the authoritative `GET /keel/v1/site/list` metadata:

- `--domain`: optional repeatable or comma-separated domain filter.
- `--site`: optional repeatable or comma-separated site-name filter.
- `--status`: optional repeatable or comma-separated status filter.
- `--tag`: optional scalar tag filter.
- `--with-vdc`: optional boolean selecting nested VDC data.
- `--with-vregion`: optional boolean selecting nested VRegion data.
- `--canonical`: optional canonical-status filter.
- `--accept-language`: optional `Accept-Language` header; metadata examples are
  `en-US` and `zh-Hans`, but no enum is declared.

Unset filters are omitted. Boolean flags preserve explicit false when written
as `--with-vdc=false`, `--with-vregion=false`, or `--canonical=false`.

The JSON result is an array of documented `Site` objects. Each site includes
`name`, localized names, `domain`, `status`, `canonical`, `purpose`,
`frontend_domain`, `extension`, `description`, `tags`, `related_domains`, and
`vregion_list`. VRegions include their documented names, areas, partition,
status, tags, on-call and sales areas, plus `vdc_list`; VDCs include their
documented names, parent site/VRegion/partition, status, tags, purpose, and
canonical state. Nullable collections are normalized to empty arrays.

This is a one-request read operation through the selected gateway and uses the
invocation's ByteCloud JWT. It does not expose the JWT or infrastructure
routing headers as flags.
