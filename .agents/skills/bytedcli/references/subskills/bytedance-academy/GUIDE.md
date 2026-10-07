---
name: bytedance-academy
description: "Operate Academy via bytedcli. Use this skill whenever the user mentions Academy, fe_config_id, Academy 3.0 FE Sources or FE Modules, module permissions, collaborators, access audit history, subgraph compile/debug/FFE sync, source_v2, raw feature set group, online/offline feature search, ad feature engineering, oceancloud.tiktok-row.net, mldp-oc-api-service, Academy console URLs, or wants repeatable Academy CLI / JSON workflows — even if they don't explicitly say 'Academy'. Prefer this skill instead of opening the web console whenever the task is supported."
---

# bytedcli Academy

Academy 是字节广告特征开发与管理平台。本 skill 覆盖 3 条检索链路、raw feature set 草稿保存、取版本代码、编译、调试、调试状态查询、数据源授权校验、提交上线、版本代码 diff、待审核工单查询、Lark 群通知，以及调度配置查询（框架版本 / 队列 / 任务参数模板 / dorado 依赖）和用户 on-call 管理员查询：

Academy 3.0 FE Source、FE Module、访问控制、subgraph 与 FFE 命令见 [`references/academy3.md`](references/academy3.md)。它们仍属于本 Academy domain，但使用独立的 `academy3` API 子模块，不能改变下列既有 `source_v2` / raw feature set 命令的路由和行为。

## ID terminology

`fe_config_id` **就是 FFE `graphVersionId`**，标识 FFE graph 的一个具体版本。它不是 logical FFE graph id，也不是 Academy `featureModuleGraphId` 或 Feature Module id。用户给出 `fe_config_id` 时，用 Academy 3.0 `feature-module search --fe-config-id` 反查，不要重新推断 ID 类型。该 endpoint 的后端字段仍叫 `ffeGraphId`。不要把 legacy `academy feature search --ffe-graph-id` 当作 `fe_config_id` 查询；它是另一个 endpoint 的既有 FFE graph id 过滤器。

- `academy source search` — 搜 source_v2 数据源
- `academy raw-feature-set group search` — 搜离线 raw feature set group
- `academy raw-feature-set draft save` — 保存 raw feature set DraftDTO 草稿
- `academy raw-feature-set version get` — 取 raw feature set 某个版本代码（codeTree / taskInfo，-1=草稿）
- `academy raw-feature-set compile` — 编译 raw feature set 某个版本的 DSL（含调度设置中所有 Region）
- `academy raw-feature-set debug` — 发起 raw feature set 某个版本的调试
- `academy raw-feature-set debug-detail get` — 查询单次调试任务详情 / 状态
- `academy raw-feature-set verify-privilege` — 校验当前版本依赖数据源是否给 dorado GDPR PSM 授权
- `academy raw-feature-set submit-online` — 提交上线（预上线）：建工单、编译校验、代码转待审核
- `academy raw-feature-set code-diff get` — diff 两个版本的 codeTree / taskInfo（git-diff 格式）
- `academy raw-feature-set active-order get` — 查当前待审核（未完成）的上线工单，无则返回 null
- `academy raw-feature-set confirm-lark` — 向 OceanCloud 平台助手 Lark 群发确认消息
- `academy raw-feature-set framework-version list` — 查某 Region 的框架版本（frameWorkResource）列表
- `academy raw-feature-set queue list` — 查用户在某 Region 可调度的 yarn 队列
- `academy raw-feature-set task-conf template get` — 取某 Region 的默认调度 taskConf 模板（spark/flink 参数）
- `academy raw-feature-set dorado-task get` — 按 task id + region 查 dorado 依赖任务信息
- `academy feature search` — 搜在线 feature
- `academy user admin-search` — 查 Academy 管理员 on-call 轮值成员列表
- `academy user on-call` — 查当前正在 on-call 的 Academy 管理员列表

除上述已覆盖能力外，其他写操作（create / update / delete）与详情接口当前不在覆盖范围。

### Academy 3.0 workflow

Academy 3.0 按以下依赖顺序执行，但只运行用户要求的阶段：

1. 读取实时 FE Module graph 与 logical-region allowlist。
2. 读取实时 FE Source graph 与 physical-region scope map。
3. 选择精确的 build-ok Feature Engine SCM；缺省时使用最新版本并明确报告。
4. 读取目标 `opName` 的实时 FE Source template。
5. 创建或修改 FE Source；每个启用 scope 都必须完整且符合 template，未知字段与非法 exclusion 必须拒绝，`long_seq_featurebank_source` 必须提供非空 `feature_view`。发起 validation 后轮询到 terminal success 才继续。
6. 创建、fork、rebase 或读取 FE Module；普通 DSL 修改保留当前 SCM 和 scope。
7. 写入或编译现有 FE Module 前先读取 `feature-module access get`。若当前调用者没有对应权限，报告 owner/collaborators 并停止；不要尝试绕过后端授权。
8. 从 module 的精确 `scmVersion` 解析 `baseCommitHash`，以该 commit 下完整的 `feature_engine_core/academy/**` 作为 DSL runtime authority；检查所有 `academy.*` 引用而不只是 `ops.*`。`scm-code-tree get` 只用于 graph code/example snapshot，不能作为 runtime allowlist。读取并保存完整 draft code tree，不要只保存 diff hunk。
9. Resolve 精确的单模块或多模块 code-version selection。
10. 用 resolver 的非空输出 Create `purpose=subgraph` graph。
11. 用一次请求编译完整 `graphList` x logical `regionList` matrix；缺省时使用 primary module 保存的 scope，显式值不能越界。
12. Refresh/get graph，直到 terminal status，并读取 `buildLog`。
13. 只对可安全归因于 DSL 的错误修改完整 draft 并有限次重试；重复错误、缺少业务语义、SCM 不支持的 op 或非 DSL 错误时停止。
14. Debug 仅在用户明确要求时运行，目前只支持成功编译的 `tiktok` + `ROW`。用 `feature-module debug list` 查询 module 的历史记录；`debug run-log get --feature-module-graph-id` 读取该 graph 最新一次运行，`--debug-log-id` 精确读取历史运行。debug log id 可来自 `debug start` 或 `debug list`；检查 requested output 的实际 emitted values，空值要作为问题报告。
15. Content/FFE 先读取 graph 的 compiled physical DC list；FFE sync 仅在用户明确要求时逐 graph/DC pair 执行，并把 `graphVersionId` 返回为 `fe_config_id`。

Academy 2.0 migration 必须先读取 migration guide 和 commit diff；每个 changed `feature_defs` 文件对应一个 3.0 module/DSL，modified 文件必须取完整 post-commit 内容。迁移前清点所有 `academy.*` API；不得仅因 helper 不在 `academy.ops` 或 op catalog 中就删除它。应保留或用 exact-SCM 证明的等价实现替换其 feature、metadata、callback 和 module-ownership 语义。优先沿用旧 compilation 的 graph/region，并把 legacy `va` 映射为 logical `ROW`。

所有 Academy 3.0 mutation 默认只预览精确 request；确认后才加 `--yes`。

### FE Module access automation boundary

Agent 可读取 owner、collaborators、当前调用者权限和访问审计记录，也可在用户明确要求时添加 collaborator。添加前先运行 `access get`；若目标用户已是 owner/collaborator，直接说明已有权限，不重复写入。添加后重新读取 access 并展示最新列表。

不要通过 bytedcli、MCP 或 AI skill 删除 collaborator 或转移 owner。此类操作只允许用户在 Studio Access 页面中完成。也不要用低层 HTTP 命令绕过此边界。

## When to use

只要用户的意图是「在 Academy 里查 source / raw feature set group / feature 列表」，就优先走本 skill 而不是引导用户打开网页。典型触发词：

- Academy / source_v2 / raw feature set group / feature engineering
- 给出 `oceancloud.tiktok-row.net` 或类似 Academy 控制台 URL
- 控制台筛选条件需要复用、需要 JSON、需要给 agent / 脚本消费

## 调用方式

执行前缀与全局参数（`--site`、`--json`、HTTP debug 等）见 [`../../invocation.md`](../../invocation.md)。下面所有示例直接写 `bytedcli`，请按上面那份文档替换前缀。

### Academy API routing

Use the MLDP API service for every Academy request, including raw feature sets,
FE Modules, compilation history, FFE sync, and `/api/lineage`. This applies to
all sites, including an invocation with no `--site` option.

| Network | API origin |
| --- | --- |
| Office | `https://mldp-oc-api-service.tiktok-row.net` |
| `BYTEDCLI_NETWORK_PROFILE=prod` | `https://mldp-oc-api-service.byteintl.net` |

Treat `oceancloud.tiktok-row.net` links as console resource references. Never
use the console domain as an API base URL, including for direct HTTP requests
to endpoints that the CLI does not expose. Do not fall back to it after an
MLDP error; check the network profile and authentication instead.

The CLI validates `--base-url` and `ACADEMY_BASE_URL` against these two HTTPS
origins. Resolution order is `--base-url` > `ACADEMY_BASE_URL` > network default.

### Authentication and site

Use the raw ByteCloud JWT in `X-Jwt-Token`. The MLDP gateways require TikTok
SSO; do not exchange the JWT for a Titan token or add passport cookies.
MLDP validates the ByteCloud JWT itself. Sending a Titan token returns
`{"code":"invalid_authentication_token","message":"X-Jwt-Token is invalid or expired"}`.

The global CLI default remains `cn`, but Academy resolves it to the MLDP host
and authenticates as `i18n-tt`. Plain `i18n`, `i18n-bd`, and `boe` also use
`i18n-tt` authentication. Explicit TikTok sites such as `us-ttp` and `eu-ttp`
keep their selected authentication site.

```bash
bytedcli --site i18n-tt auth login
bytedcli --site i18n-tt --json academy source search --source-name demo_source --owner "%"
```

Keep global options such as `--site` and `--json` before `academy`.

## Quick start

```bash
# 1. 搜 source_v2（最小调用）
bytedcli --site i18n-tt academy source search --source-name demo_source --owner "%"

# 2. 搜离线 raw feature set group，按 owner 过滤
bytedcli --site i18n-tt academy raw-feature-set group search --keyword demo-group --owners demo-user

# 3. 搜在线 feature，需要正整数 FFE graph id 过滤
bytedcli --site i18n-tt academy feature search --keyword demo_feature --ffe-graph-id 123

# 3.1 按 fe_config_id 反查 Academy 3.0 Feature Module
bytedcli --site i18n-tt academy feature-module search --fe-config-id 123

# 3.2 按 fe_config_id 读取该 FFE 版本的精确编译特征、raw feature 与 source
bytedcli --site i18n-tt academy feature-module graph analysis get --fe-config-id 123

# 3.3 查看 FE Module 访问权限和访问审计
bytedcli --site i18n-tt academy feature-module access get --feature-module-id 456
bytedcli --site i18n-tt academy feature-module access-audit list --feature-module-id 456

# 3.4 添加 collaborator（先预览，再确认提交）
bytedcli --site i18n-tt academy feature-module collaborator create \
  --feature-module-id 456 --username demo-user
bytedcli --site i18n-tt academy feature-module collaborator create \
  --feature-module-id 456 --username demo-user --yes

# 4. 保存 raw feature set 草稿（DraftDTO JSON 对象）
bytedcli --site i18n-tt academy raw-feature-set draft save --id 123 --draft-file draft.json

# 4.1 取某个版本代码（-1=草稿；含 codeTree/taskInfo，可用 --json 提取 dsl.py）
bytedcli --site i18n-tt academy raw-feature-set version get --id 123 --version -1

# 5. 编译 raw feature set 某个版本（version 传 -1 自动取草稿/最新版本）
bytedcli --site i18n-tt academy raw-feature-set compile --id 123 --version -1

# 6. 发起 raw feature set 调试（DebugReq body 可选，缺省即空 body 走后端默认值）
bytedcli --site i18n-tt academy raw-feature-set debug --id 123 --version -1 --debug-json '{"regions":["sg","ttp"]}'

# 7. 查询单次调试任务详情 / 状态（debug-id 为 debug 返回的 debug id）
bytedcli --site i18n-tt academy raw-feature-set debug-detail get --debug-id 9001

# 8. 提交上线（预上线，生产写操作；见下方 Agent Guidance 的前置与副作用说明）
bytedcli --site i18n-tt academy raw-feature-set submit-online --id 2444

# 8.1 校验当前版本依赖数据源是否给 dorado GDPR PSM 授权
bytedcli --site i18n-tt academy raw-feature-set verify-privilege --id 2444

# 8.2 diff 两个版本的代码/任务信息（0=线上/已部署版本，-1=当前版本，正数=指定版本）
bytedcli --site i18n-tt academy raw-feature-set code-diff get --id 2444 --base-version 0 --test-version -1

# 8.3 查当前待审核的上线工单（无则打印 no pending order）
bytedcli --site i18n-tt academy raw-feature-set active-order get --id 2444

# 8.4 向 OceanCloud 平台助手 Lark 群发确认消息
bytedcli --site i18n-tt academy raw-feature-set confirm-lark --username demo-user --msg "please confirm"

# 8.5 查 Academy 管理员 on-call 轮值 / 当前在班管理员
bytedcli --site i18n-tt academy user admin-search
bytedcli --site i18n-tt academy user on-call

# 9. 需要给 agent / 脚本消费时，加全局 --json
bytedcli --json --site i18n-tt academy source search --source-name demo_source --owner "%"
```

## Commands

下面的参数表列出每个子命令**自身的 option**；全局参数（`--site` / `--json` / `--http-debug` / 重试与代理等）不在此处罗列，统一放在 `academy` 前，详见 [`../../invocation.md`](../../invocation.md)。

> 列表型参数（如 `--owners`、`--statuses`、`--update-frequencies`、`--versions`）按**单字符串**透传给 Academy 后端，不做客户端拆分；如果后端支持多值，按后端约定写（一般是逗号分隔，例如 `--owners alice,bob`）。

### academy source search

搜索 Academy `source_v2` 数据源。

> **`--source-name` 和 `--owner` 实际上必填，不知道 owner 时传 `--owner "%"`。**
> 后端用 `getParameter` 读这两个参数且无默认值，参数缺失会返回 HTTP 500
> (`Required String parameter 'owner' is not present`)；而 CLI 会把空值从 query
> string 里丢掉，所以省略 `--owner` 或写 `--owner ""` 都会触发这个 500。
> `%` 是 SQL LIKE 通配符且非空，因此能同时满足"参数存在"和"不做过滤"。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 按 `--site` 解析（见上表；或 env `ACADEMY_BASE_URL`） | 仅在默认 host 不可用时覆盖；只填站点根，例如 `https://mldp-oc-api-service.tiktok-row.net`，不要带 path |
| `--page` | int (≥1) | 否 | `1` | 页码 |
| `--page-size` | int (≥1) | 否 | `20` | 每页条数 |
| `--source-name` | string | **实际必填** | - | 按 source 名称过滤，**子串匹配**（`demo_rule_based` 即可命中 `demo_db.demo_rule_based_source`）；不限定时传 `%` |
| `--owner` | string | **实际必填** | - | 单个 owner；**不知道 owner 时传 `%`**，否则会因 owner 过滤而误报 `Total: 0` |
| `--version` | string | 否 | - | 版本 |
| `--type` | string | 否 | - | source 类型 |
| `--datasource-type` | string | 否 | - | datasource 类型 |

```bash
# 只知道表名 → owner 用通配符（最常用写法）
bytedcli --site i18n-tt academy source search \
  --source-name demo_db.demo_rule_based_source --owner "%"

# 子串匹配，不用写全名
bytedcli --site i18n-tt academy source search --source-name demo_rule_based --owner "%"

# 全量列举（两个都用通配符）
bytedcli --site i18n-tt academy source search --source-name "%" --owner "%" --page-size 20
```

### academy raw-feature-set group search

搜索 Academy 离线 raw feature set group。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--page` | int (≥1) | 否 | `1` | |
| `--page-size` | int (≥1) | 否 | `20` | |
| `--keyword` | string | 否 | - | 关键字模糊匹配 |
| `--owners` | string | 否 | - | 单字符串透传，按后端格式（一般逗号分隔） |
| `--statuses` | string | 否 | - | 同上 |
| `--update-frequencies` | string | 否 | - | 同上 |
| `--versions` | string | 否 | - | 同上 |
| `--type` | string | 否 | - | group 类型 |

### academy raw-feature-set draft save

保存 Academy raw feature set 草稿，对应后端 `POST /v2/raw_feature_set/{id}/draft`，请求体为 DraftDTO JSON 对象。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |
| `--draft-json` | JSON object string | 与 `--draft-file` 二选一 | - | 内联 DraftDTO JSON 对象 |
| `--draft-file` | path | 与 `--draft-json` 二选一 | - | 读取 DraftDTO JSON 文件 |

示例：

```bash
bytedcli --site i18n-tt academy raw-feature-set draft save \
  --id 123 \
  --draft-file draft.json
```

### academy raw-feature-set version get

取 raw feature set 某个版本的代码，对应后端 `GET /v2/raw_feature_set/{id}/version/{version}`，无请求体，返回 `RawFeatureSetDTO`（含 `codeTree` / `taskInfo` 等）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |
| `--version` | int (>0 或 `-1`) | 是 | - | 代码版本；`-1` 代表自动获取草稿或最新版本 |

返回结构要点（顶层字段，非嵌在 `content` 下）：

- `codeTree`：UI 风格代码树，节点用 **`title`**（文件/目录名）+ `key` + `content` + `children`；文件叶子节点的 `content` 即源码。常见文件 `academy/dsl.py`、`academy/udf.py`。
- `taskInfo`：调度配置（含各 Region 的 `taskConfList`）。
- `currentVersion`：解析出的代码版本 id；`status`：草稿态为 `draft`。

示例（取草稿 + 用 jq 提取 dsl.py 源码）：

```bash
# 概览（人类可读会打印 name/status/currentVersion 和 codeTree 文件清单）
bytedcli --site i18n-tt academy raw-feature-set version get --id 2444 --version -1

# 提取 dsl.py 全文（JSON + jq，按 title 找文件叶子）
bytedcli --json --site i18n-tt academy raw-feature-set version get --id 2444 --version -1 \
  | jq -r '.data.raw_feature_set.codeTree.children[] | select(.title=="dsl.py") | .content'
```

### academy raw-feature-set compile

编译 Academy raw feature set 某个版本的 DSL（包含调度设置中所有 Region），对应后端 `PUT /v2/raw_feature_set/{id}/version/{version}/compile_all`，无请求体，返回 `CompileInfoDTO`。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |
| `--version` | int (>0 或 `-1`) | 是 | - | 代码版本；`-1` 代表自动获取草稿或最新版本 |

示例：

```bash
# 编译草稿 / 最新版本
bytedcli --site i18n-tt academy raw-feature-set compile --id 123 --version -1

# 编译指定历史版本
bytedcli --site i18n-tt academy raw-feature-set compile --id 123 --version 456
```

### academy raw-feature-set debug

发起 Academy raw feature set 某个版本的调试，对应后端 `PUT /v2/raw_feature_set/{id}/version/{version}/debug`，请求体为 `DebugReq` JSON 对象（可选，缺省时发空 body，后端用默认值），返回 `DebugResultDTO` 列表（每个 region 一条，含 `id`（debug id）/ `region` / `errorMsg`）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |
| `--version` | int (>0 或 `-1`) | 是 | - | 代码版本；`-1` 代表自动获取草稿或最新版本 |
| `--debug-json` | JSON object string | 否（与 `--debug-file` 二选一） | - | 内联 DebugReq JSON 对象 |
| `--debug-file` | path | 否（与 `--debug-json` 二选一） | - | 读取 DebugReq JSON 文件 |

`DebugReq` 常见字段：`regions`（string 数组，如 `["sg","ttp"]`）、`dateTime`（`yyyy-MM-dd`）、`hour`（`HH`）、`writeDebugDB` / `sourceSample`（bool）、`realtimeMaxAllowedNum` / `realtimeMaxAllowedTime`（int）等；全部有后端默认值，可只传需要覆盖的字段。

示例：

```bash
# 指定 region + 日期发起调试
bytedcli --site i18n-tt academy raw-feature-set debug \
  --id 123 --version -1 \
  --debug-json '{"regions":["sg"],"dateTime":"2026-07-10"}'

# 用文件传较大的 DebugReq
bytedcli --site i18n-tt academy raw-feature-set debug \
  --id 123 --version 456 \
  --debug-file debug.json

# 不带 body，走后端默认调试参数
bytedcli --site i18n-tt academy raw-feature-set debug --id 123 --version -1
```

### academy raw-feature-set debug-detail get

查询单次调试任务详情 / 状态，对应后端 `GET /v2/raw_feature_set/debug/{debugId}/detail`，无请求体，返回 `DebugDetailDTO`。`debugId` 由 `raw-feature-set debug` 返回。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--debug-id` | int (>0) | 是 | - | 调试任务 id（debug 命令返回的 `id`） |

示例：

```bash
bytedcli --site i18n-tt academy raw-feature-set debug-detail get --debug-id 9001
```

### academy raw-feature-set submit-online

提交上线（**预上线 / preonline**），对应后端 `PUT /v2/raw_feature_set/{id}/online`，无请求体，返回 `OrderDTO`。这是整条上线链路的**第一步**：创建上线工单、编译校验、把草稿代码与特征集切到「待审核」。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |

示例：

```bash
bytedcli --site i18n-tt academy raw-feature-set submit-online --id 2444
```

返回的 `OrderDTO` 常见字段：`id`（工单 id）、`status`（`RUNNING`/`SUCCESS`/`FAILED`/`STOPPED`/`PENDING`）、`version`（本次提交的代码版本）、`rawFeatureSetId`。

### academy raw-feature-set verify-privilege

校验某 raw feature set **当前版本**依赖的数据源是否已给 dorado GDPR PSM 授权，对应后端 `POST /v2/raw_feature_set/{id}/verify-privilege`，无请求体，返回 `verifyPrivilegeDTO`（`ok` / `errMsg`）。后端取当前版本调度配置里各 Region 的 `taskConfList`，对批式（daily）数据源逐个走 Gemini 权限校验（i18n region 跳过，授权在注册数据源时前置校验）；任一数据源未授权时 `ok=false` 且 `errMsg` 带原因。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |

示例：

```bash
bytedcli --site i18n-tt academy raw-feature-set verify-privilege --id 2444
```

`--json` 成功输出返回 `verify_privilege`：`{ "ok": false, "errMsg": "psm not authorized for ..." }`；`ok=true` 表示当前版本依赖数据源已全部授权。

### academy raw-feature-set code-diff get

Diff 两个 Academy raw feature set 版本的代码（codeTree）与任务信息（taskInfo），对应后端 `GET /v2/raw_feature_set/{id}/code_diff?baseVersion=&testVersion=`，无请求体，返回 `CodeDiffDTO`（`codeDiff` / `taskInfoDiff` 为 git-diff 格式文本，另含 `featureDiff` / `rawFeatureDiff` / `onlineRawFeatureDiff` 等结构化 diff）。后端会解析请求的版本并**始终把较小版本作为 baseline**，返回的 `baseVersion` / `testVersion` 是解析后的实际版本。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |
| `--base-version` | int (正整数 \| `0` \| `-1`) | 是 | - | base 版本：正数=指定版本，`0`=线上/已部署版本，`-1`=当前版本 |
| `--test-version` | int (正整数 \| `0` \| `-1`) | 是 | - | test 版本，取值语义同上 |

示例：

```bash
# diff 线上版本 与 当前草稿版本
bytedcli --site i18n-tt academy raw-feature-set code-diff get --id 2444 --base-version 0 --test-version -1

# 提取 code diff 全文
bytedcli --json --site i18n-tt academy raw-feature-set code-diff get --id 2444 --base-version 0 --test-version -1 \
  | jq -r '.data.code_diff.codeDiff'
```

### academy raw-feature-set active-order get

查询某 raw feature set **当前待审核（未完成）** 的上线工单，对应后端 `GET /v2/raw_feature_set/{id}/order/active`，无请求体，返回 `OrderDTO` 或 `null`（无 pending 工单时）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--id` | int (>0) | 是 | - | raw feature set id |

示例：

```bash
bytedcli --site i18n-tt academy raw-feature-set active-order get --id 2444
```

`--json` 成功输出返回 `{ "id": 2444, "order": {...} }`；无待审核工单时 `order` 为 `null`（人类可读模式打印 `no pending order`）。`OrderDTO` 常见字段：`id`（工单 id）、`status`、`workflowId`、`version`、`rawFeatureSetId`。

### academy raw-feature-set confirm-lark

向 OceanCloud 平台助手 Lark 群聊发送一条 Academy 确认消息，对应后端 `POST /v2/raw_feature_set/confirm/lark`，请求体为 `LarkConfirmMsg` JSON 对象，无返回数据。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--username` | string | 是 | - | 消息中要 @-mention 的用户名 |
| `--msg` | string | 是 | - | 消息正文 |
| `--feature-owner` | string | 否 | - | 要 @-mention 的特征 owner 用户名 |
| `--notify-admin` | string | 否 | - | 要 @-mention 的管理员用户名；**可重复**以通知多位管理员 |

示例：

```bash
bytedcli --site i18n-tt academy raw-feature-set confirm-lark \
  --username demo-user --msg "please confirm" \
  --feature-owner owner-user --notify-admin admin-a --notify-admin admin-b
```

`--json` 成功输出返回 `{ "username": ..., "feature_owner": ..., "notify_admin": [...], "sent": true }`。

### academy raw-feature-set framework-version list

查某 Region 的框架版本（frameWorkResource）列表，对应后端 `GET /v2/raw_feature_set/framework_version/list`，返回 `List<FrameWorkResourceDTO>`（含 `id` / `name` / `region` / `type` / `versionList[].version`）。组装调度 taskConf 时用于选定框架资源。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--region` | enum | 是 | - | Region，取值见下方枚举表 |
| `--update-frequency` | enum | 是 | - | 调度频率（框架 type，后端 query 参数名为 `type`），取值见下方枚举表 |
| `--group-type` | enum | 否 | - | group type；缺省则后端走「不带 groupType/calcEngineVersion」的重载 |
| `--calc-engine-version` | enum | 否 | - | 计算引擎版本 |

示例：

```bash
bytedcli --json --site i18n-tt academy raw-feature-set framework-version list \
  --region ttp --update-frequency daily --group-type user_realtime_ips --calc-engine-version spark_3_2 \
  | jq '[.data.framework_resources[] | {id, name, versions: [.versionList[].version]}]'
```

### academy raw-feature-set queue list

查用户在某 Region 可调度的 yarn 队列，对应后端 `GET /v2/raw_feature_set/queue/list`，返回 `List<QueueDTO>`（含 `queue` / `cluster` / `dc` / `region` / `cpuRate` / `memoryRate` / `queueValue`）。用于填 taskConf 的 `queueInfo`。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--user` | string | 是 | - | 队列归属用户（后端对 ttp 会内部改用固定用户查询） |
| `--region` | enum | 是 | - | Region，取值见下方枚举表 |
| `--is-stream` | bool: 字面量 `true` \| `false` | 否 | `false` | 是否查流式队列；批式填 `false` |

示例：

```bash
# 按 cpuRate+memoryRate 之和挑最空闲队列
bytedcli --json --site i18n-tt academy raw-feature-set queue list \
  --user lingfeng.chen --region ttp --is-stream false \
  | jq '.data.queues | min_by(.cpuRate + .memoryRate) | {queue, cluster, dc, cpuRate, memoryRate}'
```

### academy raw-feature-set task-conf template get

取某 Region 的默认调度 taskConf 模板，对应后端 `GET /v2/raw_feature_set/task_conf/template`，返回 `TaskConfPOJO`（含 `frameWorkResource` / `params`(spark/flink 参数) / `region` 等；注意 `queueInfo` 通常为 `null`，需另用 `queue list` 填）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--region` | enum | 是 | - | Region，取值见下方枚举表 |
| `--update-frequency` | enum | 是 | - | 调度频率，取值见下方枚举表 |
| `--group-type` | enum | 否 | 后端默认 `user_realtime_ips` | group type |
| `--task-type` | enum | 否 | 后端默认 `raw_feature_set` | taskType：`raw_feature_set` \| `sfe` |
| `--calc-engine-version` | enum | 否 | 后端默认 `flink_1_11` | 计算引擎版本；批式一般传 `spark_3_2` |

示例：

```bash
bytedcli --json --site i18n-tt academy raw-feature-set task-conf template get \
  --region ttp --update-frequency daily --group-type user_realtime_ips --calc-engine-version spark_3_2 \
  | jq '.data.task_conf | {frameWorkResource, paramKeys: (.params|keys)}'
```

### academy raw-feature-set dorado-task get

按 task id + region 查 dorado 依赖任务信息，对应后端 `GET /v2/raw_feature_set/dorado_task/{task_id}?region=`，返回 `RecommendDependDTO`（`id` / `name` / `doradoURL` / `offsets` / `offsetsType` / `frequency`）。该结构即 taskConf `dependencies[]` 的元素形态，可用于给某 Region 添加/校验依赖。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--task-id` | int (>0) | 是 | - | dorado task id |
| `--region` | enum | 是 | - | Region，取值见下方枚举表 |

示例：

```bash
bytedcli --json --site i18n-tt academy raw-feature-set dorado-task get --task-id 304327198 --region sg \
  | jq '.data.dorado_task'
```

### 枚举取值（framework-version list / queue list / task-conf template get / dorado-task get 通用）

CLI 端做了枚举校验，传错会直接报错（不发请求）。取值与后端 `enummode/*` 对齐：

| 枚举 | 取值 |
|------|------|
| `--region` | `cn` `cn_offline` `va` `sg` `gcp` `ttp` `tx` `eu` `uswest` `i18n` |
| `--update-frequency` | `realtime` `daily` `estuary_flink` `estuary_spark` |
| `--group-type` | `user_realtime_ips` `user_realtime_kv` `user_batch_bcache` `ad_realtime_kv` `user_long_sequence` |
| `--calc-engine-version` | `spark_3_2` `flink_1_11` `flink_1_17` |
| `--task-type` | `raw_feature_set` `sfe` |

### academy feature search

搜索 Academy 在线 feature。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |
| `--page` | int (≥1) | 否 | `1` | |
| `--page-size` | int (≥1) | 否 | `20` | |
| `--keyword` | string | 否 | - | |
| `--is-fountain-offline-research` | bool: 字面量 `true` \| `false` | 否 | - | **必须是字面量字符串**；`yes`/`1` 会被拒绝 |
| `--ffe-graph-id` | int (>0) | 否 | - | legacy online feature search 的 FFE graph id 过滤器；不是 `fe_config_id` 参数 |

### academy user admin-search

查 Academy 管理员 on-call 轮值成员列表，对应后端 `GET /user/admin/search`，无请求体，返回 `List<String>`（用户名列表）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |

示例：

```bash
bytedcli --site i18n-tt academy user admin-search
```

`--json` 成功输出返回 `{ "admins": ["..."], "total": N }`。

### academy user on-call

查当前正在 on-call 的 Academy 管理员列表，对应后端 `GET /user/admin/on_call`，无请求体，返回 `List<String>`（用户名列表）。

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `--base-url` | string (URL) | 否 | 同上 | |

示例：

```bash
bytedcli --site i18n-tt academy user on-call
```

`--json` 成功输出返回 `{ "admins": ["..."], "total": N }`。

## JSON 输出 schema

`--json` 模式下，三条搜索命令的成功输出结构一致：

```jsonc
{
  "status": "success",
  "data": {
    "rows": [        // 每行字段随上游接口返回；常见列：name / owner / status / version / type
      { "name": "...", "owner": "...", "version": "...", "...": "..." }
    ],
    "total": 123,    // 命中总数
    "page": 1,       // 当前页码（= 入参 --page）
    "page_size": 20  // 每页条数（= 入参 --page-size）
  },
  "context": { "execution_time_ms": 100, "timestamp": "..." }
}
```

消费要点：

- `data.rows` 的字段并非固定 schema，由 Academy 后端决定；agent 解析前应判空、字段名按需 fallback（如 `name` ↔ `sourceName`、`owner` ↔ `owners`）。
- 行内字段**保留上游原始类型**：数字仍是 `number`、布尔仍是 `boolean`、嵌套对象/数组原样透传，不做客户端 stringify。例如 `data.rows[0].ffeGraphId === 123`（不是 `"123"`）。
- 翻页：判断 `data.page * data.page_size < data.total` 决定是否继续翻；下一页用 `--page`+1 重新调用同一命令。
- 失败时 `status` 为 `error`，`data` 为 `null`，错误消息在顶层 `error` 字段。

## Agent Guidance

### 优先直接走 CLI

只要用户的目标是查 source / raw feature set group / feature 列表，直接调用对应命令；不要先让用户打开网页再人工筛选，也不要让用户复制粘贴控制台筛选项。

### Keep direct API requests on MLDP

Follow the Academy API routing section above for CLI and direct HTTP requests.
A console link or an older example does not change the API origin. Use
`--site i18n-tt` for TikTok authentication unless another TikTok site is selected.

### 提交上线（`submit-online`）是有副作用的生产写操作

`raw-feature-set submit-online` 走后端 `PUT {id}/online`（预上线），是整条上线链路的第一步，会真正改状态、发起审批流。后端逻辑要点：

1. 校验特征集非 `offline`；
2. 对当前代码版本**编译校验**，`!ok` 直接失败；
3. slot 完整性检查（禁止只下线 slot 内部分特征）；
4. 快照各 Region 调度配置、source、旧数据到工单 `OrderContext`（供回滚）；
5. **幂等拦截**：若已在审核流程中（`upgrade`/`unreviewed`/…）报 “already submitted”；若当前版本已是线上版本报 “already online”；
6. 状态机推进：特征集 `online→upgrade` 或 `→unreviewed`、代码版本 `draft→unreviewed`、创建 `AcademyOrder`。

因此使用约束：

- 这是**生产写操作**，会创建上线工单、切换代码/特征集状态、触发审批流。执行前必须与用户确认 id、目标 site、当前状态。
- 前置：特征集非 offline、当前有**未上线的草稿版本**且能编译通过；否则会被后端上述校验拦截。
- 后续正式上线（`bpm/online`）、部署等步骤本 skill 暂未接入，需在控制台继续。

### 需要机器可读输出

```bash
bytedcli --json --site i18n-tt academy ...
```

`--json` 是全局参数，必须放在 `academy` 前，写成 `academy ... --json` 不会生效。

### 参数取值踩坑

- `--is-fountain-offline-research` 只接受**字面量** `true` / `false`，传 `yes`、`1`、`True` 会被命令拒绝并提示 `Expected true or false.`。
- `academy feature search --ffe-graph-id` 只接受**正整数**；传 `0` / 负数 / 浮点会被拒。它不是 `fe_config_id` 参数。
- 列表型参数客户端不做拆分，如果不确定后端是否支持多值，先单值调用一次确认。

## Common Errors

| 现象 | 触发条件 | 处理 |
|------|----------|------|
| `Expected true or false.` | `--is-fountain-offline-research` 传了非 `true/false` 字面量 | 改成 `--is-fountain-offline-research true`（或 `false`） |
| `Expected a positive integer.` | `--ffe-graph-id` 不是正整数 | 用正整数（如 `--ffe-graph-id 123`） |
| 401 / UserNotLogin / 缺少 Academy / SSO session | 目标 site 未登录或登错 site | `BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login` 后重试，并显式补 `--site i18n-tt` |
| 已能访问网页但 CLI 报未登录 | 站点隔离：Academy 走 TikTok SSO（i18n-tt / eu-ttp），与 cn / i18n-bd 隔离 | 同上，按目标 site 单独登录 |
| `ACADEMY_INPUT_ERROR` for base URL | `--base-url` or `ACADEMY_BASE_URL` points to a console or unsupported origin | Use one of the two MLDP API origins above |
| `source search` 报 HTTP 500 `Required String parameter 'owner' (或 'sourceName') is not present` | 省略了 `--owner` / `--source-name`，或传了空串——CLI 会把空值从 query string 里丢掉 | 补上 `--owner "%"`（`%` 是 SQL LIKE 通配符且非空，等价于"不过滤"） |
| `source search` 返回 `Total: 0` 但网页上确实有这个 source | `--owner` 填的不是真实 owner，被 owner 条件过滤掉了 | 用 `--owner "%"` 重搜；owner 会在结果里显示出来 |
| 结果 `total > 0` 但 `rows` 为空 | 翻过头，`page * page_size > total` | 减小 `--page` 或检查筛选条件 |

完整 troubleshooting：[`../../troubleshooting.md`](../../troubleshooting.md)。

## References

- [`../../invocation.md`](../../invocation.md)：执行前缀、`--site` 站点表、JSON / HTTP debug 全局参数
- [`references/academy.md`](references/academy.md)：完整命令清单、参数语义、控制台对照
- [`../../troubleshooting.md`](../../troubleshooting.md)：通用错误处理
