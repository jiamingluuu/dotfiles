# Bytediff Command Reference

## 鉴权与站点

> ⚠️ **Breaking change / 迁移提示**：bytediff 的默认区域已改为 **CN**（跟随全局 `--site` 默认值 `cn`）。此前不传区域参数、依赖 i18n-sg 默认行为的脚本，必须显式加 `--site i18n-tt`（或目标站点），否则请求会打到 CN host。`--control-panel` 已 deprecated，只有 `case create` / `case update` 仍兼容。

区域由 bytedcli **全局 `--site`（+ `--vregion`）** 决定，默认就是全局默认站点 `cn`，无需任何额外参数。CLI 按站点解析 API host，并按 host 自动解析对应的 ByteCloud SSO JWT（请求头 `x-jwt-token`）与控制台 `origin`/`referer`。

| 全局参数 | API host | 登录方式 |
| - | - | - |
| 默认（等价 `--site cn`） | `https://bytediff.bytedance.net` | `bytedcli auth login` |
| `--site i18n-tt` | `https://bytediff-sg.tiktok-row.org` | `bytedcli --site i18n-tt auth login` |
| `--site i18n-tt --vregion maliva` | `https://bytediff-va.tiktok-row.org` | `bytedcli --site i18n-tt auth login` |
| `--site i18n-bd`（别名 `--site i18n`） | `https://bytediff-i18n.byteintl.net` | `bytedcli --site i18n-bd auth login` |
| `--site eu-ttp` | `https://bytediff-gcp.tiktok-eu.org` | `bytedcli --site eu-ttp auth login` |
| `--site us-ttp` | `https://bytediff-bdee.tiktok-us.org` | `bytedcli --site us-ttp auth login` |

全局参数放在子命令之前，例如 `bytedcli --site i18n-tt bytediff task get --task-id 123456`。bytediff 未部署的站点（如 `--site boe`）会直接报 `BYTEDIFF_INPUT_ERROR`，不会静默回落到 CN。

i18n / TikTok ROW 遇到 401 或缺少 JWT 时，先执行：

```bash
bytedcli --site i18n-tt auth login
```

不要用 CN 登录态判断 Bytediff ROW host 是否可用；反过来，CN 区（默认 site）也不能复用 ROW 登录态，需要 CN ByteCloud 登录（`bytedcli auth login`）。

`case create` / `case update` 仍接受历史的 `--control-panel <i18nsg|i18nva|i18nbd|eu|usbdee|cn>`，但它已 **deprecated**：显式传入会覆盖全局站点并打印一条提示，新用法请统一用全局 `--site`。

## 创建普通 Diff Task

```bash
bytedcli bytediff task create --payload-file ./bytediff-task.json --dry-run
bytedcli bytediff task create --payload-file ./bytediff-task.json --yes
```

- endpoint：`POST /valet/task/diff_task/`
- payload：完整 Bytediff 页面 API JSON body
- 安全边界：不带 `--dry-run` 或 `--yes` 会直接拒绝

## 创建 Traffic Task

```bash
bytedcli bytediff traffic-task create --payload-file ./traffic-task.json --dry-run
bytedcli bytediff traffic-task create --payload-file ./traffic-task.json --yes
```

- endpoint：`POST /valet/task/traffic_task/`
- payload：完整 Bytediff 页面 API JSON body
- 当前未暴露 `traffic-task get`：没有捕获到稳定读取 endpoint；创建后用返回 task id 到 Bytediff 控制台查看，或在确认有 reportsV2 数据时使用 `bytediff report get`

## 创建 AB Test Task

```bash
bytedcli bytediff ab-test create --payload-file ./abtest.json --dry-run
bytedcli bytediff ab-test create --payload-file ./abtest.json --yes
```

- endpoint：`POST /valet/task/abtest/`
- payload：完整 Bytediff AB test API JSON body
- 常见字段包括 `case_id`、`owner`、`data_source_config`、`versions`、`envs_info`，但 CLI 不做字段拆分或默认值填充
- 当前未暴露 `ab-test get`：没有捕获到稳定读取 endpoint；创建后用返回 task id 到 Bytediff 控制台查看，或在确认有 reportsV2 数据时使用 `bytediff report get`

## 查询 Task

```bash
bytedcli bytediff task get --task-id 123456
```

- endpoint：`GET /valet/task/diff_task?id=<taskId>`
- 返回 Bytediff 原始 envelope，适合配合 `--json` 给 agent 继续处理

## 查询 Report

```bash
bytedcli bytediff report get --task-id 123456
bytedcli bytediff report get --task-id 123456 --case-id 123456
```

- endpoint：`GET /valet/reportsV2?task_id=<taskId>&case_id=<caseId>`
- `--case-id` 可选；有具体 case 时建议传入，减少 report 返回歧义

## 查询字段任务详情（Diffy）

```bash
bytedcli bytediff diffy get --task-id 123456
```

- endpoint：`GET /valet/diffyV2/info?task_id=<taskId>`
- 返回字段 diff（diffy）任务的基础详情，适合先确认任务归属再查结果

## 查询字段 Diff 结果（Diffy Result List）

```bash
bytedcli bytediff diffy result list --task-id 123456 --version 0
bytedcli bytediff diffy result list --task-id 123456 --version 0 --endpoint 'POST|/api/foo' --path 'body.field.sub' --page-size 20
```

- endpoint：`GET /valet/diffyV2/results?task_id=<taskId>&version=<version>`
- `--task-id` 与 `--version` 必填；`--version` 是基线/目标版本序号，可为 `0`
- 可选过滤：`--batch-id`、`--endpoint`、`--dimension`、`--path`、`--log-id`、`--is-alias`、`--page-size`、`--cursor`
- 未传的可选过滤不会拼进 query，避免误传空值
- 只传 `--task-id --version` 通常返回空 `results`；字段级明细需要按 endpoint（方法名）+ path（diff 字段路径）定位，推荐先拿 endpoint 与 path 再查：
  1. `--endpoint` 取值形如 `POST|/api/v2/pixel`（method 与 path 用 `|` 连接）；可从 report/控制台或该任务的 endpoint 列表获取
  2. `--path` 是具体 diff 字段路径，如 `body.srcBytes.signal_received_at`
- `--dimension` 是精确匹配后端记录的 `dimension` 字段，多数记录该字段为空；除非明确知道维度值，否则不要传 `--dimension`，否则会过滤成空结果
- 返回结构为 `{results, next_cursor, has_more}`，每条 record 含 `path`、`left`(基线值)、`right`(测试值)、`type`(如 Value)、`log_id`、`universal_path` 等字段级 diff 明细

## 管理测试场景（Case）

对应前端的“测试场景（case）”创建、编辑、查询能力，全部落在 `/valet/case/diff_case`。

### 查询 case 列表

```bash
bytedcli bytediff case list --page 1 --page-size 20
bytedcli bytediff case list --psm demo.service.psm --name demo-scenario --owner demo-user
```

- endpoint：`GET /valet/case/diff_case`
- 可选过滤：`--page`、`--page-size`、`--fuzzy`（模糊匹配）、`--psm`、`--name`、`--owner`
- `--no-full-case` 返回不含指标配置的轻量 case（默认返回完整 case）

### 查询单个 case

```bash
bytedcli bytediff case get --case-id 123456
```

- endpoint：`GET /valet/case/diff_case?id=<caseId>`
- `--case-id` 必填；`--no-full-case` 返回轻量 case

### 创建 case（`case create`）

无需手写完整 JSON。`case create` 用显式 flag 组装 payload，内部复用 `getDiffCase`/`createDiffCase`，支持 `--dry-run` 预览与 `--yes` 提交；区域用全局 `--site`（默认 `cn`），也仍兼容 deprecated 的 `--control-panel`。全新创建直接执行，复制现有场景加 `--copy`。

从头新建（默认，无需任何标志）：

```bash
bytedcli bytediff case create \
  --case-type 冒烟测试 --psm demo.service.psm --case-name demo-brandnew \
  --protocol thrift --label Debug \
  --traffic-source odin --odin-index-id 7068 --qps 10 --press-seconds 180 \
  --metric-config '{"item":"rpc_latency","rate_threshold":"<4"}' \
  --metric-config '{"item":"ERROR","rate_threshold":"<1","abs_threshold":"<=100"}' \
  --dry-run
```

- endpoint：`POST /valet/case/diff_case`
- `--case-type` 必填：`0`/`1`/`3` 或 `接口字段`/`接口统计`/`冒烟测试`；`--psm`、`--case-name` 必填
- `--protocol`：`http`/`0` 或 `thrift`/`1`；`--label` 支持逗号分隔或 JSON 数组
- 流量源二选一：`--traffic-source odin` 必须配 `--odin-index-id`；`--traffic-source tcpcopy` 必须配 `--idc-region` 与 `--cluster`（缺参会报 `BYTEDIFF_INPUT_ERROR`）
- `--metric-config` 可重复：指标别名 `rpc_latency`/`ERROR`/`FATAL`/`CORE`/`TOTAL`，阈值按后端要求的字符串格式原样传入（如 `<4`、`<=100`，CLI 不解析比较符）；内部会按 psm+指标名查 `/valet/indicator/diff_indicator` 补齐 `indicator_id`

复制现有场景（加 `--copy`）：

```bash
bytedcli bytediff case create --copy --source-case-id 123456 --case-name demo-copy --qps 40 --press-seconds 200 --dry-run
```

- endpoint：`POST /valet/case/diff_case`（内部先 `GET` 源 case 再剥壳）
- `--source-case-id`、`--case-name` 必填；会剥掉源 case 的 `id`/`owner`/时间戳等字段，只把 `--qps`/`--press-seconds` 等改动合并进 `data_source_config`

### 修改 case（`case update`）

```bash
bytedcli bytediff case update --case-id 123456 --qps 20 --dry-run
```

- endpoint：`PUT /valet/case/diff_case`（内部先 `GET` 当前 case 再局部覆盖）
- `--case-id` 必填，且至少要改一个字段（`--qps`/`--press-seconds`/`--case-name`/`--label`/`--task-expired-min`）
- 安全边界：不带 `--dry-run` 或 `--yes` 会直接拒绝

### 删除 case

```bash
bytedcli bytediff case delete --case-id 123456 --yes
```

- endpoint：`DELETE /valet/case/diff_case?id=<caseId>`
- `--case-id` 必填；不带 `--yes` 会直接拒绝

## CN 区 ByteDiff（默认 site）

CN 区站点是 `https://bytediff.bytedance.net`，与 i18n 共用同一套 `/valet/*` 契约，但下面这些能力目前只在 CN 区验证过。CN 是全局默认站点，所以下面的命令不需要任何区域参数；同样的命令换区只要在 `bytedcli` 后加全局 `--site`（如 `bytedcli --site i18n-tt bytediff ...`）。

### 查询 diff task 列表

```bash
bytedcli --json bytediff task list --page 1 --page-size 20
bytedcli --json bytediff task list --case-id 123456 --page 1 --page-size 10
bytedcli --json bytediff task list --task-id 123456
```

- endpoint：`GET /valet/task/diff_task`（query：`id`、`case_id`、`page`、`pageSize`）
- `--task-id` 优先级最高，等价于按 task id 精确查
- **分页坑**：后端用 PageHelper，只传 `pageSize` 不传 `page` 时分页整体失效（返回近 14 天最多 1000 条）。CLI 会在只传 `--page-size` 时自动补 `page=1`，并在文本输出里提示（JSON 输出里 `page`/`page_size`/`page_auto_filled` 会显式回填）
- `pageSize` 上限 50，超过会报 `BYTEDIFF_INPUT_ERROR`
- 不带 `page` 时响应 `data` 是数组；带 `page` 时 `data` 是分页对象（`list`/`total`/`pages`/`hasNextPage`）
- **时间窗坑**：不传 `--task-id` 时只覆盖近 14 天，更老的任务必须按 task id 精确查

### 终止 diff task

```bash
bytedcli bytediff task stop --task-id 123456 --dry-run
bytedcli bytediff task stop --task-id 123456 --yes
```

- endpoint：`PUT /valet/task/diff_task/stop`，body `{"id": <taskId>}`
- 写操作：不带 `--dry-run` 或 `--yes` 会报 `BYTEDIFF_CONFIRMATION_REQUIRED`
- 终止后约 15 秒冷却期内不要立刻 `task rerun`

### 重跑 diff task

```bash
bytedcli bytediff task rerun --task-id 123456 --dry-run
bytedcli bytediff task rerun --task-id 123456 --yes
```

- endpoint：`POST /valet/task/diff_task/run`，body `{"id": <taskId>}`
- 写操作：需 `--dry-run` 或 `--yes`
- `code=311`（业务拒绝）与 `code=100`（参数被拒）不要重试，先修任务或参数；`task stop` 之后等约 15 秒再重跑

### 发起冒烟测试任务

```bash
bytedcli bytediff smoke-task create --case-id 123456 --owner demo-user --dry-run
bytedcli bytediff smoke-task create --case-id 123456 --owner demo-user \
  --trigger-type 1 --trigger-source demo-pipeline \
  --envs-info '{"base":{"psm":"demo.service.psm"}}' \
  --data-source-config '{"request_data_type":"odin","qps":10}' \
  --yes
```

- endpoint：`POST /valet/task/smoke_test`
- body 字段：`case_id`(int)、`owner`(string)、`trigger_type`(int)、`trigger_source`(string)、`envs_info`/`data_source_config`/`ab_params`（**string 化 JSON**）
- 复杂字段传 JSON 字符串会原样透传，不会二次编码；不是合法 JSON 会报 `BYTEDIFF_INPUT_ERROR`
- 两种入参模式：字段 flag 模式必须带 `--case-id`；整体 body 模式用 `--payload-file ./smoke.json` / `--payload '<json>'`（`case_id` 写在 body 里，无需 `--case-id`）。两种模式互斥，同时传会报错
- 写操作：需 `--dry-run` 或 `--yes`
- 缺 `--owner` 时会 warn：服务账号身份下任务会没有归属人；个人 token 会用 token 身份覆盖 owner

### 查询 AB 实验关联任务

```bash
bytedcli --json bytediff ab-test get --task-id 123456
bytedcli --json bytediff ab-test get --case-id 123456
```

- endpoint：`GET /valet/task/abtest`（query：`id`、`case_id`、`abtest_id`）
- `--task-id`/`--case-id`/`--abtest-id` 至少给一个，否则报 `BYTEDIFF_INPUT_ERROR`
- **坑**：按 `--abtest-id` 查询会命中服务端 SQL 缺陷，表现为 `code=310`（`unexpected EOF`）或请求长时间挂起直至超时（CN 实测约 20s）；推荐用 `--task-id`

### 查询已登记 PSM 配置

```bash
bytedcli --json bytediff psm get --psm demo.service.psm
bytedcli --json bytediff psm get --psm demo.service --fuzzy --page 1 --page-size 20
```

- endpoint：`GET /valet/psm/psm_info`（query：`psm`、`fuzzy`、`method`、`page`、`pageSize`）
- **坑**：`--method` 是**整数**（服务端只认整数，传接口名会 `code=100`）
- 同样受 PageHelper 影响：只传 `--page-size` 时 CLI 自动补 `page=1`；`pageSize` 上限 50

### 登记新 PSM

```bash
bytedcli bytediff psm create --payload-file ./bytediff-psm.json --dry-run
bytedcli bytediff psm create --payload-file ./bytediff-psm.json --yes
```

- endpoint：`POST /valet/psmV2/psm_info`
- body 字段多且深（`psm`、`owner`、`protocol`、`product_name_space`、`idl_path`、`interfaces` 等），只支持整体 JSON body（`--payload-file` / `--payload`）
- **不可回滚**：ByteDiff 没有删除 PSM 的接口，登记成功后无法自清理，必须先 `--dry-run` 预览再 `--yes`
- 写操作没有幂等键，重复执行会重复登记

### 字段 diff 报表（树形统计）

```bash
bytedcli --json bytediff diffy stats --task-id 123456 --endpoint QueryDemoFeatures --version 1
```

- endpoint：`GET /valet/diffyV2/endpoints/stats`（query：`task_id`、`endpoint`、`version` 必填，可选 `batch_id`、`dimension`）
- **`--endpoint` 是方法名**（如 `QueryDemoFeatures`），不是 URL 路径；先用 `diffy endpoint list` 拿方法名
- 只有**字段 diff 类型**任务才有这份报表，普通任务查会返回 `code=320`（服务端 NPE）
- **别传 `--batch-id 0`**：服务端会 NPE，CLI 会先拦下来报 `BYTEDIFF_INPUT_ERROR`；非数字的 batch id（如 `0abc`）也会被同一处校验拦掉；不需要就不要传

### 列出任务可用 endpoint（方法名）

```bash
bytedcli --json bytediff diffy endpoint list --task-id 123456 --version 1
```

- endpoint：`GET /valet/diffyV2/endpoints`（query：`task_id`、`version`）
- 返回的方法名直接用作 `diffy stats --endpoint`

### CN 区业务错误码

| code | 含义 | 处理 |
| - | - | - |
| `0` | 成功 | - |
| `100` | 参数被拒，且常常没有 `msg` | 线索看 `data.explainMsg` / `data.oncallUrl`，修参数后再试（不要盲重试） |
| `101` | 缺必填参数 | 补齐必填 flag |
| `103` | token 缺失 / 失效 | 重新登录对应站点（CN：`bytedcli auth login`） |
| `310` | 服务端 SQL 异常（如按 `abtest_id` 查 AB 任务） | 换查询维度，例如改用 `--task-id` |
| `311` | 业务拒绝 | **不要重试**，先确认任务状态 / 业务前置条件 |
| `320` | 服务端 NPE（如对普通任务查字段 diff 报表） | 确认任务类型与参数；`--batch-id 0` 已被 CLI 提前拦截 |

### CN 区排障速查

通用登录 / site 隔离问题见 `references/troubleshooting.md`；下面是 ByteDiff CN 特有的坑（均来自线上实测）：

| 现象 | 原因 | 处理 |
| - | - | - |
| 列表条数远超预期、`page` 不生效 | 后端 PageHelper：只传 `pageSize` 不传 `page` 时分页整体失效（近 14 天最多 1000 条） | `--page` 与 `--page-size` 成对传；只传 `--page-size` 时 CLI 自动补 `page=1`（JSON 看 `page_auto_filled`） |
| 查不到几周前的任务 | `task list` 不传 `--task-id` 只覆盖近 14 天 | 按 task id 精确查：`bytediff task list --task-id 123456` |
| `ab-test get` 返回 `code=310`（`unexpected EOF`）或请求超时 | 按 `abtest_id` 查询命中服务端 SQL 缺陷 | 改用 `--task-id` |
| `diffy stats` 返回 `code=320` | 非字段 diff 类型任务没有该报表 | 确认任务类型；不需要 batch 就不要传 `--batch-id`（传 `0` 会被 CLI 拦截） |
| `diffy stats` 报参数错误 | `--endpoint` 传了 URL 路径 | 传方法名，先用 `diffy endpoint list` 获取 |
| `psm get` 返回 `code=100` | `--method` 传了接口名 | `--method` 只接受整数 |
| `task rerun` 紧跟 `task stop` 后失败 | 终止有约 15 秒冷却期 | 等约 15 秒再重跑；`code=311`/`100` 不要盲重试 |
| 重复执行写命令产生重复数据 | ByteDiff 写接口没有幂等键 | 先 `--dry-run` 预览，再 `--yes` 提交一次 |
| `psm create` 建错了想删 | ByteDiff 没有删除 PSM 的接口 | **不可回滚**，提交前必须 `--dry-run` 核对 payload |
| 任务没有归属人 | 服务账号身份下未显式指定 owner | `smoke-task create` 带 `--owner`（缺失时 CLI 会 warn）；个人 token 会用 token 身份覆盖 owner |
