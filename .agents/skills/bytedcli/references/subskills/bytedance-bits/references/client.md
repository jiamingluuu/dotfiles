# bytedcli BITS Client 子域

`bits client` 用来承接客户端子域，不和现有的 `bits mr`、`bits component`、`bits pipeline` 对象域混在一起。
其中 workflow 相关 OpenAPI 现在只通过 `bits client workflow` 暴露，旧的根级 `bits workflow` 入口已经移除。

客户端 `/change-review/<changeId>` 开发任务的只读解析和状态查询位于根级
`bits devtask parse|get`。它先将 change-review 的 `changeId` 解析为 `devBasicId`，再读取
SMR 开发任务摘要；不要把 `changeId` 直接传给 `bits develop get --dev-id`。`parse` 是纯本地
解析；`get` 走页面同源 Web API，使用 ByteCloud 用户 JWT，不读取 `CLIENT_BITS_TOKEN`，也不
依赖浏览器 SSO 会话。

鉴权分三类：`workflow` / `integration` / `calendar` / `release-record` 走 Bits OpenAPI token（`CLIENT_BITS_TOKEN`）；
`package` / `bm` 走 ByteCloud 用户 JWT；`release-workflow` 是版本发布页 Web API，同时需要 ByteCloud 用户 JWT 与浏览器 SSO 会话。

## 目录

- [workflow](#workflow) — workflow job / pipeline / 开发任务流水线
- [integration](#integration) — 集成区版本、合入队列、封版报告
- [bm](#bm) — 按版本查询 RD 值班负责人
- [calendar](#calendar) — 版本日历 workspace / event / mark
- [release-record](#release-record) — 客户端版本发布记录
- [release-workflow](#release-workflow版本发布流程) — 版本发布 DAG、阶段/节点状态和精确节点触发
- [package（独立打包）](#package独立打包) — 构建配置、打包任务、产物下载

## 命令树概览

```bash
bytedcli bits client workflow ...
bytedcli bits client integration ...
bytedcli bits client bm ...
bytedcli bits client calendar ...
bytedcli bits client release-workflow ...
bytedcli bits client package ...
```

## workflow

适用场景：

- workflow pipeline 查询
- workflow job 查询、重试、取消、跳过、更新
- pipeline template 触发
- 开发任务流水线列表和 quick-run

结构说明：

- `bits client workflow pipeline`
  - 面向 pipeline 级操作
  - 典型输入：
    - `pipelineId`
    - `mr-id`
    - template 触发参数
  - 常见用途：
    - 查 pipeline 详情
    - 读取 pipeline template 触发参数结构
    - 触发 pipeline template
    - 从 MR 反查最新 pipeline
    - 按 MR 列出 pipeline history
- `bits client workflow job`
  - 面向 job 级操作
  - 典型输入：
    - `jobId`
  - 常见用途：
    - 查 job 详情
    - 获取 job 日志下载链接（log-url，走控制台 BFF，对 legacy build job 也有效）
    - 下载 job 完整构建日志到本地文件（download-log，日志可能 100MB+，流式落盘）
    - retry / cancel / skip
    - trigger / trigger-template
    - update / update-result / update-msg / update-url
    - add-artifacts
- `bits client workflow dev`
  - 面向开发任务挂载的流水线
  - 典型输入：
    - `dev_basic_id`
    - `task_name`
    - `space_id`
  - 常见用途：
    - 列出开发任务某个 task 下的 pipelines
    - 查看 workflow 主流水线
    - quick-run 开发任务流水线

选择建议：

- 你已经拿到 `pipelineId` 时，用 `workflow pipeline`
- 你已经拿到 `jobId` 时，用 `workflow job`
- 你要围绕某个开发任务 `dev_basic_id` 操作时，用 `workflow dev`
- 你手里只有 `mr-id`，但想看 pipeline，优先用 `workflow pipeline from-mr`
- 你要查看 MR 关联的 pipeline 历史记录时，用 `workflow pipeline list --mr-id <mr-id>`

常用示例：

```bash
# pipeline 详情
bytedcli bits client workflow pipeline get --pipeline-id 123

# 读取 pipeline template 触发参数结构
bytedcli --json bits client workflow pipeline get-template-params --template-id 123

# 触发 pipeline template（简单字段）
bytedcli bits client workflow pipeline trigger-template \
  --template-id 123 \
  --app-id 456 \
  --operator demo.user \
  --trigger-type template_custom

# 触发 pipeline template（完整 body）
bytedcli bits client workflow pipeline trigger-template \
  --body-file payload.json

# 从 MR 找最新 pipeline
bytedcli bits client workflow pipeline from-mr --mr-id 123456

# 从 MR 查询 pipeline history
bytedcli bits client workflow pipeline list --mr-id 123456
bytedcli bits client workflow pipeline list --mr-id 123456 --all
# 默认使用后端返回范围；--all 请求后端返回全量历史记录。当前 OpenAPI 只暴露 mrId/all，不支持 CLI 侧分页参数。

# job 详情 / 日志链接 / 下载日志 / 重试
bytedcli bits client workflow job get --job-id 123
bytedcli bits client workflow job log-url --job-id 123
bytedcli bits client workflow job download-log --job-id 123 --output ./job-123.log
bytedcli bits client workflow job retry --job-id 123 --env '{"key":"value"}'

# 取消 / 跳过
bytedcli bits client workflow job cancel --job-id 123 --reason "manual stop"
bytedcli bits client workflow job skip --job-id 123 --username demo.user --force true

# Pipeline jobRun 强制跳过（jobRunId，不是 legacy jobId）
bytedcli bits job-run force-skip \
  --job-run-id 123456789 \
  --pipeline-run-id 987654321 \
  --space-id 12345 \
  --reason "TeslaX skipped for this launch"

# 触发 job
bytedcli bits client workflow job trigger \
  --type service \
  --name demo \
  --operator demo.user \
  --service-name demo.service

# dev task 下流水线列表
bytedcli bits client workflow dev list-pipelines \
  --dev-basic-id 123456 \
  --unique-type 1 \
  --task-name DemoTask

# dev task quick-run
bytedcli bits client workflow dev quick-run \
  --username demo.user \
  --dev-basic-id 123456 \
  --task-name DemoTask \
  --space-id 12345
```

参数约定：

- 简单接口尽量直接展开成 flag
- 复杂结构统一支持 `--body` / `--body-file`
- `--env`、`--allow-info`、`--pending-info` 这类复杂对象可直接传 JSON
- `--callback-urls`、`--depends-on`、`--control-planes` 支持 JSON 数组或逗号分隔

特别说明：

- `bits client workflow` 走的是客户端 OpenAPI，不等价于平台原生 `bits pipeline`
- `bits client workflow job` 里的 `jobId` 不是 `bits job-run` 使用的 `jobRunId`
- `jobId` 通常出现在 `https://example.bytedance.net/space/legacy/build/logs?jobId=<jobId>` 这类 legacy workflow 链接中
- 要跳过平台 Pipeline 页面里的 `jobRunId`，用 `bits job-run force-skip`，不要用 `bits client workflow job skip`
- `bits client workflow dev quick-run` 适合客户端研发的开发任务自测，不适合替代平台主流水线编排

## integration

适用场景：

- 查某个集成区版本
- 查集成区下 MR 列表、合入队列、正在合入中的 MR
- 查或生成封版报告
- 查或创建版本群

常用示例：

```bash
# 查集成区信息
bytedcli bits client integration info \
  --group-name douyin_harmony \
  --version 1.2.3

# 查版本列表
bytedcli bits client integration version-list \
  --group-name douyin_harmony \
  --page-size 10

# 查指定版本下 MR
bytedcli bits client integration mrs \
  --app-id 12345 \
  --version 1.2.3 \
  --mr-state opened

# 查合入队列 / 正在合入
bytedcli bits client integration queue \
  --group-name douyin_harmony \
  --target-branch rc/develop
bytedcli bits client integration merging \
  --group-name douyin_harmony

# 报告
bytedcli bits client integration report get \
  --group-name douyin_harmony \
  --version 1.2.3 \
  --snapshot latest
bytedcli bits client integration report snapshot \
  --group-name douyin_harmony \
  --version 1.2.3
bytedcli bits client integration report generate \
  --group-name douyin_harmony \
  --version 1.2.3 \
  --temporary false

# 版本群
bytedcli bits client integration version-group-get \
  --group-name douyin_harmony \
  --version 1.2.3
bytedcli bits client integration version-group-create \
  --group-name douyin_harmony \
  --version 1.2.3 \
  --is-binding false \
  --group-title "v1.2.3 version group"
```

## bm

按精确版本查询 RD 值班负责人，已创建排班优先，无匹配再查 BITS 服务端预测的未来排班。

```bash
bytedcli --json bits client bm get --space-id 123456 --version 1.2.3
```

- `--space-id` 与 `--version` 必填；输入页面 URL 时，先从 `/devops/<space-id>/` 提取空间 ID。
- 使用 ByteCloud 用户 JWT，无需浏览器或 `CLIENT_BITS_TOKEN`。
- 返回 `version`、`emails`、`source`；`source=created|future`，future 是 BITS 服务端预测，不是本地轮值推算。
- `source=null` 表示两表均无匹配；有来源但 `emails=[]` 表示未分配负责人，不以未来预测覆盖；请求失败直接报错。

## calendar

适用场景：

- 查版本日历 workspace
- 查某个 event / 下一个 event / 某日 segment
- 创建或更新事件
- 维护 mark

常用示例：

```bash
# workspace
bytedcli bits client calendar workspace list
bytedcli bits client calendar workspace active --time 1711929600
bytedcli bits client calendar workspace get --workspace-id 12345

# event
bytedcli bits client calendar event get --event-id 123
bytedcli bits client calendar event query \
  --time 1711929600 \
  --group-name douyin_harmony
bytedcli bits client calendar event next \
  --workspace-id 12345 \
  --time 1711929600

# event create / update
bytedcli bits client calendar event create \
  --track-id 123 \
  --workspace-id 456 \
  --name freeze \
  --start-date 1711929600 \
  --segments '[{"name":"freeze","length":1}]'

bytedcli bits client calendar event update \
  --event '{"event_id":1,"track_id":2,"name":"freeze","start_date":"1711929600"}' \
  --segments '[{"segment_id":1,"name":"freeze","length":1}]'

# mark
bytedcli bits client calendar mark add \
  --date 20260414 \
  --event-content "freeze" \
  --event-type-id 2
bytedcli bits client calendar mark delete --mark-id 123
```

## release-record

查询客户端版本发布记录（官方 / 灰度 / 技术灰度版本、update version、发布时间）。

```bash
# 查发布记录（--bits-app-id 必填；抖音 iOS 为 112801）
bytedcli bits client release-record list --bits-app-id 112801

# 按发布类型过滤：OFFICIAL / GRAY / TECH_GRAY
bytedcli bits client release-record list --bits-app-id 112801 --type OFFICIAL

# 按版本名 / 发布平台过滤，并分页
bytedcli bits client release-record list \
  --bits-app-id 112801 \
  --type GRAY \
  --version-name 39.7.0 \
  --release-platforms BITS_RELEASE_RULE \
  --page 1 \
  --page-size 20
```

## release-workflow（版本发布流程）

对应客户端版本发布页`/release/workflow/versionPublish/detail/<integrationId>/workflow`。它读取版本DAG并按“阶段名+节点名”唯一定位一个执行节点，适合触发版本节奏里的灰度包、正式包等既有节点；它不是裸触发pipeline template，也不是独立打包。

```bash
# 读取版本DAG；也可以直接传完整版本发布页URL
bytedcli bits client release-workflow get \
  --app-id 987654321 \
  --version 1.2.3

bytedcli bits client release-workflow get \
  --url "https://bits.bytedance.net/devops/39000000001/release/workflow/versionPublish/detail/50001/workflow?appId=987654321&product_version=1.2.3"

# 默认只预览将触发的唯一节点
bytedcli bits client release-workflow trigger \
  --app-id 987654321 \
  --version 1.2.3 \
  --stage "正式阶段" \
  --atom "灰度包"

# 确认预览无误后才真实提交
bytedcli bits client release-workflow trigger \
  --integration-id 50001 \
  --stage "正式阶段" \
  --atom "灰度包" \
  --yes
```

安全与状态约定：

- `trigger`默认dry-run；只有显式`--yes`才调用节点触发接口
- 阶段名和节点名都做精确、唯一匹配；零匹配或多匹配都拒绝提交
- 节点已是`running`、`success`或`skipped`时直接复用状态，不重复触发
- 节点是`failed`、`stopped`或未知状态时失败关闭，不自动retry
- 写请求遇到登录跳转时立即停止，不跟随跳转、不重放写操作
- Web API需要浏览器SSO会话；缺失或过期时先执行`bytedcli --site cn auth login --session`
- 本地CLI可通过SSO会话访问该页面链路；FaaS环境不能默认复用个人浏览器会话，部署前仍需单独确认服务身份或会话注入方案

## package（独立打包）

认证走 ByteCloud SSO（`bytedcli auth login`），不需要 Bits OpenAPI token。

对应客户端空间「工具集 / 独立打包」页面：

```
https://bits.bytedance.net/devops/<workspace>/rd-service/tools/custom_build?devops_space_type=client&devops_space_old_id=<app-id>
```

`--app-id` 就是 URL 里的 `devops_space_old_id`。

### 三种配置来源

| `--source` | 页面名称      | 说明                                                       |
| ---------- | ------------- | ---------------------------------------------------------- |
| `job`      | Job 构建      | 应用自身的编译配置，参数骨架来自其引用的云构建模版         |
| `pipeline` | Pipeline 构建 | 客户端 Pipeline 模版，触发时固定走 `template_trigger` 形态 |
| `general`  | 通用配置      | jenkins / viper / gitlab 老配置                            |

### 查配置

```bash
# 三类配置汇总（默认只展示页面同款的 CUSTOM / DEVELOP 场景）
bytedcli bits client package config list --app-id 987654321

# 只看某几类；--all-scenarios 展示被场景过滤掉的 Job 构建配置
bytedcli bits client package config list --app-id 987654321 --source job,pipeline
bytedcli bits client package config list --app-id 987654321 --source job --all-scenarios

# 查单个配置可覆盖的参数骨架（组装 --params 用）
bytedcli bits client package config get --app-id 987654321 --source job --config-id 10001
bytedcli bits client package config get --app-id 987654321 --source pipeline --config-id 10002
```

### 触发打包

`trigger` 默认 dry-run，只打印将提交给 `/api/mr_package/build/trigger_task` 的 payload；确认后显式加 `--yes` 才真正触发。

```bash
# Job 构建：--config-id 取 config list 里的 Config ID
bytedcli bits client package trigger \
  --app-id 987654321 \
  --source job \
  --config-id 10001 \
  --branch release/1.2.0 \
  --changelog "example build" \
  --yes

# 覆盖构建参数（参数名来自 config get）
bytedcli bits client package trigger \
  --app-id 987654321 \
  --source job \
  --config-id 10001 \
  --branch release/1.2.0 \
  --params '{"MAIN_GIT_BRANCH":"release/1.2.0"}' \
  --yes

# Pipeline 构建：--git-url 必填，--config-id 是 pipeline 模版 ID
bytedcli bits client package trigger \
  --app-id 987654321 \
  --source pipeline \
  --config-id 10002 \
  --branch release/1.2.0 \
  --git-url git@code.byted.org:example-group/example-repo.git \
  --remark "example run" \
  --yes
```

`--project-id` 默认取应用主仓，跨仓触发时才需要显式传。

### 任务与产物

```bash
# 任务列表；--mine 按当前 bytedcli 登录用户过滤
bytedcli bits client package task list --app-id 987654321 --mine --page-size 10
bytedcli bits client package task list --app-id 987654321 --status success --branch release/1.2.0

# 任务详情，含产物与 dSYM / LinkMap 等附属产物
bytedcli bits client package task get --task-id 20001

# 取消任务，默认 dry-run
bytedcli bits client package task cancel --task-id 20002 --yes

# 下载产物：不加过滤取第一个包，--type 选附属产物
bytedcli bits client package download --task-id 20001
bytedcli bits client package download --task-id 20001 --type dsym --output ./demo.dSYM.zip
bytedcli bits client package download --task-id 20001 --artifact-id 30001
```

构建日志复用 workflow job 命令，`--job-id` 取任务详情里的 `jobId`：

```bash
bytedcli bits client workflow job download-log --job-id 40001
```

### Agent Guidance

- 触发前先跑一次不带 `--yes` 的 `trigger` 看 payload，确认 `config_type` 与 `params` 符合预期
- Pipeline 来源触发后拿到的是 `pipelineId` 而不是 `jobId`，构建详情在 pipeline DAG 页面
- 产物下载走任务详情里的直链，不要用 `get_package_url`：该接口按 `package_id` 返回的链接与任务产物不对应
- 任务状态是 `created` / `running` / `success` / `failed` / `canceled`；只有成功任务带产物
- `--source general` 的 `config_type` 取配置自身的 `ci_type`（0 gitlab / 1 jenkins / 2 viper / 3 bits）；配置未声明 `ci_type` 时命令直接报错，不会猜一个默认值提交
- dry-run 与 JSON 输出里的 `jenkins_info.token` 等凭据字段已脱敏，真正提交的 payload 仍带原值
- `--params` 里的键不会覆盖 `--branch` / `--git-url` / `--remark`：这三个显式参数最终生效
- `--git-url` 与 `--remark` 只在 `--source pipeline` 下有效，传给其他来源会直接报错而不是被忽略
- `package trigger --source pipeline` 会在独立打包页登记任务并产出可下载产物；只想裸触发 pipeline 模版用 `bits client workflow pipeline trigger-template`

## Notes

- `bits client` 是客户端子域，不替代现有 `bits pipeline`
- 复杂 payload 优先用 `--body-file`
- 需要结构化输出时，加全局 `--json`
