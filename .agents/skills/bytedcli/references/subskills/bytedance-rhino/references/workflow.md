# Rhino Flow 工作流

`bytedcli rhino workflow execute` 串联：创建或复用流量录制任务、等待录制完成、创建压测任务、可选发压。

## 新录制并 dry-run

```bash
bytedcli rhino workflow execute \
  --record-body @record_body.json \
  --task-body @task_body.json \
  --task-name demo-stress \
  --dry-run
```

## 复用已有录制

```bash
bytedcli rhino workflow execute \
  --record-task-id 123 \
  --psm example.psm \
  --task-body @task_body.json \
  --skip-wait
```

## record_body.json 示例

```json
{
  "psm": "example.psm",
  "dataset_name": "demo-record",
  "dataset_desc": "demo record task",
  "region": "China-North",
  "cluster": "default",
  "env": "canary",
  "sample_rate": "1",
  "record_duration": 600,
  "service_type": 0,
  "record_type": 0
}
```

## task_body.json 示例

```json
{
  "task_name": "demo-stress",
  "psm": "example.psm",
  "scene_type": 1,
  "type": 6,
  "hosts": {
    "psm": "example.psm",
    "region": "China-North",
    "cluster": "default",
    "env": "prod",
    "host_type": 2,
    "ip_port": []
  },
  "qps_config": {
    "target_qps": 200,
    "duration": 300,
    "warm_up": 30
  },
  "description": "created by bytedcli rhino"
}
```

## 注意事项

- `record_status=2` 视为录制完成，`3/4/5` 视为异常终态。
- 非 dry-run 会真实调用 `task execute` 发起压测，执行前必须确认目标服务和 QPS。
- Rhino 网关通常有接口 QPS 限制，不要在循环里高频调用。
