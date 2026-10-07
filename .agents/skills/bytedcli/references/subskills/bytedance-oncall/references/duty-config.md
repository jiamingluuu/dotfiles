# 值班配置查询

使用 `duty-config get` 一次查询租户的默认值班配置、值班 SLA、等级策略、值班流程、值班假期和标准角色：

```bash
bytedcli oncall duty-config get \
  --tenant-id "<tenant-id>" \
  --format table
```

- `--tenant-id` 必填，且必须是正整数 Oncall 租户 ID。
- 只有目标租户的管理员可以查询；非管理员调用会返回权限错误，且不会继续读取值班配置。
- 默认值班配置包含问题区域、默认值班计划、时区和服务时间。
- 值班流程中的数字节点会在表格中展示为 `L1`、`L2`、`L3`。
- SLA 和等级策略里的 `P0`、`P1`、`P2`、`P3` 是工单等级，不要与值班流程级别混用。
- 标准角色返回当前租户已配置的 RD、OP、PM、QA 等角色及关联人员。人类可读输出不展示角色 ID，JSON 输出保留接口返回的 ID。
- 使用 `--format json` 时，返回 `default_duty_configs`、`sla`、`escalation_strategies`、`duty_processes`、`holidays` 和 `standard_roles` 六个原始配置数组。
- 命令使用 CLI 认证链路提供的 JWT，不需要也不接受浏览器 Cookie。

等级策略中的 `duty_role` 仍为策略引用的角色 ID；标准角色名称和关联人员以 `standard_roles` 分区为准。
