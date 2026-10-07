# BABI companion 通用调用方式

## 安装与执行

bytedcli 管理 companion 的安装与升级；不要在本 Skill 中全局安装、升级或卸载独立 `babi-cli`。
首次业务调用会按需安装受管运行时。

```bash
bytedcli babi --version
bytedcli babi --help
bytedcli babi <command> [flags]
bytedcli --json babi <command> [flags]
```

本地开发需要覆盖 companion 二进制时，显式使用绝对路径：

```bash
BYTEDCLI_BABI_CLI_PATH=/absolute/path/to/babi-cli bytedcli babi --version
```

## Agent 认证流程

先直接执行目标业务命令，不要预先运行认证探针。bytedcli 会按当前站点获取用户 JWT，
并只在子进程内注入给 companion；不得读取、打印、复制或持久化该 JWT。
只有目标命令明确返回 `AUTH_REQUIRED` 时才运行 `bytedcli auth login`，然后重试原命令。
权限不足按权限问题处理，不要重复登录。

## 站点、网络与输出

- hosted 命令使用 bytedcli 风格的普通动作名，例如 `bytedcli babi account list`；不要添加 standalone 的 `+` 前缀。
- 站点和网关区域使用 bytedcli 全局参数，并放在 `babi` 前：`bytedcli --site boe --vregion <region> babi ...`。未指定时使用当前 bytedcli 路由。商品计费项和折溢价查询的业务筛选参数 `--region` 仍放在 BABI 命令中，不要替换为 `--vregion`。
- bytedcli 的 `--http-timeout-ms`、`--http-retry-count` 和 `--http-retry-base-delay-ms` 会映射为 companion 的 timeout、retries 和 retry-backoff；BABI 命令自身显式提供这些参数时优先。
- `BYTEDCLI_NETWORK_PROFILE=office|prod` 会映射为 companion 的 `office|production`；BABI 自身的 `--header` 等参数仍放在 `babi` 后，并以运行时 help 为准。
- hosted companion 会注入 bytedcli 登录态，因此禁用 `--base-url` 并隔离 standalone 配置，避免把宿主凭据发送到自定义地址。
- bytedcli 的 `us-ttp-bdee`、`us-ttp-usts` 在传给 companion 时统一映射为其支持的 `us-ttp`；宿主仍按原站点选择登录凭据。
- 全局 `bytedcli --json babi ...` 会强制映射为 companion 的 `--format=json`，并优先于 `babi` 后的非 JSON `--format`；不要混用这两种输出选择。
- companion 的自更新检查由宿主关闭，升级由 bytedcli 统一管理。

## 写入安全

服务端写操作只允许领域指南明确列出的白名单：

1. 按领域指南补齐该命令要求的 `--confirm-write`；它只开启受控写路径，不代表用户授权。
2. 对同一命令添加 `--dry-run`，核对目标、参数和请求体；底层方法要求时同时添加 `--confirm`。
3. 取得用户对这一次具体写入的授权。
4. 移除 `--dry-run`，保留该命令要求的确认 flags 后发送。

不要把一次授权扩展到后续写入。任何确认 flag 都不能替代用户授权。
