# ByteDoc 路由指南

当任务涉及数据库搜索、backend 消歧、site/vRegion 行为，以及 DMS/DBW 数据面路由时，使用本指南。

## 首屏规则

- 先按 `../references/selection-guards.md` 确认 `site`，再解析 backend/vregion；不要猜默认 backend 或 vregion。
- 用户请求"基本信息"、"详情"、"库信息"时，`bytedoc get` 是目标命令，不是 `bytedoc search`。裸库名直接执行 `bytedoc get --db-name "<dbName>"`，完整 PSM/service 直接执行 `bytedoc get --service "<service>"`；让 CLI resolver/static_info 解析唯一 backend/vregion，不要先问用户 backend。
- 首次搜索不要发明 backend 或 vregion；但用户已明确提供的 `backend` / `vregion` 必须原样保留到首条搜索命令中。只有用户未提供 backend/vregion 时，才只传 `--site` + keyword/service。
- 如果 site + backend + vregion + service 已由用户完整提供，且下一步是 `collections`、`document list`、`shell`、`get`、`sdk plan` 这类 resolver-backed 目标命令，直接执行目标命令并保留全部 selector；不要为了重复确认而单独执行 `bytedoc search`。
- 自动化或 traced wrapper 场景中，wrapper 只是替换 `bytedcli` 二进制；固定模板是 `<bytedcli-or-wrapper> --json --site <site> [--vregion <vregion>] bytedoc <subcommand> ...`，全局参数必须放在 `bytedoc` 前。
- 如果命令会被 wrapper 记录到 trace，只把真实路由/业务命令交给 wrapper；不要通过 wrapper 执行 `--help`。
- `BYTEDOC_AMBIGUOUS` 或 `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选给用户选择，不要自行挑选。
- `AUTH_REQUIRED` 是认证问题，不是 backend 错误；登录后重试同一条命令。
- `BYTEDOC_NOT_FOUND` 且 `agent_protocol.next_state=ASK_USER` 是当前 selector 下未找到且需要用户确认；停止并询问 service/site/backend/vregion，不要继续 search/shell 变体试错。
- `BYTEDOC_UNSUPPORTED_VREGION` 只表示用户指定的 VRegion 不在当前站点已确认的控制面 endpoint 表中；停止并报告 `details.site` / `details.vregion` / `details.searchPageVregions`，不要去掉 `--vregion`、改用默认区域或切换 site/backend 试错。搜索页可见的 VRegion 应由 CLI 路由到对应控制面，不应触发该错误。
- `BYTEDOC_SCHEMA_ERROR` 表示 ByteDoc 元数据/控制面返回结构不符合 CLI 预期；报告 endpoint、failedSources/request context 后停止，不要去掉 backend、改 keyword 或直接 shell 绕过路由确认。
- `bytedoc search` 返回 `databases=[]` 但 `sourceTotal>0`、`usableCandidateCount=0` 或 `agentProtocol.reason=no_usable_candidates` 时，只说明搜索没有拿到可执行候选；不要把它当成 backend 猜测入口。若用户原意是查库详情且给的是裸 dbName，改走同 site 的 `bytedoc get --db-name`；否则让用户确认关键词/site。
- `resources.agent.json.databases.*` 的 map key 是资源别名，不是真实 service。不要把 `cnVolc4` 这类 alias 传给 `--service`；真实 service 只能来自 `databases.<alias>.service` 或用户明确给出的 PSM。

## Backend 模型

- `backend=classic`：传统 ByteDoc；Mongo 数据面使用 DMS。
- `backend=cloud-native`：cloud-native ByteDoc；Mongo 数据面使用 DMS。
- `backend=volc`：DBW / Volc Mongo；Mongo 数据面使用 DBW。
- `deployMode=classic|cloud-native` 是历史元数据，不能表示 Volc。

## 搜索与候选确认

CLI 搜索用于候选发现和 selector 不完整时的候选展示，不等同于详情查询。用户提供 `--site` 后，如果 backend/vregion 缺失，Agent 需要用搜索结果或 resolver-backed 目标命令确认 backend 和 vregion 是否唯一；其中详情/基本信息请求优先使用 `bytedoc get --db-name` 或 `bytedoc get --service`，让 CLI resolver/static_info 给出唯一 `ref`。用户已提供 `backend=volc` 但缺 vregion 时，首条搜索必须携带 `--backend volc`，这不是猜测参数，而是保留用户约束。显式搜索 `--backend volc` 且未指定全局 `--vregion` 时，CLI 会扩展到站点已知的 Volc 候选 vregion，避免非默认区域漏查。site + backend + vregion + service 已完整时，优先执行用户真正要的 resolver-backed 目标命令，不要额外跑 standalone search。

```bash
# 用户只提供关键词和 site，先搜索候选
bytedcli --json --site cn bytedoc search --keyword "example_db"

# 用户要查裸库名的基本信息，直接走 get --db-name
bytedcli --json --site cn bytedoc get --db-name "example_db"

# 用户给完整 PSM/service 查详情，直接走 get --service
bytedcli --json --site cn bytedoc get --service "example.bytedoc.example_db"

# 用户已确认特定 backend 后，首条搜索必须保留 backend
bytedcli --json --site cn bytedoc search --keyword "example_db" --backend volc

# 海外站点
bytedcli --site i18n-tt --json bytedoc search --keyword "example_db"

# 从生产网络访问 i18n-tt classic 控制面
BYTEDCLI_NETWORK_PROFILE=prod bytedcli --json --site i18n-tt --vregion Singapore-Central bytedoc get --service "example.bytedoc.example_db" --backend classic

# 查看详情（使用已确认 backend/vregion）
bytedcli --json --site cn --vregion China-North bytedoc get --service "example.bytedoc.demo_orders" --backend classic

# 用户已经完整给出 site/backend/vregion/service，直接执行目标命令
bytedcli --json --site boe --vregion boei18n bytedoc collections --service "example.bytedoc.demo_orders" --backend classic
```

- `bytedoc search` 未指定 backend 时会合并 legacy classic、legacy cloud-native 与当前站点支持的 Volc 搜索结果；不要把 Cloud Service Search 当作 classic/cloud-native 的总入口。
- `--backend classic|cloud-native` 只走 legacy 平台搜索；`--backend volc` 走 Cloud Service / DBW 搜索，并可用于扩大 Volc 发现范围。
- i18n-tt 搜索页可见的 classic VRegion 并不都对应独立控制面：`US-East` / `US-SouthWest` 走 Maliva 控制面，`Singapore-Central` / `Singapore-Common` / `Singapore-Compliance` / `EasternEuro-TT` / `Australia-SouthEast` 走 SG 控制面，`Europe-Central` 走 EU 控制面，`ID-Compliance` / `ID-Compliance2` / `MY-Compliance` 走各自合规控制面。用户显式给出 `--vregion` 时必须保留；CLI 会根据搜索结果里的 zone/vdc 推断 VRegion 并过滤共享控制面的混区结果。
- 从生产网络调用 ByteDoc 时设置 `BYTEDCLI_NETWORK_PROFILE=prod`。CLI 会按已确认的 site/vregion/DC 为 i18n-tt classic 控制面选择对应 `*.byted.org` cloud 域名，并把 i18n-tt DMS 数据面切到生产网 ingress `https://fedms-i18n-api.byted.org`；未设置 profile 时仍使用办公网 DMS ingress `https://fedms-i18n-api.byteintl.net`。eu-ttp classic 控制面使用对应 `*.tiktoke.org` cloud 域名；`US-EastRed` / `EU-TTP` / `EU-Compliance` / `EU-Compliance2` / `EU-TTP2` 是 eu-ttp 搜索页唯一归属，即使 legacy 调用传入 `site=i18n-tt` 也会先规范化到 eu-ttp，不能静默落到 SG。该变量不改变 cloud-native 控制面或其他 site 的 DMS endpoint；DMS origin 仍使用站点既有值。生产网 profile 下，`--endpoint` / `BYTEDCLI_BYTEDOC_ENDPOINT` 只有规范化后与当前 canonical classic cloud endpoint 一致时才允许使用；其他 override 返回 `BYTEDOC_PROD_ENDPOINT_OVERRIDE_BLOCKED`，不要借此切回办公网域名。
- 生产网 profile 下 ByteDoc 仅允许只读操作；所有 Mongo、索引、授权、关注等写入或变更意图（包括 dry-run）都会在远端变更前被阻止，通常返回 `BYTEDOC_PROD_NETWORK_READ_ONLY`；全站点已禁用的破坏性操作可能优先返回 `BYTEDOC_UNSAFE_OPERATION_BLOCKED`。收到后停止，不要取消 profile、切换 ByteDoc 域名、改走 DMS/DBW 或换命令形态绕过。
- backend 和 vregion 由 CLI 从搜索结果或 resolver-backed 目标命令中解析；只有 CLI 返回多候选、`BYTEDOC_AMBIGUOUS` 或 `agent_protocol.next_state=ASK_USER` 时，才向用户询问 backend/vregion。
- 当搜索返回多个匹配项或单条匹配包含多个 vregion（`BYTEDOC_AMBIGUOUS`）时，必须让用户选择。
- 只有用户明确要求搜索/查找资源时，才可以用 search 展示候选；候选结果不能替用户自动选择。
- 搜索 JSON 中 `sourceTotal` 表示上游声称的命中数，`usableCandidateCount` 表示 CLI 当前返回的可执行候选数。`sourceTotal>0` 但 `usableCandidateCount=0` 不能证明应该切换 backend/vregion，也不能证明库不存在。

## AI Agent 解析示例

```bash
# 场景：用户说"帮我看一下 example_db 这个库的基本信息"
# Agent 先确认 site，然后直接执行详情命令；不先 search，不问 backend

# Step 1: 裸库名详情
bytedcli --json --site cn bytedoc get --db-name "example_db"

# 如果用户给的是完整 PSM：
bytedcli --json --site cn bytedoc get --service "example.bytedoc.example_db"

# Step 2: 如果 CLI 返回唯一 ref，使用 ref.backend/ref.vregion 继续后续操作
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.example_db" --backend classic
```

```bash
# 场景：用户说"搜一下 example_db"
# Agent 使用 search 展示候选

# 如果用户一开始已经给出 backend=volc，Step 1 必须保留 backend：
bytedcli --json --site cn bytedoc search --keyword "example_db" --backend volc

# 如果用户已完整给出 site + backend + vregion + service，且目标命令是 resolver-backed：
bytedcli --json --site boe --vregion boei18n bytedoc collections --service "example.bytedoc.example_db" --backend classic
# 不要为了重复确认而单独执行 `bytedoc search`

# Step 2: 如果唯一匹配，后续命令显式携带已确认的 --backend / --vregion
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.example_db" --backend classic

# Step 3: 如果 CLI 返回 BYTEDOC_AMBIGUOUS，展示候选表格让用户选择
# 候选表格包含 PSM、backend、vregion 信息
```

## Resolver 规则

- dotted PSM 不能自动推断为 cloud-native。
- CLI resolver 从搜索结果解析 backend 和 vregion；多 backend、多 vregion 或单条多 vregion 都需要用户介入。
- `bytedoc get --db-name` / `bytedoc get --service` 也是 resolver-backed 路径。详情请求中不要为了补 backend 先问用户；先让 CLI 返回唯一 `ref`，只有真实歧义才问。
- 将 `BYTEDOC_AMBIGUOUS` 和 `agent_protocol.next_state=ASK_USER` 视为必须询问用户的硬边界。
- 将 `AUTH_REQUIRED` 视为认证问题，不要把它当成尝试其他 backend 的证据。
- 将 `BYTEDOC_NOT_FOUND` 视为确定的否定结果，除非用户提供新的 selector；如果错误里已有 `agent_protocol.next_state=ASK_USER`，下一步只能询问用户，不得执行新的自动命令。
- 将 `BYTEDOC_UNSUPPORTED_VREGION` 视为控制面路由未确认，下一步只能报告缺失 endpoint 或让用户提供已支持的 VRegion；不得移除用户指定的 `--vregion` 继续搜索。若该 VRegion 出现在 ByteDoc 搜索页中，应先修复 CLI endpoint/zone 映射，而不是让 agent 回退默认区。
- 将 `BYTEDOC_SCHEMA_ERROR` 视为控制面/schema 失败，下一步只能报告错误上下文或等待平台/CLI 修复，不得移除 `--backend`、切换 backend/vregion、改 keyword、直接 shell 或使用资源别名继续试错。

## Site 与 DMS 规则

- DMS 必须使用已解析目标的 `site` / `vregion` 对应的 JWT、origin、referer 和 endpoint；如果 resolver 已返回唯一 vregion，即使用户没有显式传全局 `--vregion`，DMS 数据面也必须使用该 vregion。
- BOE DMS API host 是 `https://fedms-boe-api.byted.org`；origin 是 `https://dms-boe.bytedance.net`。
- BOE-I18N / US-BOE DMS API host 是 `https://fedms-boe-i18n-api.byted.org`；origin 是 `https://dms-boe-i18n.bytedance.net`。
- i18n-bd DMS API host 是 `https://fedms-api.byteintl.net`；origin 是 `https://dms.byteintl.net`。
- i18n-tt DMS API host 按网络 profile 选择：办公网使用 `https://fedms-i18n-api.byteintl.net`，`BYTEDCLI_NETWORK_PROFILE=prod` 使用 `https://fedms-i18n-api.byted.org`；两者的 origin 都是 `https://dms-i18n.byteintl.net`。
- US-TTP 与 EU-TTP 不暴露 classic / cloud-native DMS 数据面；CLI 必须在本地返回 `BYTEDOC_UNSUPPORTED_SITE`，不得尝试任何 DMS host/origin。
- `i18n-bd / Asia-SouthEastBD` 的 classic/cloud-native DMS 数据面当前不支持；显式、配置或默认选中该区域时，CLI 在 DMS 请求前返回 `BYTEDOC_UNSUPPORTED_SITE`，按 `agent_protocol.next_state=STOP` 停止并报告限制。既有别名 `Asia-South` / `i18nbd` / `bdsgdt` / `sgsaas1larkidc1`（不区分大小写）同样拦截，不要换别名、dc、endpoint 或 backend/vregion 重试。搜索、详情、IAM 控制面与 Volc/DBW 路径不受该限制。
- DMS `dc` 不是全站点统一规则：CN-East 物理 VDC `jj` / `zjg` / `hj` 使用 `CN_EAST`；CN-North 物理 VDC `hl` / `lq` / `lf` 保持物理 dc；i18n-bd 支持的 DMS 区域使用 `Asia-CIS` / `US-EastBD`；i18n-tt 的 `Singapore-Central` / `US-East` / `Europe-Central` 分别规范化为 `sg` / `us` / `eu`。
- 本节的 generic context 指不带 `dc` 的 subscribe 所产生的 context。DMS evaluate 的 `dc` 与 `dbId` 必须绑定在同一次 subscribe context 中；显式候选 dc 会先按该 dc 重新 subscribe，切换 dc 时也必须重新 subscribe，不能复用 generic subscribe 的 `dbId`。
- no-dc subscribe 返回非空 `region` 时，该 `region` 与同一响应的 `dbId` 保持绑定，resolver 不得覆盖它。仅 CN/BOE 的响应缺少 `region` 时，CLI 可以使用已解析 vregion 作为兼容 fallback；此时仍使用该 generic context 的 `dbId`，不会拼接另一次 subscribe 的 context。
- 候选顺序以 resolver 已确认的目标为先。CN/BOE 的 generic subscribe 可以发现物理 dc，每个物理 dc 都必须显式 subscribe 后再 evaluate；如果物理 dc 不可用，原 generic context 仍可能作为兼容 fallback。支持 DMS 的海外站点先尝试 canonical candidate，再尝试 generic context。候选切换由 CLI 自动完成，Agent 不得手工修改 selector 重试。
- subscribe 阶段遇到候选未命中或连接失败时可以换候选；evaluate 阶段只有语句已被静态证明为只读且发生连接失败时才可以换候选。写入或无法证明只读的语句不得自动重放；不要盲目重试或切换 selector。
- `site=us-ttp|eu-ttp` 当前不支持 classic / cloud-native 的 DMS 数据查询；收到 `BYTEDOC_UNSUPPORTED_SITE` 且 `details.site=us-ttp|eu-ttp` 后停止，不要猜 dc、改 endpoint 或切 vregion。控制面搜索、详情与 IAM 仍按各自 canonical site 路由。
- 海外 classic 查询不要回退到 CN JWT、CN origin 或 `dc=cn`。
- 如果 `BYTEDOC_ROUTING_UNRESOLVED` 说明 region 无法判定，询问路由上下文或停止；不要盲试 CN。

## DO / DON'T

| 场景                                                        | ✅ DO                                                                                             | ❌ DON'T                                                        |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 用户说"搜一下 xxx"，未提供 backend/vregion                  | `bytedcli --json --site cn bytedoc search --keyword "xxx"`，展示候选                              | 不要加猜测的 `--backend` 或 `--vregion`                         |
| 用户说"查/看 xxx 库基本信息"，xxx 是裸库名                  | `bytedcli --json --site cn bytedoc get --db-name "xxx"`，使用返回的 `ref.backend/ref.vregion`     | 不要先 `search --keyword`，不要问用户 classic/cloud-native/volc |
| 用户说"查/看 xxx 库基本信息"，xxx 是完整 PSM                | `bytedcli --json --site cn bytedoc get --service "xxx"`，唯一解析后展示详情                       | 不要把 PSM 拆成裸库名后反复搜索                                 |
| 用户已提供 `backend=volc`                                   | `bytedcli --json --site cn bytedoc search --keyword "xxx" --backend volc`，用结果确认 vregion     | 不要丢掉 `--backend volc` 做无过滤搜索                          |
| site/backend/vregion/service 都已提供，用户要列集合或查文档 | 直接执行 `collections` / `document list` / `shell` 等 resolver-backed 目标命令，保留全部 selector | 不要为了重复确认而单独执行 `bytedoc search`                     |
| 搜索返回 0 条结果                                           | 告诉用户未找到，确认 PSM 拼写或 site                                                              | 不要自动切换 site 或 backend 重试                               |
| 搜索 `sourceTotal>0` 但 `usableCandidateCount=0`            | 说明没有可执行候选；详情意图可改走同 site 的 `get --db-name`，其他意图让用户确认关键词/site       | 不要切 backend/vregion、不要把裸 dbName 改写成 PSM              |
| 搜索返回多条匹配或多个 vregion                              | 展示候选表格让用户选                                                                              | 不要自行挑一个继续执行                                          |
| 返回 NOT_FOUND + ASK_USER                                   | 停止，询问用户确认 service/site/backend/vregion                                                   | 不要改 keyword、去掉 backend、直接 shell 或换 vregion           |
| 返回 SCHEMA_ERROR                                           | 报告 endpoint/failedSources/request context 并停止                                                | 不要把 schema 失败当成未找到后继续变体试错                      |
| 读取 resources.agent.json                                   | 使用 `databases.<alias>.service` 作为真实 service                                                 | 不要把 `databases` 的 map key 当作 `--service`                  |
| 海外站点搜索                                                | 使用 `--site i18n-tt` 等正确 site                                                                 | 不要回退到 `--site cn`                                          |
| 命令返回 AUTH_REQUIRED                                      | `bytedcli auth login` 后重试                                                                      | 不要把认证错误当 backend 错误处理                               |

## 搜索结果为空时的处理

```bash
# 搜索未找到结果
bytedcli --json --site cn bytedoc search --keyword "nonexistent_db"
# → 返回空列表

# Agent 应该：
# 1. 告诉用户"在 cn 站点下未找到该数据库"
# 2. 询问：PSM 拼写是否正确？是否在其他 site（如 boe、i18n-bd）？
# 3. 不要自动尝试其他 site
```
