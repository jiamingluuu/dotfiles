# bytedcli labelgpt config

配置命令用于管理 `bytedcli labelgpt` 的服务地址、区域、Space 和 PPE 环境。Agent 执行业务命令时不要切换默认 Space；目标命令或 mode 需要 Space 时，在该业务命令上显式传 `--space-id <SPACE_ID>`。

配置优先级从高到低：

```text
命令行 flag > 环境变量 > 本地配置 ./.labelgpt-cli/config.yaml > 全局配置 ~/.labelgpt-cli/config.yaml > 默认值
```

## config set

写入一个配置项。默认写入全局配置；传 `--local` 时写入当前目录的本地配置。

### 用法

```bash
bytedcli labelgpt config set <key> <value> [选项]
```

### 支持的 key

- `endpoint`：服务地址。未显式指定时，TT 站点（`SG`/`BOEI18N`/`I18N-DEV`）默认 `https://labelgpt.byteintl.net`，BD 站点（`Asia-SouthEastBD`/`I18N-BD`）默认 `https://labelgpt-i18n.byteintl.net`，其它区域默认 `https://labelgpt.bytedance.net`；显式配置的 endpoint 仍优先生效。
- `custom-region`：站点区域。
- `space-id`：目标 Space ID。
- `ppe-env`：PPE 环境。

### 示例

```bash
bytedcli labelgpt config set endpoint https://labelgpt.bytedance.net
bytedcli labelgpt config set custom-region CN
bytedcli labelgpt config set ppe-env ppe_jwt
```

### 参数说明

- `<key>`：配置 key，必填。
- `<value>`：配置值，必填。
- `--local`：写入 `./.labelgpt-cli/config.yaml`，否则写入 `~/.labelgpt-cli/config.yaml`。
- `--format <pretty|raw|json>`：输出格式。
- `-o <DIR>`：写入 JSON 文件。

### 输出

`raw/json` 输出字段：

- `key`：写入的配置 key。
- `value`：写入的配置值。
- `scope`：写入范围，`global` 或 `local`。

### 输出文件

- `-o <DIR>`：写入 `config_set_<key>.json`。

### 注意事项

- `space-id` 是可配置项，但 Agent 场景不要切换默认 Space；写操作前应确认目标 Space，并在业务命令中显式追加 `--space-id <SPACE_ID>`，避免资源创建到错误 Space。

## config show

展示当前解析后的配置值和来源。

### 用法

```bash
bytedcli labelgpt config show [选项]
```

### 示例

```bash
bytedcli labelgpt config show
bytedcli labelgpt config show --format raw
LABELGPT_CLI_SPACE_ID=<SPACE_ID> bytedcli labelgpt config show --format json
```

### 输出

`raw/json` 输出字段：

- `global_config_file`：全局配置文件路径。
- `local_config_file`：本地配置文件路径或 `(none)`。
- `values`：配置项值和来源。

### 输出文件

- `-o <DIR>`：写入 `config_show.json`。

## 全局参数与环境变量

| 全局参数 | 环境变量 | 说明 |
| --- | --- | --- |
| `--endpoint` | `LABELGPT_CLI_ENDPOINT` | 服务地址。未显式指定时按区域取默认值：TT 站点（`SG`/`BOEI18N`/`I18N-DEV`）为 `https://labelgpt.byteintl.net`，BD 站点（`Asia-SouthEastBD`/`I18N-BD`）为 `https://labelgpt-i18n.byteintl.net`，其它为 `https://labelgpt.bytedance.net`。 |
| `--custom-region` | `LABELGPT_CLI_CUSTOM_REGION` | 站点区域。 |
| `--space-id` | `LABELGPT_CLI_SPACE_ID` | Space ID。 |
| `--byted-jwt-token` | `LABELGPT_CLI_BYTED_JWT_TOKEN` | 直接指定 ByteDance JWT。 |
| `--ppe-env` | `LABELGPT_CLI_PPE_ENV` | PPE 环境。 |
| `--format` | - | 输出格式：`pretty`、`raw`、`json`。 |
| `-o, --output` | - | 输出目录。 |
| `--timeout` | - | HTTP 请求超时，默认 `30s`。 |
| `--debug` | - | 调试日志写 stderr。 |
| `--trace` | - | 打印请求追踪 ID。 |

## Schema 查询索引

```bash
bytedcli labelgpt schema config set --format raw
bytedcli labelgpt schema config show --format raw
```
