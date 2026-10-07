---
name: bytedance-rhino
description: "Use bytedcli rhino for Rhino stress testing OpenAPI tasks: netflow record task list/get/create/delete, stress task list/get/create/execute/close/qps update/result, PSM stress switch update, raw Rhino OpenAPI calls, and the netflow-to-stress-task workflow execute workflow. Use when users mention Rhino, rhino_v2, 压测, 流量录制, 容量评估, PSM 压测开关, or replay-based stress tests."
---

# bytedcli Rhino

## When to use

- Rhino / `rhino_v2` 压测平台 OpenAPI
- 查询、创建、删除流量录制任务：`rhino netflow ...`
- 查询、创建、执行、停止、调 QPS、查看结果：`rhino task ...`
- 开启 / 关闭 PSM 压测开关：`rhino psm ...`
- 录制到发压闭环：`rhino workflow execute ...`
- 未封装接口探索：`rhino raw ...`

## 鉴权

Rhino 支持两种 token，命令行参数优先于环境变量：

```bash
export RHINO_JWT_TOKEN=<your_jwt_token>
export RHINO_TOKEN=<your_bearer_token>
```

- `--jwt-token` / `RHINO_JWT_TOKEN`：请求头 `X-Jwt-Token`，默认 host `https://perf.byted.org`
- `--token` / `RHINO_TOKEN`：请求头 `Authorization: Bearer <token>`，默认 host `https://paas-gw.byted.org`
- 两者同时存在时优先使用 JWT；`--base-url` 或 `--region cn|boe|i18n|i18n-bd|ttp|euttp` 可覆盖 host
- 默认 `--is-global 0`；需要全局网关时显式传 `--is-global 1`

## 常用命令

```bash
# 流量录制任务
bytedcli rhino netflow list --psm example.psm --page-size 20
bytedcli rhino netflow get --record-task-id 123 --psm example.psm
bytedcli rhino netflow create --payload-file record_body.json
bytedcli rhino netflow delete --record-task-id 123 --psm example.psm

# 压测任务
bytedcli rhino task list --psm example.psm --page-size 20
bytedcli rhino task get --task-id 456
bytedcli rhino task create --payload-file task_body.json
bytedcli rhino task execute --task-id 456
bytedcli rhino task close --task-id 456
bytedcli rhino task qps update --task-id 456 --qps 500
bytedcli rhino task result list --task-id 456 --page-size 10
bytedcli rhino task result get --task-id 456 --result-id 789

# PSM 压测开关
bytedcli rhino psm list --keyword example --page-size 20
bytedcli rhino psm switch update --psm example.psm --enabled true
bytedcli rhino psm switch update --psm example.psm --enabled false

# 录制到压测闭环
bytedcli rhino workflow execute --record-body @record_body.json --task-body @task_body.json --task-name demo-stress --dry-run
bytedcli rhino workflow execute --record-task-id 123 --psm example.psm --task-body @task_body.json --skip-wait

# 未封装接口
bytedcli rhino raw --method GET --path /perf/api/v2/task/list -q page_num=1 -q page_size=20 -q is_global=0
```

## Agent Guidance

- 写操作会改变线上状态，包括 `netflow delete`、`task create/execute/close/delete/qps update`、`psm switch update` 和 `workflow execute` 非 dry-run；执行前先向用户确认 `psm`、`task_id`、`record_task_id`、任务名和目标 QPS。
- 首次跑 `workflow execute` 时优先加 `--dry-run`，确认创建出的 `task_id` 后再去掉 dry-run 发压。
- POST body 字段可能随 Rhino 后端演进，复杂 body 用 `--payload-file file.json` / `--record-body @file.json` / `--task-body @file.json`，不要让 Agent 编造未知字段。
- 列表分页使用 bytedcli 标准 `--page` / `--page-size`，不要沿用旧脚本的 `--size`。
- 完整流程和 body 样例见 `references/workflow.md` 与 `references/api-endpoints.md`。
