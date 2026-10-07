# MindAI 图表鉴权参考

本参考只负责 `bytedcli mindai chart` 的 MindAI 网关鉴权、初始化和授权排障。正常生成、调整、下载或监听时，直接运行业务命令，不要预先重复检查状态。

## 鉴权边界

客户端只支持 `bytedcli-jwt`：

1. bytedcli 使用本地 SSO 登录态获取 fresh ByteCloud JWT。
2. 宿主通过子进程 stdin 把 JWT 注入 bundled Python 客户端。
3. Python 客户端用 JWT 调用 MindAI 网关，不把 JWT 写入 argv、配置、日志或任务状态。

客户端还会调用 MindAI 网关的 `/mindai/wiki/apiai/feishuHasAuth`。虽然接口名包含 `feishu`，它在本模块中只是 MindAI 服务的用户初始化/授权前置检查，不代表客户端会调用本地 Lark API、读写飞书文档或操作画板。

## 默认配置

如果配置文件不存在，客户端使用内置 MindAI 网关地址和 `bytedcli-jwt`。通常无需先运行 `mindai chart auth login`。

```bash
bytedcli mindai chart config get
bytedcli mindai chart auth status
```

只有需要覆盖网关地址或显式保存配置时才运行：

```bash
bytedcli mindai chart auth login --provider bytedcli-jwt
```

配置文件只保存非敏感配置，不保存 JWT。

## 常见错误

| 现象 | 含义 | 处理 |
|---|---|---|
| `Required executable not found: bytedcli` | 直接执行底层 Python 客户端且找不到宿主 | 安装 bytedcli，并从公开 `bytedcli mindai chart ...` 命令进入 |
| ByteCloud JWT 获取失败 | 当前 bytedcli SSO 登录态不可用 | 按错误提示检查 `bytedcli auth status`，必要时登录后重试原命令 |
| `feishuHasAuth` 返回 `auth=false` | MindAI 用户初始化或服务端授权未完成 | 打开错误返回的 MindAI 授权链接，完成后重试原命令 |
| `Cannot reach`、`Cannot watch` | 网关网络、代理或 DNS 问题 | 先重试；仍失败时检查内网和代理可达性 |

MindAI 请求会在 DNS 双栈结果中优先尝试 IPv4，并保留 IPv6 兜底。

## 安全约束

- 不打印或持久化 JWT、Cookie、Authorization 头和完整服务端内部错误。
- 不把 JWT 放入命令行参数或配置文件。
- 不根据 `feishuHasAuth` 的命名扩展本地 Lark 权限或文档操作。
- 文档、画板或 Canvas 需求应路由到对应 Lark/whiteboard 能力，不在 MindAI 客户端中处理。
