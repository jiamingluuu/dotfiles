# Kani OpenAPI

Kani OpenAPI 这组命令面向“先理解对象，再预览申请，再分别处理申请人与审批人动作”的使用路径。当前命令面已经覆盖：

- 对象理解：`resource get`、`permission get`
- 申请预览 / 提交：`workflow create`
- 申请人查询 / 撤回：`workflow get`、`workflow list --role applicant`、`workflow cancel`
- 审批人查询 / 决策：`workflow get`、`workflow list --role reviewer`、`workflow approve`、`workflow reject`

## 通用约定

- `--region` 支持：`cn`、`boe`、`i18n-tt|sg|row|row-tt|va`、`i18n-bd|row-bd|row-nonTT|bd|non-tt-mya`、`eu-ttp|ttp`、`us|us-ttp|tx`
- 默认认证：自动获取所选 region 的个人态 `X-JWT-Token`
- 如果没显式传 `--region`，CLI 会按全局 `--site` 推导默认 region：
  - `cn -> cn`
  - `boe -> boe`
  - `i18n-tt -> sg`
  - `i18n` / `i18n-bd -> row-nonTT`
  - `eu-ttp -> eu-ttp`
  - `us-ttp* -> us-ttp`
  - 其他情况仍回落到 `cn`
- `us`、`sg`、`eu-ttp`、`us-ttp` 的关系如下：
  - `us` 和 `us-ttp` 当前对应同一套 US-TTP OpenAPI / JWT 站点；如果你要显式访问 US-TTP，也可以直接传 `--region us-ttp`
  - `sg` 是 i18n-tt / row-tt 体系 region，兼容别名包括 `row`、`row-tt`、`va`
  - `eu-ttp` 指 EU-TTP OpenAPI：`https://kani-v2-api.tiktoke.org/v1`
  - `us-ttp` 指 US-TTP OpenAPI：`https://kani-v2-openapi.tiktokd.net/v1`
- `ttp` 现在只作为保守兼容别名，默认按 `eu-ttp` 解释
- `tx` 是 `us-ttp` 的兼容别名
- 显式 override：
  - `--jwt-token <token>`：覆盖个人态 `X-JWT-Token`
  - `--auth-token <token>`：覆盖服务态 `X-Auth-Token`
- `--metadata`：在文本模式额外展示 OpenAPI envelope metadata
- `-j, --json`：输出原始结构化结果，便于脚本消费
- 需要显式布尔值的参数统一传 `true` 或 `false`，例如 `--need-hierarchy true`
- 逗号分隔参数直接传单个字符串，例如 `--resource-keys keyA,keyB`

## OpenAPI 鉴权语义

这部分说明的是“我们当前接入的 OpenAPI 接口，在后端实现里的鉴权粒度”。CLI 本身只负责把 `X-JWT-Token` / `X-Auth-Token` 带过去，真正的允许/拒绝由后端决定。唯一例外是 `write-log list`：文档先按当前对外约定写，后端会再按这个规则收敛实现。

通用规则：

- 所有接口都要求 caller 已认证；也就是至少要有可用的个人态 `X-JWT-Token` 或服务态 `X-Auth-Token`
- “应用管理员 / namespace 管理员”在这里可以理解为：后端按 namespace wildcard resource 做 `admin` 校验，也就是 namespace 级 ACL
- 有些接口不是单纯的 namespace 级 ACL，而是会按“目标 identity”或“目标 resource/group/role 对象”做更细粒度的管理员校验
- 下表基于当前后端实现观察值整理；如果后端后续改 ACL，这里的分类也需要同步更新

按当前实现可以先这样理解：

- `任何已认证 caller 都可以用`
  - `authz check`
  - `authz path`
  - 这两个接口在 OpenAPI wrapper 里跳过了额外 ACL，不要求你先是应用管理员、资源管理员或角色管理员
- `只能查自己`
  - `identity namespace list`
  - 用户 JWT 只能查 `IdentityNamespace=user` 且 `IdentityKey=当前登录用户`
  - 服务 token 只能查 `IdentityNamespace=tce` 且 `IdentityKey=当前服务 PSM`
- `自己总能查自己；查别人需要额外管理员权限`
  - `identity permission list`
  - `member related-role list`
  - 查自己时，后端会直接放行；查别人时，后端会按目标 identity / member 再做 ACL
- `资源 / 角色 / Group 管理员可查对应对象`
  - `resource related-member list`
- `通常按应用 / namespace 管理权限理解`
  - `permission get`
  - `role get`
  - `group get`
  - `resource get`
  - `namespace get`
  - `namespace role list`
  - `namespace resource list`
  - `namespace group list`
  - `identity permission inactive-list`
  - `member related-role inactive-list`
  - `workflow create`
  - `workflow get`
  - `write-log list` 在“只传 Object，不传 Identity”时先按这一类理解

几个容易误解的点：

- `workflow create` 不是“只要想申请就一定能调”的无门槛接口。按当前后端实现，它仍然挂在 namespace 级 ACL 下
- `write-log list` 这里先按对外约定写，不再机械复述当前后端老逻辑；实现会再向文档规则收敛
- `identity permission list` 和 `member related-role list` 不是简单的“只有应用管理员可查”或“只有本人可查”二选一；更准确的理解是“本人自查放行，查别人要看后端是否认定你是目标对象的管理员”

## 推荐顺序

```bash
# 1) 先看当前 identity 能访问哪些 namespace
bytedcli kani openapi identity namespace list --identity-key alice

# 2) 再看某个 namespace 下的角色 / 资源 / 组
bytedcli kani openapi namespace role list --namespace kani_demo
bytedcli kani openapi namespace resource list --namespace kani_demo
bytedcli kani openapi namespace group list --namespace kani_demo

# 3) 继续看 identity 在 namespace 下已有的权限
bytedcli kani openapi identity permission list \
  --namespace kani_demo \
  --identity-type user \
  --identity-key alice

# 4) 需要解释权限链路时，用 path / check
bytedcli kani openapi authz path \
  --namespace kani_demo \
  --identity-type user \
  --identity-key alice \
  --object-type resource \
  --object-key demo-resource \
  --action-key read

# 5) 先用 workflow create --dry-run 预览审批链
bytedcli kani openapi workflow create --body-file ./workflow-create-resource.json --dry-run

# 6) 确认 work order / approver / nodes 后，再真正提交
bytedcli kani openapi workflow create --body-file ./workflow-create-resource.json

# 7a) 申请人查看自己提交过的 workflow，或继续跟进某条申请
bytedcli kani openapi workflow get --workflow-id wf_demo --namespace kani_demo --applicant alice
bytedcli kani openapi workflow list --role applicant --status finished --namespace kani_demo --applicant alice

# 7b) 审批人处理前，先用 workflow get / workflow list 补齐上下文
bytedcli kani openapi workflow get --workflow-id wf_demo --namespace kani_demo --applicant alice
bytedcli kani openapi workflow list --role reviewer --status finished --namespace kani_demo

# 8) 申请人需要撤回时用 cancel；审批人需要决策时用 approve / reject
bytedcli kani openapi workflow cancel --workorder-id wo_demo --comment "需求变更，撤回本次申请"
bytedcli kani openapi workflow approve --workorder-id wo_demo --comment "审批通过，允许上线使用"
```

## 模块路由

按模块读取，避免把所有 OpenAPI 命令一次性灌进上下文：

| 模块 | 何时阅读 | Reference |
| --- | --- | --- |
| resource | 查 resource、permission、resource 相关成员 | [resource.md](kani-openapi/resource.md) |
| namespace | 查 namespace 详情，枚举 namespace 下 role/resource/group | [namespace.md](kani-openapi/namespace.md) |
| role | 查单个 role，或查 member 与 role 的关联/失效关系 | [role.md](kani-openapi/role.md) |
| group | 查单个 group | [group.md](kani-openapi/group.md) |
| workflow | 预览/创建 workflow，查询 work order，并执行 approve/reject/cancel | [workflow.md](kani-openapi/workflow.md) |
| write-log | 查写操作审计日志 | [write-log.md](kani-openapi/write-log.md) |

## 保留在总览中的命令

以下几类命令具有明显的“跨模块入口”特征，因此仍保留在总览页：

- `authz check`
- `authz path`
- `identity namespace list`
- `identity permission list`
- `identity permission inactive-list`

## `authz check`

用途：用一份 JSON request body 做授权校验。

鉴权语义：

- 任何已认证 caller 都可以调用
- 这个接口不会额外要求你先具备应用管理员、资源管理员或角色管理员权限

参数说明：

- `--region <region>`：可选；未传时按全局 `--site` 推导，兜底为 `cn`
- `--body-file <path>`：必填，JSON 文件路径
- `--metadata`：可选，文本模式显示 metadata
- `--jwt-token <token>` / `--auth-token <token>`：可选，显式覆盖鉴权 header

命令示例：

```bash
bytedcli kani openapi authz check --region cn --body-file ./check.json
bytedcli --json kani openapi authz check --region boe --body-file ./check.json
bytedcli kani openapi authz check \
  --region i18n-tt \
  --body-file ./check.json \
  --jwt-token "$JWT_TOKEN"
```

`check.json` 结构说明：

- `Namespace`：必填，资源所属 namespace
- `ResourceKey`：必填，资源 key
- `ActionKey`：必填，要校验的 action key
- `Identity`：必填，发起校验的 identity
- `Identity.IdentityType`：必填，常见值是 `user`
- `Identity.IdentityKey`：必填，identity key
- `Identity.IdentityNamespace`：可选，通常填 `user`

示例：

```json
{
  "Namespace": "kani_demo",
  "ResourceKey": "demo_resource",
  "ActionKey": "read",
  "Identity": {
    "IdentityType": "user",
    "IdentityKey": "alice",
    "IdentityNamespace": "user"
  }
}
```

## `authz path`

用途：查看 identity 到对象之间的授权链路。

鉴权语义：

- 任何已认证 caller 都可以调用
- 这个接口不会额外要求你先具备应用管理员、资源管理员或角色管理员权限

参数说明：

- `--region <region>`：可选；未传时按全局 `--site` 推导，兜底为 `cn`
- `--namespace <namespace>`：必填，identity 所在业务 namespace
- `--identity-type <type>`：必填，常见值 `user`
- `--identity-key <key>`：必填
- `--identity-namespace <namespace>`：可选，默认 `user`
- `--object-type <type>`：必填，常见值 `resource`
- `--object-key <key>`：必填
- `--object-namespace <namespace>`：可选，默认复用 `--namespace`
- `--action-key <key>`：可选，按 action 过滤
- `--enable-abac <boolean>`：可选，是否启用 ABAC 计算
- `--metadata`、`--jwt-token`、`--auth-token`：同上

示例：

```bash
bytedcli kani openapi authz path \
  --namespace kani_demo \
  --identity-type user \
  --identity-key alice \
  --object-type resource \
  --object-key demo-resource \
  --action-key read
```

## `identity namespace list`

用途：查看某个 identity 相关的 namespace。这个命令通常是第一步入口。

鉴权语义：

- 只能自查
- 用户 JWT 只能查当前登录用户自己
- 服务 token 只能查当前服务自己

参数说明：

- `--region <region>`：可选
- `--identity-key <key>`：必填
- `--identity-namespace <namespace>`：可选，默认 `user`
- `--filter <filters>`：可选，逗号分隔，支持 `namespace_admin`、`any_permission`
- `--page <n>`：可选，1-based 页码
- `--page-size <n>`：可选，每页条数；未传时默认按 20 计算
- `--metadata`、`--jwt-token`、`--auth-token`：同上

示例：

```bash
bytedcli kani openapi identity namespace list --identity-key alice
bytedcli kani openapi identity namespace list --identity-key alice --filter any_permission
```

## `identity permission list`

用途：列出 identity 在某个 namespace 下当前生效的权限。

鉴权语义：

- 查自己时会直接放行
- 查别人时，后端会按目标 identity 做额外 ACL，不要把它简单理解成“所有人都能查”或“只有应用管理员能查”

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--identity-type <type>`：必填，常见值 `user`
- `--identity-key <key>`：必填
- `--identity-namespace <namespace>`：可选
- `--resource-keys <keys>`：可选，逗号分隔资源 key 列表
- `--return-authorized-end-time <boolean>`：可选，返回权限到期时间
- `--need-admin-permission <boolean>`：可选，包含 admin 权限
- `--only-direct-permission <boolean>`：可选，只看直接授权
- `--need-hierarchy <boolean>`：可选，包含继承链路
- `--metadata`、`--jwt-token`、`--auth-token`：同上

示例：

```bash
bytedcli kani openapi identity permission list \
  --namespace kani_demo \
  --identity-type user \
  --identity-key alice
```

## `identity permission inactive-list`

用途：列出已经失效的 identity 权限。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--identity-type <type>`：必填
- `--identity-key <key>`：必填
- `--identity-namespace <namespace>`：可选
- `--start-authorized-end-time <ts>`：可选，毫秒时间戳，按失效时间起点过滤
- `--metadata`、`--jwt-token`、`--auth-token`：同上

示例：

```bash
bytedcli kani openapi identity permission inactive-list \
  --namespace kani_demo \
  --identity-type user \
  --identity-key alice \
  --start-authorized-end-time 1735689600000
```
