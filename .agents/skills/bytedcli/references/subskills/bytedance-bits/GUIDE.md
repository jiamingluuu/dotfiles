---
name: bytedance-bits
description: "Use bytedcli BITS DevOps for Zhongkui static-analysis issues; AutoCase/Verse manualTask CaseId+MinderId leaf inspect/wait/export/pass; TCC imports, pipelines/compile-job, MR management (including host-sub), component upgrades, client workflow/integration/calendar OpenAPI, custom package builds, AI test cases, lane/branch bindings, releases and PPE/BOE TCE cluster upgrades; Android/iOS AppUse/AirBuild device authorization/registration, Anywheredoor/任意门 capture and interface-test sets. Also routes Dev Task creation to BITS-official bits-devops-dev-task and repository-activity branch-creator lookup to Codebase."
---

# bytedcli BITS

## 如何调用 bytedcli

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

## When to use

- 创建研发任务：先读取 `references/dev-task.md`，交给 BITS 官方 `bits-devops-dev-task` skill；submit 后继续执行该文档的“代码评审就绪检查”，分别报告任务创建结果与代码评审状态，不要按本文件中的底层命令自行拼创建参数
- 查询 BITS 仓库活动页中的分支创建人：路由到 `bytedcli codebase repo branch get --with-creation`
- 查询和推进客户端 BITS MR 流程
- 查询、等待 AutoCase / Verse scenario plan 的 `manualTask` 运行，对精确源 `CaseId + MinderId` 叶执行一次通过，或导出报告与 evidence 元数据（`bits autocase`）：先读取 `references/autocase.md`，确认 URL 的 `devops_space_old_id` 路由项目与 `run get` 返回的业务 `projectId` 不可混用，并确认默认 preview/no-op 不代表平台写入
- 查询钟馗静态检测任务、规则汇总和具体代码行定位（`bits zhongkui task get`）
- 创建主子仓 MR（单宿主+多子仓 SDK 组件发版，支持配置文件驱动和多子仓联合发版）
- 触发客户端组件升级、查询升级历史
- 在应用中心创建 Gecko PSM 并绑定已有 Gecko channel（`bits appcenter gecko create`）
- 查询客户端 workflow / integration / calendar OpenAPI 子域
- 运行自测流水线
- 将 TCC 配置导入研发任务
- 查询或变更研发任务内 TCC 配置的 BOE / PPE / PROD 发布目标
- 更新泳道配置
- 绑定代码分支
- 升级 PPE/BOE 环境内已有 TCE 集群
- 查询发布工作流
- 查询发布工单详情
- 创建发布工单
- 查询、创建或更新发布单内的 TCC Draft（已导入的 Draft 与无线上 source 基线的新建 Draft），以及 BOE / PPE / PROD deploy target
- 调试 Anywheredoor / 任意门（`bits anywhere`）：支持 Android/iOS 调试包设备录入、设备抓包监控与 curl 转换，以及 share 链接解析、设备选择、代理启停、mock 查询/创建/启停/删除、完整 Rewrite 规则创建/编辑、filter 与 black path 查询；Rewrite 配置格式见 `references/anywheredoor.md`
- 管理接口测试测试集（`bits test-set`）：查看/新增/修改/删除请求集合与保存用例（RPC、HTTP/URL、HTTP/指定实例），复制/另存为用例（`case create --from-case-id`），单发或批量执行（含批量任务轮询与逐用例结果），查看单次发送与批量发送两类执行历史及输入输出，生成与解析分享链接，导出为 `bytedcli api-test` 命令或 JSON 并跨测试集导入
- 下载 legacy workflow job 构建日志（`bits client workflow job download-log`），适用于 `bits.bytedance.net/space/legacy/build/logs?jobId=<id>` 这类链接；日志可能 100MB+，流式落盘到本地文件
- 客户端独立打包（`bits client package`）：适用于 `bits.bytedance.net/devops/<workspace>/rd-service/tools/custom_build?devops_space_type=client&devops_space_old_id=<app>` 这类链接；列出 Job 构建 / Pipeline 构建 / 通用配置三类构建配置及其参数骨架，触发与取消打包任务，查看任务历史与产物，下载 ipa/apk 包与 dSYM、LinkMap 等附属产物
- 客户端版本发布DAG（`bits client release-workflow`）：适用于`/release/workflow/versionPublish/detail/<integrationId>/workflow`页面；按版本读取阶段/节点状态，并以“精确阶段名+精确节点名”dry-run或触发单个既有节点。它不同于裸pipeline template触发和独立打包；需要浏览器SSO会话
- 浏览与维护服务模版市场（`bits market-template`）：适用于 `bits.bytedance.net/devops_open/market/template/...` 这类链接；支持模版检索、标签、版本与插件编排查询、引用配置查询、订阅，以及模版与版本的创建、修改、发布/下线、删除
- 客户端 Pipeline Marketplace 编译 Job（`bits compile-job`）：适用于 `bits.bytedance.net/devops/<space>/pipeline/marketplace?devops_space_type=client&devops_space_old_id=<app>`；列出/创建/编辑/删除 Job 与分组，并触发构建

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 大部分 Bits OpenAPI 能力（例如 `bits mr` / `bits component`）依赖 Bits OpenAPI token（请求头 `Authorization: Bearer <token>`）

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

### 查询钟馗静态检测

```bash
bytedcli bits zhongkui task get --task-id 12345678
bytedcli bits zhongkui task get --mr-id 87654321
```

两个定位参数必须二选一。`--mr-id` 是 BITS 页面 `/code/detail/<id>` 中的平台 MR ID，不是 Codebase 仓库内的 MR IID。按 MR 查询时命令会从最新 jobs 中优先选择钟馗静态分析任务，避免误选隐私检测等其他任务。文本输出包含任务摘要、规则聚合和逐条文件/行号；`--json` 返回稳定的归一化结构。

### 查询仓库活动里的分支创建人

BITS 仓库活动页的分支创建事件来自 Codebase v2 活动接口，因此使用 Codebase 的分支详情命令，不新增同义的 `bits` 命令：

```bash
bytedcli codebase repo branch get \
  -R "example-org/example-repo" \
  --name release/1.2 \
  --with-creation
```

默认最多扫描 20 页活动；较老的分支可追加 `--creation-max-pages <1..100>`。如果 JSON 输出中的 `CreationScan.Truncated` 为 `true`，表示扫描达到上限而不是确认没有创建记录。

### Token 获取与设置

- 如果缺少 token，先申请 Bits OpenAPI 权限并获取 token（参考：`https://bits.bytedance.net/open/open_api/permission`）

#### Token 优先级（从高到低）

1. 命令行 `--token <token>`（仅本次请求生效，不写入缓存；若请求 `401/403`，为避免覆盖 override token，会直接报错）
2. 环境变量 `CLIENT_BITS_SERVICE_TOKEN` + `CLIENT_BITS_USER`（必须同时存在；用于服务账号 token）
3. 环境变量 `CLIENT_BITS_TOKEN`
4. 本地 token cache（通过 `bytedcli bits auth ...` 管理；按 Bits `apiUrl` 的 host 分开缓存）

#### 推荐用法

- 普通个人 token：

```bash
export CLIENT_BITS_TOKEN="your-token"
```

- 服务账号 token（必须同时设置 user）：

```bash
export CLIENT_BITS_SERVICE_TOKEN="your-service-token"
export CLIENT_BITS_USER="service-user"
```

- i18n-tt 机房只需要统一切 Bits 域名时，设置现有的 Bits origin 入口即可；更细的旧变量（`BITS_API_URL` / `BYTEDCLI_BITS_API_BASE_URL` / `REPO_UPGRADE_API_URL`）仍会按原优先级覆盖：

```bash
export BYTEDCLI_BITS_ORIGIN="https://bits-i18n.byteintl.net"
```

- 如果还希望为当前项目提供默认的 Bits 环境或默认的 `group_name` / `project_gitlab_id`，可以额外写 `.bits/project_config.json`：

```json
{
  "apiUrl": "https://bits.bytedance.net/",
  "group_name": "demo.group",
  "project_gitlab_id": 12345
}
```

#### 通过命令管理 token cache（推荐）

当 1~2 都未提供 token 时，调用 Bits OpenAPI 的命令会自动尝试获取并缓存 token；若接口返回 `401/403`，会自动刷新一次并重试一次。

```bash
bytedcli bits auth login [--force]
bytedcli bits auth status
bytedcli bits auth logout
bytedcli bits auth config-auth --token <token>
```

> `bits auth` 会自动读取当前 Bits 配置（例如 `BITS_API_URL` / `BYTEDCLI_BITS_ORIGIN` / `.bits/project_config.json.apiUrl`），并按 host 维度管理缓存文件。

## Quick start

### 升级 PPE/BOE 环境里的已有 TCE 集群

`bits env deploy-upgrade` 支持升级已有 PPE/BOE 环境内的 TCE 集群，核心参数为：`env + psm + cluster-id + branch/version`。它只用于升级已有集群；新建环境、新增服务或新增集群仍应使用 ENV 创建链路。该命令是真实写操作：必须显式传 `--dry-run`（预览升级 payload，不调 API）或 `--yes`（提交）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`。

```bash
# 指定 SCM 版本升级。若同时传 --version 和 --branch，--version 优先生效。
bytedcli bits env deploy-upgrade \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --cluster-id 12345 \
  --version 1.0.0.370 \
  --dry-run

# 部署 Git 分支（确认无误后将 --dry-run 换成 --yes 提交）
bytedcli bits env deploy-upgrade \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --cluster-id 12345 \
  --branch feat/demo \
  --yes
```

目标 cluster id 有两条命令可取，返回同一个值：`bytedcli env service get --instance-id <instance_meta id> --standard-env <standard-env>` 取 `data.result.instances[].id`；或 `bytedcli --site <site> tce cluster list --psm <psm> --env <env>` 取 `data.clusters[].meta.id`（`--site` 见 `bytedcli env site list`，BOE 环境用 `boe`；漏填时这条命令报 `TCE_NOT_FOUND`「No TCE service found for PSM ... in env ...」，那不代表服务不存在）。**不要用 `env service list` 找 cluster id**：它打的是 `instance_meta` 接口，返回里没有 cluster 字段，`data.result.items[].id` 是 instance_meta id 而非 cluster id，误当成 cluster id 会把部署发到别处。也可以在 ENV 页面上确认。提交后返回的 `Ticket ID` 用于继续查部署进度。

### 查看 PPE/BOE 环境实例详情和部署单

ENV 实例查询走 `env` 域命令，避免和 `bits env deploy-upgrade` 的升级入口混在一起。先用 `env service list` 按 PSM 定位实例 ID，再用 `env service get` 查看集群、实例与 SCM 版本信息。

```bash
bytedcli env service list \
  --env demo-ppe \
  --standard-env online_cn \
  --search example.service.api

bytedcli env service get \
  --instance-id 123456 \
  --standard-env online_cn
```

文本输出会展示集群 ID、集群名称、机房、主仓 SCM 版本、commit 以及实例列表；JSON 输出保留 ENV API 原始结构，便于脚本提取 `instances[].repo_info[].version`。

部署单查询同样复用 `env ticket`：

```bash
bytedcli env ticket list \
  --env demo-ppe \
  --standard-env online_cn \
  --psm example.service.api

bytedcli env ticket get \
  --ticket-id ticket-123 \
  --standard-env online_cn
```

### 创建研发任务

客户端 BITS 空间的 APP/AOSP 合码请求页面（`/devops/<workspace>/code/create?devops_space_type=client&devops_space_old_id=<app>`）使用 `bits client dev create`。该命令默认 dry-run，只打印将提交给 `/api/gerrit_dev/create_dev` 的 payload；确认后显式加 `--yes` 才真实创建。

```bash
bytedcli bits client dev create \
  --workspace-id 1234567890 \
  --app-id 987654321 \
  --group-name DemoGroup \
  --template app \
  --build-type debug \
  --patch-url "https://ocean-review.byted.org/c/demo/mobile/app/+/123456" \
  --title "bugfix: 修复云同步文案覆盖今天首张截图" \
  --mr-type bug
```

`--workspace-id` 来自 URL 路径 `/devops/<workspaceId>`；`--app-id` 来自 `devops_space_old_id`。`--template app|aosp` 分别对应页面的 `APP研发流程` / `AOSP研发流程`。Patch 模式下，CLI 会从 `--patch-url` 自动派生页面同款 `patch_info`：`repo_name`、`gerrit_number_id`、`gerrit_domain`。如果需要覆盖前端解析结果，也可以显式传 `--gerrit-units` / `--gerrit-units-file`。

BITS 官方 `bits-devops-dev-task` 是创建 Dev Task 的单一事实来源。它通过 `bitscli` 的 prepare/submit 流程统一处理项目与分支识别、模板默认值、工作区状态、用户确认、多项目合并和创建后校验。

创建或新建 Dev Task 时，读取 `references/dev-task.md` 并切换到官方 skill。官方 submit 返回后执行该文档的“代码评审就绪检查”，分别报告 `task_creation` 与 `code_review_readiness`；异步初始化或 Codebase 查询不可用不否定已经成功创建的 Dev Task。不要把下面 Notes 中保留的 `bits develop create` 底层参数当作默认 Agent 工作流；这些参数仅供明确要求 bytedcli 兼容性排障时参考。

### 查询研发任务与工作流模板

```bash
# 解析客户端 change-review 链接中的 workspace/change/contribution 等标识（纯本地）
bytedcli bits devtask parse \
  --url 'https://bits.bytedance.net/devops/12345/change-review/67890?contribution_id=24680&devops_space_type=client&devops_space_old_id=13579'

# 从 change-review 链接读取客户端开发任务详情及 task/change/code-change 三层状态
bytedcli bits devtask get \
  --url 'https://bits.bytedance.net/devops/12345/change-review/67890?contribution_id=24680&devops_space_type=client&devops_space_old_id=13579'

# 已知 change-review path 中的 changeId 时也可直接读取
bytedcli bits devtask get --change-id 67890

# 直接通过 dev_basic_id 查询开发任务详情
bytedcli bits devtask get --dev-basic-id 10001

# 列出开发任务（SMR / devBasicId 维度），支持按角色、状态、关键字筛选
bytedcli bits devtask list --role author --state opened --keyword "demo"
bytedcli bits devtask list --role reviewer --state opened

# 列出待我评审的 Change Card / contribution（contributionId 维度，附 diff 与 review_status）
bytedcli bits devtask review list
bytedcli --json bits devtask review list --max-pages 5
bytedcli bits devtask review list --review-status rejected

# 列出我的开发任务（我创建的 + 我参与的，去重后按创建时间倒序）
bytedcli bits devtask mine

# 展示 CI 检测结果（check nodes、pipeline jobs、gatekeeper、钟馗静态代码检测）
bytedcli bits devtask checks 10001

# 设置/取消自动合入（ready for landing）
bytedcli bits devtask auto-merge 10001
bytedcli bits devtask auto-merge 10001 --unset

# 列出 Dev Task 下的 Change Card 分组
bytedcli bits devtask changes list 10001

# 查看 Change Card 详情及 Codebase MR 绑定
bytedcli bits devtask changes get 60001

# 查看 Change 对应的 Codebase MR diff
bytedcli bits devtask changes diff 60001

# 提交评审（通过 / 驳回 / 评论 / 撤回）
bytedcli bits devtask changes review 60001 --approve
bytedcli bits devtask changes review 60001 --request-changes -b "需要修改"
bytedcli bits devtask changes review 60001 --comment -b "建议"
bytedcli bits devtask changes review 60001 --withdraw

# 行级代码评论（单行/多行）
bytedcli bits devtask changes comment-line 60001 --file "Module/Example.m" --line 42 --body "建议"
bytedcli bits devtask changes comment-line 60001 --file "Module/Example.m" --line 42 --end-line 45 --body "多行建议"

# 标记/解除草稿
bytedcli bits devtask changes draft 60001
bytedcli bits devtask changes draft 60001 --ready

# 最近访问的 Bits spaces；space list 对应 Flux `/api/v1/space/recently_accessed`
bytedcli bits space list --page 1 --page-size 20

# 按关键词搜索 Bits spaces；space search 对应 Flux `/api/v1/space/search`
bytedcli bits space search --keyword demo --page 1 --page-size 20

# 获取 Space 详情；space get 对应 Flux `/api/v1/space/{id}/detail`
bytedcli bits space get --space-id 12345

# 指定 Bits space + 可选 work item / title / user / state / created-at 查询开发任务列表
bytedcli bits develop list \
  --space-id 12345 \
  --work-items "meego 123456" \
  --page 1 \
  --page-size 10

# 按标题模糊匹配、精确相关用户名和初始状态筛选；不自动限定当前用户
bytedcli --json bits develop list --space-id 12345 --title "demo release" --about-user demo.user --state initial --sort created-at-desc

# 只读查看合入执行结果与合入中的开发任务队列，不触发合入
bytedcli --json bits develop merge-info --dev-id 12345

# 搜索 AppCenter 候选项目；与 project list（任务内已关联项目）不同
bytedcli --json bits develop project search --keyword demo --type custom --control-plane cn --limit 20

# 查询某个 devops workspace 下可选的研发任务工作流模板（config 维度，非任务实例维度）
bytedcli bits develop workflow list --workspace-id 4084696834

# 获取某个工作流模板的启用节点详情；对应 Flux POST `/api/v1/dev/config/workflow/get`
bytedcli bits develop workflow get --workflow-id 987654

# 读取任务概览，并显式补充基本资料和成员
bytedcli --json bits develop get --dev-id 123456 --include-basic

# 按明确资源参数做权限预检（spaceId 必须保留为十进制字符串）
bytedcli --json bits develop resource-permission check --body-file ./permission-request.json

# 原生创建请求默认只预览，--yes 提交；不与模板创建参数混用
bytedcli --json bits develop create --body-file ./create-request.json --dry-run
bytedcli --json bits develop create --body-file ./create-request.json --yes

# 读取当前阶段摘要 / 阻塞项 / 下一步提示；stage 支持 dev/test/merge/release 或 raw fixedName
bytedcli bits develop stage get --dev-id 123456 --stage dev

# 读取 Dev Task 或模板变量；模板维度需要同时传 template-id + space-id
bytedcli bits develop variable list --dev-id 123456 --include-system-vars
bytedcli bits develop variable list --template-id 987654 --space-id 12345
```

`bits devtask list --role reviewer --state opened` 与 `bits devtask review list` 不可互换：
前者列 Dev Task（`devBasicId` 维度，适合找任务容器、任务状态和任务下的 changes），后者列
待当前用户评审的 Change Card / contribution（`contributionId` / `changeId` 维度，使用
reviewer contribution 队列，并批量补齐 diff 统计与 review status）。当用户语义是“待我评审 /
waiting for review / 代码评审待处理”时优先使用 `bits devtask review list`；只有要按任务容器
筛选或继续查看某个 Dev Task 内的所有 Change Card 时，才使用 `bits devtask list` 和
`bits devtask changes list <devBasicId>`。

`bits devtask` 专门读取客户端 `/change-review/<changeId>` 页面，不等同于
`bits develop get --dev-id <devBasicId>`。`get` 先调用页面同源的
`/api/v1/dev/task/change/basic` 将 `changeId` 解析为 `devBasicId`，再调用
`/api/smr/v2/dev/info` 读取开发任务摘要和 `state`；结果同时保留 change 状态与代码变更状态。
`parse` 是纯本地解析；`get` 使用 ByteCloud 用户 JWT，不读取 `CLIENT_BITS_TOKEN`，也不依赖
浏览器 SSO 会话。
URL 中存在 `contribution_id` 时会和接口返回值交叉校验，避免读取过期或拼错的链接。

`develop project search` 返回 `projects`、`raw`、`limit` 与 `truncated`，保留项目的 SCM 与控制面详情；达到 limit 时可缩小关键词或增大 limit。控制面和项目类型参数沿用 `project attach` 的语义值。

`bits develop workflow list` 走 `GET /api/v1/dev/config/workflows?workspaceId=<id>`，返回该 workspace 下可用的研发任务工作流（Dev Task template）配置列表，用于创建研发任务前挑选工作流。`--workspace-id` 取自研发任务页面 URL 的 `/devops/<workspaceId>/develop/...`。注意它是 workspace/config 维度，与 `bits develop get` 读取单个任务工作流实例（`devBasicId` 维度）不同。

`bits develop workflow get` 走 `POST /api/v1/dev/config/workflow/get`，请求体固定带 `{workflowId, onlyEnabledNode:true}`，用于读取启用节点版本；不要把它误写成旧的 GET 查询形态。

`develop get --include-basic` 在现有结果中补充 `basic`（完整 basic 接口响应），其中 `basic.data.basicInfo` 为基本资料，`basic.data.members` 为成员。文本模式追加同一份资料。该选项复用已有请求，保留业务身份字段、隐藏凭据；不传时 JSON、文本和读取行为均保持原样。关联 MR、分支和提交 SHA 可从已有 `changes_content` 读取；评审与 CI 详情可从 `gatekeeper list` 的 `checkList` 读取。

`resource-permission check` 检查给定创建参数的资源权限，返回平台的检查结论与详情，不创建任务。

`bits develop create --body/--body-file` 按原生 JSON object 创建任务，保留输入字段，默认预览，`--yes` 才写入；不能与模板创建选项混用。不使用 body 时仍按模板创建。

创建返回 `BITS_CREATE_PARTIAL_SUCCESS` 表示服务端已返回成功，但创建结果或 ID 无法解析；`details` 保留已提交阶段事实和脱敏响应。`BITS_CREATE_OUTCOME_UNKNOWN` 表示传输或响应无法确认结果。两者都应先查任务列表并读回核对，不要盲目重试。明确业务拒绝、HTTP 拒绝及认证错误保留原错误语义；CLI 不自动重试业务创建。

### 运行自测流水线

```bash
bytedcli bits develop quick-run \
  --dev-id 123456 \
  --control-planes CONTROL_PLANE_CN \
  --wait \
  --wait-timeout-sec 600

# canonical project deploy：公开控制面用语义值，不暴露后端数字 enum
bytedcli bits develop project deploy \
  --dev-id 123456 \
  --psm example.service.api \
  --type tce \
  --phase dev \
  --target-branch master \
  --control-plane cn \
  --dry-run

bytedcli bits develop project deploy \
  --dev-id 123456 \
  --psm example.service.api \
  --type tce \
  --phase dev \
  --target-branch master \
  --control-plane cn \
  --yes \
  --wait

# TCC deploy 的 dry-run 还会展示 init、sync、run-pre-check 与精确 pipeline run 计划
bytedcli bits develop project deploy \
  --dev-id 123456 \
  --psm example.service.tcc \
  --type tcc \
  --phase dev \
  --control-plane i18n-bd \
  --dry-run
```

`bits develop quick-run` 是 current-stage 高階編排命令：省略 `--stage` 時读取后端 `currentStage`；省略 `--task` 时只在当前阶段恰好有一个已初始化、可运行的 pipeline task 时自动选择。命令会先检查当前 stage、task ID 与 pipeline/project 解析结果，不会自动执行 stage pass；检查通过后先调用 task start 激活目标 task，再调用 quick-run。`--selected-projects` 表示代码项目 unique ID，只在 HYBRID、WEB、TCE、FAAS、CRONJOB、GECKO、CUSTOM pipeline 中精确匹配，Main 与 TCC pipeline 不参与候选；因此同一 ID 同时存在 TCE 与 TCC 时只选择代码 pipeline。每个 ID 仍必须在请求的 control plane 内解析为唯一代码 project type / pipeline target；缺失、多个代码类型或重复代码 pipeline 都会在写请求前失败。显式选择解析成功后，quick-run 请求不会提交宽泛的 `controlPlanes`，只提交解析出的精确 `pipelineIds`；`--dry-run` 除了展示 `pipelineIds` / `resolvedPipelines`（含类型与控制面），还会在 `quickRun.endpoint/body` 中展示 live 共用的真实请求。显式选择配合 `--wait` 时，CLI 会在提交前记录每条精确 pipeline 的最新 run ID，并只等待提交后出现的新 run；历史 succeeded run 不会被当成本次结果，quick-run 的成功空响应也不会触发重复提交。TCC 必须使用 `bits develop project deploy --psm ... --type tcc --control-plane ...`。显式传入非当前 stage 时会 fail-fast，并提示先在 Bits 完成当前阶段。若 Develop 页仍显示 `Complete development`，Test task 通常尚未初始化，此时先完成 Develop 进入 Test，再重新执行 quick-run。

`bits develop project deploy` 是 `quick-run` 的安全封装：`--phase dev` 默认映射到 `DevDevelopStage` / `DevDevelopStageSelfTestTask`，`--phase test` 默认映射到 `DevGatekeeperStage` / `DevGatekeeperStageIntegrationTestTask`；如果实际 workflow 不同，显式传 `--task`。该命令不会隐式 attach、pass 或 skip，只部署已经存在且精确匹配 `--psm + --type + --control-plane` 的 project，并要求每个 `CodeChange` 代码依赖都有精确匹配 repo / source branch / target branch 的 Change Card；`Version` 依赖使用固定版本，不要求 source branch 或 Change Card。`--target-branch` 省略时按 `master` 校验。`--dry-run` 会读取当前 workflow task，按 `projectUniqueId + projectType + controlPlane` 精确解析，并通过 `pipelineIds` 与 `resolvedPipelines` 展示目标 pipeline ID、project type 和 control plane；零个或多个匹配都会在写请求前失败。对于 `--type tcc`，dry-run 还会展示 `tccEnvironmentInitializations`、`tccVersionSyncs`、`tccPipelinePreChecks` 与 `tccPipelineRuns`。live deploy 会按目标 control plane 初始化 TCC 环境并等待返回的环境票据，再用 `sync_tcc_version` 返回的最新 TCC change item 构造非空配置运行参数；随后执行 run-pre-check，并通过 `/dev/task/pipeline/bc/run` 只启动精确匹配的 project pipeline。该 TCC 路径不会调用 task start 或 Quick Run，因此不会带起同任务的其他 pipeline；任一步失败都会停止后续调用。live deploy 必须显式传 `--yes`。

### 关闭研发任务及其流水线

`bits develop close` 对应 Bits Web 的研发任务关闭动作，走 `POST /api/v1/dev/task/close`，入参是 `devBasicId`，不是 Pipeline 页面的 `pipelineId`。从 develop detail URL 的 `/develop/detail/{devBasicId}` 提取 ID 后传 `--dev-id`；关闭原因用同组写操作通用的 `--reason`。先用 `--dry-run` 核对 payload，再真实执行。

如果页面可以关闭但 CLI 返回 `code=405` / `无权限`，优先排查 `x-jwt-token` 的租户身份是否一致。BITS close 的权限按 JWT 中的 tenant / scope / username 判断；referer、cookie 或 `devops_space_type` 不会把默认 `bytedance` 身份切到页面里的业务租户。需要临时复用页面同租户 JWT 时，用 `BYTEDCLI_USER_CLOUD_JWT="<page x-jwt-token>"` 注入后再执行 close，不要把真实 token 写入聊天、文档或提交记录。

```bash
bytedcli bits develop close \
  --dev-id 123456 \
  --reason "不需要了" \
  --dry-run

bytedcli bits develop close \
  --dev-id 123456 \
  --reason "不需要了" \
  --force
```

### 重跑 / 从失败处重试 / 取消 Pipeline run

`bits pipeline-run cancel` 面向整条 BITS Pipeline run（`runId`），对应 BITS 前端的 run-level cancel（operation `3`）。它不是 jobRun 的 force-skip；需要显式 `--reason`。

`bits pipeline-run rerun` 是 run-level 全量重跑（operation `1`），会让 BITS 按整条 run 的重跑语义重新执行，可能重跑已经成功过的节点。

`bits pipeline-run retry` 是 run-level 从失败处重试（operation `2`，rerun from failure），适合让 BITS 按 run 级失败恢复语义处理 failed jobs。它不是单个原子 / jobRun 的精确重试；只想重试某个失败节点时，用 `bits job-run retry --job-run-id ... --job-uid ...`。

`bits pipeline-run note` 用于给 BITS Pipeline run 写备注，例如发布验证完成后标记 `done`。它只更新 run note，不重跑、不取消、不改变 job 状态。若 BITS 端后续暴露 note 长度限制，应同步补到这里。

以上四个命令都是真实写操作，必须显式传 `--dry-run`（打印 endpoint 与 payload，不调 API）或 `--yes`（真实执行）二选一；都不传时报 `BITS_CONFIRMATION_REQUIRED`，两者同传时报 `BITS_INPUT_ERROR`。

本 skill 不暴露 rollback、force-failed、raw operation 或 batch run operation。

```bash
bytedcli bits pipeline-run cancel \
  --run-id 1158906980866 \
  --reason "superseded by newer run" \
  --dry-run

bytedcli bits pipeline-run rerun \
  --run-id 1158906980866 \
  --dry-run

# 确认 payload 无误后，把 --dry-run 换成 --yes 真实执行
bytedcli bits pipeline-run retry \
  --run-id 1158906980866 \
  --yes

bytedcli bits pipeline-run note \
  --run-id 1158906980866 \
  --note "done" \
  --dry-run
```

### 强制跳过 Pipeline jobRun

`bits job-run force-skip` 面向 BITS Pipeline 的 `jobRunId`，不是 legacy workflow 的 `jobId`。适合在 Pipeline 页面拿到 `jobRunId` / `pipelineRunId` 后跳过 FTF、TeslaX 等阻塞任务。必须显式传 `--dry-run`（预览跳过 payload）或 `--yes`（提交）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`。

```bash
bytedcli bits job-run force-skip \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --space-id 12345 \
  --reason "TeslaX skipped for this launch" \
  --yes
```

### 重试失败的 Pipeline jobRun

`bits job-run retry` 面向 BITS Pipeline 的失败节点重试（operation `2`，BITS failed job rerun），不是重新触发整条 pipeline。适合 Goofy / ByteFaaS / transient 类节点失败后，只重跑当前 failed jobRun。命令默认先调用 `check_op_permission` 预检 `bits.servicePipeline.rerunfailedJobrun` 权限；必须显式传 `--dry-run`（只查看请求体与权限预检）或 `--yes`（真实重试）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`。

```bash
bytedcli bits job-run retry \
  --job-run-id 2787514722 \
  --pipeline-run-id 1158906980866 \
  --space-id 4046305282 \
  --job-uid goofy_deploy-abc123 \
  --dry-run
```

### 继续发布 Pipeline jobRun

`bits job-run continue-release` 用于重放 BITS Pipeline 的 user-defined job action，既支持 `user_confirm` 的通过 / 拒绝，也支持 Canary / 小流量节点的“下一批”等动作。命令会从节点运行时的 `stepInfos.outputs.extra_action` 或 `jobAtom.actions` 自动解析 action，并完整回放其 URL、按钮状态和 body；body 中的 `target` 等路由字段不会被重新推断。多个无法区分的 action 会 fail closed，不会猜选第一项。默认选择“通过”动作，`--reject` 选择“不通过”；标准确认节点解析不到时可用 `--method-name` 手动指定，自动解析不到的非标准 action 再用 `--inputs` 明确传入完整 body。必须显式传 `--dry-run`（核对 payload，不提交 job operation）或 `--yes`（真实执行）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`。

命令会自动把当前登录用户名注入到 `inputs.username`。这是**必需**的：星盾发布质检门（atom `starshield_process_guard`，`method_name=user_define_method`）的服务端直接读 `inputs.username`，缺它会 500 `KeyError:'username'`、把节点打成 failed 并卡住主流水线；变更观测 `ContinueRelease` 等门从鉴权侧取用户名、带上无害。个别需要前端表单状态回传的 user_define gate（如 rds_edit 类原子）需要附带 `display_params`，可通过 `--display-params <json>` 以 JSON 字符串形式注入到 `inputs.display_params`，faas 端会将其作为更新后的表单数据写入 `plugin_context.display_params`。可选 `--check-permission`（需配合 `--space-id`）会先做一次 RBAC 预检，无权时直接报缺 `bits.servicePipeline.customJobrun`，不会盲发写请求；与 `--dry-run` 同时使用时仍执行只读权限预检，但不会提交 job operation。

```bash
bytedcli bits job-run continue-release \
  --job-run-id 2787514722 \
  --pipeline-run-id 1158906980866 \
  --dry-run
```

需要自行提供完整 user-defined operation inputs 时，可传 `--inputs <json>`；该对象会原样作为 `body.inputs`，不会解析或补写字段，也不需要同时传 `--method-name`。

```bash
bytedcli bits job-run continue-release \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --inputs '{"selectionIds":[1,2]}' \
  --dry-run
```

### 启动 waiting manual Pipeline jobRun

`bits job-run start` 用于启动当前明确暴露 operation `1` 的 waiting/manual jobRun，适用于 TCE Canary、TCC 全量发布等由人工启动的节点，不绑定具体 atom 或项目类型。命令会按精确 `jobRunId + pipelineRunId` 读取当前可用操作，只有目标仍包含 operation `1` 才继续；live 总是使用 `jobUid + pipelineRunId + spaceId + username` 做权限预检，不能跳过，并且必须显式传 `--yes`。

先用 `--dry-run --check-permission` 同时核对当前操作、写请求 payload 和权限。该模式只执行读取与权限预检，不会启动节点：

```bash
bytedcli bits job-run start \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --space-id 12345 \
  --dry-run \
  --check-permission
```

确认后，在同一组精确 ID 上用 `--yes` 提交。live 会再次读取当前操作并重新预检权限：

```bash
bytedcli bits job-run start \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --space-id 12345 \
  --yes
```

### 从指定 Pipeline jobRun 重新运行

`bits job-run reschedule` 从调用方指定的 jobRun 开始重新运行后续流水线（operation `7`），不同于失败节点 `retry`（operation `2`）和整条 pipeline run 的 rerun。命令不判断原子类型、仓库类型、泳道或业务阈值；调用方负责选择起点。它以单 jobRun 详情中的 `operations` 为准（批量 operations 可能为空），检查 `bits.servicePipeline.rerunfromspecified` 权限。必须显式传 `--dry-run`（执行只读详情和权限校验）或 `--yes`（只提交一次）二选一。

```bash
bytedcli bits job-run reschedule \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --space-id 12345 \
  --dry-run

bytedcli bits job-run reschedule \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --space-id 12345 \
  --yes
```

输出 `outcome=validated` 表示 dry-run 校验通过；`submitted` 表示平台接受请求，但一次即时回读尚未确认重调度；`observed` 表示同一 jobRun、pipelineRun 和 jobUid 的 `jobRescheduledSeq` 明确递增。`before` / `after` 保留状态、执行序号和起止时间，缺失字段为 `null`；时间或状态变化本身不算重调度证据。`submission=accepted|unknown` 单独说明是否收到明确接收回执，`readback_error` 说明回读失败。它们都不代表节点或下游测试执行成功。

平台明确拒绝时保留拒绝错误；超时、连接中断或响应无法识别时只回读，不重发 operation `7`，也不回退为整条流水线重跑。没有足够回读证据时返回 `BITS_JOB_RUN_RESCHEDULE_OUTCOME_UNKNOWN`（`details.outcome=unknown`），先读取原 jobRun 核对，再决定下一步。提交前的状态复核不是服务端原子锁；若有并发操作，序号递增不能证明由本次请求触发。

### 列出 Pipeline jobRun 可用操作

`bits job-run list-operations` 只读，列出某 pipeline run 下每个 jobRun 当前支持的操作枚举（`1`=start waiting/manual jobRun，`2`=retry failed jobRun，`5`=force-skip，`7`=从指定 jobRun 重新运行，`8`=user_define / continue-release）。批量结果不适合作为 operation `7` 的唯一判断依据；`job-run reschedule` 会读取单 jobRun 详情再决定是否可操作。

```bash
bytedcli bits job-run list-operations \
  --pipeline-run-id 1158906980866 \
  --space-id 4046305282
```

### 导入 TCC 配置到研发任务

```bash
# 先预览自动发现的 region / dir / config 列表
bytedcli bits develop import-tcc-configs \
  --dev-id 123456 \
  --psm example.service.api \
  --control-planes 2,3,4,6 \
  --dry-run

# 只导入指定配置名
bytedcli bits develop import-tcc-configs \
  --dev-id 123456 \
  --psm example.service.api \
  --config-names flow_config,ab_token

# 按 region + dir + config name 精确预览；结果会返回唯一 source_config_id
bytedcli bits develop import-tcc-configs \
  --dev-id 123456 \
  --psm example.service.api \
  --control-planes 2 \
  --config-name demo_config \
  --region Singapore-Central \
  --dir /default \
  --dry-run

# 真实导入复用 dry-run 返回的 source_config_id；保留坐标可同时校验 ID 未漂移
bytedcli bits develop import-tcc-configs \
  --dev-id 123456 \
  --psm example.service.api \
  --control-planes 2 \
  --config-name demo_config \
  --region Singapore-Central \
  --dir /default \
  --source-config-id 2000000000001
```

- 默认按 Dev Task workflow 导入，内部使用 BITS 的 `workflowType=2`。
- 默认控制面是 `2,3,4,6`，会按任务已配置的 region / dir 自动发现可导入配置。
- `--dry-run` 只输出导入计划，不会写入 BITS。
- 精确模式使用完整的 `--config-name + --region + --dir`，匹配 0 个或多个 source config 都会报错；dry-run 的 `selected_configs[].source_config_id` 是后续真实导入的稳定选择凭据。
- 精确坐标的真实导入必须带 `--source-config-id`。也可以只用已知的 `--source-config-id` 直接精确选择；ID 始终按字符串处理，不会经过 JavaScript number 转换。
- `--config-names` 保留批量导入语义，不能与精确模式参数混用。

### 查看研发任务的部署 project 列表

`bits develop project list` 对应研发任务页面的「Project and deployment dependencies」，列出该 Dev Task 已配置的部署 project（TCE / TCC 等）、control plane 与 owner。数据来自 `/dev/task/changes/content` 的 `projects`。

```bash
bytedcli bits develop project list --dev-id 123456
# 也支持从 develop URL 解析 dev id
bytedcli bits develop project list \
  --url 'https://example.com/devops/<workspaceId>/develop/detail/123456/tcc'

# attach 会走 full-snapshot mutation；代码类 project 必须显式传 source branch
bytedcli bits develop project attach \
  --dev-id 123456 \
  --psm example.service.api \
  --type tce \
  --branch feature/demo \
  --target-branch master \
  --control-plane cn \
  --dry-run

# AppCenter 只能按项目名检索、但任务必须挂载精确 projectUniqueId 时，分离查询词与身份
bytedcli bits develop project attach \
  --dev-id 123456 \
  --psm sample-gecko-project-id \
  --lookup-keyword demo-hybrid-project \
  --type hybrid \
  --branch feature/demo \
  --target-branch master \
  --control-plane i18n \
  --dry-run

# detach 需要精确 psm+type，并显式指定 control-plane 或 --all-control-planes
bytedcli bits develop project detach \
  --dev-id 123456 \
  --psm example.service.api \
  --type tce \
  --control-plane cn \
  --delete-change-card \
  --dry-run
```

文本输出为 Type / PSM / Control Planes / Owner 表格；JSON 输出保留 `project_count`、`version_code` 与每个 project 的 `scmDependencies` / `repoDependencies`。要在某个 TCC project 中创建或编辑 draft，用下面的 `tcc-config create/get/update`。

Project attach/detach 使用 `/dev/task/changes/content` 的最新 full snapshot 回写 `/dev/task/changes/edit`，必须保留 `changes`、`projects`、`versionCode` 与未知字段。公共参数 `--type` 使用 `tce,tcc,faas,cronjob,web,hybrid,gecko,custom`；`--control-plane` 使用 `cn,i18n,eu-ttp,us-ttp,i18n-bd`，不要对用户暴露数字 enum。代码项目 attach 必须显式 `--branch`，TCC 不需要 branch；传 `--mr <iid>` 时，CLI 会先确认该 MR 正好属于预期的 repo / source branch / target branch，验证失败不会写入 snapshot。AppCenter 搜索不到 opaque projectUniqueId 时可传 `--lookup-keyword <name>`，它只改变查询词，`--psm` 仍会作为期望 `projectUniqueId` 严格校验；HYBRID 查询返回 GECKO 时还要求每个请求 control plane 恰好一个候选 detail，返回的 GECKO 只作为查询元数据校验，Bits 任务内仍以请求的 HYBRID 类型挂载，不会采用 fuzzy first-result。detach 默认保留 Change Card，如会产生 orphan 必须显式 `--delete-change-card`。

### 管理研发任务 Change Card

```bash
bytedcli bits develop change list --dev-id 123456

bytedcli bits develop change create \
  --dev-id 123456 \
  --change "service=example.service.api,type=TCE,branch=feature/demo,target=master" \
  --dry-run

bytedcli bits develop change bind-mr \
  --dev-id 123456 \
  --change-id 789 \
  --mr 123 \
  --yes

bytedcli bits develop change delete \
  --dev-id 123456 \
  --change-id 789 \
  --dry-run
```

`change create/delete` 也按 full-snapshot 方式回写。创建、删除与 `bind-mr` 的 live mutation 都必须加 `--yes`；删除必须精确 `--change-id`。`bind-mr` 是 `reuse-mr` 的 canonical wrapper，用 BITS MR iid 绑定已有 MR。历史手工调用中，Change Card 已有目标分支时可以继续省略 `--target-branch`；目标分支为空时必须显式传入已核验值，不再猜测 `master`。Dev Task 代码评审就绪流程始终显式传 `--target-branch`，使 dry-run 与 live 调用都执行 Codebase 重校验。已绑定卡片不重复执行 `bind-mr`。

### 环境与门禁

```bash
bytedcli bits develop environment get --dev-id 123456
# 只读查询工作流和项目在创建前的环境默认配置，不保存配置或创建任务
bytedcli bits develop environment config get --body-file environment-query.json
bytedcli bits develop environment lane-update --dev-id 123456 --lane demo --dry-run

bytedcli bits develop environment lane add \
  --dev-id 123456 \
  --from-dev-id 123000 \
  --control-plane i18n-bd \
  --lane demo \
  --dry-run

bytedcli bits develop environment project-config add \
  --dev-id 123456 \
  --from-dev-id 123000 \
  --control-plane i18n-bd \
  --lane demo \
  --project example.service.api:PROJECT_TYPE_TCE \
  --dry-run

bytedcli bits develop environment project-config remove \
  --dev-id 123456 \
  --control-plane i18n-bd \
  --lane demo \
  --project example.service.api:PROJECT_TYPE_TCE \
  --dry-run

bytedcli bits develop environment lane remove \
  --dev-id 123456 \
  --control-plane i18n-bd \
  --lane demo \
  --dry-run

bytedcli bits develop stage pass --dev-id 123456 --stage dev --dry-run
bytedcli bits develop gatekeeper list --dev-id 123456 --stage DevDevelopStage
bytedcli bits develop gatekeeper retry --check-id 123 --dry-run
bytedcli bits develop gatekeeper retry --checkpoint-id 456 --dry-run
bytedcli bits develop gatekeeper skip --check-id 123 --reason "manual skip" --dry-run
bytedcli bits develop gatekeeper approve --check-id 123 --reason "approved" --dry-run
bytedcli bits develop gatekeeper reject --check-id 123 --reason "rejected" --dry-run
```

环境原子命令与 BITS 字段严格对应：`environment lane add/remove` 只操作
`laneConfigs`，`environment project-config add/remove` 只操作 `projectConfigs`。
后者的业务语义是为精确 `PSM + projectType` 配置项目在 develop environment
中的 TCE 集群落点，例如 control plane、PPE lane、zone、virtual cluster、IDC
和资源规格；它从模板复制环境配置，不会创建新的底层 TCE 集群。

`environment config get` 使用独立的 v5 环境管理查询接口，支持互斥的 `--body` /
`--body-file`。输入保留页面请求的 `spaceId`、`workflowId`（正十进制字符串）、
`nodeConfigs` 和含 `projectInfo` 的 `projects` 数组，可保留 `bizScene`、
`geckoCanDeployOnlineChannel` 及其他字段。命令验证 `BaseResp.StatusCode == 0`，
在 JSON `data.raw` 中保留完整 `BaseResp`、`nodeConfigs`、`projectConfigs` 和未知字段；
查询失败或缺少配置数组会报错，不把最近任务的配置替换成工作流默认值。
`add` 从 `--from-dev-id` 模板复制目标控制面的配置，`remove` 只解除精确匹配的
`laneType + laneId` 或 `PSM + projectType + controlPlane` 配置，不删除研发任务、
project 或 release ticket。所有命令都基于最新 full snapshot 合并并保留其它控制面
与未知字段；live mutation 必须加 `--yes`。

环境 API 固定使用 CN BITS endpoint 和 CN user JWT；`--control-plane i18n-bd`
是 payload 维度，不要附加全局 `--site i18n-bd`。`project-config` 当前只支持经过
schema 验证的 `PROJECT_TYPE_TCE`，项目必须用 `PSM:projectType` 精确选择。
`environment lane add` 只在所选控制面的 PPE lane 条目缺失时新增；显式 `--lane`
必须与任务已有的唯一非空 PPE lane ID 一致，若完全没有非空 ID 则可用于新增条目。
已有的所选 lane 条目若 `laneId` 为空或与 `--lane` 不一致，会拒绝而不会覆盖。
`environment lane remove` 和 `environment project-config add/remove` 仍要求目标存在
唯一 CN PPE lane，且 `--lane` 与其一致。

`gatekeeper retry` 必须且只能传一个 `--check-id` 或 `--checkpoint-id`，分别走 `/dev/gatekeeper/check/retry` 与 `/dev/gatekeeper/checkpoint/retry`；live retry / skip / approve / reject 都必须 `--yes`。`stage pass` 支持 `dev,test,merge,release` 语义别名，也接受 raw fixedName；live pass 必须 `--yes`。

### 研发任务关联发布单

```bash
bytedcli bits develop release candidate-list \
  --dev-id 123456 \
  --workspace-id 12345 \
  --page 1 \
  --page-size 100

bytedcli bits develop release bind \
  --dev-id 123456 \
  --release-ticket-id 987654 \
  --dry-run
```

`environment lane-update` 只更新每个 workflow stage 中已经存在的 region-scoped PPE lane type，不会根据全局 `--site` 隐式新增 CN、I18N、EU 或 US 控制面。`--idcs` 的短 IDC 会按现有 lane type 规范化；若任务尚无可更新的 region lane，使用 `environment lane add --control-plane ... --dry-run` 显式添加。

`release candidate-list` 会解析 Dev Task 的 teamFlow，再调用 Flux 已验证的 `/api/v1/cd/team_flow_config/{teamFlowId}/release_tickets`；`release bind` 是 `bind-release` 的单 dev-id canonical wrapper，live bind 必须 `--yes`。

### 创建或编辑研发任务内的 TCC draft 配置

`bits develop tcc-config create` 在已经挂载到 Bits Dev Task 的 TCC project 中创建一个没有 source/online 基线的新草稿；`get/update` 读取或编辑任务中已有的草稿。三者都不会直接修改 source/online TCC 配置，也不会发布配置或启动流水线。命令会实时解析 `dirId`、`storagePsmVersion`、change item 与 draft config id；不要从浏览器抓包复制这些内部 ID 或 token 作为参数。

创建时必须显式传 `--control-plane`、`--region` 和 `--dir`，CLI 会用这组坐标唯一解析目录 ID。读取和更新时目标 TCC draft 由 `-r/--region` 选择；CLI 会从 change item 实时解析 `sourceControlPlane`，并路由到已验证的 CN / I18N / EU-TTP / US-TTP / I18N-BD draft endpoint。CN draft GET 使用 Bits 主域名，其余控制面使用各自 gateway；所有请求都使用控制台相同的 CN user JWT。全局 `--site` 不参与目标 TCC 路由。

```bash
# 新建草稿默认只预览；也可显式写 --dry-run
bytedcli bits develop tcc-config create \
  --dev-id 123456 \
  --psm example.service.api \
  --config-name demo_config \
  --description "Demo config" \
  --control-plane 2 \
  --region Singapore-Central \
  --dir /default \
  --content-file ./demo_config.json \
  --data-type json \
  --dry-run

# 人工核对完整 payload 后才提交
bytedcli bits develop tcc-config create \
  --dev-id 123456 \
  --psm example.service.api \
  --config-name demo_config \
  --description "Demo config" \
  --control-plane 2 \
  --region Singapore-Central \
  --dir /default \
  --content-file ./demo_config.json \
  --data-type json \
  --yes

# 读取已导入的 draft，JSON 输出里包含 content_sha256，可用于后续冲突保护
bytedcli bits develop tcc-config get \
  --dev-id 123456 \
  --psm example.service.api \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --json

# 更新前先 dry-run。--content-file 是完整新配置内容，不支持局部 patch
bytedcli bits develop tcc-config update \
  --dev-id 123456 \
  --psm example.service.api \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --content-file ./demo_config.json \
  --expected-content-sha256 <content_sha256_from_get> \
  --dry-run

# 确认 dry-run 后再真实写入 draft
bytedcli bits develop tcc-config update \
  --dev-id 123456 \
  --psm example.service.api \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --content-file ./demo_config.json \
  --expected-content-sha256 <content_sha256_from_get> \
  --yes
```

- 创建命令固定创建 `static` 配置，`--data-type` 支持 `json`、`yaml`、`string`（默认 `json`）；`--encrypted`、`--with-l4-data`、`--cdn-supported` 均默认关闭。初始内容按 UTF-8 最大 4 MiB。
- 创建命令默认只读预览完整请求 payload；真实写入必须显式传 `--yes`，且不能与 `--dry-run` 同时使用。若同坐标已有任务草稿或 source 配置，会在 POST 前报错。
- 创建接口成功时可能返回空对象；CLI 会继续通过 change-item detail 精确回读 `region + dir + config-name`。若写入结果无法唯一确认，会报 `BITS_TCC_DRAFT_PARTIAL_SUCCESS`，此时先检查任务，禁止盲目重试。
- 更新命令会保留当前 draft 的 tags、schema、validator、config/data type、encryption、L4/CDN 等 metadata，只替换 `content`；可选 `--description` / `--note` 只改对应字段。
- 非 `--dry-run` 必须显式传 `--yes`。如果新内容与当前 draft 完全一致，命令返回 `no_op` 并跳过 PUT。
- 若 `--expected-content-sha256` 与当前 draft 不一致，命令会在 PUT 前报 `BITS_TCC_DRAFT_CONFLICT`，需要重新 `get` 后人工确认。

### 查询或变更 TCC 发布目标

`bits develop tcc-deploy-target` 操作的是某个 TCC change item 的 BOE / PPE / PROD 发布目标，不是挂载或卸载 Project。先用源坐标 `--psm + --source-control-plane + --source-region + --source-dir` 唯一定位 change item；`--source-control-plane` 使用 `cn`、`i18n`、`eu-ttp`、`us-ttp`、`i18n-bd`；仅 `--boe-target` 中的 `control-plane` 额外支持 `boe`（兼容平台目标 ID `5`），`--ppe-target` / `--prod-target` 保持上述五种控制面，例如 `control-plane=boe,region=China-BOE,dir=/default`。BOE 目标控制面不同于来源控制面，不要用 `cn` 代替。

```bash
# 查询当前三类发布目标
bytedcli bits develop tcc-deploy-target get \
  --dev-id 123456 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --source-dir /default

# 只替换 PPE 目标；BOE 和 PROD 保持当前完整快照
bytedcli bits develop tcc-deploy-target update \
  --dev-id 123456 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --source-dir /default \
  --ppe-target 'control-plane=i18n-bd,region=Asia-SouthEastBD,dir=/default' \
  --dry-run

# 核对 dry-run 后，用相同目标真实提交
bytedcli bits develop tcc-deploy-target update \
  --dev-id 123456 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --source-dir /default \
  --ppe-target 'control-plane=i18n-bd,region=Asia-SouthEastBD,dir=/default' \
  --yes

# 每个环境支持多个目标：重复对应 option
bytedcli bits develop tcc-deploy-target update \
  --dev-id 123456 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --boe-target 'control-plane=boe,region=China-BOE,dir=/default' \
  --ppe-target 'control-plane=i18n,region=US-East,dir=/default' \
  --ppe-target 'control-plane=i18n-bd,region=Asia-SouthEastBD,dir=/default' \
  --prod-target 'control-plane=us-ttp,region=US-EastRed,dir=/default' \
  --dry-run

# 清空某一环境必须显式使用 clear flag
bytedcli bits develop tcc-deploy-target update \
  --dev-id 123456 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --clear-ppe \
  --dry-run
```

- `--boe-target`、`--ppe-target`、`--prod-target` 中未出现的环境会原样保留；出现的环境以本次重复 option 的完整集合替换。不能用空列表隐式清空，必须显式传 `--clear-boe`、`--clear-ppe` 或 `--clear-prod`。
- CLI 会先读取最新 change-item full snapshot，再从 TCC region list 解析 `regionName`、`migrateRegionTag`、`dirId` 与开发者权限等内部字段。不要从抓包中复制这些内部字段或任何 Cookie/JWT。
- `update` 必须二选一：`--dry-run` 只输出合并后的完整 PUT payload；`--yes` 真实提交。两者都不传或同时传都会拒绝执行。
- 真实提交后会重新读取 change item 并逐环境核对目标集合。若 PUT 已提交但回读失败或不一致，会报 `BITS_TCC_DEPLOY_TARGET_PARTIAL_SUCCESS`；此时先执行 `get` 检查实际状态，禁止盲目重试。
- 目标集合没有语义变化时返回 `no_op` 并跳过 PUT，同时保留现有目标项中的全部未知字段。

### 查看 Pipeline / Job Run 状态

先用只读历史列表查看一条 Pipeline 最近的运行记录：

```bash
bytedcli bits pipeline-run list --pipeline-id <pipeline-id> --page 1 --page-size 20

# 同时按分支和触发人筛选；多个用户名可用逗号分隔
bytedcli bits pipeline-run list \
  --pipeline-id <pipeline-id> \
  --branch <branch> \
  --trigger-user <username1>,<username2>
```

该命令只发起分页 GET 请求，`--page-size` 支持 1 到 100，并只输出 run ID、序号、状态、触发人、时间和耗时等白名单元数据。BITS 原始响应即使请求 `withoutJob=true` 仍可能包含 Pipeline DSL、jobs、inputs 或 outputs；命令不会透传这些字段，HTTP 调试与错误上下文也会隐藏原始响应体。

- 按分支筛选使用 `--branch <branch>`。
- 按触发人筛选使用 `--trigger-user <username>`，支持逗号分隔。

#### 1) 用 `pipeline` 快速定位当前 run 状态和节点状态

```bash
# 最新一次 run
bytedcli bits pipeline <pipeline-id>

# 指定 run（可选）
bytedcli bits pipeline <pipeline-id> --run-seq <run-seq>

# 只看指定状态的 job（支持 failed / running / awaiting_approval）
bytedcli bits pipeline <pipeline-id> --status failed

# 默认会折叠 hidden jobs（ignored / 尚未执行），并输出 hidden 摘要计数
# 如需展开 hidden jobs 并查看隐藏原因，显式打开
bytedcli bits pipeline <pipeline-id> --run-seq <run-seq> --show-ignored

# 显式补充每个 job 当前支持的 BITS operation enums
bytedcli bits pipeline <pipeline-id> --run-seq <run-seq> --with-job-operations
```

看输出里的两部分即可：

- `Bits Pipeline Latest Run`：整条 pipeline 的当前状态（如 `running (2)` / `failed (9)`）
- `Jobs`：每个 job 的状态与 `Job Run ID`，可快速定位当前卡在哪个 job
- `--status`：只展示匹配状态的 job；排查失败节点优先用 `--status failed`
- `Operations`：仅在 `--with-job-operations` 时展示；常见值 `1`=start waiting/manual jobRun、`2`=retry failed jobRun、`5`=force-skip、`7`=从指定 jobRun 重新运行、`8`=user_define / continue-release。JSON 模式会在每个 job 上补 `operations`，并在 run 响应里保留 `jobOperations` 原始 map，方便脚本消费；operation `7` 仍以单 jobRun 详情为准。
- Pipeline run 原始结构中的凭据字段会递归替换为 `[REDACTED]`，包括嵌套对象/数组里的 JWT、token、authorization、cookie 等字段；不要依赖这些字段的明文值。
- Pipeline 的 `failed` 是整条模板的聚合状态。命令不会根据 job 名称猜测某个环境是否已部分成功；遇到目标 job 成功但其他分支失败时，用 `--status failed` 核对失败节点，并另外读取目标系统实态后再决定是否重试。

隐藏节点分类约定：

- `skipped`：run 中有记录，但状态是 `ignored (1)`（被跳过）
- `not_executed`：pipeline DSL 里定义了 job，但当前 run 还没创建该 job
  - 展开后状态会显示为 `not_started`（run 未结束）或 `not_created`（run 已结束）

#### 2) 用 `job-run` 查看单个节点的详细状态

```bash
bytedcli bits job-run <job-run-id> --pipeline-run-id <pipeline-run-id>
```

重点看：

- `Status`、`Fail Reason`
- `Steps / Atoms`（该 job 内部各 step 的状态）

#### 3) 用 `bytebuild-log` 下钻 ByteBuild / ICM 镜像构建失败

当失败节点是 ICM 镜像构建、ByteBuild、buildkit 等构建类任务时，先从 ICM version、ByteBuild 页面或 `job-run` 输出里拿 ByteBuild record ID，再直接查失败 step 日志：

```bash
# 默认自动选择第一个失败 step，并输出错误摘要和日志尾部
bytedcli bits bytebuild-log <record-id>

# 也可以直接传 ByteBuild URL，CLI 会按 URL 推断 ByteBuild 站点
bytedcli bits bytebuild-log https://example.bytedance.net/bytebuild/log/<record-id>

# 显式指定 step，例如 buildkit-push
bytedcli bits bytebuild-log <record-id> --step buildkit-push

# 查看完整日志
bytedcli bits bytebuild-log <record-id> --no-limit
```

`bytebuild-log` 会先读取 record 中的 `build_steps`，优先选择 `exit_code != 0` 或 failed 状态的 step；如果 ByteBuild 聚合日志为空，会使用 record 里的 Leafboat `origin_url` 继续读取 raw step log。因此 ICM 的 `Icm Arch Job Poll Failed` 一类外层错误，通常能在这里下钻到真实的 Dockerfile/buildctl/go mod 失败原因。

### 基于模板创建流水线

```bash
# 基于模板复制流水线
bytedcli bits pipelines create \
  --space-id 12345 \
  --name "sample pipeline" \
  --template-id 123

# 当模板里的 pipeline.varGroup 不完整时，显式补充 varGroup 字段
bytedcli bits pipelines create \
  --space-id 12345 \
  --name "sample pipeline" \
  --template-id 123 \
  --var-group '{"description":{"value":"sample var group","lang":"zh","texts":{"en":"sample var group"}}}'
```

- `bits pipelines create` 当前是模板模式，`--template-id` 必填。
- `--var-group` 必须是 JSON 对象，只会 merge 到模板里的 `pipeline.varGroup`。
- CLI 不会自动补齐 `pipeline.varGroup.description`；如果 merge 后结构仍不满足后端要求，BITS API 会直接返回错误。

### 查询模板绑定流水线（只读）

模板详情、模板列表和模板绑定流水线是不同资源。需要查询某个模板实际绑定的流水线时，使用独立的 `bound-pipeline list` 子资源命令，不要把它当作 `templates get` 的附加字段，也不要从空间级 `pipelines list` 的首屏结果推断绑定关系：

```bash
# 列出指定模板的全部绑定流水线
bytedcli --json bits pipelines templates bound-pipeline list \
  --template-id <template-id>

# 按绑定流水线名称关键词使用 BITS 服务端搜索
bytedcli --json bits pipelines templates bound-pipeline list \
  --template-id <template-id> \
  --keyword "sample pipeline"
```

- 命令根据模板详情中的所属空间读取绑定关系，不需要额外传 `--space-id`。
- 不传 `--keyword` 时，CLI 会用安全页大小读取完整绑定列表；若页面返回短页、`total` 漂移或无法证明结果完整，会进行有限重扫，最终无法证明完整时返回 `BITS_PIPELINE_DISCOVERY_INCOMPLETE`，不会把部分结果伪装成空成功；若第二次扫描仍未收敛，错误详情会标记 `termination=rescan_diverged`，便于 Agent 区分持续漂移与单页缺失。
- 传 `--keyword` 时，CLI 使用 BITS 的模板绑定流水线服务端搜索接口，并且只分页读取服务端已过滤的命中集；不会先扫描未过滤的全部绑定流水线再在本地按名称筛选。若服务端返回 `total`，CLI 会读到已收齐该总数；未返回 `total` 时以服务端空页作为终止证据。
- 同名或多条命中全部返回；名称不是流水线身份来源，不会自动选择、创建、绑定、运行、更新或删除任何流水线。后续操作前请使用 `bits pipelines get --pipeline-id <pipeline-id>` 显式核验。
- 示例中的 `<template-id>`、`sample-*` 和 `example.*` 均为占位值；不要把真实 PSM、模板/空间 ID、用户信息或内部链接写入脚本或文档。

### 更新流水线 DSL（`bits pipelines set`）

`bits pipelines set` 用来把一份完整 pipeline DSL 整体 PUT 回去，常见用法是 "拉下来 → 局部改 → 写回去"。PUT 是破坏性写操作，必须显式传 `--dry-run`（校验文件与身份后只预览完整 PUT body，不写回、不生成本地备份）或 `--yes`（正式写回）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`：

```bash
# 1. 拉当前流水线；完整 JSON 输出可以直接交给 set
bytedcli --json bits pipelines get <pipeline_id> > /tmp/pipeline.json

# 2. 编辑 /tmp/pipeline.json 里 data.pipeline 的字段，例如改某个 stage 下所有 job 的 runEnv

# 3. 写回；也接受 data.pipeline 纯 DSL、pipeline detail 或完整 PUT body
bytedcli bits pipelines set --pipeline-id <pipeline_id> --file /tmp/pipeline.json --note "调整 stage runEnv" --yes
```

输出（`-j` 模式 `data` 字段）会带：

- `fromVersion` / `toVersion`：本次编辑前后的 `pipelineVersion.version`，可用于校验是否成功 bump
- `diffUrl`：`<bits-origin>/devops/<spaceId>/pipeline/edit_record/diff?pipelineId=<id>&fromVersion=X&toVersion=Y`，给用户在浏览器里 review 改动
- `backupPath`：PUT 之前的当前 DSL 本地备份（`os.tmpdir()/bytedcli/bits-pipeline-backup/<id>-<ts>.json`），出错时可回滚
- `sanitizedI18nPaths`：被自动剥成 `null` 的空 i18n 字段路径列表（见下方 Notes）
- `response`：服务端 PUT 响应原文，含完整 echoed pipeline DSL，可用于二次校验

**注意**：

- PUT 是整体替换。`--file` 里没出现的字段会被服务端清掉，所以必须基于 `bits pipelines get` 的最新 DSL 改，不要自己拼一份小子集。
- `--file` 支持成功的 `bits pipelines get --json` 完整输出、raw API pipeline envelope、pipeline detail、完整 PUT body 或纯 DSL。若输入外层声明了 `pipelineId`，它必须和 `--pipeline-id` 一致；若声明了 `spaceId`，它必须和目标流水线实时返回的 space 一致。任一不匹配都会在备份和 PUT 前拒绝。
- 文本模式（不带 `-j`）只渲染 KV 表，不打印 `response`；要看服务端回显请用 `-j`。

### 更新最新流水线 DSL 字段（`bits pipelines update-field`）

`bits pipelines update-field` 会先拉取最新 pipeline DSL，再按 JSON Pointer 修改指定字段，最后整体 PUT 回 BITS。它适合 release project pipeline 缺少上下文变量、QDE/TCE 原子字段需要小范围修复的 recovery 场景；必须显式传 `--dry-run`（审核 payload，不写回）或 `--yes`（正式写回）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`。

```bash
# 先 dry-run，确认 data.changes / data.body.pipeline
bytedcli --json bits pipelines update-field \
  --pipeline-id <pipeline_id> \
  --set-string /stages/0/jobs/0/inputs/psm=example.psm \
  --set /stages/0/jobs/1/inputs/service_env='"CN"' \
  --note "release project pipeline recovery" \
  --dry-run

# 确认后把 --dry-run 换成 --yes 正式写回
bytedcli bits pipelines update-field \
  --pipeline-id <pipeline_id> \
  --set-string /stages/0/jobs/0/inputs/psm=example.psm \
  --set /stages/0/jobs/1/inputs/service_env='"CN"' \
  --note "release project pipeline recovery" \
  --yes
```

输出（`-j` 模式 `data` 字段）会带：

- `changes`：实际变更的 JSON Pointer、旧值和新值；若没有任何变化会拒绝写回。
- `body`：最终 PUT 请求体，dry-run 时用它审查会发给 BITS 的完整 DSL。
- `backupPath` / `diffUrl` / `fromVersion` / `toVersion`：正式写回后用于回滚和浏览器 review。
- `sanitizedI18nPaths`：和 `pipelines set` 一样，PUT 前会把空 i18n 字段置为 `null`。

**注意**：

- `--set <pointer=json>` 的右侧按 JSON 解析，字符串值需要带 JSON 引号，例如 `--set /x='"CN"'`。
- `--set-string <pointer=value>` 的右侧按普通字符串处理，适合 PSM、branch、service_env 等文本字段。
- JSON Pointer 按 RFC 6901 转义：字段名里的 `/` 写成 `~1`，`~` 写成 `~0`。

### MR 相关

`bits mr create` 是真实写操作（单仓 / 组件发布 / 平台 / multi-host / `create --host-sub` 模式）：必须显式传 `--dry-run`（预览组装好的创建 payload，不调创建 API）或 `--yes`（提交）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`。例外：配置文件驱动的 `bits mr create-host-sub` 尚未接入该门禁，创建前请先人工核对配置文件内容。下列示例为确认后的提交形态。

```bash
# 单仓 MR（使用 Bits OpenAPI，需要 CLIENT_BITS_TOKEN）
bytedcli --json bits mr create \
  --source-branch <source-branch> \
  --target-branch <target-branch> \
  --title <title> \
  --description <description> \
  --type optimize \
  --wip false \
  --remove-source true \
  --yes

# 单仓 MR + 组件发布（合入时发布该仓的一个或多个组件，--publish-component 可重复）
# publishType=auto：后端自动定版本（version 只带 correct:true，参数最省）
bytedcli --json bits mr create \
  --source-branch <source-branch> \
  --target-branch <target-branch> \
  --title "feat: SDK component release" \
  --type package \
  --group-name <group-name> \
  --project-id <gitlab-project-id> \
  --publish-component '{"componentId":39243,"publishType":"auto"}' \
  --publish-component '{"componentId":37010,"publishType":"auto"}' \
  --yes

# 单仓 MR + 组件发布（publishType=sem：显式指定 semver 定版参数）
bytedcli --json bits mr create \
  --source-branch <source-branch> \
  --target-branch <target-branch> \
  --title "feat: SDK component release" \
  --type package \
  --group-name <group-name> \
  --project-id <gitlab-project-id> \
  --publish-component '{"componentId":39243,"publishType":"sem","versionBase":"0.0.103","versionSuffix":"formal","versionUpgradeType":"patch"}' \
  --yes
# 说明：
# - --publish-component 仅作用于普通单仓 create 分支；同时传 --host-sub / --multi-host / --platform 时会走那些分支，--publish-component 被忽略。
# - componentId 等价 component repo_id；不传 --publish-component 即老单仓 MR 行为（wire body 与 master 逐字节一致）。
# - publishType 缺省为 sem；auto 交后端定版本，sem 用 versionBase/versionSuffix/versionUpgradeType（缺省 rc/patch）。

# 单仓 MR + 显式跳过组件发布（针对 ByteDanceAdSDK-Android 这类强制要求组件发布的空间/仓）
bytedcli --json bits mr create \
  --source-branch <source-branch> \
  --target-branch <target-branch> \
  --title "feat: code-only change" \
  --type package \
  --group-name <group-name> \
  --project-id <gitlab-project-id> \
  --skip-auto-publish \
  --yes
# 说明：
# - --skip-auto-publish 让 wire body 在 hosts[0] 上补 skip_auto_publish:true，用于空间强制组件发布的场景（后端否则会以 "repos must be selected" 拒收）。
# - 与 --publish-component 互斥；同时传会报 BITS_INPUT_ERROR。
# - 弱约束仓（后端不强制组件发布）不需要 --skip-auto-publish，直接不传新参数即可，行为与 master 完全一致。

# 查询空间 MR 创建表单字段和默认 custom_fields
bytedcli --json bits mr get-custom-fields \
  --group-name LarkFrontend

# 查询空间 MR 创建表单字段和默认 custom_fields
bytedcli --json bits mr get-custom-fields \
  --group-name LarkFrontend

# 单仓 MR + Meego 绑定（URL 模式，自动解析 projectKey 和 type）
bytedcli --json bits mr create \
  --source-branch feat/demo \
  --target-branch main \
  --title "feat: demo feature" \
  --type feature \
  --group-name LarkFrontend \
  --project-id 552443 \
  --meego "https://meego.larkoffice.com/larksuite/issue/detail/6841440562" \
  --yes

# 单仓 MR + Meego 绑定（ID 模式，需指定 type 和 project-key）
bytedcli --json bits mr create \
  --source-branch feat/demo \
  --target-branch main \
  --title "feat: demo feature" \
  --type feature \
  --group-name LarkFrontend \
  --project-id 552443 \
  --meego 6841440562 \
  --meego-type feature \
  --meego-project-key larksuite \
  --yes

# 平台 MR（单仓客户端 MR，走 Optimus API + JWT 认证，不要求子仓依赖）
# 与默认单仓 MR 的区别：默认单仓 MR 走 BITS OpenAPI；平台 MR 走客户端空间的平台评审流程
# group_name / host project id 在仓库存在 .bits/project_config.json 时自动读取，可省略
bytedcli --json bits mr create \
  --platform \
  --source-branch <source-branch> \
  --target-branch develop \
  --title <title> \
  --type optimize \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id> \
  --yes

# 发起平台 MR 的代码评审：先预览网页面板默认选中的 reviewer，再提交
# --mr-id 用创建平台 MR 返回的 optimus_mr_id
bytedcli --json bits mr code-review start \
  --mr-id <optimus-mr-id> \
  --dry-run

bytedcli --json bits mr code-review start \
  --mr-id <optimus-mr-id> \
  --yes

# 只有需要覆盖网页默认选择时，才手动指定 reviewer / rule
# group_name / project_id 可从 .bits/project_config.json 读取
bytedcli --json bits mr code-review start \
  --mr-id <optimus-mr-id> \
  --reviewer <reviewer-username> \
  --rule develop \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id> \
  --dry-run

# 通过平台 MR 的代码评审
# --mr-id 用创建平台 MR 返回的 optimus_mr_id；它就是 bits `code/detail/<id>` 页面 URL 里的那个数字
bytedcli --json bits mr code-review approve \
  --mr-id <optimus-mr-id> \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id>

# 用平台 MR id 反查底层 Bits-Code (GitLab) MR（project / iid / branches / web URL），便于直接在 GitLab 侧评审或评论
# --mr-id 与 start / approve 一致，都用 optimus_mr_id（= bits `code/detail/<id>` URL 里的数字）
bytedcli --json bits mr code-review gitlab \
  --mr-id <optimus-mr-id> \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id>

# 单独查询发起代码评审前可选的 reviewer 规则（诊断用途）
# --mr-id 与 start 一致，都用 optimus_mr_id（= bits `code/detail/<id>` URL 里的数字）
bytedcli --json bits mr code-review rules \
  --mr-id <optimus-mr-id> \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id>

# 修改当前代码评审中某条规则选中的 reviewer
# 该命令封装 Bits Code Review 页面 API；接口在 BAM 有登记，但不是 BITS OpenAPI。
# 如果 CLI 失败而页面可操作，优先回到页面处理并带 MR/rule 信息反馈。
# --rule-id 用 `bits mr status --mr-id <optimus-mr-id> --json` 返回的 rule_id
bytedcli --json bits mr code-review reviewer-set \
  --mr-id <optimus-mr-id> \
  --rule-id <rule-id> \
  --reviewer <reviewer-username> \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id>

# 多主仓 MR（使用 Optimus API + JWT 认证，适用于 KMP 跨端场景）
# 兼容旧的单 host 输入：--host-* + --mr-dependency
bytedcli --json bits mr create \
  --multi-host \
  --source-branch <source-branch> \
  --target-branch develop \
  --title <title> \
  --type feature \
  --group-name <host-group-name> \
  --host-project-id <host-repo-bits-project-id> \
  --host-source <host-source-branch> \
  --host-target develop \
  --mr-dependency '{"projectId":<sub-repo-bits-project-id>,"sourceBranch":"<branch>","targetBranch":"develop"}' \
  --component '{"hostProjectId":<host-project-id>,"componentId":<kmp-component-id>}' \
  --custom-fields '{"risk_level":"low"}' \
  --meego "https://meego.larkoffice.com/<project-key>/story/detail/<id>" \
  --app-id <bits-space-app-id> \
  --cloud-id <bits-space-cloud-id> \
  --yes

# 高级多 host 输入：重复传 --host，每个 host 自带私有 mrDependencies；顶层 --mr-dependency 继续作为公共子仓依赖保留
bytedcli --json bits mr create \
  --multi-host \
  --source-branch <source-branch> \
  --target-branch develop \
  --title <title> \
  --type feature \
  --group-name <host-group-name> \
  --mr-dependency '{"projectId":300,"sourceBranch":"feature/public-sub","targetBranch":"develop"}' \
  --host '{"projectId":100,"sourceBranch":"feature/host-a","targetBranch":"develop","mrDependencies":[{"projectId":200,"sourceBranch":"feature/sub-a","targetBranch":"develop"}]}' \
  --host '{"projectId":101,"sourceBranch":"feature/host-b","targetBranch":"develop","mrDependencies":[{"projectId":201,"sourceBranch":"feature/sub-b","targetBranch":"develop"}]}' \
  --custom-fields '{"risk_level":"low"}' \
  --yes

# 主子仓 MR（高级：直接传参模式，BITS OpenAPI）
> 不推荐作为主路径。主子仓 + 多子仓场景优先使用下文的“配置文件驱动（`bits mr create-host-sub`）”，参数更少且不易配错。
> 直接传参模式适用于需要手动拼装 payload 或临时验证接口字段的场景。

bytedcli --json bits mr create \
  --host-sub \
  # 注意：bits mr create 会校验 --source-branch（即使 host-sub 下宿主 source 通常为空）
  --source-branch <placeholder-branch> \
  --target-branch develop \
  --title "feat: SDK component upgrade" \
  --type feature \
  --group-name <host-group-name> \
  --host-project-id <host-repo-gitlab-project-id> \
  --host-source "" \
  # 单子仓：--sub-component 可以省略 subRepoKey
  --sub-dependency '{"projectGitlabId":<sub-repo-gitlab-project-id>,"sourceBranch":"<branch>","targetBranch":"develop"}' \
  --sub-component '{"hostProjectId":<host-project-id>,"componentId":<component-id>,"publishType":"sem","versionBase":"1.0.0","versionSuffix":"rc","versionUpgradeType":"patch"}' \
  --sub-component '{"hostProjectId":<host-project-id>,"componentId":<component-id-2>,"versionBase":"2.1.0"}' \
  --meego "https://meego.larkoffice.com/<project-key>/story/detail/<id>" \
  --wip \
  --yes

# 多子仓直接传参模式：每个 --sub-component 必须显式带 subRepoKey（=目标 --sub-dependency 的 projectGitlabId 字符串）
bytedcli --json bits mr create \
  --host-sub \
  --source-branch <placeholder-branch> \
  --target-branch develop \
  --title "feat: multi-SDK upgrade" \
  --type feature \
  --group-name <host-group-name> \
  --host-project-id <host-repo-gitlab-project-id> \
  --host-source "" \
  --sub-dependency '{"projectGitlabId":5275,"sourceBranch":"feature/sdk-a","targetBranch":"develop"}' \
  --sub-dependency '{"projectGitlabId":5276,"sourceBranch":"feature/sdk-b","targetBranch":"develop"}' \
  --sub-component '{"subRepoKey":"5275","hostProjectId":<host-project-id>,"componentId":1335,"versionBase":"1.0.0"}' \
  --sub-component '{"subRepoKey":"5276","hostProjectId":<host-project-id>,"componentId":2222,"versionBase":"2.0.0"}' \
  --yes

# 说明：
# - --host-target 用于 multi-host 场景覆盖宿主 target；host-sub 场景一般只需 --target-branch。
# - --sub-component 缺省 versionBase 时，CLI 默认会按 componentId 自动解析基线版本并回填（取后端 data.versions[0]，
#   对齐 bits component get-base-versions / Bits 组件平台 UI 默认选中；prerelease 如 -alpha.x / -rc.x 也会被采用），
#   --json 输出会新增 auto_version_base 字段（含 enabled / status / resolved / skipped / user_provided）；
#   status 取值：disabled（关闭自动补齐）、not_needed（无组件需要补齐 / 用户已全部显式给出）、
#   fully_resolved（全部由 CLI 自动补齐）、partial_resolved（部分由用户显式提供、其余由 CLI 自动补齐）；
#   user_provided 列出本次调用中用户显式带了 versionBase 的 componentId 集合。
#   如需关闭自动补齐，加 --auto-version-base false。
# - --sub-component.componentId 等价于 component repo_id，可直接复用 bits component get-base-versions 的 --repo-id。
# - 多 --sub-dependency 场景下，每条 --sub-component 必须显式声明 subRepoKey（等于目标 sub-dependency 的 projectGitlabId 字符串），
#   否则 CLI 立即抛 BITS_INPUT_ERROR 并在 hint 中列出 availableSubRepoKeys；单子仓场景可省略。
#   兼容别名：subRepoKey / sub_repo_key / subProjectGitlabId / sub_project_gitlab_id 等价。

bytedcli --json bits mr search --state opened
bytedcli --json bits mr mine --author <user>
# status 的 --json 输出含 meego_features 字段：MR 关联的 Meego 工作项列表
#   （task_id / task_title / task_url / task_type），用于反查 MR 绑定了哪些需求/缺陷。
bytedcli --json bits mr status --mr-id <mr-id>
bytedcli --json bits mr diff --mr-id <mr-id>
bytedcli --json bits mr diff --mr-id <mr-id> --patch --file "src/path/to/file.ts"
bytedcli --json bits mr review-status --mr-id <mr-id>
bytedcli --json bits mr qa-status --mr-id <mr-id>
bytedcli --json bits mr approve --mr-id <mr-id>
bytedcli --json bits mr disapprove --mr-id <mr-id>
bytedcli --json bits mr remind-review --mr-id <mr-id>
bytedcli --json bits mr remind-qa --mr-id <mr-id>

# 为已有 MR 添加 reviewer
bytedcli --json bits mr reviewer add \
  --mr-id <mr-id> \
  --reviewer alice --reviewer bob \
  --role RD \
  --is-force \
  --reason "manual_add"

# 从已有 MR 移除 reviewer
bytedcli --json bits mr reviewer remove \
  --mr-id <mr-id> \
  --username alice

# 查询 MR 的 reviewer 列表
bytedcli --json bits mr reviewer info --mr-id <mr-id>

# 为 MR 创建 Lark 群聊
bytedcli --json bits mr chat create --mr-id <mr-id>

# 向 MR 的 Lark 群聊中添加用户
bytedcli --json bits mr chat add \
  --mr-id <mr-id> \
  --username alice \
  --member-type reviewer

# 从 MR 的 Lark 群聊中移除用户
bytedcli --json bits mr chat remove \
  --mr-id <mr-id> \
  --username alice

# 解散 MR 的 Lark 群聊
bytedcli --json bits mr chat dismiss --mr-id <mr-id>

# 查询 MR 产物包（package groups）
bytedcli --json bits mr packages --project-id <project-id> --mr-iid <mr-iid>
bytedcli --json bits mr packages --project-id <project-id> --mr-iid <mr-iid> --limit 10 --last-id <last-id>

# 查询 MR 下各子仓组件发布产物（host MR 自动展开为所有子仓 MR 后聚合）
# 既可传主仓（host）MR id，也可直接传子仓（sub）MR id；host MR 会通过 relation/list
# 自动展开为所有子仓 MR 并并发查询，sub MR 直接单查。
# 文本模式按子仓维度聚合相同字段为 Summary（status / version / version_base /
# release_info / log_url / pod_source / tt_repos），组件表只保留身份列。
bytedcli --json bits mr publish-records --mr-id <host-or-sub-mr-id>

# 可选：仅在已知子仓 group_name / project_gitlab_id 时补传，便于强制走特定 host
bytedcli --json bits mr publish-records \
  --mr-id <host-or-sub-mr-id> \
  --group-name <host-group-name> \
  --project-id <host-project-gitlab-id>

# 更新已有 MR：标题 / 描述 / WIP 状态 / 自定义字段
# 标题不要带 [Feature] / [Optimize] / [Bug Fix] 前缀，Bits 按 MR type 自动补
# 描述默认同步写入绑定的 Codebase MR 描述；加 --no-sync-codebase 只改 Bits 侧
bytedcli --json bits mr update \
  --mr-id <mr-id> \
  --title "<new title>" \
  --description "<new description>" \
  --custom-fields '{"CASE_STUDY":"https://example.com/cs/123"}'

# 给已有 MR 追加绑定 Meego 工作项（URL 模式，自动解析 projectKey 和 type）
# 与 `mr create --meego` 等价，但作用在已经创建好的 MR 上
bytedcli --json bits mr update \
  --mr-id <mr-id> \
  --meego "https://meego.larkoffice.com/larksuite/issue/detail/7310890683"

# 注意 type 语义：Meego URL 里的 story=需求、issue=缺陷；
# Bits bind 接口里 task_type=issue 表示需求，task_type=bug 表示缺陷。

# 给已有 MR 追加绑定 Meego 工作项（ID 模式，需指定 type 和 project-key）
bytedcli --json bits mr update \
  --mr-id <mr-id> \
  --meego 7310890683 \
  --meego-type bug \
  --meego-project-key larksuite

# 多仓合码：查询完整 workflow / job 列表
bytedcli --json bits client workflow pipeline from-mr --mr-id <mr-id> --include-dependencies

# 查询 MR 关联的 pipeline history
# 默认使用后端返回范围；需要全量历史记录时加 --all
bytedcli --json bits client workflow pipeline list --mr-id <mr-id> --all

# 只读查询 MR 上的评审评论（thread 列表）
# 定位符二选一：--mr-id（code/detail/<id> 里的数字）或 --url（完整 code/detail 链接）
bytedcli --json bits mr comment list --mr-id <mr-id>
bytedcli --json bits mr comment list --url https://bits.bytedance.net/devops/<space>/code/detail/<mr-id>

# 过滤：--status / --author / --path / --outdated 全部是客户端过滤
# 后端一次性返回该 MR 的全部 thread，不支持分页也不接受过滤参数，
# 因此本命令组不提供 --page / --page-size。
# 注意 --path 匹配 thread 的文件路径，任何 --path 取值都会同时排除 MR 级评论。
bytedcli --json bits mr comment list --mr-id <mr-id> --status open
bytedcli --json bits mr comment list --mr-id <mr-id> --author <username> --path src/

# 状态词表：对外只用 open | resolved | closed，默认 --status all。
# JSON 输出里 status 是对外值，raw_status 保留 Codebase thread 原值。

# --limit 是客户端截断，默认 50；JSON 输出会带 limit 与 truncated，
# truncated:true 表示结果不完整，需要调大 --limit 或收紧过滤条件。
bytedcli --json bits mr comment list --mr-id <mr-id> --limit 200

# 默认丢弃 Positions[]（rebase 追踪历史）与 TruncatedDiff，这两项占原始响应约 80%；
# 需要 diff 上下文时再加 --include-diff。
bytedcli --json bits mr comment list --mr-id <mr-id> --include-diff

# 查看单个 thread 的完整评论内容
# --thread-id 必须属于 --mr-id / --url 指定的这个 MR；
# 传入同仓库其他 MR 的 thread-id 会按 not found 处理，不会跨 MR 返回数据。
bytedcli --json bits mr comment get --mr-id <mr-id> --thread-id <thread-id>
```

`bits mr comment` 只读。写评论请用 `bytedcli codebase mr comment create`。数据本身来自 Codebase thread RPC（BITS `list_threads` 是它的透传代理），bytedcli 侧只做 BITS `mr_id` -> Codebase `repo_id` + merge request 的 ID 桥接。没有文件路径的 thread 是 MR 级整体评论，文本模式渲染为 `(MR-level)`。

`bits mr diff` 与 `bits mr comment` 需要本地可用的 Codebase 登录态；优先复用 `bytedcli auth login` 的 SSO 会话，也支持 `bytedcli codebase auth config-add-pat <pat>`。`bits mr comment` 需要两套凭据：Bits OpenAPI token 用于 BITS `mr_id` -> Codebase `repo_id` 的 ID 桥接，Codebase 登录态用于读取 thread 数据。

### 主子仓 MR — 配置文件驱动（create-host-sub）

适用于单宿主仓 + 多子仓的客户端 SDK 组件发版场景：从多个子仓收集 `.host-sub-mr.json`，自动拉取组件版本并创建主子仓 MR。

**前置条件**：`CLIENT_BITS_TOKEN` 已设置，且各仓库 source branch 已 push 到远端。

**推荐目录组织**：

- 宿主仓（例如 `commerce_demo`）根目录：`.host-sub-mr.json` 只放 `host`
- 每个子仓根目录：`.host-sub-mr.json` 只放 `sdk`

```json
// 宿主仓 .host-sub-mr.json
{
  "host": {
    "group_name": "commercial_sdk_demo",
    "project_gitlab_id": 414226,
    "target": "develop",
    "testing_group_name": "commercial_sdk_demo"
  }
}
```

```json
// 子仓 .host-sub-mr.json
{
  "sdk": {
    "display_name": "开屏 SDK",
    "sub_project_gitlab_id": 5275,
    "sub_target": "develop",
    "repo_ids": [1335, 45928, 40861],
    "publish_type": "sem",
    "version_suffix": "rc",
    "version_upgrade_type": "patch"
  }
}
```

**执行示例**：

```bash
# 多子仓联合发版：从多个子仓收集配置，合并发起一个 MR
# --sub-repo 支持 path:branch 格式为每个子仓指定独立分支
bytedcli --json bits mr create-host-sub \
  --host-config /path/to/host-repo \
  --sub-repo /path/to/splash_ad_sdk:feature/splash-v2 \
  --sub-repo /path/to/ad_base_sdk:feature/ad-base-v3 \
  --host-source release/1.0 \
  --title "feat: 联合升级" \
  --type feature

# 各子仓同分支：用 --sub-source 统一指定（此时每个 --sub-repo 不必带 :branch）
bytedcli --json bits mr create-host-sub \
  --host-config /path/to/host-repo \
  --sub-repo /path/to/splash_ad_sdk \
  --sub-repo /path/to/ad_base_sdk \
  --sub-source feature/xxx \
  --host-source release/1.0 \
  --title "feat: 联合升级" \
  --custom-fields '{"risk_level":"low"}'
```

**配置文件格式**（`.host-sub-mr.json`）：

- **子仓独立格式（推荐）**：`{ "sdk": {...} }`
- **宿主仓独立格式（推荐）**：`{ "host": {...} }`
- **全量格式（兼容）**：`{ "host": {...}, "sdks": { "sdk_name": {...} } }`

**关键选项**：

| 选项                         | 说明                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| `--host-config <path>`       | 宿主仓目录或配置文件路径（必填）                                                            |
| `--sub-repo <path[:branch]>` | 子仓目录路径，可带分支 `path:branch`，可重复（必填）                                        |
| `--sub-source <branch>`      | 子仓统一分支（当不是每个 --sub-repo 都带 :branch 时必填）                                   |
| `--host-source <branch>`     | 宿主仓源分支（可选）                                                                        |
| `--title <text>`             | MR 标题（必填）                                                                             |
| `--type <type>`              | MR 类型：feature / bug / optimize / merge / lab / package / patch / slardar（默认 feature） |
| `--meego <url>`              | 绑定 Meego 工作项，可重复                                                                   |
| `--meego-type <type>`        | Meego 工单类型：bug / feature（当 --meego 传纯 ID 时必填）                                  |
| `--meego-project-key <key>`  | Meego 项目标识（当 --meego 传纯 ID 时必填）                                                 |
| `--custom-fields <json>`     | 空间自定义字段 JSON（可选，透传给 `openapi/merge_request/create` 的 `custom_fields`）       |
| `--no-wip`                   | 不标记 WIP                                                                                  |
| `--no-remove-source`         | 合并后保留 source 分支                                                                      |

**成功输出**：返回 `mr_link`（MR 链接），用于后续流转/通知。

### 主子仓 MR — 追加子仓（add-sub）

适用于已经创建好的主子仓 MR（`mr create --host-sub` 或 `mr create-host-sub`），后续再追加一个新的子仓 MR 依赖。**一次只追加 1 个子仓**；多个子仓需循环调用。

不承载 Meego 绑定；若需要补 Meego 关联请用 `bits mr update --meego ...`。

```bash
# 追加 1 个子仓到已有主子仓 MR
bytedcli --json bits mr add-sub \
  --mr-id 12345 \
  --host-project-id 414226 \
  --group-name commercial_sdk_demo \
  --sub-dependency '{"projectGitlabId":2001,"sourceBranch":"feature/demo","targetBranch":"develop"}' \
  --sub-component '{"componentId":1335}'

# --host-project-id 可省略：handler 会按 --mr-id 反查主 MR 的 project_id
bytedcli --json bits mr add-sub \
  --mr-id 12345 \
  --group-name commercial_sdk_demo \
  --sub-dependency '{"projectGitlabId":2001,"sourceBranch":"feature/demo","targetBranch":"develop"}'
```

**关键选项**：

| 选项                                | 说明                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| `--mr-id <id>`                      | 已存在的主子仓 MR ID（必填）                                                                     |
| `--group-name <name>`               | 主仓 Bits 空间 group_name；缺省时读取 `.bits/project_config.json`                                |
| `--host-project-id <id>`            | 主仓 GitLab project id；省略时按 `--mr-id` 反查                                                  |
| `--sub-dependency <json>`           | 待追加的子仓依赖 JSON（**恰好 1 条**）。必须包含 `projectGitlabId / sourceBranch / targetBranch` |
| `--sub-component <json>`            | 该子仓内的组件升级 JSON，可重复；`hostProjectId` 可省略（fallback 到 `--host-project-id`）       |
| `--auto-version-base [true\|false]` | 缺省 `true`：缺 `versionBase` 的组件自动拉取基线版本                                             |

**成功输出**：返回 `{ host_sub_append: true, mr_id, appended_sub: { project_gitlab_id, source_branch, target_branch, components_count, status: "success" } }` 以及原始响应。

### 主子仓 MR — 删除子仓（remove-sub）

适用于已经创建好的主子仓 MR，后续要把其中某一个子仓 MR 依赖从主 MR 上摘除，而不关闭整个主 MR。**一次删除 1 个子仓**；多个子仓需循环调用（与 `add-sub` 对称）。

不承载组件发布 / auto-version-base / meego（删除动作无组件/需求语义），不需要传 `--group-name` / `--host-project-id`。

```bash
# 从主子仓 MR 8204342 上删除子 MR（子仓 project=249454，子 MR iid=81）
bytedcli --json bits mr remove-sub \
  --mr-id 8204342 \
  --sub-project-id 249454 \
  --sub-iid 81
```

**关键选项**：

| 选项                    | 说明                                                           |
| ----------------------- | -------------------------------------------------------------- |
| `--mr-id <id>`          | 已存在的主子仓 MR ID（必填）                                   |
| `--sub-project-id <id>` | 待删除子仓 GitLab project id（必填）                           |
| `--sub-iid <iid>`       | 待删除子 MR 在子仓 GitLab project 内的 iid（必填，非主 MR id） |

**成功输出**：`{ host_sub_remove: true, mr_id, removed_sub: { project_id, iid, status: "success" } }` 以及原始响应。

**失败路径**：

- 后端 `code !== 200` 或 `data.success !== true` → 抛 `BITS_API_ERROR`，`details.removed_sub` 与 `details.raw_response` 便于定位。
- `--mr-id` / `--sub-project-id` / `--sub-iid` 任一缺失或非数字 → `BITS_INPUT_ERROR`，不发 HTTP 请求。

### Component 相关

提供客户端组件（如 iOS/Android 模块、跨端库等）在 Bits 平台的生命周期管理、升级与查询能力。支持的核心功能包括：

- **组件库基础查询**：根据 ID、名称或搜索条件查找组件库信息。
- **组件版本与升级管理**：执行组件升级 (`upgrade-repo`)、查询组件基准版本以及自动获取下个合理语义化版本号。
- **升级历史追溯**：根据 ID 或版本号获取某次升级的详细信息及关联构建任务流。
- **标签与关联检索**：查询平台组件标签、特定组件绑定的标签，以及获取目标组件的相关依赖和关联组件信息。

详情和所有命令用例请参考专属文档：

- `references/component.md`

### 应用中心 — 创建 Gecko PSM 并绑定已有 channel

`bits appcenter gecko create` 在 Bits 应用中心创建 Gecko 混合应用（Gecko PSM）并**绑定已有的 Gecko channel**，对应应用中心 `POST /api/v2/appcenter/creation/create_component`（`componentType=hybrid_component`），认证走 ByteCloud JWT（与 `bits component`/`bits mr` 的 OpenAPI token 链路不同，无需 Bits OpenAPI token）。

```bash
# 最小创建：仅必填 --name
bytedcli bits appcenter gecko create --name demo-gecko-psm
# 创建并绑定已有 channel（--channels 接收 JSON 数组）
bytedcli bits appcenter gecko create \
  --name demo-gecko-psm \
  --framework lynx \
  --node-id 12345678 \
  --space-id 87654321 \
  --git-full-name demo/demo_web_monorepo \
  --scm-name demo/demo/lynx_cards \
  --channels '[{"region":"tt-row","deploymentId":"7","channelId":"111111"},{"region":"us-ttp","deploymentId":"1","channelId":"222222"}]'
```

- `--name`：必填，Gecko PSM / 组件名称。
- `--framework`：框架方案 key（对应 `solutionKey`），默认 `lynx`。
- `--node-id`：服务树节点 ID；`--space-id`：关联空间 ID。
- `--git-full-name`：Git 仓库全名；`--scm-name`：SCM 名称。
- `--no-with-exist-scm` / `--no-with-exist-codebase`：默认复用已有 SCM 与 Codebase，加 `--no-*` 可关闭。
- `--is-mono` / `--mono-sub-path`：mono repo 及其子路径。
- `--channels`：JSON 数组，每项必填 `region`、`deploymentId`、`channelId`（要绑定的已有 channel 的 region 维度 id）；可选 `withExistChannel`（默认 `true`）。绑定多个 region/deployment 时各写一项。
  - `region` 既可传应用中心 provider key（`tt-row`/`tt-eu`/`tx`），也可直接传 Gecko channel 元数据里的别名（`row`/`eu-ttp`/`us-ttp`），命令会自动归一化（`row→tt-row`、`eu-ttp→tt-eu`、`us-ttp→tx`）。CN 暂未内置映射，需自行确认 CN 的 provider region key 后直接传规范值。
- 成功返回创建记录 ID（`id`，后端未返回时为 `null`，同时透出原始 `raw`）。

#### 易踩坑（实测沉淀）

- **`channelId` 取的是 region 维度的 `channelRegionId`，不是 channel meta id（平台无关原则）**：`--channels` 每项的 `channelId` 必须是某个 region+deployment 维度的 `channelRegionId`；一个 channel 名在 N 个 region × M 个 deployment 下会有 N×M 个 `channelRegionId`，每个都要作为一项写进 `--channels`（例如 3 region × 4 deployment = 12 项）。误把 channel meta id（一个 channel 名通常只有几个）当 `channelId` 传是最常见错误。
  - **TikTok Gecko 取数示例（仅适用于 TikTok 平台的 channel）**：先 `tiktok-gecko channel list --name <channel>` 找到 channel（其 `metaIdList` 是 channel meta id，**不能**直接用），再对每个 meta id 调 `tiktok-gecko channel get --channel-id <metaId>`，从 `detail.metaData.regions[].data[].channelRegionId` 逐个取值。
  - **其它 gecko 平台**（CN gecko 等）的 channel 不走 `tiktok-gecko` 命令，需从对应平台来源取 `channelRegionId`，且 region 需自行确认 provider region key（CLI 未内置 CN 映射）。
- **返回的 `id` 是创建记录 ID，不是最终 Gecko PSM / componentId**：不能用它拼 `hybrid_component:gecko_<id>` 去查 `component_summary`（会 not found）。最终 Gecko PSM 由后端异步生成，需稍后在应用中心按 `--name` 查看。
- **create 不幂等**：相同 `--name` 重复执行会创建多个组件，后端不报冲突；CLI 暂无 update/delete，重复或参数填错（如漏 `--space-id`/`--node-id`）只能去应用中心页面手动改/删。
- **参考组件的 `--space-id`/`--node-id` 无法从 `component_summary` 获取**：该接口不返回 `nodeId`、`spaceId` 常为空，需从应用中心组件页 / 服务树侧取真实值再传入。

### Client 子域

`bits client` 提供七组客户端子域：

- `bits client workflow`
  - workflow job、pipeline template、开发任务流水线
- `bits client integration`
  - 集成区版本、合入队列、封版报告、版本群
- `bits client bm`
  - 按精确版本查询 RD 值班负责人：已创建排班优先，无匹配再查未来预测排班（用户 JWT，无需浏览器）
- `bits client calendar`
  - 版本日历 workspace、event、segment、mark
- `bits client release-record`
  - 客户端版本发布记录（官方 / 灰度 / 技术灰度版本、update version、发布时间）
- `bits client package`
  - 独立打包：构建配置、打包任务、产物下载（走 SSO 会话，不需要 Bits OpenAPI token）
- `bits client release-workflow`
  - 客户端版本发布DAG：读取阶段/节点状态，精确选择并触发一个既有节点；默认dry-run，已运行/成功/跳过时不重复触发
  - 版本发布页Web API需要浏览器SSO会话；缺失时执行`bytedcli --site cn auth login --session`

详情和所有命令用例请参考专属文档：

- `references/client.md`

其中 workflow 相关 OpenAPI 已经统一收口到 `bits client workflow`，不再单独保留根级 `bits workflow` 入口。

### AI 用例生成

从飞书 PRD 文档触发 AI 测试用例生成（异步，结果 5-15 分钟后在 Bits 平台查看）。

```bash
bytedcli bits case generate \
  --devops-id <space-id> \
  --dir-id <dir-id> \
  --prd-link "https://bytedance.larkoffice.com/docx/example" \
  --case-title "example-feature"

# 关闭严格模式 + 补充文档
bytedcli bits case generate \
  --devops-id <space-id> \
  --dir-id <dir-id> \
  --prd-link "https://bytedance.larkoffice.com/docx/example" \
  --no-strict-mode \
  --supplement-links "https://bytedance.larkoffice.com/docx/tech-doc"
```

### 用例上传

使用 Markdown 内容上传测试用例，支持指定文件内容或文件地址；未传 `--case-id` 时将新建用例集。需要提供 `--model-name`（联系 lixihe.lj 获取）。默认 `isStrictMode=false`；需要严格模式时显式传 `--strict-mode`。

```bash
bytedcli bits case upload \
  --devops-id <space-id> \
  --dir-id <dir-id> \
  --case-id <case-id> \
  --case-title "example-feature" \
  --model-name "example-model" \
  --md-content "# Title\\n- item"
bytedcli bits case upload \
  --devops-id <space-id> \
  --dir-id <dir-id> \
  --case-title "example-feature" \
  --model-name "example-model" \
  --strict-mode \
  --md-file ./example.md
```

### XMind 用例导入

将本地 `.xmind` 文件导入到 Bits 手动用例目录；未传 `--case-title` 时使用文件名作为用例集标题。不传任何严格校验参数时默认启用 Bits 的严格 XMind 模板校验；需要兼容非标准模板时可传 `--no-strict-mind-version`。

```bash
bytedcli bits case import-xmind \
  --devops-id <space-id> \
  --project-id <project-id> \
  --dir-id <dir-id> \
  --xmind-file ./example.xmind \
  --case-title "example-feature" \
  --remark "需求测试" \
  --custom-fields '{}' \
  --related-requirement-file ./requirement.json
```

`requirement.json` 示例：

```json
[
  {
    "RequirementSource": "meego",
    "RequirementLink": "https://meego.larkoffice.com/demo/story/detail/1234567890",
    "RequirementId": 1234567890,
    "RequirementTitle": "demo-story",
    "project": "demo-project-id",
    "projectName": "demo-project",
    "projectSimpleName": "demo",
    "WorkItemTypeKey": "story",
    "RequirementOther": "{\"project\":\"demo-project-id\",\"projectName\":\"demo-project\",\"WorkItemTypeKey\":\"story\"}"
  }
]
```

常用参数：

- `--project-id` 对应 Bits 用例页面 URL query 中的 `projectId`，会作为上传表单的 `ProductId`。
- `--devops-id` 对应 Bits URL path 中 `/devops/<space-id>`，会作为 `x-onesite-space-id`。
- `--dir-id` 对应 Bits 用例页面 URL query 中的 `dirId`，会作为上传表单的 `DirId`。
- `--xmind-file` 是本地 `.xmind` 文件路径；`.xmind` 会作为 `MindFileType=0` 上传。
- `--case-title` 会作为 `TestCaseName`；不传时默认使用文件名去掉后缀。
- `--user-name` 会作为 `Operator`；不传时从当前登录用户自动推断。
- `--remark` 会作为上传表单的 `Remark`。
- `--custom-fields` 会作为上传表单的 `CustomFields`，默认 `{}`。
- `--related-requirement <json>` 或 `--related-requirement-file <path>` 用于关联需求，上传时会设置 `parseFields=RelatedRequirement`。
- 严格 XMind 模板校验默认启用，上传表单为 `StrictMindVersion=V2`；`--no-strict-mind-version` 用于关闭严格模板校验。
- `--dry-run` 只预览请求参数，不创建用例。

### 原生节点用例创建

需要保留 Bits `TestCaseMind.data.nodeType` 时，使用原生节点创建命令。命令会先校验
`用例标题(2) -> 前置条件(3) -> 步骤(6) -> 预期结果(13)` 链路，创建后再读取用例
详情核对严格模式字段和完整节点语义树；读回不一致时命令失败，不得以创建接口成功代替验收。

```bash
bytedcli bits case create-mind \
  --devops-id <space-id> \
  --project-id <project-id> \
  --dir-id <dir-id> \
  --mind-file ./test-case-mind.json \
  --case-title "example-feature" \
  --related-requirement-file ./requirement.json \
  --dry-run

# 本地节点校验通过后，将 --dry-run 替换为 --yes 执行创建与远端读回验收。
```

- `--mind-file` 接受一个原生 TestCaseMind 根节点，或包含顶层 `mind` 字段的 JSON 对象。
- `--dry-run` 仅执行本地结构校验并输出节点类型计数，不调用创建接口。
- 正式创建必须显式传 `--yes`；`--dry-run` 与 `--yes` 互斥。
- 正式创建固定使用 `BaseType=3`、`SourceType=11`、`IsStrict=2` 和 `StrictMindVersion=V2`。
- 成功结果中的 `verified=true` 表示已通过远端 `GetTestCase` 读回校验。
- 每个用例标题分支都必须包含非空的前置条件、步骤和预期结果；叶子节点的 `children` 可为 `[]` 或 `null`。
- 创建结果不确定或创建后读回失败时，先按返回的目录或 case 链接检查远端状态，禁止盲目重试。

### XMind 用例导出

将 Bits 手动用例导出为 `.xmind`。可以直接传用例详情页 URL，CLI 会从 URL path 解析 `case-id`，从 query 解析 `projectId` 或旧页面参数 `devops_space_old_id`，并从 `/devops/<space-id>` 解析 `devops-id`；也可以显式传 `--case-id`、`--project-id`、`--devops-id`。

```bash
bytedcli bits case xmind export \
  --url "https://example.bits.test/devops/<space-id>/quality/case/caseDetail/<case-id>?devops_space_old_id=<project-id>" \
  --output ./example.xmind

bytedcli bits case xmind export \
  --case-id <case-id> \
  --project-id <project-id> \
  --devops-id <space-id> \
  --case-title "example-feature" \
  --language zh-cn \
  --output ./example.xmind
```

常用参数：

- `--url` 是 Bits 手动用例详情页 URL，可自动解析 `--case-id`、`--project-id`、`--devops-id`。
- `--case-id` 是 Bits 手动用例 ID；未提供 `--url` 或 URL 不含用例 ID 时必填。
- `--project-id` 对应 Bits 用例页面 URL query 中的 `projectId` 或 `devops_space_old_id`；未提供 `--url` 或 URL 不含这两个参数时必填。
- `--devops-id` 对应 Bits URL path 中 `/devops/<space-id>`，会作为 `x-onesite-space-id`；URL 中已包含时可省略。
- `--case-title` 会作为导出请求的 `TestCaseName`；不传时 CLI 会先读取用例详情自动推断，详情响应未返回标题时使用 `case-<case-id>`；如果详情接口不可用，显式传 `--case-title` 可跳过详情查询。
- `--user-name` 是可选 Operator，仅用于详情标题查询；不传时不会阻塞导出。
- `--language` 控制 XMind 语言，支持 `zh-cn` / `en` / `en-us` / `zh`，默认 `zh-cn`。
- `--output` 是本地 `.xmind` 输出路径；若传入已存在目录，则自动写为 `<case-title>-<case-id>.xmind`；不传时输出后端返回的下载 URL，若后端只返回异步导出数据，则 JSON 模式会保留 `rawData`。

### 更新泳道

```bash
bytedcli bits develop update-lane \
  --dev-id 123456 \
  --lane new_lane \
  --idcs lf,lq \
  --dry-run
```

### 更新 develop 任务

```bash
# 默认 --change 只更新任务中已存在的项目；显式加 --ensure-change-card
# 才会保留未点名项目、按需补项目，并幂等补一张 Codebase Change Card。
bytedcli bits develop update \
  --dev-id 123456 \
  --lane ppe_test \
  --name "demo develop title" \
  --change "service=example.service.api,type=TCE,branch=codex/demo" \
  --change "service=example.service.worker,type=TCC,branch=codex/worker" \
  --change "service=sample-gecko-project-id,lookup=demo-hybrid-project,type=HYBRID,control-plane=i18n,branch=codex/worker" \
  --ensure-change-card \
  --dry-run

bytedcli bits develop inspect-changes --dev-id 123456
```

`develop update --change` 始终读取并回写最新 `changes/versionCode`，避免完整快照接口清空已有 Change Card；默认仍只更新任务内已存在的点名项目，不会自动补项目或卡片。相同 PSM 可能同时对应 TCE、TCC 等项目，遇到这种情况必须在每条 change 中写 `type=`；每条 change 的类型优先于全局 `--service-type`。任务快照或 AppCenter 自动发现若命中多个类型，会在任何写操作前报错，不会取搜索结果首条。显式传 `--ensure-change-card` 后，命令才保留未点名项目、按需从 AppCenter 补项目，并为缺失的 repo/branch 幂等追加 Change Card。AppCenter 只能按名称检索时，在对应 change 中添加 `lookup=<keyword>`；它只改变搜索词，`service=` 仍作为期望 `projectUniqueId` 严格校验。此模式下 `mr=<iid>` 可让新卡片指向已有 MR；卡片已存在时先用 `inspect-changes` 获取 change id，再用 canonical `develop change bind-mr` 绑定。正式执行后使用 `inspect-changes` 核对卡片。

### 绑定分支

```bash
bytedcli bits develop bind-branch \
  --dev-id 123456 \
  --branch codex/feature \
  --git-repo stone/coze-coding \
  --services example.service.api \
  --dry-run
```

### 绑定开发单到发布单

```bash
bytedcli bits develop bind-release \
  --dev-ids 2143012,2143013 \
  --release-ticket-id 1130150230274 \
  --dry-run

# 绑定到已知集成区；只支持单个任务，默认仅预览，确认执行需 --yes
bytedcli bits develop bind-release --dev-ids 12345 --integration-id 67890 --dry-run
```

`--integration-id` 与 `--release-ticket-id` 互斥。精确集成区模式调用单任务
`/api/v1/dev/task/integration/bind`，请求仅含 `devBasicId` 和 `integrationId`；不接受
code-change reuse 或流水线重跑策略，预览与执行都返回 `payload`，执行响应保留在 `raw`。
发布单模式保持原批量绑定行为，必须显式 `--dry-run` 预览或 `--yes` 执行。

### 从研发任务推进到发布

`bits develop publish` 对应 BITS 研发任务页面上的“发布”按钮，用于 1:1 DevTask 发布链路。它会优先读取 DevTask 已关联的发布单并带上 `releaseTicketId`；如果还没有关联发布单，则不会另行创建空发布单，而是通过 DevTask 的发布阶段推进接口交给 BITS 生成/关联。

```bash
bytedcli bits develop publish --dev-id 2402911 --dry-run
bytedcli bits develop publish --dev-id 2402911 --yes
```

#### Agent Guidance：发布要先认领状态机（DevTask vs 发布单）

DevTask 工作流和发布单工作流是两条独立状态机。研发任务页面上的“发布”按钮属于 **DevTask** 状态机，对应命令是 `bits develop publish`（底层推进 `DevReleaseStage`），不是 `bits release` 下的命令。

- 关键陷阱：发布单**已经存在**并不代表它已接管整条链路。只要 DevTask 的发布交接还没完成，写操作依旧归 `bits develop`。看到发布单已存在就切到 `bits release status-operation` / `bits release pipeline run` 是错误路径。
- 当某次发布源自 BITS 研发任务时，优先先查 DevTask：`bytedcli --json bits develop get --dev-id <dev-id>`；推进前用 dry-run 探一次 `bytedcli --json bits develop publish --dev-id <dev-id> --release-ticket-id <release-ticket-id> --dry-run`，能解析出 `releaseTicketId` 就说明这才是“发布”按钮的正确入口。
- 只有 DevTask 发布交接完成、发布单 integration 也完成后，才切到发布单侧只读轮询（`bits release get` / `bits release stages` / `bits release stage pipeline` / `bits release stage deploy-overview`）。

为防止误操作，`bits release pipeline run` 现在会先做 can-run 预检：只有后端明确返回 `canRun=true` 才放行。`canRun=false` 会报 `BITS_RELEASE_PIPELINE_NOT_RUNNABLE`；探测失败或响应缺少合法布尔值会报 `BITS_RELEASE_PIPELINE_CAN_RUN_UNKNOWN`。确认发布单确实已接管且已独立检查 stage 后，才可加 `--force` 跳过预检。

#### Agent Guidance：FaaS 发布单流水线两个必踩坑（demo-faas 实战 2026-08-04）

**坑 1：FaaS 升级工单 RollingPercentage 模板解析失败** —— 流水线 `create_faas_upgrade_ticket` 引用 `{{sys.release_ticket.faas_deploy_config['cluster_info']}}`，该 needLoadWhenRender 系统变量**只在发布确认表单提交时物化**。任何 CLI/脚本直接调 `cd/pipeline/run`（含 `bits release pipeline run`）都缺 `params.strategy.faasStrategy` → 模板变量不解析 → job 报 `readUint64: unexpected character`。**正解**：走发布单详情页「Run deployment pipeline」确认流（前端会依次发 run_vars → run_pre_check(带完整 params) → pre_set_batch_stage_pipeline_run_key → run），或本地复刻完整 4 步序列（见 `references/release-playbook-faas.md` §2）。`change-item deploy-strategy update` 只改存储不物化模板，别指望它修复。

**坑 2：125536 阶段流转失败 ≠ QCSS pending** —— dev 任务 `releaseTicketAssociatedOneDevTask` 指针钉在已取消的旧发布单时，pass-stage/publish 按关联单解析 QCSS 报告 → 报告不存在 → 报 125536（hint 永远说 "QCSS check items are pending"）。此时 QCSS 全绿也照样报。**解法**：r2 门禁全绿 + canRun=true 后直接走发布单维度（complete-integration → start-integration → stage check → pipeline run），**不要**试图 `bind-release` 解绑（合入阶段报 125006）。

完整链路（解锁 can-run → QCSS 人工项 → 人工卡点放行 → 发布后日志验证）见 `references/release-playbook-faas.md`；本地免浏览器直调可复用 §5 的 HTTP 端点（`can-run`/`stage`/`jobs`/`gate`/`qcss-pass`/`continue`/`log-verify` 等）。

### 处理 gatekeeper 检查项（skip / approve / reject）

`bits develop gatekeeper` 用于查看并处理研发任务某个阶段的 gatekeeper 检查项；它是推进 `pass-stage` 的前置入口。先用 `list` 拿到 `checkID`，再按检查项性质 skip / approve / reject：

```bash
# 1. 先列出当前阶段的 gatekeeper 检查项，拿到 checkID（--stage 默认 DevDevelopStage，准入阶段传 DevAccessStage）：
bytedcli bits develop gatekeeper list --dev-id 2383814
bytedcli bits develop gatekeeper list --dev-id 2383814 --stage DevAccessStage
# 2. QCSS 类检查项（质量门禁 CheckItemTypeQCSS）用 qcss get 一键下钻：展示 BITS check、QCSS report、manual_result、代码变更与下一步建议命令：
bytedcli bits develop gatekeeper qcss get --dev-id 2383814 --stage DevGatekeeperStage
# 3. 跳过可跳过的检查项（例如人工质量门禁）：
bytedcli bits develop gatekeeper skip --check-id 56616946794978 --reason "manual ops downgrade" --yes
# 传 --dev-id 时，skip 后会回读 --stage 指定阶段（不传默认 DevDevelopStage）确认 check 已变为成功；
# 若后端返回 success 但门禁仍 failed，命令会报错而不是误报成功：
bytedcli bits develop gatekeeper skip --check-id 56616946794978 --dev-id 2383814 --stage DevAccessStage --reason "manual ops downgrade" --yes
# 4. 通过人工检查项；--always 表示后续运行也始终通过：
bytedcli bits develop gatekeeper approve --check-id 56616946794978 --reason "looks good" --yes
bytedcli bits develop gatekeeper approve --check-id 56616946794978 --reason "permanent waiver" --always --yes
# 5. 驳回人工检查项：
bytedcli bits develop gatekeeper reject --check-id 56616946794978 --reason "not acceptable" --yes
```

写操作（skip / approve / reject）的 operator 默认取当前 ByteCloud 登录用户，可用 `--operator` 覆盖；都支持 `--dry-run` 先打印请求体，live 操作必须显式加 `--yes`。`skip` 不传 `--dev-id` 时只提交 skip 请求；传 `--dev-id` 时会在请求成功后回读 `--stage`（默认 `DevDevelopStage`），确认目标 `checkID` 已变为 `CheckStatusSuccess`，避免后端接受请求但门禁未生效的 no-op 被误判为成功。单独传 `--stage` 不会触发验证，因为回读必须知道研发任务 `--dev-id`。

#### 发布（DevReleaseStage / 发布单维度）门禁

「发布」阶段的门禁不是研发任务维度，而是**发布单维度**。用研发维度（`--dev-id` + `--stage DevReleaseStage`）读发布门禁会返回**空 checkList**，读不到任何检查项。要读发布门禁，传 `--release-ticket-id` 切到发布单维度，并把 `--stage` 传成**数字 stageId**（不是 `DevReleaseStage` 字符串），数字 stageId 用 `bits release stages` 拿：

```bash
# a. 拿发布单各阶段的数字 stageId（找「发布 / Release」那条）：
bytedcli bits release stages --ticket-id <release-ticket-id>
# b. 读发布门禁检查项（拿 checkID / skippable）：
bytedcli bits develop gatekeeper list --release-ticket-id <release-ticket-id> --stage <stage-id>
# b2. 自定义阶段（如「回归测试」等 BizSceneSelfDefineStageExit 阶段）必须加 --stage-kind self-defined，
#     否则按「发布」阶段查询会返回空 checkList：
bytedcli bits develop gatekeeper list --release-ticket-id <release-ticket-id> --stage <stage-id> --stage-kind self-defined
# c. 发布门禁里可跳过的项（如「质量门禁」QCSS skippable=true）同样用 skip 处理：
bytedcli bits develop gatekeeper skip --check-id <check-id> --reason "manual ops downgrade" --yes
```

`--release-ticket-id` 一旦传入即自动走发布单维度。`--stage-kind` 决定查哪一类阶段的门禁，取值 `release`（默认）/ `self-defined` / `archive`，分别构造成 `isArchiveStage=false&isReleaseStage=true`、`isArchiveStage=false&isReleaseStage=false`、`isArchiveStage=true&isReleaseStage=false`。**stage-kind 传错不会报错，只会返回空 `checkList`**，所以拿到空结果时先确认阶段类型而不是断定「没有门禁」。向后兼容：不传发布参数仍走原研发维度（`devBasicId` + 字符串 stage）。

> Limitation：发布门禁 checkpoint/info 返回的 QCSS 项 `checkResult` 为空 `{}`，人工确认项的正文（如「确认本次上线依赖的TCC配置完成」+ Passed/Fail/Request-for-Skipping）是 QCSS 平台侧数据，这条 BITS REST 概要接口拿不到正文。`gatekeeper list` 能给到检查项名称、状态、`skippable`、`checkID`，足以驱动 skip / approve；要看 QCSS 正文需走 QCSS 平台自身接口。

#### Agent Guidance：pass-stage 被 QCSS pending 阻塞

`bits develop pass-stage`（以及底层同一推进链路）遇到 QCSS 人工检查项未处理时，BITS 会返回 `bits_code 125536`（QCSS pending）。这种情况下命令会在错误里附带可直接复制的修复命令（`hint` + `details.setup_commands`），不需要再上网页或找 OnCall。处理对应的 QCSS 人工检查项后，重试同一条 `pass-stage` 即可。其中 `<space_id>` 取自 BITS workspace URL 上的 space id：

只有 QCSS 类检查项才走 `bytestable qcss manual pass`（发布期 final_result 卡住走 `qcss final-result pass`）。非 QCSS 的人工 gatekeeper 检查项现在可以直接用上面的 `bits develop gatekeeper {skip,approve,reject}` 处理（先 `gatekeeper list` 拿 `checkID`），处理后再重试 `pass-stage`，不必绕 qcss 命令。

```bash
# QCSS pending（125536）时，先处理人工项再重试 pass-stage：
bytedcli bytestable qcss manual pass --space-id 123456789 --dev-id 2402911
# 处理完成后重试：
bytedcli bits develop pass-stage --dev-id 2402911 --stage DevDevelopStage --yes
# 发布期 QCSS final_result 卡住时，走 final-result 放行：
bytedcli bytestable qcss final-result pass --psm example.psm --pipeline-id 123456789 --meego-id 7000000001 --code-repo example/repo --branch-name master --addition-info "Code-only release. No TCC config change."
# 变更观测节点需要人工继续发布时，用 job-run continue-release（必须 --dry-run 或 --yes 二选一）：
bytedcli bits job-run continue-release --job-run-id 123456789 --pipeline-run-id 987654321 --yes
# rds_edit 等需要表单状态回传的节点，通过 --display-params 注入：
bytedcli bits job-run continue-release --job-run-id 123456789 --pipeline-run-id 987654321 --method-name UserDefinedMethod --display-params '[{"type":"RdsForms","modify_infos":[{"work_type":"DDL","sql":"CREATE TABLE ...","database":"demo_db","regions":["cn"]}]}]' --yes
```

### 发布相关

```bash
# 按名称搜索发布工单（只有 workspace/space id + 工单名时，先搜出 ticket id）
# search.name 为关键词模糊匹配；不传 --name 则列出该 workspace 下全部发布工单。
# 返回每条工单的 ticket id / name / status / current stage / creator，拿到 ticket id 后再 get。
bytedcli bits release search \
  --workspace-id 4084696834 \
  --name "token修改发布"

# 查询发布工单详情
bytedcli bits release get --ticket-id <release-ticket-id>

# 查询发布工单各项目部署概览（部署状态 / 负责人 / 主仓 SCM）
bytedcli bits release deploy-overview --ticket-id <release-ticket-id>

# 查询发布工单阶段（id / name / type / status / pipeline count）
bytedcli bits release get-stages --ticket-id <release-ticket-id>

# 查询发布工作流
bytedcli bits release list-workflows \
  --workspace-id 150900021762 \
  --keyword "快速发布"

# 获取发布表单 schema
bytedcli bits release form-schema \
  --workspace-id 150900021762 \
  --workflow-id 162749140482

# 创建发布工单。--description 传工单描述；--control-plane 可重复声明工单控制面
# （cn / i18n / eu-ttp / us-ttp / i18n-bd 语义值）；
# 挂载 TCC namespace 用 --tcc-psm '<psm>@<plane>'（可重复，同一 PSM 多控制面写
# '<psm>@cn,i18n'），不要手写 --projects-json 的 TCC 条目——缺字段的条目会被后端
# 静默丢弃，CLI 会在这种情况下报错；approvers 缺省自动填当前登录的个人账号，
# 服务账号登录时不会自动填，需显式传 --release-approvers
bytedcli bits release create-ticket \
  --workspace-id 150900021762 \
  --workflow-id 162749140482 \
  --name "v1.0.0 发布" \
  --description "示例发布说明" \
  --control-plane cn \
  --control-plane i18n \
  --tcc-psm "example.service.config@i18n"

# 发布单集成阶段推进 / 状态修复；所有命令都支持 --body/--body-file 传完整后端 body
bytedcli bits release start-integration --ticket-id <release-ticket-id>
bytedcli bits release complete-integration \
  --ticket-id <release-ticket-id> \
  --operator <username> \
  --cancel-running-development-task 2
bytedcli bits release status-operation \
  --ticket-id <release-ticket-id> \
  --status <status-code> \
  --operator <username>
bytedcli bits release cancel \
  --ticket-id <release-ticket-id> \
  --operator <username> \
  --cancel-reason "not needed"
# cancel 默认使用平台取消原因类型；如需传完整后端 payload，用 --body/--body-file
bytedcli bits release check-status-recover \
  --ticket-id <release-ticket-id>

# 查询发布阶段 / 项目配置
bytedcli bits release stages --ticket-id <release-ticket-id>
bytedcli bits release project-configs \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id>

# 原子维护 release ticket 的 controlPlanes 字段
bytedcli bits release control-plane add \
  --ticket-id <release-ticket-id> \
  --control-plane i18n-bd \
  --dry-run
bytedcli bits release control-plane remove \
  --ticket-id <release-ticket-id> \
  --control-plane i18n-bd \
  --dry-run

# 查询阶段流水线和准入信息（--control-plane 用语义值：cn / i18n / eu-ttp / us-ttp / i18n-bd）
bytedcli bits release stage pipeline \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --control-plane cn
bytedcli bits release stage check-info \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id>
bytedcli bits release stage progress \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id>

# 触发阶段检查 / 阶段操作 / 重建阶段流水线
bytedcli bits release stage check \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --operator <username>
bytedcli bits release stage force-check \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id>
bytedcli bits release stage force-check-backward \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --control-plane cn
# 完成阶段前先检查 release-dimension gatekeeper；若 QCSS 等 checkpoint 失败，
# 应先处理/审核该门禁，不要重复调用 stage operation。
bytedcli bits develop gatekeeper list \
  --release-ticket-id <release-ticket-id> \
  --stage <stage-id>
# stage operation / force-rebuild-pipelines / recreate-pipelines 是真实写操作：
# 必须显式传 --dry-run（预览 body）或 --yes（提交）二选一，都不传时报 BITS_CONFIRMATION_REQUIRED
bytedcli bits release stage operation \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --operate-type 1 \
  --username <username> \
  --yes
bytedcli bits release stage force-rebuild-pipelines \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --yes
bytedcli bits release stage recreate-pipelines \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --yes

# 查询 change item 检查结果 / 部署策略；TCE 热部署 surgeConfig 可用 set-surge 快速更新
bytedcli bits release change-item check-result \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --project-unique-id <psm-or-web-name> \
  --project-type 1 \
  --control-plane cn
bytedcli bits release change-item deploy-strategy get \
  --ticket-id <release-ticket-id> \
  --project-unique-id <psm-or-web-name> \
  --project-type 1 \
  --control-plane cn
bytedcli bits release change-item deploy-strategy set-surge \
  --ticket-id <release-ticket-id> \
  --project-unique-id <psm> \
  --project-type 1 \
  --control-plane cn \
  --username <username> \
  --disable-surge \
  --surge-percent 25 \
  --min-ready-second 10

# 查询 / 锁定 release integration 项目。TCE 项目默认 PROJECT_TYPE_TCE / CONTROL_PLANE_CN。
bytedcli bits release integration lock-info \
  --integration-id <integration-id> \
  --project-unique-id <psm-or-web-name> \
  --project-name <project-name>
bytedcli bits release integration lock \
  --integration-id <integration-id> \
  --release-ticket-id <release-ticket-id> \
  --project-unique-id <psm-or-web-name> \
  --project-name <project-name>

# 将线上源 TCC 配置导入已有发布单。执行 import、sync-tcc 或 TCC pipeline run 前
# 必须读取 references/release-tcc-import.md。
# dry-run 使用 JSON 输出检查 selected_configs 中的 source_config_id 和 import_version。
bytedcli --json bits release tcc-config import \
  --ticket-id <release-ticket-id> \
  --psm example.service.api \
  --control-planes cn \
  --config-name demo_config \
  --region CN \
  --dir /default \
  --dry-run

# 批量导入也必须先预览每个配置的坐标和版本。
bytedcli --json bits release tcc-config import \
  --ticket-id <release-ticket-id> \
  --psm example.service.api \
  --control-planes cn \
  --config-names demo_config,sample_rules \
  --dry-run

# 已导入 Draft 与 deploy target 的 get/update 必须读取
# references/release-tcc-draft-target.md。该 reference 定义精确选择器、正文私有落盘、
# content/plan/snapshot SHA-256 漂移门禁、完整数组保留及 dry-run -> 独立授权 -> --yes 流程。
# 这些原子命令不会隐式 sync TCC、启动流水线、推进 stage 或发布配置。

# 查询并运行发布 pipeline。Web/前端发布常需要 --use-change-items，TCE 发布若依赖策略则加 --attach-deploy-strategy。
# pipeline run 会先做 can-run 预检：只有 canRun=true 才放行；false、缺字段或探测失败都停止。独立确认 stage 后才可加 --force 跳过。
# pipeline run 本身必须显式传 --dry-run（预览 run payload）或 --yes（真实启动）二选一，都不传时报 BITS_CONFIRMATION_REQUIRED。
bytedcli bits release pipeline change-items \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --control-plane cn
bytedcli bits release pipeline run \
  --ticket-id <release-ticket-id> \
  --stage-id <stage-id> \
  --username <username> \
  --control-plane cn \
  --use-change-items \
  --attach-deploy-strategy \
  --dry-run

# 查询 / 处理质量门禁风险任务。skip/skip-approval 支持 --body 或 --body-file 传完整后端 body。
bytedcli bits release risk summary --ticket-id <release-ticket-id>
bytedcli bits release risk latest-task \
  --business-key <business-key> \
  --deployment-key <deployment-key> \
  --detect-provider 1
# risk skip 是真实写操作：必须显式传 --dry-run（预览 body）或 --yes（提交）二选一
bytedcli bits release risk skip \
  --business-key <business-key> \
  --deployment-key <deployment-key> \
  --detect-provider 1 \
  --reason "FTF skipped for this launch" \
  --yes
bytedcli bits release risk manual-confirm \
  --business-key <business-key> \
  --operator <username> \
  --comment "confirmed"
```

执行发布单 TCC 导入、`pipeline sync-tcc` 或包含 TCC 项目的 `pipeline run` 时，必须先读取 `references/release-tcc-import.md`。该 reference 说明 source config 防漂移选择、PPE Draft 覆盖、SHA-256 回读、容量边界和后续显式发布步骤。Release 命令接受 TCC source control-plane 语义，并自动处理 EU/US 的 Release workflow slice 编号差异。所有 release import dry-run 都会返回 `plan_sha256`，live 导入必须携带 `--expected-plan-sha256 <plan_sha256>`；PPE 来源快照、普通 source 选择、导入身份或 storage version 漂移会在首次 Bits 写入前失败，Bits Draft 中由更新流程保留的现有字段不在 PPE 摘要范围内。普通 live 导入还会独立回读持久化 change item 与 Draft。`pipeline sync-tcc` 会在写前按项目核对全部 source Draft config name、Draft config ID（`--expected-config-ids` 传 Draft config ID；materialized artifact ID 由 BITS 写入时分配、写前不可知）与 expected tuple allowlist，写后按数量、name、region/dir 与不含 config ID 的 tuple 核对物化结果；live 调用同样必须回传其 dry-run 的 `plan_sha256`，该 hash 还覆盖当前 Draft 内容/版本、deploy target、物化状态和 `source_snapshot_atomic`。实际 sync 写入没有服务端 CAS，提交前会立即重读 source snapshot，成功后再从最新 change items 做独立持久化回读并重新核对源 Draft/deploy target；只有 `sync_dispatched=true` 且 `readback_verified=true` 才能确认本次物化。TCC 的 `pipeline run` 始终拒绝未物化 artifact，不会隐式 sync；必须提交完整的 project/config allowlist、每个 `projectType + projectId` 与 materialized `configId + region + dir` tuple，多项目时 config tuple 也必须绑定 project identity，并在 live run 回传固定 `runTimestamp` 的 dry-run `planSha256`，同时显式传 `--yes`。run plan 还锁定 `force` 与是否 pre-set；custom var 仅输出 presence/redaction 元数据，不提供逐值指纹；live 默认轮询 15 秒，要求每个选中项目出现新 build，且至少一个全局 build/run ID 与 mutation 响应的相关 ID 匹配，只有返回 `readbackVerified=true` 才算启动已验证。Agent 在执行 live 导入、`pipeline sync-tcc` 或 `pipeline run` 前，必须先向用户展示对应 dry-run 计划并等待该步骤的明确授权；Agent 自己检查 dry-run 不能视为用户确认，也不能用一次授权连续执行后续写操作。

查询、创建、编辑或删除发布单里的 TCC Draft / deploy target / 变更项时，必须先读取 `references/release-tcc-draft-target.md`。Draft 正文默认从 text / JSON 输出中完全省略，update 的 dry-run 也不输出新正文；live 更新必须回传最新 `content_sha256` 与 update dry-run 的 `plan_sha256`，后者锁定 Draft/source/baseline/version identity 和下一版 metadata。`tcc-config create` 在发布单上新建无线上 source 基线的 Draft：create dry-run 只回显 `content_sha256`（不回显正文与 payload），live 创建必须回传该 dry-run 的 `plan_sha256`，提交前会重跑 preflight 并复核 plan hash，任何漂移（包括同名草稿或线上同名 source 配置已存在）都会在首次写入前失败。deploy target 更新必须同时回传完整快照的最新 `snapshot_sha256` 与 dry-run 的 `plan_sha256`，且未点名的 BOE / PPE / PROD 数组原样保留。这些哈希都是 CLI 侧漂移门禁，不是服务端原子 CAS。上述命令不会执行 `pipeline sync-tcc`、`pipeline run`、stage 推进或 TCC 发布。

### Anywheredoor — Android/iOS 设备录入、抓包监控、share 链接、curl 转换与 mock

`bits anywhere` 支持 Android 调试包与 AppUse-enabled iOS 调试包设备录入，以及设备抓包监控与 capture-to-curl：`device create` / `listen` / `status` / `watch` / `get` / `stop`。这个命令树也支持 share 链接解析、设备选择、mock 查询/维护、filter 与 black path 查询。iOS AirBuild 场景使用 `device create --platform ios --appuse-port <port> --airbuild`。设备授权流程、敏感输入方式与完整命令见 `references/anywheredoor.md`。

实现要点：

- 先用 `device list` 选真实设备；`did=0` 只适合部分只读查询，不适合 create/enable/delete mock 这类写操作。
- `device create` 的非 dry-run 结果只有在 backend 对同一 DID 返回 `auth=true` 时才是 `passed`；`--dry-run` 只做预检并返回 `verification.status=not-run`。Arena Any-Code 只通过 `--arena-code-stdin` 或 TTY 隐藏输入。
- `watch` 默认走 HTTP 轮询模式（`--mode poll`），每 1.5s 拉一次 `/web-apis/proxy/v1/history` 的滑动窗口（默认 30s），按 capture id 去重，仅打印新增。
- `--url-path` 在客户端做 substring 匹配，同时把过滤值的最长 path segment 作为 backend hint 收窄响应（backend `path=` 是 per-segment 子串，多 segment 切片不识别）。
- backend 默认 10 分钟无续期会自动停止抓包；watch 超时后会拉不到新数据，需要重跑 `bits anywhere listen` 续期。
- `--mode ws` 仅作为 WebSocket 协议研究 escape hatch；实测 server 对非浏览器指纹连接 silently 拒推送，**不要在生产场景使用**。
- `share get --url <url>` 是只读查询：单条链接包含 `_proxy_share_item_id` 和 `appId`，可加 `--curl`；批量链接包含 `_proxy_share_items_id` 和 `appId`，返回原始分享数据。
- `mock create-local`、`mock create-remote`、`mock enable`、`mock disable`、`mock delete` 都是写操作，必须显式加 `--yes`；调试时优先创建 disabled 临时 mock，验证后删除。
- `mock create-local` 与 `mock create-remote` 都可用 `--query-filter key=value` 精准限制 source query；CLI 会生成 Anywheredoor backend 使用的 `content[0].extra_filter` JSON 字符串。复杂场景可传 `--extra-filter '<json-object>'`，但不要和 `--query-filter` 混用。
- `mock create-remote` 使用 `--target-url` 配置改写目标。`--query-filter` 匹配 source request，`--target-url` 中的 query 发往 target；目标必须是无凭证、无 fragment、无重复 query key 的绝对 HTTP(S) URL。

```bash
# 列出 app 下已授权设备
bytedcli bits anywhere device list --app-id 1234

# 启动抓包（10 分钟自动停止）
bytedcli bits anywhere listen \
  --app-id 1234 --did 1234567890123456

# 查询当前抓包状态
bytedcli bits anywhere status \
  --app-id 1234 --did 1234567890123456

# 实时监控某个 path 的 capture 并打印 curl（Ctrl+C 停止）
bytedcli bits anywhere watch \
  --app-id 1234 --did 1234567890123456 \
  --url-path /api/demo \
  --show-curl

# 把最近 30 分钟内 path 含 /api/demo 的 capture 全部 dump 出来
bytedcli bits anywhere watch \
  --app-id 1234 --did 1234567890123456 \
  --window-sec 1800 --include-snapshot \
  --url-path /api/demo

# 单条 capture 转 curl（已知 history_id + env，envcode 来自 list 中的 env 字段）
bytedcli bits anywhere get \
  --app-id 1234 --did 1234567890123456 \
  --history-id 1447858190 --env 8 --curl

# 从任意门 share 链接读取单条 capture，并转换为 curl
bytedcli bits anywhere share get \
  --url 'https://example.com/anywheredoor/proxy/share?appId=1234&_proxy_share_item_id=1447858190&env=8' \
  --curl

# 从任意门批量 share 链接读取原始数据
bytedcli --json bits anywhere share get \
  --url 'https://example.com/anywheredoor/proxy/share?appId=1234&_proxy_share_items_id=sample-share-id'

# 立即释放代理资源（不等 10 分钟自动停）
bytedcli bits anywhere stop \
  --app-id 1234 --did 1234567890123456

# 查询 local mock 列表
bytedcli bits anywhere mock list \
  --app-id 1234 --did 1234567890123456 \
  --type local --page-size 20

# 创建 local mock；确认后才执行写入，服务端默认启用
bytedcli bits anywhere mock create-local \
  --app-id 1234 --did 1234567890123456 \
  --name sample-local-mock \
  --method GET \
  --url-path /api/demo \
  --query-filter app=1 \
  --query-filter version_code=123456 \
  --body '{"ok":true}' \
  --serializer json \
  --yes

# 创建 remote mock；服务端默认启用，source query 与 target query 分开配置
bytedcli bits anywhere mock create-remote \
  --app-id 1234 --did 1234567890123456 \
  --name sample-remote-mock \
  --method POST \
  --url-path /api/stream \
  --query-filter mode=demo \
  --target-url 'https://example.com/mock/stream?session=sample' \
  --yes

# 完整 Rewrite：配置格式见 references/anywheredoor.md；默认预览，--yes 才提交
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 \
  --name sample-rewrite --config-file ./rewrite.json

# 规则配置也可直接传 JSON；--config 与 --config-file 互斥
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 --name sample-rewrite \
  --config '{"locations":[{"path":"/api/demo"}],"rules":[{"type":"body","scope":"response","replace":{"value":"sample response"}}]}' \
  --dry-run

# 确认后创建；可传 --enable，不传时服务端同样会启用新规则
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 \
  --name sample-rewrite --config-file ./rewrite.json --yes

# 与 Local/Remote 相同的 --enable 参数；它不替代 --yes 确认
bytedcli --json bits anywhere mock create-rewrite \
  --app-id 1234 --did 1234567890123456 \
  --name sample-rewrite --config-file ./rewrite.json --enable --yes

# 编辑会整体替换 locations/rules 并保留启用状态；将 --dry-run 换为 --yes 提交
bytedcli --json bits anywhere mock update-rewrite \
  --app-id 1234 --did 1234567890123456 --mock-id 987654321 \
  --name sample-rewrite --config-file ./rewrite.json --dry-run

# 启停或删除 mock 都要明确确认
bytedcli bits anywhere mock enable \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --yes
bytedcli bits anywhere mock disable \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --yes
bytedcli bits anywhere mock delete \
  --app-id 1234 --did 1234567890123456 \
  --mock-id 987654321 --yes

# 查询 filter / black path
bytedcli bits anywhere filter get \
  --app-id 1234 --did 1234567890123456
bytedcli bits anywhere black-path get --app-id 1234
```

`watch` 输出列：`id`、`path`、`log_id`、`env`，可作为 `get --history-id <id> --env <env>` 的输入。
配合 `--show-curl` 或 `share get --curl` 可以直接拷贝得到的 `curl` 在本地复现请求（已自动剥离 `Host` / `Content-Length` / `Accept-Encoding` 等 curl 自管头，并把 cookies 合并成 `-b`）。

`create-local`、`create-remote`、`create-rewrite` 的 `--enable` 参数一致：不传时请求发送
`enabled: false`，传入时发送 `true`。**当前后端两种情况均创建为启用状态**，不能把不传
`--enable` 当作停用创建；需要停止时使用 `mock disable --mock-id <id> --yes`，并提供对应
`--app-id`、`--did`。Rewrite 结果的 `requestedEnabled` 表示请求值，`enabled` 表示预览中
预期的状态或提交后回读确认的实际状态。详见 `references/anywheredoor.md`。

### 接口测试 test-set — 测试集、用例、执行历史与分享链接

`bits test-set` 对应 Bits「接口测试」页面（interface_test）的测试集能力：请求集合（collection）→ 目录（dir）→ 保存用例（case，含 RPC、HTTP/URL、HTTP/指定实例三种类型）。认证走 ByteCloud SSO（`bytedcli auth login`），不需要 Bits OpenAPI token。

实现要点：

- 用例的「输入」包含 body、headers、settings（超时/控制面/集群等）、rpc context 等；「输出」包含 resp body、resp headers、log_id、argos 链接。`case get` / `history get` 会同时展示两者。
- `test-set delete` 与 `case delete` 是不可逆写操作，必须显式加 `--yes`。
- `case execute` 会向目标服务发真实请求（等价页面上的「发送」），是真实写操作：必须显式传 `--dry-run`（预览请求，不发送）或 `--yes`（发送）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`；控制面默认自动推断（HTTP/URL 用例指向 BOE host 时走 offline），可用 `--plane online|offline` 强制。
- `history list` 无过滤条件时后端会报错，CLI 会自动取「今天」时间分组兜底；用 `--group-by time|api` 看分组，再用 `--start/--end` 或 `--psm/--func-name` 缩小范围。
- `share create` 等价页面「分享 → 复制链接」（`--case-id` 或 `--history-id` 二选一），输出 `https://bits.bytedance.net/interface_test?...&shareId=<id>`；`--masked` 对应「脱敏分享」。拿到别人链接里的 shareId 后用 `test-set share get --share-id <id>` 解析出完整入参与出参。
- `case create` 来源三选一：`--history-id` 从执行历史保存；`--from-case-id` 复制已有用例——带 `--collection-id` 时另存到目标测试集（等价页面「另存为」），省略 `--collection-id` 时在原目录内克隆（等价页面「复制」）；`--file` 直接提交 explorer v5 原始 snake_case 请求记录 JSON，Mock 下游等高级字段可通过该形态透传。保存时会自动剥离旧执行结果与归属字段，只保留请求定义。
- `case update` 是「取现状 → 合并 → 写回」语义：`--body`/`--body-file` 只改请求体，`--name` 改名，`--file` 合并任意原始字段。
- `batch execute` 等价页面「批量执行」：对集合（或 `--dir-id` 限定目录、`--case-ids` 显式列表）内所有保存用例发起一次批量执行，是真实写操作：必须显式传 `--dry-run`（预览批量范围，不发送）或 `--yes`（发送）二选一，都不传时报 `BITS_CONFIRMATION_REQUIRED`；`--wait` 轮询到完成并输出逐用例结果；批量任务由平台侧 replay 执行，直连外网/BOE host 的 HTTP/URL 用例可能在 replay 环境不可达。
- `history list --batch` 查看批量发送历史（对应历史 tab「批量发送」）；`history get --batch-task-id <id>` 看某次批量任务汇总与逐用例结果，`history get --replay-id <id>` 看批量里单条用例的完整输入输出。单次发送历史仍用 `history get --id`。
- `export` 把测试集用例导出为等价 `bytedcli api-test rpc-call/http-call` 命令（`--format commands`，HTTP/URL 型无 api-test 等价物、自动降级为自带 `--yes` 的 `bits test-set case execute` 命令行）或可导入的 JSON（`--format json`）；`import` 把导出的 JSON 存回任意测试集，二者构成跨集合迁移闭环。

```bash
# 查看所有测试集（集合 → 目录 → 用例）；--keyword 按 API 关键字过滤，--no-with-request 只看集合
bytedcli bits test-set list
bytedcli bits test-set list --keyword oauth

# 新建 / 修改 / 删除测试集（集合）
bytedcli bits test-set create --name demo-collection --desc "demo" --permission private
bytedcli bits test-set update --collection-id 123 --desc "new desc"
bytedcli bits test-set delete --collection-id 123 --yes

# 在测试集下新建目录
bytedcli bits test-set dir create --collection-id 123 --name demo-dir

# 查看某个用例的完整输入输出
bytedcli bits test-set case get --id 456

# 把一次执行历史保存为用例
bytedcli bits test-set case create --collection-id 123 --dir-id 45 \
  --history-id 789 --name demo-case

# 修改用例（改请求体 / 改名）
bytedcli bits test-set case update --id 456 --body '{"Key":"value"}'

# 执行用例（真实调用目标服务）；可临时覆盖请求体与超时。
# 必须显式传 --dry-run（预览执行 payload 与请求体，不发送）或 --yes（真实发送）二选一，
# 都不传时报 BITS_CONFIRMATION_REQUIRED。
bytedcli bits test-set case execute --id 456 --dry-run
bytedcli bits test-set case execute --id 456 --body '{"Key":"value"}' --timeout-ms 120000 --plane offline --yes

# 删除用例
bytedcli bits test-set case delete --id 456 --yes

# 生成分享链接（复制链接）；解析他人分享
bytedcli bits test-set share create --case-id 456
bytedcli bits test-set share create --history-id 789 --masked
bytedcli bits test-set share get --share-id sampleShareId

# 复制用例（同目录克隆，省略 --collection-id）；另存为（存到别的测试集）
bytedcli bits test-set case create --from-case-id 456 --name copied-case
bytedcli bits test-set case create --collection-id 124 --from-case-id 456 --name saved-as

# 批量执行：整个测试集 / 某个目录 / 指定用例列表；--wait 轮询到完成。
# 同样必须显式传 --dry-run（预览执行范围与规模）或 --yes（真实批量发送）二选一。
bytedcli bits test-set batch execute --collection-id 123 --dir-id 45 --wait --dry-run
bytedcli bits test-set batch execute --collection-id 123 --case-ids 456,457 --yes

# 执行历史：单次发送按时间 / 按接口分组，再看条目与详情
bytedcli bits test-set history list --group-by time
bytedcli bits test-set history list --group-by api
bytedcli bits test-set history list --psm demo.example.psm --func-name DemoMethod
bytedcli bits test-set history list --start "2026-07-20T00:00:00+08:00" --end "1h ago"
bytedcli bits test-set history get --id 789

# 执行历史：批量发送任务列表 / 任务详情 / 单条 replay 的输入输出
bytedcli bits test-set history list --batch
bytedcli bits test-set history get --batch-task-id 12
bytedcli bits test-set history get --replay-id sampleReplayId

# 导出为 api-test 命令（或 --format json）；导入回任意测试集
bytedcli bits test-set export --collection-id 123
bytedcli bits test-set export --collection-id 123 --format json --output cases.json
bytedcli bits test-set import --collection-id 124 --file cases.json
```

### 服务模版市场 — `bits market-template`

`bits market-template` 对应 Bits 控制台的「服务模版」市场（`devops_open/market/template`），也就是 app 编译环节引用的模版。它与 `bits pipelines templates`（BITS 流水线模板）是两套完全不同的资源，不要混用：前者是插件编排模版，后者是流水线模板。

模版分两层：**模版**持有基础信息（名称、负责人、标签），**版本**持有插件编排（`build` / `after_build`）与状态。发布与下线都是改版本状态，没有单独的 publish 命令。

```bash
# 浏览模版市场（默认只看已发布版本）；支持关键词与标签过滤
bytedcli bits market-template list --keyword unit --page-size 10
bytedcli bits market-template list --tags UnitTest,Android
bytedcli bits market-template tag list

# 模版详情、版本列表、某个版本的完整插件编排
bytedcli --json bits market-template get --id 7001
bytedcli --json bits market-template version list --id 7001
bytedcli --json bits market-template version get --id 7001 --iid 2

# 谁在用这个模版（当前用户可见的编译配置）
bytedcli bits market-template configuration list --template-id 7001

# 查看某个编译配置的 build / after_build 步骤及插件版本
bytedcli bits market-template configuration get --config-id 99695

# 把某个插件升到指定版本（先 --dry-run 预览，确认后加 --yes）
# --build-step 可选 build / after-build / both，默认 both
bytedcli bits market-template configuration update \
  --config-id 99695 --plugin-iid 94 --plugin-version 0.0.96 --dry-run
bytedcli bits market-template configuration update \
  --config-id 99695 --plugin-iid 94 --plugin-version 0.0.96 --build-step build --yes

# 改插件的入参取值（重复 --input 可一次改多个）
bytedcli bits market-template configuration set-input \
  --config-id 99695 --plugin-iid 94 --input SAMPLE_SDK_VERSION=release/1.0.x --dry-run
bytedcli bits market-template configuration set-input \
  --config-id 99695 --plugin-iid 94 \
  --input SAMPLE_SDK_VERSION=release/1.0.x \
  --input SAMPLE_MODEL_VERSION=sample-models --yes

# 我订阅的模版；订阅 / 取消订阅
bytedcli bits market-template subscription list
bytedcli bits market-template subscription create --id 7001
bytedcli bits market-template subscription delete --id 7001

# 新建模版（先 --dry-run 看 payload，确认后加 --yes）
bytedcli bits market-template create \
  --name sample-template \
  --english-name sample_template \
  --description "sample description" \
  --maintainers demo-user@example.com \
  --version 0.0.1 \
  --release-notes "first version" \
  --tags Android \
  --build 1119:1,2048:3:skippable \
  --dry-run

# 插件需要传参时改用 --build-json / --build-file
bytedcli bits market-template create ... \
  --build-json '[{"pluginId":1119,"pluginIid":1,"params":{"UT_SOURCE_BRANCH":"main"}}]' --yes

# 改基础信息 / 删除模版
bytedcli bits market-template update --id 7001 --description "new description" --yes
bytedcli bits market-template delete --id 7001 --dry-run

# 升版本、发布、下线、删版本
bytedcli bits market-template version create --id 7001 --name sample-template \
  --english-name sample_template --description "d" --maintainers demo-user@example.com \
  --version 0.0.2 --release-notes "second version" --build 1119:1 --yes
bytedcli bits market-template version update --id 7001 --iid 2 --state release --yes
bytedcli bits market-template version update --id 7001 --iid 2 --state draft --yes
bytedcli bits market-template version delete --id 7001 --iid 1 --yes
```

- 所有写操作（create / update / delete，含 version 子命令）默认不落库：不加 `--yes` 会报 `CLOUD_TEMPLATE_CONFIRMATION_REQUIRED`，加 `--dry-run` 打印将要发送的完整 payload。`--dry-run` 与 `--yes` 互斥，同时传会报 `CLOUD_TEMPLATE_INPUT_ERROR`。订阅类操作可逆，不需要 `--yes`。
- `--build` 的紧凑写法是 `<pluginId>:<pluginIid>[:skippable]`，逗号分隔多步；需要给插件传 `params` 时只能用 `--build-json` / `--build-file`。三者两两互斥，同时传会报 `CLOUD_TEMPLATE_INPUT_ERROR`。`pluginId` / `pluginIid` 来自插件市场。
- `version update --state release` 是发布，`--state draft` 是下线；`preview` 为预览态。
- `template update` 对应的后端接口是整体覆盖基础信息，CLI 会先读当前模版再合并，所以只传要改的字段即可，不会清空图标或标签。
- `version create` 的 `--build` 至少要有一步，空编排会被后端拒绝，`--dry-run` 阶段就会报错。
- `configuration list` 只列当前用户可见的编译配置，条数可能小于模版详情里的 app 使用数。
- `configuration get` 返回编译配置的 `build` / `after_build` 步骤，每步包含 `plugin.id` / `plugin.iid` / `plugin.name` / `plugin.version`。
- `configuration update` 按 `--plugin-iid` 定位插件并替换 `version`，`--build-step` 控制只改 `build`、只改 `after_build` 或两者都改（默认 `both`）。同样遵循 `--dry-run` 预览、`--yes` 确认的约定。
- `configuration set-input` 改的是插件入参的取值（`plugin.inputs[].value`），也就是构建时下发给该步骤的环境变量；`--input NAME=VALUE` 可重复传（同名传两次会报错），`VALUE` 允许为空以清空取值。只有插件声明过的 input 名会被接受，写错名字会直接报错并列出可用名，不会静默写进配置。`--build-step` 与 `--dry-run` / `--yes` 的语义同 `configuration update`，输出会列出每个 input 的 from → to。与 `configuration update` 一样，它作用于所有使用该 `--plugin-iid` 的步骤。
- 编译配置的构建步骤（插件版本与入参取值）都存在配置的默认参数组里，两个写命令都走 `PUT /v1/configuration/parameter`；后端 `POST /v1/configuration/update` 只落 `job_info`，改不动构建步骤。
- 只想改本次构建、或没有 Job 负责人权限时，用 `compile-job trigger --input`（见 compile-job 段）。
- 该服务只在 `cn` 与 `boe` 两个站点提供；用其他 `--site` 运行会报 `CLOUD_TEMPLATE_SITE_UNSUPPORTED`。
- 列表 JSON 输出包含 `page` / `page_size` / `has_more` / `current_count`；后端未返回总数时 `total` 为 `null`，不要用 `current_count` 当总数。
- 示例中的 `sample-*`、`demo-*`、`example.*` 与数字 ID 都是占位值。

### 客户端编译 Job — `bits compile-job`

`bits compile-job` 对应客户端空间的 Pipeline Marketplace（`/devops/<spaceId>/pipeline/marketplace?devops_space_type=client&devops_space_old_id=<appId>`）。这里的 Job 是 cloud-template 编译配置实例，不是 `bits job-run` 的 Pipeline jobRun，也不是 `bits client workflow job` 的 legacy jobId。

`--app-id` 取 URL 上的 `devops_space_old_id`。也可以传 `--space-id` 或整段 `--url`，CLI 会解析出 app id。

```bash
# 列表 + 分组；可按 group / scenario / keyword 过滤
bytedcli bits compile-job list --app-id 1234567890
bytedcli bits compile-job list --url 'https://bits.bytedance.net/devops/123/pipeline/marketplace?devops_space_old_id=1234567890'
bytedcli bits compile-job list --app-id 1234567890 --group-id 1721 --scenario develop
bytedcli bits compile-job group list --app-id 1234567890

# 详情
bytedcli --json bits compile-job get --id 10001

# 从模版创建（先 dry-run，确认后 --yes）
bytedcli bits compile-job create \
  --app-id 1234567890 \
  --name demo-compile-job \
  --english-name demo_compile_job \
  --template-id 3 \
  --queue-id 729 \
  --image-ref iOS:4.1 \
  --dry-run
bytedcli bits compile-job create \
  --app-id 1234567890 \
  --name demo-compile-job \
  --english-name demo_compile_job \
  --template-id 3 \
  --queue-id 729 \
  --image-ref iOS:4.1 \
  --yes

# 改显示名 / 删除
bytedcli bits compile-job update --id 10001 --name demo-compile-job-edited --yes
bytedcli bits compile-job delete --id 10001 --dry-run

# 触发构建；成功后用返回的 run jobId 查询或取消
bytedcli bits compile-job trigger --id 10001 --branch master --dry-run
bytedcli bits compile-job trigger --id 10001 --branch master --yes

# 本次构建临时改插件入参，不落库、不影响别人（配置本身要 Job 负责人权限才能改）
bytedcli bits compile-job trigger --id 10001 \
  --input SAMPLE_SDK_VERSION=release/1.0.x --dry-run
bytedcli bits compile-job trigger --id 10001 \
  --input SAMPLE_SDK_VERSION=release/1.0.x --plugin-iid 4 --yes
bytedcli bits compile-job trigger --id 10001 \
  --plugin-input 9:SAMPLE_TARGET=DemoApp \
  --plugin-input 42:SAMPLE_SDK=simulator --dry-run
bytedcli bits client workflow job get --job-id 20001
bytedcli bits client workflow job cancel --job-id 20001 --reason "demo cleanup"
```

- 写操作（create / update / delete / trigger / group create / group delete）必须 `--yes`；`--dry-run` 只预览 payload。两者不能同时传。
- 该服务只在 `cn` 与 `boe` 两个站点提供；用其他 `--site` 运行会报 `CLOUD_TEMPLATE_SITE_UNSUPPORTED`。修复示例：`--site cn` 或 `--site boe`。
- `--queue-id` 必须复用该 app 里已有 Job 的队列，不要编造。
- mac Job 触发前必须有 `image_ref`。缺它时 `compile-job trigger` 会立刻报 `CLOUD_TEMPLATE_INPUT_ERROR`，先 `compile-job update --id <id> --image-ref iOS:4.1 --yes`。linux / windows Job 允许空 `image_ref`。
- `compile-job trigger --branch` 会同时注入标准 `MAIN_GIT_BRANCH` 与 legacy `Main_git_branch`，兼容仍引用 `$Main_git_branch` 的旧 Job 模板。**但注入的是 env，而 Job 配置里 clone 插件填了 `MAIN_GIT_BRANCH` 时以配置为准**：构建日志会打印 `Override environment variables: (MAIN_GIT_BRANCH) value: (<配置里的分支>)`，`--branch` 静默失效。要换这类 Job 的分支，用 `--input MAIN_GIT_BRANCH=<branch>` 覆盖插件入参。
- `compile-job trigger --input NAME=VALUE` 只对本次构建生效：它改的是随触发请求发出的配置副本里的 `plugin.inputs[].value`，存档配置不变，也不影响其他人的构建。改存档配置要用 `market-template configuration set-input`，但那需要 Job 负责人权限，非负责人会收到 `HTTP 403 只有Job负责人有权限进行操作`；触发本身不需要该权限，所以非负责人换构建参数走 `trigger --input` 这条路。`--input` 可重复传（同名传两次会报错）；写了插件没声明的名字直接报错并列出可用名。一个 input 名命中多个构建步骤时**直接报错，不会批量改写**：只改一个插件时补 `--plugin-iid`；同一次构建要分别修改多个插件时，重复传 `--plugin-input IID:NAME=VALUE`。若同一个插件被用了多次，这两个参数仍表达不了「哪一次」，只能去改配置。`--dry-run` 会列出将要改的每个 input 的 from → to。
- `--scenario` 取值：`custom` / `develop` / `beta` / `normal` / `lark_in_house` / `lr` / `tech_gray`。
- 输出会去掉 `app_key` / `app_secret`。JSON 列表带 `page` / `page_size` / `has_more` / `current_count` / `groups`；过滤扫描触顶时 `truncated=true`。
- `group create` 成功后后端不一定回 id，用 `group list` 按名称确认。
- 示例中的数字 ID 与 `demo-*` 都是占位值。

## Notes

- 需要结构化输出加 `--json`
- `bits develop list` 需要显式传 `--space-id`；`--work-items` 选填
- `bits develop list --state` 支持 `initial,opened,closed,finished`，多个值用逗号分隔或重复传参；省略时不增加状态条件
- `bits develop list --title` 使用原生 `title match` 模糊过滤；`--about-user` 使用精确用户名作为 `aboutUsers` 条件，省略时不增加用户限制。若需要当前用户相关任务，先解析当前用户名再显式传入
- `bits develop list` 的 JSON `tasks[].state` 直接来自响应 `state`，缺失或非字符串时为 `null`，不会用 `status` 推断；`status` 保持原含义，完整接口响应保留在 `raw`
- `bits develop list --created-at` 使用时间戳区间 `startTs,endTs`
- `bits develop list --sort created-at-desc` 按创建时间倒序，`created-at-asc` 为正序；省略时不增加排序条件
- `bits develop merge-info --dev-id` 读取 `/api/v1/dev/task/change/merging?devBasicId=...`；JSON 的 `dev_basic_id` 保留字符串 ID，`raw` 保留完整响应，包括 `data.changeMergeInfoList` 的 `mergeStatus`、错误说明和 `data.mergingDevTaskList`。查询成功只表示读取成功，缺失字段不代表合入完成或队列为空
- `--change` 格式：`service=<PSM>,type=<TCE|TCC|FAAS|WEB|HYBRID|CRONJOB|CUSTOM>,branch=<sourceBranch>|version=<scmVersion>[,target=<targetBranch>][,scm=<scmName>][,mr=<iid>][,from=<templateDevId>]`。`type=` 可省略，但同一 PSM 存在多种项目类型时必须显式填写；优先级为 `change.type > --service-type > 自动探测`。自动探测与模板选择都要求恰好命中一个项目，模糊首条、跨类型同 ID、同一 service 的冲突 `type=` 和模板重复项都会在创建前报错
- `--var` 可重复，格式：`name=value`
- `--title` 可省略：当同时传了 `--meego` 时，CLI 会自动从 Meego 工单获取标题填充；省略 `--title` 且无法从 Meego 获取时报错
- `develop create --meego-name` / `--meego-space-key` / `--meego-type`：headless / CI agent 专用，显式传入 Meego 工作项 name 与 hex project key（`owned_project.key`）。默认 URL 形态的 `--meego` 依赖 bytedcli 自身 Meego 登录态在内部回填 name/hex；headless 沙箱无法完成该登录，会静默退化成 slug spaceId + 空 name。`--meego-name`/`--meego-space-key` 与 URL 形态的 `--meego` 互斥，必须搭配单个“裸数字” `--meego` id 且两者同时提供；`--meego-space-key` 必须是 24 位 hex（非 URL slug）。`--meego-type` 可选（`story`|`issue`，默认 `story`），决定存储 type（story→feature、issue→issue）与合成 URL 段。命中后完全不触发内部 Meego 登录/调用，并自动用 `--meego-name` 回填 `--title`
- `--team-flow-id` 显式覆盖开发单创建时的 `teamFlowId`；当 `--dev-task-template-id` 与来源模板不一致时，CLI 不再默认继承旧模板的 `teamFlowId`
- `--env-setting-map-json` 用于覆盖创建接口的 `envSettingMap` 参数
- `develop create --cluster-json` 的 CN PPE 自定义集群路径仅支持 CN-only 的 TCE project 与 `ppe_cn_env_` lane，不能与非 CN lane/project 或 `--release-ticket-id` 混用。bytedcli 会按 PSM、cluster name、region 与 IDC 解析唯一 `running` 或 `deploying` prod 基准集群，解析不到或有歧义时在创建前就报错；显式 `baseClusterId` 仅作为一致性断言。lane 创建即可部署，集群配置随创建请求一起下发，创建后读回持久化的 cluster snapshot 并按需修复一次，修复失败会关闭该任务。成功结果中的 `cluster_validation.deployment_state=requires_pipeline_check` 表示 CLI 没有回读流水线，需要自行确认自动启动的 pipeline `need_ppe=true`；**`need_ppe` 在创建任务那一刻就写死进流水线定义，为 `false` 的任务无法修复，只能重建**（0.129.0–0.131.0 的 CN 自定义集群路径会创建出这种任务，见 !3826）。
- `--services` 选择参与任务的 PSM 集合；`--cluster-json` 中的 `psm` 使用同一组 PSM 标识。多 PSM 的 `develop create --cluster-json` 要求每条配置显式携带 `psm` 和 `laneType`，并按 `psm + laneType` 精确绑定资源，避免把一个 PSM 的 CPU、内存、VC 与集群配置广播给其他 PSM。每个绑定至少声明一个 cluster；同一绑定可用不同 `name` 声明多个 cluster（例如 `default` 与 `lane-trade-core`），重名会在创建前拒绝。多个 PSM 可以使用相同的 `laneType`、`laneId` 与 IDC，但各自的 cluster entry 仍分别声明资源；单 PSM 保持兼容：仅当 PSM 和已启用泳道都能唯一推断时，`psm` 与 `laneType` 均可省略。non-CN 显式集群创建后会回读环境；缺失时先补写同一任务的 lane snapshot，再补 project snapshot，最后回读校验。失败结果会保留已创建的 task ID，调用方不得自动重新建单。
- `--dry-run` 只打印 payload 不实际创建
- `mr create` 用于基于 source/target branch 创建客户端 BITS MR；至少需要 `source-branch`、`target-branch`、`title`
- `mr create --type` 支持 `feature | bug | optimize | merge | lab | package | patch | slardar`，默认 `optimize`
- `mr create --wip [true|false]` 可设置是否 WIP；只传 `--wip` 等价于 `--wip true`
- `mr create --remove-source <true|false>` 可设置合并后是否移除 source branch，默认 true；也支持 `--no-remove-source`
- `mr create --squash-commits [true|false]` 可设置合并时是否 squash commits；只传 `--squash-commits` 等价于 `true`，配合 `--squash-commit-message <message>` 可自定义 squash commit message。不传时不在请求中携带，保持空间默认行为；该能力按 Bits 空间配置开关，未开启 squash 的空间会忽略该字段。默认单仓、`--platform`/multi-host、host-sub 三种创建模式均支持
- 如果仓库上下文无法自动推断，还需要补 `--group-name` 或 `--project-id`
- `mr get-custom-fields` 会读取 Bits 空间 `create_mr` 表单字段，并输出可传给 `mr create --custom-fields` 的默认 custom fields；`mr create` 不会自动补默认字段
- `mr create --platform` 启用平台 MR 模式（Optimus API + JWT），用于在客户端空间创建单仓 MR 并走平台评审流程；与默认单仓模式（BITS OpenAPI）走不同链路，且不要求子仓依赖
- 平台 MR 的 `--group-name` 与 `--host-project-id`（GitLab project ID）在仓库存在 `.bits/project_config.json`（含 `group_name` / `project_gitlab_id`）时自动读取、可省略；建议带 `--app-id` / `--cloud-id`（对应 `x-bits-auth-appid` / `x-bits-auth-appcloudid`）；认证只依赖 SSO 登录态，不需要 `CLIENT_BITS_TOKEN`
- `mr code-review` 的 `start` / `approve` / `gitlab` / `rules` / `reviewer-set` 子命令的 `--mr-id` 都是同一个数字：创建平台 MR 时返回的 `optimus_mr_id`，等同于 bits `code/detail/<id>` 页面 URL 里的那个数字（参见 `src/api/bits/mr-optimus.ts` 里 `mr_link` 的拼接逻辑）；不要把它跟 BITS OpenAPI 的 legacy `mr_id` 混淆
- `mr code-review start` 对平台 MR 发起代码评审（Optimus API），必须二选一传 `--dry-run` 或 `--yes`
- 默认路径会先请求 `mr code-review rules`，按项目和规则复用网页展开面板已经选中的 `members`，校验每条命中规则的 `min_request_number`，再组装 `code_review/start` 请求；`candidate_emails` 只是候选范围，不会自动选第一个。这样不需要调用者理解或手填 `--rule`
- `--dry-run` 会返回规则请求摘要、命中规则摘要和最终 start 请求，不会提交；确认后用相同命令改为 `--yes` 发起评审
- 只有需要覆盖网页默认选择时才传 reviewer：简单场景用可重复的 `--reviewer` + `--rule`（`BRANCH_REVIEWER` 时 `--rule` 为分支名），多 scope 或复杂规则用可重复的 `--review-info` JSON；覆盖模式下 `--group-name` / `--project-id` 缺省时回退 `.bits/project_config.json`，`--operator` 始终缺省取当前 SSO 用户
- `mr code-review rules` 保留为只读诊断命令，用于单独查看 scope、规则、`members`、`candidate_emails` 和最少 reviewer 数；常规发起评审不需要先手工运行它
- `mr code-review approve` 通过平台 MR 的代码评审；存在待处理评审变更时需显式加 `--always-approve` 才会强制通过
- `mr code-review gitlab` 把平台 MR 反查成底层 Bits-Code (GitLab) MR 信息（project / iid / 分支 / web URL），便于切到 GitLab 仓库做评审或评论；后端走 `/api/merge_request/branch` 接口（`dev_id` 字段），CLI 入参统一为 `--mr-id`
- `mr code-review rules` 拉取“发起代码评审前”的 reviewer 规则配置（scope / role / rule / 默认成员 / 候选人），供诊断或人工覆盖使用；可选 `--fetch-mode <int>`，默认 `0` 表示当前规则集
- `mr code-review reviewer-set` 用于修改当前代码评审中某条已命中规则选中的 reviewer：先用 `mr status --mr-id <id> --json` 查看 `review_detail.mr_rule_results[].rule_results[]` 里的 `rule_id`，再传 `--rule-id` 和一个或多个 `--reviewer`；用户名会自动补成 `@bytedance.com` 邮箱，已传邮箱则原样保留；如果同时存在 `config_rule_id`，以 `rule_id` 为准
- `mr create --multi-host` 启用多主仓模式（Optimus API + JWT），适用于 KMP 跨端场景中 bits 宿主仓检测拦截单仓 MR 的情况
- `mr create --host-sub` 启用主子仓模式（BITS OpenAPI），适用于单宿主仓+多子仓的客户端 SDK 组件发版场景
- 主子仓模式的子仓嵌套在 hosts[0].mr_dependencies 中，组件版本嵌套在 mr_dependencies[0].components 中
- 主子仓模式必须提供 `--host-project-id`（宿主仓 GitLab project ID）和至少一个 `--sub-dependency`（子仓 JSON）
- `--sub-dependency` JSON 字段：`projectGitlabId`（必填）、`sourceBranch`（必填）、`targetBranch`（可选，默认取 --target-branch）
- `--sub-component` JSON 字段：`hostProjectId`（必填）、`componentId`（必填）、`publishType`（默认 sem）、`versionBase`、`versionSuffix`（默认 rc）、`versionUpgradeType`（默认 patch）
- `--sub-component` 可重复，所有 component 会自动挂到 sub-dependency 下
- 单 `--sub-dependency` 场景下 `--sub-component` 可省略 `subRepoKey`，组件天然全部归属唯一子仓
- 多 `--sub-dependency` 场景下，每条 `--sub-component` 必须显式声明 `subRepoKey`（字符串等于目标 `--sub-dependency` 的 `projectGitlabId`）；任一条缺省时 CLI 立即抛 `BITS_INPUT_ERROR`，hint 中列出 `availableSubRepoKeys`；`subRepoKey` 取值不在 `availableSubRepoKeys` 中同样抛 `BITS_INPUT_ERROR`
- `subRepoKey` 兼容别名：`subRepoKey` / `sub_repo_key` / `subProjectGitlabId` / `sub_project_gitlab_id` 等价
- `--sub-component.componentId` 等价于 component repo_id（与 `bits component get-base-versions --repo-id` 是同一标识）
- `--sub-component` 缺省 `versionBase` 时，CLI 默认会用 `componentId` 自动解析基线版本并回填，**对齐 `bits component get-base-versions`**：直接取后端 `data.versions[0]`，与 Bits 组件平台 UI"升级"按钮的默认选中项一致（不再做客户端类型过滤，prerelease 形态如 `-alpha.x` / `-rc.x` 也会被正常采用）。`--json` 输出新增 `auto_version_base` 字段（含 `enabled` / `status` / `resolved` / `skipped` / `user_provided`）；`status` 取值：`disabled`（关闭自动补齐）、`not_needed`（无组件需要补齐 / 用户已全部显式给出）、`fully_resolved`（全部由 CLI 自动补齐）、`partial_resolved`（部分由用户显式提供、其余由 CLI 自动补齐）；`user_provided` 列出本次调用中用户显式带了 `versionBase` 的 `componentId` 集合。如需关闭自动补齐，加 `--auto-version-base false`
- 自动补齐失败按错误码分流：本地 token 缺失/为空抛 `BITS_AUTH_ERROR`（先跑 `bytedcli bits login` 再重试），其余解析失败（含 token 失效/401、网络错误、`data.versions` 为空等）抛 `BITS_VERSION_BASE_NOT_FOUND`（按 hint 跑 `bits component get-base-versions` 或显式传 `versionBase` 或 `--auto-version-base false`）；创建链路本身失败时（仅 `AppError` 路径）会把 `auto_version_base` 挂在 `error.details` 里
- 主子仓模式默认 `--wip` 为 true
- `mr create-host-sub` 是配置文件驱动的主子仓 MR 创建命令，自动从 `.host-sub-mr.json` 读取 host/sdk 配置并拉取组件版本
- `mr create-host-sub --sub-repo <path[:branch]>` 可重复指定多个子仓路径（支持 `path:branch` 格式指定独立分支），进入多子仓联合发版模式
- `mr create-host-sub --host-config <path>` 指定宿主仓目录或配置文件，搭配 `--sub-repo` 使用
- 配置文件支持三种格式：全量（host+sdks）、子仓独立（sdk only，key 取目录名）、宿主仓独立（host only）
- 配置文件驱动模式按 SDK 目录天然分组，无需 `subRepoKey`
- 多子仓模式下不传 `--sdk` 则默认使用所有收集到的 SDK
- `mr add-sub` 用于向已创建的主子仓 MR 追加一个新子仓 MR 依赖：`--mr-id` 必填；`--sub-dependency` **恰好 1 条**（含 `projectGitlabId/sourceBranch/targetBranch`），多个子仓需循环调用；`--host-project-id` 缺省时按 `--mr-id` 自动反查；`--sub-component` 内的 `hostProjectId` 可省略（fallback 到 `--host-project-id`）；不承载 Meego 绑定（如需绑定走 `mr update --meego`）；其余参数（`--group-name` / `--auto-version-base`）行为与 `mr create --host-sub` 一致
- 多主仓模式支持两种输入：
  - 兼容单 host 输入：提供 `--host-project-id`，并至少传一个 `--mr-dependency`
  - 高级多 host 输入：重复传 `--host '<json>'`，每个 host JSON 自带私有 `mrDependencies`
- 顶层 `--mr-dependency` 表示公共子仓依赖，会保留在顶层 `mr_dependencies`
- `--host` JSON 里的 `mrDependencies` 表示该 host 的私有依赖，会进入对应 `hosts[*].mr_dependencies`
- 使用 `--host` 时不要混用顶层 `--component`；公共 `--mr-dependency` 仍可与 `--host` 并存
- `--host` JSON 字段：`projectId`（必填）、`sourceBranch`（可选，默认取 `--host-source`/`--source-branch`）、`targetBranch`（可选，默认取 `--host-target`/`--target-branch`）、`mrDependencies`（数组）、`components`（数组，可选）
- `--mr-dependency` 和 `--component` 均可重复传入多个；
- `--meego` 支持传入 Meego URL 或 ID，MR 创建后自动绑定关联信息
  - URL 模式：自动从 URL 解析 `projectKey` 和 `type`，如 `https://meego.larkoffice.com/larksuite/issue/detail/6841440562`
  - ID 模式：需配合 `--meego-type` 和 `--meego-project-key` 使用
- Meego URL 的 `type` 映射规则：`story` 表示需求（绑定 Bits `task_type=issue`），`issue` 表示缺陷（绑定 Bits `task_type=bug`）；注意 Meego 的 `issue` 在此语义上等同缺陷，而非需求
- `--meego-type` 指定 Meego 工单类型：`bug` 或 `feature`（ID 模式必填）
- `--meego-project-key` 指定 Meego 项目标识，如 `larksuite`（ID 模式必填）
- `mr update --title` 更新 MR 标题；标题不要带 `[Feature]` / `[Optimize]` / `[Bug Fix]` 前缀，Bits 按 MR type 自动补，CLI 也会先剥掉已有前缀。`--title-content` 是 `--title` 的别名，同传时以它为准
- 剥掉前缀后为空的标题（`--title ""`、`--title-content ""`、`--title "[Feature]"`）抛 `BITS_INPUT_ERROR`，不会静默跳过；不改标题就不要传这两个参数
- Bits 会把新标题下推到绑定的 Codebase MR，标题无需额外同步；描述不下推，Bits 与 Codebase 各存一份
- `mr update --description` 更新 MR 描述，并默认把同一份描述写入绑定的 Codebase MR；传空串清空描述，`--no-sync-codebase` 只改 Bits 侧
- 只要传了 `--description`，JSON 输出就带 `codebase_description_sync`，`status` 为 `synced` / `skipped`（`reason`: `sync_disabled` / `no_codebase_binding`）/ `failed`（`reason`: `binding_lookup_failed` / `codebase_write_failed`，附 `error`，含 `message` / `code` / `hint` / `auth_command`）。Codebase 侧失败不影响命令退出码，与 `meego_bindings` 同一套上报方式，消费方需自行判读该字段
- `mr create --description` 创建时会把描述带到新建的 Codebase MR，无需额外同步；分叉只发生在创建之后的更新
- Bits 拒绝更新（非 2xx 响应或 envelope 报错）时抛 `BITS_MR_UPDATE_REJECTED`，此时 Bits 与 Codebase 两侧都不会被写入
- `mr update` 同样支持 `--meego` / `--meego-type` / `--meego-project-key`，用于给已经存在的 MR 追加绑定 Meego 工作项（解析规则与 `mr create` 一致），返回结果会带 `meego_bindings` 数组指明每条绑定的成功 / 失败原因；可重复传 `--meego` 一次绑多个
- `--app-id` 和 `--cloud-id` 用于传递 bits 空间鉴权 header（多主仓模式）；`--group-name` 在多主仓模式下是宿主仓的 host_group_name（可能与 bits 空间名不同）
- `mr status` 是客户端 BITS MR 的主入口；更稳定的程序化消费优先加 `--json`
- `mr packages` 查询 MR 关联的产物包（package groups），每个 group 包含多个 package（含可选 artifacts）；`--project-id` 为主仓 project_id（字符串），`--mr-iid` 为 MR 的 iid
- `mr publish-records` 查询 MR 下各子仓组件发布产物（OpenAPI `/openapi/merge_request/component/publish/record/list`）；`--mr-id` 同时支持 host MR id 与 sub MR id：host MR 会先用 `relation/list` 展开为所有子仓 MR 后并发查询，sub MR 直接单查；并发请求中单个子仓失败会被兜底写入 `sub_mrs[i].error`，不会让整体 fail-fast；host MR 实际无任何 sub-repo 时抛 `BITS_MR_NO_SUB_REPOS`
- `mr publish-records` 文本模式按子仓维度做 Summary 聚合：当一个子仓内所有组件的 `status` / `version_origin` / `version_final` / `version_base` / `release_info` / `log_url` / `pod_source` / `tt_repos` 完全一致时，提为子仓级 Summary，组件表只保留身份列（Name / Group / Module / ComponentID / PublishVersionID）；存在差异时会退化为完整列展开。`Release Window` 在缺失某一端时左/右用 `-` 兜底；`TT Repos` 超过 6 项以 `... (+N)` 截断。`-j/--json` 模式下保留全部原始字段（不截断、不聚合）
- `mr search` 适合按状态、作者、reviewer、source/target branch、mr_type 做列表筛选；`mr mine` 是带 author 过滤的快捷入口
- `mr status` 用来看整体状态、review 摘要和 pipeline 信息；`mr review-status` 聚焦 Review；`mr qa-status` 聚焦 QA
- 对于多仓合码，想拿完整 workflow / job 列表时，优先使用 `bits client workflow pipeline from-mr --include-dependencies`
- `--include-dependencies` 会同时展开 `CUSTOM_CI_MMR_HOSTS`（多主仓，`relation_type = mmr_host`）和 `CUSTOM_CI_MR_DEPENDENCIES`（多子仓 / 依赖仓，`relation_type = dependency`）
- 查询 MR 关联的 pipeline history 用 `bits client workflow pipeline list --mr-id <mr-id>`；默认使用后端返回范围，需要全量记录时加 `--all`；当前 OpenAPI 只暴露 `mrId` 和 `all`，不支持 CLI 侧分页参数
- `mr approve` / `mr disapprove` 用于审批动作；`mr remind-review` / `mr remind-qa` 用于催办动作
- `mr reviewer add` 给已有 MR 追加 reviewer；`--reviewer` 可重复或逗号分隔；`--role` 默认 `RD`；`--is-force` 强制覆盖；`--reason` 默认 `auto_add_current_developer`
- `mr reviewer remove` 从已有 MR 移除指定 reviewer；`--username` 为要移除的 reviewer 用户名
- `mr reviewer info` 查询 MR 的所有 reviewer 信息（含子仓）；`--mr-id` 必填
- `mr chat create` 为 MR 创建关联的 Lark 群聊；`--mr-id` 必填。**注意**：一个 MR 只会有一个关联群聊，第二次 create 仍会返回成功响应，但不会重新建群、也不会重新邀请 reviewer；如果群已被 `chat dismiss` 清空，请用 `mr chat add` 逐个补回 reviewer，不要再次 create
- `mr chat add` 向 MR 关联的 Lark 群聊中添加用户；`--mr-id` 和 `--username` 必填；`--member-type` 可选（如 `reviewer`、`developer`）
- `mr chat remove` 从 MR 关联的 Lark 群聊中移除用户；`--mr-id` 和 `--username` 必填
- `mr chat dismiss` 清空 MR 关联的 Lark 群聊成员（除 Bits Bot 外全部踢出，群聊本体保留）；`--mr-id` 必填；`--username` 可选（指定操作人）。dismiss 后想恢复成员请使用 `mr chat add` 逐个邀请，不要使用 `mr chat create`
- `mr review-status`、`mr approve`、`mr disapprove`、`mr remind-review`、`mr qa-status`、`mr remind-qa` 都支持两种定位方式：
  - `--mr-id`
  - `--project-id + --iid`
- 需要按客户端 Bits 维度做程序化查询时，优先使用 `bits mr ... --json`，不要自行拼装内部接口
- 如果命令报 token 缺失或鉴权失败，优先检查 `CLIENT_BITS_TOKEN` 是否已设置且权限已开通
- `component upgrade` 是客户端组件升级正式入口；payload 应符合正式 OpenAPI `req_schema`
- `bits client workflow` 适合查 workflow job / pipeline template / dev task pipeline；不会替代现有 `bits pipeline` 主域
- `bits client integration` 适合查集成区版本、封版报告、版本群、合入队列
- `bits client calendar` 适合查版本日历空间、事件和标记
- `component` 现已支持完整的组件生命周期查询，包括：`get-repo`、`search-repos`、`get-history-by-id` 等 14 个核心命令
- `--service-type` 支持：`PROJECT_TYPE_WEB`、`PROJECT_TYPE_TCE`、`PROJECT_TYPE_FAAS`、`PROJECT_TYPE_HYBRID`、`PROJECT_TYPE_TCC`、`PROJECT_TYPE_CRONJOB`、`PROJECT_TYPE_CUSTOM`；传入后会按对应项目类型自动解析 `projectUniqueId`
- `--change type=<type>` 对单条 change 生效并优先于全局 `--service-type`，用于区分相同 PSM 下的 TCE/TCC 等不同项目；未填写时才回退到 `--service-type` 或自动探测
- `--change lookup=<keyword>` 仅用于 `develop update --ensure-change-card` 的 AppCenter 缺失项目发现；`service=` 仍是必须精确匹配的 `projectUniqueId`。这适用于 opaque ID 无法直接搜索、但项目名能返回唯一候选的 HYBRID→GECKO 元数据；最终 Bits 项目类型仍为 HYBRID，不会放宽为 fuzzy first-result
- `--change` 支持可选的 `scm=<name>` 键，用于指定非主 SCM 依赖；省略时默认绑定主 SCM（`isMain === true`），行为与之前一致
- 同一个 service 可以重复传多条 `--change`，每条点名一个 `scm=`，`develop create` 会逐条应用；同一 service 内 repo + sourceBranch + targetBranch 完全相同的 Change Card 只保留一张（不同 service 的卡片不会合并）。monorepo 里一次改动影响一个项目的多条 SCM 依赖时用这种写法，不必先创建再 `develop update` 补绑
- `--change version=<scmVersion>`（仅 `develop create` 生效，`develop update` 传入会报错）与 `branch=` 互斥，且必须搭配 `scm=<name>`：把该 SCM 依赖锁到指定的已发布版本（`devMode: Version` / `pubBase: SCM_PUB_BASE_VERSION`），不生成 Change Card。用于本次不改这条依赖、但要显式指定版本（例如与线上运行版本对齐，线上版本可用 `tce service get --psm <psm>` 的 `repo_info` 查）
- `--change` 支持可选的 `mr=<iid>` 键：`develop create` 会写入新任务的卡片；`develop update` 只有同时传 `--ensure-change-card` 且确实追加新卡片时才生效，其他情况会提示该值被忽略。已有卡片需用 `develop inspect-changes` 找到 change id 后调用 canonical `develop change bind-mr`；顶层 `develop reuse-mr` 仅保留命令路径兼容。Change Card 已有目标分支时旧调用不需新增参数；历史空目标分支卡片必须显式传 `--target-branch`。它等价于 Bits Web UI 提示 "An unfinished MR already exists" 时点击 "use directly"；省略时使用 `iid=0`；`mr=` 必须是正整数
- `develop create --task-type` 支持 `feature` / `bug`；传 `--task-type bug` 会创建 Bugfix 类型研发任务。省略时沿用模板任务的 `task.type`，模板未提供时默认 `feature`
- `develop update --change` 默认保持原有项目选择语义，只更新任务内已存在的点名项目，但会回传最新 `changes/versionCode` 防止完整快照接口清空已有 Change Card。只有显式传 `--ensure-change-card` 才按最新 `changes/projects/versionCode` 做增量合并：保留未点名项目、按需补项目，并为缺失的 repo/branch 追加 Change Card；正式写入后使用 `develop inspect-changes --dev-id <id>` 核对结果
- `develop create` 使用多个 `--change` 且服务分属不同模板时，必须传 `--space-id` 以便跨模板解析项目；否则只会从首个匹配模板中取项目，未覆盖的服务将报错
- `--change` 支持可选的 `from=<templateDevId>` 键（仅 `develop create` 生效），用于从指定模板 dev task 拉取该 service 的项目配置，而不是靠 `--space-id` 按 service 名自动搜索模板。适用于目标项目组合分散在不同模板的场景（例如已有 A&B、A&C 模板，想一次建出 B&C 任务）——按 projectUniqueId 自动搜索通常搜不到，`from=` 直接锁定模板；`from=` 必须是正整数
- `develop create --release-ticket-id`（仅 `develop create` 生效，正整数）用于"在发布车上提 bugfix"：CLI 会用发布单 ID 拉取 `integrationId` 与 release train 分支（来源 `releaseTicket.integrationId` 与 `releaseTicket.workflowConfig.releaseTicketConfig.branchingModelConfig.integrationBranch.name`），并注入 `task.sourceBranchCheckoutFrom`、顶层 `integrationId`/`releaseTicketId` 以及每个 change 的 `targetBranch`，使任务作为 Bugfix 加入发布车而不是只落到常规 integration 桶。通常配合 `--task-type bug`；若 change 未显式写 `target=`，`targetBranch` 默认取 release train 分支。注意这与 `develop bind-release`（对已有任务批量绑常规集成通道）语义不同：走 bugfix 通道要在 create 阶段就带 `--release-ticket-id`
- `pipelines set` 是整体替换（PUT 语义），调用方必须基于 `pipelines get` 拿到的最新 DSL 改后再写回；命令 PUT 之前会自动把当前 DSL 备份到 `os.tmpdir()/bytedcli/bits-pipeline-backup/<id>-<ts>.json`
- `pipelines set` 会解包成功的 `pipelines get --json` 完整输出；输入携带的外层 `pipelineId` / `spaceId` 必须分别匹配命令目标和实时目标 space，否则在备份和 PUT 前拒绝。纯 DSL 或不带身份字段的 PUT body 仍可使用。
- `pipelines set` 会在 PUT 前把所有空 i18n 字段（`{value: "", lang?, texts?}` 的 `StringInMultiLang`）置为 `null`，因为 BITS 校验器会拒绝 `value` 为空字符串但 GET 接口又会返回这种 sentinel 值；被剥的路径列在 `data.sanitizedI18nPaths`，最常见的是 `varGroup.description`
- `pipelines set` 的版本字段是 `pipelineVersion.version`（一个 wrapper 对象），不是裸数字；CLI 已经做了 unwrap，正常情况下 `data.fromVersion / data.toVersion` 应该连续递增

## References

- `references/autocase.md` —— AutoCase / Verse scenario plan 的对象 ID、运行查询与等待、报告导出和已验证的平台限制
- `../../invocation.md`
- `references/release-tcc-draft-target.md` —— **发布单 TCC Draft 与 deploy target 指南**：正文脱敏落盘、精确选择、内容/快照 SHA-256 漂移门禁、完整目标数组保留、回读和流水线边界。**执行 `bits release tcc-config get/create/update/delete` 或 `bits release tcc-deploy-target get/update` 前必须读取此文档**。
- `references/release-tcc-import.md` —— **发布单 TCC 导入、物化与流水线启动指南**：普通 source config 与 PPE 环境导入、防漂移选择、确认门禁、sync 持久化回读和 TCC run build 回读。**执行 `bits release tcc-config import`、`bits release pipeline sync-tcc` 或包含 TCC 项目的 `bits release pipeline run` 前必须读取此文档**。
- `references/release-playbook-faas.md` —— **BITS 发布单 FaaS 上线 Playbook（实战沉淀）**：FaaS 流水线 `faas_deploy_config` 模板变量物化机制（只在发布确认表单提交时物化，直调 run 必炸）、解锁 can-run 固定顺序、125536 dev 指针钉取消单绕法、发布确认流 4 步序列、本地直调 HTTP 端点、发布后日志验证。**FaaS 发布（create_faas_upgrade_ticket 原子）前先读此文档**，避免 RollingPercentage 模板解析失败。


### TCC 控制面与写后确认

- 发布目标的 `--source-control-plane` / target spec `control-plane`，以及 release TCC 命令的 `--control-plane` 使用 `cn`、`i18n`、`eu-ttp`、`us-ttp`、`i18n-bd`。`develop tcc-config create --control-plane` 使用对应数字 `1`、`2`、`3`、`4`、`6`；例如 `I18N_BD` 使用 `6`，语义名称为 `i18n-bd`。不要套用其他 Bits 资源的数字枚举。
- `--source-control-plane` 定位已导入配置的来源；`--boe-target` / `--ppe-target` / `--prod-target` 中的 `control-plane` 指定部署目标，两者可以不同。Draft 的 `--control-plane`（支持该参数的命令）也是来源控制面。全局 `--site` 不选择 TCC 来源或目标。
- 非默认目录的 change item 若返回 `dirId=0`，CLI 按 namespace、来源控制面、region、directory 唯一查目录，并核对源配置与草稿的真实 ID 和路径。目录歧义、缺少源配置或 ID/路径冲突会阻止继续；部署参数使用核验后的真实 ID。
- 草稿或部署目标 PUT 返回不明确的响应时，CLI 不重试写入，而是只读回查。草稿必须版本递增、内容和 metadata 一致；部署目标必须 storage version 递增、各环境目标一致，才确认成功。无法确认时返回 `*_OUTCOME_UNKNOWN`，先用对应 `get` 检查当前状态，禁止盲目重试。
