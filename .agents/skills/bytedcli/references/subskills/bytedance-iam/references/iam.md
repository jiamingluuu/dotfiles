# IAM 命令参考

以下示例统一使用 `bytedcli iam`；全局参数放在 Domain 前面。

在 bytedcli 分发中，`bytedcli iam` 会把宿主原生命令和 Companion 命令按完整路径融合。同一路径两边都有时 Companion 优先；仅宿主拥有的叶子仍由 bytedcli 执行，例如 `get-employee` 和 `permission apply`。

## bytedcli 宿主兼容命令

```bash
# 宿主原生命令：查询员工资料
bytedcli iam get-employee <username>

# 宿主原生命令：沿用旧 IAM 申请/检查契约
bytedcli iam permission apply \
  --permission demo.feature.access \
  --psm demo.service.api \
  --check-only

bytedcli iam permission apply \
  --role demo-role \
  --node-id <node-id> \
  --reason "need temporary access" \
  --auth-duration 604800 \
  --yes
```

- `permission apply --check-only` 是 bytedcli 宿主的旧检查入口；新排障优先使用 Companion 的 `permission check`。
- `permission apply` 会直接按宿主旧契约创建「字节云IAM权限」工单；新自动化流程优先使用 `permission request submit --plan` 预览后再 `--apply --yes` 提交。
- `get-employee` 是 bytedcli 宿主员工信息查询；Companion 侧对应能力是 `user get --type user --name <username>`。

`get-employee` 返回字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `peopleId` | number | 员工 ID |
| `username` | string | 用户名 |
| `displayName` | string | 显示名称 |
| `email` | string | 邮箱地址 |
| `idPhotoUrl` | string | 证件照 URL |

`permission apply` 主要参数：

| 参数 | 必填 | 说明 |
|---|---|---|
| `--permission` | permission-code 模式必填 | IAM 权限编码；role-only 模式省略 |
| `--psm` | permission-code 模式必填 | 目标 PSM；role-only 模式可作为目标资源 |
| `--node-id` | 否 | role-only 模式目标服务树节点 ID，优先级高于 `--psm` |
| `--resource-type` | 否 | role-only 模式目标资源类型：`node_id` / `psm` / `brn` / `brn_scope` |
| `--resource-value` | 否 | role-only 模式目标资源值，必须和 `--resource-type` 成对出现 |
| `--resource-brn-target` | 否 | role-only 模式 BRN 目标补充字段 |
| `--reason` | 否 | 工单理由；省略时默认 `Need access for verification.` |
| `--role` | role-only 模式必填 | 角色 ID；permission-code 模式省略走推荐角色 |
| `--env` | 否 | 默认 `prod` |
| `--region` | 否 | 默认 `cn` |
| `--user-type` | 否 | 默认 `person_account` |
| `--username` | 否 | 默认当前登录用户 |
| `--auth-duration` | 否 | role-only 模式授权时长，单位秒；默认 604800（7 天） |
| `--approver` | 否 | role-only 模式资源 owner 审批人；省略时自动使用 IAM 推荐审批人 |
| `--data-use-purpose` | 否 | role-only 模式数据用途说明 |
| `--source-url` | 否 | 工单审计上下文 URL |
| `--platform` | 否 | 工单平台字段，默认 `bits` |
| `--extra-params` | 否 | 额外 escape params，`key=value` 可重复 |
| `--check-only` | 否 | 仅查询，不开单 |
| `--yes` | 否 | 非交互模式，直接采用推荐角色 |

`permission apply` 返回字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | `already_has`（已有权限）或 `created`（已开单） |
| `permission` | string | 权限编码 |
| `psm` | string | 目标 PSM |
| `role` | string \| null | 实际申请的角色 ID |
| `link` / `links` | string / string[] | 「字节云 IAM 权限」工单 URL |
| `check` | object | `/check/permission` 原始解析，含 `available_roles` / `default_role_id` |
| `resource_type` / `resource_value` | string | role-only 模式目标资源 |
| `auth_duration` | number | role-only 模式授权时长 |
| `resource_owner_assignees` | string[] | role-only 模式实际使用的资源 owner 审批人 |

## 资源 owner

```bash
bytedcli iam resource owner list --node-id <node-id>
bytedcli --json iam resource owner list --psm example.service.iam
bytedcli --json iam resource owner list --brn brn::bytetree:::node_id:<node-id>
```

- selector 必须且只能选择一个：`--node-id`、`--psm` 或 `--brn`。
- 返回资源基础信息、owner、路径、数据敏感级别、是否叶子节点等。
- PSM 会先通过 IAM resource-info 解析到服务树节点，再查询资源 owner。

## 资源角色发现

```bash
bytedcli iam resource role list --node-id <node-id>
bytedcli --json iam resource role list --node-id <node-id> --permission example.resource.read
bytedcli --json iam resource role list --node-id <node-id> --keyword demo-role
bytedcli --json iam resource role list --node-id <node-id> --filter-by-acl
```

- `--permission` 按权限点筛选可覆盖该权限的角色。
- `--filter-by-acl` 只看当前 ACL 相关角色；不要用它代替“可申请角色”查询。
- `--platform`、`--region`、`--scope`、`--keyword` 可组合过滤。
- 角色返回里的 `spec.permission_pattern` 是角色覆盖的权限集合，`spec.view.cn_name` 是中文展示名。

## 有效权限检查

```bash
bytedcli --json iam permission check \
  --node-id <node-id> \
  --permission example.resource.read \
  --principal demo-user \
  --principal-type person_account

bytedcli --json iam permission check \
  --psm example.service.iam \
  --permission example.resource.read
```

检查结果关键字段：

- `result`：聚合最终结论。
- `rbac_result`：RBAC 角色授权结论。
- `scp_result`：SCP 策略结论。
- `rbac_exception.in_process`：是否已有 RBAC 权限申请正在审批。
- `scp_exception.urls`：可用策略例外申请入口。
- `detail.checker_results[]`：RBAC/SCP 分项详情、推荐角色、命中策略。

判断顺序：

1. `result=true`：有效权限已放行。
2. `rbac_result=false, scp_result=true`：缺 RBAC，先申请角色/权限。
3. `scp_result=false`：策略拦截，检查 `scp_exception.urls` 或策略例外 plan。
4. `*_exception.in_process=true`：已有申请正在审批，不要重复提交同类工单。

## 授权变更历史

```bash
bytedcli --json iam permission history list \
  --node-id <node-id> \
  --principal demo-user \
  --principal-type person_account

bytedcli --json iam permission history list \
  --node-id <node-id> \
  --principal demo-user \
  --event-type revoke \
  --role demo-owner \
  --start 2026-08-13T00:00:00Z \
  --end 2026-08-20T00:00:00Z \
  --page 1 \
  --page-size 20
```

- 查询节点或 BRN 上的 RBAC grant/revoke 事件；资源必须且只能使用 `--node-id` 或 `--brn`。
- 默认查询最近 7 天；服务端只支持最近 30 天，时间使用 RFC3339。
- `--principal` 是被授权或撤权的主体；`--operator` 是执行变更的主体。CLI 会将名称与 type 转换为 IAM principal BRN。
- `--event-type` 只接受 `grant` 或 `revoke`，可重复传入或逗号分隔；`--role` 可按角色名过滤。
- 返回的 `auth_logs` 中重点查看 `operator`、`principal`、`evt_type`、`operate_time`、`operate_role_name`、`resource`；`pagination.has_more` 为 true 时继续翻页。

## 权限或角色申请

```bash
bytedcli --json iam permission request submit \
  --type permission \
  --node-id <node-id> \
  --permission example.resource.read \
  --principal demo-user \
  --reason "need cluster upgrade" \
  --request-key demo-iam-permission-001 \
  --plan

bytedcli --json iam permission request submit \
  --type role \
  --node-id <node-id> \
  --role demo-role \
  --principal demo-user \
  --duration 720h \
  --reason "operate TCE cluster" \
  --request-key demo-iam-role-001 \
  --apply --yes
```

- `--type permission` 会先调用 `permission check`，把权限点转换为 IAM 推荐角色，提交前检查 plan 中的 `role_name`。
- `--type role` 直接申请指定角色；`--role` 可重复传入或逗号分隔。
- 不传 `--apply --yes` 时只返回 plan，不提交。
- 提交必须提供明确 `--reason` 和新的 `--request-key`，用于审计和幂等。
- 审批通过后必须重新运行 `permission check` 验证最终权限，不要把“已提交”说成“已生效”。
- 在 bytedcli 中，`permission request submit` 是 Companion 新入口；`permission apply` 是宿主旧入口，只有需要复用旧工单契约或 `--check-only` 时才使用。

## RBAC binding 授权与撤销

```bash
bytedcli iam permission binding create \
  --node-id <node-id> \
  --role demo-role \
  --principal demo-user \
  --reason "temporary operation" \
  --dry-run

bytedcli iam permission binding create \
  --node-id <node-id> \
  --role demo-role \
  --principal demo-user \
  --reason "temporary operation" \
  --yes

bytedcli iam permission binding delete \
  --node-id <node-id> \
  --role demo-role \
  --principal demo-user \
  --reason "cleanup stale binding" \
  --dry-run
```

- binding 是直接授权/撤销，不是审批申请；只在用户明确要求 grant/revoke 时使用。
- 真实变更必须传 `--yes`；自动化前先使用 `--dry-run`。
- `--role` 可重复传入或逗号分隔，支持角色 ID 或角色名。
- `--duration` 和 `--expires-at` 不要同时猜测；按用户明确要求选择一种。

## SCP 策略查询

```bash
bytedcli --json iam policy list --node-id <node-id>
bytedcli --json iam policy get --uid <policy-uid>
```

- 只有 `permission check` 的 `scp_result=false` 或 `scp_exception.urls` 非空时，才按策略拦截处理。
- `policy list/get` 用于解释策略，不等同于申请例外。
- 不要从自然语言或控制台 URL 猜 policy UID；优先从 check/list 输出提取。

## SCP 策略例外申请

```bash
bytedcli --json iam policy exception submit \
  --type scp \
  --policy-uid <policy-uid> \
  --node-id <node-id> \
  --permission example.resource.read \
  --exception-user demo-user \
  --psm-exists \
  --duration 3h \
  --reason "temporary emergency upgrade" \
  --request-key demo-iam-scp-001 \
  --plan
```

- 不传 `--apply --yes` 时只返回 plan，不提交。
- 已有 PSM 例外使用 `--psm-exists --node-id <node>`；新 PSM 例外使用 `--psm-create <psm>` 且不要传 node-id。
- `--duration` 是相对时长，例如 `3h`、`24h`。
- 策略例外通过后也要重新执行 `permission check`，确认 `scp_result=true`。
- `--type aiauth` 当前用于能力边界提示，不要用 SCP 命令绕过 AI Auth 领域申请。

## 用户和服务账号查询

```bash
bytedcli --json iam user get --type user --name demo-user
bytedcli --json iam user get --type service-account --name demo-service-account
```

- `--type user` 查询人类用户。
- `--type service-account` 查询服务账号。
- 服务账号查询走 principal search；后端可能要求真实账号名，随意字符串可能返回参数或业务错误。
