---
name: "bytedance-waf"
description: "通过 bytedcli 只读查询 WAF（Web Application Firewall）安全防护规则。用于 WAF/防火墙/应用层防护、CC 防护（CCV2/CCV3/LightCC 轻量 CC）、IP 黑名单、IP 白名单、地理位置封禁、规则 ID、PSM、Host、URL、ClientIP、防护阈值、拦截/放行策略、HotState 查询；支持多站点（cn/boe/i18n-bd/i18n-tt）、PSM/Host 授权范围与 Kani 全局读权限。"
---

# bytedcli WAF

WAF（Web Application Firewall，Web 应用防火墙）是字节内部的应用层安全防护系统。这些命令通过当前用户的 ByteCloud JWT 只读查询 WAF 的防护规则配置，包括 CC 防护规则、IP 黑白名单等安全策略；不接受 operator 覆盖，不支持创建、更新或删除。

## 命令选择

| 用户意图                                 | 命令             |
| ---------------------------------------- | ---------------- |
| 查询 CCV3 防护规则列表、检查 LightCC     | `waf ccv3 list`  |
| 按 ID 查询单条 CCV3 规则                 | `waf ccv3 get`   |
| 查询旧版 CCV2 阈值防护规则列表           | `waf ccv2 list`  |
| 按 ID 查询单条 CCV2 规则                 | `waf ccv2 get`   |
| 查询 IP 黑名单或地理位置访问控制策略列表 | `waf black list` |
| 按 ID 查询单条黑名单规则                 | `waf black get`  |
| 查询 IP 白名单放行策略列表               | `waf white list` |
| 按 ID 查询单条白名单规则                 | `waf white get`  |

LightCC 是 CCV3 中 `HotState` 非普通状态的规则，当前没有单独过滤参数。查询
LightCC 时先读取 CCV3，并在 JSON 结果中检查 `HotState`（0=常态, 1=half hot, 2=hot）。

## 调用要求

- Agent 默认使用全局 `--json`，且必须放在 `waf` 前面。
- 支持 `cn`、`boe`、`i18n-bd`、`i18n-tt`；`i18n` 作为 `i18n-bd`
  的别名。显式 `--site` 使用对应 ConfCenter 和 JWT。
- Kani 全局 read 用户可见全量；其他用户只看到获授权 PSM 或 Host 下的记录。
  空列表表示当前身份没有匹配的可见记录，不等于鉴权失败。
- `get --id <id>` 后端无独立 Get 接口，通过 list + ID 过滤实现；
  CCV3 ID 过滤走服务端，其他资源由 CLI 分页扫描当前身份可见范围并精确匹配。
  未匹配时返回 `WAF_NOT_FOUND`；扫描超过安全上限时要求先用 PSM、Host 或 URL 缩小范围。

## 过滤参数

所有列表支持公共参数：`--id`、`--page`、`--page-size`、`--psm`、
`--host`、`--url`、`--enabled true|false`。`get` 仅需要 `--id`。资源特有参数：

| 资源  | 参数                                                                                                         |
| ----- | ------------------------------------------------------------------------------------------------------------ |
| CCV3  | `--client-ip`、`--cc-type <number>`、`--order id\|url`                                                       |
| CCV2  | `--single-threshold`、`--path-threshold`、`--cc-type <number>`、`--field`、`--policy <number>`、`--group-id` |
| Black | `--client-ip`、`--policy <number>`、`--group-id`、`--rule-type all\|ip\|geo`                                 |
| White | `--client-ip`、`--policy <number>`、`--group-id`                                                             |

枚举语义：

- `--policy`: `1`=拦截并记录全量日志, `2`=不生效, `4`=拦截并记录采样日志,
  `8`=观察并记录全量日志, `16`=观察并记录采样日志；Black 还支持
  `32`=JS 挑战、`64`=JS 挑战配置
- CCV3 `--cc-type`: `0`=告警, `1`=源限速, `2`=阻断, `3`=路径限速,
  `4`=入口限速, `5`=包限速, `6`=JS 挑战, `7`=人机验证, `8`=JS 挑战配置
- CCV2 `--cc-type`: 常用 `1`=源限速, `2`=阻断, `3`=路径限速,
  `4`=入口限速, `5`=包限速
- Black `--rule-type`: `all`=全部, `ip`=IP 黑名单, `geo`=地理位置封禁
- `--enabled`: `false`=禁用, `true`=启用
- `--field`: 统计维度字段，支持 `CLIENTIP`、`PATH`、`FORM`、`JSON`、逗号分隔的区域字段（如 `AREA:PROVINCE`）

CCV3 的 `--order id` 返回独立规则；`--order url` 使用 URL 模糊匹配并按
PSM/Host/URL 分组。其他 URL 查询为精确过滤。

```bash
bytedcli --json --site cn waf ccv3 list --psm example.service
bytedcli --json --site boe waf ccv3 get --id 1001
bytedcli --json --site i18n-bd waf ccv2 list --cc-type 4 --policy 2
bytedcli --json --site i18n-tt waf black list --client-ip 192.0.2.1 --rule-type ip
bytedcli --json --site cn waf white list --page 1 --page-size 20
bytedcli --json waf black get --id 42
```

## 输出说明

- 文本模式：按资源渲染表格，列包含 ID、PSM、Host、URL、ClientIP、阈值、Policy、HotState、Operator、Enable 等。
- JSON 模式：list 返回 `{ items, total, count, page, page_size }`；get 返回单条规则对象（非数组）。

## 失败处理

- 401：先执行 `bytedcli --json --site <site> auth status`；仅当结果确实要求登录时
  执行 `bytedcli --site <site> auth login`。
- 403：不要重试或重复登录。报告目标 site、endpoint 和 403；通常表示
  ConfCenter 未开启 JWT、Kani 调用异常或服务端权限拒绝。
- WAF_NOT_FOUND：get 命令中 ID 未匹配可见规则；验证 ID 与 PSM/Host 授权范围。
- WAF_SCAN_LIMIT_EXCEEDED：当前授权范围过大；增加 `--psm`、`--host` 或 `--url`
  后重试。
- 空列表：视为成功结果，说明当前授权范围或过滤条件没有匹配记录。

## References

- [`../../invocation.md`](../../invocation.md)：全局参数、站点、JSON 和 HTTP 调试
- [`../../troubleshooting.md`](../../troubleshooting.md)：通用认证与站点排障
