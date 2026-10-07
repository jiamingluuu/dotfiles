---
name: bytedance-obric-pdm
description: OBRIC CM 项目管理平台的 App Version 命令行工具。支持 App 版本列表查询、版本详情查看、新版本创建等操作。用户明确提到 bytedcli obric-pdm、App Version、release app、查询/创建 App 版本或按 versionNo 查 App 构建信息时使用；ROM 构建、构建产物和 versionDiff 使用 bytedance-obric skill。
---

# bytedcli obric-pdm

OBRIC CM 项目管理平台（OBRIC PDM）CLI 工具，用于管理和查询 App 版本编译状态。

## 命令概览

| 命令                                    | 说明                            |
| --------------------------------------- | ------------------------------- |
| `bytedcli obric-pdm app-version list`   | 列出 App 版本（支持筛选与分页） |
| `bytedcli obric-pdm app-version get`    | 获取 App 版本详情               |
| `bytedcli obric-pdm app-version create` | 创建新 App 版本（默认 dry-run） |

## 认证

使用 ByteCloud SSO JWT 认证，与其他 bytedcli 命令共享登录状态。首次使用前请先执行 `bytedcli auth login` 完成登录。

## References

- 通用 bytedcli 调用、站点切换与 JSON 输出规则：需要确认全局参数位置或安装方式时读取 `../../invocation.md`
- 常见认证、站点和网络问题排查：命令报鉴权或连接错误时读取 `../../troubleshooting.md`

## 常用命令

### 列出版本

```bash
# 列出最近的 App 版本（默认第 1 页，每页 20 条）
bytedcli obric-pdm app-version list

# 按启动人筛选
bytedcli obric-pdm app-version list --starter zhangsan

# 按状态筛选：success、compiling、terminated、failed
bytedcli obric-pdm app-version list --status success

# 按开始时间筛选
bytedcli obric-pdm app-version list --start 2024-01-01

# 分页控制
bytedcli obric-pdm app-version list --page 2 --page-size 50

# 按仓库/业务线/项目筛选
bytedcli obric-pdm app-version list --library demo/app --business-line obric

# 按关键词搜索
bytedcli obric-pdm app-version list --keyword demo-keyword

# JSON 输出（用于脚本解析）
bytedcli --json obric-pdm app-version list
```

### 查看版本详情

```bash
# 获取指定版本详情
bytedcli obric-pdm app-version get --id <version-id>

# JSON 输出
bytedcli --json obric-pdm app-version get --id <version-id>
```

### 创建新版本

```bash
# Dry-run 预览（默认，只显示将要提交的内容）
bytedcli obric-pdm app-version create \
  --repo-server review.example.com \
  --repo-name demo/app \
  --branch main

# 指定版本信息
bytedcli obric-pdm app-version create \
  --repo-server review.example.com \
  --repo-name demo/app \
  --branch main \
  --gerrit-patch https://review.example.com/c/demo/app/+/123 \
  --rebuild-version abcdef1 \
  --description "demo build"

# 确认提交（加 --yes）
bytedcli obric-pdm app-version create \
  --repo-server review.example.com \
  --repo-name demo/app \
  --branch main \
  --yes
```

## 参数说明

### app-version list 参数

| 参数                     | 类型   | 说明                                            |
| ------------------------ | ------ | ----------------------------------------------- |
| `--starter <name>`       | string | 按启动人筛选                                    |
| `--start <date>`         | string | 按开始时间筛选（YYYY-MM-DD 格式）               |
| `--status <status>`      | string | 按状态筛选：success/compiling/terminated/failed |
| `--library <name>`       | string | 按库/仓库名筛选                                 |
| `--business-line <name>` | string | 按业务线筛选，默认 `obric`                      |
| `--project <name>`       | string | 按项目/组名筛选                                 |
| `--keyword <keyword>`    | string | 按关键词搜索                                    |
| `--page <n>`             | number | 页码（默认 1）                                  |
| `--page-size <n>`        | number | 每页条数（默认 20）                             |

### app-version get 参数

| 参数        | 类型   | 必填 | 说明        |
| ----------- | ------ | ---- | ----------- |
| `--id <id>` | string | ✅   | App 版本 ID |

### app-version create 参数

| 参数                           | 类型    | 必填 | 说明                                  |
| ------------------------------ | ------- | ---- | ------------------------------------- |
| `--repo-server <host>`         | string  | ✅   | 代码服务器，例如 `review.example.com` |
| `--repo-name <path>`           | string  | ✅   | 仓库路径，例如 `demo/app`             |
| `--branch <branch>`            | string  | ✅   | 编译分支                              |
| `--business-line <name>`       | string  | -    | 业务线，默认 `obric`                  |
| `--gerrit-patch <url>`         | string  | -    | Gerrit patch/change URL               |
| `--rebuild-version <commit>`   | string  | -    | 指定 commit/version 重新编译          |
| `--description <text>`         | string  | -    | 编译描述                              |
| `--sign`                       | boolean | -    | 启用正式签名                          |
| `--apk-key-type <type>`        | string  | -    | 启用签名时的 APK key 类型             |
| `--apk-sign-keys <keys>`       | string  | -    | 启用签名时的 APK 签名 key             |
| `--app-alone-sign-keys <keys>` | string  | -    | App 级自定义签名 key                  |
| `--yes`                        | boolean | -    | 确认提交（默认 dry-run 预览）         |

## 站点支持

当前支持站点：

- `cn`（默认）：线上环境 https://obric-pdm.bytedance.net
- `boe`：BOE 测试环境

使用 `--site <site>` 指定站点。

## JSON 输出

所有命令支持全局 `--json` 参数，输出结构化 JSON 数据，便于脚本解析和流水线集成。

## Agent Guidance

1. 列表查询优先使用分页参数，避免一次性返回过多数据
2. 创建版本前建议先 dry-run 预览 payload，确认无误后再加 `--yes`
3. 状态筛选使用 CLI 语义枚举值：success、compiling、terminated、failed
4. 版本详情中的 jenkinsUrl 字段指向 Jenkins 构建页面
