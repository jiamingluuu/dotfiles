# 本地安全策略

bytedcli 支持按规范命令路径和已解析的 option 值设置 `allow`、`deny`、`confirm` 规则。策略默认关闭；用户启用并配置规则后生效。它是本地防误操作措施，服务端权限仍然决定操作是否允许。

## 生产 TCC 示例

```bash
# 只确认生产环境的配置修改和发布；其他环境、查询命令不匹配这两条规则
bytedcli self safety-policy create --id tcc-prod-update --command "tcc config update" --when env=prod --action confirm
bytedcli self safety-policy create --id tcc-prod-deploy --command "tcc deployment deploy" --when env=prod --action confirm
bytedcli self safety-policy enable
bytedcli self safety-policy show
# 命中 confirm：终端交互确认；Agent/JSON/MCP 返回 SAFETY_POLICY_CONFIRMATION_REQUIRED
bytedcli tcc config update "example.namespace" "demo-key" --env prod --value "demo"
# 必须先说明操作并取得用户明确批准，再使用 --yes 重试同一调用
bytedcli tcc config update "example.namespace" "demo-key" --env prod --value "demo" --yes
# 修改规则会在原位置替换整条规则；--when 必须重新提供全部条件
bytedcli self safety-policy update --id tcc-prod-update --command "tcc config update" --when env=prod --action deny
bytedcli self safety-policy delete --id tcc-prod-update
bytedcli self safety-policy disable
```

`tcc config update` 的 `--env` 默认值是 `ppe`；`tcc deployment deploy` 默认是 `prod`。省略 `--env` 仍按该命令的默认值匹配。TCC 已发布的平铺兼容命令，如 `update-config`、`deploy-config`，映射到上述规范命令；Commander 原生 alias 也使用规范命令名。其他独立注册的兼容命令必须显式声明规范路径，否则需要分别配置规则。

## 规则语义

- 第一条匹配规则生效；未匹配时允许执行。`allow` 只放行本地策略，不绕过原命令自身的确认或鉴权。
- 命令路径不含 `bytedcli` 和业务位置参数，不区分大小写，支持 `*` 通配符。
- 多个 `--when option=value` 是 AND。option 使用不带 `--` 的长参数名，例如 `env`、`target-env`；匹配 CLI 已解析的值，包括 Commander 默认值和 option 环境变量绑定。
- 条件值区分大小写，去除首尾空白，支持 `*`；数字与布尔值按字符串比较。数组任一元素匹配即满足该条件。缺失 option 不匹配，不能推断 handler 内部的隐式默认值。
- JSON/MCP 和非终端输入不弹交互提示。MCP 使用 `yes: true` 重试；CLI 使用 `--yes`。`deny` 不可通过确认跳过。
- 原命令自身的确认、dry-run、权限限制继续生效；本地策略不会把交互批准自动转换成原命令的 `--yes`，也不会根据 `--dry-run` 自动豁免规则。
- help 和策略管理入口不受本地规则拦截。透传命令只匹配宿主注册的路径与 option，不解析外部命令参数；需要批准时使用放在命令域前的全局 `--yes`。

## 文件与环境变量

默认文件为 `~/.local/share/bytedcli/safety-policy.json`，不随认证 profile 切换；AIME 工作区遵循 bytedcli 的用户目录隔离。文件以 `0600` 权限原子写入。每次调用重新加载，运行中的 MCP 服务也能读取后续修改。

```json
{
  "enabled": true,
  "rules": [
    {
      "id": "tcc-prod-update",
      "command": "tcc config update",
      "options": { "env": "prod" },
      "action": "confirm"
    }
  ]
}
```

环境变量优先于文件：

| 变量 | 语义 |
| --- | --- |
| `BYTEDCLI_SAFETY_POLICY_FILE` | 指定策略文件路径，适用于 CI 和隔离配置 |
| `BYTEDCLI_SAFETY_POLICY_ENABLED` | 覆盖开关，接受 `true/false/1/0` |
| `BYTEDCLI_SAFETY_POLICY_RULES` | JSON 规则数组，完整替换文件规则；`[]` 清空规则 |

文件缺失时默认关闭；文件损坏、`null`、重复规则 ID、非法动作或环境变量格式错误都会返回 `SAFETY_POLICY_CONFIG_ERROR`，业务命令不会执行。`show` 同时展示存储配置和生效配置；管理命令修改文件，不会修改进程环境变量。
