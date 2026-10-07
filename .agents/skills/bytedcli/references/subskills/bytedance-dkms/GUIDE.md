---
name: bytedance-dkms
description: "Operate DKMS (Data Key Management Service) via bytedcli: get data key info and list, check, or add permissions across BOE, BOE-I18N, CN, TikTok ROW, non-TikTok ROW, and EU-TTP regions. Use when tasks mention DKMS, data keys, encryption key permissions, or TikTok data encryption."
---

# bytedcli DKMS (Data Key Management Service)

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

- 数据密钥查询（`get-key`）
- 密钥权限列表（`list-permissions`）
- 权限检查（`check-permission`）
- 权限添加（`add-permission`）
- 数据密钥加密（`encrypt`）
- 数据密钥解密（`decrypt`）
- BOE、BOE-I18N、CN、TikTok ROW、non-TikTok ROW 或 EU-TTP 区域的数据加密密钥管理

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- `--region` 同时决定 DKMS API 域名与 JWT 认证分区；不需要用全局 `--site` 手工匹配 region。
- 先复用目标认证分区的现有登录态；只有 `auth status` 返回 `need_login` 时才执行对应站点的 `auth login`。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 获取密钥信息；默认 region 为 rowtt
bytedcli dkms get-key demo-data-key

# 查询 CN 密钥
bytedcli dkms get-key demo-data-key --region cn

# 列出 non-TikTok ROW 密钥权限
bytedcli dkms list-permissions demo-data-key --region rownontt

# 检查 EU-TTP 服务的数据面 read 权限
bytedcli dkms check-permission demo-data-key --entity-name demo.service.psm --entity-type service --permission-type read --region euttp

# 添加 BOE-I18N 服务的数据面 read 权限
bytedcli dkms add-permission demo-data-key --entity-name demo.service.psm --entity-type service --permission-type read --region boei18n

# 添加 TikTok ROW 员工的控制面 all 权限
bytedcli dkms add-permission demo-data-key --entity-name demo.user --entity-type employee --permission-type all --region rowtt

# 使用 DKMS 数据面加密文本
bytedcli dkms encrypt demo-data-key --input "demo-plaintext" --region boei18n

# 使用 DKMS 数据面解密文本
bytedcli dkms decrypt demo-data-key --input "demo-ciphertext" --region boei18n

# 从 UTF-8 文件读取输入；--input 与 --input-file 必须二选一
bytedcli --json dkms encrypt demo-data-key --input-file ./demo-plaintext.txt --region boei18n
```

## 权限语义

- `--permission-type read`：数据面权限，控制是否可通过 SDK、UDF 或数据面接口获取和使用密钥。适用于 `employee` 和 `service`。
- `--permission-type all`：控制面查看权限，仅适用于 `employee`；service 只能添加 `read`。
- key owner 隐式拥有 `all`，可以查看并编辑控制面权限；owner 不会自动拥有 `read`，如需数据面访问仍要单独添加。
- 非 owner 的 employee 获得显式 `all` 后可以查看控制面权限，但不能编辑。
- `add-permission` 和 `check-permission` 默认 `--permission-type read`。
- `check-permission` 的结果会区分 `permissionSource=owner|explicit`，并返回 `canViewControlPlane`、`canEditControlPlane`、`canReadDataPlane`。权限不存在时命令仍成功返回 `hasPermission=false`。
- `--entity-type` 只接受 `employee|service`；`--permission-type` 只接受 `all|read`。
- service 传 `--permission-type all` 时，CLI 会在发送请求前返回 `DKMS_INPUT_ERROR`；改用 `--permission-type read`。
- 密钥名可使用位置参数或 `--data-key-name`；两者同时提供时 `--data-key-name` 优先。
- `encrypt` / `decrypt` 调用 DKMS 数据面 `/api/v1/online_crypto`，请求使用 `DataKeyName`、`EncryptDecrypt` 和 `Message` 字段。
- 加解密输入必须且只能提供 `--input <text>` 或 `--input-file <path>`；文件按 UTF-8 读取并保留换行。
- text 模式只输出 `CryptoResult`；JSON 模式输出 data key、operation、region、output 和 request id，不回显输入。
- DKMS 数据面使用 Security Platform JWT（`bs-token`），与 DKMS 控制面查询/权限接口的 ByteCloud `x-jwt-token` 认证不同。

## 区域路由

| `--region` | API 域名 | JWT CloudSite |
|---|---|---|
| `boe` | `dkms-boe.byted.org` | `boe` |
| `boei18n` | `dkms-boei18n.byted.org` | `boe` + `vregion=boei18n` |
| `cn` | `dkms-cn.byted.org` | `cn` |
| `rowtt` | `dkms-sg.tiktok-row.org` | `i18n-tt` |
| `rownontt` | `dkms-row-mya.sinf.net` | `i18n-bd` |
| `euttp` | `dkms-euttp.tiktok-eu.org` | `eu-ttp` |

## Notes

- canonical region：`boe`, `boei18n`, `cn`, `rowtt`, `rownontt`, `euttp`。
- 默认 region：`rowtt`。
- 兼容旧值：`va` / `sg` 映射到 `rowtt`，`eu` 映射到 `euttp`，`boe-i18n` 映射到 `boei18n`。
- 未知 region 会返回 `DKMS_UNSUPPORTED_REGION`，不会静默访问默认区域。
- 需要结构化输出加 `--json`（全局选项，放在子命令之前）。

## References

- `references/dkms.md`
