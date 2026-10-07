---
name: bytedance-bmt
description: "Operate BMT (Byte Multi-Tenant Platform) via bytedcli: resolve a service from PSM, inspect tags, list resources, resolve MQ or RDS resource connection info, and inspect service-scoped or PSM-scoped isolation sets and user roles."
---

# bytedcli BMT

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

## When to use

- 按 PSM 反查 BMT service
- 查看 BMT service 的标签、资源、隔离集和 user role
- 按 resource code 解析 RDS 或 RocketMQ 连接信息
- 从 BMT 控制台 URL、service id、PSM、resource code 回到可执行 CLI

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- BMT 国际站请求通常需要 `--site i18n-tt`
- 首次调用前先登录目标站点：`bytedcli --site i18n-tt auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `bmt service`, `bmt tag`, `bmt resource`, `bmt isolation-set`, `bmt psm`, and `bmt user-role`.

```bash
# 按 PSM 获取 service
bytedcli --site i18n-tt bmt service get --psm "example.payment.core"

# 列 service 标签
bytedcli --site i18n-tt bmt tag list --psm "example.payment.core" --page 1 --page-size 20

# 列 service 资源
bytedcli --site i18n-tt bmt resource list --psm "example.payment.core" --type mq --page 1 --page-size 20
bytedcli --site i18n-tt bmt resource list --psm "example.payment.core" --type rds --page 1 --page-size 20

# 按 resource code 解析连接信息
bytedcli --site i18n-tt bmt resource resolve --psm "example.payment.core" --code "demo-mq-topic"
bytedcli --site i18n-tt bmt resource resolve --psm "example.payment.core" --code "demo-rds-instance" --type rds

# 查看隔离集和 user role
bytedcli --site i18n-tt bmt isolation-set list --psm "example.payment.core" --page 1 --page-size 20
bytedcli --site i18n-tt bmt psm isolation-set list --psm "example.payment.core" --page 1 --page-size 20
bytedcli --site i18n-tt bmt psm resource list --psm "example.payment.core" --isolation-set-id "1234567890123456789" --region "Singapore-Central" --type rds --page 1 --page-size 20
bytedcli --site i18n-tt bmt psm resource resolve --psm "example.payment.core" --code "demo-rds-resource" --type rds
bytedcli --site i18n-tt bmt user-role get --psm "example.payment.core"
```

## Notes

- `--json` 是全局参数，放在 `bmt` 前面，例如 `bytedcli --json --site i18n-tt bmt resource resolve ...`
- 服务级命令优先使用 `--psm`；`--service-id` 仅保留给兼容场景
- `bmt isolation-set list` 返回当前用户在 service 下可见的隔离集；`bmt psm isolation-set list` 返回目标 PSM 绑定的隔离集
- `bmt psm resource list` 需要同时提供 `--isolation-set-id` 和 `--region`，它查询的是指定 PSM 在某个隔离集/region 下绑定的资源，而不是整个 service 的全量资源
- `bmt psm resource resolve` 适合直接回答“某个 PSM 与某个资源 code 如何关联”；它会校验目标 PSM 是否真的出现在资源绑定中
- `bmt resource resolve` 未传 `--type` 时，会自动尝试 `mq -> rds`
- `--type` 使用语义值 `mq|rds`，不要传后端数字枚举
- 公开分页默认值统一为 `20`
- BMT 鉴权依赖 ByteCloud JWT，请优先用 `auth login` 获取，而不是手写请求头

## References

- `references/bmt.md`
