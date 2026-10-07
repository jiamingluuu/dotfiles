---
name: bytedance-smartq
description: "Operate SmartQ/TestIDE UI automation via bytedcli: inspect spaces and app configuration, manage case nodes, history, copies, segments and webdiff assertions, generate cases, trigger template conversations, import or export BITS cases, create plans and tasks through BITS or ByCaps, wait for execution, and download evidence. Use for SmartQ, TestIDE, 小 Q UI, 空间配置, 用例生成, 模板对话, 断言规则, ByCaps, UI 自动化用例, 探索任务, AI 探索任务, BITS 用例导入, BITS 查重, case-set list, case-set bits search, auto_steps, caseset, test plan, test task, SmartQ/TestIDE cloud-device acceptance, SmartQ/TestIDE test reports, or SmartQ run videos."
---

# bytedcli SmartQ / TestIDE

通过 bytedcli 操作 TestIDE / SmartQ 小 Q UI 自动化。支持空间配置查询、用例生成与编辑、片段和断言规则管理、计划与任务执行，以及报告和录像下载。模板对话、BITS 回传使用各自的独立接口。

## 按能力读取

| 需求 | 参考 |
| --- | --- |
| 空间、目录、应用配置、标签、Mock 场景 | [空间配置](references/spaces.md) |
| 节点编辑、复制、历史、编辑权限、Meego 关联、断言规则 | [用例与断言](references/case-operations.md) |
| 任务列表、计划用例、BITS 与 ByCaps 触发、执行链接 | [任务与计划](references/task-operations.md) |
| 用例生成、生成状态、BITS 回传、模板对话 | [生成与对话](references/generation.md) |

## Prerequisites

- 调用方式见 `../../invocation.md`
- OpenAPI 路由认证只从环境变量读取，不在命令参数或代码中写 token：

```bash
export BYTEDCLI_SMARTQ_TOKEN=<openapi-token>
export BYTEDCLI_SMARTQ_PLATFORM=<token-apply-key>
```

- `BYTEDCLI_SMARTQ_BASE_URL` 可选，默认 `https://testide.byted.org`，用于 `/openapi/...` 路由
- `case-set list` 和 `case-set bits search` 使用 SmartQ Web BFF `/api/...` 路由：优先读取 `BYTEDCLI_SMARTQ_WEB_COOKIE`；否则复用 bytedcli SSO browser session，并需要 `BYTEDCLI_SMARTQ_BDSSO_AID`；`BYTEDCLI_SMARTQ_WEB_BASE_URL` 可选，默认 `https://smartq.bytedance.net`
- 写操作默认使用当前登录用户作为 operator；需要覆盖时传 `--operator <email-prefix>`
- 本页列出的写命令要求 `--dry-run` 或 `--yes`。`segment update` 和参考文档中的空间目录、节点复制、断言、计划触发、生成和对话写命令默认预览，只有 `--yes` 才提交。两种用法都不允许同时传 `--dry-run` 与 `--yes`。
- UI OpenAPI 与 Web BFF 的认证分开；生成与模板对话使用独立客户端，详见[生成与对话](references/generation.md)。
- 创建用例集时，`--case-set-type authored` 表示编写，`generated` 表示生成，默认 `authored`；兼容已有脚本中的 `0`、`1`。

## Read Cases

```bash
# 读取用例集 xmind_content、case_nodes；加 --with-auto-steps 后继续读取自动化步骤和片段引用
bytedcli --json smartq case-set get --space-id 1000 --case-set-id 2000 --with-auto-steps

# 只读取指定 auto node 的自动化步骤
bytedcli --json smartq auto-step get --space-id 1000 --case-set-id 2000 --auto-node-id demo-node

# 只列出用例节点映射
bytedcli smartq case list --space-id 1000 --case-set-id 2000

# 检查用例集是否带有启动单次验证 / 稳定性任务所需的执行环境配置
bytedcli --json smartq case-set env status --space-id 1000 --case-set-id 2000

# 列出指定目录下的 SmartQ 用例集；可按 creator 或 name 过滤
bytedcli --json smartq case-set list --space-id 1000 --dir-id 3000 --creator demo-user --page 1 --page-size 100

# 在指定目录下扫描 SmartQ 用例集，检查某个 BITS case 链接是否已经导入
bytedcli --json smartq case-set bits search --space-id 1000 --dir-id 3000 --bits-url https://bits.bytedance.net/case/123
```

JSON 输出里的关键字段：

- `case_set.xmindContent` / `case_set.xmindContentJson`：用例集内容
- `case_list.caseNodes`：自动化节点 ID 到用例路径的映射
- `auto_steps`：按 auto node ID 聚合的自动化步骤
- `segment_refs`：从 `step_type=4` 或带 segment 字段的步骤中提取出的片段引用
- `case-set env status` 的 `environment.missing`：缺失的执行配置字段，可能包含 `aid`、`product_infos`、`schedule_info`
- `case_set.bitsUrl` / `case_set.genStage` / `case_set.genStatus` / `case_set.genFailMsg`：BITS 导入与生成状态
- `case-set list` 的 `case_sets[]`：目录下用例集摘要，包含 `id`、`name`、`creator`、`case_count`、`updated_at`、`bits_url`

## List Case Sets

`case-set list` 使用 SmartQ Web BFF 列表接口读取指定目录下的用例集，适合普通目录扫描、按创建人/名称过滤，或排查某个用例集的 `bitsUrl` 字段。JSON 输出会补齐 `page`、`page_size`、`current_count`、`has_more`、`total` 和 `filters`；若后端未返回总数，`total` 为 `null`，不要用当前页条数当作总数。

```bash
bytedcli --json smartq case-set list \
  --space-id 1000 \
  --dir-id 3000 \
  --creator demo-user \
  --page 1 \
  --page-size 100

bytedcli smartq case-set list \
  --space-id 1000 \
  --dir-id 3000 \
  --name demo
```

## Search BITS Duplicates

`case-set bits search` 基于同一个 SmartQ Web BFF 列表接口分页扫描指定目录下的用例集，并在本地按 BITS case 页面路径查重。普通目录扫描用 `case-set list`；检查某个 BITS 用例是否已经导入时用 `case-set bits search`。SmartQ Web BFF 当前不支持直接按 `bits_url` 过滤，所以 CLI 会读取目录列表后比较 `case_set.bitsUrl`；默认最多扫描 100 页，可用 `--max-pages` 调整，提前停止时 JSON 输出会带 `truncated: true`。

```bash
bytedcli --json smartq case-set bits search \
  --space-id 1000 \
  --dir-id 3000 \
  --bits-url https://bits.bytedance.net/case/123

bytedcli smartq case-set bits search \
  --space-id 1000 \
  --dir-id 3000 \
  --bits-url https://bits.bytedance.net/devops/demo-space/quality/case/caseDetail/123 \
  --creator demo-user \
  --page-size 100
```

JSON 输出里的关键字段：

- `duplicate` / `match_count` / `matches`：是否命中重复、命中数量和匹配到的 SmartQ 用例集摘要
- `scanned` / `total` / `pages` / `page_size` / `truncated`：扫描范围和是否被 `--max-pages` 截断
- `bits_url` / `bits_url_key`：输出会去掉 query 和 fragment；查重按可信 BITS origin + case path 比较

## Import BITS Cases

当 SmartQ Web 页面里“上传用例”选择“Bits链接”时，可用 CLI 提交同等导入请求。这个能力面向已有 BITS 用例链接，不是 `smartq spec build` 的 YAML/JSON 转换。`--bits-url` 只接受内置可信 BITS HTTPS Web 链接，目前支持 `https://bits.bytedance.net` 和 `https://bits-i18n.byteintl.net`，路径必须是 `/case/<id>` 或 `/devops/<space>/quality/case/caseDetail/<id>`。CLI 只保留 BITS 页面需要的安全 query 参数；JSON/text 输出会去掉 BITS URL 的 query 和 fragment，避免把页面参数写入日志。

```bash
bytedcli smartq case-set import \
  --space-id 1000 \
  --case-set-id 2000 \
  --bits-url https://bits.bytedance.net/case/123 \
  --dry-run

bytedcli --json smartq case-set import \
  --space-id 1000 \
  --case-set-id 2000 \
  --bits-url https://bits.bytedance.net/case/123 \
  --yes
```

提交后用 `case-set get` 查看 `bitsUrl`、`genStage`、`genStatus`、`genFailMsg` 等状态字段。当前命令只负责提交导入，不负责轮询生成流或同步 BITS snapshot。

## Build Spec Payloads

当调用方已经有结构化 case spec，但不想手写 SmartQ `xmind_content` 和 `node_auto_steps_list` 时，可先生成本地 payload 文件，再用现有写命令提交。

`case.yaml` 示例：

```yaml
name: "Demo case"
title: "Demo title"
precondition: "Login completed"
steps:
  - "Open the target page"
  - "Tap the demo entry"
assertions:
  - "The expected result is visible"
automation:
  action_ai_type: decision
  precondition_steps:
    - text: "Use existing login segment"
      step_type: 4
      segment_id: 3000
environment:
  aid: "1000"
  platform: android
  product_infos:
    - app_type: 1
      aid: "1000"
  schedule_info:
    package_url: "https://example.test/app.apk"
```

生成 payload：

```bash
bytedcli smartq spec build \
  --spec-file ./case.yaml \
  --case-set-id 2000 \
  --xmind-file ./xmind.json \
  --auto-steps-file ./auto-steps.json \
  --metadata-file ./metadata.json
```

生成后先 review 文件，再提交：

```bash
bytedcli smartq case-set update --space-id 1000 --case-set-id 2000 --xmind-file ./xmind.json --dry-run
bytedcli smartq case-set update --space-id 1000 --case-set-id 2000 --xmind-file ./xmind.json --yes

AUTO_NODE_ID="$(node -e 'console.log(require("./metadata.json").node_ids.auto)')"
bytedcli smartq auto-step update --space-id 1000 --case-set-id 2000 --auto-node-id "$AUTO_NODE_ID" --body-file ./auto-steps.json --dry-run
bytedcli smartq auto-step update --space-id 1000 --case-set-id 2000 --auto-node-id "$AUTO_NODE_ID" --body-file ./auto-steps.json --yes
```

`smartq spec build` 只生成通用 SmartQ payload，不创建 case-set，不写执行环境配置，也不内置业务项目的 space、directory、登录片段或 App ID。JSON 输出始终包含 `xmind_content`、`auto_steps_body`、`node_ids`、`environment` 和输出文件路径，调用方应在自己的 skill / workflow 中管理这些默认值。

## Segments

```bash
# 读取片段内容
bytedcli --json smartq segment get --space-id 1000 --segment-id 3000

# 搜索片段
bytedcli smartq segment list --space-id 1000 --keyword login --page 1 --page-size 20

# 创建片段；auto_steps 用 JSON 数组
bytedcli smartq segment create --space-id 1000 --name demo-segment --steps-file ./segment-steps.json --dry-run
bytedcli smartq segment create --space-id 1000 --name demo-segment --steps-file ./segment-steps.json --yes
```

`segment-steps.json` 示例：

```json
[
  { "auto_id": "step-1", "step_type": 2, "text": "tap login" },
  { "auto_id": "step-2", "step_type": 3, "text": "assert login success" }
]
```

## Write Cases And Auto Steps

```bash
# 创建用例集
bytedcli smartq case-set create --space-id 1000 --dir-id 3000 --name demo-case-set --creator demo-user --dry-run
bytedcli smartq case-set create --space-id 1000 --dir-id 3000 --name demo-case-set --creator demo-user --yes

# 创建后顺便写入 xmind_content
bytedcli smartq case-set create --space-id 1000 --dir-id 3000 --name demo-case-set --xmind-file ./case.json --dry-run

# 更新已有用例集 xmind_content
bytedcli smartq case-set update --space-id 1000 --case-set-id 2000 --xmind-file ./case.json --dry-run
bytedcli smartq case-set update --space-id 1000 --case-set-id 2000 --xmind-file ./case.json --yes

# 更新自动化步骤；body 可包含 step_type=4 的片段引用
bytedcli smartq auto-step update --space-id 1000 --case-set-id 2000 --auto-node-id demo-node --body-file ./auto-steps.json --dry-run
```

`auto-steps.json` 示例：

```json
{
  "node_auto_steps_list": [
    {
      "node_id": "demo-node",
      "caseset_id": 2000,
      "auto_steps": [
        { "auto_id": "step-1", "step_type": 2, "text": "tap login" },
        { "auto_id": "step-2", "step_type": 4, "segment_id": 3000, "text": "use login segment" }
      ]
    }
  ]
}
```

## Plans

```bash
# 查询源计划；JSON 输出保留 OpenAPI 返回的完整 raw 字段
bytedcli --json smartq plan get --id 4000

# 创建计划：PlanInfo body 包含执行模式、用例选择和分配；自动化模式还需平台调度字段
bytedcli smartq plan create --body-file ./plan.json --dry-run
bytedcli --json smartq plan create --body-file ./plan.json --yes

# 更新计划：先查询当前计划，保留未修改字段，提交完整 PlanInfo
bytedcli smartq plan update --id 4000 --body-file ./plan.json --dry-run
bytedcli --json smartq plan update --id 4000 --body-file ./plan.json --yes
```

`plan.json` 示例：

```json
{
  "name": "demo-plan",
  "space_id": 1000,
  "remark": "sample automation acceptance plan",
  "scene_type": 1,
  "exe_type": 1,
  "app_type": 1,
  "platforms": [1],
  "filter_type": 3,
  "caseset_list": [2000],
  "assign_type": 1,
  "assign_to": ["demo-user"],
  "trigger_type": 0,
  "app_id": "demo-app",
  "install_type": 1,
  "clean_cache": true,
  "android_schedule_info": {
    "packageUrl": "https://example.test/demo.apk"
  }
}
```

`plan create` 与 `task create` 在认证和请求前校验 body。共同必填字段为 `name`、`space_id`、`scene_type`、`exe_type`、非空 `platforms`、`filter_type`、`assign_type` 和非空 `assign_to`。

`filter_type=0` 接收完整固定选择数据；`1` 接收 `case_filter_conditions` 或 `case_filter_conditions_v2`；`3` 需要非空 `caseset_list`。`assign_type=2|3` 同时支持有、无 `_v2` 后缀的分配条件。内部字段原样提交，见[创建字段](references/task-operations.md)。

`exe_type=0` 为手工模式，无需自动化包、安装和调度设置。Task 仍需 `trigger_type`，手工 Plan 可省略。自动化模式保留 `app_type`、`trigger_type` 及各平台 `*_schedule_info` 校验；App 平台还需 `app_id`、`install_type`、`clean_cache` 和有效包选择器。

计划更新接口不是字段级 PATCH。推荐先用 `bytedcli --json smartq plan get` 读取当前数据，从输出的 `raw` 复制完整 PlanInfo，修改目标字段后依次执行 `--dry-run` 和 `--yes`。

## Tasks

```bash
# 创建任务：TaskInfo body 较大，推荐放文件；使用与上文相同的完整创建字段
bytedcli smartq task create --body-file ./task.json --dry-run
bytedcli --json smartq task create --body-file ./task.json --yes

# 创建 AI 探索任务：对应 OpenAPI POST /openapi/task/independent_v2
bytedcli smartq task exploration create --body-file ./explore-task.json --dry-run
bytedcli --json smartq task exploration create \
  --name demo-explore \
  --case-set-id 2000 \
  --platform web \
  --mac-chrome-schedule-file ./web-schedule.json \
  --yes

# 查询任务进度 / 报告
bytedcli --json smartq task get --id 4000

# 等待任务进入终态；0/1 会继续等待，2/3/4/5 返回，输出保留原始状态
bytedcli --json smartq task wait --id 4000 --timeout-ms 1800000

# 查询任务 case run 列表
bytedcli --json smartq task result list --id 4000 --page 1 --page-size 20

# 查询一条 case run 的步骤级执行详情、失败节点、截图、断言详情和日志
bytedcli --json smartq task result get --id 4000 --run-id 5000 --space-id 1000 --device-platform android

# 表格模式展开步骤耗时列
bytedcli smartq task result get --id 4000 --run-id 5000 --space-id 1000 --device-platform android --with-timing

# 精确读取报告 readiness；报告来自 taskInfo.bytestUrl
bytedcli --json smartq task evidence get --id 4000 --run-id 5000 --device-platform android --kind report

# 按 runCmdId 等待录像 readiness；录像来自 executeDetail.video
bytedcli --json smartq task evidence wait --id 4000 --run-id 5000 --device-platform android --kind video --run-cmd-id 8001 --timeout-ms 600000

# 浏览器无关地下载报告或录像
bytedcli --json smartq task evidence download --id 4000 --run-id 5000 --device-platform android --kind report --output ./report.pdf
bytedcli --json smartq task evidence download --id 4000 --run-id 5000 --device-platform android --kind video --run-cmd-id 8001 --output ./run.webm

# 单 case 重试；先 dry-run，再明确提交
bytedcli smartq task result retry --id 4000 --run-id 5000 --device-platform android --dry-run
bytedcli --json smartq task result retry --id 4000 --run-id 5000 --device-platform android --yes

# 读取某一步的 AI 决策级详情(aiResp.detailUrl 内容:step_intention、reasoning)
# 方式一:用 runCmdId 解析(需配合 --id/--run-id/--device-platform,内部先查 result 再拉取 detailUrl)
bytedcli --json smartq task ai-detail get --run-cmd-id 8001 --id 4000 --run-id 5000 --device-platform ios
# 方式二:直接传 aiResp.detailUrl
bytedcli smartq task ai-detail get --detail-url "https://testide.bytedance.net/testide-gc-proxy/tos/resource?file=..."
```

`task result get` 的 `--run-id` 使用 `task result list` 返回的 case run ID。`--device-platform`
必填(服务端用于整型转换),`--space-id` 可选(服务端不强制,可省略);设备平台使用语义值:
`android`、`ios`、`harmony`、`web`、`win-app`、`mac-app`。

`task get` 的非 `--json` 表格会展示 `Platforms` 行:把任务的 `raw.platforms` 整型 ID 映射为设备平台语义值
(如 `[1,2]` → `android, ios`);未知 ID 原样显示整数,无平台时显示 `-`。`--json` 输出保留原始 `raw.platforms`。

JSON 输出里的关键字段：

- `caseRunId`：`task result list` 返回、并用于详情接口 path 的 case run ID
- `mntRunId`：详情响应中的实际执行记录 ID；单用例重试后可能变化
- `runNodes`：按执行顺序归一化的步骤，包含 `autoId`、`nodeId`、`segmentId`、步骤文本和状态
- `failedNodes`：执行失败、执行异常、断言失败或断言异常的步骤子集
- `runNodes[].runCmds[].executeDetail`：步骤前后截图、视频、日志和 LogID，以及控件树(`controlTree`)、网络(`networkUrl`)、控制台(`consoleUrl`)、页面链接(`pageLink`)、音频(`audio`)
- `runNodes[].runCmds[].assertDetailUrl`：断言详情 JSON 地址
- `runNodes[].timeCost` / `runNodes[].runCmds[].timeCost`：步骤级、命令级耗时(含 `totalTimeCost`、`exeTimeCost`、`aiTimeCost` 等)
- `runNodes[].runCmds[].aiResp` / `assertDetail` / `imgDiff`：AI 决策、断言详情、图像 Diff(原样透传，不深解)
- `deviceInfo`：执行设备信息(`model`、`sn`、`aid`、`did`、`platform`、`slardarUrl`)
- `taskInfo`：任务级信息，`bytestUrl` 为 Bits 质量平台报告直达链接，`bytestTaskId` / `taskExeStatus`
- `raw`：小Q OpenAPI 返回的完整原始结构

### 探索任务创建

`task exploration create` 用来提交小 Q UI 的探索任务创建接口 `POST /openapi/task/independent_v2`。完整字段很多时优先把 `CreateIndependentTaskReqV2` 放到 `--body-file`；CLI 提供常用顶层字段的 option，显式 option 会覆盖 body 文件里的同名字段。

`explore-task.json` 最小示例：

```json
{
  "task_name": "demo-explore",
  "username": "demo-user",
  "caseset_id": 2000,
  "platforms": [82],
  "mac_chrome_schedule_info": {
    "domain": "example.test",
    "url": "/demo"
  }
}
```

常用字段映射：

- `--name` → `task_name`
- `--username` → `username`，省略时默认使用当前登录用户 / `--operator`
- `--case-set-id` → `caseset_id`
- `--platform android|ios|harmony|web` → `platforms` 的 OpenAPI 数字 ID
- `--android-schedule-file` / `--android-schedule-json`、`--ios-schedule-file` / `--ios-schedule-json`、`--harmony-schedule-file` / `--harmony-schedule-json`、`--mac-chrome-schedule-file` / `--mac-chrome-schedule-json` → 对应平台 schedule info
- `--case-node-id`、`--account-file` / `--account-json`、`--libra-id`、`--libra-group-id`、`--explore-retry-count`、`--explore-conf-for-cache`、`--ai-qa-flow-id` 等 → 同名 OpenAPI 字段

`agent`、`source`、`install_type`、`libra_type`、`explore_retry_strategy`、`ai_rewrite_strategy`、`auto_case_exe_type`、`none_case_exe_type`、`is_evaluate_explorable_status` 等 OpenAPI 枚举或策略字段当前没有稳定语义命名，放在 `--body-file` 里按原始字段传递，不要猜数字含义。

命令会在本地校验 `task_name`、`username`、`caseset_id` 和非空 `platforms`；未显式传 `--username` 且 body 中没有 `username` 时，会用当前登录用户 / `--operator` 补齐。schedule/account 入参必须是 JSON object。其他深层字段不强行拆散，直接通过 `--body-file` 传 OpenAPI 原始结构。

### 终态与证据下载契约

- CLI 的计划/任务创建、状态与结果读取走 `/openapi/...` 路由，固定认证头为 `Platform`、`TestIDE-Token`，写入时另带 `Operator`。SmartQ Web 使用 `/api/...` BFF，且可能补 `multi_case_scope`；`case-set list` 和 `case-set bits search` 明确走 Web BFF 列表接口，其余能力不要把页面抓包路径当成 OpenAPI endpoint。
- Web 的 `download_case_run` 是异步消息导出动作，不是直接文件下载。`task evidence download` 只消费 OpenAPI 结果中的 `taskInfo.bytestUrl` 或 `runNodes[].runCmds[].executeDetail.video`。
- `--kind report` 是 task/run 级选择器，不接受 `--run-cmd-id`。`--kind video` 在多个录像同时可用时必须传精确 `--run-cmd-id`；CLI 会列出候选 ID，不会猜一个。
- 下载只接受 HTTPS，逐跳手工处理最多五次 redirect，并逐跳限制到已捕获的 SmartQ、Bytest 与 TOS evidence origin。SmartQ token 只会发送给精确可信 origin 上的 `/testide-gc-proxy/tos/resource`，其他允许的跳转域不携带认证头。
- readiness 轮询、所有 redirect 与响应体读取共享一个 `--timeout-ms` 总 deadline。HTTP 自动重试关闭。
- 报告只接受签名与 MIME 一致的 PDF、ZIP 或 HTML；录像只接受 MP4 或 WebM。校验完成后才以 0600 权限原子发布到 `--output`；目标已存在时需显式 `--force`。

表格模式将运行节点与命令合并为一张树状表 `SmartQ Run Nodes & Commands`:节点为顶层行(`#1`、`#2`…),其下用 `├─ cmd` / `└─ cmd` 缩进全量列出该节点的 `runCmds`,展示 `Run Cmd ID`(其后拼接命令级 `stepName`,如 `找不到目标`)、`Execution`(`exeStatus` + `exeStatusDesc`)和 `AI Detail URL`(`aiResp.detailUrl`,仅 AI 决策步骤有值,其余为 `-`);可将带 URL 的 `Run Cmd ID` 直接喂给 `task ai-detail get --run-cmd-id`。失败节点明细同时给出 `run_cmd_id` 与 `ai_detail`。

`--with-timing` 在表格模式的运行节点表追加 `Duration(ms)` 列(默认关闭)。表格模式的失败节点明细(`Failed node artifacts`)只列出 `run_cmd_id` 与 `ai_detail`;控件树/网络/控制台/页面链接等完整制品仅在 `--json` 模式的 `executeDetail` 字段中提供。

`task ai-detail get` 拉取 `task result get` 响应里 `runCmds[].aiResp.detailUrl` 指向的 AI 决策 JSON(仅 AI 决策步骤有该链接),归一化出该步的建议分析:

- `runCmdId` / `detailUrl` / `logId` / `failMsg`:定位信息与该步的失败信息(顶层 `failMsg` 为空时回退取 `res.failMsg`)
- `stepIntention`:来自 `res.memory.step_intention`,含 `isSingleStep`、`analysis`、`intention`
- `reasoning`:来自 `res.reasoning`,含 `rawAction`、`rawSummary`,以及 `rawThought` 的 `pageAnalysis`、`taskPlanning`、`postExecutionExpectation`、`trialReplan`
- `raw`:detailUrl JSON 的完整原始结构

两种输入模式互斥可选:`--detail-url` 直接拉取;`--run-cmd-id` 需同时给 `--id`、`--run-id`、`--device-platform`,由 CLI 先查 `result` 再解析对应步骤的 `detailUrl`。

## Agent Guidance

- 不要把真实 token、真实测试包 URL、真实用例集 URL 写入代码、文档、测试 fixture 或示例。
- 读取已有线上用例可用 `case-set get --with-auto-steps`；写入前必须确认目标是新建测试用例集，并先 `--dry-run`。
- 扫描目录下有哪些用例集时用 `case-set list --space-id <id> --dir-id <id>`；它是只读 Web BFF 能力，支持 `--creator`、`--name`、`--page`、`--page-size`。
- 从 BITS 导入用例时使用 `case-set import --bits-url <url>`；它调用 SmartQ OpenAPI `POST /openapi/resource/{caseSetId}/upload_fr_bits`，body 只有 `bits_url`。BITS URL 只允许内置可信 BITS HTTPS origin 和用例页路径，输出展示会去掉 query/fragment。这和 `spec build` 的 YAML/JSON 本地转换是两条独立路径。
- 查 BITS 用例是否已导入 SmartQ 时使用 `case-set bits search --space-id <id> --dir-id <id> --bits-url <url>`。它扫描 `/api/caseset/` 的分页结果后本地比较 `bitsUrl`，不会调用写接口；若传 `--creator`，接口参数使用 `creators=demo-user` 这种普通字符串，不使用页面 URL 里的 JSON 数组形态。
- `auto-step update` 的 body 放 `node_auto_steps_list`；顶层 `auto_node_id` 与数值型 `caseset_id` 由 CLI 根据参数补齐。若标题节点没有自动化步骤，用 `auto_steps: []` 明确写空数组，便于后续回读。
- 一个 Eval case 应绑定一个稳定的源计划 ID；每次验收执行由调用方从源计划复制或创建单次运行计划，并将运行计划/任务 ID 与结果落库。
- `plan create` 与 `task create` 均校验真实完整创建字段；`plan update` 接收完整 PlanInfo，不要只提交单个变更字段。
- `task create` 只接收完整 JSON body，不把 Android 包、mapping、设备筛选等深层字段拆成零散 flags。
- `task exploration create` 是探索任务专用创建入口，走 `POST /openapi/task/independent_v2`；优先用 `--body-file` 承载完整 `CreateIndependentTaskReqV2`，只用 option 覆盖任务名、用例集、平台、schedule、账号、Libra、AI 改写和重试等常用字段；没有稳定语义名的 OpenAPI 枚举字段直接放在 `--body-file`。
- 验收时先 `task wait`，再从 `task result list` 取得 case run ID，随后按 kind/runCmdId 执行 `task evidence wait` 与 `download`。不要把“已进入终态”直接等同于业务成功，最终结论仍需结合原始状态、报告和录像。
- `task result retry` 是写操作，必须先 `--dry-run` 检查 task、case run 和设备平台，再由用户确认后使用 `--yes`。
- Fix loop 应使用 `task result get` 返回的运行时 `autoId` / `nodeId` 定位失败步骤，再读取当前 `auto-step` 配置；运行快照和当前配置不一致时先重试，不要覆盖较新的配置。
- `segmentId` 非 0 的运行步骤来自公共片段。修复时读取并评估对应 segment 的引用范围，不要把展开后的步骤当作 case 本地步骤直接覆盖。
- `--json` 是全局参数，放在 `smartq` 前，例如 `bytedcli --json smartq task get --id 4000`。

## 片段更新与结果筛选

`segment update` 提交完整片段替换，默认预览。先读取片段，在完整 body 上修改；`auto_steps: []` 表示清空步骤。片段列表的 `--page-size` 范围是 1–100。

```bash
bytedcli smartq segment update --space-id 1000 --segment-id 3000 --body-file ./demo-segment.json
bytedcli --json smartq segment update --space-id 1000 --segment-id 3000 --body-file ./demo-segment.json --yes

# 结果筛选使用语义值，多个值用逗号分隔
bytedcli --json smartq task result list --id 4000 --ass-status failed,exception --exe-status failed --page 2 --page-size 20
bytedcli smartq task result retry --id 4000 --run-id 5000 --device-platform safari --dry-run
```

| 筛选参数 | 语义值 |
| --- | --- |
| `--ass-status` | `pending,running,passed,failed,exception,warning` |
| `--exe-status` | `pending,running,succeeded,failed,exception,internal-error,exploration-failed,canceled` |
| `--confirmed-status` | `pending,passed,failed,blocked,skipped` |
| `--case-source` | `testide,mnt,manual` |

已发布命令的数字筛选值继续可用。`task result retry` 另支持 `multi-device`、`safari`、`edge`；结果详情和证据命令仍使用各自 help 中的设备平台集合。

`segment list` 与 `task result list` 返回请求对应的 `page`、`page_size`、`current_count`、`has_more`，并保留 `pageSize`。后端没有提供总数时不以当前页条数代替。独立 `case list` 的 `--space-id` 可省略；`case-set get` 仍需要空间 ID。
