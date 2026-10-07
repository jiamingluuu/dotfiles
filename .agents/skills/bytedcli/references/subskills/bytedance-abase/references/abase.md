# ABase

ABase2 namespace、table 与在线查询命令。

```bash
bytedcli abase list --scope all --keyword "demo.namespace" --limit 20
bytedcli abase list --scope mine --limit 20
bytedcli abase list --scope favor --limit 20
bytedcli abase search --psm "demo.namespace"
bytedcli abase search --psm "bytedance.abase2.demo_namespace"
bytedcli abase get --psm "demo.namespace"
bytedcli abase get --namespace-id 1001 --cluster "sample-cluster"

# 共享控制面：用 --site 选控制面，--region 选具体 deployment
bytedcli --site us-ttp abase get --psm "demo.namespace" --region US-TTP2
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-TTP2
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region US-EastRed
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-Compliance
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-Compliance2
bytedcli --site i18n-tt abase get --psm "demo.namespace" --region Singapore-Central
bytedcli --site i18n-tt abase get --psm "demo.namespace" --region US-East
```

Table 查询：

```bash
bytedcli abase table list --psm "demo.namespace"
bytedcli abase table list --cluster "sample-cluster" --namespace "demo_namespace"
bytedcli abase table get --psm "demo.namespace" --table "sample_table"
bytedcli abase table get --cluster "sample-cluster" --namespace "demo_namespace" --table-id 2001
```

在线查询：

```bash
bytedcli abase command list
bytedcli abase command list --psm "demo.namespace" --table "sample_table"
bytedcli abase command run --psm "demo.namespace" --table "sample_table" --command "GET" --inputs "sample-key"
bytedcli abase command run --cluster "sample-cluster" --namespace "demo_namespace" --table "sample_table" --payload-json '{"command":"GET","inputs":"sample-key"}'
```

区域元数据：

```bash
bytedcli abase region list
bytedcli abase location list
bytedcli --site i18n-tt abase region list --region "Singapore-Central"
```

ABase classic（1.0）集群查询（只读，使用独立的 ByteCloud gateway path）：

```bash
# 服务（集群）列表；--keyword 与 --limit 均为客户端本地过滤/截断（后端一次性返回全量）
bytedcli abase cluster list
bytedcli abase cluster list --keyword demo --limit 50

# 单集群详情 + 概要（version / shard_num / 磁盘用量）
# --psm 用集群 PSM（如 abase_demo_service），不是 list 里显示的短名
bytedcli abase cluster get --psm abase_demo_service
bytedcli abase cluster get --psm abase_demo_service --no-summary
```

ACP 鉴权（SDK 运行态授权，查询/新增/删除走 option 参数）：

```bash
# 查询某 namespace 已授权的 PSM / 用户（--region 为按 region 值的本地过滤，可省略）
bytedcli abase acp list --namespace "demo_namespace"
bytedcli abase acp list --namespace "demo_namespace" --perm-region "sinf"

# 新增授权：先 --dry-run 预览，再换成 --yes 提交（会生成 BPM 审批工单）
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --dry-run
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --yes
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --user "demo-user" --perm rw --yes

# 删除授权（同样生成审批工单）
bytedcli abase acp delete --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --dry-run

# 对账修复该 namespace 的 ACP 授权（对应控制台「一键修复 ACP 授权」）
bytedcli abase acp sync --namespace "demo_namespace" --dry-run
bytedcli abase acp sync --namespace "demo_namespace" --yes
```

工单（BPM workflow record，`target_system=abase2`）：

```bash
# 工单列表 / 详情 / 审批人
bytedcli abase ticket list --namespace "demo_namespace" --creator "demo-user"
bytedcli abase ticket list --status "owner_approve" --page 1 --page-size 10
bytedcli abase ticket get --id 108000001
bytedcli abase ticket approvers --id 108000001

# 审批 / 驳回 / 取消（高风险写，先 --dry-run 再 --yes）
bytedcli abase ticket approve --id 108000001 --dry-run
bytedcli abase ticket approve --id 108000001 --comment "lgtm" --yes
bytedcli abase ticket reject --id 108000001 --reason "duplicate request" --yes
bytedcli abase ticket cancel --id 108000001 --yes

# 执行失败后重试（无需重新审批）
bytedcli abase ticket retry --id 108000001
```

在 DataLeap 上创建 ABase 逻辑表：

```bash
bytedcli abase logic-table create \
  --namespace "demo_namespace" \
  --database "demo_db" \
  --table "demo_table" \
  --column "author_id:BIGINT:author" \
  --column "data_col_type:INT" \
  --column "date:VARCHAR:date" \
  --primary-key "author_id,data_col_type" \
  --key-format 'demo_table:${author_id}:${data_col_type}' \
  --value-type "general" \
  -r cn
```

按当前用户权限搜索 ABase 逻辑表（biowner）：

```bash
bytedcli abase logic-table list --name "demo_tbl" --parent-name "demo_db" -r cn
bytedcli abase logic-table list --page 2 --page-size 10 --sort-field name --sort-order asc
```

Notes:

- 国内生产默认使用 `--site cn`（可省略）；跨站点时用全局 `--site boe|i18n-bd|i18n-tt|us-ttp|eu-ttp`，再用 `--region` 选择共享控制面上的 deployment。
- `us-ttp` 站点由 `US-TTP` 与 `US-TTP2` deployment 共享控制面，`eu-ttp` 站点由 `EU-TTP`、`EU-TTP2`、`US-EastRed`、`EU-Compliance` 与 `EU-Compliance2` deployment 共享控制面。`i18n-tt` 用 `--region Singapore-Central` 或 `--region US-East` 选择 ROW 成员。使用 `--psm` 解析 namespace 时，CLI 会先聚合完整 PSM 与 suffix 的全部精确同名候选，再读取候选详情，并按 `--region` 指定的 deployment 精确筛选。
- `--region US-TTP`、`--region US-TTP2`、`--region EU-TTP`、`--region EU-TTP2`、`--region US-EastRed`、`--region EU-Compliance`、`--region EU-Compliance2`、`--region Singapore-Central` 和 `--region US-East` 是 deployment 选择条件，不是同名 namespace 的跨区域回退条件。指定 deployment 中没有候选时返回 `ABASE_NOT_FOUND`；筛选后仍有多个候选时返回 `ABASE_AMBIGUOUS`，不会接受 ROW/SG 或其他 deployment 的同名 namespace。旧 overlay 简写（如 `us`、`gcp`、`i18n`）不会进入这张表，只回落到当前 `--site` 的 default host，不要用它们选 deployment。
- 在 `i18n-tt`（默认/sg）站点，ABase2 namespace、table、command、region、location 和 ACP 请求统一通过 ByteCloud gateway；CLI 会自动补齐所需 routing header，用户无需手工传 header。Classic cluster 与 BPM ticket 继续使用各自的 gateway path，DataLeap logic-table 保持独立。
- `abase search --psm` 支持完整 PSM（例如 `bytedance.abase2.demo_namespace`）；首查无结果时会自动按 suffix（例如 `demo_namespace`）重试，短 namespace 也可直接搜索。
- `abase acp add/delete` 用 `--perm-region` 指定授权所属的 **ABase 可读 region 名**（如 `ChinaSinf-North`），与其他命令的 `--region` deployment 选择（如 `US-TTP`）不是一回事；工单 config 里的 `region` 字段用的就是这个可读名。
- `abase acp list --perm-region` 是对回读结果的本地过滤，取值是**短名**（如 `sinf`），与提交授权用的可读名不同，按 `acp list` 回读到的值填。
- 旧的 `--region` 在这三个 acp 命令上保留为**隐藏兼容别名**（`!2359` 已上线，避免破坏既有脚本），新脚本一律用 `--perm-region`；同传两个且值不同会报 `ABASE_INPUT_ERROR`。其他 abase 命令（`list`/`get`/`table`/`ticket` 等）的 `--region` 是 deployment 选择条件（如 `US-TTP`、`Singapore-Central`），语义不同，别混。
- `abase acp list` 的 JSON 输出字段名仍是 `region`（未改名，保持向后兼容）。
- `abase acp sync` 对应控制台「一键修复 ACP 授权」，请求体只有 `{namespace}`（与控制台前端一致，CLI 只发送这一个字段）；与 `acp add` / `delete` 不同，它不返回工单 id，执行后用 `acp list` 回读确认实际授权。
- ACP `add` / `delete` / `sync` 和工单 `approve` / `reject` / `cancel` 都是写操作，必须带 `--dry-run`（预览）或 `--yes`（执行）之一；两者都不带会返回 `ABASE_CONFIRMATION_REQUIRED`。
- 授权提交后返回 BPM 工单 id，生效需要 namespace owner 审批；用 `abase ticket get --id <id>` 跟进状态，`abase ticket approvers --id <id>` 查看每个阶段可审批人（`config._context_.assignees_map`），当前阶段列出的任何人都可审批。
- `abase ticket *` 使用独立的 ByteCloud gateway BPM 工单路径；`--status` 过滤用 BPM 状态 key（如 `owner_approve`、`done`）。
- `abase ticket list` 后端未返回 total 时，JSON 用 `current_count` + `page`/`page_size` 表达当前页上下文，不会用页内条数冒充 total。
- Redis / Cache 服务仍使用 `bytedcli cache ...`，ABase2 namespace / table 使用 `bytedcli abase ...`。
- `--limit` 对 namespace list/search 是本地输出上限；后端列表接口当前不返回可靠 total，JSON 输出使用 `current_count`。
- `abase logic-table create` 走 DataLeap CoralNG（`management/data-store`，`typeName=ABaseLogicalTable`），region 参数与 hive/paimon 一致；命令不生成 DDL，也不做 explain，`--primary-key` 中的列必须先出现在 `--column` 里。
- `abase logic-table create --column name:type[:comment]` 里的 `type` 是 **ByteSchema 大写枚举**：`INT / BIGINT / VARCHAR / DOUBLE / FLOAT / BOOLEAN / DATE / TIMESTAMP / BINARY`。**不要**沿用 hive / paimon skill 里的小写 `bigint / int / string`——CoralNG 后端拒识大小写敏感，会返回 `校验Schema错误: not find the byteSchemaType, the typeName = bigint`；handler 已加入拒识与 hint。
- `abase logic-table list` 走 DataLeap CoralNG（`data-stores/info/self`，`filterMode=biowner`），只返回当前登录用户有 biowner 权限的表；`--name` 匹配逻辑表名，`--parent-name` 匹配物理表 / app group 名，两者都是模糊匹配。
