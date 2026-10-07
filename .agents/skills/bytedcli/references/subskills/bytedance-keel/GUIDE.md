---
name: bytedance-keel
description: "Inspect Keel service and global site metadata through bytedcli. Trigger when users mention 元数据, Keel services, service URNs, sites, VRegions, VDCs, owners, methods, endpoints, or these CLI operations."
---

# 元数据

平台入口：[Keel 元数据平台](https://cloud.bytedance.net/meta)

Use `bytedcli keel` to inspect Keel metadata.

## Quick start

```bash
bytedcli keel service get --service-urn 'urn:meta:service:default:psm/bytecloud.meta.test:tce:container:CN:boe:prod:entity:<>'
bytedcli --json keel service get --service-urn 'urn:meta:service:default:psm/bytecloud.meta.test:tce:container:CN:boe:prod:entity:<>' --query-meta --accept-language zh-Hans
bytedcli keel service list --subject bytecloud.meta.test --pid tce --env online --page 1 --page-size 20
bytedcli --json keel service list --subject bytecloud.meta.test --last-id '<next-id>' --page-size 100
bytedcli keel deployment get --deployment-urn 'urn:meta:deployment:default:psm/bytecloud.meta.test:tce:container:CN:online:prod:entity:<>'
bytedcli --json keel deployment get --deployment-urn 'urn:meta:deployment:default:psm/bytecloud.meta.test:tce:container:CN:online:prod:entity:<>' --accept-language zh-Hans
bytedcli keel deployment list --namespace psm --subject bytecloud.meta.test --page 1 --page-size 20
bytedcli --json keel deployment list --partition CN --pid tce --env online --lane prod --last-id '<next-id>'
bytedcli keel vdc list --vregion China-North --domain bytedance --status operational
bytedcli --json keel vdc list --vdc lf --site cn --canonical
bytedcli keel vregion list --domain bytedance --status operational --partition CN
bytedcli --json keel vregion list --vregion China-North --site cn --with-vdc --canonical
bytedcli keel site list --domain bytedance --status operational
bytedcli --json keel site list --site cn --with-vregion --with-vdc --canonical
```

## Commands

- `bytedcli keel service get`: Get one Keel service. The documented
  `--service-urn` is required and must be non-empty. `--query-meta` and
  `--accept-language` remain optional and are omitted when unset.
- `bytedcli keel service list`: List Keel services. `--subject` is required and must
  be the service PSM value. `--tenant` defaults to `default`, and `--namespace`
  defaults to `psm`. Optional filters are `--partition`, `--lane`, `--env`, and
  `--pid`. Use `--page`/`--page-size` or cursor-based `--last-id`.
- `bytedcli keel deployment get`: Get one deployment. The documented
  `--deployment-urn` and `--accept-language` inputs are optional; unset inputs
  are omitted from the request.
- `bytedcli keel deployment list`: List deployments with optional service-scope and
  pagination filters. Use `--page`/`--page-size` or cursor-based `--last-id`;
  all documented filters are omitted when unset.
- `bytedcli keel vdc list`: List VDCs, including Volcengine availability zones.
  Repeatable filters cover VRegion, domain, partition, site, status, and VDC;
  `--tag` is scalar. Use `--canonical` for canonical-state filtering and
  `--accept-language` for localized names. Unset inputs are omitted.
- `bytedcli keel vregion list`: List VRegions, including Volcengine regions. Its
  repeatable filters cover status, VRegion, on-call area, partition, site,
  sales area, and domain; `--tag` is scalar. Use `--with-vdc` for nested VDCs,
  `--canonical` for canonical-state filtering, and `--accept-language` for
  localized names. Unset inputs, including optional booleans, are omitted.
- `bytedcli keel site list`: List Keel sites, optionally filtering by repeatable
  `--domain`, `--site`, and `--status`, or scalar `--tag`. Use `--with-vregion`
  and `--with-vdc` to request nested topology data, `--canonical` to filter by
  canonical status, and `--accept-language` for localized names. Unset inputs
  are omitted, including optional booleans.

Use `--json` for stable automation. The result contains the documented service
fields. Service results include `service_urn`, names, namespace, subject, platform, routing
scope, owners, methods, endpoints, ByteTree metadata, appendage, repository,
tags, and timestamps. Service-list results wrap those services with documented
pagination data. Deployment get/list results contain cluster, framework, VRegion/VDC,
related service, appendage, tags, and derivation metadata. VDC-list results
contain names, parent VRegion/site/partition, domain, status, canonical state,
tags, purpose, description, and open-ended extension JSON. VRegion-list results
contain names, areas, site, partition, domain, status, canonical state, tags,
on-call areas, sales area, and optional nested VDCs. Site-list results
contain sites with names, status,
domain, canonical state, tags, related domains, and optional nested VRegions
and VDCs. Authentication uses the invocation's ByteCloud JWT; never print or
forward it.

## References

- [Command guide](references/keel.md)
- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
