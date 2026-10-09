---
name: bytedcli
description: "Use for ByteDance internal R&D platforms, BBQ/PDI-Seed interface test automation, and CIS主数据 (also match 主数据 and EA主数据); prefer bytedcli CLI/MCP/references to web pages or hand-written APIs. Covers auth, TOP, LabelGPT, Aiden, Codebase, BAM, BITS, SCM, TCE/TCC, ByteCloud, ByteGate, ByteDoc, RDS, Hive, Dorado, Flink, APM, logging, storage, messaging, testing, deployment, observability, Guardian/星环 (小R requires incident-read intent), DECC/OG Gateway tagging, USTTP/EUTTP API tagging, MCP, and FTF (流量录制 and 流量回放 and 回归测试)."
---

# bytedcli

## 如何调用 bytedcli

**Agent Shell 规则（仅 Neptune）：** 当要执行的命令域是 `neptune`，每次实际调用都必须使用 `bytedcli --trigger-source ai [全局参数] neptune <command> [options]`。提交 Shell 工具前，逐条检查命令中 `neptune` 前是否有 `--trigger-source ai`；缺失就补齐，已有 `--trigger-source cli` 就改为 `ai`。这也适用于复制用户或 help 的命令、失败重试、循环、生成后执行的脚本，以及 Python/Node 子进程参数数组；不能只标记首次调用或外层脚本。使用 npx 时，标记放在包名后、`neptune` 前。其他命令域不要求添加此标记，不要设置全局环境变量或改写全局 alias。

```bash
# Agent 执行 Neptune：每条命令都显式携带标记
bytedcli --trigger-source ai --json neptune framework get --psm example.service
# 其他命令域保持原调用格式
bytedcli --json auth status
```

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

- 默认使用全局安装的 `bytedcli ...`，不要把 `npx -y @bytedance-dev/bytedcli@latest` 写进自动化或日常调用。
- 仅当目标环境完全无法 `npm install -g`（如临时容器、无写权限的 CI）时，才把示例里的 `bytedcli` 替换为 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest`。

这是 bytedcli 的统一入口说明。任务涉及字节内部研发平台时，先用它判断该走哪个命令域，再按需进入对应领域的详细说明。

## How to use

1. 先判断任务属于哪个平台或对象类型。
2. 先选对命令域，再调用对应的 bytedcli 命令。
3. 需要稳定机器可读输出时，默认加 `--json`，并把它放在 `<domain>` 前面。
4. 不确定命令名或参数时，先看 `--help`，不要猜。
5. 命令支持控制台 URL、文档 URL、仓库上下文自动推断时，优先直接使用这些输入。

## Quick start

```bash
bytedcli --help
bytedcli --json auth status
bytedcli <domain> --help
bytedcli self update --check
bytedcli self skill list --installed -g
bytedcli self skill update -g
bytedcli self tracking enable
bytedcli self plugin install --repo demo-tools/plugin-demo
bytedcli self plugin list
bytedcli self plugin doctor --name demo-tools
```

## Self 管理与技能更新

需要按命令和参数限制危险操作时，使用 `bytedcli self safety-policy`。例如为 `tcc config update` 配置 `env=prod → confirm`，仅生产环境修改需要确认。策略默认关闭；命中 `SAFETY_POLICY_CONFIRMATION_REQUIRED` 时，Agent 必须先取得用户明确批准，再用 `--yes`（MCP：`yes: true`）重试。`deny` 不能绕过。完整配置与默认值匹配规则见 [本地安全策略](references/safety-policy.md)。

全局安装的 bytedcli 会在普通命令执行时自动检查 CLI 与已安装技能版本；`self` 子命令自身不会触发 auto-upgrade。需要关闭自动升级时使用全局参数或环境变量：

```bash
bytedcli --no-auto-upgrade <domain> <command> [options]
export BYTEDCLI_NO_AUTO_UPGRADE=1
```

管理随 bytedcli 打包的 agent skills 时用 `self skill`，不要直接手删技能目录：

```bash
bytedcli self skill list
bytedcli self skill list --installed
bytedcli self skill install -s bytedance-codebase -g
bytedcli self skill install --all -g
bytedcli self skill update -g
bytedcli self skill remove -s bytedance-codebase -g
```

- `-g/--global` 对应全局技能目录 `~/.agents/skills/`；省略时操作当前项目的 `.agents/skills/`。
- `self skill remove` 会同时删除目录和 `~/.local/share/bytedcli/data/skill-lock.json` 中的记录；只手动删除目录时，lock 仍可能保留该技能，后续版本升级时可能被重新同步。

需要直接读取随 CLI 分发的 skill 内容（无需先安装）时用 `self skill get`：

```bash
bytedcli self skill get bytedcli           # 读取某个 skill 的 SKILL.md
bytedcli self skill get codebase           # skill 名称支持模糊匹配（自动解析为 bytedance-codebase）
bytedcli self skill get bytedcli/references/invocation.md  # 读取 skill 下的参考文件
bytedcli self skill get bytedcli/references                # 目标是目录时列出该层文件
```

`self skill get` 默认输出原始 Markdown，加 `--json` 输出 JSON 包裹格式（目录与文件通过 `type` 字段区分）。skill 名称支持模糊匹配（前缀/后缀/包含），无需输入完整 `bytedance-` 前缀。

## 生产网 prod

VA / Maliva / 生产开发机上，调 i18n-tt / i18n-bd / sg 命令前先 `export BYTEDCLI_NETWORK_PROFILE=prod`。办公网跳过。

## Route by task

- CIS主数据查询：当前支持部门、法人主体、主体账户、金融分支机构、汇率、利率、币种、银行总行、国家/地区、省/州、城市、区/县、国籍、自定义区域、时区、公共假期、语言、证件类型、源系统标识、CIS业务线、虚拟主体、人员序列、职场、楼宇、楼层、地产项目、IT库房位置、收单地址、商户号、预算科目、预算科目扩展、会计科目、会计科目扩展、会计子目、会计子目扩展、多账套会计科目、多账套会计科目扩展、财务区域、核算区域、付款类型、支出类型、支出类型Mapping、采购品类、中台属性、业务线、业务线扩展、业务线星云关系、总账侧业务线、往来模型；自然语言说主数据、CIS主数据 / CIS 主数据、EA主数据 / EA 主数据时均路由到这里。精确查询、批量查询、受限条件查询、模糊搜索或分页列表使用 `cis-master-data` / [CIS Master Data](references/subskills/bytedance-cis-master-data/GUIDE.md)
- Figma 官方 D2C：支持直接获取 Figma 原始信息，并将 Figma 设计稿直接还原为 browser（H5 / 桌面 web）或 Lynx 页面代码；同时支持视觉切分、交互识别、渲染截图、评测与精修循环：`d2c` / [bytedance-d2c](references/subskills/bytedance-d2c/GUIDE.md)
  - 单一入口：先读该 skill 的路由表，再按需加载 `references/<capability>/GUIDE.md`，不要一次性加载全部能力。
  - 任务状态与 Figma 节点描述是只读 bytedcli 子命令（走 SSO 鉴权）；切分、渲染、构建截图、评测与精修 guard 也都是 bytedcli 子命令，代码生成本身由你按 guide 自行推理完成。
  - `design-space d2c` 的 Codin D2C 只读 Figma 取数与节点推荐是另一条产品线，保持原有路由。
- SoarProfile、`bytedcli soarprofile`，或针对指定 RISC-V 服务器（当前为 ORCA）的 CPU load、PMU/进程指标、时间范围 profiling 数据及 workload 瓶颈分析：[SoarProfile](references/subskills/bytedance-soarprofile/GUIDE.md)
  - 无服务器/SoarProfile 上下文的泛 profiling、performance、Benchmark、Experiment 意图保持原有路由。
- TCS 送审/送标、Business / Scene / Jimu / Content Schema / Workflow / Queue 管理，以及 Rock 跨队列抽检或申诉配置：`tcs` / [bytedance-tcs](references/subskills/bytedance-tcs/GUIDE.md)
  - TCS 使用 SG MPSSO；写操作默认 dry-run，确认同一 payload 后才加 `--yes`。TCC 配置中心和 TCE 部署请求保持各自原有路由。
- Douyin AI Trace Span、按 LogID 查询平铺 Span 明细或总 Span 数：[Douyin AI Trace Span](references/subskills/bytedance-douyin-ai-trace-span/GUIDE.md)
  - 普通服务日志、BytedTrace 调用树或 workspace 范围的 Trace 候选查询保持原有 Log / Argos / Douyin AI 路由。
- 登录、状态、JWT、用户信息：`auth`
  - 例子：“帮我登录”“看当前账号”“拿 codebase jwt”
- UCenter 账号/资料、绑定、设备、注销/锁定、账号操作、授权和操作日志只读查询：`ucenter` / `bytedance-ucenter`
  - 账号详情默认只查基本信息；其他栏目需要显式 `--section`。
  - 日志至少带 UID 或 DID，不允许全 App 扫描；权限不足时展示申请入口，不提交申请。
- AppInfo 应用元数据、App ID、应用 code、中文名、账号组、产品线与移动端包名查询：`app-info` / `bytedance-app-info`
  - 例子：“按 App ID 查应用”“按 Android 包名搜索 AppInfo”“批量获取多个应用详情”
- ByteQuota 存储配额元数据、配额项、操作、容量检查、申请/借用/分配/回收和 bypass：`quota` / `bytedance-quota`
  - 写操作默认预览；用户确认同一 payload 后才加 `--yes`，不得自动重试。
- Vertex 平台 registry 动态命令：`vertex` / `bytedance-vertex`
  - 先用 `vertex --help` 读取 registry 命令面；再用 `vertex <module> <action> --help` 查看 action 参数、required、type、choices 和 description。
  - 执行形态为 `vertex <module> <action> --flag value`；需要强制刷新 registry cache 时加 `--refresh`。不要使用旧静态形态 `vertex schema/module/capability/invoke`。
- NAC / Network Access Control 用户规则、规则平台、NSG 规则类型、规则检索/精确匹配/下发状态、ES 日志采集配置、NAC 审计日志、用户工单、Yunque 管理员规则、灰度规则、管理工单、审批链接、本人 Admin/RD 身份、HFW/微隔离及 HFW 监控/集群/Agent/Bypass、NSG 匹配 Agent/参数/集群名、Matrix Rule 与 Dialtest 拨测：`nac` / `bytedance-nac`
  - 用户、接口权限或后端 ACL 可见命令：`nac user-rule list`、`nac permission status`、`nac user-ticket list`、`nac user-ticket get`、`nac hfw policy list`、`nac hfw acl list`、`nac hfw permission get`、`nac hfw monitor get`、`nac hfw cluster list`、`nac hfw agent list`、`nac hfw agent status`、`nac hfw default-bypass get`、`nac rule search`、`nac rule conflict-check`、`nac yunque-ticket list`
  - `admin` 命名空间只读命令：`nac admin yunque-rule search`、`nac admin gray-rule list`、`nac admin rule search`、`nac admin rule delivery-status`、`nac admin compiled-rule list`、`nac admin es-log-config get`、`nac admin audit-log list`、`nac admin nsg-rule-type list`、`nac admin nsg-agent list`、`nac admin nsg-agent-param list`、`nac admin nsg-monitor get`、`nac admin nsg-cluster list`、`nac admin nsg-cluster get`、`nac admin nsg-cluster-name list`、`nac admin matrix-rule list`、`nac admin matrix-rule get`、`nac admin dialtest-task list`、`nac admin dialtest-agent list`、`nac admin dialtest-server-psm list`
  - `--rule-plat` 表示规则平台；Yunque/Gray/管理工单/匹配 Agent 的 `--rule-type` 表示具体 NSG 规则类型，未知时先用 `nac admin nsg-rule-type list` 查询，不要把 `nsg` 当作具体类型。
  - `nac rule search` 是最全面的 NSG 正式规则查询接口，覆盖 MGT/Honeycomb、Yunque、`nac_sec`/NAC Security Center 和 TCC 四种正式规则来源；其中 `--rule-type` 可选，省略表示全部规则类型。灰度规则位于独立表，该接口查不到；灰度对象用 `nac admin gray-rule list`，最终数据面集合用 `nac admin compiled-rule list`。
  - 规则查询路由是硬约束：明确 MGT/用户规则/default/tob 表才走 `nac user-rule list`；明确 Yunque 管理员规则才走 `nac admin yunque-rule search`。其余正式规则匹配在 `nac rule search` 与 `nac admin rule search` 之间遵循“显式意图优先，条件完整度辅助”：前者查询编译前所有符合条件的规则，后者查询指定 Agent 数据面实际命中的规则。缺少精确匹配所需的 `rule_type` 或 Agent 时先发现或确认；仍无法确定时可以分别查询，但必须区分两类结果。五态匹配细节必须读取 `bytedance-nac`。
  - 只有明确查询编译后或下发到数据面的规则时使用 `nac admin compiled-rule list --rule-type <type>`；普通规则查询不得使用该命令。
  - 查询某条规则的下发情况、下发阶段或未生效原因时使用 `nac admin rule delivery-status --id <rule-id>`；CLI 自动推导 `rule_type` 和反向规则。用户未指定 Agent 时检查列表第一项；明确指定时可重复传 `--agent <ip>`，最多 4 个。包含同一 Agent 的两次查询至少间隔 5 秒；不生成 `--rule-type` 或 `--reverse-rule-exists`。
  - 查询哪些 NSG 日志会被 ES 采集时使用 `nac admin es-log-config get`；集群 IP、NSG 规则类型和规则 ID 三组条件是 OR，任一已配置条件命中即采集。
  - “我的用户规则/用户工单”先用 `auth userinfo` 读取 `data.username`，再传 `--creator`；“我的 Yunque Rule/管理工单”把同一 username 传给 `--username`。所有/可见/我能看到/POC 查询不自动添加所有权过滤。
  - Yunque 管理工单列表不属于管理员专属命令；不要生成 `nac admin ticket list`。
  - 例子：“按 ID 查用户规则”“查询某类型 Yunque Rule”“按生效 ID 查灰度规则”“列出我作为 POC 可见的 Yunque 管理工单”“获取 Ticket 的 approvalUrl”“查询 PSM 的 HFW Policy/ACL/Permission”“查看 NSG 异常集群和 Agent 状态”
  - TCC、TCE、APM、Log 各自独立路由，不因单独提到这些工具而进入 NAC。
- PIPO MIS order lookup plus security compliance KYB/KYC case search and attachment download：`pipo order get` / `pipo security compliance kyb` / `pipo security compliance download` / `bytedance-pipo`
  - 例子：“按 order id 查 PIPO 订单”“pipo order get --region my”“按 client id 查 PIPO KYB case”“搜 ukyc_ttop_merchant 的 KYC 列表”“用 --raw 看证件 file id”“下载 KYB cert 文件”
- Sky 营销直减券批次白名单读取与增删（overwrite 语义的 read-modify-write）：`sky marketing-coupon whitelist get` / `add` / `delete` / `bytedance-sky`
  - 例子：“看这个营销批次的白名单”“给营销批次加白名单”“sky marketing-coupon whitelist add --batch-id ... --members ...”“从白名单里移除某个 uid”
- TikTok LIVE DECC（DES）当前用户合规工单、Ticket 状态与内嵌 Agent 对话：`ttlive-compliance-ace` / `bytedance-ttlive-compliance-ace`
  - 例子：“列出我的 TikTok LIVE DECC 工单”“看这个 DECC session 的 Ticket 状态”“读取 Agent 历史”“继续跟工单 Agent 对话”
  - 只适用于 TikTok LIVE DECC/DES 合规数据工单，不要用于非 TikTok LIVE compliance 工作流；`ttlive-compliance-ace chat send` 默认 dry-run，只有用户明确确认目标 session 与消息原文时才加 `--yes`，超时后先查 history，不要直接重发。
- 仓库、MR、Issue、Review、CI、文件、跨仓搜索：`codebase`
  - 例子：“看这个 MR”“给这个 MR 回复评论”“查这个仓库的 CI”
- EOpsX guard 源树、权限、角色、环境和 CN/BOE 全量同步：`eopsx guard`
  - 例子：“查 eopsx guard source tree”“同步 CN 到 BOE go_guard 环境”“查看 go_guard 角色权限”
- Coco AI Code Agent：`coco` / `bytedance-coco`
  - 旧 Copilot 编程任务走 `coco task/chat/sandbox/env`；需要长期 Agent 配置、Session、多模态消息、SSE 订阅或中断时走 `coco workspace/device/agent/session`。
  - 例子：“创建一个 Coco Managed Agent session”“给 Coco session 发消息并订阅到 idle”“中断这个 Coco session”
- BMA Agent 平台控制面与 Runtime 会话：`bma` / `bytedance-bma`
  - 覆盖 Workspace、Model、Agent/Version、Session、Credential、Connector/Schedule、Dataset/Doc、Skill/Plugin，以及受控的 Runtime prompt/event/SSE 操作。
  - 写操作默认只生成确定性 plan；必须显式确认后才 apply，并在写后执行 readback。敏感 prompt、metadata、credential 值使用权限受限的文件参数，不写入 argv 或普通 HTTP trace。
  - 当前仅支持固定 CN prod/PPE 目标；`bma dataset doc update` 按已部署合同替换 FILE 文档内容，默认只生成 plan，确认后使用 `--yes` 单次提交并 readback。未被 live Engine/IDL/Frontend 契约确认的 Runtime Config、Schedule restore 等能力保持 blocked，不猜测 endpoint。
- Magibook 独立 Hive/ClickHouse/Doris SQL、book/cell、Prism、workspace、asset 与 MagiTeam agent：`magibook` / `bytedance-magibook`
  - `--region` 选择资源所在区域；所有区域的 ByteCloud JWT 鉴权都走 CN。book 和 cell 绑定单一 region，列表为空或资源不存在时先核对 region。
  - 用户只要求“执行/跑这条 Hive、ClickHouse 或 Doris SQL”，且未指定既有平台或平台资源 ID 时，默认使用 `magibook sql execute`。
  - 用户明确指定 Aeolus、Dorado、TQS、ByteHouse、Doris Ops 等既有平台，或给出其专属资源 ID（例如 Aeolus dataset、Dorado task、ByteHouse cluster、SG Doris Ops cluster）时，保留该平台原有路由，不静默改到 Magibook。
- 研发任务管理（创建发布任务、查看任务详情与部署状态、搜索任务列表、查询项目与需求）：`devflow`
  - 例子：”创建一个发布任务””查这个 devflow 任务详情””搜我的发布任务””查这个空间有哪些项目””查项目下有哪些需求”
- FTF 流量录制、流量回放、Outbound 调用成功/失败判定、API 回归测试、回放任务/报告分析与 DIFF 根因归因：`ftf` / [bytedance-ftf](references/subskills/bytedance-ftf/GUIDE.md)
  - FTF CLI 以 API-first 方式查询和操作 FTF/Tesla-X；任务或 Flow 链接先交给 `ftf target parse`，命令或参数不确定时再用 `ftf --help --all-help` 发现当前能力。
  - 核心能力：FTF v3 接入与录制状态检查；录制/采集无流量与回放无流量诊断；计划/任务查询和流量回放执行；任务、报告、Method、Flow 与 DIFF 查询；回放失败、DIFF 和回放报告智能归因分析。
  - 例子：“FTF接入”“录制不到流量”“录制无流量”“采集不到流量”“采集无流量”“回放没有流量”“回放无流量”“回放 0 条流量”“执行流量回放”“分析回放任务”“分析DIFF原因”“DIFF归因”。
  - 普通 API 测试或回归测试若没有 FTF、Tesla-X、流量录制或流量回放语境，不进入 FTF。
  - FTF task 的场景覆盖率或未命中场景走 Nario；Tesla RM 自动化测试计划/用例走 `tesla`。
- Nario 流量场景管理与计算：`nario` / `bytedance-nario`
  - 例子：“查这个 FTF task 的 Nario 场景覆盖率”“哪些场景没有命中”“分析低覆盖 method/模板”“查询或维护 Nario 模板/场景”
  - FTF task 的场景覆盖报告优先走 `nario measure report get --url/--ftf-task-id`，再用返回的 Nario task ID 查询 `scene-detail --summary`；完整未命中清单继续分页读取非汇总明细，不要用 FTF method 聚合或 raw OpenAPI 猜测未命中场景
- Dora 云真机/云手机：`dora` / `bytedance-dora`
  - 例子：“查询 Dora 云真机”“申请云手机”“获取 Dora ADB、BDC 或鸿蒙 HDC 地址”
- BITS 研发任务、流水线、MR、钟馗静态检测、release、任意门代理抓包、mock 与 Rewrite 配置：`bits` / `bytedance-bits`
  - 例子：“查 BITS pipeline”“读取钟馗错误定位”“重试这个 jobRun”“调试任意门抓包”“列任意门设备”“把任意门 capture 转 curl”“创建/启停任意门 mock”“创建/编辑任意门 Rewrite”
  - 任意门不是顶层命令域，使用 `bytedcli bits anywhere ...`；完整说明见 [references/subskills/bytedance-bits/references/anywheredoor.md](references/subskills/bytedance-bits/references/anywheredoor.md)
- Bytediff diff task、traffic task、AB test、冒烟测试任务创建，task 列表/终止/重跑，report、字段 diff 报表与 PSM 配置查询（默认即 CN 区，跨区用全局 `--site`，如 `--site i18n-tt`）：`bytediff` / `bytedance-bytediff`
  - 例子：“创建 Bytediff AB test”“查 Bytediff report”“提交普通 diff_task”；创建类命令传完整 JSON payload，先 `--dry-run`，确认后 `--yes`
- ByteFlow 工作流引擎、应用/状态机/revision 查询、workflow JSON/ASL 校验与安全写操作辅助：`bytedance-byteflow`
  - 例子：“查 ByteFlow app/状态机”“校验这个 workflow JSON”“创建或更新 ByteFlow revision”
- LG Admin MaaS / Prifly / PilotBench 只读查询：`lg-admin maas`
  - 覆盖 BU 配置、模型在线信息、PilotBench profile 记录、perf 状态与详细结果；不要使用顶层 `maas`。
- LG Admin Torch 发版/发版本、package meta 查询与 discard、镜像发布、构建历史页同款 payload、cpu/cuda/mlu Torch 版本选择、use cache / skip arm / image rebuild 等高级选项：`lg-admin torch`
  - 路由优先级：当用户明确提到 ICM 查询语义，例如 ICM prod、发布历史、最近发布、构建 commit、构建仓库、repo/build 信息查询时，优先走顶层 `icm`。产品名、包名或 repo 名中的 `lagrange`、`torch`、`cpu`、`cuda`、`mlu` 等词不能单独触发 `lg-admin`，也不要说或尝试 `lagrange torch`。
  - 例子：“发一个 lg-admin Torch DEV build / 发版 / 发版本”→ `lg-admin torch release package build`；“查询 LG Admin Torch package 版本 meta”→ `lg-admin torch release package get`；“废弃 LG Admin Torch package 版本”→ `lg-admin torch release package discard`；“发 LG 镜像 / 发布 LG Torch 镜像”→ `lg-admin torch release image build`
- Academy 广告特征开发与管理（source_v2、raw feature set group、feature 搜索）：`academy`
  - 例子：“查 Academy 里有没有这个 source”“搜某个 raw feature set group”“按关键词查在线 feature”
- People 自助请假记录查询与全天/半天假申请：`people`
  - 例子：“查我今天请了几天假”“帮我请一天年假”“给今天下午补提半天假”
- Jinshu / 云锦书消息预览与发送：`jinshu`
  - 例子：“预览这段锦书消息”“发送这段锦书消息”
- ByteCanteen 楼栋搜索与实时早 / 午 / 晚餐菜单：`canteen` / `bytedance-canteen`
  - 例子：“查某办公楼今天有什么吃的”“搜索食堂楼栋”“看今天午餐”
- Guardian（星环 / 小 R）应急管理查询，以及受保护的应急配置、业务线、事件标注/时间/报警静默、订阅、TODO 和根因分类单目标写入：`guardian` / `bytedance-guardian`
  - 面向已接入团队，仅访问和操作当前用户有权限的 CN 数据；“星环事件”“小R报警”“Guardian TODO”应路由到这里。
  - Guardian（星环）是小 R 稳定性管理平台中的应急管理模块；裸“小 R”先澄清，小 R 聊天/机器人/转发不路由到该命令。写操作默认仅预演，必须用同一计划的确认令牌和 `--yes` 提交；共享 MCP 禁止真实提交。RCA/Goalkeeper、AI 诊断及未核实的事件生命周期写入仍不支持。
- ByteHealth 按摩时段、预约与释放提醒订阅：`health` / `bytedance-health`
  - 例子：“查 12 号按摩师的时段”“预约按摩”“订阅满员时段的释放提醒”
- Lark Oncall 工单、打标/归因元数据、oncall 群消息和值班信息：`lark-oncall` / `bytedance-lark-oncall`
  - 例子：“查某业务线过去 7 天的 oncall 工单”“拿某个 ticket 的 oncall 群聊天记录”“列 oncall tag/归因选项”
- ByteCloud Oncall Platform 工单查询、智能问答、故障排查和升级：`oncall` / `bytedance-oncall`
  - 例子：“查我发起的 Oncall 工单”“用 Oncall 排查这个故障”“发起 P0 Oncall”“创建 Oncall 群”
- ByteGate 工作区、gatekeeper、规则与工单流程：`bytegate` / `bytedance-bytegate`
  - 例子：“查这个 ByteGate gatekeeper”“增加/移除 workspace 或 gatekeeper 管理员”“打开/关闭灰度开关”“增加/移除灰度白名单”“查 TCC 同步状态”“审批或拒绝这个 ByteGate 工单”
  - 资源级命令统一携带 `--workspace-id`；跨 workspace 查询（`workspace list`、`workspace follow list`）除外。CLI 会用它校验 gatekeeper / ticket 归属，规则命令还会校验 payload 内的 `workspace_id`。
  - `workspace follow list` 查询当前用户关注的 workspace；`workspace follow add --workspace-id <id>` 关注 workspace，必须显式 `--dry-run` 预览，确认后 `--yes`。
  - `gatekeeper list --keyword <name> --creator <user> --status off|gray|full` 支持按 Feature Gate 名称、创建人和开关状态筛选。
  - `workspace update --payload-file <full-config> --add-admin/--remove-admin/--add-member/--remove-member <user>` 修改成员；该接口全量替换配置，必须显式 `--dry-run` 预览，确认后 `--yes`。
  - `gatekeeper admin add/remove --gatekeeper-id <id> --user <user>` 增量维护 gatekeeper 管理员；`gatekeeper update --gatekeeper-id <id>` 用于 `--category`、`--description`、`--status off|gray|full` 等通用更新。两类命令都会先读取当前配置并保留未变更字段，必须显式 `--dry-run` 预览，确认后 `--yes`。
  - `gatekeeper delete --gatekeeper-id <id>` 先校验目标并创建删除工单，审批该工单后才真正删除；`ticket reject --ticket-id <id> --comment <reason>` 拒绝工单。两者必须显式 `--dry-run` 预览，确认后 `--yes`。
  - 规则更新前先获取完整 payload，用类型化 `--whitelist-user`、`--whitelist-device`、`--blacklist-user`、`--blacklist-device` 及对应 remove/clear 参数修改；写操作必须显式 `--dry-run` 预览，确认后 `--yes`，审批必须单独执行 `ticket approve --yes`。
- 字节内场 NAT（DCS）的配置出口与历史流量只读查询：`nat` / `bytedance-nat`；与 Bytebox 并列，独立于 ByteCloud Oncall。火山云 NAT 使用 `volcano`，办公室出口不使用本域。
  - 例子：“按 PSM、VDC 和源 IP 查内场 NAT 配置出口”“按目的公网 IP 和时间查内场 NAT 历史连接”
  - 只有用户仅说 NAT、且上下文无法判断场景时才先询问；已明确内场或火山云场景时直接路由，不重复询问。
- ByteCloud Supabase 项目、工作区、分支、数据库、Supabase 服务和原生 MCP：`supabase` / `bytedance-supabase-companion`
  - 普通 CLI 命令使用 `bytedcli supabase ...`；需要原生 MCP tools 时使用 `bytedcli supabase mcp serve`；共享 bytedcli MCP 使用 `list_commands(domain="supabase")` 和 `run_command`
- ByteCloud PostgreSQL 项目、工作区、分支、Compute、数据库、角色、BytePG 连接和原生 MCP：`postgresql` / `bytedance-postgresql-companion`
  - 普通 CLI 命令使用 `bytedcli postgresql ...`；需要原生 MCP tools 时使用 `bytedcli postgresql mcp serve`；共享 bytedcli MCP 使用 `list_commands(domain="postgresql")` 和 `run_command`
- Design Space / Codin D2C 设计转代码、Figma 节点推荐、D2C XML/预览图、图标下载与代码校验：`design-space` / `bytedance-design-space`
  - 例子：“把这个 Figma 设计稿转代码”“先帮我切分这个 Figma Canvas 里的页面节点”“用 D2C 下载这个设计稿的图标”“校验代码是否符合 Figma”
  - 如果用户给的是 Figma Canvas / Page / 大 Section，先运行 `bytedcli --json design-space d2c node suggest --url <figma-url>`，再把候选 URL 交给 `get-figma-data`
- VOC（抖音 CEM 用户反馈，cem.bytedance.net）feedback 详情查询：`voc` / `bytedance-voc`
  - 例子：“查这条 voc feedback 详情”“按 voc 控制台 URL 拉反馈”“按 voc 分享链接拉反馈列表”“看本地 voc 鉴权 cookie 是否还在”
- Procurement 采购业务线（当前支持 Supplier Management 供应商管理查询）：`procurement` / `bytedance-procurement`
  - 例子：“按统一社会信用代码查供应商”“搜索这个供应商名称”“确认第三方供应商的数据来源”
- Vimo Web 的 CapCut 海外创作者管理视图、用户查询/基础用户视图和模板查询及受控语义写操作：`vimo` / `bytedance-vimo`
  - 统一通过全局 `--site cn|i18n` 选择国内或海外；`--site i18n vimo creator` 表示创作者管理视图，`--site i18n vimo user` 表示用户查询/基础用户视图，两者是同级业务域，不能混用
  - 例子：“查询/修改海外创作者权限或标签”“按用户ID/CapCut UID查询基础用户视图”“下载 Vimo 模板包”“创建线索下发计划”“终止征稿任务”“发布任务奖励”“上下线模板”
  - RID、Vimo 资源 URL 或模板 ZIP 下载走 `--site cn vimo template get/download`；模板管理页面的 TemplateID 精确查询走 `--site i18n vimo template list --query-mode server --template-ids ...`，并要求对应的区域业务 ID。上下文不足时先澄清，不要猜测两类 ID 可以互换。
  - 边界：查询 leaf 与语义写 leaf 必须分流；所有写入默认 dry-run，确认相同 payload 后才追加 `--yes` 单次提交，结果未知绝不重试。Creator BFF 权限/标签与 Material OpenAPI operator 权限不是同一体系；后者及上传/服务账号工作流仍用 `vimocli`
- IconBox 图标库、分组、图标查询、SVG 上传与 React/Vue/CDN/字体导出：`iconbox` / `bytedance-iconbox`
  - 写入默认 dry-run；检查目标库、分组、名称和颜色模式后再加 `--yes`
- TOP 资源管理、新热挖掘、合集管理、榜单管理、热榜入库、批量导入、数据提取、批量操作与系列管理：`top` / `bytedance-top`
  - 分别使用 `top entity|discovery|album|ranking|warehouse|import|extract|batch|series`；写命令默认 dry-run，必须确认预览后显式添加 `--yes`
- Warlock 网络抓包分享读取：`warlock` / `bytedance-warlock`
  - 例子：“读取这个 Warlock share 的 API response”“拿 response headers / x-tt-logid”“查看脱敏后的 request headers”
  - 使用 `bytedcli --json warlock share get --url '<warlock-share-url>'`；不要对分享页调用 `insearch get` 后解析 HTML
- Logifier 日志回捞与 batch 查询：`logifier` / `bytedance-logifier`
  - 用户明确提到 Logifier、Logifier batch、Logifier DSL，或要求按业务线和设备 ID 回捞日志时路由。它与 PSM / LogID / Footprint 日志查询不同，不要混用 `log` 命令。
  - 回捞时只补问缺少的业务线、设备 ID 和时间范围，然后先执行 `logifier retrieval create --party <party> --device-id <id> --last <duration>` 预览；用户确认后追加 `--yes --wait`，需要筛选时传 `--dsl` 自动查询完成的 batch。已有 batch 则先用 `logifier batch get --batch-id <id>` 核对，再用 `logifier batch query --batch-id <id> --dsl <expression>` 查询；任务尚未完成时用 `logifier retrieval wait --task-id <id>` 续等；回捞结果指定其他 Logifier 集群时再传 `--api-base-url`。
- FundEye / Fullink 核对规则、diff、告警：`fundeye`
  - 例子：“查这个规则详情”“按 rule_id 看最近一天的 diff”“查某个 alarm_order_id 对应的 diff”
- Starling 文案平台、项目、空间、文案搜索：`starling`
  - 例子：“查这个 Starling 项目”“创建一个 Starling space”“搜索某个文案 key”
- Luban npm 包查询、PyPI 制品仓库搜索/版本查询与发布：`luban`
  - 例子：“查某个 TTP-US npm 包在 Luban 里有没有”“看某个包的 2.1.x 版本”“按 pip 包名查 Luban PyPI 仓库”“查 Luban PyPI 仓库版本列表”“基于 master 分支发布 PyPI 版本，先 dry-run，再确认发布并轮询结果”
- Luban BPT 制品仓库、分支、commit、版本查询与发布：`luban bpt`
  - 例子：“查 Luban BPT 仓库的分支和版本”“预览 BPT 发布 payload，确认后创建任务并轮询结果”
- Lynx 开发、DevTool/CDP 调试、Sandbox、性能 trace、运行时录制、堆快照/实时全局内存检查与 LynxExample app 工作流：`lynx` / `bytedance-lynx`
  - 非 LynxExample 任务先运行 `bytedcli lynx skills list`，再按实时 description 加载最具体的返回项；不要猜测 Skill 名称或 agent-lynx 子命令。
- SAR Creator Arcade 游戏制作、项目状态与可玩预览：`sar`
  - 例子：“帮我做一个塔防小游戏”“查看我刚才生成的游戏”“拿到游戏预览地址”
- Argus Hybrid 工单生成：`argus hybrid`
  - 例子：“给 Lynx 应用绑定 Gecko channel”“给 H5 应用新增安全 URL”“申请 H5/Lynx JSB 权限”“申请 secure 方法”“搜一下这个宿主 label”
  - 当前用户身份来自 `bytedcli auth userinfo`；命令通过 Argus Hybrid OpenAPI 创建工单，默认只生成工单，不自动执行。`--hosts` 支持 label-only 模糊搜索，唯一 host 或 host group 命中会自动解析，多命中返回候选。
- Mango / 芒果任务管理：`bytedance-mango`
  - 例子：“登录 Mango”“列出 Mango 空间”“查询 Mango 任务”
- Gecko CN 控制台资源查询（诊断、App、Project、Deployment、Channel 概览/分组/巡检、离线规则树、资源包与 workflow/tag/scan/stats 子资源）及 PPE 离线资源包创建、env lane 启用/停用：`gecko`
  - 例子：“查 Gecko CN 某个 channel 的详情”“列某个 channel 下的离线资源包”“查看资源包处理日志”“从 SCM 构建创建 PPE 离线资源包并启用或停用 env lane”
- TikTok Gecko 控制台只读资源查询（工作台、App、Channel、Ticket、Host App、Deployment）与资源下发诊断（diagnose 任务）：`tiktok-gecko`
  - 例子：“查 Gecko 某个 channel 的详情”“列出 deployment 下所有 channel”“筛选某个 creator 的 Gecko 工单”“诊断 TikTok Gecko 资源为什么没下发到设备”
- 技术文章、知识问答、AI 对话 / 附件 prompt：`bitsai`、`tika`、`aime`、`ida`
- iDA Deep Research、iDA Agent / Skill / MCP / raw session 查询：`ida` / `bytedance-ida`
- DevSpec 代码规范、扫描规则、Golang/JavaScript/TypeScript 核心规范摘要：`devspec`
  - 例子：“读取 ByteDance Go 代码规范”“按语言拉取扫描规则”“按 DevSpec 检查 REQUIRED 规则”“没有登录态时先用 Go/JS 离线摘要兜底”
- AI Dev Pro AFS / Agent File System 代码、接口、PSM、调用图、DB caller、FE wiki 等研发流程内的知识查询：`ai-dev-pro afs`
  - 例子：“查这个 PSM 的接口参数”“搜某个代码实体”“查接口下游”“查 某个psm的AGENTS.md 知识”
- ByteCloud 产品与组件的官方文档、架构、原理、能力、用法、限制和排障：`cloud-docs` / `bytedance-cloud-docs`
  - 例子：“RDS 的架构是什么”“TCE 怎么接入”“BMQ 有哪些使用限制”“neptune的原理是什么”
- 跨来源内部搜索（飞书文档、内网、ByteTech 文章、BitsAI 问答）与内部 URL 只读 GET：`insearch`
  - 例子：“搜索 kitex ppe 环境”、“查飞书文档里有没有 BMQ 接入指南”、“用 BitsAI 问一下 TCC 怎么配置”、“用当前登录态 GET 这个内部接口”
  - 读取内部 HTTP(S) URL 用 `insearch get <url>`；无法结构化解析的允许 URL 会自动走只读 GET fallback
- DevMind / DataMind 指标故事、复杂指标维度与 data_mart 取数：`devmind` / `bytedance-devmind`
- SQL、数据库平台、数据资产、报表、离线任务：`aidap`（Serverless PostgreSQL 的 Workspace/Branch/Compute/账号/数据库/连接/异步操作）、`rds`（ByteRDS MySQL 系；子组：`db`/`slow`/`alert`/`ops`/`bpm`）、`rds-pg`（字节云 RDS PostgreSQL，实例 ID 形如 `postgres-xxxxxxxx`，控制台路径 `/rds_pg/`）、`bytedoc`（ByteDoc/MongoDB 默认入口）、`tokadb`（TokaDB/Bytetable）、`bytekv`（个人 CN 身份，只读 namespace / table、业务鉴权配置和单 key）、`doris-ops`、`hive`、`bamboo`（离线规则增改查、Hive 规则详情与离线结果详情）、`hdfs`（HDFS 资源组配额 / 成员，以及目录容量、文件数与分区下钻）、`maxwell`（Maxwell Sample Center 只读样本、schema、任务、血缘、预览和校验接口）、`lg-admin maas`（MaaS / Prifly / PilotBench）、`magnus`（Magnus GLS metadata、表属性安全写入，以及 CN 表内容的 HSQL 执行面与 `magnus query` 分流）、`dorado`（子组：`project`/`task`/`instance`/`debug`/`adhoc`）、`blade`（子组：`task`，当前支持 `task get` 和 `--region mycis`；鉴权优先复用 `blade.byteintl.net` 站点 cookie 与 fresh ByteCloud JWT）、`oceanus`（子组：`project`/`tree-node`/`node`/`task`）、`aeolus`、`maya`（dashboard/chart/业务方向指标发现与取数）、`dataq`（RDS SQL 以及 ByteDoc 只读 find 查询）、`tqs`、`forge`
  - 例子：”查我关注的 ByteDoc 数据库””看这个库的慢查询””执行一段 SQL””查这个 dashboard 对应的数据集”
  - 独立 SQL 执行默认走 `magibook sql execute`（免配队列，支持查数与写表）；需指定队列或导出飞书/CSV 走 `aeolus query-editor query one`；已有 Dorado 任务载体走 `dorado adhoc exec`；指定平台或资源 ID 时用对应命令。
  - TokaDB Owner 表与关联 Cluster 盘点、本地 Markdown、飞书文档统一使用 `tokadb report`；不要分别调用 list 后手工拼文档。USTTP/EUTTP 是默认支持区域，缺凭证时分别运行 `bytedcli --site us-ttp auth login` / `bytedcli --site eu-ttp auth login`；只有本次任务明确不需要某些区域时才使用 `--exclude-regions <region,...>`。
  - TokaDB 创建 CF 工单使用 `tokadb ticket cf create`、禁用表工单使用 `tokadb ticket table disable`；字段规则见 `bytedance-tokadb` 的 `references/ticket.md`，必须收集完整，先 dry-run，用户确认后才 `--yes`。当前仅开放这两类工单。
  - 已有 SG Doris cluster id，需要直接执行 SQL：`doris-ops query run`
  - 在 hive-sql 上进行语法检查、提交 sql 任务、获取状态和结果：`tqs`
- Flink / Godel 流批任务的只读根因诊断、JM 静默、启动与 failover、checkpoint、Lag、反压、吞吐、延迟、倾斜、资源和配置咨询：`flink` / `bytedance-flink`
  - 例子：“诊断这个 Dorado Flink 任务为什么持续 Lag”“确认 JM 静默还是宿主机不可用”“分析 checkpoint 变慢的决定性证据”
  - 先固定 task、application attempt、job、版本和故障时间窗；自动流程只读取证，证据不足时输出 `PARTIAL/UNKNOWN`，不自动重启、扩缩容、改配置或重置 offset。
- TEA / tea-next 看板、报表、快照、DSL、analysis 查询、行为细查、事件元数据、事件上报、SG LLM workbench operations-agent 的 agent 会话，以及 CN Titan 项目角色查询与新成员邀请：`tea` / `bytedance-tea`
  - 例子：“读这个 TEA 链接的数据”“从 tea-next 快照拿 DSL 并查询”“查某个事件按维度分组”“查询 behavior-detail 行为流”“看 agent 会话每一步调了哪些工具”“列出项目可分配角色”“邀请新成员并绑定角色”
  - tea-captain SG 链接做 `get-dsl | query` 时，query 阶段也传同一个 `--url`；完整说明见 [references/subskills/bytedance-tea/GUIDE.md](references/subskills/bytedance-tea/GUIDE.md)
- NVQoS / VQoS 空间、数据集与智能归因：`nvqos` / `bytedance-nvqos`
  - 例子：“列出某个 NVQoS 空间下的数据集”“触发 rootcause 归因分析”“按 Filters JSON 发起归因”
- Eventbus CN-only event 详情查询：`eventbus-cn`
  - 例子：“查国内 CN 这个 event 的详情”“确认 event 绑定了哪些 topic”“验证 eventbus OpenAPI 是否可用”
  - 限定：仅支持国内 CN/BOE，i18n、US、EU 用户不支持该 skill
- BMT 多租户服务、标签、资源、隔离集与 user role 查询：`bmt`
  - 例子：“按 PSM 反查 BMT service”“看这个 PSM 绑定了哪些 RDS 或 RocketMQ 资源”“查某个 BMT resource code 对应的连接信息”
- 搬站平台项目、组件、消费者和流水线查询：`move-engine`
  - 例子：“按 PSM 查搬站项目”“列出项目下的 TCE item”“查 TCE/FaaS 消费组”“按 UUID 查搬站流水线”
  - 仅支持 `--site cn|i18n-tt`；一期命令全部只读
- Watchdog Diag HTTP/FaaS、日志查询与合规区 RPC/DB 断言：`watchdog` / `bytedance-watchdog`
  - 例子：“BDEE 打不了 US-TTP 的 RPC/DB，用 Diag 在合规区断言字段是否等于预期”“RDS 打 US-TTP2/useast8 / EU-TTP2/no1a”
  - 与 ByteDog（`bytedog`）不是同一产品。BDEE 无法直接调用 US-TTP / EU-TTP 内的 RPC；Diag 在合规区内执行并对结果断言。ROW 可读回包用来写 `--assert`；合规区只回是否命中
- ByteGraph V3 API 多 Vregion 元数据查看与 Gremlin Extended 只读查询：`bytegraph` / `bytedance-bytegraph`
  - 例子：“查看这个 ByteGraph 的部署机房、点边、TTL 和索引”“在 Singapore-Central 用 Gremlin 查指定顶点”
  - 元数据命令传全局 `--site`、`--vregion`；查询还要传全局 `--vdc`，并在 Gremlin 中显式使用 `.limit(...)`
- 模型下发平台场景、模型聚合信息、模型修订历史与场景版本历史查询：`model-dispatcher` / `bytedance-model-dispatcher`
  - 例子：“列出我能访问的模型下发场景”“查 demo_model 的模型信息和历史”“查场景版本历史”
  - 认证使用独立站点 Web Session；先执行 `auth login --session`，不要用 ByteCloud JWT 代替
- ByteMesh 服务、升级计划、资源/plugin 市场、已安装插件、工单与异常的多站点只读查询：`bytemesh`
  - 例子：“读取这个 ByteMesh 服务接入链接”“查服务有哪些 plugin”“看某个 cluster 的 plugin graph”
  - 鉴权复用目标 `--site` 的 ByteCloud 用户 JWT，不读取浏览器凭据且不跨站 fallback；401 登录同站点，403 申请目标资源的 RBAC 权限
- 查询或诊断 Forge 训练任务：`forge job diagnose` / `forge job get` / `forge logs`
  - 需要同时查看显式 Forge log error code、经 job/stage 校验的 Primus application exit code/diagnostic 和有界 pod 状态时，优先 `forge job diagnose`；text 最多展示 20 条异常 pod，`--json` 保留全部 retained pod items
- 判定模型是否还分发到某条推理 serving：`forge service-hub diagnose`
  - 例子：“这个 serving 的错误率涨了，是不是模型没部署”“某个模型在 Service Hub 上还在不在”
  - `verdict=not_deployed` 表示模型在 Model Hub 已下线，serving 上没有它；`verdict=healthy` 可用于排除分发方向。只覆盖经 Model Hub 分发的 serving
- Chronos 调度平台：`chronos`
  - 例子：“分页列出命名空间”“按 namespace 看任务列表”“按 task_id 看 HTTP 调度链接和报警接收人”
- OneService query 元信息、版本详情、SQL 提取：`oneservice`
  - 例子：“查这个 OneService query 的元信息”“按 queryId 拿当前 ONLINE 版本的 SQL”“按 versionId 看 query detail”
- Holmes demotion 降级预案查询、TrustPress、TikDiff、TrustData、ByteCore、IndexService proto/record debug、TBase 产品/字段/row-key 查询、release checker、code-review 与 TikTok Debug：`holmes` / `bytedance-holmes`
  - 例子：“列 Holmes IndexService proto”“按显式参数读一条 IndexService record”“倒排 IndexService 查询”“查这个 TBase product 的配置”“列某个产品的字段”“给 TBase 新增字段提审”“按 row key 查多字段或 all-fields”
- Byterec 平台所有组件统一使用 `bytedance-byterec`：覆盖 Candidate DB / CandsDB、Elements / Darwin 特征工程、Index Service、模型配置、Viking service config / ByteKV 与 Viking DB：`byterec candidate-db` / `byterec elements` / `byterec darwin` / `byterec indexservice` / `byterec model` / `byterec viking`
  - 例子：“查看 Candidate DB 页面”“按 label 查询候选库记录”“管理抽前/抽后特征和 feature group”“查询 Darwin 生产特征组”“按 PSM 或 service ID 看 Index Service config/cluster/operation”“修改 Viking flags 或部署 ByteKV”“执行 Viking DB DSL recall”
- Merlin job 提交和从中抽取 YAML 描述，Merlin job run 列表与 job->trial 解析，Merlin trial diagnose/local-log，Merlin job/trial 的 stdout/stderr 日志查询，Merlin tracking project、run、metrics 和 job 链接读取，`merlin` 计算资源 quota 的 group、cluster 只读查询：`merlin`
  - 例子：“提取这个 Merlin job 的 YAML”“把这份 `trial.yaml` 重提到 `seed-cn`”“看这个 Merlin tracking run 的 config/summary”“根据 job id 找 tracking 链接”“拉这个 Merlin trial 的 stdout/stderr”“查这个 trial 为什么还在排队”
- Helix 模型与 AI 任务生命周期，当前覆盖 Video AIPF 数据准备、训练/评估提交、状态查询、停止和记录查询：`helix`
  - 例子：“提交一个 Video AIPF 数据准备任务”“提交一个 Video AIPF 训练任务”“查询 Helix 评估状态”“停止这个 Video AIPF Ray 评估任务”“查最近的 Helix 训练记录”
- Fornax 官方 CLI 代理：prompt、trace/span/trajectory、execution/backflow、dataset/eval、experiment、label/label-job、analysis insight、warehouse、application、user、model 与 skill：`fornax`
  - 例子：“查询 Fornax trajectory”“查看 execution backflow”“列出 label job”“查询 analysis insight 报告”“执行只读 warehouse SQL”“发布 prompt”“查询 experiment 结果”
- LabelGPT 官方 CLI 代理：Space、Plugin、Service Node、Agent 工作流与任务、Dataset、Model、Metrics 和 Schema V2：`labelgpt`
  - 例子：“列出 LabelGPT Space”“发布业务插件”“编辑并校验 Agent 工作流”“查询 Agent 任务状态”“导入 Dataset”“查看 LabelGPT 核心指标”
- BES 元信息修改工单：`bes`
  - 例子：`bytedcli bes metadata update --config '{"title":"demo-ticket"}'`
- Kani 权限审批：`kani`
  - 例子：“查 Kani request 页工单”“看 reviewer 视角的已完结审批”
- 报销单查询与 AI 订阅报销草稿：`reimbursement`
  - 例子：“查最近报销单”“检测这个报销单”“用这张订阅收据创建 AI 学习研究报销草稿”“关闭/删除这个草稿”“确认后提交这个报销单”
- 配置中心、配置查询、新建、更新、发布与权限申请：`tcc`（子组：`namespace`/`config`/`deployment`/`env`/`site`/`permission`）、`bytestable`（子组：`wcc`、`qcss`）
  - 例子：”查 TCC namespace 下的配置””更新一个 TCC 配置并发布””申请某个 TCC namespace 的读写权限””在 WCC 里新建配置””更新 WCC 配置值””发起 WCC 配置工单””通过 QCSS 检查项”
- Ratel iOS setting 创建、setting 变更记录查询、generalservice 列表与服务判断：`ratel` / `bytedance-ratel`
  - 例子：“创建一个 Ratel iOS bool setting”“查某段时间内的 Ratel setting 变更”“列 3900 版本 generalservice”“判断某个 service 是否是 generalservice”
- 部署、环境、ByteCopy、服务树、TrafficRoute PrivateZone、域名治理、对象存储、云函数资源、Ent Platform Storage IAC 新表 workflow 提交/已有表 entry 导入/字段标注校验与 MOSS 测试物料管理平台查询：`tce`、`env`（子组：`site`/`service`/`bytecopy`/`device`/`ticket`）、`bytetree`、`ent`、`trafficroute`、`goofy`、`netlink`、`neptune`、`tos`、`faas`、`volcano`、`bytecloud`、`moss`
  - 例子：”查服务实例””看发布单””更新配置””做一个 Goofy preview””通过 Ent Platform 提交新表 workflow””导入已有 RDS 表到 Storage IAC entry””查询 TrafficRoute PrivateZone 的 zone / record / resolver”
  - FaaS 中的“BOE sandbox”“FaaS sandbox 测试环境”或 `faas-sandbox.byted.org` 必须路由为 `bytedcli --site sandbox faas ...`；该站点直连 sandbox 控制面并复用 BOE JWT。
- 火山账号自身账单（费用中心，账号视角）：按自定义时间范围（整月、跨月日期段、精确到分钟的时段、含当天并标注截至时间）查询应付费用，按天、产品、项目、计费项、实例下钻并对账：`volcano` / `bytedance-volcano`；内部成本中心、服务树或团队成本、预算与成本异动归因（BABI 口径）仍使用 `babi`
  - 例子：“查这个火山账号 9 月的费用并对账”“看今天截至现在花了多少钱”“10 月 1 日到现在每天各产品的费用”“昨天 10 点到 12 点的费用”
- CloudDev BOE 泳道开发实例创建、代码同步部署与本地 space 绑定管理：`clouddev`（子组：`instance`/`space`）
  - 例子：“在 BOE 泳道给这个 PSM 创建一个 CloudDev 开发实例”“把本地代码同步到这个 CloudDev 实例并跑起来”“改完代码重新同步 reload 一下”“停掉这个 CloudDev 实例”“列出本地记住的 CloudDev space”
- Devbox 开发机（BOE）目录浏览与创建（GPU 走 xflow 审批）、生命周期管理、SSH/SCP、IDE/监控/Web 终端连接、快照、云盘扩容、Computer Use 沙箱：`devbox`（子组：`snapshot`/`volume`/`xflow`/`sandbox`）、`bytedance-devbox`
  - 例子：“看看我有哪些开发机”“创建一台通用型开发机，先 dry-run”“查 GPU 开发机的审批进度”“SSH 到开发机执行命令”“打开开发机的 Web 终端”“给开发机数据盘扩容”“创建整机快照/回滚”“创建一个 Computer Use 沙箱并跑 GUI 任务”
  - 与 `clouddev`（BOE 泳道开发实例）不是同一平台，不要混淆。写操作遵循先 `--dry-run` 预览 payload、再 `--yes` 提交；SG/US-BOE 用 `--site boe --vregion sg|us`（US-BOE 新建入口已下线）。
- TAE / AI PaaS（MCP Server/Tool 优先用 `bytedcli tae mcp ...`；Sandbox 会话、Bash/PTY、进程、文件和端口用 `bytedcli tae sandbox ...`；Sandbox Connector 出网域名加白 / 访问策略（access-policy）用 `bytedcli tae connector domain|release|ticket ...`；其他未覆盖能力走内部 API 指南）：`bytedance-tae`
  - 例子：“在 TAE MCP Server 批量录入 RPC tools”“修复 MCP Input Schema”“把 HTTP tools 改成 RPC tools”“发布 MCP server revision”“给 sandbox connector 加白域名并提发布工单”“调研 TAE Agent/Sandbox/Memory API”
- TMates unified Space、Memory Store、managed agent 与 sandbox run：`tmates` / `bytedance-tmates`
  - 例子：“看这个 TMates share URL 的运行详情”“列这个 unified Space 的 Memory Store 并读 `MEMORY.md`”“创建或更新 TMates Space”“查 MP2C Regression Steward Agent 配置摘要”“确认当前 bytedcli JWT 是否能调 TMates OpenAPI”
  - `tmates space` 只支持 unified Space；已知兼容 scope ID 可显式传 `--scope-type ma-space`，不会跨 scope 回退。Space / agent / run 写入都要求 `--yes`。TikTok ROW 网关用 `--site i18n-tt`。
- Janus / Janus Mini 泳道、group、配置、IDL、endpoint、backend 与发布 workflow：`janus` / `janus-mini` / `bytedance-janus` / `bytedance-janus-mini`
  - 例子：“创建 Janus 泳道”“查询 Janus Mini group service_type”“创建 endpoint/backend”“创建 publish workflow 并查询状态”
- Spark Platform 空间与链路资源：`spark-platform`
  - 例子：“列出 Spark space”“按业务线 bid 列 link”“某个 space 下的 link”“拿某个 link 的完整 raw（含所有 version 与原始 deployConfig）用 `link get`”“要最新已发布 version + 解析后的 schema（含 schemaUrl / bundle / bundlePath）用 `link summary`”“列某个 link 的 env 配置”“给 link 设置 PPE env，先 `--dry-run` 看 payload 再真实执行”“删除某个 env”“指定非默认 `--app-id`”
- Kross workspace、容器 workload 与虚拟机管理，含 VM 镜像、创建、电源操作及 SSH/RDP 本地转发：`kross`
  - 例子：“查询 workspace 可用的 VM 镜像并创建虚拟机”“启动、停止或重启 Kross VM”“通过 loopback 端口转发访问 VM 的 SSH/RDP”“创建 job workload”“通过 webshell 执行命令”“上传或下载 workload 文件”
- GPCP（SYS-OnePlatform）伞平台：Aegis 工单只读列表/详情用 `gpcp aegis issue list/get`；SDP 合规诊断用 `gpcp sdp`；MSC 应用、BPEA DFID、三方 SDK API、DS TPSDK 查询及已有 API 的受限治理注册用 `gpcp msc`
  - 例子：“按 repo / commit / rule 查 Aegis 工单”“看 Aegis ticket 详情”“给 CloudIDE workspace 创建 SDP 实例”“通过 SDP 跑 `tail -n 200`”“按中英文应用名找 MSC app id”“查询 BPEA DFID”“按 class name 查组件归属”
- 日志、Footprint/TCE pod 文件日志、没有 application/History 上下文的独立 concrete 日志 URL 下载、监控、告警、Dashboard、Kubernetes 对象生命周期 trace、App 异常趋势、App/OS symbol、Redis / ABase / Kafka / RocketMQ / EventBus、Vela 单机指标：`log`（Footprint 入口是 `log footprint`）、`apm`（子组：`service`/`redis`）、`kelemetry`、`slardar`（子组：`web`/`app`/`os`）、`vela`（子组：`one-machine`）、`cache`、`abase`、`bmq`、`eventbus-cn`、`rmq`（含 Mirror 同步链路查询、已有集群 Topic 创建审批与 PSM Topic 权限申请；创建默认 dry-run，`--yes` 提交审批）
  - 例子：”查这个 logid””下载这个独立 Footprint / mljob-log-proxy 日志 URL””tail 这个 Footprint pod 日志文件””先看某个接口的总体瓶颈””按 logid 看链路各节点延迟””查某个 K8s 对象的 Kelemetry trace””看 Redis 大 key””分析这个告警页””查这个 Vela one-machine 页面里的指标””根据 Slardar dashboard URL 看看板配置或改标题””用 Slardar App issue URL retrace native 栈””用 Slardar OS issue URL 解析主线程 native 栈””搜索 RocketMQ topic””查看 RocketMQ consumer group 列表””在已有 RMQ 集群上先 dry-run 预览 Topic 创建审批，确认后用 `--yes` 提交””给 example.service.consumer 申请 RocketMQ Topic 的消费权限””为 PSM 申请 RMQ producer 权限前先展开精确 Topic 范围”
- EOpsX 电商运维：服务元数据/服务树/调用对强弱依赖（meta）、报警事件列表（alarm）、变更事件中心（event）、稳定性度量与事故数/业务 SLA（fatal）、限流子配置（limit）、VOC 客诉感知预警（voc）、链路 SLA 与不可用事件（sla）、BCP 业务异常检测/错账（bcp）、风险巡检/风险项/风险工单（risk）、归因 Skill 开发/草稿管理/远端测试与 Session 调试（dev）：`eopsx` / `bytedance-eopsx`
  - 例子：“查电商业务线树”“列某个 PSM 的报警事件”“看这段时间的变更事件”“查业务 SLA 总结”“查某条链路的不可用事件”“搜 BCP 核对规则”“列风险巡检工单”
- Primus UI/History 应用列表与详情、AM、Conf/Job/Data、环境变量、role/pod、Doctor/Timeline/TaskBuild、Streaming/Flow、日志、CRD、Pod 生命周期：`primus` / `bytedance-primus`
  - 例子：“查这个 Primus app 为什么失败”“拿 role pod 的日志索引”“看 Primus CRD 和 Pod lifecycle”
- Godel Explainer 调度诊断、Pod/PodGroup/Application pending、FIFO 队头和节点组资源，且已有精确 cluster、namespace 和 workload name：`godel` / `bytedance-godel`
  - 例子：“用 demo-cluster、demo-namespace 和 demo-podgroup 查这个 PodGroup 为什么一直 pending”“查询已有 diagnosis id”
  - 当前只支持 `cn` 与 `i18n-tt` 生产 API；BOE、I18NBD、EUTTP、USTTP 以及 Primus/Forge/Fed 自动解析均不支持，不跨区域 fallback。
  - Godel stream-applications / Flink Web 中的 job、checkpoint、failover、lag 和反压仍属于 `flink` / `bytedance-flink`，不走 Godel Explainer。
- ByteDog ：`bytedog`
  - 例子：”采一个 CPU 火焰图””分析这个 ByteDog URL 的 profile 结果””查历史 profiling 任务””先查这个 pod 里的 PID””分析 pthread 锁竞争””看 jemalloc 内存分配火焰图”“remote gdb分析coredump”
- ByteSan 任务 / 扫描列表、各 ByteCloud 区域下 `/byteq/bytesan` 控制台 URL、Task / Run / Bug / Report / Build ID、Sanitizer 原始报告与构建 Git 元数据：`bytesan` / `bytedance-bytesan`
  - 例子：“按仓库筛选任务”“按 PSM 和仓库筛选扫描”“按 Task ID 拉全部缺陷”“按 Bug ID 找报告和构建”“读取 ASAN 原始报告”“按 Build ID 查主仓库与依赖仓库 commit”
  - URL 先按 path / query 区分 Task、Run、Bug，再将完整链接传给对应命令的 `--url`；host 决定 site。关联 ID 的后续查询沿用结果中的 `data.site`。
- Libra / DataTester A/B 实验、指标组、指标组模版：`libra`
  - 例子：“看这个实验详情”“查这个 flight 的报告”“按标签列出某个 App 下的指标组”“根据 template 页面 URL 查看 metric-group template”
- Pearl 平台 Nova 应用/来源/国家发现、任务查询与承接 schema 查询（**只读**，无写操作）：`pearl nova application|source|country` 与 `pearl nova application schema` 与 `pearl nova source task`；DMP 人群包规模与占该国比例：`pearl dmp set get`（加 `--refresh` 重算并带数据分区日期）；SSAP Case Center 风控 case 检索与 appeal/violation 详情（**只读**）：`pearl case list|get`
  - 例子：“列出 US 的 Nova source”“按 application_key 找 source”“查看 Nova 任务详情”“按 schema_id 查承接落地页配置”“查某个达人的申诉 case”“按 case id 看申诉与处罚详情”（写操作如编辑/审核提交/case 处置不支持，需人工在 console 操作）
- Dolphin 动态决策平台查询、settings、写操作和发布都使用 `dolphin` / `bytedance-dolphin`；已建模操作优先语义命令，未显式建模的 OpenAPI 接口才使用内建 `bytedcli dolphin api execute ...`
  - 例子：“按 Dolphin 控制台 URL 修改规则组配置”“发布 Dolphin 规则”“维护 Dolphin testcase”
- Tesla RM 自动化测试平台：测试任务触发/查询/run 等待、列表、失败归因，测试计划 CRUD 与统计：`tesla`
  - 例子：“按计划 507863 触发一个 Tesla 任务并等结果”“查这个 Tesla 任务的状态和失败用例”“列出这个计划最近 7 天的任务”“看这个测试计划的执行统计”
- TestIDE / SmartQ 小 Q UI 自动化：读取用例集与自动化步骤，创建计划/任务，等待终态并下载报告或录像证据：`smartq`
  - 例子：“读取这个 TestIDE 用例集的自动化步骤和引用片段”“创建一个小 Q UI 测试任务”“查询 TestIDE 任务结果”
- Panama 平台 RPC 工具执行：`panama rpc execute`
  - 例子：“用 Panama 调一个 RPC 方法”“把这段 RPC body 通过 Panama 工具执行”“查看 Panama assertion 结果”
- OneService 查询：`oneservice`
  - 例子：“查这个 query 的 meta”“查这个 query version detail”“取当前 ONLINE 版本 SQL”
- Life 生活服务生财有数平台：`life live-screen`
  - 例子：“根据直播间 ID 看直播数据工作台核心指标”“按主播昵称 / 主播 ID / 抖音号 / 直播间 ID 获取用户信息”
- Live Trace / 消息链路排查：`live trace`
  - 例子：“发起 ack_trace”“查这个 task_id 的明细”“解析这段 pb_payload”
- ByteIO 埋点、需求、点位、测试用例、广告元数据查询，以及数据加工转换规则的查询 / 修改 / 测试 / 上线申请：`bytedance-byteio`
  - 例子：“查这个 app_id 下某个 event_name 是否存在”“校验这个埋点参数”“查询 ByteIO 需求详情 / BTM 点位 / 测试用例 / 广告 tag”
- DECC / OG Gateway 区域打标核验、工单查询/撤回/评论，以及跨区域数据交换：`decc` / `bytedance-decc`
  - 例子：“核验这个 USTTP/EUTTP API 的字段打标”“查 pending DECC ticket”“撤回指定版本工单”“看 ticket reject comment”“创建 DECC channel”“注册 DECC data”
  - DECC 控制面固定使用 `--site i18n-tt`；USTTP/EUTTP 是业务 region，不能改成 `--site us-ttp` / `eu-ttp`
- 安全与权限：`dkms`、`kmsv2`、`iam`、`tsp`、`waf`
  - 例子："查 data key 权限""给 key 加 ACL""搜一个员工""获取凭据值""查 WAF 防护规则""看 CC 防护配置""查 IP 黑白名单"
  - `waf`：WAF（Web Application Firewall）相关操作的统一入口。涉及 WAF、Web 应用防火墙、应用层防护、CC 防护、IP 黑白名单、防护规则、防护策略等场景时使用 `waf` 命令，具体支持的子命令和参数见 `waf --help` 或 [WAF Domain Guide](references/subskills/bytedance-waf/GUIDE.md)。
- 混沌工程、故障注入、演练方案创建：`chaos`
  - 例子："创建一个演练方案，为 xxx 注入 cpu 受限 80% 的故障，持续时间 300 s，使用新建隔离环境的策略，选择最新的 rhino 流量"
- Dataleap Pontus 成本与资产管理，如：Hive表存储大小与增长量查询：`pontus` / `bytedance-pontus`
  - 例子："查询某个 Hive 表的存储大小与增长量"
- 将 bytedcli 暴露给宿主、升级本地安装或管理受信任 CLI 插件：`mcp`、`self`
- 架构图、流程图、ER 图、时序图、甘特图、思维导图或图表模板：`mindai chart`（只交付 SVG；飞书文档和画板操作走对应 Lark 能力）
  - 例子：“画一个订单履约架构图”“继续修改这张流程图”“用模板生成漏斗图”

<!-- bytedcli: generated-domain-routes:start -->
<!-- prettier-ignore -->
- Aiden：使用 Aiden 执行或管理任务、查看运行和产物、配置 Agent，或根据 Aiden task / run 链接跟进已有任务时，使用 `bytedcli aiden`。普通开发请求或未确定平台的任务不触发；D2C 设计转代码与 DeepWiki 知识检索分别走 `bytedance-d2c`、`bytedance-deepwiki`: [bytedance-aiden](references/subskills/bytedance-aiden/GUIDE.md)
- 明确要求使用或排查 `bytedcli anniex` / `anniex` CLI，或查询其命令参数与 JSBridge / Event 研发流程: [bytedance-anniex](references/subskills/bytedance-anniex/GUIDE.md)
- 内部方舟控制台 `ark.bytedance.net`（方舟 / ARK console）只读查询：在指定 ARK 账号下列出 project、foundation-model、inference endpoint（`ep-*`）与脱敏 API Key；不适用于火山公有云 volcengine.com 控制台: [bytedance-ark](references/subskills/bytedance-ark/GUIDE.md)
- BABI 账号、火山账号、成本、收入、利润、BABI-Finops 优化建议、容量利用率、商品信息、计费项调价信息及平台监控（商品监控报警、APP 监控报警、服务树成本监控报警）: [bytedance-babi](references/subskills/bytedance-babi/GUIDE.md)
- BBQ / PDI-Seed 接口自动化测试平台的用例、模版、测试计划、执行报告和相关资源；当前 Agent 可用 `bbq-cli` Skill 时优先使用 `bbq-cli` Skill，否则使用 `bytedcli bbq`: [bytedance-bbq](references/subskills/bytedance-bbq/GUIDE.md)
- ByteDoc/MongoDB 业务代码 review、提交前检查与 MR diff 审查：发现业务查询后确认目标并请求只读查库授权，结合线上索引、可用 schema 和版本判断风险: [bytedance-bytedoc](references/subskills/bytedance-bytedoc/GUIDE.md)
- ByteLink、liveim、unicast、multicast、broadcast，查询租户/方法/重保房间/WRDS/WSS、app/namespace/uplink 平台元数据，或诊断设备连接、房间消息发送/推送、消息 ACK、组播订阅快照与 liveim log ID Trace 反查: [bytedance-bytelink](references/subskills/bytedance-bytelink/GUIDE.md)
- OpsData、运维数据资产平台、合适数据源、数据集 Schema、服务记录或运维知识检索；先发现实时目录与契约，再按数据集支持能力使用 GraphQL、RAG 或 OpenViking 只读查询: [bytedance-bytestable-opsdata](references/subskills/bytedance-bytestable-opsdata/GUIDE.md)
- CDN 域名配置、带宽/流量/QPS/状态码指标、文件上传下载与团队空间权限：`cdn`；指标使用 `cdn metric query`，按 `--site cn|i18n-tt|us-ttp` 查询: [bytedance-cdn](references/subskills/bytedance-cdn/GUIDE.md)
- CodeVision、跨仓库代码证据、授权仓库发现、CodeGraph 查询、源码文件定位与有界读取: [bytedance-codevision](references/subskills/bytedance-codevision/GUIDE.md)
- 本机豆包桌面端、个人版 / 豆包工作、当前账号状态、已渲染会话/消息及确认后纯文本发送；实验性回环 CDP 入口，不复用企业 SSO、不允许匿名降级发送、不自动改权限: [bytedance-doubao](references/subskills/bytedance-doubao/GUIDE.md)
- ByteDTS 原生同步任务 ID、`/bytedts/datasync/detail` 链接、`DescribeTaskInfo`、任务状态或完整源表到目标表映射查询；TT-DTS / DES-MQ 通道改用 `bytedance-tt-dts`，Dorado DTS 元数据改用 `bytedance-dorado`: [bytedance-dts](references/subskills/bytedance-dts/GUIDE.md)
- Guardian 或星环应急管理查询，以及带预演、确认令牌、预算和读回校验的单目标写入；小R仅在与事件、事故、应急、报警、TODO、策略、配置、统计、订阅、审计、空间或业务意图共同出现时进入，裸小R先澄清，聊天/机器人/转发不进入；RCA/Goalkeeper、AI诊断和未核实的事件生命周期写入不支持: [bytedance-guardian](references/subskills/bytedance-guardian/GUIDE.md)
- Hive / DataLeap 数据资产与 Hive Copilot：查询 Hive 表、schema、分区、血缘、DataLeap/Coral 资产，或当用户给出 Spark `application_*` 并要求诊断失败/慢因、比较 Spark 作业、分析数据倾斜/Shuffle/资源配置、明确要求 Hive Copilot / Hive Agent 与 CN Spark/Hive 知识问答时使用；原始 Spark UI 取证走 `bytedance-megatron`: [bytedance-hive](references/subskills/bytedance-hive/GUIDE.md)
- Luban OHPM/Harmony 包搜索、版本前缀查询、制品详情与 HAR 下载，以及 NPM、Maven、PyPI、BPT 包查询和发布: [bytedance-luban](references/subskills/bytedance-luban/GUIDE.md)
- Merlin 工作台 SSH 公钥列表、上传与删除使用 `merlin cpu-devbox ssh-keys get/upload/delete`；ROW 带 `--site i18n-tt`。上传／删除支持 `--key-file`，默认预览，`--yes` 才提交: [bytedance-merlin](references/subskills/bytedance-merlin/GUIDE.md)
- Mira 对话、续聊、飞书登录与会话历史（`mira`）: [bytedance-mira](references/subskills/bytedance-mira/GUIDE.md)
- MusicFlow 工作流、定义、批次、算子和执行实例只读查询，以及单实例重试，使用 `musicflow`: [bytedance-musicflow](references/subskills/bytedance-musicflow/GUIDE.md)
- Netlink、调流工单、单 IDC QPS 阶跃、流量重分配、Observe 日志与 OLAP 或 namespace/dataset 发现: [bytedance-netlink](references/subskills/bytedance-netlink/GUIDE.md)
- Obric 内部研发工具集中的 OBRIC CM ROM 构建、构建产物、自动挑单、Coverity、Jenkins、OpenGrok、Ocean Assistant 管理后台、Ocean Review 和 Quality Data 能力；用户提到 ROM 构建、构建产物、自动挑单、versionDiff、Coverity issue/CID、Jenkins 构建日志、OpenGrok、OAssistant Zeus、Ocean Review、Gerrit change、Quality Data 或质量反馈时使用。OBRIC PDM App Version 使用独立的 bytedance-obric-pdm skill: [bytedance-obric](references/subskills/bytedance-obric/GUIDE.md)
- 当用户需要列出 Nova 应用/来源/国家、读取 source/task/承接 schema、查询 DMP 人群包规模、搜索 creator appeal 等 risk-control case、查看操作日志、发现 Odin endpoint、读取 SOP 定义/变量/缓存/checkpoint 报告，或预览并按本地写 gate 执行明确要求的 Odin mutation 时使用；Nova 与 Case mutation 不可用，Odin mutation 默认 dry-run，live 提交需要人工开启本机 gate 并加 --yes: [bytedance-pearl](references/subskills/bytedance-pearl/GUIDE.md)
- Quantum 平台、Polestar link-debug、Link Skills MCP、按 UID 和时间窗创建链路调试任务、获取实时事件列表或事件详情: [bytedance-quantum](references/subskills/bytedance-quantum/GUIDE.md)
- CN Ray Dashboard 的 Jobs、Serve、Cluster/Nodes、Actors、Streaming、指标与日志查询；OpenStudio 项目 Ray 服务列表、详情、配置编辑、重启、停止和回滚使用 `ray service`，须先展示变更与高风险提示，人工在聊天中明确确认后 Agent 可代为执行；不用于 TCE 发布: [bytedance-ray](references/subskills/bytedance-ray/GUIDE.md)
- SmartQ / TestIDE 小 Q UI 自动化：空间与应用配置、用例节点和编辑历史、片段、webdiff 断言、用例生成、模板对话、BITS / ByCaps 计划触发、任务结果和报告录像: [bytedance-smartq](references/subskills/bytedance-smartq/GUIDE.md)
- Super Relay trace/session 调查、model bad case、重复输出或 tool_call/function-call 协议残留、Payload Response Body 精确检索、完整 Trace 下载、trace feedback 查询与预览/确认提交: [bytedance-super-relay](references/subskills/bytedance-super-relay/GUIDE.md)
<!-- bytedcli: generated-domain-routes:end -->

## Common inputs

- 如果用户给的是 MR / issue / 文档 / 配置 / 告警控制台 URL，优先直接用 URL，不要先手拆 ID。
- 如果用户只给出独立的 Footprint 页面或 concrete `mljob-log-proxy` 文件 URL，且没有 Primus application、History、role、pod 或 Forge/Reckon Primus 上下文，进入 Log 领域并使用 `bytedcli log footprint ...`；当前 CLI 没有顶层 `bytedcli footprint`。一旦任务带有上述 Primus 上下文，整个 application → role → pod → concrete file → content 链路都归 `bytedance-primus`，持续使用 `bytedcli primus log list/get`，不要把发现出的 concrete URL 再交给 Log skill。Primus/History 解析出的 mljob landing URL 也不是具体文件；先看 `primus log get` 的 `logResolutionStatus`，`landing-only` 表示日志后端未暴露 concrete file。
- `godel instance get` 只接受精确 `--cluster --namespace --name`，不能直接接收 Primus/Forge URL 或 Fed task selector。只有相邻平台上下文时，先用对应 `primus` / `forge` workflow 获取精确坐标，再单独调用 Godel；坐标不完整时不要猜测。如果用户给的是 Godel stream-applications / Flink Web URL，则使用 `flink`；两者只是共享 Godel 名称，诊断对象不同。
- 如果用户给出 `warlock.byteintl.net/share?key=...` 或 Warlock share key，使用 `warlock share get` 读取规范化的 response body 和 headers，不要走通用页面 HTML 读取。
- 如果任务是 Meego，优先直接使用工作项 / 视图 URL；很多命令支持 `--url` 自动回填 `project_key`、`work_item_id`、`view_id` 等标识。
- 如果用户给的是仓库目录上下文，优先让 Codebase 自动从当前 `origin` 推断仓库；当前支持 `code.byted.org` 和 `code-tx.byted.org` remote。如果推断失败，CLI 会继续说明是非 Git 仓库、缺少 `origin`、host 不支持，还是 remote 无法解析。
- 如果任务跨站点，先确认 `--site` 或 `BYTEDCLI_CLOUD_SITE`。
- DECC API 打标优先使用 `decc gateway tagging get --region <US|EU>`，工单优先使用 `decc ticket list/get/cancel` 和 `decc ticket comment list`，不要先打开浏览器。DECC 鉴权固定使用 `--site i18n-tt`；若报 `DECC_GATEWAY_REGION_MISMATCH` 或 `DECC_GATEWAY_REGION_AMBIGUOUS`，停止完成性判断，不能猜 assurance path、改用另一 region 或 Chrome 结果替代。撤回先默认 dry-run；若用户原始请求未明确授权真实撤回，必须展示结果并等待用户肯定答复，之后才能对同一 selector/version/reason 加 `--yes`，不得用 agent 自己的校验代替用户授权。
- 如果命令失败，优先看 `error.hint`、`error.auth_command`，或参考排障说明。

## Domain guides

任务已经收敛到某个具体领域时，继续看对应领域说明：

- Codebase: [references/subskills/bytedance-codebase/GUIDE.md](references/subskills/bytedance-codebase/GUIDE.md)
- AppInfo: [references/subskills/bytedance-app-info/GUIDE.md](references/subskills/bytedance-app-info/GUIDE.md)
- ByteQuota: [references/subskills/bytedance-quota/GUIDE.md](references/subskills/bytedance-quota/GUIDE.md)
- TikTok LIVE compliance data tickets: [references/subskills/bytedance-ttlive-compliance-ace/GUIDE.md](references/subskills/bytedance-ttlive-compliance-ace/GUIDE.md)
- BMA managed-agent platform: [references/subskills/bytedance-bma/GUIDE.md](references/subskills/bytedance-bma/GUIDE.md)
- Dora: [references/subskills/bytedance-dora/GUIDE.md](references/subskills/bytedance-dora/GUIDE.md)
- BITS / 任意门: [references/subskills/bytedance-bits/GUIDE.md](references/subskills/bytedance-bits/GUIDE.md)
- Bytediff: [references/subskills/bytedance-bytediff/GUIDE.md](references/subskills/bytedance-bytediff/GUIDE.md)
- Jinshu: [references/subskills/bytedance-jinshu/GUIDE.md](references/subskills/bytedance-jinshu/GUIDE.md)
- ByteCanteen: [references/subskills/bytedance-canteen/GUIDE.md](references/subskills/bytedance-canteen/GUIDE.md)
- Guardian: [references/subskills/bytedance-guardian/GUIDE.md](references/subskills/bytedance-guardian/GUIDE.md)
- ByteHealth: [references/subskills/bytedance-health/GUIDE.md](references/subskills/bytedance-health/GUIDE.md)
- Lark Oncall: [references/subskills/bytedance-lark-oncall/GUIDE.md](references/subskills/bytedance-lark-oncall/GUIDE.md)
- Cloud Docs: [references/subskills/bytedance-cloud-docs/GUIDE.md](references/subskills/bytedance-cloud-docs/GUIDE.md)
- ByteCloud Oncall: [references/subskills/bytedance-oncall/GUIDE.md](references/subskills/bytedance-oncall/GUIDE.md)
- ByteGate: [references/subskills/bytedance-bytegate/GUIDE.md](references/subskills/bytedance-bytegate/GUIDE.md)
- ByteCloud Supabase: [references/subskills/bytedance-supabase-companion/GUIDE.md](references/subskills/bytedance-supabase-companion/GUIDE.md)
- ByteCloud PostgreSQL Companion: [references/subskills/bytedance-postgresql-companion/GUIDE.md](references/subskills/bytedance-postgresql-companion/GUIDE.md)
- UCenter: [references/subskills/bytedance-ucenter/GUIDE.md](references/subskills/bytedance-ucenter/GUIDE.md)
- VOC: [references/subskills/bytedance-voc/GUIDE.md](references/subskills/bytedance-voc/GUIDE.md)
- Procurement: [references/subskills/bytedance-procurement/GUIDE.md](references/subskills/bytedance-procurement/GUIDE.md)
- Vimo: [references/subskills/bytedance-vimo/GUIDE.md](references/subskills/bytedance-vimo/GUIDE.md)
- WAF: [references/subskills/bytedance-waf/GUIDE.md](references/subskills/bytedance-waf/GUIDE.md)
- WJ / ByteSurvey: [references/subskills/bytedance-wj/GUIDE.md](references/subskills/bytedance-wj/GUIDE.md)
- IconBox: [references/subskills/bytedance-iconbox/GUIDE.md](references/subskills/bytedance-iconbox/GUIDE.md)
- TOP: [references/subskills/bytedance-top/GUIDE.md](references/subskills/bytedance-top/GUIDE.md)
- Warlock: [references/subskills/bytedance-warlock/GUIDE.md](references/subskills/bytedance-warlock/GUIDE.md)
- Logifier: [references/subskills/bytedance-logifier/GUIDE.md](references/subskills/bytedance-logifier/GUIDE.md)
- FundEye: [references/subskills/bytedance-fundeye/GUIDE.md](references/subskills/bytedance-fundeye/GUIDE.md)
- Starling: [references/subskills/bytedance-starling/GUIDE.md](references/subskills/bytedance-starling/GUIDE.md)
- Luban: [references/subskills/bytedance-luban/GUIDE.md](references/subskills/bytedance-luban/GUIDE.md)
- Lynx: [references/subskills/bytedance-lynx/GUIDE.md](references/subskills/bytedance-lynx/GUIDE.md)
- SAR Creator Arcade: [references/subskills/bytedance-sar/GUIDE.md](references/subskills/bytedance-sar/GUIDE.md)
- Argus Hybrid: [references/subskills/bytedance-argus/GUIDE.md](references/subskills/bytedance-argus/GUIDE.md)
- TCC: [references/subskills/bytedance-tcc/GUIDE.md](references/subskills/bytedance-tcc/GUIDE.md)
- TSP: [references/subskills/bytedance-tsp/GUIDE.md](references/subskills/bytedance-tsp/GUIDE.md)
- Chronos: [references/subskills/bytedance-chronos/GUIDE.md](references/subskills/bytedance-chronos/GUIDE.md)
- BES: [references/subskills/bytedance-bes/GUIDE.md](references/subskills/bytedance-bes/GUIDE.md)
- WCC / QCSS: [references/subskills/bytedance-bytestable-wcc/GUIDE.md](references/subskills/bytedance-bytestable-wcc/GUIDE.md)
- TCE: [references/subskills/bytedance-tce/GUIDE.md](references/subskills/bytedance-tce/GUIDE.md)
- EOpsX（电商运维：meta/alarm/event/fatal/limit/voc/sla/bcp/risk/dev）: [references/subskills/bytedance-eopsx/GUIDE.md](references/subskills/bytedance-eopsx/GUIDE.md)
- ENV / ByteCopy: [references/subskills/bytedance-env/GUIDE.md](references/subskills/bytedance-env/GUIDE.md)
- Ent Platform / UDS Storage IAC: [references/subskills/bytedance-ent/GUIDE.md](references/subskills/bytedance-ent/GUIDE.md)
- TrafficRoute: [references/subskills/bytedance-trafficroute/GUIDE.md](references/subskills/bytedance-trafficroute/GUIDE.md)
- ByteSD: [references/subskills/bytedance-sd/GUIDE.md](references/subskills/bytedance-sd/GUIDE.md)
- GPCP (SYS-OnePlatform; read-only Aegis issues, SDP, MSC queries, and guarded governance registration): [references/subskills/bytedance-gpcp/GUIDE.md](references/subskills/bytedance-gpcp/GUIDE.md)
- TQS: [references/subskills/bytedance-tqs/GUIDE.md](references/subskills/bytedance-tqs/GUIDE.md)
- Kross: [references/subskills/bytedance-kross/GUIDE.md](references/subskills/bytedance-kross/GUIDE.md)
- Bytetree: [references/subskills/bytedance-bytetree/GUIDE.md](references/subskills/bytedance-bytetree/GUIDE.md)
- BMT: [references/subskills/bytedance-bmt/GUIDE.md](references/subskills/bytedance-bmt/GUIDE.md)
- Move Engine: [references/subskills/bytedance-move-engine/GUIDE.md](references/subskills/bytedance-move-engine/GUIDE.md)
- Watchdog Diag: [references/subskills/bytedance-watchdog/GUIDE.md](references/subskills/bytedance-watchdog/GUIDE.md)
- ByteGraph: [references/subskills/bytedance-bytegraph/GUIDE.md](references/subskills/bytedance-bytegraph/GUIDE.md)
- Model Dispatcher: [references/subskills/bytedance-model-dispatcher/GUIDE.md](references/subskills/bytedance-model-dispatcher/GUIDE.md)
- ByteMesh: [references/subskills/bytedance-bytemesh/GUIDE.md](references/subskills/bytedance-bytemesh/GUIDE.md)
- Vertex: [references/subskills/bytedance-vertex/GUIDE.md](references/subskills/bytedance-vertex/GUIDE.md)
- ByteKV: [references/subskills/bytedance-bytekv/GUIDE.md](references/subskills/bytedance-bytekv/GUIDE.md)
- TokaDB: [references/subskills/bytedance-tokadb/GUIDE.md](references/subskills/bytedance-tokadb/GUIDE.md)
- RDS: [references/subskills/bytedance-rds/GUIDE.md](references/subskills/bytedance-rds/GUIDE.md)
- RDS PostgreSQL: [references/subskills/bytedance-rds-pg/GUIDE.md](references/subskills/bytedance-rds-pg/GUIDE.md)
- AIDAP Serverless PostgreSQL: [references/subskills/bytedance-aidap/GUIDE.md](references/subskills/bytedance-aidap/GUIDE.md)
- DB (bytedcli db): [references/subskills/bytedance-db/GUIDE.md](references/subskills/bytedance-db/GUIDE.md)
- ByteHouse: [references/subskills/bytedance-bytehouse/GUIDE.md](references/subskills/bytedance-bytehouse/GUIDE.md)
- CIS Master Data: [references/subskills/bytedance-cis-master-data/GUIDE.md](references/subskills/bytedance-cis-master-data/GUIDE.md)
- Doris Ops: [references/subskills/bytedance-doris-ops/GUIDE.md](references/subskills/bytedance-doris-ops/GUIDE.md)
- TEA: [references/subskills/bytedance-tea/GUIDE.md](references/subskills/bytedance-tea/GUIDE.md)
- NVQoS: [references/subskills/bytedance-nvqos/GUIDE.md](references/subskills/bytedance-nvqos/GUIDE.md)
- ByteFlow: [references/subskills/bytedance-byteflow/GUIDE.md](references/subskills/bytedance-byteflow/GUIDE.md)
- LG Admin: [references/subskills/bytedance-lg-admin/GUIDE.md](references/subskills/bytedance-lg-admin/GUIDE.md)
- Blade: [references/subskills/bytedance-blade/GUIDE.md](references/subskills/bytedance-blade/GUIDE.md)
- Magnus: [references/subskills/bytedance-magnus/GUIDE.md](references/subskills/bytedance-magnus/GUIDE.md)
- OneService: [references/subskills/bytedance-oneservice/GUIDE.md](references/subskills/bytedance-oneservice/GUIDE.md)
- Merlin: [references/subskills/bytedance-merlin/GUIDE.md](references/subskills/bytedance-merlin/GUIDE.md)
- MOSS: [references/subskills/bytedance-moss/GUIDE.md](references/subskills/bytedance-moss/GUIDE.md)
- Pearl: [references/subskills/bytedance-pearl/GUIDE.md](references/subskills/bytedance-pearl/GUIDE.md)
- PIPO: [references/subskills/bytedance-pipo/GUIDE.md](references/subskills/bytedance-pipo/GUIDE.md)
- Helix: [references/subskills/bytedance-helix/GUIDE.md](references/subskills/bytedance-helix/GUIDE.md)
- Holmes: [references/subskills/bytedance-holmes/GUIDE.md](references/subskills/bytedance-holmes/GUIDE.md)
- Byterec: [references/subskills/bytedance-byterec/GUIDE.md](references/subskills/bytedance-byterec/GUIDE.md)
- AI Dev Pro AFS: [references/subskills/bytedance-ai-dev-pro/GUIDE.md](references/subskills/bytedance-ai-dev-pro/GUIDE.md)
- Recall Center: [references/subskills/bytedance-recall-center/GUIDE.md](references/subskills/bytedance-recall-center/GUIDE.md)
- AI Dev Pro AFS: [references/subskills/bytedance-ai-dev-pro/GUIDE.md](references/subskills/bytedance-ai-dev-pro/GUIDE.md)
- TMates: [references/subskills/bytedance-tmates/GUIDE.md](references/subskills/bytedance-tmates/GUIDE.md)
- Fornax: [references/subskills/bytedance-fornax/GUIDE.md](references/subskills/bytedance-fornax/GUIDE.md)
- LabelGPT: [references/subskills/bytedance-labelgpt/GUIDE.md](references/subskills/bytedance-labelgpt/GUIDE.md)
- Meego: [references/subskills/bytedance-meego/GUIDE.md](references/subskills/bytedance-meego/GUIDE.md)
- Libra: [references/subskills/bytedance-libra/references/libra.md](references/subskills/bytedance-libra/references/libra.md)
- Ratel: [references/subskills/bytedance-ratel/references/ratel.md](references/subskills/bytedance-ratel/references/ratel.md)
- Tesla: [references/subskills/bytedance-tesla/GUIDE.md](references/subskills/bytedance-tesla/GUIDE.md)
- SmartQ / TestIDE: [references/subskills/bytedance-smartq/GUIDE.md](references/subskills/bytedance-smartq/GUIDE.md)
- Panama: [references/subskills/bytedance-panama/references/panama.md](references/subskills/bytedance-panama/references/panama.md)
- FTF: [references/subskills/bytedance-ftf/GUIDE.md](references/subskills/bytedance-ftf/GUIDE.md)
- Nario: [references/subskills/bytedance-nario/GUIDE.md](references/subskills/bytedance-nario/GUIDE.md)
- FaaS: [references/subskills/bytedance-faas/GUIDE.md](references/subskills/bytedance-faas/GUIDE.md)
- TAE / AI PaaS: [references/subskills/bytedance-tae/GUIDE.md](references/subskills/bytedance-tae/GUIDE.md)
- Log / Footprint: [references/subskills/bytedance-log/GUIDE.md](references/subskills/bytedance-log/GUIDE.md)
- Argos Agent（服务端可观测诊断与 Dashboard/Folder 创建、修改、导入；诊断仅当 log/apm 能力不够或用户明确要求 SRE Agent 时使用）: [references/subskills/bytedance-argos/GUIDE.md](references/subskills/bytedance-argos/GUIDE.md)
- Primus: [references/subskills/bytedance-primus/GUIDE.md](references/subskills/bytedance-primus/GUIDE.md)
- Godel Explainer: [references/subskills/bytedance-godel/GUIDE.md](references/subskills/bytedance-godel/GUIDE.md)
- Archer: [references/subskills/bytedance-archer/GUIDE.md](references/subskills/bytedance-archer/GUIDE.md)
- ByteDog: [references/subskills/bytedance-bytedog/GUIDE.md](references/subskills/bytedance-bytedog/GUIDE.md)
- ByteSan: [references/subskills/bytedance-bytesan/GUIDE.md](references/subskills/bytedance-bytesan/GUIDE.md)
- Kelemetry: [references/subskills/bytedance-kelemetry/GUIDE.md](references/subskills/bytedance-kelemetry/GUIDE.md)
- Slardar: [references/subskills/bytedance-slardar/GUIDE.md](references/subskills/bytedance-slardar/GUIDE.md)
- Vela: [references/subskills/bytedance-vela/GUIDE.md](references/subskills/bytedance-vela/GUIDE.md)
- Devflow: [references/subskills/bytedance-devflow/GUIDE.md](references/subskills/bytedance-devflow/GUIDE.md)
- Academy: [references/subskills/bytedance-academy/GUIDE.md](references/subskills/bytedance-academy/GUIDE.md)
- Safe: [references/subskills/bytedance-safe/GUIDE.md](references/subskills/bytedance-safe/GUIDE.md)
- Douyin AI Trace Span: [references/subskills/bytedance-douyin-ai-trace-span/GUIDE.md](references/subskills/bytedance-douyin-ai-trace-span/GUIDE.md)
- bytedance-d2c: [references/subskills/bytedance-d2c/GUIDE.md](references/subskills/bytedance-d2c/GUIDE.md)
- Life: [references/subskills/bytedance-data-life-live/GUIDE.md](references/subskills/bytedance-data-life-live/GUIDE.md)
- Live Trace: [references/subskills/bytedance-live/GUIDE.md](references/subskills/bytedance-live/GUIDE.md)
- ByteIO: [references/subskills/bytedance-byteio/GUIDE.md](references/subskills/bytedance-byteio/GUIDE.md)
- Janus: [references/subskills/bytedance-janus/GUIDE.md](references/subskills/bytedance-janus/GUIDE.md)
- Janus Mini: [references/subskills/bytedance-janus-mini/GUIDE.md](references/subskills/bytedance-janus-mini/GUIDE.md)
- Search: [references/subskills/bytedance-insearch/GUIDE.md](references/subskills/bytedance-insearch/GUIDE.md)
- DevSpec: [references/subskills/bytedance-devspec/GUIDE.md](references/subskills/bytedance-devspec/GUIDE.md)；Go/JS 离线摘要见 [references/subskills/bytedance-devspec/references/core-language-digests.md](references/subskills/bytedance-devspec/references/core-language-digests.md)
- People: [references/subskills/bytedance-people/GUIDE.md](references/subskills/bytedance-people/GUIDE.md)
- Reimbursement: [references/subskills/bytedance-reimbursement/GUIDE.md](references/subskills/bytedance-reimbursement/GUIDE.md)
- MindAI Chart: [references/subskills/bytedance-mindai/GUIDE.md](references/subskills/bytedance-mindai/GUIDE.md)
- 其他领域路径索引: [references/subskills-index.md](references/subskills-index.md)

## References

- `references/command-surface.md`
- `references/invocation.md`
- `references/troubleshooting.md`
