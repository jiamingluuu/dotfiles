---
name: bytedance-volcano
description: >-
  使用火山引擎 CLI（ve）操作 ECS、VPC、CLB、ALB、RDS、Redis、CR、DBW（Database
  Workbench）、VKE、Kubernetes Deployment/Pod/Service/CRD 与 Pod logs、veFaaS 等资源，
  以及 Resource Center 跨产品资源发现与统计。
  ve 已支持的 Action 全部使用 ve；火山方舟 Ark foundation models/inference endpoints/API keys、
  日志服务 TLS、对象存储 TOS、CtxSearch 或明确缺少安全等价能力时使用 bytedcli volcano。
  用户提到火山引擎、Volcengine、ve 命令、登录、云资源操作或 ve 报错时使用。
license: MIT
metadata:
  openclaw:
    requires:
      bins:
        - ve
        - bytedcli
    envVars:
      - name: VOLCENGINE_ACCESS_KEY
        required: false
        description: AK/SK 认证使用的 AccessKey，可替代 ve login
      - name: VOLCENGINE_SECRET_KEY
        required: false
        description: AK/SK 认证使用的 SecretKey
      - name: VOLCENGINE_SESSION_TOKEN
        required: false
        description: 临时凭证可选的 STS SessionToken
      - name: VOLCENGINE_REGION
        required: false
        description: 默认地域，未设置时使用 cn-beijing
      - name: VOLCENGINE_ENDPOINT
        required: false
        description: --force 调用和扩展脚本未定义产品 endpoint 时使用的兜底地址
      - name: VOLCENGINE_PROFILE
        required: false
        description: 扩展脚本读取 ve 凭证时使用的可选 profile
      - name: VOLCSTACK_PROFILE
        required: false
        description: VOLCENGINE_PROFILE 的兼容别名
      - name: VOLCENGINE_CLI_CONFIG_FILE
        required: false
        description: ve 配置文件路径，默认 ~/.volcengine/config.json
      - name: VOLCENGINE_LOGIN_CACHE_DIRECTORY
        required: false
        description: 扩展脚本读取 Console Login 缓存时使用的可选目录
      - name: VOLCENGINE_CLI_DOWNLOAD_BASE_URL
        required: false
        description: scripts/install_ve.sh 下载 release 的基础地址
      - name: VOLCENGINE_CLI_SKIP_SKILLS
        required: false
        description: 设为 1 时，安装 ve 后不运行 ve skills update
      - name: VE_VERSION
        required: false
        description: scripts/install_ve.sh 安装的指定 ve 版本
      - name: VE_INSTALL_DIR
        required: false
        description: scripts/install_ve.sh 的安装目录
      - name: VE_LOGIN_URL_TIMEOUT
        required: false
        description: 等待 ve 输出设备码登录 URL 的秒数，默认 30
      - name: VE_LOGIN_APPROVAL_TIMEOUT
        required: false
        description: Babi 自动批准后等待 ve 登录完成的秒数，默认 60
---

# 火山引擎 CLI

通过 `ve` 调用火山引擎 OpenAPI；ve 未覆盖或缺少安全等价能力时使用 bytedcli 增强实现。

需要调用 bytedcli 增强入口但本机没有 `bytedcli` 时，先阅读 [bytedcli 通用调用方式](../../invocation.md)；bytedcli 命令失败时阅读 [通用排障](../../troubleshooting.md)。

## 入口选择

| 场景                                                                        | 默认入口                         | 原因                                                           |
| --------------------------------------------------------------------------- | -------------------------------- | -------------------------------------------------------------- |
| ECS、VPC、CLB、ALB、RDS、Redis、IAM、KMS、DBW、VKE、veFaaS 等已收录 OpenAPI | `ve`                             | ve 已支持的 Action 全部优先使用                                |
| 火山方舟 Ark 模型、推理接入点、API Key                                      | `bytedcli volcano ark ...`       | `ve` 未覆盖当前所需控制台能力                                  |
| TLS project/topic/index/log/trace                                           | `bytedcli volcano tls ...`       | 当前 `ve` 没有 TLS 命令                                        |
| TOS bucket/object 查询与下载                                                | `bytedcli volcano tos ...`       | 当前 `ve` 没有 TOS 命令，bytedcli 可用 Babi Session 换临时凭证 |
| CtxSearch scene/API Key                                                     | `bytedcli volcano ctxsearch ...` | ve 未收录 CtxSearch metadata 与环境路由语义                    |
| Resource Center 服务状态、类型目录、资源搜索与统计                          | `ve resourcecenter ...`          | 四个只读 Action 均已收录，详见产品说明                         |
| DBW 本地 SQL 文件、VKE Secret 默认脱敏、VKE TLS 离线日志                    | 对应 bytedcli fallback           | ve 没有文件参数、默认脱敏或跨服务编排的安全等价能力            |

不要因为 bytedcli 仍保留其他 Volcano 命令就优先使用它们；ve 已支持的 Action 一律从 `ve` 开始，只有 reference 明确标注无安全等价能力时才 fallback。

## 0. 安装或升级 ve

要求 `ve >= 1.1.5`，并且 `ve login --help` 必须包含 `--no-browser`。

```bash
ve version
ve login --help
```

不满足要求时优先使用 npm：

```bash
env VOLCENGINE_CLI_SKIP_SKILLS=1 \
  npm install -g @volcengine/cli@latest \
  --registry=https://registry.npmjs.org
```

没有 Node.js 或 npm 不可用时，使用本 skill 自带、可审计的 `scripts/install_ve.sh`；不要下载远程 shell 后直接管道执行。安装器校验发布包 SHA-256，默认跳过 `ve skills update`，避免额外安装英文 `volcengine-cli` 并与本地化入口重复：

```bash
scripts/install_ve.sh
```

只有用户明确要求安装 ve 官方 skills 时，才为该脚本设置 `VOLCENGINE_CLI_SKIP_SKILLS=0`。

安装器会读取 CDN 最新版本、下载与当前 OS/CPU 匹配的压缩包、校验 `SHA256SUMS`，优先安装到 `/usr/local/bin`，否则安装到 `~/.local/bin`，不会调用 `sudo`。它还支持 `--version`、`--install-dir`、`--dry-run` 及对应环境变量。

## 1. 每次会话开始时初始化

### 系统参数

每个 `ve <service> <Action>` 都可在 Action 后使用以下双连字符参数：

| 参数                                     | 用途                                     |
| ---------------------------------------- | ---------------------------------------- |
| `--profile <name>`                       | 仅本次调用使用指定 profile               |
| `--region <region>`                      | 仅本次调用覆盖地域                       |
| `--endpoint <host>`                      | 覆盖 endpoint                            |
| `--lang EN\|ZH`                          | 设置帮助和错误语言                       |
| `--version <YYYY-MM-DD>`                 | 指定 API 版本；`--force` 时必填          |
| `--method GET\|POST`                     | 指定 HTTP 方法                           |
| `--force`                                | 跳过本地 metadata 校验；只能写 `--force` |
| `--output <fmt>` / `--query <jmespath>`  | 输出格式与结果投影                       |
| `--header Name=Value` / `--body '{...}'` | 自定义 header 或 JSON body               |

OpenAPI 参数使用 PascalCase，例如 `--Region`、`--InstanceIds.1`；系统参数使用小写。只有 API 自己也定义了完全同名的小写参数时，系统参数才写成三个连字符，例如 `---query`，其他场景不要使用三个连字符。

### 固定本次会话的 profile

Agent 不得自行选择 profile。

- 用户未指定 profile：直接使用默认解析，先运行 `ve sts GetCallerIdentity`。
- 用户明确指定 profile：后续所有 `ve` 和扩展脚本调用都沿用该 profile。
- 不得根据 profile 名、列表顺序、最近使用时间或任务内容猜测身份。
- 默认身份不符合任务风险时，只列候选 profile 名并让用户选择。
- `--region` 只改变本次请求地域，不会改变 profile 绑定的账号。

```bash
ve sts GetCallerIdentity
```

成功时向用户说明当前账号与地域。失败或任务中途出现 session/refresh token 过期时，执行下面的 Babi 自动登录。

### 默认登录：Babi 自动批准 ve 设备码

仅在用户明确要求登录，或已批准的火山任务因缺少凭证无法继续时执行。默认使用用户指定地域，否则使用 `VOLCENGINE_REGION`，再否则使用 `cn-beijing`。

前置条件：

```bash
bytedcli auth login
bytedcli volcano auth list-accounts
bytedcli volcano auth config --volc-account-id <account-id>
```

从 `list-accounts` 的同一行取得账号 ID 和 Babi 账号名称。后续 `<babi-name>` 必须使用该名称，不能用 account ID 替代。

执行：

```bash
scripts/ve_login_babi.sh \
  --region cn-beijing \
  --profile <babi-name> \
  --volc-account-id <account-id>
```

脚本会完成以下步骤：

```text
检查 ve >= 1.1.5 且支持 --no-browser
→ 启动 ve login --no-browser --lang en --region <region> --profile <babi-name>
→ 从 ve 输出的验证 URL 解析 trace_id
→ 用 bytedcli 内部保存的 Babi 火山 Session 批准该 TraceId
→ 等待 ve 轮询并缓存 STS
→ ve sts GetCallerIdentity 验证结果
→ ve configure profile --profile <babi-name>
```

`ve login --profile` 只指定登录结果写入哪个 profile，不负责切换当前 profile；最后一条 `ve configure profile` 必须在登录落盘后执行。`verify` exit 13 也表示登录已经落盘，因此仍需切换 profile，再处理网络问题。

新版 bytedcli 通过 `volcano auth approve-device` 在进程内使用 Cookie；兼容旧版命令面的脚本 fallback 也只通过已安装 bytedcli 的 auth 模块取得登录态，并严格校验 `console.volcengine.com`。两条路径都禁止读取 Cookie 文件，或把 Cookie 打印、写入 argv、环境变量和临时文件。`approve-device` 默认只预览脱敏 payload，完整 TraceId 也不进入输出或 HTTP trace；真实提交必须带 `--yes`。登录脚本在用户已经请求登录的前提下代为传入 `--yes`。

登录脚本会向支持该参数的 bytedcli 传递 `--user-code <device-code>`，先执行 `submitUserCode`，再携带更新后的 CSRF Cookie 和签名调用 `confirmDeviceAuthorization`。手动调用也应同时传 `--trace-id` 和 `--user-code`；仅传 TraceId 适用于已经提交过设备码的请求。Passport 的确认成功响应可能只包含 `ResponseMetadata.RequestId`；仍须拒绝空对象、非零 Code、非空 Error、`success:false` 和 `Approved:false`。HTTP 401 最多刷新同一 Babi 账号的 session 并重试一次，403 或业务拒绝不会触发刷新。

如果自动批准失败，完整阅读 [控制台登录说明](references/console-login.md)，使用 `scripts/ve_login_remote.sh` 把设备码链接交给用户手动批准。不要直接运行孤立的 `ve login`，否则 Agent 工具调用结束时可能杀死轮询进程。

### 备选：AK/SK

CI/CD 或用户明确选择 AK/SK 时：

```text
bytedcli volcano auth config \
  --access-key-id <AK> \
  --secret-access-key <SK>

# bytedcli 会同步执行：
ve configure set --profile bytedcliak --mode ak --region cn-beijing \
  --endpoint open.volcengineapi.com \
  --access-key <AK> --secret-key <SK>
ve configure profile --profile bytedcliak
```

临时凭证在 bytedcli 命令中追加 `--session-token <TOKEN>`，该值会同步写入 `bytedcliak`。也可以只在当前 shell 设置 `VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`、`VOLCENGINE_REGION` 和可选的 `VOLCENGINE_SESSION_TOKEN`；环境变量不会持久化或切换 profile。

如果此前保存过默认 Babi account ID，配置 AK/SK 会保留它：ve current profile 切到 `bytedcliak`，但 bytedcli 资源命令仍沿用既有的“保存的 Babi account ID 优先于保存的 AK/SK”规则。需要让单条 bytedcli 资源命令使用 AK/SK 时显式传 `--access-key-id` / `--secret-access-key`；Ark 继续使用保存的 Babi account ID。

支持 OpenAPI 的 bytedcli 命令也读取官方 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` / `VOLCENGINE_SESSION_TOKEN`；旧变量 `VOLC_ACCESSKEY` / `VOLC_SECRETKEY` / `VOLC_SESSION_TOKEN` 仍优先。环境变量只参与当前请求的凭据选择，不同步 ve profile。

支持两种认证的 bytedcli 命令按以下顺序选取整组凭据：显式 `--volc-account-id` → CLI AK/SK → `VOLC_*` → `VOLCENGINE_*` → 保存的 Babi 账号 → 保存的 AK/SK。因此，完整的官方环境凭据会优先于保存的 Babi 默认账号；要固定 Babi 身份，需显式传 `--volc-account-id`。Ark 仍仅支持 Babi；CtxSearch 和 bytedcli Resource Center 仅使用 AK/SK/STS，不使用 Babi。

每组 AK/SK/token 必须来自同一来源。选中来源只有半套 AK/SK、空值或只有 token 时直接报错，不从低优先级来源补齐。非空 CLI `--session-token` 可覆盖完整环境凭据组的 token；显式 CLI AK/SK 没有 token 时不继承环境或保存的 token。`VOLCENGINE_REGION` / `VOLCENGINE_ENDPOINT` 不覆盖 bytedcli 资源命令的默认值，需显式传命令支持的 `--region` / `--host`。

### bytedcli 凭据检查与 ve 离线诊断

```bash
# 预览 bytedcli 的凭据来源；不登录、不刷新、不在线验证
bytedcli --json volcano auth status
bytedcli --json volcano auth status --volc-account-id <account-id>

# 安全检查 ve 安装、profile、region/endpoint 和凭据字段是否齐全
bytedcli --json volcano auth doctor
bytedcli volcano auth doctor --profile <babi-name>
bytedcli volcano auth doctor --config-file ./demo-ve-config.json --profile demo-dev
```

`auth status` 的 `selected.validated` 始终为 false；它只检查 bytedcli 的来源选择，不读取 ve profiles。`auth doctor` 中的 `--profile` 指 ve profile，不是 bytedcli 全局 profile；选择顺序为显式 profile → ve current → `VOLCENGINE_PROFILE` → `VOLCSTACK_PROFILE` → 默认凭据链。doctor 只按安全白名单展示配置和字段存在性，不执行 ve、不刷新凭据、不读外部登录/OIDC token 文件、不访问云 API，始终返回 `authentication_validated: false`。独立二进制版本无法离线确认时显示 unknown，npm 包版本也不等于实测二进制版本。

Agent 不直接读取 `~/.volcengine/config.json` 或运行会展示密钥的配置命令；需要诊断时使用上述 doctor。不要回显 AK/SK 或 SessionToken。让用户自己在终端输入 SecretKey，避免秘密进入 shell 历史和 Agent 日志。

### Babi Logout

`volcano auth logout` 只处理 Babi Console Login，不删除 AK/SK，也不删除 `bytedcliak`：

```bash
# 退出 auth config 保存的默认 Babi 账号
bytedcli volcano auth logout

# 退出指定 Babi 账号
bytedcli volcano auth logout --volc-account-id <account-id>

# 退出 bytedcli 已缓存的全部 Babi 账号
bytedcli volcano auth logout --all
```

本地 Babi session 始终先清理；账号名可解析且 ve 已安装时，再 best-effort 执行 `ve logout --profile <babi-name>`。账号名无法解析、ve 未安装或命令失败时，只把 ve 侧结果标记为 skipped/failed，不阻断本地恢复。`--all` 逐个尝试 bytedcli 已缓存账号对应的 profile，不能替换成 `ve logout --all`，否则会影响用户自行维护的其他 Console Login profile。logout 保留 bytedcli 的默认 Babi account ID 和 ve profile；如果该 profile 仍是 current，后续调用会要求重新登录，logout 不自动选择另一身份。

无参数且没有默认 Babi 账号时，保持旧版行为：清理全部本地 Babi session，并明确输出作用范围。显式空账号会报错，不会退回默认账号或全量清理。ve 低于 1.1.5 或缺少所需能力时，ve 侧标记 `skipped`；logout 从不安装或升级 ve。

### 备选：Cloud Identity Center SSO

用户明确选择企业 SSO 时，先询问 start URL 和 session 名：

```text
ve configure sso-session --name <session-name> \
  --start-url https://<sso-host>/userportal \
  --region cn-beijing \
  --registration-scopes cloudidentity:account:access,offline_access

ve configure sso --profile <profile-name> --sso-session <session-name>
ve configure profile --profile <profile-name>
ve sso login --sso-session <session-name> --no-browser
```

## 2. 安全规则

| 级别   | 操作                                                                          | 行为                     |
| ------ | ----------------------------------------------------------------------------- | ------------------------ |
| 只读   | `Describe*`、`List*`、`Get*`、`Query*`                                        | 可直接执行               |
| 写入   | `Create*`、`Run*`、`Allocate*`、`Attach*`、`Associate*`、`Authorize*`         | 展示完整命令并等待确认   |
| 破坏性 | `Delete*`、`Terminate*`、`Release*`、`Revoke*`、`Modify*`、`Stop*`、`Detach*` | 展示命令和影响，必须确认 |

若接口支持 `--DryRun true`，先做 DryRun。`DryRunOperation` 通常以 exit code 1 返回，这是参数校验成功，不是执行失败：

```text
output=$(ve <svc> <action> --DryRun true ... 2>&1)
if echo "$output" | grep -q "DryRunOperation"; then
  echo "参数校验通过"
fi
```

## 3. 定位 API 与参数

```text
已知 service 和 Action → 直接使用
已知 service、未知 Action → ve <service> 2>&1 | grep -i <keyword>
两者都未知 → ve 2>&1 | grep -i <keyword>
仍未找到 → python3 scripts/find_api.py <keyword>
```

确定 Action 后：

- 只读接口通常先看 `ve <service> <Action> --help`。
- 写入/删除接口必须看 `--help --detail`，确认必填字段、枚举、范围和示例。
- 需要中文参数说明时加 `--lang ZH`。
- 不要猜测参数名、方法、endpoint 或 API 版本。

默认版本使用基础 service 名；非默认版本通常使用 `service + 去掉连字符的版本号`，例如 IAM `2021-08-01` 对应 `iam20210801`。

### metadata 尚未收录的 API

确认 API 真实存在但 `ve` 报 unknown service/action 时可用 `--force`：

```bash
ve newservice DescribeNewResource \
  --version 2024-01-01 \
  --endpoint open.volcengineapi.com \
  --SomeParam value \
  --force
```

`--force` 必须同时提供版本；未知 service 还必须提供 endpoint。POST API 加 `--method POST`，JSON body 使用 `--body`。参数来源只能是用户材料、CLI 详细帮助、官方接口说明或 [扩展 API](references/extend-apis.md)。

当接口必须同时发送 URL query 和 JSON body、而 `ve --force` 无法表达时，才使用扩展脚本：

```bash
python3 scripts/call_extend_api.py --list
python3 scripts/call_extend_api.py --api QueryMetrics --params '{"workspace":"<id>","query":"up"}'
```

升级 ve 后可运行 `python3 scripts/audit_extend_apis.py`，检查哪些扩展接口已能由 ve 原生覆盖。

## 4. 执行 API

```text
ve <ServiceCode> <ActionName> --ParamName "value" [系统参数]
```

根据 `--help` 判断参数形态：

- 展开参数：使用 `--Key value`。
- 数组：使用帮助中展示的编号格式，例如 `--InstanceIds.1`。
- JSON body：只显示 `--body` 时传完整 JSON，不要与展开参数混用。

```bash
ve ecs RunInstances --ZoneId "cn-beijing-a"
ve ecs RunInstances --NetworkInterfaces.1.SubnetId "subnet-<id>"
ve ecs RunInstances --Tags.1.Key "publish-by" --Tags.1.Value "demo-skill"
```

### 输出与查询

| `--output`            | 用途                                               |
| --------------------- | -------------------------------------------------- |
| `json`                | 默认；保留完整响应，适合 Agent 解析                |
| `table` / `table-num` | 向用户展示列表                                     |
| `text`                | 捕获单个值或 ID 列表                               |
| `yaml`                | 展示嵌套详情                                       |
| `off`                 | 执行但不输出；不得用于需要读取新资源 ID 的创建操作 |

`--query` 使用 JMESPath，并在格式化前作用于完整响应，所以路径通常从 `Result.` 开始：

```bash
ve sts GetCallerIdentity --query 'Result.AccountId' --output text
ve ecs DescribeInstances \
  --query 'Result.Instances[].{Id:InstanceId,Name:InstanceName,Status:Status,Zone:ZoneId}' \
  --output table
ve vpc DescribeVpcs --query 'length(Result.Vpcs)' --output text
```

成功响应通常是：

```json
{ "ResponseMetadata": { "RequestId": "..." }, "Result": {} }
```

失败响应通常在 `ResponseMetadata.Error` 中。命令退出失败或响应含 Error 时，完整阅读 [常见错误](references/common-errors.md)，再按请求格式、依赖、账号状态、产品开通、实名认证、购买资格或权限分类。

### 异步资源

VKE、RDS、ECS 等创建后可能需要数分钟。创建成功后按对应 Describe/List 接口轮询到目标状态；遇到 API 失败立即停止，不要继续盲目轮询。轮询间隔和总时限按资源类型设定，不要假设所有产品都使用 `Running`。

## 5. 执行流程

```text
1. GetCallerIdentity 验证身份，固定 profile 与地域
2. 判断操作是只读、写入还是破坏性
3. 用 ve help 定位 service/Action；必要时使用 find_api.py 或 --force
4. 写入操作读取 --help --detail
5. 用只读 List/Describe 获取依赖资源 ID
6. 只读直接执行；写入先 DryRun/预览并确认
7. 检查 HTTP/业务错误，报告结果；异步资源继续轮询
```

## 6. Ark、TLS、TOS、CtxSearch 保留能力

### Ark

Ark 仅使用 Babi Session：

```bash
bytedcli volcano auth config --volc-account-id <account-id>
bytedcli volcano ark model list
bytedcli volcano ark endpoint list
bytedcli volcano ark api-key list
bytedcli volcano ark api-key get --id <api-key-id> --reveal
```

`api-key get --reveal` 会显示明文凭证，只能在用户明确要求后执行，且不得把结果写入文档、日志或代码。

### TLS

```bash
bytedcli volcano tls project list --page-size 20
bytedcli volcano tls topic list --project-id <project-id> --page-size 50
bytedcli volcano tls index get --topic-id <topic-id>
bytedcli volcano tls log search --topic-id <topic-id> --query "level:ERROR" --range 15m
bytedcli volcano tls trace list --topic-id <topic-id> --range 24h
bytedcli volcano tls trace get --topic-id <topic-id> --trace-id <trace-id> --format tree
```

TLS trace 是在 `SearchLogs` 上按 OpenTelemetry 字段封装的视图，不是 TLS 原生资源。完整错误排查用 `--http-debug`。

除上述手写命令外，`bytedcli volcano tls <group> <verb>` 从契约全量生成 312 个操作 / 26 个命令组，覆盖告警、仪表盘、机器组、采集配置、数据导入/加工/投递、消费组、定时 SQL、Copilot 等全部 TLS 资源域。高危操作需 `--confirm`，非 GET 支持 `--dry-run` 预览，列表命令支持 `--page`/`--limit` 分页。完整命令组列表与约定见 [volcano-tls](references/volcano-tls.md)。`bytedcli volcano tls raw --action <Action>` 是逃生舱，可直接调用任意 TLS Action（含未生成的操作）。

### TOS

TOS bucket/object 查询、历史版本列举与指定版本下载使用 bytedcli，详见 [TOS](references/volcano-tos.md)：

```bash
bytedcli volcano tos bucket list --volc-account-id <account-id> --region cn-beijing
bytedcli volcano tos object list --bucket <bucket-name> --prefix demo/
bytedcli volcano tos object get --bucket <bucket-name> --key <object-key>
bytedcli volcano tos version list --bucket demo-bucket --prefix releases/ --limit 50
bytedcli volcano tos object download --bucket <bucket-name> --key <object-key> --output <path>
bytedcli volcano tos object download --bucket demo-bucket --key releases/demo.zip --version-id <version-id> --output ./demo.previous.zip
```

### CtxSearch

CtxSearch 的 qa/dev 环境使用不同签名 service 和 `x-tt-env` 语义，继续使用 bytedcli：

```bash
bytedcli volcano ctxsearch scene list --env qa
bytedcli volcano ctxsearch api-key list --env qa
```

## 7. 产品说明

- bytedcli 通用调用方式：[../../invocation.md](../../invocation.md)
- bytedcli 通用排障：[../../troubleshooting.md](../../troubleshooting.md)
- 常见错误：[references/common-errors.md](references/common-errors.md)
- 控制台登录：[references/console-login.md](references/console-login.md)
- Cloud Control：[references/cloudcontrol.md](references/cloudcontrol.md)
- ECS：[references/ecs.md](references/ecs.md)
- VPC：[references/vpc.md](references/vpc.md)
- CR：[references/cr.md](references/cr.md)
- ALB：[references/alb.md](references/alb.md)
- CLB：[references/clb.md](references/clb.md)
- VKE：[references/vke.md](references/vke.md)
- VKE 操作与 Kubernetes API 映射：[references/volcano-vke.md](references/volcano-vke.md)
- veFaaS：[references/vefaas.md](references/vefaas.md)
- RDS：[references/rds.md](references/rds.md)
- DBW 数据库、表与 SQL：[references/volcano-dbw.md](references/volcano-dbw.md)
- Resource Center 跨产品资源发现与统计：[references/volcano-resource-center.md](references/volcano-resource-center.md)
- TLS 全量命令参考（312 操作 / 26 组）：[references/volcano-tls.md](references/volcano-tls.md)
- 消息队列：[references/mq.md](references/mq.md)
- 存储：[references/storage.md](references/storage.md)
- 可观测性：[references/observability.md](references/observability.md)
- DNS/边缘：[references/dns-edge.md](references/dns-edge.md)
- IAM：[references/iam.md](references/iam.md)
- KMS：[references/kms.md](references/kms.md)
- Redis：[references/redis.md](references/redis.md)
- NAT 网关：[references/natgateway.md](references/natgateway.md)
- EBS：[references/ebs.md](references/ebs.md)
- 扩展 API：[references/extend-apis.md](references/extend-apis.md)
