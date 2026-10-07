---
name: merlin-tracking-experiment
description: 查询和分析 Merlin/Seed Tracking 实验数据的完整工具集：项目与 Run 管理、Metrics 列表与时序数据、Run 配置/摘要/标量曲线对比、实验图表面板、表格数据、Weave LLM/Agent 链路追踪、趋势分析。当用户说"查看 Tracking 指标/loss 趋势/训练曲线/实验图表/experiment panel/metrics 分析/指标对比/Run 配置/Run 摘要/标量曲线/表格数据/Weave 调用/Trace 追踪/项目列表/Run 列表"时使用。
---

# Tracking 实验与指标分析

查询和分析 Merlin Tracking 实验数据，包括项目与 Run 管理、Metrics 查询与对比、实验图表、表格数据、Weave 链路追踪、趋势分析。

## 前置条件

- `bytedcli merlin` 可用

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

如果出现认证错误（401/403），运行 `bytedcli auth login`。

---

## 1. 项目与 Run 管理

### 1.1 列出项目

分页列出当前用户可见的 Tracking 项目，可按名称、关键字、角色筛选。

```bash
bytedcli merlin tracking projects list --filter '{"keyword":"my-project"}' --page-size 20
```

`--filter` 支持：`keyword`（模糊匹配名称与描述）、`name`（精确匹配）、`role`（`MyCreated` / `MyInvolved` / `MyFavorite`）。`--options` 控制派生字段返回：`include_is_favorited`、`include_run_count`、`include_url`。分页用 `--page-size` 限制条数、`--page-token` 传上次响应的 `next_page_token` 翻页；走外部数据源时用 `--region` 指定查询 region。

### 1.2 获取项目详情

获取单个项目的元数据与可见范围信息。

```bash
bytedcli merlin tracking projects get --id project_xxx
```

`--id` 为项目 ID（必填）。可选 `--options '{"include_run_count":true,"include_url":true}'` 在响应中附带派生字段（`include_is_favorited` / `include_run_count` / `include_url`）。

### 1.3 列出 Run

分页列出某个项目下的 Run（实验运行记录）。

```bash
bytedcli merlin tracking runs list --filter '{"project_ids":["project_xxx"]}' --page-size 20
```

`--filter` 支持：`project_ids`（项目 ID 白名单）、`ids`（Run ID 白名单）、`keyword`（模糊匹配 name / run_id / user_id / outer_id）、`name_keyword`（Run 名称关键字）、`my_created`（仅自己创建的）、`status`（Run 状态）、`outer_ref`（外部系统引用，`{"type":"merlin","id":"<job_id>"}` 表示按 Merlin job id 反查）。`--options` 控制派生字段：`include_config` / `include_summary` / `include_url` / `include_outer_url`。分页用 `--page-size` / `--page-token`。

### 1.4 获取 Run 详情

获取单个 Run 的配置、摘要、标签等详细信息。

```bash
bytedcli merlin tracking runs get --id run_xxx --project-id project_xxx
```

`--id`（Run ID）与 `--project-id`（所属项目 ID）均为必填。可选 `--options` 附带派生字段。

---

## 2. 指标查询

### 2.1 列出 Metrics（Entity）

列出给定 Project + Run 下已上报的 Metrics（entity）。`--project-run-ids` 为必填数组，每个元素含 `project_id` / `run_id` / `region`（三者均必填，`region` 一般填服务部署区域，如 `cn`）。

```bash
bytedcli merlin tracking run-entities list --project-run-ids '[{"project_id":"project_xxx","run_id":"run_xxx","region":"cn"}]'
```

可选 `--name` 按 entity 名称过滤。若手头只有 Merlin job id，先用 `tracking runs list --filter '{"outer_ref":{"type":"merlin","id":"<job_id>"}}'` 反查出 `project_id` / `run_id`，再填入 `--project-run-ids`。指标的时序曲线数据通过第 3 节的 `tracking run-scalar-charts get` 获取（v4 已移除单独的 entity-step 时序下载接口）。

### 2.2 获取 Run 配置项

按 Project + Run 列表读取配置项（config）键值。`--project-run-ids` 与 `--config-keys` 均为必填；`--config-keys` 传要查询的 config key 列表。

```bash
bytedcli merlin tracking run-configs list --project-run-ids '[{"project_id":"project_xxx","run_id":"run_xxx","region":"cn"}]' --config-keys '["learning_rate","batch_size"]'
```

### 2.3 获取 Run 摘要

按 Project + Run 列表读取摘要（summary）指标键值。`--project-run-ids` 与 `--summary-keys` 均为必填；`--summary-keys` 传要查询的 summary key 列表。

```bash
bytedcli merlin tracking run-summaries list --project-run-ids '[{"project_id":"project_xxx","run_id":"run_xxx","region":"cn"}]' --summary-keys '["best_loss","final_accuracy"]'
```

---

## 3. 标量曲线对比

获取多个 Run 的标量曲线数据，用于自定义图表和跨 Run 对比。

```bash
bytedcli merlin tracking run-scalar-charts get --project-run-ids '[{"ProjectId":"project_xxx","RunId":"run_aaa","Region":"cn"},{"ProjectId":"project_xxx","RunId":"run_bbb","Region":"cn"}]' --xaxis '{"Name":"Step"}' --yaxis '{"Metrics":[{"Name":"loss"}]}'
```

注意本接口的 JSON 字段名为 PascalCase：`--project-run-ids` 元素用 `ProjectId` / `RunId` / `Region`（均必填），`--xaxis` 用 `{"Name":"Step"}`，`--yaxis` 用 `{"Metrics":[{"Name":"loss"}]}`。可选 `--step-range '{"Min":0,"Max":100}'` 限定 step 区间；`--option` 控制曲线处理，如 `{"RemoveAbnormalValue":true,"Smooth":{"Ema":0.6},"DisableDownsample":true}`（`Smooth` 支持 `Ema` / `Sma` / `Cma`，`DisableDownsample:true` 返回完整曲线而非降采样点）。

---

## 4. 实验图表（Experiment Insight）

### 4.1 获取 Experiment Group View

根据实验视图 SID 获取 Experiment Group View 详情。

```bash
bytedcli merlin tracking get-group-view --experiment-group-view-sid '<view_sid>'
```

### 4.2 搜索实验图表面板

查询实验图表基础信息，包括图表名称、x 轴范围、legends 列表。

```bash
bytedcli merlin tracking search-panel --insights '[{"insight_sid":"<insight_id>","experiment_group_sid":"<group_id>"}]'
```

每个 legend 是图表中一条线的唯一标识，可用于后续获取该线的详细数据。

### 4.3 获取图表时序数据

获取实验图表中特定 legend 的详细时序数据。

```bash
bytedcli merlin tracking get-timeseries --insight-sid '<insight_id>' --experiment-group-sid '<group_id>' --filters '{"legends":["<legend_id_1>","<legend_id_2>"],"step_range":[0,10000]}'
```

`legends` 和 `step_range` 通常直接复用 `search-panel` 返回的值。

---

## 5. 表格数据

### 5.1 列出 Run 的表格

列出给定 Run 下已上报的表格类实体。

```bash
bytedcli merlin tracking run-tables list --project-run-ids '[{"project_id":"project_xxx","run_id":"run_xxx","region":"cn"}]'
```

`--project-run-ids` 为必填数组（元素含 `project_id` / `run_id` / `region`）。可选 `--name`（表名模糊过滤）、`--page-size` / `--page-token`（分页）、`--options`（是否返回表格数据内容）。

### 5.2 获取表格行数据

读取单个 Run 中某张表格的分页行数据与列名。

```bash
bytedcli merlin tracking run-tables get --project-id project_xxx --run-id run_xxx --name '<table_name>'
```

`--name` 须与 `run-tables list` 返回的表名一致，`--project-id` / `--run-id` / `--name` 均为必填。可选 `--options '{"include_data":true,"max_rows":1000}'` 返回表格数据内容（`max_rows` 未传默认 10000，最大 50000，超出会截断并在 `data.truncated` 中体现）。

---

## 6. Weave 链路追踪

Weave 用于追踪 LLM/Agent 的调用链路，分析输入输出、执行状态和调用树。

### 6.1 列出 Weave Calls

列出符合条件的 Call 记录。

```bash
bytedcli merlin tracking list-weave-calls --project-id project_xxx --filter '{"trace_ids":["<trace_id>"]}'
```

`filter` 支持：`call_ids`、`trace_ids`、`thread_ids`、`start_time_from` / `start_time_to`（Unix 时间戳）。

### 6.2 获取单个 Weave Call

查询单个 Call 的详情（输入输出、状态等）。

```bash
bytedcli merlin tracking get-weave-call --project-id project_xxx --call-id '<call_id>'
```

可选 `start_date`（格式 `YYYY-MM-DD`）缩小检索范围。

### 6.3 获取 Weave Trace

查询某次 Trace 的调用树（根 Call 与子 Call 嵌套），用于分析 LLM/Agent 完整链路。

```bash
bytedcli merlin tracking get-weave-trace --project-id project_xxx --trace-id '<trace_id>'
```

可选参数：`sub_tree_root_call_id`（仅拉取以该 Call 为根的子树）、`time_range`（时间范围）、`external_region`（跨区场景）。

---

## 7. 趋势分析

下载 CSV 数据后，使用分析脚本进行趋势与波动分析：

```bash
python3 skills/bytedance-merlin/references/merlin-tracking-experiment/scripts/analyze_metrics_csv.py \
  loss_data.csv --state_dir ./metrics_state --metrics loss --smooth 21 --out ./loss_report.html
```

固定复用 `--state_dir` 支持增量分析，避免重复处理已分析区间。

---

## 脚本

| 脚本 | 路径 | 作用 |
|------|------|------|
| CSV 指标分析 | `scripts/analyze_metrics_csv.py` | 趋势与波动分析 + HTML 曲线图 |
| CSV 处理工具 | `scripts/csv_metrics_utils.py` | CSV 列裁剪与多文件拼接 |
| 旧版分析脚本 | `scripts/analyze_metrics.py` | 兼容用途 |

### 使用示例

```bash
# 输出摘要
python3 scripts/analyze_metrics_csv.py https://example.com/metrics.csv --metrics loss accuracy

# 生成可视化报告
python3 scripts/analyze_metrics_csv.py ./metrics.csv --out ./metrics_report.html --smooth 21

# 对比多个 run
python3 scripts/analyze_metrics_csv.py run1.csv run2.csv --metrics loss --out compare.html --ema 0.2

# CSV 列裁剪
python3 scripts/csv_metrics_utils.py select ./metrics.csv --columns step,loss,accuracy --out ./small.csv

# 拼接多个 run
python3 scripts/csv_metrics_utils.py concat run1.csv run2.csv --out ./all_runs.csv
```

---

## 常见工作流

### 从零开始查看某个任务的 loss 曲线

1. `run-entities list`（传 `--project-run-ids`）→ 获取 Metrics 列表
2. `run-scalar-charts get` → 拉取 loss 的标量曲线数据
3. `analyze_metrics_csv.py` → 生成趋势报告

### 跨 Run 对比指标

1. `projects list` → 找到目标项目
2. `runs list` → 列出项目下所有 Run
3. `run-scalar-charts get` → 拉取多个 Run 的标量曲线数据并对比

### 查看 Run 的训练配置差异

1. `run-configs list` 在 `--project-run-ids` 传入多个 Run → 批量获取配置
2. 对比不同 Run 的配置差异

### 分析 Weave LLM 调用链路

1. `list-weave-calls` → 找到目标 Call
2. `get-weave-trace` → 获取完整调用树
3. `get-weave-call` → 查看单个 Call 的输入输出细节

---

## 注意事项

- `tracking run-entities list` 通过 `--project-run-ids`（`project_id` / `run_id` / `region`）定位 Metrics；只有 Merlin job id 时先用 `tracking runs list --filter '{"outer_ref":{"type":"merlin","id":"<job_id>"}}'` 反查 Run
- `run-configs list` / `run-summaries list` 的 `--config-keys` / `--summary-keys` 均为必填，传要查询的 key 列表
- 如果某个指标获取失败，跳过并记录
- 关注异常波动（如 loss 突然上升）
- Weave 相关操作需要有效的 JWT 身份凭证

---

## 关联技能

- `job-monitor`（`seed/rd-skills`）：任务监控总调度
- `merlin-job-devops`：查看任务日志
