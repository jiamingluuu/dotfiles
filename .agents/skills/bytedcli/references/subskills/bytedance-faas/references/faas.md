# FaaS

FaaS 命令按资源分组为 `function`、`cluster`、`trigger`、`filter-plugin`、`revision`、`template`、`release`、`log`、`instance log`、`invoke`、`remove`。

## 服务与集群创建

CreateService 和 CreateCluster 是两个同步、独立的写操作。命令默认只 dry-run；显式传 `--yes` 才 POST，并在成功后立即 GET 回读。

```bash
# CreateService dry-run / execute
bytedcli --site i18n-tt --vregion Singapore-Central \
  faas function create --payload-file ./faas-service.json
bytedcli --site i18n-tt --vregion Singapore-Central \
  faas function create --payload-file ./faas-service.json --yes

# CreateCluster dry-run / execute
bytedcli --site i18n-tt --vregion Singapore-Central faas cluster create \
  --service-id <service-id> --region sg \
  --payload-file ./faas-cluster.json
bytedcli --site i18n-tt --vregion Singapore-Central faas cluster create \
  --service-id <service-id> --region sg \
  --payload-file ./faas-cluster.json --yes
```

`--vregion Singapore-Central` 控制 ByteCloud 网关路由，`--region sg` 控制 FaaS 资源路径；两者不是同一个值。

底层端点：

- CreateService：`POST /api/v1/faas/v2/services`，响应关键字段 `data.service_id`
- CreateCluster：`POST /api/v1/faas/v2/services/{service_id}/regions/{region}/clusters`，响应关键字段 `data.region` / `data.cluster`

payload 文件必须是 JSON object。CLI 按当前 FaaS 前端生成客户端的字段 allowlist 生成实际 body；被剔除字段出现在 dry-run 的 `request.omitted_fields`。预览和执行回执中的敏感值会替换为 `[REDACTED]`，路径列在 `request.redacted_fields`，实际 POST body 不受影响。`service_id` 和 `region` 属于 cluster API path，不进入 body。

CreateService 的账号字段 wire type 不一致：`admins` / `authorizers` 是英文逗号分隔且不含空格的 string（`"alice,bob"`），`subscribers` 是 string array（`["alice","bob"]`）。CLI 在 dry-run 与执行前都会做本地 preflight 校验。

带 `--yes` 的 CreateService 会在 POST 前以 `search_type=all`、`search_fields=psm`、`skip_test=false` 精确检查 PSM，而不是依赖默认的 subscribe 列表。若存在同名 PSM，命令返回 `FAAS_PSM_CONFLICT` 和现有 `service_id`，不发送 POST；dry-run 保持零网络请求。

不要把两次写入当作事务：服务成功、集群失败时，CLI 返回服务 receipt，不自动回滚或删除服务。写入成功但 GET 回读失败时返回 `verified=false`，应先按返回的 ID 查询，避免重复创建。

## 服务与集群查询

```bash
# 服务列表（支持搜索、分页）
bytedcli faas function list --limit 10 --search "demo" --env prod
bytedcli faas function list --sort-by "-updated_at" --offset 20

# 服务详情
bytedcli faas function get --service-id <service-id>

# 集群列表
bytedcli faas cluster list --service-id <service-id> --limit 20
bytedcli faas cluster list --service-id <service-id> --region cn-north

# 集群详情（含最新发布状态）
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

`faas cluster update` 会读取当前 `format_envs`，合并 `--env`、`--env-from-env` 与 `--unset-env` 后提交集群更新。命令输出只展示 env key 和更新结果，不展示 env value。

运行配置参数：`--request-timeout-seconds`（普通集群 1–900 秒，异步集群 1–10800 秒）、`--initializer-timeout-seconds`（1–900 秒，native runtime 上限 180 秒）、`--max-concurrency`（1–1000，独占/异步模式只允许 1）、`--cpu-milli` 和 `--memory-mb`（正整数）。CPU/内存必须匹配服务端按 runtime/region 返回的可用规格；仅指定其中一个时，另一个保留当前值，非法组合会返回允许的套餐。嵌套资源中的 disk、socket、GPU 等字段保持原值。本命令不调整副本数和伸缩策略。

只要包含运行配置参数，整个更新（含同时指定的 env）默认 dry-run，输出逐字段 `before` / `after` 和 PATCH 预览，显式 `--yes` 才提交。env-only 调用保持直接提交；可加 `--dry-run` 预览。`--dry-run` 与 `--yes` 互斥。env 的前后值及请求体始终脱敏。没有实际变化时不发送 PATCH。

执行后 `outcome=configuration_updated`、`verified=true` 表示 GET 已确认保存的配置，不代表运行实例已完成发布；`release_required` 表示返回了发布单，需根据输出的 ticket ID/URL 检查并推进发布。`unconfirmed` 表示回读失败或不匹配，应先用 `faas cluster get` 和 `faas release status` 核验，避免盲目重试。PATCH 不自动重试。调整请求超时后，也应检查相关超时报警阈值。

`--env-from-env <TARGET_KEY[=SOURCE_ENV]>` 可重复使用；省略 `=SOURCE_ENV` 时，从与 target 同名的进程环境变量读取。CLI 只从 `process.env` 取值，不把 secret value 放入 argv、payload 文件或 stdout/stderr。source 不存在或值为空时会在发起远端请求前报错。每个 target 只能在 `--env` / `--env-from-env` 中设置一次，也不能同时出现在 `--unset-env`。

`faas function list --search-type all` 会跨全部服务（含他人名下与测试服务）查询，后端对该视角要求页大小 `--limit <= 99`；传 `--limit 100` 或更大会被后端以 HTTP 400（`search count cloud not be larger than 100`）拒绝，CLI 在发起请求前即抛 `FAAS_INPUT_ERROR` 并提示改用 `--limit 99` 或更小。默认 `--search-type subscribe` 视角不受此限制。

## 触发器管理

```bash
# 列出触发器
bytedcli faas trigger list --service-id <service-id>

# 查看触发器详情（--id 或 --name 选其一）
bytedcli faas trigger get --service-id <service-id> --id <trigger-id>
bytedcli faas trigger get --service-id <service-id> --name <trigger-name>
bytedcli faas trigger get --service-id <service-id> --trigger-type mqevent --id <trigger-id>

# 创建 timer 触发器
bytedcli faas trigger create --service-id <service-id> --type timer --name demo-timer --cron "*/10 * * * *" --enabled

# 创建 HTTP 触发器
bytedcli faas trigger create --service-id <service-id> --type http --name demo-http --path /api/handler --method POST

# 创建 RocketMQ trigger；--close-multi-env 表示关闭泳道改写，消费原始 topic/group
bytedcli faas trigger create --service-id <service-id> --region <region> --cluster <cluster> --type mqevent --name demo-mq --mq-type rocketmq --mq-region <mq-region> --mq-cluster demo-mq-cluster --topic demo-topic --consumer-group demo-group --sub-expr demo-tag --initial-offset Latest --close-multi-env --disabled

# 更新触发器
bytedcli faas trigger update --service-id <service-id> --trigger-id <id> --trigger-type timer --cron "0 * * * *" --disabled
bytedcli faas trigger update --service-id <service-id> --trigger-id <id> --trigger-type mqevent --mq-type rocketmq --topic demo-topic --consumer-group demo-group --open-multi-env --enabled

# 盘点、重启和调整副本限制
bytedcli faas trigger search --type mq --psm demo.psm --region <region> --topic demo-topic --consumer-group demo-group --mq-cluster demo-mq-cluster --mq-type rocketmq
bytedcli faas trigger execute --action restart --service-id <service-id> --trigger-id <id> --trigger-type mqevent
bytedcli faas trigger replica-limit update --service-id <service-id> --trigger-id <id> --trigger-type mqevent --replica-max-limit '{"default":2}'

# 重置 RocketMQ trigger offset；真实 reset 必须传 --confirm
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

更新 `topic`、`consumer-group`、`mq-cluster`、`sub-expr`、多环境或 Filter Plugin 等需要按 MQ 类型编码的字段时必须显式传 `--mq-type kafka|rocketmq`，避免把 Kafka 配置写入 RocketMQ option。`--close-multi-env`、`--open-multi-env`、`--multi-env-version`、`--enable-multi-tags`、`--orderly` 与 Filter Plugin 字段仅适用于 RocketMQ，更新这些字段时必须传 `--mq-type rocketmq`；和 `--mq-type kafka` 同时使用会直接报错，不会静默丢弃。

Filter Plugin zip 必须保留平台模板目录结构：`filter_plugin/filter.go` 和 `filter_plugin/filter.pb.go`。只把 Go 文件放在 zip 根目录会导致 FaaS trigger 无法正常完成插件发布。`trigger bind-filter-plugin` 在未传 `--filter-source` / `--filter-source-type` 时会从 `filter-plugin list` 自动按 `--plugin-id` 解析。

`trigger reset-offset` 支持 `latest`、`earliest`、`timestamp`、`offset` 四种 reset type；`timestamp` 需要 `--timestamp <epoch_ms>`，`offset` 需要 `--offset <offset>` 或一个/多个 `--queue <queue_id=offset>`。`--offline` 会向 FaaS reset API 发送 `seek_offset=true`。`--dry-run` 在目标解析和只读 Trigger 查询后，仅向 offset 接口发送 `dry_run=true` 校验请求，绝不更新、禁用、恢复或发布 trigger。如果是真实 reset 且目标 trigger 当前为 enabled，命令会先禁用并等到 ready，依次执行 dry-run 校验与真实 reset，再在 reset readback 完成后恢复。禁用 / 恢复只提交 enabled 状态及服务端要求的标识字段，不会重新编码当前 MQ 或 filter plugin 配置。可用 `--no-disable-before-reset` 或 `--no-enable-after-reset` 关闭相应默认行为；`--[no-]preserve-filter-plugin` 仅为命令行兼容保留，不再改变启停请求。

## 报警规则

```bash
# 列出某集群的报警规则（单集群服务可省略 --region / --cluster）
bytedcli faas alarm list --service-id <service-id>
bytedcli faas alarm list --service-id <service-id> --region <region> --cluster <cluster>

# JSON 输出（含 rule_format / threshold / handle_suggestion 等完整字段）
bytedcli --json faas alarm list --service-id <service-id> --region <region> --cluster <cluster>
```

报警规则按集群配置（每集群一组：invoke error / exit / memory / cpu / latency）。
通知接收人不在规则里，由服务 owner / admins / subscribers / authorizers 解析；要改谁收报警，改这些成员字段而不是规则本身。

## 日志查看

```bash
# 最近 10 分钟日志（默认）
bytedcli faas log --service-id <service-id>

# 指定时间范围和类型
bytedcli faas log --service-id <service-id> --since 1h --type stderr

# 按 pod 过滤
bytedcli faas log --service-id <service-id> --pod <pod-name> --limit 100

# JSON 输出
bytedcli --json faas log --service-id <service-id> --since 30m
```

`--since` 支持 `5s`、`2m`、`3h`、`1d` 格式，默认 `10m`。`--type` 可选 `stdout`、`stderr`、`all`（默认 `all`）。

## 单实例 stage 日志

```bash
# 查看 pod 的 initialize 阶段日志
bytedcli faas instance log --service-id <service-id> --region sg --cluster faas-sg --zone my2 --instance-id <pod-name> --revision-id <revision-id> --stage initialize

# 查看 pod 的全部 stage 日志
bytedcli faas instance log --service-id <service-id> --region sg --cluster faas-sg --zone my2 --instance-id <pod-name> --revision-id <revision-id>

# JSON 输出
bytedcli --json faas instance log --service-id <service-id> --region sg --cluster faas-sg --zone my2 --instance-id <pod-name> --revision-id <revision-id>
```

`faas instance log` 直接查询 `/instances/<pod>/stages`，适合排查 `initialize`、`start_container`、`pull_image` 这类 cluster log API 覆盖不到的单实例阶段日志。`--zone` 和 `--revision-id` 都是必填项：前者用于选择正确的 ByteCloud gateway，后者是 FaaS stage API 的必需 query 参数。若只关心单个阶段，传 `--stage <name>` 在客户端过滤，例如 `initialize`。

## 函数调用

```bash
# HTTP 调用（默认 POST）
bytedcli faas invoke --service-id <service-id>
bytedcli faas invoke --service-id <service-id> --data '{"key":"value"}'
bytedcli faas invoke --service-id <service-id> --data-file payload.json --method GET --path /health

# Timer 调用
bytedcli faas invoke --service-id <service-id> --type timer --timer-name demo-timer

# Kafka 调用
bytedcli faas invoke --service-id <service-id> --type kafka --kafka-topic demo-topic --kafka-consumer-group demo-group --data '{"msg":"hello"}'

# RocketMQ 调用
bytedcli faas invoke --service-id <service-id> --type rocketmq --rocketmq-topic demo-topic --rocketmq-consumer-group demo-group

# 显示响应头
bytedcli faas invoke --service-id <service-id> --verbose
```

`--type` 支持：`http`（默认）、`timer`、`kafka`、`rocketmq`、`eventbus`、`tos`。`--timeout` 默认 180 秒。

`--type http` 打的是触发器自己的域名。主 URL 是内网直连域名，非内网环境连不上（表现为卡约 90 秒后
`connect ETIMEDOUT`），此时会自动改用同一触发器的 `secondary_url` 重试。结果里的 `Trigger URL`
是最终真正调用的地址，被跳过的地址列在 `Unreachable` 一行（JSON 模式 `unreachable_trigger_urls`）。
回退只在连接失败时发生，`--timeout` 超时不换地址。其余 `--type` 走 ByteCloud 网关，不受影响。

## 发布管理

```bash
# 创建发布（滚动蓝绿）
bytedcli faas release create --service-id <service-id>
bytedcli faas release create --service-id <service-id> --code-revision 1.0.5 --traffic-ratio 50 --rolling-step 10
bytedcli faas release create --service-id <service-id> \
  --pipeline-template <gray-template-id> --pipeline-type MultiClusterGrayNormalRelease \
  --traffic-ratio 10 --rolling-step 10 \
  --approver <approver-id> --approver-user-type organization_account

# 查看当前发布状态
bytedcli faas release status --service-id <service-id>

# 列出发布历史
bytedcli faas release list --service-id <service-id> --limit 10

# 重试已有工单上唯一可重试的失败步骤；--step-id 仅用于核对该唯一候选
bytedcli faas release retry --service-id <service-id> --ticket-id <ticket-id>
bytedcli faas release retry --service-id <service-id> --ticket-id <ticket-id> --step-id <step-id>

# 预检当前 pending 步骤的 run 动作（默认 dry-run）
bytedcli faas release run-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster>

# 审阅目标 revision / step / 状态后执行一次；也可使用 --yes
bytedcli faas release run-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster> --execute

# 预检 / 确认当前 running 步骤（默认 dry-run）
bytedcli faas release confirm-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster>
bytedcli faas release confirm-step --service-id <service-id> --ticket-id <ticket-id> \
  --step-id <step-id> --region <region> --cluster <cluster> --execute

# 中止发布
bytedcli faas release abort --service-id <service-id>
```

`--traffic-ratio` 指定最大流量百分比（0-100，默认 100）。`--rolling-step` 指定每步流量迁移百分比（默认 10）。CLI 不会推断默认审批人；`--approver` 与 `--approver-user-type` 必须同时提供或同时省略。`release retry` 写前会校验原工单的集群和失败步骤，最多发送一次写请求；结果不明确时仅回查，不自动重复写入。`release run-step` 默认只读预检并输出目标 revision / step / 状态；只有显式 `--execute` 或 `--yes` 才发送一次 `run`。`release confirm-step` 要求 current step 为 `running + allowed_actions=confirm`，并在写后核对相同 target revision 与 exact step 的状态变化。两者都只写一次，无法权威确认时不得盲目重试。

## 代码版本

```bash
# 列出代码版本
bytedcli faas revision list --service-id <service-id> --limit 10

# 查看版本详情
bytedcli faas revision get --service-id <service-id> --revision <rev>

# 下载在线编辑代码 zip（revision=0 表示当前在线编辑代码）
bytedcli faas revision download --service-id <service-id>
bytedcli faas revision download --service-id <service-id> --revision 24 --output source.zip

# 基于已有 revision 克隆并替换 SCM 依赖版本
bytedcli faas revision create --service-id <service-id> \
  --from-revision latest \
  --scm-version example/repo=1.0.0.96

# 预览把已有 online-edit / TOS 函数切换为 SCM-backed revision
bytedcli faas revision scm create --service-id <service-id> \
  --scm-repo example/faas/sample --scm-version 1.0.0.1

# 确认后创建 code revision；不会发布到集群
bytedcli faas revision scm create --service-id <service-id> \
  --scm-repo example/faas/sample --scm-version 1.0.0.1 \
  --from-revision <preview-base-revision> --number <preview-revision-number> --yes
```

`faas revision download` 使用 Web 在线编辑器同源的 legacy `code.zip` 接口；`--revision 0` 表示当前在线编辑代码，指定数字可下载历史函数 revision。
`faas revision create --scm-version <repo=version>` 必须搭配 `--from-revision`，会按 base revision 的 `dependency[].name` 精确匹配 repo 并替换 `version`；找不到匹配项时命令拒绝创建。多个依赖可重复传 `--scm-version`，也可用逗号分隔。
`faas revision scm create` 改变函数自身的部署 source：默认克隆 latest revision，并设置 `source=<scm-repo>:<scm-version>`、`source_type=scm`、`deploy_method=scm`、`dependency=[]`。非空 `run_cmd` 从基线继承，仅在基线为空时补 `/opt/bytefaas/run.sh`，显式 `--run-cmd` 才覆盖。默认只 dry-run 展示完整 POST body，并输出可复制的 `--from-revision <resolved-base> --number <new-revision> --yes`；真实执行缺少任一固定值都会拒绝，确保写入与已审核预览一致。带 `--yes` 只创建 code revision，而且不会启动任何集群发布。执行前若 latest 已匹配目标 SCM 配置，则幂等返回、不重复创建，适合写请求超时后的安全重试。
`faas revision create` 使用 `--from-revision` 且省略 `--number` 时，会把 base revision number 的最后一个数字段加一（例如 `1.0.63` → `1.0.64`）；bootstrap revision `0` 会生成首个合法编号 `1.0.1`。新 revision 编号至少包含三个点分隔数字段；显式 `--number` 仍可覆盖自动推导结果。

### 本地 Go 源码边界

创建服务/集群不会上传代码。现有 `faas revision create` 需要已经存在的构建 source，不能替代本地编译或 `PUT /services/{id}/code` multipart 上传。平台流程还包含 CreateCodeRevision、CreateRevision（cluster revision）和 release；Go online-edit 代码必须先本地编译并打包。官方 client 中的 build API 会返回 Revision，并可从 `build_desc_map[region]` 读取状态；但 bytedcli 尚未对本地 Go 包格式、code upload 返回值与完整链路做 live validation，不要用 raw Go 源 zip 猜测发布链路。

## 函数模板

```bash
# 列出可用模板
bytedcli faas template list
bytedcli faas template list --runtime golang/v1

# 查看模板详情
bytedcli faas template get --name <template-name>
```

## 删除资源

```bash
# 删除集群
bytedcli faas remove cluster --service-id <service-id> --region <region> --cluster <cluster> --force

# 删除服务（须先删除所有集群）
bytedcli faas remove service --service-id <service-id> --force
```

**警告：** 删除操作不可逆。必须传 `--force` 确认。非交互模式下（`--json` 或 pipe）也需要显式传 `--force`。

## 多站点

通过 `--site` 切换（等价于 bytefaas CLI 的 `APP_ENV`）：

| `--site`      | 等价 `APP_ENV` | 说明                                                     |
| ------------- | -------------- | -------------------------------------------------------- |
| `cn`          | `production`   | 中国站（默认）                                           |
| `boe`         | `boe`          | BOE 测试                                                 |
| `sandbox`     | `sandbox`      | BOE sandbox；FaaS 直连 sandbox 控制面，JWT 复用 BOE 凭据 |
| `i18n-bd`     | `i18n`         | ByteIntl                                                 |
| `i18n-tt`     | `i18n`         | TikTok ROW                                               |
| `us-ttp-usts` | `-`            | US-TTP；CLI 自动拆分 limited API 与 Web/JWT 控制面       |
| `eu-ttp`      | `-`            | EU-TTP；CLI 自动使用 EU limited API gateway              |

```bash
bytedcli --site boe faas function list --limit 10
bytedcli --site sandbox faas release create --service-id <service-id>
bytedcli --site i18n-tt faas log --service-id <service-id>
bytedcli --site us-ttp-usts --vregion US-TTP --vdc useast5 \
  faas release status --service-id <service-id> --region us-ttp --cluster <cluster>
bytedcli --site eu-ttp --vregion EU-TTP \
  faas release status --service-id <service-id> --region eu-ttp --cluster <cluster>
```

用户提到“BOE sandbox”“FaaS sandbox 测试环境”或 `faas-sandbox.byted.org` 时，必须选择仅限 `faas` 命令的 `--site sandbox`；不要设置 `BYTEDCLI_CLOUD_SITE=sandbox`，普通 `--site boe` 仍走 BOE 控制面。

## 智能集群解析

单集群服务可省略 `--region` 和 `--cluster`；多集群时必须指定，否则报错并列出可用集群。
