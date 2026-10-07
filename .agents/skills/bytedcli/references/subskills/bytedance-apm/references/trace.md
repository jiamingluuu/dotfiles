# Argos Trace Search (`apm argos trace`)

Four commands wrapping `bytedtrace.byted.org/trace_api/v2/trace/query_obj_list`
(main search), `/trace_api/v2/trace/topology` (service call topology) and
`/trace_api/v1/meta/*` (discovery), authenticated with the Bytecloud JWT from
`cloud.bytedance.net`.

## When to use

- User asks to "search traces" / "找一下出错的 trace" / "找 ee.kunlun.datax 上一小时 5xx" / referencing the Argos page `/argos/trace/retrieve/conditionRetrieve`.
- User pastes a `bytedtrace.byted.org/trace_api/v2/trace/query_obj_list` curl.
- User asks for a service's "拓扑图 / 调用拓扑 / 上下游依赖图"（Argos 控制台的服务拓扑页面）— use `trace topology`.

For _single-trace expansion_ (`/trace_api/v2/trace/query_transactions`,
`query_trace_tree`) this skill is **not** the right entry — those live under
`log` today and remain unchanged.

## Commands

### `bytedcli apm argos trace search`

Required:

- `--psm <psm>` — service PSM.

Time window (either pair):

- `--from <epoch> --to <epoch>` — both required together; `--to > --from`.
- `--duration <d>` — relative window, e.g. `10m`, `1h`, `30s`. Default `10m` when neither pair is given.

Scope:

- `--category` (default `span`), `--type` (default `server`), `--view-point` (default empty; `callee` etc.).
- `--metrics-region` — defaults to `cn` for `cn`/`boe` sites, `sg` for `i18n-tt`.
- `--only-normal-trace` / `--no-only-normal-trace` — default true.
- `--desc` — sort by timestamp descending.
- `--page-size <n>` — 1..100, default 10.

Filters (JSON pass-through, AI-friendly):

- `--filter-tags-json '[{"tag_key":"_is_error","values":["true"],"data_type":"BOOL","is_range_query":false}]'`
- `--filter-tags-file <path>`

`data_type` accepts `STRING` (default) / `INT` / `LONG` / `BOOL`. `is_range_query` defaults to `false`.

Pagination:

- `--page-token <token>` — pass back the `next_page_token` (base64 cursor) from a previous response.

### `bytedcli apm argos trace categories --psm <psm>`

Returns the `(category, type, view_point)` combinations available for the PSM, plus their supported metrics. Use before search if unsure which `--category/--type` to pass.

### `bytedcli apm argos trace dimensions --psm <psm> --category <c> --type <t> [--view-point <v>]`

Returns the filter dimensions for that combo: `tag_key`, `tag_data_type`, `tag_display_name`, `is_range_query_tag`, `values` previews. Use before search to pick valid `tag_key` and the correct `data_type`.

### `bytedcli apm argos trace topology`

Fetches the directed service-call topology graph around one root node
(`nodes` + `edges`, same data as the Argos console topology page).

Required:

- `--psm <psm>` — root service PSM.

Root node narrowing (all optional; the backend `node_filters_v2.attrs` array is
derived from the flags actually provided):

- `--method <m>` / `--dc <dc>` / `--cluster <c>` — narrow the root node down to
  one method / dc / cluster combination. With `--psm` only, the graph contains
  one root node per existing method × dc × cluster combination.

Graph depth:

- `--upstream <n>` / `--downstream <n>` — layer counts, both default 1
  (console default). Depth ≥2 can grow the graph quickly (a depth-3 fan-out on
  a busy service can exceed 150 nodes).

Time window:

- Default: latest snapshot (`start_time: -1`, console default).
- `--start <epoch> --end <epoch>` — both required together; unix seconds.

Result filters (repeatable or comma-separated; omitted → backend defaults,
i.e. no filtering):

- `--swd strong,weak,unmarked,vague,biz_strong` — edge strong/weak-dependency marks.
- `--priority P0,P1,P2,P3` — node priority levels.
- `--service-type http,rpc,storage,mq,other` — node service types.

Output:

- Text mode: edge table (`FROM` / `TO` / `SWD` / `MAG_RATIO`), node labels
  resolved to `psm.method@dc/cluster`. Add `--mermaid` to also print a
  ` ```mermaid ` graph block ready to paste into docs.
- JSON mode: raw `nodes[]` + `edges[]` plus the `request` echo. Edge
  `swd_mark` / `traffic_estimation` are flattened out of the backend `extra`
  object; node/edge `id`s are opaque strings that only serve as `from`/`to`
  join keys.

## JSON output shape (search)

```json
{
  "status": "success",
  "data": {
    "items": [
      /* raw span objects from backend, untouched */
    ],
    "next_page_token": "eyJQcmVPZmZzZXQiOjEwfQ==",
    "request": {
      /* the body the CLI actually posted */
    }
  }
}
```

`next_page_token` is always present in the response (never null when more pages remain). The backend does not return `total`. To continue paging, call the same command with `--page-token <next_page_token>`.

## Typical AI usage

1. `bytedcli --json apm argos trace categories --psm example.demo.api` → pick `(category, type)`.
2. `bytedcli --json apm argos trace dimensions --psm example.demo.api --category span --type server` → discover `tag_key` + `data_type` for the filter you want.
3. `bytedcli --json apm argos trace search --psm example.demo.api --duration 10m --filter-tags-json '[{"tag_key":"_is_error","values":["true"],"data_type":"BOOL"}]' --page-size 20` → run the search.

Topology:

```bash
# 最新快照，方法/机房/集群圈定根节点，默认上下游各 1 层
bytedcli --json apm argos trace topology --psm example.demo.api --method sort --dc demo-dc --cluster default

# 只按 PSM 圈根节点 + 上游 2 层，只看强依赖边
bytedcli --json apm argos trace topology --psm example.demo.api --upstream 2 --swd strong

# 文本模式直接出 mermaid 图源码
bytedcli apm argos trace topology --psm example.demo.api --mermaid
```

## Common pitfalls

- 已验证的 site：`cn / boe / i18n-tt / eu-ttp / us-ttp` 五个。其它 site（`i18n` / `i18n-bd` / `us-ttp-bdee` / `us-ttp-usts`）会被显式 `CLI_INPUT_ERROR` 拒绝，理由是 bytedtrace 后端 host 与 ByteCloud JWT origin 的对应关系尚未验证，避免静默回退到错域名/错租户。若你确实需要这些 site，先在线下抓包确认 host + JWT issuer，再扩 `BYTEDTRACE_HOST_BY_SITE` + 补一条对应的离线测试。
- site → host 映射：`cn / boe` → `bytedtrace.byted.org`；`i18n-tt` → `bytedtrace-sg.tiktok-row.org`；`eu-ttp` → `bytedtrace-i18n.tiktok-eu.org`；`us-ttp` → `bytedtrace-og.tiktok-us.org`。
- **`us-ttp` 网络路由**：办公网/devbox 直连 `bytedtrace-og.tiktok-us.org` 常不可达（`fetch failed`），按 devbox 网络策略加 `--http-proxy`（如 RD 代理）重试；`eu-ttp` 默认直连可达，偶发 SSL 超时重跑即可。
- **`eu-ttp` 数据分区**：EU 实例同时承载 EU-TTP2（`no1a` 等挪威/爱尔兰 dc）与 US-EastRed（`useast2b`）两个分区，同一 PSM 的拓扑节点可能只落在其中一个分区——用 `--dc` 过滤区分；某 dc 返回空图代表该分区无此节点的拓扑数据，不是链路故障。
- **EU/US 网关（OG）对 body 做 schema 打标强校验**：请求体出现未登记字段会被整体拒绝（`invalid tagging` 错误）。CLI 只发已验证的字段集合，不要通过别的途径向这些 host 加自定义 body 字段。
- `metrics_region` 默认值：cn / boe → `"cn"`，i18n-tt → `"sg"`，eu-ttp → `"eu"`，us-ttp → `"us"`。需要查别的 vregion 时显式 `--metrics-region`。
- `--from/--to` and `--duration` are mutually exclusive — passing both is an input error.
- Backend is strict about `data_type`: passing `_is_error=true` with `data_type=STRING` may return zero rows. Always look up the real `data_type` via `dimensions` (or trust UI exports verbatim).
- The UI's `only_completed_trace` URL param is the same as the body's `only_normal_trace`. Use `--only-normal-trace` / `--no-only-normal-trace`.
