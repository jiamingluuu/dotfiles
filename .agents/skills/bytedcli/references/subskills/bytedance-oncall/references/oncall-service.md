# Oncall 未封装能力处理

bytedcli oncall 只提供当前已注册的 Oncall 命令，不提供通用 service、schema 或 raw API 入口。

## 处理顺序

1. 运行 `bytedcli oncall --help` 确认当前命令。
2. 运行 `bytedcli oncall <resource> <action> --help` 确认叶子命令参数。
3. 如果帮助中没有对应能力，明确说明当前 CLI 不支持；需要新增能力时回到组件仓确认和实现，不要猜测资源名、方法或参数。

## 安全约束

- 不得通过未暴露的底层接口绕过 `flow close` 的权限校验。
- 创建 Oncall、提单、P0 提单或创建 Oncall 群时，返回主技能并完整读取 [故障排查与升级](escalation.md)，按其中的分类条件和确认门禁执行。
- 写操作必须来自用户明确请求，并遵守命令要求的确认门禁。
