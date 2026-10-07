# BITS 发布单 TCC 导入

执行 `bits release tcc-config import`、`bits release pipeline sync-tcc` 或包含 TCC 项目的
`bits release pipeline run` 前读取本文档。导入命令只把线上 TCC source config 或指定 PPE
环境的内容导入已有发布单，不会自动物化 TCC 版本或运行发布流水线。

## 选择与确认

- 发布单使用 `workflowType=1`；研发任务的 `bits develop import-tcc-configs` 使用 `workflowType=2`。
- `--control-planes` 必须显式传一个或多个语义值：`cn`、`i18n`、`eu-ttp`、`us-ttp`、`i18n-bd`。
- 这些值始终表示 TCC source control plane。Release change-item list 的内部 slice 编号与 TCC 在 EU/US 不同；CLI 会自动将 `eu-ttp` 的 source ID 3 映射到 Release slice 4、将 `us-ttp` 的 source ID 4 映射到 Release slice 5，调用方不要手工替换语义值。
- 使用 `--config-names` 批量筛选，或使用 `--config-name + --region + --dir` 选择一个精确坐标；两种模式不能混用。
- 必须且只能选择一种确认模式：`--dry-run` 或 `--yes`。
- 不带 `--env` 的精确 live 导入必须复用 dry-run 返回的 `selected_configs[].source_config_id`，防止同名配置或页面状态漂移导致误导入。
- 带 `--env` 的 PPE 导入会自行唯一映射线上 source config，不能传 `--source-config-id`。
- 所有 release live 导入都必须回传最新 dry-run 的 `plan_sha256`；这不是 PPE 专属门禁。

## Agent 写操作授权

- Agent 必须先运行与拟执行写操作参数一致的 dry-run，向用户展示目标发布单、PSM、环境、control plane、配置列表及计划摘要，然后等待用户明确授权。
- Agent 自己读取或检查 dry-run 结果不构成用户授权；用户此前要求“看看”“测试一下”或批准其他步骤，也不能推定为当前写操作授权。
- live `tcc-config import`、`pipeline sync-tcc` 和 `pipeline run` 是三个独立写操作。每一步都要先展示该步 dry-run 计划并分别等待用户明确授权，不能因前一步已授权而连续执行后续步骤。
- 收到授权后，只能执行刚展示的计划。参数或服务端计划发生变化时，必须重新 dry-run 并再次请求授权。

## 导入线上 Source Config

先用全局 JSON 模式 dry-run，并检查 `selected_configs[].region`、`dir`、`source_config_id`、
`import_version` 和 `plan_sha256`：

```bash
bytedcli --json bits release tcc-config import \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-planes cn \
  --config-name demo_config \
  --region CN \
  --dir /default \
  --dry-run
```

精确 live 导入时，复用 dry-run 返回的 `source_config_id` 与 `plan_sha256` 并显式确认：

```bash
import_plan_sha256='paste-the-latest-64-character-plan-sha256-here'
bytedcli bits release tcc-config import \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-planes cn \
  --config-name demo_config \
  --region CN \
  --dir /default \
  --source-config-id 2000000000001 \
  --expected-plan-sha256 "$import_plan_sha256" \
  --yes
```

默认导入线上 source config 的元数据和版本基线。source config 存在未发布最新版本时，
`import_version` 使用 `latestVersion`；否则使用当前 `version`。计划 hash 覆盖 workflow、PSM、
control plane、storage version、全部所选 source config 身份/坐标/版本和最终导入 payload；任一项
漂移都会在导入 POST 前失败。

live 普通导入只有在 mutation 明确成功且最新 change items 与持久化 Draft 都逐项回读匹配后，才返回 `readback_verified=true`。回读失败会报告 partial success，表示导入可能已经生效，必须先检查发布单而不是直接重试。

批量导入也必须先 dry-run，并逐项检查返回的配置坐标和版本：

```bash
bytedcli --json bits release tcc-config import \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-planes cn \
  --config-names demo_config,sample_rules \
  --dry-run
```

## 从 PPE 环境导入

指定 `--env ppe_*` 时，命令读取该 PPE 环境的最新配置内容，按 `config name + region + dir + control plane` 唯一映射线上 source config，先导入线上基线，再把 PPE 内容覆盖到 Bits Draft，并通过 SHA-256 回读确认。PPE config ID 不会被当作 `sourceConfigId`。

PPE 模式只允许一个 control plane。先 dry-run 检查 `selected_configs[]` 中的 `source_config_id`、`env_version` 和 `env_content_sha256`，并记录返回的 `plan_sha256`：

```bash
bytedcli --json bits release tcc-config import \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-planes cn \
  --env ppe_demo \
  --config-name demo_config \
  --region CN \
  --dir /default \
  --dry-run
```

向用户展示计划并取得明确授权后，使用同一份 dry-run 返回的 `plan_sha256` 执行 live 导入；PPE 模式不传 `--source-config-id`：

```bash
ppe_plan_sha256='paste-the-latest-64-character-plan-sha256-here'
bytedcli bits release tcc-config import \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-planes cn \
  --env ppe_demo \
  --config-name demo_config \
  --region CN \
  --dir /default \
  --expected-plan-sha256 "$ppe_plan_sha256" \
  --yes
```

live 命令会重新读取 PPE、线上 source config 和发布单状态并计算计划。PPE 来源的版本、内容、坐标、导入身份、将要覆盖的 Draft 元数据或 storage version 发生漂移时，会在首次 Bits 写入前以 `BITS_TCC_PPE_PLAN_CONFLICT` 失败；此时必须重新 dry-run、展示新计划并重新取得授权。`plan_sha256` 不锁定 Bits Draft 中未从 PPE 复制的现有字段；baseline 导入后会先预检整批 Draft 的 identity、内容版本和加密状态，全部通过后才执行 Draft PUT，并拒绝用 PPE 明文覆盖已启用加密的 Draft，成功写入后再执行完整回读验证。

成功结果的 `selected_configs[]` 会包含 Draft ID、是否应用更新以及验证后的 SHA-256，不包含配置正文。以下情况会在写入前整体失败：

- 加密配置或不可读内容
- `data_type` 不是 `json`、`yaml` 或 `string`
- 单配置超过 4 MiB
- 累计内容超过 16 MiB
- 一次选择超过 20 个配置
- PPE 配置无法唯一映射线上 source config

如果线上基线已经导入，但 Draft 更新或回读失败，命令会报告 partial success。此时先检查发布单实际状态，不要盲目重试。

## 后续发布

导入命令不会执行 `sync-tcc`、物化 TCC 版本或启动流水线。确认 Draft 后，显式使用现有命令完成后续步骤：

```bash
bytedcli bits release pipeline sync-tcc --help
bytedcli bits release pipeline run --help
```

根据发布单 stage、control plane 和期望配置填写这两个命令要求的参数。Agent 必须分别执行 dry-run、向用户展示计划并等待明确授权，才能执行对应 live 命令；导入授权不自动授权物化或启动流水线。

`pipeline sync-tcc` 的 `--expected-config-ids` 指 source Draft config ID（即 dry-run `source_snapshots[].configs[].draft_config_id`）。物化后的 artifact config ID 由 BITS 在 sync 写入时才分配，首次 sync 前不可知，且一个 Draft 可能物化出多个区域的 artifact，因此 `--expected-config-count` 统计的是物化后的 config 数量，可以大于 Draft ID 数量。当期望物化多个 config/target 时，还必须为每个结果重复传入完整 tuple（同一 Draft 的多个 target 复用同一个 config-id），例如：

```bash
bytedcli --json bits release pipeline sync-tcc \
  --ticket-id 1000000000001 \
  --stage-id 1000000000002 \
  --control-plane us-ttp \
  --use-change-items \
  --env-json 'null' \
  --expected-config-count 2 \
  --expected-config-ids 1700000000001 \
  --expected-config-names demo_service_account_token \
  --expected-regions US-TTP,US-TTP2 \
  --expected-dirs /default \
  --expected-config-target 'project-type=12,project-id=example.service.api,config-id=1700000000001,config-name=demo_service_account_token,region=US-TTP,dir=/default' \
  --expected-config-target 'project-type=12,project-id=example.service.api,config-id=1700000000001,config-name=demo_service_account_token,region=US-TTP2,dir=/default' \
  --dry-run
```

示例值均为占位数据；实际执行时替换成当前发布单回读值。tuple 的数量必须等于 `--expected-config-count`。多项目 sync 的每个 tuple 都必须携带 `project-type + project-id`；单项目调用可省略这两个字段。dry-run 会先按项目核对所有 source Draft config name、Draft config ID 与 tuple allowlist，出现额外或缺失 Draft 时不会生成可执行计划。返回的 `plan_sha256` 覆盖 ticket、stage、control plane、env、完整项目身份、当前物化状态、每个 Draft 的 ID/version/source/baseline/content SHA-256、deploy-target snapshot 及全部期望 tuple。推荐用 `--use-change-items` 重新读取当前项目；live sync 必须把最新 dry-run 的 hash 作为 `--expected-plan-sha256` 回传，任一受保护字段变化都会在 mutation 前失败。live sync 的成功响应会按 project/config name/region/dir tuple（不含 config ID）校验关联，避免只比较各字段集合时漏掉项目或目标交换；单目标调用可省略 tuple 参数，由四个单值 allowlist 自动组成 tuple。

未物化 dry-run 的 `config_names_verified=false` 表示预览尚未产生 materialized artifact；source Draft 名称与 Draft config ID 已在写前核对，不能把该字段解释成 source 名称未验证。live 结果仍为 `false` 时，说明最新 materialized change-item 回读没有返回 `confName` / `configName`；此时 CLI 已验证物化数量、region/dir 与 project 级 tuple 关联，但不能证明 artifact 中的 config name，必须把这项限制保留在验收结论中。

live sync 收到明确成功响应后，会重新读取最新 change items，并以持久化结果校验 artifact、metadata
和 tuple。回读失败或不一致会报告 `BITS_RELEASE_TCC_SYNC_PARTIAL_SUCCESS`；网络错误、HTTP
408/5xx 或无法分类的成功响应会报告 outcome unknown。这两类结果都表示写入可能已经生效，必须
先查询现状，禁止直接重跑 sync。

服务端没有为 sync source snapshot 提供原子 CAS。实际物化写入的 dry-run 与 live 结果会明确返回
`source_snapshot_atomic=false`，该值也进入 `plan_sha256`；live 会在提交前立即重新读取一次 Draft、
版本和 deploy target snapshot 以缩小竞态窗口，但不能消除请求提交瞬间的 TOCTOU 风险。只有
`sync_dispatched=true` 且 mutation 后的 `readback_verified=true` 才能确认本次写入已被独立回读。

CLI 已自动完成持久化回读；为了外部审计或处理 partial/outcome-unknown，也可以再次执行完整 JSON 查询：

```bash
bytedcli --json bits release pipeline change-items \
  --ticket-id 1000000000001 \
  --stage-id 1000000000002 \
  --control-plane us-ttp
```

在 `pipelineChangeItems[].changeItemContent` 中找到相同 project/control-plane，逐项核对 materialized `configId + region + dir` tuple；响应提供 `confName` / `configName` 时还要核对名称。不要用默认 text 输出做此验收，因为摘要可能截断原始对象。

启动 TCC pipeline 时必须只消费已独立回读确认的 materialized artifact，禁止让 `pipeline run` 隐式再次 sync：

```bash
bytedcli --json bits release pipeline run \
  --ticket-id 1000000000001 \
  --stage-id 1000000000002 \
  --control-plane us-ttp \
  --username demo.user \
  --use-change-items \
  --require-materialized-tcc \
  --expected-project-count 1 \
  --expected-project-ids example.service.api \
  --expected-project-target 'project-type=12,project-id=example.service.api' \
  --expected-tcc-config-count 2 \
  --expected-tcc-config-ids 2000000000001,2000000000002 \
  --expected-tcc-regions US-TTP,US-TTP2 \
  --expected-tcc-dirs /default \
  --expected-tcc-config-target 'project-type=12,project-id=example.service.api,config-id=2000000000001,region=US-TTP,dir=/default' \
  --expected-tcc-config-target 'project-type=12,project-id=example.service.api,config-id=2000000000002,region=US-TTP2,dir=/default' \
  --env-json 'null' \
  --run-timestamp 1788307200000 \
  --readback-timeout-ms 15000 \
  --dry-run
```

示例值均为占位数据。TCC run 的 dry-run 与 live 都必须使用 `--use-change-items` 获取当前项目，且都不支持 `--no-pre-set`；显式 `--selected-projects-json/file` 只适用于非 TCC run。TCC run 始终拒绝未物化 artifact，不会隐式执行 sync；所有 project/config allowlist 与每个 `configId + region + dir` tuple 都必须完整提供，多项目 run 的每个 config tuple 还必须携带 `project-type + project-id`。只有 dry-run 返回 `tccSyncRequired=false`、`expectationsVerified=true` 和 `planSha256`，并且计划经独立授权后，才可执行 live run。live 必须保留完全相同的参数（包括固定的 `--run-timestamp`），移除 `--dry-run`，并回传 dry-run hash：

```bash
run_plan_sha256='paste-the-latest-64-character-planSha256-here'
bytedcli --json bits release pipeline run \
  --ticket-id 1000000000001 \
  --stage-id 1000000000002 \
  --control-plane us-ttp \
  --username demo.user \
  --use-change-items \
  --require-materialized-tcc \
  --expected-project-count 1 \
  --expected-project-ids example.service.api \
  --expected-project-target 'project-type=12,project-id=example.service.api' \
  --expected-tcc-config-count 2 \
  --expected-tcc-config-ids 2000000000001,2000000000002 \
  --expected-tcc-regions US-TTP,US-TTP2 \
  --expected-tcc-dirs /default \
  --expected-tcc-config-target 'project-type=12,project-id=example.service.api,config-id=2000000000001,region=US-TTP,dir=/default' \
  --expected-tcc-config-target 'project-type=12,project-id=example.service.api,config-id=2000000000002,region=US-TTP2,dir=/default' \
  --env-json 'null' \
  --run-timestamp 1788307200000 \
  --readback-timeout-ms 15000 \
  --expected-plan-sha256 "$run_plan_sha256" \
  --yes
```

`--expected-project-target` 用 `project-type + project-id` 复合身份锁定项目，避免不同类型复用同一 ID
时被误判为同一个项目。`planSha256` 覆盖最终 run payload，以及 `--force`、是否执行 pre-set 两项
执行控制；任一项变化都必须重新 dry-run 和授权。payload 包括项目 artifact/strategy、custom vars、env、
operator、stage/control-plane 和 run timestamp；dry-run 只输出 custom var 的 `value_present` / `value_redacted` 等安全元数据，不回显值，也不提供可复用的逐值指纹。完整值仍进入整体 `planSha256`，因此值变化会触发计划漂移。TCC live run 必须同时携带 `--yes`；不能复用 sync 授权。
`can-run` 在流程起点以及所有预检/即时计划刷新完成后的第一次写入前都必须明确返回 `true`；false、响应缺字段或探测失败都会停止，`--force` 只能在独立
确认 stage 可运行后显式使用。

live run 会先记录 stage pipeline 当前 build，再提交 run，并轮询等待可归因的新 build；默认最多等待
15000 ms，可用正整数 `--readback-timeout-ms` 调整。每个选中的 `project-type + project-id` 都必须出现
对应的新 project build，并且至少一个新 build 的 `pipeline_run_id` / `build_id` 必须与 run 响应中的
相关 ID 匹配。只有返回 `readbackVerified=true` 才表示运行已由独立状态回读确认；live 输出只保留
`preSetApplied`、`runAccepted`、`runCorrelationIds` 和回读白名单，不回显原始 mutation 响应。若 run-key
预留成功后 run 失败，或 run 接受后没有观察到可归因的新 build，命令会报告
`BITS_RELEASE_PIPELINE_RUN_PARTIAL_SUCCESS`，并携带 `pre_set_applied`、三态 `run_outcome`、
`run_accepted`（unknown 时为 null）和 `run_timestamp`；此时先查 pipeline 与审批节点，禁止盲目重跑。
