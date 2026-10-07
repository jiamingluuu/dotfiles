---
name: bytedance-vnet
description: "Use bytedcli for VNet (私有网络) resource search, detail lookup, Grafana dashboard links, and account quota usage or limits. Trigger when tasks mention VNet, VPC, Subnet, ENI, PLB, CLB, EIP, NAT, VPN, VNet quota, account quota, quota codes, or other ByteDance internal network resources."
---

# VNet (私有网络)

## 如何调用

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

## When to use

- 需要搜索 VNet 网络资源（VPC、子网、弹性网卡、负载均衡等），这些资源均为火山引擎私有网络（Volcano Engine VPC）的网络资源信息
- 需要查询网络资源的详情信息
- 需要通过 IP 地址反查所属资源

## 前置条件

- 需要鉴权，先登录：`bytedcli auth login --session`
- VNet 命令依赖浏览器 Session Cookie，必须使用 `--session` 方式登录

## 功能分组

- **VNet Search**：`references/vnet-search.md`
- **VNet Endpoint (ep)**：`vnet get --id ep-xxx --region cn-beijing`，详见 `references/vnet-search.md`
- **VNet Grafana Dashboards**：`references/vnet-dashboards.md`
- **VNet Quota**：查询账号在多个地域的用量与上限时，读取 `references/vnet-quota.md`

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前）
- `--json` 模式下搜索命令默认关闭终端二维码，并自动启用 `--qr-image`
- 需要排查具体请求链路时，使用 `--http-debug`
- VNet 认证复用全局 SSO Session，通过浏览器 Cookie 捕获 `_vnet-session`
- `vnet dashboards` 是平台 Grafana 大盘索引的"列表 + 链接生成器"；要拿监控指标值请用 `bytedcli apm grafana query` 或浏览器打开 Link。
- `vnet quota get` 只查询服务端当前 Quota 数据，不做告警阈值、多账号巡检、扩容建议或通知编排。

## References

- `../../troubleshooting.md`
- `references/vnet-dashboards.md`
- `references/vnet-search.md`
- `references/vnet-quota.md`
