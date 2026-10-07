# 芒果登录态与显式上下文

本文件说明 `mango` 命令使用前需要准备哪些信息，以及哪些内容会保存在本地。

## 登录态

首次使用或登录失效时，按顺序执行：

```bash
bytedcli --site cn auth login --session --auto
bytedcli auth userinfo
```

常用命令：

| 命令                                      | 用途                                                |
| ----------------------------------------- | --------------------------------------------------- |
| `--site cn auth login --session --auto`   | 准备 Mango/open-admin 请求需要的 SSO browser session。 |
| `auth userinfo`                           | 查看并刷新当前 bytedcli 登录用户，用于 `Operator`。 |

`mango` 业务接口会自动从 bytedcli 本地 `userinfo.json` 读取当前用户名并填入 `Operator`。不需要、也不支持在命令里显式传入 `Operator`。如果本地用户信息缺失，先执行一次：

```bash
bytedcli auth userinfo
```

如果 `auth userinfo` 报 `refresh token failed`、`http 401`，或 Mango 命令提示 SSO session 缺失/过期，重新执行：

```bash
bytedcli --site cn auth login --session --auto
bytedcli auth userinfo
```

## 本地保存内容

`mango` 使用 bytedcli 已有登录信息，不维护独立的芒果 session 文件：

| 内容        | 说明                                                 |
| ----------- | ---------------------------------------------------- |
| SSO session | `--site cn auth login --session --auto` 维护的浏览器 SSO 状态。 |
| 用户信息    | bytedcli 登录后保存的当前用户名，用于补 `Operator`。 |

Mango 请求会按需用 SSO session 访问 `https://open-admin.bytedance.net/platformApi/main/login`，跟随重定向后获取 open-admin cookie；`mango` 不维护独立的芒果 session 文件，不保存默认空间、默认应用或默认任务。调试本地 cookie 问题时，可临时设置 `BYTEDCLI_MANGO_COOKIE` 覆盖自动获取的 cookie header。`mango task list` 必须显式传 `--space-id` 和 `--module`，其他操作具体任务或接口的命令也要显式传入所需上下文。

## 显式上下文

| 上下文       | 获取方式                                                           | 后续参数                    |
| ------------ | ------------------------------------------------------------------ | --------------------------- |
| 空间 ID      | `bytedcli mango space list`                                       | `--space-id <id>`           |
| 应用模块     | `bytedcli mango app list --space-id`                              | `--module <module>`         |
| 应用 AGW PSM | `bytedcli mango app list --space-id`                               | `--agw-psm <psm>`，接口录入时必传 |
| 任务 ID      | `bytedcli mango task list/create`                                  | `--task-id <id>`            |

空间列表：

| ID  | 空间             |
| --- | ---------------- |
| 1   | 开发者平台       |
| 2   | 基础平台         |
| 3   | 企业机构帐号平台 |
| 4   | 服务商平台       |
| 5   | 抖开内管平台     |
| 6   | ai开放平台       |
| 7   | 抖音云内管       |

## 快速自检

```bash
bytedcli auth userinfo
bytedcli mango space list
bytedcli mango app list --space-id 5
```
