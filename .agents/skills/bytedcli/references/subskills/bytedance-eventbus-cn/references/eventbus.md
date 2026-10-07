# Eventbus 命令说明

Eventbus CN-only 命令使用 `bytedcli eventbus-cn`，仅支持国内 `cn` 和 `boe` 站点；国内生产 `--region` 支持 `CN`（华北）、`China-East`（华东）、`China-North6`（华北6），BOE 站点使用 `BOE`。i18n、US、EU 用户不支持该 skill。

当前开放命令：

```bash
bytedcli eventbus-cn event info --event <event-name> --region <region>
bytedcli eventbus-cn event storage list --event <event-name> --region <region> [--skip-rmq-quota]
bytedcli eventbus-cn event storage list --event-id <event-id> --region <region>
bytedcli eventbus-cn client get --event <event-name> --role <producer|consumer> --id <client-id|psm|group> [--region <region>]
bytedcli eventbus-cn client search [--event <event-name>] [--psm <psm>] [--region <region>] [--client-type <consumer|producer|all>]
bytedcli eventbus-cn mirror info --event <event-name>
bytedcli eventbus-cn message search --event <event-name> --region <region> --type msg_key --msg-key <key> --start-time <ms> --end-time <ms> [--storage-descriptor <list>] [--total <n>]
bytedcli eventbus-cn message search --event <event-name> --region <region> --type time_range --start-time <ms> --end-time <ms> [--storage-descriptor <list>] [--total <n>]
bytedcli eventbus-cn message search --event <event-name> --region <region> --type offset_range --partition <partition> --start-offset <offset> --end-offset <offset> [--storage-descriptor <list>] [--total <n>]
bytedcli eventbus-cn producer create --event <event-name> --owner <owner> --psm <psm> --desc <desc> --region <region> [--print-body] [--yes]
bytedcli eventbus-cn producer create --event <event-name> --data <json> --yes
bytedcli eventbus-cn consumer create --event <event-name> --owner <owner> --psm <psm> --group <group> --desc <desc> --region <region> [--print-body] [--yes]
bytedcli eventbus-cn consumer create --event <event-name> --data-file <path> --yes
```

## OpenAPI 路径

Eventbus 命令通过网关调用以下 OpenAPI 路径：

```text
GET  /api/v1/open/:event/info
GET  /api/v1/open/client/base_info
GET  /api/v1/open/client/base/list
GET  /api/v1/open/event/storage/list
GET  /api/v1/open/:event/mq_mirror
POST /api/v1/open/:event/search/msg_v2
POST /api/v1/open/:event/consumer/create
POST /api/v1/open/:event/producer/create
```

## 读接口

- `event info` 查询 event 详情，文本模式输出 Event、Region、Status、Type、Owners、Topics、Namespace、IAM、URL。
- `event storage list` 查询 event storage 绑定，接受 `--event-id <id>` 或 `--event <name>` 二选一；使用 `--skip-rmq-quota` 可跳过 RocketMQ quota 查询。
- `client get` 查询单个 producer/consumer client；`--id` 为非数字时，producer 按 PSM、consumer 按 group 查询，并需要 `--region`。
- `client search` 使用 Eventbus OpenAPI `client/base/list`；不同于控制面批量 search API，OpenAPI 单次请求接受一个 event、一个 psm、一个 region 和一个 role。精确 consumer group 查询请使用 `client get`。
- `mirror info` 查询 MQ mirror 信息。
- `message search` 使用 Eventbus OpenAPI `search/msg_v2` 查询消息；支持 `time_range`、`offset_range`、`msg_key` 三种结构化模式，`msg_key` 模式必须同时传 `--msg-key`、`--start-time`、`--end-time`，`--storage-descriptor` 默认 `0`，需要完整消息体时使用 `--json`。

## 写接口

- `producer create` 和 `consumer create` 通过 `--data` 或 `--data-file` 传 JSON object。
- `producer create` 未传 `--data/--data-file` 时，可通过 `--owner`、`--psm`、`--desc`、`--region` 组装请求体。
- `producer create` 默认填充推荐发送/告警参数，并按 PSM 从 ByteTree 派生 `service_tree_id` / `product_line`；可用 `--no-fill-defaults` 或 `--no-derive-bytetree` 关闭。
- `producer create --print-body` 只打印最终请求体，不发起创建请求。
- `consumer create` 未传 `--data/--data-file` 时，可通过 `--owner`、`--psm`、`--group`、`--desc`、`--region` 组装请求体。
- `consumer create` 默认填充推荐消费/告警参数，并按 PSM 从 ByteTree 派生 `service_tree_id` / `product_line`；可用 `--no-fill-defaults` 或 `--no-derive-bytetree` 关闭。
- `consumer create --print-body` 只打印最终请求体，不发起创建请求。
- 写接口必须显式传 `--yes` 才会发起真实请求。
- 请求体字段与 Eventbus OpenAPI 保持一致；常用字段包括 `owner`、`psm`、`desc`、`region`，consumer 还需要 `group`。

## JSON 输出

JSON 模式会返回：

- 解析后的核心字段
- 列表类结果数组
- `raw` 原始接口 payload；消息查询会保留 OpenAPI 返回的 header/body/origin_body
