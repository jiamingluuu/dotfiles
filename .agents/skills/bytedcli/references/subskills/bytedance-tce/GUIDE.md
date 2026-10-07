---
name: bytedance-tce
description: "Operate TCE via bytedcli: list/search/get/create/update/delete services, list/create/update/scale/reset clusters, list/search instances, migrate instances via instance delete, force-delete instances, and download allowed CN instance files (logs/core), list/get/cancel/action deployments, env cascader, deploy lane. Use when tasks mention TCE services, clusters, deployments, environment queries, or downloading files/logs/core from a TCE instance."
---

# bytedcli TCE

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

- 服务列表/搜索/详情/创建/更新/删除
- 集群信息查询/创建/更新/扩缩容/删除/滚动重启
- 实例列表/搜索/迁移（`instance delete`）/强制删除（`instance force-delete`）
- CN 实例文件下载（日志、core 等 TCE 允许目录）
- 发布工单查询与操作（列表/详情/取消/工单级 action/步骤级 action）
- 环境级联查询
- 泳道部署

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `tce service`, `tce cluster`, `tce instance`, and `tce deployment`. Old flat names (e.g. `tce list-starred-service`, `tce search-service`, `tce get-service`, `tce list-service-clusters`, `tce list-instance`, `tce list-deployment`, `tce get-deployment`) still work as hidden aliases.

> 在 ByteDance 生产网络内使用 `--site i18n-tt` 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`，TCE OpenAPI 与 ByteCloud JWT host 会自动切到生产网可达的 `cloud-i18n.bytedance.net`。

```bash
# 列出支持的站点
bytedcli tce list-sites

# 列出我订阅/收藏的服务（默认；加 --recent 可改列最近访问的服务）
bytedcli tce service list --page 1 --page-size 10

# 搜索服务
bytedcli tce service search --keyword "keyword" --env "ppe_xxx" --page 1 --page-size 10

# 获取服务详情（也支持 --psm + 可选 --env）
bytedcli --site cn tce service get <service_id>
bytedcli --site cn tce service get --psm example.service.api --env prod

# 查询 PSM 运行时治理状态（对应控制台微服务治理状态，如 running / stopped）
bytedcli tce service governance get --psm example.service.api

# 查询服务健康档案（健康分、各维度得分与风险项计数；需要数字 service id）
bytedcli tce service health get --service-id 123456

# 列出服务集群（支持 --service-id 或 --psm）
bytedcli --site cn tce cluster list --service-id <service_id> --page 1 --page-size 10
bytedcli --site cn tce cluster list --psm example.service.api --env prod --page 1 --page-size 10
bytedcli --site boe tce cluster list --service-id 234558 --cluster-name tls_mix_proxy_boe --page 1 --page-size 10
# 其它命令里 <cluster_id> 的取值就是本命令返回的 data.clusters[].meta.id

# 创建/更新/删除服务（默认必须先 dry-run，真实提交加 --yes）
bytedcli tce service create --service-info-file service-info.json --dry-run
bytedcli tce service create --service-info-file service-info.json --yes
bytedcli tce service update --service-id <service_id> --update-info-file update-info.json --dry-run
bytedcli tce service delete --service-id <service_id> --dry-run

# 查询和校验服务可用 SCM 包
bytedcli tce service repo-info-list --service-id <service_id>
bytedcli tce service check-repos --service-id <service_id> --request-file check-repos.json --dry-run
bytedcli tce service check-repos --psm example.service.api --env prod --request-file check-repos.json --dry-run

# 创建/删除集群（cluster_info 建议来自平台推荐模板或控制台导出的 payload）
bytedcli tce cluster create --service-id <service_id> --cluster-info-file cluster-info.json --dry-run
bytedcli tce cluster create --service-id <service_id> --cluster-info-file cluster-info.json --yes
bytedcli tce cluster reset --service-id <service_id> --cluster-id <cluster_id> --dry-run
bytedcli tce cluster reset --psm example.service.api --env prod --cluster-name default --dry-run

# 更新集群（通过 JSON 文件提交 update_info）
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes
bytedcli tce cluster update --cluster-name default --psm example.service.api --env prod --update-info-file payload.json --dry-run
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --wait --note "demo update"

# 镜像升级：--psm 与 --service-id 同用时仅用于 image_tag 查询，不会作为服务 selector 发送
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 --psm example.image.service --dry-run

# 集群扩缩容（调整各 IDC 副本数）
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --dry-run
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --yes
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> --scale-info-file scale.json --wait --pipeline-template 400013643

# 集群滚动重启（TCE 原生「操作实例 → 重建实例」，由 TCE 按并发粒度滚动重建）
bytedcli tce cluster restart --psm example.service.api --env prod --cluster-name demo-prod --dry-run
bytedcli tce cluster restart --cluster-id <cluster_id> --service-id <service_id> --surge-percent 25 --interval-sec 10 --yes --wait

# 列出服务实例（推荐使用 --psm + --env）
bytedcli --site cn tce instance list --psm example.service.api --env prod --ordering -cpu

# 搜索服务实例（兼容方式：使用 service_id）
bytedcli --site cn tce instance search --service-id <service_id> --ordering cpu --page 1 --page-size 10

# 按 node IP 过滤服务实例
bytedcli tce instance list --service-id 234558 --node-ip 10.35.142.21 --force-update --page 1 --page-size 10 --tce-site boe

# 从指定 PPE Pod 下载日志文件；默认上限 10 MiB，失败不保留半文件
bytedcli --site cn tce instance download \
  --psm example.service.api \
  --env ppe_demo \
  --pod-name demo-pod \
  --container-name main \
  --remote-path /opt/tiger/toutiao/log/result.log.gz \
  --output ./result.log.gz



# 直接复用本地浏览器态 SSO session，自动从 PSM/env 建立 webshell 会话
bytedcli --json auth login --begin --session --session-method qr --no-terminal-qr
bytedcli --json auth login --complete <complete_token>
bytedcli tce webshell open --psm example.service.api --env prod --first
bytedcli tce webshell exec --session-id ws_demo --command 'hostname; date'
# 仅当上一步返回 TCE_WEBSHELL_OTP_REQUIRED 时使用；TTY 会隐藏输入，Agent 应通过子进程 stdin pipe 注入一行
bytedcli tce webshell exec --session-id ws_demo --command 'hostname; date' --otp-stdin
bytedcli tce webshell interactive --psm example.service.api --env prod --first
# 交互模式同样支持自动输入 OTP：TTY 下先隐藏输入，连上后看到提示只自动提交一次
bytedcli tce webshell interactive --psm example.service.api --env prod --first --otp-stdin
```

### 工单幂等与重试

`service create/update/delete` 与 `cluster create/reset/update/scale/restart` 会在内部自动生成一次性 `client_token`；同一命令进程内的网络重试会复用完全相同的 Token 和请求体。该机制不提供用户输入、输出或跨进程复用入口。`deployment action/cancel/execute-step`、`instance delete`、`instance force-delete`、`service check-repos` 和 `deploy-lane` 不启用这项自动写重试。

### WebShell OTP（Agent Guidance）

- 首次调用 `tce webshell exec` 时不要预先索要 OTP。若目标无需 OTP，命令会按原流程执行。
- WebShell 的 OTP 提示有三种文案，bytedcli 均能识别：`please input otp code`、`please input seal/feilian OTP code`、`请输入Google Authenticator OTP码（输入q退出）`。
- 返回 `TCE_WEBSHELL_OTP_REQUIRED` 时，保留原 `session-id` 与命令，通过模型对话之外的 secret input 获取一个当前 Seal/飞连 OTP，再用 `--otp-stdin` 重试同一命令。
- exec 模式：Agent 以 stdin pipe 启动子进程，写入一行 OTP 后关闭 stdin 即可（exec 不占用进程 stdin）。
- interactive 模式：TTY 下会先显示隐藏输入提示，OTP 在 WebShell 打印提示时自动提交，然后正常进入 shell；非 TTY 管道中 OTP 行之后的字节会回留给会话使用，但 stdin 一旦 EOF 会话立即关闭——只喂一行 OTP 就关 stdin 会在门禁提示出现前结束，OTP 无法提交。因此非 TTY 场景不要用 interactive，改用 `tce webshell exec --otp-stdin`（exec 不占用 stdin）。
- 不要把 OTP 拼进 shell 命令，也不要通过 argv、环境变量、文件、日志或普通对话传递。
- OTP 只在连接后 30 秒的门禁窗口内自动提交一次。`TCE_WEBSHELL_OTP_INVALID` 表示 OTP 无效或已过期：丢弃该值并重新请求，禁止自动重放；interactive 模式下服务端再次提示时由用户手工输入或退出重进。
- `TCE_WEBSHELL_OTP_TIMEOUT` 表示认证后未在时限内进入 shell：重新连接同一持久化会话并使用当前 OTP 重试。
- bytedcli 会在看到 OTP 提示后先单独提交 OTP，确认出现认证后终端输出才发送业务命令；错误分支不会把业务命令当作 OTP。

## 发布工单

```bash
# 查询发布工单列表
bytedcli tce deployment list --service-id <service_id> --type upgrade
bytedcli tce deployment list --psm example.service.api --env prod --type upgrade

# 查询发布工单详情
bytedcli tce deployment get <deployment_id>

# 取消发布工单
bytedcli tce deployment cancel <deployment_id>

# 执行工单级 action（先通过 deployment get 查看 pipeline.allow_actions）
bytedcli tce deployment action --deployment-id <deployment_id> --action start --dry-run
bytedcli tce deployment action --deployment-id <deployment_id> --action start --yes

# 执行步骤级 action（先通过 deployment get 查看 step.allow_actions）
bytedcli tce deployment execute-step --step-id <step_id> --action start --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action start --yes

# 跨站点查询
bytedcli --site boe tce deployment list --service-id <service_id>
bytedcli --site byteintl tce deployment get <deployment_id>
```

## 环境级联查询

```bash
# 查询 PSM 的环境级联信息（partition -> env -> lane）
bytedcli tce env-cascader --psm example.service.api

# 指定分区
bytedcli tce env-cascader --psm example.service.api --partition CN

# 指定环境
bytedcli tce env-cascader --psm example.service.api --env prod
```

## 泳道部署

```bash
# 部署泳道（需要指定 env、standard-env、psm、flow-base、branch）
bytedcli tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --flow-base prod \
  --branch master

# 部署指定 SCM 版本（仅提交指定仓库，不携带完整 SCM 列表）
bytedcli tce deploy-lane \
  --env prod \
  --standard-env boe \
  --psm example.service.api \
  --flow-base boe \
  --scm-repo-name example/service/api \
  --scm-repo-version 1.0.0.8 \
  --action upgrade

# 创建时注入自定义环境变量（逗号分隔 key=value）
bytedcli tce deploy-lane \
  --env boe_demo \
  --standard-env boe \
  --psm example.service.api \
  --action create \
  --cluster-names default \
  --env-vars "scmVersion=1.0.0.100"

# 开启热部署
bytedcli tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --flow-base prod \
  --branch master \
  --action create \
  --hot-deploy
```

### 精确 SCM 制品部署到 PPE

当 PPE 验证必须证明某个 Git/MR commit 已实际运行时，不要直接按可漂移的 branch 部署。先构建该 commit 的 SCM test 制品并从 `data.versions[]` 精确核对 `version`、`base_commit_hash`、`status=build_ok`，再使用 `--scm-repo-name + --scm-repo-version` 只提交一次泳道升级。完整的写前漂移门禁、不明结果恢复、ENV/TCE 工单回读、实例健康和共享域名 PPE 路由验证见 `references/tce.md` 的「精确 SCM 制品到 PPE 泳道」章节。

## 环境变量注入（upgrade-tce）

```bash
# 升级时设置自定义环境变量（upgrade-tce 是真实写操作：--dry-run 预览 / --yes 提交，二选一）
bytedcli env service upgrade-tce \
  --psm example.service.api \
  --env boe_demo \
  --standard-env boe \
  --cluster-id 12345 \
  --env-vars "scmVersion=1.0.0.100" \
  --yes
```

`--env-vars` 支持逗号分隔的多个键值对，如 `--env-vars "key1=val1,key2=val2"`。值会合并到集群的 `new_env_vars` 中，不会覆盖未指定的已有环境变量。

## 跨站点示例

```bash
bytedcli --site boe tce service search --keyword "my-service"
bytedcli --site byteintl tce service search --keyword "my-service"
bytedcli --site ttp-us-limited tce service search --keyword "my-service"
bytedcli --site ttp-eu tce service search --keyword "my-service"
```

## 输出结构（--json）

加 `--json`（全局选项，放在子命令之前）时，列表类命令返回统一信封结构：

- 顶层：`{ status, data, error, context }`；成功时 `status="success"`、`error=null`。
- 列表数据位于 `data.<资源复数>[]`：收藏/搜索服务在 `data.services[]`，集群在 `data.clusters[]`，工单在 `data.deployments[]`。**例外：实例列表在 `data.pods[]`（不是 `data.instances`）。**
- 分页信息位于 `data.page_info{ total_count, page_num, page_size }`；另有冗余字段 `data.total`。**实例（`instance list`）按「是否走服务实例分页接口」分两类：含 `data.page_info`（`--page-size` 生效）——`--psm [--env]`，或 `--service-id` 搭配 `--ordering` / `--node-ip`；无 `data.page_info`、只有 `data.total`、一次返回全量——裸 `--service-id` 或裸 `--cluster-id`（二者互斥，不能同传）。**
- 执行上下文位于 `context{ execution_time_ms, timestamp, api_endpoint }`。

下游脚本/Agent 解析时，统一按「成功看 `status`、取列表读 `data.<资源复数>`、取分页读 `data.page_info`」处理；`instance list` 的列表始终读 `data.pods[]`，分页则按上一条区分：走服务实例分页接口的形态（`--psm [--env]`、或 `--service-id` 加 `--ordering`/`--node-ip`）有 `page_info`，裸 `--service-id`、裸 `--cluster-id` 仅有 `data.total`。

## Notes

### 服务负责人字段

查询服务负责人读 `data.auth.iam_info.owners[]`（每项含 `username`、`email`，保留完整列表）；`auth.owner_name` 是 GDPR/ZTI 鉴权用户名、`auth.owner` 为已废弃 ID，均非负责人。`owners` 缺失或为空时如实说明未返回 IAM owner，不要用这两个字段兜底。

### 安全规则

- **`cluster update` 安全规则（MUST follow）**：(1) ALWAYS 先 `--dry-run` 并展示完整请求给用户；(2) ALWAYS 等用户明确确认后才执行真正提交；(3) `update_info` 为替换语义——修改 `env_list` 时 MUST 包含全部已有环境变量，否则遗漏的变量会被永久删除；(4) 首次提交不要用 `--yes`，让 CLI 弹确认。详见 `references/tce.md` 中的 CRITICAL SAFETY RULES
- **`cluster scale` 安全规则**：与 `cluster update` 相同——(1) ALWAYS 先 `--dry-run`；(2) 等用户确认后再真正提交；(3) 首次提交不要用 `--yes`。`--dry-run` 仍会调用 TCE scale API 并发送 `dry_run: true`，可能触发后端校验，但不应创建真实变更。服务定位用 `--psm`（可选 `--env`，不传默认 `prod`）或 `--service-id`，且只能二选一；集群定位用 `--cluster-name` 或 `--cluster-id`，且只能二选一。遇到 `InvalidParameter.Ambiguous` 时 MUST 展示后端 message 中的候选 ID 并让用户选择，不得自动选择。可用 `--replicas` 自动按集群 IDC 扩缩容，或用 `--scale-info-file` 传 `{ "dc_info": [...], "canary_dc_info": [...] }`；预留模式缩容时 `dc_info[].quota_op` 支持 `{ "type": "reserve", "to_psm": "<target_psm>" }`
- **服务/集群创建安全规则**：`service create/update/delete`、`cluster create/reset`、`service check-repos`、`deployment action`、`deployment execute-step` 默认必须二选一：先 `--dry-run` 展示请求体，或在用户明确确认后加 `--yes` 提交；同时传 `--dry-run` 和 `--yes` 时，`--dry-run` 优先生效且不会提交真实请求。创建 LGP/TCE 服务时优先使用平台推荐模板或控制台导出的 `service_info` / `cluster_info` payload，不要凭空拼接复杂 payload。
- **`cluster restart` 安全规则**：该命令调用 TCE 正式「操作实例 → 重建实例」接口（`/deployment/cluster/pod_exec/`，`exec_type=rebuild`），由 TCE 按 `--surge-percent`（并发粒度，默认 10%）和 `--interval-sec`（操作间隔，默认 30s）滚动重建整集群实例，**不是逐个删 Pod**。(1) ALWAYS 先 `--dry-run` 看请求体；(2) 等用户确认后再加 `--yes` 真正执行；(3) 不要把「重启」与 `instance delete` 混用——本命令是显式的滚动重建工单，可用 `--wait` 等待工单到终态。
- `service get`、`cluster list`、`deployment list` 都支持 `--psm`；如果同一 PSM 在多个 env 下都有服务，可加 `--env` 做唯一定位
- `service check-repos`、`cluster reset/update` 也支持 `--psm [--env]`；省略 `--env` 时按 `prod` 发送。`cluster reset/update` 的服务选择器和集群选择器彼此独立，可以组合 `--service-id + --cluster-name` 或 `--psm [--env] + --cluster-id/--cluster-name`
- `cluster list --cluster-name` 可按集群名过滤结果；当同一 vregion 下存在多个同名集群时，建议和 `--service-id` 或 `--psm --env` 一起使用
- **PPE 环境**：当 `--env` 值匹配 `ppe` 或 `ppe_*` 时，bytedcli 自动按 PPE 环境查询，无需显式传 `--ppe`。拿到 PPE service ID 后，`deployment list`、`cluster update`、`instance list` 等命令直接用 `--service-id`
- `instance list` 推荐使用 `--psm + --env` 组合；兼容方式也支持 `--service-id`
- `instance list --node-ip` 可按 node IP 过滤服务实例；仅支持和 `--service-id` 或 `--psm --env` 一起使用，不支持 `--cluster-id`
- `instance list` 的文本表格会展示 `IDC` 列；按 `--node-ip` 排查时可直接看到实例所在机房
- 实例迁移沿用 `instance delete` 命令，调用 `DELETE /open-apis/v1/pods/`；需要同时传 `--cluster-id`、`--idc`、`--pod-name`；推荐先 `--dry-run` 检查 DELETE 请求，默认会要求交互确认，非交互场景可显式加 `--yes`
- **`instance force-delete` 稳定性规则（MUST follow）**：
  (1) 仅在用户明确要求强制删除时使用；必须告知其会绕过 PDB 并上报故障宿主机。
  (2) 删除前先用 `instance list` / `instance search` 确认目标站点及实例当前仍存在且唯一，避免用过期 pod 名或模糊匹配结果直接删。
  (3) 执行 `--pod-name <name> --dry-run` 展示请求；再次确认后才加 `--yes`，`--dry-run` 优先。
  (4) 每次仅处理一个实例，执行前检查健康副本，执行后重新查询实例状态；状态异常时停止，不与其他实例或部署变更并发执行。
- **`instance delete` 稳定性规则（MUST follow）**：
  (1) 除非用户明确要求“删除实例 / 删除 pod”，或上下文明确是在做“实例迁移 / 节点迁移”并且删除实例是迁移动作的一部分，否则不要主动建议或执行 `tce instance delete`；不要把“重启”“排障”“恢复”“摘流量”自动等同为删除实例。
  (2) 禁止一次性删除 2 个或以上实例；任何多实例场景都只能单个串行执行，每删一个都要重新观察，再决定下一个。
  (3) 任何真实删除前都必须先执行 `--dry-run`，并向用户展示精确的 `cluster-id / idc / pod-name`。
  (4) 任何真实删除都必须二次确认：第一次确认目标实例是否正确，第二次确认是否现在执行删除；不要复用历史确认。
  (5) 删除前先用 `instance list` / `instance search` 确认目标实例当前仍存在且唯一，避免用过期 pod 名或模糊匹配结果直接删。
  (6) 删除前先检查剩余实例数量与状态；如果无法确认删除后仍有足够健康副本，尤其是 prod / 单副本 / 低副本场景，先提示风险并暂停，等待用户明确继续。
  (7) 删除后必须重新执行实例查询，确认 replacement / remaining pods 状态，再继续任何下一步操作；如果删除后状态异常，不要继续串行删第二个。
  (8) 不要把实例删除和 `cluster update`、扩缩容、deployment 操作并发混用；有正在进行的发布或变更时，优先提醒用户存在叠加风险。
- **`instance download` 下载规则**：当前只支持 `--site cn`，远端文件必须位于 TCE 官方允许目录；默认最多下载 10 MiB，可用 `--max-bytes` 调大。命令流式写入输出目录中的本地临时文件，校验响应长度并计算本地 SHA-256，成功后才原子落盘；失败时仅清理本地未完成的临时文件，不会修改或删除 Pod 内的远端文件。默认不覆盖已有的本地文件，明确需要覆盖时才传 `--force`。一次性 relay 签名 URL 不会出现在成功输出中。

### 资源定位参数

- `service get`、`cluster list`、`deployment list` 都支持 `--psm`；如果同一 PSM 在多个 env 下都有服务，可加 `--env` 做唯一定位
- `service check-repos`、`cluster reset/update` 也支持 `--psm [--env]`；省略 `--env` 时按 `prod` 发送。`cluster reset/update` 的服务选择器和集群选择器彼此独立，可以组合 `--service-id + --cluster-name` 或 `--psm [--env] + --cluster-id/--cluster-name`
- `cluster list --cluster-name` 可按集群名过滤结果；当同一 vregion 下存在多个同名集群时，建议和 `--service-id` 或 `--psm --env` 一起使用
- **PPE 环境**：当 `--env` 值匹配 `ppe` 或 `ppe_*` 时，bytedcli 自动按 PPE 环境查询，无需显式传 `--ppe`。拿到 PPE service ID 后，`deployment list`、`cluster update`、`instance list` 等命令直接用 `--service-id`
- 实例迁移沿用 `instance delete` 命令，调用 `DELETE /open-apis/v1/pods/`；需要同时传 `--cluster-id`、`--idc`、`--pod-name`；推荐先 `--dry-run` 检查 DELETE 请求，默认会要求交互确认，非交互场景可显式加 `--yes`

### 分页与输出

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json tce instance list --psm example.service.api --env prod ...`）；返回信封结构见上方「输出结构（--json）」
- `instance list` 推荐使用 `--psm + --env` 组合；兼容方式也支持 `--service-id`
- `instance list --node-ip` 可按 node IP 过滤服务实例；仅支持和 `--service-id` 或 `--psm --env` 一起使用，不支持 `--cluster-id`
- `instance list` 的文本表格会展示 `IDC` 列；按 `--node-ip` 排查时可直接看到实例所在机房
- `instance list --ordering` 支持 `cpu/mem/idc/createtime/podstatus`，带 `-` 前缀表示倒序

### 站点与别名

- Flag renames: `--page-num` is now `--page`; old name still works as a hidden alias
- 使用全局 `--site` 选择站点（`cn|boe|byteintl|ttp-us-limited|ttp-eu`），不传则默认跟随 `BYTEDCLI_CLOUD_SITE`。Per-service `--tce-site` is a hidden alias for backward compatibility.
- 常用别名：`prod=cn`、`i18n=byteintl`、`tx-ttp=ttp-us-limited`、`eu-ttp=ttp-eu`

### WebShell

- `tce webshell` 适合在 `instance list` / `deployment get` 已经定位到目标 pod 之后做补充排障；agent 优先使用 `auth login --begin --session --session-method qr --no-terminal-qr` + `auth login --complete <token>` 准备浏览器态 SSO session，再使用 `tce webshell open/exec/close`，人用交互场景再使用 `tce webshell interactive --psm --env`。BOE webshell 若返回 SSO HTML 或 `invalid JSON response`，通常需要额外补一次 `--site cn` 的 session。

## References

- `references/tce.md`
