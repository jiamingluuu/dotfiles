# bytedcli labelgpt core

核心命令用于查看版本、发现命令列表、查询单个命令的输入输出契约。AI Agent 调用前优先使用 `commands` 和 `schema` 做能力发现。

## 快速导航

- [version](#version)：查看 CLI 版本。
- [commands](#commands)：发现当前可用命令。
- [schema](#schema)：查询叶子命令的输入输出契约。
- [Agent 使用建议](#agent-使用建议)：按 schema-first 顺序调用。
- [Schema 查询索引](#schema-查询索引)：查询核心命令自身的契约。

## version

打印 CLI 版本。

### 用法

```bash
bytedcli labelgpt version [选项]
bytedcli labelgpt --version
```

### 示例

```bash
bytedcli labelgpt version
bytedcli labelgpt version --format raw
```

### 输出

`raw/json` 输出字段：

- `version`：CLI 版本字符串。

### 输出文件

- `-o <DIR>`：写入 `version.json`。

## commands

列出所有可用命令，并标记是否已注册 schema。

### 用法

```bash
bytedcli labelgpt commands [选项]
```

### 示例

```bash
bytedcli labelgpt commands --format raw
bytedcli labelgpt commands --format json -o ./out
```

### 输出

`raw/json` 输出字段：

- `commands`：命令摘要数组。

每个命令摘要包含：

- `name`：命令名称。
- `use`：完整用法。
- `short`：简短说明。
- `path`：命令路径字符串，例如 `plugin debug`。
- `aliases`：别名数组。
- `hidden`：是否隐藏。
- `has_schema`：是否有注册 schema。

### 输出文件

- `-o <DIR>`：写入 `commands.json`。

## schema

显示某个命令的机器可读输入和输出 schema。

### 用法

```bash
bytedcli labelgpt schema <command-path> [选项]
```

`<command-path>` 可以由多个参数组成，例如 `plugin debug`。

### 示例

```bash
bytedcli labelgpt schema plugin debug --format raw
bytedcli labelgpt schema agent workflow add-node --format json
bytedcli labelgpt schema config show
```

### 参数说明

- `<command-path>`：命令路径，必填。例如 `plugin debug`、`agent workflow add-node`、`config show`。
- `--format`：输出格式，建议 Agent 使用 `raw`。
- `-o <DIR>`：写入 schema JSON 文件。

### 输出

`raw/json` 输出字段：

- `schema_version`：schema 版本，当前为 `2`。
- `command`：命令路径。
- `path`：canonical 命令路径。
- `description`：命令描述。
- `aliases`：命令 alias 数组，非 canonical path。
- `global_inputs`：命令级全局参数字段定义数组，例如 `space-id`、`format`、`output`、`timeout`。多模式命令应优先看 `modes[].global_inputs`，因为 `space-id` 是否必填可能按 mode 不同。
- `modes`：模式数组；普通命令通常只有 `default`，多模式命令如 `agent task`、`dataset status` 会拆分为多个模式。
- `examples`：示例命令数组。
- `notes`：补充说明数组。

`modes[]` 字段包含：

- `name`：字段名。
- `global_inputs`：该 mode 下全局参数是否必填的最终契约；判断 `space-id` 是否需要用户提供时以这里为准。
- `description`：字段说明。
- `input_schema`：命令输入的 JSON Schema。
- `output_schema`：命令输出的 JSON Schema，是该命令返回结构的权威契约。字段名以这里为准，
  不要凭字段含义猜测。例如 `dataset list` 的返回顶层 key 是 `datasets`（对象数组），不是
  `dataset_list`；按错误的 key 解析会读到空数组，据此得出的结论也会是错的。
- `constraints`：互斥、联动等补充约束。
- `examples`：模式级示例。
- `notes`：模式级补充说明。

### 输出文件

- `-o <DIR>`：写入 `schema_<command-path>.json`；文件名会清理路径中的危险字符，命令路径中的空格会保留。

## Agent 使用建议

处理未知需求时，推荐顺序：

```bash
bytedcli labelgpt commands --format raw
bytedcli labelgpt schema <command-path> --format raw
bytedcli labelgpt <command-path> ... --format raw
```

不要依赖帮助文本解析输出字段；输出契约以 `schema` 命令的 `output_schema` 为准。例如先查
`bytedcli labelgpt schema dataset list --format raw`，其 `output_schema` 会明确顶层返回
`datasets`（对象数组）、`total`、`page_num`、`page_size`、`space_id`，再据此解析实际返回，
避免误用 `dataset_list` 等不存在的 key。

## Schema 查询索引

```bash
bytedcli labelgpt schema version --format raw
bytedcli labelgpt schema commands --format raw
bytedcli labelgpt schema schema --format raw
```
