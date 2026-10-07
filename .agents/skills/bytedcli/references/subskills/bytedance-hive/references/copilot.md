# Hive Copilot / Hive Agent 调用方式

Hive Copilot 是 `bytedcli hive` 下的托管诊断能力，用于 Spark Application 诊断、性能调优、作业对比或 Spark/Hive 知识回答。

## 路由边界

当用户给出 Spark `application_*` 并要求诊断失败/慢因、比较 Spark 作业、分析数据倾斜/Shuffle/资源配置，或明确要求 Hive Copilot / Hive Agent 与 CN Spark/Hive 运行时知识问答时，使用 `bytedcli hive copilot`。

不要把以下场景误路由到 Hive Copilot：

- 原始 Spark UI evidence、Stage、Task、Executor 或 event-log 取证：改用 `bytedance-megatron`。
- Hive 表、schema、分区、血缘或 DataLeap/Coral 资产查询：继续使用 `bytedance-hive` 的元数据命令。

## 支持站点

Hive Copilot 只支持两个全局 `--site` 值：

| 站点值    | 用途                                                                  | 登录要求               |
| --------- | --------------------------------------------------------------------- | ---------------------- |
| `cn`      | 国内 Spark Application 诊断、作业对比、性能调优和 Spark/Hive 知识问答 | ByteDance SSO          |
| `i18n-tt` | SG Spark Application 诊断、作业对比和性能调优                         | TikTok SSO，需单独登录 |

`i18n-tt` 在 Hive Copilot 中只代表 SG，不代表其他国际区域。其他 `--site` 值不要用于 Hive Copilot。

办公网默认使用 SG office endpoint；生产网运行时设置 `BYTEDCLI_NETWORK_PROFILE=prod`。创建 Session 与后续诊断或下钻必须使用相同 `--site` 与 network profile。

## 认证

Hive Copilot 使用 bytedcli 内部的 person-account ByteCloud JWT。不要让用户复制 JWT，也不要输出 JWT、请求 header 或内部 payload。

```bash
bytedcli --site cn auth login
bytedcli --site i18n-tt auth login
```

## Session-first workflow

先显式创建 Session：

```bash
bytedcli --site cn hive copilot create-session \
  --name "Hive Copilot diagnosis"
```

再使用返回的 `session_id` 进行首次诊断：

```bash
bytedcli --site cn hive copilot \
  --session-id sample-session \
  --query "请诊断 application_example_001，分析失败原因并给出修复建议" \
  --max-wait-seconds 3600
```

继续下钻时复用同一个 Session：

```bash
bytedcli --site cn hive copilot \
  --session-id sample-session \
  --query "继续分析最慢的 Stage，并说明关键证据" \
  --max-wait-seconds 3600
```

SG 诊断使用 `--site i18n-tt`：

```bash
bytedcli --site i18n-tt hive copilot create-session \
  --name "SG diagnosis"

bytedcli --site i18n-tt hive copilot \
  --session-id sample-session \
  --query "请诊断 application_example_002，定位失败根因" \
  --max-wait-seconds 3600
```

不要把首次诊断和下钻描述成两种模式：它们使用同一条命令和同一个 Session，区别只是 query 内容不同。首次诊断前必须先创建 Session。

## JSON 输出

需要给脚本或 Agent 消费时，把全局 `--json` 放在 domain 前：

```bash
bytedcli --json --site cn hive copilot create-session \
  --name "Hive Copilot diagnosis"
bytedcli --json --site cn hive copilot \
  --session-id sample-session \
  --query "请诊断 application_example_001" \
  --max-wait-seconds 3600
```

`create-session` JSON 输出里的 `data.session_id` 是后续诊断和下钻需要传给 `--session-id` 的值。

诊断默认把启动、首个事件、每 30 秒心跳、模型输出和完成状态写到 stderr；stdout 仍只包含最终文本或单个 JSON 结果，因此可以继续安全地重定向或交给 `jq`。进度只包含事件数、白名单事件类型和活跃时间，不包含原始 SSE payload、工具参数或模型中间正文。需要安静运行时传 `--no-progress`。

```bash
bytedcli --json --site cn hive copilot \
  --session-id sample-session \
  --query "请诊断 application_example_001" \
  --max-wait-seconds 3600
```

## Query 模板

- 失败诊断：请诊断 Spark Application：application_example_001，定位失败根因并给出修复建议。
- 作业对比：请比较 application_example_001 和 application_example_002 的运行耗时、失败/重试、Stage/Task、SQL plan、Spark conf、资源配置、Shuffle/Input 指标，并区分证据与推测。
- 卡住分析：请分析 application_example_001 为什么长时间无进展，确认卡住位置、关键证据、根因、立即止损和长期优化。
- OOM：请诊断 application_example_001，区分 Driver、Executor、overhead、off-heap、GC 与 container memory limit，并引用日志、配置和退出码证据。
- CN 知识问答：Hive 读取数据提示上游表文件不存在，但对应分区存在，请给出可能原因、排查步骤和修复建议。

普通诊断保持默认输出；确实需要完整 Agentic 分析过程时加 `--verbose`。

## 输出契约

命令只在收到 `RUN_FINISHED` 后返回成功：

- `available=true`：`report` 是最后一个非空 `MODEL_OUTPUT.contentText`；文本和 JSON 都返回 Session ID。
- `available=false, status=unavailable`：等待期限内没有看到 `RUN_FINISHED`，命令返回退出码 2，并保留 `session_id` 与 `client_request_id`。使用同一个 `--session-id` 和 `--client-request-id` 显式重试，避免重复逻辑请求。
- `RUN_ERROR`：返回结构化错误和非零退出码。命令不自动重试 Chat。

`--max-wait-seconds` 默认值和最大值都是 3600。

最终 JSON 还包含 `model_output_count` 与 `stream_metrics`，用于区分首事件延迟、首个模型输出延迟、最大事件间隔和最后事件时间。当前服务端的 `MODEL_OUTPUT.contentText` 按完整快照处理；CLI 保留最后一个非空快照，不把多个快照直接拼接。

## 常见问题

### 提示缺少 `--session-id`

`hive copilot` 不会隐式创建 Session，诊断和下钻都必须传入已有 Session ID。先创建 Session，再把返回的 `session_id` 传给诊断命令。

```bash
bytedcli --site cn hive copilot create-session \
  --name "Hive Copilot diagnosis"

bytedcli --site cn hive copilot \
  --session-id sample-session \
  --query "请诊断 application_example_001，分析失败原因并给出修复建议" \
  --max-wait-seconds 3600
```

### 站点不支持

Hive Copilot 只支持 `cn` 和 `i18n-tt`；其中 `i18n-tt` 只支持 SG。确认 Application 所属站点后重试。除 `cn` 和 `i18n-tt` 外，不要把其他 `--site` 值用于 Hive Copilot。

### 401 / 403 鉴权失败

按同一个站点登录后重试。`i18n-tt` 使用 TikTok SSO，通常需要单独登录。

```bash
bytedcli --site cn auth login
bytedcli --site i18n-tt auth login
```

不要手动复制或输出 JWT。命令会在内部读取 person-account ByteCloud JWT。

### SG 网络不通

`i18n-tt` 对 Hive Copilot 只代表 SG，办公网和生产网使用不同 endpoint。办公网保持默认；生产网运行时设置 `BYTEDCLI_NETWORK_PROFILE=prod`，并确保创建 Session 与后续诊断使用相同 network profile。

```bash
BYTEDCLI_NETWORK_PROFILE=prod bytedcli --site i18n-tt hive copilot create-session \
  --name "SG diagnosis"
```

### 等待超时或结果不可用

等待窗口内没有收到 `RUN_FINISHED`，或 SSE 在结束前中断时，复用同一个 `--session-id` 和返回的 `client_request_id` 显式重试，避免提交重复逻辑请求。

```bash
bytedcli --site cn hive copilot \
  --session-id sample-session \
  --client-request-id 00000000-0000-4000-8000-000000000001 \
  --query "请诊断 application_example_001，分析失败原因并给出修复建议" \
  --max-wait-seconds 3600
```

## 向用户转述

1. 保留报告中的证据、根因和建议，不把推测改写成事实。
2. 证据不足时建议用 `bytedance-megatron` 获取 Spark UI 原始指标继续核验。
3. 不向用户展示 JWT、内部请求 payload 或凭据相关错误细节；Session ID 仅用于按用户要求继续下钻。
