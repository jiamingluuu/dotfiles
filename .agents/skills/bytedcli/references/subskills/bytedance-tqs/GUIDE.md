---
name: bytedance-tqs
description: "Use bytedcli TQS commands to validate Hive SQL, submit async query jobs, poll status, fetch preview results, and download full CSV results. Supports multi-cluster routing via `--cluster`, `--profile`, or automatic `--site` inference (e.g. `--site i18n-tt` → sg_row). Use when tasks mention TQS, Hive SQL syntax check, async SQL execution, polling query jobs, `tqs analyze`, `tqs submit`, `tqs wait`, `tqs result`, `tqs execute`, `TQS_APP_ID`, `TQS_YARN_CLUSTER`, `TQS_YARN_QUEUE`, `--cluster`, or `--profile`."
---

# bytedcli TQS

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

- 对 Hive SQL 做语法检查
- 提交 TQS 查询任务并异步等待结果
- 查询已有 TQS job 的状态
- 获取成功任务的预览结果或下载完整 CSV
- 需要显式指定 YARN cluster / queue，或从环境变量提供默认值
- 排障（**仅限持有 TQS 管理台管理员 session 的 SRE / 平台人员**）：按 TQS job id 读取不属于自己的 job 的元数据（SQL 原文、生效 conf、executionInfo、YARN application id）和提交 / 查询日志（`tqs job get` / `tqs job log`）。普通用户没有这份权限，执行时会得到 `TQS_MANAGEMENT_PERMISSION_DENIED`；查自己的 job 仍用 `tqs status`

## 前置条件

- 使用通用调用方式：`../../../invocation.md`
- 先完成 `bytedcli auth login`
- 在 `.env` 中提供 TQS 凭证：`TQS_APP_ID`、`TQS_APP_KEY`（如何申请见 [TQS 应用申请](https://bytequery.bytedance.net/docs/tqs/super_app_apply)）
- 可选环境变量：`TQS_CLUSTER`、`TQS_YARN_CLUSTER`、`TQS_YARN_QUEUE`
- 如需管理多套凭证（不同集群使用不同 appId/appKey），可使用 `--profile` 机制（见下文）

> 执行前缀见 `../../../invocation.md`；下面示例直接写 `bytedcli`。

## 凭证 Profile

当需要同时管理多套 TQS 应用凭证时，可以使用 `--profile <name>` 选项。

### 环境变量命名规则

```bash
# 默认凭证（不指定 --profile 时使用）
TQS_APP_ID=xxx
TQS_APP_KEY=xxx
TQS_CLUSTER=cn

# profile "sg" 的凭证
TQS_PROFILE_SG_APP_ID=xxx
TQS_PROFILE_SG_APP_KEY=xxx
TQS_PROFILE_SG_CLUSTER=sg
```

### 使用方式

```bash
# 使用默认凭证查询 CN
bytedcli tqs execute --sql "SELECT 1" --json

# 使用 sg profile 的凭证查询 SG 集群
bytedcli tqs execute --profile sg --sql "SELECT 1" --json
```

- `--profile` 的 name 会被转为大写拼接到环境变量前缀：`TQS_PROFILE_<NAME>_`
- 如果 profile 对应的 key 不存在，会回退到默认 key（`TQS_APP_ID` 等）
- `--profile` 中配置的 `TQS_PROFILE_<NAME>_CLUSTER` 会自动设置集群，无需再传 `--cluster`
- `--cluster` 仍可覆盖 profile 中的集群设置

## 集群路由

### `--cluster` 选项

所有 `tqs` 子命令均支持 `--cluster <cluster>` 通用选项，用于显式指定 TQS 集群：

```bash
# 直连新加坡 TikTok ROW 集群
bytedcli tqs execute --sql "SELECT 1" --cluster sg_row --json

# 直连 VA 集群
bytedcli tqs execute --sql "SELECT 1" --cluster va --json
```

可用集群名称：`cn`, `lq`, `va`, `sg`, `sg_row`, `boe`, `boei18n`, `oci`, `gcp`, `jp_lark`, `sg_lark_adhoc`, 以及各 `*_adhoc` 集群。完整列表：

```bash
bytedcli tqs clusters
```

### `--site` 自动推断

当未显式指定 `--cluster` 和 `TQS_CLUSTER` 时，bytedcli 会根据全局 `--site` 参数自动推断目标 TQS 集群：

| `--site` 值                                         | 推断的 TQS 集群 |
| --------------------------------------------------- | --------------- |
| `cn`（默认）                                        | `cn`            |
| `boe`                                               | `boe`           |
| `i18n-tt`                                           | `sg_row`        |
| `i18n-bd` / `i18n`                                  | `sg`            |
| `us-ttp` / `us-ttp-bdee` / `us-ttp-usts` / `eu-ttp` | `va`            |

```bash
# 使用 --site 自动推断到 sg_row 集群
bytedcli --site i18n-tt tqs execute --sql "SELECT 1" --json

# 等效于
bytedcli tqs execute --sql "SELECT 1" --cluster sg_row --json
```

**优先级**：`--cluster` > `TQS_CLUSTER` 环境变量 > `--site` 自动推断 > 默认 `cn`

## 排障：读取他人 job 的管理员命令（`tqs job`）

> **权限前提**：`tqs job get` / `tqs job log` 读取的是 TQS **管理台**数据，服务端只放行管理员身份。使用前先确认你持有 TQS 管理台的管理员 session（SRE / 平台 oncall 才有）；没有的话命令返回 `TQS_MANAGEMENT_PERMISSION_DENIED`，这是预期行为，不是故障。bytedcli 本身不授予任何权限，权限校验全部在 TQS 服务端完成。

这两条命令走 TQS **管理台 v3 API**（`/api/v3/management/tasks/{id}/status`），和上面的 OpenAPI 命令是两套认证模型：

| 路径                           | 身份                                                                                    | 何时使用                                                                                                                             |
| ------------------------------ | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 注入管理台 session（主要用法） | `BYTEDCLI_TQS_MANAGEMENT_COOKIE` 环境变量，值是管理员登录 TQS 管理台后的 session cookie | 持有管理员 session 的 SRE；可跨全部集群查找                                                                                          |
| ByteCloud 网关（兜底）         | 你自己的 SSO（`bytedcli auth login`）                                                   | 仅当 TQS 平台已把管理 API 授权给你的个人账号；默认未授权，返回 `TQS_MANAGEMENT_PERMISSION_DENIED`。网关每个 site 只对应一个 TQS 部署 |

- 没有注入 session 时命令走网关，被拒返回 `TQS_MANAGEMENT_PERMISSION_DENIED`（hint 带 `logId`）。普通用户看到这个错误就应停止，不要尝试绕过；只有确实承担 TQS 排障职责的人才应持有管理台 session 或向 TQS 平台申请网关权限。
- 注入 cookie 的格式是登录后 TQS 控制台的完整 Cookie 请求头：`tqs-token=<token>; tqs-username=<user>`（不含 `Cookie:` 前缀）。bytedcli 只透传，不存储、不写日志、不刷新；过期后重新注入。不要把它写进 shell profile，放在 owner-only 的 env 文件里按需加载。
- JSON 输出用全局 `-j/--json`（放在子命令前，例如 `bytedcli -j tqs job get …`）；`tqs job` 子命令本身没有局部 `--json`。
- 网关路径下 `--region` 会被拒绝（网关每个 site 只对应一个部署，无法扫描），`--cluster` 不改变回答的部署，只用来标记结果和改写日志域名，并在 `warnings` 里说明。
- cookie 路径下不带 `--cluster` 会并行扫描全部生产集群（TQS id 只在集群内唯一），`--region <cn|sg|va|us|my|norway|eupipo|gcp|pinnacle|jp>` 可缩小范围（`sg` 含东南亚的 `my_*` / `nonttmy_*`：它们的 YARN app 在 Megatron 里也标为 sg）；单个集群查询失败不会中断扫描，会记录在 `warnings`；多个集群同时命中返回 `TQS_JOB_AMBIGUOUS`，用 `--cluster` 钉死。
- `tqs job log` 从结果存储下载日志（无需认证，只接受 https 且主机在已知结果存储域名后缀内）；存储只支持整档下载，`--tail-bytes` / `--head-bytes` 在本地截取，`--output` 保存整档（此时忽略 head / tail）；单档上限 512 MB，超过返回 `TQS_LOG_TOO_LARGE`。my / norway / eupipo / iepipo / gcp / pinnacle / usbd 集群的日志 URL 会自动改写到办公网可达域名。
- JSON 输出字段：`job_id`、`status`、`user_name`、`engine_type`、`application_id`（从 progress / executionInfo 恢复的 YARN app id）、`query`、`conf`、`execution_info`、`progress`、`log_url`、`query_log_url`、`tqs_cluster`、`route`、`searched_clusters`、`warnings`。

```bash
# 管理员：注入 TQS 管理台 session 后查询（普通用户没有这份 session，会得到 PERMISSION_DENIED）
export BYTEDCLI_TQS_MANAGEMENT_COOKIE='tqs-token=<token>; tqs-username=<admin-user>'
bytedcli -j tqs job get --job-id 930747398
bytedcli tqs job get --job-id 930747398 --region cn
bytedcli -j tqs job get --job-id 930747398 --cluster cn_priest

# 提交日志尾部 / 查询日志开头 / 整档落盘
bytedcli tqs job log --job-id 930747398 --cluster cn_priest --tail-bytes 20000
bytedcli tqs job log --job-id 930747398 --cluster cn_priest --kind query --head-bytes 4000000
bytedcli tqs job log --job-id 930747398 --cluster cn_priest --kind query --output ./query.log
```

## Quick start

```bash
# 查看支持的 TQS clusters
bytedcli tqs clusters

# 只做 Hive SQL 语法检查
bytedcli tqs analyze --sql "SELECT 1"

# 提交查询，拿到 jobId 后异步处理
bytedcli tqs submit --sql "SELECT 1" --json

# 查询任务状态
bytedcli tqs status --job-id <job-id> --json

# 轮询直到任务完成
bytedcli tqs wait --job-id <job-id> --json

# 获取结果预览
bytedcli tqs result --job-id <job-id> --json

# 一步完成提交 + 轮询 + 结果预览
bytedcli tqs execute --sql "SELECT 1" --json

# 下载完整 CSV
bytedcli tqs result --job-id <job-id> --format csv --output ./result.csv

# 查询新加坡 TikTok ROW 集群数据
bytedcli tqs execute --sql "SELECT 1" --cluster sg_row --json
```

## Auto analyze

`tqs submit` 和 `tqs execute` 默认在提交前自动执行 SQL analyze：

- analyze 失败时直接报错退出，不会继续提交任务
- 如需跳过自动 analyze，传 `--skip-analyze`

```bash
# 默认行为：先 analyze 再 submit
bytedcli tqs submit --sql "SELECT 1" --json

# 跳过 analyze 直接提交
bytedcli tqs submit --sql "SELECT 1" --skip-analyze --json
```

## Recommended flow

### Validate only

1. 如果只想确认语法或分析信息，用 `tqs analyze --sql ...`。

### Async job flow

1. 用 `tqs submit --sql ... --json` 提交任务并记录 `jobId`（自动包含 analyze）。
2. 后续需要时，用 `tqs status --job-id ...` 或 `tqs wait --job-id ...` 继续查询。
3. 任务成功后，用 `tqs result --job-id ...` 取预览结果。
4. 如果需要完整结果文件，再用 `tqs result --format csv --output <path>` 下载。

### One-shot flow

1. 如果不需要手动拆分流程，直接用 `tqs execute --sql ...`（自动包含 analyze）。
2. `execute` 会先 analyze，再提交任务，再轮询，最后返回结果预览。
3. 如果只想拿到完整文件，仍然推荐显式使用 `result --format csv --output ...`。

## Yarn options

- `--yarn-cluster <cluster>`：单次查询指定 YARN cluster
- `--yarn-queue <queue>`：单次查询指定 YARN queue
- `TQS_YARN_CLUSTER`：默认 YARN cluster，可不填
- `TQS_YARN_QUEUE`：默认 YARN queue，可不填
- 命令行参数优先级高于环境变量默认值

## Polling behavior

- `tqs wait` / `tqs execute` 默认采用自适应轮询
- 前 `60` 秒每 `10` 秒轮询一次
- 超过 `60` 秒后每 `30` 秒轮询一次
- 默认 `--max-wait` 为 `300` 秒
- 如需覆盖默认策略，可显式传 `--poll-interval <seconds>` 和 `--max-wait <seconds>`

## Result behavior

- `tqs result` / `tqs execute` 只对成功任务返回结果数据
- `sample_data` 是预览数据，不单独返回 CSV 表头
- `with_header` 表示当前解析逻辑是否将 CSV 第一行识别为表头
- 如需完整结果，使用 `--format csv --output <path>` 下载
- 需要机器可读输出时，优先使用 `--json`

## 凭证文件加载

bytedcli TQS 从以下位置加载凭证，优先级从高到低：

1. **进程环境变量**（`TQS_APP_ID`、`TQS_APP_KEY` 等）
2. **当前目录** **`.env`** **文件**（自动解析 `KEY=VALUE` 格式）
3. 可通过 `--env-file <path>` 指定其他 `.env` 文件路径

> 注意：不自动读取 `.env.local`，只读取 `.env`。如需使用 `.env.local`，可通过 `source .env.local && bytedcli tqs ...` 手动注入到进程环境变量。

## References

- `../../../invocation.md`
- `../../../troubleshooting.md`
- [TQS 应用申请](https://bytequery.bytedance.net/docs/tqs/super_app_apply)
