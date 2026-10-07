# TCE

## 站点

```bash
# 列出支持的站点
bytedcli tce list-sites
```

在 ByteDance 生产网络内使用 `--site i18n-tt` 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`，TCE OpenAPI 与 ByteCloud JWT host 会自动切到生产网可达的 `cloud-i18n.bytedance.net`。

## 服务查询

```bash
# 收藏的服务
bytedcli tce service list --page 1 --page-size 10

# 搜索服务
bytedcli tce service search --keyword "keyword" --env "ppe_xxx" --page 1 --page-size 10

# 获取服务详情（也支持 --psm + 可选 --env）
bytedcli --site cn tce service get <service_id>
bytedcli --site cn tce service get --psm example.service.api --env prod

# 列出服务集群（支持 --service-id 或 --psm）
bytedcli --site cn tce cluster list --service-id <service_id> --page 1 --page-size 10
# 集群列表两种视图（默认聚合 vs. IDC 明细）

# 1）默认视图（聚合，加权汇总，每个集群一行；IDC 列隐藏）
bytedcli --site cn tce cluster list --psm example.service.api --env prod --page 1 --page-size 10
bytedcli --site boe tce cluster list --service-id 234558 --cluster-name tls_mix_proxy_boe --page 1 --page-size 10

# 2）IDC 明细视图（每个集群 × IDC 一行）
bytedcli --site cn tce cluster list --psm example.service.api --env prod --with-idc --page 1 --page-size 10
# 列出 PPE 集群（--env ppe_* 自动推断 PPE 环境，无需显式传 --ppe）
bytedcli --site ttp-us-limited tce cluster list --psm example.service.api --env ppe_rd_test_env --page-size 100
```

### 服务负责人字段

查询服务负责人读 `data.auth.iam_info.owners[]`（每项含 `username`、`email`，保留完整列表）；`auth.owner_name` 是 GDPR/ZTI 鉴权用户名、`auth.owner` 为已废弃 ID，均非负责人。`owners` 缺失或为空时如实说明未返回 IAM owner，不要用这两个字段兜底。

## 服务与集群创建

> **SAFETY RULES — MUST follow:** `service create/update/delete`、`cluster create/reset`、`service check-repos`、`deployment action`、`deployment execute-step` 都会操作真实 TCE 工单、部署步骤或真实校验请求。Agent 必须先执行 `--dry-run` 并展示完整请求体，只有用户明确确认后才加 `--yes` 提交。同时传 `--dry-run` 和 `--yes` 时，`--dry-run` 优先生效且不会提交真实请求。

**工单幂等 Token：**`service create/update/delete` 与 `cluster create/reset/update/scale/restart` 在内部生成 UUIDv4 `client_token`，并仅为这些已有 Token 契约的工单提交启用 HTTP 重试。同一条命令的所有重试复用同一个请求体和 Token。Token 不作为 CLI 参数或用户输出，也不支持跨进程复用。`deployment action/cancel/execute-step`、`instance delete`、`instance force-delete`、`service check-repos`、`deploy-lane` 不自动重试。

```bash
# 创建服务：service_info 建议来自平台推荐模板或控制台导出的 payload
bytedcli tce service create --service-info-file service-info.json --dry-run
bytedcli tce service create --service-info-file service-info.json --yes

# 更新 / 删除服务
bytedcli tce service update --service-id <service_id> --update-info-file update-info.json --dry-run
bytedcli tce service delete --service-id <service_id> --dry-run

# 查询和校验服务可用 SCM 包
bytedcli tce service repo-info-list --service-id <service_id>
bytedcli tce service check-repos --service-id <service_id> --request-file check-repos.json --dry-run
bytedcli tce service check-repos --psm example.service.api --env prod --request-file check-repos.json --dry-run

# 创建 / 删除集群：cluster_info 同样建议来自平台推荐模板或控制台导出的 payload
bytedcli tce cluster create --service-id <service_id> --cluster-info-file cluster-info.json --dry-run
bytedcli tce cluster create --service-id <service_id> --cluster-info-file cluster-info.json --yes
bytedcli tce cluster reset --service-id <service_id> --cluster-id <cluster_id> --dry-run
bytedcli tce cluster reset --service-id <service_id> --cluster-name default --dry-run
bytedcli tce cluster reset --psm example.service.api --env prod --cluster-name default --dry-run
```

`check-repos.json` 只包含 `repos` 和 `cluster_ids`；服务选择器写入 URL path，不要在 JSON body 中添加 `service_id`。`--psm` 模式省略 `--env` 时，bytedcli 按 `prod` 发送。`cluster reset/update` 的服务选择器和集群选择器彼此独立，名称由 TCE 后端解析；名称不唯一时会原样返回候选集群信息。

### PPE 环境操作流程

PPE 服务的 service ID 与 prod 不同。当 `--env` 值匹配 `ppe` 或 `ppe_*` 时，bytedcli 自动按 PPE 环境查询，无需显式传 `--ppe`。
获取到 PPE service ID 后，其他所有命令（`cluster update`、`deployment list`、`instance list` 等）直接使用 `--service-id` 即可。

```bash
# 第 1 步：用 --env ppe_* 查到 PPE 服务和集群（自动推断 PPE，假设返回 service_id=100343）
bytedcli --site ttp-us-limited tce cluster list --psm example.service.api --env ppe_rd_test_env

# 第 2 步：后续命令直接用 --service-id
bytedcli --site ttp-us-limited tce deployment list --service-id 100343
bytedcli --site ttp-us-limited tce cluster update --cluster-id 305999 --service-id 100343 --update-info-file payload.json --yes
bytedcli --site ttp-us-limited tce instance list --service-id 100343
```

## 集群更新

> **CRITICAL SAFETY RULES — MUST follow ALL steps in order:**
>
> 1. **ALWAYS `--dry-run` first.** Never submit a cluster update without first running `--dry-run` and showing the full request body to the user.
> 2. **ALWAYS ask the user for explicit confirmation** before running the real update (without `--dry-run`). Do NOT proceed based on prior approval or assumptions — ask every time.
> 3. **ALWAYS include ALL existing values** in `update_info`. The API uses **replace semantics** — any field you omit will be wiped. For example, if a cluster has 7 environment variables and you only send 1, the other 6 will be deleted.
> 4. **Before modifying `env_list`**, first retrieve the current environment variables (from TCE console or the cluster detail API) and include every existing variable in your payload, only changing the ones the user asked to modify.
> 5. **`--yes` 必须显式带上才会提交。** 不传 `--yes`（且不传 `--dry-run`）时命令会直接报 `TCE_CONFIRMATION_REQUIRED` 并提示加 `--yes` / `--dry-run`，不会进入交互等待。这使 agent 场景下命令可脚本化；但意味着首次执行前务必按规则 1 先 `--dry-run` 给用户看。

```bash
# Step 1: ALWAYS dry-run first — show the request to the user
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --dry-run

# Step 2: ONLY after user explicitly confirms the dry-run output, submit with --yes
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes --note "description of change"

# Step 3 (optional): wait for completion
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes --wait --note "description of change"

# 也可交叉组合服务与集群选择器；省略 --env 时按 prod 发送
bytedcli tce cluster update --service-id <service_id> --cluster-name default --update-info-file payload.json --dry-run
bytedcli tce cluster update --psm example.service.api --env prod --cluster-id <cluster_id> --update-info-file payload.json --dry-run
bytedcli tce cluster update --psm example.service.api --env prod --cluster-name default --update-info-file payload.json --dry-run
# 可选参数：--purpose、--delay-online、--pipeline-template、--change-single-dc、--block-delay-config
# 等待参数：--wait-timeout-sec（默认 600）、--poll-interval-sec（默认 5）
```

### US-TTP 自动分发

`/deployment/cluster/update/` 在 US-TTP 被 `bytepaas.gateway.common` 的 OG schema 拦截（`update_info.repo_info.*` 字段未登记）。当站点为 US-TTP (`--site us-ttp*` 或 `--tce-site ttp-us-limited`) 且 **update_info 只包含 `repo_info`（纯版本升级）** 时，`cluster update` 内部自动改走 console 的 pipeline 升级端点 `/deployment/cluster/upgrade/`，无需用户切换命令。其它情况（含 `env_list` / resource / weight 等非版本字段）仍走原 `/update/` 端点——在 US-TTP 上这些字段目前仍受 OG 限制，如需修改请走 console。

```bash
# US-TTP 上纯版本升级 — 自动走 pipeline 端点
bytedcli --site us-ttp tce cluster update --cluster-id 400581289 --service-id 3987 --update-info-file repo_only.json --yes

# CN / 其他站点也可主动走 pipeline 端点（当 update_info 只含 repo_info 时）
# --pipeline-template 可省：省略时请求体不带 pipeline_template，由 TCE 服务端解析
#   该 service 自己配置的升级管线。仅当某 service 需要特定模板时才显式传 --pipeline-template <id>。
bytedcli tce cluster update --cluster-name default --psm example.service.api --env prod \
  --update-info-file repo_only.json --yes
```

> **单集群 repo-only 升级的 pipeline_template**：省略 `--pipeline-template` 时
> bytedcli 不发送 `pipeline_template`，TCE 服务端按 service 自身配置解析升级管线。
> 若某 service 没有可解析的默认升级管线，会报 `get pipeline_template error: ... no documents in
result`——此时显式传 `--pipeline-template <id>`，或改用 `tce deploy-lane` / 控制台。

### 一单多集群（multi-cluster ticket）

`cluster update` 支持用 `--cluster-ids id1,id2,...`（逗号分隔，与 `--cluster-id` 互斥）把多个集群放进**一张**部署单。pipeline 升级端点 `/deployment/cluster/upgrade/` 的 `cluster_list` 是数组，能一单覆盖多集群；旧的 `/deployment/cluster/update/` 端点只有单 `cluster` 字段、不能批量。因此 `--cluster-ids` **仅适用于会路由到 upgrade 端点的两类升级**：

- **纯版本升级**：`--update-info-file` 的 `update_info` 只含 `repo_info`（与上面 US-TTP 自动分发同一条件）。
- **镜像模式**：`--image-version`（见下一节）。

若 `--cluster-ids` 配合的 `update_info` 含 `env_list` / resource / weight 等非 `repo_info` 字段，命令会以 `TCE_INPUT_ERROR` 拒绝（这类变更只能走旧 `/update/` 单集群端点，多集群请改用控制台批量升级或每集群一单）。

```bash
# 多集群纯版本升级 — 先 dry-run 看 cluster_list 是否两个集群都在
bytedcli tce cluster update --cluster-ids 12345,67890 --service-id <service_id> \
  --update-info-file repo_only.json --dry-run

# 也可用 --cluster-names + psm/env；pipeline upgrade 端点会编码为 cluster_list[].name
bytedcli tce cluster update --cluster-names canary,default --psm example.service.api --env prod \
  --update-info-file repo_only.json --dry-run

# 用户确认后提交一张覆盖两集群的升级单
bytedcli tce cluster update --cluster-names canary,default --psm example.service.api --env prod \
  --update-info-file repo_only.json --yes

# 多集群镜像模式
bytedcli tce cluster update --cluster-ids 12345,67890 --service-id <service_id> \
  --image-version 1.0.0.86 --psm <psm> --yes
```

> **灰度建议**：逐集群一单（`--cluster-id X` 每集群一单，可独立观察/回滚）与一单多集群（`--cluster-ids` 一次覆盖多集群）按需选择；一单多集群等价于控制台「批量升级」，回滚以单为粒度。

### 镜像模式（image-mode / manifest-mode）服务升级

`image_mode=false`（console 升级页 "基于 SCM 配置" radio disabled）的服务**不接受 SCM-mode 升级**，必须按 image_version + image_tag 提交，否则 server 返回：

```
HTTP 400 image_version is not provided for upgrading service in manifest mode
```

`cluster update` 用 `--image-version`（与 `--update-info-file` 互斥）走 image-mode 路径：

```bash
# Step 1: dry-run — image_tag 自动从 image_versions_info 解析
bytedcli --site i18n-tt tce cluster update \
  --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 --pipeline-template <template_id> --dry-run

# Step 2: 用户确认后提交
bytedcli --site i18n-tt tce cluster update \
  --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 --pipeline-template <template_id> --yes

# 直接指定 image-tag（跳过 image_versions_info 查询）
bytedcli --site i18n-tt tce cluster update \
  --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 \
  --image-tag tce/example.image.service:abcdef0123456789 \
  --pipeline-template <template_id> --yes
```

> **SAFETY RULES — 同 SCM 模式**：必须先 `--dry-run` 给用户看完整请求体，确认后再 `--yes`。不传 `--yes` / `--dry-run` 时命令直接报 `TCE_CONFIRMATION_REQUIRED` 中止。

互斥关系：

- `--update-info-file` 与 `--image-version` 二选一，必须有一个
- `--image-version` + `--image-tag` 直接发；只传 `--image-version` 时自动 GET `/services/<id>/image_versions_info/` 按 image_version 匹配 `image_name → image_tag`
- 自动解析查不到（默认前 50 条），传 `--psm` 触发 manifest_info 兜底（但 i18n-tt 等站点 manifest_info 通常不带 image_tag，命中率不高）
- image 模式允许兼容调用 `--service-id <id> --psm <psm>`：`--service-id` 仍是升级请求的服务 selector，`--psm` 只用于 image_tag 查询，最终请求只发送 `service`。该组合不能再带 `--env`
- 仅使用 `--psm [--env]` 时，PSM/env 是服务 selector，最终请求发送 `psm` 和 `env`，不发送 `service`；此模式必须显式传 `--image-tag`

请求体差异（与 SCM 模式对比）：

- `cluster_info.runtime.repo_info`: `[]`（空数组），与 SCM 模式真实 repo 数组不同
- `cluster_info.runtime.image_tag` / `image_version`: 必填
- `pipeline_template`: 可省略；镜像模式服务若需要具体模板，从 console 升级页"流水线模板" 下拉或 `/pipeline_template?...&type=upgrade` 拿 ID 后用 `--pipeline-template` 显式传入

什么时候用哪个：

- 服务有 SCM 配置（升级页能选 "基于 SCM 配置"）→ `--update-info-file` 传 `repo_info`
- 服务只能选 image_version → `--image-version`

其中 `repo_only.json`：

```json
{
  "repo_info": [
    {
      "name": "ies/tiktok_plus/tiktok_predict",
      "version": "2.0.1.5922",
      "scm_repo_id": "425818",
      "main_repo": true
    }
  ]
}
```

**update_info JSON 示例**（修改环境变量 — 注意包含全部已有变量）：

```json
{
  "runtime": {
    "env_list": [
      { "env_name": "DEPLOY_PATH", "env_value": "/opt/tiger/example_bin" },
      { "env_name": "RUNTIME_IDC_NAME", "env_value": "useast5" },
      { "env_name": "SCM_NAME", "env_value": "data.search.example_us" },
      { "env_name": "SCM_VERSION", "env_value": "2.0.3.1752" },
      { "env_name": "SEC_KV_AUTH", "env_value": "1" },
      { "env_name": "START_SCRIPT", "env_value": "bash /opt/tiger/example_bin/runs/tce_run" },
      { "env_name": "TCE_PRELOAD_SCRIPT", "env_value": "preload.sh" }
    ]
  }
}
```

> **WARNING**: `update_info` fields use **replace semantics**. If you modify `env_list`, you MUST include the cluster's complete set of environment variables. Omitted variables will be permanently deleted. Always retrieve the current cluster configuration first, then make targeted changes on top of the full list.

## 集群扩缩容

> **SAFETY RULES — 同 `cluster update`：** ALWAYS 先 `--dry-run` 并展示请求给用户，用户确认后再加 `--yes` 提交；不传 `--yes` / `--dry-run` 时命令会直接报 `TCE_CONFIRMATION_REQUIRED` 中止。`cluster scale --dry-run` 仍会调用 TCE scale API 并发送 `dry_run: true`，因此可能触发后端校验，但不应创建真实变更。

```bash
# Step 1: dry-run 预览（推荐：直接使用 PSM 和集群名）
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --dry-run

# Step 2: 用户确认后提交
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --yes

# 兼容方式：显式传 ID 和 scale_info 文件
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> --scale-info-file scale.json --dry-run

# 可选：等待部署完成
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> --scale-info-file scale.json --yes --wait --pipeline-template 400013643

# 输入规则：
# - service 标识：--service-id，或 --psm + 可选的 --env，二选一；--env 不传时默认 prod
# - cluster 标识：--cluster-id 或 --cluster-name 二选一
# - scale 输入：--replicas 或 --scale-info-file 二选一
# 可选参数：--canary-replicas（默认 0）、--is-reservation、--pipeline-template
# 预留模式缩容时，scale-info-file 的 dc_info[].quota_op 支持 { "type": "reserve", "to_psm": "<target_psm>" }
# 等待参数：--wait-timeout-sec（默认 600）、--poll-interval-sec（默认 5）
```

当后端返回 `InvalidParameter.Ambiguous` 时，Agent 必须展示 error message 中的候选 ID 并让用户选择，再使用 `--cluster-id` 重试；不得自行选择第一个候选。

## 集群滚动重启

调用 TCE 正式「操作实例 → 重建实例」接口（`POST /deployment/cluster/pod_exec/`，请求体包含 `service`、`cluster`、`exec_type=rebuild`、`exec_params`，可选 `pipeline_template` / `note`），由 TCE 自身按并发粒度滚动重建整集群实例，不是逐个删 Pod。

> **SAFETY RULES — `cluster restart` MUST follow ALL steps in order:**
>
> 1. **ALWAYS `--dry-run` first.** 先展示将要提交的重建请求体。
> 2. **Wait for explicit user confirmation before the real run.** 真正执行前再加 `--yes`。
> 3. **不要把「重启」与 `instance delete` 混用。** 本命令是显式的滚动重建工单，不需要手工删 Pod。
> 4. **Do not overlap with cluster update / scale / deployment changes.** 避免与其它发布或变更并发执行。

参数：`--surge-percent`（并发粒度 %，默认 10）、`--interval-sec`（操作间隔秒，默认 30）、`--pipeline-template`（可选流水线模板 id）、`--note`、`--wait` 及 `--wait-timeout-sec`（默认 600）/`--poll-interval-sec`（默认 5）。

```bash
bytedcli tce cluster restart --psm example.service.api --env prod --cluster-name demo-prod --dry-run
bytedcli tce cluster restart --cluster-id <cluster_id> --service-id <service_id> --surge-percent 25 --interval-sec 10 --yes --wait
```

**scale_info JSON 示例**（调整各 IDC 副本数）：

```json
{
  "dc_info": [{ "idc": "us-east1", "count": 5, "quota_op": { "type": "no-process" } }],
  "canary_dc_info": [{ "idc": "us-east1", "count": 1 }]
}
```

**预留模式缩容并预留给指定 PSM**：

```json
{
  "dc_info": [
    {
      "idc": "MY",
      "count": 27,
      "quota_op": {
        "type": "reserve",
        "to_psm": "example.service.target"
      }
    },
    { "idc": "MY2", "count": 31, "quota_op": { "type": "no-process" } }
  ],
  "canary_dc_info": [
    { "idc": "MY", "count": 2 },
    { "idc": "MY2", "count": 1 }
  ]
}
```

## 发布工单

```bash
# 查询发布工单
bytedcli tce deployment list --service-id <service_id> --type upgrade
bytedcli tce deployment get <deployment_id>

# 取消发布工单
bytedcli tce deployment cancel <deployment_id>

# 工单级 action：先从 deployment get 的 pipeline.allow_actions 确认合法 action
bytedcli tce deployment action --deployment-id <deployment_id> --action start --dry-run
bytedcli tce deployment action --deployment-id <deployment_id> --action start --yes

# 步骤级 action：先从 deployment get 的 step.allow_actions 确认合法 action
bytedcli tce deployment execute-step --step-id <step_id> --action start --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action skip --yes
```

## 服务实例

```bash
# 推荐方式：使用 --psm + --env
bytedcli --site cn tce instance list --psm example.service.api --env prod --ordering -cpu

# 兼容方式：使用 --service-id
bytedcli tce instance list --service-id <service_id> --ordering cpu --page 1 --page-size 10

# 按 node IP 过滤服务实例
bytedcli tce instance list --service-id 234558 --node-ip 10.35.142.21 --force-update --page 1 --page-size 10 --tce-site boe

# 强制刷新缓存
bytedcli tce instance list --psm example.service.api --env prod --force-update

# 获取全部实例（不分页）
bytedcli tce instance list --psm example.service.api --env prod --no-pagination

# 迁移指定实例，推荐先 dry-run
bytedcli tce instance delete --cluster-id 123456 --idc sample-idc --pod-name sample-pod-1 --dry-run
bytedcli tce instance delete --cluster-id 123456 --idc sample-idc --pod-name sample-pod-1 --yes --tce-site boe

# 强制删除实例（绕过 PDB 并上报故障机），默认预览，提交加 --yes
bytedcli --site cn tce instance force-delete --pod-name demo-pod --dry-run
bytedcli --site cn tce instance force-delete --pod-name demo-pod --yes
```

> **CRITICAL SAFETY RULES — `instance delete` MUST follow ALL steps in order:**
>
> 1. **Do not propose or run instance deletion unless the user explicitly asks to delete a specific instance, or the context is clearly an instance/node migration where deleting the instance is part of the migration workflow.** Do not infer delete from broader intents like restart, recover, or troubleshoot.
> 2. **Never delete more than one instance at a time.** If the user wants multiple instances removed, handle them strictly one-by-one, with a fresh checkpoint between each deletion.
> 3. **ALWAYS `--dry-run` first** and show the exact `cluster-id`, `idc`, and `pod-name` that would be deleted.
> 4. **ALWAYS get a second explicit confirmation before the real delete.** One confirmation is for target identity; a second confirmation is for executing the deletion now.
> 5. **Before deleting, re-check that the target pod still exists and is unique** via `instance list` or `instance search`. Never delete based on stale output alone.
> 6. **Before deleting, check remaining capacity and health.** If you cannot confirm that enough healthy replicas remain after deletion, especially in prod or low-replica services, stop and surface the risk first.
> 7. **After deleting, re-list instances and inspect status before taking any further action.** If the service does not recover as expected, do not continue with any second deletion.
> 8. **Do not overlap instance deletion with cluster update / scale / deployment changes.** If another change is in flight, warn about compounded risk before proceeding.

### 从实例下载文件（CN）

`tce instance download` 通过 TCE 文件 relay 把实例内文件直接流式写到本地，不经过 WebShell 输出通道，因此不受终端输出截断影响。当前仅支持经过验证的 `--site cn` 链路。

```bash
# 推荐：用 PSM/env + 精确 Pod/容器名解析 container id
bytedcli --site cn tce instance download \
  --psm example.service.api \
  --env ppe_demo \
  --pod-name demo-pod \
  --container-name main \
  --remote-path /opt/tiger/toutiao/log/result.log.gz \
  --output ./result.log.gz

# 调大下载上限和超时；只有明确需要覆盖本地文件时才加 --force
bytedcli --site cn tce instance download \
  --pod-name demo-pod \
  --container-name main \
  --container-id containerd://demo \
  --remote-path /var/log/tiger/result.log.gz \
  --output ./result.log.gz \
  --max-bytes 52428800 \
  --timeout-ms 180000 \
  --force
```

- TCE 允许的远端目录：`/opt/tiger/cores/`、`/opt/tiger/toutiao/log/`、`/opt/tiger/data/log/`、`/var/log/tiger/`。
- 默认 `--max-bytes 10485760`（10 MiB）、`--timeout-ms 120000`。命令会同时检查 `Content-Length` 和实际流式字节数；超限、超时、中断或校验失败时清理临时文件。
- 默认拒绝覆盖已有本地文件；`--force` 仅覆盖已有普通文件。下载在目标目录内先写私有临时文件，成功后原子提交。
- 成功结果包含 `output_path`、`bytes`、`sha256`、Pod/容器标识和远端路径；一次性签名 URL 不会进入输出。
- 需要先存在浏览器态 SSO session；收到 `AUTH_SESSION_REQUIRED` 时执行 `bytedcli auth login --session` 后重试。

## Relay WebShell

```bash
# 先生成浏览器态 SSO session，再直接从 PSM/env 建连
bytedcli --json auth login --begin --session --session-method qr --no-terminal-qr
bytedcli --json auth login --complete <complete_token>
bytedcli tce webshell open --psm example.service.api --env prod --first
bytedcli tce webshell exec --session-id ws_xxx --command 'hostname; date'
# 仅当上一步返回 TCE_WEBSHELL_OTP_REQUIRED 时使用；TTY 会隐藏输入，Agent 应通过子进程 stdin pipe 注入一行
bytedcli tce webshell exec --session-id ws_xxx --command 'hostname; date' --otp-stdin
bytedcli tce webshell interactive --psm example.service.api --env prod --first
# interactive 同样支持 --otp-stdin：TTY 下先隐藏输入，看到 OTP 提示时自动提交一次
bytedcli tce webshell interactive --psm example.service.api --env prod --first --otp-stdin

# 保存输出到本地文件
bytedcli tce webshell exec --session-id ws_xxx --command-file /tmp/diag.sh --output-file /tmp/diag.out
```

### OTP 编排

1. Agent 先正常调用 `tce webshell exec`。若目标无需 OTP，命令直接执行。
2. 收到 `TCE_WEBSHELL_OTP_REQUIRED` 后，保留相同 `session-id` 与命令，通过模型对话之外的 secret input 获取当前 Seal/飞连 OTP。OTP 提示文案可能是 `please input otp code`、`please input seal/feilian OTP code` 或 `请输入Google Authenticator OTP码（输入q退出）`，bytedcli 均能识别。
3. exec 模式以 stdin pipe 启动带 `--otp-stdin` 的同一命令，写入一行 OTP 后关闭 stdin；interactive 模式 TTY 下先隐藏输入、连上后自动提交。非 TTY 管道不要配 interactive：stdin EOF 会立即关闭会话，只喂一行 OTP 会在门禁提示出现前结束——管道场景统一用 exec。不要通过 argv、环境变量、文件、日志或普通对话传递 OTP。
4. OTP 只在连接后 30 秒的门禁窗口内自动提交一次。收到 `TCE_WEBSHELL_OTP_INVALID` 时丢弃该值并请求新 OTP，禁止自动重放；interactive 下服务端再次提示需手工输入或重进。收到 `TCE_WEBSHELL_OTP_TIMEOUT` 时重新连接同一持久化会话再试。

bytedcli 会在 WebSocket 内先等待 OTP 提示，单独提交 OTP，并在认证后终端输出出现后才发送业务命令。OTP 缺失、无效或超时时不会发送业务命令。

## 发布工单

```bash
# 查询发布工单列表（按服务 ID + 类型筛选）
bytedcli tce deployment list --service-id <service_id> --type upgrade
bytedcli tce deployment list --psm example.service.api --env prod --type upgrade

# 按状态筛选
bytedcli tce deployment list --service-id <service_id> --status finished --page 2

# 获取发布工单详情（返回 meta + pipeline stages + runtime）
bytedcli tce deployment get <deployment_id>

# 获取全局发布工单详情（返回 global ticket + service_info/cluster_info）
bytedcli tce deployment get <global_ticket_id> --global

# 跨站点查询工单
bytedcli --site boe tce deployment list --service-id <service_id>
bytedcli --site byteintl tce deployment get <deployment_id>

# us-ttp 专用：在 USTS Review 步骤选择 USTS-NOC 作为 TTP 审批人并确认
# 对应 UI "操作 → 选择TTP审批人 → 弹窗选 USTS-NOC → 确定"，仅 us-ttp 租户下的部署会有该动作
# 不传 --step-id 时，会自动根据 deployment 详情定位含 choose_ttops_approver 的 ConfirmStep
bytedcli --site us-ttp tce deployment select-ttops-approver "https://cloud-ttp-us.bytedance.net/tce/deployment_new/<deployment_id>?service_id=<service_id>"
bytedcli --site us-ttp tce deployment select-ttops-approver <deployment_id> --step-id <step_id>

# 手动驱动 deployment 流水线中某一步（通用版的 step action 入口）。
# 用途：通过 `tce cluster update` 这类直连 TCE API 创建的部署，UpgradeStep / DetectorStep
# 默认 auto_start=false，需要逐步手动触发；console 上点 "开始" / "跳过" 等于本命令。
# 通过 `bytedcli tce deployment get <deployment_id>` 查看每个 step 的 allow_actions。
bytedcli tce deployment execute-step --step-id <step_id> --action start --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action start --yes
bytedcli tce deployment execute-step --step-id <step_id> --action skip --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action skip --yes
# 需要额外字段的 action（合并到请求体顶层，但 --action 本身不可被覆盖）：
bytedcli tce deployment execute-step --step-id <step_id> --action choose_ttops_approver \
  --extra-json '{"approver_type":"organization_account","is_noc":true}' --dry-run
```

### 流水线整步驱动示例（部署不自动推进时）

直连 `tce cluster update --yes` 创建的部署会以 `auto_start: false` 卡在 deploy stage。
传统做法是去 TCE console 点 "开始" / "跳过"，纯命令行链路用循环 + execute-step 替代：

```bash
TICKET_ID=<from cluster update>
while true; do
  DEP=$(bytedcli --json tce deployment get "$TICKET_ID")
  STATUS=$(echo "$DEP" | jq -r '.data.meta.status')
  case "$STATUS" in
    finished|success) break ;;
    failed|cancelled|canceled) echo "deploy failed: $STATUS"; exit 1 ;;
  esac

  NEXT=$(echo "$DEP" | jq -r '
    .data.pipeline.stages[].steps[]
    | select(.status == "pending")
    | (.id|tostring) + " " + (.allow_actions[]? | select(.name | IN("start","skip")) | .name)
  ' | head -1)
  [[ -z "$NEXT" ]] && { sleep 10; continue; }

  bytedcli tce deployment execute-step \
    --step-id $(echo "$NEXT" | awk '{print $1}') \
    --action  $(echo "$NEXT" | awk '{print $2}') \
    --yes
done
```

## 环境级联查询

```bash
# 查询 PSM 的环境级联信息
bytedcli tce env-cascader --psm example.service.api

# 指定分区
bytedcli tce env-cascader --psm example.service.api --partition CN

# 指定环境
bytedcli tce env-cascader --psm example.service.api --env prod

# 排除分区
bytedcli tce env-cascader --psm example.service.api --excluded-partitions SG,VA
```

## 泳道部署

```bash
# 部署泳道
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

# 开启热部署
bytedcli tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --flow-base prod \
  --branch master \
  --action create \
  --hot-deploy

# 创建时注入自定义环境变量（逗号分隔 key=value）
bytedcli tce deploy-lane \
  --env boe_demo \
  --standard-env boe \
  --psm example.service.api \
  --action create \
  --cluster-names default \
  --env-vars "scmVersion=1.0.0.100"

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

## 精确 SCM 制品到 PPE 泳道

当 PPE 测试需要证明某个 Git/MR commit（而不是可漂移的分支或仓库 latest version）已经运行时，使用以下证据门禁。该流程包含真实远端写入：写前必须冻结目标并获得明确授权；提交结果不明时禁止盲重试。

### 只读写前门禁

1. 冻结本地与远端 source SHA，确认 worktree clean、远端 source branch 与本地 `HEAD` 一致。
2. 通过 `tce env-cascader` 和 ENV/TCE 查询解析 `PSM -> partition -> standard_env -> PPE lane -> lane service/RID -> cluster`。PPE service ID 与 prod service ID 不同，禁止按约定推导。
3. 读取目标泳道当前主仓版本、目标 cluster 的**顶层**实例列表、running/pending 发布工单。递归遍历或聚合得到的实例数不能作为写入前置条件；后续直接读取发生漂移时，必须生成新计划并重新确认。
4. 构建精确 commit 的 SCM test 制品，并按返回 version 回读 `data.versions[]`：只接受唯一一条同时满足 `version=<exact_version>`、`base_commit_hash=<source_sha>`、`status=build_ok` 的记录。请求 filter、filter echo、`data.repo.version` 或列表第一项都不是制品身份证据。
5. 把 source SHA、SCM version、泳道/cluster、expected-before 版本与实例数、唯一一次 upgrade、验收条件和回滚边界绑定到不可变计划。用户确认的是这个计划，不是后续漂移后的新状态。

```bash
# 构建精确 commit 的 test 制品
bytedcli --json scm repo build example/service/api \
  --commit <source_sha> --type test --arch x86_64

# 按返回 version 回读并从 data.versions[] 做唯一精确匹配
bytedcli --json scm repo version list example/service/api \
  --version <exact_version> --page-size 100

# 解析 PPE lane、确认目标集群与直接实例状态
bytedcli --json tce env-cascader --psm example.service.api --partition CN
bytedcli --json tce cluster list --psm example.service.api --env ppe_demo --with-idc --page-size 50
bytedcli --json tce instance list --cluster-id <cluster_id> --page 1 --page-size 50

# 确认没有并发发布者
bytedcli --json tce deployment list --psm example.service.api --env ppe_demo --status running
bytedcli --json tce deployment list --psm example.service.api --env ppe_demo --status pending
```

### 单次受控写入

第二次只读核对仍满足不可变计划后，使用明确 SCM repo/version 只提交一次 upgrade；不要用 mutable branch 代替精确版本。

```bash
bytedcli --json tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --env-type ppe \
  --flow-base prod \
  --scm-repo-name example/service/api \
  --scm-repo-version <exact_version> \
  --action upgrade
```

保存返回的 ENV ticket 和关联 TCE deployment。若命令超时、退出结果不明确或本地进程句柄丢失，先查询同一 ticket、同一泳道与同一 cluster；不得创建第二张工单“再试一次”。

### 只读部署后验收

必须同时证明：

- 原 ENV/TCE 工单进入成功终态，且绑定预期泳道与 cluster；
- 泳道 service/cluster 报告预期 SCM version；
- 目标 cluster 的顶层实例列表达到 expected healthy state；
- 不再有 running/pending 发布工单；
- 共享域名 smoke 携带完整 PPE 路由身份；CN TCE 常见形态为 `x-use-ppe: 1` 与 `x-tt-env: <lane>` 同时存在；
- 返回的公开业务字段证明目标行为，而不只是 HTTP 200。

仅带 `x-tt-env` 的请求可能回落到 online，可作为路由对照，但禁止作为 PPE 验证证据。若新 SCM version 已生效、Pod 健康而响应仍像旧版本，先补齐完整 PPE headers 并重读泳道身份，再判断代码或运行配置问题。主 selector 建议重复请求多次；存在等价 ID selector 时也应同时验证。

smoke 失败时不要自动回滚。保留原工单与现场状态，基于当前 observed state 生成独立 rollback plan，并为回到 prior exact SCM version 单独获取授权。

## 跨站点示例

```bash
bytedcli --site boe tce service search --keyword "my-service"
bytedcli --site byteintl tce service search --keyword "my-service"
bytedcli --site ttp-us-limited tce service search --keyword "my-service"
bytedcli --site ttp-eu tce service search --keyword "my-service"
```

## Notes

- 站点别名：`prod=cn`、`i18n=byteintl`、`tx-ttp=ttp-us-limited`、`eu-ttp=ttp-eu`
- `cluster update` 的 `--update-info-file` JSON 为替换语义；修改 `env_list` 等字段时必须包含全部值，否则覆盖已有配置；`tce cluster edit` 为隐藏别名
- `service get`、`cluster list`、`deployment list` 都支持 `--psm`；如果同一 PSM 在多个 env 下都有服务，可加 `--env` 做唯一定位
- `service check-repos`、`cluster reset/update` 也支持 `--psm [--env]`；省略 `--env` 时按 `prod` 发送。`cluster reset/update` 的服务选择器和集群选择器彼此独立，可以组合 `--service-id + --cluster-name` 或 `--psm [--env] + --cluster-id/--cluster-name`
- `cluster list --cluster-name` 可按集群名过滤结果；当同一 vregion 下存在多个同名集群时，建议和 `--service-id` 或 `--psm --env` 一起使用
- `instance list` 推荐使用 `--psm + --env`；兼容方式也支持 `--service-id`
- `instance list --node-ip` 可按 node IP 过滤服务实例；仅支持和 `--service-id` 或 `--psm --env` 一起使用，不支持 `--cluster-id`
- `instance list` 的文本表格会展示 `IDC` 列；按 `--node-ip` 排查时可直接看到实例所在机房
- 实例迁移沿用 `instance delete` 命令，调用 `DELETE /open-apis/v1/pods/`；需要同时传 `--cluster-id`、`--idc`、`--pod-name`；推荐先 `--dry-run` 输出请求，再决定是否执行。默认要求交互确认，非交互场景可显式加 `--yes`
- `--ordering` 可选值：`cpu/-cpu/mem/-mem/idc/-idc/createtime/-createtime/podstatus/-podstatus`；`-` 前缀表示倒序，不带 `-` 表示升序
- `tce webshell` 提供 `open/exec/close/interactive` 四个子命令；其中 `open` 先基于 `--psm --env` 建立并持久化会话，`exec` 通过 `--session-id` 执行命令，`close` 删除本地会话，`interactive` 用于完整交互态；执行前需要先通过 `auth login --begin --session --session-method qr --no-terminal-qr` 和 `auth login --complete <token>` 准备本地浏览器态 SSO session。BOE webshell 若返回 SSO HTML 或 `invalid JSON response`，通常需要额外补一次 `--site cn` 的 session。
- `tce webshell exec` 每次会重新建立 websocket，因此不会保留上一次命令的 cwd / export / alias；如果需要完整交互态，仍然使用 `tce webshell interactive`
- `tce webshell exec --otp-stdin` 只从 stdin 读取一行 Seal/飞连 OTP；无 OTP 提示时不会提交该值。Agent 应按 `OTP_REQUIRED → secret input → 同 session 重试` 编排，且不得让 OTP 进入 argv、环境变量、文件、日志或模型对话。`tce webshell interactive --otp-stdin` 仅适用于 TTY：连接前隐藏输入 OTP，连上后 30 秒门禁窗口内看到提示自动提交一次；管道场景用 exec，不要用 interactive。
