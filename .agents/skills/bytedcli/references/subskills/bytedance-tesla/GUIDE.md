---
name: bytedance-tesla
description: "Operate Tesla test platforms via bytedcli: Tesla RM task/plan workflows and TeslaX folder/env-tag/report/plan commands under bytedcli tesla. Use when tasks mention Tesla, TeslaX, RM, Repository Mode, test plan, test task, 触发测试, 测试计划, 失败归因, plan stats, enable_tesla, or a TCE_ Tesla token."
---

# bytedcli Tesla (RM 自动化测试平台)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

Tesla RM（Repository Mode）是 ByteDance 内部的自动化测试执行平台。通过静态 Tesla RM token 认证，无需 SSO。

## When to use

- 按测试计划触发测试任务（`plan start-task`），或触发并等待完成、输出摘要（`plan run-task`）
- 查询任务状态与完整元数据（`task get`，自动合并失败用例明细 / Plan Name / Duration / Web URL）
- 列出 / 搜索任务（按计划、时间范围、状态过滤）
- 取消运行中的任务（`task cancel`）
- 查看任务失败归因分析（`task get --with-analysis`，并发合并完整归因条目）
- 管理 Tesla RM 测试计划：查看详情、列表、窗口聚合统计、创建、更新（部分更新）、删除
- 管理 TeslaX 资源：`tesla folder list`、`tesla env-tag list`、`tesla report list/case`、`tesla plan list/create/get/records/update/delete/trigger`

## Prerequisites

- 调用方式见上文“如何调用 bytedcli”
- 需要 Tesla RM token，优先级：`--token TCE_xxx` > `BYTEDCLI_TESLA_TOKEN` 环境变量 > 配置文件 token（项目级覆盖用户级）
- 配置两层、均可放 token（项目级优先）：用户级 `~/.local/share/bytedcli/data/tesla.yaml`；项目级 `.tesla/config.yaml`（仅读取当前目录，不向上查找，已被 gitignore，token 不进版本库），可按仓库覆盖 token / `base` / `default_rm` / `default_plan_id`
- Base URL 优先级：`--base <url>` > `BYTEDCLI_TESLA_BASE_URL` > 配置文件中 `base`（项目级覆盖用户级）> 默认 `http://tesla.bytedance.net/rm`

## 任务管理

```bash
# 触发新任务（动词跟着输入资源 plan 走，返回 task_id）
bytedcli tesla plan start-task --id 507863 --token TCE_xxx

# 触发并等待完成（start → 轮询 → 摘要报告）
bytedcli tesla plan run-task --id 507863 --token TCE_xxx --env-label ppe

# 查看完整任务元数据（自动合并失败用例明细 / Plan Name / Duration / Web URL）
bytedcli tesla task get --id 289935400 --token TCE_xxx
bytedcli tesla task get --id 289935400 --with-analysis --token TCE_xxx   # 同时拉失败归因合并到结果

# 列出任务（支持计划 / 时间 / 状态过滤）
bytedcli tesla plan list-task --id 507863 --since '7d ago' --token TCE_xxx

# 取消
bytedcli tesla task cancel --id 289935400 --token TCE_xxx
```

## 测试计划管理

```bash
# 查看详情（自动并行抓近 30 天的执行 stats；--since/--until/--trigger-type 可调时间窗与过滤）
bytedcli tesla plan get --id 507863 --token TCE_xxx
bytedcli tesla plan get --id 507863 --since '7d ago' --token TCE_xxx

# 在指定 repo 下列出 / 创建 plan（动词跟 repo 走，--id 即 repo_id，可从 --rm 兜底）
bytedcli tesla repo list-plan --id 3878 --token TCE_xxx
bytedcli tesla repo create-plan --id 3878 --name demo-plan --token TCE_xxx

# 更新（部分更新，只改传入字段；后端要求每次更新带 git_branch）/ 删除
bytedcli tesla plan update --id 507863 --name new-name --git-branch main --token TCE_xxx
bytedcli tesla plan update --id 507863 --body @patch.json --token TCE_xxx   # 没有专用 flag 的字段
bytedcli tesla plan delete --id 507863 --token TCE_xxx
```

## TeslaX 资源与计划

```bash
# TeslaX folder / envTag
bytedcli --json tesla folder list --space-id 1000 --branch master
bytedcli --json tesla env-tag list --space-id 1000

# TeslaX report
bytedcli --json tesla report list --space-id 1000 --task-id "<task-id>" --bearer-token "<bearer-token>"
bytedcli --json tesla report case --space-id 1000 --task-id "<task-id>" --case-id 123 --bearer-token "<bearer-token>"

# TeslaX-only plan CRUD
bytedcli tesla plan list --space-id 1000 --psm example.psm
bytedcli tesla plan get --space-id 1000 --plan-id 2000
bytedcli tesla plan records --space-id 1000 --plan-id 2000
bytedcli tesla plan create --space-id 1000 --plan-name "sample plan" --psm example.psm --replay-env sample_env --execute
bytedcli tesla plan update --space-id 1000 --plan-id 2000 --plan-name "updated sample plan" --execute
bytedcli tesla plan delete --space-id 1000 --plan-id 2000 --execute
bytedcli tesla plan trigger --space-id 1000 --plan-id 2000 --payload '{}' --execute
```

- `tesla plan create` 使用 `--space-id` 时创建 TeslaX-only 计划，默认写入 `enable_ftf=false`、`enable_tesla=true`、`platform=teslax`。
- `tesla plan get/update/delete` 同时支持 Tesla RM 和 TeslaX：传 `--id` 时走 Tesla RM，传 `--space-id + --plan-id` 时走 TeslaX。

## JSON 输出

所有命令支持全局 `--json`，仅输出 JSON：

```bash
bytedcli --json tesla plan list-task --id 507863 --token TCE_xxx
bytedcli --json tesla plan get --id 507863 --token TCE_xxx
```

## 参考

- `references/tesla.md` — 各命令完整示例、认证与 `tesla.yaml` 配置格式
- `references/teslax/overview.md` — TeslaX folder/env-tag/report/plan 命令总览
- `references/teslax/plan/plan-crud.md` — TeslaX plan/folder/envTag/report API 与常用命令
- `references/teslax/plan/plan-api-idl.md` — TeslaX plan create/update/get/delete IDL 字段口径
- `references/teslax/plan/plan-scaffold-guide.md` — TeslaX plan 深层 payload scaffold 模板
- `references/teslax/report/report-openapi.md` — TeslaX report list/case OpenAPI 映射
