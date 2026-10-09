---
name: bytedance-bytetree
description: "Use bytedcli ByteTree for 服务树/业务树 nodes/domains, parent-child hierarchy, owner/负责人 role members, subscriptions, providers and mounted resources. Invoke for 服务归属、业务域、节点层级/订阅、Provider、资源挂载 or 父子链路 queries."
---

# ByteTree CLI

## When to use

- 搜索服务树节点，或单个、批量查询节点详情
- 查看节点资源、直接子节点或完整父链
- 查看或调整节点 IAM Owner 角色成员
- 查看、添加或删除当前用户的节点订阅
- 查询 Provider、创建平台、云产品映射和 Provider 注册资源
- 根据服务树定位服务、资源、PSM、文件夹或负责人
- 搜索业务树业务域，查询子域、叶子域、标签、权限与资源
- 展开业务域关联或排除的服务树节点

## Quick start

使用 `bytedcli bytetree`；首次调用会按锁定版本安装 Companion：

```bash
# 查询服务树节点
bytedcli bytetree search --keyword "demo-service-tree"
bytedcli bytetree get --node-id 1234567
bytedcli bytetree batch-get --node-id 1234567,2345678

# 查看节点关系和资源
bytedcli bytetree resources --node-id 1234567 --provider codebase
bytedcli bytetree children --node-id 1234567
bytedcli bytetree parents --node-id 1234567

# bytedcli 宿主命令：管理节点 Owner
bytedcli bytetree owner list --node-id 1234567
bytedcli bytetree owner add --node-id 1234567 --user demo.owner

# 管理节点订阅
bytedcli bytetree subscription list
bytedcli bytetree subscription create --node-id 1234567 --yes

# Provider 查询
bytedcli bytetree provider search --name tce
bytedcli bytetree provider get --name tce
bytedcli bytetree provider resource list --name tce

# 查询业务树
bytedcli bytetree biz search --keyword "demo-business"
bytedcli bytetree biz get --domain-code demo_domain --expand-bytetree
```

## Agent guidance

- 不知道节点 ID 时先用 `search`，拿到 ID 后再调用 `get`、`children`、`parents` 或 `resources`。
- 有一批精确 ID、叶子节点名或路径时使用 `batch-get`；三类条件按 OR 组合，总数最多 10000。
- `owner list/add/delete/set` 是 bytedcli 宿主命令；写操作默认 dry-run，核对 payload 后才加 `--yes`。
- `subscription create/delete` 不带 `--yes` 时只返回 dry-run 预览，不发送写请求；核对节点 ID 后才加 `--yes`。
- Provider 自身注册的资源用 `provider resource list`；节点挂载视角使用顶层 `resources`。
- 服务树与业务树是两套层级；业务组织结构使用 `biz`，不要用服务树 `search` 替代。
- 稳定消费结果时使用 `--json`，并把全局参数放在 domain/command 前面。
- `bytedcli bytetree` 会把宿主原生命令和 Companion 命令按完整路径融合；同路径冲突时 Companion 优先，只有宿主拥有的 `owner` 叶子仍由 bytedcli 执行。
- 参数或输出不确定时优先查看对应命令的 `--help`，不要猜测位置参数。

## References

- [bytetree.md](./references/bytetree.md)
- [invocation.md](./../../invocation.md)
- [troubleshooting.md](./../../troubleshooting.md)
