---
name: bytedance-mock
description: "Operate ByteMock (API Mock) via bytedcli: create/list/update/delete mock rules, manage namespaces and services, configure dyeing (traffic routing) rules, preload services. Use when tasks mention mock, bytemock, mock rule, API mock, mock data, dyeing rule, or traffic routing."
---

# bytedcli Mock

## When to use

- 创建/查看/修改/删除 Mock 规则
- 管理 Mock 命名空间和服务
- 配置染色规则（流量牵引）
- 预加载服务 IDL

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 查看规则
bytedcli --site boe mock rule list --namespace boe_demo_lane --psm example.service.downstream

# 创建规则
bytedcli --site boe mock rule create --namespace boe_demo_lane --callee-psm example.service.downstream --method SampleMethod --name "demo-rule" --mock-data '{"field":"value"}' --protocol thrift

# 查看/启用/禁用/删除规则
bytedcli --site boe mock rule get --id 12345
bytedcli --site boe mock rule enable --id 12345
bytedcli --site boe mock rule disable --id 12345
bytedcli --site boe mock rule delete --id 12345

# 管理命名空间
bytedcli --site boe mock namespace list --keyword demo
bytedcli --site boe mock namespace create --name boe_demo_lane

# 管理服务
bytedcli --site boe mock service list --namespace boe_demo_lane
bytedcli --site boe mock service create --psm example.service.downstream --namespace boe_demo_lane --protocol thrift

# 染色规则
bytedcli --site boe mock dyeing list --namespace boe_demo_lane
bytedcli --site boe mock dyeing update --callee example.service.downstream --caller example.service.caller --method SampleMethod --dyeing "ENV:boe_demo_lane" --type thrift

# 预加载
bytedcli --site boe mock service prepare --psm example.service.downstream
```

## Notes

- `--site` 控制目标环境（prod/boe/boei18n/i18n/i18n-tt/i18n-bd/us-ttp/eu-ttp），域名自动映射；i18n 控制面区分办公网 OG 域名与生产网域名，默认优先探测办公网、不可达再回退生产网，也可用 `BYTEDCLI_NETWORK_PROFILE=prod|office` 显式指定。完整域名表与探测规则见 `references/mock.md`「Domain Mapping」
- `--mock-data` 接受 JSON 字符串，`--mock-data-file` 接受文件路径
- `mock rule list` 推荐使用 `--psm` 过滤被调用方；`--callee-psm` 保留为兼容别名。HTTP 接口规则可同时传 `--path` 与 `--http-method` 精确过滤，`--status` 支持 `all|on|off|1|0`
- 创建的规则默认 `status=1`（启用）；传 `--status 0` 时会在创建后自动补一次禁用，确保不立即生效
- 染色规则的 `--dyeing` 格式为 `ENV:<lane_name>`，如 `ENV:boe_demo_lane`

## References

- `references/mock.md`
- `../../invocation.md`
- `../../troubleshooting.md`
