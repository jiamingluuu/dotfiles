---
name: bytedance-neptune
description: "Use bytedcli Neptune for service callers/callees/dependencies, framework/language, deployment sites/zones/clusters, security/ACL, lanes/resources and strict-authorization applications. Query exact governance OpenAPI rules: strict auth/MTLS, timeout/retry/circuit breaker/drop percentage/adaptive breaker, instance/cluster rate limits, redirect, IDC traffic/scheduling, load balancing, preferred address/IP version, stability and dispatch."
---

# bytedcli Neptune

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli --trigger-source ai neptune <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest --trigger-source ai neptune <command> [options]
```

## When to use

- Neptune 平台：安全/稳定性/限流/调度配置排查
- 安全配置按目标选择：caller→callee 授权与 MTLS 规则使用 `strict-auth get` / `mtls get`；服务级严格授权、鉴权与 MTLS 配置使用 `strict-auth service get` / `authen service get` / `mtls service get`。以上查询不代表 product-domain ACL 治理状态或最终访问结果。
- 稳定性配置包括请求超时、请求重试、熔断、比例丢弃和自适应熔断；按具体配置类型选择下列对应查询命令。
- 当前支持查询的调度配置包括流量重定向、机房调度、负载均衡策略和优先地址/IP 版本；按具体配置类型选择下列对应查询命令。
- 跨环境（CN/BOE/ByteIntl）排查配置差异
- 查询服务框架、语言和部署平台：使用 `neptune framework get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询服务部署的区域、集群和部署平台列表：使用 `neptune deploy-unit list`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询单个服务的严格授权、鉴权、MTLS、过载保护或 Archon 框架适用配置：使用对应的 `neptune <resource> service get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 提交严格授权申请（strict authorization / ACL application）：使用 `neptune strict-auth apply`（需按目标控制面指定 `--site`）；命令会按目标 ACL 控制面探测并补齐 extra_info、机房限流 QPS、domain custom form 与 leader review 校验
- 查询精确 caller→callee 访问授权规则：使用 `neptune strict-auth get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee MTLS 流量状态规则：使用 `neptune mtls get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 请求超时规则：使用 `neptune timeout get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 请求重试规则：使用 `neptune retry-config get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 熔断规则：使用 `neptune circ-brkr get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 比例丢弃规则：使用 `neptune drop-pct get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 自适应熔断规则：使用 `neptune adaptive-breaker get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 单实例限流规则：使用 `neptune rate-lmt get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 简单集群限流规则：使用 `neptune cluster-rate-lmt get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 流量重定向规则：使用 `neptune redirect get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 机房调度规则：使用 `neptune idc-traffic get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 负载均衡策略：使用 `neptune lb-policy get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询精确 caller→callee 优先地址/IP 版本规则：使用 `neptune prior-addr get`（支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`）
- 查询泳道组（lane groups）列表
- 查询某个泳道组下的泳道（lanes）
- 查询泳道下的服务列表（list PSM in lane）
- 在指定泳道下新增服务（add PSM to lane）

## 不支持场景反馈

当用户明确要求 Neptune 完成某项操作，但本 Skill 和当前 CLI 没有对应的已支持命令时：

1. 用一句完整的话概括用户希望 Neptune 完成的动作和期望结果。
2. 保留业务对象、动作和必要约束；删除真实 PSM、cluster、URL、ID、用户名、文件路径、token、Cookie 和其他凭据。
3. 不复制用户原始输入，不猜测未来命令名、flag、参数类型或 schema。
4. 把脱敏后的摘要展示给用户，并说明事件还会附带 CLI 版本和 CLI 从本地获取的用户标识；明确询问是否允许上传。未经用户明确同意，不执行反馈命令。
5. 用户明确同意后，每个用户需求只执行一次：

   ```bash
   bytedcli --trigger-source ai neptune feedback send --request "<脱敏后的 Neptune 能力需求摘要>" --yes
   ```

6. 无论反馈是否上报成功，都继续回答用户，明确说明当前不支持的边界；不要把反馈成功描述为需求已经受理或能力已经实现。

鉴权失败、权限不足、网络错误、资源不存在、参数遗漏和后端临时错误属于已有命令的运行故障，不执行 `neptune feedback send`。不要为 feedback 命令自身的失败再次上报 feedback。CLI 会做第二层模式脱敏并拒绝明显凭据，但不能保证识别所有敏感内容；Agent 和用户确认仍是上传前的必要步骤。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`
- 在 TCE、FaaS、PPE 或其他生产网络中调用 Neptune 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`。Neptune 会按当前 site 的生产网路由自动选择 API、Origin 和 ByteCloud JWT host（例如 i18n-tt、eu-ttp）；无需新增 site 或命令参数。

## Agent Guidance

- **Shell 执行前检查：** 逐条检查实际执行的 Neptune 命令，固定使用 `bytedcli --trigger-source ai [全局参数] neptune <command> [options]`。复制用户或 help 的命令时补齐标记，已有 `--trigger-source cli` 改为 `ai`。失败重试、循环、生成后执行的脚本及 Python/Node 子进程中的每次调用都要携带，不能只标记首次调用或外层脚本。参数数组以 `["bytedcli", "--trigger-source", "ai", ...]` 开头；npx 调用将标记放在包名后、`neptune` 前。此要求仅针对 Neptune，不扩展到其他命令域，也不要求用户设置环境变量或修改全局 alias。

- Agent 执行的每条 Neptune 命令都必须在 `neptune` 子命令前传全局参数 `--trigger-source ai`，例如 `bytedcli --trigger-source ai --json neptune ...`。该参数只会在现有 Neptune 业务请求上附加来源元数据，由服务端负责分类和上报；bytedcli 不会单独发送遥测事件或额外请求。不要用 `--json`、TTY 或运行环境猜测来源。直接 CLI 和 bash 脚本调用的优先级为：显式 `--trigger-source` > `BYTEDCLI_NEPTUNE_TRIGGER_SOURCE` > 默认值 `cli`。
- 每次运行 `bytedcli --trigger-source ai neptune ...` 前，先加载并遵守 `references/neptune.md` 中的 **Neptune Request Pacing**。满足该节的执行门槛后再运行命令。
- `neptune framework get` 按 PSM 查询服务框架信息，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`。JSON 只输出 `psm`、`framework`、`language`、`deployment_platform`；后端未提供的可选字段返回 `null`。不支持站点会在认证和请求前失败。
- `neptune deploy-unit list` 按 PSM 查询区域集群列表，支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`。JSON 只输出 `psm` 和 `deploy_units`；每项包含 `zone`、`cluster`、`deployment_platform`，未提供部署平台时返回 `null`。请求只向后端传 `psm`；全局 `--site` 仅用于选择 OpenAPI host 和认证环境。不支持站点会在认证和请求前失败。

以下管理台服务级配置命令均支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`：

六站点路由均受支持。普通未配置会成功返回 `rule.exist=false`、`rule.config=null`；只有后端 category 查询能力不可用时才返回 `NEPTUNE_CATEGORY_UNAVAILABLE`。CLI 不回退到其他管理台配置、站点或旧接口。

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

Archon 是服务框架。后四条命令（访问控制、Token 注入、请求超时、熔断）仅适用于使用 Archon 框架的服务；查询结果不能证明目标是否使用 Archon。所有 `service get` 都接收 `--zone`、`--psm`、`--cluster`；严格授权和服务鉴权还必须提供 `--method`，可传具体方法或字面量 `'*'`。`neptune strict-auth get`、`neptune mtls get`、`neptune timeout get`、`neptune circ-brkr get`（不含 `service`）仍是 caller→callee 五元组命令。

CLI 会始终向查询接口传完整五元组。严格授权、服务鉴权、MTLS、过载保护和 Archon 访问控制按被调服务查询；Archon Token 注入、请求超时和熔断按调用服务查询。五元组中不属于该服务级配置的字段使用字面量 `*`，不会省略或传空字符串。

服务级配置 JSON 保留 `rule.exist`、完整 `rule.config`、`rpc_meta` selector 身份和 `log_id`（LogID）。只有后端明确返回 `exist=false` 且 value 缺失或为 null 时，`rule.config` 才是 null；缺失或畸形数据会作为查询错误返回，不会归一化为 disabled 或“未启用”。CLI 不推断生效/effective 状态、继承、框架身份或 enabled/disabled 状态。

服务过载保护规则已配置时，若后端省略 `cpu_usage_threshold` 或返回 null，`rule.config.cpu_usage_threshold` 按管理台默认值投影为 `80`；后端返回显式值时保持不变。未配置的服务过载保护规则仍返回 `config:null`，其他服务级配置不应用该默认值。

caller→callee 的精确 `get` 命令必须显式提供 `--zone` 和五个 selector：`--caller-psm`、`--caller-cluster`、`--callee-psm`、`--callee-cluster`、`--method`。每次只查一个 category 和一个完整五元组，不接受 `--direction`。使用 `service get` 查询服务级配置时，按上表提供对应服务参数。

字面量 `'*'` 表示该精确存储元组中的值，须加引号避免 shell 展开；它不代表扫描所有规则，也不能代替未知参数。目标信息不足时先补齐查询目标；`caller list` / `callee list` 只返回服务与集群，不提供 method 或规则枚举。

- `neptune strict-auth get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，必须显式提供 zone，并用五个 rpc_meta selector 精确查询一条 `acc_ctrl` 规则。不支持站点会在认证和请求前失败；category 不可用、无精确匹配、重复匹配或关键字段缺失时直接报查询错误，不回退旧命令。JSON 只输出核心规则字段 `exist` 和 `value`。
- `neptune mtls get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，caller、caller cluster 和 method 允许传字面量 `*` 或实际值，并与 callee、callee cluster 一起精确查询一条 `mtls_egress` 规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `enabled`；未配置时为 `exist=false`、`enabled=null`。OpenAPI 响应中的 `inherit`、`editable`、`effective`、`effective_details` 是不可用的默认占位值，不参与解析或验收。
- `neptune timeout get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，caller、caller cluster 和 method 允许传字面量 `*` 或实际值，并与 callee、callee cluster 一起精确查询一条 `timeout` 请求超时规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `timeout_ms`；未配置时为 `exist=false`、`timeout_ms=null`，不把管理台默认值冒充显式规则。
- `neptune retry-config get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `retry_config` 出流量请求重试规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune circ-brkr get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `circ_brkr` 出流量熔断规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune drop-pct get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `drop_pct` 出流量比例丢弃规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune adaptive-breaker get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `adaptive_breaker` 出流量自适应熔断规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune rate-lmt get` 应优先用于精确五元组查询；支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `rate_lmt` 入流量单实例限流规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune cluster-rate-lmt get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `cluster_rate_lmt` 入流量简单集群限流规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune redirect get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `redirect` 出流量重定向规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune idc-traffic get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `idc_traffic` 出流量机房调度规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune lb-policy get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `lb_policy` 出流量负载均衡策略。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。
- `neptune prior-addr get` 支持 `cn`、`boe`、`i18n-tt`、`i18n-bd`、`us-ttp` 和 `eu-ttp`，五个 selector 均允许传字面量 `*` 或实际值，精确查询一条 `prior_addr` 优先地址/IP 版本规则。不支持站点会在认证和请求前失败；查询错误不回退旧命令。JSON 的核心规则字段只有 `exist` 和 `config`；未配置时为 `exist=false`、`config=null`。

## Quick start

```bash
# 发现 Neptune 支持的站点（best-effort）
bytedcli --trigger-source ai neptune list-sites

# 查看某个站点支持的 zones/vregions（best-effort）
bytedcli --trigger-source ai --site cn neptune list-cp-regions
bytedcli --trigger-source ai --site boe neptune list-cp-regions
bytedcli --trigger-source ai --site byteintl neptune list-cp-regions
bytedcli --trigger-source ai --site i18n-tt neptune list-cp-regions

# 查询服务级严格授权配置（显式指定方法；不推断启用、灰度或继承状态）
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth service get --psm example.callee.api --cluster default --zone SGALI --method example.Method

# 查询服务框架、语言和部署平台（支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune framework get --psm example.service

# 查询服务部署的区域、集群和部署平台列表（支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune deploy-unit list --psm example.service

# 查询完整上游服务列表（内部按调用链全分页并按 PSM + cluster 去重）
bytedcli --trigger-source ai --site cn neptune caller list \
  --zone CN --callee-psm example.callee --callee-cluster default

# 查询完整下游服务列表（内部按调用链全分页并按 PSM + cluster 去重）
bytedcli --trigger-source ai --site cn neptune callee list \
  --zone CN --caller-psm example.caller --caller-cluster default

# 查询一条精确 caller→callee 访问授权规则（支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune strict-auth get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method "*"

# 查询一条精确 caller→callee MTLS 流量状态规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune mtls get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster lane-demo \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 请求超时规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune timeout get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster lane-demo \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 请求重试规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune retry-config get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 熔断规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune circ-brkr get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 比例丢弃规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune drop-pct get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 自适应熔断规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune adaptive-breaker get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 单实例限流规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune rate-lmt get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 简单集群限流规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune cluster-rate-lmt get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 流量重定向规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune redirect get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 机房调度规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune idc-traffic get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method GetItem

# 查询一条精确 caller→callee 负载均衡策略（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune lb-policy get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method "*"

# 查询一条精确 caller→callee 优先地址/IP 版本规则（selector 支持 * 或实际值；支持 cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）
bytedcli --trigger-source ai --site cn neptune prior-addr get \
  --zone CN \
  --caller-psm example.caller.api \
  --caller-cluster default \
  --callee-psm example.callee.api \
  --callee-cluster default \
  --method "*"

# 严格授权申请（支持重复或逗号分隔 --method / --zone）
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth apply \
  --caller-psm demo.caller.service \
  --caller-cluster default \
  --callee-psm demo.callee.service \
  --callee-cluster default \
  --method GetProductByID \
  --method MGetProductsByIds \
  --zone SGALI \
  --reason "Need access for demo workflow"

# JSON/agent 场景：后端要求 ACL extra_info 时，显式确认使用默认值，或用 JSON 覆盖字段/机房 QPS
bytedcli --trigger-source ai --json --site i18n-tt neptune strict-auth apply \
  --caller-psm demo.caller.service \
  --caller-cluster default \
  --callee-psm demo.callee.service \
  --callee-cluster default \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --accept-extra-info-defaults

# domain custom form 命中时，用命令错误 details 中的 custom_form_payload_template 补齐 --custom-form-payloads-json
bytedcli --trigger-source ai --json --site i18n-tt neptune strict-auth apply \
  --caller-psm demo.caller.service \
  --callee-psm demo.callee.service \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --custom-form-payloads-json '[{"form_id":1001,"govern_view_code":"sample-domain","callee_list":["demo.callee.service"],"fields":{"purpose":"demo workflow"}}]'

# leader review 文本模式会交互选择 usage scenario，并要求显式确认
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth apply \
  --caller-psm demo.caller.service \
  --callee-psm demo.callee.service \
  --method GetProductByID \
  --zone SGALI \
  --reason "Need access for demo workflow" \
  --approval-mode leader_review \
  --leader-confirm

# 使用完整 payload 申请
bytedcli --trigger-source ai --site i18n-tt neptune strict-auth apply --payload-file /tmp/neptune_strict_auth_payload.json

# 泳道组列表（问：当前有哪些泳道组？）
bytedcli --trigger-source ai neptune lane-group list
bytedcli --trigger-source ai neptune lane-group list --page 2 --page-size 20

# 泳道列表（问：某个泳道组下有哪些泳道？）
bytedcli --trigger-source ai neptune lane list --domain-code demo-domain --zone CN
bytedcli --trigger-source ai neptune lane list --domain-code demo-domain --zone CN --page 2 --page-size 50

# 查询指定泳道下的服务列表（问：某个泳道下有哪些服务？）
bytedcli --trigger-source ai neptune psm list --domain-code demo-domain --lane-name demo-lane-canary
bytedcli --trigger-source ai neptune psm list --domain-code demo-domain --lane-name demo-lane-canary --zone CN --page 1 --page-size 100

# 在指定泳道下新增服务（问：在某个泳道下新增一个服务？）
bytedcli --trigger-source ai neptune psm add --domain-code demo-domain --lane-name demo-lane-canary --zone CN --resource-psm example.resource.service
bytedcli --trigger-source ai neptune psm add --domain-code demo-domain --lane-name demo-lane-canary --zone CN --resource-psm example.resource.service --logic-unit-name default --resource-type tce --operation-type create

# 需要结构化输出时加 --json
bytedcli --trigger-source ai --json neptune lane-group list
bytedcli --trigger-source ai --json neptune lane list --domain-code demo-domain --zone CN
```

## 按问题查询访问控制配置

- 查看服务严格授权配置：`neptune strict-auth service get`，显式提供 zone、psm、cluster 和 method。
- 查看指定 caller→callee 的授权规则：`neptune strict-auth get`，显式提供 zone 和完整五元组。
- 已知服务使用 Archon，且需要查看其访问控制配置：`neptune acc-ctrl service get`。不要将 Archon 配置用于其他框架，也不要通过查询结果推断框架身份。

只有问题涉及多个层面时才分别查询；目标不完整时先补齐，不用 `'*'` 代替未知信息。以上结果不能组合推断 product-domain ACL 的治理状态、治理负责人或匹配规则详情，也不能判断数据面当前生效或 caller→callee 最终 allow/deny。

**站点对照**：

- US-TTP / US-TTP2 → `--site us-ttp`（API 走 `cloud.tiktok-us.net`）
- EU-TTP / EU-TTP2 / USEASTRED → `--site eu-ttp`（API 走 `bc-iedt-gw.tiktok-eu.net`）
- SGALI → `--site i18n-tt`（API 走 `cloud.tiktok-row.net`）
- CN / BOE / ByteIntl → `--site cn|boe|byteintl`

## 查 US-TTP / EU-TTP 合规区配置

US-TTP 和 EU-TTP 是两个独立控制面，跟 CN / BOE / i18n-tt 走的是不同的 API gateway 和 JWT 链路。CLI 已经做了透明封装，**只要选对 `--site`、传对 `--zone`，可使用 `strict-auth service get` 查询服务严格授权配置**。

**`--site` 与 zone 对应关系**：

| 控制面                     | `--site`                   | 可选 zone                        | UI host（浏览器看的）        | API host（CLI 实际打的）   |
| -------------------------- | -------------------------- | -------------------------------- | ---------------------------- | -------------------------- |
| US-TTP（BDEE / USTS 公用） | `us-ttp`                   | `US-TTP`, `US-TTP2`              | `cloud-ttp-us.bytedance.net` | `cloud.tiktok-us.net`      |
| EU-TTP                     | `eu-ttp`                   | `EU-TTP`, `EU-TTP2`, `USEASTRED` | `cloud-eu.tiktok-row.net`    | `bc-iedt-gw.tiktok-eu.net` |
| SGALI                      | `i18n-tt`（不是 `eu-ttp`） | `SGALI`                          | `cloud.tiktok-row.net`       | 同左                       |

**常见姿势**：

```bash
# 查 US-TTP 上某服务的严格授权配置
bytedcli --trigger-source ai --json --site us-ttp neptune strict-auth service get \
  --psm example.service.callee --cluster default \
  --zone US-TTP --method example.GetItem

# 同一个服务在 EU-TTP2 的严格授权配置
bytedcli --trigger-source ai --json --site eu-ttp neptune strict-auth service get \
  --psm example.service.callee --cluster default \
  --zone EU-TTP2 --method example.GetItem
```

**关键易踩的坑**：

- **不要走 `--site i18n-tt --zone US-TTP/EU-TTP` 这条路**。i18n-tt 控制面虽然 `list-cp-regions` 会列出这两个 zone，但拿到的是"远端摘要"，数据跟 US-TTP / EU-TTP 真实控制面**不一致**。要查 US-TTP 必须 `--site us-ttp`，要查 EU-TTP 必须 `--site eu-ttp`。
- US-TTP / EU-TTP 都用 ByteDance SSO 换 JWT（不是 TikTok SSO）。本地 `bytedcli auth login` 登好就行，不需要额外操作；查询命令（strict-auth service get）仅在本机有 SSO 登录态时可用。

## Notes

- 使用全局 `--site` 选择站点（`cn|boe|byteintl|i18n-tt|us-ttp|eu-ttp`，默认 `cn`）。Per-service `--neptune-site` is a hidden alias for backward compatibility.
- 配置查询不解析继承来源，也不能证明数据面当前生效状态或 caller→callee 最终 allow/deny。
- `neptune strict-auth apply` 命令：
  - 结构化参数模式要求 `--caller-psm`、`--callee-psm`、`--reason`、至少一个 `--method`，可选 `--caller-cluster`、`--callee-cluster`、`--zone`、`--reviewer`、`--viewer`
  - `--method` 和 `--zone` 支持重复传入或逗号分隔；payload 中会写入 `zones: string[]`
  - 仅 `cn` 站点：申请区域命中 `China-North`（中国北部）、`China-North6`（中国北部6）、`China-East`（中国东部）但未覆盖全部三者时，TTY 会提示三地 ACL 应保持一致并要求 `y/yes`；JSON 或非交互模式确认申请范围后必须传 `--confirm-acl-coverage`
  - 如平台字段超出 CLI flags，使用 `--payload-json` 或 `--payload-file` 传完整 strict authorization payload；raw payload 模式不要混用结构化 flags
- `--page` 和 `--page-size` 用于分页（`--page-count` 和 `--page-num` 是隐藏的兼容别名）
- `neptune lane list` 命令：
  - `--domain-code`: 域名代码（必填）
  - `--group-code`: 组代码（可选，默认同 domain-code）
  - `--zone`: 区域（可选；默认值按站点推导：`CN(cn/byteintl)`、`BOE(boe)`、`SGALI(i18n-tt)`、`US-TTP(us-ttp)`、`EU-TTP(eu-ttp)`）
  - `--lane-name`: 泳道名称过滤（可选）
  - `--logic-unit-name`: 逻辑单元名称（可选，默认 "default"）
  - `--psm`: PSM 过滤（可选）
- `neptune psm add` 命令：
  - `--domain-code`: 域名代码（必填）
  - `--lane-name`: 泳道名称（必填）
  - `--zone`: 区域（可选，默认：CN 适用于 cn/byteintl，BOE 适用于 boe，SGALI 适用于 i18n-tt，US-TTP 适用于 us-ttp，EU-TTP 适用于 eu-ttp）
  - `--resource-psm`: 服务 PSM（必填）
  - `--logic-unit-name`: 逻辑单元名称（可选，默认 "default"）
  - `--resource-type`: 资源类型（可选，默认 "tce"）
  - `--is-sub-lane`: 是否为子泳道（可选，默认 false）
  - `--operation-type`: 操作类型（可选，默认 "create"）
- `neptune psm list` 命令：
  - `--domain-code`: 域名代码（必填）
  - `--lane-name`: 泳道名称（必填）
  - `--zone`: 区域（可选，默认：CN 适用于 cn/byteintl，BOE 适用于 boe，SGALI 适用于 i18n-tt，US-TTP 适用于 us-ttp，EU-TTP 适用于 eu-ttp）
  - `--logic-unit-name`: 逻辑单元名称（可选，默认 "default"）
  - `--page`: 页码（可选，默认 1）
  - `--page-size`: 每页数量（可选，默认 100）

## References

- `references/neptune.md`
