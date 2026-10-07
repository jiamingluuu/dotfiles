# Volcano TLS 全量命令参考

`bytedcli volcano tls` 通过契约生成器（`bytedcli-dev sync tls`）从 ve-tls-cli 的 Swagger 派生契约全量生成，覆盖火山引擎日志服务（TLS）的 311 个操作，按 26 个命令分组组织。

## 命令结构

```
bytedcli volcano tls <group> <verb> [options]
```

- `<group>`：契约 id 前缀（如 `alarm`、`log`、`dashboard`），对应 TLS 的资源域。
- `<verb>`：契约 id 后缀（如 `create`、`list`、`delete`），对应具体操作。
- 选项名由契约字段名 PascalCase → kebab-case 派生（`TopicId` → `--topic-id`）。

## 命令分组（26 组 / 311 操作）

| 命令组              | 操作数 | 说明                                 |
| ------------------- | ------ | ------------------------------------ |
| `log`               | 62     | 日志管理（写入、查询、消费、回流等） |
| `alarm`             | 26     | 告警管理                             |
| `import`            | 21     | 数据导入                             |
| `host-group`        | 18     | 机器组管理                           |
| `dashboard`         | 17     | 仪表盘                               |
| `etl`               | 17     | 数据加工                             |
| `template-market`   | 15     | 模板市场                             |
| `copilot`           | 14     | Copilot                              |
| `processor`         | 14     | 数据处理器                           |
| `collector`         | 13     | 采集配置管理                         |
| `index`             | 12     | 索引管理                             |
| `consumer-group`    | 11     | 消费组管理                           |
| `olap`              | 9      | OLAP 分析                            |
| `schedule-sql-task` | 8      | 定时 SQL 分析                        |
| `trace`             | 8      | Trace 存储                           |
| `shipper`           | 7      | 数据投递                             |
| `account`           | 6      | 账号管理                             |
| `metric-topic`      | 5      | 指标主题管理                         |
| `tag`               | 5      | 标签管理                             |
| `topic`             | 5      | 日志主题管理                         |
| `kafka-proxy`       | 4      | Kafka 协议消费                       |
| `log-back-flow`     | 4      | 数据回流                             |
| `materialized-view` | 3      | 物化视图                             |
| `project`           | 3      | 日志项目管理                         |
| `shard`             | 3      | 分区管理                             |
| `api-key`           | 2      | ApiKey 管理                          |

> 另有 9 个手写命令（`project list/get`、`topic list/get`、`index get`、`log search`、`log context`、`trace list/get`）提供更富 UX（id-or-name 解析、定制表格），不在生成层中。`PutLogs` / `WebTracks` 两个写操作因需要 protobuf / webtracks 线格式编解码，以手写命令提供（见下文「写入日志」）。

## 通用约定

### 高危操作与 `--confirm`

契约标记 `risk.level: "high"` 的操作（180 个）必须显式传 `--confirm` 才会真正发送请求；未启用 `--dry-run` 且缺少 `--confirm` 时拒绝执行并提示：

```bash
# 高危操作不加 --confirm → 拒绝
bytedcli volcano tls alarm delete --alarm-id demo-alarm
# → Error: `volcano tls alarm delete` is a high-risk operation and was not sent.

# 加 --confirm → 真正执行
bytedcli volcano tls alarm delete --alarm-id demo-alarm --confirm
```

### `--dry-run` 预览

所有非 GET 操作支持 `--dry-run`：打印将发送的 method / path / query / body，不实际发送请求，也不需要 `--confirm`。同时传入 `--dry-run` 和 `--confirm` 时，仍只预览。预览在本地完成，不验证云端权限、资源是否存在或服务端参数约束。GET 操作语义安全，即使传 `--dry-run` 也会正常发送。

```bash
bytedcli volcano tls alarm delete --alarm-id demo-alarm --dry-run
# → 输出 Dry run - request not sent 预览（Method/Path/Query/Headers/Body）

bytedcli volcano tls alarm delete --alarm-id demo-alarm --dry-run --confirm
# → 仍只输出预览，不发送删除请求
```

### 分页

带分页元数据的列表命令（45 个）注册 `--page`（1-based，默认 1）与 `--page-size`（默认值取自契约）为主分页参数，与 bytedcli 全局 `addPaginationOptions` 约定一致；`--page-number` / `--limit` 为隐藏兼容别名（无默认值，显式传入时优先于主参数）。handler 自动映射回契约的 `PageNumber` / `PageSize` 参数。

```bash
bytedcli volcano tls alarm list --project-id p-1 --page 2 --page-size 20
```

### 复杂字段 `--field-json`

object / array-of-object / 嵌套数组等复杂类型字段通过 `--field-json <json>` 传入，CLI 解析 JSON 后填充到请求。解析失败报 `VOLCANO_INPUT_ERROR` 并提示。

```bash
bytedcli volcano tls alarm create \
  --project-id p-1 --alarm-name cpu-high \
  --alarm-notify-group-json '["grp-1","grp-2"]' --confirm
```

### 凭证选项重命名

业务字段名为 `AccessKeyId` / `Region` 的操作，其 CLI 选项自动重命名为 `--source-access-key-id` / `--resource-region`，避免与凭证全局选项冲突。

### 隐藏命令

17 个操作仍生成且可执行，但从 `--help` / JSON help / 命令建议中隐藏（`_hidden` 标记）。它们分三类：

- **agent 协议**（非人工操作）：`consumer-group consume`（ConsumerHeartbeat）、`log consume-original-logs`、`log get-kafka-offset`。
- **一次性 onboarding / 法律协议**：`account activate`（ActiveTlsSvc，开通服务）、`account confirm-tls-copilot-agreement`（接受 Copilot 协议，应在控制台阅读协议文本后确认）。
- **控制台 UI 私有后端**：`log upload-assistant-attachment`、`log get-session-answer`、收藏夹三件套（`log add` / `get-favourites` / `delete`）、搜索页 V1 辅助接口六件套（`get-histogram-v1` / `statistics` / `log-field-quick-analyse` / `search-docids` / `search-full-texts` / `get-log-reduce-wildcard-summaries`）、`collector split-with-quote`。

知道命令名时仍可直接调用或查看其 `--help`；调试场景也可走下文「逃生舱」。

### 输出

- 文本模式：分页列表 → 紧凑表格 + Showing 摘要；普通数组 → 表格；扁平对象 → KV 表；空 → "OK"。
- `--json`：完整响应对象，不做字段裁剪。

## 写入日志

`volcano tls log put` 与 `volcano tls log web-tracks` 是两个手写写命令，线格式不是普通 JSON，因此不经过生成器。两者均为高危操作，需 `--confirm`；支持 `--dry-run` 预览逻辑请求体（编码前的 LogGroups / Logs）。

### `log put`（PutLogs，protobuf 线格式）

请求体是 protobuf 编码的 `LogGroupList`（`Content-Type: application/x-protobuf`），可选 zlib 压缩。CLI 自动计算 `x-tls-bodyrawsize`（压缩前字节数）、`log-count`、`earliest-log-time`、`latest-log-time` 等 stats 头，V4 签名覆盖编码后的线上字节。

```bash
bytedcli volcano tls log put \
  --topic-id <topic-id> \
  --log-groups-json '[{"Logs":[{"Time":1700000000000,"Contents":{"level":"INFO","msg":"hello"}}],"Source":"1.2.3.4"}]' \
  --confirm
```

- `--log-groups-json`（必填）：LogGroup 数组。每个 Log 的 `Time` 接受 Unix 毫秒（13 位）；秒（10 位）与纳秒（19 位）会像 SDK 一样归一化为毫秒；`<= 0` 取当前时间。
- `Contents` / `LogTags` 接受 `[{Key,Value}]` 数组或 `{key:value}` map 两种形式。
- `--compress-type none|zlib`（默认 `none`）：本运行时无 lz4，SDK 的 lz4 路径不可用。
- `--hash-key`（可选）：路由到指定 shard（`x-tls-hashkey`）。

### `log web-tracks`（WebTracks，JSON 线格式）

请求体是 JSON `{Source, Logs}`（`Content-Type: application/json`），不压缩发送（`x-tls-compresstype: none`）。

```bash
bytedcli volcano tls log web-tracks \
  --project-id <project-id> --topic-id <topic-id> \
  --logs-json '[{"event":"click","page":"/home"}]' \
  --confirm
```

- `--logs-json`（必填）：扁平 key→value map 数组，每个元素代表一行日志。
- `--source`（可选）：日志来源标识。

## 示例

```bash
# 查看某组下所有操作
bytedcli volcano tls alarm --help

# 查看单个操作的全部选项
bytedcli volcano tls alarm create --help

# 列出告警（分页）
bytedcli volcano tls alarm list --project-id <project-id> --page-size 20

# 创建告警（高危，需 --confirm）
bytedcli volcano tls alarm create \
  --project-id <project-id> \
  --alarm-name cpu-high \
  --severity critical \
  --alarm-notify-group-json '["grp-1"]' \
  --confirm

# 预览删除请求而不发送，无需 --confirm
bytedcli volcano tls alarm delete --alarm-id demo-alarm --dry-run

# JSON 输出
bytedcli --json volcano tls alarm list --project-id <project-id>
```

## 逃生舱

`bytedcli volcano tls raw --action <Action> [--body-json <json>] [--query-json <json>]` 可直接调用任意 TLS Action（含未生成的操作），用于调试或临时访问。

## 再生成

契约快照签入 `src/api/volcano/tls/contract/operations.json`。契约更新后：

```bash
bytedcli-dev sync tls            # 再生成全部产物
bytedcli-dev sync tls --check    # CI 漂移守卫（产物过期则非零退出）
```
