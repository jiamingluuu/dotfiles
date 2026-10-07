# webcast.platform.scheduler / webcast.scheduler.job 只读接口参考

PSM：

- 控制面：`webcast.platform.scheduler`
- 执行层：`webcast.scheduler.job`（`GetDebugStatus`）

默认集群：`default`。站点跟随全局 `--site` / `BYTEDCLI_CLOUD_SITE`，当前支持 `cn` 与 `boe`。

下文列出本 Skill 开放的只读接口请求字段。所有请求都携带 thrift `base.Base`，bytedcli 会自动注入 `Caller=aime.bytetask.scheduler.skill`，无需手动构造。

---

## 1. GetProject — 项目查询（`bytetask project list`）

| 字段           | 类型              | 说明                                 |
| -------------- | ----------------- | ------------------------------------ |
| ID             | i64 (optional)    | 项目 ID                              |
| PSM            | string (optional) | 业务 PSM 精确匹配                    |
| FuzzySymbol    | string (optional) | PSM/项目名模糊匹配                   |
| Subscriber     | string (optional) | 按订阅者过滤                         |
| SubscribedOnly | bool (optional)   | 仅看订阅项目                         |
| Offset / Count | i64               | CLI 用 `--page` / `--page-size` 生成 |

返回：`ProjectList: list<Project>`、`TotalCount`。

`Project` 关键字段：`ID, PSM, Description, Creator, ServiceTreeID, AuthorUsers, LarkGroups, Status, EnableReview, ReviewerType, EnableServerlessTenant, MidPlatform`。

---

## 2. GetTask — 任务查询（`bytetask task list`）

| 字段           | 类型                   | 说明                                                 |
| -------------- | ---------------------- | ---------------------------------------------------- |
| ID             | i64 (optional)         | 任务 ID                                              |
| ProjectID      | i64 (optional)         | 项目 ID                                              |
| FuzzySymbol    | string (optional)      | 名称模糊匹配                                         |
| TaskStatus     | i64 (optional)         | CLI 用 `deleted/pending/running/paused` 映射         |
| TriggerType    | TriggerType (optional) | CLI 用 `crontab/defer/direct/manual/fixrate/mq` 映射 |
| Env            | string (optional)      | CLI `--task-env prod|ppe`                            |
| Offset / Count | i64                    | CLI 用 `--page` / `--page-size` 生成                 |

返回：`TaskList: list<Task>`，每个 Task 包含 `Trigger`、`Executors`、`Quota`、`Downstreams` 等子结构。

---

## 3. GetRecordList — 调度记录列表（`bytetask record list`）

| 字段              | 类型                 | 说明                                                     |
| ----------------- | -------------------- | -------------------------------------------------------- |
| TaskId            | i64                  | **必填**，任务 ID                                        |
| ExecutorId        | i64 (optional)       | 执行器 ID                                                |
| JobStatus         | JobStatus (optional) | CLI 用 `init/running/success/fail/cancel/triggered` 映射 |
| LogId             | string (optional)    | 调度链路 LogID                                           |
| Id                | i64 (optional)       | 单条记录 ID                                              |
| Key               | string (optional)    | 业务 unique key                                          |
| Engine            | string (optional)    | 引擎类别                                                 |
| FromTime / ToTime | i64                  | **毫秒**时间戳                                           |
| Offset / Limit    | i64                  | CLI 用 `--page` / `--page-size` 生成                     |

返回：`Count`、`RecordList: list<Record>`。

`Record` 关键字段：`ID, PSM, Env, TriggerType, JobStatus, JobType, ErrCode, ErrMsg, TriggerTime, CostTime, LogId, Pod, Process, JobName, Description, Operator, Key, StartTime, EndTime`。

---

## 4. GetRecord — 单条记录详情（`bytetask record get`）

| 字段 | 类型 | 说明    |
| ---- | ---- | ------- |
| ID   | i64  | 记录 ID |

返回：`Record`。

---

## 5. GetMapRecordList — 分片记录列表（`bytetask map-record list`）

| 字段              | 类型                 | 说明                                                     |
| ----------------- | -------------------- | -------------------------------------------------------- |
| JobID             | i64                  | **必填**，主调度 Job ID                                  |
| ID                | i64 (optional)       | 单条                                                     |
| JobStatus         | JobStatus (optional) | CLI 用 `init/running/success/fail/cancel/triggered` 映射 |
| MapType           | MapType (optional)   | CLI 用 `init/map/reduce` 映射                            |
| FromTime / ToTime | i64 (optional)       | 毫秒时间戳                                               |
| Offset / Limit    | i64                  | CLI 用 `--page` / `--page-size` 生成                     |

返回：`Count`、`MapRecordList: list<MapRecord>`，含 `MapType, MapReq, MapRet, JobStatus, ErrCode, ErrMsg, CostTime, LogId, Pod`。

---

## 6. GetTaskRecord — 任务记录组（按 RecordID 聚合，`bytetask task-record list`）

| 字段              | 类型                    | 说明                                 |
| ----------------- | ----------------------- | ------------------------------------ |
| ProjectID         | i64 (optional)          |                                      |
| TaskID            | i64 (optional)          |                                      |
| RecordID          | string (optional)       |                                      |
| Status            | list<string> (optional) | 状态过滤（CLI `--status` 逗号分隔）  |
| LogID             | string (optional)       |                                      |
| Key               | string (optional)       |                                      |
| Env               | string (optional)       | CLI `--task-env prod|ppe`           |
| EngineType        | string (optional)       |                                      |
| FromTime / ToTime | i64 (optional)          | 毫秒时间戳                           |
| Offset / Count    | i64                     | CLI 用 `--page` / `--page-size` 生成 |

返回：`TaskRecordGroups: list<TaskRecordGroup>`，每组按 RecordID 聚合多条 `TaskRecord`。

---

## 7. GetCronTimes — Cron 表达式预测（`bytetask cron-times get`）

| 字段       | 类型   | 说明                           |
| ---------- | ------ | ------------------------------ |
| Expression | string | 必填，Cron 表达式（Guru 风格） |

返回：`CronTimes: list<string>`。

---

## 8. GetTaskByPsm — 按业务 PSM 反查依赖任务（`bytetask task-by-psm list`）

| 字段 | 类型   | 说明 |
| ---- | ------ | ---- |
| Psm  | string | 必填 |

返回：`ProjectList: list<ProjectInfo>`，每个 Project 含 `Tasks: list<TaskInfo{TaskId, TaskName}>`。

---

## 枚举速查

```
TriggerType:  crontab=1 | defer=2 | direct=3 | manual=4 | fixrate=5 | mq=6
TaskStatus:   deleted=0 | pending=1 | running=2 | paused=4
JobStatus:    init=1 | running=2 | success=3 | fail=4 | cancel=5 | triggered=6
JobType:      normal=1 | shard=2 | mapReduce=3
MapType:      init=1 | map=2 | reduce=3
```

---

## 9. GetDebugStatus — Debug 状态查询（`bytetask debug-status get`）

PSM：`webcast.scheduler.job`

| 字段       | 类型 | 说明 |
| ---------- | ---- | ---- |
| TaskID     | i64  | 必填 |
| ExecutorID | i64  | 必填 |

返回：`HasLastRecord, Status (INIT/RUNNING/FINISH/ERROR), Message, LogID, FromPod, ActivitiesStatus, DebugTime`。

---

## 调用示例

```bash
# 查看任务完整配置（原始网关响应）
bytedcli bytetask task list --id 67890 --raw

# 查看某 Executor 上一次 Debug 状态
bytedcli bytetask debug-status get --task-id 67890 --executor-id 11
```
