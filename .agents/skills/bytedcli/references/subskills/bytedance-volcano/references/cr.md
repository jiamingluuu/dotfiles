# CR 服务说明

## Namespace 与 Repository 需要 Registry

`ListNamespaces` 缺少 `Registry` 时会返回：

```text
MissingParameter.Registry: The required parameter Registry is missing.
```

Registry 不存在时会返回 `NotFound.Registry`。先用 `ListRegistries` 或 `CreateRegistry` 的输出获得真实 Registry，再查询或创建 Namespace/Repository。

## 写接口使用 JSON body

CR 创建接口使用 `--body`，不要混用展开参数。

## Docker 认证

VKE 没有使用 `cr-credential-controller` 免密拉取时，通过短期授权 Token 登录 Docker：

```bash
token_json=$(ve cr GetAuthorizationToken --Registry "$registry_name")
cr_username=$(printf '%s' "$token_json" | jq -r '.Result.Username // empty')
cr_password=$(printf '%s' "$token_json" | jq -r '.Result.AuthorizationToken // empty')
[ -n "$cr_username" ] || { echo "CR response missing Result.Username" >&2; exit 1; }
[ -n "$cr_password" ] || { echo "CR response missing Result.AuthorizationToken" >&2; exit 1; }
printf '%s' "$cr_password" | docker login "$registry_endpoint" \
  --username "$cr_username" \
  --password-stdin
```

- 不得打印或保存 `AuthorizationToken`。
- Token 是临时凭证，长时间后 push/pull 失败应重新申请。
- 响应缺少 Username 时停止并检查原始响应，不得猜默认用户名。
- VKE 私有镜像优先使用 `cr-credential-controller`，否则显式配置 `imagePullSecret`。
