# NAC 只读命令返回字段覆盖

本 reference 是文本输出的强制覆盖清单。JSON 保留接口原始结构和未知字段；文本输出按前端展示语义收敛。

字段分为四类：

- **前端展示**：默认文本输出必须覆盖，名称和业务语义与前端一致。
- **显然或直接翻译**：无需维护额外映射，但前端展示时仍必须输出。
- **前端未展示**：默认文本不输出；仅在 JSON 中保留。
- **未知或未验证**：不得猜测语义；仅在 JSON 中保留，补齐前端证据后再调整分类。

## `nac user-rule list`

- 前端展示：工单 ID、规则平台、规则 ID、生效状态、创建时间、结束时间、创建人、规则详情入口。
- 显然或直接翻译：ID、时间和创建人。
- 前端详情交互：规则属性由前端点击后以结构化详情展开；CLI 默认文本只提示使用 `--json` 查看，避免输出未经语义核对的裸值。
- 前端未展示：模型内部更新时间、删除时间等数据库字段。
- 未知或未验证：loose schema 捕获的其他字段。

## `nac permission status`

- 前端展示：当前身份的 NAC Admin 状态；支持 RD 检查的站点展示 RD 状态。
- 显然或直接翻译：NAC site。
- 前端未展示：无。
- 未知或未验证：服务端未来新增的身份位。

## `nac user-ticket list`

- 前端展示：工单 ID、工单标题、工单状态、隔离动作、访问源、访问目的、源端口、目的端口、创建人、所属部门、创建时间、过期时间。
- CLI 导航字段：审批链接。
- 显然或直接翻译：地址、端口、时间、创建人和部门。
- 前端未展示：数据库内部模型字段、详情页专用原始数据。
- 未知或未验证：loose schema 捕获的其他 Ticket 字段。

## `nac user-ticket get`

- 前端展示：与 Ticket 列表相同的核心工单字段。
- CLI 导航字段：审批链接。
- 显然或直接翻译：地址、端口、时间、创建人和部门。
- 前端未展示：数据库内部模型字段。
- 未知或未验证：详情响应中的额外规则数据和未来扩展字段；JSON 保留。

## `nac admin yunque-rule search`

- 前端展示：ID、规则名称、源 IP、源 PSM、目的 IP、目的 PSM、目的域名、协议、动作、状态、优先级、双向规则、创建人。
- 显然或直接翻译：ID、名称、IP、PSM、域名、协议、优先级和创建人。
- 前端语义字段：动作映射为放行/阻断/抓包；状态映射为未启用/生效中；双向规则映射为是/否。
- 前端未展示：TCE PSM、源域名、源/目的端口、备注、Record、Internal、Status 等详情或内部字段。
- 未知或未验证：loose schema 捕获的其他 Yunque Rule 字段；JSON 保留。

## `nac admin gray-rule list`

- 前端展示：灰度 ID、生效 ID、规则类型、操作类型、原规则 ID、状态、灰度生效类型、灰度生效范围、工单 ID、规则名称、创建人、源 IP/PSM/端口、目的 IP/PSM/域名/端口、动作、优先级、协议、备注、Internal、Record、Reversed、创建时间、更新时间。
- 显然或直接翻译：ID、地址、名称、优先级、协议、备注和时间。
- 前端语义字段：生效 ID 按前端偏移规则派生；操作类型、发布状态和动作使用前端中文；布尔字段显示是/否。
- 前端未展示：顶层 `source`、嵌套 TCE PSM 和 POC 邮箱。
- 未知或未验证：loose schema 捕获的其他 Gray Rule 字段；JSON 保留。

## `nac yunque-ticket list`

- 前端展示：工单 ID、名称、规则类型、工单状态、工单类型、动作、灰度状态、灰度生效类型/范围、源 IP/PSM、目的 IP/PSM/域名/端口、创建人、优先级、部门、创建时间、过期时间、联系人、备注和申请原因。
- CLI 导航字段：审批链接。
- 显然或直接翻译：ID、名称、地址、创建人、优先级、部门、时间、联系人、备注和申请原因。
- 前端语义字段：状态使用 1–12 映射；类型显示创建/更新；动作显示放行/阻断/抓包；灰度状态显示开启灰度/未开启灰度。
- 前端未展示：TCE PSM、源域名/端口、协议、Record、Reversed、Internal、免审批位、原始 SourceRule、Extra、Duration 和提醒次数。
- 未知或未验证：loose schema 捕获的其他管理工单字段；JSON 保留。

## `nac hfw policy list`

- 前端展示：全局策略配置状态、PSM 出内网默认策略、PSM 出公网默认策略；两项都只表示出方向，未配置时均按“策略未配置，默认放行”展示；自定义策略的策略 ID、策略动作、生效区域、源信息、目的信息、协议、来源、优先级。
- 前端派生展示：自定义策略数量由 `customRules.length` 计算；响应 `count` 同样表示自定义策略数量，但前端未直接读取，CLI 默认文本无需重复输出。
- 显然或直接翻译：PSM、provider、HFW site、IP、域名、端口、协议。
- 前端未展示：规则方向单列、全局规则原始详情、规则组规则。
- 未知或未验证：自定义策略和规则组中的额外字段；JSON 保留。

## `nac hfw acl list`

- 前端展示：全局策略配置状态、PSM 出内网默认策略、PSM 出公网默认策略；两项都只表示出方向，未配置时均按“策略未配置，默认放行”展示；自定义策略的策略 ID、策略动作、生效区域、源信息、目的信息、协议、来源、优先级。
- 显然或直接翻译：PSM、provider、HFW site、IP、域名、端口、协议。
- 前端未展示：规则方向单列、规则组规则。
- 未知或未验证：ACL 规则中的额外状态和扩展字段；JSON 保留。

## `nac hfw permission get`

- 前端展示：平台管理员、PSM Owner、API 访问。
- 显然或直接翻译：PSM、provider、HFW site。
- 前端未展示：普通用户权限位。
- 未知或未验证：未来新增权限位；JSON 保留。

## `nac hfw monitor get`

- 前端展示：集群总量、Agent 总量、异常 Agent 数、存在规则异常的 Agent 数、Bypass Agent 数。
- CLI 的后端语义修正：健康集群使用 `clusterAliveCount`；异常集群使用 `clusterCount - clusterAliveCount`；规则溢出 Agent 数使用 `agentRuleOverflowCount`。后端健康标准是死亡 Agent 比例不超过 1%。
- 显然或直接翻译：NAC site 和各计数。
- 前端错误绑定：前端把 `clusterCount` 当作规则总量、把 `agentAbnormalCount` 当作异常集群；CLI 不复刻，也不输出不存在的规则总量。
- 派生输入：`agentAliveCount`、`agentAbnormalCount`、`agentOfflineCount`、`agentMortalityCount` 共同计算 Agent 总量；除了前端单独展示的异常 Agent 数，不把其他分项重复扩展为默认概览指标。
- 未知或未验证：未来新增监控计数；JSON 保留。

## `nac hfw cluster list`

- 前端展示：集群名称、区域、Agent 存活数、Agent 异常数、Agent 离线数、规则异常 Agent 数、Agent 死亡数；计数同时显示占 Agent 总数的百分比。
- CLI 导航字段：Agent 总数，用于解释数量和百分比。
- 显然或直接翻译：集群名称、区域和计数。
- 前端错误绑定：前端把不存在的 `clusterStatus` 固定显示为健康；后端列表没有集群状态字段，CLI 不输出该列。
- 前端未展示：规则溢出 Agent 数、Bypass Agent 数只保留在 JSON。
- 未知或未验证：loose schema 捕获的其他集群字段；JSON 保留。

## `nac hfw agent list`

- 前端展示：Agent IP、Agent 状态、Agent 规则数、PSM 数、Bypass 状态。
- 显然或直接翻译：Agent IP、规则数和 PSM 数。
- 前端语义字段：`alive/abnormal/offline/mortality` 显示为存活/异常/离线/死亡；`bypass/unbypass` 显示为已开启/已关闭。
- 前端未展示：无。
- 未知或未验证：loose schema 捕获的其他 Agent 字段；JSON 保留。

## `nac hfw agent status`

- 前端展示：集群名称、时间、当前状态、规则状态、Bypass 状态。
- 显然或直接翻译：Agent IP、集群名称和时间。
- 前端语义字段：Bypass `bypass/unbypass` 显示为已开启/已关闭。
- 未知或未验证：当前状态 `stat` 与规则状态 `ruleStat` 没有稳定枚举说明；默认文本不展示，只保留在 JSON。其他扩展字段同样只保留在 JSON。
- 前端未展示：无已确认字段。

## `nac hfw default-bypass get`

- 前端展示：集群名称、默认 Bypass 状态。
- 显然或直接翻译：集群名称和 NAC site。
- 前端语义字段：`bypass/unbypass` 显示为默认 Bypass 已开启/已关闭。
- 前端未展示：无。
- 未知或未验证：未来新增的 HFW backend 元数据；JSON 保留。

## `nac admin nsg-monitor get`

- 前端展示：集群总数、异常集群数、Agent 总数、Bypass Agent 数、离线 Agent 数。
- 显然或直接翻译：NAC site 和计数。
- 前端未展示：Watch Agent 数。
- 未知或未验证：未来新增监控计数；JSON 保留。

## `nac admin nsg-rule-type list`

- 前端展示：NSG 规则类型、显示名称。
- 显然或直接翻译：具体 `rule_type` 值。
- 前端未展示：无。
- 未知或未验证：loose schema 捕获的其他规则类型字段；JSON 保留。

## `nac admin nsg-agent list`

- 前端展示：FW 客户端 IP、存活状态。
- 显然或直接翻译：IP。
- 前端语义字段：`alive=true/false` 显示为存活/异常。
- 前端未展示：无。
- 未知或未验证：loose schema 捕获的其他 Agent 字段；JSON 保留。

## `nac rule search`

- 能力范围：最全面的 NSG 正式规则查询接口；不带过滤条件时覆盖全部规则类型，以及 MGT/Honeycomb、Yunque、`nac_sec`/NAC Security Center 和 TCC 四种正式规则来源。独立表中的灰度规则不在结果内。
- 前端展示：规则 ID、动作、规则类型、规则名称、用户名、优先级、协议、源/目的 IP、PSM、PSM ID、域名、端口、Record、Reversed、Internal、备注和来源。
- 显然或直接翻译：ID、名称、用户名、优先级、IP、PSM、域名、端口、协议和备注。
- 前端语义字段：动作显示放行/阻断；来源转换为 Yunque 管理员规则、TCC 规则、MGT 用户规则或 NAC 安全中心规则；Record/Reversed/Internal 显示为是/否。
- 前端未展示：无；loose schema 的扩展字段仅保留在 JSON。
- 未知或未验证：后端新来源值；JSON 保留原值，文本不得猜测业务来源。

`record`、`internal` 为 `false` 时可能被后端 `omitempty` 省略。字段缺失与明确返回 `false` 必须区分，CLI 不得自行补值。

## `nac rule conflict-check`

- 风险结论：`has_risk` 表示本次候选规则是否存在完全重复、冗余、冲突或重叠；`summary` 是四类风险的全量计数。
- 风险明细：`results[*].type`、`reason`、已有规则 `rule` 及 `impact` 是综合分析依据；不得用截断明细数量替代 `summary`。
- 显然或直接翻译：已有规则 ID、名称、规则类型、源/目的地址、端口和协议。
- 前端语义字段：`ACCEPT/DROP` 显示为放行/阻断；优先级数值越小越高；`candidate_cover_ratio` 是新规则被覆盖率，`target_cover_ratio` 是已有规则被覆盖率；`overlap_rule` 是实际相交范围。
- CLI 导航字段：`site`、`limit`、`sort`、`truncated` 说明请求站点、明细上限、排序和结果是否截断。
- CLI 派生字段：`existing_rule_has_higher_priority` 仅由已有规则优先级与候选优先级确定，用于解释优先级关系。
- 前端未展示：loose schema 捕获的其他扩展字段只保留在 JSON。
- 未知或未验证：未来新增风险类型、影响方向或精度枚举；JSON 保留原值，文本与 Agent 分析不得猜测。

## `nac admin compiled-rule list`

- 能力范围：准备下发数据面的最终编译规则；服务端可能按请求链路 `X-Real-IP` 叠加当前 Agent 命中的发布中灰度规则。

- 数据范围：指定具体 NSG 规则类型已经编译并下发到数据面的全量规则；不同于 `nac rule search` 的编译前但已 normalize 规则。
- 接口语义展示：`current_count` 是本次规则数，`rule_type` 是具体 NSG 规则类型，`site` 是 NAC API 与认证站点。接口不返回数据面版本，CLI 不生成对应字段。
- 显然或直接翻译：规则 ID、创建人、优先级、源/目的 IP、端口和协议。
- 业务语义字段：动作 `permit/deny/pcap/reverse` 显示为放行/阻断/抓包/反向处理；`record` 显示“记录命中：是/否”；`internal` 显示“内部规则：是/否”。
- 编译结果特性：PSM 和域名通常已解析为 IP；CLI 仍完整保留地址对象中服务端实际返回的 PSM、PSM ID、域名和端口。
- Go `omitempty` 语义：编译后响应省略 `record` 或 `internal` 时等价于 `false`，CLI 规范化为否；缺失的地址数组规范化为 `[]`。
- 前端未展示：无已确认字段；未知扩展字段只在 JSON 中保留，文本不得猜测。

## `nac admin rule search`

- 前端展示：命中规则时与规则检索使用同一规则字段；没有规则 ID 时展示“未匹配到具体规则”。
- 显然或直接翻译：规则地址、协议、名称、用户名和备注。
- 前端语义字段：动作显示放行/阻断；是否命中由规则 ID 是否存在决定。
- 前端未展示：未命中时后端为诊断返回的 Agent 默认动作。
- 未知或未验证：Agent 新增的匹配元数据；JSON 保留。

## `nac admin rule delivery-status`

- 前端查询摘要：输入 Rule ID、归一化 Rule ID、反向 Rule ID、反向规则是否存在、NSG 规则类型、请求 Agent 数和完成 Agent 数。
- CLI 编排上下文：用于检查的 1–4 台 Agent IP，以及每台 Agent 在选择列表中的存活/异常状态；未指定时只选择列表第一台。
- 源规则预览：正向和反向源规则的 ID、名称、来源、规则类型、动作、优先级、源/目的地址、协议、创建人、反向规则标记和备注。
- 每个 Agent/方向的状态：主状态、子状态、置信度、失效阶段和判断依据。主状态表示已确认到达的最远阶段，不把后续接口失败解释为前序阶段回退。
- 四阶段证据：Server `/acl`、Agent `/acl`、Agent `/acl2FW` 和 `/agent/status` 的查询状态与命中/可用结果；同时展示 Server 规则版本、转换实例数、Engine 状态、Agent/FW 版本和更新状态。
- Server 编译后规则：完整结构保留在 JSON；文本展示规则 ID、类型、地址、协议、动作、优先级、Record 和 Internal。
- 前端语义字段：方向显示正向规则/反向规则；状态、子状态、原因和查询状态使用前端中文；动作显示放行/阻断/抓包；布尔值显示是/否；不可用或查询失败的证据显示不支持或无法判断。
- 前端未展示：`summary.state_counts` 和 loose schema 捕获的未来扩展字段；只在 JSON 中保留。
- 未知或未验证：未来新增状态、原因、置信度、失效阶段或 Engine 状态；JSON 保留原始值，文本显示未知，不猜测业务语义。

## `nac admin es-log-config get`

- 前端展示：`hostList` 为配置采集的集群 IP，`ruleTypeList` 为配置采集的 NSG 规则类型，`ruleIdList` 为配置采集的规则 ID。
- 显然或直接翻译：各列表中的 IP、规则类型和规则 ID 值，以及 NAC site。
- 前端组合语义：三组条件是 OR 关系；CLI 以 `match_relation=or` 保留该确定性解释，文本显示“任一条件命中即采集”。
- 空值语义：缺失或 `null` 列表规范化为 `[]`；空列表只表示对应维度未配置条件，不表示全量匹配。
- 前端未展示：无已知字段；loose schema 捕获的未来扩展字段只在 JSON 中保留。
- 未知或未验证：未来新增字段；不在文本中推断含义。

## `nac admin audit-log list`

- 前端展示：Log ID、操作类型、对象类型、对象 ID、操作人、操作时间、结果、原因和操作详情。
- 显然或直接翻译：ID、操作人、时间和原因。
- 前端语义字段：操作类型转换为增加/创建/更新/删除/取消/启用/禁用；结果转换为成功/失败；对象类型转换为命令参考中定义的具体业务对象名称。
- 前端未展示：Actor 的 employeeID、邮箱、组织、区域、地点、账号类型和角色等扩展身份字段；默认文本输出不展示，JSON 保留。
- 未知或未验证：未来新增的操作、结果或对象类型；JSON 保留原值，文本不得猜测。

## `nac admin nsg-cluster list`

- 前端展示：集群名称、集群状态、区域、PSM、环境、类型、预期状态、部署类型、TT、描述、规则、Tag、Agent 总数、Agent 打点故障数、Agent 离线数、Agent Bypass。
- CLI 导航字段：集群 ID。
- 显然或直接翻译：区域、PSM、环境、类型、描述、规则和 Tag。
- 前端未展示：内部 IP 列表和内部 bypass 配置字段。
- 未知或未验证：TT 返回值 `0/1` 缺少稳定业务语义，默认文本不展示，只保留在 JSON；loose schema 捕获的其他集群字段同样由 JSON 保留。

三个 Agent 异常计数按前端格式同时展示数量和占总 Agent 数的百分比。

## `nac admin nsg-cluster get`

- 前端展示：Agent IP、状态、Metric Status、Machine Type、OS、Kernel Version、Firewall Version、Client Version、Region、PSM、IDC、VDC、Package、Warranty Time、BGP Bypass。
- 显然或直接翻译：IP、版本、Region、PSM、IDC、VDC、Package 和时间。
- 前端未展示：`diagnose`、NLB Bypass、Force Bypass、默认动作和其他参数详情；只在 JSON 中保留。
- 未知或未验证：loose schema 捕获的其他 Agent 字段；JSON 保留。

BGP Bypass 必须按前端开关语义显示，不输出原始数字。

## `nac admin nsg-cluster-name list`

- 前端展示：集群名称选择项。
- 显然或直接翻译：集群名称和 NAC site。
- 前端未展示：无。
- 未知或未验证：未来新增的选择项元数据；JSON 保留。

## `nac admin nsg-agent-param list`

- 前端展示：Agent 参数面板中已有中文说明的参数。
- 显然或直接翻译：Agent IP。
- 前端语义字段：参数名使用前端参数面板的说明，不以裸 snake_case 代替含义。
- 前端未展示：服务端新增但前端参数面板尚未列出的参数。
- 未知或未验证：未知参数只保留在 JSON。

前端参数面板覆盖：ACL 阻断命中动作、ACL 检查服务器方向、ACL 默认动作、ACL 抓包功能、ARP 解析退出/超时、无同步创建会话、数据平面接受/阻断流量日志、ACL 日志级别、日志服务器方向、强制全部/丢弃/发送抓包、强制绕过、IP 统计超时、IPC 流最大长度、最大 ACL 池大小、TCP 重传超时和 VXLAN 本地 ARP 响应。

## `nac admin matrix-rule list`

- 前端展示：源地址范围、目的地址范围、隔离支持状态、描述。
- CLI 导航字段：Matrix Rule ID。
- 显然或直接翻译：区域、provider、地址类型和描述。
- 前端语义字段：`allowed=0/1/2` 显示为不支持/支持隔离规则/无隔离。
- 前端未展示：NSG/HFW/NAC Proxy/XACL 内部开关、Protego 类型和各平台规则类型数组。
- 未知或未验证：loose schema 捕获的其他 Matrix 字段；JSON 保留。

## `nac admin matrix-rule get`

- 前端展示：与列表相同的源地址范围、目的地址范围、隔离支持状态和描述。
- CLI 导航字段：Matrix Rule ID。
- 显然或直接翻译：创建人、更新人。
- 前端未展示：平台内部开关与规则类型数组。
- 未知或未验证：其他详情扩展字段；JSON 保留。

## `nac admin dialtest-task list`

- 前端展示：ID、策略名称、源 Agent、目的、IP 版本、协议、预期动作、关联 NSG 集群、状态、最近运行结果。
- 显然或直接翻译：ID、名称、Agent、IP、域名、端口、协议和集群。
- 前端语义字段：预期动作显示预期放行/预期阻断；任务状态显示启用/禁用；每个协议的最近结果显示执行成功/执行失败，并展示延迟、时间和错误。
- 前端未展示：方向、全局动作、任务类型、payload、响应匹配配置、Server PSM 和原始拨测环境字段。
- 未知或未验证：未来新增任务或结果字段；JSON 保留。

## `nac admin dialtest-agent list`

- 前端展示：ID、名称、状态、部署类型、VDC、Public IPv4/IPv6、HTTP Domain/Port、TCP/UDP/Manage Port、PSM、Server PSM、Cluster。
- 显然或直接翻译：ID、名称、IP、域名、端口、PSM、VDC 和 Cluster。
- 前端语义字段：`online/offline` 显示为在线/离线。
- 前端未展示：创建时间、更新时间。
- 未知或未验证：未来新增 Agent 字段；JSON 保留。

## `nac admin dialtest-server-psm list`

- 前端展示：配置的拨测服务环境/Server PSM 选择项。
- 显然或直接翻译：字符串选择项和 NAC site。
- 前端未展示：无。
- 未知或未验证：未来扩展元数据；JSON 保留。
