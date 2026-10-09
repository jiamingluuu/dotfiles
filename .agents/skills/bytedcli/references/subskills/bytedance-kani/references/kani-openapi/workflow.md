# Kani OpenAPI: Workflow

在以下场景读取本文件：

- 你要查询、预览、提交或操作 workflow
- 你在“先理解对象，再 dry-run，再提交”的链路里，需要把对象信息转换成 workflow 参数
- 你在区分 `workflow create` / `workflow get` / `workflow list` / `workflow approve|reject|cancel` 的语义

## 推荐顺序

对于一般 Kani 申请路径，可以先按这个顺序理解：

1. 先确认对象和动作
   - `resource get`
   - `permission get`
2. 再做申请前预览
   - `workflow create --dry-run`
3. 确认 work order / approver / node 后，再真正提交
   - `workflow create`
4. 申请人后续查看或撤回时，再查询 / 操作
   - `workflow get`
   - `workflow list --role applicant`
   - `workflow cancel`
5. 审批人需要判断时，再查询 / 决策
   - `workflow get`
   - `workflow list --role reviewer`
   - `workflow approve|reject`
## 审批人判断前建议

如果你是 reviewer，要决定 approve / reject，通常先补齐这几类信息：

1. 当前审批单到底在批什么
   - 用 `workflow get` 看 `WorkOrders`、`PermissionItems` / `RoleItems` / `GroupItems`
   - 重点看对象 `namespace/key`、动作、`SecurityLevel`、申请原因、当前 `Nodes`
2. 这单现在走到谁、后面还会经过谁
   - `workflow get` 可以看到当前 node、assignees、operators
   - 这有助于判断自己是不是当前应该拍板的人，以及后续是否还有 owner / authority owner / cross-region approver
3. 以前有没有类似记录可参考
   - 用 `workflow list --role reviewer --status finished` 看自己最近批过的相似单
   - 需要按对象查变更历史时，可以再用 `write-log list` 看相关 resource / role / group 的写操作记录
4. 拒绝时最好给出可执行的理由
   - 比如对象不对、action 不合理、reason 不充分、缺少业务背景、时长过长
   - 这样申请人更容易按你的反馈重提

## `workflow create`

用途：创建或预览 Kani workflow。它适合“我已经知道要申请哪个对象和动作，现在要先 dry-run 看审批链，确认后再提交”的场景。

鉴权语义：

- 按当前后端实现，它仍是 namespace 级 ACL
- 也就是更接近“应用 / namespace 管理权限接口”，不是完全无门槛的申请入口

参数说明：

- `--region <region>`：可选
- `--body-file <path>`：必填，JSON 文件路径
- `--dry-run`：可选；把 request body 里的 `DryRun` 置为 `true`，只预览 work order 和 approver，不真正提交
- `--metadata`：可选，文本模式显示 metadata
- `--jwt-token <token>` / `--auth-token <token>`：可选

命令示例：

```bash
bytedcli kani openapi workflow create --region cn --body-file ./workflow-create-resource.json
bytedcli kani openapi workflow create --region cn --body-file ./workflow-create-resource.json --dry-run
bytedcli kani openapi workflow create --region cn --body-file ./workflow-create-role.json
bytedcli kani openapi workflow create --region cn --body-file ./workflow-create-group.json
bytedcli kani openapi workflow create \
  --region i18n-bd \
  --body-file ./workflow-create-role.json \
  --auth-token "$AUTH_TOKEN"
```

`--body-file` 顶层结构说明：

- `Applicant`：必填，申请人用户名
- `Reason`：必填，申请原因
- `PermissionItems` / `RoleItems` / `GroupItems`：至少传一种
- `DryRun`：可选；显式传 `true` 时预览 workflow，不真正提交。CLI 也可以直接用 `--dry-run` 注入这个字段
- 建议一次 body 只表达一种申请类型，避免把资源、角色、组混在同一个请求里

### 申请 resource permission

字段说明：

- `PermissionItems[].Namespace`：必填
- `PermissionItems[].ResourceKey`：必填
- `PermissionItems[].ActionKey`：必填，permission action key
- `PermissionItems[].IdentityNamespace`：必填，身份命名空间
- `PermissionItems[].IdentityID`：必填，身份 ID

示例：

```json
{
  "Applicant": "alice",
  "Reason": "Need read access for troubleshooting",
  "PermissionItems": [
    {
      "Namespace": "kani_demo",
      "ResourceKey": "demo_resource",
      "ActionKey": "read",
      "IdentityNamespace": "tce",
      "IdentityID": "alice"
    }
  ]
}
```

### 申请 role

字段说明：

- `RoleItems[].Namespace`：必填
- `RoleItems[].RoleKey`：必填

示例：

```json
{
  "Applicant": "alice",
  "Reason": "Need role for release operation",
  "RoleItems": [
    {
      "Namespace": "kani_demo",
      "RoleKey": "demo_role"
    }
  ]
}
```

### 申请 group

字段说明：

- `GroupItems[].Namespace`：必填
- `GroupItems[].GroupKey`：必填

示例：

```json
{
  "Applicant": "alice",
  "Reason": "Need group membership for collaboration",
  "GroupItems": [
    {
      "Namespace": "kani_demo",
      "GroupKey": "demo_group"
    }
  ]
}
```

## `workflow get`

用途：查询 workflow 详情和 work order 明细。它是查看 `approve|reject|cancel` 目标 `workorder-id` 的主要入口。

参数说明：

- `--region <region>`：可选
- `--workflow-id <id>`：必填
- `--namespace <namespace>`：必填
- `--applicant <user>`：必填
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi workflow get \
  --workflow-id wf_demo \
  --namespace kani_demo \
  --applicant alice
```

审批人通常会从这个接口确认：

- `WorkOrders[].ID`：后续 approve / reject / cancel 要用的 `workorder-id`
- `Status` / `Nodes`：当前卡在哪个审批节点，谁是 assignee / operator
- `PermissionItems` / `RoleItems` / `GroupItems`：申请人具体要拿什么权限
- `SecurityLevel` / `Reason`：安全级别和申请理由是否匹配

## 使用说明

- `workflow create` 继续只保留 `--body-file` 模式，但现在推荐优先加 `--dry-run`
- `workflow get` 用于按 `workflow-id + namespace + applicant` 查询详情
- `workflow list` 用于列出现有 workflow；申请人通常配 `--role applicant`，审批人通常配 `--role reviewer`
- `workflow cancel` 更偏申请人撤回自己的申请
- `workflow approve|reject` 更偏审批人对具体 work order 做决策
- 历史隐藏兼容路径仍可用，但不作为对外推荐入口，也不在本页展开参数与示例

## `workflow list`

用途：列出现有 workflow，公开参数收敛为更接近 OpenAPI list 的模式；底层仍复用 approval/workflow 查询语义，但按 workflow region 做多地域路由。

参数说明：

- `--region <region>`：可选，兼容 `cn|boe|i18n-tt|sg|row|row-tt|va|i18n-bd|row-bd|row-nonTT|bd|non-tt-mya|eu-ttp|ttp|us|us-ttp|tx`
- `workflow list` 会按 workflow region 归一化路由到对应 Kani workflow 后端；未传 `--region` 时默认跟随全局 `--site`
- `--role <role>`：可选，`applicant|reviewer`
- `--applicant <user>` / `--reviewer <user>`：可选
- `--status <status>`：可选；不传时默认查当前/running，查已完成可用 `--status finished`
- `--namespace <namespace>` / `--security-level <level>`：可选
- `--created-at <startISO,endISO>`：可选
- `--page <n>` / `--page-size <n>`：可选；在 running 场景下默认查询 `urgent=false` 的稳定 bucket
- 历史参数仍保留隐藏兼容，但不再作为对外推荐用法
- 查询到 workflow 后，通常还需要再用 `workflow get` 看 work order 详情；申请人再决定是否 cancel，审批人再决定是否 approve/reject

示例：

```bash
bytedcli kani openapi workflow list
bytedcli kani openapi workflow list --role reviewer
bytedcli kani openapi workflow list --status finished
bytedcli kani openapi workflow list --namespace kani_demo --page 2 --page-size 50
bytedcli kani openapi workflow list --role reviewer --status finished --namespace kani_demo
```

申请人常见用法：

- 看自己最近提交过的单：`workflow list --role applicant --applicant <user>`
- 看自己已经结束的历史申请：`workflow list --role applicant --status finished --applicant <user>`

审批人常见用法：

- 看当前待处理的单：`workflow list --role reviewer`
- 看自己最近批过的相似单：`workflow list --role reviewer --status finished --namespace <ns>`
- 如果想缩小到同类高风险对象，可以再加 `--security-level <level>`

## `workflow approve`

用途：审批某个 work order。

参数说明：

- `--region <region>`：可选
- `--workorder-id <id>`：必填
- `--comment <text>`：可选；如果传，至少 5 个字符
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi workflow approve --region cn --workorder-id wo_demo
bytedcli kani openapi workflow approve \
  --region cn \
  --workorder-id wo_demo \
  --comment "审批通过，允许上线使用"
```

说明：

- OpenAPI action 接口按 `workorder-id` 操作，不是按 `workflow-id`
- 现实里 workflow 和 work order 常常接近 1:1，但 CLI 仍按底层模型显式要求 `workorder-id`
- 可以先用 `workflow get` 查看 `WorkOrders[].ID`
- 审批前建议至少先看一次 `workflow get`；如果判断依赖历史相似案例，再配合 `workflow list --role reviewer --status finished`

## `workflow reject`

用途：驳回某个 work order。

参数说明：

- `--region <region>`：可选
- `--workorder-id <id>`：必填
- `--comment <text>`：建议填写；如果传，至少 5 个字符

示例：

```bash
bytedcli kani openapi workflow reject \
  --region cn \
  --workorder-id wo_demo \
  --comment "Missing business context"
```

建议拒绝前先确认：

- 申请对象和 action 是否真的不合理，而不是申请人填错了 key
- `Reason` 是否足够支撑这次申请
- 自己过去在类似 namespace / security level 下是否有可参考的已完成单
- `--comment` 尽量写成申请人可执行的修改建议，而不只是简短否定

## `workflow cancel`

用途：取消某个已提交的 work order，通常用于申请人自己停止当前申请。

参数说明：

- `--region <region>`：可选
- `--workorder-id <id>`：必填
- `--comment <text>`：可选；如果传，至少 5 个字符

示例：

```bash
bytedcli kani openapi workflow cancel \
  --region cn \
  --workorder-id wo_demo \
  --comment "Superseded by a new request"
```

说明：

- `cancel` 更偏申请人或发起方自助停止，不是 reviewer 的主要决策动作
- 如果你是 reviewer，通常优先考虑 `approve` 或 `reject`
