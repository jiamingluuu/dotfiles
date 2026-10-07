---
name: bytedance-ent
description: "Operate Ent Platform / UDS Storage IAC via bytedcli. Use when tasks mention Ent Platform, UDS, Entity, Storage IAC, StorageUri, entity schema workflow, ORM generation, ent.tiktok-row.net, or creating/importing MySQL/RDS tables through Entity workflows."
---

# bytedcli Ent Platform / UDS

## When to use

- 用户提到 Ent Platform、UDS、Entity、Entity Schema、Storage IAC、StorageUri、ORM 生成、`ent.tiktok-row.net`。
- 需要把新的 MySQL/RDS 表通过 Entity 平台录入元信息并提交 workflow，审批通过后由平台执行建表。
- 需要把已有 RDS 表导入/迁移为 Storage IAC entry，并检查字段描述/annotation 覆盖率。
- 需要解释 UDS MySQL、Entity、StorageUri、mapping、schema workflow、ORM 生成之间的关系。

如果任务只是直接查询或操作 RDS 数据、提交传统 RDS BPM DDL/DML 工单，请使用 `bytedance-rds`。如果任务只是查询 BMT 资源绑定，请使用 `bytedance-bmt`。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 国际站 Ent Platform 通常使用：`bytedcli --site i18n-tt ...`
- 首次调用前先登录目标站点：`bytedcli --site i18n-tt auth login`
- 当前命令只自动化 Entity Platform 的提交动作，不负责申请 MySQL 集群或审批 workflow。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Platform Concepts

- **UDS / Unified Data Storage**：面向业务 Entity 的数据访问层。对 MySQL 场景，UDS 负责 Entity Schema 管理、ORM 模型和接口代码生成；底层 MySQL 集群资源、容量、运维和跨机房能力仍需要由对应平台或 owner 管理。
- **Entity**：业务语义对象及其字段、主键、索引、owner、描述等元信息。Entity 名称应表达业务对象，不要只按数据库或表名命名。Storage IAC 表工作流会把 DDL 映射成 Entity fields、indices 和 MySQL mapping。
- **StorageUri**：Entity 绑定的底层存储映射，例如 `sample/mysql/demo`。生产 StorageUri 不要猜，优先由用户提供或从平台/UDS oncall 确认。
- **Mapping**：Entity 字段与底层 MySQL 表字段、主键、索引、表选项之间的映射关系。
- **Schema Change Workflow**：提交 Entity 变更后的平台流水线。典型阶段包含检查/审批、schema 合入、DDL 执行以及后续集成。
- **ORM Generation**：Entity Schema 合入后的集成动作之一，生成 Entity Model 与 CRUD API。workflow 提交成功不等于业务服务已经接入 ORM。

## Full Workflow

新建 MySQL 表的完整链路不是一个单点 API，而是一串平台动作：

1. **确认目标环境**
   - 明确站点：通常国际站用 `--site i18n-tt`。
   - 明确 `StorageUri`、目标 `vregion`、RDS DC/VDC、owner。
   - 确认底层 DB/StorageUri 已存在或已由平台/oncall 准备好。

2. **准备 DDL 与元信息**
   - DDL 必须是 `CREATE TABLE`。
   - 字段要带清晰 `COMMENT`，因为 CLI 会用 comment 生成 Entity field description。
   - 主键、普通索引、唯一索引要在 DDL 中声明；索引名遵循业务规范。
   - 准备 Entity 描述、owner、明确合规声明；含 TikTok user data 时用 `--contains-tt-user-data`，不含时必须由用户提供 `--compliance-reason`。不确定是否包含 TikTok user data 时不要替用户判断。

3. **提交新表 workflow**
   - CLI 会先按 `storage_uri + table` 做 entity precheck，避免重复创建。
   - CLI 解析 DDL，生成 Entity fields、indices、MySQL columns、table indices、table options。
   - CLI 调用 Ent Platform `schema_change` 创建 workflow。
   - 如果这里报 `no prod storage schema`，不要反复重提 `submit-table`；这通常说明 Ent metadata / storage schema 状态不匹配，应转下面的 Existing Metadata DDL Fallback。

```bash
bytedcli --site i18n-tt --json ent storage-iac submit-table \
  --storage-uri sample/mysql/demo \
  --table sample_table \
  --ddl-file ./sample_table.sql \
  --owner user.name \
  --vregion Singapore-Central \
  --rds-dc sg1 \
  --description "Sample table for demo workflow" \
  --compliance-reason "Demo table without TikTok user data"
```

4. **平台审批与检查**
   - 返回 `workflow_id` / `workflow_url` 后，后续由 Ent Platform workflow 推进。
   - Entity owner 或相关审批人需要在平台上审核。
   - Remote/check stage 会做 schema、权限、合规、DDL 等检查。

5. **Apply / DDL 执行**
   - 审批通过后，平台合入 Entity Schema。
   - 对 Storage IAC 新表流程，平台根据提交的 DDL 执行建表或变更动作；不要绕过平台直连 RDS 手动建表。

6. **Integration**
   - ORM 代码生成需要在平台 setting / workflow 中开启并等待完成。
   - 若涉及 DECC 或互通打标，需要按平台集成阶段处理；当前 CLI 不自动完成这类人工选择或跳过动作。

7. **业务接入与验证**
   - ORM 生成完成后，业务服务再引入 `ent_orm` 并初始化对应 Entity runtime。
   - 通过平台、RDS 读命令或服务侧 smoke 验证表、schema、读写路径。

## Existing Table Import

已有 RDS 表不走 `submit-table`，而走 entry migration：

```bash
bytedcli --site i18n-tt --json ent storage-iac create \
  --storage-uri sample/mysql/demo \
  --table existing_table
```

这条命令会：

- 按表预检查 entity 是否存在。
- 调用 `entry/batch_migrate` 导入/迁移 Storage IAC entry。
- 提交后反查 entity detail，汇总字段 description/annotation 覆盖率。

它不会执行 RDS 物理建表 DDL，也不是新表 workflow。

## Metadata-only Workflow Fallback

当 `submit-table` 因 Ent 后端找不到 prod storage schema 等平台兼容问题失败，但目标 StorageUri 已存在、且需要先创建 Entity metadata 时，使用 `create-metadata` 提交前端同款的 V1 `schema_change`。这一步只登记 Ent metadata，不下发物理 RDS DDL：

```bash
bytedcli --site i18n-tt --json ent storage-iac create-metadata \
  --storage-uri tiktok/mysql/gpcp \
  --table sample_table \
  --ddl-file ./sample_table.sql \
  --owner user.name \
  --vregion Singapore-Central \
  --rds-dc sg1 \
  --compliance-reason "Demo table without TikTok user data"
```

这条命令会：

- 按 `storage_uri + table` 预检查 Entity 是否已存在。
- 解析 `CREATE TABLE` DDL，生成 Entity fields、indices、MySQL mapping 和 `table_form`。
- 调用 `/api/platform/v1/schema_change` 创建 metadata workflow，`modification_type=1`。
- 不携带 `ddl_execution_data_list`，因此不会执行物理建表；metadata applied 后，再用 `deploy-table-ddl` 下发物理 DDL。
- 提交前校验 payload：`format_version` 必须是 `V2`，DDL 字段不能含字面量 `\n`。

## Existing Metadata DDL Fallback

当 Ent metadata 已经存在，但物理 RDS 表缺失时，不要再用 `submit-table` 创建新 Entity，也不要直连 RDS 执行 DDL。使用 `deploy-table-ddl` 基于现有 Entity detail 的 `hash_version` 提交 V2 `schema_change`，让 Ent/Storage IAC 下发物理 DDL：

```bash
bytedcli --site i18n-tt --json ent storage-iac deploy-table-ddl \
  --storage-uri tiktok/mysql/gpcp \
  --table agent_iteration_runtime_command \
  --ddl-file ./agent_iteration_runtime_command.sql \
  --vregion Singapore-Central \
  --rds-dc sg1 \
  --creator user.name
```

这条命令会：

- 查询 `/api/platform/v2/entity/{entity}`，读取现有 `entity_mapping` 和 `hash_version`。
- 构造 V2 `schema_change`，带 `previous_hash_version`，`modification_type=2`。
- 更新 `entity.modules.iac.table_form.sql_ddl`、MySQL mapping 的 table option DDL，以及 `ddl_execution_data_list[].sql`。
- 保留现有 `entity.modules.iac.table_form.creator`；当平台返回 `E-M-S` 占位或缺失时，默认回退到 Entity owner，也可通过 `--creator` 显式指定。
- 用结构化 JSON 提交，避免 shell quoting 把换行变成字面量 `\n`。
- 提交前校验 payload：`format_version` 必须是 `V2`，DDL 字段不能含字面量 `\n`。
- 输出 `workflow_id`、`workflow_url`、当前 workflow status（如果平台返回）、`logid`，以及用于验证的 RDS 查询命令。

适用判断：

- `submit-table` 报 `no prod storage schema`，并且平台上已经能看到对应 Entity metadata。
- RDS 上物理表缺失，需要 Ent/Storage IAC 正式下发 DDL。
- 不是“已有物理表导入 metadata”的场景；已有物理表仍用 `storage-iac create`。

DDL 准备坑位：

- 用 `--ddl-file` 优先于 `--ddl`。如果命令里出现字面量 `\n`，CLI 会拒绝提交；请把 SQL 写入文件保留真实换行。
- 索引命名遵循 `idx_...`；唯一键命名遵循 `uk_<field_name>` 或业务约定下的 `uk_` 前缀，不要继续使用 `ix_`。
- 需要验证 RDS 结果时，用 `bytedcli rds db query ... "SHOW CREATE TABLE <table>"` 或 `SHOW TABLES` / `SELECT`。`rds db query` 不适合作为直连 DDL 执行入口。

## Command Boundaries

- `submit-table` 会创建 Entity workflow，但不会审批 workflow、关闭 workflow、轮询到最终成功、创建 MySQL 集群、申请 StorageUri、接入 ORM 或修改业务代码。
- `submit-table` 是“新表 + 新 Entity + 物理 DDL”的 happy path。若它因平台兼容问题失败，但 StorageUri 已存在且 Entity metadata 尚不存在，fallback 是 `create-metadata`。
- `create-metadata` 只创建 Entity metadata workflow，不执行物理 RDS DDL、不审批、不关单。
- `deploy-table-ddl` 只提交基于已有 Entity metadata 的 V2 `schema_change`，不会创建新 Entity、不会审批、不会关单。
- `create` 是已有表导入/迁移，不是创建新 RDS 表。
- CLI 不会替用户判断 TikTok user data 合规状态；`submit-table` 必须显式传 `--contains-tt-user-data` 或 `--compliance-reason`。
- 不要为了测试绕过 Ent Platform 直连 RDS 建表；真实 smoke 应使用 `bytedcli ent storage-iac submit-table` 创建测试 workflow。
- 不要把通用 UDS MySQL 文档中的历史手工 RDS ticket 流程直接套到 Storage IAC `schema_change` 自动建表链路上；当前 CLI 以平台 workflow 为准。
- 审批动作可能需要 CN token：如果 ROW token 能提交但审批失败，检查 `token_bytecycle`，不要只看 ROW 站点 token。
- Workflow `RUNNING` 是 IaC 下发中的正常状态，不要误判为失败。只有 payload 明显坏掉（例如字面量 `\n`、V1/V2 形态不对、缺 `previous_hash_version`）时，才应关单重提。

## Quick Checks

```bash
# 查看命令帮助
bytedcli --site i18n-tt ent storage-iac --help
bytedcli --site i18n-tt ent storage-iac submit-table --help
bytedcli --site i18n-tt ent storage-iac deploy-table-ddl --help

# 确认当前登录态
bytedcli --site i18n-tt --json auth status

# 新表 workflow 提交后，输出中应包含 workflow_id / workflow_url / logid
bytedcli --site i18n-tt --json ent storage-iac submit-table \
  --storage-uri sample/mysql/demo \
  --table sample_table \
  --ddl-file ./sample_table.sql \
  --owner user.name \
  --vregion Singapore-Central \
  --compliance-reason "Demo table without TikTok user data"

# 已有 metadata 但物理表缺失时，补 DDL 下发 workflow
bytedcli --site i18n-tt --json ent storage-iac deploy-table-ddl \
  --storage-uri tiktok/mysql/gpcp \
  --table agent_iteration_runtime_command \
  --ddl-file ./agent_iteration_runtime_command.sql \
  --vregion Singapore-Central \
  --rds-dc sg1
```

## References

- `../../invocation.md`
- `../../troubleshooting.md`
- UDS MySQL User Guide: https://bytedance.larkoffice.com/wiki/wikcnLupCgyA4k9cdhBaA44uZZd
