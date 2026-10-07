# NAC 故障处理

## 命令不存在

- 旧的 `nac rule list` 不存在：升级 CLI/Skill，迁移到 `nac user-rule list`。
- 旧的 `nac mgt-rule list` 不存在：使用 `nac user-rule list`。
- 明确查询 MGT/用户规则时，`user-rule get` 不存在：使用 `nac user-rule list --id <rule-id>`。
- 未说明来源的规则 ID 被错误查成用户规则：改用 `nac rule search --id <rule-id>`。只有明确的 MGT/用户规则/default/tob 表 ID 才使用 `nac user-rule list --id`；明确的 Yunque 管理员规则使用 `nac admin yunque-rule search`。
- 未说明来源的“我的规则”被错误查成 MGT 用户规则：保持 `nac rule search` 路由，先读取 `auth userinfo` 的 `data.username`，再传 `--username`。“我的”只增加创建人过滤，不选择规则接口。
- 旧的 `nac ticket list/get` 不存在：使用 `nac user-ticket list/get`。
- 旧的根级 `nac dialtest` 不存在：按资源使用 `nac admin dialtest-task list`、`nac admin dialtest-agent list` 或 `nac admin dialtest-server-psm list`。
- `nac admin ticket list` 不存在：Yunque 管理工单的只读列表使用 `nac yunque-ticket list`。
- `nac admin rule delivery-status` 不存在：升级 CLI 和 Skill；不要用 compiled-rule 全量列表代替单条规则的下发阶段。

```bash
bytedcli self update
bytedcli self skill update -g
bytedcli --json nac user-rule list --id 123 --table-type default
```

## 空结果与 ACL

检查 `--site`、`--table-type`、`--rule-plat`、时间等显式过滤条件。

- “我的规则”为空：重新执行 `bytedcli --json auth userinfo`，确认使用了所选接口的创建人字段——正式规则检索用 `--username`，MGT Rule 用 `--creator`，Yunque Rule 用 `--username`，Gray Rule 用 `--rule-username`；不要传 `me` 或“我的”字面量。
- “我的用户工单/管理工单”为空：确认把同一 `data.username` 分别传给 `--creator` / `--username`。
- “所有/我能看到的/可见的/作为 POC”为空：确认没有误加 `--creator`、`--username` 或 `--rule-username`。这类查询由后端 ACL 决定可见范围，Ticket 可包含本人创建或本人作为 POC 的记录。
- `auth userinfo` 没有非空 `data.username`：执行 `bytedcli auth login` 刷新身份。不要省略 creator 后继续执行“我的”查询，否则查询范围会被扩大。

## Ticket 审批链接

- `approvalUrl=null`：工单没有可用审批流；不要自行调用 Kani API或打开网页。
- `approvalFlowId` 含连字符时，CLI 会生成 Lark mini app 链接；否则按 NAC site 生成 Kani 链接。

## Permission Status

I18N 返回 `isRd=null`、`rdSupported=false`，表示该站点未执行 RD 检查，并非“不是 RD”。CN/BOE 才同时检查 Admin 和 RD。

## 参数错误

- 当前版本的 NAC `--site` 注册在每个叶子命令上，规范写法是 `bytedcli --json nac permission status --site cn`。如果叶子命令返回 `unknown option '--site'`，说明 CLI 版本过旧；先升级或重新构建 CLI。把 `--site` 放在全局位置只能作为旧调用的兼容方案，不应作为长期修复。
- `--enabled` 后补 `true` 或 `false`。
- 地址缺半时同时补齐 type/value；不需要该过滤时同时删除两项。
- 状态名非法时使用主 Skill 中列出的语义名，不直接传后端数字枚举。
- site 错误时改为 `cn`、`boe`、`i18n-row-tt` 或 `i18n-bd`；NAC 不支持 `eu-ttp`。
- start 晚于 end 时修正时间范围；日期型 end 已自动包含当天。
- Yunque Rule 缺少 `--rule-type` 时先运行 `nac admin nsg-rule-type list` 获取具体 NSG 规则类型；接口不会在未选择类型时返回全量，也不能用规则平台值 `nsg` 代替。
- `nsg-agent list` 缺少 `--rule-type` 时使用同一规则类型列表选择非空值。类型通常为 `xx.gw`，但 CLI 不硬编码后缀。
- `nac rule search` 不要求 `--rule-type` 或其他过滤条件；无参数表示查询全部 ACL 可见的 NSG 规则类型和四种正式规则来源，不包含灰度规则。五元组的显式空字符串是 `empty`，不能当成未提供；字面 `"*"` 是 `all`，不能去掉引号后变成 `any`。
- 五元组参数收到 HTTP 400：保留服务端 `code/msg`，再检查空列表项、裸 `*` 与具体值混用、超过 10 个值、非法 IP/CIDR、非法端口、非数字 TCE PSM ID 或非法协议。CLI 不自行发明替代值。
- 候选 IP 横杠范围被拒绝：把整个字段改为 1–10 个逗号分隔项，每一项使用单 IP 或 CIDR；只有端口候选接受 `start-end` 范围。
- Domain/PSM 候选中的 `*` 或 `?` 没有按查询通配符工作：这是正确语义；模式字符属于已有规则。需要限定只匹配具体已有规则时，使用保留字面双引号的 `precise` 输入。
- `nac rule search` 查不到已知灰度规则：这是接口边界，不是空结果故障。灰度对象使用 `nac admin gray-rule list`；要观察准备下发数据面的最终集合，使用 `nac admin compiled-rule list --rule-type <type>`，并注意灰度命中取决于请求链路的 `X-Real-IP`。
- 用户要普通规则却生成 `nac admin compiled-rule list`：改回 `nac rule search`。只有明确说“编译后”或“下发到数据面”才使用 compiled-rule。
- `compiled-rule list` 缺少 `--rule-type`：先运行 `nac admin nsg-rule-type list`，再选择具体类型；该接口不支持省略类型后的全量类型查询。
- `compiled-rule list --site` 被拒绝：使用标准 NAC 站点 `cn`、`boe`、`i18n-row-tt` 或 `i18n-bd`；I18N 兼容别名由 NAC 站点解析统一处理。
- 编译后规则解析失败：保留 `NAC_COMPILED_RULE_LIST_PARSE_ERROR`。服务端 `data` 应是规则数组；字符串、对象、标量或 `null` 都不能冒充成功结果，也不得回退到未编译规则并冒充结果。
- `nac admin rule search` 缺少 Agent：先用同一 `rule_type` 调用 `nac admin nsg-agent list`，选择 FW 客户端 IP。
- `delivery-status` 未指定 `--agent`：这是默认行为，CLI 自动推导类型并检查 Agent 列表第一项。
- `delivery-status --agent` 被拒绝：指定 IP 必须属于自动推导出的规则类型；先用 `nac admin nsg-agent list --rule-type <type>` 核对。一次最多重复 4 个不同 Agent，不自动拆批。
- 连续查询同一 Agent：两次下发状态调用之间至少等待 5 秒，不并发调用；这是接口开销约束，不通过拆分命令规避。
- 下发状态返回规则不存在：检查 Rule ID、NAC site 和当前身份的规则类型读取权限；不要放宽成全量 compiled-rule 查询。
- 下发状态返回规则类型不唯一：源规则数据存在歧义，先核实规则；CLI 不会任意选择一种类型。
- 下发状态返回 Agent 列表为空：检查该规则类型的集群和 Agent 注册；CLI 不会伪造或改用其他类型的 Agent。
- 默认第一台 Agent 状态异常：仍保留本次诊断结果并明确 Agent 状态；不要静默换用第二台。只有用户明确指定其他 Agent 时才添加 `--agent`。
- 精确匹配没有规则 ID：这是“未匹配到具体规则”，不要把返回的默认动作当作命中规则。
- 审计 HFW 过滤参数不完整：`--psm`、`--provider`、`--hfw-site` 必须同时提供；`--site` 不能替代 `--hfw-site`。
- 审计日志返回 401：接口只允许 Kani 超级管理员，不能改用其他读写接口绕过。
- ES 日志采集配置返回 401 或 `unauthorized`：`nac admin es-log-config get` 只允许 Kani 超级管理员，不能直连 Redis、改用写接口或其他查询绕过。
- ES 日志采集配置某个列表为空：只表示该维度没有配置条件；三组条件仍按 OR 解释，不得把空列表说成匹配全部。
- Gray Rule 状态使用 `releasing`、`rolled-back`、`completed`；操作类型使用 `add`、`update`、`delete`。
- HFW `--psm` 或 `--provider` 为空时提供非空值；provider 不确定时省略该参数以使用默认 `tce`。
- HFW 资源站点只接受 `cn`、`boe`、`i18n`、`i18n-bd`、`tob_cn`。NAC I18N site 写 `--site i18n-row-tt`，对应 HFW site 是 `i18n`，不能把两套名称互换。
- `nsg-agent-param list` 缺少 `--ip` 或 IP 非法时，提供合法 IPv4/IPv6；不要把集群名或 PSM 当作 Agent IP。
- Matrix `--allowed` 只使用 `unsupported`、`supported`、`no-isolation`；源/目的地址类型只接受 `ip`、`psm`、`domain`。
- Dialtest 环境只接受 `tob`、`toc`；协议只接受 `tcp`、`udp`、`icmp`、`http`；预期动作只接受 `accept`、`deny`。

## HFW 空结果与站点

先查看 JSON 中的 `site` 与 `hfwTriple`：`site` 是 NAC API/认证站点，`hfwTriple.site` 是 HFW 资源站点。需要跨站查询时同时显式提供，例如：

```bash
bytedcli --json nac hfw acl list \
  --psm service.demo \
  --site cn \
  --hfw-site boe
```

如果用户说“BOE 的微隔离策略”，命令却只有 `--site boe`，说明自然语言区域映射错了：应改为 `--hfw-site boe`，NAC API `--site` 保持默认 `cn`。只有用户明确要求 NAC API/认证也走 BOE 时才同时添加 `--site boe`。

TikTok ROW 的 HFW 资源使用 `--hfw-site i18n`，不是 `--hfw-site i18n-row-tt`。CLI 的站点自动推导仅作为兜底；用户明确提到区域时应显式传 `--hfw-site`，避免把资源区域误当 NAC API 区域。

HFW 监控、集群和 Agent 命令不使用 HFW triple，只接受 NAC `--site`。不要给 `nac hfw monitor/cluster/agent` 添加 `--hfw-site`、`--psm` 或 `--provider`。

如果 HFW 监控概览与页面标签不一致，以后端字段语义为准：`clusterCount` 是集群总量，异常集群由 `clusterCount - clusterAliveCount` 得出，`agentAbnormalCount` 是异常 Agent 数。接口没有规则总量；不要把 `clusterCount` 重命名为规则总量。HFW 监控接口需要对应的后端接口权限，401 或非零 envelope 时保留 `code/msg`，不得改用 Bypass 写接口绕过。

Policy/ACL 的规则数组为空表示接口没有返回对应规则，不要把缺失或 `null` 当成解析失败。Permission 的 `adminAccess`、`ownerAccess`、`apiAccess`、`normalUserAccess` 是 PSM 维度权限，不等同于 `nac permission status` 的 Admin/RD 身份检查。

## 认证与服务端错误

NAC envelope 非零时保留 `code/msg`。认证错误先检查对应 ByteCloud site 登录状态，尤其 NAC `i18n-row-tt` 对应认证 site `i18n-tt`：

```bash
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json auth status
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login
bytedcli --json nac permission status --site i18n-row-tt
```

## NSG 管理员监控

- 返回 `admin required`、401 或管理员鉴权错误：当前身份不是 NAC Kani 超级管理员。不要改用用户接口或直接调用后端绕过鉴权。
- 列表短 ID 查询详情失败：直接把短 ID 传给 `nac admin nsg-cluster get --id`，CLI 会自动补 `nsg-cluster-`；不要手工重复前缀。
- “集群状态”结果不符合预期：实际健康/异常使用 `--cluster-state`；`--expected-status` 是配置的预期在线、离线或废弃状态。
- “打点异常”使用 `--metric-status dead`，请求会映射为前端的 `metricStatus=1`。
- `bgp_bypass`、`nlb_bypass` 等原始值不清楚时，保留数值并说明 CLI 未做业务推断。
- NSG 规则类型列表或匹配 Agent 返回 401 / admin required：两条接口也经过 NAC 管理员鉴权，不要改用用户规则接口绕过。
- NSG 集群名、Agent 参数或 Matrix Rule 返回 401 / admin required：这些接口同样经过管理员鉴权，不要直连 Agent、Matrix 或后端服务绕过。
- Agent 参数出现未知参数名：JSON 保留，文本模式不猜测含义；补齐前端参数面板证据后再加入语义映射。

## Matrix Rule 与 Dialtest

- Matrix Rule 的 `allowed` 使用隔离支持状态解释：不支持、支持隔离规则、无隔离。不要显示裸数字。
- Matrix 列表没有结果时先检查源/目的区域、provider、地址类型和隔离支持状态；不要自动删除管理员边界。
- Dialtest 命令分别位于 `nac admin dialtest-task`、`nac admin dialtest-agent` 和 `nac admin dialtest-server-psm`。如果生成了根级 `nac dialtest` 或多余的 `dialtest` 命令组，应改用对应资源命令。
- Dialtest Task 的 `--page-size` 会映射到接口请求体 `size`；帮助和用户输入仍统一使用 `--page-size`。
- 任务没有 `dial_results` 表示没有可展示的最近运行结果；不要伪造执行状态。
- Dialtest Agent 为空时检查 `--dialtest-env` 和显式过滤项；不要回退到 `nac admin nsg-agent`，两类 Agent 用途不同。

## Yunque 与灰度查询

- Yunque Rule 或 Gray Rule 返回 401 / admin required：两条接口经过服务端管理员鉴权，不要改用其他接口绕过。
- Yunque Rule 除 `--rule-type` 外的过滤条件由 CLI 按前端逻辑本地完成；结果过多时缩小过滤条件或调整本地分页。
- Gray Rule `--id` 同时接受原始灰度 ID、正向生效 ID和双向规则的反向生效 ID。
- Yunque Ticket 为空时先检查显式过滤条件和后端 ACL；“所有/可见”查询不得补 `--username`。
- Yunque Ticket 的 `approvalUrl=null` 与用户 Ticket 相同，表示没有可用审批流链接，不要额外调用 Kani。
