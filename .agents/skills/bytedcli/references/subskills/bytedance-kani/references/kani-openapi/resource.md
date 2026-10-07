# Kani OpenAPI: Resource

在以下场景读取本文件：

- 你已经知道目标 `resource`，需要读取详情、权限定义或相关成员
- 你在排查“某个资源谁有权限、谁是管理员、资源下有哪些 action”
- 你正在为后续 `workflow create` 收集资源侧上下文

## `permission get`

用途：读取某个资源下的权限定义。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填，资源所属 namespace
- `--resource-key <key>`：必填
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi permission get --namespace kani_demo --resource-key demo-resource
```

## `resource get`

用途：读取单个 resource。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--resource-key <key>`：必填
- `--need-descendant-resources <boolean>`：可选，是否同时返回下级资源
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi resource get --namespace kani_demo --resource-key demo-resource
```

## `resource related-member list`

用途：查看与某个 resource 相关的成员。

鉴权语义：

- 这是当前命令面里最明确的“资源管理员入口”之一
- 后端会按目标 `resource` 做对象级 ACL；namespace 管理员也可以通过

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--resource-key <key>`：必填
- `--action-keys <keys>`：可选，逗号分隔 action key 列表
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi resource related-member list \
  --namespace kani_demo \
  --resource-key demo-resource
```
