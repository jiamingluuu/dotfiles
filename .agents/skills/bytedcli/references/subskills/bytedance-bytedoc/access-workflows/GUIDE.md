# ByteDoc 授权流程指南

当任务涉及 `BYTEDOC_ACCESS_REQUIRED`、角色查看、权限预检、PSM 授权或 IAM 用户权限管理时，使用本指南。

## 首屏规则

- `site` 是硬门禁；授权前还必须明确目标数据库的 `backend` 和 `vregion`。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一；任一维度多值时必须让用户选择。
- 用户已给 `backend` 但缺 `vregion` 时，首条搜索/resolver 必须保留该 `backend`。例如 `backend=volc` 时用 `bytedoc search --backend volc` 解析 vregion，不要退回无 backend 的聚合搜索。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选表，不要自行选择后继续授权或换 backend 重试。
- 先确认授权对象：PSM 授权使用 `--roles`，IAM 用户/角色授权使用 `--role-name`；两类 role 不能互换。
- 用户说“写权限”时，不要猜 `write`、`rw`、`DML_RW`；必须展示固定 role 选项并等待用户确认。
- 所有创建/申请类命令先 dry-run，展示 `confirmation.reviewTable`、`payload`、`missingFields` 和 `nextActions`；用户明确确认前不要提交 live。
- 设置 `BYTEDCLI_NETWORK_PROFILE=prod` 时，只允许角色、权限和授权状态查询；ticket/PSM/IAM 用户授权等所有变更意图（包括 dry-run）都会返回 `BYTEDOC_PROD_NETWORK_READ_ONLY`。收到后停止，不要取消 profile、切 ByteDoc 域名或改走 DMS/DBW 绕过。
- `BYTEDOC_ACCESS_REQUIRED` 的恢复命令以 `error.details.setup_commands` 为真源；不要手写不存在的 `access apply`。

## 核心状态机

1. 收集选择器：`site` 必须确认；`backend` 和 `vregion` 必须由用户提供或搜索/resolver 证明唯一。缺少 `site` 时按 `../references/selection-guards.md` 一次性询问；用户已给 backend 时解析命令必须保留 backend，backend/vregion 多值时展示候选让用户选择。
2. 区分授权对象：先确认是 PSM 授权，还是 IAM 用户 / 角色授权；两类 role 不能混用。
3. 查看固定选项和当前状态：classic / Volc IAM 用户/角色流程运行 `bytedoc access role list`；`permission get` 只检查当前操作者是否具备发起授权的前置权限，不能证明 caller PSM 已授权。只要 caller PSM 已知，PSM/token 授权状态必须先运行 `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或使用 `--db-name <db>`）定位目标库；若尚未确定唯一 target/service/db-name、backend 或 vregion，先完成 search/resolver 选择后再跑 `access psm list`；先完成 `access psm list`，再根据状态决定是否进入 `ticket create` / `psm create` dry-run。Volc IAM 用户/角色授权不要改走 PSM。
4. 校验枚举：用户给出的 role/role-name 不完全匹配合法选项时，展示全部正确选项并等待确认，不尝试错误命令。
5. 写操作只做 dry-run：创建 ticket、PSM 或 IAM 预览时不要携带 live submit 标记。
6. 展示 review：展示 `confirmation.reviewTable`、`payload`、`missingFields` 和 `nextActions`。
7. 等待用户明确确认后，才允许进入任何真实提交路径。

## 固定 role 选项

PSM 授权 `--roles` 只能使用：`read`、`readWrite`、`readWriteNoDrop`、`dbOwner`、`dbOwnerNoDrop`、`enableShardingOnly`。

IAM 用户 / 角色授权 `--role-name` 常用选项按 site 的 IAM region 选择：

- `site=cn` / `site=boe`：`bytedoc.data_reader.cn`、`bytedoc.data_writer.cn`、`bytedoc.viewer.cn`、`bytedoc.operator.cn`、`bytedoc.owner.cn`、`owner`。
- `site=i18n-bd` / `site=i18n-tt`：`bytedoc.data_reader.i18n`、`bytedoc.data_writer.i18n`、`bytedoc.viewer.i18n`、`bytedoc.operator.i18n`、`bytedoc.owner.i18n`、`owner`。
- `site=us-ttp`：以 `access role list` 返回的真实 role 为准；当前已验证默认可选 role 是 `owner.tx`。
- `site=eu-ttp`：以 `access role list` 返回的真实 role 为准；当前已验证默认可选 role 是 `owner`。

- 用户说“写权限”时，先确认授权对象。如果是 PSM 授权，让用户在 PSM role 列表中选择；如果是 IAM 授权，让用户在 IAM role 列表中选择。
- `owner` 和 `bytedoc.owner.<region>` 适用边界不同，必须分别展示。
- 不要把 `readWrite` 传给 `--role-name`，也不要把 `bytedoc.data_writer.cn` 传给 `--roles`。
- i18n 站点不要沿用 `.cn` IAM role；否则后端会返回 `role region and iam region not match`。
- 不要根据默认枚举或请求参数合成/猜测 role；`role-name` 必须来自 `access role list` 返回的真实 role。

## DO / DON'T

| 场景                                 | ✅ DO                                                                                                                                                                                                             | ❌ DON'T                                                                                                |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 用户说"写权限"                       | 先问：PSM 授权还是 IAM 用户授权？                                                                                                                                                                                 | 不要直接用 `--roles write`                                                                              |
| 用户给了 `readWrite`                 | 确认是 PSM 授权 `--roles readWrite`                                                                                                                                                                               | 不要传给 IAM 的 `--role-name`                                                                           |
| 用户给了 `bytedoc.data_writer.cn`    | 确认是 IAM 授权 `--role-name bytedoc.data_writer.cn`                                                                                                                                                              | 不要传给 PSM 的 `--roles`                                                                               |
| i18n 站点 IAM 用户授权               | 使用 `bytedoc.data_writer.i18n` 等 `.i18n` role，或以 `access role list` 返回为准                                                                                                                                 | 不要把 `bytedoc.data_writer.cn` 用到 i18n 站点                                                          |
| `us-ttp` IAM 用户授权                | 以 `access role list` 返回的 `owner.tx` 等真实 role 为准                                                                                                                                                          | 不要合成或猜 `bytedoc.data_writer.cn` / `.i18n` / `.tx`                                                 |
| `eu-ttp` IAM 用户授权                | 以 `access role list` 返回的 `owner` 等真实 role 为准                                                                                                                                                             | 不要合成或猜 `bytedoc.data_writer.cn` / `.i18n` / `.eu`                                                 |
| 用户已给 `backend=volc` 但缺 vregion | 先用 `bytedoc search --backend volc` 确认唯一 vregion；IAM 用户授权进入 `access role list` / `access permission get` / `access user apply`，PSM/token 授权进入 `access psm list/create`                           | 不要先执行无 backend 搜索；不要把 Volc IAM 用户授权改成 PSM 授权                                        |
| Volc IAM 用户/角色授权               | 使用 `access role list --backend volc` 展示角色，再用 `access permission get --backend volc` 检查前置权限，最后走 `access user apply` dry-run                                                                     | 不要用 `access psm create` 创建 PSM/token 工单替代用户 IAM 工单                                         |
| 已知 caller PSM 的当前权限判断       | 先运行 `access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）读取 `accountCheck.status` / `accountCheck.authorized`（若返回）/ `accountCheck.roles` | 不要用 `permission get`、`role list` 或申请 dry-run 证明 caller PSM 已授权                              |
| IAM 用户授权的 `--duration` 参数     | 仅用于 `access user grant` / `access user update` / `access user apply`；用 `30d`（30天）、`24h`（24小时）或秒数                                                                                                  | 不要给 `access psm create` / `access ticket create` 携带 `--duration`；不要写 `30min`（不支持分钟单位） |
| dry-run 成功                         | 展示 reviewTable 等用户确认                                                                                                                                                                                       | 不要直接提交 live                                                                                       |
| `Invalid role` 错误                  | 展示完整枚举让用户重选                                                                                                                                                                                            | 不要换一个相似的值重试                                                                                  |

## 被动错误流程

- 如果 Mongo / database 命令返回 `BYTEDOC_ACCESS_REQUIRED`，以 `error.details.setup_commands` 为真源。
- 如果 `agent_protocol.next_state=RUN_SETUP_COMMANDS`，先执行或展示这些 setup commands，再考虑写操作。
- 如果缺少 `site`，按 `../references/selection-guards.md` 向用户询问；如果 backend/vregion 未明确，先搜索或执行 resolver 命令确认唯一候选。
- 如果错误是 `Invalid ByteDoc access role` 或 `ByteDoc access role not found`，停止重试，展示合法 role 列表让用户选择。

## Classic 与 Cloud-Native

```bash
bytedcli --json --site cn --vregion China-North bytedoc access psm list --service "example.bytedoc.demo_orders" --backend classic --account "example.caller.psm"
bytedcli --json --site cn --vregion China-North bytedoc access role list --service "example.bytedoc.demo_orders" --backend classic
bytedcli --json --site cn --vregion China-North bytedoc access permission get --service "example.bytedoc.demo_orders" --backend classic --role-name "bytedoc.data_reader.cn"
bytedcli --json --site cn --vregion China-North bytedoc access ticket create --service "example.bytedoc.demo_orders" --backend classic --account "example.caller.psm"
```

- 已知 caller PSM 时，先使用带目标选择器的 `psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）读取当前 PSM 授权状态；`accountCheck.status=authorized` 时直接展示已有权限，`not_authorized` 时再询问是否申请。
- classic 返回 `inspection.source=classic_get_db_accounts`、cloud-native 返回 `inspection.source=cloud_native_get_account` 时，信任 `accountCheck.status` 和 `accountCheck.roles`；这两类来源读取的是 ByteDoc 数据库账号/Token 授权表，不是 IAM 用户角色绑定。
- 使用 `role list` 展示可选角色和当前绑定。
- 使用 `permission get` 检查当前操作者是否具备发起授权的前置权限；不能证明 caller PSM 已授权。
- 必填字段齐全且 `psm list` 已确认缺权限后，使用 `ticket create` 生成 dry-run 预览。

## Volc PSM 授权

```bash
# 如果用户已给 site/backend/service，但缺 vregion，先保留 backend 解析 vregion
bytedcli --site cn --json bytedoc search --keyword "example.bytedoc.demo_volc" --backend volc

bytedcli --site boe --json --vregion China-BOE bytedoc access psm list --service "example.bytedoc.demo_volc" --backend volc
bytedcli --site boe --json --vregion China-BOE bytedoc access psm list --service "example.bytedoc.demo_volc" --backend volc --account "example.caller.psm"
bytedcli --site boe --json --vregion China-BOE bytedoc access psm create --service "example.bytedoc.demo_volc" --backend volc --operation apply --account "example.caller.psm" --roles "readWrite" --reason "Need confirmed PSM authorization"
```

- Volc PSM token 授权不能用 classic IAM role bindings 证明。
- Volc PSM/token 授权不是 IAM 用户/角色授权；用户明确要“给我/某用户申请 ByteDoc 数据访问角色”时，不要用本节命令替代。
- Volc 返回 `inspection.source=bytedoc_multicloud_get_account` 和 `accountCheck.status` 时，信任这两个字段。
- 不要把 BPM ticket 历史当作当前权限真源。
- `access psm create` 不支持 `--duration`；即使 case 资源里存在 `access.duration`，PSM 授权 dry-run 也不要把它透传到命令中。

## IAM 用户权限管理

```bash
bytedcli --json --site cn --vregion China-North bytedoc access user grant --service "example.bytedoc.demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --principal "demo.user" --principal-type user --duration 30d --reason "Need temporary view access"
bytedcli --json --site cn --vregion China-North bytedoc access user update --service "example.bytedoc.demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --principal "demo.user" --duration 7d --reason "Shorten authorization"
bytedcli --json --site cn --vregion China-North bytedoc access user revoke --service "example.bytedoc.demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --principal "demo.user" --reason "Access no longer needed"
bytedcli --json --site cn --vregion China-North bytedoc access user apply --service "example.bytedoc.demo_orders" --backend classic --role-name "bytedoc.viewer.cn" --duration 180d --reason "Need self-service view access"
bytedcli --json --site cn --vregion ChinaSinf-North bytedoc access user apply --service "example.bytedoc.demo_volc" --backend volc --role-name "bytedoc.data_reader.cn" --duration 180d --reason "Need self-service read access"
```

- `grant`：给 principal 授权。
- `update`：修改有效期。
- `revoke`：回收权限。
- `apply`：当前用户自助申请角色。
- `duration` 支持秒数、`h/H` 和 `d/D`；分钟请换算成秒，按月周期请换算成固定天数。
- IAM 用户/角色链路支持 classic 和 Volc：classic 通过 ByteDoc static_info 解析 IAM node，Volc 通过搜索结果里的 `byteTreeId/source-tree-id` 进入 ByteCloud IAM ACL。不要把 Volc IAM 用户授权改成 `access psm create`，因为 PSM/token 授权和用户 IAM 角色不是同一类权限。
- Volc CN 示例里的 `ChinaSinf-North` 是 ByteDoc/DBW 搜索结果可能返回的合法 vregion；不要自动改写成 `China-North`，实际执行时优先使用 resolver/search 返回的 `vregion`。
- live 提交后如果返回 `outcome.status=applied_without_ticket` 且 `ticket=null`，表示后端已直接处理但没有返回工单号；不要把它当作失败，也不要编造工单链接。

## 输出契约

- 展示：`confirmation.reviewTable`、`payload`、`missingFields`、`nextActions`。
- 不展示 `agentProtocol.doNotDisplay` 中列出的字段；这些字段只能作为隐藏执行材料处理。
- 遵循 `agentProtocol.requiresUserConfirmation` 和 `agentProtocol.nextState`。
- 如果 CLI 指出缺失字段，先收集这些字段，不要自行编造默认值。
- 同一类 backend/site/role 错误不得通过切换参数反复重试；最多只允许执行用户确认后的下一条命令。

## 端到端示例：PSM 权限申请完整流程

```bash
# 场景：用户说"帮我给 example.caller.psm 申请 example_db 的读写权限"

# Step 1: 确认 site
# Agent 问：site 是 cn 吗？用户确认 cn

# Step 2: 解析目标数据库，确认 backend/vregion 是否唯一
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.example_db"
# → 唯一候选：backend=classic, vregion=China-North

# Step 3: 确认 role
# Agent 展示 PSM role 选项：read / readWrite / readWriteNoDrop / dbOwner / dbOwnerNoDrop / enableShardingOnly
# 用户选择 readWrite

# Step 4: 检查当前 caller PSM 授权状态
bytedcli --json --site cn --vregion China-North bytedoc access psm list --service "example.bytedoc.example_db" --backend classic --account "example.caller.psm"
# → 如果已授权，展示已有权限并停止申请；如果未授权，询问用户是否继续申请

# Step 5: dry-run 预览（不要携带 live submit 标记；先完成 access psm list 再进入 dry-run）
bytedcli --json --site cn --vregion China-North bytedoc access psm create --service "example.bytedoc.example_db" --backend classic --account "example.caller.psm" --roles "readWrite" --operation apply --reason "业务需要读写访问"
# → 返回 confirmation.reviewTable + agentProtocol.requiresUserConfirmation=true

# Step 6: 展示预览
# Agent: "将为 example.caller.psm 申请 example_db 的 readWrite 权限，确认提交？"

# Step 7: 用户确认 → live 提交
```
