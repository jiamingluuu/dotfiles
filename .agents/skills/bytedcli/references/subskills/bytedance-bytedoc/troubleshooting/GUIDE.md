# ByteDoc 故障分诊路由

当 ByteDoc 命令失败或返回结构化错误时，使用本指南。

## 错误码

| Error/code                                                              | 处理动作                                                                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AUTH_REQUIRED`、401、not authenticated                                 | 针对目标站点运行 `bytedcli auth login`，然后重试同一条命令。                                                                                                                                                                                                                |
| `BYTEDOC_ACCESS_REQUIRED`                                               | 加载 `access-workflows/GUIDE.md`，遵循 `error.details.setup_commands`。                                                                                                                                                                                                     |
| `BYTEDOC_DBW_IAM_REQUIRED`                                              | **这是 ByteCloud IAM 权限问题，不是 PSM 授权问题。** 用户缺少 DBW 平台的 IAM action 权限（如 `dbw:ExecuteSQL`）。MongoDB 级别的 PSM 授权已经到位，不要走 `access psm create`。引导用户到 `error.details.iam_console_url` 申请 IAM 策略。                                    |
| `BYTEDOC_NON_JSON_RESPONSE`、`Failed to parse JSON` 且响应包含 `<html>` | 这是 HTTP/auth/gateway 层返回了 HTML 页面，不是 Mongo 查询语法错误。读取 `status_code`、`endpoint`、`details.response_preview_format` 和 `details.response`；不要把 `document list` / `find()` 改成 `findOne()` 试错。                                                      |
| `BYTEDOC_DMS_ERROR`                                                     | DMS subscribe/evaluate 阶段失败。读取 `details.stage`、`endpoint`、`request_id` 和 `details.upstream_details`；按 `agent_protocol.next_state=STOP` 停止，不要切 backend/vregion、猜库名、发起权限申请，或改用 `document update` / `shell updateOne` 等同类 Mongo 变体继续。 |
| `BYTEDOC_PLATFORM_SCHEMA_ERROR`                                         | ByteDoc 平台网关/schema tagging 拒绝。读取 `endpoint`、`request_id`、`details.upstream_response`；按 `agent_protocol.next_state=STOP` 停止，并把信息反馈给平台维护方。不要把它当成 DB 权限或查询语法问题。                                                                  |
| `BYTEDOC_UNSUPPORTED_SITE`，且 `details.site` 是 `us-ttp` 或 `eu-ttp`   | US-TTP / EU-TTP classic / cloud-native 不支持 DMS 数据查询。告知用户该限制并停止；不要猜 dc、改 DMS endpoint、切 backend/vregion 或申请权限。搜索、详情、IAM 等控制面能力不受影响。                                                                                         |
| i18n-bd / Asia-SouthEastBD DMS 返回 `BYTEDOC_UNSUPPORTED_SITE`          | 该区域的 classic/cloud-native DMS 当前不支持，按 `agent_protocol.next_state=STOP` 停止并报告限制；既有别名、配置和默认区域同样受限。不要重试、猜 dc、改 endpoint、切 backend/vregion 或申请权限。搜索、详情、IAM、Volc/DBW 与其他受支持的 i18n-bd 区域不受影响。            |
| `BYTEDOC_AMBIGUOUS`                                                     | 展示候选表格给用户选择（包含 PSM、backend、vregion 信息）；不要猜。                                                                                                                                                                                                         |
| `BYTEDOC_INDEX_CREATION_REQUIRES_BPM`                                   | classic DMS shell 建索引被禁用。停止当前 Mongo shell 路径，加载 `index-governance/GUIDE.md`，用 `bytedoc index create` 先生成 dry-run；不要改用 query-file、DMS direct helper 或脚本。                                                                                      |
| `BYTEDOC_UNSAFE_OPERATION_BLOCKED`                                      | 停止，并引导用户走经过审核的管理流程。                                                                                                                                                                                                                                      |
| `BYTEDOC_ROUTING_UNRESOLVED`                                            | 询问或核对 site、vRegion、service 和返回的 region；不要回退到 CN。                                                                                                                                                                                                          |
| `BYTEDOC_INPUT_ERROR`                                                   | 如果是 selector 或 role 非法，展示 `../references/selection-guards.md` 中的完整选项并询问用户；不要自行换值重试。                                                                                                                                                           |
| `PaginationParamError`、DBW `ListTables` 错误                           | 这是 DBW 数据面错误；保留同一 backend/vregion 复查，不要切到 classic IAM 授权接口。                                                                                                                                                                                         |
| SDK connection/auth/DNS/Consul/Mesh failure                             | 加载 `sdk-access/GUIDE.md` 并运行 `sdk doctor`。                                                                                                                                                                                                                            |

## 常用检查

```bash
bytedcli auth status
bytedcli auth login
bytedcli --json --site cn bytedoc search --keyword "demo_orders"
```

## BYTEDOC_AMBIGUOUS 处理

当 CLI 返回 `BYTEDOC_AMBIGUOUS` 时：

1. 从 `error.details.matches` 中提取候选表格
2. 向用户展示完整候选信息（PSM、backend、vregion）
3. 等待用户选择后，使用用户选定的 `--service`、`--backend` 和全局 `--vregion` 继续执行
4. 同一类 selector 错误禁止连续重试

```bash
# 示例：用户选择候选后，带上明确的 backend/vregion 重试
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.example_db" --backend classic
```

## Agent 规则

- 优先使用结构化 JSON 字段，不要优先依赖文本匹配。
- 重试时保留用户的全局 site / vRegion。
- backend 和 vregion 没有默认值；任何 selector 修正都必须来自用户选择或 CLI 返回的唯一候选。
- 不要把认证失败、歧义、路由无法解析、非法 role 或危险操作拦截当成随机 fallback 的邀请。
- `backend=volc` 的集合/查询链路走 DBW；失败时先看结构化错误类型。IAM 用户角色授权按 `access role list` / `permission get` / `user apply`；PSM/token 授权按 `access psm list/create --backend volc`。不要用其中一种授权链路证明另一种权限。
- `bytedoc shell --query 'db.getCollectionNames()'` 是库级只读命令，不需要 `--collection`，但它走 ExecuteSQL 权限；不要因为缺少 collection 就放弃这个复核路径，也不要把它当成 `collections` 的等价替代。
- 收到 `BYTEDOC_NON_JSON_RESPONSE` 或 `Failed to parse JSON: ... <html>` 时，停止改写 Mongo 查询语句；这类错误发生在 HTTP 响应解析阶段，说明还没拿到 DBW 的 JSON 执行结果。
- 收到 `BYTEDOC_UNSUPPORTED_SITE` 且 `details.site=us-ttp|eu-ttp` 时，说明 US-TTP / EU-TTP 不支持 DMS 数据查询；停止，不要继续尝试 dc、DMS endpoint、backend、vregion 或权限申请。
- `i18n-bd / Asia-SouthEastBD` 的 classic/cloud-native DMS 当前不支持；收到 `BYTEDOC_UNSUPPORTED_SITE` 时按 `agent_protocol.next_state=STOP` 报告区域限制，不要把它当作登录、权限或临时网络故障重试，也不要切换别名、dc、endpoint、backend 或 vregion。
- 收到 `BYTEDOC_DMS_ERROR` 或 `BYTEDOC_PLATFORM_SCHEMA_ERROR` 时，按 `agent_protocol.next_state=STOP` 停止；这类错误不能通过换 backend/vregion、猜集合/库名、申请权限，或改用 `shell` / `document` 变体继续同一 Mongo 操作来修复。
- 如果存在 `agent_protocol.next_state`，严格按它执行。
- 同一类 selector/role 错误最多允许执行一次用户确认后的修正命令；禁止连续切换 backend、site、deployMode 或 role 猜测。

## DO / DON'T

| 场景                              | ✅ DO                                                                                             | ❌ DON'T                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 命令返回 401                      | `bytedcli auth login` 后重试同一命令                                                              | 不要把它当 backend 错误换参数                                                               |
| BYTEDOC_AMBIGUOUS                 | 展示完整候选表，问用户                                                                            | 不要自己选一个重试                                                                          |
| UNSAFE_OPERATION_BLOCKED          | 停止，说明原因                                                                                    | 不要换路径、换 site、换命令绕过                                                             |
| ACCESS_REQUIRED                   | 执行 `setup_commands`                                                                             | 不要换 backend 或猜 role 重试                                                               |
| DBW_IAM_REQUIRED                  | 告知用户这是 ByteCloud IAM 权限问题，引导到 IAM 控制台                                            | 不要走 PSM 授权流程（`access psm create`）                                                  |
| US-TTP / EU-TTP UNSUPPORTED_SITE  | 告知用户对应 TTP 站点不支持 DMS 数据查询并停止                                                    | 不要猜 dc、改 endpoint、切 backend/vregion                                                  |
| Asia-SouthEastBD DMS              | 收到 UNSUPPORTED_SITE 后停止并报告该区域限制                                                      | 不要重试、猜 dc、改 endpoint、切 backend/vregion                                            |
| DMS_ERROR / PLATFORM_SCHEMA_ERROR | 报告 stage/endpoint/request_id/上游响应，并停止                                                   | 不要换 backend/vregion、猜库名、申请权限，或改用 `shell updateOne` / `document update` 变体 |
| NON_JSON_RESPONSE / `<html>`      | 查看 status、endpoint、HTML 摘要；刷新认证或确认本地 bytedcli 版本后重试同一条命令                | 不要把 `find()` 换成 `findOne()`，也不要切 backend                                          |
| Volc `collections` 返回 DBW 错误  | 保留 Volc selector，读取结构化错误；必要时用 `db.getCollectionNames()` 复核但注意 ExecuteSQL 权限 | 不要跳到 classic `access role list`                                                         |
| ROUTING_UNRESOLVED                | 询问 site/vregion                                                                                 | 不要回退到 cn                                                                               |
| INPUT_ERROR (role 非法)           | 展示合法枚举让用户选                                                                              | 不要自行换一个相似的 role                                                                   |

## 端到端示例：命令失败 → 恢复 → 成功

```bash
# 场景：Agent 执行命令后收到错误

# Step 1: 执行命令
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.example_db" --backend classic
# → 返回错误: { "code": "BYTEDOC_ACCESS_REQUIRED", "details": { "setup_commands": ["bytedcli --json --site cn --vregion China-North bytedoc access psm create --service example.bytedoc.example_db --backend classic --account example.caller.psm --operation apply --roles read --reason ..."] } }

# Step 2: Agent 遵循 setup_commands 原样执行或展示权限申请（dry-run）
# 不手写 access 命令，不把 role 改成猜测值
# → 返回 dry-run 预览，展示给用户确认

# Step 3: 用户确认后提交
# → 权限生效

# Step 4: 重试原始命令
bytedcli --json --site cn --vregion China-North bytedoc collections --service "example.bytedoc.example_db" --backend classic
# → 成功返回集合列表
```
