# 应用账号 AK/SK 认证（非交互式 / CI）

bytedcli 支持把应用账号 AK/SK 按控制面交给 ByteCloud Auth SDK 管理。SDK 自动获取、缓存和刷新短期 JWT；无需为每次日志查询手工换取 JWT。`BYTEDCLI_USER_CLOUD_JWT` 仍保留为一次性 JWT 注入方式。

## 前置条件

使用服务账号查询日志前，需完成以下三步：

### 1. 创建服务账号

在字节云 IAM 控制台创建服务账号：

- CN：https://cloud.bytedance.net/iam/acls/account/list?listTab=1
- 其他控制面需在对应控制面创建

参考：[使用服务账号获取 JWT](https://cloud.bytedance.net/docs/bytecloud/docs/63c4c6df7e9d2a021ec21002/6588f1ea670f3002f535c8f9)

### 2. 绑定非个人 Project

服务账号需要绑定到一个非个人 project 才能使用。在 Argos 项目设置中将服务账号添加为成员。

### 3. 申请日志 OpenAPI 接口权限

服务账号查询日志时使用日志 OpenAPI 相关接口进行鉴权，需申请以下接口权限：

- **关键字滚动查询**：[申请链接](https://cloud.bytedance.net/open/explorer/api-explorer?data=%7B%7D&groupName=Uncategorized&query=%7B%7D&serviceCode=streamlog&uniqueId=e59afa491eb63381c6a75813516ab30e0a539a46&version=v1&x-bc-region-id=bytedance&x-resource-account=public)
- **关键字检索**：[申请链接](https://cloud.bytedance.net/open/explorer/api-explorer?data=%7B%7D&groupName=%E6%97%A5%E5%BF%97%E6%9F%A5%E8%AF%A2%E7%9B%B8%E5%85%B3&query=%7B%7D&serviceCode=streamlog&uniqueId=1ab15c1207d2c1fa166a2db1823392e84c775406&version=v1&x-bc-region-id=bytedance&x-resource-account=public)
- **LogID 日志检索**：[申请链接](https://cloud.bytedance.net/open/explorer/api-explorer?data=%7B%7D&groupName=Uncategorized&query=%7B%7D&serviceCode=streamlog&uniqueId=edf75aa88e6610a5f8ef812a4ce4fd0a0d4b5392&version=v1&x-bc-region-id=bytedance&x-resource-account=public)

此外，对于开启日志访问鉴权的 PSM，还需要服务账号有对应 PSM 的日志访问权限，参考：[PSM 开启访问控制后 Argos 日志查询指导](https://cloud.bytedance.net/docs/argos/docs/63a91dd0caaad3021d130a84/64a3e96c7e5972021dd3969b)

## 推荐：配置应用账号 AK/SK

AK 和 SK 必须属于同一个应用账号及控制面。SK 不支持命令行参数，避免进入 shell history。

```bash
# 交互终端：随后出现隐藏 SK 输入
bytedcli --site i18n-tt auth app set \
  --access-key-id sample-ak

# CI / 非交互：从 stdin 读取 SK
printf %s "$BYTECLOUD_APP_SK" | \
  bytedcli --site i18n-tt auth app set \
    --access-key-id sample-ak

# 也可从权限为 0600 的文件读取
bytedcli --site i18n-bd auth app set \
  --access-key-id sample-ak \
  --secret-file ./sample-app.sk

# 检查配置并强制刷新一次短期 JWT；输出不会包含 JWT/SK
bytedcli --site i18n-tt --json auth app status --refresh

# 仅删除当前 site 的本地应用账号 AK/SK
bytedcli --site i18n-tt auth app clear --yes
```

业务命令按目标 host/site 自动选择对应凭据。显式 `BYTEDCLI_USER_CLOUD_JWT` 或 ByteCloud JWT override 的优先级更高，可用于临时覆盖；当前 site 已配置应用账号时，业务请求优先使用 app JWT，再回退到个人 session JWT。

日志 SDK 路径下，服务账号还需显式设置其非个人 Argos project：

```bash
export BYTEDCLI_ARGOS_PROJECT=sample-argos-project
bytedcli --site i18n-tt log search-psm-log \
  --psm example.service.api \
  --vregion Singapore-Central \
  --keyword error \
  --max-logs 100 \
  --output console
```

## 受管环境注入服务账号 JWT

受管 Agent / Workflow 环境可以直接注入已经签发的服务账号 JWT。日志 SDK 路径优先读取当前站点的变量，再读取通用变量：

```bash
export BYTEDCLI_SERVICE_ACCOUNT_JWT_CN='<cn-jwt>'
export BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_TT='<i18n-tt-jwt>'
export BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_BD='<i18n-bd-jwt>'
export BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP='<us-ttp-jwt>'
export BYTEDCLI_SERVICE_ACCOUNT_JWT_EU_TTP='<eu-ttp-jwt>'
export BYTEDCLI_SERVICE_ACCOUNT_JWT='<generic-jwt>'
export BYTEDCLI_ARGOS_PROJECT=sample-argos-project
```

`us-ttp`、`us-ttp-bdee`、`us-ttp-usts` 共享 `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP`，不要创建 alias 专属变量。设置 `ARGOS_SERVER_URL` 自定义 Agent Center 地址时，bytedcli 不会向该地址发送受管服务账号 JWT。

## Fallback：注入一次性用户 JWT

临时联调时，也可以直接注入已经签发的一次性用户 ByteCloud JWT；长期任务仍应使用 `auth app set`，由 SDK 自动刷新。

```bash
export BYTEDCLI_USER_CLOUD_JWT='<bytecloud-jwt>'
```

> 不同控制面的应用账号 AK/SK 相互独立，需在对应控制面分别创建和配置。

## 支持的命令

以下 `bytedcli log` 子命令均支持服务账号 JWT 认证：

| 命令                           | 说明                        |
| ------------------------------ | --------------------------- |
| `log search-psm-log`           | 按 PSM / 关键词搜索日志     |
| `log get-logid-log`            | 按 LogID 查询日志           |
| `log search-prod-instance-log` | 生产实例日志搜索            |
| `log get-lane-instance-log`    | 泳道实例日志搜索            |
| `log get-log-cluster`          | 日志聚类                    |
| `log trace-tree`               | LogID 调用树（BytedTrace）  |
| `log analysis performance`     | 接口总体性能分析            |
| `log footprint get`            | Footprint TCE Sync pod 日志 |
| `log footprint download`       | Footprint 日志 URL 下载     |

## 一次性 JWT 完整用法示例

```bash
# 1. 获取服务账号 JWT
export BYTEDCLI_USER_CLOUD_JWT=$(curl -sD - -o /dev/null \
  https://cloud.bytedance.net/auth/api/v1/jwt \
  -H "Authorization: Bearer $SA_SECRET" \
  | grep -i 'x-jwt-token' | cut -d' ' -f2 | tr -d '\r\n')

# 2. 正常使用 log 命令（自动使用注入的 JWT）
bytedcli log search-psm-log --psm "example.service.api" \
  --start "2026-07-14T10:00:00" --end "2026-07-14T11:00:00" \
  --max-logs 100 --output console

# LogID 查询同样支持
bytedcli log get-logid-log "20260714100000ABCDEF1234567890" --output console
```

## 注意事项

- 服务账号只能查询其有权限访问的 PSM 日志，无权限时后端返回 `101403 AccessForbidden`。
- SDK 管理的短期 JWT 过期时会使用已保存的长期凭据自动刷新；手工注入的 JWT 过期后仍需重新获取。
- 服务账号凭据按 ByteCloud Auth site 存储。不同控制面分别配置；`us-ttp-bdee` / `us-ttp-usts` 复用 `us-ttp` 凭据分区。
- `log` 的部分 legacy microservice 接口只接受 `person_account`。默认 Log SDK 路径用于支持服务账号；不要设置 `ARGOS_SDK=0` 强制回退 legacy 路径。
- `BYTEDCLI_USER_CLOUD_JWT` 对所有 bytedcli 命令生效，不仅限于 log。
- 同时支持 `AIME_USER_CLOUD_JWT` 作为备选环境变量名（兼容 AIME 平台注入）。
