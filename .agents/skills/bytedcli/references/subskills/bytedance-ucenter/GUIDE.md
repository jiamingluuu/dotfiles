---
name: bytedance-ucenter
description: "Use bytedcli for ByteCloud UCenter read-only account and profile queries. Trigger when the user asks to query a UID's account basics, bindings, registration/login devices, cancellation or locking history, account operations, authorizations, account operation logs, profile basics, profile operation logs, or UCenter query permissions. Keep this workflow strictly read-only and require UID or DID scope for every log query."
---

# bytedcli UCenter

使用 `bytedcli ucenter` 查询用户中台 UCenter。该能力只暴露经过白名单约束的查询接口；不要构造绑定、解绑、修改、锁定、注销、恢复、撤销授权或权限申请等写请求。

## 路由

| 用户意图                    | 命令                       |
| --------------------------- | -------------------------- |
| 按 UID 查询账号信息         | `ucenter account get`      |
| 按 UID/DID 查询账号操作日志 | `ucenter account-log list` |
| 按 UID 查询资料基本信息     | `ucenter profile get`      |
| 按 UID/DID 查询资料操作日志 | `ucenter profile-log list` |

完整参数、栏目、权限和脱敏约束见 [UCenter 查询参考](references/ucenter.md)。

## 执行约束

1. 每次查询都要求用户明确给出 `--app-id`；不要猜测、缓存或复用其他 App ID。
2. 账号详情默认只查 `base`。只有用户明确要求时才追加 `--section bindings|devices|lifecycle|operations|authorizations|all`。
3. 日志查询至少带 `--uid` 或 `--did`。两者都有时同时传入，语义是 AND；不得通过省略两者执行全 App 扫描。
4. 默认使用全局 `--json`，便于读取稳定字段和 `missing_permissions`。
5. 默认脱敏。只有用户明确要求查看明文时才使用 `--show-sensitive`；命令会先校验明文权限，失败后停止，不得绕过。
6. 缺少基础账号权限或资料权限时，向用户展示错误中的 permission、operation、app_id 和申请链接。仅缺账号细分权限时保留已查询结果，并逐项展示 `missing_permissions`。
7. 权限申请只打开或转交命令返回的链接；不要代替用户提交申请，也不要寻找写接口绕过权限。
8. 当前只支持 CN。其他 site 返回不支持时停止，不要改 host、region 或资源账号重试。

## 快速示例

```bash
bytedcli --json ucenter account get \
  --app-id 123 \
  --uid demo-uid

bytedcli --json ucenter account get \
  --app-id 123 \
  --uid demo-uid \
  --section bindings,devices

bytedcli --json ucenter account-log list \
  --app-id 123 \
  --uid demo-uid \
  --start '24h ago'

bytedcli --json ucenter profile get \
  --app-id 123 \
  --uid demo-uid

bytedcli --json ucenter profile-log list \
  --app-id 123 \
  --did demo-did
```

## 进一步参考

- 全局参数或 JSON 调用方式不确定时读取 [UCenter 调用方式](references/ucenter-invocation.md)。
- 遇到版本、认证、权限或网络问题时读取 [UCenter 排障](references/ucenter-troubleshooting.md)。
