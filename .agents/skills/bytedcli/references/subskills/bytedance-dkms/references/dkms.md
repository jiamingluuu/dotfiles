# DKMS (Data Key Management Service)

```bash
# 获取密钥信息；默认 region 为 rowtt
bytedcli dkms get-key <dataKeyName>

# BOE
bytedcli dkms get-key <dataKeyName> --region boe

# BOE-I18N
bytedcli dkms get-key <dataKeyName> --region boei18n

# CN
bytedcli dkms get-key <dataKeyName> --region cn

# TikTok ROW
bytedcli dkms get-key <dataKeyName> --region rowtt

# non-TikTok ROW
bytedcli dkms get-key <dataKeyName> --region rownontt

# EU-TTP
bytedcli dkms get-key <dataKeyName> --region euttp

# 列出密钥权限
bytedcli dkms list-permissions <dataKeyName> --region rowtt

# 检查数据面 read 权限
bytedcli dkms check-permission <dataKeyName> --entity-name <serviceOrEmployee> --entity-type <service|employee> --permission-type read --region rowtt

# 检查员工控制面 all 权限
bytedcli dkms check-permission <dataKeyName> --entity-name <username> --entity-type employee --permission-type all --region rowtt

# 添加服务 read 权限
bytedcli dkms add-permission <dataKeyName> --entity-name <serviceName> --entity-type service --permission-type read --region rowtt

# 添加员工 all 权限
bytedcli dkms add-permission <dataKeyName> --entity-name <username> --entity-type employee --permission-type all --region rowtt

# 数据面加解密
bytedcli dkms encrypt demo-data-key --input "demo-plaintext" --region boei18n
bytedcli dkms decrypt demo-data-key --input "demo-ciphertext" --region boei18n
bytedcli dkms encrypt demo-data-key --input-file ./demo-plaintext.txt --region boei18n
bytedcli --json dkms decrypt demo-data-key --input-file ./demo-ciphertext.txt --region boei18n
```

## 权限类型

| `--permission-type` | 含义 | 支持实体 |
|---|---|---|
| `read` | 数据面获取和使用密钥 | `employee`, `service` |
| `all` | 控制面查看权限 | `employee` |

- 默认值为 `read`。
- key owner 隐式拥有 `all`，并且只有 owner 能编辑控制面权限；owner 不会自动拥有 `read`。
- 非 owner employee 的显式 `all` 只能查看控制面权限，不能编辑。
- service 只能添加 `read`；如果传 `all`，CLI 会在发送请求前返回 `DKMS_INPUT_ERROR`，并提示改用 `--permission-type read`。
- `check-permission` 返回 `permissionSource`、`isOwner`、`canViewControlPlane`、`canEditControlPlane`、`canReadDataPlane`；无权限时返回 `hasPermission=false`，不是命令错误。
- `--entity-type` 仅接受 `employee|service`。
- 密钥名可以使用位置参数 `<dataKeyName>` 或 `--data-key-name <name>`；两者同时提供时 `--data-key-name` 优先。
- `encrypt` / `decrypt` 的 key name 同样支持位置参数和 `--data-key-name`，且后者优先。
- `--input` 与 `--input-file` 必须二选一；同时提供或都不提供返回 `DKMS_INPUT_ERROR`。
- `encrypt` 请求 `EncryptDecrypt=encrypt`，`decrypt` 请求 `EncryptDecrypt=decrypt`，结果来自 `Result.CryptoResult`。
- text 模式只输出结果字符串；JSON 模式不包含输入内容。

## 区域、域名与认证

| `--region` | API 域名 | JWT CloudSite |
|---|---|---|
| `boe` | `dkms-boe.byted.org` | `boe` |
| `boei18n` | `dkms-boei18n.byted.org` | `boe` + `vregion=boei18n` |
| `cn` | `dkms-cn.byted.org` | `cn` |
| `rowtt` | `dkms-sg.tiktok-row.org` | `i18n-tt` |
| `rownontt` | `dkms-row-mya.sinf.net` | `i18n-bd` |
| `euttp` | `dkms-euttp.tiktok-eu.org` | `eu-ttp` |

`--region` 会同时选择 API 域名和 JWT 分区，不需要额外传入匹配的全局 `--site`。

数据面加解密使用 Security Platform `bs-token`；控制面查询与权限接口继续使用 ByteCloud JWT `x-jwt-token`。

## 兼容别名

- `va`, `sg`, `us`, `us-east`, `virginia`, `singapore` → `rowtt`
- `eu`, `eu-ttp`, `europe`, `gcp` → `euttp`
- `boe-i18n` → `boei18n`

默认 region 为 `rowtt`。未知值会返回 `DKMS_UNSUPPORTED_REGION`。

## 实体类型

- `service`：服务标识（如 `demo.service.name`）
- `employee`：员工用户名（如 `demo.user`）
