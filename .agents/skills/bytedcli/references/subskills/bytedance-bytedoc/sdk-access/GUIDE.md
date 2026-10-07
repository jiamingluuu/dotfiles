# ByteDoc SDK 接入指南

当用户希望从代码访问 ByteDoc 数据库、询问授权后如何连接，或只提供 ByteDoc PSM 并希望获得 SDK 接入帮助时，使用本指南。

## 首屏规则

- 先确认 `site`；再确认目标数据库的 `backend` 和 `vregion` 是否唯一。缺少 `site` 时按 `../references/selection-guards.md` 询问。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一；任一维度多值时必须让用户选择。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选表，不要自行选择后继续 `sdk plan` / `sdk generate`。
- 先运行 `sdk plan` 判断接入方式、前置条件、warning 和 next actions；`supportStatus=unsupported|needs_input` 时停止，不生成 SDK 代码。
- 对 `unsupported` 结果要解释原因，不要用猜测连接串绕过；对 `ambiguous` 结果，询问 CLI 返回的 `questions[]`。
- `accessMethod.kind=visual-query` 只说明用户要可视化查询，不需要 SDK 代码；不要把 `sdk plan` 的可视化建议当成 `collections` / `shell` / `document` 查询命令直接执行。
- 如果用户在 `visual-query` 后继续要求查看集合、抽样数据或执行查询，切换到 `mongo-ops` 或 `mongodb-natural-language-querying` 流程。
- ByteDoc 专属决策优先于通用 MongoDB 最佳实践；Mesh、Consul、Token、开发调试账号密码、PSM 授权和 BOE/CN 网络边界由 ByteDoc 决定。
- 将 bytedcli 视为 ByteDoc 专家工具，不要从 bytedcli 扫描或修改用户项目；coding agent 在用户确认后再把返回的方案和代码素材应用到项目中。

## 核心流程

- SDK 生成请求：确认 site 后，先用 `bytedoc search` 或 `sdk plan` resolver 确认 backend/vregion 唯一；唯一后后续命令显式携带已确认的 `--backend` 和必要的全局 `--vregion`。需要代码时按用户语言传 `--language <go|python|java|nodejs|cpp>`（默认 `go`）；只有纯接入方案问题且不需要代码时，才可以省略 `--language`。
- 对 `tce` 和 `faas`，`--runtime-network` 是 caller TCE/FaaS 所在运行网络，只能来自用户确认的 caller 运行环境证据；如果用户已知业务运行网络，传 `--runtime-network boe|boei18n|cn|i18n-bd|i18n-tt|us-ttp|eu-ttp`。不要用目标库的 site/vregion/搜索页/VDC 反推 `--runtime-network`。
- 如果已知是 `tce/faas` 但运行网络未知，即使用户提供了调用方 TCE PSM，也优先询问用户确认运行网络；不要为了推断 `runtimeNetwork` 主动搜索 TCE / Keel 证据。
- 已知 caller PSM 时，`sdk plan` 和 `sdk generate` 都显式携带 `--caller-psm <caller.psm>`，用于保留同一个调用方上下文；它不会驱动 runtime-network 推断，也不能替代 `--runtime-network`。CLI 在缺少 runtime network 时会返回 `supportStatus=needs_input` 与 `questions[]`，必须停止并让用户确认。
- 明确的 BOE、CN 或海外站点运行环境证据只有在用户确认后才映射到对应 `--runtime-network boe|boei18n|cn|i18n-bd|i18n-tt|us-ttp|eu-ttp`；不要用目标库网络 fallback 代替用户确认。
- BOE 内部分区不能压扁：目标库 `site=boe` 且 `vregion=US-BOE`/`boei18n` 时，caller 只确认 `boe` 仍不足以证明同分区；必须确认 caller TCE/FaaS VRegion。确认 caller 也在 US-BOE/boei18n 后用 `--runtime-network boei18n`；如果 caller 在 China-BOE，则不能按同站点经典库接入继续生成代码。
- `--engine-version 4.0|8.0` 只用于 resolver 已确定唯一目标、但平台元数据未返回引擎版本，且用户或平台证据已经明确版本的场景。元数据已有版本时不要传该参数；若 CLI 返回 `BYTEDOC_SDK_ENGINE_VERSION_CONFLICT`，停止并修正目标或版本，不能用参数覆盖平台事实。
- 默认使用 `--reference-mode fixed`。只有用户明确希望补充字节云文档搜索结果，或担心固定链接过期时，才使用 `--reference-mode hybrid`。
- 如果 `sdk plan` 返回 `references[]`，向用户展示每个 reference 的标题、URL 和原因；固定 reference 可作为 unsupported 或 ambiguous 结论的证据。
- 如果 `referenceSearch.status=success`，只把动态 Top3 reference 当作补充材料；不要让动态结果覆盖确定性接入矩阵。若 `referenceSearch.status=error`，继续使用固定 reference，并说明补充搜索不可用。

## DO / DON'T

| 场景                                      | DO                                                            | DON'T                                             |
| ----------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| 用户说"生成 SDK 代码"                     | 先 `sdk plan` 确认支持，再 `sdk generate`                     | 不要跳过 plan 直接 generate                       |
| `supportStatus=unsupported`               | 展示原因和 references，停止生成代码                           | 不要猜一个连接串给用户                            |
| `accessMethod.kind=visual-query`          | 口语化说明可用控制台可视化查看；继续查询时切到查询流程        | 不要直接执行 `collections` / `shell` / `document` |
| 用户没说 collection                       | 先询问或列集合                                                | 不要用 `BYTEDOC_COLLECTION` 占位值当真实代码      |
| 用户有 caller PSM 但 runtime network 未知 | 运行带 `--caller-psm <caller.psm>` 但不带 `--runtime-network` 的 `sdk plan`，收到 `supportStatus=needs_input` 后停止并询问用户确认 caller runtime-network | 不要主动搜索 TCE / Keel 证据推断 runtime-network；不要把目标库 site/vregion/搜索页/VDC 当作 `--runtime-network` |
| `access-env` 未知                         | 使用 `--access-env auto`                                      | 不要猜 `tce` 或 `local-mac`                       |
| SDK 接入已知 caller PSM                   | 代码素材后先运行 `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）检查 caller PSM 当前授权；target/backend/vregion 需先确认唯一 | 不要直接用 `permission get` 或 dry-run 推断 caller PSM 权限 |
| Volc 后端                                 | 按 resolver 返回的结果走，用 `access psm list --backend volc` | 不要用 classic 的 `role list` 验证 Volc 权限      |
| 唯一 Volc 目标缺少引擎版本元数据          | 取得明确版本证据后传 `--engine-version 4.0|8.0`               | 不要猜版本，也不要覆盖平台已有版本                |

## Access Env 取值

- `local-mac`：本地 Mac 开发。
- `devbox`：DevBox 开发。
- `tce`：TCE 运行时。
- `faas`：ByteFaaS 运行时。
- `visual`：仅可视化查询。
- `auto`：接入环境未知；仅在用户没有提供足够上下文时使用。

## 当前矩阵

- 区分 `accessEnv` 和 `runtimeNetwork`：`accessEnv` 描述 local Mac、DevBox、TCE、FaaS 或 visual access；`runtimeNetwork` 描述 TCE/FaaS 运行在 BOE 还是 CN。
- CN classic 从 CN TCE/FaaS 访问使用 `consul-token`。
- CN Volc 从 CN TCE/FaaS 访问使用 `mesh-token`，且需要 ByteDoc Service Mesh egress；Go 官方 SDK 需使用支持自动接入 Mesh 的版本（最低 v1.2.6）。
- CN classic 从 BOE 本地开发或 BOE TCE/FaaS 访问不支持，因为网络不可达。
- BOE classic 从同一 BOE 分区的 TCE/FaaS 访问使用 `consul-token`；访问路径与 CN classic 一致，前提是运行环境到目标 BOE 经典库网络/VDC 可达。`China-BOE` 与 `US-BOE`/`boei18n` 需要分别确认，不能只凭 `boe` 放行。
- 海外 classic（`i18n-bd` / `i18n-tt` / `us-ttp` / `eu-ttp`）从同站点 TCE/FaaS 访问使用 `consul-token`；访问路径与 CN classic 一致，前提是运行环境到目标海外经典库网络/VDC 可达。
- BOE Volc MongoDB 4.0 从 BOE 本地开发或 BOE TCE/FaaS 访问使用 `consul-token`。
- BOE Volc MongoDB 8.0 从本地开发访问使用开发调试账号密码。兼容字段仍返回 `accessMethod.kind=consul-temporary-credential`，并通过 `canonicalKind=consul-password` 表达稳定语义；该凭据仅用于开发。
- BOE Volc MongoDB 8.0 从 BOE TCE/FaaS 访问使用 `mesh-token`，且需要 ByteDoc Service Mesh egress。
- BOE Volc 从 CN TCE/FaaS 访问不支持，因为网络不可达。
- 仅可视化访问使用 `visual-query`，不得触发 SDK 代码生成。

## Volc 开发凭据

- `sdk credential` 管理的是用户维度的 Volc 开发调试账号密码，只用于 `local-mac` / `devbox`。它不是 caller PSM 授权、当前用户 IAM 权限或 TCE/FaaS 生产凭据；不要混用这三类状态。
- 先运行 `sdk plan`。只有 `supportStatus=supported` 且 `accessMethod.kind=consul-temporary-credential` 时才进入开发凭据流程；`consul-token`、`mesh-token`、`visual-query`、`unknown` 或 `unsupported` 都不得查询或创建开发凭据。
- 凭据命令必须显式提供全局 `--site <site>`，海外或共享控制面还要携带已确认的全局 `--vregion <vregion>`。目标 service 和 `--backend volc` 在查询、预览和提交阶段必须保持一致。
- 先运行 `credential get`。CLI 只返回凭据状态，不返回密码材料；Agent、traced wrapper 和审计 wrapper 不得尝试读取或打印明文。只有 SDK bootstrap runtime 可以在内部 service 边界取得密码，并直接注入子进程环境或 mode-0600 文件。
- `current.valid=true` 时复用现有凭据并停止，不要刷新。只有 `current=null` 或 `current.valid=false` 时才运行 create dry-run 并询问用户是否创建或刷新。
- 创建或刷新是两阶段动作：第一次不带 `--yes-i-know-this-is-live`，向用户展示 `preview.confirmation.reviewTable` 和 warning；用户明确确认同一 service、region、user、days 后，才以完全相同参数追加 live flag。
- `userNameSource=stored_fallback` 只能用于无明文查询和预览。真实提交或内部读取密码前必须恢复 user-scoped ByteCloud 认证；显式 `--user-name` 也必须与当前认证用户一致。
- 若返回 `BYTEDOC_DEV_CREDENTIAL_GRANT_OUTCOME_UNKNOWN` 或 `doNotRetryAutomatically=true`，只重跑 `credential get` 核对当前状态；不要自动再次提交 create。
- 将结果中的 `officialWorkflow.url` 返回给用户，便于查看官方步骤；不要把开发凭据申请误写成工单或 GUI token 流程。

```bash
bytedcli --json --site <site> --vregion <confirmed-vregion> bytedoc sdk credential get --service "example.bytedoc.demo_volc" --backend volc
bytedcli --json --site <site> --vregion <confirmed-vregion> bytedoc sdk credential create --service "example.bytedoc.demo_volc" --backend volc --user-name "example.user" --days 1
# 用户确认 dry-run 中的同一组字段后：
bytedcli --json --site <site> --vregion <confirmed-vregion> bytedoc sdk credential create --service "example.bytedoc.demo_volc" --backend volc --user-name "example.user" --days 1 --yes-i-know-this-is-live
```

## SDK 素材（多语言）

- 仅当 `sdk plan` 支持且 backend/vregion 已确认后，才调用 `bytedcli --json --site <site> --vregion <confirmed-vregion> bytedoc sdk generate --service <psm> --backend <confirmed-backend> --access-env <env> --runtime-network <boe|boei18n|cn|i18n-bd|i18n-tt|us-ttp|eu-ttp> --caller-psm <caller.psm> --language <go|python|java|nodejs|cpp> --collection <collection> --operation find-one`；如果 caller PSM 未知才省略 `--caller-psm`。
- `--language` 支持 `go`、`python`、`java`、`nodejs`、`cpp`，默认 `go`；按用户使用的语言选择。
- `local-mac`、`devbox` 和 `visual` 省略 `--runtime-network`；`tce` 和 `faas` 需要携带。
- 将 `codeSamples[]` 视为给 coding agent 适配到业务仓库的素材。
- 当用户要求 SDK 代码或代码素材时，最终答复先完整展开 `codeSamples[].content`，再总结依赖、环境变量或验证命令。
- 代码后必须包含“接入指导”段落。优先使用 `integrationGuidance[]`，再总结选定接入方式、运行网络假设、collection 占位/真实值、验证路径和下一步友好动作。
- 即使答复还包含权限状态、授权 dry-run 输出、warning 或 SDK doctor 诊断，也不要省略“接入指导”。
- 如果 `BYTEDOC_COLLECTION` 仍是占位值，不要只输出 CLI 命令；需要说明“如果不知道 collection 名，可以让我继续帮你查询一下”。
- 如果用户要求真实可运行代码但未提供 collection，先询问 collection，不能猜业务集合名。
- 生成代码使用对应语言的 ByteDoc 官方 driver：Go 用 `code.byted.org/bytedoc/mongo-go-driver`、Python 用 `bytedpymongo`、Java 用 `com.bytedance.bytedoc:mongo-java-driver`、Node.js 用 `@byted/bytedmongodb`、C++ 用 blade `bytedoc/mongo-cxx-driver`；不要使用 upstream MongoDB driver（如 `go.mongodb.org/mongo-driver`）。
- 阅读并应用 `sdk generate` 返回的 `relatedGuides[]`；这些 guide 指向 ByteDoc 适配过的 MongoDB 官方 skill 指南。
- 不要从 bytedcli 把生成代码写入用户仓库。
- 保留质量要求：复用 client 实例（Go `mongo.Client` / Node `MongoClient` / C++ `mongocxx::pool` 等），在语言支持范围内设置连接/查询超时，不要记录 token 或完整 URI。`--operation find-one|find` 只生成对应的只读查询；`find` 示例必须保留明确的结果上限。不要把 `sdk generate` 当成写操作样例生成器。

## 授权检查位置

- 将 PSM 授权视为运行时就绪检查，而不是生成 SDK 代码素材的阻断条件。
- 如果用户同时提供调用方 PSM 和目标 ByteDoc PSM，且接入矩阵支持，先完成 `sdk plan` 和 `sdk generate`。
- 代码素材之后，只要用户提供了 caller PSM，就先运行 `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或使用 `--db-name <db>`）检查 caller PSM 当前授权状态；classic、cloud-native、Volc 都遵循这条规则，Volc 仍显式带 `--backend volc`。若尚未确定唯一 target/service/db-name、backend 或 vregion，先完成 search/resolver 选择后再跑 `access psm list`。
- `access role list` 用于展示 IAM 角色和绑定选项；`access permission get` 只检查当前操作者是否具备发起授权的前置权限，不能证明 caller PSM 已授权。不要把 `permission get`、`role list` 或审批 dry-run 当作 caller PSM 授权状态。
- 先完成 `access psm list`，再根据 `accountCheck.status`、`accountCheck.authorized`（若返回）、`accountCheck.roles` 和 `inspection.source` 给出权限结论；如果已经授权，说明当前权限并继续给验证命令。
- 如果 `accountCheck.status=not_authorized`，或返回了 `accountCheck.authorized=false`，不要用授权 warning 替代生成代码；在末尾追加“权限状态”段落，询问是否继续协助申请授权。只有授权缺失且用户希望继续协助申请时，才进入 `ticket create` / `psm create` dry-run。
- 如果 `inspection.status=unknown`（结合 `inspection.source` / `inspection.reason` 描述不确定性）或读取失败，报告不确定性和下一步动作，不要直接断言无权限，也不要直接进入 dry-run。
- 授权 dry-run 可以在用户同意继续申请后执行，但真实提交必须获得用户明确确认。确认后由 Agent 自己遵循 CLI 确认协议；不要让用户复制隐藏 live-submit 命令。
- 对 `backend=volc`，先区分 IAM 用户角色授权与 PSM/token 授权。IAM 用户角色授权使用 `access role list` / `access permission get` / `access user apply`；PSM/token 授权状态使用 `access psm list --service <target.psm> --backend volc --account <caller.psm>`，或遵循错误码为 `BYTEDOC_ACCESS_REQUIRED` 的错误对象路径 `error.details.setup_commands`。当返回 `inspection.source=bytedoc_multicloud_get_account` 和 `accountCheck.status` 时信任它们，只有 PSM/token 授权缺失时才准备 `access psm create --backend volc` dry-run。

## SDK 诊断

- 当用户报告 SDK 连接、鉴权、超时、Consul、Mesh、DNS 或权限失败时，使用 `bytedcli --json bytedoc sdk doctor --error-text "<error text>"`。
- 如果用户已提供相关信息，携带 `--service <psm>`、`--backend <confirmed-backend>`、`--caller-psm <caller.psm>`、`--access-env <env>` 和 `--runtime-network <boe|boei18n|cn|i18n-bd|i18n-tt|us-ttp|eu-ttp>`；site 未知时先询问。
- 将返回的 `category`、`severity`、`evidence`、`likelyCauses`、`nextActions` 和 `verificationCommands` 作为给 coding agent 和用户的诊断材料。
- 如果 category 是 `permission` 且已知 caller PSM，先执行返回的 `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）验证 `accountCheck.status`；只有 `not_authorized` 时才继续准备返回的 `psm create` / `ticket create` dry-run，`authorized` 时展示已有角色并回到 SDK 接入排查。
- PSM/token 当前授权真源按 backend 区分：classic 是 `inspection.source=classic_get_db_accounts`，cloud-native 是 `inspection.source=cloud_native_get_account`，Volc 是 `inspection.source=bytedoc_multicloud_get_account`。不要用 IAM `permission get`、`role list` 或申请 dry-run 替代这些来源。
- 如果 category 是 `network` 或 `credential`，运行 `sdk plan`，并将实际代码/运行环境与返回的接入方式对齐。
- 诊断时不要从 bytedcli 扫描或修改业务代码；coding agent 可以在展示 CLI 诊断后再检查用户项目。

## 已适配的 MongoDB 指南

- `mongodb-connection/GUIDE.md`：client 生命周期、context timeout、token / 临时凭证处理和连接故障排查。
- `mongodb-natural-language-querying/GUIDE.md`：将用户查询意图适配为有边界的 read filter、projection 和 sample query。
- `mongodb-query-optimizer/GUIDE.md`：慢查询、索引、explain、sort 和 query shape 分析。
- `mongodb-schema-design/GUIDE.md`：生成 SDK struct 或查询需求暴露 schema 设计取舍时使用。
- upstream 来源和排除的 MongoDB 官方 skill 记录在 `../references/mongodb-upstream-adaptation.md`。
- MongoDB 官方 agent-skill 指南已经适配进 ByteDoc 规则；不要要求用户另装 upstream MongoDB skill。
- ByteDoc SDK 包选择基于 ByteDoc 官方文档；具体链接以 `sdk plan` / `sdk generate` 返回的 `references[]` 为准，不在 Skill 中固化具体文档 token。

## 端到端示例：SDK 接入完整流程

```bash
# 场景：用户说"帮我生成 example_db 的 Go 接入代码，我在 TCE 环境"

# Step 1: 确认 site 后解析目标数据库
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.example_db"
# → 确认唯一候选：backend=classic, vregion=China-North

# Step 2: 执行 plan（显式带入已确认 backend/vregion/caller；TCE 运行网络未知时先确认）
bytedcli --json --site cn --vregion China-North bytedoc sdk plan --service "example.bytedoc.example_db" --backend classic --access-env tce --caller-psm "example.caller.psm" --language go
# → 返回 supportStatus=needs_input，questions[] 要求确认 TCE/FaaS 是否运行在 CN 同站点网络或网络互通

# Step 3: 用户确认 TCE 运行在 CN 网络后，重新执行 plan
bytedcli --json --site cn --vregion China-North bytedoc sdk plan --service "example.bytedoc.example_db" --backend classic --access-env tce --runtime-network cn --caller-psm "example.caller.psm" --language go
# → 返回 supportStatus=supported, accessMethod=consul-token, runtimeNetwork=cn

# Step 4: 生成代码
bytedcli --json --site cn --vregion China-North bytedoc sdk generate --service "example.bytedoc.example_db" --backend classic --access-env tce --runtime-network cn --caller-psm "example.caller.psm" --language go --collection "orders" --operation find-one
# → 返回 codeSamples[] + integrationGuidance[]

# Step 5: 展示代码和接入指导
# Agent 完整展示 codeSamples[].content，再附接入指导段落

# Step 6: 检查 caller PSM 权限（后置，不阻断代码生成；先完成 access psm list 再考虑 dry-run）
bytedcli --json --site cn --vregion China-North bytedoc access psm list --service "example.bytedoc.example_db" --backend classic --account "example.caller.psm"
# → 如果 accountCheck.status=authorized，展示已有权限；如果 not_authorized，追加"权限状态"段落询问是否协助申请，再准备 ticket create dry-run
```

## Backend 感知解析

- ByteDoc 有三个 backend（`classic`、`cloud-native`、`volc`），元数据来源不同；`sdk plan` 必须复用 resolver 确认的来源，不要无条件调用 legacy classic / cloud-native detail API。
- 对 `backend=volc`（DBW / Volc Mongo），使用 resolver 返回的 Cloud Service Search summary；不要调用 cloud-native `/api/service/:service` 的 `getDatabaseDetail`，该接口对 Volc 数据库会返回 `mongo: no documents in result`。
- 新增需要数据库 overview 的 ByteDoc service flow 时，优先使用 `fetchDatabaseOverviewForQuery` 或等价的 backend-aware helper，让 DBW / Volc 路径绕过 classic detail API。
- 测试必须覆盖 Cloud Service Search 能解析数据库、但 legacy detail API 不支持该数据库的路径（典型 Volc 场景）。
