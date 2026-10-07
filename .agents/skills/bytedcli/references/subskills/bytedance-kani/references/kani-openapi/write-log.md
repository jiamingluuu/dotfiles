# Kani OpenAPI: Write Log

在以下场景读取本文件：

- 你要查询 Kani 写操作审计日志
- 你在排查某个 identity、resource、role、group 最近发生了哪些写请求
- 你需要理解 `write-log list` 的鉴权边界和默认搜索行为

## `write-log list`

用途：查询 Kani 写操作审计日志。

鉴权语义：

- 只传 `Object`，不传 `Identity`
  - 继续走原来的 admin 鉴权路径，保持旧行为
- 传了完整 `Identity`，但没传 `Object`
  - 只允许 JWT 证明这个 identity 就是调用者自己
- 同时传了 `Identity` 和 `Object`
  - 命中以下任一条件即可放行：
  - JWT self
  - Namespace Admin
  - Object Admin

这里的“完整 `Identity`”可以理解为：至少把 `--identity-namespace` 和 `--identity-key` 都明确传上。

参数说明：

- `--region <region>`：可选
- `--identity-namespace <namespace>`：可选，principal namespace
- `--identity-key <key>`：可选，principal key
- `--object-namespace <namespace>`：可选，对象所属 namespace
- `--object-type <type>`：可选，支持 `resource`、`group`、`role`、`app`
- `--object-key <key>`：可选
- `--time-range <range>`：可选，支持 `1h`、`1d`、`3d`、`7d`、`30d`、`365d`
- `--page <n>`：可选，1-based 页码
- `--page-size <n>`：可选，每页条数；未传时默认按 20 计算
- `--reason-include <text>`：可选，只保留 reason 包含该文本的记录
- `--reason-exclude <text>`：可选，排除 reason 包含该文本的记录
- `--return-raw-records <boolean>`：可选，同时返回 old/new record 原始内容
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

默认行为：

```bash
bytedcli kani openapi write-log list
```

额外示例：

```bash
bytedcli kani openapi write-log list \
  --identity-namespace user \
  --identity-key alice \
  --time-range 7d
bytedcli kani openapi write-log list \
  --object-namespace kani_demo \
  --object-type resource \
  --object-key demo-resource \
  --time-range 7d
```

说明：

- 默认搜索“当前登录 identity”近 `30d` 的 write log
- 如果显式传了 `--identity-key` / `--identity-namespace`，则以显式值为准
- `--object-namespace`、`--object-type`、`--object-key`、`--reason-include` 等参数都是附加过滤条件
