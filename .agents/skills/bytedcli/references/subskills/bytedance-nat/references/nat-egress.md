# 字节内场 NAT（DCS）出口公网 IP 查询

根据运行中工作负载的 PSM、VDC/IDC 和可选源身份，查询 Pisces 配置的公网出口网段：

```bash
bytedcli nat egress get \
  --psm "example.service.api" \
  --vdc "demo-vdc" \
  --source "10.0.0.1"

bytedcli --json nat egress get \
  --psm "example.service.api" \
  --vdc "demo-vdc"
```

## 参数语义

- `--psm`：必填；用于查询当前处于 Running 状态的 TCE Pod。
- `--vdc`：可选；与 Pod 的 VDC 或 IDC 精确匹配。省略时返回该 PSM 当前运行 Pod 涉及的所有 VDC。
- `--source`：可选；与 Pod IP、Host IP、Node、Pod 名或 Deployment 名精确匹配。源 IP 可直接传给该参数。
- `--site`：可选；显式传 `cn` 或 `boe`，省略时跟随 CLI 的站点配置。不支持的站点会报错，不静默改查 CN；先确认目标环境，再选择受支持的站点。

## 结果判断

- `data_quality=configured`：出口网段来自 Pisces `nat_snat` 配置；不代表机器运行态已经生效，也不证明某条连接实际使用了该公网 IP。
- `data_quality=current` / `fallback`：兼容旧版本响应。查看每条网段的 `source` 和 `warnings`；不能据此认定实际 SNAT 出口，旧版本 IPSet 口径不等于公网出口配置。
- `data_quality=missing`：没有可展示的出口网段；不要把 `srcset` 当作公网出口范围。
- `source_matches` 仅在传入 `--source` 时返回，用于确认源 IP/身份确实命中了运行中的 Pod。

该命令是只读诊断，不触发实时 IPSet 扫描，也不修改 NAT 配置。若 PSM 没有匹配的运行中 Pod，命令会直接报错，不猜测 VDC。要确认历史连接实际使用的公网出口 IP，读取 [NAT 历史流量查询](nat-traffic.md)，以观测记录中的 `egress_ip` 为准。
