# bytedcli tiktok-scheduler 命令参考

`bytedcli tiktok-scheduler` 操作 TikTok Scheduler 控制面 HTTP API。命令分三组：

- `onetime <create|get|list|terminate>` —— 一次性任务（含**延迟/延时执行**）。
- `recurring <create|update|pause|unpause|trigger|delete|get|list>` —— 周期性任务（cron / interval）。
- `namespace <create|get|delete|add-owner|add-permission|upsert-rate-limit>` —— 命名空间管理。

通用约定：

- `onetime` / `recurring` 的 env 完全由 `--region` 决定（含 `BOE` → boe，否则 prod），**没有单独的环境参数**；访问 BOE 用 `--region US-BOE`。
- `namespace` 组**不按 region 路由**：命名空间存在按 env 隔离的控制面里、以 ns 为键，后端自己按部署区域扇出。所以用 `--env prod|boe`（默认 prod）选控制面；只有 `create` 需要用可重复的 `--region` 指定部署区域。
- 写操作（create/update/pause/unpause/trigger/delete/terminate）默认只打印 dry-run 预览，需 `-y/--yes` 才真正执行。
- 三类 action（rpc/http/workflow）的 flag 用法见下文「Action 入参」一节，`onetime create` 与 `recurring create/update` 共用。
- `get` / `list` 响应里的 `schedule_type` / `action_type` / `status` / `overlap_policy` 等是 **int 枚举**，含义对照下文「枚举值对照」一节，不要凭印象猜。
- 任何参数不确定时先看 `bytedcli tiktok-scheduler <group> <command> --help`。

---

## 控制台详情页链接（手动拼，CLI 不返回）

CLI 只返回后端 JSON，**不会**给出可点的控制台链接。用户想要「详情页 / 控制台链接」时，按下表自己拼一个。

- 控制台 host 固定是 `https://ttscheduler.aipa.bytedance.net`，**和 API host（`ttscheduler-sg.tiktok-row.net` 等）不是一回事**，不要用 API host 拼控制台链接。
- 前端是 **hash 路由**：所有页面都在 `/#/` 下面，query 跟在 hash 路由后面。
- 环境不分 host：prod / boe 都用同一个 host，靠 `env=<prod|boe>` query 区分。
- 每个链接都要带两个 query：`env=<prod|boe>` 和 `vregion=<vregion>`。
- `vregion` 取值：`onetime` / `recurring` 用命令里的 `--region`；`namespace` 命令本身不带 region，取该 namespace 部署区域之一（`namespace get` 响应里 `vregion_infos[0].vregion`）。
- 控制台**没有**独立的「namespace 详情页」「schedule 详情页」，给链接时用下表最接近的页面（ns → 其 schedule 列表；schedule → 其执行列表；最深是单次执行详情）。

`<host>` = `https://ttscheduler.aipa.bytedance.net`

| 想看 | 链接模板 |
| --- | --- |
| 全部 namespace | `<host>/#/?env=<env>&vregion=<vregion>` |
| 某 namespace（≈ 其 schedule 列表） | `<host>/#/namespace/<ns>/schedules?env=<env>&vregion=<vregion>` |
| 某 schedule（≈ 其执行列表） | `<host>/#/namespace/<ns>/schedules/<scheduleId>/executions?env=<env>&vregion=<vregion>` |
| 某次执行详情 | `<host>/#/namespace/<ns>/schedules/<scheduleId>/executions/<executionId>/detail?env=<env>&vregion=<vregion>` |

示例（prod、Singapore-Central 区、ns=`my-ns`、schedule=`daily-2am`）：

```
https://ttscheduler.aipa.bytedance.net/#/namespace/my-ns/schedules/daily-2am/executions?env=prod&vregion=Singapore-Central
```

- `<ns>` 里有特殊字符要做 URL encode。
- 链接只是定位，最终能不能看到取决于用户在控制台的权限。

---

## 一次性任务（onetime）

命令组：`bytedcli tiktok-scheduler onetime <create|get|list|terminate>`。

一次性任务的两种典型用法：

1. **立即只跑一次**：不带 `--start-delay-ms`（默认 `0`）。
2. **延迟/延时执行（延迟任务）**：带 `--start-delay-ms <毫秒>`，任务在「create 时刻 + 该延迟」后只触发一次。这是平台做「延迟任务 / 定时一次 / N 分钟后执行」的标准方式，不要用周期(cron)任务去模拟一次性延迟。

### 延迟执行（延迟任务）

```bash
# 1 小时后只跑一次（3600000 ms）
bytedcli tiktok-scheduler onetime create \
  --namespace my-ns --region Singapore-Central \
  --start-delay-ms 3600000 \
  --action-type rpc --rpc-psm my.psm --rpc-method MyService.Run --rpc-data '{}' \
  -y
```

- `--start-delay-ms` 是**相对延迟**：基准是请求到达后端的时刻，不是绝对时间戳；单位**毫秒**。常用换算：1 分钟=`60000`、10 分钟=`600000`、1 小时=`3600000`、1 天=`86400000`。
- `--jitter-ms` 是在延迟基础上再叠加的随机抖动（0~该值，毫秒），用于打散同一批延迟任务、避免同一瞬间惊群；只想精确延迟就别传（默认 `0`）。
- 平台不接受「绝对触发时间戳」入参；要在某个具体时刻跑，自行用 `(目标时刻 - 当前时刻)` 换算成毫秒填 `--start-delay-ms`。

### create（写操作，需 dry-run + `-y`）

```bash
bytedcli tiktok-scheduler onetime create \
  --namespace <namespace> --region <region> \
  --action-type http --http-url https://my.svc/run --http-method POST \
  [--schedule-id <id>] [--start-delay-ms 0] [--jitter-ms 0] \
  [--ctx-env ppe_xxx] [--group-key g1] [--custom-key c1] \
  [-y]
```

- `--schedule-id` 可选；省略时由后端自动生成。
- `--start-delay-ms` / `--jitter-ms` 均默认 `0`（`0` = 立即执行 / 不抖动）。要做**延迟任务**就靠 `--start-delay-ms`，详见上方「延迟执行（延迟任务）」。
- 不带 `-y` 先看 dry-run，确认 body 后再补 `-y` 执行。

rpc 示例：

```bash
bytedcli tiktok-scheduler onetime create \
  --namespace my-ns --region Singapore-Central --schedule-id once-1 \
  --action-type rpc --rpc-psm my.psm --rpc-method MyService.Run \
  --rpc-data '{"k":"v"}' -y
```

### get（读操作）

```bash
bytedcli tiktok-scheduler onetime get \
  --namespace <namespace> --region <region> --schedule-id <id> \
  [--execution-id <eid>]
```

- 一次性任务详情通常需要 `--execution-id` 才能定位某次执行。

### terminate（写操作，需 dry-run + `-y`）

终止一次性任务某次正在运行的执行（execution）。

```bash
bytedcli tiktok-scheduler onetime terminate \
  --namespace <namespace> --region <region> \
  --schedule-id <id> --execution-id <eid> \
  [-y]
```

- `--execution-id` 必填，且通常只对 `status=RUNNING`（见「枚举值对照」）的执行有意义；先用 `get` 查到 execution 与状态。
- 不带 `-y` 先看 dry-run，确认后再补 `-y` 执行。

### list（读操作）

```bash
bytedcli tiktok-scheduler onetime list \
  --namespace <namespace> --region <region> \
  [--query <filter>] [--page-size 20] [--next-page-token <token>]
```

- 分页：用上一次响应里的 `next_page_token` 续查。
- `--query` 是高级过滤（Temporal list-filter 语法），语法、可用字段与示例见下方「list --query 过滤语法」一节。
- 响应里的 `schedule_type` / `action_type` / `status` 等是 **int 枚举**，含义见「枚举值对照」。

---

## 周期性任务（recurring）

命令组：`bytedcli tiktok-scheduler recurring <create|update|pause|unpause|trigger|delete|get|list>`。所有写操作（create/update/pause/unpause/trigger/delete）默认 dry-run，需 `-y/--yes` 才执行。

### 调度规格：cron vs interval

- `--cron <expr>`：**7 位秒级** cron 表达式（字段顺序：秒 分 时 日 月 周 年），单条，不支持配置多个。例：`--cron '0 0 2 * * * *'`（每天 02:00）。不支持 `?`，请直接用 `*` 代替（CLI 也会自动把 `?` 替换成 `*`）。
- `--interval-sec <n>`（可配 `--interval-offset-sec`）：固定间隔触发。
- create 至少要给 `--cron` 或 `--interval-sec` 之一；两者语义不同，通常二选一。
- 生效时间窗（都映射到 `schedule_spec`，均可选）：
  - `--start-ts <Unix秒>`：调度生效起始时间，**此刻之前不触发**；不传 = 立即生效。
  - `--end-ts <Unix秒>`：调度失效结束时间，**此刻之后不再触发**；不传 = 永不过期。
  - `--jitter-ms <毫秒>`：每次触发在计划时间上叠加的**随机抖动上限**，用于打散并发、避免同一时刻惊群；不传 = 无抖动。

### 开关类参数（无需传值）

- `--paused`：创建为暂停态。不传则创建后即生效（默认不暂停）。是开关，**不要**写成 `--paused true`；想之后改状态用 `pause` / `unpause` 子命令。
- `--trigger-immediately`：开关，创建后立即额外触发一次。

### overlap_policy

`--overlap-policy` 取值（上一次还没结束时如何处理新触发）：
`skip` / `buffer_one` / `buffer_all` / `cancel_other` / `terminate_other` / `allow_all`。

### create（写操作）

```bash
bytedcli tiktok-scheduler recurring create \
  --namespace <ns> --region <region> --schedule-id <id> \
  --cron '0 0 2 * * * *' \
  [--overlap-policy skip] [--paused] [--trigger-immediately] \
  [--start-ts <sec>] [--end-ts <sec>] [--jitter-ms 0] \
  --action-type http --http-url https://my.svc/run --http-method POST \
  [--ctx-env ppe_xxx] [--group-key g1] [--custom-key c1] \
  [-y]
```

间隔触发示例：

```bash
bytedcli tiktok-scheduler recurring create \
  --namespace my-ns --region Singapore-Central --schedule-id every-5m \
  --interval-sec 300 \
  --action-type rpc --rpc-psm my.psm --rpc-method S.M --rpc-data '{}' -y
```

### update（写操作，全量替换）

```bash
bytedcli tiktok-scheduler recurring update \
  --namespace <ns> --region <region> --schedule-id <id> \
  --cron '0 0 3 * * * *' [--overlap-policy buffer_one] \
  --action-type rpc --rpc-psm my.psm --rpc-method S.M --rpc-data '{}' \
  [--ctx-env ppe_xxx] [-y]
```

- **后端 update 是整体替换、不是 patch**：它会用请求体里的 `cyclical_options` / `action` / `ctx_payload` 整体覆盖原值，且会无条件解引用 `schedule_spec`。所以和 `create` 一样，**必须把完整配置重新传一遍**（调度规格 + `--action-type` + 该类型的 action flag），CLI 原样透传，不做内部 get/合并。
- 与 create 相同的必填项：`--cron` 或 `--interval-sec`（二选一）、`--action-type` + 对应 action flag。没传会报错。
- 没传的字段会按 create 的默认值落库（例如 `--http-method` 默认 `GET`、未传 header 即为空），**不会保留原 schedule 的旧值**。要保留就得显式重传。
- **action_type 必须与现有 schedule 一致**：后端不允许变更 action_type，传了不同类型会被后端拒绝（需删除后重建）。
- **update 不支持 `--paused` / `--trigger-immediately`**：这两个是 create-only，后端 update 不生效。改暂停状态用 `pause` / `unpause` 子命令，手动触发一次用 `trigger`。
- update 请求体不含 `group_key` / `custom_key`（接口模型没有这两个字段）。

### pause / unpause / trigger / delete（写操作）

```bash
bytedcli tiktok-scheduler recurring pause   --namespace <ns> --region <region> --schedule-id <id> [-y]
bytedcli tiktok-scheduler recurring unpause --namespace <ns> --region <region> --schedule-id <id> [-y]   # 恢复已暂停的任务
bytedcli tiktok-scheduler recurring trigger --namespace <ns> --region <region> --schedule-id <id> [-y]   # 手动触发一次
bytedcli tiktok-scheduler recurring delete  --namespace <ns> --region <region> --schedule-id <id> [-y]
```

- `pause` ↔ `unpause` 一一对应后端 `/pause`、`/unpause` 接口（没有单独的 start/resume 接口）。

### get / list（读操作）

```bash
bytedcli tiktok-scheduler recurring get  --namespace <ns> --region <region> --schedule-id <id>
bytedcli tiktok-scheduler recurring list --namespace <ns> --region <region> \
  [--query <filter>] [--page-size 20] [--next-page-token <token>]
```

- `--query` 是高级过滤，语法与可用字段见下方「list --query 过滤语法」一节。

---

## list --query 过滤语法（onetime / recurring 共用，字段不同）

`onetime list` / `recurring list` 的 `--query` 是一段 **Temporal List Filter**（类 SQL 的可见性查询）子句。CLI 把它原样透传到后端的 `query` 参数，后端再用 `AND` 拼到它自己的内置过滤条件后面（onetime 内置「只列一次性执行」，recurring 内置「只列运行中的周期 schedule」）。所以你只写**附加过滤条件**那一段，不要自己写整句、也不用关心内置条件。

### 基本写法

- 单条件：`` `<字段key>` <操作符> <值> ``，字段 key 用反引号包裹。
- 字符串 / 时间 / 枚举值用**双引号**：`` `ttsched-sys-group-key` = "my-group" ``；布尔值**不加引号**：`` `TemporalSchedulePaused` = false ``。
- 时间值用 RFC3339：`` `ttsched-sys-create-time` >= "2026-06-01T00:00:00+08:00" ``。
- 多条件用 `AND` / `OR` 连接，可加括号分组：`` (`ttsched-sys-group-key` = "g1") AND (`ttsched-sys-action-type` = "HTTP") ``。
- shell 里整段 query 用**单引号**包住，内部的反引号 / 双引号原样保留，避免被 shell 解释。
- 不传 `--query` = 不附加过滤，返回该 namespace + region 下的全部（仅受内置条件约束）。

### 可用字段（query 里必须用 key 列，不是别名）

> 字段集合来自后端 `query-options` 接口，**onetime 与 recurring 部分字段不同**：onetime 查 workflow 执行可见性、recurring 查 schedule 可见性。下表「key」才是写进 query 的字段名，「别名」只是控制台展示用。

共用字段：

| 别名       | query key                | 类型         | 操作符                                          |
| ---------- | ------------------------ | ------------ | ----------------------------------------------- |
| GroupKey   | `ttsched-sys-group-key`  | string       | `starts_with` `=` `!=` `is null` `is not null`  |
| CustomKey  | `ttsched-sys-custom-key` | string       | `starts_with` `=` `!=` `is null` `is not null`  |
| ActionType | `ttsched-sys-action-type`| string(枚举) | `=`；值：`RPC` / `HTTP` / `WORKFLOW`            |
| Creator    | `ttsched-sys-creator`    | string       | `starts_with` `=` `!=` `is null` `is not null`  |
| CreateTime | `ttsched-sys-create-time`| datetime     | `>=` `<=` `is null` `is not null`               |

onetime（一次性）额外字段：

| 别名       | query key         | 类型         | 操作符                                         |
| ---------- | ----------------- | ------------ | ---------------------------------------------- |
| ScheduleId | `WorkflowId`      | string       | `starts_with` `=` `!=` `is null` `is not null` |
| Status     | `ExecutionStatus` | string(枚举) | `=`；值：`Running` / `Completed` / `Failed` / `Terminated` |

recurring（周期性）额外字段：

| 别名       | query key                | 类型 | 操作符                            |
| ---------- | ------------------------ | ---- | --------------------------------- |
| ScheduleId | `ScheduleId`             | string | `starts_with` `=` `!=` `is null` `is not null` |
| Paused     | `TemporalSchedulePaused` | bool   | `=`；值：`true` / `false`         |

> 关键差异：onetime 的 ScheduleId 用 key `WorkflowId`，recurring 用 `ScheduleId`；「状态」过滤 onetime 用 `ExecutionStatus`（执行状态枚举），recurring 用 `TemporalSchedulePaused`（是否暂停的布尔）。用错对象的字段会被后端拒绝。

### 操作符含义

- `=` / `!=`：等于 / 不等于。
- `starts_with`：字符串前缀匹配。
- `>=` / `<=`：时间比较（time 类型只支持 `>=` `<=`）。
- `is null` / `is not null`：字段是否有值，**不带值**，写成 `` (`<key>` is null) ``。

### 示例

```bash
# onetime：按 GroupKey 精确过滤
bytedcli tiktok-scheduler onetime list --namespace my-ns --region Singapore-Central \
  --query '`ttsched-sys-group-key` = "order-close"'
# onetime：只看失败执行 + CustomKey 前缀
bytedcli tiktok-scheduler onetime list --namespace my-ns --region Singapore-Central \
  --query '(`ExecutionStatus` = "Failed") AND (`ttsched-sys-custom-key` starts_with "uid-")'
# onetime：按创建时间区间
bytedcli tiktok-scheduler onetime list --namespace my-ns --region Singapore-Central \
  --query '(`ttsched-sys-create-time` >= "2026-06-01T00:00:00+08:00") AND (`ttsched-sys-create-time` <= "2026-06-05T00:00:00+08:00")'
# recurring：ScheduleId 前缀 + 只看未暂停
bytedcli tiktok-scheduler recurring list --namespace my-ns --region US-TTP \
  --query '(`ScheduleId` starts_with "daily-") AND (`TemporalSchedulePaused` = false)'
# recurring：按 ActionType 过滤
bytedcli tiktok-scheduler recurring list --namespace my-ns --region US-TTP \
  --query '`ttsched-sys-action-type` = "RPC"'
```

---

## Namespace 管理（namespace）

命令组：`bytedcli tiktok-scheduler namespace <create|get|delete|add-owner|add-permission|upsert-rate-limit>`。写操作（create/delete/add-owner/add-permission/upsert-rate-limit）默认 dry-run，需 `-y/--yes` 才执行；`get` 为读操作。

### 路由模型（重要，和 onetime/recurring 不同）

- 用 `--env prod|boe`（默认 `prod`）选控制面 host / JWT，**不传 region 也不从 region 推断 env**。
- 命名空间用 path 段 `:ns` 定位，所以 get/delete/add-owner/add-permission/upsert-rate-limit 都**不带 region**。
- 只有 `create` 需要部署区域：用可重复的 `--region` 传，落到请求体的 `vregion_specs`。
- 部署 region 白名单（按 env 校验，CLI 会本地拦截）：
  - prod：`Singapore-Central / US-EastRed / EU-TTP2 / US-TTP / US-TTP2`
  - boe：`US-BOE`

### 命名规则

- namespace 名、限流 key 的命名规则由**服务端校验**（CLI 不再本地拦截，避免规则变动时还要改 CLI）。不合法时后端会报错，按提示修正即可。

### create（写操作）

```bash
bytedcli tiktok-scheduler namespace create \
  --namespace my_ns \
  --region Singapore-Central --region US-TTP \
  [--owner a@bytedance.com --owner b@bytedance.com] \
  [--description "..."] [--execution-retention-minutes 4320] \
  [-y]
```

- `--region` 可重复，至少 1 个，必须在所选 `--env` 的白名单内。
- `--owner` 可重复、可选；调用者会被后端自动加为 owner。
- `--execution-retention-minutes` 默认 `4320`（=3 天）= 执行历史保留时长。

### get / delete

```bash
bytedcli tiktok-scheduler namespace get    --namespace my_ns [--env prod]
bytedcli tiktok-scheduler namespace delete --namespace my_ns [--env prod] [-y]
```

### add-owner / add-permission

```bash
# 加人（员工）：授予该命名空间的 all 权限
bytedcli tiktok-scheduler namespace add-owner --namespace my_ns --owner a@bytedance.com [-y]
# 加服务（PSM）：固定授予 all 权限给一个 SERVICE holder
bytedcli tiktok-scheduler namespace add-permission --namespace my_ns --holder-name tiktok.scheduler.svc [-y]
```

- `add-owner` 给**员工**（EMPLOYEE）授权；`add-permission` 给**服务**（SERVICE/PSM）授权。
- `add-permission` 已**锁定**为「`all` 权限 + SERVICE 类型」，与控制台一致，不暴露权限/类型选择；要给人授权请用 `add-owner`。

### upsert-rate-limit（写操作）

为某个限流 key 设置/更新各区域 QPS（未列出的区域不动）：

```bash
bytedcli tiktok-scheduler namespace upsert-rate-limit \
  --namespace my_ns --key order_create \
  --qps US-TTP=100 --qps Singapore-Central=50 \
  [-y]
```

- `--qps <region>=<n>` 可重复，至少 1 个；region 必须在所选 env 白名单内，`n` 为非负整数（`0` 表示限流到 0，全部拒绝）。
- burst 由服务端按 qps 设定，不暴露。

---

## Action 入参（create / update 共用）

`onetime create` 与 `recurring create/update` 的 action 配置是同一套。

> **权威 flag 列表以 `--help` 为准**：`bytedcli tiktok-scheduler onetime create --help`（或 `recurring create --help`）。本节只记 `--help` 表达不清的几条约束，不重复罗列 flag。

### 约束

- **先 `--action-type rpc|http|workflow` 选类型，三类 flag 互斥**：选了某类就只能用该类前缀的 flag，混用（如 `--action-type rpc` 又传 `--http-*`）会报错。
- **`recurring update` 是全量替换**：必须重传完整 action（`--action-type` + 对应 flag），未传字段回默认值、不保留旧值；且 action_type 必须与现有 schedule 一致（后端不允许变更，需删除后重建）。
- **rpc/http 默认同步**：RPC 返回 / HTTP 响应即视为本次执行完成。只有当目标逻辑是「先收下请求、稍后再异步回调上报结果」时，才加 `--rpc-async` / `--http-async`——此时执行不会因返回而结束，会一直等外部完成回调，或等到 `--*-async-complete-timeout-ms` 超时。

### workflow 的 `--task`（`--help` 给不了结构）

workflow 的 task 是异构嵌套结构，没法拍平成纯 flag，所以每个 task 传一段 `WorkflowTask` JSON；`--task` 可重复，至少 1 个：

```bash
--action-type workflow \
  --task '{"alias":"step1","action_type":"http","action":{"http_action":{"url":"https://a/step1","method":"POST"}}}' \
  --task '{"alias":"step2","action_type":"rpc","action":{"rpc_action":{"psm":"my.psm","method":"S.M","request":{"json_data":"{}"}}}}'
```

- task JSON 字段：`action_type` **只支持 `rpc` / `http`**（或数字 `1`/`2`），不支持 `workflow`——workflow 不能再嵌套 workflow；`action` 相应只接受 `rpc_action` / `http_action`（不接受 `workflow_action`），且 payload 必须包在对应键下（`http` → `action.http_action`，`rpc` → `action.rpc_action`），其内部字段名与 rpc/http 的 IDL 字段一致。
- `--execution-mode single|sequential|parallel`（默认 `sequential`）、`--parallel-post-task <WorkflowTask json>`（仅 parallel 模式有意义）见 `--help`。

---

## 枚举值对照（解读响应里的 int 字段）

后端响应里的枚举字段返回的是 **int**（Thrift enum 序号），不是字符串。读取 `get` / `list` 等响应时，按下表把 int 还原成含义；不要凭印象猜。

### 响应里最常见的字段 → 取值

`onetime/recurring list` 与 `get` 返回的 `Schedule` / 描述里会出现：

| 字段路径                                   | 枚举                       | 见下表                     |
| ------------------------------------------ | -------------------------- | -------------------------- |
| `schedule_type`                            | ScheduleType               | ScheduleType               |
| `action_type`                              | ActionType                 | ActionType                 |
| `description.acyclical_description.status` | ScheduleExecutionStatus    | ScheduleExecutionStatus    |
| `description.cyclical_description.status`  | CyclicalScheduleStatus     | CyclicalScheduleStatus     |
| `...cyclical_options...overlap_policy`     | OverlapPolicy              | OverlapPolicy              |
| workflow `execution_mode`                  | WorkflowTasksExecutionMode | WorkflowTasksExecutionMode |
| workflow 节点 `status`                     | WorkflowNodeStatus         | WorkflowNodeStatus         |
| pending activity `state`                   | PendingActivityState       | PendingActivityState       |

### 对照表

#### ScheduleType

| int | 名称      | 含义                    |
| --- | --------- | ----------------------- |
| 0   | UNKNOWN   | 未知                    |
| 1   | ACYCLICAL | 一次性任务（onetime）   |
| 2   | CYCLICAL  | 周期性任务（recurring） |

#### ActionType

| int | 名称     | 含义                |
| --- | -------- | ------------------- |
| 0   | UNKNOWN  | 未知                |
| 1   | RPC      | RPC 调用            |
| 2   | HTTP     | HTTP 调用           |
| 3   | WORKFLOW | Workflow（多 task） |

#### ScheduleExecutionStatus

一次性任务（onetime）单次执行状态。
| int | 名称 | 含义 |
|---|---|---|
| 0 | UNSPECIFIED | 未指定 |
| 1 | RUNNING | 执行中 |
| 2 | COMPLETED | 成功完成 |
| 3 | FAILED | 失败 |
| 4 | CANCELED | 已取消 |
| 5 | TERMINATED | 已终止 |
| 6 | CONTINUED_AS_NEW | 以新执行续跑 |
| 7 | TIMED_OUT | 超时 |

#### CyclicalScheduleStatus

周期性任务（recurring）整体状态。
| int | 名称 | 含义 |
|---|---|---|
| 0 | UNSPECIFIED | 未指定 |
| 1 | PAUSED | 已暂停 |
| 2 | RUNNING | 运行中 |

#### OverlapPolicy

周期任务两次触发重叠时的处理策略。
| int | 名称 | 含义 |
|---|---|---|
| 0 | UNSPECIFIED | 未指定 |
| 1 | SKIP | 跳过新触发 |
| 2 | BUFFER_ONE | 缓冲一个 |
| 3 | BUFFER_ALL | 缓冲全部 |
| 4 | CANCEL_OTHER | 取消正在跑的 |
| 5 | TERMINATE_OTHER | 终止正在跑的 |
| 6 | ALLOW_ALL | 允许并发全部 |

#### WorkflowTasksExecutionMode

| int | 名称       | 含义    |
| --- | ---------- | ------- |
| 0   | UNKNOWN    | 未知    |
| 1   | SINGLE     | 单 task |
| 2   | SEQUENTIAL | 串行    |
| 3   | PARALLEL   | 并行    |

#### WorkflowNodeStatus

| int | 名称      | 含义   |
| --- | --------- | ------ |
| 0   | UNKNOWN   | 未知   |
| 1   | RUNNING   | 执行中 |
| 2   | SUCCEEDED | 成功   |
| 3   | FAILED    | 失败   |

#### PendingActivityState

| int | 名称             | 含义       |
| --- | ---------------- | ---------- |
| 0   | UNSPECIFIED      | 未指定     |
| 1   | SCHEDULED        | 已排程     |
| 2   | STARTED          | 已开始     |
| 3   | CANCEL_REQUESTED | 已请求取消 |

#### SearchAttributeSpecValueType

（query-options 等元信息里出现）
| int | 名称 | 含义 |
|---|---|---|
| 0 | UNKNOWN | 未知 |
| 2 | KEYWORD | 字符串/关键字 |
| 3 | INT | 整数 |
| 4 | DOUBLE | 浮点 |
| 5 | BOOL | 布尔 |

> 来源：`scheduler_server.thrift` 的 enum 定义。枚举有新增时以 IDL 为准。
