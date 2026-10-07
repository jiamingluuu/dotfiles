# BMT

```bash
# 按 PSM 获取 service
bytedcli --site i18n-tt bmt service get --psm "example.payment.core"

# 标签 / 隔离集 / user role
bytedcli --site i18n-tt bmt tag list --psm "example.payment.core" --page 1 --page-size 20
bytedcli --site i18n-tt bmt isolation-set list --psm "example.payment.core" --page 1 --page-size 20
bytedcli --site i18n-tt bmt psm isolation-set list --psm "example.payment.core" --page 1 --page-size 20
bytedcli --site i18n-tt bmt psm resource list --psm "example.payment.core" --isolation-set-id "1234567890123456789" --region "Singapore-Central" --type rds --page 1 --page-size 20
bytedcli --site i18n-tt bmt psm resource resolve --psm "example.payment.core" --code "demo-rds-resource" --type rds
bytedcli --site i18n-tt bmt user-role get --psm "example.payment.core"

# 资源列表
bytedcli --site i18n-tt bmt resource list --psm "example.payment.core" --type mq --page 1 --page-size 20
bytedcli --site i18n-tt bmt resource list --psm "example.payment.core" --type rds --page 1 --page-size 20

# 资源解析：省略 --type 时自动尝试 mq -> rds
bytedcli --site i18n-tt bmt resource resolve --psm "example.payment.core" --code "demo-mq-topic"
bytedcli --site i18n-tt bmt resource resolve --psm "example.payment.core" --code "demo-rds-instance" --type rds

# 机器可读输出
bytedcli --json --site i18n-tt bmt resource resolve --psm "example.payment.core" --code "demo-mq-topic"
```

## Notes

- BMT 服务级命令优先使用 `--psm`
- `--service-id` 仅用于兼容旧脚本，不建议新调用继续使用
- `bmt isolation-set list` 查看当前用户在 service 下可见的隔离集；`bmt psm isolation-set list` 查看指定 PSM 绑定的隔离集
- `bmt psm resource list` 需要 `--isolation-set-id` 和 `--region`；它返回指定 PSM 在该隔离集/region 下绑定的资源
- `bmt psm resource resolve` 直接回答某个 PSM 与资源 code 的关联详情，并校验目标 PSM 是否真的出现在资源绑定中
- `resource resolve` 返回的是匹配到的单个 resource 及其展开后的实例、PSM 连接信息
- `mq` 资源重点看 `cluster` / `topic`；`rds` 资源重点看 `db_name` / `psm`
