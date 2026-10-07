---
name: bytedance-gpcp
description: "Use bytedcli gpcp for the GPCP (SYS-OnePlatform) umbrella platform. Covers Data Inventory asset search, verified SG Hive asset-ID resolution, and asset metadata lookup; Privacy Policy Center (策略中心) policy list and detail lookup, label-management enum group and condition group queries, selection run (圈选任务) list and detail, plus guarded creation of a mock policy and of a manual selection run; read-only Aegis issue inspection; SDP compliant diagnostics (jobs, whitelist, bounded WebShell commands); MSC privacy/software-composition and rule-template queries; guarded DS TPSDK governance registration for APIs that already exist in SDKAPIV3; cmpflow Ticket Center governance ticket queries (list/stats); and cmpflow workflow configuration get/export/guarded-import (including ROW→BOE) plus customized-role create/update."
---

# bytedcli GPCP (SYS-OnePlatform) — Data Inventory, Privacy Policy Center, Aegis, SDP, MSC, and cmpflow

GPCP ("SYS-OnePlatform") is the umbrella platform.
bytedcli exposes Data Inventory asset lookup under `bytedcli gpcp data-inventory asset ...`,
**Privacy Policy Center** (策略中心) policy, label-management, and selection-run queries plus
mock-policy create and manual selection runs under
`bytedcli gpcp privacy-policy-center ...`, read-only **Aegis issue inspection** under
`bytedcli gpcp aegis issue ...`, **SDP** (System Diagnosis Platform,
系统诊断平台) under `bytedcli gpcp sdp ...`, **MSC** under
`bytedcli gpcp msc ...`, the read-only **cmpflow Ticket Center**
(operation_center governance tickets) under `bytedcli gpcp cmpflow ticket ...`,
and guarded **workflow-config import / role maintenance** under
`bytedcli gpcp cmpflow workflow-config ...` and `bytedcli gpcp cmpflow role ...`.

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

## When to use

- 需要查询 Aegis 工单列表，按 repo / commit / rule / location / status 等条件筛选，或读取一个 ticket 的完整详情。
- 用户提到 Aegis issue、Aegis ticket、静态扫描工单、matched rule、logical status。
- 需要在合规区域（ROW `sg` / `va`）对 CloudIDE 空间创建 SDP 指令执行实例。
- 需要通过 SDP WebShell 执行一条**有界、只读**的诊断 / 日志指令（如 `ls`、`tail -n N <file>`）。
- 用户提到 GPCP、SYS-OnePlatform、SDP、系统诊断平台、白屏化运维、指令执行实例、SDP WebShell。
- 需要搜索 Data Inventory 资产、按 SG Hive `database.table` 确认唯一 `asset_id`，或读取已知资产 ID 的元数据。
- 需要在策略中心（Privacy Policy Center）按状态、使用类型或策略类型检索策略，或不知道 policy id 需要先找出来。
- 需要查询策略中心标签管理里的枚举组（某标签的可选值）或条件组（可复用的 label_condition 子句），或需要知道拼 `label_condition` 时 `label_id` / `operator` 该怎么写。
- 需要查询策略中心（Privacy Policy Center）单个策略的详情、它的圈选规则（label_condition），或某个历史版本的策略快照。
- 需要查看某个策略下跑过哪些圈选任务、单次圈选任务的状态与对应的 dorado 任务链接。
- 需要在策略中心创建仿真策略（MOCK），或在某个策略上创建单次圈选任务。
- 用户提到策略中心、strategy center、data protection policy、仿真策略、MOCK policy、圈选任务、adhoc 策略下建 task、策略详情、圈选记录、策略列表、标签管理、枚举组、条件组、enum group、condition group。
- 需要查询 MSC 三方 SDK API 主数据（3rd SDK API / SDKAPIV3）。
- 需要查询 DS TPSDK 扫描任务、版本事实/离线分析报告、app 级 API 治理状态。
- 需要把 SDKAPIV3 中已经存在的 API 按 `api_id` 注册到 app 级 DS TPSDK 治理；默认只预检，明确 `--yes` 才写入。
- 需要查询 DS TPSDK 全局组件分类 cache 或 API 数据标签 cache。
- 需要按 BITS 应用和 class name 查询跨版本的组件归属、owner、value chain 与 POC。
- 需要按中英文应用名找到 `bits_appid`（BPEA 的 `msc_app_id`），查询 BPEA DFID、登记表单、原始 schema data，或读取一个 BPEA 扫描工单及其问题列表。
- 需要查询 MSC 规则模板、模板版本、模板中的规则快照、规则历史版本或规则类型。
- 需要查询 GPCP cmpflow（Ticket Center / operation_center）治理工单：按二级项目（secondary project）拉工单列表、按状态过滤（如 Overdue 逾期）、或查看顶部状态统计与完成率。
- 这是 GPCP 下的 SDP（合规运维 shell），不是 SPD（Security Privacy Data），也不是 ByteSD（`sd` 服务发现）。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- Aegis 使用独立的 GPCP Web cookie session；`username`、Aegis
  `access_token` 与 GPCP persistence token 只在进程内存中使用，不写磁盘、
  不输出。缓存 cookie 失效时，CLI 会在有 GUI 的机器上打开临时浏览器，需在
  TikTok SSO 页面用账号密码完成登录。无 GUI 的 Linux 主机会快速返回
  `GPCP_AEGIS_INTERACTIVE_BROWSER_REQUIRED`；请换到有 GUI 的机器完成命令。
  通用 ROW SSO 登录态本身不保证已建立 GPCP Aegis session。
- SDP 需要 ROW SSO 登录态：`bytedcli --site i18n-tt auth login`（GPCP ROW 是 tiktok-env 服务）。
- Privacy Policy Center 走 ROW GPCP 平台 Web session（与 cmpflow 同一套换票）：首次或会话过期时运行 `bytedcli --site i18n-tt auth login --session --auto`。
- MSC 按资源选择默认 deployment：app、规则模板、3rdsdkapi、ds-tpsdk 默认 CN，需要 `bytedcli --site cn auth login`；symbol-component search 与 BPEA micro 默认 ROW，需要 `i18n-tt` 登录态。
- BPEA DFID/form/schema/order 查询由 GPCP 主应用提供认证信息，但业务请求直达 MSC；除 Cloud JWT 外还需一次性建立 Web session：`bytedcli --site i18n-tt auth login --session --auto`。登录只需在会话过期后重做，不需要给每条查询命令添加 `--site`。
- cmpflow Ticket Center 查询走 ROW GPCP 平台 Web session（与 BPEA 同一套 `/api/v1/platform/oauth2/login` + user-info 换票）；首次或会话过期时运行 `bytedcli --site i18n-tt auth login --session --auto`。
- CloudIDE target 需要目标 workspace 的权限（可共享）。
- SDP 仅覆盖 ROW；eu-ttp 机器因网络问题暂不支持。US 合规区域受限时按合规通道处理。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 查询 Aegis 工单（只读；默认 page=1 / page-size=20 / pipeline-page=1）
bytedcli --json gpcp aegis issue list --repo-name example/repository

# 搜索 Data Inventory 资产；精确 SG Hive 解析会校验完整祖先路径
bytedcli gpcp data-inventory asset search --asset-type-id core.hive_v2.table --keyword sample_table
bytedcli --json gpcp data-inventory asset get --full-name sample_database.sample_table --region sg
bytedcli --json gpcp data-inventory asset metadata get --asset-id sample-asset-id --field core.owner

# 常用筛选：commit / logical status / rule / location / scan type
bytedcli --json gpcp aegis issue list \
  --repo-name example/repository \
  --commit-hash demo-commit-hash \
  --logical-status 1 \
  --status 0 \
  --matched-rule demo-rule \
  --location demo/file.go:42 \
  --scan-type code

# 查询单个工单完整详情（numeric ticket id）
bytedcli --json gpcp aegis issue get --ticket-id 123456

# 创建 SDP 指令执行实例（--user 必填；--target 默认 cloudide，默认 region sg）
bytedcli --json gpcp sdp job create --target cloudide --workspace-id ws-example --user byteide

# 其他 target（TCE / Bernard / Merlin / Yarn）
bytedcli --json gpcp sdp job create --target tce --pod-name data-...-4dtvk --user root
bytedcli --json gpcp sdp job create --target bernard --pod-name data-...-4dtvk --user root
bytedcli --json gpcp sdp job create --target tce --pod-name data-...-4dtvk --tce-container-type sidecar --container-name main --user root
bytedcli --json gpcp sdp job create --target merlin --merlin-type devbox --merlin-id 36319 --user root
bytedcli --json gpcp sdp job create --target merlin --merlin-type trial --merlin-id pod-abc --user tiger
bytedcli --json gpcp sdp job create --target yarn --ip 192.0.2.10 --app-id application_123 --user root

# 查询已创建实例的详情
bytedcli --json gpcp sdp job get --job-id 123

# 查白名单（可执行指令），keyword 为服务端子串匹配（可选）
bytedcli --json gpcp sdp whitelist list --keyword vim

# 通过 WebShell 执行一条有界诊断指令
bytedcli --json gpcp sdp command execute --job-id 123 --command "tail -n 200 /path/to/log"

# 保留 ANSI 转义序列（默认会剥离）
bytedcli --json gpcp sdp command execute --job-id 123 --command "ls --color" --no-strip-ansi

# 查询 MSC 三方 SDK API 与 SDK catalog
bytedcli --json gpcp msc sdk-api list --keyword location --page-size 20
bytedcli --json gpcp msc sdk-api-version get --api-id 101
bytedcli --json gpcp msc sdk list

# app / 三方 SDK API / DS TPSDK 默认 deployment 是 cn；诊断时可显式选择 row
bytedcli --json gpcp msc sdk-api list --deployment row --keyword location --page-size 20

# 查询 DS TPSDK task / report
bytedcli --json gpcp msc tpsdk-task get --task-id sample-task-id
bytedcli --json gpcp msc tpsdk-report get --scope offline_analysis --task-id sample-task-id
bytedcli --json gpcp msc tpsdk-report get --scope version_facts --bits-app-id 123456 --app-version 1.0.0

# 查询 app 级治理与两个全局 cache
bytedcli --json gpcp msc tpsdk-governance list --bits-app-id 123456 --platform iOS
bytedcli --json gpcp msc tpsdk-component-cache list --platform iOS --data-sharing true
bytedcli --json gpcp msc tpsdk-api-label-cache list --sdk sample-sdk --sensitive true

# 只预检：确认 api_id 全部存在于 SDKAPIV3 且平台一致，不产生写入
bytedcli --json gpcp msc tpsdk-governance register --bits-app-id 123456 --platform iOS --api-ids 101,102 --dry-run

# 明确确认后注册治理行；即使带 --yes，也会先执行同一套 SDKAPIV3 预检
bytedcli --json gpcp msc tpsdk-governance register --bits-app-id 123456 --platform iOS --api-ids 101,102 --yes

# 按中英文应用名找 bits_appid；该值就是后续 BPEA 命令的 msc_app_id
bytedcli --json gpcp msc app list --name sample
bytedcli --json gpcp msc app list --region oversea --bits-app-id 123456

# 按 class name 查询跨版本组件归属；该资源默认 ROW
bytedcli --json gpcp msc symbol-component search --bits-app-id 123456 --class-name sample.ClassName --page-size 10

# 查询已聚合去重的 DFID、登记表单，以及批量原始 schema_data 字符串
bytedcli --json gpcp msc bpea-dfid list --msc-app-id 123456 --dataflow-type 3 --page-size 20
bytedcli --json gpcp msc bpea-dfid-form list --msc-app-id 123456 --dataflow-type 2 --sdk-names sample-sdk
bytedcli --json gpcp msc bpea-dfid-schema get --msc-app-id 123456 --dfids dfid-a,dfid-b

# 按原生 order_id 读取 BPEA 扫描工单及其 issues；页面 URL 的 projectId/mscId 无需传入
bytedcli --json gpcp msc bpea-order get --order-id 12345

# 查询规则模板、模板版本，以及模板版本中的规则
bytedcli --json gpcp msc template list --app-id 123 --all true
bytedcli --json gpcp msc template-snapshot list --template-id 456
bytedcli --json gpcp msc template-rule list --template-snapshot-id 789
bytedcli --json gpcp msc template-rule list --bits-app-id 123456 --alias sample-alias --all true

# 管理页面同款规则筛选、当前线上规则、反查模板和历史版本
bytedcli --json gpcp msc template-rule search --template-id 456 --template-snapshot-id 789 --keyword sample --page-size 20
bytedcli --json gpcp msc rule list --app-id 123
bytedcli --json gpcp msc template-by-rule list --rule-id 101
bytedcli --json gpcp msc rule-version list --rule-id 101 --template-id 456
bytedcli --json gpcp msc rule-type list --keyword sample
```

### Data Inventory 资产查询

Data Inventory 资源统一在 `bytedcli gpcp data-inventory asset ...` 下：

- `asset search`：按类型、关键词、路径或元数据筛选做模糊发现；`--asset-type-id` 必填，支持可重复的 `--filter <key=value>`、`--page` 和 `--page-size`。
- `asset get`：用于 SG Hive 表的精确 `asset_id` 解析；传 `--full-name <database.table> --region sg`。命令会在 SG VRegion 查询同名候选、遍历分页，并验证 `hive.sg.<database>` 祖先路径与叶节点身份；没有唯一匹配时返回 not-found 或 ambiguous，不按候选顺序猜测。
- `asset metadata get`：按已知 `--asset-id` 读取元数据；可重复 `--field <metadata-id>` 限定字段，`--include-aggregated-metadata` 返回聚合元数据。

Data Inventory 使用 `i18n-tt` ByteCloud user JWT；会话过期时执行：

```bash
bytedcli --site i18n-tt auth login
```

对于已有 `pnscli di asset-search ...` 工作流，改用 `bytedcli gpcp data-inventory asset search ...`。实际命令面以 `bytedcli gpcp data-inventory --help` 为准。

### Privacy Policy Center（策略中心）

检索策略、查询标签管理里的枚举组与条件组、查询单个策略与它的圈选任务，创建仿真策略（`usage_type=MOCK`），或在某个策略上创建单次圈选任务：

```bash
# 列出策略（默认 --status online / page=1 / page-size=20），用来找 policy id
bytedcli gpcp privacy-policy-center policy list

# 只看仿真策略；按策略类型过滤；翻页
bytedcli gpcp privacy-policy-center policy list --usage-type mock --page-size 50
bytedcli --json gpcp privacy-policy-center policy list --policy-type exemption --page 2

# 精确取若干策略；--policy-id 可重复
bytedcli --json gpcp privacy-policy-center policy list --policy-id 900001 --policy-id 900002

# 需要完整策略记录（规则树 / 执行配置 / 豁免配置）时才加 --full
bytedcli --json gpcp privacy-policy-center policy list --usage-type mock --full

# 标签管理：枚举组（某个标签的可选值集合）
bytedcli gpcp privacy-policy-center enum-group list --scope governance
bytedcli gpcp privacy-policy-center enum-group get --id 900101

# 标签管理：条件组（可复用的 label_condition 子句）
bytedcli gpcp privacy-policy-center condition-group list
bytedcli gpcp privacy-policy-center condition-group get --id 900201

# 查询单个策略详情（含 label_condition 规则树）
bytedcli gpcp privacy-policy-center policy get --id 900001

# 查询某个历史版本的策略快照
bytedcli --json gpcp privacy-policy-center policy get --id 900001 --version 3

# 列出该策略上的圈选任务（默认 page=1 / page-size=20）
bytedcli gpcp privacy-policy-center process list --policy-id 900001

# 需要每个阶段的 dorado 任务明细时才加 --stages
bytedcli --json gpcp privacy-policy-center process list --policy-id 900001 --page-size 50 --stages

# 查询单次圈选任务，含 dorado 任务与实例链接
bytedcli gpcp privacy-policy-center process get --id 68001

# 需要本次执行时的策略快照时才加 --policy-info
bytedcli --json gpcp privacy-policy-center process get --id 68001 --policy-info

# 默认 dry-run，只打印将要提交的完整 payload
bytedcli gpcp privacy-policy-center policy create \
  --name demo-mock-policy --description 'demo mock policy' \
  --business-case DR --user-group-id 10001 \
  --label-condition '{"combine_type":"AND","combines":[{"logic":"A","label_group_name":"Resource","sub_logics":[{"id":"A","values":[{"enum_name":"0","enum_id":null}],"label_group_name":"Resource","label_id":100,"entity_type":"TABLE","label_name":"demo_table_label","operator":"is not null"}]}]}'

# 确认无误后加 --yes 才真正提交
bytedcli --json gpcp privacy-policy-center policy create \
  --name demo-mock-policy --description 'demo mock policy' \
  --business-case DR --user-group-id 10001 \
  --label-condition '{"combine_type":"AND","combines":[{"logic":"A","label_group_name":"Resource","sub_logics":[{"id":"A","values":[{"enum_name":"0","enum_id":null}],"label_group_name":"Resource","label_id":100,"entity_type":"TABLE","label_name":"demo_table_label","operator":"is not null"}]}]}' \
  --yes

# 带括号的 A&&B&&(C||D) 树同样直传 label_condition 对象，不要包一层 {"label_condition":...}
bytedcli gpcp privacy-policy-center policy create \
  --name demo-mock-policy --description 'demo mock policy' \
  --business-case DR --user-group-id 10001 \
  --label-condition '{"combine_type":"AND","combines":[{"logic":"A&&B&&(C||D)","label_group_name":"Resource","sub_logics":[{"id":"A","values":[{"enum_name":"1","enum_id":null}],"label_group_name":"Resource","label_id":100,"entity_type":"TABLE","label_name":"demo_table_label_a","operator":"in"},{"id":"B","values":[{"enum_name":"0","enum_id":null}],"label_group_name":"Resource","label_id":200,"entity_type":"TABLE","label_name":"demo_table_label_b","operator":"is not null"},{"id":"C","values":[{"enum_name":"0","enum_id":null}],"label_group_name":"Resource","label_id":300,"entity_type":"TABLE","label_name":"demo_table_label_c","operator":"not equal"},{"id":"D","values":[{"enum_name":"7","enum_id":null}],"label_group_name":"Resource","label_id":400,"entity_type":"TABLE","label_name":"demo_table_label_d","operator":"exclude any"}]}]}'

# 默认 dry-run，只打印将要提交的完整 payload
bytedcli gpcp privacy-policy-center process create \
  --policy-id 900001 --label-date 20260315 --secondary-project-id 35 \
  --source-table sample_database.sample_table --source-region sg \
  --data-filter "date='20260315'" --output-label 100:demo_table_label

# 确认无误后加 --yes 才真正提交
bytedcli --json gpcp privacy-policy-center process create \
  --policy-id 900001 --label-date 20260315 --secondary-project-id 35 \
  --source-table sample_database.sample_table --source-region sg \
  --data-filter "date='20260315'" --partition date=20260315 \
  --output-labels-file ./demo-labels.json --yes

# Condition Expression 圈选（task_data_source_type=LABEL_CONDITION）
bytedcli gpcp privacy-policy-center process create \
  --policy-id 900001 --label-date 20260315 --secondary-project-id 35 \
  --data-source-type label-condition \
  --label-condition '{"combines":[{"logic":"A","sub_logics":[{"id":"A","values":[{"enum_name":"0","enum_id":null}],"label_group_name":"Resource","label_id":100,"entity_type":"TABLE","label_name":"demo_table_label","operator":"is not null"}]}]}' \
  --output-label 100:demo_table_label

# Result Process = None，不创建 Cogos 工单；Is Deduplication = No
bytedcli gpcp privacy-policy-center process create \
  --policy-id 900001 --label-date 20260315 \
  --result-process none --deduplication no \
  --source-table sample_database.sample_table --source-region sg \
  --output-label 100:demo_table_label

# Ticket handle = Auto，指定 UTC 发单时间；不传 --send-ticket-time 则任务完成后自动发
bytedcli gpcp privacy-policy-center process create \
  --policy-id 900001 --label-date 20260315 --secondary-project-id 35 \
  --ticket-handle auto --send-ticket-time '2026-03-15 12:00:00' \
  --source-table sample_database.sample_table --source-region sg \
  --output-label 100:demo_table_label
```

Agent Guidance：

- 认证走 GPCP 网页登录态，不使用 ZTI：先执行一次 `bytedcli --site i18n-tt auth login --session --auto`，否则命令返回 `PRIVACY_POLICY_CENTER_AUTH_REQUIRED`。只跑 `auth login`（不带 `--session`）不够。
- 默认只预览不提交；确认 payload 后再加 `--yes`。
- `policy create` 固定发送 `usage_type=MOCK` 与 `policy_type=REGULAR_POLICY`，不要改成 ONLINE。`--label-condition` 对应控制台请求体字段 `label_condition`，传入该字段的 JSON 对象本身（`{"combine_type":"AND","combines":[...]}`），包括 `logic` 为 `A&&B` 或 `A&&B&&(C||D)` 的多标签树；不要再包一层 `{"label_condition":...}`，也不要为 `in` / `not equal` / `exclude any` 另造 flag。
- `process create` 默认 `--result-process cogos-ticket`（控制台 Result Process = Cogos Ticket，`governance_result_handle_type=1`），会走发单链路，不要随意提交；只需圈选不发单时用 `--result-process none`。`--ticket-handle` 对应 Cogos Ticket 旁边的 Manual/Auto，默认 `manual`；`auto` 可再带 `--send-ticket-time`（UTC `YYYY-MM-DD HH:mm:ss`），不传则任务完成后自动发。`--deduplication` 对应控制台 Is Deduplication，默认 `yes`。`--secondary-project-id`（Ticket Template）只在 `cogos-ticket` 时必填。
- `process create` 默认 `--data-source-type hive-table`，需要 `--source-table` 与 `--source-region`。Condition Expression 圈选用 `--data-source-type label-condition`，并传 `--label-condition` / `--label-condition-file`（控制台提交体是 `{"combines":[{"logic":"...","sub_logics":[...]}]}`，不要再包一层 `{"label_condition":...}`）。两种模式都要带 `--output-label`。
- 分区表必须传 `--data-filter`（例如 `--data-filter "date='20260315'"`）。只传 `--partition` 不会给圈选 SQL 加分区条件，后端会报「未指定分区查询条件」。
- 后端拒绝重复的标签名：同一个 `label_name` 只能带一个 `label_id`（例如 TABLE 与 FIELD 两份同名标签不能一起传），否则报「存在重复的标签名称」。`--output-label` 的 entity type 默认 `TABLE`。
- `--label-date` 决定后端生成的分群名；同一策略上重复使用同一个日期会报「分群名称已存在」，换一个未用过的日期即可。
- 圈选接口成功时不返回 process id，CLI 会在提交前后比对圈选任务列表把它找回来，并用 `process_id_resolution` 说明结果：`resolved` 时 `process_id` 可用；`ambiguous` 表示同时出现多个新任务，候选 id 在 `candidate_process_ids`；`not_found` 表示新任务还没出现在列表里；`unavailable` 表示列表读不到。**这四种都不代表提交失败**，`submitted` 才是提交结果，未取到 id 时用 `process list --policy-id <id>` 继续跟进。
- 不知道 policy id 时先用 `policy list` 找。后端**要求且只接受一个** `--status`（策略生命周期状态，默认 `online`，与返回行里的 `AVAILABLE` 等状态不是同一个字段），不传会匹配不到任何数据。真正生效的过滤只有 `--usage-type`、`--policy-type`、`--policy-id`；后端没有按名称或 owner 搜索的能力，CLI 因此不提供 `--name` / `--keyword` / `--owner`，不要编造这些参数（传了会直接报未知参数错误）。需要按名称找策略时，先按 `--usage-type` / `--policy-type` 缩小范围再在结果里筛。
- `policy list` 每行默认只给 `basic_info` 且不含 `label_condition`；需要规则树、执行配置或豁免配置时加 `--full`。行的结构与 `policy get` 一致，可以同样方式读取。
- 要拼 `--label-condition` 却不知道 `label_id` / `label_name` / `operator` 怎么写时，用 `condition-group get --id <id>`：它会逐条列出可直接抄进 `sub_logics` 的 `label_id`、`label_name`、`entity_type`、`operator` 与 `values`。某个标签有哪些合法取值则用 `enum-group get --id <id>` 查。
- 注意 GPCP 另有一个前端应用也叫 `privacy-policy-center`（`/privacy-policy` 隐私政策导航），与这里的 `bytedcli gpcp privacy-policy-center`（策略中心 `/strategy-center`）不是一回事。
- `policy get` 返回哪些段落由 `basic_info.policy_type` 决定，**与 MOCK / ONLINE 无关**，且 `execution_config` 与 `basic_info.policy_segment_info` 各自独立、有其一不代表有另一个：`REGULAR_POLICY` 两者都有，`ADHOC_POLICY` 只有 `execution_config`，`BASE_POLICY` 只有分群信息，`EXEMPTION_POLICY` 两者都为 null、改带 `business_info.exemption_config` 与 `extra_info.exempt_meta`。即便同为 `REGULAR_POLICY`，`execution_basic` 也可能只填两个字段、也可能是完整的周调度配置。不要假设某个段落一定存在。
- `policy get` 的文本输出把 `label_condition` 渲染成可读规则，`--json` 保留原始规则树。`policy get` 与 `process get` 传入不存在的 id 时都报 `PRIVACY_POLICY_CENTER_NOT_FOUND`，错误消息里会写明是策略还是圈选任务。
- `policy get` 只返回策略本身，不含圈选任务；圈选任务要走 `process list` / `process get`。
- `process list` 每行默认省略各阶段的 dorado 任务明细（单行约 2 KB），需要时加 `--stages`；`process get` 默认省略内嵌的策略快照，需要时加 `--policy-info`。
- 时间字段在不同接口形态不同：策略是秒级时间戳，圈选任务详情是毫秒级时间戳，圈选任务列表是 ISO 字符串。文本模式下秒级和毫秒级都会转成本地可读时间，ISO 字符串按后端原样展示；`--json` 一律保留原值。

### cmpflow Ticket Center

```bash
# 查看某二级项目的工单状态统计 / 完成率（只读）
bytedcli --json gpcp cmpflow ticket stats --secondary-project-id 123456

# 列出工单（默认 page=1 / page-size=20）
bytedcli gpcp cmpflow ticket list --secondary-project-id 123456

# 只看逾期工单；多状态用逗号拼接；翻页用 --page
bytedcli --json gpcp cmpflow ticket list --secondary-project-id 123456 --status Overdue
bytedcli --json gpcp cmpflow ticket list --secondary-project-id 123456 --status Ongoing,Overdue --page 1 --page-size 20

# 需要工单类型相关明细时，加 --extra-info 原样带出 extra_info（大字段，默认关闭）
bytedcli --json gpcp cmpflow ticket list --secondary-project-id 123456 --status Overdue --page-size 5 --extra-info
```

### cmpflow 工单流程配置（workflow-config）与自定义角色（role）

```bash
# 读取某二级项目完整工单流程配置（只读）：状态机 + 节点表单 + 通知 + 角色
bytedcli --json gpcp cmpflow workflow-config get --secondary-project-id 123456

# 导出为可迁移的 JSON bundle
bytedcli gpcp cmpflow workflow-config export --secondary-project-id 123456 -o /tmp/sample-wf.json

# 把线上 ROW(sg) 项目的流程复制到 BOE 项目：先 dry-run 预览两个写请求，再加 --yes
bytedcli --json gpcp cmpflow workflow-config import \
  --source-secondary-project-id 123456 --source-region sg \
  --target-secondary-project-id 654321 --target-region boe
bytedcli gpcp cmpflow workflow-config import \
  --source-secondary-project-id 123456 --target-region boe --target-secondary-project-id 654321 --yes

# 也可以从导出文件导入；--sections 控制范围（默认 graph,nodes；notification 需显式带上）
bytedcli --json gpcp cmpflow workflow-config import --from /tmp/sample-wf.json \
  --target-region boe --target-secondary-project-id 654321 --sections graph,nodes

# 自定义角色是与流程相互独立的能力：先在目标项目建/改角色（同样默认 dry-run）
bytedcli gpcp cmpflow role create --region boe --secondary-project-id 654321 \
  --role-key sample_bp --role-name 'Sample BP' --rotate-users sample.user --rotate-days 7
bytedcli gpcp cmpflow role update --region boe --secondary-project-id 654321 \
  --role-key sample_bp --rotate-users a.example,b.example --yes
```

## Agent Guidance

### MSC

- **写入边界**：除 `tpsdk-governance register` 的受限 `api_id` 注册外，MSC 只提供查询。SDKAPIV3 add/update/delete、治理 update/delete、cache 写入和注册接口的 `api_info` 分支均未暴露；不要改用原始 HTTP、脚本或其他入口绕过该边界。
- **资源映射**：三方 SDK API 主数据用 `sdk-api list`；单 API 全版本快照用 `sdk-api-version get`；SDK 三元组 catalog 用 `sdk list`。
- **模板规则关系**：MSC 数据关系是 `App -> Template -> TemplateSnapshot -> RuleSnapshot -> Rule`。`template list` 返回模板基本信息和当前线上 `current_template_snapshot_id`；`template-snapshot list` 返回一个模板的全部版本；`template-rule list/search` 返回实际挂在模板版本中的规则快照。
- **模板规则查询分流**：`template-rule list` 对应普通查询，可传 `--template-id`、优先级更高的 `--template-snapshot-id`，或成对的 `--bits-app-id + --alias`；`template-rule search` 对应管理页面筛选接口，支持 rule/type/tag/level/platform、排序和分页，不支持组合模板，组合模板改用 `template-rule list`。
- **合码 MR 卡口模板**：将 `base_info.aliases[]` 中任一 Alias 含 `bitscd` 的模板识别为合码 MR 卡口规则集；分析时先取 `current_template_snapshot_id`，再检查该线上模板版本中的规则。命中规则定义的 API 调用会阻断合码，不要把这类模板当作普通审计规则集。
- **合码卡口检测体系**：按 `snapshot_info.tags[].tag_value` 区分两套 API 检测：`BPEA_CI` / `BPEA_CD` 属于 BPEA/DFID API 检测，`CI` / `CD` 属于传统 API 检测。判断 API 是否被卡口覆盖时，同时检查当前模板版本的 tag 与规则内容（`clause` / `v3_apis` / `apis`）；不要仅凭规则名或方法名判断检测体系。
- **规则反查与历史**：`rule list --app-id` 查询该 App 所有模板的当前线上规则，也可用 `--rule-type-id` 或 `--rule-snapshot-ids`；`template-by-rule list --rule-id` 反查规则出现过的模板版本；`rule-version list --rule-id --template-id` 返回规则在指定模板中的历史快照。历史接口虽然使用 POST，但属于只读查询，不需要 `--dry-run`/`--yes`。
- **模板规则原始字段**：模板、快照、规则、规则类型及嵌套关系保留 MSC snake_case 字段和未知扩展字段；CLI 只把分页外层统一为 `{items,page,page_size,total}`，不重写状态、规则内容或关联数据。
- **symbol component 查询**：`symbol-component search` 按 `--bits-app-id + --class-name` 在多个应用版本中做服务端 class-name 搜索，返回组件、owner、value chain 和 POC；平台由 BITS 应用决定，没有独立 `--platform` 参数。
- **SDK API 全量与筛选互斥**：`--fetch-all true` 不得同时传 API id、SDK、CA path、keyword 或 datatype 等筛选；需要筛选时省略该参数或显式传 false。
- **DS TPSDK 查询**：`tpsdk-task get`、`tpsdk-report get`、`tpsdk-governance list`、`tpsdk-component-cache list`、`tpsdk-api-label-cache list`。
- **应用与 BPEA DFID 查询**：先用 `app list --name <中文或英文名>` 找 `bits_appid`；它就是 `bpea-dfid*` 命令要求的 `--msc-app-id`。
- **deployment 与应用 region 不同**：`app list` 默认访问 CN deployment；`app list --region oversea` 只是筛选 CN project service 中的海外应用分区。返回条目中的 `region=oversea` 不等于切换到 ROW host；后续 BPEA 命令会按自己的 ROW 默认访问海外 BPEA 服务。
- **DFID 类型**：`--dataflow-type` 必须是 `1=OS API`、`2=3rd SDK`、`3=network`、`4=app2app`、`5=webview`。`bpea-dfid list` 返回服务端已经按 `dataflow_id` 聚合去重的结果，不要再做客户端去重。
- **原生筛选**：DFID 与 form list 支持 `--page/--page-size/--keyword/--status/--owner-email/--start-time/--end-time/--platform/--create-way`；form 另支持 OS datatype、SDK 名、父 SDK、JSB 和 scene tag 筛选。
- **Schema 保持原样**：`bpea-dfid-schema get` 批量返回 `schema_data` 字符串；不要在 CLI/agent 内假定它一定是合法 JSON，也不要自动解析或编排。
- **BPEA 工单详情**：`bpea-order get --order-id <id>` 直接返回服务端 `order + issues`。`status`、`order_type`、`operation`、`audit_type` 等数值 code 不在 CLI/agent 内改写；工单页面 URL 中的 `projectId` 和 `mscId` 是前端上下文，不是该接口参数。
- **report scope 严格互斥**：`offline_analysis` 只传 `--task-id`；`version_facts` 只传 `--bits-app-id + --app-version`。
- **筛选布尔值显式写 `true|false`**，例如 `--orphan false`、`--sensitive true`，避免“未传”和 false 混淆。
- **治理查询**：`tpsdk-governance list` 要求 `--bits-app-id`，可用 `--orphan true` 查询缺失 SDK API 主数据的治理行。
- **治理注册默认不写**：`tpsdk-governance register` 要求 `--bits-app-id + --platform + --api-ids`，省略 `--yes` 时就是 dry-run；可显式传 `--dry-run`。不要同时传 `--dry-run --yes`。
- **治理注册只接受已有 API**：一次只能传 1-100 个不重复的正 int32 `api_id`。CLI 会批量查询 SDKAPIV3，要求全部存在且平台与 `--platform` 一致，然后才允许 `--yes` 写入；请求中只会发送 `api_id`，不会创建或更新 SDKAPIV3 API。
- **治理注册权限与结果**：服务端要求目标 `bits_app_id` 的 write 或 sci_admin 权限。注册只新增治理行，不回写历史报告；治理完成状态使用服务端初始值。返回 item 级失败时 CLI 抛出 `MSC_PARTIAL_FAILURE` 并保留完整结果，因为同批其他 item 可能已经成功，随后用 `tpsdk-governance list` 核对实际状态。
- **cache 是全局数据**：component classification 与 API label cache 跨 app/version 共享；当前只提供 list 查询。
- **认证/deployment**：MSC 使用独立的 `--deployment cn|row` 与 `BYTEDCLI_GPCP_MSC_DEPLOYMENT`，不复用 SDP 的 `--region sg|va`。默认值按资源确定：app、规则模板、`3rdsdkapi`、`ds-tpsdk` 为 `cn`，symbol-component search 与 BPEA micro 为 `row`；显式参数优先于环境变量，环境变量优先于资源默认值。`cn` 使用个人 CN Cloud JWT，`row` 使用个人 `i18n-tt` Cloud JWT。
- **BPEA 认证**：`bpea-dfid*` 和 `bpea-order` 最终请求 ROW MSC business origin；GPCP 主应用只提供认证插件。首次使用或 Web session 过期时，先运行 `bytedcli --site i18n-tt auth login --session --auto`；CLI 会在内存中完成 GPCP OAuth 换票并携带短期平台 token、用户 token 和用户名，不跨域发送 Cookie，也不记录或输出 token。
- **BPEA 部署差异**：BPEA 目前只有 I18N production，四个资源命令默认 ROW 且不自动跨区回退。显式传 `--deployment cn` 会命中没有 production upstream 的 CN 网关并返回 TLB 502，只用于诊断。
- **当前部署目标**：app、规则模板、`3rdsdkapi` 和 `ds-tpsdk` 默认 CN；`symbol-component`、`bpea-dfid`、`bpea-dfid-form`、`bpea-dfid-schema`、`bpea-order` 默认 ROW。symbol-component 使用普通 ROW Cloud JWT，不需要 BPEA Web session；CN 同路径当前返回 TLB 502。通常不要传 `--deployment`，除非明确需要覆盖资源默认值。
- **业务 API 不走 GPCP shell host**：MSC 页面挂在 GPCP 下，但 CLI 会按 deployment 选择独立 MSC API origin；不要把 `/api/rule`、`/api/sca` 或 `/api/bpea` 拼到 GPCP 页面 host。

### Aegis

- **Aegis 当前严格只读**：仅实现 `issue list` / `issue get`。没有 recheck、
  false-positive、exemption、close、status update 等写命令；不要自行拼
  `POST` 请求。recheck 前端 payload/校验契约未稳定确认。
- **Aegis 列表过滤**：支持 `--page` / `--page-size` / `--pipeline-page`、
  `--space-id`、`--project-id`、`--scene-id`、`--life-cycle-id`、`--repo-name`、
  `--commit-hash`、`--logical-status`、`--matched-rule`、`--location`、
  `--scan-type`、`--scene-period`、`--context-type`、`--status`。其中
  `--pipeline-page` 转为 `pipeline_page` 并默认发送正整数 `1`，与前端请求
  契约一致；`--scan-type` 转为前端契约的复数 query key `scan_types`；其余
  普通筛选按平台 query 透传，不做客户端模糊匹配。
- **Aegis 状态必须传数字 code**：`--status` 仅允许 `0=Open`、
  `1=HangUp/Processing`、`2=Closed`；`--logical-status` 仅允许
  `1=NeedToFix`、`2=FalsePositive`、`3=Exempt`、`4=Fixed`、
  `5=FPUNconfirmed`、`7=RiskConfirmed`、`10=ExemptRisk`、
  `11=PendingApproval`、`12=Skipped`、`13=Discarded`。CLI 和 API 层都会
  拒绝 `pending` / `open` 等自由文本，避免静默返回空结果。
- **Aegis 输出**：list 的文本模式至少展示完整 ticket id、logical/status、
  matched rule、location 与 repo；JSON 保留平台新增字段。get 返回单 ticket
  的完整 loose object。
- **Aegis 鉴权刷新**：若 Aegis 返回 HTTP/business-code 401，CLI 只强刷一次
  GPCP user-info credential 并重试一次；第二次失败直接返回，不循环。403 不
  当作 stale session 刷新。

### cmpflow

- **ticket 读命令严格只读**：`ticket list` / `ticket stats` 对应前端 `/cogos-api/tickets` 与 `/cogos-api/tickets/statistics`。工单维度没有催办（urge）、改负责人、流转节点等写命令；不要自行拼 `POST` 或 `can_urge`。
- **流程配置写入口**：唯一的写面是 `workflow-config import`（复制流程）与 `role create|update`（维护自定义角色），二者**默认 dry-run，必须显式 `--yes` 才写**；不要同时传 `--dry-run --yes`。`workflow-config get/export` 仍是只读。
- **两条独立写流程**：注册状态机（`POST /workflow/templates`）不依赖角色；只有保存节点表单（`POST .../conf`）时，若某节点 `operate_role=customized_role`，其真实 `role_key`（在 `form_data.nodeInfos.operate_role` 里）必须已存在于目标项目。import **不会自动建角色**：预检发现缺角色会以 `CMPFLOW_WORKFLOW_ROLE_MISSING` 中止且零写入，需先用独立的 `role create` 建好再重跑。
- **GET→POST 序列化差异由 CLI 归一化**：`timeout/sort/primary_node_sort` GET 是字符串、POST 必须是 int；自定义角色节点 POST 必须发真实 role_key 而不是占位符 `customized_role`；节点对象只回传白名单字段（name/name_en/timeout/operate_role/sort/form_data/form_data_en/primary_node_sort），GET 多出的 operators/description 等字段不回传。
- **import 范围**：默认 `--sections graph,nodes`（先注册状态机，再写节点表单）；`notification` 需显式加入才会用**源**通知配置覆盖。注意 `POST .../conf` 是整段替换（节点+通知一起），因此默认导入会把**目标当前**的 `notification_configuration` 原样回传，保证不会清空目标已有通知；只有加了 `notification` 段才按源覆盖。不提供、也不接受同步 `duty_operators`、`customized_roles`、项目元信息（这些走 `role` 命令或平台 UI）。源只能是 ROW 在线项目（`--source-region sg|va`）或 `--from` 导出文件；目标写操作仅支持 `--target-region sg|boe`（va 未验证同域写会话，不支持写）。
- **导出 bundle 格式**：`workflow-config export` 产出 `{bytedcli:"gpcp-cmpflow-workflow-config", schema_version, source, exported_at, conf}`，import 只接受该结构；`conf` 为 GET 原样快照，归一化只发生在导入时。
- **鉴权**：sg/va 走 ROW GPCP 平台 Web session（内存中完成 OAuth 换票，携带短期 rpc token，不记录 token）；`boe` 走 gpcp-boe + test-sso 会话，先用 `bytedcli --site boe auth login --session --auto` 登录。所有 cogos 请求额外带 `x-tenant-token: pns` 与 `rpc-persist-gpcp-*` 头；会话过期报 `CMPFLOW_AUTH_REQUIRED`，按对应 hint 登录后重试。
- **区域（workflow-config / role）**：读取支持 `--region sg|va|boe`；**写操作（`workflow-config import`、`role create|update`）只支持 `sg|boe`**，传 `va` 会在写前显式报 `CMPFLOW_WORKFLOW_INPUT_ERROR`，不回退默认值。boe host 为 `gpcp-boe.bytedance.net`；SDP/WebShell 仍只有 sg/va。
- **分页用 `--page`/`--page-size`**（默认 page=1 / page-size=20）：CLI 内部映射为后端的 `limit`+`offset` 线参，外部只暴露 page/page-size。JSON 返回 `total/page/page_size/has_more`；文本模式用标准分页表展示。
- **状态过滤**：`--status` 接受逗号拼接的多值，合法值为 `Ongoing|Done|Overdue|Abandoned|Pending|Unactivated|Queued`；非法值在发请求前就报 `CMPFLOW_INPUT_ERROR` 并列出全部合法值。不传则返回全部状态。
- **stats 口径**：`ticket stats` 返回 `secondary_project_id/total/ongoing/overdue/done/pending/unactivated/abandoned` 与 `done_rate`。`done_rate` 已是百分数字符串（如 `"28.2"`），文本模式直接拼 `%`，不要再乘 100。
- **列表输出**：JSON 把工单通用字段规范化为 camelCase（id/owner/opsOwner/curNode/curNodeId/ticketStatus 等），并带上 `secondary_project_id` 与分页字段。`extra_info` 是**每个工单类型各自定义**的大字段（不同 secondary project 结构完全不同，可能是顶层 `db_name/table_name/columns`，也可能是 `psms/field_msg` 等），CLI **不做固定解析**：默认不输出；需要时加 `--extra-info`，CLI 会 best-effort JSON 解析后**原样透传**（解析失败则保留原始字符串），由调用方按工单类型自行解读。文本模式用分页表展示 id / status / priority / owner / 当前节点 / 工单名。
- **鉴权**：cmpflow 与 BPEA 一样走 ROW GPCP 平台 Web session（内存中完成 OAuth 换票，携带短期平台 token、用户 token 与用户名，不跨域发 Cookie、不记录 token）。会话过期报 `CMPFLOW_AUTH_REQUIRED`，按 hint 运行 `bytedcli --site i18n-tt auth login --session --auto` 后重试。
- **区域（ticket）**：只读 ticket 仅支持 `--region sg|va`（默认 sg，`gpcp.tiktok-row.net`）；显式传 `boe` 会报 `CMPFLOW_INPUT_ERROR`（boe 无线上票据数据，绝不静默回退 sg）。`va` 路由可能被 ROW OG 准入网关拦截，当前以 sg 为主路径。
- **暂未暴露的筛选**：owner / ops_owner / 当前节点（workflow node）/ biz_line / org_domain / department / priority / keyword 等下拉过滤的真实 query 参数名尚未抓包确认，当前版本不透传；`tickets/options`、`primary_projects` 与单条工单详情也未接入。
- 示例中的项目 id、姓名、PSM、库表名、节点名均为 `demo-*` / `sample-*` / 占位数字，请勿在对外文案中使用真实业务标识符。

### SDP

- **两步流程**：先 `gpcp sdp job create` 拿 `jobId`，再 `gpcp sdp command execute --job-id <jobId>`。
- **支持的 target（`--target`）**：`cloudide`（默认）、`tce`、`bernard`、`merlin`、`yarn`。每种的必填入参不同：
  - cloudide → `--workspace-id`
  - tce / bernard → `--pod-name`（`--tce-container-type` 默认 primary；选 sidecar 时 `--container-name` 必填；bernard 走 targetType `T_BERNARD`）
  - merlin → `--merlin-id`（`--merlin-type` 默认 trial；trial 时 `--user` 必须是 tiger）
  - yarn → `--ip` + `--app-id`（`--yarn-container-id` 选填）
  - 未覆盖：machine / k8s / tlb / cronjob / faas（需 Host IP 或额外基建，未实现）。
- **`--user` 必填**（不默认 root）：root / tiger；cloudide 另有 byteide；merlin trial 只能 tiger。执行用户权限差异大，需显式指定。
- **`source` 字段**：CLI 恒发 `"bytedcli"`（纯来源标注，非 target 选择、服务端不校验），SDP 列表里显示成 "bytedcli 创建"，便于区分 CLI 建的 job。
- **区域**：`--region sg`（默认，`gpcp.tiktok-row.net`，BDEE 主路）或 `--region va`（`gpcp-us.tiktok-row.net`）。也可用 `BYTEDCLI_GPCP_REGION` 环境变量。
- **CloudIDE 交接**：SDP 与 CloudIDE 只交换稳定的生产资源引用——生产 CloudIDE **workspace id**。不要在两个平台间传 `x-cloudide-token` 或 SDP WebShell token。
- **指令白名单由平台服务端强制**。被拒指令会如实上报，**不会**被 CLI 改写或拆解；不要尝试绕过白名单，也不要追加 `printf` / 变量赋值 / marker 等隐藏指令。执行前可用 `gpcp sdp whitelist list [--keyword]` 查清单（约 317 条）——`--keyword` 是**服务端子串匹配**，CLI 只做透传不加额外判定（如 `--keyword vim` 命中 `/usr/bin/vim`）。白名单走 open-api（`X-Jwt-Token` ByteCloud JWT 鉴权），与执行的 WebShell 同一份 JWT。白名单是合规允许清单，不等于"非交互安全命令"，服务端在执行时才是权威。
- **只支持非交互式指令**：`vim` / `tmux` / `mysql` 等交互式命令不受支持；优先 `tail -n N`、`ls`、`ps aux` 等有界只读命令。`tail -f` 会一直挂住，别用。
- **只能单条命令,不支持复合命令**：`;`、`&&`、`||`、后台 `&` SDP **都不支持**（实测会一直等不到完成、直到超时）；**管道 `|` 支持**。复合逻辑请拆成多次 `command execute`。CLI 已在客户端前置拦截这些运算符并快速报 `SDP_INPUT_ERROR`（而不是白等超时）；前置拦截只做轻量词法分析（会跳过引号内与转义的运算符，如 `find … -exec … \;`、`awk -F';'` 不会误拦），服务端才是权威。
- **重定向**（`>` / `>>`）不保证在白名单内，用前先 `whitelist list` 确认。
- **`exitCode` 恒为 `null`**：SDP 协议返回的 `code` 是 handler 状态，不是 shell 退出码。用 `completed` 判断指令是否正常结束；用 `output` 读结果。
- **输出**：默认剥离 ANSI 并按字节上限截断（`truncated` 标记），可用 `--no-strip-ansi` 保留、`--max-output-bytes` 调整上限、`--timeout-ms` 调整完成超时。
- **合规**：SDP 面向合规运维；日志读取需目标 OS 用户对文件有读权限。不要在默认输出里暴露敏感路径 / 凭据。
- **未覆盖能力**：文件上传下载、脚本下发、ATOP、GDB 目前未在 CLI 中实现（GDB 应走更强确认，不进默认诊断循环）。
- 示例中的 `example/repository`、`demo-*`、`ws-example`、`123456`、
  `/path/to/log` 均为占位值。
