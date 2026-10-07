---
name: bytedance-bfo
description: "Operate BFO (Byte FinOps) via bytedcli: search service tree nodes, query CPU spec upgrade summary/clusters/details/profit. Use when tasks mention BFO, Byte FinOps, CPU spec upgrade, CPU 规格升级, 规格升配, 性能优化, or 收益回收."
---

# BFO

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

BFO (Byte FinOps) 平台的 CLI 操作工具，当前支持 CPU 规格升级查询。

## Capabilities

- 服务树搜索：通过关键词搜索 Galaxy 服务树节点，获取 node ID
- CPU 规格升级概览：查看指定服务树节点下的 CPU 规格升级推荐覆盖范围与预估收益
- 逻辑集群列表：分页列出推荐升级的逻辑集群，支持按 Pod CPU 规格过滤
- 物理集群详情：查看逻辑集群下的物理集群规格详情（当前规格、建议规格、预期收益）
- 收益回收记录：查看 CPU 规格优化后的实际收益回收数据

## Usage

```bash
# 搜索服务树节点（获取 node-id）
bytedcli bfo tree search --keyword example-service

# CPU 规格升级概览
bytedcli bfo cpu-spec summary --node-id 17

# 列出推荐升级的逻辑集群（分页）
bytedcli bfo cpu-spec list --node-id 17 --page-num 1 --page-size 20

# 按 Pod CPU 规格过滤（小于 8 核）
bytedcli bfo cpu-spec list --node-id 17 --cpu-spec 8

# 查看物理集群详情
bytedcli bfo cpu-spec detail --psm example.service.api --cluster default

# 指定 region
bytedcli bfo cpu-spec detail --psm example.service.api --cluster default --region China-East

# 查看收益回收记录
bytedcli bfo cpu-spec profit --node-id 17

# Agent 调用必须加上 --json
bytedcli --json bfo tree search --keyword example-service
bytedcli --json bfo cpu-spec summary --node-id 17
bytedcli --json bfo cpu-spec list --node-id 17
bytedcli --json bfo cpu-spec detail --psm example.service.api --cluster default
bytedcli --json bfo cpu-spec profit --node-id 17
```

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--region <region>` | Region | `China-North` |
| `--page-num <num>` | Page number | `1` |
| `--page-size <size>` | Page size | `10` |
| `-j, --json` | JSON output | - |
