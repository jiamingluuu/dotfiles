# Lego release actions

<!-- Load: MANDATORY for pipeline/scope/order/confirm/step-info actions; CONDITIONAL for end-to-end compile-and-release after compilation succeeds; Do NOT Load for plugin-only registration, branch, commit, or compile-detail tasks. -->

## 发布候选发现

创建工单且需要用户选择版本、流水线或发布域时，先确认 site 和 region，再把 `plugin version list`、`pipeline list`、`scope list` 作为一个候选发现阶段。

- `plugin version list` 会在 service 层先查询 plugin detail；查询成功即可作为插件存在性验证。只有任务需要展示插件详情时才单独调用 `plugin get`。
- 运行时支持并行 tool call 时并行执行三项查询；不支持时按 version → pipeline → scope 顺序执行。串行路径中某项失败后仍继续其余只读查询。不要用后台 shell、临时文件或重试机制模拟并行。
- 等待三项查询全部结束后再处理结果。任一查询失败时，保留并展示其它成功结果和失败项，把候选集标记为不完整并停止所有写操作。
- 三项查询全部成功后，展示候选让用户选择具体版本、流水线和发布域；用户完成选择后才生成 `order create` dry-run。

### pipeline list

列出插件的发布流水线。

```bash
bytedcli --site cn lego --region online pipeline list --plugin-name demo_plugin
```

| 参数                         | 必填 | 说明                                                                                                                                                                                     |
| ---------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--plugin-name <pluginName>` | 是   | 插件名                                                                                                                                                                                   |
| `--is-used-publish`          | 否   | 仅显示用于发布的流水线                                                                                                                                                                   |
| `--category-name <name>`     | 否   | 按单一类目名过滤                                                                                                                                                                         |
| `--pipeline-kind <kind>`     | 否   | 按流水线类型过滤（语义值：`plugin_publish \| conf_publish \| adaptive_switch_init_phase \| adaptive_switch_runtime_phase`，见 [状态与错误参考](statuses-and-errors.md) 的 PipelineKind） |

> 后端不支持分页，所有匹配的流水线一次性返回。

JSON：`{ items, total }`，每个 item 含 `id`、`name`、`category_name`、`region`、`pipeline_kind`。创单选 `pipeline_kind = 1`（PluginPublish 插件发布）的流水线。

### pipeline confirm

人工确认发布工单的当前步骤（写操作）。

```bash
bytedcli --site cn lego --region online pipeline confirm --order-id 12345
bytedcli --site cn lego --region online pipeline confirm --order-id 12345 --yes
```

| 参数                   | 必填 | 说明                                                              |
| ---------------------- | ---- | ----------------------------------------------------------------- |
| `--order-id <orderId>` | 是   | 工单 id                                                           |
| `-y, --yes`            | 否   | live confirm 必需；agent / 脚本 / 非 TTY 场景在检查工单状态后使用 |

行为：

1. 先读 `order get` 拿 `region` / `current_flow_index` / `current_step_index`（这三个缺失才会抛 `LEGO_ORDER_DETAIL_MISSING_FIELD`），再用 `pipeline step-info get` 取当前步骤作为 `confirm_target`。`plugin_name` / `pipeline_id` 只用于拼网页兜底地址，缺失时不会单独报字段缺失。
2. **不传 `--yes`** 时返回 dry-run 预览结果，包含 `dry_run: true`、`confirm_target`、`confirmed: false`，不会调用写接口。agent 展示 `confirm_target` 和本次推进风险，并按 SKILL.md 的用户确认协议等待用户明确授权当前目标；只有获得该授权后才能补 `--yes`，未授权时停止，不能自动重试。
3. **传 `--yes`** 时调用后端 `manualConfirm`：成功 → `confirmed: true`；后端拒绝 → 命令失败并优先保留上游 `AppError` 的 `code` / `hint`，JSON error 会补 `details.error_message`；`details.web_url` 仅 best-effort，只有拿得到 `plugin_name` 时才会附带网页兜底地址。只有上游抛的不是 `AppError` 时，才兜底成 `LEGO_CONFIRM_ORDER_FAILED`。
4. **CLI live confirm 仅限 `--site boe`**：只有 `--site boe` 允许通过 CLI 提交 live confirm；其它站点（`cn` / `i18n-bd` / `i18n-tt` / `us-ttp` / `eu-ttp`）在写入前直接抛 `LEGO_CONFIRM_SITE_NOT_ALLOWED`，`details` 带 `order_id` / `lego_site` 与可选 `web_url`，请打开该 `web_url` 到网页上人工确认，不要重试。dry-run 预览（不带 `--yes`）不受站点限制，任意站点都能查看 confirm target。

JSON：dry-run / live 成功 → `{ dry_run, order_id, region, current_flow_index, current_step_index, confirm_target: { flow_index, step_index, step }, confirmed, web_url }`；其中成功返回里的 `web_url` 也是 best-effort，可能缺失。后端拒绝 live 写入时返回 JSON error：若上游是 `AppError`，则保留原始 `code` / `hint`（例如 `LEGO_ENVELOPE_ERROR`、`LEGO_AUTH_REQUIRED`）；若不是，才兜底为 `LEGO_CONFIRM_ORDER_FAILED`。`details.error_message` 为后端 / 上游错误信息，`details.web_url` 仅在能生成网页兜底地址时出现。

### pipeline step-info get

查询发布工单指定步骤详情。

```bash
bytedcli --site cn lego --region online pipeline step-info get --order-id 12345 --flow-index 0 --step-index 0
```

| 参数                       | 必填 | 说明      |
| -------------------------- | ---- | --------- |
| `--order-id <orderId>`     | 是   | 工单 id   |
| `--flow-index <flowIndex>` | 是   | flow 下标 |
| `--step-index <stepIndex>` | 是   | step 下标 |

JSON：`data.step`，含 `id`、`name`、`type`（见 [状态与错误参考](statuses-and-errors.md) 的 StepType）、`task_status`、`check_task_status`（见同文件的 CheckTaskStatus）、`operator`、`assignees`、`create_time`、`process_end_time`、`process_second_duration` 等。

> 步骤详情命令在 `pipeline` 组下，不是 `order step-info get`（旧文档写错了）。

### order create

创建发布工单（写操作）。默认 dry-run 预览；确认后加 `--yes` 执行。

```bash
bytedcli --site cn lego --region online order create \
  --plugin-name demo_plugin --version 1.0.0.1 --scope-name 全量发布 --order-type hot_upgrade
```

| 参数                             | 必填 | 说明                                                                |
| -------------------------------- | ---- | ------------------------------------------------------------------- |
| `--plugin-name <pluginName>`     | 是   | 插件名                                                              |
| `--version <version>`            | 是   | 编译产物版本（**不是 `--commit-tag`**）                             |
| `--scope-name <scopeName>`       | 是   | 发布域名；`全量发布` 为全量发布内置值，或 `scope list` 返回的任意值 |
| `--order-type <orderType>`       | 是   | 工单类型，当前仅支持 `hot_upgrade`（OrderTypeHotUpgrade）           |
| `--pipeline-id <pipelineId>`     | 否   | 流水线 id；泳道发布可不传                                           |
| `--ready-sec <readySec>`         | 否   | ready 秒数                                                          |
| `--surge-percent <surgePercent>` | 否   | surge 百分比，整数 `1`-`100`（单位 `%`）                            |
| `--enable-go-version-cleanup`    | 否   | 开启 go version 清理                                                |
| `--cleanup-pipeline-id <id>`     | 否   | 清理流水线 id                                                       |
| `--publish-parameters <json>`    | 否   | 发布参数 JSON 对象（value 必须为字符串）                            |
| `-y, --yes`                      | 否   | 执行 live 创单                                                      |

`--publish-parameters` 示例只写单行内联 JSON：

```bash
bytedcli --site cn lego --region online order create \
  --plugin-name demo_plugin --version 1.0.0.1 --scope-name 全量发布 --order-type hot_upgrade \
  --publish-parameters '{"lane":"lane-a","branch":"main"}'
```

行为与 `--version` 语义：

- 未传 `--yes` 时默认 dry-run，只返回请求体不执行。
- dry-run 和 live 路径都会查询 plugin detail。插件不存在时返回 `LEGO_PLUGIN_NOT_FOUND` 并停止。
- service 层按 `isMultiVer = (kind === 3 MulVerNative || is_adaptive === true || is_multi_ver === true)` 决定：多版本插件把 `--version` 作为 `commit_tag` 下发，普通插件作为 `version` 下发。`kind`、`is_adaptive`、`is_multi_ver` 都来自 plugin detail，不是用户输入；调用方统一只传 `--version`。
- `--order-type` 传非 `hot_upgrade` 的值会在参数解析阶段被拒。

JSON：默认 dry-run → `{ dry_run: true, request }`（含 `pipelineId`、`pluginName`、`publishScopeName`、`orderType` 等；普通插件 request 含 `version`，多版本 / 自适应插件 request 含 `commitTag`，两者都来自用户传入的 `--version`）；`--yes` → `{ order_id, web_url? }`。

### order list

列出某插件的发布工单（PublishHistory）。

```bash
bytedcli --site cn lego --region online order list --plugin-name demo_plugin
```

| 参数                               | 必填 | 说明                                                                                                                   |
| ---------------------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------- |
| `--plugin-name <pluginName>`       | 是   | 插件名                                                                                                                 |
| `--page <page>`                    | 否   | 页码，默认 `1`                                                                                                         |
| `--page-size <pageSize>`           | 否   | 每页条数，默认 `20`                                                                                                    |
| `--start <start>`                  | 否   | 起始日期，如 `2026-01-01`                                                                                              |
| `--end <end>`                      | 否   | 结束日期，如 `2026-01-31`                                                                                              |
| `--order-type <orderType>`         | 否   | 按单一工单类型过滤（语义值：`hot_upgrade \| conf_upgrade \| adaptive_switch_plugin_conf \| adaptive_switch_psm_conf`） |
| `--target-version <targetVersion>` | 否   | 按目标版本（scm_version 或 commit_tag）过滤                                                                            |
| `--create-user <createUser>`       | 否   | 按创建者过滤                                                                                                           |
| `--order-id <orderId>`             | 否   | 按工单 id 过滤                                                                                                         |
| `--lane <lane>`                    | 否   | 按泳道过滤                                                                                                             |
| `--publish-scope <publishScope>`   | 否   | 按发布域过滤                                                                                                           |
| `--order-status <status>`          | 否   | 按单一工单状态过滤（语义值：`off \| finish \| online \| cancel \| ready \| wait \| building \| canceling \| suspend`） |

JSON：`{ items, count, page, page_size }`。文本表格列：ID / Commit Tag / Status / Order Type / Region / Scope / Lane / Create Time。

用户问“最近一次工单”或某插件“进行到哪一步”时，把完整 JSON 输入 skill 自带脚本：

```bash
python3 <skill-dir>/scripts/lego_workflow_state.py select --kind latest-order < order-list.json
```

脚本按 `create_time` 选择唯一最新工单。任一记录时间缺失或非法、混用带时区和不带时区的时间，或最高时间并列时返回 `selected=null`；此时展示 `reason` 和候选让用户选择，不自行按 id 或列表顺序打破并列。`selected` 非空时取其 order id，再执行 `order get` / `pipeline step-info get`。

### order get

查询发布工单详情。

```bash
bytedcli --site cn lego --region online order get --id 12345
```

| 参数             | 必填 | 说明    |
| ---------------- | ---- | ------- |
| `--id <orderId>` | 是   | 工单 id |

JSON：`data.order`，含 `id`、`plugin_name`、`pipeline_name`、`region`、`origin_version` / `origin_commit_tag`、`target_version` / `target_commit_tag`、`status`、`order_type`、`current_flow_index`、`current_step_index`、`flow_info`（含每个 flow 的 `type` 与 steps）。文本模式对 version 做 fallback：优先 `*_version`，为空再用 `*_commit_tag`。

### scope list

列出发布域。

```bash
bytedcli --site cn lego --region online scope list --plugin-name demo_plugin
```

| 参数                         | 必填 | 说明                |
| ---------------------------- | ---- | ------------------- |
| `--plugin-name <pluginName>` | 是   | 插件名              |
| `--page <page>`              | 否   | 页码，默认 `1`      |
| `--page-size <pageSize>`     | 否   | 每页条数，默认 `20` |
| `--scope-name <scopeName>`   | 否   | 按 scope 名过滤     |
| `--psm <psm>`                | 否   | 按 PSM 过滤         |

JSON：`{ items, count, offset, limit }`，每个 item 含 `scope_name`、`plugin_name`、`psm`、`region`。

> 分页契约说明：尽管命令对外暴露 `--page` / `--page-size`，`scope list --json` 为兼容既有自动化，仍只回显 `offset` / `limit`，不会额外返回 `page` / `page_size`。调用方如需页码语义，应以自身传入的请求参数为准。
>
> `全量发布` 是内置发布域，不出现在 `scope list` 接口返回或 JSON `items` 里，但可直接用于 `order create --scope-name 全量发布`。
