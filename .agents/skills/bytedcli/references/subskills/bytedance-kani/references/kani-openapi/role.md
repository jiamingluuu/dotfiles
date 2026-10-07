# Kani OpenAPI: Role

在以下场景读取本文件：

- 你需要读取单个 role，或查看 member 与 role 的关联关系
- 你在解释“某个人为什么有某个 role / 什么时候失效”
- 你要为 role 相关申请或排障补上下文

## `role get`

用途：读取单个 role。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--role-key <key>`：必填
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi role get --namespace kani_demo --role-key demo-role
```

## `member related-role list`

用途：列出某个 member 关联到的 role。

鉴权语义：

- 查自己时会直接放行
- 查别人时，后端会按目标 member 做额外 ACL

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--member-type <type>`：必填，支持 `user`、`department`、`group`、`department-name`
- `--member-key <key>`：必填
- `--member-namespace <namespace>`：可选
- `--return-authorized-end-time <boolean>`：可选
- `--return-join-time <boolean>`：可选
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi member related-role list \
  --namespace kani_demo \
  --member-type user \
  --member-key alice
```

## `member related-role inactive-list`

用途：列出某个 member 已失效的 role 关系。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--member-type <type>`：必填，支持 `user`、`department`、`group`、`department-name`
- `--member-key <key>`：必填
- `--member-namespace <namespace>`：可选
- `--start-authorized-end-time <ts>`：可选，毫秒时间戳
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi member related-role inactive-list \
  --namespace kani_demo \
  --member-type user \
  --member-key alice \
  --start-authorized-end-time 1735689600000
```
