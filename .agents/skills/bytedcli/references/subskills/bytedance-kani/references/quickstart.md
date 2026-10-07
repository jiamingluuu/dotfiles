# Kani Quick Start

在以下场景读取本文件：

- 你已经确定要用 Kani skill，但想先看一组最短可用命令
- 你想快速区分 `workflow create` / `workflow get` / `workflow list` 的入口
- 你需要一份面向 Agent 的常用命令速查表

## 常用命令

```bash
# 查看帮助
bytedcli kani --help

# 检索 Kani 知识库
bytedcli kani knowledge search --query "如何申请 Kani 资源权限"

# Kani OpenAPI 第一步：先找当前 identity 能访问的 namespace
bytedcli kani openapi identity namespace list --identity-key alice

# 列出 workflow（默认查当前/running）
bytedcli kani openapi workflow list

# 创建 workflow（`create` 走 `--body-file` 模式）
bytedcli kani openapi workflow create --body-file ./workflow-create-resource.json

# 查询 workflow 详情
bytedcli kani openapi workflow get \
  --workflow-id wf_demo \
  --namespace kani_demo \
  --applicant alice

# write-log 默认查当前 identity 最近 30 天
bytedcli kani openapi write-log list

# 机器可读输出（全局参数，必须放在子命令前）
bytedcli --json kani openapi workflow list
bytedcli --json kani knowledge search --query "如何申请 Kani 资源权限"
```

## 快速规则

- `workflow create` / `workflow get` / `workflow list` 都可直接使用
- `workflow list` 默认查当前/running；若需要查已完成记录，传 `--status finished`
- `workflow list` 在 running 场景下使用公开 `--page/--page-size` 分页时，默认查询 `urgent=false` 的稳定 bucket
- `workflow list` 当前只沿用 `cn|boe` 这组保守 region 口径
- `workflow create`：`--body-file` 模式，直接提交原始 JSON request body
- 隐藏兼容路径仍可用，但不作为对外推荐入口
