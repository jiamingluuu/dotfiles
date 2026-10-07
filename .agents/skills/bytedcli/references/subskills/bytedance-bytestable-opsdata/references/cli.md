# CLI 契约

所有例子使用占位数据集/路径，须先 `dataset list` 和 `dataset get`。
结构化调用前缀：`bytedcli --as user --json bytestable opsdata`。子命令选项全部为命名参数。

| 子命令            | 必填项                           | 可选项与边界                                                              |
| ----------------- | -------------------------------- | ------------------------------------------------------------------------- |
| `tools list`      | 无                               | 查看部署工具及 inputSchema；不需要应用 Key                                |
| `dataset list`    | 无                               | 返回当前应用可访问的 Markdown 目录                                        |
| `dataset get`     | `--name NAME`                    | 返回当前有效检索契约的 Markdown 详情                                      |
| `graphql query`   | `--dataset NAME --query GRAPHQL` | 无通用 `--limit`，分页写在契约允许的查询参数中                            |
| `rag search`      | `--dataset NAME --query TEXT`    | `--filters JSON_OBJECT` 或 `--filters-file PATH`；`--limit` 默认 10，1–50 |
| `document search` | `--paths PATH... --query TEXT`   | `--limit` 默认 10，1–50                                                   |
| `document list`   | `--paths PATH...`                | `--recursive`；`--limit` 默认 50，1–200，每个路径分别限制                 |
| `document grep`   | `--paths PATH... --pattern TEXT` | `--ignore-case`；`--limit` 默认 10，1–100；先检查 list 范围               |
| `document read`   | `--paths PATH...`                | `--offset` 默认 1（行号）；`--limit` 默认 200，1–500，-1 全文             |

read 最多 3 个路径，其他 document 命令最多 10 个。路径格式为 `数据集 en_name/服务端返回的相对路径`，数据集根就是 en_name。不接受绝对路径、`..`、提供方 URI 或飞书 URL；不能从文档标题/URL 猜虚拟路径。

数据集 Schema 中的 `document_handle` 等字段描述 MCP 能力模型；CLI 调用 OpenViking 时以本页命令的 `--paths` 参数为准，只传数据集根或服务端 search/list/grep 返回的虚拟路径，不直接传 MCP 模板字段。

所有叶子命令接受 `--env`（默认 prod）、`--psm`（默认配置的运维 MCP）、`--timeout-ms`（默认 60000，1–600000）、`--api-key-file PATH`。站点是全局 `--site`，支持 cn、boe、i18n-bd、i18n-tt；i18n 归一到 i18n-bd。不要为了排障盲目变更这些参数。

## 接口如何配合

```text
dataset list
  -> dataset get（只读准备查询的 1–3 个候选）
       -> graphql query                    精确结构化事实
       -> rag search                       语义知识片段
       -> document search -> document read 未知位置的原文
       -> document list -> grep -> read    已知范围的精确文本
```

- `dataset list` 负责找合适的数据源和初步能力，不提供最终查询契约。
- `record_set` 适合结构化事实，尤其在关注新鲜度时优先考虑；它也可能包含历史事件、审计记录或快照，不能只凭类型判断为当前数据。文档型数据集通常沉淀经验、流程和知识。类型只用于初筛，最终以数据集描述、字段、时效、覆盖范围和详情能力为准。
- `dataset get` 是后续参数的唯一依据。GraphQL 字段和参数、RAG filters、OpenViking 路径与示例都从这里取得。
- 一次证据需求先走一条最匹配的查询链路。只有结果不足、缺正文或需要交叉验证时再补另一条，避免重复调用。
- 多数据集不能在接口内直接 join。分别查询后，只按双方都有的稳定标识关联，例如 PSM、环境、事件 ID、文档路径或错误码。
- `tools list` 用于已部署命令缺失、input schema 不匹配等兼容性排障；不要把它当数据集目录。

`dataset list/get` 固定向 MCP 请求 `response_format=markdown`。普通文本模式直接输出 Markdown；全局 `--json` 模式保留标准 JSON envelope，其中 `data` 是 Markdown 字符串。例如：

```bash
bytedcli --as user bytestable opsdata dataset get --name '<dataset_en_name_from_dataset_list>'
bytedcli --as user --json bytestable opsdata dataset get --name '<dataset_en_name_from_dataset_list>'
```

## 返回结构

全局 `--json` 模式的标准输出为 `{status, data, error, context}` JSON；普通文本模式下的 `dataset list/get` 默认直接输出 Markdown。stderr 与 stdout 分开处理，不能混合解析。

- `dataset list` 的 Markdown 包含应用、数据空间、数据集标识、名称、检索能力与说明。目录中的检索能力是提示，最终以 `dataset get` 为准。
- `dataset get` 的 Markdown 包含数据集元信息、有效检索契约、字段、关联关系与查询示例。
- GraphQL 业务 `data` 包含内部 `data`（root 到记录）、`errors`、`stats`、`record_references` 和可能的 `log_id`。外层 success 不排除部分失败。
- 文档 list 通常为 `data.directories[].entries[]`；read 为 `data.documents[]`。每篇 read 结果关注 `path/content/source_url/offset/returned_lines/has_more/next_offset`。
- 搜索结果的字段随提供方变化。先查看真实结构，再提取正文与出处；不要为兼容性而把未知 JSON 全部当成正文。

命令不识别时先 `bytedcli bytestable opsdata <子命令> --help`；部署差异用 `tools list` 检查工具存在与 inputSchema。CLI 不提供通用任意 MCP 工具调用入口；发现新工具需要扩展 CLI，不能臆造子命令。

## 个人访问

- `bytedcli --as user --json bytestable opsdata auth status`：只读检查注册状态、本地凭证状态、当前模式和已启用数据集数；不证明 MCP 可达。
- `bytedcli --as user --json bytestable opsdata auth login`：幂等开通并本地保存个人凭证，返回状态但不返回 Key；保留既有数据集选择。
- login 后用 `dataset list` 验证真实检索；公开数据集的个人选择在平台「接入应用」管理，管理员默认列表仅影响首次开通。
