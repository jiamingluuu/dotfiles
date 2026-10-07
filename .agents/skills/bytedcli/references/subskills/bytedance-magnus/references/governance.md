# Magnus 高级治理配置

通过专用 GLS 治理接口查看或修改 Dorado 队列、数据清理、数据压缩、数据过期和快照过期。
这些接口负责服务端任务工作流；普通 `schema property update` 不等价于治理配置更新。
命令沿用 Magnus 全局 `--site` 和 Cloud JWT 路由，当前已在 CN 验证；其他站点取决于对应 GLS 部署能力。

```bash
bytedcli --json magnus config get --name demo_catalog.demo_db.demo_table
bytedcli magnus config update --name demo_catalog.demo_db.demo_table --config-file governance.yaml
# 确认预览并获得具体变更授权后提交
bytedcli magnus config update --name demo_catalog.demo_db.demo_table --config-file governance.yaml --yes
```

## 配置文件

`--config-file` 接受 UTF-8 JSON 或 YAML 对象，字段使用 lowerCamelCase。下列示例展示所有治理项；只保留本次确实需要修改的项。

```yaml
resourcePoolName: root.demo_queue
resourcePoolCluster: demo-cluster
cleanProperties:
  enabled: true
  ttl: 604800000
compactionProperties:
  enabled: true
  targetSize: 134217728
  minInputFiles: 2
  repeatHour: 1
  frequency: daily
  scheduleHour: "12"
dataExpirationProperties:
  enabled: true
  timeColumnIndex: event_date
  timeFormat: yyyyMMdd
  ttl: 259200000
snapshotProperties:
  enabled: true
  ttl: 259200000
  minSnapshotNum: 1
```

| 字段 | 单位与约束 |
| --- | --- |
| `resourcePoolName` / `resourcePoolCluster` | Dorado 队列名 / 集群名；启用或更新任一策略时两者必填，避免任务隐式回退默认资源；集群必须伴随启用策略 |
| `enabled` | 布尔值；每个提供的策略必填。`false` 停用该策略 |
| `ttl` | 正整数毫秒；清理至少 3 天（259200000）；数据/快照过期小于 5 年（157680000000） |
| `targetSize` | 正整数字节；134217728 表示 128 MiB |
| `minInputFiles` | 正整数文件数 |
| `repeatHour` | 正整数小时，不超过 2147483647 |
| `frequency` | `daily` 或 `hourly` |
| `scheduleHour` | 必须是字符串；天级别为一个 `0`–`23` 小时；小时级为 `"*"` 或 `"0,6,12,18"` |
| `timeColumnIndex` | 数据过期的基准时间列名称；沿用 GLS 字段名，值为列名 |
| `timeFormat` | 基准列日期格式，例如 `yyyyMMdd`，由服务端进一步校验 |
| `minSnapshotNum` | 保留的最少快照数，1–2147483646 |

启用策略时必须提供该策略的全部设置：清理 `ttl`；压缩 `targetSize/minInputFiles/repeatHour/frequency/scheduleHour`；数据过期 `ttl/timeColumnIndex/timeFormat`；快照过期 `ttl/minSnapshotNum`。不自动填入可能改变数据保留行为的默认值。未知字段、错误类型、重复 YAML/JSON 键和空配置会被拒绝。

## 更新与读取语义

- 默认 dry-run：先验证文件，再读取现状，输出 `plan.before` 和精确 `plan.request`。只有 `--yes` 才 POST，POST 不自动重试。
- 每个提供的策略整体替换其设置；省略的策略不提交、不改变。关闭清理示例：`{"cleanProperties":{"enabled":false}}`。修改一个策略时，服务端可能重建其任务参数；不要通过复制 `get` 的完整输出提交全部策略。
- 仅提供 `resourcePoolName` 更新表的资源池绑定，不改变现有 Dorado 任务的队列。修改任务资源时需一并提供该策略完整设置及明确的队列、集群。
- 队列设置与各策略更新可能分步生效，GLS 不提供 CAS；提交失败或超时后先运行 `config get` 核对，再决定是否重试。不要把提交成功当作后台治理任务已执行完成。
- 所有策略关闭时，GLS 配置接口返回 `config: null`，不能据此认定没有保存队列或关闭状态下的设置。
- `config get` 输出 `tasks`，包括 `taskType`、字符串 `taskId`（Dorado 任务 ID）、字符串 `projectId` 和 `nextRunTime`。任务关联元数据暂时不可用时 `tasks: null` 并附 `warnings`；响应契约异常（含不完整列表或无效 ID）以 `MAGNUS_RESPONSE_ERROR` 失败；`tasks: []` 表示完整查询未找到相关治理策略。
- 当前治理接口不返回下一次运行时间，`nextRunTime` 明确为 `null`；不会将其他执行时间或本地估算当作下一次运行时间。
- `config` 保留服务端扩展字段，顶层和策略字段规范为 lowerCamelCase，策略内的自定义参数映射保留原始键；更新文件只接受上述四类治理策略和队列字段。服务端仍负责权限、资源池和日期格式等校验。
