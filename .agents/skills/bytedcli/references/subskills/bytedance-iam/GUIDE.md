---
name: bytedance-iam
description: "Inspect IAM resource owners, RBAC roles, effective permissions, authorization history, policy decisions, permission applications, bindings, policy exceptions, employee/user profiles, and service accounts through bytedcli. Invoke whenever tasks mention IAM、鉴权、权限检查、授权历史、角色申请、授权、SCP、策略例外、owner、employee、service account、权限工单, or another component returns an IAM permission interception."
---

# IAM

## When to use

- 查询 IAM 资源 owner、可申请角色或当前 ACL 角色
- 检查某个用户、服务账号、PSM、节点、BRN 或 BRN scope 是否拥有权限
- 查询最近 30 天内节点或 BRN 的 RBAC 授权、撤权历史
- 判断拒绝来自 RBAC、SCP 策略，还是已有申请正在审批
- 处理其他组件返回的 IAM 权限拦截、authorization failure、permission denied 或权限申请入口
- 提交 RBAC 角色/权限申请，或授予/撤销 RBAC binding
- 查询 SCP 策略，申请 SCP 策略例外
- 查询 user、employee 或 service account 基础信息

## Quick start

使用 `bytedcli iam`；首次调用会按锁定版本安装 Companion：

```bash
# 查询资源 owner 与可申请角色
bytedcli iam resource owner list --node-id <node-id>
bytedcli iam resource role list --node-id <node-id> --permission example.resource.read

# 检查有效权限和聚合决策
bytedcli --json iam permission check --node-id <node-id> --permission example.resource.read

# 先生成申请计划，再明确提交
bytedcli --json iam permission request submit \
  --type permission \
  --node-id <node-id> \
  --permission example.resource.read \
  --principal demo-user \
  --reason "need cluster upgrade" \
  --request-key demo-iam-permission-001 \
  --plan

bytedcli --json iam permission request submit \
  --type permission \
  --node-id <node-id> \
  --permission example.resource.read \
  --principal demo-user \
  --reason "need cluster upgrade" \
  --request-key demo-iam-permission-001 \
  --apply --yes

# bytedcli 宿主兼容命令
bytedcli iam get-employee demo.user
bytedcli iam permission apply --permission demo.feature.access --psm demo.service.api --check-only
```

## bytedcli merged command surface

`bytedcli iam` 是 bytedcli 宿主原生命令和 bytecloud-official-pack Companion 命令按完整路径融合后的命令面；不是整个 `iam` group 一次性归属某一侧。

| Command path                                         | Owner in bytedcli | Notes                                        |
| ---------------------------------------------------- | ----------------- | -------------------------------------------- |
| `iam get-employee`                                   | bytedcli host     | 宿主原生命令，查询员工资料                   |
| `iam permission apply`                               | bytedcli host     | 宿主原生命令，保留旧申请/`--check-only` 契约 |
| `iam permission check`                               | Companion         | 同路径冲突时 Companion 优先                  |
| `iam permission history list`                        | Companion         | 查询最近 30 天授权/撤权历史                  |
| `iam permission request submit`                      | Companion         | 新申请入口，支持 `--plan` 与 `--apply --yes` |
| `iam permission binding create/delete`               | Companion         | 直接授权/撤销，真实变更需 `--yes`            |
| `iam resource ...`, `iam policy ...`, `iam user get` | Companion         | 新 IAM domain 能力                           |

## Agent guidance

- 先跑 `permission check --json`，再根据 `result`、`rbac_result`、`scp_result` 和 `*_exception.in_process` 判断下一步。
- 排查“曾有权限但当前无权限”时，在 `permission check` 后运行 `permission history list`；按 principal、operator、role 和 grant/revoke 筛选，确认授权何时被撤销及操作者。该接口仅支持最近 30 天，默认查最近 7 天。
- 其他组件返回 IAM 拦截时，优先保留其中的 resource selector、permission、principal、policy UID、申请 URL 或 request ID；缺字段时再用 IAM 查询补齐，不要从错误文案猜。
- `result=false, rbac_result=false, scp_result=true` 表示 RBAC 缺失；优先提交 RBAC 权限/角色申请。
- `scp_result=false` 或 `scp_exception.urls` 非空时，才进入策略例外申请；不要因为输出里出现 policy metadata 就误判为策略拦截。
- `permission request submit --type permission` 会基于 `permission check` 推荐角色生成申请；提交前先看 `--plan` 中的 `role_name`。
- 写操作必须有边界：申请类先 `--plan`，提交时使用新的 `--request-key`、明确 `--reason` 和 `--apply --yes`；binding 类先 `--dry-run`，真实变更传 `--yes`。
- 资源 selector 按命令语义选择；`resource owner list` 仅支持 `--node-id`、`--psm` 或 `--brn`。PSM 检查报 `psm and nodeID do not match` 时，先用 `resource owner list --psm` 解析 node，再用 node-id 复查。
- 稳定消费结果时使用 `--json`，并把全局参数放在 domain/command 前面。
- 认证状态按 Binary/Host 隔离；`bytedcli iam` 使用宿主一次性注入的 JWT，独立入口使用各自 Binary 的登录态。
- 参数或输出不确定时优先查看对应命令的 `--help`，不要猜测请求体、policy UID 或审批 URL。

## Custom user groups (iam user-group)

Manage IAM 门户自定义用户组 (custom group) membership and resource-role grants across `cn` / `i18n-tt` / `us-ttp` / `eu-ttp`.

- `bytedcli [--site <site>] iam user-group list --keyword <name>` — resolve group uid/admins.
- `bytedcli --site <site> iam user-group member list --group <name>` — list members/admins (member_type 1=member, 2=admin).
- `bytedcli iam user-group grant --group <name> (--node-id <id>|--psm <psm>) --role <i18n-role> [--sites i18n-tt,us-ttp,eu-ttp] [--yes]` — grant role(s) to a group. i18n role suffixes auto-map per region (`*.i18n` -> US `*.tx`, EU bare role); `--keep-role` disables mapping.
- `bytedcli --site <site> iam user-group revoke --group <name> --node-id <id> --role <role> [--yes]` — revoke (group admins are exempt from the resource-owner check).
- `bytedcli iam user-group member add --group <name> --users <a,b> [--admin] [--sites ...] [--yes]` — add members (default) or admins.
- `bytedcli --site <site> [-j] iam user-group check --group <name> --psm <psm>` — read back a group's role bindings on a node.

Write commands run a hard precheck: the operator must be an **admin of the target custom group** (member_type=2) — resource-owner role is not required. Every site target is prechecked before any write, then each mutation is read back and verified. Non-interactive callers pass `--yes`; `-j` emits structured results.

## Command groups

| Area               | Commands                                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------------------------ |
| Custom user group  | `user-group list`, `user-group member list/add`, `user-group grant`, `user-group revoke`, `user-group check` |
| Resource           | `resource owner list`, `resource role list`                                                                  |
| Permission         | `permission check`, `permission history list`, `permission request submit`                                   |
| Binding            | `permission binding create`, `permission binding delete`                                                     |
| Policy             | `policy list`, `policy get`, `policy exception submit`                                                       |
| Principal          | `user get`                                                                                                   |
| bytedcli host-only | `get-employee`, `permission apply`                                                                           |

For pure Companion entries, older shortcut names map to the new command paths:

- old `permission apply` is `permission request submit`
- old `permission grant` is `permission binding create`
- old `permission revoke` is `permission binding delete`
- old `policy exception apply` is `policy exception submit`

In `bytedcli`, `iam permission apply` still exists as a host-owned compatibility command. Prefer Companion commands for new IAM diagnostics and structured workflows; use host `permission apply` only when you explicitly need its legacy ticket contract or `--check-only` behavior.

## References

- [iam.md](./references/iam.md)
- [invocation.md](./../../invocation.md)
- [troubleshooting.md](./../../troubleshooting.md)
