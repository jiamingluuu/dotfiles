# UCenter 排障

## 命令不存在或版本过旧

先检查更新，再重试原命令：

```bash
bytedcli self update --check
bytedcli self update
```

## CN 认证失败

UCenter 只检查 CN 登录态，不扫描或切换其他站点：

```bash
bytedcli --json auth status
```

仅当状态明确要求登录时执行：

```bash
bytedcli --site cn auth login
```

登录后用原 UCenter 命令重试。不要改 host、region、资源账号或 JWT 来源。

## 缺少查询权限

`UCENTER_PERMISSION_REQUIRED` 会提供 `permission`、`operation`、`app_id` 和 `apply_url`。把这些内容展示给用户，由用户自行打开返回的申请入口并提交申请。

账号细分权限缺失时，命令可能部分成功；检查 `missing_permissions`，不要把被跳过的栏目解释为空数据。不要自动申请权限，也不要使用写接口或其他 endpoint 绕过。

## 网络或响应异常

- 确认当前位于可访问 ByteCloud 的网络环境。
- 保留结构化错误码和 endpoint，避免输出 UID、DID、JWT、Cookie 或原始响应。
- 已获权 endpoint 超时或 schema 异常时直接报告错误，不要降级为空结果。
