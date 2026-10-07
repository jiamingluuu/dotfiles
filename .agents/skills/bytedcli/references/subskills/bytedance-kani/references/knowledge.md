# Kani 知识库检索

检索 Kani 权限系统相关知识库，回答权限申请、审批、排障类问题。

```bash
# 检索 Kani 权限系统相关知识
bytedcli kani knowledge search --query "如何申请 Kani 资源权限"

# 带上下文检索并限制返回知识库切片数量
bytedcli kani knowledge search \
  --query "Kani 权限审批失败怎么办" \
  --context "用户正在排查权限申请" \
  --result-limit 10

# JSON 输出（全局参数必须放在子命令前）
bytedcli --json kani knowledge search --query "如何申请 Kani 资源权限"
```

## 参数一览（kani knowledge search）

> 具体可用参数以 `bytedcli kani knowledge search --help` 为准。

- `--query <query>`：用于知识库检索的用户查询语句（必填）
- `--context <context>`：辅助检索的聊天记录或用户上下文信息
- `--result-limit <n>`：返回知识库切片数量，`1..50`，默认 `5`

## 站点

- 默认站点 `cn`，BOE 走隐藏参数 `--kani-site boe`。
