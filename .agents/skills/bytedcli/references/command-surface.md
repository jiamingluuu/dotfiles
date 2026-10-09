# bytedcli Command Surface

用这个文件把用户任务映射到顶层命令域。它不是完整子命令手册；需要精确参数或最新子命令时，继续执行：

```bash
bytedcli <domain> --help
```

## 目录

- General utilities
- Code, release, and configuration
- Collaboration, docs, and AI knowledge
- Data, storage, and analytics
- Runtime, logs, and observability
- Quick routing by artifact

## General utilities

- `auth`: SSO 登录、登出、状态、用户信息、ByteCloud JWT、Codebase JWT。
- `mcp`: 用同一套 Commander 命令树启动 stdio MCP server。
- `self`: bytedcli 自管理能力；当前包含 `self update`（升级全局 npm / pnpm 安装）、`self skill`（安装、列出、更新、删除随 bytedcli 打包的 agent skills）、`self plugin`（受信任 CLI 插件管理）和 `self tracking`（匿名 CLI/agent 使用追踪管理）。自动升级可用全局参数 `--no-auto-upgrade` 或环境变量 `BYTEDCLI_NO_AUTO_UPGRADE=1` 关闭。`self skill` 默认操作项目级 `.agents/skills/`，`-g/--global` 操作 `~/.agents/skills/`；删除技能必须用 `self skill remove` 同步清理 lock，避免下次版本升级重新同步。`self tracking enable` 支持 `--agent all|claude|codex|coco`（默认 `all`）和 `--mode global|project`（默认 `global`）；hook 上报前会移除参数值、prompt、文件内容和真实路径，只保留命令结构、flag 名、状态、耗时和匿名 session / cwd。

## Code, release, and configuration

- `app-info`: AppInfo 应用元数据查询，支持按 App ID、应用 code、中文名、账号组、产品线与移动端包名搜索，以及单条或批量获取应用详情。
- `quota`: ByteQuota 存储配额查询与管理，覆盖配额元数据、配额项、操作、容量检查、申请/借用/分配/回收和 bypass；写操作默认预览，确认后才加 `--yes`。
- `codebase`: 仓库、创建仓库（默认 validate_only）、MR、Review、Issue、评论、文件、Check Runs、CI、Merge Queue、创建分支。
- `codecov`: 全量与增量覆盖率报告管理。增量已有报告查询使用 `codecov report incr get`，重新触发生成使用独立的 `codecov report incr rerun`（按 `--report-id` 或 `--psm` + `--branch` 定位，`--region cn|i18n` 显式选择 coverage 数据面）；`incr update` 仅做文件归因标记，不能代替 rerun。
- `bam`: PSM 列表/搜索、方法列表/详情、代码生成规则与生成任务、版本列表、IDL 更新。子组：`psm`/`method`/`codegen`/`version`/`idl`；旧的平铺命令保留为隐藏别名。
- `bytediff`: Bytediff diff task、traffic task、AB test、冒烟测试任务创建，task 列表/终止/重跑，AB 实验关联任务、report、字段 diff 结果与报表查询，PSM 配置查询/登记，测试场景（case）管理。创建类命令（除 `case create`/`smoke-task create` 支持显式 flag）只接受完整 JSON payload，先用 `--dry-run` 预览，再用 `--yes` 提交。区域由全局 `--site` 决定，默认 `cn`；跨区用 `bytedcli --site i18n-tt bytediff ...`（另有 `i18n-bd` / `eu-ttp` / `us-ttp`，Virginia 再加 `--vregion maliva`）。
- `bbq`: BBQ / PDI-Seed 接口自动化测试平台，覆盖用例、模版、计划、执行与报告；当前 Agent 可用 `bbq-cli` Skill 时优先使用 `bbq-cli` Skill，否则使用 `bytedcli bbq` 并读取 BBQ 领域指南。
- `agw`: AGW 产品列表/搜索/详情、服务搜索、环境注册、IDL 更新与发布。子组：`product`/`service`/`env`/`idl`；旧的平铺命令保留为隐藏别名。
- `argus`: Argus Hybrid 工单生成、前端应用查询与宿主选择辅助。当前覆盖 `argus hybrid app list`、`argus hybrid host search`、`argus hybrid gecko bind`、`argus hybrid jsb apply --platform h5|lynx`、`argus hybrid safe-url add`、`argus hybrid secure-method apply` 和 raw `ticket create`；用户身份来自 `auth userinfo`，默认只创建工单，不自动执行。`--hosts` 支持 label-only 模糊搜索，唯一 host 或 host group 命中会自动解析，多命中返回候选。JSB `--group` 默认不传；URL 输入可用完整 URL，query 会自动去掉；H5 secure 方法必须带频控、PRD 和 secure URL，Lynx secure 方法必须带频控和 PRD。
- `mango`: 芒果平台任务与接口录入管理。子组：`auth`/`space`/`app`/`module`/`task`；
- `academy`: Academy 广告特征开发与管理；当前覆盖 `source search`、`raw-feature-set group search`、`feature search`，支持按 source / owner / version / type / datasourceType 或 feature 相关筛选条件检索，并可通过全局 `--site` 或 `--base-url` 指向 TikTok ROW Academy 控制面。
- `bits`: develop 任务、lane、流水线、release workflow、RPC 调用，以及 Anywheredoor / 任意门代理抓包与 mock。任意门命令入口是 `bits anywhere`，不是顶层 `anywhere`。
- `eopsx`: EOpsX 电商运维平台；`eopsx guard` 覆盖 EPS go_guard source tree/source/permission/role/env 查询和受确认门保护的 CN→BOE full sync。
- `dora`: Dora 云真机 / 云手机设备操作。子组：`device`；支持查询公有设备和我的占用、查看设备详情、占用、预约申请、释放、续期，以及获取 ADB / BDC / Harmony HDC 远端调试地址。
- `bes`: BES 元信息修改工单；当前提供 `metadata update --config <json-object>`，内部固定使用 `workflow_config_id=1491`。
- `ent`: Ent Platform / UDS Storage IAC；`storage-iac submit-table` 从 `CREATE TABLE` DDL 录入 Entity 元信息并提交新表 workflow，`storage-iac create` 用于已有 RDS 表导入/迁移 Storage IAC entry 并检查字段描述覆盖率。
- `bpm`: BPM 工单查询、日志、评论、可执行操作、状态推进与取消。子组：`ticket`。
- `lg-admin`: LG Admin 平台命令。`maas` 子组提供 MaaS / Prifly / PilotBench 只读查询，覆盖 `meta get`、`bu list|get`、`model list|get`、`pilotbench list`、`pilotbench status get`、`pilotbench result get`；`torch` 子组提供 package/image 发版、serving 查询与 inspect。Torch 写操作默认 dry-run，真实提交需 `--yes`。ICM 发布历史、prod 最近发布、构建 commit、仓库查询走顶层 `icm`；repo/package 名中的 lagrange、torch、cpu、cuda、mlu 等词不能单独触发 `lg-admin`。
- `lego`: Lego 插件从编译到发布上线的全流程；覆盖插件注册、编译、版本/分支/commit 查询、发布流水线与发布域查询、发布工单创建/列表/详情、发布步骤详情与人工确认。子组：`plugin`/`pipeline`/`order`/`scope`。
- `test-plan`: Bits 测试计划用例获取，脑图解析并导出 Markdown。
- `bitsai`: 研发知识、研发资产、TCE/TCC/FaaS/Goofy 等工程问答。
- `panama`: Panama 平台 RPC 工具执行；`panama rpc execute` 使用 ByteCloud JWT，`--env` 默认 `prod`，`--idc` 支持 `TTP|TTP2|GCP|NO1A|USEAST2B`，RPC 方法请求体通过 `--body` 或 `--body-file` 传入。
- `scm`: 仓库列表/搜索/创建/构建/构建日志/构建诊断、版本列表。构建排障入口为 `scm repo diagnose`；子组：`repo`（含 `repo version`）；旧的平铺命令保留为隐藏别名。
- `luban`: Luban npm 包查询、PyPI 制品发布、BPT 制品仓库与版本管理；`search` 支持按 `--npm` 查询 Bytedance 或 TTP Luban 里的 bnpm 包记录，并可选传 `-v/--package-version` 做版本前缀过滤；`pypi` 覆盖仓库查询、版本列表/详情查询和版本发布，发布支持 `--dry-run`、重复成功版本检测、`--yes` 确认、默认轮询和 `--no-wait`；`bpt` 覆盖 BPT 仓库列表/详情、分支列表、commit 列表、版本列表/详情查询和版本发布，发布支持 `--dry-run`、重复成功版本检测、`--yes` 确认、默认立即返回和显式 `--wait`。
- `lynx`: Lynx 开发、DevTool/CDP 调试、Sandbox、trace、Recorder、heap snapshot、实时全局内存与 LynxExample app 能力。非 LynxExample 任务先通过 `lynx skills list` 查看当前说明，再加载最具体的返回项；完整命令树以 `lynx --help` 为准。
- `manta`: Manta 数据探查、表监控规则查询、报警记录查询与两表对比平台；当前覆盖 `yarn-queues`（列出用户可用的 YARN 队列）、`monitor list`（按表/项目/状态/类型查询监控规则）、`monitor result list`（按业务日期范围/规则 ID/我的结果/是否报警查询 Hive 模板和自定义 SQL 报警结果）、`alarm-record list`（按报警时间范围、项目、状态、是否我的报警、是否夜间报警查询报警记录详情）、`profile rule create`（创建数据探查任务）、`comparison job create`（创建两表数据对比任务）和 `comparison sql create`（基于 SQL 的数据比对，自动处理 map/array 字段）；支持 `--region`（cn/sg/va/eu/mycis，默认 cn）；监控查询参数：`--table-name-query`、`--project-id`（可重复，必填）、`--mine`、`--triggered-only`、`--monitor-state`、`--monitor-type`（可重复）、`--limit`、`--offset`；报警结果参数：`--mode`（template/custom/all）、`--business-date-start` + `--business-date-end`（范围边界，需成对传入）、`--rule-id`、`--mine`、`--only-alarm`、`--project-id`（可重复，必填）、`--page`、`--page-size`；报警记录参数：`--project-id`（可重复，必填）、`--alarm-time-start` + `--alarm-time-end`（范围边界，需成对传入）、`--status`（all/unresponded/responding/processed）、`--mine`、`--night-alarm`、`--page`、`--page-size`；探查参数：`--db-name`、`--tb-name`、`--partitions`、`--columns`（省略自动探查全部字段），YARN 队列自动选取；对比参数：`--db-name-old/new`、`--tb-name-old/new`、`--partition-old/new`、`--primary-keys`（JOIN 匹配行，`;` 分隔）、`--comparison-columns`（对比字段，`;` 分隔），YARN 队列自动选取；SQL 比对参数：`--source-table`/`--target-table`（`db.table` 格式）、`--source-filter`/`--target-filter`、`--join-keys`（逗号分隔）、`--map-keys`（map 字段展开 key）、`--dry-run`（仅预览 SQL），YARN 队列自动选取；鉴权由 bytedcli 自动完成（ByteCloud SSO JWT 换取 Dataleap JWT，写入 `x-dataleap-jwt-token`，无需浏览器/cookie），只需先完成对应站点 SSO 登录：cn/sglark 走 `cn` 站点、sg/va/eu 走 `i18n-tt` 站点、mycis/jplark/uspipo 走 `i18n-bd` 站点。
- `coral`: Coral 元数据平台；覆盖 `ai-generate`（触发 AI 生成资产使用说明文档，`--table-name`、`--operator` 必填，资产全限定名根据表名与区域 cid 自动拼接，`--region` 支持 cn/sg/gcp/va/mycis、默认 sg，`--generate-type` 默认 ASSET_INSTRUCTION）、Hive 元数据查询、实体搜索，以及 `permission apply` / `permission answer` / `permission create` / `permission withdraw` 申请、补充问卷、提交或撤回 Hive 表/列权限；申请权限使用 `--db-name`、`--table-name`、`--auth-object`，列级权限用可重复/逗号分隔的 `--column` 指定，并用枚举参数限制 `--permission`（read/write）、`--auth-type`（person/psm）、`--requirement-type`（data-analysis/index-calculation）和 `--region`（cn/sg/gcp/va），必要时可用高级参数 `--cluster` 覆盖 Coral 权限 group；若 apply 返回 draft/questions，用 `permission answer --draft-file ... --question-id ... --answer ...` 填写，再用 `permission create --draft-file ...` 提交；撤回权限使用 `--id` 和 `--region`，需要同 group 覆盖时可带 `--cluster`；鉴权优先使用 Session Cookie，也支持 JWT 自动 fallback。
- `overpass`: IDL 同步、代码生成、生成分支、项目维度管理（repo 搜索、分支查询、订阅管理）。
- `goofy`: 站点、项目、部署、region、quick preview、回滚、channel。
- `nexde`: NexDE 部署平台；当前覆盖 `project list`，支持 `--region sg` 列出当前用户可见项目，鉴权复用 Titan Passport session。
- `tcc`: namespace、配置查询、创建、更新、发布、deployment detail、审批、权限申请。子组：`namespace`/`config`/`deployment`/`env`/`site`/`permission`；旧的平铺命令保留为隐藏别名。
- `bytestable`: Bytestable 平台命令组；
  - `bytestable opsdata`: 发现适合当前问题的运维数据源与实时 Schema，并通过 GraphQL、RAG 或 OpenViking 执行只读检索。
  - `bytestable qcss`: 用于更新 QCSS 检查项结果，支持按 BITS dev task 自动解析并通过 QCSS 人工项、封装“通过”检查项的 Bytest 接口，以及发布 final_result 放行。
  - `bytestable wcc`: 用于 WCC 的 service、namespace、env、配置查询、新建、元信息更新、结构定义更新、配置值更新，以及相关 deployment、codegen、发布工单。
- `tce`: 服务列表/搜索/详情、集群列表、实例列表/搜索、发布工单列表/详情/取消、env cascader、lane 部署。子组：`service`/`cluster`/`instance`/`deployment`；旧的平铺命令保留为隐藏别名。
- `clouddev`: CloudDev BOE 泳道开发实例，首版覆盖 TCE runtime + BOE region。子组：`instance`（create/list/get/log/start/reload/stop/delete，`start`/`reload` 会按实例返回的 `sync.method` 自动走 rsync 或 bsync 同步本地代码；`instance delete` 永久销毁实例、不可恢复，与只停服务、可再 start 的 `stop` 语义不同）与 `space`（本地记住的 space -> 工作目录绑定，`list`/`delete`，只读本地状态不查远端）。所有写操作默认 dry-run，必须显式 `--yes` 才提交；`start --wait` 轮询到实例就绪。不要与 Devbox 开发机（`devbox`）或 Cloud IDE 混淆。
- `devbox`: Devbox 开发机（BOE），与 cloud-boe devbox 控制台能力对等。`catalog`（可购机型/镜像/软件目录，`--type`/`--flavor` 钻取）、`create`（默认 dry-run 预览 payload，`--yes` 提交；`need_apply` 机型走 xflow 审批）、`list`/`get`、生命周期 `start`/`stop`/`reboot`/`rebuild(--full)`/`delete`/`resize`（`--yes`）、`ssh`/`scp --download`/`ide --type vscode|cursor|trae`、`monitor`/`web-terminal`（`--open` 打开浏览器）；子组：`snapshot`（list/create/delete/rollback，后两者 dry-run+`--yes`）、`volume`（list/extend，`extend_volume` 校验当前容量与上限）、`xflow`（list）、`sandbox`（Computer Use：list/terminal/create/delete/run；`run --task` 为 SSE 流，JSON 模式输出 NDJSON）。站点路由：默认/`--site boe` 走 China-BOE（ec2.byted.org），`--site boe --vregion sg|us` 共享 i18nbd host（US-BOE 新建入口已下线）。写操作一律先 `--dry-run` 预览 payload 再 `--yes` 提交，输入校验错误带 `code` + `hint`。
- `spark-platform`: Spark OpenAPI 资源能力，覆盖：`space list`；`link list`（`--bid` 走 `/api/openapi/v1/links`，`--space-id` 走 `/api/openapi/v1/spaces/:space_id/links`，二选一）；`link create`（CreateShortLink，支持 `--dry-run`）；`link get`（完整 raw 数据，包含所有 version 与原始 deployConfig，无派生字段）；`link summary`（取最新已发布 version，并把 deployConfig 解析成 `schema.pageConfigs[]`，字段含 `schemaUrl`/`bundle`/`bundlePath`/`abParams`/`dynamicParams` 等）；`link env list` / `set` / `delete`（`--app-id` 可选，默认 `22`；`set` 与 `delete` 支持 `--dry-run` 打印最终 payload 不实际发请求）。注意：`--bid` 是业务线 ID，不是 space 的 `id`，两者不互通。
- `kross`: 创建多平台（Linux、macOS、Windows）容器环境（workload），支持 workspace 列表、workspace 维度的 container template 查询、workload 列表、workload 创建/删除，通过 webshell 在 workload 容器内执行命令，以及基于临时 capability URL 的 workload 文件上传/下载。子组：`workspace`/`template`/`workload`。
- `env`: 环境搜索、标准环境、创建、设备、审计、TCE 服务升级/部署、ByteCopy service/instance/目标地址管理。子组：`site`/`service`/`bytecopy`/`device`/`ticket`；旧的平铺命令保留为隐藏别名。
- `faas`: FaaS 服务全生命周期管理（子组：`function`/`cluster`/`trigger`/`revision`/`template`/`release`/`log`/`invoke`/`remove`）；查询服务、集群、触发器、代码版本、模板；查看日志；调用函数（HTTP/Timer/Kafka/RocketMQ/EventBus/TOS）；创建/中止发布；创建/更新/删除触发器；删除服务和集群。
- `tae`: TAE / AI PaaS 命令；当前覆盖平台原生 `tae agent search/list/get`、`tae sandbox search/list/get`、`tae mcp server search/list/get/create/update/release`、`tae mcp tool list/get/create/update/delete/import-bam`、`tae mcp schema generate/update`，以及已确认路径的 `tae api get/post/update/delete` 原生透传。
- `bytedance-tae`: TAE / AI PaaS 内部 API 工作流；重点覆盖 Agent/Sandbox list/get、`/tae/mcp_server/...` 页面下 MCP Server 新建/list/detail/update、tools 的 create/update/delete、从 Thrift IDL 生成 `tool_input_schema`、release 发布与验证；也记录 Memory、Skill、A2A Registry、Security、Keys 等已发现页面/操作名。CLI 未覆盖能力时使用该 skill 指南。
- `tmates`: TMates OpenAPI 命令；覆盖 OAuth check、followed project list/get、run list/detail/create、unified `space` 的 list/get/create/update/delete、按明确 `space|ma_space` scope 列 managed agent 和 Memory Store，以及 Memory Store 文件 list/read。默认使用 unified `space`；已知兼容 scope ID 必须显式 `--scope-type ma-space`，不跨 scope 回退；不提供已下线 legacy Space 服务的发现接口。Space、agent 和 run 写入要求 `--yes`。TikTok ROW 网关用 `--site i18n-tt`。
- `bma`: BMA Agent 平台内置命令域；详细路由 skill 为 `bytedance-bma`。覆盖 Workspace、Model、Agent/Version、Session、Credential、Connector/Schedule、Dataset/Doc、Skill/Plugin，以及受控的 Runtime prompt/event/SSE。固定使用 CN prod/PPE 目标和现有 ByteCloud JWT；mutation 先输出 plan，显式确认后执行一次写入并 readback。`dataset doc update` 只替换 FILE 文档内容，从 `--file` 读取非空普通文件；未被 live contract 确认的 Runtime Config、Schedule restore 等能力不注册。
- `warlock`: Warlock 网络抓包分享只读查询；`share get --url <share-url>` 返回规范化的 request identity、response body 与 response headers，可显式请求始终脱敏的 request headers。
- `volcano`: Volcano Engine；支持 Babi SSO session（`volcano auth config --volc-account-id <account-id>`）和 AK/SK（`volcano auth config --access-key-id <ak> --secret-access-key <sk>`）。AK/SK 会同步到 ve 固定 profile `bytedcliak` 并切换生效；Babi 设备码登录以账号名作为 ve profile，登录后显式切换。`volcano auth list-accounts` 可列出当前用户有权限的火山账号，`volcano auth approve-device` 可用选定的 Babi Session 批准 `ve login --no-browser` 设备码，`volcano auth logout` 只同步退出 Babi Console Login profile。ve 已支持的标准 OpenAPI Action 全部优先使用 `ve`；bytedcli 保留 Ark、TLS、TOS，以及 DBW 本地 SQL 文件、VKE Secret 默认脱敏和 VKE TLS 离线日志等无安全等价入口的增强能力。
- `bytecloud` / `cloud`: 站点、vregion、VDC 等字节云基础信息。
- `janus`: Janus 泳道、group、配置、IDL 版本、endpoint、backend 与发布 workflow 管理；backend create/update 支持 thrift/http 协议。
- `moss`: MOSS 测试物料管理平台，支持测试账号测试标查询、名下测试账号列表，以及虚拟证件列表。鉴权使用 ByteCloud SSO JWT。
- `bytetree`: 服务树节点搜索、详情查询、子节点遍历、父链查询。
- `netlink`: 域名、路径、topology、servername、域名配置。
- `neptune`: dispatch、stability、rate limit、security 治理配置，ACL/strict-auth 原始状态查询，`strict-auth apply` 权限申请（含 extra_info、custom form、leader review 补参），以及泳道资源管理；不提供 caller→callee allow/deny verdict。
- `settings`: Settings 配置全流程能力（`item`/`draft`/`review`/`deploy`/`whitelist`/`ut`/`var`/`biz`）。
- `cloud-ticket`: 工单查询、审批、按创建者/待审批/全部筛选。
- `kani`: Kani 权限审批工单的创建、查询，以及 Kani 权限系统知识库检索。
- `dkms`: data key 查询、权限检查、权限列表、授权。
- `kmsv2`: keyring、customer key、ACL 权限管理。
- `iam`: 员工信息查询。
- `byteio`: ByteIO 埋点元数据、参数校验、需求、BTM 点位、测试用例、点位映射与广告 tag/label 查询；`btm point create` 额外支持通过 `data.bytedance.net` Web session 创建 BTM 点位；`transformation` / `transform` 子组覆盖数据加工（Mario 转换规则）的查询、修改、测试与上线申请。子组：`event`/`requirement`/`btm point`/`test-case`/`map`/`ad`/`transformation`/`transform`；查询与 OpenAPI 写链路鉴权通过 `BYTEDCLI_BYTEIO_AUTHORIZATION`，BTM 创建与 transform 系列复用浏览器登录态或 `BYTEDCLI_BYTEIO_WEB_COOKIE`。
- `tiktok-scheduler`: TikTok Scheduler 调度平台；`onetime`（一次性任务）与 `recurring`（周期任务）两类调度，action 支持 rpc/http/workflow。子组：`onetime`/`recurring`。

## Collaboration, docs, and AI knowledge

- `insearch`: 跨源搜索字节内部知识、文档、服务与工具。当前覆盖 `query`（默认仅查确定性源：Feishu 文档/消息、ByteCloud 文档、bytedance.net 内网搜索、ByteTech 技术文章；BitsAI 需显式 `--source bitsai.bytedance.net`）、`get`（按 URL 或 ID 获取内容，并对允许的内部 HTTP(S) URL 提供只读 GET fallback）、`ask run/list/delete`（独立执行或管理 Ask Feishu Q&A）、`login`（一键登录所有搜索服务）、`status`（检查各源认证状态）。
- `lark`: 文档、Wiki、评论、Drive 媒体、日历、会议、任务、Sheet、Bitable、消息、聊天。
- `oncall`: ByteCloud Oncall Platform 工单查询与受限关单、群聊、智能问答与总结、租户/问题分类/值班人/文档/公告/历史工单查询，以及具有明确 Oncall 意图的故障排查、提单和按确认门禁创建 Oncall 群。
- 字节内场 NAT（DCS）的配置出口与历史流量只读查询：`nat` / `bytedance-nat`；与 Bytebox 并列，独立于 ByteCloud Oncall。火山云 NAT 使用 `volcano`；仅当用户泛称 NAT 且上下文无法区分内场与火山云时先确认场景，不承接办公室 NAT。
- `people`: People 自助请假记录查询与全天/半天假申请；`people leave list --start-date <YYYY-MM-DD>` 查询当前账号请假记录，`people leave apply --date <YYYY-MM-DD> --full-day --leave-type <type>` 申请单条全天假，或用 `--half-day am|pm` 申请单条半天假；两者都会先做提交前校验，真实提交必须显式传 `--yes`。
- `jinshu`: 锦书 / 云锦书消息预览与发送；当前覆盖 `message preview` 和 `message send`，支持 `--content` / `--content-file`，正文固定按锦书体发送。首次真实请求前先执行 `auth login --session --feishu`；真实发送必须传 `--yes`。
- `fundeye`: fundeye 资金安全平台，覆盖 Risk-O 业务变更分析，以及 fullink / tcheck 核对规则详情、差异、告警详情和列表。
- `starling`: Starling 文案平台全量命令面；Shortcuts 覆盖项目、空间、翻译 Key、任务、译文、发布、文档项目、文档任务、工作流；API Runner 覆盖全部 OpenAPI；支持 RAG 搜索（`search docs/knowledge`）；`bytedcli starling upgrade` 手动升级运行时。
- `cloud-docs`: 云文档搜索、业务列表、文档列表、Markdown 正文获取。
- `meego`: OAuth 登录后的资源命令域，优先使用 URL 或资源化子命令，不要手拆 MCP tool 名；完整命令树见 `bytedance-meego` guide。常用入口有 `workitem`、`view`、`comment`、`chart`、`team`、`node`、`state`，URL 优先如 `comment list --url <workitem-url>`、`chart list --url <view-url>`、`view get --url <view-url>`、`workitem get --url <workitem-url>`，流转前置检查用 `state required-fields get`，`array<string>` 类型原生参数除 JSON 外也支持单值、逗号或竖线分隔（如 `--user-keys foo,bar` 或 `--user-keys foo|bar`），非 JSON 模式优先输出表格，查评论、图表、团队、成员、排期时默认看文本模式即可。需要富文本详情（Quill Delta 转 Markdown、图片/附件下载 URL、linked_story 展开）时加 `--rich`，如 `meego workitem get --rich --url <issue-url>`；执行前先跑 `bytedcli auth login --session --feishu`，CLI 会复用保存下来的 Feishu Web session，通过纯 HTTP 链路换出 Meego goapi 所需 cookie。附件下载走 `meego workitem download-attachment --url <attachment-url> --output <dir>`，URL 从 `--rich` 输出的 description Markdown 里提取。工作项删除走 GoAPI：`meego workitem delete --url <workitem-url>` 或 `meego workitem delete --project-key <project-key> --work-item-id <id> --type story`，同样依赖 `auth login --session --feishu` 保存的 Web session。节点子任务删除走 GoAPI：`meego node subtask delete --project-key <project-key> --work-item-id <parent-id> --task-id <sub-task-id[,sub-task-id]>`。issue view 排序和分组可显式设置：`meego view preference apply --project-key <project-key> --target-url <view-url> --group-fields priority,template,work_item_status --sorts priority:ASC`；从模板同步筛选/分组/排序用：`meego view preference apply-template --project-key <project-key> --template-url <template-view-url> --target-url <view-url> --filter merge --group replace --sort replace`。多排序用逗号分隔，建议先加 `--dry-run` 检查 diff。
- `fornax`: prompt workspace、prompt 查询、创建、更新、发布，以及 experiment 创建、详情、results、aggr-results；experiment 额外支持 `fornax auth config/status` 配置 JWT 或 AK/SK。
- `aime`: AIME space 列表/详情、session 创建/获取/列表/发送（支持附件上传；通过全局 `--site cn` 使用 `aime.bytedance.net`，`--site i18n-tt` 使用 `aime.tiktok-row.net`；`--auth-site` 只覆盖 SSO 环境，不选择 AIME API host）、完整事件历史回放（`aime session replay-events`，保留工具输入输出原始 payload）、personal assistant 列表/发送/事件/模型（`aime assistant list/send/event list/model list`）、模型选择与锁定（`aime assistant model update` / `aime assistant model-lock update`，默认 dry-run）、chat、interactive、DeepWiki。子组：`space`/`session`/`assistant`；旧的平铺命令保留为隐藏别名。
- `mindai`: MindAI 远程图表能力；当前 `mindai chart` 覆盖 `create`/`execute`、`update`、`watch`、`svg download`、`template search|get|execute`，交付边界为本地 SVG 和 MindAI 会话链接。
- `ida`: iDA Deep Research、Agent、模型、skill market、MCP、session/message 与 raw chatCompletion。普通研究和总结优先用 `ida deep-research create`；需要 web-style iDA agent/session 流程时再用 raw chat/session/message 命令。完整说明见 `bytedance-ida` guide。
- `tika`: Tika AI 对话、conversation、model、space。

## Data, storage, and analytics

- `ttlive-compliance-ace`: TikTok LIVE DECC/DES 合规工单与内嵌 Agent 对话。只用于 TikTok LIVE compliance 数据工单，不用于其他业务域。`task list` 只列当前登录用户并对上游模糊 owner 结果做精确过滤，`task get --session-id` 查看任务与各区域 Ticket，`chat history --session-id` 只读回放，`chat send --session-id --message` 默认 dry-run，显式 `--yes` 才发送。task/get/history/live send 都校验 session owner；live send 超时后先查 history，避免重复消息。
- `abase`: ABase2 namespace / table 查询，支持列表、按 PSM 搜索、详情、`command list`、online query、region/location 元数据、classic(1.0) 集群 list/get（走网关 /api/v1/abase_classic，只读）；`acp list/add/delete/sync` 管理 SDK 运行态鉴权（授权 region 用 `--perm-region`，`--region` 为隐藏兼容别名）（新增/删除授权生成 BPM 审批工单，`sync` 对账修复 ACP 授权；写操作需 `--dry-run` 或 `--yes`）；`ticket list/get/approvers/approve/reject/cancel/retry` 跟进与审批 ABase BPM 工单。Redis / Cache 服务仍使用 `cache`。
- `rds`: 收藏数据库、库详情、表、schema、SQL 查询、BPM 工单（含 `bpm permission apply`、`bpm update --sql`）。子组：`db`/`slow`/`alert`/`ops`/`bpm`（含 `bpm permission`）；旧的平铺命令保留为隐藏别名。
- `magibook`: 独立 Hive/ClickHouse/Doris SQL 执行与状态、有限结果预览、取消，以及 book/cell、Prism、workspace、asset、MagiTeam agent。未指定既有平台或平台资源 ID 的 standalone SQL 默认使用 `sql execute`；明确指定 Aeolus、Dorado、TQS、ByteHouse、Doris Ops 或其专属资源 ID 时保留原平台路由。
- `bytehouse`: 在 ByteHouse 集群上执行 SQL；`cluster search` 支持按 keyword / region / dc / product 搜索 ByteHouse 集群，`query run` 支持通过 `--cluster-id` 或 `--cluster-name` 在对应集群执行 SQL，SQL 可来自 `--sql` 或 `--file`，支持 `--dry-run` 与 `--rows`。
- `doris-ops`: 在指定 Doris Ops 集群上执行 SQL；`query run` 要求 `--cluster-id`，`--sql` / `--file` 二选一，`--region` 当前仅支持且默认 `sg`，`--rows` 只截断输出。单条明确只读的 SELECT/SHOW/DESC/DESCRIBE 默认可执行，其他或有歧义的 SQL 必须经用户确认后显式传 `--yes`。
- `bytedoc`: ByteDoc 数据库搜索、关注列表、详情、集合、文档 CRUD、慢查询、Mongo shell 风格数据查询。
- `cis-master-data`: CIS主数据只读查询，当前支持部门、法人主体、主体账户、金融分支机构、汇率、利率、币种、银行总行、国家/地区、省/州、城市、区/县、国籍、自定义区域、时区、公共假期、语言、证件类型、源系统标识、CIS业务线、虚拟主体、人员序列、职场、楼宇、楼层、地产项目、IT库房位置、收单地址、商户号、预算科目、预算科目扩展、会计科目、会计科目扩展、会计子目、会计子目扩展、多账套会计科目、多账套会计科目扩展、财务区域、核算区域、付款类型、支出类型、支出类型Mapping、采购品类、中台属性、业务线、业务线扩展、业务线星云关系、总账侧业务线、往来模型；自然语言说主数据、CIS主数据 / CIS 主数据、EA主数据 / EA 主数据时均路由到这里。支持范围由模型命令组决定，构造精确或受限条件查询前先读取对应模型指南，不猜测字段或条件组合。
- `dataq`: 海外 DataQ RDS 查询，主要覆盖 `i18n-tt` 站点。
- `hive`: DataLeap 资产搜索、schema、lineage、partition、rows，以及 Hive 表创建与字段修改。
- `bamboo`: Bamboo 离线规则 list/create/update/get 与离线结果详情；开放接口无需 bytedcli 鉴权，写入默认 dry-run，显式 `--yes` 才提交。
- `oneservice`: OneService query 元信息、query version detail，以及按 queryId 自动解析当前 ONLINE version 后提取 SQL；当前覆盖 `meta get --id <queryId>`、`detail get --id <versionId>`、`sql get --id <queryId>`；鉴权依赖所选站点的浏览器 session cookie，默认 `cn` 使用国内 OneService 端点，`--site i18n-tt` 使用 i18n-tt OneService 端点，需先对目标站点执行 `auth login --session`。
- `devmind`: Bits DevMind / DataMind 指标故事只读查询；覆盖 `doctor`、`node get|search`、`meta`、`user get`、`space tree`、`report list`、`story list`、`dashboard get`、`model list|get`、`model partition get`、`model dimension list|values`、`model metric list`、`drill dimensions|get`、`metric list|get|query`、`query`、`builtin metric list|query|tool-ratio list`（「开发人员AI使用分析」内置目录与工具分项贡献率），用于发现报告与指标、查看复杂指标维度并通过 `data_mart` 取数。
- `byterec`: Byterec 平台统一工具；Candidate DB / CandsDB 使用 `candidate-db`，Elements / Darwin 特征工程使用 `elements` / `darwin`，Index Service 使用 `indexservice`，模型配置使用 `model`，Viking service config / ByteKV / Viking DB 使用 `viking`。查询、写入安全、站点与组件资源边界统一见 `bytedance-byterec` guide；所有支持写入的组件默认 dry-run，只有显式 `--yes` 才提交。
- `holmes`: Holmes TrustPress、TikDiff、TrustData、ByteCore、IndexService proto/record debug、TBase 产品/字段/row-key 查询、release checker、code-review 与 TikTok Debug 工具。IndexService 覆盖 `holmes indexservice proto list/create/get`、`holmes indexservice record get`；TBase 覆盖 `holmes tbase product get`、`holmes tbase config get`、`holmes tbase field list/describe/add/get`、`holmes tbase trigger list`。首次使用前先 `bytedcli auth login --session`；详细工作流见 `bytedance-holmes` guide。
- `clickhouse`: DataLeap CoralNG ClickHouse 建表（`create`：结构化字段 + 引擎参数，支持 HaMergeTree / HaUniqueMergeTree / CnchMergeTree 等，`--cluster-name` 不传时按 `--database` 自动反查）、改字段（`field update`：按 GUID 整表替换列 / 分区键 / 主键，默认非主键列自动包 `Nullable(...)`，可用 `--no-auto-nullable` 关闭）、改表级属性（`attr update`：按 GUID 修改 TTL / 描述 / owner / 业务联系人 / 权限管理员 / 安全等级 / 核心资产标记，未传的 option 保留原值）与库元信息查询（`db get`：返回 cluster / virtualWarehouse / owners / env）。
- `aeolus`: dashboard/dataset 搜索、字段详情、SQL 查询、权限申请。
- `life`: 生活服务生财有数平台的工具集；当前覆盖直播数据工作台的工具集 `life live-screen`，其中 `summary --room-id <room-id>` 用于获取核心指标、指标元数据与诊断文案，`user-info` 支持按主播 ID、主播抖音号、直播间 ID 或主播昵称获取用户信息。认证复用 `auth login --session --auto` 保存的 Data portal 浏览器会话。
- `merlin`: Merlin job 按 job id 或完整 job URL 提取 submit-ready YAML、从本地 YAML 再次提交 job，支持 `merlin job list` 查看当前用户的 job runs、`merlin job trials` 优先按 Arnold `custom_id = job_run_id` 枚举所有 trials、`merlin trial diagnose` / `merlin trial local-log` 处理 trial 级问题；`merlin logs get` 查询 Merlin job/trial 的 stdout/stderr 日志；Merlin tracking 的 project/run/metric/job-link 只读查询；`merlin quota` 下的 group/cluster 只读查询。`--site` 控制鉴权拿 JWT，`--vregion` 选择 Merlin 环境，默认 `cn`，支持 `cn`、`i18n-bd`、`i18n-tt`、`eu-ttp`、`us-ttp-bdee`、`us-ttp-usts`，其中 `cn` 和 `i18n-bd` 支持 `--vregion seed`；支持 `merlin job list-sites`、`merlin tracking list-sites` 与 `merlin quota list-sites` 查看映射，其中 `merlin job list-sites` 会额外展示 job core / job trials 的 route 字段。
- `helix`: 模型与 AI 任务生命周期入口；当前覆盖 `helix train video-aipf submit/status/stop/list`、`helix eval video-aipf submit/status/stop/list` 与 `helix data video-aipf submit/get`。训练和评估通过 Helix BFF 提交、查询、停止 Video AIPF 训练和 Ray 评估任务，鉴权使用 `BYTEDCLI_HELIX_API_KEY` 或 `--api-key`，需要非默认网关时才传 `--endpoint`；数据准备不使用 BFF API Key，`data video-aipf submit --source` 接收飞书表格 URL，表格列顺序必须是 `item_id`、`neg_vote`、`pos_vote`、`label`、`label_cn`，`--target-table` 只填写 `content_moderation_omni.aipf` 下的表名后缀；`--input-table` / `--table-identifier` 支持 `table?[predicate]`，但拒绝空 `?[]`；记录查询用 `--start` / `--end` 过滤提交时间，分页默认 `--page 1 --page-size 20`；`eval video-aipf submit --limit 0` 表示全量评估；`eval video-aipf submit --positive-vote-threshold` 可覆盖正例票数阈值；`eval video-aipf submit --worker-count` 默认 1；`eval video-aipf submit --branch-name` / `--commit-sha` 是高级可选参数，普通提交推荐不写，CLI 默认使用验证过的 recipes ref。
- `tardis`: Tardis 模型服务/流水线平台；子组：`project`/`shadow`/`service`。`project list --base-url <url>` 列出项目资源；`shadow query [--space-id N]` 按 space_id 查 shadow 模型（默认 18）；`service node-types` 列出流水线支持的 node 类型与每个 node `execute` 必填字段（agent 调用 `service run` 前先查这一接口）；`service run --node-type <type> --action <execute|check_finished> [--body <json> | --body-file <path>]` 触发或查询 node 任务，CLI 不本地校验 body 字段，省略 `--body` 时由后端结构化返回缺哪些字段，agent 按 `msg` 多轮补全。`submitter` 字段必须填发起人邮箱前缀（如 `zhangsan@bytedance.com` -> `zhangsan`），AI agent 代发起时使用当前已登录到 bytedcli 的用户邮箱前缀（读 `~/.local/share/bytedcli/data/userinfo.json` 或 `bytedcli --json auth status`），不要写成 `agent` / `bot` / `ai` 等字面量；无法可靠拿到邮箱前缀时先向用户索要。host 自动按 `BYTEDCLI_NETWORK_PROFILE=prod` 切到生产网，统一在 `src/api/tardis/site.ts` 解析。鉴权走 Titan Passport cookie，需先 `bytedcli auth login`。
- `dorado`: project、task、folder、instance、Debug 终止、query diff、ad-hoc SQL 执行与结果查询、MySQL->Hive binlog 状态检查与接入，以及节点草稿上的 Spark-jar operator 配置。子组：`project`/`task`/`folder`/`instance`/`debug`/`adhoc`/`spark-jar`/`task binlog`；旧的平铺命令保留为隐藏别名。
- `blade`: Blade 平台数据同步任务查询、创建、补数据与更新。子组：`task`、`resource`；当前支持 `blade task get --id <taskId>`、`blade task list [--task-name <name>] [--owner <owner>] [--project-id <id>] [--create-status created] [--task-type data-sync] [--page <n>] [--page-size <n>]`、`blade task operation list --id <taskId>`、`blade task project list/get --project-id <projectId>`、`blade resource precheck --resource-id <resourceId> --resource-region <code> --auth-object <psm>`、`blade task create (--payload-json <json> | --payload-file <path>) (--dry-run | --yes)`、`blade task backtrack --id <taskId> --user-id <userId> [--rps 5000] (--dry-run | --yes)` 与 `blade task update --id <taskId> (--payload-json <json> | --payload-file <path>) (--dry-run | --yes)`，并内置 `--region mycis` 到 `i18n-bd` 的鉴权站点映射；鉴权优先复用 `blade.byteintl.net` 站点 cookie 与 fresh ByteCloud JWT，Titan Passport 仅作 best-effort 兜底；`task create` / `task backtrack` / `task update` 是显式写操作，必须先 `--dry-run` 预览请求，再 `--yes` 提交。
- `tqs`: Table Query Service SQL 执行。
- `forge`: Forge 任务概要与训练诊断；`forge job diagnose` 聚合有界 Forge log error code、经上下文校验的 Primus application exit code/diagnostic 和 pod 状态，text 最多展示 20 条异常 pod，`--json` 保留全部 retained pod items；`forge job get` 查看概要，`forge logs` 拉原始日志窗口。
- `kaboo`: Kaboo 内部 AI coding 用量追踪器，收集本地工具 (Claude Code / Cursor / Copilot / Codex 等) 的 token 用量并上报到 https://kaboo.bytedance.net，用户可查看个人统计、排行榜、趋势。`bytedcli kaboo ...` 首次运行自动准备运行时并注入 ByteCloud JWT，参数原样透传。
- `byteio`: ByteIO 埋点 OpenAPI + ByteIO Web BTM 创建；覆盖 `event get`（单个埋点元数据详情）、`event check-params`（埋点参数校验）、`event list`（按邮箱前缀查埋点）、`requirement list/get/locations`、`btm point get/create`、`test-case list/get`、`map locations/events`、`ad tags/labels`、`transformation list/get/space list/auditor list`、`transform list/get/version list|diff/create/update/test/test-history list/release check|create|list|get|delete`。支持 `--region cn|sg`（默认 cn）处理 OpenAPI 查询，POST 类命令支持 `--body-json` 合并请求体；`btm point create` 走 `data.bytedance.net/byteio/api/v1/btm_codes`，transform 系列走 `data.bytedance.net/mario/api/v2`，都优先复用浏览器登录态；transform 写命令默认 dry-run，`--yes` 才提交。
- `bmt`: Byte Multi-Tenant Platform；覆盖 `service get`、`tag list`、`resource list`、`resource resolve`、`isolation-set list`、`user-role get`。服务级命令公开入口优先用 `--psm`，CLI 会先解析 `psm -> service`，再查询标签、资源和 user role；`--type mq` 可解析 RocketMQ `cluster/topic`，`--type rds` 可解析 RDS `psm/db_name`，`resource resolve` 省略 `--type` 时会自动尝试 `mq -> rds`。
- `vertex`: Vertex 平台 registry 驱动的动态命令命名空间；没有静态业务子命令，先用 `vertex --help` 从 registry 查看当前可用命令，例如 `vertex operation-log list [options]`，再用 `vertex <module> <action> --help` 查看该 action 的参数、required、type、choices 和 description；执行形态为 `vertex <module> <action> --flag value`。registry 会按 `site + origin` 做本地缓存，传 `--refresh` 强制刷新；联调可用 `BYTEDCLI_VERTEX_BASE_URL` 覆盖请求 origin。
- `es`: Elasticsearch DSL 查询、mapping 查询与更新。
- `cache`: Redis 服务搜索、慢日志、大 key、工单、命令执行。
- `bmq`: Kafka topic 列表/详情、cluster 列表、consumer 列表、mirror 列表。子组：`topic`/`cluster`/`consumer`/`mirror`；旧的平铺命令保留为隐藏别名。
- `eventbus-cn`: Eventbus CN-only event、client、storage、mirror、producer、consumer 查询，消息查询；详细参数见 `bytedance-eventbus-cn` skill。
- `tos`: bucket、用户信息（`get-user-info`）、用户记录、站点与 vregion。`user-info` 已重命名为 `get-user-info`，旧名保留为隐藏别名。
- `dolphin`: 动态决策平台（事件、规则组、规则）查询、创建、更新、删除、规则组部署、测试用例检查与内建 raw API 请求。子组：`api execute`、`event`（含 `event group`/`event var`/`event param`/`event testcase`）/`group`（含 `group factor`/`group feature-env`/`group testcase`）/`rule`；旧的平铺命令保留为隐藏别名。
- `safe`: 内容治理平台。认证（SSO 或 cookie 登录）、配置管理（tenant/business）、Puzzle 特征/实体/数据源/租户/包/集合、样本查询、Hawk scene/service/scope 元数据与 ops list/get 查询、Hawkpro trace、SafeMind model/graph/trace（含 test-node），以及 Digital Employee agent、图实例校验/更新、run-agent 试运行、仿真结果和批量仿真任务。子组：`puzzle`、`sample`、`hawk`（`service list` / `scope list` / `scene list` / `ops list|get`）、`hawkpro`、`safemind`、`eva`、`de` / `digital-employee`；`ds` 是 `datasource` 别名，`pkg` 是 `package` 别名。相关子命令支持 `--tenant` 选项，优先级：`--tenant` > `SAFE_TENANT` env > config > 默认 `ecology`。

## Runtime, logs, and observability

- `byteflow`: ByteFlow 状态机 / 工作流引擎管理命令，语义类似 AWS Step Functions；覆盖 app / statemachine / revision / execution / activity / DAG 查询、workflow JSON/ASL 校验、BRN 资源语法说明，以及带 dry-run 与逐次确认保护的创建/更新/revision 辅助。底层转发到 `bytedance-byteflow` bundled helper。
- `cronjob`: 挂载、可用 zone、任务、执行记录、实例详情、工单、发布、集群资源 / Argos、集群创建、暂停 / 恢复 / 删除、重跑、debug。
- `log`: PSM 日志、LogID 查询、按接口维度做 BytedTrace 总体性能分析（`analysis performance`）、按 `logId` 查看 BytedTrace 调用树（`trace-tree`）、实例日志、日志聚类，以及 Footprint TCE Sync / Megatron URL 下载（入口为 `log footprint`，不是顶层 `footprint`）。
- `primus`: Primus 只读诊断；`app list|get` 发现并汇总应用，`am|config|job|data|env|cluster|doctor|streaming|flow ... get`、`role|pod|task|timeline|task-build ... list` 与 `devops ...` 查询 UI/History 资源，`log list|get` 通过区域 CLI API 查询日志元数据，并在 TTP 站点通过 Footprint 读取正文；当日志结果为 `logResolutionStatus: "landing-only"` 或 `"no-files"` 时，表示后端未暴露 concrete file，不能把 `resolvedLogUrl` 当日志正文下载；Argos/streamlog tenant-query URL 不是 Primus executor raw log；`export` 生成本地排障转储。
- `godel`: Godel Explainer 生产 API 的只读调度诊断。`cluster list` 列出当前站点的可用集群；`instance get` 使用 `--cluster --namespace --name [--type pod|podgroup|application]` 精确目标，并支持 `--diagnosis-id` 和 `--timeout-ms`。当前只支持 `cn` 与 `i18n-tt`，其他站点 fail closed；不解析 Primus/Forge URL 或 Fed task selector。命令不会 kill、重提或修改调度对象。Godel stream-applications / Flink Web 的 job、checkpoint、failover、lag 和反压仍走 `flink`。
- `archer`: 链路级覆盖率查询（按 PSM + traceId 查询流量级函数调用链路与覆盖行明细）。
- `apm`: service preview、QPS、下游、Redis 监控。子组：`service`/`redis`；旧的平铺命令保留为隐藏别名。
- `bytedog`: ByteDog 性能诊断、可创建、查询和列出常见的 profiling（`<oncpu|thread-overview|sprofile|offcpu|pthread|je-stats|je-flamegraph>`）或 GDB 分析任务（`gdb`）。
- `bytesan`: ByteSan 只读扫描结果；支持各 ByteCloud 区域下 `/byteq/bytesan` 控制台 URL，按仓库列 Task，按 PSM / 仓库列 Scan，按 Task / Run 列 Bug，按 Bug 列 Report / Build ID，并读取原始报告和构建 Git 元数据。
- `slardar`: Slardar Web / App / PC / OS 统一命令组。
  - `slardar web`: query assistant、告警 URL 分析、`alarm-rule-list`、`alarm-history`、JS Error、SOP 与 Investigation。
  - `slardar app`: Slardar App 工具集；`issue log` 支持从 Slardar App issue URL 拉日志，`issue log --symbolicate` 支持 Slardar retrace 与 native 栈符号化 fallback，`symbol url` 支持 `--build-id`、`--so-file` 或 `--uuid` 生成 native symbol uuid / symbol URL。
  - `slardar pc`: Slardar PC 桌面端工具集；`issue log` 支持从 `/node/pc_detail/jank/detail` 或 `/node/pc_detail/crash/detail` URL 读取 Jank/Crash 事件详情和已符号化线程堆栈。
  - `slardar os`: Slardar OS 工具集；`issue log` 支持从 Slardar OS issue URL 拉取事件 summary，`issue log --symbolicate` 支持复用 Slardar App native symbol 能力解析主线程 native 栈。
- `vela`: Vela one-machine 单机指标查询；当前覆盖 `one-machine query`，支持直接传 monitor-view URL，或通过 `--selected-name` / `--host`、`--cur-count`、`--time` 查询 VM 指标序列。

## Quick routing by artifact

- `code.byted.org/.../merge_requests/...`、`issues/...`、仓库路径：走 `codebase`
- `bits.bytedance.net/quality/dora/...`、Dora 云真机设备序列号：走 `dora`
- `bytedance.larkoffice.com/...`、`larksuite.com/...`、sheet / bitable / doc / wiki 链接：优先 `lark`
- `starling.bytedance.net/...`、Starling 项目 / 空间 / OpenAPI 文档：优先 `starling`
- Cloud Docs 文档搜索/正文：`cloud-docs`
- 字节内部搜索（飞书/ByteCloud/内网/ByteTech/BitsAI 多源）：`insearch`
- 架构图、流程图、ER 图、时序图、甘特图、思维导图或已有 MindAI 图表任务：`mindai chart`
- `cloud.bytedance.net/tcc/.../publish-details/...`：`tcc deployment get` / `tcc deployment approve`
- Argus Hybrid、JSB 权限、安全 URL、secure 方法、Lynx Gecko channel 绑定工单、宿主 label 搜索：`argus hybrid`
- `cloud.bytedance.net/bytedoc/...`：`bytedoc`
- `fornax.bytedance.net/space/...`：`fornax`
- `ml.bytedance.net/development/instance/jobs/...` 或 `seed.bytedance.net/development/instance/jobs/...`：`merlin job extract` / `merlin logs get`
- `ml.bytedance.net/experiment/tracking/...` 或 `seed.bytedance.net/experiment/tracking/...`：`merlin tracking`
- `bits.bytedance.net/space/legacy/build/logs?jobId=...`：`bits client workflow job download-log --job-id <jobId>`
- `bits.bytedance.net` 的 DataMind / DevMind / `datamind/report` 指标页面：`devmind`
- `reckon.bytedance.net/forge2/jobs/...`、`reckon-us.tiktok-row.net/forge2/jobs/...`、`reckon-ttp.tiktok-row.net/forge2/jobs/...`、`reckon-eu.tiktok-row.net/forge2/jobs/...`（Forge job/logs 页面 URL）：排查训练失败或错误码时用 `forge job diagnose --url <url>`；只拉原始日志窗口时用 `forge logs --url <url>`
- `lagrange-admin.bytedance.net/om/maas/...`、MaaS / Prifly / PilotBench BU、模型 profile、perf record 或 Prifly model metadata：`lg-admin maas`
- `primushistory.../jobhistory/app/...`、`primus-history.../jobhistory/app/...`、`primus-ui.../<app>/webapps/primus`：先用 `primus app get --url <url>`；再按需执行 `primus config get`、`primus job get`、`primus data get`、`primus env get`、`primus doctor get`、`primus timeline list`、`primus task-build list` 等并复用 `--url <url>`。查日志先执行 `primus role list --url <url>`，再用 `primus log list --url <url> --role <role>` 或 `primus log get --url <url> --role <role>`
- Godel Explainer 的 Pod/PodGroup/Application pending 目标且已知精确坐标：`godel instance get --cluster <cluster> --namespace <namespace> --name <name>`；只有 Primus/Forge URL 时先走对应 domain 获取坐标，不要给 Godel 传 URL 或猜测坐标
- `footprint.tiktok-row.net`、Primus `redirect_log.html`、concrete `mljob-log-proxy` 文件 URL：`log footprint download --url <url>`；plain mljob landing URL 不是 concrete file
- `tmates.tiktok-row.net/task/share/<run_id>`、TMates run id、managed agent id / space id：`tmates`
- TikTok LIVE DECC 合规数据工单页、DECC/DES `session_id`、当前用户合规工单或其 Agent 对话：`ttlive-compliance-ace`；非 TikTok LIVE compliance 工作流不走此入口
- `warlock.byteintl.net/share?key=...`、Warlock share key、API response / response headers / x-tt-logid：`warlock`
- Footprint TCE Sync / pod 本地日志文件 tail/head/ls/grep：`log footprint get`
- TCE deployment / service / cluster 页面或 deployment id：`tce`
- `cloud.bytedance.net/lego/...`、`cloud.byteintl.net/lego/...`、`cloud.tiktok-row.net/lego/...` 等 Lego 控制台 URL，或插件名 / order id / version / commit_tag：`lego`
- `pipo-bmt-sea.tiktok-row.net/bmt/...` 等 BMT 控制台 URL、service id、resource code、PSM：`bmt`
- Panama RPC 工具页面或 RPC 执行需求：`panama rpc execute`
- `cloud.tiktok-row.net/tae/...`、`/ai/mcp_server`、TAE MCP Server/Agent/Sandbox/Memory/Skill 页面：`bytedance-tae`
- Ent Platform Entity / Storage IAC 页面、StorageUri、UDS MySQL 新表 workflow：`ent`
- 字节云服务树页面、节点 id、目录层级：`bytetree`
- Goofy deploy / preview 页面、静态站点目录：`goofy`
- ABase2 namespace / table / online query / ACP 鉴权授权 / BPM 工单审批：`abase`
- Redis、slow log、big key：`cache`
- ES index、mapping、DSL：`es`
- Eventbus event、client、storage、mirror、producer、consumer、消息查询：`eventbus-cn`
- Hive 表、Dorado task id、报表 dataset：在 `hive` / `dorado` / `aeolus` 间选
- Bamboo 离线规则、Hive 质量规则 ID 或离线结果 ID：`bamboo`
- 已有 SG Doris cluster id、要直接经 Doris Ops 执行 SQL：`doris-ops query run`
- OneService queryId、versionId、invoker_server SQL：`oneservice`
- Byterec PSM、indexservice product/config 查询：`byterec indexservice`
- Byterec Candidate DB 候选库详情、记录、样本、监控链接、关联模型和生命周期：`byterec candidate-db`
- Byterec model/version、namespace 下模型列表查询：`byterec model list`
- Slardar 告警页 URL：`slardar web analyze-alarm-url`
- 任意 Slardar Web URL（含 `*.tiktok-row.net`）：`slardar web analyze-url`（离线解析、推荐下一条命令）
- ByteDog profile detail URL、火焰图 / continuous profiling / off-cpu / pthread / jemalloc 任务：`bytedog profile get`、`bytedog profile <type> create/list`
- ByteSan `/byteq/bytesan` URL、仓库 / PSM、Task / Run / Bug / Report / Build ID、ASAN / TSAN / UBSAN 原始报告：`bytesan task list`、`bytesan scan list`、`bytesan task-bug list`、`bytesan run-bug list`、`bytesan bug-build-report list`、`bytesan report-content get`、`bytesan build-metadata get`；URL 按 path / query 选择对应命令并传入 `--url`，后续 ID 查询沿用结果中的 `data.site`
- Vela monitor-view one-machine URL / 单机 VM 指标：`vela one-machine query`
- Android `.so` BuildID / native symbol：`slardar app symbol url`；Slardar App issue retrace/native 栈：`slardar app issue log --symbolicate`
- Slardar PC issue URL（`/node/pc_detail/jank/detail`、`/node/pc_detail/crash/detail`）：`slardar pc issue log`
- Slardar OS issue URL / APK embedded native stack：`slardar os issue log --symbolicate`
- `safe.bytedance.net/...` 特征/实体/数据源/租户/包/集合、SafeMind、Digital Employee 页面或标识：`safe`

## Quick routing by user intent

- “帮我登录 / 看当前账号 / 拿 token”：`auth`
- “看 MR / 发 review / 查 CI / 回评论”：`codebase`
- “查某个 TTP-US npm 包在 Luban 里是否存在 / 看某个版本前缀 / 发布 PyPI 制品版本”：`luban`
- “调试 Lynx / Sandbox 设备 / 录 trace 或 replay / 获取堆快照或实时全局内存 / 使用 LynxExample”：`lynx`；LynxExample 直接查 `lynx example --help`，其他任务先 `lynx skills list`，再加载最具体的返回项
- “更新配置 / 发配置 / 审批发布单”：`tcc`
- “查 WCC 服务 / namespace / env / 配置 / 新建配置 / 更新配置 / 发布工单”：`bytestable wcc`
- “通过 BITS QCSS 人工确认项”：`bytestable qcss manual pass`
- “通过 QCSS 检查项 / 更新 Bytest quality check item”：`bytestable qcss check-item pass`
- “通过发布 QCSS final_result”：`bytestable qcss final-result pass`
- “用 Panama 调 RPC / 复用 Panama assertion 执行 RPC 工具”：`panama rpc execute`
- “列 Spark space / 创建 Spark link / 列某个 bid 或某个 space 下的 link_key / 看 link 的 env / 给 link 设置或删除某个 PPE env”：`spark-platform`
- “部署服务 / 看实例 / 查 cluster”：`tce` 或 `env`
- “通过 Entity 平台创建新 MySQL 表 / 提交 Storage IAC workflow / 导入已有 RDS 表到 Entity entry / 看 UDS MySQL 完整流程”：`ent`
- “查 ByteCopy service / instance / 目标地址 / 添加目标地址”：`env bytecopy`
- “查某个 workspace 可用模板 / 看这个 workspace 下有哪些 workload / 创建临时 job workload / 在 workload 容器里执行命令或传文件”：`kross`
- “查服务树 / 搜节点 / 看父子层级”：`bytetree`
- “看 FaaS 服务 / cluster / trigger / 日志 / 调用函数 / 发布 / 中止发布 / 代码版本 / 模板 / 删除服务”：`faas`
- “查 ByteFlow app / 状态机 / revision / execution / 校验 workflow JSON / 创建或更新 ByteFlow revision”：`byteflow`
- “发 lg-admin / LG Admin Torch 版本 / Lagrange Torch / lg-torch / lgtorch / 发版 / 发版本 / 指定 cpu cuda mlu Torch 版本 / usecache / skip arm”：`lg-admin torch release package build`。不要使用 `lagrange torch`。
- “查询 / 拉取某个已知 LG Admin Torch package release version 的 meta”：`lg-admin torch release package get --release-version <version>`；需要完整结构时使用 `--json`。
- “discard / disable / 废弃 / 下线某个已知 LG Admin Torch package release version”：`lg-admin torch release package discard --release-version <version>`；先 dry-run，确认写入后再加 `--yes`。
- “发 LG 镜像 / 发布 LG 镜像 / LG Torch 镜像 / LG Admin 镜像 / build LG image / LG image release / LG image rebuild”：`lg-admin torch release image build`。只有已有 LG Admin image task id/build version 并要查任务详情时才用 `lg-admin torch release image get`。
- “ICM 查询 / ICM prod / 发布历史 / 最近发布 / 构建 commit / 构建仓库 / repo 或 build 信息查询”：顶层 `icm`。repo/package 名里的 lagrange、torch、mlu、cuda、cpu 不改变路由。
- “注册 Lego 插件 / 触发插件编译 / 看插件 scm_id / 列 plugin 编译版本 / 看编译详情 / 列发布流水线 / 列发布域 (scope) / 创建发布工单 (order) / 查发布工单详情 / 看发布步骤 / 人工确认 Lego 发布工单”：`lego`
- “按 MCP 名称查 TAE server_id / 查询 TAE Agent/Sandbox / 录入 TAE MCP tools / 修复 MCP Input Schema / 发布 MCP server revision / 调研 TAE Memory Skill API”：`bytedance-tae`
- “看 TMates share URL / 查 sandbox run 详情 / 调试 MP2C Regression Steward Agent / 查看 managed agent 或 space 摘要”：`tmates`
- “管理 BMA Workspace/Agent/Session/Connector/Schedule/Dataset/Skill，或向 BMA Runtime Session 发送 prompt 并订阅 SSE”：`bma`
- “列出我的 TikTok LIVE DECC 工单 / 看 DECC session 的 Ticket 状态 / 查看或继续该工单的 Agent 对话”：`ttlive-compliance-ace`
- “读取 Warlock share / 查看抓包 API response / response headers / x-tt-logid / 脱敏 request headers”：`warlock`
- “看火山引擎函数 / 实例 / 实例日志 / 发布状态 / 发布记录 / 发起发布 / sandbox / sandbox image / CR / TLS topic / TLS 日志 / VKE / VPC / NAT 网关 / 子网 / 安全组 / 火山账号列表 / SSO 登录火山引擎”：`volcano`
- “查 Starling 项目 / 创建 Starling space / 搜索文案 key / 配置 Starling AKSK / 用 shortcut +list +create +info / 用 API Runner 调 Starling OpenAPI / 搜索 Starling 文档和知识 / 升级 Starling 运行时”：`starling`
- “查 Fornax workspace / prompt / prompt 发布 / experiment 结果 / 配置 Fornax experiment JWT 或 AKSK”：`fornax`
- “查文档 / 改文档 / 发飞书消息 / 约会议”：`lark`
- “查我的请假 / 今天请了几天假 / 补请半天病假 / 申请 People 请假”：`people leave list` / `people leave apply`
- “预览锦书消息 / 发送云锦书卡片”：`jinshu`
- “查技术文章 / 内部知识 / AI 问答”：`insearch`、`bitsai`、`tika`、`aime`、`ida`
- “查 Eventbus event / client / storage / mirror / producer / consumer / 消息查询”：`eventbus-cn`
- “搜索内部文档 / 查字节内部知识 / 搜飞书文档 / 搜 ByteCloud 文档”：`insearch`
- “提取这个 Merlin job 的 YAML / 把这份 `trial.yaml` 重提到 `seed-cn` / 拉这个 Merlin trial 的 stdout/stderr / 看这个 tracking run 的 config 和 summary / 列出某个 project 下的 runs / 根据 Merlin job id 找 tracking 链接 / 查某个 trial 为什么还在排队”：`merlin`
- “用精确 cluster、namespace 和 name 查这个 Pod/PodGroup/Application 为什么调度 pending / 看 FIFO 队头或节点资源过滤”：`godel instance get`
- “提交 Video AIPF 训练 / 查询 Helix 训练状态 / 停止 Video AIPF 评估 / 查 Helix 评估记录 / 提交 Video AIPF 数据准备”：`helix`
- “查 ByteDoc 数据库 / 看慢查询 / 查集合 / 查改文档 / 看关注列表”：`bytedoc`
- “查某个 PSM 属于哪个 BMT service / 看 BMT tag、resource、隔离集、当前 user role / 解析 RDS 或 MQ 资源连接信息”：`bmt`
- “执行/跑这条 Hive、ClickHouse 或 Doris SQL”，且没有指定既有平台或平台资源 ID：`magibook sql execute`
- “明确在 Aeolus、Dorado、TQS、ByteHouse、Doris Ops 等既有平台跑 SQL”，或给出该平台专属资源 ID：保留对应平台路由
- “查 schema / 看 lineage / 查报表字段”：`rds`、`hive`、`dorado`、`aeolus`、`dataq`、`tqs`
- “已有 SG Doris cluster id、明确要直接经 Doris Ops 跑 SQL”：`doris-ops query run`
- “查 ByteIO 埋点是否存在 / 校验埋点参数 / 查 ByteIO 需求、点位、BTM、测试用例、广告 tag/label / 改 ByteIO 数据加工转换规则并测试、申请上线”：`byteio`
- “创建 Bytediff diff task / traffic task / AB test / 查 Bytediff report”：`bytediff`
- “查 OneService 元信息 / 看 query version detail / 按 queryId 取 SQL”：`oneservice`
- "查 Safe 特征 / 实体 / 数据源 / 租户 / 包 / 集合 / 内容治理平台 / SafeMind / Digital Employee"：`safe`
- “根据直播间 ID 看直播数据工作台 / GMV / 订单 / CTR / CVR / GPM”：`life live-screen summary`
- “按主播昵称 / 主播 ID / 抖音号 / 直播间 ID 获取直播数据工作台用户信息”：`life live-screen user-info`
- “CPU 高 / 采火焰图 / 分析 ByteDog profile 结果 / 查历史 profiling 任务 / 查 PID / off-cpu / pthread lock / jemalloc 内存分配”：`bytedog`
- “查日志 / Footprint / footprint.tiktok-row.net / mljob-log-proxy / 指标 / 告警 / Vela one-machine / native symbol / Redis / ABase / Kafka”：`log`（Footprint 用 `log footprint`）、`apm`、`slardar`、`vela`、`cache`、`abase`、`bmq`

## Notes

- 当多个域都可能成立时，优先选更贴近原始对象的域。
- 当任务目标是"把 bytedcli 暴露给宿主作为工具"，直接用 `mcp`，不要再手工包一层自定义 server。
- Global verb renames: `view` -> `get`, `edit` -> `update`, `find` -> `search`, `detail` -> `get`, `patch` -> `update`. Old names still work as hidden aliases.
- Global flag renames: `--page-num` -> `--page`, `--begin` -> `--start`, `--dbname` -> `--db-name`. Old names still work as hidden options.
