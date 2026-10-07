---
name: bytedance-bytediff
description: "Operate Bytediff via bytedcli: create diff tasks, traffic tasks, AB test tasks, smoke test tasks, list/stop/rerun diff tasks, read AB test tasks, query and register PSM configs, read field-diff endpoint lists and stats reports, manage test scenarios (cases) including create/update/delete from explicit flags, where copy uses the `case create --copy` flag and edit maps to `case update`, and query task/report/field-diff responses. Region follows the global `--site` (default `cn`); i18n / TikTok ROW / EU / US deployments are reached with `--site i18n-tt` / `i18n-bd` / `eu-ttp` / `us-ttp`. Use when tasks mention Bytediff, bytediff task, diff_task, traffic_task, smoke_test, AB test diff, /valet/task/abtest, /valet/task/diff_task, /valet/psm/psm_info, /valet/psmV2/psm_info, /valet/diffyV2/endpoints, /valet/case/diff_case, test scenario, case create/update/delete, `case create --copy`, case update, control panel, CN ByteDiff, traffic source odin/tcpcopy, metric config, reportsV2, diffyV2, or field diff results."
---

# bytedcli Bytediff

通过 bytedcli 调用 Bytediff API，覆盖 diff task、traffic task、AB test task 创建，测试场景（case）管理，以及 task/report/字段 diff 查询。

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

临时环境无法安装时再用 npx：

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When To Use

- 创建普通 Bytediff diff task：`bytediff task create`
- 查询普通 Bytediff diff task：`bytediff task get`
- 查询 diff task 列表：`bytediff task list`
- 终止 / 重跑 diff task：`bytediff task stop` / `bytediff task rerun`
- 创建 Bytediff traffic task：`bytediff traffic-task create`
- 发起冒烟测试任务：`bytediff smoke-task create`
- 创建 Bytediff AB test task：`bytediff ab-test create`
- 查询 AB 实验关联任务：`bytediff ab-test get`
- 查询 Bytediff report：`bytediff report get`
- 查询字段任务详情：`bytediff diffy get`
- 查询字段 diff 结果：`bytediff diffy result list`
- 查询字段 diff 报表（树形统计）：`bytediff diffy stats`
- 列出任务可用 endpoint（方法名）：`bytediff diffy endpoint list`
- 查询 / 登记 PSM 配置：`bytediff psm get` / `bytediff psm create`
- 管理测试场景（case）：`bytediff case list` / `get` / `create` / `update` / `delete`
- 用显式参数创建场景（无需手写 JSON）：`bytediff case create`（从头建）/ `create --copy`（复制现有）；改字段用 `bytediff case update --case-id`
- 操作 CN 区 ByteDiff：默认即 CN，无需任何区域参数
- 操作 i18n / ROW 等海外区 ByteDiff：全局 `--site`，如 `bytedcli --site i18n-tt bytediff ...`

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- ⚠️ **Breaking change（迁移提示）**：bytediff 的默认区域现在是 **CN**（跟随全局 `--site` 默认值 `cn`）。此前不传任何区域参数、依赖 i18n-sg 默认行为的脚本，必须显式加 `--site i18n-tt`（或所需站点），否则请求会打到 CN host。
- 区域由 **bytedcli 全局 `--site`** 决定（与 argos / tce 等 domain 一致），默认就是 `cn`。
- **CN 区（默认）**：host 是 `https://bytediff.bytedance.net`，走 CN ByteCloud SSO JWT（请求头 `x-jwt-token`）；未登录时执行 `bytedcli auth login`。无需任何额外参数。
- **i18n / TikTok ROW 等海外区**：加全局 `--site`，如 `bytedcli --site i18n-tt bytediff ...`（`bytediff-sg.tiktok-row.org`）；Virginia 再加 `--vregion maliva`（`bytediff-va.tiktok-row.org`）。其它可选：`--site i18n-bd`（`bytediff-i18n.byteintl.net`）、`--site eu-ttp`（`bytediff-gcp.tiktok-eu.org`）、`--site us-ttp`（`bytediff-bdee.tiktok-us.org`）。鉴权按 host 走，需用同一站点登录：`bytedcli --site i18n-tt auth login`，CN 登录态不适用于这些 host。
- bytediff 未部署的站点（如 `--site boe`）会直接报 `BYTEDIFF_INPUT_ERROR`，不会静默回落到 CN。

## Quick Start

```bash
# 创建普通 diff task：先预览完整 payload
bytedcli bytediff task create --payload-file ./bytediff-task.json --dry-run

# 确认后提交普通 diff task
bytedcli bytediff task create --payload-file ./bytediff-task.json --yes

# 创建 traffic task
bytedcli bytediff traffic-task create --payload-file ./traffic-task.json --dry-run

# 创建 AB test task
bytedcli bytediff ab-test create --payload-file ./abtest.json --dry-run
bytedcli bytediff ab-test create --payload-file ./abtest.json --yes

# 查询任务与 report
bytedcli bytediff task get --task-id 123456
bytedcli bytediff report get --task-id 123456 --case-id 123456

# 查询字段任务详情与字段 diff 结果（diffyV2）
bytedcli bytediff diffy get --task-id 123456
bytedcli bytediff diffy result list --task-id 123456 --version 0
bytedcli bytediff diffy result list --task-id 123456 --version 0 --endpoint 'POST|/api/foo' --path 'body.field.sub' --page-size 20

# 管理测试场景（case）：查询、创建、修改、删除
bytedcli bytediff case list --psm demo.service.psm --name demo-scenario
bytedcli bytediff case get --case-id 123456
bytedcli bytediff case delete --case-id 123456 --yes

# 用显式参数管理场景（无需手写 JSON），全新创建直接 case create
bytedcli bytediff case create --case-type 冒烟测试 --psm demo.service.psm --case-name demo-brandnew --protocol thrift --traffic-source odin --odin-index-id 7068 --qps 10 --press-seconds 180 --metric-config '{"item":"rpc_latency","rate_threshold":"<4"}' --dry-run
# 复制现有场景：加 --copy + --source-case-id
bytedcli bytediff case create --copy --source-case-id 123456 --case-name demo-copy --qps 40 --dry-run
# 修改现有场景的字段
bytedcli bytediff case update --case-id 123456 --qps 20 --dry-run
```

### CN 区（默认 site，无需区域参数）

```bash
# 任务列表：page-size 必须配 page（只传 page-size 时 CLI 会自动补 page 1）
bytedcli --json bytediff task list --page 1 --page-size 20
bytedcli --json bytediff task list --task-id 123456

# 终止 / 重跑任务（写操作，默认不提交）
bytedcli bytediff task stop --task-id 123456 --dry-run
bytedcli bytediff task stop --task-id 123456 --yes
bytedcli bytediff task rerun --task-id 123456 --yes

# 发起冒烟测试任务（复杂字段是 string 化 JSON，原样透传）
bytedcli bytediff smoke-task create --case-id 123456 --owner demo-user \
  --trigger-type 1 --trigger-source demo-pipeline \
  --envs-info '{"base":{"psm":"demo.service.psm"}}' --dry-run

# 查询 AB 实验关联任务（推荐用 task id）
bytedcli --json bytediff ab-test get --task-id 123456

# PSM 配置：查询 / 登记（登记不可回滚）
bytedcli --json bytediff psm get --psm demo.service.psm
bytedcli --json bytediff psm get --psm demo.service --fuzzy --page 1 --page-size 20
bytedcli bytediff psm create --payload-file ./bytediff-psm.json --dry-run

# 字段 diff 报表：先拿方法名，再查报表
bytedcli --json bytediff diffy endpoint list --task-id 123456 --version 1
bytedcli --json bytediff diffy stats --task-id 123456 --endpoint QueryDemoFeatures --version 1
```

## Agent Guidance

- **创建类命令只接受完整 JSON body**：Bytediff 创建体是页面 API 的原始结构，字段深且场景差异大。优先从浏览器/curl/API payload 保存成 JSON 文件，再传 `--payload-file <path>`；小 payload 才用 `--payload '<json>'`。
- **写操作确认**：`task create`、`traffic-task create`、`ab-test create`、`smoke-task create`、`psm create`、`task stop`、`task rerun` 默认不会提交。先用 `--dry-run` 看 endpoint 和 payload；真实执行必须传 `--yes`。
- **查询边界**：`traffic-task` 暂只暴露 `create`，因为还没有捕获到稳定的读取 endpoint；创建后用返回的 task id 到 Bytediff 控制台查看，或在确认有 reportsV2 数据时使用 `bytediff report get`。
- **已确认 endpoint**：
  - 普通 diff task：`POST /valet/task/diff_task/`
  - traffic task：`POST /valet/task/traffic_task/`
  - AB test task：`POST /valet/task/abtest/`
  - task 查询：`GET /valet/task/diff_task?id=<taskId>`
  - task 列表：`GET /valet/task/diff_task`（`id`/`case_id`/`page`/`pageSize`）
  - task 重跑 / 终止：`POST /valet/task/diff_task/run`、`PUT /valet/task/diff_task/stop`（body 均为 `{"id": <taskId>}`）
  - 冒烟测试任务：`POST /valet/task/smoke_test`
  - AB 实验关联任务：`GET /valet/task/abtest`（`id`/`case_id`/`abtest_id`）
  - report 查询：`GET /valet/reportsV2?task_id=<taskId>&case_id=<caseId>`
  - 字段任务详情：`GET /valet/diffyV2/info?task_id=<taskId>`
  - 字段 diff 结果：`GET /valet/diffyV2/results?task_id=<taskId>&version=<version>`（可选过滤：`batch_id`、`endpoint`、`dimension`、`path`、`log_id`、`is_alias`、`limit`、`cursor`）
  - 字段 diff 报表：`GET /valet/diffyV2/endpoints/stats`（`task_id`/`endpoint`/`version` 必填，可选 `batch_id`/`dimension`）
  - 任务 endpoint 列表：`GET /valet/diffyV2/endpoints?task_id=<taskId>&version=<version>`
  - PSM 配置：`GET /valet/psm/psm_info`、`POST /valet/psmV2/psm_info`
  - 测试场景（case）：`GET/POST/PUT/DELETE /valet/case/diff_case`（list/create/update/delete；get 用 `?id=<caseId>`，delete 用 `?id=<caseId>`）
- **测试场景（case）管理**：对应前端“测试场景”的创建、修改、查询。`case create`/`case update` 用显式 flag 组装 payload，无需手写完整 JSON，默认不提交，需 `--dry-run` 或 `--yes`。`case delete` 需 `--case-id` + `--yes`。
- **显式参数管理场景**：全新创建直接 `case create`（从头建，无需任何标志）；复制现有场景加 `--copy --source-case-id <id>`；`case update` 用 `--case-id` 只改传入的字段（内部复用 `getDiffCase`/`createDiffCase`/`updateDiffCase`）。都支持 `--dry-run`/`--yes`；区域用全局 `--site`（默认 `cn`），这两个命令还保留了 deprecated 的 `--control-panel`（旧用法兼容，会提示改用 `--site`）。全新创建时 `--case-type` 用 `冒烟测试`/`接口字段`/`接口统计`（或 `3`/`0`/`1`），流量源 `--traffic-source odin` 必须带 `--odin-index-id`，`--traffic-source tcpcopy` 必须带 `--idc-region`+`--cluster`（缺参会报 `BYTEDIFF_INPUT_ERROR`），`--metric-config` 可重复且内部会查 `/valet/indicator/diff_indicator` 补 `indicator_id`。`--copy` 只需 `--source-case-id`+`--case-name`，会自动剥掉源 case 的 id/owner 等字段。`case update` 需 `--case-id` 且至少改一个字段。具体见 `references/bytediff.md`。
- **字段 diff 结果取数**：`diffy result list` 只传 `--task-id --version` 常返回空；字段级明细需按 `--endpoint`（形如 `POST|/api/v2/pixel`）+ `--path`（如 `body.srcBytes.signal_received_at`）定位。`--dimension` 是精确匹配、多数记录为空，除非确知维度值否则不要传，否则会过滤成空。
- **JSON 输出**：`--json` 是全局参数，放在命令前，例如 `bytedcli --json bytediff report get --task-id 123456`。
- **生产网络 403 / OG 拒绝**：仅当 Bytediff 在已确认的生产网络中返回与生产网络或 OG 拒绝相关的 403 时，先检查当前 shell 是否设置 `BYTEDCLI_NETWORK_PROFILE=prod`；办公网络不要设置该变量。此检查不能替代目标站点登录、权限或参数排查，也不要在未确认网络环境时反复切换该变量。
- **CN 区实测踩坑（必读，默认站点即 CN）**：
  1. **分页**：列表接口用 PageHelper，只传 `pageSize` 不传 `page` 时分页整体失效（返回近 14 天最多 1000 条）。CLI 会在只传 `--page-size` 时自动补 `page=1` 并在输出里提示；不带 `page` 时响应 `data` 是数组，带 `page` 时是分页对象（`data.list`/`total`/`pages`/`hasNextPage`）。`pageSize` 上限 50。
  2. **时间窗**：`task list` 不传 `--task-id` 只覆盖近 14 天，更老的任务必须按 task id 精确查。
  3. **AB 任务**：按 `--abtest-id` 查询会命中服务端 SQL 缺陷（`code=310`，`unexpected EOF`；也可能一直挂起到超时），推荐用 `--task-id`。
  4. **字段 diff 报表**：`diffy stats --endpoint` 是方法名（如 `QueryDemoFeatures`），先用 `diffy endpoint list` 拿；只有字段 diff 类型任务有该报表，普通任务会返回 `code=320`（服务端 NPE）；`--batch-id 0` 会让服务端 NPE，CLI 直接拦掉（报 `BYTEDIFF_INPUT_ERROR`），非数字的 batch id（如 `0abc`）同样会被拦掉，不需要就别传。
  5. **PSM 查询**：`psm get --method` 是整数（服务端只认整数，传接口名会 `code=100`）。
  6. **冷却期**：`task stop` 之后约 15 秒内不要立刻 `task rerun`。
  7. **无幂等键**：写操作没有幂等键（`case create` 连跑两次会建两个 case）；ByteDiff 没有删除 PSM 的接口，`psm create` 成功后不可回滚，所以务必先 `--dry-run` 再 `--yes`。
  8. **归属人**：服务账号身份下创建任务必须显式 `--owner`，否则任务没有归属人；个人 token 会用 token 身份覆盖 owner。
  9. **业务错误码**：`0` 成功；`100` 参数被拒且常常无 msg（线索在 `data.explainMsg` / `data.oncallUrl`）；`101` 缺必填参数；`103` token 缺失/失效；`310` 服务端 SQL 异常；`311` 业务拒绝（不要重试）；`320` 服务端 NPE。

更多示例见 `references/bytediff.md`。
