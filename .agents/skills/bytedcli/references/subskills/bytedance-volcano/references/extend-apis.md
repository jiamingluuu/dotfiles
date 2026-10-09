# 扩展 API

当 OpenAPI 未进入 `ve` metadata（unknown service/action）时使用本文件。工具优先级固定为：

1. `ve ... --force`：默认选择，适用于普通 Action/Version API；
2. `scripts/call_extend_api.py`：仅用于同一个 POST 同时要求 URL query 与 request body、而 ve 无法表达的接口。

两条路径都遵循主 SKILL 的读写与破坏性确认规则。

## 1. `ve --force`

`--force` 跳过本地 service/action 校验，因此必须补齐 metadata 原本提供的信息：

```bash
ve <service> <Action> \
  --version <YYYY-MM-DD> \
  --endpoint <host> \
  [--method GET|POST] \
  [--region <region>] \
  --<Param> <value> ... \
  --force
```

- `--version` 必填。
- 未知 service 必须有 `--endpoint`，也可由 profile 或 `VOLCENGINE_ENDPOINT` 提供。
- 默认 GET；POST 显式加 `--method POST`。
- 部分媒体/边缘接口无论资源位置都使用 `cn-north-1` 签名地域。
- `--body` 发送 JSON，不能与展开的 `--Param` 混用。
- `--header` 可增加 header，但 Host、Authorization、Content-Length 被禁止覆盖。
- `--force` 是 presence flag，只写 `--force`。
- `--output`、`--query` 照常可用。

```bash
ve domain_openapi CheckFee --version 2022-12-12 \
  --endpoint open.volcengineapi.com --region cn-north-1 \
  --domain example.com --force

ve dcdn DescribeRealtimeData --version 2021-04-01 \
  --endpoint open.volcengineapi.com --region cn-north-1 --method POST \
  --body '{"StartTime":"2026-01-01 00:00:00","EndTime":"2026-01-01 01:00:00","Metrics":["all"]}' \
  --force

ve metrics ListWorkspace --version 2024-06-29 \
  --endpoint metrics.cn-beijing.volcengineapi.com --method POST \
  --body '{"PageNumber":1,"PageSize":20,"ListGlobal":true}' --force
```

### 已确认的 service recipe

| Service          | Version      | Endpoint                             | Region        | Method   | Action                                                                                                           |
| ---------------- | ------------ | ------------------------------------ | ------------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| `account_verify` | `2018-01-01` | `open.volcengineapi.com`             | profile 默认  | POST     | `GetVerifyInfo`                                                                                                  |
| `agentkit`       | `2025-10-30` | `open.volcengineapi.com`             | profile 默认  | POST     | `ListRuntimes`、`GetRuntime`（只读，用 `--query` 白名单投影，见 [账单](billing.md)）                             |
| `cdn`            | `2021-03-01` | `cdn.volcengineapi.com`              | `cn-north-1`  | POST     | `DescribeOriginTopStatisticalData`                                                                               |
| `cp`             | `2023-05-01` | `open.volcengineapi.com`             | profile 默认  | POST     | `ListPipelineRunStagesInner`                                                                                     |
| `dcdn`           | `2021-04-01` | `open.volcengineapi.com`             | `cn-north-1`  | POST     | `DescribeRealtimeData`、`DescribeOriginRealtimeData`、`DescribeTopIPs`、`DescribeTopReferers`、`DescribeTopUrls` |
| `domain_openapi` | `2022-12-12` | `open.volcengineapi.com`             | `cn-north-1`  | GET/POST | 域名查询；`RegisterDomain` 为计费 POST                                                                           |
| `flink`          | `2021-06-01` | `open.volcengineapi.com`             | profile 默认  | GET/POST | GMS/GRS/GAS/GWS；部分 GWS 走 helper                                                                              |
| `flink`          | `2022-06-01` | `open.volcengineapi.com`             | profile 默认  | GET      | `ListGMCSResourcePool`                                                                                           |
| `ga`             | `2022-03-01` | `open.volcengineapi.com`             | `cn-north-1`  | GET/POST | 加速区域、带宽包、监听器日志等                                                                                   |
| `iot`            | `2021-12-14` | `iot.cn-shanghai.volcengineapi.com`  | `cn-shanghai` | POST     | 实例、产品、设备、物模型、属性、事件、服务调用                                                                   |
| `live`           | `2023-01-01` | `live.volcengineapi.com`             | `cn-north-1`  | POST     | 批量流转码与 Session 数据                                                                                        |
| `mcdn`           | `2022-03-01` | `open.volcengineapi.com`             | `cn-north-1`  | GET      | `DescribeCdnDomainConfig`                                                                                        |
| `metrics`        | `2024-06-29` | `metrics.<region>.volcengineapi.com` | 对应 region   | POST     | Workspace、QueryCluster、Preagg、Influx/Metrics query                                                            |
| `sec_agent`      | `2025-01-01` | `open.volcengineapi.com`             | profile 默认  | POST     | `Run*` 安全分析 workflow                                                                                         |
| `trademark`      | `2023-06-01` | `open.volcengineapi.com`             | `cn-north-1`  | GET/POST | 商标、申请人、需求与搜索                                                                                         |
| `veenedge`       | `2021-04-30` | `veenedge.volcengineapi.com`         | `cn-north-1`  | POST     | `StopCloudServer`、`RebootCloudServer`                                                                           |
| `vke`            | `2022-05-12` | `open.volcengineapi.com`             | profile 默认  | POST     | `CreateVirtualNode`、`ListVirtualNodes`                                                                          |
| `vmp`            | `2021-03-03` | `vmp.<region>.volcengineapi.com`     | 对应 region   | POST     | 仅 helper                                                                                                        |

如果 `ve <service> <Action> --help` 已成功，忽略本表并使用普通命令。升级 ve 后运行 `python3 scripts/audit_extend_apis.py` 查找已经被原生覆盖的 recipe。

`find_api.py` 只能定位 Service/Action/Version，不能确定 method、endpoint 或参数；这些必须来自用户材料、CLI 详细帮助或官方接口说明。

## 2. query + body helper

`ve --force --body` 无法把一部分字段放 URL query、其余放 body。只有这类接口才使用：

```bash
python3 scripts/call_extend_api.py --list
python3 scripts/call_extend_api.py --describe QueryMetrics
```

### 已登记 API

| Service | Version      | Endpoint                         | Body            | Action 与 query key                                                                                               |
| ------- | ------------ | -------------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------- |
| `vmp`   | `2021-03-03` | `vmp.<region>.volcengineapi.com` | form-urlencoded | `QueryMetrics`、`QueryMetricsRange`、`GetLabels`、`GetSeries` → `workspace`；`GetLabelValues` → `workspace,label` |
| `flink` | `2021-06-01` | `open.volcengineapi.com`         | JSON            | GWS Directory/Application/Draft/Event 操作；query keys 由 `--describe` 输出                                       |

所有字段统一放进 `--params` JSON，脚本负责把登记的 query key 移到 URL：

```bash
python3 scripts/call_extend_api.py \
  --api QueryMetrics \
  --params '{"workspace":"vmp-workspace-<id>","query":"up"}'

python3 scripts/call_extend_api.py \
  --api CreateGWSApplicationDraft \
  --params @request.json
```

主要选项：`--region`、`--host`、`--content-type`、`--output json|pretty`、`--show-headers`、`--profile`。STS Token 从环境变量或 profile 读取，不得放入命令行。

### 自由模式

只用于未登记但同样需要 query/body 拆分的 API：

```bash
python3 scripts/call_extend_api.py \
  --api SomeAction --service <svc> --version <YYYY-MM-DD> \
  --query-keys ProjectId,Type [--body-keys-also ProjectId] \
  [--method POST] [--host <endpoint>] \
  [--content-type application/x-www-form-urlencoded] \
  --params '{"ProjectId":"project-<id>","Type":"JOB","Other":"demo"}'
```

自由模式必须传 `--query-keys`；没有 query/body 拆分时应使用 `ve --force`。`--body-keys-also` 表示某个 query key 还必须保留在 body。

### 凭证解析顺序

1. 显式传 `--profile` 时严格使用该 profile；不存在、模式不支持或凭据无效时直接报错，不回退环境身份；
2. 未显式传 `--profile` 时，先使用 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` 及可选 `VOLCENGINE_SESSION_TOKEN`；
3. 环境 AK/SK 不完整时，再使用配置的 current profile，然后使用 `VOLCENGINE_PROFILE` / `VOLCSTACK_PROFILE` 选择的 profile。

helper 只支持普通 `ak`（含旧配置中的空 mode）和 `console-login` profile；后者只读取尚未过期的登录缓存，即使 profile 残留静态 AK 字段也不使用。`sso`、`ramrolearn`、`oidc`、`ecsrole` 和未知 mode 必须改用 ve，helper 会明确拒绝，不能用源 AK/SK 静默降级。helper 不刷新 SSO、不 assume role、不读取 ECS metadata。不得打印 AK/SK/SessionToken。

## 3. 参数说明

### 账号认证

`GetVerifyInfo` 无参数。个人实名为 `IsVerified=true, IdentityType=individual`；企业实名为 `IdentityType=enterprise`。

### CDN

`DescribeOriginTopStatisticalData` 必填 `Domain`、Unix 秒的 `StartTime/EndTime`、`Item=url` 和 `Metric`。

### CodePipeline

`ListPipelineRunStagesInner` 必填 `WorkspaceId`、`PipelineId`、`PipelineRunId`。先用公开的 `ve cp` list 接口获得 ID。

### DCDN

- Realtime 接口必填 24 小时内的 `StartTime/EndTime`（`YYYY-MM-DD HH:MM:SS`）和 `Metrics` 数组。
- Top 接口必填 `StartTime/EndTime`、`Sort`，Limit 为 1–100。

### Domain

参数为小写 snake_case：`CheckFee` 用 `domain`；`GetDomain` 用 `domain` 或 `instance_no`；`GetAsyncTask` 用 `task_no`；`GetTemplate` 用 `tag`。`RegisterDomain` 必填 `domain`、`template_tag`，会计费并创建异步任务，执行前必须确认。

### Flink

- GET 接口按帮助传 ProjectName/ProjectId/AppIdKey 和分页字段。
- `GetGWSApplication` 必填 `Id`；`ListGASLogs` 使用 Application、Project、时间范围及可选日志过滤。
- GWS helper 的 ProjectId、Id、JobName、DirectoryId、ResourcePool 等字段以 `--describe <Action>` 为准；不得在不同 Action 间照搬。

### Global Accelerator

带宽包、加速器维度、监听器日志和 Endpoint 关联查询均要求对应资源 ID 与分页/时间字段。先用只读 List 接口获得真实 ID。

### IoT

不同层级使用 InstanceId、ProductKey/ProductID、DeviceName/DeviceID、物模型 Identifier 等字段。`CallService`、`SetProperty` 是写操作，必须提供真实设备标识和输入参数并确认。

### Live

批量转码/Session 数据接口的 `StartTime/EndTime` 使用 RFC3339，可选 DomainList 和分页字段。

### Metrics

Workspace、QueryCluster、Preagg 使用各自 ID 与分页结构；InfluxQuery/MetricsQuery 需要 workspace、query 和时间范围。

### Security workflow

`sec_agent Run*` 必须使用真实告警、PCAP、URL、截图或文本；空调用不是有效验证。

### Trademark

Get 接口使用对应 ApplicantID/TrademarkID/RequirementID；List 接口使用分页和过滤；Search 至少提供商标名、申请人或注册号之一。

### VEEN

metadata 已有的 `StartCloudServer` 和 usage Action 使用普通 `ve veenedge`。`StopCloudServer`、`RebootCloudServer` 仍使用 force，参数为 `cloud_server_id`，执行前必须确认。

### VKE

`ListVirtualNodes` 支持分页与集群/节点过滤。`CreateVirtualNode` 需要 Kubeconfig 与 VirtualNodeConfig，且本表没有对应删除 Action，创建前必须先规划官方 VKE 清理路径。

### VMP

- QueryMetrics：`query` 和可选 `time`；Range 再加 `start/end/step`。
- Labels/Series/LabelValues 使用 Prometheus API 字段 `match[]`，不是 `match` 或 `matches`。
- 刚 remote-write 的样本只能在不早于样本时间的 instant query 中看到。
- 测试 Workspace、BasicAuth 和 remote-write endpoint 必须按当前 `ve vmp --help --detail` 验证，不得把凭证写入日志。

## 4. Agent 约束

- CLI 已知 Action 时始终用普通命令；只在 metadata 缺失时用 `--force`；helper 只处理 query+body。
- 不得发明参数。缺少业务 ID 时先用只读 List/Get 获取，仍无法确定再询问用户。
- `AccessDenied` 常表示 IAM 或产品 entitlement，不是请求形态问题；按 [常见错误](common-errors.md) 分类。
