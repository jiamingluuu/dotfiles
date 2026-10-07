# Nario 打标参考

当用户需要检查流量能否被 Nario 打标、是否命中模板/场景，或模板/场景表达式调试行为时，使用本参考资料。

## 命令映射

| 目标                             | 命令                                                                                                                                                           |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 对完整流量 payload 打标但不写入  | `bytedcli --json nario tagging flow tag --payload-file ./flow.json --dry-run --need-detail`                                                                    |
| 按 PID 为已存储流量打标但不写入  | `bytedcli --json nario tagging flow tag --psm example.psm --pid sample-pid --flow-collection flow_tagged --dry-run`                                            |
| 列出 PID 命中的模板/场景         | `bytedcli --json nario tagging flow hit --psm example.psm --pid sample-pid`                                                                                    |
| 列出带 Nario 链接的命中明细行    | `bytedcli --json nario tagging flow hit --psm example.psm --pid sample-pid --view detail`                                                                      |
| 检查后写入打标结果               | `bytedcli nario tagging flow tag --payload-file ./flow.json --yes`                                                                                             |
| 根据数据源执行单场景调试         | `bytedcli --json nario tagging scene-debug execute --psm example.psm --pid sample-pid --template-id 3000001 --scene-id 2200001 --build-from-sources`           |
| 检查自动构建的单场景调试 payload | `bytedcli --json nario tagging scene-debug execute --psm example.psm --pid sample-pid --template-id 3000001 --scene-id 2200001 --build-from-sources --dry-run` |
| 调试模板匹配                     | `bytedcli --json nario tagging debug execute --kind scene-template --payload-file ./debug.json --dry-run`                                                      |
| 调试场景匹配                     | `bytedcli --json nario tagging debug execute --kind psm-scene --payload-file ./debug.json --dry-run`                                                           |
| 调试模板表达式匹配               | `bytedcli --json nario tagging debug execute --kind expression-scene-template --payload-file ./debug.json --dry-run`                                           |
| 调试场景表达式匹配               | `bytedcli --json nario tagging debug execute --kind expression-psm-scene --payload-file ./debug.json --dry-run`                                                |

## 安全规则与默认值

- `flow tag` 接受完整流量 payload，或已存储流量选择条件（`--psm`、`--pid`、`--flow-collection`）。后端默认为 `not_write=true`；仅当用户明确要求写入打标结果时使用 `--yes`。
- `--dry-run` 会打印计划请求，仍是建议的第一步。
- 后端支持时，`--need-detail` 会要求返回命中明细。诊断时使用该参数。
- `flow hit` 是面向用户的“这个 PID 命中了哪些模板/场景”快捷入口。省略 `--flow-collection` 时，CLI 先尝试 `flow_temporary`；仅当缺少已存储流量时才回退到 `flow_tagged`。
- `flow hit` 默认为 `--view summary`，返回紧凑的 `{ templateName: [sceneName, ...] }` 视图。仅当用户要求表格行或链接时使用 `--view detail`；后端返回足够标识时，明细行包含空间、模板 URL 和场景 URL。
- `--ignore-business <id>` 可重复传入或以逗号分隔。仅当用户希望从命中分析中排除已知空间时使用。
- 最终回答中不要粘贴或打印原始生产流量数据。应汇总 PSM、method、PID、命中数和后续操作。

## 流量打标 payload

`nario tagging flow tag` 接受经过检查的 JSON 对象。payload 通常表示已捕获的 FTF/Nova 流量，常见内容包括服务、method、协议、请求/响应、outbound 和身份字段。CLI 仅检查 payload 是否为 JSON 对象；字段语义归 Nario consumer 后端所有。

推荐工作流：

1. 将已捕获流量放入 `./flow.json`。
2. 运行 `bytedcli --json nario tagging flow tag --payload-file ./flow.json --dry-run --need-detail`。
3. 如果 dry-run 计划正确，移除 `--dry-run` 执行只读打标计算。除非传入 `--yes`，否则仍保持 `not_write=true`。
4. 检查 `summary.hitTemplateCount`、`summary.hitSceneCount`、`summary.isTagged` 和 `result.data.hit_detail`。

## 已存储流量打标输入

| 参数                      | 含义                                           |
| ------------------------- | ---------------------------------------------- |
| `--psm`                   | 已存储流量所属的 PSM。                         |
| `--pid`                   | 流量 PID。                                     |
| `--flow-collection`       | 后端流量集合名称，例如 `flow_tagged`。         |
| `--only-modeling`         | 后端支持时，仅执行建模打标。                   |
| `--use-translated <bool>` | 后端是否使用翻译后的流量字段，默认为翻译模式。 |

## PID 命中列表工作流

当用户从 PID 出发询问匹配的模板/场景时，使用 `flow hit`。该命令执行只读打标并返回：

| 输出字段                   | 含义                                                           |
| -------------------------- | -------------------------------------------------------------- |
| `collection`               | 产生结果的集合。                                               |
| `attemptedCollections`     | 按顺序尝试的集合。                                             |
| `summary.hitTemplateCount` | `hit_detail` 中的模板条目数。                                  |
| `summary.hitSceneCount`    | 匹配模板下的场景数。                                           |
| `hits[]`                   | 包含模板 ID/名称和场景 ID/名称的扁平化命中明细。               |
| `hitSummary`               | 用于用户回答的紧凑 `{ templateName: [sceneName, ...] }` 映射。 |
| `hitDetails[]`             | 在 `--view detail` 中出现；包含 Nario 链接的扁平化命中明细。   |

普通用户回答使用 `hitSummary`。详细回答将 `hitDetails[]` 渲染为表格；原始 `result.data.hit_detail` 仅用于后端调试。

## 单场景调试工作流

当用户询问某个目标场景是否会命中流量时，使用 `tagging scene-debug execute`。该能力有意与全流量打标分离，因为已禁用模板或超大规模全流量扫描可能掩盖聚焦结果。

1. 如果用户提供 PSM、PID、模板 ID 和场景 ID，直接运行命令；未提供 payload 时，CLI 默认使用从数据源构建模式。它会加载 FTF 流量详情和 Nario 模板/场景元数据，并调用聚焦的后端调试端点。
2. 生成的 payload 需要检查时添加 `--dry-run`。payload 包含 FTF 流量请求/响应、`scene_meta`、`psm_scene`、特征列表和 `log_id`。
3. 如果缺少 FTF 历史流量且未指定 `--flow-type`，CLI 会回退到场景流量。
4. 仅对所有者检查过的自定义 payload，或自动构建的数据源不完整时，使用 `--payload-file ./psm_scene_debug.json`。

## 调试类型

| 类型                        | 端点用途                  |
| --------------------------- | ------------------------- |
| `scene-template`            | 调试场景模板匹配。        |
| `psm-scene`                 | 调试具体 PSM 场景匹配。   |
| `expression-scene-template` | 调试场景模板表达式匹配。  |
| `expression-psm-scene`      | 调试 PSM 场景表达式匹配。 |

用户已有聚焦的模板/场景表达式 payload 时使用调试命令。用户从已捕获流量出发、希望了解 Nario 会打标什么时，使用流量打标命令。
