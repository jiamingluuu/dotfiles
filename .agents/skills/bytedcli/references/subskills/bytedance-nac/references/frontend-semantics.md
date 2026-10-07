# NAC 前端过滤语义与返回解释

## 目录

- [MGT Rule 与 Ticket](#mgt-rule-过滤条件)
- [Yunque Rule、Gray Rule 与管理工单](#yunque-rule管理员规则过滤条件)
- [HFW 查询与返回解释](#hfw-查询上下文)
- [NSG 监控、规则类型与 Agent](#nsg-监控过滤条件)
- [规则检索、精确匹配与审计](#规则检索与精确匹配)
- [Matrix Rule](#matrix-rule)
- [Dialtest（拨测）](#dialtest拨测过滤条件)

本 reference 解决两件事：

1. 把用户的中文查询表达映射到前端真实过滤项和 CLI 参数。
2. 解释无法从字段名直接判断的返回值。

不建立完整字段翻译表。`ip`、`domain`、`src`、`dst` 等通用字段，以及字段名和前端中文可直接对应的字段，不在返回语义表中重复解释。

## 所有权语义

“我的”适用于所有规则查询接口，固定表示规则创建人是当前登录用户；它不是 MGT Rule 的同义词，也不能参与接口选择。先根据用户明确的规则来源和查询能力完成路由，再执行 `auth userinfo` 取得 `data.username`：

| 已选查询接口 | “我的”对应条件 |
|---|---|
| 未说明来源的正式规则检索 | `nac rule search --username <username>` |
| MGT Rule / 用户规则 | `nac user-rule list --creator <username>` |
| Yunque Rule / 管理员规则 | `nac admin yunque-rule search ... --username <username>` |
| Gray Rule / 灰度规则 | `nac admin gray-rule list --rule-username <username>` |

查询接口没有创建人参数时，使用 JSON 返回中的可靠创建人字段做本地严格过滤；没有可靠字段时说明当前接口无法表达“我的”，不得把 ACL 可见全集当作本人创建。

## MGT Rule 过滤条件

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| MGT Rule ID、用户规则 ID、default/tob 表规则 ID | 用户规则数据库筛选中的规则 ID | `--id <rule-id>` |
| 工单 ID、来源工单、工单关联规则 | 工单 ID | `--ticket-id <ticket-id>` |
| 规则平台、NSG/HFW/NAC Proxy/XACL 平台规则 | 规则平台 | `--rule-plat <platform>` |
| 启用、已启用、生效 | 生效状态：启用 | `--enabled true` |
| 禁用、已禁用、未生效 | 生效状态：禁用 | `--enabled false` |
| 生效时间、开始日期、结束日期、某段时间内生效 | 生效时间 | `--start <time> --end <time>` |
| 规则属性、default 表、ToB 表 | 规则属性 | `--table-type default\|tob` |
| 创建人、某人创建的规则 | 创建人 | `--creator <username>` |
| 我的 MGT Rule、我的用户规则 | 创建人是当前登录用户 | 先取 `auth userinfo` 的 `data.username`，再传 `--creator` |
| 所有规则、可见规则、我能看到的规则 | 后端 ACL 可见范围 | 不传 `--creator` |

规则平台使用前端值：`nsg`、`hfw`、`nac_proxy`、`xacl_idc`、`xacl_internal_devbox`、`xacl_internal_boe`。不要把这些平台值称为规则类型。

只有规则平台为 `nsg` 的 MGT Rule 才具有具体 NSG `rule_type`。NSG 规则来源包括：Honeycomb 的 MGT Rule NSG 部分、NSG Server 的 Yunque Rule、NAC Security Center 的 `nac_sec` Rule，以及 TCC 的 TCC Rule。

注意：MGT Rule 的 `--start/--end` 对应前端“生效时间”，不要称为“创建时间”过滤。

MGT Rule 前端列表把 `attributes` 放在点击后展开的规则详情中。默认文本输出的“规则详情”只提示使用 `--json` 查看，不直接展开未完成前端语义核对的枚举、布尔值或组合字段；JSON 仍完整保留原始属性。

## Ticket 过滤条件

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| 工单 ID | 工单 ID | `--id <ticket-id>` |
| 源地址、源 IP | 源地址 | `--src-type ip --src <ip>` |
| 源 PSM、访问源服务 | 源地址 | `--src-type psm --src <psm>` |
| 目的地址、目的 IP | 目的地址 | `--dst-type ip --dst <ip>` |
| 目的 PSM、访问目的服务 | 目的地址 | `--dst-type psm --dst <psm>` |
| 目的域名 | 目的地址 | `--dst-type domain --dst <domain>` |
| 创建时间、开始日期、结束日期 | 创建时间 | `--start <time> --end <time>` |
| 创建人、某人创建的工单 | 创建人 | `--creator <username>` |
| 所属部门、部门 | 所属部门 | `--department <keyword>` |
| 工单状态 | 工单状态 | `--status <name>`，见下表 |
| 放行、允许访问 | 隔离动作：放行 | `--action accept` |
| 阻断、拒绝访问 | 隔离动作：阻断 | `--action drop` |
| 我的工单 | 创建人是当前登录用户 | 先取 `auth userinfo` 的 `data.username`，再传 `--creator` |
| 所有工单、可见工单、我作为 POC 的工单 | 后端 ACL 可见范围 | 不传 `--creator` |

源和目的地址的 type/value 必须成对，不得只生成其中一个参数。

### 工单状态

| 前端中文 | CLI 语义名 | 数字 |
|---|---|---:|
| 审批中 | `in-approval` | 1 |
| 审批通过 | `accepted` | 2 |
| 审批拒绝 | `rejected` | 3 |
| 执行中 | `in-progress` | 4 |
| 执行失败 | `execute-fail` | 5 |
| 已生效 | `exec-success` | 6 |
| 禁用中 | `disabling` | 7 |
| 已禁用 | `disabled` | 8 |
| 过期处理中 | `expiring` | 9 |
| 已过期 | `expired` | 10 |
| 已取消 | `canceled` | 11 |
| 已废弃 | `deprecated` | 12 |

## Yunque Rule（管理员规则）过滤条件

Yunque Rule 查询使用 `nac admin yunque-rule search`，并且前端必须先选择具体 NSG 规则类型。值通常为 `xx.gw`，未知时先执行 `nac admin nsg-rule-type list`，不得填规则平台值 `nsg`：

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| 管理员规则、Yunque Rule、某 NSG 规则类型 | NSG 规则类型 | `--rule-type <type>`，必填 |
| 规则 ID | ID | `--id <rule-id>` |
| 规则名称 | Name | `--name <name>` |
| 源 IP / PSM / 端口 | Src IP / PSM / Port | `--src-ip` / `--src-psm` / `--src-port` |
| 目的 IP / PSM / 域名 / 端口 | Dst IP / PSM / Domain / Port | `--dst-ip` / `--dst-psm` / `--dst-domain` / `--dst-port` |
| 放行 | Action | `--action accept` |
| 阻断 | Action | `--action drop` |
| 抓包 | Action | `--action pcap` |
| 优先级 | 优先级 | `--priority <n>` |
| 创建人 | 创建人 | `--username <username>` |
| 我的 Yunque Rule、我的管理员规则 | 创建人是当前登录用户 | 先取 `auth userinfo` 的 `data.username`，再传 `--username` |
| 仅展示有效规则 | 前端有效规则开关 | `--effective-only true` |

接口本身不支持前端模糊搜索。CLI 与前端一致：请求只发送 `rule_type`，其余条件在返回列表上本地过滤。

`--effective-only true` 对应前端“仅展示有效规则”，会排除源或目的含回环地址的规则。`--effective-only false` 与不传该参数都保留全部规则，不得反向过滤出无效规则。

### Yunque Rule 返回语义

| 返回值 | 前端业务含义 |
|---|---|
| Yunque Rule `action=ACCEPT` | 放行 |
| Yunque Rule `action=DROP` | 阻断 |
| Yunque Rule `action=PCAP` | 抓包 |
| `state=0` | 未启用 |
| `state=1` | 生效中 |
| `reversed=true/false` | 双向规则：是 / 否 |

## Gray Rule（灰度规则）过滤条件

Gray Rule 使用 `nac admin gray-rule list`。用户说“灰度规则”时不要路由到 Yunque Rule，因为灰度规则是独立生命周期对象。

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| 灰度 ID、生效 ID | 灰度 ID | `--id <id>` |
| 新增 / 更新 / 删除 | 操作类型 | `--op-type add\|update\|delete` |
| 灰度发布 | 状态 | `--status releasing` |
| 灰度发布已回滚 | 状态 | `--status rolled-back` |
| 正式发布 | 状态 | `--status completed` |
| 灰度生效类型 | 生效类型 | `--target-type ip\|cluster\|all` |
| 灰度生效范围 | 生效范围 | `--target-value <values>` |
| 原规则 ID | 原规则 ID | `--origin-id <rule-id>` |
| 工单 ID | 工单 ID | `--ticket-id <ticket-id>` |
| 灰度规则中的创建人 | 灰度规则字段：创建人 | `--rule-username <username>` |
| 灰度规则中的动作 | 灰度规则字段：Action | `--rule-action accept\|drop\|monitor` |

其他嵌套规则条件统一使用 `--rule-*`，避免与灰度管理对象自身字段混淆。

### Gray Rule 返回语义

| 返回值 | 前端业务含义 |
|---|---|
| Gray Rule `RELEASING` | 灰度发布 |
| `ROLLED_BACK` | 灰度发布已回滚 |
| `COMPLETED` | 正式发布 |
| `ADD/UPDATE/DELETE` | 新增 / 更新 / 删除 |
| 嵌套规则 `ACCEPT/DROP/MONITOR` | 放行 / 阻断 / 抓包 |
| `30000000 + gray ID` | 正向生效 ID |
| 双向规则的 `130000000 + gray ID` | 反向生效 ID |

## Yunque 管理工单过滤条件

管理员规则工单使用 `nac yunque-ticket list`，不是 `nac admin ticket list`。名称中的“管理员规则”描述工单申请的规则类型，不表示列表接口只允许管理员调用。

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| 管理员工单、Yunque 管理工单 | 管理员规则工单列表 | `nac yunque-ticket list` |
| 我的管理工单 | 用户名是当前登录用户 | 先取 `auth userinfo` 的 `data.username`，再传 `--username` |
| 所有/可见/我能看到的管理工单 | 后端 ACL 可见范围 | 不传 `--username` |
| 源 IP / PSM / 域名 | 源地址 type/value | `--src-type ... --src ...` |
| 目的 IP / PSM / 域名 / 端口 | 目的地址 type/value | `--dst-type ... --dst ...` |
| 创建时间 | 创建时间 | `--created-start` / `--created-end` |
| 过期时间 | 过期时间 | `--expired-start` / `--expired-end` |
| 联系人、POC | 联系人 | `--poc-emails <keyword>` |
| 开启灰度 / 未开启灰度 | 灰度状态 | `--gray-enabled true\|false` |

工单状态沿用上面的 1–12 映射；动作额外支持 `pcap`。返回中的 `CREATE/UPDATE` 显示为创建/更新，`grayEnabled` 显示为开启灰度/未开启灰度，`approvalUrl` 仍由 `approvalFlowId` 本地派生。

## HFW 查询上下文

`i18n-row-tt`、`i18n-tt`、`i18n` 表达同一个 TikTok ROW 逻辑站点，但分别属于 NAC API site、ByteCloud 认证 site 和 HFW resource site。自然语言出现任一标识时，先归一为 TikTok ROW，再按当前参数维度选择 `--site i18n-row-tt`、认证 `i18n-tt` 或 `--hfw-site i18n`；这些线协议值不能直接互换。

| 用户表达 | CLI 参数 | 含义 |
|---|---|---|
| PSM、服务 | `--psm <psm>` | 前端当前选择的 PSM |
| provider、资源提供方、TCE | `--provider <provider>` | HFW triple 的 provider，默认 `tce` |
| HFW 站点、资源站点、资源环境 | `--hfw-site <site>` | HFW triple 的 site |
| NAC 站点、API 站点、认证站点 | `--site <site>` | NAC host 与 ByteCloud 认证路由 |

`--site` 和 `--hfw-site` 不是同一个过滤维度。微隔离 Policy、ACL、Permission 查询中，用户说“BOE 的”“某区域/环境的”“TikTok ROW 的”但没有明确限定 API/认证时，优先视为 HFW 资源区域：

| 用户区域表达 | 默认 CLI 参数 |
|---|---|
| 中国、CN | `--hfw-site cn` |
| BOE | `--hfw-site boe` |
| TikTok ROW、I18N ROW | `--hfw-site i18n` |
| ByteDance I18N、I18N BD | `--hfw-site i18n-bd` |
| ToB CN | `--hfw-site tob_cn` |

只有“NAC API 走 BOE”“认证站点是 TikTok ROW”“NAC 控制面使用 i18n-row-tt”等明确表述才映射到 `--site`。如果两个维度都出现，分别保留；例如“NAC API 走 CN，查询 BOE 资源”使用 `--site cn --hfw-site boe`。

CLI 的自动推导只是未传 `--hfw-site` 时的兜底。用户已明确资源区域时，不得依赖推导省略 `--hfw-site`。这条规则不适用于 `nac user-rule list --rule-plat hfw`：该命令没有 `--hfw-site`，其中的区域使用 `--site`。

## 返回字段解释约束

文本输出必须覆盖前端展示字段，并使用前端已经确认的概念。明显字段和直接翻译字段不需要额外维护映射表，但不能因此从输出中遗漏。

禁止直接展示非显然的后端枚举、布尔值和组合字段。方向、动作、状态等共同组成一个前端概念时，必须整体解释，不得拆成后端字段和值逐项输出。前端未展示的字段不进入默认文本输出；未知或未验证字段只保留在 JSON 中。

对后端一次性返回的完整列表，结果元数据只报告 `current_count`。不得伪造 `page`、`page_size` 或 `has_more`，以免让用户误以为还能翻页。

### HFW Policy 与 ACL

| 返回值 | 业务含义 |
|---|---|
| `globalRuleState=false` 或 `globalRule.state=false` | 全局默认策略未配置；PSM 出内网默认策略和 PSM 出公网默认策略都显示“策略未配置，默认放行” |
| `globalRuleState=true` 或 `globalRule.state=true` | 全局默认策略已配置；此时才解释默认规则动作或允许位 |
| `allowInner=true` | PSM 出内网默认策略：允许 |
| `allowInner=false` | PSM 出内网默认策略：阻断 |
| `allowOuter=true` | PSM 出公网默认策略：允许 |
| `allowOuter=false` | PSM 出公网默认策略：阻断 |
| `globalInnerRule.action=accept` | PSM 出内网默认策略：允许 |
| `globalInnerRule.action=deny/drop` | PSM 出内网默认策略：阻断 |
| `globalOuterRule.action=accept` | PSM 出公网默认策略：允许 |
| `globalOuterRule.action=deny/drop` | PSM 出公网默认策略：阻断 |
| 规则 `action=accept` | 放行 |
| 规则 `action=deny/drop` | 阻断 |

Policy 和 ACL 的两项全局默认策略只表示出方向，不表示入方向。当全局策略状态为“未配置”时，接口中的 `allowInner`、`allowOuter` 和默认全局规则动作属于占位数据，必须忽略；不得据此分别输出允许、阻断或“配置值”。状态字段缺失或未知时保持“策略状态未知”，不得套用默认放行。

Policy 和 ACL 的默认文本输出只展示前端自定义策略列：策略 ID、策略动作、生效区域、源信息、目的信息、协议、来源、优先级。自定义规则按前端页签分组：`dir=out` 进入“出流量自定义策略”，`dir=in` 进入“入流量自定义策略”，`dir` 缺失或为 `all` 时同时进入两组；方向不再单独显示。规则组数据在当前前端页面未展示，不进入默认文本输出。

### HFW PSM 权限

| 返回值 | 业务含义 |
|---|---|
| `adminAccess=true` | Honeycomb 平台管理员可修改当前 PSM 的微隔离规则 |
| `ownerAccess=true` | PSM Owner 可修改当前 PSM 的微隔离规则 |
| `apiAccess=true` | 允许通过 API 修改当前 PSM 的微隔离规则 |
| `normalUserAccess` | 后端普通用户权限位；当前前端不展示该配置项，不补充未经证实的 UI 含义 |

这些字段是指定 PSM 的规则修改权限配置，不是当前登录人的 `nac permission status`。

### HFW 监控过滤条件

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| HFW/微隔离监控概览 | HFW Agent 监控概览 | `nac hfw monitor get` |
| 集群名称、集群名 | 集群名称 | `nac hfw cluster list --cluster <name>` |
| Agent IP、IP 模糊搜索 | Agent IP | `nac hfw agent list --cluster <name> --ip <value>` |
| 存活 Agent | Agent 状态：存活 | `--status alive` |
| 异常 Agent | Agent 状态：异常 | `--status abnormal` |
| 离线 Agent | Agent 状态：离线 | `--status offline` |
| 死亡 Agent | Agent 状态：死亡 | `--status mortality` |
| Agent 规则数排序 | Agent 规则数 | `--order-by agentRuleCount --order ascend\|descend` |
| PSM 数排序 | PSM | `--order-by agentPSMCount --order ascend\|descend` |
| Agent 状态详情 | 查询 HFW Agent 状态 | `nac hfw agent status --ip <ip>` |
| 集群默认 Bypass | 集群配置中的默认 Bypass | `nac hfw default-bypass get --cluster <name>` |

集群列表排序字段使用前端 wire 值；`--order-by` 与 `--order` 必须成对。HFW 监控接口只有 NAC `--site`，不要生成 `--hfw-site`、`--psm` 或 `--provider`。

### HFW 监控返回语义

| 返回字段或字段组合 | 业务含义 |
|---|---|
| `clusterCount` | HFW 集群总量；不是规则总量 |
| `clusterAliveCount` | 健康集群数；后端标准是死亡 Agent 比例不超过 1% |
| `clusterCount - clusterAliveCount` | 异常集群数；后端标准是死亡 Agent 比例超过 1% |
| `agentAliveCount + agentAbnormalCount + agentOfflineCount + agentMortalityCount` | Agent 总量 |
| `agentAbnormalCount` | 异常 Agent 数；心跳间隔超过 65 秒且不超过 180 秒 |
| `agentRuleErrorCount` | 存在规则异常的 Agent 数；不是异常规则条数 |
| `agentRuleOverflowCount` | 存在规则溢出的 Agent 数；不是规则条数 |
| `agentBypassCount` | 处于 Bypass 的 Agent 数 |
| Agent `agentStatus=alive/abnormal/offline/mortality` | 存活 / 异常 / 离线 / 死亡 |
| Agent `agentBypassStatus=bypass/unbypass` | Bypass 已开启 / 已关闭 |
| 集群默认 Bypass `bypass/unbypass` | 默认 Bypass 已开启 / 已关闭 |

前端当前把 `clusterCount` 绑定到“规则总量”、把 `agentAbnormalCount` 绑定到“异常集群”，这两个绑定与后端定义冲突，CLI 不复刻。集群列表中的“集群状态”由前端固定显示为健康，后端列表没有相应状态字段，CLI 不伪造该列。Agent 状态详情中的 `stat`、`ruleStat` 业务语义未知，默认文本不展示，只保留在 JSON 中。

### Ticket 与身份

| 返回值 | 业务含义 |
|---|---|
| Ticket `status=1..12` | 使用上面的前端工单状态表解释 |
| Ticket `action=ACCEPT/DROP` | 放行 / 阻断 |
| `approvalUrl` | 由 `approvalFlowId` 本地派生；不是额外调用 Kani API 获取 |
| `approvalUrl=null` | 当前工单没有可用审批流链接 |
| I18N `isRd=null` | 该站点未执行 RD 检查，不能解释成“当前用户不是 RD” |
| `rdSupported=false` | 当前 NAC 站点不执行 RD 检查 |

## NSG 监控过滤条件

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| 集群名称、集群名 | 集群名称 | `--cluster <name>` |
| NSG 规则类型 | NSG 规则类型 | `--rule <rule-type>` |
| Agent IP | Agent IP | `--agent-ip <ip>` |
| PSM | PSM | `--psm <psm>` |
| 健康集群、实际状态健康 | 集群状态：健康 | `--cluster-state healthy` |
| 异常集群、实际状态异常 | 集群状态：异常 | `--cluster-state unhealthy` |
| Agent 类型、类型 | 类型 | `--agent-type <type>` |
| Agent 环境、环境、ToB、IDC | 环境 | `--agent-env ToB\|IDC` |
| 预期在线、预期离线、预期废弃 | 预期状态 | `--expected-status online\|offline\|deprecated` |
| 部署类型 | 部署类型 | `--deploy-type <type>` |
| Agent 打点正常、打点正常 | Agent 打点状态：正常 | `--metric-status active` |
| Agent 打点异常、打点异常 | Agent 打点状态：异常 | `--metric-status dead` |
| TT 开启 / 关闭 | TT | `--tt true\|false` |

“集群状态”没有额外限定时，按前端含义映射为实际集群状态 `--cluster-state`，不要映射到 `--expected-status`。

### NSG 监控返回语义

| 返回值 | 业务含义 |
|---|---|
| Cluster `state=0` | 集群实际状态健康 |
| Cluster `state=1` | 集群实际状态异常 |
| Cluster `status=online/offline/deprecated` | 集群预期状态为在线 / 离线 / 已废弃 |
| Agent `status=online/offline` | Agent 在线 / 离线 |
| Agent `metric_status=active/dead` | Agent 打点正常 / 打点异常 |
| Agent `bgp_bypass=0` | BGP Bypass 已开启 |
| Agent `bgp_bypass` 为其他数值 | BGP Bypass 已关闭 |

NSG 集群列表返回的 TT `0/1` 缺少稳定业务语义，默认文本不展示，只保留在 JSON 中。`diagnose` 没有前端展示位置，同样只保留在 JSON。

当前前端只展示 BGP Bypass。`nlb_bypass`、`force_bypass` 不进入默认文本输出；仍保留在 JSON 原始结构中。

## NSG 规则类型与匹配 Agent

| 用户表达 | 前端能力 | CLI |
|---|---|---|
| 有哪些 NSG 规则类型、管理员规则类型列表 | 当前用户可用规则类型 | `nac admin nsg-rule-type list` |
| 某规则类型有哪些 Agent/FW 客户端、用于匹配的客户端 | 规则匹配的 FW 客户端 | `nac admin nsg-agent list --rule-type <type>` |

`rule_type` 和 `rule_name` 分别是选择器值与显示名称。匹配 Agent 的 `alive=true/false` 在前端显示为“存活/异常”；文本输出不得直接展示布尔值。

## 规则检索与精确匹配

| 用户表达 | 前端能力 | CLI |
|---|---|---|
| MGT Rule ID、用户规则 ID、default/tob 表规则 ID | 用户规则数据库筛选 | `nac user-rule list --id <rule-id>` |
| Yunque 管理员规则 | Yunque 数据库筛选 | `nac admin yunque-rule search` |
| 规则 ID、这条规则（未说明来源） | 跨来源语义规则检索 | `nac rule search --id <rule-id>` |
| 规则检索、模糊匹配、查所有会匹配的规则 | 规则检索 | `nac rule search` |
| 全部正式 NSG 规则、最全面的正式规则查询、四种正式来源规则 | 跨类型正式规则检索 | `nac rule search`，不附加 `--rule-type` |
| 灰度规则、发布中灰度规则 | 独立灰度规则表 | `nac admin gray-rule list`；`nac rule search` 查不到 |
| 编译后或下发数据面的最终规则 | 正式规则加当前请求命中的灰度叠加结果 | `nac admin compiled-rule list --rule-type <type>` |
| 精确匹配、让 FW 客户端判断命中规则 | 精确匹配 | `nac admin rule search` |
| 某条规则的下发情况、下发到哪一步、为什么没生效 | 规则下发状态 | `nac admin rule delivery-status --id <rule-id>` |
| IP 到域名、源 IP 目的 Domain | 严格 Host 地址类型 | `--src-ip '*'` 且源侧其他 Host 字段为 `empty`；`--dst-domain '*'` 且目的侧其他 Host 字段为 `empty` |
| PSM 到 PSM | 严格 Host 地址类型 | `--src-psm '*'` / `--dst-psm '*'`，两侧其他 Host 字段分别为 `empty` |
| 源/目的 PSM ID、TCE PSM ID | 返回字段 `psm_id` | `--src-tce-psm` / `--dst-tce-psm` |
| 内部规则 | Internal | `--internal true\|false` |
| 记录日志、流量记录 | Record | `--record true\|false` |
| 双向规则、自动反向规则 | Reversed | `--reversed true\|false` |
| 规则来源 | Source | `--source <value>` |

来源专用路由优先：只有明确提到 MGT Rule、用户规则、default 表或 tob 表才使用 `nac user-rule list`；只有明确提到 Yunque 管理员规则才使用 `nac admin yunque-rule search`。这两条命令都是数据库层面的 LIKE 筛选。明确查询灰度对象或编译后全量集合时，分别使用 gray-rule 或 compiled-rule。

“下发情况”“下发阶段”“为什么没生效”表示对一条规则做下发链路诊断，优先级高于 compiled-rule 全量集合路由。只要用户提供 Rule ID，就使用 `nac admin rule delivery-status --id <rule-id>`；CLI 自动推导规则类型、反向规则和 Agent，不向用户索取这些内部参数。

其余匹配意图按“显式意图优先，条件完整度辅助”选择：

| 用户意图与条件 | 路由 |
|---|---|
| 明确要所有符合条件、覆盖候选的规则，或明确说模糊查询、规则列表 | `nac rule search`；即使给出了完整五元组也不改成精确匹配 |
| 明确要数据面实际命中、最终命中、指定 Agent 命中，或明确说精确匹配 | `nac admin rule search`；即使只给了局部条件也尊重该意图 |
| 未明确意图，但给出了具体源、具体目的、端口、协议等接近完整五元组 | 倾向精确匹配；缺少 `rule_type` 或 Agent 时先发现或向用户确认 |
| 未明确意图，只给出 IP、CIDR、Domain、PSM 等局部条件 | 倾向模糊匹配，查询编译前所有符合条件的规则 |
| 仍然不确定，或用户明确要求两种都查 | 可以同时执行模糊与精确查询；精确查询仍须先确定 `rule_type` 和 Agent |

不得根据条件完整度推翻用户的明确意图，也不得任意选择 Agent。两类查询同时执行时，输出必须分成“编译前符合条件的规则”和“指定 Agent 数据面实际命中的规则”，不能合并计数或混称为同一种命中。

`nac rule search` 是最全面的 NSG 正式规则查询接口，查询编译前但已 normalize 的规则并返回所有符合条件的结果，覆盖 MGT/Honeycomb、Yunque、`nac_sec`/NAC Security Center 和 TCC 四种正式规则来源。`--rule-type` 可选；省略时查询全部规则类型。所有条件都省略是合法的全量 ACL 可见正式规则查询。灰度规则位于独立表，该接口查不到。

执行查询前必须先提取用户表达的全部过滤条件，并把接口可表达的五元组、规则类型、所有权、来源和其他元数据条件下推到服务端。只有明确要求全量时才可直接使用无过滤查询；服务端无法表达的条件只能在已充分收窄的结果上做本地过滤。

五元组条件使用 `any/all/empty/value/precise` 五态；已有规则字段使用 `all/empty/concrete` 三态。自然语言中的“不限”“只匹配全量”“为空”“包含具体值且允许全量规则”“只匹配具体规则”必须分别映射到正确模式。后端请求缺少五元组字段表示 `empty`，CLI 省略选项时必须发送 `*` 才表示 `any`。Host 字段只在已有规则预处理状态时互相影响；匹配阶段每个字段独立，最后组合各字段谓词。`empty` Host 字段表示该字段没有值且同侧至少一个其他 Host 字段有值。所有详细映射、多值规则和用户描述组合见 [rule-search.md](rule-search.md)，不得复用旧匹配说明。

“地址类型是 A 到 B”“源是某 Host 类型”“目的使用某 Host 类型”等描述必须使用 [rule-search.md](rule-search.md) 的严格 Host 地址类型模板在服务端表达：选中字段用 `any`，同侧其他三个 Host 字段用 `empty`。能由该组合表达时，不得先查询全量规则再用 `jq` 或本地字段判断。包含 OR 的地址类型描述拆成多次服务端查询，并按 `rule_type + id` 去重。

规则检索来源的业务语义：`sql` 是 Yunque 管理员规则，`tcc` 是 TCC 规则，`mgt` 是 MGT 用户规则，`nac`/`nac2.0`/`nac3.0` 是 NAC 安全中心规则。文本回答必须使用业务名称，不直接解释为裸来源值。

`nac admin rule search` 以指定 Agent 数据面加载的编译后规则执行匹配，返回流量实际命中的规则。精确匹配返回没有规则 ID 时，前端语义是“未匹配到具体规则”。不要把返回中的 Agent 默认动作描述为命中了一条规则。

### 规则下发状态

`nac admin rule delivery-status` 对齐前端“规则下发状态”页。CLI 先按归一化后的正向 ID 和反向 ID 查询源规则，再推导唯一 `rule_type` 和反向规则是否存在；随后获取该类型的 Agent。用户未指定 Agent 时固定选择接口返回的第一台，即使其显示异常也仍用于本次检查；用户明确指定时可选择该列表中的 1–4 台。结果应说明全部所选 IP 及其列表状态。

下发状态接口开销较大。一次最多选择 4 个不同 Agent，不自动拆批；任何两次包含同一 Agent 的查询至少间隔 5 秒，不并发查询同一 Agent。

下发阶段固定解释为 Server 编译、Agent 拉取、Agent 转换、Engine 编译。每个方向都展示主状态、子状态、置信度、失效阶段和判断依据；接口证据展示查询状态、是否命中或可用、Server 版本、转换实例数、Agent/FW 版本、Engine 状态和是否正在更新。动作转换为放行、阻断或抓包，布尔值转换为是/否，不直接向用户展示状态码或裸布尔值。

主状态是当前证据确认的最远下发阶段；后续观察失败不否定已确认的前序阶段。规则未找到、同一 ID 对应多个规则类型、或该规则类型没有 Agent 时，报告 CLI 的结构化错误，不能改用 compiled-rule 结果冒充下发状态。

## 编译后数据面规则

仅当用户明确说“编译后规则”或“下发到数据面的规则”时路由到 `nac admin compiled-rule list --rule-type <type>`。普通的正式规则列表、ID 查询、模糊查询或匹配仍使用 `nac rule search`；后者返回编译前但已 normalize 的四来源正式规则。明确查询灰度对象时使用 `nac admin gray-rule list`。compiled-rule 返回准备下发数据面的最终集合，可能包含依据请求链路 `X-Real-IP` 动态叠加的灰度效果。

该接口没有前端分页或字段过滤器，唯一业务输入是具体 NSG 规则类型；未知时先使用 `nac admin nsg-rule-type list`。`current_count` 表示本次返回的编译后规则数；接口不返回数据面版本，不得推断或补充。编译动作必须转换为业务语义：`permit` 表示放行，`deny` 表示阻断，`pcap` 表示抓包，`reverse` 表示反向处理。布尔值按字段整体显示为“记录命中：是/否”“内部规则：是/否”，不得展示裸布尔值。

该命令通过 NAC 管理员接口调用，`--site` 选择标准 NAC API 与认证站点，支持 `cn`、`boe`、`i18n-row-tt`、`i18n-bd` 及已有兼容别名；它不是 HFW 资源站点。

## ES 日志采集配置

“哪些日志会被 ES 采集”“ES 采集了哪些 NSG 集群/规则类型/规则 ID”使用 `nac admin es-log-config get`。前端三个配置项分别是集群 IP、NSG 规则类型和规则 ID；三项是 OR 关系，任一已配置条件命中即进入 ES 采集范围。

文本回答必须整体说明“任一条件命中即采集”，不能把三组列表并列后留给用户猜测关系。某一列表为空表示该维度未配置采集条件，不表示该维度匹配全部，也不能据此宣称所有日志都会被采集。

## NAC 审计日志

| 用户表达 | 过滤项 | CLI 参数 |
|---|---|---|
| 谁操作的、操作人 | Actor | `--actor <name>` |
| 增加/创建/更新/删除/取消/启用/禁用 | Action | `--action add\|create\|update\|delete\|cancel\|enable\|disable` |
| 成功/失败 | Result | `--result success\|failed` |
| 操作对象、对象类型 | Object | `--object <backend-type>` |
| 操作时间 | Time | `--start` / `--end` |
| 某 HFW PSM/Provider/资源站点的审计 | Object Detail | `--psm` + `--provider` + `--hfw-site` |

对象类型以服务端完整枚举为准，中文业务名称按 [commands.md](commands.md) 的审计对象表解析。文本输出必须展示具体业务对象名称，不直接展示 `serverRule`、`clientCall`、`adminRuleTicket` 等内部值。

审计对象的 `detail` 对应前端“操作详情”，默认文本输出必须保留该列；它是用户显式查看审计详情的入口，不得因为结构复杂而静默丢弃。

## NSG 集群名与 NSG Agent 参数

| 用户表达 | 前端能力 | CLI |
|---|---|---|
| NSG 集群名、集群名称选择项 | 集群名称选择器 | `nac admin nsg-cluster-name list` |
| 某 Agent 的运行参数、参数面板 | Agent 参数查询 | `nac admin nsg-agent-param list --ip <ip>` |

Agent 参数文本名称必须复用前端参数面板的中文含义，包括 ACL 命中动作、ACL 检查方向、默认动作、抓包开关、ARP 解析、无同步会话、数据平面日志、强制抓包/绕过、IP 统计超时、IPC 流长度、ACL 池大小、TCP 重传超时和 VXLAN 本地 ARP 响应。未在前端参数面板出现的新字段只保留在 JSON 中。

## Matrix Rule

| 用户表达 | 过滤项 | CLI 参数 |
|---|---|---|
| 源区域 | 源区域 | `--src-region <region>` |
| 源 provider | 源 provider | `--src-provider <provider>` |
| 源地址类型 | 源地址类型 | `--src-addr-type ip\|psm\|domain` |
| 目的区域 | 目的区域 | `--dst-region <region>` |
| 目的 provider | 目的 provider | `--dst-provider <provider>` |
| 目的地址类型 | 目的地址类型 | `--dst-addr-type ip\|psm\|domain` |
| 不支持隔离规则 | 隔离支持状态 | `--allowed unsupported` |
| 支持隔离规则 | 隔离支持状态 | `--allowed supported` |
| 无隔离 | 隔离支持状态 | `--allowed no-isolation` |

`allowed=0` 表示不支持，`allowed=1` 表示支持隔离规则，`allowed=2` 表示无隔离。文本输出把源区域/provider/地址类型作为“源地址范围”整体展示，把目的三元组作为“目的地址范围”整体展示。

## Dialtest（拨测）过滤条件

### 拨测任务及最近运行结果

拨测任务及最近运行结果使用 `nac admin dialtest-task list`。

| 用户表达 | 前端过滤项 | CLI 参数 |
|---|---|---|
| 拨测环境、ToB、ToC | Dialtest Env | `--dialtest-env tob\|toc` |
| 任务 ID | ID | `--id <task-id>` |
| 策略名称 | Name | `--name <name>` |
| 源 Agent | Source Agent | `--src-agent <name>` |
| 目的 Agent | Destination Agent | `--dest-type agent --dst-agent <name>` |
| 外部目的 | Destination | `--dest-type external` 加目的 IP/端口/域名 |
| IP 版本 | IP Version | `--ip-version ipv4\|ipv6` |
| TCP/UDP/ICMP/HTTP | Protocols | `--protocols <values>` |
| 预期放行/拒绝 | Expected Actions | `--expected-actions accept\|deny` |
| 关联 NSG 集群 | Traversed Cluster | `--traversed-cluster <cluster>` |
| 启用/禁用任务 | Status | `--status enable\|disable` |

任务列表的 `--page-size` 对应接口请求体字段 `size`。返回中的 `expected_actions` 将 `accept` 显示为“预期放行”、将 `deny` 显示为“预期阻断”；不得直接展示后端裸值。`dial_results.<protocol>.status=success/fail` 显示为执行成功/执行失败，并连同最近运行延迟、时间或错误信息整体展示。

### 拨测 Agent 与 Server PSM

可执行拨测的 Agent 使用 `nac admin dialtest-agent list`。

Agent 过滤项与前端一致：拨测环境、ID、名称、状态、部署类型、VDC、Public IPv4/IPv6、HTTP Domain/Port、TCP/UDP Port、PSM、Server PSM、Cluster、Manage Port。`Dialtest Agent status=online/offline` 显示为在线/离线。

“拨测服务环境”“拨测 Server PSM”“配置了哪些拨测后端”使用 `nac admin dialtest-server-psm list`；不要路由到 NSG Agent 或 TCE 服务查询。
