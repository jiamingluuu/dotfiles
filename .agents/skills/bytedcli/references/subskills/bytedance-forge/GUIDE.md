---
name: bytedance-forge
description: "Access ByteDance Reckon Forge model platform via bytedcli: diagnose a training job across Forge logs and verified Primus application/pod signals (`forge job diagnose`), fetch task logs (`forge logs`), inspect job summaries / latest stage / step status (`forge job get`, `forge details`, `forge stages`), read complete source snapshots for a Forge commit (`forge commit get`) and compute file-level code diffs (`forge commit diff`), and diagnose whether a model is still distributed to a serving PSM (`forge service-hub diagnose`). Use when tasks mention Forge, Reckon Forge, training failure/error codes, Primus exit codes or pod states for a Forge job, model source code, historical commit, model commit diff, train log, sail/lagrange model, a Forge job URL, Service Hub, model distribution / 分发诊断, or a model that looks offline on an inference serving."
---

# Forge — Reckon Forge Model Platform

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

## 前置条件

- 需要本机已经登录：`bytedcli auth login`
- 大部分接口走 ByteCloud JWT；commit/code 接口走相同 JWT
- 训练任务、Service Hub 和 commit 读取命令的 `--url` 均按精确 Forge UI 域名选择控制面及 JWT site。`forge commit get` / `diff` 也支持显式 `--site`（包括全局 `--site`）；仅给 ID 且未指定站点时保留 US-TTP 默认。URL 与显式站点或 endpoint override 冲突时报错，未知域名不会携带凭据请求。
- CN commit 通过 `get_commit?with_code=1` 读取本地代码，不要求 `global_id`。其他站点沿用元数据 + global-site snapshot 链路。版本页面指向当前编辑器；复核历史训练代码应先从任务确定 commit，再读取该 commit。

## 子命令一览

| 子命令                        | 用途                                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| `bytedcli forge logs`         | 拉训练日志，支持 `--site`、`--url`、`--job-id`、`--offset`、`--limit`、`--raw`               |
| `bytedcli forge job get`      | 任务概要 + stage 列表（首选；`forge details` / `forge stages` 已隐藏保留）                   |
| `bytedcli forge job diagnose` | 一次返回 Forge stage/log error code、Primus application exit code/diagnostic 和有界 pod 状态 |
| `bytedcli forge commit get` | 读取指定 commit 的全部源码，支持精确 `--path` 文件筛选 |
| `bytedcli forge commit diff`  | 比对两个 commit 的代码改动，生成文件级 unified diff                                          |
| `bytedcli forge service-hub diagnose` | 判定某个模型是否还分发到指定 serving PSM（Service Hub「分发诊断」）                   |

## Logs

最常用的 3 种用法：

```bash
# 直接给 logs 页面 URL
bytedcli forge logs --url "https://reckon-ttp.tiktok-row.net/forge2/jobs/123456/logs"

# 给 job-id + 站点（推荐）
bytedcli forge logs --job-id 123456 --site us-ttp

# 拿 raw response（debug 用）
bytedcli forge logs --job-id 123456 --site us-ttp --raw
```

常用参数：

- `--offset <n>`：默认 `-1`（从末尾开始），早期日志可用 `--offset 0`
- `--limit <n>`：默认 `500`
- `--site <site>`：可选 `cn`、`us`、`us-ttp`、`eu`；已经传完整 URL 时通常不需要再指定。
- 输出 `--json` 时，`data.logs` 是字符串

## Job summary

```bash
bytedcli forge job get --job-id 123456
# 或
bytedcli forge job get --url "https://reckon-ttp.tiktok-row.net/forge2/jobs/123456"

# 调试 raw 数据
bytedcli --json forge job get --job-id 123456 --raw
```

输出包含：`job_id`、`tracing_base_url`、最新 stage / status、stage 列表（默认 page=0, page_size=10）。

跨区域任务优先传完整 `--url`，命令会由 UI 域名选择对应 tracing 控制面；只传 `--job-id` 时沿用 US-TTP 默认。

## Job diagnosis

排查一个训练任务时优先使用聚合诊断，而不是手工拼接多个命令：

```bash
# 自动完整扫描有界 stage 列表，并确定性选择 latest stage
bytedcli forge job diagnose --job-id 123456

# 精确诊断某个 stage
bytedcli forge job diagnose \
  --url "<forge-job-url>" \
  --stage-id 789

# Forge 没有暴露唯一 Primus 链接时，显式提供 History/UI URL；仍会校验 job/stage
bytedcli --json forge job diagnose \
  --job-id 123456 \
  --primus-url "<verified-primus-history-url>"
```

Selector 与边界：

- `--job-id` 和 `--url` 必须且只能传一个，避免详情与日志被拼到不同 job。
- `--url` 的精确 UI 域名决定 Forge tracing、train-log 与 JWT site；未知/伪造域名返回 `FORGE_UNTRUSTED_ORIGIN`。只传 `--job-id` 时沿用 US-TTP 默认。
- `--stage-id` 省略时，只有 stage 分页扫描完整，且多个 stage 的时间都可比较、最新时间唯一时才会选择 latest；扫描不完整、时间缺失/非法或并列时不会猜测，按 hint 传准确的 `--stage-id`。
- `--log-limit` 默认 `500`、最大 `5000`，只扫描 Forge 返回窗口中最后这部分日志，并额外限制本地扫描字符数。没有命中时状态是 `not_found_in_scanned_window`，不代表完整任务日志里没有错误码。
- 日志只提取显式标记的 `error_code`、`errorCode`、`err_code` 标量，以及 `multiple collected error_code_info before failure reason reporting` 结构化映射的顶层 error-code key；不会把 metadata 数字、普通数字、HTTP 状态或任意 `code` 猜成 Forge 任务错误码。错误文案不查静态码表：只有同一个 code metadata 自带且没有冲突的 message 时才给该 match 补 `error_message`。collected map 后紧邻同一 pod/operator/run context 的 `exception: ... fail task` 会作为独立 terminal-exception context 返回，不会根据 map 顺序或 `strategy` 猜测属于哪个 code。
- `--max-pods` 默认 `500`、最大 `5000`，是所有 Primus role 合计的 pod 明细上限。结果会返回 `truncated`、`projection_truncated`、`has_more`、role 完成度和 `complete_for_request`；Primus 未提供可靠 total 时保持 `null`。
- text 模式只展示最多 `20` 条异常 pod 明细；`--json` 在 `primus.pods.items` 中保留本次有界扫描返回的全部 pod items。完整性仍以 `--max-pods`、`truncated` 和 `complete_for_request` 为准。
- `--timeout-ms` 默认 `120000`、最大 `300000`，是整次诊断共享的总时限，不是每个请求各自重置。时限耗尽后停止后续远端请求，保留已经取得的证据，并把未完成来源标为 `partial` / `unavailable`，同时返回 `FORGE_DIAGNOSIS_DEADLINE_EXCEEDED` coverage error。
- role 数、分页请求和单次 Primus 响应另有固定安全上限；application/pod 诊断请求的响应上限均为 2 MiB，且在共享总时限内不做 transport retry。触发任一上限时会标记 partial/truncated，并在 `retrieval.errors` 返回对应 coverage code，不会把未扫描部分冒充完整结果。

JSON 重点字段：

- `diagnosis.root_cause_status`：`identified`、`inconclusive` 或 `not_applicable`；状态未知或证据不足且没有信号时是 `inconclusive`，只有权威状态已知且非异常时才是 `not_applicable`。
- `diagnosis.signals[]`：按根因优先级返回至多 `1000` 个信号，并用 `signals_seen` / `signals_truncated` 披露完整计数与截断；每个信号保留 `source`、`kind` 和有界 `value`，Forge log code、application exit code 与 pod exit code 不会混成一个含糊的 `error_code`。Forge code metadata 能可靠提供文案时，对应 code signal 的 `message` 使用该文案；未校验到 selected stage 的 terminal exception 仅作 supporting context，不参与根因排序。
- `forge.log_error_codes`：显式日志 code 的规则、首次相对行号与出现次数；`matches[].error_message` 始终存在，只在同一结构化 code entry 能可靠归属且文案未超限时返回字符串，否则为 `null`，超长文案另由 `error_messages_truncated` 披露。相邻 execution 级异常单独放在 `context_messages[]`，并用 `context_messages_truncated` 披露 100 个 unique `(operator, message)` 上限或超长 context。结果分别用 `window_truncated`、`matches_truncated` 披露扫描窗口、100 个 unique code 上限，或 collected map 不完整、格式错误、超过本地解析上限等情况；map 未完整成功解析时，`unique_matches_seen` 只是成功解析部分的下界。结果不包含原始整段日志。HTML fallback 没有识别出日志容器时不会扫描整页 source，避免把页面脚本里的字段误当任务错误码。
- `primus.resolution`：`verified`、`not_linked`、`ambiguous`、`mismatch`、`unverified` 或 `unavailable`，并用 `discovery_truncated` 披露有界候选扫描是否完整。只有候选发现完整、所有候选均通过 application id / job / stage / attempt 上下文校验，且唯一指向同一 application/attempt 时才是 `verified`；pod 查询会固定到同一 attempt。
- `primus.application`：`final_status`、`exit_code`、`diagnostic` 和上游 endpoint 完整性；status/exit 最多 128 字符且必须精确投影，diagnostic 最多 4096 字符，任何无效或裁剪字段都会令 `projection_truncated=true`、`complete=false`。
- `primus.pods`：reported/observed state counts、每个 pod 的 `state`、`exit_code`、diagnostic，以及明确的扫描覆盖范围；state/exit 字段最多 128 字符，diagnostic/status 字段最多 512 字符，裁剪通过 `projection_truncated` 披露；对象型上游字段只投影允许的状态/原因/消息/code，不返回整块原始 Pod 对象；对象内 exit leaf 只接受 string/finite number，diagnostic leaf 只接受 string，非法值不会成为根因信号。
- `retrieval.sources` / `retrieval.errors`：每个数据源是 `complete`、`partial`、`unavailable`、`not_requested` 或 `not_applicable`，可选 enrichment 失败不会抹掉已经取得的证据。

训练任务本身处于 failed、存在非零 exit code 或命中日志错误码，仍表示“诊断请求成功”，CLI exit code 为 0。输入非法或 Forge job/stage/log 均无法取得任何可用证据时才返回调用错误。

若需要继续查看具体 Primus 文件日志，使用诊断结果里的 verified application URL，按 `bytedcli primus role list` → `primus pod list` → `primus log get` 的顺序排查；不要把未校验或 stage mismatch 的 application 当成当前任务证据。

## Service Hub 分发诊断

指标只能告诉你「哪个模型在报错」，回答不了「这个模型现在还在不在这条 serving 上」。
`forge service-hub diagnose` 调用 Service Hub 页面上「分发诊断」背后的接口，把结论解析成结构化字段：

```bash
# 直接给 serving PSM + 模型名
bytedcli forge service-hub diagnose --psm example.serving.api --model example_model_r0_0

# 直接给 Service Hub 页面 URL（同时定站点、解析 psm 与 model_name）
bytedcli forge service-hub diagnose --url "<forge-service-hub-url>"

# 机器可读；诊断在服务端跑，慢时调大 --timeout-ms（默认 120000，上限 300000）
bytedcli --json forge service-hub diagnose --psm example.serving.api --model example_model_r0_0 --timeout-ms 180000

# 需要人工核对原始报告时加 --raw（仅文本模式；--json 始终带 markdown 字段）
bytedcli forge service-hub diagnose --psm example.serving.api --model example_model_r0_0 --raw
```

`verdict` 是这条命令的结论字段：

| verdict        | 含义                                                                       |
| -------------- | -------------------------------------------------------------------------- |
| `not_deployed` | 模型在 Model Hub 已下线，这条 serving 上根本没有它；上游还在请求就会一直失败 |
| `healthy`      | 分发正常（可能仍带 load lag、实例未就绪这类良性原因）；可排除分发方向        |
| `problem`      | 报告标了异常，但原因不属于已知的「已下线」形态；读 `reasons` 与 `instances` |
| `unknown`      | 报告为空、没有实例块，或实例状态标记不在已知集合内；只有 `markdown` 字段可信 |

其他字段：`reasons` 是去重后的原因标识，**健康原因也在里面**（`serving_no_load_lag` 这类），它是报告里出现过什么的索引，不是故障清单——下结论只看 `verdict`；`instances[]` 按 snapshot 版本给出 `level`（`ok` / `problem` / `info`）、`reason`、`conclusion`、`monitor_url`；`attributes` 是报告头部信息（模型架构、硬件类型、Dense 来源等）；`model_hub_url` / `service_hub_url` 便于跳回平台页面。`level` 为 `info` 表示状态标记不在已知集合内，此时整体 `verdict` 会退化为 `unknown`。

判读要点：

- 「单个模型失败率接近 100%、同 serving 上其他模型正常」是本命令最典型的适用场景；全部模型一起失败通常是 serving 集群问题，不要用分发诊断结案。
- 上游拿到的模型错误码名不一定指向真实根因，看到疑似模型级故障时先跑一次分发诊断再按错误码深挖。
- 只覆盖通过 Model Hub 分发的 serving；不经 Model Hub、直连推理服务的模型不适用。

## Commit 源码读取

读取指定 commit 的完整文件内容与 SHA-256。JSON 返回 `commit`、`site`、`region`、`files[]`；每个文件包含 `path`、`file_id`、`content`、`content_sha256`。不要求任务仍运行或训练成功，只要求 commit 快照存在且有读取权限。

```bash
# 国内：读取整个 commit；JSON 保留 Unicode、换行及空文件内容
bytedcli --site cn --json forge commit get --commit-id 123456
# 精确读取单个文件
bytedcli forge commit get --url '<forge-commit-url>' --path models/demo.py
# 将完整 JSON 快照保存到本地；命令自身不写文件
bytedcli --site cn --json forge commit get --commit-id 123456 > source.json
```

- `--url` 接受 `/forge2/commits/<id>` 页面，不接受版本编辑器或任务 URL；与 `--commit-id` 同传时必须指向同一 commit。
- 省略 `--path` 返回全部文件，指定路径不存在时返回 `FORGE_COMMIT_FILE_NOT_FOUND`。
- 文本模式展示路径和源码，并去除终端控制序列；需要精确保留内容时使用 JSON 中的 `files[].content`。
- `--raw` 在 JSON 结果中附加原始响应。源码不执行，不触发训练、编译或发布。
- 单次响应上限 16 MiB；文件树上限 10,000 个节点、100 层路径，超过上限或内容缺失时明确报错，不返回静默截断的源码。

## Commit diff

`forge commit diff` 复用源码读取路径，按 repo-relative path 关联两个 commit 的文件，输出 added / removed / modified / unchanged 和 unified diff。

CN 读取 `get_commit?with_code=1`；其他站点先取元数据中的 `global_id` 与 `region`，再取 `global_site/get_commit_code`。`global_id=0` 不影响 CN 本地源码读取。

```bash
# 直接给 UI 上的完整 diff URL（最省事）
bytedcli forge commit diff \
  --url "https://reckon-ttp.tiktok-row.net/forge2/commits/885953?target_commit_id=894613"

# 显式给 base + target
bytedcli forge commit diff --base 885953 --target 894613

# 拿机器可读 JSON（含 summary + per-file diff 文本）
bytedcli --json forge commit diff --base 885953 --target 894613

# 调试：保留 raw API payload
bytedcli --json forge commit diff --base 885953 --target 894613 --raw
```

### 输出结构（JSON 模式）

```jsonc
{
  "data": {
    "base":   { "id": 885953, "global_id": 2799458470, "region": "ttp", "version": 1064, ... },
    "target": { "id": 894613, "global_id": 1107921825, "region": "ttp", "version": 1065, ... },
    "region": "ttp",
    "context_lines": 3,
    "summary": {
      "files_total": 4, "files_added": 1, "files_removed": 1,
      "files_modified": 1, "files_unchanged": 1,
      "added_lines": 12, "removed_lines": 8
    },
    "files": [
      {
        "path": "models/feature.py",
        "status": "modified",
        "base_file_id": 1066135124,
        "target_file_id": -1046351223,
        "base_sha256": "...",
        "target_sha256": "...",
        "added_lines": 5,
        "removed_lines": 3,
        "diff": "--- commit/885953/models/feature.py\n+++ commit/894613/models/feature.py\n@@ -1,3 +1,5 @@\n ..."
      }
    ]
  }
}
```

文件配对策略是「按 path 关联」，因为同一文件在不同 commit 里 `treeView.id` 会变。

### 常用选项

- `--region <region>`：非 CN 默认从两端元数据推断共同 region，均缺失时沿用 `ttp`；CN 只允许省略或指定 `cn`。
- `--context-lines <n>`：unified diff 上下文行数，默认 3
- diff 保留 `--api-base-url` / `--global-site-base-url` / `--ui-base-url` 兼容参数，但仅接受与所选站点匹配的内置可信地址。旧脚本应优先迁移到 `--url` 或 `--site`；不再支持任意代理 host。
- `--raw`：在 JSON 输出里附 `raw_base_commit` / `raw_target_commit` / `raw_base_code` / `raw_target_code`

## Troubleshooting

- **`FORGE_AUTH_REQUIRED`**：先跑 `bytedcli auth login`；JWT 过期、刚切换 site 时常见
- **`FORGE_DIAGNOSIS_UNAVAILABLE`**：Forge job/stage/log 都没有返回可用证据；按 hint 检查登录态、job selector 和目标网络后重试
- **`FORGE_SITE_CONFLICT` / `FORGE_UNTRUSTED_ORIGIN`**：使用目标任务所在 Forge 控制面的原始 UI URL，不要混用另一区域的 tracing/logs override
- **Primus resolution 为 `unverified` / `mismatch`**：不要手工接受该 application；使用当前 stage 对应的准确 Primus History/UI URL重跑 `forge job diagnose --primus-url ...`
- **`FORGE_MODEL_DIST_ERROR`**：分发诊断接口调用失败或返回失败状态；确认 `--psm` 是 serving PSM（不是调用方 PSM）、`--model` 是 Model Hub 上的模型名，并检查登录态与 `--site`
- **`FORGE_MODEL_DIST_PARSE_ERROR`**：接口返回体结构与预期不符（常见于登录回跳返回 HTML）；确认登录态与 `--site` 后重试
- **`verdict` 为 `unknown`**：报告为空、没有实例块，或状态标记变了；直接读 `--json` 输出的 `markdown` 字段，不要凭 `verdict` 下结论
- **`FORGE_COMMIT_API_ERROR (code=4005)`** 或类似 `非办公网`：换办公网 / Lynx 代理重试
- **`FORGE_COMMIT_SOURCE_UNAVAILABLE`**：核对 commit 页面、站点、快照是否可用及源码读取权限；缺少 global ID 不等于任务已删除，CN commit 使用本地取码路径。
- **`FORGE_COMMIT_SCHEMA_ERROR`**：返回的快照格式异常、文件树或内容不完整；不要将其当成空文件或无代码变更。
- 若 `code_snippet` 为空：检查 `get_commit_code` 是否被 region 错配（例如把 `va` commit 用 `ttp` 拉），可显式指定 `--region`

## Notes

- 缺少必填参数会输出完整帮助信息
- 需要机器可读输出时加 `--json`
- `--json` 是全局参数，必须放在子命令前，例如 `bytedcli --json forge commit diff --base ...`
- 需要排查具体请求链路时，优先使用全局参数 `--http-debug`；可配合 `--http-trace-file <path>` 把 trace 落盘
