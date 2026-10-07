---
name: bytedance-move-engine
description: "Query Move Engine migration projects, component items and Byteladder deployment metadata, TCE/FaaS consumer metadata and current filter configuration, regional MQ clusters, and migration pipelines through bytedcli. Use for 搬站平台 or byteElevator read-only discovery by project name, region, VDC, label, PSM, component type, status, owner, job, or pipeline on cn and i18n-tt, including inspection of BPM ticket metadata."
---

# bytedcli Move Engine

## 前置条件

- 一期命令全部只读
- 只支持 `--site cn` 与 `--site i18n-tt`，不做跨站 fallback
- 请求使用目标站点的 ByteCloud 用户 JWT；首次调用前先执行 `bytedcli --site <site> auth login`
- `--json` 是全局参数，放在 `move-engine` 前

## Quick start

```bash
# 项目
bytedcli --site cn move-engine project list --src-region sample-region
bytedcli --site cn move-engine project get --project-id 1
bytedcli --json --site i18n-tt move-engine project search --psm example.service.api --product-type tce

# 组件 item
bytedcli --json --site cn move-engine item list --project-id 1 --product-type tce --page 1 --page-size 20
bytedcli --site cn move-engine item projection list --project-id 1 --product-type tce --field deploy_status
bytedcli --json --site cn move-engine item deployment get --project-id 1 --product-type tce --job-id 2 --psm example.service.api

# 消费者与 MQ 集群
bytedcli --json --site cn move-engine consumer group list --project-id 1 --product-type tce --psm example.consumer.service
bytedcli --site i18n-tt move-engine consumer mq-cluster list --region sample-region

# 流水线
bytedcli --site cn move-engine pipeline get --project-id 1 --pipeline-id sample-pipeline-id
bytedcli --site cn move-engine pipeline list --project-id 1
bytedcli --json --site cn move-engine pipeline search --project-id 1 --psm example.service.api --product-type tce
```

## Agent Guidance

- 不知道 project ID 时，优先用 `project search --psm` 或 `project list --keyword`
- `item list` 的 `--page`、`--before-id`、`--after-id` 三选一；都不传时默认第 1 页
- 常用 item 过滤器直接用显式参数；高级过滤用 `--filters-json` 或 `--filters-file`，两者不能同时使用
- `item deployment get` 的四个选择器都必填；JSON 中的 `deployment.bpm_external` 可用于读取 BPM 工单 ID 和链接
- `consumer group list --product-type` 只接受 `tce|faas`；`--psm` 可重复或逗号分隔
- `pipeline search` 传 `--psm` 时必须同时传 `--product-type`；无过滤条件时使用 `pipeline list`
- pipeline ID 是字符串，可能是 UUID，不要按整数解析

## References

- 需要完整命令、过滤器 schema 和枚举值时，读取 `references/move-engine.md`
- 不确定 bytedcli 安装方式、`--site` / `--json` 等全局参数或 HTTP 调试方式时，读取 `../../invocation.md`
- 命令执行失败，出现版本过期、缺少命令/参数、未认证或网络权限问题时，读取 `../../troubleshooting.md`
