---
name: bytedance-bytelink
description: "通过 bytedcli 查询 ByteLink 各子能力的元数据与 Trace：liveim 租户/方法/重保房间/WRDS/WSS，ByteLink app、unicast/multicast/broadcast 方法、multicast namespace、uplink service，以及设备连接、消息发送、消息推送、订阅快照与 log ID 反查。当用户提到 ByteLink、liveim、unicast、multicast、broadcast、app/namespace/uplink 元数据、消息发送/推送链路、设备连接或 Trace 时使用。"
---

# bytedcli ByteLink

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

## 使用范围

ByteLink 是产品名称，liveim、unicast、multicast、broadcast 是其并列子能力。命令分为两类：

- 元数据查询（`bytedcli bytelink <resource> ...`）：查询 liveim 租户/方法/重保房间/WRDS/WSS，以及 ByteLink app、unicast/multicast/broadcast 方法、multicast namespace、uplink service 的平台元数据。
- Trace 诊断（`bytedcli bytelink trace ...`）：既有 `liveim-*` 用于 liveim 子模块，`bytelink-*` 用于 ByteLink 的设备连接、单播、组播和广播事实。

两类命令并存，按要查询的对象或诊断的子能力选择，不存在迁移或替换关系。所有命令均为只读，不会发送消息或修改线上配置。

## 元数据查询命令

统一经 `cloud_admin` 只读 facade 返回 `total` 与 `items`；不支持分页，也不使用时间窗口参数。list 接口的文本搜索字段按模糊匹配处理，`--status`、`--forward-type` 等枚举字段按精确值匹配；get 接口按业务主键精确匹配。

| 查询对象            | 命令                                            | 关键入参                                                                |
| ------------------- | ----------------------------------------------- | ----------------------------------------------------------------------- |
| liveim 租户列表     | `bytedcli bytelink liveim tenant list`          | 可选 `--tenant-id`、`--owner`、`--im-cluster`（均模糊）                 |
| liveim 租户详情     | `bytedcli bytelink liveim tenant get`           | `--tenant-id`                                                           |
| liveim 方法列表     | `bytedcli bytelink liveim method list`          | `--tenant-id`，可选 `--method`、`--message-type`、`--caller`            |
| liveim 方法详情     | `bytedcli bytelink liveim method get`           | `--tenant-id`、`--method`                                               |
| 重保房间列表        | `bytedcli bytelink liveim focus-room list`      | `--tenant-id`，可选 `--room-id`（模糊）、`--status`                     |
| 重保房间详情        | `bytedcli bytelink liveim focus-room get`       | `--tenant-id`、`--room-id`                                              |
| 重保房间 Top 100    | `bytedcli bytelink liveim focus-room top`       | `--tenant-id`                                                           |
| WRDS 房间数据列表   | `bytedcli bytelink liveim tool-room-wrds list`  | `--tenant-id`、`--room-id`，可选 `--sync-key`                           |
| WSS 设备在线列表    | `bytedcli bytelink liveim tool-device-wss list` | `--tenant-id`，且 `--user-id` / `--device-id` 至少一个，可选 `--app-id` |
| ByteLink 应用列表   | `bytedcli bytelink app list`                    | `--app-id` 或 `--keyword` 至少一个                                      |
| ByteLink 应用详情   | `bytedcli bytelink app get`                     | `--app-id`                                                              |
| 单播方法列表        | `bytedcli bytelink unicast method list`         | `--method` 或 `--owner` 至少一个                                        |
| 单播方法详情        | `bytedcli bytelink unicast method get`          | `--method`                                                              |
| 组播 namespace 列表 | `bytedcli bytelink multicast namespace list`    | `--namespace`                                                           |
| 组播 namespace 详情 | `bytedcli bytelink multicast namespace get`     | `--namespace`                                                           |
| 组播方法列表        | `bytedcli bytelink multicast method list`       | `--namespace` 或 `--method` 或 `--owner` 至少一个                       |
| 组播方法详情        | `bytedcli bytelink multicast method get`        | `--namespace`、`--method`                                               |
| 广播方法列表        | `bytedcli bytelink broadcast method list`       | `--method` 或 `--owner` 至少一个                                        |
| 广播方法详情        | `bytedcli bytelink broadcast method get`        | `--method`                                                              |
| 上行服务列表        | `bytedcli bytelink uplink service list`         | `--id`/`--psm`/`--uri`/`--owner`/`--forward-type` 至少一个              |
| 上行服务详情        | `bytedcli bytelink uplink service get`          | `--id`                                                                  |

```bash
# liveim 租户与方法元数据
bytedcli bytelink liveim tenant list --owner demo-owner
bytedcli bytelink liveim method list --tenant-id demo-tenant --method DemoMessage

# 重保房间：列表、详情与当前 Top 100
bytedcli bytelink liveim focus-room list --tenant-id demo-tenant --status focusing
bytedcli bytelink liveim focus-room top --tenant-id demo-tenant

# WRDS / WSS 只读排障
bytedcli bytelink liveim tool-room-wrds list --tenant-id demo-tenant --room-id 10002
bytedcli bytelink liveim tool-device-wss list --tenant-id demo-tenant --device-id 10001

# ByteLink 原生元数据：app / method / namespace / uplink
bytedcli bytelink app list --keyword demo-app
bytedcli bytelink unicast method get --method DemoMethod
bytedcli bytelink multicast namespace list --namespace demo-ns
bytedcli bytelink multicast method get --namespace demo-ns --method DemoMethod
bytedcli bytelink broadcast method list --owner demo-owner
bytedcli bytelink uplink service list --forward-type rpc
```

- `--forward-type` 仅支持 `http` 或 `rpc`。
- 组播方法详情必须同时传入精确 `--namespace` 和精确 `--method`，避免不同 namespace 下的同名方法产生歧义。
- 重保房间 `--status` 可省略，或传入 `all`（全部）、`focusing`（重保中）、`finished`（已结束）；bytedcli 在命令边界映射为后端 wire 值。
- 精确详情与工具查询使用的 `--room-id`、`--device-id`、`--user-id`、`--app-id`、`--id` 必须是 `1..9223372036854775807` 范围内的十进制字符串，可安全查询超过 JavaScript 安全整数范围的 ID；普通列表过滤中的 `--room-id`、`--app-id`、`--id` 是模糊匹配文本片段，不受该整数范围约束。
- 元数据命令不支持 `--page` / `--page-size` / `--limit`，也不接受时间窗口参数；通过过滤参数控制返回范围。

## Trace 诊断命令

| 诊断目标                          | 命令                                                        | 关键入参                                                                                                                                                                              |
| --------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| liveim 设备连接、短轮询、重连     | `bytedcli bytelink trace liveim-device-connection list`     | `--device-id`，可选 `--tenant-id`、`--room-id`                                                                                                                                        |
| liveim 房间消息发送和丢弃事实     | `bytedcli bytelink trace liveim-room-message-send list`     | `--tenant-id`、`--room-id`，可选 `--log-id`、`--method`、`--msg-id`、`--with-drop`                                                                                                    |
| liveim 设备推送、拉取、ACK        | `bytedcli bytelink trace liveim-device-message-push list`   | `--tenant-id`、`--room-id`、`--device-id`，可选 `--method`、`--msg-id`                                                                                                                |
| liveim log ID 反查发送事实        | `bytedcli bytelink trace liveim-logid-message-send list`    | `--log-id`                                                                                                                                                                            |
| ByteLink 设备连接事件             | `bytedcli bytelink trace bytelink-device-connection list`   | `--device-id`，可选 `--user-id`、`--app-id`                                                                                                                                           |
| ByteLink 单播、组播、广播发送     | `bytedcli bytelink trace bytelink-message-send list`        | `--msg-type`；unicast 需 `--device-id` / `--user-id`，multicast 需 `--namespace`、`--publisher-id`，all 同时需要两组选择器；可选 `--method`、`--msg-id` / `--msg-id-list`、`--app-id` |
| ByteLink 设备推送事实             | `bytedcli bytelink trace bytelink-message-push list`        | `--device-id`，可选 `--msg-id` / `--msg-id-list`、`--app-id`                                                                                                                          |
| ByteLink 组播订阅快照和窗口前基线 | `bytedcli bytelink trace bytelink-multicast-subscribe list` | `--device-id`，可选 `--namespace`、`--publisher-id`、`--app-id`                                                                                                                       |

## 前置条件

- 使用 ByteCloud SSO 登录；命令会自动获取所需 JWT。
- `liveim-device-connection list`、`liveim-room-message-send list` 和 `liveim-device-message-push list` 的查询时间窗口必须位于最近 7 天，且最长为 30 分钟；使用 `--start`、`--end` 传入 Unix 毫秒。
- `liveim-device-message-push list` 必须同时提供 tenant、room 和 device。
- `--log-id` 仅用于 `liveim-room-message-send list` 收窄发送事实，或作为 `liveim-logid-message-send list` 的主查询条件；设备连接和设备推送路由不消费该筛选项。
- `--room-id`、`--device-id` 和 `--msg-id` 均以 `1..9223372036854775807` 范围内的十进制字符串原样传递；`--msg-id` 支持重复传入或逗号分隔，三者均可安全查询超过 JavaScript 安全整数范围的 ID。返回结果中的 `room_id`、`msg_id`、`device_id`、`user_id` 也为十进制字符串。
- 所有 Trace 命令均支持 `--limit`，默认值为 `3000`。CLI 只校验 `--limit` 为正整数，不设置最大值，具体上限交给后端处理。Trace 不支持分页。
- 原子 Trace 的 `--start`、`--end` 是 Unix 毫秒，窗口最长 30 分钟且必须位于最近 7 天。`--device-id`、`--user-id`、`--msg-id` 和 `--msg-id-list` 均为 `1..9223372036854775807` 范围内的十进制字符串；`--msg-id-list` 最多 100 个且不能与 `--msg-id` 同时使用。`--app-id` 受客户端限制，必须是正 JavaScript 安全整数。
- `bytelink-message-send list` 必须显式传入 `--msg-type <unicast|multicast|broadcast|all>`：unicast 需要 `--device-id` 或 `--user-id`；multicast 需要 `--namespace` 与 `--publisher-id`；all 同时需要这两组选择器；broadcast 不需要额外选择器。`all` 由 CloudAdmin 在单次查询中完成聚合、排序并按 `limit` 截断，bytedcli 不会分别请求三种消息类型。

## 快速开始

```bash
# 在最近 7 天内生成一个五分钟窗口
now_ms=$(($(date +%s) * 1000))

# 设备连接事件
bytedcli bytelink trace liveim-device-connection list --device-id 10001 --start $((now_ms - 300000)) --end "$now_ms"

# 房间消息发送和丢弃事实
bytedcli bytelink trace liveim-room-message-send list --tenant-id demo-tenant --room-id 10002 --start $((now_ms - 300000)) --end "$now_ms" --method DemoMessage --with-drop

# 设备消息推送、拉取和 ACK 事实
bytedcli bytelink trace liveim-device-message-push list --tenant-id demo-tenant --room-id 10002 --device-id 10001 --start $((now_ms - 300000)) --end "$now_ms"

# 根据 log ID 反查发送事实
bytedcli bytelink trace liveim-logid-message-send list --log-id sample-log-id --limit 100

# ByteLink 设备连接事件
bytedcli bytelink trace bytelink-device-connection list --device-id 10001 --start $((now_ms - 300000)) --end "$now_ms"

# ByteLink 全类型消息发送；由 CloudAdmin 返回单一 records 集合
bytedcli bytelink trace bytelink-message-send list --msg-type all --device-id 10001 --namespace demo-namespace --publisher-id demo-publisher --start $((now_ms - 300000)) --end "$now_ms" --limit 100

# 单播发送：device_id、user_id 至少提供一个
bytedcli bytelink trace bytelink-message-send list --msg-type unicast --user-id 10003 --start $((now_ms - 300000)) --end "$now_ms"

# 组播发送：namespace、publisher_id 必填
bytedcli bytelink trace bytelink-message-send list --msg-type multicast --namespace demo-namespace --publisher-id demo-publisher --start $((now_ms - 300000)) --end "$now_ms"

# 设备推送事实
bytedcli bytelink trace bytelink-message-push list --device-id 10001 --start $((now_ms - 300000)) --end "$now_ms"

# 组播订阅快照与窗口前基线
bytedcli bytelink trace bytelink-multicast-subscribe list --device-id 10001 --namespace demo-namespace --publisher-id demo-publisher --start $((now_ms - 300000)) --end "$now_ms"
```

## 输出说明

- 默认文本模式展示查询元数据、记录表和服务端提示。
- 使用全局 `--json` 获取结构化结果。元数据命令返回 `total` 与 `items`（get 命令返回 `total=1` 与单元素 `items`）；Trace 命令的 `records` 为诊断事实，`total` 为匹配总数，`query_meta` 包含实际时间窗口、limit 和截断状态。
- JSON 会保留 CloudAdmin 返回的前向兼容字段，但凭据类字段会递归脱敏；WRDS `data_sync_key_value` 中 protobuf 定义的 int64 字段会无损转成十进制字符串。单次响应超过 16 MiB 时命令会拒绝读取并返回结构化错误。
- 原子 Trace 按端点返回不同记录：连接记录包含 device/user/app、事件时间与类型、平台/pod/集群/IDC；发送记录包含 `msg_id`、首字母大写的消息类型字符串、创建时间与状态码；Push 当前只返回 `record_type=push` 的行，不单独返回 ACK 记录，匹配 ACK 时 `ack_time_ms` 为 ACK 时间、未匹配时为 `0`，`foreign_key` 是 push/ACK 关联键，匹配 ACK 的 `ErrorMsgIds` 会让受影响的 push 行携带 `client_parse_error=true`；订阅记录包含 publisher 列表及 `is_baseline`、`baseline_unknown`、可选 `publisher_matched`。组播基线最多向窗口前回看 6 小时，`baseline_unknown=true` 表示未找到可用快照，不等于设备未订阅。组播订阅的 `--publisher-id` 不筛除快照，只用于计算每条记录的 `publisher_matched`。
- Trace 出现截断提示时，请缩短查询时间范围，也可增加当前端点支持的过滤项：`liveim-room-message-send` 与 `liveim-device-message-push` 可用 `--method` / `--msg-id`；`bytelink-message-send` 可用 `--method` / `--msg-id` / `--msg-id-list`，`bytelink-message-push` 仅支持 `--msg-id` / `--msg-id-list`；设备连接可用该命令 help 中列出的 tenant/room/user/app 等条件，组播订阅可用 namespace/app，`--publisher-id` 仅计算匹配标记。CLI 不声明端点最大值。Trace 不支持翻页获取后续记录。元数据命令没有分页，请用过滤参数缩小范围。
- 当 CloudAdmin 原子 Push 记录的 `msg_type=unknown` 时，表示上游尚未提供可靠的消息类型分类。必须原样保留并明确告知用户，可结合 `msg_id` 查询发送记录或核查上游 Trace；不要推断为 `unicast`、`multicast` 或 `broadcast`。
