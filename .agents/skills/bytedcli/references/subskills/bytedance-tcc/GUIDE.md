---
name: bytedance-tcc
description: "Use bytedcli TCC/config center for namespace lookup, environment list/create/delete, config versions/decryption/diffs, config creation/update/deployment, exact multi-region consistency whitelist entries, directories, base-config import, namespace permission applications and metadata."
---

# bytedcli TCC

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

- Namespace/Config 查询
- Namespace 详情查询
- 环境（PPE 泳道）查询、创建与删除
- 配置版本查询与版本间 diff
- 配置创建、更新、发布（通过 `--publish-mode` 控制发布策略）
- 访问控制 PSM 白名单查询、申请、删除与审核
- 多区域一致性白名单查询与精确单配置申请
- 目录查询与基准配置导入

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `tcc namespace`, `tcc config`, `tcc deployment`, `tcc env`, `tcc site`, and `tcc permission`. Old flat names (e.g. `tcc list-sites`, `tcc search-namespace`, `tcc get-config`) still work as hidden aliases.

```bash
bytedcli tcc site list
bytedcli --site cn tcc namespace list --page 1 --size 50
bytedcli --site cn tcc namespace search "keyword" --scope all --page 1 --size 50
bytedcli --site cn tcc namespace get "namespace"
# List caller PSMs that depend on (read) a namespace (BOE example)
bytedcli --site boe tcc namespace psm-dependency list "demo.namespace" --env boe
bytedcli tcc config list "namespace" --region CN --keyword "demo" --dir-path "/default"
bytedcli tcc config list "namespace" --region CN --keyword "queue-id" --search-field value --dir-path "/default"
bytedcli tcc config get "namespace" "config_name" --region CN --dir "/default"
# View decrypted clear value for encrypted configs
bytedcli tcc config get "namespace" "config_name" --region CN --dir "/encrypt" --decrypt
bytedcli tcc config version list "namespace" "config_name" --region CN --dir "/default"
bytedcli tcc config version get "namespace" "config_name" --ver 3 --region CN --dir "/default"
bytedcli tcc config version diff "namespace" "config_name" --from-version 2 --to-version 3 --region CN --dir "/default"
bytedcli --site i18n-bd tcc config dir list "namespace" --env ppe_xxx
bytedcli --site i18n-bd tcc config meta list --env ppe_xxx
bytedcli --site cn tcc config create "namespace" "config_name" --env ppe --region CN --dir "/default" --description "demo config" --data-type yaml --encrypted true --value "a: b"
bytedcli --site cn tcc config update "namespace" "config_name" --env ppe --region CN --encrypted false --value "a: b"
# Only update the explicitly requested region; do not expand same-key sync-group peers
bytedcli --site cn tcc config update "namespace" "config_name" --env ppe --region CN --no-sync-group --value "a: b"
# TCC v2 non-prod requires an OpenAPI service token; validate with mock mode first
export TCC_OPENAPI_TOKEN="service-token"
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe_demo --region CN --dir-path "/default" --dry-run
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe_demo --region CN --dir-path "/default"
# Web V1 only: deploy one region without expanding same-key sync-group peers
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe --region CN --dir-path "/default" --no-sync-group
# Web V1: without --to-version/--from-version each target region (sync group or --region all) deploys
# its own online -> latest versions; with several target regions an explicit version is refused
# unless it matches every region's online_version (--from-version) / latest_version (--to-version)
# Merge several configs of one namespace into a single deployment ticket (comma-separated;
# legacy web namespaces only — TCC v2/AgV2 namespaces reject multiple names)
bytedcli --site cn tcc deployment deploy "namespace" "conf_a,conf_b" --env prod --region all --publish-mode manual
bytedcli --site i18n-bd tcc config import "namespace" --config-ids "123,456" --target-env ppe_xxx
# If --target-env reports NO_ACTIVE_ENV_FOUND, the PPE lane env does not exist yet; create it first
bytedcli --site i18n-bd tcc env create "namespace" --env ppe_xxx --regions "Singapore-Central"
# tcc env delete is destructive; preview first, then confirm with --yes (skips the interactive prompt)
bytedcli --site i18n-bd tcc env delete "namespace" --env ppe_xxx --dry-run
bytedcli --site i18n-bd tcc env delete "namespace" --env ppe_xxx --yes
# On TCC v2 non-prod, manual calls modify_only (modify without publishing)
bytedcli tcc deployment deploy "namespace" "config_name" --env ppe_demo --region CN --dir-path "/default" --publish-mode manual
# Deploy with review support (auto mode, default): auto-publish if no review, otherwise return review info
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env prod --region CN --dir-path "/default" --publish-mode auto
# TCC v2 prod: select one or more PSMs for the small-traffic stage
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env prod --region CN --gray-psm "example.service" --publish-mode manual
# Force auto-publish regardless of review requirement
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env prod --region CN --dir-path "/default" --publish-mode force-auto
# Query publish details by deployment ID or control-panel URL
bytedcli --site cn tcc deployment get "1234567890" --env prod
bytedcli tcc deployment get "https://example.com/tcc/namespace/demo.namespace/publish-details/1234567890??x-resource-account=demo&x-bc-region-id=example" --env prod
# Query only deployment metadata, config_changes, and step data; skip large config diff fetching
bytedcli --site cn tcc deployment get "1234567890" --env prod --no-diff
# Operate deployment or approve/reject current review step
bytedcli tcc deployment operate "1234567890" --operation start --env prod
bytedcli tcc deployment approve "https://example.com/tcc/namespace/demo.namespace/publish-details/1234567890??x-resource-account=demo&x-bc-region-id=example" --env prod
bytedcli tcc deployment reject "1234567890" --env prod
# Access control: add caller PSM authorization for a directory and region
bytedcli --site cn tcc access-control dir info --namespace "demo.namespace" --region CN --dir-path "/default"
# Enable ACL grayscale (observation mode) on a directory — only gray/off allowed, full enforcement (on) is disabled (BOE example)
bytedcli --site boe tcc access-control dir operate --namespace "demo.namespace" --region China-BOE --dir-path "/default" --target-status gray --env boe --dry-run
bytedcli --site boe tcc access-control dir operate --namespace "demo.namespace" --region China-BOE --dir-path "/default" --target-status gray --env boe --yes
bytedcli --site cn tcc access-control rule list --namespace "demo.namespace" --region CN --dir-path "/default" --search-psm "sample.service"
bytedcli --site cn tcc access-control rule create --namespace "demo.namespace" --region CN --dir-path "/default" --psm "sample.service" --operator "demo-user" --dry-run
bytedcli --site cn tcc access-control rule create --namespace "demo.namespace" --region CN --dir-path "/default" --psm "sample.service" --operator "demo-user" --yes
bytedcli --site cn tcc access-control rule approve --rule-id 123456 --operator "demo-reviewer" --yes
# Multi-region consistency whitelist: exact directory/config only. The expected
# regions must match the complete effective policy set before a request can run.
bytedcli --site us-ttp tcc region-consistency whitelist list --namespace "demo.namespace"
bytedcli --site us-ttp tcc region-consistency whitelist create --namespace "demo.namespace" --dir-path "/default" --config-name "demo_config" --reason "Region-specific business config" --expected-regions "US-TTP,US-TTP2" --dry-run
bytedcli --site us-ttp tcc region-consistency whitelist create --namespace "demo.namespace" --dir-path "/default" --config-name "demo_config" --reason "Region-specific business config" --expected-regions "US-TTP,US-TTP2" --yes
# Apply for a TCC namespace permission (files an auth/bpm ticket routed to the namespace owners)
bytedcli --site i18n-tt tcc permission apply "namespace" --access write --reason "Need config access"
# Preview the exact request body without submitting
bytedcli --site i18n-tt tcc permission apply "namespace" --access write --reason "Need config access" --dry-run
# Use an explicit TCC role instead of the --access mapping
bytedcli --site i18n-tt tcc permission apply "namespace" --role tcc.ns_operator --reason "Need config access"
```

## TCC v2 发布（尤其 PPE / non-prod）

CLI 会自动识别 `former_tcc` / `tcc_v2` namespace，调用方不需要手动选择 v1/v2 接口。v2 的发布链路按环境分流：

| 环境                          | `publish-mode`           | 后端链路                                  | 行为                             |
| ----------------------------- | ------------------------ | ----------------------------------------- | -------------------------------- |
| `prod`                        | `manual/auto/force-auto` | `config/upsert_deploy/v2` activity 发布单 | 创建发布单，并按模式决定是否推进 |
| 非 prod（如 `ppe` / `ppe_*`） | `manual`                 | `/api/v2/open/config/modify_only`         | 修改配置，不发布                 |
| 非 prod（如 `ppe` / `ppe_*`） | `auto/force-auto`        | `/api/v2/open/config/modify`              | 修改配置并发布                   |

v2 非 prod 的推荐流程：

1. 用 `tcc config update ... --env ppe_xxx` 写入待发布值。
2. 设置 `TCC_OPENAPI_TOKEN`。这是 CLI 为接口请求体 `token` 字段新增的环境变量入口，值必须是 TCC 平台分配的 OpenAPI service token，不能用 SSO/JWT 代替；也可以直接传 `--token`，但可能进入 shell history。
3. 用 `tcc deployment deploy ... --env ppe_xxx --publish-mode auto` 发布。CLI 会读取最新值，以 `latest_version` 作为默认 `from_version`，重新提交给组合式修改/发布接口；这不是 activity 发布单，也不是单纯的“发布已有版本”。
4. 每次只传一个明确的 `--region`；v2 非 prod 不支持 `--region all`，也不会扩展 sync group。该链路没有发布策略或区域并行发布单，因此不能使用 `--strategy-id` / `--region-parallel`。通常不要传 `--from-version`；若显式传入，它必须等于当前 `latest_version`，否则 CAS 校验会被 CLI 拒绝。

字段映射：`--dir-path` → `confspace`（`/default` → `default`），`--remark` → `note`。`--app-name` 对应 `app_name`，仅当 TCC 平台明确分配了 app_name 时才需要传，未分配时保持默认空字符串；`--operator` 对应版本历史修改人，通常无需传，省略时优先使用本地 bytedcli 登录用户名。JSON 输出会对 service token 和配置值脱敏。

可先加 `--dry-run` 做 OpenAPI mock 验证；验证成功后仍需移除 `--dry-run` 才会真实修改并发布。`--dry-run` 只支持 v2 非 prod；Web V1/v3 或 v2 prod 使用该参数会直接报错，不会把它当成无效参数后继续发布。

## Notes

- `tcc config create` / `tcc config update` 支持 `--enable-cdn true|false`，映射到 TCC v2 的 `config_data.enable_cdn`；省略时为 `false`（更新时也不会继承原配置值）。仅支持 `former_tcc` / `tcc_v2` namespace；Web V1 显式传入该参数会报错。

- 环境/region/dir 建议显式指定
- `tcc config create` 写入 `ppe` / `ppe_*` 环境时，如果目标 PPE TCC service 尚不存在，CLI 会自动创建该 env 的 TCC service 绑定；此绑定会优先使用本次命令的 `--region`。若该 region 不在 ENV TCC conf space 列表中，CLI 会直接报错并列出可用 regions，避免静默绑定到其他 region。
- `tcc config get` 支持 `--decrypt`，用于查看加密配置（`enable_encryption=true`）的明文值；不传 `--decrypt` 时加密配置只显示提示信息，不输出密文
- `tcc config list` 支持 `--keyword`、`--search-field name|value|description` 和 `--dir-path`；`--search-field` 默认是 `name`，`value` 搜索配置内容，`description` 搜索配置描述。列表请求不会返回配置正文
- `former_tcc` / `tcc_v2` namespace 仅支持 `--search-field name`；内容或描述搜索会明确报错，不会退化为全量读取配置
- `tcc config version diff` 按 namespace、config name、from/to version 直接输出两个配置版本的 unified diff；JSON 配置会先格式化再 diff，可用 `--context-lines` 调整上下文行数。diff 计算使用受限的时间与估算内存预算（直接取 V8 当前报告的完整安全可用堆空间 `total_available_size`）；差异过大时返回 `DIFF_RESOURCE_LIMIT`，不要通过增大 Node heap 反复重试，应缩小比较内容或在 deployment 查询场景使用 `--no-diff`
- `tcc deployment deploy` 支持 `--dir-path`，用于在同一 namespace 下存在同名配置时按目录锁定目标配置
- `tcc deployment deploy` 在策略类型为 `feature` 时，`--env` 仅支持 `ppe`/`ppe_*` 或 `boe`/`boe_*`（例如 `ppe_demo`、`boe_demo`）
- 使用全局 `--site` 选择站点（`cn|boe|i18n|i18n-bd|i18n-tt|us-ttp|eu-ttp`，别名：`prod` -> `cn`）。Per-service `--tcc-site` is a hidden alias for backward compatibility.
- `tcc namespace get <namespace>` 查询 namespace 详情，返回 namespace id、owner/operator/viewer、regions、Bytetree 节点等控制台详情字段。
- `tcc namespace psm-dependency list <namespace>` 列出依赖（读取）该 namespace 的调用方 PSM，走 TCC Web BFF `namespace/psm_dependency`。JSON 输出含去重后的 `psm_list`（`total_psm`）与按 region/dc 拆分的 `details`（`total_details`，同一 PSM 会在多个 `tcc_region`/`dependency_dc` 下重复），每条带 `dependency_cluster`、`sdk_language`、`sdk_version` 等字段。站点用全局 `--site` 或隐藏的 `--tcc-site`，`--env` 选环境；BOE 可用 `--site boe` 或仅 `--env boe`（未显式指定站点时按 env 回退到对应站点）。
- `tcc env create <namespace> --env <env> --regions <region...>` 为 namespace 创建 TCC 环境（如 PPE 泳道）：自动解析 namespace 对应的 ns_id，创建后用 `tcc env list` 回读校验新 env 是否出现，未确认出现或回读失败时返回 warning 而不是静默成功
- `tcc config import --target-env` 报 `NO_ACTIVE_ENV_FOUND` 时，说明目标 PPE 泳道环境还不存在，需要先用 `tcc env create` 建出该环境，再重试 `config import`
- `tcc env delete <namespace> --env <env>` 删除 namespace 下的 TCC 环境，是破坏性操作、不可撤销：不带 `--dry-run`/`--yes` 时会在交互终端二次确认，非交互终端必须显式传 `--yes` 才会执行；`--dry-run` 只解析 ns_id 并打印待提交的删除请求，不真正调用删除接口；删除后会用 `tcc env list` 回读确认该 env 是否已消失，仍存在或回读失败时返回 warning 而不是静默成功
- `tcc permission apply <namespace>` 申请 TCC namespace 权限：复用 TCC 控制台同款 `auth/bpm/create` 接口（走 `/api/v3/tcc/bcc/` 网关，不受 `iam permission apply` 在 i18n-tt 上遇到的 IAM 网关白名单限制）。命令会自动从 namespace 名解析 `ns_id` 和负责人（`rs_owners`），并按当前登录用户填申请人；工单路由给 namespace 负责人审批
  - `--access` 映射 TCC 角色：`read->tcc.ns_viewer`、`write->tcc.ns_operator`、`admin->tcc.ns_owner`；也可用 `--role` 直接指定角色（覆盖 `--access`）
  - `--approver <username...>` 覆盖默认负责人；`--username` 覆盖申请人；`--dry-run` 只打印请求体不提交
  - namespace 入参支持直接给名字，或给 `https://<host>/tcc/namespace/<name>` 形式的控制台 URL
- 任意 `tcc` 命令报 `TCC_PERMISSION_DENIED`（后端原文通常是 `Unauthorized Error logid:...`）：这次请求用的身份在该 namespace 下没有角色，或角色（`details.role`）权限不够，不是登录过期。TCC 返回调用身份时放在 `details.caller.user_name`；如果请求不是以你本人身份发出（用了 app 凭据或 JWT 覆盖），加全局 `--as user` 以本人身份重试。JSON 错误的 `details.rs_owners` 列出 namespace 负责人（最多 20 个，总数见 `rs_owners_total`），`hint` 会点名前几位。可以直接找负责人授权，或带上与原命令相同的 `--site` / `--env` 提交申请：`bytedcli --site us-ttp tcc permission apply "demo.namespace" --access read --reason "Need config access"`（已有只读角色、要改配置时用 `--access write`）
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json tcc config list "namespace" --region CN ...`）
- `tcc config create` 需要显式传 `--description`；TCC Web 创建接口要求 description 非空，CLI 会先在本地校验
- `tcc config create` 的 `--data-type` 默认值是 `yaml`，CLI 不会根据 `--value` / `--file` 内容自动识别类型。**调用 `tcc config create` 之前，必须先根据待写入内容推断 data type，并显式传入 `--data-type`**：
  - 内容能被 `JSON.parse` 解析成对象/数组（典型形如 `{...}` / `[...]`） → `--data-type json`
  - 内容是 YAML 文档（含 `key: value`、缩进列表、`---` 文档分隔等典型 YAML 结构） → `--data-type yaml`
  - 内容是单行/多行纯文本，且既不是合法 JSON 也不是 YAML 结构 → `--data-type string`
  - 用 `--file` 传入时，优先按扩展名判断（`.json` → json，`.yaml` / `.yml` → yaml，其他 → 用上面的内容判断兜底）
  - 推断不确定时优先选 `string`，避免被 TCC 当作 yaml 解析失败或字段语义错配
- `tcc config create` / `tcc config update` 支持 `--encrypted <boolean>`，用于显式控制 Web V1 namespace 的 `enable_encryption`
- `tcc config create` 在 `former_tcc` / `tcc_v2` namespace 上会自动回退到 V2 `service_id` 创建接口，不需要手写内部 API
- `tcc config update` 在 `former_tcc` / `tcc_v2` namespace 上会自动回退到 V2 `service_id` 的 `config/upsert/v2` 接口，按传入的 `--region` 和 `--dir` 更新对应副本
- `tcc config create` / `tcc config update` 在 `former_tcc` / `tcc_v2` namespace 上暂不支持 `--encrypted`；CLI 会直接报错，避免静默忽略
- `tcc config update` 在 Web V1 namespace 上默认会根据 `sync_config_regions` 自动补齐同组内所有已存在副本的 `extend_regions` 和 `update_base_version`；例如同一配置同时存在于 `CN` / `China-East` 时，不需要手动拆成多次更新，JSON 输出会返回实际覆盖的 `regions`
- 如需只更新显式传入的 `--region`，可加 `--no-sync-group`；CLI 将跳过同步组扩展，只更新单个 region
- `tcc deployment deploy` 在 `former_tcc` / `tcc_v2` 的 `prod` 环境会切到 TCC AG V2 activity 链路：先用 `service_id` 读取配置，再调用 `config/upsert_deploy/v2` 创建或复用发布单，并按 `deployment/step_info` 判断是否继续推进 `next`
- TCC v2 prod 发布可用 `--gray-psm` 指定小流量 PSM；参数可重复或传逗号分隔值。CLI 会按控制台契约发送 `gray_deploy=true`，并在 `gray_settings` 中使用 `query_type=consul`、`duration=3600` 和去重后的 `psm_list`。该参数不支持 Web V1 或非 prod 发布链路
- TCC v2 的 `ppe` / `ppe_*` 等非 prod 环境不走 activity 发布单：`--publish-mode manual` 调用 `/api/v2/open/config/modify_only`（只修改不发布），`auto` / `force-auto` 调用 `/api/v2/open/config/modify`（修改并发布）。该 OpenAPI 没有“只发布已有版本”的独立接口，因此 CLI 会读取配置的 `latest_version` 和最新值，以最新版本作为默认 `from_version`，将该值重新提交给组合式修改/发布接口
- TCC v2 非 prod OpenAPI 只接受单个明确的 `--region`，不支持 `--region all`。必须通过 `TCC_OPENAPI_TOKEN`（推荐）或 `--token` 提供 TCC service token，不能使用 SSO/JWT 代替；token 和配置值会在 JSON 输出中脱敏
- 首次验证应加 `--dry-run`：请求会携带 `tcc-openapi-mock: 1`，成功只代表 mock 请求校验通过，不会真实修改或发布；此时 `deployment_id` 可能为 `null`，属于正常结果。确认后必须移除 `--dry-run` 才会真实提交
- `tcc deployment deploy` 在 Web V1 namespace 上默认会根据 `sync_config_regions` 自动补齐同组内所有已存在副本的 `config_changes` 与 `check_review conf_ids`；例如同一配置同时存在于 `CN` / `China-East` 时，不需要手动拆成多次发布，JSON 输出会返回实际覆盖的 `regions` / `config_ids`
- 如需只发布显式传入的 `--region`，可加 `--no-sync-group`；CLI 将跳过同步组扩展，只创建单 region 发布单
- 如需区域并行发布，在命令中添加 `--region-parallel`
- `tcc deployment deploy` 通过 `--publish-mode` 控制发布策略：
  - Web V1 / TCC v2 prod：`auto` 在无需 review 时自动推进；`manual` 只创建发布工单；`force-auto` 忽略 review 尝试自动推进
  - TCC v2 非 prod：`auto` / `force-auto` 均调用 `modify` 修改并发布；`manual` 调用 `modify_only`，只修改不发布
  - 被 SCP 策略封禁时，返回逃逸申请链接
- 当策略阶段配置了 `force_rolling=true` 时，`tcc deployment deploy` 会自动把对应阶段的 `enable_rolling` 一并置为 `true`，避免 Web 发布 payload 因滚动开关不一致被拒绝
- `tcc deployment get` 支持直接传 TCC 控制台 `publish-details` URL；未显式传 `--site` 时，会优先按 URL host 自动推断站点
- `tcc deployment get --no-diff` 只读取发布单详情与 `get_step` 步骤信息，跳过配置版本内容读取和 diff 生成；适合大配置，或只需要 `config_changes` 与“全量发布”阶段 `started_at` / `completed_at` 的场景
- `tcc deployment get` 的单个配置 diff 超出时间或内存预算时，主查询仍保持成功，该项 `changes[].diff.available=false`；JSON 输出可通过 `error_code=DIFF_RESOURCE_LIMIT` 与 `resource_limit` 查看限制详情，文本模式显示 diff unavailable。无需内容差异时使用 `--no-diff` 完全跳过 diff
- `tcc deployment get` 默认会并发调用 `get_step`，把当前步骤索引、阶段类型和 `allow_operations` 一起返回；若 `get_step` 失败，不会影响主查询结果。文本模式下拿到 step 信息时也会打印当前 step 摘要，方便继续执行 `tcc deployment operate`
- `tcc deployment operate` 直接透传底层 `deployment/operate`；未显式传 `--current-step-index` 时，会自动调用 `get_step` 推断当前步骤
- `tcc deployment approve` / `tcc deployment reject` 分别封装 review 步骤的 `review_pass` / `review_reject`
- `tcc access-control` 用于管理目录级调用方 PSM 访问控制：常规站点走 TCC Platform OpenAPI，`us-ttp` / `eu-ttp` 自动切换到对应站点的 TCC Web BFF；写操作必须传 `--dry-run` 或 `--yes`，且 `--dry-run` 优先
- `tcc access-control rule create` 支持用 `--psm` 生成 `psm_list`，也支持通过 `--request-json` / `--request-file` 直接提供完整 payload；创建后可能进入 `review_on`，需要非申请人使用 `rule approve` / `rule reject` 处理审核
- `tcc access-control dir operate` 切换目录级 ACL 鉴权状态，走 TCC Web BFF `acl/dir/operate`（与 `dir info` 同一网关，命令会先读当前 status 再提交）。`--target-status` **只允许 `gray`（灰度/观察模式）和 `off`（关闭）**；**`on`（全量开启鉴权）被刻意禁用**（choices/schema/handler 三层拦截），影响面大，只能去 TCC 控制台操作。写操作必须带 `--dry-run` 或 `--yes`；当前 status 已等于目标时非 dry-run 会直接报 `TCC_ACL_NOOP`（后端拒绝 no-op），dry-run 则照常预览请求体并标注 `would_be_noop`。BOE 用 `--site boe` 或仅 `--env boe`（未显式指定站点时按 env 回退到对应站点，避免误打到 CN 生产），region 用 `China-BOE`/`US-BOE`。
- `us-ttp` / `eu-ttp` 的 Web BFF 删除请求必须同时提供 `--rule-id`、`--psm`、`--namespace`、`--region`、`--dir-path`；审批/驳回必须同时提供 `--rule-id` 和完整的 namespace/region/directory scope。CLI 会在 dry-run 和提交前校验这些字段
- 访问控制按 `namespace + region + dir-path` 维度生效；如果同一 TCC namespace 在多个 region 下读取配置，需要分别申请同一调用方 PSM
- 控制台展示的聚合区域可能不是 OpenAPI region 参数；例如常见聚合区域在 OpenAPI 中可能需要传 `CN`，应先用 `access-control dir info` 做只读验证
- `tcc region-consistency whitelist create` 只接受一个精确 `namespace + dir-path + config-name`，拒绝 `*` 和原始 JSON 覆盖；写操作必须传 `--dry-run` 或 `--yes`
- 一致性白名单本身不带 region 字段，可能影响该配置所在的全部有效一致性区域组。命令会先读取 policy，并要求 `--expected-regions` 与所有有效 policy 的完整 region 并集一致；不匹配或无法读取时拒绝写入
- 创建前会扫描现有白名单；精确条目已存在时不再 POST。创建 POST 固定只发一次，响应不明确时只做 list 回读并禁止自动重试
- `bpm_url` 表示工单仍待审批，不代表白名单已生效；list 出现条目也只标记为 `listed`，因为该 API 不提供 activation 状态。后续仍应重新执行原发布预检验证豁免是否真正生效

## References

- `references/tcc.md`
- `references/third-party-notices.md` — jsdiff BSD-3-Clause license notice
