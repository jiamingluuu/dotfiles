# ByteIO

## Capability

ByteIO commands wrap the documented ByteIO OpenAPI surface for event tracking metadata, requirements, BTM points, test cases, location attributes, and ad metadata. The event send command additionally submits an MCS JSON envelope to an approved built-in origin.

Flow commands additionally support requirement/event write workflows with JSON payload input. BTM point creation uses the ByteIO web API, whose origin is site-derived (`i18n-tt` → `https://io-sg.tiktok-row.net`, else `https://data.bytedance.net`).

`byteio transformation ...` and `byteio transform ...` cover ByteIO 数据加工 (Mario transformations and their transform rules): rule-set and rule queries, version history and diff, rule create/update, the console rule test, and release (上线 / 下线) request submission, tracking, and withdrawal. They call Mario under `/mario/api/v2` on the console origin with the same Web BFF cookie chain; write commands preview by default and submit only with `--yes`.

## Authentication

ByteIO OpenAPI commands and ByteIO console Web BFF commands have distinct credentials.

`byteio event send` uses neither credential surface. It submits directly to an
allowlisted MCS HTTPS origin without an OpenAPI authorization header, Web BFF
cookie, or bytedcli login state.

## MCS HTTPS allowlist

`byteio event send --domain` accepts only an HTTPS origin whose hostname appears
below. Paths, credentials, custom ports, HTTP origins, and hostnames removed from
the official MCS registry are rejected. Redirect targets are checked against the
same list.

| Deployment                          | Approved hostnames                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| China and business-specific         | `mcs.zijieapi.com`, `mcs.bytedance.net`, `mcs.snssdk.bytedance.net`, `mcs.sztzyg.com`, `mcs.daliapp.net`, `mcs.daliapp.cn`, `monitor.daliapp.net`, `monitor.daliapp.cn`, `mcs.dongchedi.com`, `mcs-bd.feishu.cn`, `internal-api.feishu-pre.cn`, `internal-api.feishu.cn`, `mcs.volceapplog.com`, `mcs.czgts.cn`, `vephonemon.volces.com`, `vegamemon.volces.com`, `wap.openlanguage.com`, `m.openlanguage.com`, `f.openlanguage.com`, `api-ek12.openlanguage.com` |
| China BOE                           | `boe-mcs.snssdk.com`                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Virginia                            | `maliva-mcs.byteoversea.com`, `vaali-mcs.byteoversea.com`, `mcs-va.tiktokv.com`, `mcs-va.tiktok.com`, `mcs-va.fannoshop.com`, `mcs-bd.larksuite.com`, `mcs.itobsnssdk.com`, `mcs-va-mobilegame.byteintlapi.com`, `mcs-va.ifyooou.com`, `mcs.letschat.com`, `mcs-va.ciciai.com`, `mcs-va.coze.com`, `mcs-va.anybagel.com`, `tea31-va.letschatclient.com`                                                                                                           |
| Singapore and global                | `sgali-mcs.byteoversea.com`, `mcs.byteoversea.net`, `mcs-sg.byted.org`, `mcs-sg.tiktokv.com`, `mcs-sg.tiktok.com`, `mcs.tiktok-row.net`, `mcs-global.picoxr.com`, `mcs-global.picovr.com`, `mcs.tobsnssdk.com`, `mcs-sg.ciciai.com`, `mcs-sg.coze.com`, `mcs-sg.anybagel.com`                                                                                                                                                                                     |
| Lark Singapore, Japan, and Malaysia | `mcs-sg.larksuite.com`, `mcs-bd-sg.feishu.cn`, `mcs-jp.larksuite.com`, `mcs-bd-my.byteintl.com`, `mcs-bd-my.larkoffice.com`                                                                                                                                                                                                                                                                                                                                       |
| AWS France                          | `awsfr-mcs.byteintlapi.com`                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| US and TTP                          | `mcs.us.tiktokv.com`, `mcs.us.tiktok.com`, `mcs.tiktokv.us`, `mcs-ttp2.us.tiktok.com`, `mcs-ttp2.tiktokv.us`, `mcs-va-useast2a.tiktokv.com`, `mcs-i18n.tiktok.com`                                                                                                                                                                                                                                                                                                |
| Europe                              | `mcs16-normal-useastred.tiktokw.eu`, `mcs-ie2.tiktokw.eu`, `mcs-ie.tiktokw.eu`, `mcs16-normal-no1a.tiktokw.eu`                                                                                                                                                                                                                                                                                                                                                    |

The OpenAPI gateway expects an `authorization` header for query/read commands. bytedcli reads it from:

1. `BYTEDCLI_BYTEIO_AUTHORIZATION`

Flow write commands use the same `authorization` header:

```bash
export BYTEDCLI_BYTEIO_AUTHORIZATION=<byteio-openapi-authorization>
```

Never hardcode real authorization values in repository files, test fixtures, skill docs, or user-facing summaries.

The ByteIO console Web BFF origin is site-derived from the global `--site`: `i18n-tt` targets the sg BFF `https://io-sg.tiktok-row.net`, every other site targets `https://data.bytedance.net/byteio/api/v1/*`. Set `BYTEDCLI_BYTEIO_WEB_ORIGIN` to override the origin explicitly. In default or explicit `auto` mode, bytedcli resolves the Web BFF cookie in this order:

1. `BYTEDCLI_BYTEIO_WEB_COOKIE` when it validates against a protected Web BFF probe.
2. A valid local Chromium cookie for the site-derived origin (`io-sg.tiktok-row.net` for `i18n-tt`, `data.bytedance.net` otherwise).
3. A host-scoped `titan_passport_id` derived from `bytedcli auth login`.

In `auto`, when a Web BFF business request returns HTTP 401, bytedcli force-refreshes the Titan Passport once and retries as before. The default acquisition/probe fallback and diagnostics are unchanged.

`byteio --auth-mode auto|titan|browser` overrides `BYTEDCLI_BYTEIO_AUTH_MODE`; an explicit `auto` overrides the environment too. Invalid Web BFF modes fail before credential access. `titan` ignores `BYTEDCLI_BYTEIO_WEB_COOKIE` and local browser cookies, uses bytedcli's existing Titan credentials/cache/overrides, and never accesses browser Keychain storage or opens interactive login. `browser` uses the explicit Cookie environment variable or local Chromium cookies, never Titan. A failed explicit Cookie is not replaced and must be updated by the caller.

In `titan` / `browser`, acquisition, probe and business request share at most one refresh after a clear 401 (Titan refresh or local browser reread). Explicit Cookies are never refreshed. 403, timeout, network and 5xx errors do not refresh credentials or switch sources; transport-level HTTP retries remain separate. Diagnostics preserve safe failure categories and HTTP status without raw credential values.

This option covers console, BTM creation, suite, test-case writes, realtime watch, transformation and transform workflows. Named MCP tools accept `authMode` and do not retain it across calls. OpenAPI (including test-case list/get) ignores the mode environment variable and rejects explicit `titan` / `browser`; `auto` keeps its existing Authorization behavior. MCS event send also rejects explicit strict modes.

```bash
bytedcli --site cn auth login
bytedcli --site cn --json byteio --auth-mode titan console event get --app-id 123 --event-name demo_event
```

Console commands do not accept `--region`; use the same global `--site` value that was used for `auth login`. `console business-module list` fetches a non-paginated backend response and applies `--limit` locally (default: `100`); JSON exposes `truncated` when more modules are available.

## Regions

| Region                                 | OpenAPI base                                             |
| -------------------------------------- | -------------------------------------------------------- |
| `cn`                                   | `https://openapi-dp.byted.org/openapi/byteio-cn`         |
| `sg` (default, office network)         | `https://openapi-alisg.tiktok-row.org/openapi/byteio-sg` |
| `sg` (`BYTEDCLI_NETWORK_PROFILE=prod`) | `https://openapi-alisg.byted.org/openapi/byteio-sg`      |

Use `--region cn|sg`; default is `cn`.

SG 有两个 host，按网络环境切换：

- 默认（办公网 / 本地 CLI）：`openapi-alisg.tiktok-row.org`，仅办公网可达，生产网不可用。
- `BYTEDCLI_NETWORK_PROFILE=prod`：`openapi-alisg.byted.org`，开发机 / BOE / PPE / 线上服务端可达，办公网不可达。

## Commands and APIs

| User task                    | Command                                                                                                                                         | Method / path                                                           |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 上报 ByteIO 事件             | `byteio event send --domain <url> [--input-file <path> \| --input-json <json>]`                                                                 | `POST <domain>/v1/json`                                                 |
| 实时抓取真机 event_log       | `byteio event watch --app-id <id> --device-id <did> [--main-app-id <id>] [--duration <seconds>] [--event <name>] [--log-type <name>] [--max-events <n>]` | `POST /byteio/api/v1/logverify/client + Frontier WS`                    |
| 查询单个埋点元数据详情       | `byteio event get --app-id <id> --event-name <name>`                                                                                            | `GET /byteio/open/v1/schema/detail`                                     |
| 创建埋点元数据               | `byteio event create --app-id <id> --name <name> --owner <owners> --creator <creator> --description <text> --category <category> --os <osList>` | `POST /open/v1/schema`                                                  |
| 修改埋点元数据               | `byteio event update --app-id <id> --name <name> --operator <operator> --description <text> --category <category> --os <osList>`                | `PUT /open/v1/schema`                                                   |
| 校验埋点参数                 | `byteio event check-params --app-id-list <ids> --event-name-list <names> --param-name-list <names>`                                             | `POST /byteio/open/v1/schema/param/check`                               |
| 查询需求列表                 | `byteio requirement list --app-id <id>`                                                                                                         | `POST /byteio/open/v1/requirements/list`                                |
| 查询需求详情                 | `byteio requirement get --requirement-id <id>`                                                                                                  | `GET /byteio/open/v1/requirements/{id}/`                                |
| 创建 BTM 点位                | `byteio btm point create --app-id <id> --parent-id <id> --type <kind> --site-id <id> --owner <owner> --label <label>`                           | `POST /byteio/api/v1/btm_codes`                                         |
| 查询 BTM 点位详情            | `byteio btm point get --operator <user> --requirement-id <id>`                                                                                  | `POST /open/v1/btm_requirement/get_point_details`                       |
| 查询测试用例信息列表         | `byteio test-case list --app-id <id>`                                                                                                           | `POST /open/v1/test_case_suite/test_case/info/list`                     |
| 查询测试用例详情             | `byteio test-case get --test-case-id <id>`                                                                                                      | `GET /open/v1/test_case_suite/test_case/{test_case_id}`                 |
| 根据业务线查询点位           | `byteio map locations --app-id <id> --business-module-ids <ids>`                                                                                | `POST /open/v1/event_map/location_attribute/tree`                       |
| 根据点位查询点位上的埋点     | `byteio map events --app-id <id> --full-identifier-list <ids>`                                                                                  | `POST /byteio/open/v1/event_map/location_attribute/group/event/list`    |
| 查询需求中的点位列表         | `byteio requirement locations --app-id <id> --requirement-id <id>`                                                                              | `POST /byteio/open/v1/event_map/location_attribute/list_in_requirement` |
| 查询广告 tag 列表            | `byteio ad tags`                                                                                                                                | `GET /open/v1/ad/data_manage/tag/list`                                  |
| 查询广告 label 列表          | `byteio ad labels`                                                                                                                              | `GET /open/v1/ad/data_manage/label/list`                                |
| 根据用户邮箱前缀查询埋点信息 | `byteio event list --owner <owner>`                                                                                                             | `POST /byteio/open/v1/schema/name/list`                                 |
| 查询控制台事件及完整参数     | `byteio console event get --app-id <id> --event-name <name>`                                                                                    | `GET /byteio/api/v1/dynamic_schema/basic/`                              |
| 控制台事件列表               | `byteio console event list --app-id <id>`                                                                                                       | `GET /byteio/api/v1/dynamic_schema/`                                    |
| 控制台需求详情               | `byteio console requirement get --app-id <id> --requirement-id <id>`                                                                            | `GET /byteio/api/v1/requirements/{requirement_id}/`                     |
| 控制台需求列表               | `byteio console requirement list --app-id <id>`                                                                                                 | `GET /byteio/api/v1/requirements/`                                      |
| 控制台位置属性列表           | `byteio console location-attribute list --app-id <id>`                                                                                          | `GET /byteio/api/v1/event_map/location_attribute/list`                  |
| 控制台业务模块列表           | `byteio console business-module list --app-id <id> [--limit <n>]`                                                                               | `GET /byteio/api/v1/business_module/all`                                |
| 控制台事件级自定义参数列表   | `byteio console parameter list --app-id <id> [--scope event]`                                                                                   | `GET /byteio/api/v2/param/list`                                         |
| 控制台全局公共属性列表       | `byteio console parameter list --app-id <id> --scope header`                                                                                    | `GET /byteio/api/v2/param/header_list`                                  |
| 控制台预置 header 参数列表   | `byteio console parameter list --app-id <id> --scope system`                                                                                    | `GET /byteio/api/v1/param/system/header/list`                           |
| 控制台新建全局公共属性       | `byteio console parameter create --app-id <id> --name <name> --data-type <type> --description <desc> --rd-owners <a,b> [--yes]`                   | `POST /byteio/api/v1/param/?virtual_project_id={vpid}`                  |
| 控制台删除全局公共属性       | `byteio console parameter delete --app-id <id> --id <param-id> [--yes]`                                                                         | `DELETE /byteio/api/v1/param/{id}`                                      |
| 数据加工空间列表             | `byteio transformation space list`                                                                                                              | `GET /mario/api/v2/space/`                                              |
| 数据加工（规则集）列表       | `byteio transformation list [--space-code <code>] [--keyword <kw>]`                                                                             | `GET /mario/api/v2/transformations/`                                    |
| 数据加工基础信息             | `byteio transformation get --transformation <name>`                                                                                             | `GET /mario/api/v2/transformations/{name}/basics/`                      |
| 数据加工审批人列表           | `byteio transformation auditor list --transformation <name>`                                                                                    | `GET /mario/api/v2/transformations/{name}/auditors/`                    |
| 转换规则列表                 | `byteio transform list --transformation <name> [--status <s>] [--keyword <kw>] [--transform-id <id>]`                                           | `GET /mario/api/v2/transformations/{name}/transforms/`                  |
| 转换规则详情（某版本）       | `byteio transform get --transform-id <id> [--version <n>]`                                                                                      | `GET /mario/api/v2/transformations/transforms/{id}/?version=<n>`        |
| 转换规则版本列表             | `byteio transform version list --transform-id <id>`                                                                                             | `GET /mario/api/v2/transformations/transforms/{id}/versions/`           |
| 转换规则版本 diff            | `byteio transform version diff --transform-id <id> --from-version <a> --to-version <b>`                                                         | `GET /mario/api/v2/transformations/transforms/version/compare/{ha}/{hb}/` |
| 新建转换规则                 | `byteio transform create --transformation <name> --name <rule> [--filter-file <path>] [--yes]`                                                  | `POST /mario/api/v2/transformations/{name}/transforms/`                 |
| 修改转换规则（保存新版本）   | `byteio transform update --transform-id <id> [--base-version <n>] [--filter-file <path>] [--yes]`                                               | `PUT /mario/api/v2/transformations/transforms/{id}/`                    |
| 测试转换规则                 | `byteio transform test --transform-id <id> [--version <n>] --input-file <path>`                                                                 | `POST /mario/api/v2/transformations/{name}/transform-test/`             |
| 转换规则测试历史             | `byteio transform test-history list --transform-id <id>`                                                                                        | `GET /mario/api/v2/transformations/transforms/{id}/test/`               |
| 上线预检                     | `byteio transform release check --transform-id <id> --version <n> [--action online\|offline]`                                                   | `GET .../transforms/{id}/online_check/` + `GET /mario/api/v2/alarms/transforms/message/{id}/` |
| 提交上线 / 下线申请          | `byteio transform release create --transform-id <id> --version <n> --auditor <user> --comment <text> [--yes]`                                   | `POST /mario/api/v2/transformations/transforms/{id}/publish/`           |
| 上线申请记录                 | `byteio transform release list --transform-id <id>`                                                                                             | `GET /mario/api/v2/transformations/transforms/{id}/publish/all/`        |
| 上线申请详情                 | `byteio transform release get --release-id <id>`                                                                                                | `GET /mario/api/v2/transformations/transforms/publish/{id}/`            |
| 撤回上线申请                 | `byteio transform release cancel --release-id <id> [--yes]`                                                                                     | `DELETE /mario/api/v2/transformations/transforms/publish/{id}/`         |

## Important parameters

- `console requirement get`: `--app-id`, `--requirement-id`; 返回需求 `id`、`name`、绑定表格 `sheetParseType` / `sheetToken` / `sheetId` 和 `events`，复用控制台登录态。
- `console event get`: `--app-id`, `--event-name`; output contains normalized event metadata, `parameterCount`, and complete parameter definitions in `parameters`
- `event get`: `--app-id`, `--event-name`, optional `--include-scene`
- `event watch`: `--app-id` is the sub-application id to capture (for example `123`; the ByteIO page URL may call it `subAppId`, while the Frontier subscription body uses `app_id`), `--main-app-id` is the host `main_app_id` for that sub-application (for example `456`; auto-resolved through app selector by default and only needed as a manual override), `--device-id`; optional `--duration`, repeatable `--event <name>` exact `log_info.event_name` filter, repeatable `--log-type <name>` exact `raw_event.log_type` filter, `--max-events`, `--output`; global `--json` streams one event_log JSON object per line without a final envelope. Without filters, it outputs all events; with filters, `--event` and `--log-type` use OR semantics and `--max-events` counts only matched events. Fragmented Frontier event frames are reassembled before parsing/filtering. Run only one watch per device at a time when possible; v1 does not reconnect automatically, and unexpected disconnects fail and require rerunning the command.
- `event create`: `--app-id`, `--name`, `--owner`, `--creator`, `--description`, `--category`, `--os`; optional `--trigger-type`, `--tag`, `--image-url`, `--involved-employee`, `--cost-business-line-name`, `--business-module-name`, `--business-module-id`, `--params-json`, `--payload-json`, `--locale`
- `event update`: `--app-id`, `--name`, `--operator`, `--description`, `--category`, `--os`; optional `--owner`, `--trigger-type`, `--tag`, `--image-url`, `--involved-employee`, `--cost-business-line-name`, `--business-module-name`, `--business-module-id`, `--params-json`, `--payload-json`, `--locale`
- `event check-params`: either the three list flags or `--checks-json`; use `--param-name-list '*'` to check all params
- `requirement list`: `--app-id`; optional `--keyword`, `--owner`, `--requirement-status`, `--requirement-status-list`, `--requirement-id-list`, `--type`, `--external-rid`, `--page`, `--page-size`, `--filter-empty-location-attribute`
- `btm point create`: `--app-id`, `--parent-id`, `--type` (`page|block|module`), `--site-id`, `--owner`, `--label`; optional `--image-url`, `--index-code`, `--parent-ids`, `--business-modules-json`, `--locale`, `--body-json`
- `btm point get`: `--operator`, `--requirement-id`; optional `--btm-full-code-list`
- `test-case list`: `--app-id`; optional `--test-case-ids`, `--test-case-suite-ids`, `--name`, `--event-name`, `--page`, `--page-size`
- `map locations`: `--app-id`; optional `--business-module-ids` as comma-separated values or JSON array
- `map events`: `--app-id`, `--full-identifier-list`; optional `--event-trigger-type-list`, `--page`, `--page-size`
- `transformation list`: optional `--space-code`, `--keyword`, `--page`, `--page-size`; `transformation get` / `transformation auditor list`: `--transformation`
- `transform list`: `--transformation`; optional `--keyword`, `--transform-id`, `--status` (`not-online`, `online`, `was-online`, `online-reviewing`, `offline-reviewing`, `upgrade-reviewing`, `gray-reviewing`; comma-separated or repeated), `--tag` (single tag filter), `--event-name`, `--last-publisher`, `--subscribed`, `--page`, `--page-size`
- `transform get`: `--transform-id`; optional `--version`. `transform version list`: `--transform-id`. `transform version diff`: `--transform-id`, `--from-version`, `--to-version`
- `transform create`: `--transformation`, `--name`; `transform update`: `--transform-id`, optional `--base-version`, `--name`; both accept `--comment`, `--filter-json` / `--filter-file`, `--action-json` / `--action-file`, `--pass-through` / `--no-pass-through`, `--tags` (comma-separated or repeated; replaces existing tags), `--event-name`, `--action-codes`, `--action-type`, `--payload-json` / `--payload-file` (cannot override `id`, `version`, `transformation`), `--locale`, `--yes`. Each json / file pair is mutually exclusive and file inputs are capped at 1 MiB. `transform update` output carries `stale_base` (true when the base version is not the latest saved version) and `warnings`; the dry-run hint pins `--base-version` for the `--yes` run, and `--yes` on a stale base fails with `BYTEIO_TRANSFORM_BASE_STALE` unless `--allow-stale-base` is passed.
- `transform test`: `--transform-id`, exactly one of `--input-json` / `--input-file`; optional `--version`, `--source-dataset`, the same rule override flags as `transform update`, `--dry-run`
- `transform release check` / `transform release create`: `--transform-id`, `--version`; optional `--action online|offline` (default `online`); `release create` also takes `--comment` (required), `--auditor`, `--auto-approval` / `--no-auto-approval`, `--yes`
- `transform release list`: `--transform-id`; `transform release get` / `transform release cancel`: `--release-id` (`cancel` needs `--yes` to send)

### Realtime event watch

```bash
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --event click_video_player --event go_video_detail_new --max-events 10
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --log-type bb_preload --log-type bb_task --max-events 10
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --event click_video_player --log-type bb_preload --max-events 10
```

`--app-id` is the sub-application id whose events should be captured, for example `123`; ByteIO web pages may expose the same value as `subAppId`, and realtime `event_log.data.app_id` also carries it. `--main-app-id` is the host `main_app_id` for that sub-application, for example `456`; bytedcli normally resolves it from `GET /byteio/api/v1/app/selector/{app_id}`, so pass it only when automatic lookup fails or a manual override is required. `--event <name>` is repeatable and matches `log_info.event_name` by exact equality; matching is case-sensitive and does not support substring, prefix, or wildcard matching. If the event name is uncertain, omit `--event` first to inspect the actual `event_name`, then rerun with an exact filter. `--log-type <name>` is repeatable and matches `raw_event.log_type` by exact equality; use it for technical events whose `event_name` is empty and whose real name appears in `raw_event.log_type`. When both filters are provided, a record matching either `--event` or `--log-type` is output. Omit both filters to output every `event_log`. When filters are enabled, `--max-events` counts only matched events. Frontier may split large `method=5` payloads across frames with `id`/`idx`/`len`; bytedcli acknowledges each frame, reassembles the payload bytes, then parses and filters the complete `event_log`.

Running and stopping: the command keeps the connection open and streams events live, so trigger the events on the device (tap/scroll/play) while it runs. Run only one watch per device at a time when possible; the backend may not support multiple subscriptions for the same device, so a new connection may kick the old connection or interfere with it. With neither `--duration` nor `--max-events` it runs until you stop it with Ctrl-C (a graceful shutdown that sends the Frontier FINISH frame and closes the session cleanly). Use `--duration <seconds>` to auto-stop after a fixed time, `--max-events <count>` to auto-stop after that many matched events, or both (whichever fires first). The device must stay inside its byteio connection-page activation window (a time-limited session, empirically ~18 minutes); if it expires or the socket drops, the command fails and must be rerun (v1 has no auto-reconnect).

POST commands that have typed options also support `--body-json <json>` to merge additional documented fields into the request body.

`event create` / `event update` do not use `--body-json`; they accept:

- `--params-json <json>` for the `params` array
- `--payload-json <json>` for the final object-level override

`--payload-json` replaces duplicate scalar or array fields as whole values. Arrays such as `params`, `tags`, and `os` are not merged element-by-element.

## BTM create authentication

`btm point create` does not use the OpenAPI `Authorization` header. It uses the same ByteIO Web BFF credential resolution as `byteio console ...`.

- For Titan-only automation: run `bytedcli --site i18n-tt auth login`, then run the command with `byteio --auth-mode titan` (this targets the sg BFF `https://io-sg.tiktok-row.net`).
- In `auto` or `browser`, existing browser sessions are reused when available (scoped to the site-derived origin's cookie domain).
- In `auto` or `browser`, override: set `BYTEDCLI_BYTEIO_WEB_COOKIE` to a valid cookie header for the site-derived origin (`io-sg.tiktok-row.net` for `i18n-tt`, `data.bytedance.net` otherwise).

## BTM create examples

```bash
# 字段版：常用字段直接走 flags
bytedcli byteio btm point create \
  --app-id 7418 \
  --parent-id 196916 \
  --type block \
  --site-id 189925 \
  --owner demo.user \
  --label 测试区块 \
  --image-url 'https://data.bytedance.net/byteio/api/v1/file/images/demo.png'

# 贴近浏览器请求：补 business_modules / parent_ids / codes 细项
bytedcli byteio btm point create \
  --app-id 7418 \
  --parent-id 196916 \
  --type block \
  --site-id 189925 \
  --owner demo.user \
  --label 测试区块 \
  --body-json '{"business_modules":[null],"parent_ids":[196916],"codes":[{"label":"测试区块","image_url":"https://data.bytedance.net/byteio/api/v1/file/images/demo.png","index_code":false}]}'
```

## Transform rules (数据加工 / 转换规则)

All `byteio transformation ...` / `byteio transform ...` commands call Mario at `<console origin>/mario/api/v2/...` with the console Web BFF cookie chain (`--site cn` for `https://data.bytedance.net`). Responses are Mario envelopes `{ status: 200, message: "SUCCESS", data, page?, auth? }`. In default/`auto` mode, a non-200 `status` surfaces as `BYTEIO_API_ERROR`. In `titan`/`browser` mode, failures use sanitized `BYTEIO_WEB_*` categories, such as `BYTEIO_WEB_FORBIDDEN` for 403 and `BYTEIO_WEB_SERVICE` for 503.

List commands expose `total` (backend total, `null` when Mario omits page metadata) plus `currentCount`; `version list`, `auditor list`, `release list`, and `test-history list` expose `count`. Rule content (`transform get`) is normalized to camelCase; `filter`, `flatFilter`, and `action` are passed through verbatim because they are the Mario DSL the console editor stores:

```json
{
  "bool": "and",
  "clauses": [
    { "field": "header.app_id", "op": "in", "value": "(123,456)", "pid": "1" },
    {
      "pid": "1",
      "bool": "or",
      "clauses": [
        { "field": "event_name", "op": "in", "value": "(\"demo_event\")", "pid": "3" },
        { "field": "params", "func": ".asJson().getStringField(\"scene\",\"\")", "op": "==", "value": "\"demo\"", "pid": "3" }
      ]
    }
  ]
}
```

Status labels:

| Field                                      | Values                                                                                                                          |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `transform get` / `version list` `status`  | 0 `draft`, 1 `online`, 2 `was_online`, 3 `online_reviewing`, 4 `offline_reviewing`, 5 `upgrade_reviewing`, 6 `gray`, 7 `online_test` |
| `transform list` `status`                  | 0 `not_online`, 1 `online`, 2 `was_online`, 3 `online_reviewing`, 4 `offline_reviewing`, 5 `upgrade_reviewing`, 6 `gray_reviewing` |
| `transformation` `status`                  | 0 `configuring`, 1 `online`, 2 `testing`, 3 `offline`                                                                           |
| release `auditType`                        | 1 `online` (first release), 2 `offline`, 3 `upgrade` (a version is already online)                                             |
| release `auditStatus`                      | -1 `withdrawn`, 0 `pending`, 1 `gray`, 2 `rejected`, 3 `completed`                                                              |
| `transform test` item `status`             | -1 `format_error`, 0 `not_matched`, 1 `matched`, 2 `test_exception`                                                             |

Write behavior:

- `transform update` loads the base version (`--base-version`, default latest), rebuilds the console editor's request body (`transformation`, `id`, `version`, `name`, `comment`, `pass_through`, `filter`, `action`, `tag_list`, plus `event_name` / `action_codes` / `action_type` for `transform_e2a` transformations), applies the flags, and sends `PUT`. Read-only fields from `transform get` (`filterView`, `flatFilter`, `sourceFilters`, status and audit metadata) are never sent. The response `data` is the new draft version number (`new_version`). `transform create` sends the same body without `id` / `version` and returns the new rule id.
- `transform test` sends the same rule body plus `data` (the input message text; a leading `/* ... */` comment block is stripped like the console editor) and optional `source_dataset`. The rule under test is the item whose `rule_id` is `-1` (falling back to the real rule id); `matched` is `true` / `false` only for `matched` / `not_matched`, otherwise `null` with `currentStatusLabel` (`test_exception` / `format_error`) and `currentException`.
- `transform release check` / `create` run the console preflight: the target version must be `draft` or `was_online` for `--action online` and `online` for `--action offline`; `online_check` failures (for example `NOT_FROM_ONLINE_VERSION`) are warnings; a rule alarm that is not configured (`alarm.alarmDisabled`) blocks `--action online` and only warns for `--action offline`; when the transformation has `requireAudit`, `--auditor` must be one of `transformation auditor list`. `release create` sends `{ audit_type, version, env: "prod", comment, auditor?, process_type? }` (`process_type` 1 / 0 from `--auto-approval` / `--no-auto-approval`).
- `release cancel` sends `DELETE .../publish/{id}/`, the console 撤回上线申请 action; the record stays in `release list` with status `withdrawn`. Preview shows the current record first.
- Every write previews as `status: "dry_run"` with the exact request until `--yes` is passed; JSON success payloads carry `applied: true` and `mode` (`created` / `updated` / `submitted` / `cancelled`).

## Response interpretation

For existence checks:

- `exists: true`: `byteio console event get` succeeds and `data.event.name` matches the requested event.
- `exists: false`: the command returns `BYTEIO_CONSOLE_EVENT_NOT_FOUND`.
- `exists: "unknown"`: authorization, permission, network, timeout, invalid JSON, or unclear business errors.

Always include concise evidence: the structured error code when present, or the matched event name and `parameterCount` for successful detail responses.

## Flow write workflow

```bash
# 本地 JSON 全链路
BYTEDCLI_BYTEIO_AUTHORIZATION=<token> \
bytedcli byteio flow run \
  --app-id 1128 \
  --requirement-payload-json '{"name":"byteio-demo","sync_app_ids":[1128],"os":["android"],"owners":["demo.user"],"creator":"demo.user","develop_owners":"review.user"}' \
  --events-json '[{"event_name":"demo_event","trigger_type":"tech","description":"描述","category":"business"}]'

# dry-run 校验，不发请求
BYTEDCLI_BYTEIO_AUTHORIZATION=<token> \
bytedcli byteio flow run \
  --app-id 1128 \
  --requirement-payload-json '{"name":"byteio-demo","sync_app_ids":[1128],"os":["android"],"owners":["demo.user"],"creator":"demo.user","develop_owners":"review.user"}' \
  --events-json '{"creator":"demo.user","events":[{"event_name":"demo_event","trigger_type":"tech","description":"描述","category":"business"}]}' \
  --dry-run

# JSON 输出
BYTEDCLI_BYTEIO_AUTHORIZATION=<token> \
bytedcli --json byteio flow run \
  --app-id 1128 \
  --requirement-payload-json '{"name":"byteio-demo","sync_app_ids":[1128],"os":["android"],"owners":["demo.user"],"creator":"demo.user","develop_owners":"review.user"}' \
  --events-json '{"creator":"demo.user","events":[{"event_name":"demo_event","trigger_type":"tech","description":"描述","category":"business"}]}'
```

Behavior notes:

- `flow run` 使用 JSON 输入创建需求并批量录入事件。
- 创建链路为：先调当前 region 对应的 `/service/available` 获取 `requirement:create_requirement_v2` 的 `url` 并创建需求，再获取 `requirement:import_event_v2` 的 `url`，拼接成完整 URL 后以 `{ creator, events }` 调用 `event_records?requirement_id=...` 批量创建需求内埋点。
- requirement v2 请求体按 `name`、`description`、`sync_app_ids`、`os`、`owners`、`creator` 组织；响应需求 ID 在 `data.id`。`creator` 若未显式传入，会使用 `--events-json` 包装对象里的 `creator` 或 `owners[0]`。
- v2 支持 `product_owners`、`develop_owners`、`test_owners`；CLI 接受逗号分隔字符串或字符串数组，发送时统一转成逗号分隔字符串。`involved_employee` 不属于 v2 创建请求，CLI 不会发送该字段。
- `--events-json` 的最小事件字段为 `event_name`、`trigger_type`、`description`、`category`；`trigger_type` 取值范围为 `click/show/stay/slide/play/page_view/result/tech`。可选字段包括 `cost_business_line_name`、`image_urls`、`tags`、`business_module_id`、`scenes`、`remark`、`params`。兼容输入别名 `name -> event_name`。
- `params` 中 `param_data_type` 仅支持 `string` / `integer` / `float` / `boolean`；`param_type` 仅支持 `ordinary` / `enum` / `range`；`is_required` 支持 `0/1`（字符串或数字）及布尔值输入。
- `--events-json` 支持数组、单对象，以及包装对象中的 `events` / `event_records`；`schemas` 可作为兼容别名读取。
- `sync_app_ids` 自动补齐当前 `--app-id`。
- 批量创建接口失败时，会为本批次中的每个事件生成 retry list。
- 成功输出会汇总 `requirementId`、`createdCount`、`failedCount`、`failures`、`batchEventResponse`；`failures[]` 内含 `index`、`event_name`、`code`、`message`。
