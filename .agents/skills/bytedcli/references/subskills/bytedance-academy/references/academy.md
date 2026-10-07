# Academy

支撑文档：本文件给 SKILL.md 当详细参考，SKILL.md 已经覆盖最常用的调用方式与参数表，这里补充控制台对照、参数语义、草稿保存、翻页与示例细节。

## 平台定位

Academy 用于广告特征开发与管理。本 skill 覆盖 3 条检索能力、raw feature set 草稿保存、取版本代码、编译、调试、调试状态查询、提交上线、版本代码 diff、待审核工单查询、Lark 群通知，以及调度配置查询（框架版本 / 队列 / 任务参数模板 / dorado 依赖）和用户 on-call 管理员查询：

- source_v2 数据源搜索（控制台 → Academy / Datasource）
- raw feature set group 搜索（控制台 → Academy / Feature Engineering / Offline）
- raw feature set 草稿保存（后端 `POST /v2/raw_feature_set/{id}/draft`）
- raw feature set 取版本代码（后端 `GET /v2/raw_feature_set/{id}/version/{version}`，-1=草稿/最新）
- raw feature set 编译（后端 `PUT /v2/raw_feature_set/{id}/version/{version}/compile_all`，含调度设置中所有 Region）
- raw feature set 调试（后端 `PUT /v2/raw_feature_set/{id}/version/{version}/debug`）
- raw feature set 调试详情 / 状态（后端 `GET /v2/raw_feature_set/debug/{debugId}/detail`）
- raw feature set 数据源授权校验（后端 `POST /v2/raw_feature_set/{id}/verify-privilege`）
- raw feature set 提交上线 / 预上线（后端 `PUT /v2/raw_feature_set/{id}/online`）
- raw feature set 版本代码 diff（后端 `GET /v2/raw_feature_set/{id}/code_diff`）
- raw feature set 待审核工单查询（后端 `GET /v2/raw_feature_set/{id}/order/active`）
- Lark 群确认消息（后端 `POST /v2/raw_feature_set/confirm/lark`）
- 框架版本列表（后端 `GET /v2/raw_feature_set/framework_version/list`）
- 用户可用队列列表（后端 `GET /v2/raw_feature_set/queue/list`）
- 调度 taskConf 模板（后端 `GET /v2/raw_feature_set/task_conf/template`）
- dorado 依赖任务信息（后端 `GET /v2/raw_feature_set/dorado_task/{task_id}`）
- feature 搜索（控制台 → Academy / Feature Engineering / Online）
- 管理员 on-call 轮值成员列表（后端 `GET /user/admin/search`）
- 当前在班 on-call 管理员列表（后端 `GET /user/admin/on_call`）

除上述已接入能力外，其他写操作和详情接口暂未接入。

## 命令清单

```bash
bytedcli academy source search ...
bytedcli academy raw-feature-set group search ...
bytedcli academy raw-feature-set draft save ...
bytedcli academy raw-feature-set version get ...
bytedcli academy raw-feature-set compile ...
bytedcli academy raw-feature-set debug ...
bytedcli academy raw-feature-set debug-detail get ...
bytedcli academy raw-feature-set verify-privilege ...
bytedcli academy raw-feature-set submit-online ...
bytedcli academy raw-feature-set code-diff get ...
bytedcli academy raw-feature-set active-order get ...
bytedcli academy raw-feature-set confirm-lark ...
bytedcli academy raw-feature-set framework-version list ...
bytedcli academy raw-feature-set queue list ...
bytedcli academy raw-feature-set task-conf template get ...
bytedcli academy raw-feature-set dorado-task get ...
bytedcli academy feature search ...
bytedcli academy user admin-search ...
bytedcli academy user on-call ...
```

参数表见 [`SKILL.md`](../SKILL.md#commands)。本文件下面只补示例与控制台对照。

## API origin and authentication

All Academy commands use the MLDP API service, including the default `cn` site.
The same origins serve `/api/academy` and `/api/lineage`.

| Network | API origin |
| --- | --- |
| Office | `https://mldp-oc-api-service.tiktok-row.net` |
| `BYTEDCLI_NETWORK_PROFILE=prod` | `https://mldp-oc-api-service.byteintl.net` |

- Use raw ByteCloud JWT authentication in `X-Jwt-Token`, without Titan exchange
  or passport cookies. Academy uses `i18n-tt` authentication unless the selected
  site already belongs to TikTok SSO (such as `us-ttp` or `eu-ttp`).
- `--base-url` takes precedence over `ACADEMY_BASE_URL`, then the network default;
  both overrides must use one of the two MLDP HTTPS origins.
- Treat console URLs as resource references. Never call Academy APIs through
  `oceancloud.tiktok-row.net`, including direct HTTP requests for missing CLI
  endpoints. Check network/authentication errors on MLDP without a console fallback.

## source_v2 搜索

后端用 `getParameter` 读 `sourceName` 与 `owner` 且两者都没有默认值，缺失时返回 HTTP 500
（`Required String parameter 'owner' is not present`）；CLI 又会把空值从 query string 里丢掉，
所以这两个参数**实际必填**。不想过滤时传 SQL LIKE 通配符 `%`——非空且语义上等价于"不过滤"
（实测 `--source-name "%" --owner "%"` 与后端传空串结果一致）。`sourceName` 是**子串匹配**。

```bash
# 1) 只知道 source 名（含通配 owner）——最常用
bytedcli --site i18n-tt academy source search \
  --source-name demo_source \
  --owner "%" \
  --page 1 \
  --page-size 20

# 2) 按 datasource 类型 + 版本过滤，输出 JSON 给 agent
bytedcli --json --site i18n-tt academy source search \
  --source-name "%" \
  --owner "%" \
  --datasource-type hive \
  --version v1 \
  --page 1 --page-size 50
```

若填了错误的 `--owner` 会直接得到 `Total: 0`（不是 source 不存在，而是被 owner 条件过滤掉），
统一先用 `--owner "%"` 搜到再从结果里读真实 owner。

控制台等价：进入 Academy `/academy/datasource/academy`，按 source 名称 / owner / version / type / datasource type 筛选并翻页。

## raw feature set group 搜索

```bash
# 1) keyword + owners 过滤
bytedcli --site i18n-tt academy raw-feature-set group search \
  --keyword demo-group \
  --owners demo-user \
  --page 1 \
  --page-size 20

# 2) 多 owner / 多 status 过滤（按后端约定的逗号分隔）
bytedcli --site i18n-tt academy raw-feature-set group search \
  --keyword demo \
  --owners alice,bob \
  --statuses active,deprecated
```

> `--owners` / `--statuses` / `--update-frequencies` / `--versions` 由 CLI 直接透传给后端，不做客户端拆分。如果不确定后端是否支持逗号分隔，先用单值跑一次确认。

控制台等价：进入 `/academy/feature-engineering/offline`，按 keyword / owners / statuses / update frequencies / versions / type 筛选并翻页。

## raw feature set 草稿保存

```bash
# 从 DraftDTO JSON 文件保存草稿
bytedcli --site i18n-tt academy raw-feature-set draft save \
  --id 123 \
  --draft-file draft.json

# 或直接传内联 DraftDTO JSON 对象
bytedcli --site i18n-tt academy raw-feature-set draft save \
  --id 123 \
  --draft-json '{"codeTree":{"name":"root","children":[]},"taskInfo":{"taskConfList":[]}}'
```

请求体必须是 JSON object，对应 Academy 后端 `DraftDTO`：顶层常见字段为 `codeTree` 和 `taskInfo`。如果草稿体较大，优先使用 `--draft-file`，避免 shell 转义问题。

`--json` 模式成功输出会返回后端保存后的 raw feature set DTO：

```jsonc
{
  "status": "success",
  "data": {
    "id": 123,
    "raw_feature_set": { "id": 123, "name": "demo-set", "...": "..." }
  }
}
```

## raw feature set 取版本代码

```bash
# 取草稿（-1）；人类可读模式打印 name/status/currentVersion + codeTree 文件清单
bytedcli --site i18n-tt academy raw-feature-set version get --id 2444 --version -1

# 取指定历史版本
bytedcli --site i18n-tt academy raw-feature-set version get --id 2444 --version 12479

# 提取 dsl.py 源码（JSON + jq，按 codeTree 节点的 title 匹配）
bytedcli --json --site i18n-tt academy raw-feature-set version get --id 2444 --version -1 \
  | jq -r '.data.raw_feature_set.codeTree.children[] | select(.title=="dsl.py") | .content'
```

对应后端 `GET /v2/raw_feature_set/{id}/version/{version}`，无请求体，返回 `RawFeatureSetDTO`。

- `--id` 必填正整数；`--version` 必填，正整数为具体版本、`-1` 取草稿或最新版本。
- 常用于**取草稿 DSL**、做版本代码 diff、或在改写草稿前先拉全量 `codeTree` + `taskInfo`（配合 `draft save` 安全回写，避免只传部分文件导致覆盖丢失）。

返回结构要点（**均为顶层字段**，注意不在 `content` 下）：

- `codeTree`：UI 风格代码树。根节点 `title` 一般是 `academy`；节点字段是 **`title`（文件/目录名）+ `key` + `content` + `children`**（不是 `name`/`content`）。文件叶子的 `content` 即源码，常见 `dsl.py`、`udf.py`。
- `taskInfo`：调度配置，含各 Region 的 `taskConfList`。
- `currentVersion`：解析出的代码版本 id；`status`：草稿为 `draft`；另有 `name` / `owner` / `regions` / `updateFrequency` 等。

`--json` 成功输出结构：

```jsonc
{
  "status": "success",
  "data": {
    "id": 2444,
    "version": -1,
    "raw_feature_set": {
      "id": 2444,
      "name": "lingfeng_test_debug_batch_v1",
      "status": "draft",
      "currentVersion": 12479,
      "codeTree": {
        "title": "academy",
        "children": [
          { "title": "dsl.py", "key": "...", "content": "sql = '''...'''" },
          { "title": "udf.py", "key": "...", "content": "..." }
        ]
      },
      "taskInfo": { "taskConfList": [] }
    }
  }
}
```

## raw feature set 编译

```bash
# 编译草稿 / 最新版本（version 传 -1）
bytedcli --site i18n-tt academy raw-feature-set compile \
  --id 123 \
  --version -1

# 编译指定历史版本
bytedcli --site i18n-tt academy raw-feature-set compile \
  --id 123 \
  --version 456
```

对应后端 `PUT /v2/raw_feature_set/{id}/version/{version}/compile_all`（编译时包含调度设置中所有 Region），无请求体：

- `--id` 必填，正整数，raw feature set id
- `--version` 必填；正整数代表具体代码版本，`-1` 代表自动获取草稿或最新版本
- 传 `0` / 其他负数 / 浮点会被 CLI 拒绝并提示 `Expected a positive integer or -1.`

`--json` 模式成功输出会返回后端的 `CompileInfoDTO`（`ok` 表示编译是否通过，其余字段随上游返回，如 `compiledFeatures` / `sourceV2` / `log` 等）：

```jsonc
{
  "status": "success",
  "data": {
    "id": 123,
    "version": -1,
    "compile_info": { "ok": true, "rawFeatureSetId": 123, "...": "..." }
  }
}
```

编译失败（DSL 语法 / 依赖问题等）时后端可能返回 `compile_info.ok=false` 或携带错误 `log`；HTTP 层错误则走顶层 `error` 字段。

## raw feature set 调试

```bash
# 指定 region + 日期发起调试
bytedcli --site i18n-tt academy raw-feature-set debug \
  --id 123 --version -1 \
  --debug-json '{"regions":["sg"],"dateTime":"2026-07-10"}'

# 用文件传较大的 DebugReq
bytedcli --site i18n-tt academy raw-feature-set debug \
  --id 123 --version 456 \
  --debug-file debug.json

# 不带 body，走后端默认调试参数
bytedcli --site i18n-tt academy raw-feature-set debug --id 123 --version -1
```

对应后端 `PUT /v2/raw_feature_set/{id}/version/{version}/debug`，请求体为 `DebugReq` JSON 对象：

- `--id` 必填，正整数
- `--version` 必填；正整数为具体版本，`-1` 自动获取草稿或最新版本
- `--debug-json` / `--debug-file` 二选一且都可省略；省略时发送空 body（`{}`），`DebugReq` 各字段走后端默认值
- 传入内容必须是 JSON object，否则报 `Academy debug payload must be a JSON object.`；两者同传报互斥错误

`DebugReq` 常见字段（都可选，只传要覆盖的）：

- `regions`：string 数组，如 `["sg","ttp"]`
- `dateTime`：`yyyy-MM-dd`，默认当天；`hour`：`HH`，默认 `00`
- `writeDebugDB` / `sourceSample`：bool
- `realtimeMaxAllowedNum`（默认 100）/ `realtimeMaxAllowedTime`（默认 120s）：int
- `frequency`：调度频率（如 `daily`）

`--json` 模式成功输出会返回 `DebugResultDTO` 列表（后端按 region 各返回一条，含 `id`（debug id）/ `rawFeatureSetId` / `region` / `errorMsg`）：

```jsonc
{
  "status": "success",
  "data": {
    "id": 123,
    "version": -1,
    "results": [
      { "id": 9001, "rawFeatureSetId": 123, "region": "sg", "errorMsg": null },
      { "id": 9002, "rawFeatureSetId": 123, "region": "ttp", "errorMsg": null }
    ]
  }
}
```

某个 region 调试发起失败时，对应条目的 `errorMsg` 会带错误信息（其余 region 仍可成功）；拿到 `id`（debug id）后可用下面的 `debug-detail get` 查询任务详情 / 状态。

## raw feature set 调试详情 / 状态

```bash
# 用 debug 返回的 debug id 查询单次调试详情
bytedcli --site i18n-tt academy raw-feature-set debug-detail get --debug-id 9001
```

对应后端 `GET /v2/raw_feature_set/debug/{debugId}/detail`，无请求体：

- `--debug-id` 必填，正整数，即 `raw-feature-set debug` 返回列表里的 `id`
- 传 `0` / 负数 / 浮点会被 CLI 拒绝

`--json` 模式成功输出会返回后端的 `DebugDetailDTO`（常见字段：`status` 调试状态、`region`、`user`、`applicationId` / `yarnURL` 任务信息，以及 `logList` / `codeList` / `outputList` 等调试结果）：

```jsonc
{
  "status": "success",
  "data": {
    "debug_id": 9001,
    "detail": {
      "id": 9001,
      "entityId": 123,
      "user": "demo-user",
      "region": "sg",
      "status": "SUCCESS",
      "applicationId": "application_123",
      "...": "..."
    }
  }
}
```

用途：发起 `debug` 后轮询 `debug-detail get`，通过 `detail.status` 判断调试任务是否结束 / 成功，失败时看 `logList` 等字段定位原因。

## raw feature set 数据源授权校验

```bash
# 校验当前版本依赖的数据源是否给 dorado GDPR PSM 授权
bytedcli --site i18n-tt academy raw-feature-set verify-privilege --id 2444
```

对应后端 `POST /v2/raw_feature_set/{id}/verify-privilege`，无请求体，返回 `verifyPrivilegeDTO`：

- `--id` 必填，正整数，raw feature set id

**后端校验逻辑**（`RawFeatureCompileService.verifySourcePrivilege`）：取 raw feature set 当前版本调度配置里的 `taskConfList`（为空抛「Task Conf is null」），逐个 Region 校验数据源权限：

- 数据源标记 `skipDeploy` 时跳过；
- i18n region 跳过（授权在注册数据源时前置校验）；
- 批式（`daily` 低时效）逐个 hive 数据源走 Gemini `verifyPrivilege` 校验对应 dorado GDPR PSM 的 `select` 权限；三段式 datalake 宽表（`academy.*`）跳过；
- 任一数据源未授权则返回 `ok=false` 且 `errMsg` 带原因，全部通过则 `ok=true`。

`--json` 成功输出：

```jsonc
{
  "status": "success",
  "data": {
    "id": 2444,
    "verify_privilege": {
      "ok": false,
      "errMsg": "psm not authorized for hive academy.demo_table"
    }
  }
}
```

用途：上线 / 部署前预检当前版本依赖的数据源授权，`ok=false` 时按 `errMsg` 补授权后再走 `submit-online`。

## raw feature set 提交上线 / 预上线

```bash
# 提交上线（预上线）：为当前草稿版本创建上线工单并进入待审核
bytedcli --site i18n-tt academy raw-feature-set submit-online --id 2444
```

对应后端 `PUT /v2/raw_feature_set/{id}/online`，无请求体，返回 `OrderDTO`。

**后端上线逻辑总结**（`RawFeatureDeployService.online`，`@Transactional(SERIALIZABLE)`）：这是整条上线链路的**第一阶段（预上线 / preonline）**，做实际的校验 + 状态机推进，但不真正部署。

1. **前置校验**：特征集存在且非 `offline`；
2. **编译校验**：`compileAndAnalyze` 当前代码版本，`!ok` 抛 `compile failed`；
3. **slot 完整性**：online 特征与 deprecated 特征的 databaseSet 交集非空（且非自身名）→ 抛「不能下线 slot 内部分特征」；
4. **快照工单上下文** `OrderContext`：按 Region 存 taskConf / deployRegionList / doradoTaskId、source(V2)、`modified/deprecated` 特征，以及回滚用的 `OldBackUp`（旧特征集 / 特征 / databaseSet）；若有上次成功工单则继承 storeConfig / flags；
5. **幂等拦截**：特征集已处于 `upgrade/unreviewed/qualitycheck*` → 抛 “already submitted”；`currentCodeVersionId == deployCodeVersionId` → 抛 “already online”；
6. **状态机推进**：特征集 `online→upgrade`（升级）或 `→unreviewed`（首次）；代码版本 `draft→unreviewed`（CAS 校验旧状态）；unreviewed 特征落库；工单轨迹「申请预上线[preonline]」；
7. **特化**：`daily` 低时效且对应 databaseSet 不存在时，新建 `AcademyDatabaseSet`。

后续的正式上线 `PUT {id}/bpm/online`（推进审批流）、部署等步骤本 skill 暂未接入。

调用约束：

- 前置：特征集非 offline、当前有**未上线的草稿版本**且能编译通过，否则被上述校验拦截。
- 这是**生产写操作**：创建工单、切换代码/特征集状态、发起审批流；agent 调用前须与用户确认 id / site / 当前状态。

`--id` 必填正整数。`--json` 模式成功输出返回 `OrderDTO`：

```jsonc
{
  "status": "success",
  "data": {
    "id": 2444,
    "order": {
      "id": 5001,               // 工单 id
      "rawFeatureSetId": 2444,
      "status": "RUNNING",      // RUNNING/SUCCESS/FAILED/STOPPED/PENDING
      "version": 789            // 本次提交的代码版本
    }
  }
}
```

## raw feature set 版本代码 diff

```bash
# diff 线上/已部署版本(0) 与 当前版本(-1)
bytedcli --site i18n-tt academy raw-feature-set code-diff get --id 2444 --base-version 0 --test-version -1

# diff 两个指定历史版本
bytedcli --site i18n-tt academy raw-feature-set code-diff get --id 2444 --base-version 788 --test-version 789

# 提取 code diff / task info diff 全文（git-diff 格式）
bytedcli --json --site i18n-tt academy raw-feature-set code-diff get --id 2444 --base-version 0 --test-version -1 \
  | jq -r '.data.code_diff.codeDiff'
```

对应后端 `GET /v2/raw_feature_set/{id}/code_diff?baseVersion=&testVersion=`，无请求体，返回 `CodeDiffDTO`。

- `--id` 必填正整数；`--base-version` / `--test-version` 必填。
- 版本语义（`getActualVersion`）：正整数=指定版本；`0`=线上 / 已部署版本；`-1`=当前版本。
- 后端会解析请求的两个版本并**始终把较小版本作为 baseline**（`codeDiff` 是从 base 到 test 的 git-diff 文本），返回的 `baseVersion` / `testVersion` 是解析后的实际版本 id。

`CodeDiffDTO` 字段：`rawFeatureSetId` / `baseVersion` / `testVersion`（解析后版本），`codeDiff` / `taskInfoDiff`（git-diff 格式文本），`featureDiff` / `rawFeatureDiff` / `onlineRawFeatureDiff`（结构化 diff map）。

`--json` 成功输出：

```jsonc
{
  "status": "success",
  "data": {
    "id": 2444,
    "base_version": 0,        // = 入参 --base-version（未解析）
    "test_version": -1,       // = 入参 --test-version（未解析）
    "code_diff": {
      "rawFeatureSetId": 2444,
      "baseVersion": 788,     // 后端解析后的实际版本
      "testVersion": 789,
      "codeDiff": "@@ ... @@\n- old\n+ new",
      "taskInfoDiff": "..."
    }
  }
}
```

用途：上线前对比草稿/当前版本与线上版本的代码差异，或审查两个历史版本改动。

## raw feature set 待审核工单查询

```bash
# 查当前待审核（未完成）的上线工单
bytedcli --site i18n-tt academy raw-feature-set active-order get --id 2444
```

对应后端 `GET /v2/raw_feature_set/{id}/order/active`，无请求体，返回 `OrderDTO` 或 `null`。

- `--id` 必填正整数。
- 无待审核工单时后端返回 `null`，CLI 的 `data.order` 为 `null`，人类可读模式打印 `no pending order`。

`--json` 成功输出：

```jsonc
{
  "status": "success",
  "data": {
    "id": 2444,
    "order": {                 // 无待审核工单时为 null
      "id": 5001,              // 工单 id
      "rawFeatureSetId": 2444,
      "status": "RUNNING",     // RUNNING/SUCCESS/FAILED/STOPPED/PENDING
      "workflowId": 88,
      "version": 789
    }
  }
}
```

用途：`submit-online` 后确认是否已有在途工单、或在推进/停止工单前先查询当前 pending 工单及其状态。

## Lark 群确认消息

```bash
# 向 OceanCloud 平台助手 Lark 群发确认消息
bytedcli --site i18n-tt academy raw-feature-set confirm-lark \
  --username demo-user --msg "please confirm"

# @-mention 特征 owner 与多位管理员
bytedcli --site i18n-tt academy raw-feature-set confirm-lark \
  --username demo-user --msg "please confirm the online request" \
  --feature-owner owner-user \
  --notify-admin admin-a --notify-admin admin-b
```

对应后端 `POST /v2/raw_feature_set/confirm/lark`，请求体为 `LarkConfirmMsg` JSON 对象，无返回数据。

- `--username` / `--msg` 必填。
- `--feature-owner` 可选，@-mention 特征 owner。
- `--notify-admin` 可选且**可重复**，每个值追加到 `notifyAdmin` 数组，用于 @-mention 多位管理员。

请求体（`LarkConfirmMsg`）：`{ "username", "featureOwner", "msg", "notifyAdmin": [...] }`。

`--json` 成功输出：

```jsonc
{
  "status": "success",
  "data": {
    "username": "demo-user",
    "feature_owner": "owner-user",   // 未传时为 null
    "notify_admin": ["admin-a", "admin-b"],  // 未传时为 []
    "sent": true
  }
}
```

用途：在上线 / 审核链路里向平台助手群发通知，可配合 `user admin-search` / `user on-call` 拿到要 @-mention 的管理员用户名。

## 调度配置查询（framework-version list / queue list / task-conf template get / dorado-task get）

这四条只读命令用于**组装某 Region 的调度 taskConf**（框架资源 + 队列 + spark 参数 + 依赖）。

枚举取值（CLI 侧校验，与后端 `enummode/*` 对齐）：

- `--region`：`cn` `cn_offline` `va` `sg` `gcp` `ttp` `tx` `eu` `uswest` `i18n`
- `--update-frequency`：`realtime` `daily` `estuary_flink` `estuary_spark`
- `--group-type`：`user_realtime_ips` `user_realtime_kv` `user_batch_bcache` `ad_realtime_kv` `user_long_sequence`
- `--calc-engine-version`：`spark_3_2` `flink_1_11` `flink_1_17`
- `--task-type`：`raw_feature_set` `sfe`

```bash
# 1) 框架版本列表（frameWorkResource）
bytedcli --json --site i18n-tt academy raw-feature-set framework-version list \
  --region ttp --update-frequency daily --group-type user_realtime_ips --calc-engine-version spark_3_2 \
  | jq '[.data.framework_resources[] | {id, name, versions: [.versionList[].version]}]'

# 2) 用户可用队列，挑最空闲（cpuRate+memoryRate 最小）
bytedcli --json --site i18n-tt academy raw-feature-set queue list \
  --user lingfeng.chen --region ttp --is-stream false \
  | jq '.data.queues | min_by(.cpuRate + .memoryRate)'

# 3) taskConf 模板（spark 参数；queueInfo 通常为 null，需另用 queue list 填）
bytedcli --json --site i18n-tt academy raw-feature-set task-conf template get \
  --region ttp --update-frequency daily --group-type user_realtime_ips --calc-engine-version spark_3_2 \
  | jq '.data.task_conf | {frameWorkResource, paramKeys: (.params|keys)}'

# 4) dorado 依赖任务信息（返回结构=taskConf dependencies[] 的元素形态）
bytedcli --json --site i18n-tt academy raw-feature-set dorado-task get \
  --task-id 304327198 --region sg | jq '.data.dorado_task'
```

对应后端：
- `GET /v2/raw_feature_set/framework_version/list?region=&type=&groupType=&calcEngineVersion=` → `List<FrameWorkResourceDTO>`
- `GET /v2/raw_feature_set/queue/list?user=&region=&isStream=` → `List<QueueDTO>`
- `GET /v2/raw_feature_set/task_conf/template?region=&updateFrequency=&groupType=&taskType=&calcEngineVersion=` → `TaskConfPOJO`
- `GET /v2/raw_feature_set/dorado_task/{task_id}?region=` → `RecommendDependDTO`

## feature 搜索

```bash
# 1) keyword + 在线特征
bytedcli --site i18n-tt academy feature search \
  --keyword demo_feature \
  --page 1 \
  --page-size 20

# 2) 限定 fountain 离线研究 + 指定 FFE graph id
bytedcli --site i18n-tt academy feature search \
  --keyword demo_feature \
  --is-fountain-offline-research true \
  --ffe-graph-id 123
```

参数取值约束：

- `--is-fountain-offline-research` 只接受字面量 `true` / `false`，否则 CLI 直接报 `Expected true or false.`
- `--ffe-graph-id` 必须是正整数，`0` / 负数 / 浮点会被拒
- 这是 legacy online feature search 的既有 FFE graph id 过滤器，不是 Academy 3.0 `fe_config_id` 参数

控制台等价：进入 `/academy/feature-engineering/online`，按 keyword / isFountainOfflineResearch / ffeGraphId 筛选。

## 用户 on-call 管理员查询

```bash
# 管理员 on-call 轮值成员列表
bytedcli --site i18n-tt academy user admin-search

# 当前正在 on-call 的管理员
bytedcli --site i18n-tt academy user on-call
```

对应后端：
- `GET /user/admin/search` → `List<String>`（on-call 轮值成员用户名）
- `GET /user/admin/on_call` → `List<String>`（当前在班管理员用户名）

两条命令都无入参（除全局参数 + 可选 `--base-url`），`--json` 成功输出结构一致：

```jsonc
{
  "status": "success",
  "data": {
    "admins": ["admin-a", "admin-b"],
    "total": 2
  }
}
```

用途：拿到管理员用户名后可传给 `raw-feature-set confirm-lark --notify-admin` 做 @-mention 通知。

## 翻页与 JSON 消费

`--json` 模式输出（成功）：

```jsonc
{
  "status": "success",
  "data": {
    "rows": [ /* 每行字段由后端决定，常见列：name/owner/status/version/type */ ],
    "total": 123,
    "page": 1,
    "page_size": 20
  }
}
```

翻页判断：`page * page_size < total` 时还有下一页，`--page` 自增重跑。

行字段不固定时的取值建议：

- name：`name` ↔ `sourceName` ↔ `featureName` ↔ `groupName`
- owner：`owner` ↔ `owners`
- status：`status` ↔ `statuses`
- updateFrequency：`updateFrequency` ↔ `updateFrequencies`
- datasourceType：`datasourceType` ↔ `dataSourceType`

## 使用建议

- 没特殊说明，先加 `--site i18n-tt`
- 给 agent / 脚本消费时，加全局 `--json`（必须放在 `academy` 前）
- 默认 host 不可用时再用 `--base-url`，且只填根 origin（不要带 path / 末尾斜杠）
- 当前除 raw feature set 草稿保存、取版本代码、编译、调试（含状态查询）与提交上线外，以检索类命令为主；遇到未覆盖写操作或详情需求，先告知用户当前能力边界，再按需求扩 CLI
- `submit-online` 是有副作用的生产写操作（编译校验、切换状态、创建工单、发起审批流），调用前先和用户确认

## 常见问题速查

完整版见 [`troubleshooting.md`](troubleshooting.md)，下面列三条 academy 高频项：

| 现象 | 处理 |
|------|------|
| 401 / UserNotLogin | `BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login` 后重试，命令上保留 `--site i18n-tt` |
| `Expected true or false.` | `--is-fountain-offline-research` 必须传 `true` / `false` 字面量 |
| `Expected a positive integer.` | `--ffe-graph-id` 必须是正整数 |
