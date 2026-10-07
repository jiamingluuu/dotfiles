# RDS 服务说明

当前 ve 使用以下 service 名：

| 引擎       | service                                |
| ---------- | -------------------------------------- |
| MySQL      | `rdsmysql`（也支持 `rds_mysql` alias） |
| PostgreSQL | `rdspostgresql`                        |
| SQL Server | `rdsmssql`                             |

不要使用 `ve rds_postgresql` 或 `ve rds_mssql`。

## PostgreSQL 易错点

- `CreateDBInstance` 使用 JSON body。
- HA PostgreSQL 的 `NodeInfo` 同时需要 Primary 和 Secondary；只有 Primary 会失败。
- 应用登录账号的 `AccountPrivileges` 可使用 `Inherit,Login`，不要套用 MySQL/Redis 的 `ReadWrite`。
- 创建 Database 时优先把 Owner 设置为应用账号；默认 `public` schema 权限不足时再调用 `ModifySchemaOwner`。
- `CharacterSetName` 只有在当前接口枚举经过确认后才传，不要凭经验写 `UTF8`。
- 实例显示 Running 后，账号、数据库、schema、endpoint 操作仍可能短暂遇到独占状态；短间隔重试，不要重建实例。

## 生命周期与清理

RDS 创建耗时且计费。只在明确批准后创建最小按量实例，等待引擎特定状态，验证后立即删除并回查。现有 AllowList 是账号资源，不得当作测试资源删除。
