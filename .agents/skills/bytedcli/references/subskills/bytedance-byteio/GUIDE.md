---
name: bytedance-byteio
description: "Operate ByteIO via bytedcli: send a complete 1-50 event envelope through an approved MCS HTTPS origin, watch realtime event_log JSONL from an online device, query and create/update event schema metadata, check event parameters, inspect requirements, BTM points, test cases, location attributes, location events, ad tags/labels, run the Authorization-based requirement/event write workflow (`byteio flow run`), and manage ByteIO 数据加工 transform rules (Mario transformations): list rule sets and rules, read versions and diffs, create rules and save new rule versions, run the console rule test, and submit, track, or withdraw release (上线/下线) requests via `byteio transformation ...` / `byteio transform ...`. Use `byteio event send` only with an approved MCS origin and complete envelope; use `tea event send` for a single app_id/event/params event or dry-run. Also use for ByteIO metadata/governance, realtime capture, 需求, 点位, BTM, 测试用例, 广告 tag/label, 导入写入链路, ByteIO 数据加工 (Mario 转换规则), and ByteIO 转换规则修改/测试/上线申请。"
---

# bytedcli ByteIO

Use this skill for ByteIO event tracking metadata and governance queries, plus the requirement/event write workflow.

## When to use

- 用户要确认某个埋点、事件名或 `event_name` 是否存在，或查看单个埋点元数据详情
- 用户要创建或修改 ByteIO 埋点元数据（event schema）
- 用户已有获批的 MCS domain、app_id 和已注册 event_name，需要上报单个或一批 ByteIO 事件
- 用户要校验埋点参数是否匹配 ByteIO schema
- 用户要查询 ByteIO 需求列表、需求详情、需求中的点位列表
- 用户要查询或创建 BTM 点位、业务线下点位、点位上的埋点
- 用户要查询测试用例信息列表、测试用例详情
- 用户要查询广告 tag / label，或按用户邮箱前缀查询埋点信息
- 用户要在 ByteIO 中创建需求并录入技术埋点事件
- 用户要执行 `byteio flow run`
- 用户要从在线真机实时抓取 ByteIO 埋点事件，使用 `byteio event watch`
- 用户要查询 ByteIO 数据加工（transformation / 规则集）、转换规则、规则版本、版本 diff、发布记录或审批人，使用 `byteio transformation ...` / `byteio transform ...`
- 用户要新建转换规则、修改转换规则（保存新版本）、用样例消息测试规则、提交或撤回上线 / 下线申请，使用 `byteio transform create|update|test|release ...`（`create` / `update` / `release create|cancel` 默认 dry-run，`--yes` 才提交；`test` 直接执行，`--dry-run` 仅预览请求体）

## Authentication

ByteIO has two authentication surfaces:

- OpenAPI commands use an `authorization` header from `BYTEDCLI_BYTEIO_AUTHORIZATION`.
- `byteio console ...` commands and existing Web BFF commands use the ByteIO console. The Web BFF origin is derived from the global `--site`: `i18n-tt` targets the sg BFF `https://io-sg.tiktok-row.net`, every other site targets `https://data.bytedance.net`. Set `BYTEDCLI_BYTEIO_WEB_ORIGIN` to override the origin explicitly. In default/`auto` mode, console commands first reuse `BYTEDCLI_BYTEIO_WEB_COOKIE` or a local Chromium session, then automatically fall back to the Titan Passport derived from `bytedcli auth login`.

Configure the OpenAPI credential before running OpenAPI query/read commands:

```bash
export BYTEDCLI_BYTEIO_AUTHORIZATION=<byteio-openapi-authorization>
```

ByteIO flow write commands use the same `authorization` header as ByteIO query/read commands:

```bash
export BYTEDCLI_BYTEIO_AUTHORIZATION=<byteio-openapi-authorization>
```

`byteio event send` is an independent MCS HTTP path. It does not use the OpenAPI
authorization header, a ByteIO Web BFF cookie, or the bytedcli login state. The
target origin, `app_id`, and registered event names provide the business routing
context; they are not authentication credentials.

Do not print or persist authorization/session secrets in summaries, docs, fixtures, or examples.

Web BFF authentication is selected with the group option `byteio --auth-mode auto|titan|browser` or `BYTEDCLI_BYTEIO_AUTH_MODE`. Precedence: explicit CLI value (including `auto`) > environment variable > `auto`.

- `auto` preserves the existing cookie order, fallback, refresh/retry behavior and errors: `BYTEDCLI_BYTEIO_WEB_COOKIE` → local Chromium cookies → Titan Passport. It may read browser private storage and trigger macOS Keychain permission prompts. A 401 on a business request refreshes Titan once as before.
- `titan` uses only the existing bytedcli Titan chain, including its site/profile/identity, cache and credential overrides. It ignores `BYTEDCLI_BYTEIO_WEB_COOKIE`, never extracts browser cookies and never starts interactive login. A clear 401 during acquisition, the probe or the business request shares one Titan refresh/retry budget. Missing credentials are reported with the matching site's `bytedcli auth login` command.
- `browser` uses `BYTEDCLI_BYTEIO_WEB_COOKIE` when nonempty; otherwise it extracts local Chromium cookies. A rejected explicit cookie must be updated by the caller; it is never replaced by another source. Local browser credentials can be reread once after a clear 401. It never falls back to Titan or opens an interactive login.
- In explicit `titan` / `browser` mode, 403, timeouts, network errors and 5xx never trigger authentication refresh or source switching. Errors distinguish missing/expired credentials, permissions, network/timeout and service failures without returning credential values.

For automation that must avoid browser Keychain access:

```bash
bytedcli --site cn auth login
bytedcli --site cn byteio --auth-mode titan console event get --app-id 123 --event-name demo_event
BYTEDCLI_BYTEIO_AUTH_MODE=titan bytedcli --site cn byteio console event get --app-id 123 --event-name demo_event
```

The mode applies to `console ...`, `btm point create`, `suite ...`, `test-case create|update|delete`, `event watch`, and all `transformation ...` / `transform ...` commands. It also applies to every request within those workflows. The same named MCP tools accept `authMode`, scoped to that invocation.

OpenAPI commands (including `event get`, `btm point get`, `test-case list|get` and `flow run`) continue using `BYTEDCLI_BYTEIO_AUTHORIZATION` and their existing routes. The auth-mode environment variable does not affect them; explicitly passing `titan` or `browser` is an error. Explicit `auto` preserves their behavior. Independent MCS `event send` likewise rejects explicit `titan` / `browser`.

## Common options

- `--auth-mode auto|titan|browser`: Web BFF authentication; default `auto` may read browser cookies. Explicit CLI values override `BYTEDCLI_BYTEIO_AUTH_MODE`.
- `--region cn|sg`: ByteIO OpenAPI region. Default: `cn`.
- `--body-json <json>`: supported by POST commands to merge extra request body fields from the API document.
- `--json`: global bytedcli flag. Put it before the command, for example `bytedcli --json byteio event get ...`.
- `byteio console ...` does not accept `--region`; it uses the ByteIO Web BFF and the global `--site` login state. The BFF origin follows `--site`: `i18n-tt` targets the sg BFF `https://io-sg.tiktok-row.net`, all other sites target `https://data.bytedance.net`. Pass the same `--site` value used with `auth login`.

## Command map

```bash
export MCS_ORIGIN=https://mcs.zijieapi.com

# 通过已获批的 MCS domain 上报事件；默认从 stdin 读取完整 envelope
printf '%s\n' '{"header":{"app_id":123},"events":[{"event_name":"demo_event","params":{"result":"success"}}]}' |
  bytedcli byteio event send --domain "$MCS_ORIGIN"

# 从文件上报；结构化输出的 --json 必须放在 byteio 前面
bytedcli --json byteio event send \
  --domain "$MCS_ORIGIN" \
  --input-file ./sample-event.json

# 查询单个埋点元数据详情
bytedcli byteio event get --app-id 123 --event-name demo_event

# 从在线真机实时抓取 event_log（仅 cn；默认 stdout 为 NDJSON）
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --max-events 10
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --event click_video_player --event go_video_detail_new --max-events 10
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --log-type bb_preload --log-type bb_task --max-events 10
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --event click_video_player --log-type bb_preload --max-events 10
bytedcli --site cn byteio event watch --app-id 123 --device-id did-under-test --main-app-id 456 --output ./events.ndjson
bytedcli byteio event get --app-id 123 --event-name demo_event --include-scene

# 创建 / 修改埋点元数据
bytedcli byteio event create --app-id 123 --name demo_event --owner demo.user --creator demo.user --description "演示埋点" --category business --os ios --payload-json '{"trigger_type":"click","params":[]}'
bytedcli byteio event update --app-id 123 --name demo_event --operator demo.user --description "更新后的埋点描述" --category business --os ios --payload-json '{"trigger_type":"click"}'

# 校验埋点参数
bytedcli byteio event check-params \
  --app-id-list 123 \
  --event-name-list demo_event \
  --param-name-list demo_param

bytedcli byteio event check-params \
  --checks-json '[{"app_id_list":[123],"event_name_list":["demo_event"],"param_name_list":["*"]}]'

# 根据用户邮箱前缀查询埋点信息
bytedcli byteio event list --owner demo.user

# 查询需求列表 / 详情 / 需求中的点位列表
bytedcli byteio requirement list --app-id 123 --keyword demo --page 1 --page-size 50
bytedcli byteio requirement get --requirement-id 456
bytedcli byteio requirement locations --app-id 123 --requirement-id 456

# 创建 / 查询 BTM 点位
bytedcli byteio btm point create --app-id 7418 --parent-id 196916 --type block --site-id 189925 --owner demo.user --label 测试区块
bytedcli byteio btm point create --app-id 7418 --parent-id 196916 --type block --site-id 189925 --owner demo.user --label 测试区块 --image-url 'https://data.bytedance.net/byteio/api/v1/file/images/demo.png'
bytedcli byteio btm point create --app-id 7418 --parent-id 196916 --type block --site-id 189925 --owner demo.user --label 测试区块 --body-json '{"business_modules":[null],"parent_ids":[196916],"codes":[{"label":"测试区块","image_url":"https://data.bytedance.net/byteio/api/v1/file/images/demo.png","index_code":false}]}'
bytedcli byteio btm point get --operator demo.user --requirement-id 456
bytedcli byteio btm point get --operator demo.user --requirement-id 456 --btm-full-code-list demo.point

# 查询测试用例信息列表 / 详情
bytedcli byteio test-case list --app-id 123 --event-name demo_event --page 1 --page-size 20
bytedcli byteio test-case get --test-case-id demo-case-id

# 根据业务线查询点位；根据点位查询点位上的埋点
bytedcli byteio map locations --app-id 123 --business-module-ids 1,2
bytedcli byteio map events --app-id 123 --full-identifier-list demo.page.button

# 查询广告 tag / label
bytedcli byteio ad tags
bytedcli byteio ad labels

# 查询 ByteIO 控制台 Web BFF 数据（复用 bytedcli 登录态）
bytedcli --site cn --json byteio console event get --app-id 123 --event-name demo_event
bytedcli --site i18n-tt byteio console event list --app-id 123 --page 1 --page-size 20
bytedcli --site i18n-tt byteio console requirement list --app-id 123
bytedcli --site cn --json byteio console requirement get --app-id 123 --requirement-id 456
bytedcli --site i18n-tt byteio console location-attribute list --app-id 123
bytedcli --site i18n-tt byteio console business-module list --app-id 123 --limit 100
bytedcli --site i18n-tt byteio console parameter list --app-id 123
bytedcli --site i18n-tt byteio console parameter list --app-id 123 --scope header   # 全局公共属性（Header.custom）
bytedcli --site i18n-tt byteio console parameter list --app-id 123 --scope system   # 平台预置 header 参数（只读，不分页）
bytedcli --json byteio console parameter create --app-id 123 --name demo_environment --data-type string --description "demo global attribute" --rd-owners demo.user   # 默认只预览，加 --yes 才提交
bytedcli --json byteio console parameter delete --app-id 123 --id 123456 --yes       # 删除前会校验该 id 属于全局公共属性

# 数据加工 / 转换规则（Mario transformation → transform rules；复用控制台登录态，写操作默认 dry-run）
bytedcli --site cn byteio transformation space list
bytedcli --site cn byteio transformation list --space-code data --keyword demo_sequence
bytedcli --site cn byteio transformation get --transformation data.demo_sequence
bytedcli --site cn byteio transformation auditor list --transformation data.demo_sequence
bytedcli --site cn byteio transform list --transformation data.demo_sequence --status online,was-online --keyword demo
bytedcli --site cn --json byteio transform get --transform-id 123 --version 2
bytedcli --site cn byteio transform version list --transform-id 123
bytedcli --site cn byteio transform version diff --transform-id 123 --from-version 1 --to-version 2
bytedcli --site cn byteio transform create --transformation data.demo_sequence --name data.demo_sequence_demo_rule --comment demo --filter-file ./filter.json
bytedcli --site cn byteio transform update --transform-id 123 --filter-file ./filter.json --comment "add demo_event"
bytedcli --site cn --json byteio transform update --transform-id 123 --base-version 2 --filter-file ./filter.json --comment "add demo_event" --yes
bytedcli --site cn byteio transform test --transform-id 123 --version 3 --input-file ./sample-event.json
bytedcli --site cn byteio transform test --transform-id 123 --filter-file ./filter.json --input-json '{"event_name":"demo_event","header":{"app_id":123},"params":"{}"}'
bytedcli --site cn byteio transform test-history list --transform-id 123
bytedcli --site cn byteio transform release check --transform-id 123 --version 3
bytedcli --site cn byteio transform release create --transform-id 123 --version 3 --auditor demo.user --comment "demo release"
bytedcli --site cn --json byteio transform release create --transform-id 123 --version 3 --auditor demo.user --comment "demo release" --yes
bytedcli --site cn byteio transform release list --transform-id 123
bytedcli --site cn byteio transform release get --release-id 555
bytedcli --site cn byteio transform release cancel --release-id 555
bytedcli --site cn byteio transform release cancel --release-id 555 --yes
```

## Realtime event watch

`byteio event watch` 仅支持 `--site cn`，默认把每条 `event_log` 输出为一行 JSON。`--app-id` 是要抓取的子应用 ID（例如 123；ByteIO 页面 URL 中也可能写作 `subAppId`，订阅帧里仍使用 `app_id`）；`--main-app-id` 是该子应用的宿主 `main_app_id`（例如 456），CLI 默认通过 app selector 自动反查，只有反查失败或需要手动覆盖时才传。`--event <name>` 按 `log_info.event_name` 精确等值匹配，可重复传入，例如 `--event click_video_player --event go_video_detail_new`；匹配区分大小写，不支持子串、前缀或通配，事件名不确定时先不加 `--event` 看全量输出里的实际 `event_name`，再精确过滤。`--log-type <name>` 按 `raw_event.log_type` 精确等值匹配，可重复传入，适合过滤 `event_name` 为空且真名位于 `raw_event.log_type` 的技术事件，例如 `bb_preload` / `bb_task`。同时提供 `--event` 与 `--log-type` 时，命中任一条件即输出；两者都不提供时输出全部事件。启用过滤后，`--max-events` 只计算过滤后命中的事件数。CLI 会在解析前重组 Frontier 下发的多分片事件帧。

运行与停止：命令会保持连接并实时输出事件，运行期间需在设备上触发埋点（点击/滑动/播放）才有数据。同一设备同一时刻建议只运行一个 watch；后端可能不支持同设备多订阅，新连接可能踢掉旧连接或相互干扰。若既不传 `--duration` 也不传 `--max-events`，命令会一直监听，直到你按 Ctrl-C 手动停止（Ctrl-C 是优雅关闭：发送 Frontier FINISH 帧、干净关闭会话，不会把设备遗留在 active 状态）。用 `--duration <秒>` 到时自动停止，用 `--max-events <条数>` 收满指定条数后自动停止，或两者同时用（先到先停）。设备必须处于 byteio connection 页激活的限时会话窗口内（实测约 18 分钟），窗口过期或连接断开时命令会失败退出，需重新执行（v1 不自动重连）。

## MCS event sending

入口选择：

- 已有获批的 MCS HTTPS origin，并且输入是完整 envelope（1～50 个 events）：
  使用 `byteio event send`。
- 只需要通过 `app_id`、单个 `event` 和 `params` 上报，或需要 CLI 自动解析
  用户身份、使用 `--dry-run`：使用 `tea event send`。

`byteio event send` 接收一个完整的 `user/header/events` JSON envelope。输入来源为：

- 默认 stdin；
- `--input-file <path>` 读取 UTF-8 JSON 文件；
- `--input-json <json>` 接收内联 JSON。

`--input-file` 与 `--input-json` 互斥。`--domain` 必填，只允许使用
[ByteIO reference](references/byteio.md#mcs-https-allowlist) 中内置白名单里的
HTTPS origin；HTTP、凭据和自定义端口都会被拒绝。不要根据 app_id 或 event_name
猜测域名。示例通过 `MCS_ORIGIN` 明确选择一个获批的白名单 origin。
`--path` 默认 `/v1/json`，只能是同源绝对 path；`--timeout-ms` 范围为
2000～3000，默认 2500。

真实发送属于业务写操作。执行前必须向用户汇总并确认：精确 domain/path、
`app_id`、event_name 列表、事件数量、重复执行次数与事件 QPS 上界，以及将要发送
的 payload 字段范围。只有用户已经在当前任务中明确确认这些值时才能直接发送；
不能用历史验证批次替代本次确认。

每次调用只提交一个 envelope，接受 1～50 个 events 并保持顺序。输入最大 1 MiB，
响应最大 64 KiB。命令不会自动重试；301/302/303/307/308 按标准方法转换跟随，
最多跟随 20 跳，但每一跳都必须仍在 HTTPS host 白名单内。HTTP 2xx 且 MCS
响应中 `e=0` 只表示接口接受请求，不等于下游最终入库。
需要端到端验收时，继续在业务批准的 Metrics 查询中确认 app_id 和 event_name。

## Existence checks

For "埋点是否存在" tasks, prefer:

```bash
bytedcli --site cn auth login
bytedcli --site cn --json byteio console event get --app-id 123 --event-name demo_event
```

Interpretation:

- `exists: true`: request succeeds and `data.event.name` matches the requested event.
- `exists: false`: command returns `BYTEIO_CONSOLE_EVENT_NOT_FOUND`.
- `exists: unknown`: authorization, permission, network, timeout, non-JSON, or unclear business errors.

The success result contains normalized event metadata, `parameterCount`, and complete parameter definitions in `parameters`. Always report `app_id`, `event_name`, existence, and concise response evidence. Do not include authorization or session values.

## Flow write workflow

`byteio event create` / `byteio event update` 直接写 ByteIO schema 元数据，使用与 OpenAPI 查询命令相同的 `BYTEDCLI_BYTEIO_AUTHORIZATION` 认证头：

```bash
export BYTEDCLI_BYTEIO_AUTHORIZATION=<byteio-openapi-authorization>
bytedcli byteio event create --app-id 123 --name demo_event --owner demo.user --creator demo.user --description "演示埋点" --category business --os ios --payload-json '{"trigger_type":"click","params":[]}'
bytedcli byteio event update --app-id 123 --name demo_event --operator demo.user --description "更新后的埋点描述" --category business --os ios --payload-json '{"trigger_type":"click"}'
```

Notes:

- `event create` 写入 `POST /open/v1/schema`。
- `event update` 写入 `PUT /open/v1/schema`。
- 两个命令都会先根据常用 flags 组装基础 payload，再用 `--payload-json` 覆盖同名字段。
- `--params-json` 只接受 JSON object 数组；`--payload-json` 只接受 JSON object。
- `event create` 要求 `--owner` 和 `--creator`；`event update` 要求 `--operator`，`--owner` 可选。

```bash
# 本地 JSON 全链路（创建需求 -> 在该需求下批量创建事件）
BYTEDCLI_BYTEIO_AUTHORIZATION=<token> \
bytedcli byteio flow run \
  --app-id 1128 \
  --requirement-payload-json '{"name":"byteio-demo","description":"需求备注","sync_app_ids":[1128],"os":["android","ios"],"owners":["demo.user"],"creator":"demo.user","develop_owners":"review.user"}' \
  --events-json '[{"event_name":"demo_event","trigger_type":"tech","description":"描述","category":"business"}]'

# dry-run 只做校验和归一化，不发请求
BYTEDCLI_BYTEIO_AUTHORIZATION=<token> \
bytedcli byteio flow run \
  --app-id 1128 \
  --requirement-payload-json '{"name":"byteio-demo","sync_app_ids":[1128],"os":["android"],"owners":["demo.user"],"creator":"demo.user","develop_owners":"review.user"}' \
  --events-json '{"creator":"demo.user","events":[{"event_name":"demo_event","trigger_type":"tech","description":"描述","category":"business"}]}' \
  --dry-run
```

Notes:

- `flow run` 使用 JSON 输入创建需求并批量录入事件。
- 创建链路为：先调当前 region 对应的 `/service/available` 获取 `requirement:create_requirement_v2` 的 `url` 并创建需求，再获取 `requirement:import_event_v2` 的 `url`，拼接成完整 URL 后以 `{ creator, events }` 调用 `event_records?requirement_id=...` 批量创建需求内埋点。
- requirement v2 请求体按 `name`、`description`、`sync_app_ids`、`os`、`owners`、`creator` 组织；响应需求 ID 在 `data.id`。`creator` 若未显式传入，会使用 `--events-json` 包装对象里的 `creator` 或 `owners[0]`。
- v2 支持 `product_owners`、`develop_owners`、`test_owners`；CLI 接受逗号分隔字符串或字符串数组，发送时统一转成逗号分隔字符串。`involved_employee` 不属于 v2 创建请求，CLI 不会发送该字段。
- `--events-json` 的最小事件字段为 `event_name`、`trigger_type`、`description`、`category`；`trigger_type` 取值范围为 `click/show/stay/slide/play/page_view/result/tech`。可选字段包括 `cost_business_line_name`、`image_urls`、`tags`、`business_module_id`、`scenes`、`remark`、`params`。兼容输入别名 `name -> event_name`。
- `params` 中 `param_data_type` 仅支持 `string` / `integer` / `float` / `boolean`；`param_type` 仅支持 `ordinary` / `enum` / `range`；`is_required` 支持 `0/1`（字符串或数字）及布尔值输入。
- `--events-json` 支持数组、单对象，以及包装对象里的 `events` / `event_records`；`schemas` 可作为兼容别名读取。
- `sync_app_ids` 会自动补齐当前 `--app-id`。
- 批量创建接口失败时，会为本批次中的每个事件生成 retry list。
- 成功输出会汇总 `requirementId`、`createdCount`、`failedCount`、`failures`、`batchEventResponse`；`failures[]` 内含 `index`、`event_name`、`code`、`message`。
- 当没有 `BYTEDCLI_BYTEIO_AUTHORIZATION` 时，会返回 `BYTEIO_AUTH_REQUIRED`；先设置环境变量后重试。

## Transform rule workflow (数据加工 / 转换规则：修改 → 测试 → 申请上线)

`byteio transformation ...` 操作 Mario 数据加工（规则集），`byteio transform ...` 操作规则集里的单条转换规则。所有命令走控制台 Web BFF 登录态（`--site cn`），不需要 `BYTEDCLI_BYTEIO_AUTHORIZATION`。需要 `filter` DSL 树的完整示例、`status` / `auditStatus` / `auditType` / 测试 status 的数值→语义映射，或各写命令的请求体与预检细节时，读 `references/byteio.md` 的 "Transform rules (数据加工 / 转换规则)" 小节。

定位目标：

- 控制台 URL `/byteio/transformations/<transformation>/transforms/<id>?type=transform&version=<n>` 直接给出 `--transformation`、`--transform-id`、`--version`。
- 只知道规则集名称时先 `transform list --transformation <name> --keyword <fragment>`（`--transform-id <id>` 精确定位）；只知道序列名称片段时先 `transformation list --keyword <fragment>`。

读取基线：

- `bytedcli --site cn --json byteio transform get --transform-id <id> --version <n>` 返回 `filter`（Mario 过滤 DSL 树：`{bool, clauses:[{field, func?, op, value} | {bool, clauses}]}`）、`action`、`passThrough`、`filterView`（可读文本）、`status`/`statusLabel`；先保存这份输出作为变更前基线。
- `transform version list` 给出每个版本的状态（`draft` / `online` / `was_online` / `*_reviewing`）与 `latestVersion`、`onlineVersion`；`transform version diff` 输出两版本的可读规则文本。

修改：

- 新建规则用 `transform create --transformation <name> --name <rule> --filter-file ./filter.json`，成功后返回新的 `transform_id`（版本 1，草稿）。
- 修改已有规则时复制 `filter` 到本地文件做最小改动，再 `transform update --transform-id <id> --filter-file ./filter.json [--comment ...] [--base-version <n>]`。不带 `--yes` 只输出 `dry_run` 预览（完整 PUT body 与 `changed_fields`），确认 diff 与用户意图一致后再加 `--yes`。
- `--base-version` 默认是最新版本；从旧版本改动时显式指定。预览与结果都带 `stale_base` 与 `warnings`：基线不是最新版本时 `stale_base: true`，表示新草稿会丢掉后续版本的改动。预览提示会给出 `--yes --base-version <预览基线>`，按它执行可保证提交的基线就是确认过的那份；中途有人保存新草稿时 `--yes` 那次报 `BYTEIO_TRANSFORM_BASE_STALE` 拒绝提交，确认要丢弃后续版本改动时再加 `--allow-stale-base`。保存成功会返回 `new_version`，规则进入草稿状态，线上版本不受影响。
- `filter` / `action` 是整块替换；`--tags` 整体替换标签，`--pass-through` / `--no-pass-through` 切换透传；`--payload-json` 只在需要补文档未拆成 flags 的规则字段时使用，不能覆盖 `id` / `version` / `transformation`。请求体只包含控制台编辑器发送的字段（`transformation`、`name`、`comment`、`pass_through`、`filter`、`action`、`tag_list`，以及 update 的 `id` / `version`），`transform get` 里的 `filterView` / `flatFilter` / `sourceFilters` 等只读字段不会回传。没有任何字段变化时命令报 `BYTEIO_TRANSFORM_NO_CHANGES`。

测试：

- `transform test --transform-id <id> --version <new_version> --input-file ./sample-event.json` 等价于控制台「测试」抽屉；输入必须是一条与 Kafka 源数据格式一致的消息（可从 `transform test-history list` 的历史输入或控制台样例复制）。
- 结果里 `matched` 为 `true` / `false` 时表示当前规则命中 / 未命中；为 `null` 时说明规则执行异常或输入格式错误，看 `current_status_label` 与 `current_exception`，不要把它当成"未命中"。`items[]` 列出整个规则集下每条规则的结果（`matched` / `not_matched` / `test_exception` / `format_error`）。围绕本次 diff 至少覆盖应命中、应不命中、边界样例各一条，并记录版本号。
- 传 `--filter-file` 等覆盖项可以在保存前测试未落盘的改动；正式提交审批前必须用已保存的版本号重测一次。

申请上线：

- `transform release check --transform-id <id> --version <n>` 先做预检：目标版本状态、`online_check`（例如 `NOT_FROM_ONLINE_VERSION` 只是警告）、规则报警门禁（未配置报警会成为 blocker）、`require_audit` 与可选审批人列表。
- `transform release create --transform-id <id> --version <n> --auditor <user> --comment <理由>` 默认只预览；`--yes` 才提交 `POST .../publish/`。`audit_type` 由 CLI 自动推导：从未上线 → 1（上线），已有线上版本 → 3（升级），`--action offline` → 2（下线）。规则集开放自动审批时可加 `--auto-approval` / `--no-auto-approval`。存在 blocker 时即使 `--yes` 也拒绝提交。
- 提交后用 `transform release list --transform-id <id>` 跟踪 `auditStatusLabel`（`pending` / `gray` / `rejected` / `completed` / `withdrawn`）；审批通过后规则才真正上线，`release get --release-id <id>` 可核对审核文本与线上文本。撤回待审批的申请先不带 `--yes` 运行 `release cancel --release-id <id>` 预览当前申请记录，与用户确认后再加 `--yes`（记录保留在 `release list` 中，状态变为 `withdrawn`）。
- 不要用 `byteio event update`、`byteio flow run` 或 `byteio test-case` 替代转换规则的保存、测试或上线；它们操作的是埋点 schema / 需求 / 埋点测试用例。

## References

- `references/byteio.md`：命令与 API 路径对照、参数清单、MCS 白名单，以及 transform 规则的 filter DSL 示例、状态码表和写命令请求体；需要精确端点、数值状态含义或请求体字段时读。
- `../../invocation.md`：bytedcli 调用与 `--json` 输出约定；首次在 Agent 流程中调用 bytedcli 时读。
- `../../troubleshooting.md`：鉴权、cookie、网络类报错的排查；命令报 `BYTEIO_WEB_AUTH_REQUIRED` 等错误时读。
