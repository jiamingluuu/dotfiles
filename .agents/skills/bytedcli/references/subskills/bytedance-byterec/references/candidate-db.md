# Candidate DB / CandsDB

## 能力范围

- 查询 Candidate DB 列表、详情、schema、元信息、生成的 sinker 配置和监控链接。
- 按 region 与 label 精确查询候选记录，或抽样查看候选数据。
- 查询 Candidate DB 绑定的模型。
- 查询 Candidate DB 支持的 region、可选 TBase source 和 schema。
- 创建、更新或删除 Candidate DB；写操作默认 dry-run，只有显式 `--yes` 才提交。
- 用户给出 `/candidate_db/detail/<id>?namespace=<namespace>` 页面 URL 时，直接用 `--url` 解析 ID、namespace 和控制面。

## 选择器与前置条件

- 详情类命令使用 `--id` 或 `--url` 二选一；完整 URL 会解析 ID、namespace 和可信控制面 host。
- `record get` / `sample list` 未传 `--region` 时使用详情中的第一个 region；显式 region 必须属于该 Candidate DB。

## Detail Tab 映射

| 页面 Tab | CLI                        | 行为                                         |
| -------- | -------------------------- | -------------------------------------------- |
| Overview | `candidate-db get`         | 返回详情、schema、元信息、sinker 配置和链接  |
| Query    | `candidate-db record get`  | 按 region + label 读取一条记录               |
| Sample   | `candidate-db sample list` | 按 region 抽样记录                           |
| Monitor  | `candidate-db monitor get` | 返回详情已有的 Grafana/TBase statistics 链接 |
| Model    | `candidate-db model list`  | 返回绑定的 Fermat 模型                       |

页面代码还声明了 Alert 枚举，但当前详情页没有渲染组件或接口，因此不要虚构 Alert 命令。

## Quick start

```bash
# 列表和 Overview
bytedcli --site i18n-tt byterec candidate-db list --namespace demo_namespace
bytedcli --json byterec candidate-db get --url "$CANDIDATE_DB_URL"

# Query Tab
bytedcli --site i18n-tt byterec candidate-db record get \
  --id 12345 --region sg --label sample-label

# Sample Tab
bytedcli --site i18n-tt byterec candidate-db sample list \
  --id 12345 --region sg --sample-count 10

# Monitor / Model Tab
bytedcli --site i18n-tt byterec candidate-db monitor get --id 12345
bytedcli --site i18n-tt byterec candidate-db model list \
  --id 12345 --namespace demo_namespace --page 1 --page-size 20

# 创建或编辑前发现合法的 region、source 和 schema
bytedcli --site i18n-tt byterec candidate-db const get
bytedcli --site i18n-tt byterec candidate-db source list --namespace demo_namespace
bytedcli --site i18n-tt byterec candidate-db schema list --namespace demo_namespace

# 创建、更新、删除：以下命令均只生成 dry-run 计划
bytedcli --site i18n-tt byterec candidate-db create \
  --namespace demo_namespace --name demo_candidate_db --schema-name demo_schema \
  --source-names data.tbase.demo.sg --description 'demo candidate db'
bytedcli --site i18n-tt byterec candidate-db update \
  --id 12345 --description 'updated demo'
bytedcli --site i18n-tt byterec candidate-db delete --id 12345
```

## 写操作安全

- `create`、`update`、`delete` 默认只输出 `dry_run: true`、method、path、body 和目标摘要，不发送写请求。
- 只有用户明确要求提交并确认 dry-run 目标与 payload 后，才能在同一命令上追加 `--yes`。
- 写请求禁用自动重试；结果不确定时不要重复提交，先用 `candidate-db get` 回读。
- `update` 和 `delete` 会先读取当前资源，确保计划对应明确目标。
- `create --do-bucket` 必须同时传 `--foreign-key`；默认关闭，也可显式传 `--no-do-bucket`。
- 不接受任意 raw API path；只使用结构化 Candidate DB 命令。

## 输出说明

- `candidate-db get` 返回 Overview 全量结构；文本模式展示元数据、监控链接和 `sinker.yaml`。
- `record get` 与 `sample list` 保留 schema-dependent 动态 JSON；文本模式提供可读摘要。
- `monitor get` 只返回 Candidate DB 详情已有链接，不代理 Grafana 查询。
- `list`、`model list`、`source list`、`schema list` 返回 `page`、`page_size`、`current_count`、`total` 与 `has_more`。
- `sample list` 使用 `--sample-count` 控制本次抽样数量，并返回 `page: 1`、`page_size`、`current_count` 与 `truncated`；抽样接口没有全局总数。
- 写命令默认返回确定性的 dry-run `plan`；显式 `--yes` 后返回提交结果。

## 实现参考

- `docs/domains/byterec/byterec-candidate-db-api-research.md`
- `src/cli/commands/byterec/candidate-db.ts`
- `src/cli/handlers/byterec/candidate-db.ts`
