# Kani OpenAPI: Namespace

在以下场景读取本文件：

- 你需要先看某个 namespace 的详情，或继续枚举它下面的 role / resource / group
- 你已经从 `identity namespace list` 拿到了可访问 namespace，准备做下一层查询
- 你在给用户生成 namespace 级巡检、资产盘点或申请前置检查

## `namespace get`

用途：读取 namespace 详情。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi namespace get --namespace kani_demo
```

## `namespace role list`

用途：列出 namespace 下的 role。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--page <n>`：可选，1-based 页码
- `--page-size <n>`：可选，每页条数；未传时默认按 20 计算
- `--keyword <keyword>`：可选，按关键字搜索
- `--custom-tags <tags>`：可选，逗号分隔标签
- `--inactive-statuses <values>`：可选，逗号分隔 inactive status
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi namespace role list --namespace kani_demo
bytedcli kani openapi namespace role list --namespace kani_demo --keyword developer
```

## `namespace resource list`

用途：列出 namespace 下的 resource。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--page <n>`：可选，1-based 页码
- `--page-size <n>`：可选，每页条数；未传时默认按 20 计算
- `--action-keys <keys>`：可选，逗号分隔 action key 列表
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi namespace resource list --namespace kani_demo
```

说明：

- 返回中的空字符串 `ResourceKey` 已在 CLI 侧过滤掉，不再展示无意义的空 key

## `namespace group list`

用途：列出 namespace 下的 group。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--page <n>`：可选，1-based 页码
- `--page-size <n>`：可选，每页条数；未传时默认按 20 计算
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi namespace group list --namespace kani_demo
```
