# Neptune

## 查询服务框架

`neptune framework get` 通过 Neptune OpenAPI 按 PSM 查询服务框架、语言和部署平台，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune framework get --psm example.service
```

JSON 只输出 `psm`、`framework`、`language`、`deployment_platform`。后端未提供的可选字段返回 `null`。该命令调用 `GET /api/neptune/open_api/service_info/query`，不需要 zone、cluster、category 或 rpc_meta。

## 查询区域集群列表

`neptune deploy-unit list` 通过 Neptune OpenAPI 按 PSM 查询服务部署的区域、集群和部署平台，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune deploy-unit list --psm example.service
```

JSON 只输出 `psm` 和 `deploy_units`。每个 deploy unit 包含 `zone`、`cluster`、`deployment_platform`；后端未提供部署平台时返回 `null`，未部署时返回空数组。该命令调用 `GET /api/neptune/open_api/deploy_units/query`，请求 query 只包含 `psm`；全局 `--site` 仅用于选择 OpenAPI host 和认证环境，不会作为请求参数发送。

## 查询服务级配置

以下八条 `service get` 命令通过 Neptune OpenAPI 查询单个 PSM + cluster 的服务级配置，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

六站点路由均受支持。普通未配置会成功返回 `rule.exist=false`、`rule.config=null`；只有后端 category 查询能力不可用时才返回 `NEPTUNE_CATEGORY_UNAVAILABLE`。CLI 不回退到其他配置、站点或旧接口。

| 命令                               | 管理台配置与适用范围                           |
| ---------------------------------- | ---------------------------------------------- |
| `neptune strict-auth service get`  | 服务级严格授权配置                             |
| `neptune authen service get`       | 服务鉴权配置                                   |
| `neptune mtls service get`         | 服务 MTLS 配置                                 |
| `neptune over-ctrl service get`    | 服务过载保护配置                               |
| `neptune acc-ctrl service get`     | 访问控制配置，仅适用于使用 Archon 框架的服务   |
| `neptune inject-token service get` | Token 注入配置，仅适用于使用 Archon 框架的服务 |
| `neptune timeout service get`      | 请求超时配置，仅适用于使用 Archon 框架的服务   |
| `neptune circ-brkr service get`    | 熔断配置，仅适用于使用 Archon 框架的服务       |

所有 `service get` 都需要 `--zone`、`--psm`、`--cluster`；严格授权和服务鉴权还需要 `--method`，可以传具体方法或字面量 `'*'`。CLI 会为对应管理台配置发送完整五元组：

```text
严格授权、服务鉴权：caller="*", caller_cluster="*", callee=psm, callee_cluster=cluster, method=--method
MTLS、过载保护、Archon 访问控制：caller="*", caller_cluster="*", callee=psm, callee_cluster=cluster, method="*"
Archon Token 注入、请求超时、熔断：caller=psm, caller_cluster=cluster, callee="*", callee_cluster="*", method="*"
```

五元组的五个字段每次都会发送；上面没有使用的位置统一传字面量 `*`，不会省略或传空字符串。`--psm`、`--cluster` 始终表示正在查询的服务，CLI 会根据配置语义把它放到 caller 或 callee。`neptune strict-auth get`、`neptune mtls get`、`neptune timeout get`、`neptune circ-brkr get`（不含 `service`）仍是 caller→callee 五元组命令，需要各自的 caller、callee、cluster 和 method 参数；不要在两类命令间替换 selector。

Archon 是服务框架。访问控制、Token 注入、请求超时和熔断这四条服务级配置命令仅适用于使用 Archon 框架的服务；查询结果只能陈述配置的适用范围，不能证明目标是否使用 Archon。CLI/rules 响应也不支持从 `exist` 或 `config` 反推框架身份。

JSON 保留 `rule.exist`、完整 `rule.config`、`rpc_meta` selector 身份和 `log_id`（LogID）。只有后端明确返回 `exist=false` 且 value 缺失或为 null 时，`rule.config` 才是 null；缺失或畸形的 selector、配置、`exist` 或 config 会作为查询错误返回，不会归一化为 disabled 或“未启用”。CLI 不推断生效/effective 状态、继承、框架身份或 enabled/disabled 状态。

服务过载保护规则已配置时，若后端省略 `cpu_usage_threshold` 或返回 null，`rule.config.cpu_usage_threshold` 按管理台默认值投影为 `80`；后端返回显式值时保持不变。未配置的服务过载保护规则仍返回 `config:null`，其他服务级配置不应用该默认值。

```bash
# 服务级严格授权配置
bytedcli --trigger-source ai --site cn neptune strict-auth service get \
  --zone CN \
  --psm example.service.api \
  --cluster default \
  --method example.Method

# 服务鉴权配置
bytedcli --trigger-source ai --site cn neptune authen service get \
  --zone CN \
  --psm example.service.api \
  --cluster default \
  --method '*'

# 服务 MTLS 配置
bytedcli --trigger-source ai --site cn neptune mtls service get \
  --zone CN \
  --psm example.service.api \
  --cluster default

# 服务过载保护配置
bytedcli --trigger-source ai --site cn neptune over-ctrl service get \
  --zone CN \
  --psm example.service.api \
  --cluster default

# 访问控制配置（仅适用于使用 Archon 框架的服务）
bytedcli --trigger-source ai --site cn neptune acc-ctrl service get \
  --zone CN \
  --psm example.service.api \
  --cluster default

# Token 注入配置（仅适用于使用 Archon 框架的服务）
bytedcli --trigger-source ai --site cn neptune inject-token service get \
  --zone CN \
  --psm example.service.api \
  --cluster default

# 请求超时配置（仅适用于使用 Archon 框架的服务）
bytedcli --trigger-source ai --site cn neptune timeout service get \
  --zone CN \
  --psm example.service.api \
  --cluster default

# 熔断配置（仅适用于使用 Archon 框架的服务）
bytedcli --trigger-source ai --site cn neptune circ-brkr service get \
  --zone CN \
  --psm example.service.api \
  --cluster default
```

## 精确查询访问授权规则

`neptune strict-auth get` 通过 Neptune OpenAPI 查询一个 caller→callee 的 `acc_ctrl` 规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune strict-auth get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method "*"
```

JSON 的 `rule` 只输出核心规则字段 `exist`、`value`。`exist=false` 表示该精确 selector 没有独立规则；管理台仍可能从 `*` 方法或全局严格授权设置派生展示状态。OpenAPI 响应中的 `inherit`、`editable`、`effective`、`effective_details` 是不可用的默认占位值，本命令不解析或输出这些字段。

所有 selector 参数均需显式提供。每次请求仅包含一个 category 和一个 `rpc_meta`；查询结果无法唯一确认目标规则时直接报错，不回退旧命令。

## 精确查询 MTLS 流量状态规则

`neptune mtls get` 通过 Neptune OpenAPI 查询一个 caller→callee 的 `mtls_egress` 规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune mtls get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster lane-demo \
  --callee-psm example.callee \
  --callee-cluster default \
  --method GetItem
```

`--caller-psm`、`--caller-cluster` 和 `--method` 允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的 `rule` 只输出核心规则字段 `exist`、`enabled`。显式规则从布尔型 `value.tls_enabled` 映射 `enabled`；未配置规则返回 `exist=false`、`enabled=null`。OpenAPI 响应中的 `inherit`、`editable`、`effective`、`effective_details` 是不可用的默认占位值，本命令不解析或输出这些字段。

每次请求仅包含 category `mtls_egress` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺有效状态字段或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询请求超时规则

`neptune timeout get` 通过 Neptune OpenAPI 查询一个 caller→callee 的 `timeout` 请求超时规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune timeout get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster lane-demo \
  --callee-psm example.callee \
  --callee-cluster default \
  --method GetItem
```

`--caller-psm`、`--caller-cluster` 和 `--method` 允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `timeout_ms`。显式规则从对象型 `value.rpc_timeout_ms` 映射毫秒值 `timeout_ms`；未配置规则返回 `exist=false`、`timeout_ms=null`。管理台可能同时展示 1000ms 等平台默认请求超时，但该默认值不是当前 selector 的显式规则，本命令不会用默认值替代 `null`。读超时、写超时和连接超时也不属于本命令的 `timeout` 规则输出。

每次请求仅包含 category `timeout` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、非法毫秒值或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询请求重试规则

`neptune retry-config get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量请求重试规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune retry-config get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster "*" \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value.config` 返回完整请求重试配置；未配置规则返回 `exist=false`、`config=null`。管理台中的“满足配置生效条件”不是数据面实时状态，本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `retry_config` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value.config`、关键配置字段非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询熔断规则

`neptune circ-brkr get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量熔断规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune circ-brkr get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster "*" \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整熔断配置；未配置规则返回 `exist=false`、`config=null`。管理台中的配置生效条件不是数据面实时状态，本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `circ_brkr` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、关键配置字段非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询比例丢弃规则

`neptune drop-pct get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量比例丢弃规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune drop-pct get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster "*" \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整比例丢弃配置；未配置规则返回 `exist=false`、`config=null`。`idc_percentages` 的非空结构尚未独立验证，CLI 仅要求该属性存在并保留后端原值。管理台中的配置生效条件不是数据面实时状态，本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `drop_pct` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、缺 `drop_percentage` / `idc_percentages`、非法丢弃比例或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询自适应熔断规则

`neptune adaptive-breaker get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量自适应熔断规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune adaptive-breaker get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster "*" \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整自适应熔断配置；未配置规则返回 `exist=false`、`config=null`。CLI 仅校验管理台已独立确认的 `algorithm`、`breaker_option.min_k`、`breaker_option.max_k` 和 `dry_run`，其余嵌套字段保留后端原值。管理台中的配置生效条件不是数据面实时状态，本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `adaptive_breaker` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、关键配置字段非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询单实例限流规则

`neptune rate-lmt get` 应优先用于精确五元组查询，通过 Neptune OpenAPI 查询一个 caller→callee 的入流量单实例限流规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune rate-lmt get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster default \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整单实例限流配置；未配置规则返回 `exist=false`、`config=null`。CLI 要求 `mode` 为有限整数，并要求限额候选字段中至少一个为有限数值；候选字段存在时仅接受 `null` 或有限数值，其余字段保留后端原值。管理台中的配置生效条件不是数据面实时状态，本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `rate_lmt` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、限额配置非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询简单集群限流规则

`neptune cluster-rate-lmt get` 通过 Neptune OpenAPI 查询一个 caller→callee 的入流量简单集群限流规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune cluster-rate-lmt get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster default \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整简单集群限流配置；未配置规则返回 `exist=false`、`config=null`。CLI 要求 `mode` 为有限整数；`idc_rate_limits` 与 `dry_run_idc_rate_limits` 存在时必须为对象，每个 IDC 项必须为对象，`con`、`qph`、`qpm`、`qps` 存在时仅接受 `null` 或有限数值，两个 map 合计至少包含一个有限限额。其余字段保留后端原值。本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `cluster_rate_lmt` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、关键配置非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询流量重定向规则

`neptune redirect get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量重定向规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune redirect get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster default \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整重定向配置；未配置规则返回 `exist=false`、`config=null`。CLI 校验非空 `stage`、至少一个非空重定向目标、可选的 0 到 100 比例和字符串或 null 过期时间，其余字段保留后端原值。本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `redirect` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、关键配置非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询机房调度规则

`neptune idc-traffic get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量机房调度规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune idc-traffic get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster default \
  --method GetItem
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整机房调度配置；未配置规则返回 `exist=false`、`config=null`。CLI 要求 `mode` 与 `idc_traffic_mode` 为有限整数，`idc_weights` 为非空数组，每项的 `caller_idc`、`callee_idc` 为非空字符串，`weight` 为 0 到 100 的有限数值；其余字段保留后端原值。本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `idc_traffic` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、关键配置非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询负载均衡策略

`neptune lb-policy get` 通过 Neptune OpenAPI 查询一个 caller→callee 的出流量负载均衡策略，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune lb-policy get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster sample-cluster \
  --method "*"
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整负载均衡配置；未配置规则返回 `exist=false`、`config=null`。CLI 要求 `lb_type` 为有限整数；`ringhash_replicas` 存在时必须为正有限整数，但不会要求其他策略提供该字段，也不会把数值类型硬编码为策略名称。其余字段保留后端原值。本命令不输出 `effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `lb_policy` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、关键配置非法或 category 不可用时直接报查询错误，不回退旧命令。

## 精确查询优先地址/IP 版本规则

`neptune prior-addr get` 通过 Neptune OpenAPI 查询一个 caller→callee 的优先地址/IP 版本规则，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

```bash
bytedcli --trigger-source ai --site cn neptune prior-addr get \
  --zone CN \
  --caller-psm example.caller \
  --caller-cluster default \
  --callee-psm example.callee \
  --callee-cluster sample-cluster \
  --method "*"
```

五个 selector 参数都允许字面量 `*` 或实际值；CLI 将输入原样作为一个精确 selector，不展开通配符、不批量扫描。所有 selector 参数均需显式提供。

JSON 的核心规则字段只有 `exist` 和 `config`。显式规则从对象型 `value` 返回完整优先地址配置，其中 `priority` 必须是非空字符串；未配置规则返回 `exist=false`、`config=null`。其余字段保留后端原值。本命令不输出 `status`、`effective`、`inherit`、`editable` 或匹配基数。

每次请求仅包含 category `prior_addr` 和一个 `rpc_meta`。无精确匹配、重复匹配、缺 category、缺 `exist`、缺 `value`、缺或非法 `priority`、或 category 不可用时直接报查询错误，不回退旧命令。

Neptune 用于服务治理配置查询（安全/稳定性/限流/调度）和严格授权申请，支持跨站点排查差异。

## 调用来源标记（Agent Guidance）

Agent 执行每条 Neptune 命令时，必须在 `neptune` 子命令前传全局参数 `--trigger-source ai`：

```bash
bytedcli --trigger-source ai --json neptune strict-auth service get --psm example.service.api --cluster default --zone CN --method example.GetItem
```

bytedcli 会继续在现有 Neptune 业务请求中发送 `X-Call-Source: byted-cli`，并通过 `X-Trigger-Source: ai|cli` 携带调用来源元数据。该字段由服务端用于来源分类和上报；bytedcli 不会为此单独发送遥测事件或额外请求。不要根据 `--json`、TTY 或运行环境推断来源。直接 CLI 和 bash 脚本调用的优先级为：显式 CLI 参数 `--trigger-source` > 环境变量 `BYTEDCLI_NEPTUNE_TRIGGER_SOURCE` > 默认值 `cli`。

## Neptune Request Pacing（Agent Guidance）

Neptune Request Pacing 主要是 Agent 侧的 best-effort 命令间隔规范，用于降低自动扫描对 Neptune 控制面的压力；整体不是 bytedcli 运行时强制限流，也不保证服务端视角下的 1 QPS。一条命令本身可能产生多个控制面请求。`neptune caller list` 与 `neptune callee list` 的内部分页是明确例外：CLI 会串行全分页，并在每个后续页请求前固定等待约 1.1 秒。

每次执行 `bytedcli --trigger-source ai neptune ...` 时：

1. 每次只运行一条 Neptune 命令，当前命令结束前保持其他 Neptune 命令等待。
2. 当前命令结束后至少等待 1 秒，再启动下一条 Neptune 命令。
3. 优先使用明确的 site、region、PSM、method 和其他过滤条件执行聚焦查询；获得满足用户目标的结果后停止。
4. 把遍历多个 site / region / PSM / method、自动翻页、循环调用列表接口和连续探测多个 Neptune endpoint 视为广泛扫描。仅在用户明确要求该扫描时执行；执行时仍保持串行、使用可用过滤条件并尽早停止。

执行门槛：启动命令前，确认没有其他 Neptune 命令正在运行，并且上一条 Neptune 命令结束后已经等待至少 1 秒。

## 环境与站点

Use global `--site` to select the ByteCloud deployment. Per-service `--neptune-site` is a hidden alias for backward compatibility.

- CN: `--site cn`（默认）
- BOE: `--site boe`
- ByteIntl: `--site byteintl`
- TikTok ROW: `--site i18n-tt`（aliases: `i18ntt|row|tiktok|tiktok-row`；`sg` 保持兼容 ByteIntl）

站点差异（bytedcli 内部已处理）：

- CN/BOE：API host 在 ByteCloud 控制台域名下（`cloud.bytedance.net` / `cloud-boe.bytedance.net`），请求需要 `x-bcgw-tenant-id: bytedance`
- ByteIntl：API host 为 `cloud.byteintl.net`，请求不需要 `x-bcgw-tenant-id`
- TikTok ROW：API host 为 `cloud.tiktok-row.net`，请求不需要 `x-bcgw-tenant-id`

## 站点/VRegion 自动发现（best-effort）

命令：`neptune list-sites`

CLI 会调用平台 meta 接口 `list_platform_vregions?platform=neptune`（并缓存 1 天）来尽量列出支持的站点与 VRegion。

## zones/vregions 列表（best-effort）

命令：`bytedcli --trigger-source ai --site <site> neptune list-cp-regions`

用于查询 Neptune 当前站点支持的 `zones` 与 `vregions` 列表，便于为后续配置查询选择正确的 `--zone`。

## 命令映射

- `neptune caller list`：查询指定 callee 的完整上游服务列表，内部使用 ingress 调用链串行全分页、在后续页请求前等待约 1.1 秒，并按 PSM + cluster 去重。
- `neptune callee list`：查询指定 caller 的完整下游服务列表，内部使用 egress 调用链串行全分页、在后续页请求前等待约 1.1 秒，并按 PSM + cluster 去重。

两条调用链命令最多读取 100 页；接近上限时，仅页间等待即可接近 109 秒。调用期间不要并发启动其他 Neptune 命令，也不要仅因等待而提前判断命令卡死。

- CLI 不提供 caller→callee allow/deny verdict：控制面配置不能证明数据面当前实际生效。
- `neptune strict-auth apply`：严格授权申请（支持结构化参数，或 `--payload-json` / `--payload-file` 传完整 payload）；提交前会按控制面补齐 ACL extra_info、机房限流 QPS、domain custom form 与 leader review 校验

## 严格授权申请

命令：`bytedcli --trigger-source ai --site <site> neptune strict-auth apply`

结构化参数模式：

```bash
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth apply \
  --caller-psm example.caller.service \
  --caller-cluster default \
  --callee-psm example.callee.service \
  --callee-cluster default \
  --method GetProductByID \
  --method MGetProductsByIds \
  --zone SGALI \
  --reason "Need access for demo workflow"
```

完整 payload 模式：

```bash
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth apply --payload-file ./sample-neptune-strict-auth.json
```

- `--method` 和 `--zone` 支持重复传入或逗号分隔。
- 未传 `--zone` 时默认：`CN(cn/byteintl)`、`BOE(boe)`、`SGALI(i18n-tt)`、`US-TTP(us-ttp)`、`EU-TTP(eu-ttp)`。
- 平台新增字段尚未映射为 CLI flag 时，优先使用 `--payload-json` 或 `--payload-file`；raw payload 模式不要混用结构化 flags。
- 仅 `cn` 站点：申请区域命中 `China-North`（中国北部）、`China-North6`（中国北部6）、`China-East`（中国东部）但未完全覆盖时，TTY 会提示三地 ACL 应保持一致，并只在输入 `y/yes` 后继续；JSON 或非交互模式确认申请范围后必须传 `--confirm-acl-coverage`。

### strict-auth apply 动态补充信息

`strict-auth apply` 不是只把基础 caller/callee/method payload 发给后端。CLI 会先按目标 `site + zone + rpc_meta_list` 查询后端要求的附加信息，并在提交前校验：

1. ACL extra_info：额外字段与机房限流 QPS。
2. domain custom form：命中 domain governance 规则时要求的自定义表单。
3. leader review：`--approval-mode leader_review` 的 usage scenario 与风险确认。
4. CN 区域覆盖确认：防止 `China-North`（中国北部）、`China-North6`（中国北部6）、`China-East`（中国东部）的 ACL 只申请到部分区域。

Agent / JSON 模式建议：

- 普通 TTY 模式下，命令会交互式提示填写 extra_info / custom form。
- `--json` 模式不会交互；遇到缺失信息时，错误 `details` 会返回模板或后端要求，agent 应按模板补参后重试。
- `cn` 站点部分覆盖 `China-North`（中国北部）、`China-North6`（中国北部6）、`China-East`（中国东部）时，`--json` 不会交互；agent 必须先确认申请范围，再传 `--confirm-acl-coverage` 重试。
- 如果确认可以使用后端默认 extra_info，传 `--accept-extra-info-defaults`；否则在 `--json` 模式下用 `--extra-fields-json` 和 `--rate-limit-json` 显式覆盖，文本模式传这两个参数会直接报错。
- custom form 校验命中时，优先读取错误 `details.custom_form_payload_template`，再用 `--custom-form-payloads-json` 补齐；只有所有必填字段都有默认值时，才可以用 `--accept-custom-form-defaults`。
- `--approval-mode leader_review` 必须同时传 `--leader-confirm`；文本模式未传 `--usage-scenario` 时会交互选择当前站点的合法场景，`--json` 模式则必须显式传入合法值；当 rate limit extra_info 命中时不能使用 leader review。
- 这些错误 hint 会追加 Neptune Oncall 提示；需要业务判断或后端规则不清时，按提示咨询 Neptune Oncall。

常用补参示例：

```bash
# JSON/agent 场景：允许使用默认 extra_info
bytedcli --trigger-source ai --json --site i18n-tt neptune strict-auth apply \
  --caller-psm example.caller.service \
  --callee-psm example.callee.service \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --accept-extra-info-defaults

# 显式覆盖 extra field 与机房 QPS；rate-limit key 使用错误 details / payload 中的 caller|cluster|callee|cluster|method tuple
bytedcli --trigger-source ai --json --site i18n-tt neptune strict-auth apply \
  --caller-psm example.caller.service \
  --callee-psm example.callee.service \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --extra-fields-json '{"sample_extra_field":"sample value"}' \
  --rate-limit-json '{"example.caller.service|default|example.callee.service|default|GetProductByID":{"sample-idc":100}}'

# custom form：优先从错误 details.custom_form_payload_template 复制模板后填字段
bytedcli --trigger-source ai --json --site i18n-tt neptune strict-auth apply \
  --caller-psm example.caller.service \
  --callee-psm example.callee.service \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --custom-form-payloads-json '[{"form_id":1001,"govern_view_code":"sample-domain","callee_list":["example.callee.service"],"fields":{"purpose":"demo workflow"}}]'

# leader review：文本模式会交互选择当前站点的合法 usage scenario
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth apply \
  --caller-psm example.caller.service \
  --callee-psm example.callee.service \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --approval-mode leader_review \
  --leader-confirm
```
