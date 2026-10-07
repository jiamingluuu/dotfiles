# VNet Quota

`bytedcli vnet quota get` 通过 VNet 原生 Quota API 查询一个账号在多个地域的当前用量和上限。命令复用 VNet Session 与 NightHawk 签名，不需要 Ego、Playwright 或 CDP。

## 命令

```bash
bytedcli --json --site cn vnet quota get \
  --account-id 2000000000 \
  --regions cn-beijing,cn-guangzhou,cn-shanghai \
  --service-code vpc \
  --quota-codes shuttle,shuttle/shuttle_client,shuttle/shuttle_server,shuttle_client,shuttle_server

bytedcli --json --site i18n-tt vnet quota get \
  --account-id 2000000000 \
  --regions ap-southeast-1,ap-southeast-3,cn-hongkong \
  --service-code vpc \
  --quota-codes shuttle,shuttle/shuttle_client,shuttle/shuttle_server,shuttle_client,shuttle_server
```

所有查询参数均为必填；站点使用 bytedcli 全局 `--site`，默认 `cn`：

| 参数             | 说明                                                                        |
| ---------------- | --------------------------------------------------------------------------- |
| `--account-id`   | 正整数形式的 VNet 账号 ID；按字符串发送，不做数值转换                       |
| `--regions`      | 逗号分隔的地域列表；一次请求查询全部地域                                    |
| `--service-code` | VNet service code，例如 `vpc`                                               |
| `--quota-codes`  | 逗号分隔的 quota code；支持 `shuttle/shuttle_client` 这类带 `/` 的层级 code |
| 全局 `--site`    | `cn`、`boe` 或 `i18n-tt`；分别映射 VNet `cn`、`sdv`、`sg`，默认 `cn`         |

列表参数会去除首尾空格和重复值。空成员、非法站点或非法 code 会在本地返回 `VNET_QUOTA_INPUT_ERROR`。

## JSON 输出

命令使用 bytedcli 标准 envelope。`data` 中的稳定字段包括：

- `account_id`、`instance_id`、`service_code`
- `requested_regions`、`missing_regions`、`quota_codes`
- `region_count`、`item_count`
- `regions`：每个地域的 quota map，Quota 值保留已确认的 `count`、`total`、`type`、`serviceCode`、`quotaCode`、`description` 和 `region` 字段
- `items`：按地域和请求的 quota code 展平，每条包含 `region`、`service_code`、`quota_code`、`available`、`count`、`total`

服务端未返回某个请求指标时，该条 `items` 仍保留，值为 `available: false`、`count: null`、`total: null`；不要把缺失数据当作零使用。服务端返回空地域数组时命令成功，`regions` 和 `items` 均为空。

## 认证与站点

先为目标站点准备 SSO Session：

```bash
# CN
bytedcli auth login --session

# SDV / BOE
bytedcli --site boe auth login --session

# SG
bytedcli --site i18n-tt auth login --session
```

Quota 命令会自动兑换并复用对应的 `_vnet-session`。持久化 Session 失效时会清理对应站点的缓存、重新兑换并最多重试一次；显式设置的 `BYTEDCLI_VNET_COOKIE` 被拒绝时，需要更新该变量或 unset 后改用自动 SSO 兑换。`sg` 的 API host 由 VNet 站点配置决定，不根据页面域名推导。

## 能力边界

该命令只提供原子查询能力。warning/critical 阈值、多账号或多批次巡检、报告、飞书写入、定时调度和扩容建议由调用方实现。
