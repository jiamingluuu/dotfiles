---
name: bytedance-rds-pg
description: "Inspect and manage ByteCloud RDS PostgreSQL via bytedcli rds-pg: resolve password-free local connection metadata and TCP reachability; list instances, databases, schemas, accounts, parameters, backups and logs; manage read-only nodes, endpoints and accounts. Use when tasks mention RDS PostgreSQL, rds_pg instances (postgres-xxxxxxxx), BOE connection setup, or PostgreSQL troubleshooting on ByteCloud."
---

# bytedcli RDS PostgreSQL

`bytedcli rds-pg` 提供字节云 RDS PostgreSQL（控制台 `/rds_pg/`）的查询能力，以及只读节点、连接终端与数据库账号的变更能力。支持国内生产（`--site cn`）和 BOE（`--site boe`）控制面；两者都使用 `bytedcli auth login` 的登录态，无需火山 AK/SK。

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

- 查看 PostgreSQL 实例状态、规格、节点与连接端点
- 为本地项目解析连接地址、端口、PSM、账号与数据库，并检查 TCP 可达性
- 用只读账号执行诊断 SQL，不必登录实例所在网络
- 列出库、schema、账号、参数
- 查看备份列表与备份策略
- 排查线上问题：错误日志、慢日志、运维事件
- 查看白名单、SSL 配置与可购规格目录

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权时先登录：`bytedcli auth login`
- 国内生产：每条命令都需要 `--volc-account-id` 与 `--project-name`，两者都在控制台 URL 的 query 参数里（`volcano_account_id`、`volcano_project_name`）
- BOE：全局参数 `--site boe` 必须放在 `rds-pg` 前，并传控制台 URL 中的 `ProjectId` 作为 `--project-id`

## Quick start

```bash
# BOE 实例列表与详情；--site 是全局参数，必须放在 rds-pg 前
bytedcli --site boe rds-pg instance list --project-id rds-pg-project_demo
bytedcli --site boe rds-pg instance get --project-id rds-pg-project_demo \
  --instance-id postgres-sample

# 给本地项目收集连接信息；输出不含密码，IPv6 会规范化为 [IPv6]:port
bytedcli --json --site boe rds-pg connection get \
  --project-id rds-pg-project_demo --instance-id postgres-sample \
  --database demo_db --username app_user --check-connectivity

# 实例列表与详情（详情含节点与连接端点）
bytedcli rds-pg instance list --volc-account-id 2100000000 --project-name rds-pg_demo
bytedcli rds-pg instance get --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample

# 库、schema、账号；schema 必须指定业务库，系统库会被服务端拒绝
bytedcli rds-pg database list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample
bytedcli rds-pg schema list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample --database demo_db
bytedcli rds-pg account list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample

# 参数：--modified-only 只看与默认值不同的项；change-log 查参数修改历史（时间窗必填）
bytedcli rds-pg param list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample --modified-only
bytedcli rds-pg param change-log list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample \
  --start-time 2026-08-01T00:00:00Z --end-time 2026-08-18T00:00:00Z

# 备份列表与策略
bytedcli rds-pg backup list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample
bytedcli rds-pg backup policy get --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample

# 排查线上问题：错误日志、慢日志、运维事件
bytedcli rds-pg log error list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample
bytedcli rds-pg log slow list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample \
  --start-time 2026-08-17T00:00:00Z --end-time 2026-08-17T12:00:00Z
bytedcli rds-pg log event list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample
bytedcli rds-pg maintenance planned-event list --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample

# 安全配置
bytedcli rds-pg security allowlist list --volc-account-id 2100000000 --project-name rds-pg_demo
bytedcli rds-pg security allowlist get --volc-account-id 2100000000 --project-name rds-pg_demo --allow-list-id acl-sample
bytedcli rds-pg security ssl get --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample

# 全局目录：地域、可用区、规格、引擎版本
bytedcli rds-pg catalog region list --volc-account-id 2100000000 --project-name rds-pg_demo
bytedcli rds-pg catalog zone list --volc-account-id 2100000000 --project-name rds-pg_demo
bytedcli rds-pg catalog spec list --volc-account-id 2100000000 --project-name rds-pg_demo --limit 10
bytedcli rds-pg catalog engine-version list --volc-account-id 2100000000 --project-name rds-pg_demo

# MPP 集群信息（非 MPP 实例返回空值）
bytedcli rds-pg mpp get --volc-account-id 2100000000 --project-name rds-pg_demo --instance-id postgres-sample

# 只读节点：不加 --yes 时由服务端评估影响并返回变更计划，不执行
bytedcli rds-pg node create --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --node-spec rds.postgres.2c4g --zone cn-beijing-a
bytedcli rds-pg node create --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --node-spec rds.postgres.2c4g --zone cn-beijing-a --yes
bytedcli rds-pg node delete --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --node-id postgres-sample-ro1 \
  --node-spec rds.postgres.2c4g --zone cn-beijing-a --yes
bytedcli rds-pg node update --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --node-id postgres-sample-ro1 \
  --node-spec rds.postgres.4c8g --zone cn-beijing-a --yes

# 只读终端：诊断流量走独立终端，不影响业务的默认终端
bytedcli rds-pg endpoint create --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --nodes postgres-sample-ro1 --name diagnose-ro --yes
bytedcli rds-pg endpoint delete --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --endpoint-id postgres-sample-custom-0001 --yes

# 读写分离（作用于默认终端，会造成 1~2 次业务闪断）
bytedcli rds-pg endpoint rw-split --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --endpoint-id postgres-sample-cluster --enable --max-delay-time 30 --yes

# 只读账号：密码只能经 --password-file、--password-stdin 或 TTY 提示输入
printf '%s' "$PGPASS" | bytedcli rds-pg account create \
  --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --account-name diag_readonly --password-stdin --yes

# 只读 SQL：走 DBW，需要数据库账号；只接受一条 SELECT / EXPLAIN SELECT
bytedcli rds-pg sql execute \
  --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --database demo_db \
  --username diag_readonly --password-file ./diag_readonly.password \
  --sql 'SELECT count(*) FROM demo_table'

# 查询走只读终端，不落到主节点；终端地址取自 instance get 的 Endpoints
bytedcli --json rds-pg sql execute \
  --volc-account-id 2100000000 --project-name rds-pg_demo \
  --instance-id postgres-sample --database demo_db \
  --username diag_readonly --password-file ./diag_readonly.password \
  --address postgres-sample-custom-0000-private.rds-pg.example.com:5432 \
  --sql-file ./diagnose.sql --limit 100
```

## Agent Guidance

- 国内生产使用 `--volc-account-id` 与 `--project-name`，从控制台 URL 的 `volcano_account_id=<账号>`、`volcano_project_name=<项目>` 直接取。一个账号下通常有数十个项目，`[禁止]` 只凭账号 ID 猜项目。
- 国内生产的 `--project-name` 用于解析网关鉴权所需的服务树节点。若已知节点 ID，可用 `--bytetree-id` 跳过这一步解析。
- BOE 使用 `bytedcli --site boe rds-pg ... --project-id <ProjectId>`；`ProjectId` 来自 BOE 控制台 URL，`[禁止]` 把生产环境的 `--project-name` 或火山账号参数混入 BOE 命令。
- 本地项目接入前先运行 `connection get`。它聚合实例集群端点、所有可用地址、PSM、账号列表和数据库列表；指定 `--database` / `--username` 可生成无密码 `connection_uri` 与 `psql_command`。省略 `--endpoint-id` 时优先选集群终端，其次读写终端。
- `connection get --check-connectivity` 会并行探测同一终端的全部候选地址，并把第一个可达候选提升为主 `address`；全部不可达时命令以 `RDS_PG_CONNECTION_UNREACHABLE` 失败。它只建立 TCP 连接，不做数据库认证、不执行 SQL。BOE 常返回 IPv6，输出的 `display_address` 使用 `[IPv6]:port`，本地驱动配置则分别使用 `host` 与数值 `port`。
- `connection get` 不猜测 TLS 模式；本地项目应按驱动策略配置，必要时另查 `security ssl get`。无密码 `connection_uri` 依赖 libpq 的默认协商行为，不代表服务端 SSL 已开启或关闭。
- 已有数据库账号的密码不可从 RDS 控制面取回，`connection get` 会固定返回 `password.retrievable: false`。若密码遗失，使用 `account reset-password` 设置新密码；`[禁止]` 在日志、JSON 或命令行参数中回显密码。
- `schema list` 的 `--database` 必须是业务库；传 `postgres` 等系统库会返回 `cannot describe schema in system db`。
- 定位线上问题的顺序建议：`log error list` 看报错 → `log event list` 看是否有变配/重启等运维动作 → `param list --modified-only` 看参数是否被改过 → `param change-log list` 确认改动时间点。
- `log slow list` 与 `log error list` 用游标分页：翻页传上一次输出的 `--context`，这两个接口不接受页码。`log event list` 与 `maintenance planned-event list` 则使用 `--page` / `--page-size`。
- **`--limit` 会关闭游标翻页**：它在客户端截断当前游标页，继续跟随 `--context` 会跳过被截断的条目，因此截断发生时 CLI 不再输出游标，JSON 给出 `has_more: true` + `paging_blocked_by_limit: true`。要完整读完日志就不要加 `--limit`，按 `has_more` 循环跟随 `--context`。
- 日志类命令省略 `--start-time` / `--end-time` 时使用服务端默认窗口，其长度未在接口中声明；需要确定的时间范围时显式传两个参数。
- JSON 输出约定：容器字段是 snake_case（`instances`、`error_logs`、`page_count`），业务字段保持上游 PascalCase（`InstanceId`、`BackupStatus`）。`get` 类命令直接返回上游对象。
- `param change-log list` 只提供参数名、新旧值与修改时间，**不包含操作人**。
- 控制面命令支持 `--site cn` 与 `--site boe`；其他站点会明确报 `RDS_PG_UNSUPPORTED_SITE`，不会静默路由到生产或 BOE。BOE 与生产使用独立网关、鉴权上下文和项目参数。
- `catalog spec list` 的服务端不支持分页，始终返回完整目录；用 `--limit` 客户端截断，输出会显式提示被截断。
- 全局 `--json` 可用于所有子命令，适合脚本与 Agent 消费。
- 写命令默认只预览，`--yes` 是唯一的执行开关。两种预览语义不同，输出里的 `preview` 字段会标明是哪一种：
  - `node` 系列为 `server_estimate`：服务端用同一份 payload 做评估，返回变更计划（`plans`）与连接影响（`effects`），预览通过基本意味着真实执行也会通过。
  - `endpoint` 与 `account` 系列为 `local_payload`：仅在本地回显请求体，**服务端未做任何校验**，预览通过不代表提交会成功。
- 账号密码 `[禁止]` 通过命令行参数传入（会落入 shell 历史与进程表）。只支持 `--password-file <path>`、`--password-stdin` 或 TTY 掩码提示；dry-run 阶段不读取密码。
- `[必须]` MCP / Agent 调用只能用 `--password-file <path>` 提供密码。`[禁止]` 在 MCP 下传 `--password-stdin`：这些命令同时是 MCP 工具，而 MCP 用同一个 stdin 传 JSON-RPC，读取 stdin 会吞掉协议流并挂起会话。
- `--password-stdin` 仅用于 shell 管道场景（如 `printf '%s' "$PW" | bytedcli ...`）。`[禁止]` 指望 stdin 被隐式读取：不传 `--password-file` 或 `--password-stdin` 时，非交互运行会直接报错而不会去读 stdin。
- `node` 命令组只管理只读节点。传 `--node-type Primary` 或 `Secondary` 会被拒绝；改主备节点属于实例级变更，需到控制台执行。
- `node` 的 dry-run 若未能从服务端取回评估结果，命令会报 `RDS_PG_ESTIMATE_UNCONFIRMED` 而非声称"未改动"。遇到该错误 `[必须]` 立即用 `instance get` 与 `log event list` 核对实例状态，`[禁止]` 直接重试。
- `--distribution-type Custom` 需要逐节点权重，CLI 无法表达，会被拒绝；自定义权重请在控制台设置。
- 诊断账号用 `--account-type InstanceReadOnly`（默认值）：它对实例下所有数据库只读，不需要逐库授权，也不必分发高权限账号密码。该类型 `[禁止]` 同时传 `--privileges`。
- 新增只读节点的约束：CPU 与内存均不得低于主节点的一半（建议与主节点同规格），单可用区实例只能选主节点所在可用区，单实例最多 10 个只读节点。变更期间有 3~4 次连接闪断。
- `--switch-type MaintainTime` 在未配置可维护时间段的实例上会失败（`fail to get instance maintenance window`）；不确定时不要传该参数。
- 删除只读节点会**同时删除绑定该节点的只读终端**。一个只读终端只能绑一个只读节点且绑定后不可换绑。
- 新增只读节点会自动加入默认终端，但读写分离未开启时其权重为 0、不承接流量。这是预期状态，不代表只读节点未生效。
- 写命令（账号三件套除外）都是异步的：命令返回成功只表示请求被接受。用 `instance get` 或 `log event list` 确认最终结果。
- 变更实例规格、重启实例、改参数、建库这类操作不在命令面内，需到控制台执行。
- `sql execute` 目前仅支持 `--site cn`。它走 DBW 而非 RDS PostgreSQL 控制面 OpenAPI（后者没有数据面），因此是本命令面唯一需要数据库账号的命令；BOE 会明确报 `RDS_PG_SQL_UNSUPPORTED_SITE`。BOE 本地读 SQL 属于项目自身的数据访问职责：先用 `connection get` 取无密码连接信息，再由项目选择 psql、驱动和连接池。
- `sql execute` 只接受一条 `SELECT` 或 `EXPLAIN SELECT`，并在 `READ ONLY` 事务中执行。`[必须]` `--username` 是 `InstanceReadOnly` 账号，否则命令直接拒绝连接；确需用高权限账号时显式加 `--allow-privileged-account`，该次执行会在输出里标记 `privileged_account`。
- `sql execute` 还会拒绝：`WITH`（CTE，改写成子查询）、语句中的 `;` 与注释（`--`、`/* */`）、以及 `READ ONLY` 事务拦不住的副作用函数（`dblink*`、`lo_export`、`pg_sleep*`、`pg_read_file`、`pg_ls_dir`、`pg_terminate_backend`、`pg_advisory_*`、`set_config`、`pg_replication_*` 等）。`nextval` 这类由事务本身拒绝的不在此列。
- `sql execute` 默认返回 500 行，上限 3000（`--limit`）。输出里的 `truncated` 表示是否还有更多行；文本模式每个单元格截断到 100 字符，取完整值用全局 `--json`。
- `sql execute` 的 `--address` 传只读终端地址可让诊断查询不落到主节点；终端地址取自 `instance get` 的 `Endpoints`。
- 变更类 SQL（DDL/DML）不在命令面内，走控制台或工单流程。

## References

- `../../invocation.md`
- `../../troubleshooting.md`
