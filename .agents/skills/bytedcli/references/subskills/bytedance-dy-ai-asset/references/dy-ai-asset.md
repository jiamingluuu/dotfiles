# DY AI Asset API 与 CLI 命令映射

`bytedcli dy-ai-asset` 下的命令会按子命令访问以下 host：

- `search`：走抖音AI资产平台资源查询接口（`https://douyin-ai.bytedance.net/api/v1/ai_resource/resource/query`），依赖 ByteCloud JWT。
- `get-tool`：可能走两种链路：
  - 仅传 `--tool-key` 时，优先走 抖音AI平台网关 的 `mcp_server/query` / `tools/query_v2` 代理接口。
  - 否则走 `resource/query` 接口，再在返回的 `mcp_config` 中按 `tool_name` / `tool_key` 命中目标工具。
- `call`：走 抖音AI资产 的 `mcp/call` 接口（同上 host 与 path prefix）。

所有请求 header 包含：

```
x-jwt-token: <ByteCloud JWT>
UserToken:   <ByteCloud JWT>
ClientToken: <DOUYIN_AI_ASSET_CLIENT_TOKEN env，可空>
```

> 三个子命令都支持 `--env <env>`：传入时会额外写入 `x-use-ppe: 1` 和 `x-tt-env: <env>` 两个 header；不传时这两个 header 不会出现在请求中。

Gateway 代理链路使用 `x-skill-token` 作为身份；`Content-Type` 在 POST 时统一为 `application/json; charset=utf-8`。

## 命令 ↔ API 映射

| CLI 命令                                                                           | HTTP 方法 | 路径                                                                       |
| -------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------ |
| `bytedcli dy-ai-asset search [...]`                                              | `POST`  | `https://douyin-ai.bytedance.net/api/v1/ai_resource/resource/query`      |
| `bytedcli dy-ai-asset get-tool --resource-id <id> --tool-name <name>`            | `POST`  | `https://douyin-ai.bytedance.net/api/v1/ai_resource/resource/query`      |
| `bytedcli dy-ai-asset get-tool --tool-key <key>`（gateway 链路）                    | `GET`   | `.../api/ai_platform/gateway_ingress/proxy/mcp_server/query`             |
| `bytedcli dy-ai-asset get-tool --tool-key <key>`（gateway 链路 fallback）           | `GET`   | `.../api/ai_platform/gateway_ingress/proxy/tools/query_v2`               |
| `bytedcli dy-ai-asset call [...]`                                                | `POST`  | `https://douyin-ai.bytedance.net/api/v1/ai_resource/mcp/call`            |

## 请求

### search（resource/query）

请求 body 为 snake_case：

```json
{
  "resource_ids": ["asset-1", "asset-2"],
  "out_resource_ids": ["out-1"],
  "fuzzy_search": { "names_like": ["demo"] },
  "search_filter": {
    "types": [1, 2],
    "resource_platform": "example-platform",
    "resource_biz_line": "example-biz"
  }
}
```

响应结构：

```json
{
  "code": 0,
  "message": "success",
  "resource_list": [
    {
      "resource_id": "asset-1",
      "out_resource_id": "out-1",
      "name": "demo",
      "desc": "...",
      "type": 2,
      "mcp_config": [
        {
          "name": "tool-name",
          "key": "tool-key",
          "description": "...",
          "tool_input_schema": "...",
          "tool_response_schema": "..."
        }
      ],
      "skill_config": [{ "input_schema": "...", "output_schema": "..." }],
      "depended_resource_list": [
        { "resource_id": "...", "out_resource_id": "...", "name": "..." }
      ]
    }
  ]
}
```

`type` 取值：

| `type` | 含义        |
| ------ | --------- |
| 1      | Skill     |
| 2      | MCP Tool  |
| 3      | Knowledge |
| 4      | Memory    |

### get-tool（gateway 链路）

仅传 `--tool-key` 时，CLI 会优先调用：

```
GET .../proxy/mcp_server/query?tool_id=<tool-key>
```

若未命中，再 fallback：

```
GET .../proxy/tools/query_v2?id=<tool-key>&status=2&ignore_check_permission=true
```

请求会携带 `x-skill-token`；返回的工具元信息在 CLI 层归一化成 `DyAiAssetSimplifiedTool`。

### get-tool（resource/query 链路）

传 `--resource-id` 或 `--out-resource-id` 时，CLI 会先发 `resource/query`，然后从 `mcp_config` 中按 `tool_name` 或 `tool_key` 匹配。返回结构由 service 层规整：

```json
{
  "source": "resource_query",
  "code": 0,
  "message": "...",
  "tool": { "name": "...", "key": "...", "description": "...", "input_schema": "...", "output_schema": "..." },
  "resource_lookup": {
    "resource_found": true,
    "resource_type": 2,
    "available_tools": [{ "name": "...", "key": "...", "description": "..." }]
  }
}
```

### call（mcp/call）

请求 body 为 snake_case，例如：

```json
{
  "tool_key": "tool-key",
  "tool_arguments": "{\"param1\":\"value1\"}"
}
```

`resource_id` 走 query 参数：

```
POST .../mcp/call?resource_id=<resource-id>
```

响应：

```json
{ "code": 0, "message": "success", "data": "<tool result string>" }
```

`code != 0` 时表示失败，`message` 携带错误信息。

## 字段映射

### search / get-tool 的 MCP 工具字段

| CLI 字段          | API 原始字段              | 说明              |
| --------------- | -------------------- | --------------- |
| `name`          | `name`               | 工具名             |
| `key`           | `key`                | 工具唯一键           |
| `description`   | `description`        | 工具说明            |
| `input_schema`  | `tool_input_schema`  | 输入参数 schema（字符串） |
| `output_schema` | `tool_response_schema` | 输出 schema（字符串）  |

### search 的 Skill 字段

| CLI 字段          | API 原始字段                          | 说明        |
| --------------- | -------------------------------- | --------- |
| `name`          | `name`                           | Skill 名称  |
| `description`   | `desc`                           | Skill 描述  |
| `input_schema`  | `skill_config[0].input_schema`   | 输入 schema |
| `output_schema` | `skill_config[0].output_schema`  | 输出 schema |

### search 的依赖资源

| CLI 字段            | API 原始字段          | 说明                |
| ----------------- | ---------------- | ----------------- |
| `resource_id`     | `resource_id`    | 依赖资源 id           |
| `out_resource_id` | `out_resource_id` | 依赖资源外部 id         |
| `name`            | `name`           | 依赖资源名             |

## 错误码

| 错误                       | 场景                                                                                |
| ------------------------ | --------------------------------------------------------------------------------- |
| `DY_AI_ASSET_INPUT_ERROR`| 缺少 `--resource-id`、`--tool-name`/`--tool-key`、`--tool-arguments` 等必填项             |
| `DY_AI_ASSET_UNAUTHORIZED` | 未登录或 ByteCloud JWT 失效，且环境变量回退也不可用，需重新执行 `bytedcli auth login`                  |
| 业务非零 `code`             | 服务端返回 `{ code: !=0, message }`，CLI 文本模式会输出 `Error: <message>`，JSON 模式 `code` 字段透传 |
| HTTP 4xx / 5xx           | 走 `@/utils/http` 通用重试与错误结构，请检查内网访问与 ByteCloud JWT 是否过期                          |

## int64 ID 精度

`get-tool` gateway 链路的响应里若包含 16+ 位的 `id` / `server_id` / `tool_id`，CLI 会在解析前自动加引号，避免 JS Number 精度丢失（>2^53-1 会被四舍五入）。
