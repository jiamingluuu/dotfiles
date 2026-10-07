# BABI Platform 监控排障

1. 用 `bytedcli babi platform monitor ... --help` 确认必填参数。
2. 加全局 `--dry-run` 检查目标路径、`domain: babi;v1`、实体 ID、监控项和时间范围。
3. 仍不清楚时加 `--debug`，并保留服务端 `logId` / `RequestId`。

| 现象 | 检查 |
|---|---|
| 列表为空 | 核对 Product ID、`entity_type`、监控项以及开闭区间 |
| 详情为空 | 核对 `alarm_id` 是否属于传入实体范围 |
| 负责人为空 | 查看返回的任务选择和 fallback，不能把空结果直接写成无人负责 |
| 参数校验失败 | 时间戳必须为正，结束时间必须大于开始时间，分页从合法范围开始 |

报告空结果时写明查询实体、监控项、时间范围和 RequestId。不要把后端空数据、权限失败、请求未发送和展示遗漏混为一谈。
