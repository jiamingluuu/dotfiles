# BBQ graphJson 最小约束

只在创建或修改 case/schema 的 `graph-json` 时读取。优先从 `case get` / `schema get` 获取现有图并做局部修改；不要因为字段可用就生成无关结构。

## 结构底线

- `graphJson` 必须是合法、非空且不超过 10 MB 的 JSON；顶层 `nodes` 必须非空，并包含 `edges` 数组。
- 节点 ID 必须唯一；边的 `from` / `to` 必须引用现有节点，且不能形成自环。
- 节点类型仅使用 `start`、`end`、`action`、`loop`、`condition`、`empty`、`group`、`schema`。
- `action`、`loop`、`condition`、`group`、`schema` 节点必须包含 `data`。
- action 类型仅使用 `echoAction`、`emptyAction`、`httpAction`、`pbAction`、`rpcAction`、`pushAction`、`roomPbAction`、`httpPbAction`。

## 事件和引用

- `hooks[].event_list` 只使用 `expression`、`func`、`script`、`sleep`。
- `request.event_list` 只使用 `expression`、`func`；每个事件的 `path` 必须命中非空 `request.original_content` 中已经存在的字段。
- `response.event_list` 只使用 `extract_var`；不要使用历史类型名 `function`。
- `dependent_params.value_point` 只使用 `responseBody`、`responseHeader`、`requestHeader`、`requestBody`；`value_type` 只使用 `JSONPath`、`JMESPath`，并提供非空表达式。
- `loop.target_ref`、`condition.branches[].target_ref`、`group.nodes[]` 使用字符串节点 ID，并指向真实节点。
- schema、setup、teardown 引用的 schema ID，以及 `func` / `script` 引用的 `func_id`，必须是平台查询所得的真实正整数。
- `pbAction` / `roomPbAction` 必须提供合法 command；使用 master IDL 时，command、IDL 文件、请求类型和响应类型必须与 `interface pb-command-mapping` 返回值一致。

## 提交前检查

- 确保存在清晰的 start → end 可达路径，并检查 condition、loop、group 与 edges 的关系；平台静态校验不一定覆盖这些运行语义。
- 确保表达式、JSONPath/JMESPath、请求体和变量提取在目标环境可执行。
- 提交 `case create/update` 或 `schema create/update` 后读取返回的校验问题；一次修复全部明确问题，再重试，避免逐条试错。
