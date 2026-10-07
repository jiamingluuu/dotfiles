# Model Dispatcher command reference

## Authentication

```bash
# CN
bytedcli --site cn auth login --session
bytedcli --site cn model-dispatcher auth login
bytedcli --site cn --json model-dispatcher auth status
bytedcli --site cn model-dispatcher auth logout

# US；必须显式使用 ByteDance SSO
bytedcli --site us-ttp --auth-site bytedance auth login --session
bytedcli --site us-ttp model-dispatcher auth login
bytedcli --site us-ttp --json model-dispatcher auth status
bytedcli --site us-ttp model-dispatcher auth logout
```

模型下发控制台使用独立站点 Cookie。ByteCloud Auth ready 不等于模型下发已登录；CLI 从已保存的 BDSSO 会话执行 OAuth 换票，并用用户信息接口验证站内身份。CN 与 US Cookie 分文件保存，不跨控制面复用。

| `--site` | 控制面                               | SSO                          |
| -------- | ------------------------------------ | ---------------------------- |
| `cn`     | `model-dispatcher.bytedance.net`     | ByteDance                    |
| `us-ttp` | `model-dispatcher-us.tiktok-row.net` | ByteDance（不是 TikTok SSO） |

除 `cn`、`us-ttp` 外的站点会直接返回 `MODEL_DISPATCHER_SITE_UNSUPPORTED`，不会静默回退到 CN。下列资源命令两站一致；查询 US 时在 `model-dispatcher` 前加全局参数 `--site us-ttp`。

## Scenario

```bash
bytedcli model-dispatcher scenario list
```

只返回当前用户有权限看到的场景。`scenarioId` 是后续模型和版本查询的必填选择器。

## Model

```bash
bytedcli model-dispatcher model get --scenario-id 101 --name demo_model
bytedcli model-dispatcher model history list --scenario-id 101 --name demo_model --page-size 20 --page-token 0
```

`model get` 返回模型聚合信息与 `history_count`。`model history list` 返回嵌套修订记录的分页投影，按更新时间倒序排列；JSON 字段包括 `total`、`current_count`、`page_size`、`page_token` 和 `next_page_token`。

## Version

```bash
bytedcli model-dispatcher version list --scenario-id 101 --page-size 20 --page-token 0
```

版本历史属于场景维度，表示模型映射表的演进。分页使用 cursor 语义；后端不回显 cursor，因此 CLI 会把请求的 `page_token` 和计算出的 `next_page_token` 补入输出。
