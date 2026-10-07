# Cloud Control API（cloudcontrol）服务说明

## 适用场景

`ve cloudcontrol` 是统一的资源型控制面，通过 JSON Schema 描述数百种火山资源。优先使用已经明确覆盖任务的产品命令；以下情况再用 Cloud Control：

- 资源类型没有独立的 `ve <service>` 命令；
- 需要 schema 驱动、类似 IaC 的工作流；
- 需要用同一套接口管理多种资源。

主要 Action：

- `ListResourceTypes`：列出支持的资源类型；
- `DescribeResourceType`：获取 Draft-7 JSON Schema；
- `ListResources` / `GetResource`：查询资源；
- `CreateResource` / `UpdateResource` / `DeleteResource`：变更资源；
- `GetTask` / `ListTasks`：跟踪异步任务。

TypeName 格式为 `Volcengine::<Service>::<Resource>`，例如 `Volcengine::IAM::User`。

## 命令形态

`ListResourceTypes`、`DescribeResourceType` 只使用展开参数。其余 Action 同时支持展开参数和 `--body`；属性、Filter、Patch 等嵌套结构优先使用 JSON body。

```bash
ve cloudcontrol ListResourceTypes --MaxResults 100
ve cloudcontrol DescribeResourceType --TypeName "Volcengine::IAM::User"
ve cloudcontrol ListResources --TypeName "Volcengine::IAM::User" --MaxResults 50
ve cloudcontrol GetResource --TypeName "Volcengine::IAM::User" --Identifier "demo-user"
```

## Schema-first：创建和更新前必须执行

Cloud Control 严格按资源 Schema 校验。每次创建或更新前先运行 `DescribeResourceType`，检查：

- `required`：创建必填字段；
- `createOnlyProperties`：只能在创建时设置；
- `readOnlyProperties`：只能读取，不能发送；
- `writeOnlyProperties`：可写但不会回读，例如密码；
- `primaryIdentifier`：Get/Update/Delete 使用的 Identifier 组成；
- `filterProperties`：List 可用和必需的过滤字段；
- `handlers.<operation>.permissions`：底层产品权限。

缺少必填业务值时询问用户，禁止编造。

### Create

属性必须放在 `TargetState`，不能展开到顶层：

```bash
ve cloudcontrol CreateResource --body '{
  "TypeName": "Volcengine::IAM::User",
  "ClientToken": "demo-create-user-001",
  "TargetState": {
    "UserName": "demo-user",
    "Description": "created by demo workflow"
  }
}'
```

每个逻辑操作只生成一次 `ClientToken`；同一操作重试必须复用，生成新 Token 会破坏幂等并可能创建重复资源。

### Update

`PatchDocument` 使用 RFC 6902 JSON Patch，不能修改 create-only/read-only 字段：

```bash
ve cloudcontrol UpdateResource --body '{
  "TypeName": "Volcengine::IAM::User",
  "Identifier": "demo-user",
  "PatchDocument": [
    {"op":"replace","path":"/Description","value":"updated by demo workflow"}
  ]
}'
```

支持 `add`、`remove`、`replace`、`move`、`copy`、`test`。`add/replace/test` 需要 `value`，`move/copy` 需要 `from`。create-only 属性只能重建资源或使用产品专属更新接口。

### Delete

```bash
ve cloudcontrol DeleteResource --body '{
  "TypeName": "Volcengine::IAM::User",
  "Identifier": "demo-user",
  "ClientToken": "demo-delete-user-001"
}'
```

删除是破坏性操作，必须展示影响并获得明确确认；批量删除要明确确认目标集合。

## ListResources 的两个陷阱

### 父资源 Filter

子资源通常不能跨账号直接列出。Schema 的 `filterProperties.required` 会声明必需父级，例如 CLB Rule 需要 ListenerId、CR Repository 需要 Registry：

```bash
ve cloudcontrol ListResources --body '{
  "TypeName": "Volcengine::CLB::Rule",
  "MaxResults": 50,
  "Filter": {"ListenerId":"listener-<id>"}
}'
```

### 分页

`ListResources` 和 `ListResourceTypes` 都会返回 `NextToken`。必须逐页读取到 Token 为空；任何一页失败都要停止，不能把失败或第一页无结果当成资源不存在。

```python
import json, subprocess

type_name = "Volcengine::ECS::Image"
next_token = ""
items = []
while True:
    body = {"TypeName": type_name, "MaxResults": 50}
    if next_token:
        body["NextToken"] = next_token
    result = subprocess.run(
        ["ve", "cloudcontrol", "ListResources", "--body", json.dumps(body)],
        capture_output=True,
        text=True,
        check=True,
    )
    page = json.loads(result.stdout, strict=False)["Result"]
    items.extend(page.get("ResourceDescriptions", []))
    next_token = page.get("NextToken", "") or ""
    if not next_token:
        break
print(len(items))
```

## Identifier

Get/Update/Delete 必须原样使用 List/Get/Create/GetTask 返回的 `Identifier`。复合主键的序列化由服务端定义，禁止自行拼接或重排。

## 异步任务

Create/Update/Delete 会返回 `OperationStatus`，异步操作还返回 `TaskID`：

- `SUCCESS`：已完成，不要再查 GetTask；
- `FAILED`：报告错误并停止；
- `IN_PROGRESS` 或其他非终态：按 `TaskID` 轮询。

```bash
ve cloudcontrol GetTask --TaskId <task-id>
```

注意响应字段是 `TaskID`，参数是 `--TaskId`。只把 `SUCCESS`、`FAILED` 当终态；缺少或未知状态时停止并报告。轮询必须有总时限。Create 只有拿到 Identifier 后才能报告成功；Delete 成功结果可能没有 ResourceModel。

## 权限

调用者同时需要 Cloud Control 权限和底层产品权限。仅有 `CloudControlFullAccess` 不代表能够操作目标资源；以 Schema 的 `handlers.<operation>.permissions` 为准。

- `CloudControlFullAccess`：Cloud Control 管理权限；
- `CloudControlReadOnlyAccess`：Cloud Control 只读权限。

官方权限说明：https://www.volcengine.com/docs/86682/1850846

## 资源类型发现

只有完整翻完 `ListResourceTypes` 的所有分页后，才能判断某个 TypeName 不存在。NextToken 可能很长，响应字符串也可能含控制字符，使用支持宽松字符串解析的真实 JSON parser，并检查每次命令退出码。

## 易错点

- TypeName 大小写和分段必须与接口返回完全一致。
- Schema 是当前事实来源，创建/更新校验失败时重新读取。
- Region 可省略以使用 profile 默认值；显式 `--region` 会改变本次地域。
- 区域资源不能跨地域看到；IAM User 等全局资源可能例外。
- Cloud Control 未覆盖的类型回退到产品专属 `ve <service>`。
- 复杂资源要先创建并等待依赖资源就绪。

官方资源类型列表：https://www.volcengine.com/docs/86682/1850848
