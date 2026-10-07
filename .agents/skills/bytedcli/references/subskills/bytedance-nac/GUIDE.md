---
name: bytedance-nac
description: "Use bytedcli for NAC, Network Access Control, 网络隔离, user-rule/MGT Rule/用户规则, user-ticket/NAC Ticket/用户工单, HFW/微隔离/监控/集群/Agent/Bypass, rulePlatform/规则平台, NSG rule_type/规则类型, 规则检索/模糊匹配/精确匹配/冲突检查, 编译后规则/下发到数据面, 规则下发状态/下发阶段/未生效诊断, ES 日志采集配置, NAC 审计日志, Yunque Rule/管理员规则, Gray Rule/灰度规则, Yunque 管理工单, NSG 匹配 Agent/运行参数/集群名, Matrix Rule, admin Dialtest/拨测任务/拨测 Agent/Server PSM, approvalFlowId/Kani 审批链接, NAC Admin/RD 身份检查, NSG 监控/集群/Agent 状态, and NAC sites cn, boe, i18n-row-tt, or i18n-bd."
---

# bytedcli NAC

使用 `bytedcli` 完成 Honeycomb/NAC 用户侧、ACL 可见范围和管理员专属的只读查询。Honeycomb/NAC API 之外的平台工具不属于本 Skill，应由其独立 Skill 处理。

## 固定术语与边界

- **MGT Rule（用户规则）**：用户通过 NAC 工单产生的持久化规则。
- **Rule Platform（规则平台）**：接口字段 `rulePlatform`，CLI 参数为 `--rule-plat`；取值是 `nsg`、`hfw`、`nac_proxy`、XACL 等平台，绝不能称为“规则类型”。
- **NSG Rule Type（NSG 规则类型）**：接口字段 `rule_type`，通常是 `xx.gw` 形式的动态值。只有 `rulePlatform=nsg` 的 MGT Rule 才具有 `rule_type`。
- **NSG 正式规则来源**：正式规则有四种来源：MGT Rule 中的 NSG 部分来自 Honeycomb；Yunque Rule 来自 NSG Server；`nac_sec` Rule 来自 NAC Security Center；TCC Rule 来自 TCC。来源不同不改变 `rulePlatform` 与 `rule_type` 的含义。
- **Ticket（用户规则工单）**：用户规则申请工单；后端 ACL 允许查看本人创建或本人作为 POC 的工单。
- **Yunque Rule（管理员规则）**：管理员规则；查询接口经过服务端管理员鉴权，并按规则类型检查读取权限。
- **Gray Rule（灰度规则）**：保存在独立表中的独立生命周期对象，不属于四种正式规则来源，也不能把灰度对象直接称为管理员规则。NSG Server 会按请求 Agent 动态把命中的灰度规则叠加到正式规则后再下发数据面。
- **Yunque Ticket（管理员规则工单）**：用于申请创建或更新 Yunque Rule 的管理工单。列表不是管理员专属；后端 ACL 可返回本人创建、本人作为 POC，或本人有读取权限的规则类型对应工单。
- **Permission Status**：当前登录身份在指定 NAC site 的 Admin/RD 状态。
- **TikTok ROW 站点**：`i18n-row-tt`、`i18n-tt`、`i18n` 是同一个 TikTok ROW 逻辑站点在不同参数维度下的标识。NAC API site 使用 `i18n-row-tt`，ByteCloud 认证 site 使用 `i18n-tt`，HFW resource site 使用 `i18n`。用户说出任一标识时，先理解为 TikTok ROW，再按参数维度选择对应值；三者不能直接互换为同一个参数值。
- **HFW（微隔离）**：按 PSM 查询 HFW Policy、有效 ACL 与该 PSM 的访问权限；也可查询 HFW 监控概览、集群、Agent 和集群默认 Bypass。监控接口使用独立接口权限，由后端鉴权。
- **NSG Rule Type / Match Agent**：管理员查询本人可用的 NSG 规则类型，以及某个具体规则类型用于匹配的 FW 客户端。
- **NSG Monitor**：NAC 管理员查看 NSG 监控概览、受监控集群和集群 Agent 详情。
- **NSG Agent Params**：管理员按 Agent IP 查询前端参数面板；请求由 NAC 服务代理到 Agent。
- **Matrix Rule**：NAC 管理员查询区域、provider、地址类型组合之间是否支持隔离规则；不是顶层 Matrix 任务诊断能力。
- **Dialtest（拨测）**：管理员查询拨测任务及最近运行结果、可执行拨测的 Agent、已配置的拨测服务环境/Server PSM；分别使用 `nac admin dialtest-task`、`nac admin dialtest-agent` 和 `nac admin dialtest-server-psm`。
- **approvalUrl**：根据 Ticket 的 `approvalFlowId` 在本地派生；不是额外调用 NAC 或 Kani API 得到。
- **Rule Analysis**：不表示持久化规则类型。`nac rule search` 查询编译前但已 normalize 的正式规则，统一覆盖四种正式规则来源并返回所有符合条件的规则，但查不到独立表中的灰度规则。`nac admin rule search` 让指定 NSG Agent 使用数据面编译后的规则执行精确匹配，返回该流量实际命中的规则。`nac rule conflict-check` 检查一条候选规则与现有正式规则的完全重复、冗余、冲突和重叠风险。
- **Compiled Rule（编译后规则）**：已解析 PSM/域名、完成地址规范化并准备下发到数据面的最终规则集合。它不同于 `nac rule search` 返回的编译前但已 normalize 的四来源正式规则，并可能包含按请求来源动态叠加的灰度规则。
- **Rule Delivery Status（规则下发状态）**：按一条规则 ID 判断其在 Server 编译、Agent 拉取、Agent 转换和 Engine 编译四个阶段已到达或停留的位置。它查询下发过程，不等同于列出某类全部编译后规则。
- **ES Log Collection Config（ES 日志采集配置）**：管理员查看哪些 NSG 日志会被 ES 采集。集群 IP、NSG 规则类型、规则 ID 三组条件是 OR 关系，任一已配置条件命中即采集。
- **Audit Log（审计日志）**：NAC 用户操作日志；后端只允许 Kani 超级管理员读取，过滤对象类型以服务端定义为准并转换为具体业务语义。

当前封装三十四个只读叶子命令：十五个用户、接口权限或后端 ACL 可见的只读叶子，十九个放在 `admin` 命名空间的只读叶子。`admin` 是 CLI 能力分组；具体服务端鉴权以各接口实现为准。

| 用户意图 | 必须选择的命令 |
|---|---|
| 明确列出/筛选 MGT Rule、用户规则、default 表或 tob 表 | `nac user-rule list` |
| 明确按 ID 查询 MGT Rule、用户规则、default 表或 tob 表 | `nac user-rule list --id <rule-id>` |
| 根据工单查关联规则 | `nac user-rule list --ticket-id <ticket-id>` |
| 检查本人 NAC 身份 | `nac permission status` |
| 列出/筛选用户工单 | `nac user-ticket list` |
| 查看工单详情或审批链接 | `nac user-ticket get --id <ticket-id>` |
| 列出 HFW 平台的 MGT Rule | `nac user-rule list --rule-plat hfw` |
| 查询 PSM 的 HFW Policy | `nac hfw policy list --psm <psm>` |
| 查询 PSM 的有效 HFW ACL | `nac hfw acl list --psm <psm>` |
| 查询 PSM 的 HFW 权限 | `nac hfw permission get --psm <psm>` |
| 查看 HFW 监控概览 | `nac hfw monitor get` |
| 列出/筛选 HFW 监控集群 | `nac hfw cluster list` |
| 列出某 HFW 集群的 Agent | `nac hfw agent list --cluster <cluster>` |
| 查询一个 HFW Agent 的状态 | `nac hfw agent status --ip <agent-ip>` |
| 查询集群默认 Bypass | `nac hfw default-bypass get --cluster <cluster>` |
| 查询全部有权读取的 NSG 规则类型和四种正式规则来源 | `nac rule search` |
| 未明确规则来源的规则 ID 查询 | `nac rule search --id <rule-id>` |
| 查询编译前符合条件的所有正式规则 | `nac rule search ...` |
| 检查候选规则的重复、冗余、冲突和重叠风险 | `nac rule conflict-check` |
| 列出/筛选 Yunque 管理工单 | `nac yunque-ticket list` |
| 明确查询 Yunque 管理员规则 | `nac admin yunque-rule search --rule-type <type>` |
| 查询灰度规则 | `nac admin gray-rule list` |
| 列出当前管理员可用的 NSG 规则类型 | `nac admin nsg-rule-type list` |
| 查询某个 NSG 规则类型用于匹配的 FW 客户端 | `nac admin nsg-agent list --rule-type <type>` |
| 明确查询编译后或下发到数据面的全量规则 | `nac admin compiled-rule list --rule-type <type>` |
| 在指定 NSG Agent 上精确匹配 | `nac admin rule search --rule-type <type> --agent <ip>` |
| 查询某条规则的下发情况、下发到哪一步或为什么没生效 | `nac admin rule delivery-status --id <rule-id>` |
| 查询哪些 NSG 日志会被 ES 采集 | `nac admin es-log-config get` |
| 查询 NAC 用户操作审计日志 | `nac admin audit-log list` |
| 查看 NSG 监控概览 | `nac admin nsg-monitor get` |
| 列出/筛选 NSG 监控集群 | `nac admin nsg-cluster list` |
| 查看 NSG 集群 Agent 详情 | `nac admin nsg-cluster get --id <cluster-id>` |
| 列出 NSG 集群名选择项 | `nac admin nsg-cluster-name list` |
| 查询 NSG Agent 运行参数 | `nac admin nsg-agent-param list --ip <agent-ip>` |
| 列出/筛选 NAC Matrix Rule | `nac admin matrix-rule list` |
| 查看 Matrix Rule 详情 | `nac admin matrix-rule get --id <rule-id>` |
| 查询拨测任务及最近运行结果 | `nac admin dialtest-task list` |
| 查询可执行拨测的 Agent | `nac admin dialtest-agent list` |
| 查询拨测服务环境/Server PSM | `nac admin dialtest-server-psm list` |

路由优先级是硬约束：用户查询某条规则的“下发情况”“下发到哪一步”或“为什么没生效”时使用 `nac admin rule delivery-status --id <rule-id>`；不要误用列出全量结果的 compiled-rule。仅当用户明确说“编译后规则”或“下发到数据面的规则集合”时才使用 `nac admin compiled-rule list`。明确提到 MGT Rule、用户规则、default 表或 tob 表时才使用 `nac user-rule list`，它只提供数据库层面的 LIKE 筛选；明确提到 Yunque 管理员规则时才使用 `nac admin yunque-rule search`，它同样只提供数据库层面的 LIKE 筛选；明确查询灰度规则时使用 `nac admin gray-rule list`。其余规则匹配在 `nac rule search` 与 `nac admin rule search` 之间遵循“显式意图优先，条件完整度辅助”：用户要所有符合条件、覆盖关系、模糊检索时使用前者；用户要指定 Agent 数据面实际命中、最终命中或精确匹配时使用后者。没有明确意图时，具体源、具体目的、端口和协议等接近完整五元组的条件倾向精确匹配；只有 IP、CIDR、Domain、PSM 等局部条件倾向模糊匹配。若精确匹配缺少 `rule_type` 或 Agent，先发现或向用户确认，绝不能任意选择 Agent；仍不确定时可以同时执行模糊与精确查询，但必须分别标为“编译前符合条件的规则”和“指定 Agent 数据面实际命中的规则”。“我的”只表示创建人过滤，不能用于选择规则查询接口。未说明来源的“我的规则”先按上述意图路由，再使用相应命令的创建人条件。不得生成 `user-rule get`，也不得回退到旧命令。完整参数见 [references/commands.md](references/commands.md)。
用户使用中文描述过滤条件或需要解释查询结果时，读取 [references/frontend-semantics.md](references/frontend-semantics.md)。
实现或审计返回字段时，必须读取 [references/response-field-coverage.md](references/response-field-coverage.md)。
用户询问 NSG 规则字段、合法性、来源、扩展、域名匹配、ID 反查、优先级或编译链路已知限制时，必须读取 [references/nsg-rule-model.md](references/nsg-rule-model.md)。该 reference 解释规则模型，不改变上面的命令路由。

## 调用约束

1. 查询优先使用全局 `--json`，并把它放在 `nac` 前：`bytedcli --json nac ...`。
2. NAC `--site` 是每个叶子命令的参数，规范位置是在完整命令之后，例如 `bytedcli --json nac permission status --site cn`。放在 `nac` 前的全局位置仅用于兼容已有调用，Skill 必须生成叶子命令位置。未指定 NAC site 时使用 `cn`；非 HFW 查询中，用户明确指定 NAC 区域时传 `--site`。
3. List 默认 `--page 1 --page-size 20`。
4. “我的”对所有规则查询接口都表示创建人是当前登录用户，但不参与命令路由。先按规则来源选择命令，再执行 `bytedcli --json auth userinfo` 并读取非空 `data.username`：
   - 未说明来源的“我的规则”使用 `nac rule search --username <username>`。
   - “我的 MGT Rule/用户规则”使用 `nac user-rule list --creator <username>`；“我的用户工单”使用 `nac user-ticket list --creator <username>`。
   - “我的 Yunque Rule”使用 `nac admin yunque-rule search --username <username>`；“我的 Yunque Ticket”使用 `nac yunque-ticket list --username <username>`。
   - “我的灰度规则”使用 `nac admin gray-rule list --rule-username <username>`。
   - 规则查询命令没有创建人参数时，先用 `--json` 获取结果，再按返回规则的创建人字段在本地严格过滤；结果没有可靠创建人字段时明确说明无法表达，不得退化为可见全集。
   - 用户未说明所有权，或说“所有”“我能看到的”“可见的”“我作为 POC 的”时，不添加 `--creator`、`--username` 或 `--rule-username`，让后端 ACL 返回当前身份可见的结果。
   - 不新增或猜测 `--mine`。无法取得非空 `data.username` 时先报告认证问题，不得通过省略所有权过滤条件扩大“我的”查询。
5. Ticket 地址的 type/value 必须成对：`--src-type`/`--src`、`--dst-type`/`--dst`。
6. MGT Rule 的 `--enabled` 必须带 `true` 或 `false`，且不存在 `--rule-type`。`--rule-plat` 只表示规则平台；Yunque、Gray、管理工单和 NSG Agent 查询中的规则类型是具体 `rule_type`，通常为 `xx.gw`，不得把平台值 `nsg` 填入。
7. 未知 site、错误布尔值、地址参数缺半、非法状态或 start 晚于 end 时停止并报告参数错误。
8. HFW 查询必须提供非空 `--psm`；`--provider` 默认 `tce`，也可透传任意非空 provider。
9. HFW 的 `--site` 选择 NAC API 与认证站点；`--hfw-site` 选择 HFW 资源站点。微隔离 Policy、ACL、Permission 查询中，用户只提到一个区域时，优先把该区域解释为 HFW 资源区域并显式生成 `--hfw-site`。只有用户明确说“NAC API”“认证站点”“NAC host/控制面走某站点”时，才据此生成 `--site`；不要混用两者。
10. HFW 监控、集群和 Agent 命令只使用 NAC `--site`，不接收 PSM triple 或 `--hfw-site`。它们位于 `nac hfw`，所需接口权限由后端判断；鉴权失败时不得改用写接口或其他接口绕过。
11. `nac admin yunque-rule`、`nac admin gray-rule`、`nac admin nsg-rule-type/nsg-agent/nsg-agent-param`、`nac admin nsg-monitor/nsg-cluster`、`nac admin matrix-rule` 和三个 `nac admin dialtest-*` 资源都属于管理员命令。普通用户查询不要因结果为空或 401 而改用其他接口绕过鉴权。
12. `nac yunque-ticket list` 不属于管理员专属命令；不要错误生成 `nac admin ticket list`。
13. Dialtest 三条命令使用 `nac admin dialtest-task`、`nac admin dialtest-agent` 和 `nac admin dialtest-server-psm`，不得省略 `admin`；默认拨测环境为 `tob`，任务/Agent 列表默认 `page=1`、`page-size=20`。
14. 规则匹配先判定用户要“编译前符合条件的所有规则”还是“指定 Agent 数据面实际命中的规则”。显式意图优先，条件完整度只作辅助；缺少精确匹配所需的 `rule_type` 或 Agent 时先发现或确认。用户同意两种都查或仍无法确定时可分别执行两类查询，但不得混合结果语义。
15. 执行规则查询前，必须先从用户输入中提取所有可表达的过滤条件，并尽可能下推到 NAC 服务端。只有服务端确实无法表达的剩余条件，才允许在已充分收窄的结果上做本地过滤。`nac rule search` 的 `--rule-type` 可选；省略时查询全部有权读取的 NSG 规则类型。所有过滤条件都可省略，此时返回四种正式规则来源的完整 ACL 可见集合，但不包含灰度规则。五元组候选严格使用 `any/all/empty/value/precise` 五态，已有规则使用 `all/empty/concrete` 三态。后端原始请求不传某个五元组字段表示 `empty`；CLI 省略对应选项时会主动发送 `*`，因此 CLI 省略表示 `any`。IP、Domain、TCE PSM ID、PSM 只在已有规则预处理 `all/empty/concrete` 状态时互相影响；匹配时每个候选字段完全独立，各字段谓词最后按 AND 组合。用户按地址类型查询时，必须优先用五态参数在服务端表达严格类型；只要能用选中字段 `any` 加同侧其余 Host 字段 `empty` 表达，就不得退化为无条件全量查询后本地筛选。执行任何带五元组或地址类型过滤的检索前，必须读取 [NSG 规则检索五态匹配](references/rule-search.md)，保留字面引号、显式空字符串和完整逗号列表。
16. `nac admin rule search` 必须同时提供具体规则类型和同一规则类型下的 FW 客户端 `--agent`；Agent 优先来自 `nac admin nsg-agent list`。没有返回规则 ID 表示“未匹配到具体规则”，不要把后端附带的默认动作伪装成命中规则。
17. `nac admin audit-log list` 的 HFW 对象详情过滤必须同时提供 `--psm`、`--provider`、`--hfw-site`。这里 `--site` 仍选择 NAC API/认证站点，`--hfw-site` 只过滤审计详情中的 HFW 资源站点。
18. `nac admin compiled-rule list` 通过 NAC 管理员接口查询，只接受具体 `--rule-type` 和标准 NAC `--site`。站点支持 `cn`、`boe`、`i18n-row-tt`、`i18n-bd` 及已有兼容别名，并沿用 NAC 登录与管理员鉴权。不要添加分页、Agent IP 或其他过滤条件，也不要伪造接口未返回的版本号。
19. `nac admin rule delivery-status` 必须提供 `--id`，可选 `--site` 和可重复的 `--agent <ip>`。CLI 会自动归一化正反向 ID、分别检索正反向规则、推导唯一 `rule_type`、判断反向规则是否存在并查询该类型的 Agent。用户未指定 Agent 时省略 `--agent`，固定检查列表第一台，即使其状态异常也不换台；用户明确指定时原样传递 1–4 个属于该规则类型的 Agent IP，最多 4 个，不得擅自扩展或自动分批。不得生成 `--rule-type` 或 `--reverse-rule-exists`。该接口开销较大：包含同一 Agent 的两次查询之间必须至少等待 5 秒，不得通过并发或拆分命令绕过。规则不存在、类型不唯一、指定 Agent 不属于该类型或 Agent 列表为空时保留结构化错误，不得回退为 compiled-rule 全量列表。
20. `nac admin es-log-config get` 只接受可选的 NAC `--site`。结果中的集群 IP、NSG 规则类型和规则 ID 是三组 OR 条件：任一组内任一已配置值命中时，相关日志会被 ES 采集。不得解释成三个字段必须同时匹配，也不得把空列表说成全量采集。
21. 每次 `bytedcli --json nac rule conflict-check ...` 成功后，都必须读取 [冲突检查综合风险分析](references/conflict-risk-analysis.md)，直接依据完整 JSON 和原命令参数执行不可跳过的分析。命令失败时不分析；不得调用其他模型或风险 API。

## MGT Rule 查询

只有用户明确说 MGT Rule、用户规则、default 表或 tob 表时才进入本节。该命令提供数据库层面的 LIKE 筛选，不等同于跨来源的语义规则匹配。已知表类型时附加 `--table-type default|tob`；已知规则平台时附加 `--rule-plat`。`default` 与 `tob` 是两套存储表，未知时保留并报告全部匹配项，不擅自认为规则 ID 在两张表间全局唯一。

规则平台 `rulePlatform` 与前端值一致：`nsg`、`hfw`、`nac_proxy`、`xacl_idc`、`xacl_internal_devbox`、`xacl_internal_boe`。这些值不是 `rule_type`。只有规则平台为 `nsg` 的 MGT Rule 才在规则详情中具有具体 NSG 规则类型。

```bash
# 默认列出后端 ACL 允许查看的 MGT Rule
bytedcli --json nac user-rule list

# “我的 MGT 用户规则”：先取得当前登录 username，再填入现有 creator 字段
bytedcli --json auth userinfo
bytedcli --json nac user-rule list --creator demo-user

# 按 ID 查 default 表中的 MGT 用户规则
bytedcli --json nac user-rule list --id 123 --table-type default

# 查询 BOE 中已禁用的 NSG 规则
bytedcli --json nac user-rule list \
  --site boe \
  --rule-plat nsg \
  --enabled false
```

## Permission 与 Ticket 查询

Permission 身份自动来自当前登录用户，不提供 username/email 参数。Ticket list 在“所有/可见”语义下不发送 creator，因此结果可以包含“本人创建”或“本人作为 POC”的工单；只有“我的工单”才解析当前 `data.username` 并发送 creator。

```bash
# 检查当前用户权限
bytedcli --json nac permission status --site cn

# 查源 PSM 到目的域名的已生效工单
bytedcli --json nac user-ticket list \
  --src-type psm \
  --src service.demo \
  --dst-type domain \
  --dst example.com \
  --status exec-success

# “我的工单”：复用上面 auth userinfo 返回的 data.username
bytedcli --json nac user-ticket list --creator demo-user

# 获取工单和 Kani 审批链接
bytedcli --json nac user-ticket get --id 456
```

Ticket status 输入只使用语义名；下表中的数字仅用于解释服务端返回值：

| 数字 | 语义名 | 数字 | 语义名 |
|---:|---|---:|---|
| 1 | `in-approval` | 7 | `disabling` |
| 2 | `accepted` | 8 | `disabled` |
| 3 | `rejected` | 9 | `expiring` |
| 4 | `in-progress` | 10 | `expired` |
| 5 | `execute-fail` | 11 | `canceled` |
| 6 | `exec-success` | 12 | `deprecated` |

## Yunque Rule、Gray Rule 与管理工单

只有用户明确说 Yunque 管理员规则时才使用 Yunque Rule 查询。它提供数据库层面的 LIKE 筛选，必须提供前端选择的具体 NSG 规则类型。接口只提交 `rule_type`，其余前端过滤条件、排序和分页由 CLI 按前端逻辑完成。未知类型时先执行 `nac admin nsg-rule-type list`，不得猜测或把 `nsg` 当成规则类型。

```bash
# 查看当前管理员可用的 NSG 规则类型
bytedcli --json nac admin nsg-rule-type list

# 查询 demo.gw 类型用于匹配的 FW 客户端
bytedcli --json nac admin nsg-agent list --rule-type demo.gw

# 查询 demo.gw 类型的 Yunque 管理员规则
bytedcli --json nac admin yunque-rule search --rule-type demo.gw

# “我的 Yunque Rule”：先解析当前 username
bytedcli --json auth userinfo
bytedcli --json nac admin yunque-rule search \
  --rule-type demo.gw \
  --username demo-user

# 查询正在灰度发布的规则
bytedcli --json nac admin gray-rule list --status releasing

# 生效 ID 和原始灰度 ID 都使用 --id
bytedcli --json nac admin gray-rule list --id 130000038

# 查询后端 ACL 允许看到的全部 Yunque 管理工单
bytedcli --json nac yunque-ticket list

# “我的 Yunque 管理工单”
bytedcli --json auth userinfo
bytedcli --json nac yunque-ticket list --username demo-user
```

Yunque Ticket 列表的后端 ACL 可包含本人创建、本人作为 POC，或本人拥有读取权限的 NSG 规则类型。用户说“所有/可见/我能看到的”时不得自动添加 `--username`。完整过滤参数和中文映射见 references。

Gray Rule 位于独立表，不是第五种正式规则来源。`nac admin gray-rule list` 查询灰度对象本身；`nac rule search` 查不到它。处于发布中的灰度规则只有命中特定 Agent 后才会改变该 Agent 收到的最终规则集合，具体命中与合并语义见 [NSG 规则模型与来源](references/nsg-rule-model.md)。

## 规则检索、精确匹配与审计日志

`nac rule search` 是最全面的 NSG 正式规则查询接口，查询编译前但已 normalize 的四来源正式规则，返回所有符合条件的规则，适合“哪些规则符合/覆盖这些条件”“模糊匹配”“列出相关规则”等意图。未说明来源的规则 ID 也使用该命令。不带参数时查询后端 ACL 允许读取的全部规则类型，结果统一包含 MGT/Honeycomb、Yunque、`nac_sec`/NAC Security Center 和 TCC 四种正式规则来源；`--rule-type` 仅用于按具体类型收窄，不是必填。该接口查不到灰度规则。五元组和严格 Host 地址类型过滤必须遵循 [NSG 规则检索五态匹配](references/rule-search.md)，优先由服务端过滤；元数据过滤保持原 V2 契约。

```bash
# 查询 ACL 允许读取的全部 NSG 规则类型和四种正式规则来源
bytedcli --json nac rule search

# 未说明来源的“我的规则”：不改变 rule search 路由
bytedcli --json auth userinfo
bytedcli --json nac rule search --username demo-user

# 按 ID 查询未说明来源的规则
bytedcli --json nac rule search --id 123 --site boe

# 按具体规则类型和目的域名收窄
bytedcli --json nac rule search \
  --rule-type demo.gw \
  --dst-domain example.com

# 检查候选规则的冲突风险
bytedcli --json nac rule conflict-check \
  --rule-type demo.gw \
  --action ACCEPT \
  --priority 100 \
  --src-ip 192.0.2.0/24 \
  --dst-port 443
```

`conflict-check` 成功后必须按 [冲突检查综合风险分析](references/conflict-risk-analysis.md) 处理结果。`has_risk=false` 时只输出一句限定性结论；`has_risk=true` 时只输出 `总体结论`、`关键依据`、`可能影响`，不得输出处理建议。

`nac admin rule search` 使用指定 Agent 数据面加载的编译后规则判断流量实际命中，适合“实际会命中哪条”“最终命中”“让某台 FW 客户端判断”等精确匹配意图。显式意图优先于条件多少；没有明确意图时，具体源、具体目的、端口和协议接近完整五元组才倾向精确匹配，IP、CIDR、Domain、PSM 等局部条件倾向模糊查询。精确匹配必须先取得具体 `rule_type` 和该类型的 Agent；缺少任一项就发现或确认，不得任意选 Agent。仍不确定时可以两种都查，但必须将结果分成“编译前符合条件的规则”和“指定 Agent 数据面实际命中的规则”。该接口同时要求 NAC 管理员权限和规则类型读取权限。

“NAC 审计日志”“谁修改了某类 NAC 对象”使用 `nac admin audit-log list`，只允许 Kani 超级管理员调用。`--object` 接受后端定义的全部对象类型；Agent 必须使用命令参考中的业务语义理解和展示，不能把 `serverRule`、`clientCall` 等裸值直接作为用户解释。

规则检索返回的 `record`、`internal` 在值为 `false` 时可能被后端 JSON 的 `omitempty` 省略。字段缺失表示接口没有返回该值，不能擅自补成 `false`。

## 编译后数据面规则

仅当用户明确要求“编译后规则”或“下发到数据面的规则”时使用：

```bash
bytedcli --json nac admin compiled-rule list --rule-type demo.gw --site boe
```

`--rule-type` 是必填的具体 NSG 规则类型；未知时先执行 `nac admin nsg-rule-type list`。该命令通过 NAC 管理员接口返回所选类型准备下发到数据面的全量编译结果，没有分页和二次筛选；结果先读取四来源正式规则，再按请求链路的 `X-Real-IP` 动态叠加当前 Agent 命中的发布中灰度规则，因此可能包含 `nac rule search` 查不到的灰度效果。CLI 不提供 `--agent-ip`，不能声称能够任意模拟其他 Agent。支持标准 NAC 站点 `cn`、`boe`、`i18n-row-tt`、`i18n-bd`。`current_count` 是 CLI 根据本次规则数组计算的规则数；接口不返回数据面版本，CLI 不得伪造。动作必须解释为业务语义：`permit` 表示放行，`deny` 表示阻断；不得只向用户展示裸值。普通正式规则查询继续使用 `nac rule search`，灰度对象查询使用 `nac admin gray-rule list`。

## HFW（微隔离）查询

HFW MGT Rule 仍属于用户规则列表，不新增重复入口：

```bash
bytedcli --json nac user-rule list --rule-plat hfw
```

Policy、ACL、Permission 三条命令共享参数：`--psm` 必填，`--provider` 默认 `tce`，`--site` 默认 `cn`。`--hfw-site` 接受 `cn`、`boe`、`i18n`、`i18n-bd`、`tob_cn`。

自然语言区域的优先级：

- 用户说“BOE 的微隔离策略”“TikTok ROW 的 HFW ACL”等，只给出一个区域时，这个区域默认指 HFW 资源，必须显式生成 `--hfw-site boe` 或 `--hfw-site i18n`；不要自动生成 `--site boe` 或 `--site i18n-row-tt`。
- 只有用户明确指定 NAC API、认证站点或控制面站点时才生成 `--site`。
- 用户同时指定两个维度时分别生成，例如“NAC API 走 CN，查 BOE HFW”使用 `--site cn --hfw-site boe`。
- CLI 在省略 `--hfw-site` 时仍会按下表自动推导，这是命令执行的兜底行为。用户已经明确提到 HFW 区域时，不得依赖自动推导而省略 `--hfw-site`。

| NAC `--site` | 默认 HFW `--hfw-site` |
|---|---|
| `cn` | `cn` |
| `boe` | `boe` |
| `i18n-row-tt` | `i18n` |
| `i18n-bd` | `i18n-bd` |

```bash
# 查询 service.demo 的 HFW Policy
bytedcli --json nac hfw policy list --psm service.demo

# 用户只说 BOE：区域优先解释为 HFW 资源站点
bytedcli --json nac hfw policy list \
  --psm example.hfw.service \
  --hfw-site boe

# 用户只说 TikTok ROW：HFW 资源站点值是 i18n
bytedcli --json nac hfw permission get \
  --psm service.demo \
  --hfw-site i18n

# 查询 service.demo 的有效 HFW ACL
bytedcli --json nac hfw acl list --psm service.demo

# 查询 service.demo 的 HFW 权限
bytedcli --json nac hfw permission get --psm service.demo

# NAC API 走 CN，但查询 BOE 的 HFW 资源
bytedcli --json nac hfw acl list \
  --psm service.demo \
  --site cn \
  --hfw-site boe
```

这条自然语言区域规则只适用于 `nac hfw policy list`、`nac hfw acl list` 和 `nac hfw permission get`。HFW 平台的 MGT Rule 没有 `--hfw-site` 参数；“查询 BOE 的 HFW 用户规则”仍使用 `nac user-rule list --rule-plat hfw --site boe`。

HFW 监控命令只使用 NAC `--site`：

```bash
# HFW 监控概览
bytedcli --json nac hfw monitor get

# 按集群名筛选，并按死亡 Agent 数降序
bytedcli --json nac hfw cluster list \
  --cluster demo \
  --order-by mortalityCount \
  --order descend

# 查询集群内异常 Agent
bytedcli --json nac hfw agent list \
  --cluster demo \
  --status abnormal

# 查询 Agent 状态和集群默认 Bypass
bytedcli --json nac hfw agent status --ip 192.0.2.10
bytedcli --json nac hfw default-bypass get --cluster demo
```

监控概览中，`clusterCount` 是集群总量，不是规则总量；异常集群按 `clusterCount - clusterAliveCount` 派生。后端把死亡 Agent 比例不超过 1% 的集群判为健康。`agentAbnormalCount` 是异常 Agent 数，不能称为异常集群；`agentRuleErrorCount`、`agentRuleOverflowCount` 分别是存在规则异常、规则溢出的 Agent 数，不是规则条数。

## NSG 管理员监控

```bash
# NSG 监控概览
bytedcli --json nac admin nsg-monitor get --site cn

# 查询实际异常、Agent 打点异常的集群
bytedcli --json nac admin nsg-cluster list \
  --cluster-state unhealthy \
  --metric-status dead

# 按前端集群名称、PSM、预期状态和部署类型过滤
bytedcli --json nac admin nsg-cluster list \
  --cluster demo \
  --psm service.demo \
  --expected-status online \
  --deploy-type nat

# 列表返回短 ID 时可直接查询详情
bytedcli --json nac admin nsg-cluster get --id demo

# 列出 NSG 集群名选择项
bytedcli --json nac admin nsg-cluster-name list

# 查询一个 NSG Agent 的运行参数
bytedcli --json nac admin nsg-agent-param list --ip 192.0.2.10
```

列表过滤条件与前端一致：

- “集群状态/实际状态/健康/异常”使用 `--cluster-state healthy|unhealthy`，请求映射到 `agentStatus=0|1`。
- “Agent 打点状态/打点正常/打点异常”使用 `--metric-status active|dead`，请求映射到 `metricStatus=0|1`。
- “预期状态”使用 `--expected-status online|offline|deprecated`；不要与实际集群状态混淆。
- `--cluster`、`--rule`、`--agent-ip`、`--psm`、`--agent-type`、`--agent-env`、`--deploy-type`、`--tt` 对应前端同名过滤项。
- `nsg-cluster get --id` 接受列表短 ID 和完整 `nsg-cluster-*` ID；不要手工重复前缀。

## NSG 规则类型与匹配 Agent

`nac admin nsg-rule-type list` 返回当前管理员有权使用且实际存在的 NSG `rule_type`。前端在 Yunque Rule、Gray Rule、管理工单、规则匹配和监控筛选中复用这组动态值。

`nac admin nsg-agent list --rule-type <type>` 返回该具体规则类型用于规则匹配的 FW 客户端。`--rule-type` 必填，优先使用上一条命令返回的值；文本状态使用前端的“存活/异常”。

## Matrix Rule 与拨测

Matrix Rule 是管理员只读能力。列表按源/目的区域、provider、地址类型和隔离支持状态筛选；详情按 ID 查询。

```bash
bytedcli --json nac admin matrix-rule list --allowed supported
bytedcli --json nac admin matrix-rule get --id 7
```

拨测命令使用前端筛选项，并固定属于 `nac admin`：

```bash
bytedcli --json nac admin dialtest-task list --dialtest-env tob
bytedcli --json nac admin dialtest-agent list --status online
bytedcli --json nac admin dialtest-server-psm list
```

任务列表返回每个协议最近一次运行结果。CLI 的 `--page-size` 映射到任务接口请求体的 `size`；这是线协议字段差异，不是新增过滤语义。

## 输出处理

- MGT Rule list 返回 `rules`、`total`、`page`、`page_size`、`site`。
- Ticket list/get 中每个 Ticket 都带 `approvalUrl`；无可用审批流时为 `null`，不要自行调用 Kani API 或打开网页补查。
- Yunque Ticket 同样本地派生 `approvalUrl`；动作、状态、工单类型和灰度状态使用前端业务含义。
- Yunque Rule 文本输出把动作和状态映射为前端概念；Gray Rule 文本输出解释生效 ID、操作类型、发布状态和嵌套规则动作。
- I18N Permission Status 的 `isRd` 为 `null`、`rdSupported=false`，表示该站点未执行 RD 检查。
- HFW JSON 输出保留前端结构，并增加 NAC API `site` 与最终的 `hfwTriple`。规则数组缺失或为 `null` 时输出 `[]`。
- HFW 监控 JSON 保留后端字段并增加 NAC API `site`；集群/Agent 列表缺失或为 `null` 时输出 `[]`。监控文本不展示不存在的“规则总量”，也不把 `agentAbnormalCount` 标成异常集群。
- JSON 模式保留接口原始结构和未知字段；文本模式只展示前端已展示的字段、CLI 导航必需字段，以及已经确认的业务语义。
- 文本输出必须与前端字段名称、枚举解释、组合语义和显示范围一致。禁止向用户直接展示非显然的后端裸值；不得用字段名和值的机械拼接代替业务解释。
- 组合字段必须整体解释。属于同一个前端概念的方向、动作、状态或布尔字段不能拆成多个后端字段逐项输出。
- 明显字段和直接中英文对应不建立重复翻译表，但仍必须覆盖前端实际展示的列。前端未展示的字段不进入默认文本输出；未知或未验证字段只保留在 JSON 中。
- HFW Policy/ACL 的全局默认策略只表示出方向，使用“PSM 出内网默认策略”“PSM 出公网默认策略”作为完整概念。状态为未配置时，两项都显示“策略未配置，默认放行”，不得解释接口中的占位动作或布尔值；状态为已配置时才显示“允许”或“阻断”，状态未知时保持未知。自定义策略使用前端的策略 ID、策略动作、生效区域、源信息、目的信息、协议、来源、优先级。协议缺失时显示“未提供”，不得推断为 TCP。
- NSG Cluster `state=0/1` 分别表示实际健康/异常；`status` 是预期状态。Agent `metric_status=active/dead` 分别表示打点正常/异常；BGP Bypass 按前端开关语义解释。
- NSG Rule Type 文本输出显示具体 `rule_type` 和前端显示名称；匹配 Agent 的 `alive=true/false` 显示为存活/异常。
- NSG Agent 参数使用前端参数面板的中文含义。
- Matrix Rule 的 `allowed=0/1/2` 分别显示为不支持/支持隔离规则/无隔离；源和目的的区域、provider、地址类型作为整体范围展示。
- Dialtest Task 的 `dial_results` 按协议显示执行成功/执行失败、延迟、时间和错误；Agent `online/offline` 显示为在线/离线。
- Rule Conflict Check JSON 包含 `has_risk`、四类全量计数 `summary`、风险明细 `results`、`limit`、`sort`、`truncated` 和 `site`；Agent 摘要必须遵循冲突分析 reference。
- NAC envelope 非零错误必须保留服务端 `code/msg`。

故障处理见 [references/nac-troubleshooting.md](references/nac-troubleshooting.md)。
