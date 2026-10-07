# KMS v2 (Key Management Service v2)

```bash
# 获取密钥环信息（ROW TikTok 区域）
bytedcli kmsv2 get-keyring <keyring> --region rowtt

# 获取密钥环信息（CN 区域）
bytedcli kmsv2 get-keyring <keyring> --region cn

# 获取密钥环信息（BOE 区域）
bytedcli kmsv2 get-keyring <keyring> --region boe


# 获取密钥环信息（BOE-I18N 区域）
bytedcli kmsv2 get-keyring <keyring> --region boei18n

# 列出客户密钥
bytedcli kmsv2 list-keys <keyring> --region rowtt

# 获取客户密钥详情
bytedcli kmsv2 get-key <keyring> --key-name <keyName> --region rowtt

# 添加服务权限（PSM 自动转换为 SPIFFE）
bytedcli kmsv2 add-permission <keyring> --key-name <keyName> --services <psm1> <psm2> --region rowtt

# 添加用户权限
bytedcli kmsv2 add-permission <keyring> --key-name <keyName> --users <user1> <user2> --region rowtt

# 同时添加服务和用户权限
bytedcli kmsv2 add-permission <keyring> --key-name <keyName> --services <psm1> --users <user1> --region rowtt

# CN 普通密钥：服务权限合并到 Decode 和 Encode
bytedcli kmsv2 add-permission <keyring> --key-name <keyName> --services <psm1> --region cn

# 数据编码与解码
bytedcli kmsv2 encode demo.keyring --key-name demo-key --input "demo-text" --region rowtt
bytedcli kmsv2 decode demo.keyring --key-name demo-key --input "demo-ciphertext" --region rowtt
bytedcli kmsv2 encode demo.keyring --key-name demo-key --input-file ./demo-input.txt --operation EncodeForQuery2 --region rowtt
bytedcli --json kmsv2 decode demo.keyring --key-name demo-key --input-file ./demo-ciphertext.txt --operation V2Decode --region rowtt

# CN secret：服务权限合并到 GetSecret，StoreSecret 等其他 ACL 保持不变
bytedcli kmsv2 add-permission <keyring> --key-name <secretName> --services <psm1> --region cn
```

## 区域与 API 域名对应关系

兼容区域别名：`va` / `sg` → `rowtt`，`eu` → `euttp`。

- BOE：`boe-kmsv2-control.byted.org`
- CN：`prod-cn-kmsv2-control.byted.org`
- ROW TikTok (`rowtt`)：`prod-row-kmsv2-control-og.tiktok-row.org`
- EU-TTP (`euttp`)：`prod-eu-ttp-kmsv2-control.tiktok-eu.org`
- ROW non-TikTok (`rownontt`)：`prod-row-kmsv2-control-nontt.byted.org`
- BOE-I18N：`boei18n-kmsv2-control.byted.org`

## 权限管理说明

- `--services`：服务 PSM 名称，会自动转换为 SPIFFE URI；普通密钥添加到 Decode 和 Encode ACL，secret 同时添加到 GetSecret 和 StoreSecret ACL
- `--users`：用户名，添加到 user_authorization_data
- `--resource-type key|secret`：可选覆盖；默认根据 `purpose` 与 ACL action 自动推断
- `add-permission` 是增量操作，新权限会与现有权限合并
- `encode` 和 `decode` 的 keyring 既支持现有位置参数，也支持 `--keyring` 或兼容的 `--namespace`。
- `--input` 与 `--input-file` 必须二选一，文件按 UTF-8 读取并保留换行；两者同时提供或都不提供都会返回 `KMSV2_INPUT_ERROR`。
- `encode` 默认 operation 为 `V2Encode`，可选 `V2Encode`、`Encode`、`EncodeForQuery2`、`EncodeWithMetadata`。
- `decode` 默认 operation 为 `V2Decode`，可选 `V2Decode`、`Decode`；不能把 encode operation 传给 decode，反之亦然。
- text 模式只打印 output；JSON 模式返回 keyring、keyName、region、operation、output，不包含输入内容。
- `V2Encode` / `V2Decode` 使用 KMS v2 编码格式；`Encode` / `Decode` 为兼容格式；`EncodeForQuery2` 产生适合 query 参数的结果；`EncodeWithMetadata` 产生带编码元数据的结果。
- 输出写入 stdout，便于管道消费；不新增输出文件参数。
- KMS v2 更新接口会全量替换 ACL；CLI 必须先 GET 完整 ACL，保留所有 action 后再写回。普通密钥 payload 使用 `Decode`/`Encode`，secret payload 使用 `GetSecret`/`StoreSecret`。不能把 secret 权限改写到 `Decode`，否则 `GetSecret` 权限会被清空

## SPIFFE URI 格式

服务 PSM 会按区域转换为 SPIFFE URI：
- CN：`spiffe://prod-cn.byted.org/ns:*/r:*/vdc:*/id:<psm>`
- ROW 普通密钥：`spiffe://row.byted.org/ns:*/r:*/vdc:*/id:<psm>`
- ROW secret（rowtt/rownontt）：`spiffe://prod-row.byted.org/ns:*/r:*/vdc:*/id:<psm>`
- EU-TTP secret：`spiffe://prod-eu-ttp.tiktoke.org/ns:*/r:*/vdc:*/id:<psm>`
- BOE：`spiffe://boe.byted.org/ns:*/r:*/vdc:*/id:<psm>`

## ⚠️ 并发安全警告

`add-permission` 命令采用 read-modify-write 模式实现：
1. 读取当前密钥权限
2. 合并新权限
3. 写回更新后的权限

此操作**不是原子的**，存在竞态条件风险。如果多个操作同时执行，可能导致部分权限丢失。

**请勿在以下场景使用**：
- 高频自动化脚本
- 多人同时操作同一密钥
- CI/CD 并行任务
