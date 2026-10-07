# ByteDoc MongoDB 连接指南

当任务涉及生成或审查 ByteDoc SDK 连接代码、诊断连接失败，或判断连接问题来自凭证、网络边界还是运行环境时，使用本指南。

本指南将 MongoDB 官方 `mongodb-connection` agent-skill 规则适配到 ByteDoc 场景。纳入和排除的 upstream skill 见 `../references/mongodb-upstream-adaptation.md`。

## ByteDoc 优先

- 建议连接串前，先按 `../references/selection-guards.md` 确认 `site`，并确认目标数据库的 `backend` 和 `vregion` 是否唯一。随后运行 `sdk plan`，并显式携带已确认的 `--backend` 和必要的全局 `--vregion`。
- `backend` 和 `vregion` 没有默认值：只能由用户明确提供，或由搜索/resolver 证明唯一；任一维度多值时必须让用户选择。
- `BYTEDOC_AMBIGUOUS` / `agent_protocol.next_state=ASK_USER` 是硬边界：展示候选表，不要自行选择后继续生成连接方案。
- 将 `supportStatus`、`accessMethod`、`prerequisites`、`warnings` 和 `references` 作为真源。
- 不要编造 hostname、token、Consul endpoint、Mesh socket 或 direct MongoDB URI。
- 如果 `supportStatus` 是 `unsupported` 或 `needs_input`，停止生成代码，改为展示 `questions[]`、`warnings[]` 和 `references[]`。
- `accessMethod.kind=visual-query` 不生成连接代码；如果用户继续要查数据，切换到 `mongo-ops` 或 `mongodb-natural-language-querying`。

## 连接代码规则

- Go 代码使用 ByteDoc 官方 driver `code.byted.org/bytedoc/mongo-go-driver`；生成 ByteDoc 示例时不要直接依赖 upstream `go.mongodb.org/mongo-driver`。
- upstream MongoDB driver 文档只作为 API 形态参考；ByteDoc package 选择以 ByteDoc 官方 SDK 文档为准。
- 每个进程或组件生命周期复用一个 `mongo.Client`；不要每个请求都 connect/disconnect。
- `Connect`、`Ping` 和每次查询操作都使用 `context.WithTimeout`。
- 不要把 `SEC_TOKEN_STRING`、开发调试用户名/密码或完整 URI 写入日志、错误、metrics 或 panic 输出。
- 开发调试账号密码使用 `net/url` 或等价方式转义；不要把原始密码直接拼进 URI。
- close/disconnect 逻辑放在进程退出或 owner 生命周期边界，不要放在热查询路径。

## ByteDoc 访问方式

- `consul-token`：使用运行时 token 注入，例如 `SEC_TOKEN_STRING`；不要要求用户粘贴 token。
- `consul-temporary-credential`：兼容 kind；仅在 `sdk plan` 返回支持的本地/开发环境中使用开发调试账号密码，稳定语义见 `canonicalKind=consul-password`。
- `mesh-token` / `mesh-socket`：先确认 TCE/FaaS Mesh egress 前置条件，再判断是否是 driver 代码问题。
- `visual-query`：不要生成 SDK 代码；引导用户使用可视化/查询流程。

## 排障流程

1. 确认 site 后，先用 `bytedoc search` 或 `sdk plan` resolver 确认 backend/vregion 唯一；多值时让用户选择。
2. 重新运行 `bytedcli --json --site <site> --vregion <confirmed-vregion> bytedoc sdk plan --service <psm> --backend <confirmed-backend> --access-env <env> --language go`。
   只有目标唯一、平台元数据缺少引擎版本且已有明确版本证据时，才补 `--engine-version 4.0|8.0`；不得用该参数覆盖平台已有版本。
3. 确认实际运行环境与 plan 匹配：`local-mac`、`devbox`、`tce` 或 `faas`。
4. 已知 caller PSM 时，先用 `bytedoc access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）检查 caller PSM 当前授权状态；classic / cloud-native / Volc 都适用，target/backend/vregion 需先确认唯一。IAM 用户/角色授权可用 `bytedoc access permission get` 检查当前操作者是否具备发起授权的前置权限，但不能证明 caller PSM 已授权；Volc PSM/token 授权继续显式携带 `--backend volc`，或遵循错误码为 `BYTEDOC_ACCESS_REQUIRED` 的错误对象路径 `error.details.setup_commands`。先完成带目标选择器的 `access psm list`，再根据状态决定是否进入 `ticket create` / `psm create` dry-run；不要把 Volc IAM 用户/角色授权改成 PSM 授权。
5. 确认代码使用了 `sdk generate` 返回的接入方式和必要环境变量。
6. 只有 ByteDoc 事实一致后，再检查 driver 级错误、timeout、连接池使用和 context deadline。

## 连接排障示例

```bash
# 场景：用户说"连接 example_db 报超时"

# Step 1: 确认 site 后解析目标数据库
bytedcli --json --site cn bytedoc search --keyword "example.bytedoc.example_db"
# → 确认唯一候选：backend=classic, vregion=China-North

# Step 2: 查看接入方案
bytedcli --json --site cn --vregion China-North bytedoc sdk plan --service "example.bytedoc.example_db" --backend classic --access-env tce --caller-psm "example.caller.psm" --language go

# Step 3: 检查 caller PSM 授权状态
bytedcli --json --site cn --vregion China-North bytedoc access psm list --service "example.bytedoc.example_db" --backend classic --account "example.caller.psm"

# Step 4: 如果问题仍未解决，使用 sdk doctor
bytedcli --json --site cn --vregion China-North bytedoc sdk doctor --error-text "connection timeout" --service "example.bytedoc.example_db" --backend classic --access-env tce --caller-psm "example.caller.psm"
```

## 不要做

- 不要推荐 Atlas 连接配置、Atlas UI 步骤或 MongoDB MCP setup。
- 不要把调整连接池大小作为第一修复手段；先收集延迟、并发和 timeout 证据。
- 不要建议用 SSH tunnel 或 direct database endpoint 绕过 ByteDoc 网络边界。

## DO / DON'T

| 场景 | ✅ DO | ❌ DON'T |
| --- | --- | --- |
| 诊断连接问题 | 先 `sdk plan` 确认接入方式 | 不要直接调连接池参数 |
| 超时报错 | 先区分是建连超时还是查询超时 | 不要一律建议加大 timeout |
| 用户问连接串 | 用 `sdk plan` / `sdk generate` 获取 | 不要编造 URI 或 hostname |
| Mesh 连接失败 | 确认 TCE Mesh egress 前置条件 | 不要建议换 direct connect |
| 开发调试账号密码 | 确认是 dev 环境且 plan 支持 | 不要在 prod 环境使用开发凭据 |
| caller PSM 授权诊断 | 使用 `access psm list --service <target.psm> --backend <confirmed-backend> --account <caller.psm>`（或 `--db-name <db>`）读取当前授权状态 | 不要用 IAM `permission get`、`role list` 或 dry-run 证明 caller PSM 权限 |
| Volc PSM/token 授权诊断 | 使用 `access psm list --service <target.psm> --backend volc --account <caller.psm>` 或 setup_commands | 不要用 IAM `permission get` 证明 PSM token 权限 |
| 用户要求可视化查询 | 说明不生成 SDK，切换查询流程 | 不要输出连接代码或机械执行数据面命令 |
