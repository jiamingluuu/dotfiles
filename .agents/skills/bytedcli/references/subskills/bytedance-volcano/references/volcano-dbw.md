# Volcano DBW（Database Workbench）

DBW 在 `ve 1.1.5+` 已提供对应命令面。数据库、表、表结构和内联 SQL 默认使用 `ve dbw`；只有 ve 没有等价参数的本地 SQL 文件入口保留 bytedcli fallback。

## 能力路由

| 任务               | 入口                                                                |
| ------------------ | ------------------------------------------------------------------- |
| 发现数据库实例     | 按引擎使用 `ve rdsmysql/rdspostgresql/rdsmssql/redis/mongodb/vedbm` |
| 列数据库           | `ve dbw ListDatabases`                                              |
| 列数据表           | `ve dbw ListTables`                                                 |
| 获取表结构         | `ve dbw GetTableInfo`                                               |
| 执行内联只读 SQL   | `ve dbw ExecuteSQL`                                                 |
| 从本地文件读取 SQL | `bytedcli volcano dbw sql execute --command-file ...`               |

## 认证与地域

先按照主 skill 的 Babi 自动登录流程为 ve profile 建立凭证，再确认身份：

```bash
ve sts GetCallerIdentity
```

上述 ve 命令统一通过系统参数 `--profile <name>` 和 `--region <region>` 选择身份与地域，不传 bytedcli 的 `--volc-account-id`、`--access-key-id` 或 `--secret-access-key`。本地 SQL 文件 fallback 仍按 bytedcli 命令帮助选择认证参数。

bytedcli fallback 支持显式 Babi 账号、CLI AK/SK、完整的旧 `VOLC_ACCESSKEY` / `VOLC_SECRETKEY` 或官方 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` 环境凭据。旧环境变量优先，STS token 从同一来源读取；完整环境凭据优先于保存的 Babi 默认账号，不完整的高优先级凭据直接报错。Ark 的 Babi-only 限制不适用于 DBW。

## 发现实例

`ve dbw` 没有统一的实例列表 Action，使用产品自身的 ve service：

```bash
# MySQL
ve rdsmysql ListDBInstances \
  --Region cn-beijing --Limit 100 --Offset 0 \
  --region cn-beijing

# PostgreSQL
ve rdspostgresql DescribeDBInstances \
  --PageNumber 1 --PageSize 100 \
  --region cn-beijing

# SQL Server
ve rdsmssql DescribeDBInstances \
  --PageNumber 1 --PageSize 100 \
  --region cn-beijing

# Redis
ve redis DescribeDBInstances \
  --RegionId cn-beijing --PageNumber 1 --PageSize 100 \
  --region cn-beijing

# MongoDB
ve mongodb DescribeDBInstances \
  --PageNumber 1 --PageSize 100 \
  --region cn-beijing

# VeDB MySQL
ve vedbm DescribeDBInstances \
  --PageNumber 1 --PageSize 100 \
  --region cn-beijing
```

不同引擎的分页和地域业务参数不同，不能把一条命令的参数照搬给另一条；执行前以对应 `--help --detail --lang ZH` 为准。

## InstanceType

DBW Action 要求显式 `--InstanceType`。已知值包括：

```text
MySQL | Mongo | Redis | Postgres | MSSQL | VeDBMySQL
```

常见实例 ID 前缀可辅助判断：`mysql-`、`mongo-`、`redis-`、`postgres-`/`pgsql-`、`mssql-`、`vedb-`/`vedbm-`。前缀只是辅助，不能覆盖用户明确给出的类型；无法确定时先查询产品实例详情。

## 列数据库

```bash
ve dbw ListDatabases \
  --InstanceID <instance-id> \
  --InstanceType MySQL \
  --PageNumber 1 --PageSize 20 \
  --region cn-beijing
```

## 列数据表

```bash
ve dbw ListTables \
  --InstanceID <instance-id> \
  --InstanceType MySQL \
  --Database demo_db \
  --PageNumber 1 --PageSize 20 \
  --region cn-beijing
```

## 获取表结构

```bash
ve dbw GetTableInfo \
  --InstanceID <instance-id> \
  --InstanceType MySQL \
  --Database demo_db \
  --Table demo_table \
  --region cn-beijing
```

## 执行只读 SQL

`ExecuteSQL` 的 Action 名无法表明 SQL 是否写入。Agent 只能直接执行明确的单条 `SELECT`、`SHOW`、`DESCRIBE`、`DESC` 或 `EXPLAIN`；其他 SQL 一律按写操作处理，不得通过 DBW ExecuteSQL 绕过审批或工单流程。

```bash
ve dbw ExecuteSQL \
  --InstanceID <instance-id> \
  --InstanceType MySQL \
  --Database demo_db \
  --Commands 'SELECT * FROM demo_table LIMIT 20' \
  --TimeOutSeconds 60 \
  --region cn-beijing
```

以下情况必须停止并改走对应的变更工单或经确认的专用命令：

- DDL、DML、存储过程调用或多语句脚本；
- SQL 类型无法确定；
- 查询包含副作用函数；
- 用户要求修改线上数据或 schema。

## SQL 文件 fallback

ve 没有与 `--command-file` 等价的文件参数。需要直接读取本地文件时保留 bytedcli；该命令仍只允许读取类 SQL：

```bash
bytedcli volcano dbw sql execute --instance-id <instance-id> --instance-type MySQL --region cn-beijing --database demo_db --command-file <file-path>
```

不要把文件内容通过命令替换拼进 `ve --Commands`，否则多行 SQL、引号和敏感文本会进入 argv。后续 ve 如果新增原生文件参数，再将本 fallback 改为 ve。

## 参数差异

| 旧 bytedcli 参数    | ve DBW 参数            |
| ------------------- | ---------------------- |
| `--instance-id`     | `--InstanceID`         |
| `--instance-type`   | `--InstanceType`       |
| `--database`        | `--Database`           |
| `--table`           | `--Table`              |
| `--command`         | `--Commands`           |
| `--timeout-seconds` | `--TimeOutSeconds`     |
| `--region`          | ve 系统参数 `--region` |

## 参考文档

- [SQL 任务执行](https://www.volcengine.com/docs/6956/152609?lang=zh)
- [ListDatabases](https://www.volcengine.com/docs/6956/2068408?lang=zh)
- [ListTables](https://www.volcengine.com/docs/6956/2068409?lang=zh)
