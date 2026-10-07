---
name: bytedance-maxwell
description: "Maxwell Sample Center read-only API skill. Use when tasks mention Maxwell, Sample Center, sample metadata, sample schema, sample preview, sample job, joiner, backfill, lineage, monitor, or resource group queries. Provides explicit bytedcli commands for the reviewed read-only API surface."
---

# bytedcli Maxwell

本 Skill 用于调用 Maxwell Sample Center 已审核的只读接口。命令入口是 `bytedcli maxwell`，每个接口都暴露为显式资源和动作命令，不提供任意 endpoint-id 直连调用。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要结构化输出时，把 `--json` 放在 `maxwell` 前面：`bytedcli --json maxwell ...`

## Agent Guidance

- 默认执行 Maxwell 查询时调用 `bytedcli maxwell ...`；不要把用户侧示例改写成 `node dist/bytedcli.js ...`。
- 只有在 bytedcli 仓库内明确验证当前分支本地编译产物时，且已先执行构建命令，才使用 `node dist/bytedcli.js ...`。
- 若需要确认当前全局命令是否指向本仓，先运行 `realpath "$(which bytedcli)"`；指向本仓 `dist/bytedcli.js` 时仍优先直接调用 `bytedcli ...`。
- 从 Sample Center URL 解析 `site`、`region`、样本名或任务标识后，直接执行对应的只读命令。
- 默认先执行目标查询。bytedcli 会复用共享 SSO session；不要为不同 Maxwell 资源重复登录。
- 收到 `MAXWELL_AUTH_ERROR` 时，直接处理错误 details 里的授权 challenge：
  1. `login_status=success`：重试原命令。
  2. `login_status=pending`：优先把 `lark_applink_url` 作为可点击授权入口发给用户；没有该字段或链接不可用时使用 `verification_uri_complete`；两种链接都不可用时，上传 `qr_image_path` 对应的图片。执行返回的 `complete_command` 直到登录成功，再重试原命令。
  3. `login_status=expired`：`complete_command` 对应的 challenge 已被 CLI 删除，不能重复执行它；重试原 Maxwell 命令以生成新的 `MAXWELL_AUTH_ERROR`、授权链接和 `complete_token`。
- `lark_applink_url` 会在 PC 飞书中打开同一个 SSO 登录 challenge。`verification_uri_complete` 是浏览器授权链接。`qr_image_path` 是 Agent 运行环境的本地文件，只能读取并上传图片内容，不能把路径原样发给用户。
- Agent 执行查询、登录轮询和查询恢复；不要让用户执行 Maxwell 命令或回传 JSON。
- 全程只读。不要执行创建、更新、删除、上线、停止、回滚、订阅、编译或实例操作。

## Quick Start

```bash
# 查看已支持的只读接口
bytedcli maxwell endpoint list
bytedcli maxwell endpoint list --resource sample

# 查询样本列表 / 详情 / schema / 分区
bytedcli maxwell sample list --query-json '{"page_no":1,"page_size":20}'
bytedcli maxwell sample get --name demo-sample
bytedcli maxwell sample schema list --name demo-sample --query-json '{"page_no":1,"page_size":20}'
bytedcli maxwell sample partition list --name demo-sample --query-json '{"page_no":1,"page_size":20}'
bytedcli maxwell dump-task list --name demo-sample
bytedcli maxwell sample monitor list --name demo-sample --sample-type MAIN_TABLE

# 跨区域样本详情：--site 选择 Sample Center API origin，--region 独立写入业务 header
bytedcli --site i18n --json maxwell sample get --region va --name demo-sample
bytedcli --site eu-ttp --json maxwell sample get --name demo-sample
bytedcli --site us-ttp --json maxwell sample get --name demo-sample
bytedcli --site boe --json maxwell sample get --name demo-sample

# Joiner / Backfill / 任务 / 资源组查询
bytedcli maxwell joiner list
bytedcli maxwell joiner get --name demo-joiner
bytedcli maxwell joiner compile get --name demo-joiner --compile-name demo-compile
bytedcli maxwell joiner version list --name demo-joiner
bytedcli maxwell feature-backfill list
bytedcli maxwell label-backfill history list --name demo-backfill
bytedcli maxwell task list
bytedcli maxwell resource-group list

# 只读校验 / 预览 / 对比
bytedcli maxwell query sample-preview get --query-json '{"sample_name":"demo-sample"}'
bytedcli maxwell query sql validate --body-json '{"sql":"select 1"}'
bytedcli maxwell work-order validate --body-json '{"name":"demo-work-order"}'
bytedcli maxwell joiner version compare --name demo-joiner --body-json '{"base_version":"v1","target_version":"v2"}'
```

## Notes

- `maxwell endpoint list` 是发现入口，返回 command、HTTP method、path 和 BAM endpoint id。
- `--site` 是全局参数，决定 Sample Center host；`--region` 是 Maxwell 业务上下文，会写入 `Byte-Region`。不要用全局 `--http-header` 传 region。
- 已验证的默认 region：`--site cn` 默认 `cn`，`--site eu-ttp` 默认 `eu`，`--site us-ttp-bdee` `--site us-ttp` 默认 `tx`；`i18n` 这类一站多 region 的场景请显式传 `--region va|sg|...`。
- `--site cn`、`--site boe`、`--site i18n` 与 `--site i18n-tt` 的 Sample Center backend 使用 `Byte-Region` 和 `Byte-Staff-Name` 请求头识别业务上下文，不依赖 Maxwell Cookie 或 ByteCloud JWT；staff name 取当前 bytedcli 登录后持久化的 username。`i18n` 与 `i18n-tt` 是一站多 region 场景，必须显式传 `--region`。其他 site 仍按各自既有的 session/JWT 认证链路执行。
- 已暴露显式 option 的必填查询参数优先使用对应 option；只在接口需要额外筛选、且该字段尚未提供显式 option 时才使用 `--query-json`。POST 只读校验接口的请求体放在 `--body-json`。
- 路径参数使用显式 option，例如路径里的 `:compileName` 对应 `--compile-name`。
- GET 接口不接受 `--body-json`。
- 已排除创建、更新、删除、上线、停止、回滚、订阅、编译、实例操作等非只读接口。

## References

- `../../invocation.md`
- `../../troubleshooting.md`
