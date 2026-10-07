# Kani OpenAPI: Workflow

在以下场景读取本文件：

- 你要查询或创建 workflow
- 你在“先查再申请”的链路里，需要把对象信息转换成 workflow 创建或查询参数
- 你在区分 `workflow create` / `workflow get` / `workflow list` 三条命令的语义

## `workflow create`

用途：提交 Kani workflow。当前 `workflow create` / `workflow get` / `workflow list` 都可直接使用，其中 `create` 是写操作入口。

鉴权语义：

- 按当前后端实现，它仍是 namespace 级 ACL
- 也就是更接近“应用 / namespace 管理权限接口”，不是完全无门槛的申请入口

参数说明：

- `--region <region>`：可选
- `--body-file <path>`：必填，JSON 文件路径
- `--metadata`：可选，文本模式显示 metadata
- `--jwt-token <token>` / `--auth-token <token>`：可选

命令示例：

```bash
bytedcli kani openapi workflow create --region cn --body-file ./workflow-create-resource.json
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

用途：查询 workflow 详情。

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

## 使用说明

- `workflow create` 继续只保留 `--body-file` 模式
- `workflow get` 用于按 `workflow-id + namespace + applicant` 查询详情
- `workflow list` 用于列出现有 workflow
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

示例：

```bash
bytedcli kani openapi workflow list
bytedcli kani openapi workflow list --role reviewer
bytedcli kani openapi workflow list --status finished
bytedcli kani openapi workflow list --namespace kani_demo --page 2 --page-size 50
```
