---
name: bytedance-janus-mini
description: "Manage Janus Mini swimlanes (泳道), IDL versions, API endpoints, backends, config, and groups via bytedcli. Use when tasks mention Janus Mini, Janus Mini BOE, swimlane, lane create/delete/publish, IDL version update, endpoint management, backend service, config get, or Janus Mini group search."
---

# bytedcli Janus Mini

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`
- 生产 / PPE 命令使用 ByteDance SSO 登录态；如果登录态过期，执行 `bytedcli auth login`
- BOE 命令使用 BOE/test SSO 登录态；如果只登录过生产环境，先执行 `bytedcli --site boe auth login`
- Janus Mini site 优先遵循 bytedcli 全局站点语义，支持全部 ByteCloud 站点：`cn`、`boe`、`i18n`、`i18n-bd`、`i18n-tt`、`us-ttp`、`us-ttp-bdee`、`us-ttp-usts`、`eu-ttp`；常用全局 `--site cn`（生产 / PPE 网关）或 `--site boe`（China-BOE 网关）；`--site cn --vregion sinf` 访问 SINF 网关；`--site i18n-bd` 默认等价 `--vregion non-tt-sg`，可显式传 `--vregion non-tt-us`，二者走 `cloud.byteintl.net` 并设置 `x-bcgw-cluster`；`--site i18n-bd --vregion sinfi18n` 访问 SINF i18n 网关；BOE i18n 分区使用全局 `--site boei18n` 或全局 `--site boe --vregion boei18n`；`prod`、`row`、`usttp` 等作为兼容别名，不在新示例中推荐
- CLI 命令域为 `janus-mini`；所有命令默认走 Janus Mini 网关
- `--mini` 是兼容旧调用的 no-op，不需要主动添加

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## When to use

- 泳道（swimlane）创建、删除、发布、查询
- Janus Mini group 搜索和信息查询
- 在线配置 / stash 配置查询
- IDL 版本查询和更新
- API endpoint 和 backend 创建/更新
- 查询 BAM IDL 版本和方法列表

## 鉴权与路由

- Janus Mini 命令使用 ByteCloud JWT 鉴权，不依赖浏览器 Cookie 或 OpenCLI 登录态。
- `--site cn` 使用 ByteDance SSO（`sso.bytedance.com`）登录态，并换取生产站点 ByteCloud JWT；旧脚本里的 `--site prod` 会兼容映射到 `cn`。
- 全局 `--site boe` 使用 BOE/test SSO（`test-sso.bytedance.net`）登录态，并换取 China-BOE 站点 ByteCloud JWT；BOE i18n 分区使用全局 `--site boei18n` 或全局 `--site boe --vregion boei18n`。
- 国际站点（`i18n-bd`、`i18n-tt`、`us-ttp`、`eu-ttp` 等）按各自 SSO 与 ByteCloud JWT 解析，登录方式见对应站点 `bytedcli --site <site> auth login`。
- 操作生产 / PPE 网关前可用 `bytedcli auth status` 检查登录态；过期时执行 `bytedcli auth login`。
- 操作其他站点前可用 `bytedcli --site <site> auth status` 检查登录态；过期时执行 `bytedcli --site <site> auth login`。
- 所有 Janus Mini API 通过 ByteCloud 网关访问，host 按站点解析：`cn` 走 `cloud.bytedance.net`，`cn --vregion sinf` 走 `cloud.sinf.net`，`boe` 走 `cloud-boe.bytedance.net`，`boei18n` 走 `cloud-boei18n.bytedance.net`，`i18n-bd` 默认/`--vregion non-tt-sg` 走 `cloud.byteintl.net` 且带 `x-bcgw-cluster: non-tt-sg`，`i18n-bd --vregion non-tt-us` 走 `cloud.byteintl.net` 且带 `x-bcgw-cluster: non-tt-us`，`i18n-bd --vregion sinfi18n` 走 `cloud-i18n.sinf.net`，`i18n-tt` 默认/`--vregion sg` 走 `cloud-sg.tiktok-row.net`，`i18n-tt --vregion us` 走 `cloud.tiktok-row.net`，`us-ttp` 走 `cloud.tiktok-us.net`，`eu-ttp` 走 `bc-iedt-gw.tiktok-eu.net`。
- 如果 Janus Mini BOE 请求返回 401，先确认命令是否带了 `--site boe`，以及是否已经执行 `bytedcli --site boe auth login`。

## Quick start

Commands are grouped under `janus-mini lane`, `janus-mini group`, `janus-mini config`, `janus-mini idl`, `janus-mini endpoint`, and `janus-mini backend`.

```bash
# ===== 泳道管理 =====
# 列出某 PSM 的所有泳道
bytedcli janus-mini lane list --psm example.psm

# 创建泳道（从 master 复制，7 天 TTL）
bytedcli janus-mini lane create --psm example.psm --lane ppe_example_lane --from-lane master --days 7

# 在 BOE 创建泳道
bytedcli --site boe janus-mini lane create --psm example.psm --lane boe_example_lane --from-lane prod --days 3
bytedcli janus-mini lane create --psm example.psm --lane ppe_skip_deploy --from-lane prod --days 7 --skip-deploy

# 删除泳道
bytedcli janus-mini lane delete --psm example.psm --lane ppe_example_lane

# 创建发布 workflow（不代表发布已经完成）
# 只创建与查询 workflow；bytedcli 不提供 workflow 推进命令，避免 Agent/脚本自动完成发布流水线
bytedcli --json janus-mini publish create --psm example.psm --lane ppe_example_lane

# 查询发布 workflow
bytedcli janus-mini publish list --psm example.psm --lane ppe_example_lane --workflow-id 123

# ===== Group 管理 =====
# 搜索 group（收藏 / 全部）
bytedcli janus-mini group list --psm example.psm
bytedcli janus-mini group list --mode favorite
bytedcli --site cn --json janus-mini group list --psm example.psm --page-size 20
bytedcli --site boe --json janus-mini group list --psm example.psm --page-size 20
bytedcli --json janus-mini group get --psm example.psm

# ===== 配置管理 =====
# 查询线上配置（默认 lane=prod）
bytedcli janus-mini config get --psm example.psm

# 查询泳道 stash 配置
bytedcli janus-mini config get --psm example.psm --lane ppe_example_lane

# 用控制面导出的完整 ConfigStruct 或直接的完整 ConfigDetailStruct JSON 替换非生产泳道 stash（只写 stash，不创建版本或发布工单）
bytedcli janus-mini config import --psm example.psm --lane ppe_example_lane --config-file ./config.json --confirm-replace-stash

# ===== IDL 版本管理 =====
# 查询 BAM IDL 版本列表
bytedcli janus-mini idl version list --psm example.psm

# 更新泳道 IDL 版本
bytedcli janus-mini idl update --psm example.psm --lane ppe_example_lane --version 1.0.155

# 查询 Janus Mini group 当前绑定 IDL 的方法
bytedcli janus-mini idl method list --psm example.psm

# ===== Endpoint 管理 =====
# 创建 endpoint
bytedcli janus-mini endpoint create --janus-group example.psm --janus-lane ppe_example_lane --endpoint /api-gateway/svc/method

# 查询泳道内 endpoint
bytedcli janus-mini endpoint list --janus-group example.psm --janus-lane ppe_example_lane

# 更新 endpoint
bytedcli janus-mini endpoint update --id 1 --mid 123 --method POST --endpoint /api/svc/method --janus-group example.psm --janus-lane ppe_example_lane

# ===== Backend 管理 =====
# 创建 thrift group 的 backend（协议自动跟随 group service_type）
bytedcli janus-mini backend create --eid 123 --idl-version 1.0.0 --rpc-method GetUser --backend-psm example-backend.psm --janus-group example-group.psm --janus-lane ppe_example_lane

# 创建 HTTP group 的 backend（协议自动跟随 group service_type）
bytedcli janus-mini backend create --eid 123 --url-pattern /api/test --method GET --backend-psm example-backend.psm --janus-group example-group.psm --janus-lane ppe_example_lane

# 更新 thrift group 的 backend
bytedcli janus-mini backend update --id 456 --eid 123 --idl-version 1.0.0 --rpc-method GetUser --backend-psm example-backend.psm --janus-group example-group.psm --janus-lane ppe_example_lane

# 更新 HTTP group 的 backend
bytedcli janus-mini backend update --id 456 --eid 123 --url-pattern /api/test --method GET --backend-psm example-backend.psm --janus-group example-group.psm --janus-lane ppe_example_lane

# 查询 common arg
bytedcli janus-mini common-arg get --mid 123 --janus-group example.psm --janus-lane prod
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json janus-mini lane list --psm example.psm`）
- Janus Mini site 支持全部 ByteCloud 站点（`cn`/`boe`/`i18n`/`i18n-bd`/`i18n-tt`/`us-ttp`/`us-ttp-bdee`/`us-ttp-usts`/`eu-ttp`）；不传时继承全局 `--site` / `BYTEDCLI_CLOUD_SITE`，`prod` 等作为兼容别名映射到对应站点；BOE i18n 分区使用全局 `--site boei18n` 或全局 `--site boe --vregion boei18n`
- `--site` 表示 Janus Mini 网关站点，不是泳道名或发布环境名。不要把 PPE 这类目标写成 `--site ppe`；这类目标应按平台配置体现在 `--lane` / `--from-lane`，并使用默认 `cn` 站点或显式 `--site cn`
- `lane create` 必须指定 `--from-lane`（源泳道）和 `--days`（TTL 天数）；需要跳过创建后的部署时传 `--skip-deploy`；命令提交创建请求后返回，endpoint 会从源泳道异步复制。用 `lane list` 查看 `pipeline_run_status`（8 表示复制 pipeline 完成），用 `endpoint list` 查看目标泳道 endpoint 是否已经可见
- 创建泳道后，在 endpoint 复制完成前不要假设目标泳道配置已经稳定；需要新增或修改 endpoint/backend 时，先确认 `pipeline_run_status` 已完成且 `endpoint list` 能看到预期配置，避免后台复制结果覆盖提前写入的配置
- `endpoint create` / `backend create` 需要完整的 `--janus-group` 和 `--janus-lane` 上下文字段
- `backend create` / `backend update` 的协议自动跟随 `group get` 返回的 `service_type`；thrift group 需要 `--idl-version` / `--rpc-method`，HTTP group 需要 `--url-pattern` / `--method`，不确定时先执行 `janus-mini group get --psm example.psm`
- `group list` 分页使用 `--page` / `--page-size`；后端字段名 `count` 不作为 CLI 参数暴露
- `idl update` 不需要 `--bam-psm`；Janus Mini 后端会从 group metadata 解析 IDL 绑定
- `config import` 支持控制面“导出配置”复制出的完整 `ConfigStruct`（自动提取其中的 `detail`），也支持直接的完整 `ConfigDetailStruct`；两种输入都会整份替换目标非生产泳道的 stash，必须显式传 `--confirm-replace-stash`，禁止传 `prod`，且固定走 stash-only OpenAPI，不创建配置版本或发布 workflow
- 完整 `detail` 必须包含 `endpoints`、`idls`、`service_govern`、`idls_ex`、`idls_new`、`idl_from_pod` 六个根字段；Go slice/map/pointer 对应字段允许为 `null`，endpoint/backend、loader、IDL、治理配置及未来未知字段会原样透传；不要传 endpoint-only 局部 patch 或带 `config` 外层的 API response envelope
- `endpoint list` 按 group/lane 返回当前 endpoint 集合，后端接口不暴露分页参数
- `endpoint update` / `common-arg get` 需要 `--mid`（Janus Mini group module ID），可通过 `group list --psm` 查询获取；`common-arg get` 推荐同时传 `--janus-group` 和 `--janus-lane` 补齐请求上下文
- `publish create` 只创建 Janus Mini 发布 workflow，并在 JSON 输出中返回 `data.data.workflow.wid`；它不会自动把 workflow 推进到灰度、全量或完成状态
- `publish list` 用上一步返回的 workflow ID 查询发布工单状态；bytedcli 不提供 workflow 推进接口。
- `publish list` 返回的 `deploy_status`：0=无需部署, 1=部署中, 2=部署完成；仅当 `status=5` 且 `deploy_status=2` 且 `failed_reason` 为空时发布完成
- workflow 推进可能触发灰度、全量、完成等发布流水线动作，Agent 或脚本自动推进存在安全隐患；不要引导用户自动执行发布流水线或自行调用底层 workflow/change 接口。
- Agent/脚本场景优先使用 `--json`，从 `data.data.workflow.wid` 读取 workflow ID，再调用 `publish list` 查询状态
- 缺少必填参数会自动输出帮助信息

## References

- `../../troubleshooting.md` — 常见问题与处理
