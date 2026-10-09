# FTF 智能归因噪音查询与修复

使用此流程查询 LLM 归因的噪音汇总或明细，并在用户明确授权后提交两类平台修复。
该能力使用 CN-only scene-mining 控制台；bytedcli 自动使用 ByteCloud JWT，不使用浏览器 Cookie。

## Use Cases

- 当需要查询指定 FTF 任务和 PSM 的 LLM 噪音归因结果时使用。
- 当已确认具体 Diff 聚类和修复范围，需要预览或提交 Schema/数组匹配修复时使用。
- 不用于一般 DIFF 根因分析或从 repair plan 直接执行动作。

## Inputs

- 必填：FTF 顶层任务 ID 和目标 PSM，来自任务详情或可信的 FTF 链接。
- 查询明细或修复时必填：查询结果中的一个或多个 `similar_diff_id`。
- 数组匹配修复还需目标 method、scene、精确数组 path、匹配方式和后端父配置中的 mode。

## Workflow

### 1. 查询

先查询汇总。默认请求 `dry_run`，不会写入平台：

```bash
bytedcli --site cn --json ftf remediation noise list \
  --task-id <task-id> \
  --psm example.psm \
  --method GetDemo \
  --page 1 \
  --page-size 20
```

JSON 结果中的 `noise_clusters` 始终是当前页聚类数组，`page` 和 `page_size` 位于 `data`
顶层。后端提供总数时输出 `total`；否则不伪造总数，改为输出当前页条数 `page_count`。
完整后端回执保留在 `context.backend`。需要一个或多个聚类的完整明细时，使用逗号分隔的
`similar_diff_id`，结果位于 `noise_details`：

```bash
bytedcli --site cn --json ftf remediation noise multi-get \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1,diff-2
```

`--is-outbound` 是布尔开关，`--noise-key` 是精确单值。`--op-source`、`--method`、
`--outbound-psm` 和 `--outbound-method` 支持逗号分隔的多个筛选值。

### 2. 预览与修复

仅当用户已确认准确的任务、PSM、`similar_diff_id` 和修复范围时才进入本节。两类写入均先发送
`process_mode=dry_run` 预览；只有加上 `--yes` 才发送 `process_mode=execute`。

Schema 噪音或时间偏移修复：

```bash
bytedcli --site cn --json ftf remediation schema update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --operation add-noise-template

bytedcli --site cn --json ftf remediation schema update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --operation add-noise-template \
  --yes
```

数组匹配修复要求提供完整的 outbound 定位信息。`--outbound-psm` 取自目标
diff 元数据或代表 Flow 中 outbound 的 `TargetPsm`；`bizmethod`、`biz_data`
等伪 outbound 的 `TargetPsm` 为空时应省略该参数，不得伪造 PSM。`--mode` 必须读取对应
`PSM + Method + Scene` 的 FTF 断言父配置，值为 `system` 或 `sandbox`，不得猜测。
CLI 会分别转换为后端要求的 `1` 或 `2`。`order` 不接受 `--key-list`；`key`
必须提供一个或多个稳定键：

`--path` 必须指向实际发生元素对齐问题的精确数组 path。父数组配置不会自动覆盖元素
内部的嵌套数组。例如 Diff 位于
`query_dsl->bool->must->[*]->bool->should->[*]`，而现有配置只有
`query_dsl->bool->must->[*]` 时，必须向 `arrayPrimaryKeyList` 新增前者，不能
改为配置父 path。执行后须回读并确认精确 path 已保存；写接口返回成功本身不构成
生效证据。

```bash
bytedcli --site cn --json ftf remediation array-match update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --method GetDemo \
  --scene default \
  --outbound-psm downstream.example \
  --outbound-method GetDownstream \
  --mode system \
  --path '$.items' \
  --match-type key \
  --key-list id

bytedcli --site cn --json ftf remediation array-match update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --method GetDemo \
  --scene default \
  --outbound-psm downstream.example \
  --outbound-method GetDownstream \
  --mode system \
  --path '$.items' \
  --match-type key \
  --key-list id \
  --yes
```

## Write Constraints

- 未经用户明确确认，不得追加 `--yes`。
- dry-run 与 execute 必须使用相同的任务、PSM、Diff ID 和修复参数。
- 写入结果未知时停止后续写入，先重新查询相同 selector；不得盲目重试。
- 数组匹配写入后必须回读精确 path，确认保存结果与预览一致。

## Results

- `requested_process_mode` 表示客户端请求模式；`process_mode` 和 `executed` 表示后端确认的
  执行模式与是否实际写入，后端未返回时为 `null`，不能只根据本地 `--yes` 推断完成。
- 成功：查询返回目标和分页回执；写入返回 `executed=true`，并通过后续查询确认目标状态。
- 部分完成：查询结果可用但某些明细缺失时，只报告已验证范围和缺口，不执行修复。
- 失败：输入、鉴权或 API 契约错误时停止，并按结构化错误的 hint 恢复。
- 写入后重新运行 `noise list` 或 `noise multi-get`，确认目标噪音的服务端状态。
- `FTF_AUTH_REQUIRED` 时按主 Skill 的 ByteCloud JWT 恢复流程处理；不要提供 Cookie、JWT 或
  浏览器抓包头。
- `FTF_API_ERROR` 时保留脱敏的 endpoint、`status_code` 和 `status_message`。未知结果不要重试
  写入；先用相同 selector 重新查询。
