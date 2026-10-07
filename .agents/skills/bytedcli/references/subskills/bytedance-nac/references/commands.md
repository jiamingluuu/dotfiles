# NAC 命令参考

## 目录

- [站点、身份与用户资源](#站点与认证)
- [规则分析与审计](#nac-rule-search)
- [Yunque、灰度与管理工单](#nac-admin-yunque-rule-search)
- [HFW（微隔离）](#hfw微隔离只读命令)
- [NSG 规则类型、监控和 Agent](#nsg-规则类型与匹配-agent)
- [编译后数据面规则](#nac-admin-compiled-rule-list)
- [规则下发状态](#nac-admin-rule-delivery-status)
- [Matrix Rule](#matrix-rule)
- [Dialtest（拨测）](#dialtest拨测)
- [时间格式](#时间格式)

## 站点与认证

| NAC `--site` | NAC API 逻辑站点 | 对应 ByteCloud 认证 site |
|---|---|---|
| `cn` | 中国线上 | `cn` |
| `boe` | 中国 BOE | `boe` |
| `i18n-row-tt` | TikTok ROW | `i18n-tt` |
| `i18n-bd` | ByteDance I18N | `i18n-bd` |

`i18n-row-tt`、`i18n-tt`、`i18n` 是同一个 TikTok ROW 逻辑站点的三个上下文标识：NAC API `--site` 使用 `i18n-row-tt`，ByteCloud 认证使用 `i18n-tt`，HFW `--hfw-site` 使用 `i18n`。用户提到任一标识时都先识别为 TikTok ROW，再按参数维度选值；三个原始值不能直接互换。

NAC 不支持 `eu-ttp`。`--json` 是全局参数，必须放在 `nac` 前面。NAC `--site` 注册在每个叶子命令上，规范位置是在完整命令之后，例如 `bytedcli --json nac permission status --site cn`；放在 `nac` 前的全局位置仅保留兼容性，Agent 不应生成该写法。

## “我的”与可见范围

- “我的”对所有规则查询接口固定表示创建人是当前登录用户，但不决定查询接口。先按规则来源和查询能力选择命令，再执行 `bytedcli --json auth userinfo` 并读取非空的 `data.username`。
- 未说明来源的“我的规则”使用 `nac rule search --username <username>`；MGT 的“我的规则”使用 `nac user-rule list --creator <username>`。
- Yunque 的“我的规则”使用 `nac admin yunque-rule search --rule-type <type> --username <username>`；“我的灰度规则”使用 `nac admin gray-rule list --rule-username <username>`。
- “我的用户工单”使用 `nac user-ticket list --creator <username>`；“我的 Yunque 管理工单”使用 `nac yunque-ticket list --username <username>`。
- 查询命令没有创建人参数时，必须使用 JSON 结果按返回规则的创建人字段在本地严格过滤。结果没有可靠创建人字段时报告无法表达，不能把 ACL 可见全集当作“我的”。
- 用户未说明所有权，或说“所有”“我能看到的”“可见的”“我作为 POC 的”时，不传 `--creator`、`--username` 或 `--rule-username`，由后端 ACL 决定可见范围。
- 不存在 `--mine`。不要把 `me` 或“我的”直接作为 creator 值；身份解析失败时先执行 `bytedcli auth login`，不要退化为无 creator 查询。

## `nac user-rule list`

仅在用户明确提到 MGT Rule、用户规则、default 表或 tob 表时使用。它按用户规则存储表执行数据库层面的 LIKE 筛选，不是跨四种 NSG 正式规则来源的语义匹配接口。

| 参数 | 说明 |
|---|---|
| `--page <n>` | 页码，默认 1 |
| `--page-size <n>` | 每页数量，默认 20，最大 100 |
| `--id <rule-id>` | 按 MGT/用户规则 ID 做数据库 LIKE 筛选；未说明来源的规则 ID 不走此命令 |
| `--ticket-id <ticket-id>` | 按来源工单筛选 |
| `--rule-plat <platform>` | 规则平台 `rulePlatform` |
| `--enabled <true\|false>` | 前端“生效状态”，值不可省略 |
| `--start <time>` / `--end <time>` | 前端“生效时间”范围 |
| `--table-type <default\|tob\|all>` | 前端“规则属性”；默认 all |
| `--creator <username>` | MGT 创建人过滤；仅“我的 MGT Rule/我的用户规则”使用 `auth userinfo` 的 `data.username` |
| `--site <site>` | NAC 站点，默认 cn |

不存在 `--rule-type`。规则平台值：`nsg`、`hfw`、`nac_proxy`、`xacl_idc`、`xacl_internal_devbox`、`xacl_internal_boe`。只有规则平台为 `nsg` 的 MGT Rule 才在规则详情中具有具体 NSG `rule_type`。
中文过滤表达和返回值解释见 [frontend-semantics.md](frontend-semantics.md)。

## `nac permission status`

只有 `--site <site>`，默认 `cn`。username/email 自动使用当前登录身份，不接受用户输入。

## `nac user-ticket list`

| 参数 | 说明 |
|---|---|
| `--page <n>` / `--page-size <n>` | 默认 1 / 20，page-size 最大 100 |
| `--id <ticket-id>` | 按工单 ID 筛选 |
| `--src-type <ip\|psm>` + `--src <value>` | 源地址，必须成对 |
| `--dst-type <ip\|psm\|domain>` + `--dst <value>` | 目的地址，必须成对 |
| `--status <name>` | 状态语义名 |
| `--action <accept\|drop>` | 工单动作 |
| `--start <time>` / `--end <time>` | 创建时间范围 |
| `--creator <username>` | 创建人过滤；“我的工单”使用 `auth userinfo` 的 `data.username`，其他情况默认不发送 |
| `--department <keyword>` | 部门关键词过滤 |
| `--site <site>` | NAC 站点，默认 cn |

`--src-type` 与 `--src` 必须成对，`--dst-type` 与 `--dst` 必须成对。不要暴露 PSM provider/env、protocol 或 port 等未注册参数。

## `nac user-ticket get`

- `--id <ticket-id>`：必填。
- `--site <site>`：默认 `cn`。

返回 Ticket 详情及本地派生的 `approvalUrl`。

## `nac rule search`

按前端“规则检索”调用 `POST /v2/rule/match_all`。这是最全面的 NSG 正式规则查询接口，返回后端 ACL 允许读取的 MGT/Honeycomb、Yunque、`nac_sec`/NAC Security Center 和 TCC 四种正式规则来源。`--rule-type <type>` 可选；所有条件都省略时查询全部规则类型和正式来源。接口没有分页，返回全部匹配项，但查不到独立表中的灰度规则。

| 参数 | 前端过滤项 / 请求字段 |
|---|---|
| `--rule-type <type>` | 可选的具体 NSG 规则类型 / `rule_type`；省略表示全部规则类型 |
| `--id <rule-id>` | ID / `id` |
| `--name` / `--username` / `--comment` | Name / Username / Comment；未说明来源的“我的规则”把当前 `data.username` 传给 `--username` |
| `--src-ip` / `--src-psm` / `--src-tce-psm` / `--src-domain` / `--src-port` | 全部源五元组候选；每个字段支持 1–10 个逗号分隔值，必须由同一条已有规则全部包含；TCE PSM 参数传数字 ID |
| `--dst-ip` / `--dst-psm` / `--dst-tce-psm` / `--dst-domain` / `--dst-port` | 全部目的五元组候选；每个字段支持 1–10 个逗号分隔值，必须由同一条已有规则全部包含；TCE PSM 参数传数字 ID |
| `--protocol <value>` | Protocol / `proto` 五态候选；支持 1–10 个逗号分隔值，必须由同一条已有规则全部包含 |
| `--action <*\|accept\|drop\|permit\|deny>` | Action；`*` 表示不限制，`accept/drop` 转为大写线值 |
| `--priority <n>` | Priority，允许 0 |
| `--internal <true\|false>` | Internal 三态过滤；不传表示不限 |
| `--record <true\|false>` | Record 三态过滤；不传表示不限 |
| `--reversed <true\|false>` | Reversed 三态过滤；不传表示不限 |
| `--source <value>` | Source |
| `--site <site>` | NAC API 与认证站点，默认 `cn` |

除明确的 MGT/用户规则/default/tob 表查询和明确的 Yunque 管理员规则查询外，先在本命令与 `nac admin rule search` 之间按意图选择。用户要编译前所有符合条件、覆盖关系或模糊检索时使用本命令；用户要指定 Agent 数据面实际命中、最终命中或精确匹配时使用 `nac admin rule search`。显式意图优先，条件完整度只作辅助：接近完整五元组时倾向精确匹配，只有 IP、CIDR、Domain 或 PSM 等局部条件时倾向本命令。精确匹配缺少具体 `rule_type` 或 Agent 时先发现或确认；仍无法确定时可以分别查询，但必须区分“编译前符合条件的规则”和“指定 Agent 数据面实际命中的规则”。未说明来源的规则 ID 使用 `nac rule search --id <rule-id>`。

本命令的五元组字段使用 `any/all/empty/value/precise` 五态候选，对已有规则的 `all/empty/concrete` 三态执行 5×3 匹配。后端缺少字段表示 `empty`，CLI 省略选项会发送 `*` 表示 `any`。Host 字段只在已有规则预处理阶段互相影响；匹配阶段字段独立，最终组合各字段谓词。完整输入、包含关系、预处理和错误契约见 [rule-search.md](rule-search.md)。

返回规则中的 PSM ID 字段是 `psm_id`，对应 CLI 的 `--src-tce-psm` / `--dst-tce-psm`。按 IP、PSM、PSM ID 或 Domain 地址类型查询时，必须使用 [rule-search.md](rule-search.md) 的严格 Host 地址类型模板交给服务端过滤，不得先查全量再用本地字段筛选。

## `nac rule conflict-check`

调用 `POST /v2/rule/conflict_check` 检查一条候选 NSG 规则与已有规则之间的完全重复、冗余、冲突和重叠风险。该命令不会创建或修改规则。

| 参数 | 候选规则字段 |
|---|---|
| `--rule-type <type>` | `rule_type`，必填 |
| `--action <ACCEPT\|DROP>` | 候选动作，必填 |
| `--priority <n>` | 候选优先级，必填且允许 0；数值越小优先级越高 |
| `--id <id>` | 编辑已有规则时排除自身 ID |
| `--src-ip` / `--src-psm` / `--src-tce-psm` / `--src-domain` / `--src-port` | 候选源条件 |
| `--dst-ip` / `--dst-psm` / `--dst-tce-psm` / `--dst-domain` / `--dst-port` | 候选目的条件 |
| `--proto <value>` | 候选协议 |
| `--sort <field>` | `candidate_cover_ratio`、`target_cover_ratio`、`absolute_width_log2` 或 `priority`；默认 `candidate_cover_ratio` |
| `--limit <n>` | 返回风险明细上限，默认 100，范围 1–500 |
| `--site <site>` | NAC API 与认证站点，默认 `cn` |

至少提供一个源、目的、端口或协议流量选择器。成功的 JSON 返回必须继续按照 [conflict-risk-analysis.md](conflict-risk-analysis.md) 做综合风险分析；不得调用其他模型或风险 API。

## `nac admin rule search`

按前端“精确匹配”调用 `POST /v1/nsg_rule/match`。`--rule-type <type>` 和 `--agent <ip>` 必填；Agent 应来自同一规则类型的 `nac admin nsg-agent list`。

可选条件为 `--src-ip`、`--src-psm`、`--src-port`、`--dst-ip`、`--dst-psm`、`--dst-port`、`--dst-domain`、`--protocol icmp|icmpv6|tcp|udp` 和 `--site`。该接口要求 NAC 管理员权限和所选规则类型的读取权限。返回规则没有 ID 时表示未匹配到具体规则。

## `nac admin rule delivery-status`

查询一条规则在数据面下发链路中已经到达或停留的阶段。Rule ID 必填；Agent 可省略或重复指定：

| 参数 | 说明 |
|---|---|
| `--id <rule-id>` | 必填；正向或反向 Rule ID 均可 |
| `--agent <ip>` | 可重复；指定该规则类型返回的 Agent，去重后最多 4 个；省略时检查第一台 |
| `--site <site>` | NAC API 与认证站点，默认 `cn` |

```bash
bytedcli --json nac admin rule delivery-status --id 123
bytedcli --json nac admin rule delivery-status --id 123 \
  --agent 192.0.2.10 \
  --agent 192.0.2.11
```

CLI 自动完成以下只读编排：归一化正反向 ID，分别检索正向与反向规则，推导唯一 NSG `rule_type`，判断反向规则是否存在并加载该类型的 Agent。用户没有指定 Agent 时固定检查接口返回的第一台，Agent 是否存活不改变选择；用户明确给出 Agent 时才添加对应 `--agent`，且所选 IP 必须来自该规则类型的 Agent 列表。不要添加 `--rule-type` 或 `--reverse-rule-exists`。

该接口开销较大。一次命令最多查询 4 个不同 Agent；Agent 不得把更多 IP 自动拆批。任何两次包含同一 Agent 的下发状态查询之间必须至少等待 5 秒，不得并发调用或用多条命令规避间隔。

返回状态按前端四阶段解释：Server 编译、Agent 拉取、Agent 转换、Engine 编译。主状态表示已确认到达的最远阶段；单个后续接口失败不会覆盖已经确认的前序证据。响应同时保留正/反向结果、每个阶段的查询状态与命中证据、版本信息、原因和 Server 编译后规则。

该命令用于“某条规则的下发情况”“下发到了哪一步”“为什么没生效”。它不同于 `nac admin compiled-rule list`：后者按规则类型列出最终编译规则集合，前者按规则 ID 诊断下发阶段。

## `nac admin compiled-rule list`

返回所选规则类型准备下发数据面的最终编译规则。服务端先读取四来源正式规则，再根据请求链路的 `X-Real-IP` 动态叠加当前 Agent 命中的发布中灰度规则，因此可能看到 `nac rule search` 查不到的灰度效果。CLI 不提供 `--agent-ip`，不要声称能任意模拟其他 Agent。

获取某个具体 NSG 规则类型已经编译并下发到数据面的全量规则。仅当用户明确要求“编译后”或“下发到数据面”时选择；普通查询继续使用返回编译前但已 normalize 规则的 `nac rule search`。

| 参数 | NAC 管理员接口输入 |
|---|---|
| `--rule-type <type>` | 路径中的具体 NSG 规则类型，必填；从 `nac admin nsg-rule-type list` 获取 |
| `--site <site>` | NAC API 与认证站点：`cn`、`boe`、`i18n-row-tt`、`i18n-bd`，默认 `cn`；兼容已有 I18N 别名 |

该接口不接受分页、Agent 或规则字段过滤，并沿用 NAC 登录与管理员鉴权。响应 `data` 是编译后规则数组；CLI 保留规则内容并附加 `current_count`、`rule_type` 与 `site`。接口不返回数据面版本，CLI 不得自行补充。

## `nac admin es-log-config get`

读取前端“配置 ES 日志采集集群”对应的管理员配置：

```bash
bytedcli --json nac admin es-log-config get
bytedcli --json nac admin es-log-config get --site boe
```

命令没有业务过滤参数，只接受可选的 NAC `--site`。返回字段为：

| 字段 | 前端含义 |
|---|---|
| `hostList` | 配置采集的集群 IP |
| `ruleTypeList` | 配置采集的 NSG 规则类型 |
| `ruleIdList` | 配置采集的规则 ID |
| `match_relation` | CLI 补充的固定关系 `or` |

三组配置是 OR 关系：一条相关日志只要命中任一已配置的集群 IP、NSG 规则类型或规则 ID，就属于 ES 采集范围。空列表表示该维度没有配置条件，不能解释为全量采集。接口仅允许 NAC Kani 超级管理员访问。

## `nac admin audit-log list`

只读查询 `GET /v1/audit/use_logs`，仅 Kani 超级管理员可访问。

| 参数 | 前端/后端过滤项 |
|---|---|
| `--page` / `--page-size` | 后端分页，默认 1 / 20 |
| `--actor <name>` | 操作人 |
| `--action <add\|create\|update\|delete\|cancel\|enable\|disable>` | 操作类型 |
| `--object <type>` | 服务端操作对象类型，完整语义见下表 |
| `--result <success\|failed>` | 操作结果 |
| `--start` / `--end` | 操作时间范围 |
| `--psm` + `--provider` + `--hfw-site` | HFW 对象详情三元组过滤，必须同时提供 |
| `--site <site>` | NAC API 与认证站点，默认 `cn` |

| `--object` 值 | 业务语义 |
|---|---|
| `rdTicket` | RD 权限申请工单 |
| `ticket` | 用户网络访问工单 |
| `nsgRule` | 用户 NSG 规则 |
| `hfwRule` | HFW 微隔离规则 |
| `hfwGroupRule` | HFW 微隔离规则组规则 |
| `nacProxyRule` | NAC Proxy 规则 |
| `xaclIdcRule` | XACL IDC 规则 |
| `xaclInternalBoeRule` | XACL BOE 内网规则 |
| `xaclInternalDevboxRule` | XACL Devbox 内网规则 |
| `clusterInfo` | NSG 集群配置 |
| `serverRule` | Yunque 管理员规则 |
| `clientCall` | NSG Client 调用 |
| `adminRuleTicket` | Yunque 管理员规则工单 |
| `matrixRule` | NAC Matrix 规则 |

`--site` 与 `--hfw-site` 不能混淆：前者选 NAC host 和认证站点，后者只匹配审计详情中的 HFW 资源站点。

## `nac admin yunque-rule search`

仅在用户明确提到 Yunque 管理员规则时使用。该命令针对 Yunque 数据执行数据库层面的 LIKE 筛选；未说明来源的规则查询使用 `nac rule search`。

管理员专属，只读查询 `POST /v1/nsg_server/rule/search`。`--rule-type` 必填，表示具体 NSG 规则类型，通常为 `xx.gw`；先从 `nac admin nsg-rule-type list` 获取。接口按前端行为只提交该字段，其余条件由 CLI 在全量结果中做不区分大小写的模糊过滤。

| 参数 | 前端过滤项 |
|---|---|
| `--rule-type <type>` | NSG 规则类型，必填 |
| `--id <rule-id>` | ID |
| `--name <name>` | Name / 规则名称 |
| `--src-ip` / `--src-psm` / `--src-port` | Src IP / Src PSM / Src Port |
| `--dst-ip` / `--dst-psm` / `--dst-domain` / `--dst-port` | Dst IP / Dst PSM / Dst Domain / Dst Port |
| `--action <accept\|drop\|pcap>` | Action：放行 / 阻断 / 抓包 |
| `--priority <n>` | 优先级，精确匹配 |
| `--username <username>` | 创建人；“我的 Yunque Rule”使用当前 `data.username` |
| `--effective-only <true\|false>` | 仅展示有效规则；排除源或目的为 loopback 的规则 |
| `--order <ascend\|descend>` | 前端排序方向 |
| `--order-by <id\|priority>` | 前端排序字段 |
| `--page` / `--page-size` | CLI 本地分页，默认 1 / 20 |
| `--site <site>` | NAC API 与认证站点 |

## `nac admin gray-rule list`

管理员专属，只读查询 `POST /v1/nsg_server/gray/rules`。灰度规则是独立表中的独立生命周期对象，不属于四种正式规则来源；正式规则匹配接口查不到它。

灰度管理字段：

| 参数 | 前端过滤项 |
|---|---|
| `--gray-rule-type <type>` | NSG 规则类型 |
| `--id <gray-or-effective-id>` | 灰度 ID；同时支持前端派生的生效 ID |
| `--op-type <add\|update\|delete>` | 操作类型 |
| `--origin-id <rule-id>` | 原规则 ID |
| `--status <releasing\|rolled-back\|completed>` | 灰度发布 / 已回滚 / 正式发布 |
| `--target-type <ip\|cluster\|all>` | 灰度生效类型 |
| `--target-value <values>` | 灰度生效范围；逗号或换行分隔 |
| `--ticket-id <ticket-id>` | 工单 ID |

嵌套灰度规则字段使用 `--rule-*`：`--rule-name`、`--rule-username`、`--rule-priority`、`--rule-proto`、`--rule-src-ip`、`--rule-src-psm`、`--rule-src-port`、`--rule-dst-ip`、`--rule-dst-psm`、`--rule-dst-domain`、`--rule-dst-port`、`--rule-action accept|drop|monitor`、`--rule-record true|false`、`--rule-reversed true|false`、`--rule-internal true|false`。

`--page` / `--page-size` 默认 1 / 20，由 CLI 按前端行为本地分页。

## `nac yunque-ticket list`

只读查询 `GET /v1/admin_rule_ticket`，但不是管理员专属。后端 ACL 允许返回本人创建、本人作为 POC，或本人有读取权限的规则类型对应工单。不要生成 `nac admin ticket list`。

| 参数 | 前端过滤项 |
|---|---|
| `--page` / `--page-size` | 后端分页，默认 1 / 20 |
| `--id <ticket-id>` | 工单 ID |
| `--source-rule-id <rule-id>` | 源规则 ID |
| `--rule-type <type>` | NSG 规则类型 |
| `--username <username>` | 用户名/创建人；“我的管理工单”使用当前 `data.username` |
| `--priority <n>` | 优先级 |
| `--src-type <ip\|psm\|domain>` + `--src <value>` | 前端源地址组合框，必须成对 |
| `--dst-type <ip\|psm\|domain\|port>` + `--dst <value>` | 前端目的地址组合框，必须成对 |
| `--name <name>` | 名称 |
| `--action <accept\|drop\|pcap>` | 动作 |
| `--status <name>` | 工单状态 |
| `--created-start` / `--created-end` | 创建时间 |
| `--expired-start` / `--expired-end` | 过期时间 |
| `--poc-emails <keyword>` | 联系人 |
| `--department <keyword>` | 部门 |
| `--gray-enabled <true\|false>` | 灰度状态 |
| `--target-type <ip\|cluster\|all>` | 灰度生效类型 |
| `--target-value <value>` | 灰度生效范围 |
| `--site <site>` | NAC API 与认证站点 |

## HFW（微隔离）只读命令

| 命令 | 对应能力 |
|---|---|
| `nac hfw policy list` | PSM 的 HFW Policy，包括全局规则、自定义规则和规则组规则 |
| `nac hfw acl list` | PSM 当前有效的 HFW ACL |
| `nac hfw permission get` | 当前身份对指定 PSM 的 HFW 访问权限 |
| `nac hfw monitor get` | HFW Agent 监控概览 |
| `nac hfw cluster list` | HFW 监控集群列表 |
| `nac hfw agent list` | 指定集群的 HFW Agent 列表 |
| `nac hfw agent status` | 指定 IP 的 HFW Agent 状态 |
| `nac hfw default-bypass get` | 指定集群的默认 Bypass 状态 |

三条命令共享参数：

| 参数 | 说明 |
|---|---|
| `--psm <psm>` | 必填，非空服务 PSM |
| `--provider <provider>` | 默认 `tce`；接受任意非空字符串，由后端判断是否合法 |
| `--hfw-site <site>` | HFW 资源站点：`cn`、`boe`、`i18n`、`i18n-bd`、`tob_cn` |
| `--site <nac-site>` | NAC API 与 ByteCloud 认证站点，默认 `cn` |

`--site` 与 `--hfw-site` 是两个不同维度：前者选择 NAC host/认证，后者进入请求 `hfwTriple.site`。

Skill/Agent 生成命令时遵循以下优先级：

- 微隔离 Policy、ACL、Permission 查询中，用户只说一个区域时，优先解释为 HFW 资源区域并显式生成 `--hfw-site`。
- 只有用户明确说 NAC API、认证站点、NAC host 或控制面站点时，才从该表达生成 `--site`。
- 例如“BOE 的 `example.hfw.service` 微隔离策略”生成 `bytedcli --json nac hfw policy list --psm example.hfw.service --hfw-site boe`。
- “TikTok ROW 的 HFW 权限”使用 `--hfw-site i18n`；`i18n-row-tt` 是 NAC API site，不是 HFW 资源站点值。

CLI 未指定 `--hfw-site` 时仍按下表自动推导。这只是执行兜底；用户明确给出 HFW 区域时，Skill 不得省略 `--hfw-site`：

| NAC `--site` | 默认 HFW `--hfw-site` |
|---|---|
| `cn` | `cn` |
| `boe` | `boe` |
| `i18n-row-tt` | `i18n` |
| `i18n-bd` | `i18n-bd` |

HFW 平台的用户规则仍用 `nac user-rule list --rule-plat hfw`，不要创建或猜测 `hfw rule list`。该命令没有 `--hfw-site`；其中的区域继续映射到 NAC `--site`，例如 `nac user-rule list --rule-plat hfw --site boe`。

### HFW 监控参数

HFW 监控命令不使用 PSM triple，也不接收 `--hfw-site`。`--site` 选择 NAC API 与认证站点，默认 `cn`。

`nac hfw cluster list`：

| 参数 | 前端过滤项 / 请求字段 |
|---|---|
| `--page <n>` / `--page-size <n>` | `page` / `pageSize`，默认 1 / 20，最大 100 |
| `--cluster <name>` | 集群名称模糊搜索 / `filterCluster` |
| `--order-by <field>` | 前端排序字段：`totalCount`、`aliveCount`、`abnormalCount`、`offlineCount`、`mortalityCount`、`ruleOverflowCount`、`ruleErrorCount`、`bypassCount` |
| `--order <ascend\|descend>` | 前端排序方向，映射为 `orderType=ASC\|DESC` |
| `--site <site>` | NAC API 与认证站点 |

`--order-by` 与 `--order` 必须一起使用。

`nac hfw agent list`：

| 参数 | 前端过滤项 / 请求字段 |
|---|---|
| `--cluster <name>` | 必填，集群名称 / `cluster` |
| `--page <n>` / `--page-size <n>` | `page` / `pageSize`，默认 1 / 20，最大 100 |
| `--ip <value>` | Agent IP 模糊搜索 / `filterAgentIP` |
| `--status <alive\|abnormal\|offline\|mortality>` | Agent 状态 / `filterAgentStatus` |
| `--order-by <agentRuleCount\|agentPSMCount>` | 前端排序字段 |
| `--order <ascend\|descend>` | 前端排序方向，映射为 `orderType=ASC\|DESC` |
| `--site <site>` | NAC API 与认证站点 |

`nac hfw agent status` 要求合法 IPv4/IPv6 `--ip`。`nac hfw default-bypass get` 要求非空 `--cluster`；它只查询默认 Bypass，不调用同路径的 POST 设置接口。

## NSG 规则类型与匹配 Agent

两条命令都经过服务端管理员鉴权：

| 命令 | API | 参数 |
|---|---|---|
| `nac admin nsg-rule-type list` | `GET /v1/nsg_rule/types` | 只有 `--site`，默认 `cn` |
| `nac admin nsg-agent list` | `GET /v1/nsg_clusters/agents` | `--rule-type <type>` 必填；`--site` 默认 `cn` |

规则类型列表返回当前用户有权使用、且 NSG 集群中实际存在的具体 `rule_type` 与显示名称。Agent 查询的 `--rule-type` 接受任意非空动态值，不由 CLI 固定枚举；优先使用列表返回值。

## NSG 管理员监控命令

以下监控命令都经过服务端管理员鉴权：

| 命令 | API |
|---|---|
| `nac admin nsg-monitor get` | `GET /v1/status/nsg_monitor` |
| `nac admin nsg-cluster list` | `GET /v1/status/nsg_cluster_list` |
| `nac admin nsg-cluster get --id <cluster-id>` | `GET /v1/status/nsg_cluster_detail/:id` |
| `nac admin nsg-cluster-name list` | `GET /v1/status/nsg_cluster_names` |

### `nac admin nsg-cluster list`

| 参数 | 前端过滤项 / 请求字段 |
|---|---|
| `--page <n>` / `--page-size <n>` | `page` / `pageSize`，默认 1 / 20 |
| `--cluster <name>` | 集群名称 / `cluster` |
| `--rule <rule-type>` | NSG 规则类型 / `rule` |
| `--agent-ip <ip>` | Agent IP / `agentIp` |
| `--psm <psm>` | PSM / `psm` |
| `--cluster-state <healthy\|unhealthy>` | 集群实际状态 / `agentStatus=0\|1` |
| `--agent-type <type>` | 类型 / `agentType` |
| `--agent-env <ToB\|IDC>` | 环境 / `agentEnv` |
| `--expected-status <online\|offline\|deprecated>` | 预期状态 / `expectedStatus` |
| `--deploy-type <nat\|p4\|p4rt\|virline\|xgw>` | 部署类型 / `deployType` |
| `--metric-status <active\|dead>` | Agent 打点状态 / `metricStatus=0\|1` |
| `--tt <true\|false>` | TT / `tt` |
| `--site <site>` | NAC API 与认证站点，默认 `cn` |

`--agent-type` 使用前端值：`boeprod`、`devprod`、`dmz`、`finance`、`gaea`、`internet`、`others`、`tobtoc`、`xboard`。`--agent-env` 只接受前端选项 `ToB`、`IDC`。

### `nac admin nsg-cluster get`

- `--id <cluster-id>` 必填；接受列表的短 ID 或完整 `nsg-cluster-*` ID。
- 短 ID 会在请求路径中自动添加 `nsg-cluster-`。
- `--site <site>` 默认 `cn`。

### `nac admin nsg-cluster-name list`

只有 `--site <site>`，默认 `cn`。返回前端集群名称选择器使用的完整名称列表。

## NSG Agent 参数

| 命令 | API | 参数 |
|---|---|---|
| `nac admin nsg-agent-param list` | `GET /v1/nsg_agent/params/list`，经 NAC 代理 | `--ip <agent-ip>` 必填；`--site` 默认 `cn` |

`--ip` 必须是合法 IPv4 或 IPv6。Agent 参数名称和文本解释使用前端参数面板。

## Matrix Rule

两条命令都经过服务端管理员鉴权：

| 命令 | API |
|---|---|
| `nac admin matrix-rule list` | `GET /v1/matrix/rules` |
| `nac admin matrix-rule get --id <rule-id>` | `GET /v1/matrix/rules/:id` |

### `nac admin matrix-rule list`

| 参数 | 请求过滤项 |
|---|---|
| `--page <n>` / `--page-size <n>` | 默认 1 / 20 |
| `--src-region <region>` | 源区域 |
| `--src-provider <provider>` | 源 provider |
| `--src-addr-type <ip\|psm\|domain>` | 源地址类型 |
| `--dst-region <region>` | 目的区域 |
| `--dst-provider <provider>` | 目的 provider |
| `--dst-addr-type <ip\|psm\|domain>` | 目的地址类型 |
| `--allowed <unsupported\|supported\|no-isolation>` | 隔离支持状态 |
| `--site <site>` | NAC API 与认证站点，默认 `cn` |

`unsupported/supported/no-isolation` 分别映射为线值 `0/1/2`。

### `nac admin matrix-rule get`

- `--id <rule-id>` 必填，正整数。
- `--site <site>` 默认 `cn`。

## Dialtest（拨测）

三条命令是 `nac admin` 下的独立资源命令。`--site` 均为 NAC API 与认证站点，默认 `cn`。

### `nac admin dialtest-task list`

只读查询 `POST /v1/dialtest/task/list`，返回任务及每个协议最近一次运行结果。

| 参数 | 前端过滤项 / 请求字段 |
|---|---|
| `--dialtest-env <tob\|toc>` | 拨测环境，默认 `tob` |
| `--page <n>` / `--page-size <n>` | 默认 1 / 20；`--page-size` 映射请求体 `size` |
| `--id <task-id>` | 任务 ID |
| `--name <name>` | 策略名称 |
| `--src-agent <name>` | 源 Agent |
| `--dest-type <agent\|external>` | 目的类型 |
| `--dst-agent <name>` | 目的 Agent |
| `--dst-ip <ip>` / `--dst-port <port>` / `--dst-domain <domain>` | 外部目的信息 |
| `--ip-version <ipv4\|ipv6>` | IP 版本 |
| `--protocols <tcp,udp,icmp,http>` | 协议，多值逗号分隔 |
| `--expected-actions <accept,deny>` | 预期动作，多值逗号分隔 |
| `--traversed-cluster <cluster>` | 关联 NSG 集群 |
| `--status <enable\|disable>` | 任务状态 |

### `nac admin dialtest-agent list`

只读查询 `GET /v1/dialtest/agent/list`。

| 参数 | 前端过滤项 |
|---|---|
| `--dialtest-env <tob\|toc>` | 拨测环境，默认 `tob` |
| `--page <n>` / `--page-size <n>` | 默认 1 / 20 |
| `--id <agent-id>` / `--name <name>` | Agent ID / 名称 |
| `--status <online\|offline>` | Agent 状态 |
| `--deploy-type <HOST\|TCE>` | 部署类型 |
| `--vdc <vdc>` | VDC |
| `--public-ipv4` / `--public-ipv6` | Public IP |
| `--http-domain` / `--http-port` | HTTP Domain / Port |
| `--tcp-port` / `--udp-port` | TCP / UDP Port |
| `--psm` / `--server-psm` | PSM / Server PSM |
| `--cluster` | Cluster |
| `--manage-port` | Manage Port |

### `nac admin dialtest-server-psm list`

只读查询 `GET /v1/dialtest/server_psm/list`。除 `--site` 外没有过滤参数，返回前端配置的拨测服务环境/Server PSM 选择项。

## 时间格式

沿用 bytedcli 公共格式：Unix 秒/毫秒、RFC3339、`YYYY-MM-DD`、`1h ago` 等相对时间。日期型 start 从当天 00:00:00 开始，日期型 end 包含当天至 23:59:59；start 不得晚于 end。MGT Rule 和用户 Ticket 向 NAC 发送 Unix 秒；Yunque Ticket 按前端请求发送 ISO 时间。
