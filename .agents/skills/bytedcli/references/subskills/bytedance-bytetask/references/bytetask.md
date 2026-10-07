# ByteTask

ByteTask 调度系统控制面只读查询，覆盖项目、任务、调度记录、分片记录、任务记录组、业务 PSM 反查、Cron 触发时间预测和 Debug 状态查询。

```bash
# 项目和任务
bytedcli bytetask project list --fuzzy demo --page-size 20
bytedcli bytetask task list --project-id 12345 --task-status running --page-size 50

# 调度记录
bytedcli bytetask record list --task-id 67890 --job-status fail --page-size 20
bytedcli bytetask record get --id 99999
bytedcli bytetask map-record list --job-id 12345 --page-size 20
bytedcli bytetask task-record list --record-id demo-record --task-id 67890

# 诊断辅助
bytedcli bytetask task-by-psm list --psm demo.live.sample
bytedcli bytetask cron-times get --expression "0 0 * * *"
bytedcli bytetask debug-status get --task-id 67890 --executor-id 11
```

## Command Surface

- `bytetask project list`：按项目 ID、PSM、模糊词、订阅人查询项目。
- `bytetask task list`：按任务 ID、项目 ID、任务状态、触发类型、任务环境查询任务。
- `bytetask record list`：按 TaskID、执行器、状态、LogID、时间区间查询执行记录。
- `bytetask record get`：按记录 ID 查询单条执行记录详情。
- `bytetask map-record list`：按 JobID 查询分片调度记录。
- `bytetask task-record list`：按 RecordID、LogID、Key 等查询任务记录组。
- `bytetask task-by-psm list`：按业务 PSM 反查依赖的 ByteTask 任务。
- `bytetask cron-times get`：解析 Cron 表达式的预计触发时间。
- `bytetask debug-status get`：查询指定 TaskID + ExecutorID 的 Debug 状态。

## Notes

- 当前只支持只读查询；写操作、状态变更、重跑、暂停、恢复、Debug 触发等需求请转到 ByteTask 平台或正式变更流程。
- 站点跟随全局 `--site` / `BYTEDCLI_CLOUD_SITE`，当前支持 `cn` 与 `boe`。
- `BYTETASK_PERMISSION_ERROR` 表示当前用户缺少 BAM / 接口测试平台对 `webcast.platform.scheduler` 的 PSM 调用权限，不是普通登录态失效。请到 BAM 平台 https://cloud.bytedance.net/bam/rd/webcast.platform.scheduler/ 申请 `psm=webcast.platform.scheduler` 的调用权限，申请理由写「使用 bytedcli skill」。
- `--task-status` 使用 `deleted|pending|running|paused`，`--job-status` 使用 `init|running|success|fail|cancel|triggered`，`--task-env` 使用 `prod|ppe`。
- 默认文本输出业务摘要；加 `--raw` 输出网关原始响应；结构化输出使用全局 `--json`。
- 详细字段、后端方法和枚举见 `bytedance-bytetask` skill 的 `references/api-reference.md`。
