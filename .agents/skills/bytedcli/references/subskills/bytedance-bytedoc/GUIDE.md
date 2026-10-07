---
name: bytedance-bytedoc
description: "Use when tasks mention ByteDoc, bytedoc, or unqualified Mongo/MongoDB database work in ByteDance: business-code review of diffs/MRs with live metadata, Mongo libraries, collections, documents, shell queries, slow queries, indexes, SDK access, PSM authorization, IAM user permission management, or ByteDoc/Mongo errors such as not authorized, access denied, forbidden, no permission, BYTEDOC_ACCESS_REQUIRED, BYTEDOC_AMBIGUOUS, or BYTEDOC_UNSAFE_OPERATION_BLOCKED. In ByteDance context, generic Mongo/MongoDB usually means ByteDoc unless the user explicitly names DMS or another platform."
---

# bytedcli ByteDoc Skill

ByteDoc 路由器。不同 backend（classic / cloud-native / volc）和不同 site 使用完全不同的 API 基础设施。**不要猜测参数；先停下来确认，再执行命令。**

**触发规则：在字节内部，用户泛称 `mongo`、`MongoDB`、Mongo 库、集合、文档、慢查询、索引、连接、SDK 或权限时，默认按 ByteDoc 处理。只有用户明确说 DMS、DMS 控制台、DMS `db-id`、或明确要求非 ByteDoc 的 MySQL/Redis/DMS 统一查询时，才转到其它数据库 skill。**

**用户手册入口：当用户咨询 “bytedcli 中 bytedoc 支持什么能力”、 “bytedance-bytedoc 这个 skill 支持什么能力”、 “ByteDoc Agent 有哪些功能” 或类似泛能力问题时，优先返回用户可见的 ByteDoc Agent 能力用户手册：`https://bytedance.larkoffice.com/wiki/Ym4NwFbY3iZAzzkunU4cUYwFnyb`。这份文档只面向用户了解能力范围，不作为 Agent 执行参考；Agent 的参数、路由、权限、安全边界和操作流程仍以本 `SKILL.md`、各 `GUIDE.md`、CLI `--help` 与结构化输出为准。**

CLI / MCP 场景也可以用 `bytedcli bytedoc get-manual` 获取同一个用户手册入口。

**写入与变更确认提示（必须展示）：凡是 Agent 准备向用户确认 ByteDoc Mongo 写入或变更（包括 `collection create`、`document insert/update`、写入型 `shell`、Volc `createIndex`），无论确认材料来自 CLI dry-run 还是 Agent 基于只读查询自行生成的业务预览，确认问题里都必须完整展示：`注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。` 用户明确确认后，才可追加 `--execute --yes-i-understand-agent-write-risk` 执行。**

**写入确认时序（硬约束）：只读查询结果只能用于确认影响范围，不能作为最终确认问题。查到待变更记录后，禁止直接问“是否继续/确认执行”。必须先运行一次“最终将执行的写入命令”且不带 `--execute`，让 CLI 返回 dry-run confirmation；随后展示 CLI 的 `confirmation.reviewTable` 和 `confirmation.warning` 再问用户。错误路径示例：`document list` / `shell find` 查到 3 条后直接询问用户是否执行 `updateOne`。正确路径：查到影响范围后，继续运行 `document update` 或写入型 `shell` dry-run，由 CLI 打出风险提示，再向用户确认。**

**生产网只读硬边界：设置 `BYTEDCLI_NETWORK_PROFILE=prod` 时，bytedcli 只允许 ByteDoc 只读操作。Mongo/索引/授权/关注等所有写入或变更意图（包括 dry-run）都会在远端变更请求前被阻止：生产网策略返回 `BYTEDOC_PROD_NETWORK_READ_ONLY`，全站点已禁用的 drop/delete/rename 等破坏性操作仍可能优先返回 `BYTEDOC_UNSAFE_OPERATION_BLOCKED`。收到任一错误后必须停止；不要取消变量、切换 ByteDoc 域名、改走 DMS/DBW 或换命令形态绕过。该变量会为 i18n-tt 同时选择 ByteDoc classic 控制面的生产 cloud 域名和生产网 DMS API ingress；办公网、其他 site 与 DMS origin 不受影响。此时 `--endpoint` / `BYTEDCLI_BYTEDOC_ENDPOINT` 只有与当前 site/vregion 的 canonical 生产 cloud endpoint 一致时才允许使用，否则返回 `BYTEDOC_PROD_ENDPOINT_OVERRIDE_BLOCKED`。**

---

## 🛑 STOP — 执行任何命令前必须通过

以下条件未满足时，**禁止执行任何 ByteDoc 命令**：

| #   | 条件                                                 | 未满足时的行为                                                                                                                                                              |
| --- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `site` 已确认                                        | **立即询问用户**，给出选项：`cn / boe / i18n-bd / i18n-tt / us-ttp / eu-ttp`                                                                                                |
| 2   | 目标库 selector 可被用户输入或 CLI resolver 唯一确定 | 基本信息/详情请求中，裸 `dbName` 直接用 `bytedoc get --db-name`，完整 PSM 直接用 `bytedoc get --service`；不要先问 backend。只有 CLI 返回多候选或 `ASK_USER` 时才让用户选择 |
| 3   | CLI 未返回 `BYTEDOC_AMBIGUOUS`                       | **展示候选表格给用户选择**，不要自行挑选                                                                                                                                    |
| 4   | CLI 未返回 `BYTEDOC_UNSAFE_OPERATION_BLOCKED`        | **立即停止**，不要换路径绕过                                                                                                                                                |
| 5   | CLI 未返回 `BYTEDOC_PROD_NETWORK_READ_ONLY`          | **立即停止**，不要取消生产网 profile、切域名或改走 DMS/DBW                                                                                                                  |
| 6   | 权限 role 来自固定枚举                               | **展示枚举让用户选**，不要猜 `write`/`rw`                                                                                                                                   |

**硬性约束：同一类错误不得通过切换 backend、site 或 role 反复重试。收到 AMBIGUOUS/STOP 后只接受用户的明确选择。**

---

## AI Agent 决策树

```text
用户请求到达
│
├─ 1. site 已知？
│   ├─ 否 → 🛑 立即询问（展示 site 选项表）→ 拿到 site 后继续
│   └─ 是 ↓
│
├─ 2. 用户意图是基本信息/详情/库信息？
│   ├─ 是，用户给的是裸 dbName：
│   │     bytedcli --json --site <site> bytedoc get --db-name "<dbName>"
│   │     → 让 CLI resolver/static_info 解析唯一 backend/vregion；不要先 search，不要问 backend
│   ├─ 是，用户给的是完整 PSM/service：
│   │     bytedcli --json --site <site> bytedoc get --service "<service>"
│   │     → 唯一则直接展示；多候选时再展示候选让用户选
│   └─ 否 ↓
│
├─ 3. backend/vregion/service 是否已经完整？
│   ├─ 是：site + backend + vregion + service 已由用户提供，且目标命令是 resolver-backed
│   │     → 直接执行目标命令并显式携带 selector；不要为了重复确认而单独执行 `bytedoc search`
│   └─ 否 ↓
│
├─ 4. 搜索/解析目标（确认 backend + vregion 唯一性）
│   │   若用户已给 backend：
│   │     bytedcli --json --site <site> bytedoc search --keyword "<PSM或关键词>" --backend <backend>
│   │   若用户已给 vregion：
│   │     bytedcli --json --site <site> --vregion <vregion> bytedoc search --keyword "<PSM或关键词>"
│   │   若用户未给 backend/vregion：
│   │     bytedcli --json --site <site> bytedoc search --keyword "<PSM或关键词>"
│   │
│   ├─ 唯一候选 → 记录 backend + vregion，后续命令显式携带
│   ├─ BYTEDOC_AMBIGUOUS → 🛑 展示候选表给用户选择
│   ├─ BYTEDOC_ACCESS_REQUIRED → 执行 setup_commands
│   ├─ AUTH_REQUIRED → auth login 后重试
│   └─ 无匹配 → 告知用户，确认关键词/site 是否正确
│
├─ 5. 确定意图类型，执行目标命令（显式带已确认 selector；resolver 唯一时不需要用户补 backend）
│   ├─ 搜索候选       → bytedoc search
│   ├─ 查看详情       → bytedoc get
│   ├─ 读写文档       → bytedoc shell / document list|insert|update
│   ├─ 权限申请/检查  → IAM 用 access role|permission|user；PSM/token 用 access psm
│   ├─ SDK 原子能力   → bytedoc sdk plan / generate / doctor
│   ├─ 跑通 SDK demo  → 加载 sdk-bootstrap/GUIDE.md，执行 bytedoc sdk bootstrap execute
│   ├─ 慢查询诊断    → bytedoc slow-query overview / detail / index-recommend
│   ├─ 索引治理      → bytedoc index list/task list/task get/create（create 必须 dry-run 后确认）
│   └─ 一站式治理流程 → 加载 `playbooks/GUIDE.md` 串联原子能力和用户阶段门禁
│
└─ 6. 响应用户
```

**关键：不要把缺 backend 当成必须问用户。一个 site 下如果 CLI resolver 能从 `dbName` 或 service PSM 证明唯一目标，就直接使用解析出的 backend/vregion；只有返回 `BYTEDOC_AMBIGUOUS`、多条候选或 `agent_protocol.next_state=ASK_USER` 时才让用户选择。用户已提供的 `backend` / `vregion` 必须保留到首条解析命令和后续命令中，首条解析或目标命令都不得丢弃用户已经明确给出的 `backend` 或 `vregion`。**

---

## DO / DON'T

| 场景                                                                                                                             | ✅ DO                                                                                                                                                                                                                                                                                                                                                                                                                 | ❌ DON'T                                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 用户未提供 site                                                                                                                  | 立即询问，给出选项表                                                                                                                                                                                                                                                                                                                                                                                                  | 假设 `cn` 或从上下文猜测                                                                                                                                                                                                        |
| 用户说"查/看 xxx 库基本信息/详情"                                                                                                | 先确认 site；裸库名用 `bytedoc get --db-name "<db>"`，完整 PSM 用 `bytedoc get --service "<psm>"`，让 CLI resolver 返回唯一 backend/vregion                                                                                                                                                                                                                                                                           | 先跑 `search --keyword`，把裸库名改写成 PSM，或先问用户 backend 是 classic/cloud-native/volc                                                                                                                                    |
| 用户说"搜一下 xxx" 或要求候选                                                                                                    | 用 `bytedoc search --keyword "<keyword>"` 展示候选；唯一候选才进入后续操作                                                                                                                                                                                                                                                                                                                                            | 把 search 当成详情查询，或用 search 空结果否定 `get --db-name` 可查的 classic 库                                                                                                                                                |
| 用户只说 `mongo` / `MongoDB` / Mongo 库、集合、文档、慢查询、索引或连接                                                          | 按 ByteDoc 目标处理，先确认 site，再走 ByteDoc resolver/集合/文档/慢查询/SDK 链路                                                                                                                                                                                                                                                                                                                                     | 因为没有出现 `ByteDoc` 字样就跳到 DMS、RDS 或通用数据库 skill                                                                                                                                                                   |
| 首次执行命令                                                                                                                     | 先解析 backend/vregion；用户已给 backend/vregion 时原样带入解析命令，唯一后显式带入后续命令                                                                                                                                                                                                                                                                                                                           | 猜一个 `--backend classic` 加上去，或丢弃用户已给的 `--backend` 做无过滤搜索                                                                                                                                                    |
| CLI 返回 BYTEDOC_AMBIGUOUS                                                                                                       | 原样展示候选表格，问用户选哪个                                                                                                                                                                                                                                                                                                                                                                                        | 从候选中自行挑选一个执行                                                                                                                                                                                                        |
| CLI 返回 BYTEDOC_ACCESS_REQUIRED                                                                                                 | 执行 `error.details.setup_commands`                                                                                                                                                                                                                                                                                                                                                                                   | 换一个 backend 或 site 重试                                                                                                                                                                                                     |
| CLI 返回 `BYTEDOC_NOT_FOUND` 且 `agent_protocol.next_state=ASK_USER`                                                             | 停止并让用户确认 service/site/backend/vregion                                                                                                                                                                                                                                                                                                                                                                         | 改 keyword、去掉 backend、直接 shell 或换 vregion 试错                                                                                                                                                                          |
| CLI 返回 `BYTEDOC_SCHEMA_ERROR`                                                                                                  | 报告 endpoint、failedSources/request context，遵循 STOP                                                                                                                                                                                                                                                                                                                                                               | 去掉 `--backend`、改 keyword、直接 shell 绕过路由                                                                                                                                                                               |
| `bytedoc search` 返回 `databases=[]` 但 `sourceTotal>0`、`usableCandidateCount=0` 或 `agentProtocol.reason=no_usable_candidates` | 说明搜索没有给出可执行候选；如果用户要基本信息且给的是裸 dbName，改走同 site 的 `bytedoc get --db-name`；否则让用户确认拼写/site                                                                                                                                                                                                                                                                                      | 猜 `--backend volc`、切 vregion、把裸 dbName 拼成 PSM、或连续尝试 classic/cloud-native/volc；不要把裸 dbName 改写成 PSM                                                                                                         |
| CLI 返回 `BYTEDOC_UNSUPPORTED_SITE`，且 `details.site` 是 `us-ttp` 或 `eu-ttp`                                                   | 告知用户 US-TTP / EU-TTP 不支持 DMS 数据查询，遵循 `agent_protocol.next_state=STOP`                                                                                                                                                                                                                                                                                                                                   | 猜 dc、换 DMS endpoint、切 backend/vregion 后重试                                                                                                                                                                               |
| i18n-bd / Asia-SouthEastBD DMS 返回 `BYTEDOC_UNSUPPORTED_SITE`                                                                   | 告知用户该区域 classic/cloud-native DMS 当前不支持，遵循 `agent_protocol.next_state=STOP`；搜索、详情、IAM 和 Volc/DBW 不受该限制                                                                                                                                                                                                                                                                                     | 不要重试、猜 dc、改 endpoint、切 backend/vregion                                                                                                                                                                                |
| CLI 返回 BYTEDOC_DMS_ERROR / BYTEDOC_PLATFORM_SCHEMA_ERROR                                                                       | 报告 stage/endpoint/request_id，遵循 `agent_protocol.next_state=STOP`                                                                                                                                                                                                                                                                                                                                                 | 原命令重试、改用 `document update` / `shell updateOne` 等同类 Mongo 变体、切 backend/vregion、猜库名或发起权限申请                                                                                                              |
| CLI 返回 HTTP 400/500 错误                                                                                                       | 读取结构化错误信息，按错误码处理                                                                                                                                                                                                                                                                                                                                                                                      | 猜测"可能是权限问题"并跳到 access 流程                                                                                                                                                                                          |
| SDK 接入已知 caller PSM                                                                                                          | 先完成 `access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）判定 caller PSM 在目标库上的当前授权；若 target/backend/vregion 尚未确认唯一，先走 resolver/search                                                                                                                                                                                         | 直接用 `permission get`、`role list` 或 `ticket create` / `psm create` dry-run 当作 caller PSM 已授权/未授权的证据                                                                                                              |
| SDK 接入已知 caller PSM 但 caller 运行网络未知                                                                                   | `sdk plan` 和 `sdk generate` 都显式携带 `--caller-psm <caller.psm>`；不带 `--runtime-network` 运行 plan，让 CLI 返回 `supportStatus=needs_input` 后停止并询问用户确认 caller TCE/FaaS 运行网络                                                                                                                                                                                                                        | 不要把目标库的 site/vregion/搜索页/VDC 当作 `--runtime-network`，也不要因为目标库在 eu-ttp 就猜 caller runtime-network 是 eu-ttp；BOE 目标为 `US-BOE`/`boei18n` 时，caller 只确认 `boe` 仍不够，必须确认是否同为 `boei18n` 分区 |
| 用户说"写权限"                                                                                                                   | 展示 PSM role 和 IAM role 两类选项让用户确认                                                                                                                                                                                                                                                                                                                                                                          | 直接用 `--roles write`                                                                                                                                                                                                          |
| 用户未提供 collection                                                                                                            | 先用 `bytedoc collections` 列出可用集合                                                                                                                                                                                                                                                                                                                                                                               | 猜 collection 名                                                                                                                                                                                                                |
| 命令成功但 data 为空，且 CLI 已确认 collection 存在                                                                              | 告诉用户"该条件下没有匹配数据"                                                                                                                                                                                                                                                                                                                                                                                        | 未确认 collection 存在时直接断言为空，或切 backend 重试                                                                                                                                                                         |
| Mongo `collection create`、`document insert/update`、`shell updateOne` 等写入与变更                                              | 先运行不带 `--execute` 的命令获取 CLI dry-run 确认预览，展示 `confirmation.reviewTable` 和以“注意：”开头的 `confirmation.warning`；如果需要在 dry-run 前基于只读查询自行生成业务预览并询问用户，确认问题里也必须完整展示同一句“注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。”；用户明确确认后才追加 `--execute --yes-i-understand-agent-write-risk` 执行 | 首次命令直接带执行 flag，跳过 CLI 确认预览，或在失败后换 `shell` / `document` 变体绕过；向用户询问写入确认时省略风险提示                                                                                                        |
| ByteDoc access 写操作                                                                                                            | 先走 dry-run 预览，展示 review table，等用户确认                                                                                                                                                                                                                                                                                                                                                                      | 直接提交授权/工单                                                                                                                                                                                                               |
| classic 建索引                                                                                                                   | 先走 `bytedoc index create` dry-run，展示 payload/workflow/collection/keys，等用户确认后再追加 `--execute --yes-i-know-this-is-live`                                                                                                                                                                                                                                                                                  | 直接调用 index_manager 回调口、用 classic DMS `createIndex/createIndexes/ensureIndex`，或首次命令直接 live                                                                                                                      |
| Volc/火山版 建索引                                                                                                               | 加载 `mongo-ops/GUIDE.md`，通过 DBW 路径运行不带 `--execute` 的 `bytedoc shell --backend volc --query 'db.<collection>.createIndex(...)'` 获取写入确认预览；用户确认后才追加 `--execute --yes-i-understand-agent-write-risk`                                                                                                                                                                                          | 改走 `bytedoc index create` 工单，或套用 classic DMS 的 `BYTEDOC_INDEX_CREATION_REQUIRES_BPM` 处理                                                                                                                              |
| 慢查询索引推荐到治理                                                                                                             | 从慢查结果主动推进治理时加载 `playbooks/GUIDE.md`；先完成慢查证据摘要并询问用户是否进入索引治理阶段，确认后才生成候选索引和 `index create` dry-run                                                                                                                                                                                                                                                                    | 慢查结果一出来就直接跑 `index create` dry-run，或跳过 dry-run 提交工单                                                                                                                                                          |
| `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`                                                                                            | 停止，改用 `bytedoc index create` dry-run 生成 BPM 工单预览                                                                                                                                                                                                                                                                                                                                                           | 换 `shell --query-file`、DMS direct helper 或脚本继续执行 `createIndex/createIndexes/ensureIndex`                                                                                                                               |
| `BYTEDOC_UNSAFE_OPERATION_BLOCKED`                                                                                               | 停止，告知用户被拦截                                                                                                                                                                                                                                                                                                                                                                                                  | 换 BOE/DMS/DBW/脚本绕过                                                                                                                                                                                                         |

---

## 端到端示例：从零开始查询一个数据库

```text
用户："帮我查一下 order_service 这个库最近的订单"

Agent 内部决策：
  → site 未知 → 必须先问
```

**Agent → 用户：** "请确认目标站点（site）：cn / boe / i18n-bd / i18n-tt / us-ttp / eu-ttp"

```text
用户："cn"

Agent 内部决策：
  → site=cn 已确认
  → backend/vregion 未知 → 必须先搜索解析
```

```bash
# 步骤 1：查看库详情时，裸库名直接走 get --db-name
bytedcli --json --site cn bytedoc get --db-name "order_service"
# → 返回 ref.backend/ref.vregion/ref.service 和库详情
```

```text
Agent 内部决策：
  → CLI resolver 已唯一解析：backend=classic, vregion=China-North
  → 后续命令显式携带这两个参数
```

```bash
# 步骤 2：列出集合
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.order_service" --backend classic
# → ["orders", "users", "payments"]

# 步骤 3：查询文档（用户关心 "最近的订单"）
bytedcli --json --site cn --vregion China-North bytedoc shell --service "example.bytedoc.order_service" --backend classic --collection "orders" --query 'find({}).sort({"created_at":-1}).limit(5)'
# → 返回最近 5 条订单文档
```

**Agent → 用户：** 展示查询结果。

---

## 调用方式

- 默认命令前缀：`bytedcli`。
- 自动化场景使用结构化输出：`--json` 放在 `bytedoc` 前，例如 `bytedcli --json bytedoc search --keyword demo_orders`。
- 全局路由参数放在 `bytedoc` 前：`--site`、`--vregion`。
- 自动化或 traced wrapper 场景中，wrapper 只是替换 `bytedcli` 二进制；固定模板是 `<bytedcli-or-wrapper> --json --site <site> [--vregion <vregion>] bytedoc <subcommand> ...`。
- `--json`、`--site`、`--vregion` 都是全局参数，必须放在 `bytedoc` 前，不要追加到 `document list`、`collections`、`shell` 等子命令之后。
- 如果命令会被 wrapper 记录到 trace，只把真实业务命令交给 wrapper；不要通过 wrapper 执行 `--help`。需要确认命令形态时，读本 skill/guide 或父层提供的执行协议。
- 如果需要登录，针对目标站点执行 `bytedcli auth login`。

## Agent 协议

- 成功的 access 预览使用 camelCase：`agentProtocol` 和 `agentProtocol.nextState`。
- 错误详情使用 snake_case：`agent_protocol` 和 `agent_protocol.next_state`。
- `safeToExecuteAutomatically=false` → 获得用户决策前必须停止自动化执行。
- `requiresUserConfirmation=true` → 渲染 review table 并请求用户明确确认。
- `nextState=COLLECT_REQUIRED_FIELDS` → 向用户补齐 CLI 返回的缺失字段。
- `next_state=RUN_SETUP_COMMANDS` → 先执行或展示 `setup_commands`。
- `next_state=ASK_USER` → 🛑 用户消歧。
- `next_state=STOP` → 🛑 不要重试，不要绕路。
- `site=us-ttp|eu-ttp` 的 classic/cloud-native DMS 数据面命令返回 `BYTEDOC_UNSUPPORTED_SITE` 是终止态；说明 US-TTP / EU-TTP 不支持 DMS 查询，不要继续猜 dc、endpoint、backend 或 vregion。搜索、详情、IAM 等控制面能力不受该限制。
- `i18n-bd / Asia-SouthEastBD` 的 classic/cloud-native DMS 数据面当前不支持，CLI 在 DMS 请求前返回 `BYTEDOC_UNSUPPORTED_SITE` 和 `agent_protocol.next_state=STOP`。显式、配置或默认选中该区域（含既有别名）均需停止并报告限制，不要重试、猜 dc、改 endpoint 或切 backend/vregion。该限制不影响搜索、详情、IAM、Volc/DBW，也不表示 `Asia-CIS` / `US-EastBD` 不支持。
- `BYTEDOC_SCHEMA_ERROR`、`BYTEDOC_DMS_ERROR` 和 `BYTEDOC_PLATFORM_SCHEMA_ERROR` 都是终止态；报告结构化详情，不要通过去掉 backend、切换 backend/vregion、改 keyword、直接 shell、改用 `document update` / `shell updateOne` 等同类 Mongo 变体或申请权限来绕过。
- SDK 接入中，`--runtime-network` 描述 caller TCE/FaaS 所在运行网络，只能来自用户确认的 caller 运行环境证据；不要用目标库 site/vregion/搜索页/VDC 反推 `--runtime-network`。允许值：`boe|boei18n|cn|i18n-bd|i18n-tt|us-ttp|eu-ttp`。如果 caller 运行网络未知，先执行带 `--caller-psm <caller.psm>` 但不带 `--runtime-network` 的 `sdk plan`；当返回 `supportStatus=needs_input` 时必须停止并询问用户。
- BOE 分区必须单独确认：目标库 `site=boe` 且 `vregion=US-BOE`/`boei18n` 时，`--runtime-network boe` 只说明 BOE 运行环境，不足以证明 caller 在 US-BOE/boei18n 分区；必须让用户确认 caller TCE/FaaS VRegion，确认同为 US-BOE/boei18n 后才用 `--runtime-network boei18n` 继续。
- 已知 caller PSM 时，`sdk plan` 和 `sdk generate` 都显式携带 `--caller-psm <caller.psm>`，用于把接入方案、代码素材和后续权限检查绑定到同一个调用方上下文。
- `--engine-version 4.0|8.0` 只用于唯一目标缺少引擎版本元数据、且已有明确版本证据的场景；元数据已有版本时不要传。`BYTEDOC_SDK_ENGINE_VERSION_CONFLICT` 是停止信号，不能覆盖平台事实。
- SDK 接入或连接排障中，只要用户给出 caller PSM 和目标库，权限状态必须来自 `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）。`bytedoc access permission get` 只说明当前操作者是否具备发起授权的前置权限，不能证明 caller PSM 已授权；先完成带目标选择器的 `access psm list`，再根据 `accountCheck.status` 决定是否准备 `ticket create` / `psm create` dry-run。
- `resources.agent.json.databases.*` 的 map key 是测试/执行资源别名，不是真实 service PSM。永远不要把 `cnVolc4` 这类 alias 传给 `--service`；真实 service 只能来自 `databases.<alias>.service` 或用户明确给出的 PSM。
- `resources.agent.json.databases.*.siteArgs` 是全局路由参数片段；拼接命令时必须放在 `bytedoc` 前，不能放到业务子命令后。

## 不可违背的规则

- `classic`、`cloud-native`、`volc` 是三个独立 backend。`volc` 是 DBW / Volc Mongo，不是 cloud-native。
- `deployMode` 是历史两态元数据：`classic|cloud-native`。严格消歧使用 `--backend classic|cloud-native|volc`。
- 搜索 Volc 时，如果用户没有明确指定 `--vregion`，优先使用 `bytedoc search --backend volc` 让 CLI 扩展到站点已知的 Volc 候选 vregion；后续目标操作仍要保留已确认的唯一 vregion。
- 授权和写入场景中，`site`、权限枚举、backend 和 vregion 都必须已确认；不允许用 classic 或任意 vregion 作为隐式默认值。
- ByteDoc access 写操作必须先 dry-run。展示 `confirmation.reviewTable`、`payload`、`missingFields` 和 `nextActions`；不要展示隐藏执行材料。
- ByteDoc Mongo 写入与变更命令（`collection create`、`document insert/update`、写入型 `shell`）必须先 dry-run。展示 `confirmation.reviewTable` 和 `confirmation.warning`，其中 warning 必须完整包含：`注意：写入与变更相关功能仅建议在测试库使用。Agent 幻觉可能导致误操作，若用于生产环境，风险由用户自行承担。` 如果 Agent 基于只读查询自行生成写入预览并向用户确认，确认问题里也必须完整展示这句注意提示；用户明确确认后，Agent 才可追加 `--execute --yes-i-understand-agent-write-risk` 重新执行；不要要求用户复制执行命令。
- ByteDoc 索引创建工单必须先 dry-run。dry-run 也会读取 BPM workflow config 来确认 workflow 正确，因此需要对应 BPM 读权限；若这里返回 403，按 BPM 权限/登录问题处理，不要误判为已提交失败。展示 `payload.workflowConfigId`、`payload.region`、`payload.config`、`confirmation.requiredReview` 和 `nextActions`；用户明确确认后才运行带 `--execute --yes-i-know-this-is-live` 的命令。双确认 flag 是防误提交和防 workflow 误路由的安全边界，不要简化成单 `--execute`。
- 不要向用户暴露 `agentProtocol.doNotDisplay` 中列出的隐藏执行字段。
- Volc PSM 授权真源是 ByteDoc multi-cloud account 数据，不是 classic IAM role bindings 或 BPM ticket 历史。

---

## 按需加载指南

业务代码 review、提交前检查、MR diff 中的 ByteDoc/Mongo 用法审查：加载 `code-review/GUIDE.md`。发现业务查询后列出库和集合信息，请用户确认并授权读取真实线上元数据，结合现有索引判断慢查隐患。确认索引不匹配后给出候选索引并询问是否续接治理，第一次同意只授权 dry-run。

| 用户意图或错误                                                                                                                | 下一步加载                                                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 搜索/列表/详情、backend 歧义、site/vRegion、DMS/DBW 路由                                                                      | `routing/GUIDE.md`                                                                                                                                |
| 集合查看、Mongo shell 查询、文档 list/insert/update、危险操作拦截                                                             | `mongo-ops/GUIDE.md`                                                                                                                              |
| `BYTEDOC_ACCESS_REQUIRED`、角色选项、权限预检、PSM/IAM 授权                                                                   | `access-workflows/GUIDE.md`                                                                                                                       |
| SDK 接入计划、多语言 SDK 素材、Volc 开发账号密码查询/申请、SDK 连接/鉴权/网络失败                                             | `sdk-access/GUIDE.md`                                                                                                                             |
| 跑通 ByteDoc SDK demo、本地起 Go 项目、DevBox 或 TCE 端到端验证                                                               | `sdk-bootstrap/GUIDE.md`；先展示完整路线图并一次性收集资源，再执行 `bytedoc sdk bootstrap execute`                                                |
| 慢查询 overview/detail/metrics/index recommend                                                                                | `slow-query/GUIDE.md`；成功后如需治理文档，模板见 `slow-query/governance.md`                                                                      |
| 索引列表、索引创建/删除/TTL 修改状态、经典版创建索引工单、慢查询推荐到建索引治理                                              | `index-governance/GUIDE.md`                                                                                                                       |
| 慢查分析到建索引、权限申请到接入跑通等跨原子能力的一站式流程                                                                  | `playbooks/GUIDE.md`                                                                                                                              |
| classic 集群水位巡检（cpu/config-cpu/config-connections/qps/mongos-connections/io/cache-bandwidth/disk/doc-size，或整体 all） | `inspect/GUIDE.md`                                                                                                                                |
| 错误码分诊与常见失败恢复                                                                                                      | `troubleshooting/GUIDE.md`                                                                                                                        |
| ByteDoc SDK 素材确定后的 MongoDB client/query/schema 质量优化                                                                 | `mongodb-connection/GUIDE.md`、`mongodb-natural-language-querying/GUIDE.md`、`mongodb-query-optimizer/GUIDE.md`、`mongodb-schema-design/GUIDE.md` |

---

## 命令速查（参考区）

```bash
# 搜索候选：仅当用户要求搜索/候选，或目标操作确实需要先展示候选时使用
bytedcli --json --site cn bytedoc search --keyword "demo_orders"

# 查看详情：裸 dbName 直接用 get --db-name；完整 PSM 用 get --service
bytedcli --json --site cn bytedoc get --db-name "demo_orders"
bytedcli --json --site cn bytedoc get --service "example.bytedoc.demo_orders"

# Mongo 读取链路
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.demo_orders" --backend classic
bytedcli --json --site cn --vregion China-North bytedoc document list --service "example.bytedoc.demo_orders" --backend classic --collection "demo_items" --limit 10

# 授权发现与 dry-run 预览
bytedcli --json --site cn --vregion China-North bytedoc access role list --service "example.bytedoc.demo_orders" --backend classic
bytedcli --json --site cn --vregion China-North bytedoc access permission get --service "example.bytedoc.demo_orders" --backend classic --role-name "bytedoc.data_reader.cn"
bytedcli --json --site cn --vregion China-North bytedoc access psm list --service "example.bytedoc.demo_orders" --backend classic --account "example.caller.psm"
bytedcli --json --site cn --vregion China-North bytedoc access ticket create --service "example.bytedoc.demo_orders" --backend classic --account "example.caller.psm"

# SDK 计划与诊断
bytedcli --json --site cn --vregion China-North bytedoc sdk plan --service "example.bytedoc.demo_orders" --backend classic --access-env auto --language go
bytedcli --json --site cn --vregion China-North bytedoc sdk plan --service "example.bytedoc.demo_orders" --backend classic --access-env tce --caller-psm "example.caller.psm" --language go
# 若 supportStatus=needs_input，停止并询问 caller runtime-network；不要把目标库 site/vregion/搜索页推成 --runtime-network
# 仅当唯一目标缺少引擎版本元数据且已有明确证据时，才为 sdk plan/generate/bootstrap 补 --engine-version 4.0|8.0
# --language 支持 go|python|java|nodejs|cpp（默认 go），sdk generate 同理
bytedcli --json --site cn --vregion China-North bytedoc sdk generate --service "example.bytedoc.demo_orders" --backend classic --access-env tce --runtime-network cn --caller-psm "example.caller.psm" --language go --collection "demo_items" --operation find-one
bytedcli --json --site cn --vregion China-North bytedoc sdk doctor --service "example.bytedoc.demo_orders" --backend classic --caller-psm "example.caller.psm" --error-text "not authorized on demo_orders"

# 慢查询
bytedcli --json --site cn --vregion China-North bytedoc slow-query overview --service "example.bytedoc.demo_orders" --backend classic

# 索引治理：查询索引、查询创建状态、创建索引工单 dry-run
bytedcli --json --site cn --vregion China-North bytedoc index list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items"
bytedcli --json --site cn --vregion China-North bytedoc index task list --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --operation create --status doing --collection "demo_items"
bytedcli --json --site cn --vregion China-North bytedoc index task get --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --ticket-id 24680
bytedcli --json --site cn --vregion China-North bytedoc index create --service "example.bytedoc.demo_orders" --backend classic --db-name "demo_orders" --collection "demo_items" --keys-json '{"tenant":1,"createdAt":-1}' --name "tenant_1_createdAt_-1"
# classic 集群水位巡检（仅 classic；--metric 选单项或整体，默认 all）
bytedcli --json --site cn bytedoc inspect cluster get --cluster 240085
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085 --metric cpu
bytedcli --json --site cn bytedoc inspect cluster check --cluster 240085
bytedcli --json --site cn bytedoc inspect cluster check --service "example.bytedoc.demo_orders" --backend classic --metric disk
```

## 参考资料

- `references/bytedoc.md`：更完整的命令矩阵。
- `references/selection-guards.md`：backend、site、区域和权限枚举的执行前澄清门禁。
