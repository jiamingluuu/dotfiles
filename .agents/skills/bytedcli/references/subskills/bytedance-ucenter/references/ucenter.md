# UCenter 只读查询参考

## 账号详情

```bash
bytedcli --json ucenter account get \
  --app-id 123 \
  --uid demo-uid \
  --section base
```

`--section` 接受逗号分隔值：

| 值               | 内容                                                       |
| ---------------- | ---------------------------------------------------------- |
| `base`           | 账号基本信息；默认值，也是其他栏目的查询前提               |
| `bindings`       | 当前绑定和绑定历史                                         |
| `devices`        | 注册设备、常用/最近/当前登录、登录设备、亲密设备和登录历史 |
| `lifecycle`      | 注销记录、锁定记录和删除历史                               |
| `operations`     | 账号操作历史                                               |
| `authorizations` | 当前授权和授权历史                                         |
| `all`            | 上述全部栏目；必须单独使用                                 |

即使仅传 `--section devices`，结果仍包含 `base`。没有被显式选择的栏目不会发起请求。

若 `base` 没有匹配请求 UID，JSON 返回 `base_not_found: true`，并在 `skipped_sections` 中列出没有继续查询的显式栏目。该状态表示账号主体不存在或响应主体不匹配，不会伪装成权限缺失。

## 操作日志

账号日志：

```bash
bytedcli --json ucenter account-log list \
  --app-id 123 \
  --uid demo-uid \
  --did demo-did \
  --start '24h ago' \
  --page 1 \
  --page-size 20
```

资料日志：

```bash
bytedcli --json ucenter profile-log list \
  --app-id 123 \
  --uid demo-uid \
  --start '24h ago' \
  --page 1 \
  --page-size 20
```

- `--uid`、`--did` 至少提供一项；两项并存时为 AND。
- 默认时间窗口为最近 24 小时，默认 `--page 1 --page-size 20`。
- 账号日志单次最大跨度 3 个月、最大 1000 条。
- 资料日志单次最大跨度 6 个月、最大 10000 条。
- 后端没有游标分页；CLI 通过扩大同一主体查询窗口并在本地切页，因此 `page × page-size` 不能超过上述最大条数。
- UID/DID 已传给上游，CLI 仍会对每条结果做防御性主体校验。分页边界按上游原始顺序计算，再过滤错主体记录；因此异常响应可能产生稀疏页。`current_count` 是本页最终返回数，`truncated` 表示原始抓取已达到 `page × page-size` 边界，而不是本页过滤后一定满页。
- 不支持原始表达式或无主体的全 App 扫描。

## 资料基本信息

```bash
bytedcli --json ucenter profile get \
  --app-id 123 \
  --uid demo-uid
```

资料查询正常展示 screen name、description 和 avatar 等资料字段；手机号、邮箱、第三方账号、IP、Session Key 和日志参数等敏感字段仍默认脱敏。

## 权限与部分成功

- 账号基础查询权限缺失：命令失败，错误提供 `permission`、`operation`、`app_id` 和申请入口。
- 账号基础信息已获权但没有匹配 UID：命令返回 `base_not_found: true`；显式细分栏目列入 `skipped_sections`，不写入 `missing_permissions`。
- 账号细分 operation 缺失：命令成功返回已获权栏目，并在 `missing_permissions` 中逐项列出跳过内容。
- 资料查询权限缺失：命令失败并提供申请入口。
- `--show-sensitive` 明文权限缺失：整条命令在数据查询前失败。
- 已获权 endpoint 请求失败、超时或响应异常：命令失败，不把错误降级为空结果。

申请入口只用于提醒用户自行申请。不要自动提交权限申请，也不要改用写接口或其他 endpoint 绕过。

## 输出与敏感信息

- 推荐全局 `--json`，例如 `bytedcli --json ucenter ...`。
- JSON 结果仅包含规范化字段，不包含上游 envelope、JWT、Cookie 或原始响应。
- UID、DID 作为查询主键保留；其他明确敏感字段显示为 `[REDACTED]`。
- 仅当用户明确要求且已获明文权限时添加 `--show-sensitive`。
- 不把查询结果、UID、DID、明文字段或权限响应写入文件，除非用户明确指定安全的输出目标。

## 站点与认证

- 当前固定支持 CN；不要为此命令生成其他 `--site`。
- 命令使用当前调用者的用户态 ByteCloud 登录身份，不使用服务账号扩大权限。
- 认证失败时先运行 `bytedcli --json auth status` 检查 CN 登录状态；需要登录时由用户完成 `bytedcli --site cn auth login`。
