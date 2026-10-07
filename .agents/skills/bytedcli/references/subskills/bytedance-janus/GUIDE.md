---
name: bytedance-janus
description: "Manage Janus swimlanes (泳道), IDL versions, API endpoints, backends, config, common args, publish workflows, and groups via bytedcli. Use when tasks mention Janus, Janus BOE/PPE, janus lane create/delete/publish, Janus IDL update, endpoint/backend management, config get, or Janus group search."
---

# bytedcli Janus

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`
- 生产 / PPE 命令使用 ByteDance SSO 登录态；如果登录态过期，执行 `bytedcli auth login`
- BOE 命令使用 BOE/test SSO 登录态；如果只登录过生产环境，先执行 `bytedcli --site boe auth login`
- Janus site 优先遵循 bytedcli 全局站点语义，支持全部 ByteCloud 站点：`cn`、`boe`、`i18n`、`i18n-bd`、`i18n-tt`、`us-ttp`、`us-ttp-bdee`、`us-ttp-usts`、`eu-ttp`；常用全局 `--site cn`（生产 / PPE 网关）或 `--site boe`（China-BOE 网关）；`--site cn --vregion sinf` 访问 SINF 网关；`--site i18n-bd` 默认等价 `--vregion non-tt-sg`，可显式传 `--vregion non-tt-us`，二者走 `cloud.byteintl.net` 并设置 `x-bcgw-cluster`；`--site i18n-bd --vregion sinfi18n` 访问 SINF i18n 网关；BOE i18n 分区使用全局 `--site boei18n` 或全局 `--site boe --vregion boei18n`
- CLI 命令域为 `janus`；所有命令默认走 Janus 网关

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## When to use

- Janus 泳道（swimlane）创建、删除、发布、查询
- Janus group 搜索和信息查询
- 在线配置 / stash 配置查询
- IDL 版本查询和更新
- API endpoint 和 backend 创建/更新
- 查询 common arg

## 鉴权与路由

- Janus 命令使用 ByteCloud JWT 鉴权，不依赖浏览器 Cookie 或 OpenCLI 登录态。
- `--site cn` 使用 ByteDance SSO（`sso.bytedance.com`）登录态，并换取生产站点 ByteCloud JWT。
- 全局 `--site boe` 使用 BOE/test SSO（`test-sso.bytedance.net`）登录态，并换取 China-BOE 站点 ByteCloud JWT；BOE i18n 分区使用全局 `--site boei18n` 或全局 `--site boe --vregion boei18n`。
- 国际站点（`i18n-bd`、`i18n-tt`、`us-ttp`、`eu-ttp` 等）按各自 SSO 与 ByteCloud JWT 解析，登录方式见对应站点 `bytedcli --site <site> auth login`。
- 所有 Janus API 通过 ByteCloud 网关访问，host 按站点解析：`cn` 走 `cloud.bytedance.net`，`cn --vregion sinf` 走 `cloud.sinf.net`，`boe` 走 `cloud-boe.bytedance.net`，`boei18n` 走 `cloud-boei18n.bytedance.net`，`i18n-bd` 默认/`--vregion non-tt-sg` 走 `cloud.byteintl.net` 且带 `x-bcgw-cluster: non-tt-sg`，`i18n-bd --vregion non-tt-us` 走 `cloud.byteintl.net` 且带 `x-bcgw-cluster: non-tt-us`，`i18n-bd --vregion sinfi18n` 走 `cloud-i18n.sinf.net`，`i18n-tt` 默认/`--vregion sg` 走 `cloud-sg.tiktok-row.net`，`i18n-tt --vregion us` 走 `cloud.tiktok-row.net`，`us-ttp` 走 `cloud.tiktok-us.net`，`eu-ttp` 走 `bc-iedt-gw.tiktok-eu.net`。
- 如果 Janus BOE 请求返回 401，先确认命令是否带了 `--site boe`，以及是否已经执行 `bytedcli --site boe auth login`。

## Quick start

Commands are grouped under `janus lane`, `janus group`, `janus config`, `janus idl`, `janus endpoint`, `janus backend`, `janus common-arg`, and `janus publish`.

```bash
# ===== 泳道管理 =====
bytedcli janus lane list --psm example.psm
bytedcli janus lane create --psm example.psm --lane ppe_example_lane --from-lane prod --days 7
bytedcli --site boe janus lane create --psm example.psm --lane boe_example_lane --from-lane prod --days 3
bytedcli janus lane create --psm example.psm --lane ppe_skip_deploy --from-lane prod --days 7 --skip-deploy
bytedcli janus lane delete --psm example.psm --lane ppe_example_lane

# ===== 发布 workflow =====
# 只创建与查询 workflow；bytedcli 不提供 workflow 推进命令，避免 Agent/脚本自动完成发布流水线
bytedcli --json janus publish create --psm example.psm --lane ppe_example_lane
bytedcli janus publish list --psm example.psm --lane ppe_example_lane --workflow-id 123

# ===== Group 管理 =====
bytedcli janus group list --psm example.psm --page-size 50
bytedcli janus group list --mode favorite --page-size 50
bytedcli --site boe --json janus group list --psm example.psm --page-size 50

# ===== 配置管理 =====
bytedcli janus config get --psm example.psm
bytedcli janus config get --psm example.psm --lane ppe_example_lane
# 用控制面导出的完整 ConfigStruct 或直接的完整 ConfigDetailStruct JSON 替换非生产泳道 stash（只写 stash，不创建版本或发布工单）
bytedcli janus config import --psm example.psm --lane ppe_example_lane --config-file ./config.json --confirm-replace-stash

# ===== IDL 版本管理 =====
bytedcli janus idl version list --psm example.psm
bytedcli janus idl update --psm example.psm --lane ppe_example_lane --version 1.0.155 --bam-psm example.backend
bytedcli janus idl method list --psm example.backend --version 1.0.155

# ===== Endpoint 管理 =====
bytedcli janus endpoint create --janus-group example.psm --janus-lane ppe_example_lane --endpoint /api-gateway/svc/method
bytedcli janus endpoint list --janus-group example.psm --janus-lane ppe_example_lane
bytedcli janus endpoint update --id 1 --mid 123 --method POST --endpoint /api/svc/method --janus-group example.psm --janus-lane ppe_example_lane

# ===== Backend 管理 =====
# 创建 Thrift backend
bytedcli janus backend create --eid 123 --protocol thrift --backend-psm demo-thrift.psm --cluster default --idl-version 1.0.0 --rpc-method GetUser --janus-group sample-group.psm --janus-lane ppe_example_lane

# 创建 HTTP backend
bytedcli janus backend create --eid 123 --protocol http --backend-psm demo-http.psm --cluster default --url-pattern /api/test --method GET --janus-group sample-group.psm --janus-lane ppe_example_lane

# 更新 Thrift backend
bytedcli janus backend update --id 456 --eid 123 --protocol thrift --backend-psm demo-thrift.psm --cluster default --idl-version 1.0.0 --rpc-method GetUser --janus-group sample-group.psm --janus-lane ppe_example_lane

# 更新 HTTP backend
bytedcli janus backend update --id 456 --eid 123 --protocol http --backend-psm demo-http.psm --cluster default --url-pattern /api/test --method GET --janus-group sample-group.psm --janus-lane ppe_example_lane

# 查询 common arg
bytedcli janus common-arg get --mid 123 --janus-group example.psm --janus-lane prod
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json janus lane list --psm example.psm`）
- `--site` 表示 Janus 网关站点，不是泳道名或发布环境名。不要把 PPE 这类目标写成 `--site ppe`；这类目标应按平台配置体现在 `--lane` / `--from-lane`，并使用默认 `cn` 站点或显式 `--site cn`
- `lane create` 必须指定 `--from-lane`（源泳道）和 `--days`（TTL 天数）；需要跳过创建后的部署时传 `--skip-deploy`
- `endpoint create` / `backend create` 需要完整的 `--janus-group` 和 `--janus-lane` 上下文字段
- `backend create` / `backend update` 必须显式传 `--protocol thrift|http`；Thrift backend 必须传 `--idl-version` 和 `--rpc-method`，可省略 `--url-pattern` / `--method`（请求体中为 `null`）
- HTTP backend 必须传 `--protocol http`、`--url-pattern` 和 `--method`，不要传 `--idl-version` 或 `--rpc-method`；`--cluster` 默认 `default`，backend `--group` 默认空字符串
- `group list` 分页使用 `--page` / `--page-size`；后端字段名 `count` 不作为 CLI 参数暴露
- `config import` 支持控制面“导出配置”复制出的完整 `ConfigStruct`（自动提取其中的 `detail`），也支持直接的完整 `ConfigDetailStruct`；两种输入都会整份替换目标非生产泳道的 stash，必须显式传 `--confirm-replace-stash`，禁止传 `prod`，且固定走 stash-only OpenAPI，不创建配置版本或发布 workflow
- 完整 `detail` 必须包含 `endpoints`、`idls`、`service_govern`、`idls_ex`、`idls_new`、`idl_from_pod` 六个根字段；Go slice/map/pointer 对应字段允许为 `null`，endpoint/backend、loader、IDL、治理配置及未来未知字段会原样透传；不要传 endpoint-only 局部 patch 或带 `config` 外层的 API response envelope
- `endpoint list` 按 group/lane 返回当前 endpoint 集合，后端接口不暴露分页参数
- `endpoint update` / `common-arg get` 需要 `--mid`（Janus group module ID），可通过 `group list --psm` 查询获取；`common-arg get` 推荐同时传 `--janus-group` 和 `--janus-lane` 补齐请求上下文
- `idl update` 必须显式传 `--bam-psm`，它是要绑定到 Janus group 的 BAM IDL PSM；不要从 `--psm` 推断
- `publish create` 只创建 Janus 发布 workflow，并在 JSON 输出中返回 workflow 信息；它不会自动把 workflow 推进到灰度、全量或完成状态
- `publish list` 用 workflow ID 查询发布工单状态；bytedcli 不提供 workflow 推进接口。
- workflow 推进可能触发灰度、全量、完成等发布流水线动作，Agent 或脚本自动推进存在安全隐患；不要引导用户自动执行发布流水线或自行调用底层 workflow/change 接口。

## References

- `../../troubleshooting.md` — 常见问题与处理
