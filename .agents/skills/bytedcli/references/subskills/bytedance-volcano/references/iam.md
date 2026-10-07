# IAM 服务说明

## UpdateUser 不支持 Tags

`UpdateUser` 只能修改 Description、DisplayName 等基础属性。用户或角色标签必须单独使用 `TagResources`：

```bash
ve iam TagResources \
  --ResourceType User \
  --ResourceNames.1 <user-name> \
  --Tags.1.Key demo-key \
  --Tags.1.Value demo-value
```

角色使用 `ResourceType=Role`。

## 临时用户标签测试

只有在用户明确批准后才创建专用临时用户，并在同一次流程中删除。`CreateUser` 可设置初始标签，之后用 `TagResources` 添加、`UntagResources` 删除。

```bash
user_name="demo-cli-user"
ve iam CreateUser --UserName "$user_name" --Description demo-user
ve iam TagResources --ResourceType User --ResourceNames.1 "$user_name" \
  --Tags.1.Key purpose --Tags.1.Value demo
ve iam GetUser --UserName "$user_name"
ve iam UntagResources --ResourceType User --ResourceNames.1 "$user_name" --TagKeys.1 purpose
ve iam DeleteUser --UserName "$user_name"
```

删除后 `GetUser` 应返回 `UserNotExist`，以此作为清理证据。
