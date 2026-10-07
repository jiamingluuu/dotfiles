# DevFlow RDS 工单创建引用文档

本引用文档用于通过本仓库 CLI 发起 DevFlow RDS 工单创建，仅覆盖发单，不覆盖审批、执行或催办。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 创建 RDS DDL / DML / CLEAR 工单
- 在 DevFlow 里为某个 RDS 资源发 SQL 变更单
- 希望通过 CLI / skill 多轮补参并最终拿到工单链接

## 意图映射

根据用户需求先判断工单类型，再决定 `rds_op_type`：

- DDL：`CREATE TABLE`、`ALTER TABLE`、新增/修改/删除字段、加索引、改表结构等结构变更
- DML：`INSERT`、`UPDATE`、`DELETE` 等数据写入/更新/删除
- CLEAR：重命名表（rename）、清除表数据（truncate）、删除表（drop）

强约束：

- 当用户需求是“重命名表”“rename table”“truncate table”“清空表/清除表数据”“drop table”“删除表”时，必须走 CLEAR 工单
- 不要因为用户给了 SQL，就把 `rename` / `truncate` / `drop` 误判成 DML
- CLEAR 场景必须设置 `--rds_op_type="clear"`，并继续补 `clear_table_type`
- 其中：
  - rename -> `clear_table_type="rename"`
  - truncate -> `clear_table_type="truncate"`
  - drop -> `clear_table_type="drop"`

## 目标参数

优先从用户对话中收集参数；除 CLI 本地校验要求外，用户未明确提供的参数不要自行猜测，交给后端返回 `pending` 提示继续补齐。

### 通用参数

| 参数 | 类型与取值 | 是否必填 | 作用与省略行为 |
| --- | --- | --- | --- |
| `name` | 字符串 | 由后端按场景校验 | RDS 数据库名。空字符串不会写入请求，由后端提示候选值或要求补充。 |
| `work_item_id` | 十进制整数 | 可选 | 关联的 Meego / WorkItem ID。仅大于 `0` 时写入请求；省略或传 `0` 时不发送。 |
| `rds_op_type` | `ddl` / `dml` / `clear`，大小写不敏感 | 必填 | 工单类型。CLI 会在本地校验，缺失或取值非法时直接报错，不会请求后端。 |
| `risk_confirm` | 布尔值，使用 `--risk_confirm=true` 或 `--risk_confirm=false` | 可选 | 用户是否已确认 DDL 风险。仅在用户看过完整风险和工单计划并明确确认后传 `true`；省略时该字段不写入请求，不能把省略等同于显式 `false`。 |
| `change_background` | 字符串，不超过 200 字 | 由后端按场景校验 | 变更背景或原因。CLI 会去除首尾空白；空值不写入对应的 DDL、DML 或 CLEAR 请求。 |
| `order_auto_exec` | 布尔值，使用 `--order_auto_exec=true` 或 `--order_auto_exec=false` | 可选 | 是否在工单创建后自动执行，适用于 DDL、DML 和 CLEAR。省略时不写入请求，由后端采用默认策略；显式传 `false` 会把 `false` 写入请求。 |

所有布尔参数都应显式写成 `--参数名=true` 或 `--参数名=false`。CLI 只在参数实际出现时才把对应字段写入请求，因此“不传”与“显式传 `false`”语义不同。

### DDL 参数

| 参数 | 类型与取值 | 是否必填 | 作用与省略行为 |
| --- | --- | --- | --- |
| `sql` | 字符串 | 与 `sql_file` 二选一；是否必须由后端校验 | 直接传入 DDL SQL。CLI 会去除整段内容首尾空白。不得与 `sql_file` 同时使用。 |
| `sql_file` | 本地文件路径 | 与 `sql` 二选一；是否必须由后端校验 | 从文件读取完整 DDL SQL，适合包含反引号、引号或换行的复杂 SQL。文件不存在或不可读时 CLI 直接报错；不得与 `sql` 同时使用。 |
| `sync_alert_to_shadow_table` | 布尔值 | 可选 | 是否将 DDL 告警同步到影子表。省略时不写入请求，由后端采用默认策略。 |
| `create_shard_table` | 布尔值 | 可选 | 是否创建分片表。后端提示分片库建表时传 `true`，并同时补充 `shard_key` 和 `shard_key_type`；省略时不写入请求。 |
| `shard_key` | 字符串 | 创建分片表时按后端提示补充 | 分片键字段名。CLI 会去除首尾空白；空值不写入请求。 |
| `shard_key_type` | 推荐值 `int` / `string`；兼容别名 `integer` / `varchar`，大小写不敏感 | 创建分片表时按后端提示补充 | 分片键类型。CLI 将 `int` / `integer` 转为整数类型，将 `string` / `varchar` 转为字符串类型；其他值会在本地报错。 |
| `ban_rename_time_range` | 字符串，例如 `00:00-06:00` | 条件必填 | gh-ost alter 场景的禁止 rename 时间段。仅在后端返回 `include_gh_ost_alter` 相关提示时按提示补充；CLI 不校验时间格式，最终格式与范围由后端校验。 |
| `allow_kill_long_transaction` | 布尔值 | 可选 | 是否允许处理过程中终止长事务。省略时不写入请求；必须依据用户选择或后端提示传值，不得自行设为 `true`。 |
| `master_slave_delay_detect_type` | `all` / `single` / `single_per_vdc`，大小写不敏感 | 可选 | 主从延迟检测策略：`all` 表示全部实例，`single` 表示单实例，`single_per_vdc` 表示每个 VDC 单实例。其他值会在本地报错；省略时不写入请求。 |
| `shard_db_max_concurrent_exec` | 十进制 `int64` 整数 | 可选 | 分片库 DDL 的最大并发执行数。CLI 只校验能否解析为整数，具体有效范围由后端校验；省略或传空字符串时不写入请求，由后端采用默认策略。 |

DDL 同样使用通用参数 `change_background` 和 `order_auto_exec`。

### DML 参数

| 参数 | 类型与取值 | 是否必填 | 作用与省略行为 |
| --- | --- | --- | --- |
| `sql` | 字符串 | 与 `sql_file` 二选一；是否必须由后端校验 | 直接传入 DML SQL。CLI 会去除整段内容首尾空白。不得与 `sql_file` 同时使用。 |
| `sql_file` | 本地文件路径 | 与 `sql` 二选一；是否必须由后端校验 | 从文件读取完整 DML SQL。文件不存在或不可读时 CLI 直接报错；不得与 `sql` 同时使用。 |

DML 同样使用通用参数 `change_background` 和 `order_auto_exec`。

### CLEAR 参数

| 参数 | 类型与取值 | 是否必填 | 作用与省略行为 |
| --- | --- | --- | --- |
| `clear_table_type` | `rename` / `truncate` / `drop`，大小写不敏感 | CLEAR 场景必填 | CLEAR 操作类型：重命名表、清空表数据或删除表。其他值会在本地报错。 |
| `modify_table_names` | JSON 对象字符串，例如 `{"old_table":"new_table"}` | `clear_table_type=rename` 时按后端提示补充 | 重命名映射，键是原表名，值是新表名。必须是 JSON 对象；CLI 会去除键和值的首尾空白并丢弃空键或空值，清理后为空对象会报错。 |
| `clear_or_drop_table_names` | 字符串列表 | `clear_table_type=truncate` 或 `drop` 时按后端提示补充 | 待清空或删除的表名。可重复传同名参数，也可用逗号分隔，例如 `--clear_or_drop_table_names="table_a,table_b"`；空项会被忽略。 |
| `sync_to_ce` | 布尔值 | 可选 | CLEAR 工单是否同步到 CE。省略时不写入请求，由后端采用默认策略。 |

CLEAR 同样使用通用参数 `change_background` 和 `order_auto_exec`。

## 执行原则

- 不要先设计独立 info 查询流程；缺参、风险确认和限制提示全部依赖同一个 create 接口返回 `pending`
- 如果用户意图属于 rename / truncate / drop，优先按 CLEAR 处理，不要走 DML
- DDL 场景下，只有在用户明确确认风险后，才传 `--risk_confirm=true`
- `change_background` 根据用户需求生成，生成时必须控制在 200 字以内；若超出，应压缩表达并保留核心变更信息后再创建工单
- 如果后端返回 `include_gh_ost_alter` 相关 pending，必须要求用户补充 `ban_rename_time_range`
- 如果后端返回分片库建表相关 pending，必须要求用户补充 `create_shard_table=true`、`shard_key`、`shard_key_type`
- `modify_table_names` 必须传 JSON 对象字符串，例如 `{"old_table":"new_table"}`
- `clear_or_drop_table_names` 允许多值，按多次传参或逗号拆分均可
- 当 SQL 里包含反引号、引号、换行等容易触发 shell 转义问题的内容时，优先使用 `--sql_file`，不要直接把 SQL 原文内联到命令参数里
- 如果在完成本技能任务过程中需要使用其他技能，必须优先使用名称带有 `bytedance-devflow-` 前缀的技能

## 调用方式

- DDL：

```bash
bytedcli devflow rds create --name="<name>" --rds_op_type="ddl" --sql="<sql>" --change_background="<change_background>" --bytedcli-skill-dir="<skill所在目录>"
```

- DDL（推荐，复杂 SQL 走文件）：

```bash
bytedcli devflow rds create --name="<name>" --rds_op_type="ddl" --sql_file="<sql_file_path>" --change_background="<change_background>" --bytedcli-skill-dir="<skill所在目录>"
```

- DML：

```bash
bytedcli devflow rds create --name="<name>" --rds_op_type="dml" --sql="<sql>" --change_background="<change_background>" --bytedcli-skill-dir="<skill所在目录>"
```

- CLEAR：

```bash
bytedcli devflow rds create --name="<name>" --rds_op_type="clear" --clear_table_type="<rename|truncate|drop>" --change_background="<change_background>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 优先原样展示 CLI 输出
- `pending` 时必须先把后端返回的提示原样展示给用户，再继续补参或发起确认，不能只概括成“请确认风险”或“请确认操作”
- 如果 `pending` 文案里包含 DDL 风险提示、工单计划详情、候选表名、候选高级选项等内容，必须完整转述这些内容；至少要让用户看到：
  - 当前风险点
  - 当前工单计划详情
  - 需要用户确认或补充的具体字段
- 当 `pending` 场景需要用户确认 `risk_confirm=true` 时，先展示完整风险与计划详情，再明确询问用户是否确认；严禁跳过展示、直接代用户确认
- 成功时只展示工单链接，不额外补充审批或执行指引
- 失败时优先保留原始错误信息，只补充最少量必要说明
