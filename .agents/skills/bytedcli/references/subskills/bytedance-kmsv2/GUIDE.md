---
name: bytedance-kmsv2
description: "Operate KMS v2 (Key Management Service v2) via bytedcli: manage keyrings, customer keys, secrets, and permissions for CN, TikTok ROW, and BOE-I18N regions. Use when tasks mention KMS v2, keyring, customer key, secret ACL, encryption key ACL, or Security Platform authentication."
---

# bytedcli KMS v2 (Key Management Service v2)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 密钥环查询（get-keyring）
- 客户密钥列表（list-keys）
- 客户密钥详情（get-key）
- 密钥权限管理（add-permission）
- 指定客户密钥的数据编码（encode）与解码（decode）
- CN、BOE、TikTok ROW（rowtt）或 BOE-I18N 区域的 KMS v2 密钥与 secret 权限管理

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要安装 Chrome/Chromium 和 puppeteer（`npm install -g puppeteer-core@24`，走系统 Chrome，不下载 Chromium）
- KMS v2 使用 Security Platform JWT（bs-token）认证，**与 ByteCloud SSO 不同**
- 首次使用会自动打开浏览器，通过 CDP 捕获登录后的 bs-token
- Token 缓存 55 分钟，过期后自动重新触发浏览器登录

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 获取密钥环信息
bytedcli kmsv2 get-keyring demo.privacy.test --region rowtt

# 获取 CN 密钥详情
bytedcli kmsv2 get-key demo.privacy.test --key-name demo-key --region cn

# 获取 BOE secret 详情
bytedcli kmsv2 get-key demo.keyring --key-name demo-secret --region boe

# 列出密钥环下的客户密钥
bytedcli kmsv2 list-keys demo.privacy.test --region rowtt

# 获取客户密钥详情
bytedcli kmsv2 get-key demo.privacy.test --key-name default --region rowtt

# 添加服务权限（通过 PSM）
bytedcli kmsv2 add-permission demo.privacy.test --key-name default --services my.service.psm --region rowtt

# 添加用户权限
bytedcli kmsv2 add-permission demo.privacy.test --key-name default --users demo.user bob --region rowtt

# 同时添加服务和用户权限
bytedcli kmsv2 add-permission demo.privacy.test --key-name default --services svc1 svc2 --users demo.user --region rowtt

# 使用指定客户密钥编码文本（默认 V2Encode）
bytedcli kmsv2 encode demo.keyring --key-name demo-key --input "demo-text" --region rowtt

# 使用指定客户密钥解码文本（默认 V2Decode）
bytedcli kmsv2 decode demo.keyring --key-name demo-key --input "demo-ciphertext" --region rowtt

# 从 UTF-8 文件读取多行输入；--input 与 --input-file 必须二选一
bytedcli --json kmsv2 encode demo.keyring --key-name demo-key --input-file ./demo-input.txt --operation EncodeWithMetadata

# 给 CN 普通密钥增加服务权限：合并到 Decode 和 Encode
bytedcli kmsv2 add-permission demo.privacy.test --key-name demo-key --services demo.reader.service --region cn

# 给 CN secret 增加服务权限：同时合并到 GetSecret 和 StoreSecret
bytedcli kmsv2 add-permission demo.privacy.test --key-name demo-secret --services demo.reader.service --region cn
```

## 区域路由

兼容区域别名：`va` / `sg` → `rowtt`，`eu` → `euttp`。

| 区域 | API 域名 | Security Platform |
|------|----------|-------------------|
| BOE | `boe-kmsv2-control.byted.org` | `security-boe.bytedance.net` |
| CN | `prod-cn-kmsv2-control.byted.org` | `security.bytedance.net` |
| ROW TikTok (`rowtt`) | `prod-row-kmsv2-control-og.tiktok-row.org` | `security.tiktok-row.net` |
| EU-TTP (`euttp`) | `prod-eu-ttp-kmsv2-control.tiktok-eu.org` | `security.bytedance.net` |
| ROW non-TikTok (`rownontt`) | `prod-row-kmsv2-control-nontt.byted.org` | `security.bytedance.net` |
| BOE-I18N | `boei18n-kmsv2-control.byted.org` | `security-boe-i18n.bytedance.net` |

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前）
- `add-permission` 是增量操作，会与现有权限合并，不会覆盖
- `--resource-type key|secret` 为可选覆盖；默认从 GET 返回的 `purpose` 与 ACL action 自动推断资源类型
- `add-permission` 会先读取完整 ACL，再按现有 ACL 类型更新：普通密钥合并到 `Decode`/`Encode`，secret 同时合并到 `GetSecret`/`StoreSecret`，并保留其他 action
- 服务 PSM 会自动转换为 SPIFFE URI 格式
- `encode` / `decode` 只处理 UTF-8 文本，必须且只能提供 `--input <text>` 或 `--input-file <path>`。
- 文本模式只输出编码/解码结果；`--json` 输出包含 keyring、keyName、region、operation 和 output，不回显输入。
- `encode` 支持 `V2Encode`（默认）、`Encode`、`EncodeForQuery2`、`EncodeWithMetadata`；`decode` 支持 `V2Decode`（默认）和 `Decode`。
- `V2Encode` / `V2Decode` 是 KMS v2 格式，`Encode` / `Decode` 用于兼容旧格式；`EncodeForQuery2` 适合需要 query-safe 输出的场景，`EncodeWithMetadata` 用于需要携带编码元数据的场景。具体格式由后端 key 配置决定。
- 编码和解码结果直接写到 stdout，不提供 `--output-file`；不要把明文、密文或 token 写入 shell 历史、日志或错误报告。

> ⚠️ **警告**：`add-permission` 命令采用 read-modify-write 模式，不支持并发安全。请勿在高频场景或多人同时操作时使用，以避免竞态条件导致权限丢失。

## References

- `references/kmsv2.md`
