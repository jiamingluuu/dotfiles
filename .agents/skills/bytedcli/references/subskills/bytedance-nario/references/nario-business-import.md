# Nario 业务表格导入参考

当用户希望从飞书表格、CSV 或 JSON 表格批量创建或更新 Nario 模板/场景时，使用本参考资料。本文件描述业务工作流层；单端点 OpenAPI 的基础说明保留在 `nario-openapi.md`。

## 使用场景

- 用户提供包含 Nario 模板/场景信息的飞书表格或 CSV。
- 用户要求批量创建/更新模板或场景，但不了解原始 OpenAPI payload。
- 用户使用业务术语描述模板绑定特征、场景规则或推荐配置。

## 安全规则

- 除非用户明确要求使用经过检查的输入执行真实操作，否则务必先运行 `--dry-run`。
- 真实写入必须使用 `--yes`。
- 业务导入按操作 ID 执行。如果真实执行失败，bytedcli 会记录已完成阶段和失败阶段，并在执行后续操作前停止。
- `--max-rows <n>` 是可选的显式保护参数，默认没有硬性行数上限。

## 模板创建表格

```csv
操作ID,模板名称,空间ID,PSM,接口,协议,优先级,特征名,路径,来源,路径类型,是否启用
T1,sample-template,2,example.psm,GetDemo,http,P2,user_id,user_id,请求,Body,是
T1,,,,,,,commit,commit,请求,Query,
```

`操作ID` 将多个特征行归入同一个模板创建工作流。bytedcli 先创建基础模板，再使用新建模板 ID 更新特征。

默认值：

| 列       | 默认值                                       |
| -------- | -------------------------------------------- |
| 来源     | 请求，映射为 `req`                           |
| 路径类型 | `Body`                                       |
| 优先级   | 省略时由 bytedcli 填入安全默认值             |
| 创建人   | 存在缓存的 bytedcli 登录用户名时使用该用户名 |

## 模板更新表格

```csv
操作ID,目标模板ID,目标模板名称,PSM,接口,新模板名称,优先级,是否启用,进入度量白名单,特征动作,特征ID,特征名,路径,来源,路径类型,推荐失败时忽略,定制推荐配置JSON（或描述）
TU1,3000000,,,,sample-template-v2,P1,是,是,更新,,user_id,user_id,请求,Body,,
TU1,,,,,,,,,新增,,commit,commit,请求,Query,是,
TU1,,,,,,,,,删除,3000001,legacy_feature,,,,,
```

定位特征时优先使用特征 ID，其次使用特征名称。支持的特征动作为新增、更新、删除。

省略 `更新人` 时，如果存在缓存的 bytedcli 登录用户名，bytedcli 使用该用户名。

`定制推荐配置JSON（或描述）` 映射为 `single_recommend_config_model`。该列会整体替换特征推荐配置，而不是按字段合并。单元格为空表示不更新推荐配置。

常见推荐配置示例：

```json
{
  "not_use_basic_equal_strategy": true,
  "default_condition_list": [
    { "default_attribute": "$compare_value", "default_condition": "$eq", "ignore_value": true },
    {
      "default_attribute": "$exists",
      "default_condition": "$eq",
      "default_value_list": "[\"false\"]"
    }
  ],
  "skip_recommend_when_not_hit": false,
  "recommend_for_too_large": false
}
```

```json
{
  "not_use_basic_equal_strategy": true,
  "default_condition_list": [
    { "default_attribute": "$compare_value", "default_condition": "$eq", "ignore_value": true }
  ],
  "skip_recommend_when_not_hit": true,
  "recommend_for_too_large": false
}
```

当推荐规则要匹配具体值（`$compare_value` + `$eq`/`$ne`，而非 `ignore_value`）时，`default_value_list` 同样要走双重 JSON 序列化。例如特征 `code`（数字）等于 `0` 或不等于 `0`，特征 `message`（字符串）等于 `success` 或不等于 `success`：

```json
{
  "not_use_basic_equal_strategy": true,
  "default_condition_list": [
    {
      "default_attribute": "$compare_value",
      "default_condition": "$eq",
      "default_value_list": "[\"0\"]"
    },
    {
      "default_attribute": "$compare_value",
      "default_condition": "$ne",
      "default_value_list": "[\"0\"]"
    },
    {
      "default_attribute": "$compare_value",
      "default_condition": "$eq",
      "default_value_list": "[\"\\\"success\\\"\"]"
    },
    {
      "default_attribute": "$compare_value",
      "default_condition": "$ne",
      "default_value_list": "[\"\\\"success\\\"\"]"
    }
  ],
  "skip_recommend_when_not_hit": false,
  "recommend_for_too_large": false
}
```

`default_value_list` 是字符串字段，不能写成数组 `[0]` 或 `["success"]`；数字 `0` 的 wire 值是 `"[\"0\"]"`，字符串 `success` 的 wire 值是 `"[\"\\\"success\\\"\"]"`。推导见下方「规则值」一节的类型对照表。

## 场景创建表格

```csv
操作ID,场景名称,模板ID,空间ID,模板名称,优先级,特征名,比较属性,比较条件,比较值,比较值类型（可作为约束补充）
S1,sample-scene,3000000,2,,P2,user_id,比较值,等于,123,数字
S1,,,,,,commit,比较值,等于,main,字符串
```

场景的 PSM 和 method 来自模板。业务导入默认将场景来源设为外部导入，即 `SceneSourceOuter = 8`。

省略 `创建人` 时，如果存在缓存的 bytedcli 登录用户名，bytedcli 使用该用户名。

## 场景更新表格

```csv
操作ID,目标场景ID,目标场景名称,模板ID,新场景名称,优先级,规则动作,特征名,比较属性,比较条件,比较值,比较值类型（可作为约束补充）
SU1,220000000,,3000000,sample-scene-v2,P1,更新,user_id,比较值,等于,456,数字
SU1,,,,,,新增,commit,比较值,等于,main,字符串
```

规则更新在内部需要后端规则 ID，但用户通常不知道该 ID。bytedcli 会尽可能使用特征/规则列定位；无法将 Nario 建模信息唯一映射到规则时会快速失败。

省略 `更新人` 时，如果存在缓存的 bytedcli 登录用户名，bytedcli 使用该用户名。

## 规则值

Nario 后端对规则值使用 `TransMeasureCheckValueToFe` 序列化：**先对每个实际值执行一次 JSON 字符串化，再对得到的字符串列表整体执行一次 JSON 字符串化**。这一规则同时适用于场景的 `check_value_list` 和模板推荐配置中的 `default_value_list`，两次 stringify 缺一不可。

可以用 `bytedcli nario rule check-value encode --type <type> --value <v>` 生成一次编码后的 `check_value_list`（中间数组形态）；加 `--wire` 可直接输出 `default_value_list` 需要的双重 stringify 后的 wire 字符串，可直接粘贴进推荐配置 JSON。

```bash
# 数字 0 -> default_value_list: "[\"0\"]"
bytedcli nario rule check-value encode --type number --value 0 --wire

# 字符串 success -> default_value_list: "[\"\\\"success\\\"\"]"
bytedcli nario rule check-value encode --type string --value success --wire

# 布尔 false -> default_value_list: "[\"false\"]"
bytedcli nario rule check-value encode --type boolean --value false --wire
```

类型对照表（以单值为例）：

| 实际值  | 类型    | 一次 stringify（每个元素） | 再 stringify 数组（wire `default_value_list`） |
| ------- | ------- | -------------------------- | ---------------------------------------------- |
| `0`     | number  | `"0"`                      | `"[\"0\"]"`                                    |
| `123`   | number  | `"123"`                    | `"[\"123\"]"`                                  |
| `success` | string | `"\"success\""`            | `"[\"\\\"success\\\"\"]"`                      |
| `""`（空字符串） | string | `"\"\""`             | `"[\"\\\"\\\"\"]"`                             |
| `true`  | boolean | `"true"`                   | `"[\"true\"]"`                                 |
| `false` | boolean | `"false"`                  | `"[\"false\"]"`                                |

多值（如 `$in`）时，把每个实际值分别 stringify 成字符串后放进数组，再整体 stringify 一次。例如实际值为 `[0, 1]`：每个元素 stringify 为 `"0"`、`"1"`，组成 `["0","1"]`，再整体 stringify 得到 `"[\"0\",\"1\"]"`。

常见错误：

- 只对整体做一次 `JSON.stringify([0])` 得到 `"[0]"`，少了一层元素 stringify，写入后实际匹配不到数字 `0`。
- 把字符串 `"success"` 写成 `"[\"success\"]"`（元素未 stringify），正确值是 `"[\"\\\"success\\\"\"]"`。
- 在 payload 中把 `default_value_list` 写成 JSON 数组 `[0]` 或 `["success"]`；该字段是**字符串**，不是数组。
- 依赖服务端自动补齐缺失的一层序列化：服务端对一半情况会容错、一半会原样存下错误值，表现不一致，必须按双重 stringify 后的值下发。

业务表格中规则值的简写：

| 用户单元格 | 含义                   |
| ---------- | ---------------------- |
| `""`       | 等于空字符串           |
| `!""`      | 不等于空字符串         |
| `null`     | 等于 null              |
| `!null`    | 不等于 null            |
| `exist`    | 字段存在               |
| 空单元格   | 字段不存在             |
| `!=foo`    | 不等于 `foo`           |
| `"123"`    | 字符串 `123`，不是数字 |

## 命令

```bash
# 可选：将可复用的 Nario 令牌保存到本地。bytedcli 不会打印令牌值。
bytedcli nario auth token set --authorization-token <token>

# 打印模板创建业务表格示例。
bytedcli nario import example get --operation template-create --format csv

# 预览飞书表格导入。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario import sheet execute \
  --operation template-create \
  --sheet-url <sheet-url> \
  --dry-run

# 检查 dry-run 计划后执行。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario import file execute \
  --operation scene-create \
  --file ./scene-create.csv \
  --yes
```
