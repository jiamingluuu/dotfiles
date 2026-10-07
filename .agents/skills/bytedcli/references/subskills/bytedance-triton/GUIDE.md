---
name: bytedance-triton
description: "Use bytedcli Triton commands for DataLeap 数据安全 permission workflows: apply for Hive table, column, or row/partition-scoped data permission (delegates to Coral, with the 304 合规问卷 / compliance questionnaire flow), answer questionnaire questions, create the application from an answered draft, directly grant table permissions without approval (表管理员/Owner 直接授权 grant), inspect granted privileges of a table (表已授权清单反查 managed), renew expiring permissions in one click, and browse the 审批中心 (approval center) — list my submitted applications, applications awaiting my approval (todo), my historical approval records, and fetch an application detail by group id. Use when the task mentions Triton, 权限申请, 直接授权, 免审授权, 表已授权清单, managed privileges, grant, 分区权限, 行级权限, 权限续期, 续期, 一键续期, 审批中心, approval / approval center, 申请权限, dataleap triton, or 304 / 合规问卷."
---

# bytedcli Triton

Use this skill when the task mentions Triton, 权限申请 (permission apply), 直接授权 (direct
grant), 表已授权清单 (managed privileges), 审批中心 (approval center), approval, 申请权限,
dataleap triton, or 304 / 合规问卷 (compliance questionnaire).

Triton 的权限管理 + 审批中心后端就是 Coral 的权限 API（`coral_<cluster>_api`，同一个
DataLeap host 与认证）。apply/answer/create 直接 delegate 给 Coral；审批中心命令读
`applications/merged/*` / `approvals/merged/*` 端点；grant / managed 走 `privileges/add`
与 `privileges/managed`。

## Invocation

```bash
bytedcli --json triton <command> [options]
bytedcli --json --site i18n-tt triton <command> [options]
```

`--json`, `--site`, `--http-proxy`, `--socks5-proxy`, and every other bytedcli
global flag must appear after `bytedcli` and before `triton`. Keep domain flags such as
`--region` after the Triton subcommand. For example:

```bash
bytedcli --json --site i18n-tt triton approval get --region us-eastred --id 1001
```

本仓库本地测试用：

```bash
node dist/bytedcli.js --json triton <command> [options]
```

The commands below match the current CLI contract and can be used directly. Use
`triton --help` / `triton apply --help` / `triton approval --help` only for options not
covered here; do not guess flags.

`--region` 以 `triton apply --help` 为准；常用值包括 `cn | sg | va | gcp | mycis |
sglark | jplark | uspipo | us-eastred | us`。`cn` 会映射到国内 DataLeap 的
`coral_api` / `cluster=default`；`mycis` 会映射到 DataLeap MYCIS 的
`coral_pinnacle_api` / `cluster=pinnacle`，适合
DataLeap MYCIS Triton 权限申请页面抓包里的 Hive 权限工单。
不传时按 `--site` 映射出默认 region。

### Preserve region across the workflow

Treat the CLI region as routing context, not as a property to rediscover from the returned
resource:

1. Preserve an explicit region from the user, alert, URL, draft, or prior command context.
2. `triton apply` and `triton apply create` return `data.region`; keep that value for later
   `approval list/get/approve/reject` calls. When a group id comes from `approval list`, use
   the same `--region` that produced the list.
3. If the only routing evidence is `groupName=i18ngcp` or `cluster=i18ngcp`, use
   `--site i18n-tt --region us-eastred`.
4. Do not replace that route because an application detail or resource reports
   `cluster=gcp`. That is resource metadata. CLI `--region gcp` selects the separate
   `cluster=texas` permission gateway; it is not the route for i18ngcp.

A wrong region can return HTTP 401 even when the current credential is valid. On 401, first
verify that site and region were preserved or mapped as above, then evaluate authentication;
do not immediately conclude that login is broken.

### Keep target routing separate from network transport

`--site` and `--region` select the target. A proxy only changes how the same request reaches
that target. On a network-class failure such as DNS failure, timeout, or `fetch failed`, keep
the target flags and all Triton arguments unchanged and follow the runtime-specific network
guidance for a read-only retry. Put any proxy flag before `triton`:

```bash
bytedcli --socks5-proxy <proxy-url> --json --site i18n-tt \
  triton approval get --region us-eastred --id 1001
```

Do not copy a development-machine proxy value into this generic skill, and do not change
site/region merely because a proxy is needed.

## 权限申请（apply → answer → create）

apply 不会直接建工单；它返回权限草稿，若命中合规问卷（304）则必须逐题作答后再 create。

```bash
# 1) 发起申请，拿到草稿（可能内联返回 304 合规问卷）
bytedcli --json triton apply \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --permission read --ttl 365

# 列级权限：重复 --column；分区/行级权限：重复 --row-filter column=value
# 注意：传 --column 时默认会自动查询元数据并补齐表的分区字段（如 date, p_date 等），避免后续查询报 403；若不需要补齐可加 --no-auto-partition
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --auth-object demo-user
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --no-auto-partition --auth-object demo-user
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --auth-object demo-user

# 同一字段允许多个精确值；每个值重复一次 --row-filter
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --row-filter app=sample-app-lite --auth-object demo-user

# PSM 接收方：--auth-type psm（ttl 默认 0）
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.psm --permission write --ttl 0

# 跨库转储 / 写入权限（ETL 跨库写入、数据回流清洗场景）
# --can-dump 开启转储权限；--dump-database 指定允许转储的目标数据库（可重复或逗号分隔）
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --can-dump --dump-database target_db --auth-object demo-user
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --can-dump --dump-database db1,db2 --auth-object demo-user --dry-run

# CN：国内机房默认走 coral_api / cluster=default
bytedcli --json triton apply --region cn \
  --db-name example_db --table-name example_table \
  --auth-object demo-user --permission read --ttl 365

# MYCIS / pinnacle：发起 Hive 表读权限审批工单，PSM 接收方 ttl 通常为 0
bytedcli --json triton apply --region mycis \
  --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.project.psm \
  --permission read --ttl 0 --lang zh_CN \
  --reason "Need read access for approved data analysis."

# PIPO US：保留页面 notice 确认（提交 ignore_notice=false）
bytedcli --json triton apply --region uspipo \
  --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.psm \
  --permission read --ttl 0 --lang zh_CN --no-ignore-notice

# 2) 若检测到 304 合规问卷，逐题作答（question id / option 来自 apply 输出）
bytedcli --json triton apply answer \
  --draft-file /tmp/triton-permission-draft.json \
  --question-id q1 --answer "是 Yes"

# 3) 逐题答完后，用已作答的草稿创建申请工单
bytedcli --json triton apply create \
  --draft-file /tmp/triton-permission-answered-draft.json
```

### 304 合规问卷说明

- "304 文档" 是接口**内联返回**的结构化问答题（`resource_questions_answers{id,type,topic,options}`），
  **不是**要上传的合规文件。
- `triton apply` 默认发送 `ignore_notice=true`；只有产品抓包或页面流程明确要求
  `ignore_notice=false` 时，才加 `--no-ignore-notice`。
- apply 输出会列出每道题的 `id` / `type` / `topic` / `options`；用这些 id 去 `apply answer`。
- 多选题：重复 `--answer`。question id 与 option 必须来自 apply/draft 输出，**禁止臆造**。
- 真实工作流里，作答前先问用户；不要擅自替用户回答合规问题。
- `--row-filter` 表示精确的行级/分区授权范围，不是 SQL 条件。格式必须是
  `column=value`；同一字段的多个值重复传参。不要用 `--column app` 代替
  `--row-filter app=sample-app`，前者只申请读取 `app` 列。

## 表管理员免审直接授权（grant）

表 Owner 或管理员可直接给用户或 PSM 授予权限，无需走审批流。

```bash
# 预览授权计划（--dry-run）
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --dry-run

# 确认直接授权给个人用户（默认读权限 read，TTL 365天）
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --yes

# 授权给 PSM（PSM 授权 TTL 默认 0，即永不过期；支持写权限 write）
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.psm --permission write --ttl 0 --yes

# 指定自定义申请/授权理由
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --reason "用于数据分析业务需求" --yes
```

- **确认门**：默认 dry-run 保护，只有传 `--yes` 时才会实际调用接口；JSON 模式无 `--yes`
  直接抛 `TRITON_CONFIRM_REQUIRED`。
- **TTL 默认值**：`--auth-type psm` 时默认 0（永不过期）；`person` 时默认 365 天。

## 表已授权清单反查（managed list）

表 Owner / 管理员反查某张 Hive 表当前已生效的授权列表。

```bash
# 查询表的已授权列表
bytedcli --json triton managed list \
  --region sg --db-name example_db --table-name example_table

# 按授权对象或类型过滤
bytedcli --json triton managed list \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user

# 分页查询
bytedcli --json triton managed list \
  --region sg --db-name example_db --table-name example_table \
  --page 1 --page-size 20
```

## 审批中心（approval center，只读）

```bash
# 单一 verb-last 的 list 命令，--type 选队列：submitted(我提交,默认) | todo(待我审批) | reviewed(我审批过)
# 我提交的权限申请（默认 --type submitted）；--days 仅 submitted 生效，默认 180
bytedcli --json triton approval list --region sg --page-size 5
bytedcli --json triton approval list --type submitted --region sg --days 30 --query example_table

# 待我审批：等我审批的工单
bytedcli --json triton approval list --type todo --region sg --page-size 5

# 审批记录：我历史的审批决策
bytedcli --json triton approval list --type reviewed --region sg --page-size 5

# 申请详情：按 group id 看单条申请
bytedcli --json triton approval get --region sg --id 1001

# i18ngcp：沿用 list/apply/create 的 us-eastred region；不要改成 gcp
bytedcli --json --site i18n-tt triton approval get --region us-eastred --id 1001
```

## 通过 / 拒绝（approve / reject）

```bash
# 通过：approve-as-requested，原样回写 ttl/permission/permission_usage（已 live 抓包验证）
bytedcli triton approval approve --region sg --id 100001 --yes

# 拒绝：强制 --reason（作为审批 comment）
bytedcli triton approval reject --region sg --id 100001 --reason "duplicate request" --yes
```

端点（已 live 抓包，见 `src/api/triton/AGENTS.md`）：先 `GET applications/merged/detail/{id}`
取 `application_dto.resources[].aid`，再 `POST /api/v1/applications/update/tasks`（per-resource
决策数组）。1-resource batch 通常即返回 `SUCCESS`，否则轮询 `GET /api/v1/tasks/{taskId}?cluster=`。

- **确认门**：不带 `--yes` 不会真改。JSON 模式无 `--yes` 直接报
  `TRITON_CONFIRM_REQUIRED`（不交互）；text 模式打印 summary 后让你加 `--yes` 重跑。
- 只操作 `--id` 单工单，绝不批量其他工单。
- ⚠️ **reject 的 `status:"REFUSED"` + `comment` 字段是未验证假设**（抓包时不会拒真实申请人，
  approve 才实测过）：**首次真实 reject 前，务必先在 DataLeap web 端人工复核该工单是否真被拒绝；
  若 CLI 返回与预期不符，按真实抓包修正后再用。** 不要把 reject 当成已验证行为陈述。

## 我的权限续期（renew）

一键续期当前用户在 Triton 上即将到期的权限。命令先列出"我的权限"，默认只续期服务端标记
`suggest_to_renew=true` 的权限（到期前 30 天内才会标记）；没有需要续期的权限时不调用
续期 API，直接返回"无需操作"。

```bash
# 预览哪些权限会被续期（不实际执行）
bytedcli --json triton renew --dry-run

# 确认续期（需要 --yes）
bytedcli --json triton renew --yes

# 指定 region / cluster（默认 cn / default）
bytedcli --json triton renew --region cn --cluster cn6 --yes

# 自定义续期时长（天，默认 365，不超过上次审批通过时长）
bytedcli --json triton renew --ttl 90 --yes

# 把服务端标记 can_renew（当前允许续期）但尚未建议续期的权限也一并处理
bytedcli --json triton renew --include-renewable --yes
```

- **默认只续期 `suggest_to_renew=true` 的权限**：这是平台在临期时主动给出的建议，无人值守
  任务只处理这一类。CLI 会先过滤，不会对全部权限发起续期。
- **`--include-renewable` 放宽到 `can_renew`**：服务端另有 `can_renew` 表示当前允许续期
  （Triton UI 据此点亮每行的续期按钮），它可能在远未到期时就为真，因此不纳入默认范围 ——
  否则会比平台预期早得多地续期。当默认范围为空但存在这类权限时，命令会说明有几条并提示
  该参数，避免出现"页面按钮可点、CLI 说没有需要续期的"这种困惑。
- **必填申请参数自动复用**：续期接口要求需求类型和非空的详细原因（UI 表单标红星的两项），
  缺失会被服务端逐条拒绝且任务仍报 SUCCESS。CLI 复用该资源上次提交的内容
  （`last_apply_desc_map`），无记录时兜底填 `其他 / Others` 加一段通用原因；空对象、空串、
  `null` 都按"无记录"处理。
- **TTL 按资源逐条收敛**：服务端限制续期时长不超过上次审批通过的时长，且该上限按资源不同。
  `--ttl` 只作上限，每个对象取 `min(请求值, 自己的 last_ttl)`。
- **跨 cluster 自动分组**：如果待续期权限分布在多个 cluster（如 default 和 cn6），CLI
  会按 cluster 分组发送续期请求，结果按 cluster 返回明细；同一 cluster 内每 50 条分批提交。
- **单批失败不影响其余批次**：批次是彼此独立的服务端任务，某批失败时其余批次继续提交，
  失败批次会在结果中列出它提交过的资源。
- **续期 0 条视为失败**：任务返回 SUCCESS 但 `successCount=0` 时报错退出，避免把静默失效
  报成续期成功。
- **确认门**：与 approve/reject 一致，`--dry-run` 预览、`--yes` 才提交；JSON 模式无
  `--yes` 报 `TRITON_CONFIRM_REQUIRED`。
- L4 数据不允许自助续期，到期后需重新走审批。
- 返回结果包含 `action`（`none` / `dry-run` / `renewed`）、`renewed`（成功数）、
  `batches`（每个 cluster 的任务明细）、`privileges`（权限明细），以及 `failures`
  （未成功续期的资源，按批次给出 `cluster` / `resources` / `exact`；`exact=false` 表示
  服务端只回了计数、无法精确定位到具体某条，只能确定失败发生在该批次内）。

## Rules that matter

- 草稿、debug payload 写 `/tmp`，不要把临时文件写进仓库。
- apply/answer/create 的 question id、option id 必须来自 Coral draft/API 输出，禁止编造 schema 或答案 id。
- 真实工作流里，作答合规问卷前先问用户；只有在明确授权的测试里才随机作答。
- `--auth-type psm` 时 `--ttl` 默认 0；`person` 时默认 365。
- `approval get` 的 `--id` 是申请的 group id（与列表返回的 group id 同源）。
- 查询、通过或拒绝已有工单时，沿用 apply/create/list 的 CLI region；
  `groupName/cluster=i18ngcp` 对应 `--region us-eastred`，不能因返回资源含
  `cluster=gcp` 改成 `--region gcp`。
- 写操作（approve/reject/renew）必须 `--yes` 确认；⚠️ reject 的 REFUSED 字段为未验证假设，
  首次真实 reject 前务必先在 DataLeap web 端人工复核该工单是否真被拒绝；
  若 CLI 返回与预期不符，按真实抓包修正后再用。不要把 reject 当成已验证行为陈述。
- renew 默认只续期 `suggest_to_renew=true` 的权限，`--include-renewable` 才放宽到
  `can_renew`；没有待续期权限时不调用 API，返回"无需操作"。
