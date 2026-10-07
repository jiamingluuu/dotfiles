---
name: bytedance-faas
description: "Manage ByteCloud FaaS (Serverless) functions via bytedcli: safely create services and clusters from payload files; list/get services, clusters, triggers, filter plugins, revisions, templates; create SCM-backed revisions for existing functions; update cluster runtime configuration (timeouts, concurrency, CPU/memory) with a dry-run diff and explicit confirmation; update cluster env vars, including secret-safe process env input; view cluster logs and per-instance stage logs; download revision source zips; invoke functions; create/abort releases, including BOE sandbox releases; create/update/delete triggers and filter plugins; reset MQ trigger offsets; remove services and clusters. Use when tasks mention FaaS, Serverless, cloud functions, ByteFaaS, BOE sandbox functions, function runtime configuration, request/initialization timeouts, concurrency, CPU/memory, function env, function triggers, trigger filter plugins, function deployment, function source, SCM deployment mode, or function logs."
---

# bytedcli FaaS

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 查询 FaaS 服务列表、详情、集群、触发器、代码版本、函数模板
- 从完整 JSON payload 安全创建 FaaS 服务和集群（默认 dry-run，`--yes` 才写入）
- 查看函数运行日志（支持实时流）
- 查看单实例 stage 日志，排查 cluster log API 看不到的 pod 初始化 / 启动问题
- 更新集群运行配置（超时、并发、CPU/内存，默认预览）与环境变量
- 调用函数（HTTP / Timer / Kafka / RocketMQ / EventBus / TOS）
- 创建发布（滚动蓝绿部署）、查看发布状态、中止发布
- 在 BOE sandbox 测试控制面查询和发布函数
- 创建 / 更新 / 删除触发器（timer、http、kafka 等）
- 重置 RocketMQ trigger consumer offset（支持 latest / earliest / timestamp / offset）
- 下载 / 上传 / 更新 / 删除 trigger filter plugin，并绑定到 RocketMQ trigger
- 下载在线编辑代码版本的源码 zip
- 将已有 online-edit / TOS 函数切换为 SCM-backed code revision（默认 dry-run）
- 删除服务或集群

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

### 创建服务与首个集群

服务和集群是两个独立资源。先 dry-run 服务请求，确认后加 `--yes`；拿到返回的 `service_id` 后，再用同样方式创建集群。CLI 不会在集群创建失败时删除已成功创建的服务。

```bash
# 1. 预览 / 创建服务
bytedcli --site i18n-tt --vregion Singapore-Central \
  faas function create --payload-file ./faas-service.json
bytedcli --site i18n-tt --vregion Singapore-Central \
  faas function create --payload-file ./faas-service.json --yes

# 2. 预览 / 创建 Singapore-Central 的 FaaS sg 集群
bytedcli --site i18n-tt --vregion Singapore-Central faas cluster create \
  --service-id <service-id> \
  --region sg \
  --payload-file ./faas-cluster.json
bytedcli --site i18n-tt --vregion Singapore-Central faas cluster create \
  --service-id <service-id> \
  --region sg \
  --payload-file ./faas-cluster.json \
  --yes
```

`--vregion Singapore-Central` 是 ByteCloud 网关路由；`--region sg` 是 FaaS 资源路径中的逻辑 region。两者不能互换。

payload 文件应来自当前 CreateService / CreateCluster 请求或按同一 API schema 生成。CLI 会按当前前端 API allowlist 投影实际发送的 body，并在 dry-run 的 `omitted_fields` 中列出 `create_method`、`region_type`、`service_id`、`region` 等 UI/path 字段；输出中的敏感值会替换为 `[REDACTED]`，对应路径列在 `redacted_fields`，实际 POST body 不受影响。必须先检查 `request.body` 再执行。

CreateService 中 `admins` / `authorizers` 是英文逗号分隔的字符串（例如 `"alice,bob"`），`subscribers` 才是 JSON string array。CLI 会在 dry-run 阶段校验这些 wire types，不会把错误类型发到后端。

带 `--yes` 的 CreateService 在 POST 前会用 `search_type=all`（不是默认的订阅视角）按 PSM 精确查询全部服务，并包含测试服务。若 PSM 已存在，命令返回 `FAAS_PSM_CONFLICT` 和现有 `service_id`，不会发送 POST；先用 `bytedcli faas function get --service-id <service-id>` 检查现有服务。dry-run 不执行远端查询。

写入后会立即 GET 回读。若 POST 已成功但回读失败，结果保留 `service_id` 或 `region`/`cluster`，并标记 `verified=false`；不要盲目重试 create，应先用 `bytedcli faas function get` / `bytedcli faas cluster get` 确认。

### 查询服务与集群

```bash
# 列出 FaaS 服务
bytedcli faas function list --limit 10
bytedcli faas function list --search "demo-service" --limit 20

# 查看服务详情
bytedcli faas function get --service-id <service-id>

# 列出集群
bytedcli faas cluster list --service-id <service-id>

# 查看集群详情（单集群服务可省略 --region / --cluster）
bytedcli faas cluster get --service-id <service-id> --region <region> --cluster <cluster>

# 预览运行配置的逐字段 before/after；未指定的字段保持原值
bytedcli faas cluster update --service-id <service-id> --region <region> --cluster <cluster> --request-timeout-seconds 900
bytedcli faas cluster update --service-id <service-id> --region <region> --cluster <cluster> --initializer-timeout-seconds 120 --max-concurrency 100 --cpu-milli 1000 --memory-mb 2048

# 核对预览后提交一次；回执区分配置回读成功与待处理发布单
bytedcli faas cluster update --service-id <service-id> --region <region> --cluster <cluster> --request-timeout-seconds 900 --yes

# 更新集群环境变量（单集群服务可省略 --region / --cluster）
bytedcli faas cluster update --service-id <service-id> --env FEATURE_FLAG=true
bytedcli faas cluster update --service-id <service-id> --region <region> --cluster <cluster> --env KEY=value --unset-env OLD_KEY

# 从当前进程环境变量安全读取 secret；不把 value 放入 argv
bytedcli faas cluster update --service-id <service-id> --env-from-env ADMIN_TOKEN
bytedcli faas cluster update --service-id <service-id> --env-from-env ADMIN_TOKEN=DEPLOY_ADMIN_TOKEN
```

`faas cluster get` 会回读实例 CPU/内存/磁盘、单实例最大并发、请求与初始化超时、终止宽限、
扩缩容开关和各机房实例数区间，可用于确认配置已经随最新发布生效；不要只以页面“有更新”或
服务 `deployed` 作为资源变更完成证据。

`faas cluster update` 会读取当前 `format_envs` 后合并变更，再提交集群更新；输出只展示更新结果和 env key 名，不展示 env value。

`faas function list` 加 `--search-type all`（跨全部服务、含他人名下与测试服务）时，后端要求页大小 `--limit <= 99`；传 `--limit 100` 或更大会被后端以 HTTP 400 拒绝，CLI 会在发起请求前抛 `FAAS_INPUT_ERROR` 并提示改用 `--limit 99` 或更小。默认 `--search-type subscribe` 视角不受此限制，可用更大的 `--limit`。

运行配置参数：`--request-timeout-seconds`（普通集群 1–900 秒，异步集群 1–10800 秒）、`--initializer-timeout-seconds`（1–900 秒，native runtime 上限 180 秒）、`--max-concurrency`（1–1000，独占/异步模式只允许 1）、`--cpu-milli` 和 `--memory-mb`（正整数）。CPU/内存必须匹配服务端按 runtime/region 返回的可用规格；仅指定其中一个时，另一个保留当前值，非法组合会返回允许的套餐。嵌套资源中的 disk、socket、GPU 等字段保持原值。本命令不调整副本数和伸缩策略。

只要包含运行配置参数，整个更新（含同时指定的 env）默认 dry-run，输出逐字段 `before` / `after` 和 PATCH 预览，显式 `--yes` 才提交。env-only 调用保持直接提交；可加 `--dry-run` 预览。`--dry-run` 与 `--yes` 互斥。env 的前后值及请求体始终脱敏。没有实际变化时不发送 PATCH。

执行后 `outcome=configuration_updated`、`verified=true` 表示 GET 已确认保存的配置，不代表运行实例已完成发布；`release_required` 表示返回了发布单，需根据输出的 ticket ID/URL 检查并推进发布。`unconfirmed` 表示回读失败或不匹配，应先用 `faas cluster get` 和 `faas release status` 核验，避免盲目重试。PATCH 不自动重试。调整请求超时后，也应检查相关超时报警阈值。

`--env-from-env <TARGET_KEY[=SOURCE_ENV]>` 可重复使用；省略 `=SOURCE_ENV` 时，从与 target 同名的进程环境变量读取。CLI 只从 `process.env` 取值，不把 secret value 放入 argv、payload 文件或 stdout/stderr。source 不存在或值为空时会在发起远端请求前报错。每个 target 只能在 `--env` / `--env-from-env` 中设置一次，也不能同时出现在 `--unset-env`。

### 服务成员管理

告警接收人按服务成员（owner / admins / authorizers / subscribers）解析。owner、admins、authorizers 用 `update` 整列设置；`remove-member` 只从 admins / authorizers 中删除指定用户，避免手工传全量列表时误删其他成员。subscribers 是“当前用户订阅”，只能本人 `subscribe` / `unsubscribe`，无法替他人增删。

```bash
# 整列设置 owner / admins / authorizers（传入的列表会整体覆盖原值）
bytedcli faas function update --service-id <service-id> --owner alice --admins alice,bob --authorizers alice

# 只从 admins / authorizers 中移除指定用户（保留其余成员不变）
bytedcli faas function remove-member --service-id <service-id> --admins bob
bytedcli faas function remove-member --service-id <service-id> --authorizers bob,carol

# 当前用户订阅 / 取消订阅服务告警通知
bytedcli faas function subscribe --service-id <service-id>
bytedcli faas function unsubscribe --service-id <service-id>
```

### 触发器

```bash
# 列出触发器
bytedcli faas trigger list --service-id <service-id>

# 查看触发器详情
bytedcli faas trigger get --service-id <service-id> --id <trigger-id>
bytedcli faas trigger get --service-id <service-id> --trigger-type mqevent --id <trigger-id>

# 创建 timer 触发器
bytedcli faas trigger create --service-id <service-id> --type timer --name demo-timer --cron "*/10 * * * *" --enabled

# 创建 RocketMQ trigger；--close-multi-env 表示关闭泳道改写，消费原始 topic/group
bytedcli faas trigger create --service-id <service-id> --region <region> --cluster <cluster> --type mqevent --name demo-mq --mq-type rocketmq --mq-region <mq-region> --mq-cluster demo-mq-cluster --topic demo-topic --consumer-group demo-group --sub-expr demo-tag --initial-offset Latest --request-timeout-ms 3600000 --close-multi-env --disabled

# 更新触发器
bytedcli faas trigger update --service-id <service-id> --trigger-id <id> --trigger-type timer --cron "0 * * * *"
bytedcli faas trigger update --service-id <service-id> --trigger-id <id> --trigger-type mqevent --mq-type rocketmq --topic demo-topic --consumer-group demo-group --request-timeout-ms 3600000 --open-multi-env --enabled

# 盘点、重启和调整副本限制
bytedcli faas trigger search --type mq --psm demo.psm --region <region> --topic demo-topic --consumer-group demo-group --mq-cluster demo-mq-cluster --mq-type rocketmq
bytedcli faas trigger execute --action restart --service-id <service-id> --trigger-id <id> --trigger-type mqevent
bytedcli faas trigger replica-limit update --service-id <service-id> --trigger-id <id> --trigger-type mqevent --replica-max-limit '{"default":2}'

# 重置 RocketMQ trigger offset；--dry-run 只校验且绝不改变 trigger 状态；真实 reset 必须传 --confirm，enabled trigger 会自动先禁用并在结束后恢复
bytedcli faas trigger reset-offset --service-id <service-id> --region <region> --cluster <cluster> --trigger-type mqevent --trigger-id <id> --reset-type latest --offline --confirm
bytedcli faas trigger reset-offset --service-id <service-id> --trigger-type mqevent --trigger-id <id> --reset-type timestamp --timestamp 1760000000000 --dry-run
bytedcli faas trigger reset-offset --service-id <service-id> --trigger-type mqevent --trigger-id <id> --reset-type offset --queue 0=12345 --confirm

# Filter Plugin：模板下载、上传和绑定
bytedcli faas filter-plugin template download --service-id <service-id> --output default-filter-plugin.zip
bytedcli faas filter-plugin create --service-id <service-id> --name demo-filter --zip-file demo-filter-plugin.zip
bytedcli faas filter-plugin update --service-id <service-id> --plugin-id <plugin-id> --name demo-filter --zip-file demo-filter-plugin.zip
bytedcli faas filter-plugin list --service-id <service-id>
bytedcli faas filter-plugin delete --service-id <service-id> --plugin-id <plugin-id> --force
bytedcli faas trigger bind-filter-plugin --service-id <service-id> --trigger-id <id> --trigger-type mqevent --plugin-id <plugin-id>

# 删除触发器（需 --force）
bytedcli faas trigger delete --service-id <service-id> --trigger-id <id> --trigger-type timer --force
```

`--request-timeout-ms` 对应 MQ trigger 顶层 `request_timeout` 字段，单位是毫秒；它与 CLI 等待回读使用的 `--wait-timeout-ms` 不是同一个超时。长视频等异步消费者应按单条消息最坏处理时长预留 buffer，并在更新后通过 trigger 回读确认生效。

Filter Plugin zip 必须保留平台模板目录结构：`filter_plugin/filter.go` 和 `filter_plugin/filter.pb.go`。只把 Go 文件放在 zip 根目录会导致 FaaS trigger 无法正常完成插件发布。

### 报警规则

```bash
# 列出某集群的报警规则（单集群服务可省略 --region / --cluster）
bytedcli faas alarm list --service-id <service-id>
bytedcli faas alarm list --service-id <service-id> --region <region> --cluster <cluster>
```

报警规则按集群维度配置（每个集群一组：invoke error / exit / memory / cpu / latency）。
通知接收人不存储在规则上，由服务的 owner / admins / subscribers / authorizers 解析；
要调整谁收到报警，改这些成员字段（见 `faas function update` / `faas function subscribe`），而不是改报警规则。

### 查看日志

```bash
# 查看最近 10 分钟日志
bytedcli faas log --service-id <service-id>

# 查看最近 1 小时的 stderr 日志
bytedcli faas log --service-id <service-id> --since 1h --type stderr

# 按 pod 过滤
bytedcli faas log --service-id <service-id> --pod <pod-name> --limit 100
```

`-f/--follow` 只是把 `follow=true` 透传给日志查询接口，单次拉取当前窗口，不是流式跟随；持续跟踪日志需自行循环调用。

### 查看单实例 stage 日志

当 `faas log` 拿不到 pod 初始化、拉镜像、启动容器等阶段日志时，改用实例级 stage 日志接口：

```bash
# 查看某个 pod 的 initialize 阶段日志
bytedcli faas instance log \
  --service-id <service-id> \
  --region sg \
  --cluster faas-sg \
  --zone my2 \
  --instance-id <pod-name> \
  --revision-id <revision-id> \
  --stage initialize

# 查看该 pod 的全部 stage
bytedcli faas instance log \
  --service-id <service-id> \
  --region sg \
  --cluster faas-sg \
  --zone my2 \
  --instance-id <pod-name> \
  --revision-id <revision-id>
```

`faas log` 走 cluster log API，适合查运行期 stdout/stderr；`faas instance log` 走实例 `stages` API，适合查 `initialize`、`start_container`、`pull_image` 等单 pod 生命周期日志。`--zone` 必填，因为它决定使用哪个 ByteCloud gateway；`--revision-id` 必填，因为实例 stage API 需要该参数定位目标 revision。

### 调用函数

```bash
# HTTP 调用
bytedcli faas invoke --service-id <service-id>
bytedcli faas invoke --service-id <service-id> --data '{"key":"value"}' --method POST

# Timer 调用
bytedcli faas invoke --service-id <service-id> --type timer --timer-name demo-timer --data '{}'

# Kafka 调用
bytedcli faas invoke --service-id <service-id> --type kafka --kafka-topic demo-topic --kafka-consumer-group demo-group --data '{"msg":"hello"}'
```

`--type http` 打的是触发器自己的域名，其中主 URL 是内网直连域名（`10.x` / IPv6 ULA），非内网环境
连不上，症状是卡约 90 秒后 `connect ETIMEDOUT`、且重试时目标 IP 每次不同。这种情况下 `invoke` 会
自动改用同一触发器的 `secondary_url` 重试：结果里的 `Trigger URL` 是最终真正调用的地址，被跳过的
地址列在 `Unreachable` 一行（JSON 模式为 `unreachable_trigger_urls`）。判断是不是这个问题：同一台
机器上 `faas function get` / `trigger list` 等查询命令能通（走 ByteCloud 网关），只有 `invoke` 超时。
回退只在连接失败时触发，`--timeout` 超时不会换地址；两个地址都不可达时可用 `--http-proxy` /
`--socks5-proxy` 指定能路由到内网的代理。其余 `--type` 走 ByteCloud 网关，不受影响。

### 发布管理（工单制）

`faas release create` 现在会提交一个发布工单（`tickets/release_clusters`），
由 FaaS 平台异步编排灰度发布。工单信息（ticket id / ticket url）会在结果中返回。

```bash
# 创建工单，使用最新 code revision（默认）
bytedcli faas release create --service-id <service-id>

# 指定 code revision id
bytedcli faas release create --service-id <service-id> --code-revision <rev-id>

# 指定 rolling-step / min-ready-percentage / traffic-ratio
bytedcli faas release create --service-id <service-id> \
  --rolling-step 20 --min-ready-percentage 95 --traffic-ratio 100

# 指定 pipeline-template（平台/服务特定，可从 Web 界面获取）
bytedcli faas release create --service-id <service-id> --pipeline-template <template-id>

# 显式指定灰度模板和审批人；审批人 id 与类型必须同时传入
bytedcli faas release create --service-id <service-id> \
  --pipeline-template <gray-template-id> --pipeline-type MultiClusterGrayNormalRelease \
  --traffic-ratio 10 --rolling-step 10 \
  --approver <approver-id> --approver-user-type organization_account

# 查看最近发布
bytedcli faas release status --service-id <service-id>

# 列出发布历史
bytedcli faas release list --service-id <service-id>

# 重试已有工单上唯一可重试的失败步骤；--step-id 仅用于核对该唯一候选
bytedcli faas release retry --service-id <service-id> --ticket-id <ticket-id>
bytedcli faas release retry --service-id <service-id> --ticket-id <ticket-id> --step-id <step-id>

# 预检并预览当前 pending 步骤的 run 动作（默认 dry-run，不写入）
bytedcli faas release run-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster>

# 确认目标 revision / step / 状态后执行一次；--yes 等价于 --execute
bytedcli faas release run-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster> --execute

# 预检 / 确认当前 running 步骤；默认 dry-run，执行时显式加 --execute 或 --yes
bytedcli faas release confirm-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster>
bytedcli faas release confirm-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster> --execute

# 中止发布
bytedcli faas release abort --service-id <service-id>
```

默认参数：`--rolling-step=10`、`--min-ready-percentage=90`、`--rolling-interval=0`、
`--traffic-ratio=100`。
CLI 不会推断默认审批人；`--approver` 与 `--approver-user-type` 必须同时提供或同时省略。
`release retry` 会先读取原工单并严格校验集群、失败状态和 `retry` 动作，只发送一次写请求；
写结果不明确时仅回查原工单，不会自动重复写入。
`release run-step` 默认只读预检：严格核对 service、单一 cluster、running ticket/pipeline、
唯一 current step，以及 `pending + allowed_actions=run`，并输出目标 revision。只有显式传入
`--execute` 或 `--yes` 才发送一次写请求；随后回读工单，超时或未确认时禁止盲目重试。
`release confirm-step` 使用同样的保护，但要求 current step 为
`running + allowed_actions=confirm`；回读时还会核对原 target revision 与 exact step 的状态变化。

### 代码版本

```bash
# 列出代码版本
bytedcli faas revision list --service-id <service-id>

# 查看版本详情
bytedcli faas revision get --service-id <service-id> --revision <rev>

# 下载在线编辑代码 zip（revision=0 表示当前在线编辑代码）
bytedcli faas revision download --service-id <service-id>
bytedcli faas revision download --service-id <service-id> --revision 24 --output source.zip

# 基于最新版本创建一个新版本（克隆字段，仅覆盖指定字段）
bytedcli faas revision create --service-id <service-id> \
  --from-revision latest \
  --source faas/example:demo:1.0.0.95 --description "release 1.0.0.95"

# 基于最新版本创建一个新版本，并把指定 SCM 依赖切到新版本
bytedcli faas revision create --service-id <service-id> \
  --from-revision latest --number 1.0.66 \
  --scm-version example/repo=1.0.0.96 --description "release example/repo 1.0.0.96"

# 预览把已有 online-edit / TOS 函数切换为 SCM-backed revision
bytedcli faas revision scm create --service-id <service-id> \
  --scm-repo example/faas/sample --scm-version 1.0.0.1

# 确认请求体后创建 revision；该命令不会发布到集群
bytedcli faas revision scm create --service-id <service-id> \
  --scm-repo example/faas/sample --scm-version 1.0.0.1 \
  --from-revision <preview-base-revision> --number <preview-revision-number> --yes
```

`--scm-version <repo=version>` 必须和 `--from-revision` 一起使用；CLI 会读取 base revision 的 `dependency[]`，按 `dependency[].name` 精确匹配 repo 并只替换对应 `version`。找不到匹配 repo 时会拒绝创建，避免生成仍指向旧 SCM 包的 revision。多个依赖可重复传 `--scm-version`，也可用逗号分隔。

`faas revision scm create` 用于改变函数自身的部署 source，不是修改已有 SCM dependency。它默认克隆 latest revision，并固定设置 `source=<scm-repo>:<scm-version>`、`source_type=scm`、`deploy_method=scm`、`dependency=[]`；非空 `run_cmd` 从基线继承，仅在基线为空时补 `/opt/bytefaas/run.sh`，显式 `--run-cmd` 才覆盖。不带 `--yes` 时只展示完整 POST body，并输出可复制的 `--from-revision <resolved-base> --number <new-revision> --yes`，不写入；真实执行缺少任一固定值都会拒绝，确保写入与已审核预览一致。带 `--yes` 只创建 code revision，不会发布到任何集群。执行前若 latest 已匹配目标 SCM 配置，则幂等返回、不重复创建，适合写请求超时后的安全重试。

使用 `--from-revision` 且省略 `--number` 时，CLI 会把 base revision number 的最后一个数字段加一（例如 `1.0.63` → `1.0.64`）；bootstrap revision `0` 会生成首个合法编号 `1.0.1`。新 revision 编号至少包含三个点分隔数字段。只有需要指定其他版本号时才显式传 `--number`。

`faas function create` / `faas cluster create` 只创建控制面资源，不上传或编译本地源码。`faas revision create` 也只为已有的 `source`（TOS 路径、镜像等）创建 code revision 快照。对于本地 Go FaaS 插件，不能把 raw Go 源码 zip 当作已构建产物上传；当前 bytedcli 尚未覆盖经过端到端实测的本地 Go 编译 + `/services/{id}/code` 上传 + code/cluster revision build 全链路。官方 client 已定义 build 端点及 `build_desc_map` 状态字段，但本地 Go 包格式、上传响应与整体状态转移仍需 live validation。该步骤继续使用 ByteFaaS CLI 的本地构建工作流。

### 函数模板

```bash
# 列出可用模板
bytedcli faas template list
bytedcli faas template list --runtime golang/v1

# 查看模板详情
bytedcli faas template get --name <template-name>
```

### 删除资源

```bash
# 删除集群（需 --force）
bytedcli faas remove cluster --service-id <service-id> --region <region> --cluster <cluster> --force

# 删除服务（需 --force，且须先删除所有集群）
bytedcli faas remove service --service-id <service-id> --force
```

## 多站点支持

FaaS 通过 `--site` 切换环境（替代 bytefaas CLI 的 `APP_ENV`）：

当用户提到“BOE sandbox”“FaaS sandbox 测试环境”或 `faas-sandbox.byted.org` 时，使用仅限 `faas` 命令的 `--site sandbox`，不要使用普通的 `--site boe`，也不要设置 `BYTEDCLI_CLOUD_SITE=sandbox`。该选项会把 FaaS v2 请求直连 `https://faas-sandbox.byted.org/v2`，JWT 自动复用 BOE 站点凭据。

```bash
# 中国站（默认）
bytedcli faas function list --limit 10

# BOE 环境
bytedcli --site boe faas function list --limit 10

# BOE sandbox 测试环境：直连 sandbox 控制面，并复用 BOE JWT
bytedcli --site sandbox faas function list --limit 10
bytedcli --site sandbox faas release create --service-id <service-id>

# TikTok ROW (i18n-tt)
bytedcli --site i18n-tt faas function list --limit 10

# ByteIntl (i18n-bd)
bytedcli --site i18n-bd faas function list --limit 10

# US-TTP：API、Web/JWT 控制面由 CLI 自动拆分
bytedcli --site us-ttp-usts --vregion US-TTP --vdc useast5 \
  faas release status --service-id <service-id> --region us-ttp --cluster <cluster>

# EU-TTP：CLI 自动使用 EU limited API gateway
bytedcli --site eu-ttp --vregion EU-TTP \
  faas release status --service-id <service-id> --region eu-ttp --cluster <cluster>
```

## 智能集群解析

当目标服务只有一个集群时，`--region` 和 `--cluster` 可以省略，bytedcli 会自动解析。

```bash
# 服务只有一个集群时，以下两种写法等效：
bytedcli faas trigger list --service-id <service-id>
bytedcli faas trigger list --service-id <service-id> --region cn-north --cluster default
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前）
- `--service-id` 是大多数命令的必填参数
- `faas revision download` 使用 Web 在线编辑器同源的 legacy `code.zip` 接口；`--revision 0` 表示当前在线编辑代码，指定数字可下载历史函数 revision。
- 删除操作（`remove service`、`remove cluster`、`trigger delete`）需要 `--force` 确认
- `faas log` 别名 `faas logs`；`faas remove` 别名 `faas rm`
- `trigger get` / `revision get` / `template get` 均有 `view` 别名

## References

- `references/faas.md`
