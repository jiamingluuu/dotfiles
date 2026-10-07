# ByteDoc 选择器与枚举门禁

本文件定义 Agent 在执行 ByteDoc 命令前必须完成的选择器澄清和固定枚举校验。目标是避免 "猜一个参数 -> 命令失败 -> 换参数重试" 的长链路。

## 首屏停止规则

- 缺少 `site`：立即询问，不执行 ByteDoc 命令。
- 缺少 `backend` / `vregion`：不要猜默认值，也不要先问用户猜 backend；先用全站搜索或 resolver-backed 目标命令确认唯一候选，任一维度多值时让用户选择。
- 详情/基本信息请求：裸库名直接用 `bytedoc get --db-name "<dbName>"`，完整 PSM/service 直接用 `bytedoc get --service "<service>"`；这是 resolver-backed 路径，可先执行以获得唯一 `ref.backend/ref.vregion`。
- site + backend + vregion + service 已完整且目标命令是 resolver-backed 时，直接执行目标命令并保留全部 selector；不要为了重复确认而单独执行 `bytedoc search`。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER`：展示候选表格，让用户选择；不要自行挑选。
- role 非法或不完全匹配枚举：展示完整合法值，让用户选择；不要猜 `write`、`rw`、`DML_RW`。
- `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`：立即停止 classic DMS shell 建索引路径；加载 `../index-governance/GUIDE.md`，改用 `bytedoc index create` dry-run / BPM 工单链路。该错误只表示 classic DMS 旁路被禁用；Volc/火山版 建索引应走 DBW `bytedoc shell --backend volc` 的 mongoshell 写入确认流程。
- `BYTEDOC_UNSAFE_OPERATION_BLOCKED`：立即停止；不要换 site/backend、DBW/DMS direct API、query file 或脚本绕过。

## 1. 硬性门禁：Site

以下参数是执行任何 ByteDoc 命令的必备前提，缺失时立即停下来问用户：

| 参数     | 说明                                  | 选项                                                                                                |
| -------- | ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `--site` | 不同 site 使用完全不同的 API 基础设施 | `cn` / `boe` / `i18n-bd` / `i18n` / `i18n-tt` / `us-ttp` / `us-ttp-bdee` / `us-ttp-usts` / `eu-ttp` |

Site 选项含义：

| 选项          | 含义                 | 备注                                        |
| ------------- | -------------------- | ------------------------------------------- |
| `cn`          | 国内生产             | 默认站点，但授权/写入场景仍需用户显式确认   |
| `boe`         | BOE 测试站           | BOE 下可能存在 `China-BOE`、`US-BOE` 等区域 |
| `i18n-bd`     | ByteIntl 国际站      | 通常复用 ByteDance SSO                      |
| `i18n`        | `i18n-bd` 的兼容别名 | 优先向用户推荐 `i18n-bd`                    |
| `i18n-tt`     | TikTok 国际站        | 通常需要 TikTok SSO                         |
| `us-ttp`      | US TTP               | 需要 TTP 路由上下文                         |
| `us-ttp-bdee` | US TTP BDEE          | 需要 TTP 路由上下文                         |
| `us-ttp-usts` | US TTP USTS          | 需要 TTP 路由上下文                         |
| `eu-ttp`      | EU TTP               | 需要 TTP 路由上下文                         |

区域规则：

- `US-BOE` 不是 site 值，它是 `site=boe` 下的区域 / vRegion。
- 用户选择 `boe` 时，可以先只传 `--site boe` 做搜索/解析；如果候选跨 `China-BOE` / `US-BOE`，必须让用户选择。
- 只有用户明确提供区域，或搜索/CLI 返回 `BYTEDOC_AMBIGUOUS` / `BYTEDOC_ROUTING_UNRESOLVED` 时，才让用户选择或补充 vRegion。
- 失败时不得删除 `--site` 或将 BOE 请求回退到 CN。

## 2. 消歧选择器：Backend 与 VRegion

**Backend 和 VRegion 必须在执行目标操作前明确。** 用户可以直接提供；也可以由 CLI 全站搜索/resolver 解析出唯一候选。不要把 `classic` 或任意 vRegion 当默认值。

### Backend 选项

| 选项           | 含义                 | 典型路径                        |
| -------------- | -------------------- | ------------------------------- |
| `classic`      | 传统 ByteDoc         | DMS 数据面、classic 慢查询      |
| `cloud-native` | Cloud Native ByteDoc | DMS 数据面、cloud-native 慢查询 |
| `volc`         | DBW / Volc Mongo     | DBW 数据面、多云 PSM 授权       |

规则：

- `volc` 是独立 backend，不等同于 `cloud-native`。
- `deployMode=classic|cloud-native` 不能表示 `volc`。
- dotted PSM 不能自动推断 backend。
- 当搜索或 CLI 返回多个 backend 时，展示选项让用户选择。

### VRegion

VRegion 由 CLI 从搜索结果中解析。若同一 PSM 存在于多个 VRegion，或单条候选包含多个 VRegion，必须让用户消歧。

## 3. 解析与确认规则

CLI 采用 ByteDoc 发现搜索来解析 backend 和 vregion：classic / cloud-native 候选来自 legacy 平台搜索，Volc 候选来自当前站点支持的 Cloud Service / DBW 搜索。

1. **解析行为**：未指定 backend 时合并当前 site 下 legacy classic、legacy cloud-native 与可用 Volc 搜索结果；用户显式给出的 backend/vregion 必须原样保留。
2. **唯一匹配**：只有当 backend 和 vregion 都唯一时，才可视为目标已明确。
3. **多匹配（BYTEDOC_AMBIGUOUS）**：当同一 PSM 在不同 vregion 或 backend 下存在多个匹配，或单条匹配包含多个 vregion 时，CLI 输出选项表（含 PSM、backend、vregion 列），Agent 必须将此表格展示给用户并让用户选择。
4. **用户显式传入**：用户显式传入 `--backend` 或 `--vregion` 时，CLI 使用指定值过滤，但仍不得自行补默认值。

Agent 行为要求：

- 用户首次提出请求时，先确认 `site` + PSM/dbName；详情/基本信息请求优先执行 `bytedoc get --db-name` 或 `bytedoc get --service`，其它候选发现或不明确目标再执行 `bytedoc search` 或具备 resolver 的目标命令确认候选唯一性。
- site + backend + vregion + service 已完整且目标命令是 resolver-backed 时，直接执行目标命令；不要为了重复确认而单独执行 `bytedoc search`。
- 如果解析出唯一候选，记录 backend/vregion，后续数据面、授权、写入、SDK、慢查询命令显式携带 `--backend`，并在已确认 vregion 时携带全局 `--vregion`。
- 如果返回 `BYTEDOC_AMBIGUOUS`，将候选表格展示给用户，让用户选择后补充 `--backend` 和/或全局 `--vregion` 重新执行。

## 4. PSM 授权 role 选项

`bytedoc access psm create --roles` 只能使用下列值；用户说"写权限"时不能映射成 `write`：

| 选项                 | 含义                   |
| -------------------- | ---------------------- |
| `read`               | 只读                   |
| `readWrite`          | 读写                   |
| `readWriteNoDrop`    | 读写但不允许 drop      |
| `dbOwner`            | DB owner               |
| `dbOwnerNoDrop`      | DB owner 但不允许 drop |
| `enableShardingOnly` | 开分片权限             |

规则：

- 用户给出的权限文本不完全等于上述值时，必须展示完整列表并让用户选择。
- "写权限""读写权限""writer" 只能作为意图提示，不能直接执行。
- `operation=delete` 场景通常不需要新增 role；如果用户仍提供 role，先确认。

## 5. IAM 用户 / 角色权限选项

`bytedoc access user grant|apply|update|revoke --role-name` 使用 IAM role 名称。role kind 固定，region suffix 按 site 的 IAM region 选择：

- `site=cn` / `site=boe` 使用 `.cn`，例如 `bytedoc.data_reader.cn`、`bytedoc.data_writer.cn`。
- `site=i18n-bd` / `site=i18n-tt` 使用 `.i18n`，例如 `bytedoc.data_reader.i18n`、`bytedoc.data_writer.i18n`。
- `site=us-ttp` 以 `access role list` 返回的真实 role 为准；当前已验证默认可选 role 是 `owner.tx`，不要合成或猜 `.cn` / `.i18n` / `.tx` role。
- `site=eu-ttp` 以 `access role list` 返回的真实 role 为准；当前已验证默认可选 role 是 `owner`，不要合成或猜 `.cn` / `.i18n` / `.eu` role。

| 选项                                                  | 适用边界                                                                 |
| ----------------------------------------------------- | ------------------------------------------------------------------------ |
| `bytedoc.data_reader.cn` / `bytedoc.data_reader.i18n` | 查询 / 读取数据，通常用于数据访问读权限                                  |
| `bytedoc.data_writer.cn` / `bytedoc.data_writer.i18n` | 查询 / 修改数据，通常用于数据访问写权限                                  |
| `bytedoc.viewer.cn` / `bytedoc.viewer.i18n`           | 访问 / 操作字节云页面的只读或查看能力                                    |
| `bytedoc.operator.cn` / `bytedoc.operator.i18n`       | 访问 / 操作字节云页面的操作能力                                          |
| `bytedoc.owner.cn` / `bytedoc.owner.i18n`             | ByteDoc 数据库负责人组件权限                                             |
| `owner` / `owner.tx`                                  | IAM 超管 / PSM owner 类官方角色，只有用户明确指定或 CLI 返回该选项时使用 |

规则：

- 不要把 PSM 授权 role（如 `readWrite`）传给 `--role-name`。
- 不要把 IAM role（如 `bytedoc.data_writer.cn`）传给 PSM 授权的 `--roles`。
- 用户说"写权限"时，同时说明可能对应 PSM `readWrite` 或 IAM `bytedoc.data_writer.<cn|i18n>`，让用户先确认授权对象是 PSM 还是 IAM 用户 / 角色。
- `owner` / `owner.tx` 和 `bytedoc.owner.<cn|i18n>` 适用边界不同，必须分别展示，不得合并。
- i18n 站点不要沿用 `.cn` IAM role；否则后端会返回 `role region and iam region not match`。
- US-TTP 站点不要沿用 `.cn` / `.i18n` IAM role；当前真实默认 role 是 `owner.tx`，其它 role 必须来自 `access role list` 返回。
- 不要根据默认枚举或请求参数合成/猜测 role；`role-name` 必须来自 `access role list` 返回的真实 role。

## 6. 错误后停止规则

遇到以下错误时，立即停止猜测并向用户展示正确选项：

- `Invalid ByteDoc access role`
- `ByteDoc access role not found`
- `authorization is not verified for backend`
- `database not found for backend`
- `BYTEDOC_AMBIGUOUS`
- `BYTEDOC_ROUTING_UNRESOLVED`

针对 `BYTEDOC_AMBIGUOUS` 的特殊处理：

- CLI 会返回一个候选匹配表，包含 PSM、backend、vregion 等列。
- Agent 必须将此表格原样展示给用户，让用户选择序号或明确指定参数。
- **不要**自行从候选中挑选一个尝试执行。
- 用户选择后，补充对应的 `--backend` 和/或 `--vregion` 重新执行命令。

同一类 selector 错误不得通过切换 backend、site、role 或 deployMode 反复重试。最多只允许执行用户确认后的下一条命令。

## 7. 澄清问题模板

### 缺少 site 时

```text
请确认目标站点（site）：
cn / boe / i18n-bd / i18n-tt / us-ttp / us-ttp-bdee / us-ttp-usts / eu-ttp
```

### 授权场景需要确认权限类型时

```text
为了避免猜错导致反复失败，请确认以下信息：
1. site：cn / boe / i18n-bd / i18n-tt / us-ttp / us-ttp-bdee / us-ttp-usts / eu-ttp
2. 授权对象：PSM 授权还是 IAM 用户/角色授权？
3. 如果是 PSM 授权，roles 请选择：read / readWrite / readWriteNoDrop / dbOwner / dbOwnerNoDrop / enableShardingOnly
4. 如果是 IAM 授权，role-name 按 site 选择：cn/boe 使用 bytedoc.data_reader.cn / bytedoc.data_writer.cn / bytedoc.viewer.cn / bytedoc.operator.cn / bytedoc.owner.cn / owner；i18n-bd/i18n-tt 使用 bytedoc.data_reader.i18n / bytedoc.data_writer.i18n / bytedoc.viewer.i18n / bytedoc.operator.i18n / bytedoc.owner.i18n / owner；us-ttp 以 access role list 返回的 owner.tx 等真实 role 为准；eu-ttp 以 access role list 返回的 owner 等真实 role 为准，不要猜 role
```

### 遇到 BYTEDOC_AMBIGUOUS 时

```text
CLI 发现多个匹配的数据库，请从以下选项中选择：
[展示 CLI 返回的候选表格]
请告诉我您要操作的是哪一个（输入序号或明确指定 --backend / --vregion）。
```

注意：backend 和 vregion 不应凭空询问或猜默认值；应先搜索/解析候选，只有唯一候选才能继续，否则让用户选择。

## 8. AI Agent 行为速查

### 最常见的错误路径（避免！）

1. **错误使用搜索**：用户只要查裸库名基本信息，Agent 先 `search --keyword`，再按空搜索结果猜 backend/vregion → 正确做法：直接 `get --db-name`，让 CLI resolver/static_info 返回唯一 ref
2. **猜测 backend**：Agent 看到 PSM 名字就猜 `--backend classic` → 正确做法：用搜索结果或用户选择决定 backend
3. **猜测 role**：用户说"写权限"，Agent 直接用 `--roles write` → 正确做法：展示枚举让用户选
4. **收到错误后自行切换参数**：返回 AMBIGUOUS 后 Agent 自己选一个 → 正确做法：展示候选让用户选
5. **绕过安全拦截**：UNSAFE_OPERATION_BLOCKED 后换路径重试 → 正确做法：停止并说明

### 正确的最小路径

```text
用户请求 → 确认 site → 搜索/解析候选 → backend/vregion 唯一则显式带入后续命令；多值则让用户选择
```

这是所有 ByteDoc 操作的通用入口。无论是搜索、查询、授权还是 SDK 接入，都遵循同一模式。
