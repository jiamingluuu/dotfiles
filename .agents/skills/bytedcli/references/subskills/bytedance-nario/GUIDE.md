---
name: bytedance-nario
description: "通过 bytedcli 查询 Nario 场景覆盖率与度量报告、定位未命中场景，或管理空间/模板/场景时使用。用户提供 FTF task URL/ID、Nario 度量任务 ID，询问覆盖率、低覆盖分布、未命中场景、模板统计或场景建模时使用；用户要求一键刷新模板/接口下的推荐场景、初始化推荐场景、基于存量流量重新打标时同样使用；优先使用专用命令，raw OpenAPI 仅作为白名单兜底。"
---

# bytedcli Nario

## 使用场景

当用户希望通过 bytedcli 使用 Nario 流量场景管理与计算能力时，使用本 skill。按用户任务选择专用命令，不要先拆成原始端点：

- 当用户提供 FTF task URL/ID，或询问任务场景覆盖率、低覆盖分布、未命中场景时，查询 Nario 度量报告和场景明细。
- 列出空间、模板或场景。
- 根据 ID 获取空间、模板或场景详情。
- 获取空间列表、模板特征聚合/统计信息或未覆盖场景 ID。
- 使用经过检查的 OpenAPI JSON payload 或 schema 驱动的语义字段创建或更新空间，以及创建、更新或删除模板和场景。
- 构建模板/场景创建与更新 payload，并从飞书表格或本地 CSV/JSON 文件导入 Nario 建模信息。
- 当用户希望从表格批量创建或更新模板/场景、但不想手写 OpenAPI payload 时，使用业务表格工作流导入。
- 当用户需要场景覆盖率或命中统计时，创建并检查 Nario 度量任务和报告。
- 当用户需要检查流量是否命中模板/场景或排查覆盖率偏低原因时，执行安全的流量打标/调试请求。
- 当用户要求刷新模板下的场景、初始化推荐场景、重新打标某个模板或接口时，基于存量场景流量一键刷新推荐场景。
- 将已存储的流量 PID 解析为命中的模板/场景，规划单场景调试请求，并将 FTF 任务 URL 桥接到 Nario 度量报告。
- 在强提醒下刷新模板覆盖率，或编码规则 `check_value_list` 值。

## 覆盖报告路由

| 用户输入或目标                          | 首选路径                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------------------ |
| FTF task URL 或 ID                      | `nario measure report get --url ...` 或 `--ftf-task-id ...`                                      |
| Nario 度量任务 ID                       | `nario measure report get --task-id ...`                                                         |
| 报告尚未进入终态                        | 使用已解析的 Nario 任务 ID 运行 `nario measure report poll --task-id ...`                        |
| 定位低覆盖 method、模板或未命中场景样例 | 使用 `resolvedTask.taskId` 运行 `nario measure report scene-detail --summary --task-id ...`      |
| 获取完整精确未命中场景清单              | 分页运行非汇总 `scene-detail`，读取全部页面并筛选命中流量计数为 `0` 的场景行                     |
| 查看某个模板的当前统计或全局未覆盖场景  | `nario template statistics get` 或 `nario scene list --uncovered`，不要解释为某次任务的 hit/miss |
| 重新计算模板覆盖率统计                  | `nario template coverage refresh --dry-run`；这是异步写操作，不是覆盖报告查询                    |

- FTF task ID 与 Nario 度量任务 ID 是不同标识。通过 FTF 路由时，以 `report get` 返回的 `resolvedTask.taskId` 作为后续 `poll` 和 `scene-detail` 的 `--task-id`。
- 任务级覆盖率和精确未命中场景以 Nario `measure report` / 非汇总 `scene-detail` 为准。`scene-detail --summary` 只返回 Top 低覆盖分组和每组最多 5 个未覆盖样例；不能把样例并集表述为完整清单。FTF task/report 的 method 流量分布只能作为辅助证据，不能替代 Nario 场景明细或用于猜测未命中场景。
- 报告必须区分总体场景覆盖率、hit/miss 数、低覆盖 method/模板和精确未命中场景 ID；没有场景明细证据时明确说明缺口，不根据场景创建时间、规则形态或全局流量标记做启发式认定。
- 完整工作流和报告口径见 `references/nario-case-measure-report-coverage.md`；字段与筛选说明见 `references/nario-measure.md`。

## 安全规则

- 绝不打印或回显 Nario OpenAPI 授权令牌。优先使用 `NARIO_OPENAPI_AUTHORIZATION_TOKEN`，或显式运行 `bytedcli nario auth token set --authorization-token <token>`；不要优先使用一次性的 `--authorization-token` 参数。
- 仅当用户明确要求保存令牌时才持久化。Nario 本地令牌文件使用私有权限，命令输出绝不能包含令牌值。
- 写命令必须使用 `--dry-run` 或 `--yes`。
- 创建、更新和删除操作应先运行 `--dry-run`；仅当用户已提供经过检查的请求 payload 并明确要求执行时，才可跳过此步骤。
- `nario raw execute` 仅用于没有专用命令、且用户明确需要白名单内 manager 端点的兜底请求。覆盖报告、未命中场景、模板/场景查询和写入均优先使用对应专用命令；不要猜测路径、传入任意 URL 或非 Nario 路径。
- `nario template coverage refresh` 可能长时间运行，并会影响模板覆盖率统计。务必先 dry-run，并避免重复调用。
- `nario template flush execute` 是重操作：传 `--template-id` 时会**先清除该模板下的推荐场景**再基于存量流量重建。务必先 `--dry-run` 检查前置校验报告，确认后才用 `--yes`。后端为异步任务，返回成功只代表已受理，须用 `nario template flush status` 查询是否结束，不要重复触发。刷新锁的粒度是 `psm+method` 接口维度而非模板，TTL 24 小时。仅当用户明确要求绕过前置校验时才传 `--skip-preflight`。完整语义见 `references/nario-flush.md`。
- `nario tagging flow tag` 接受经过检查的流量 payload，或 `--psm`/`--pid`/`--flow-collection`，默认使用 `not_write=true`。仅当用户明确要求写入打标结果时才传入 `--yes`。
- 对于“这个 PID 命中了哪些模板/场景”一类问题，优先使用 `nario tagging flow hit`。集合未知时，命令会先尝试 `flow_temporary`，再尝试 `flow_tagged`。
- 单场景调试使用 `nario tagging scene-debug execute`。没有经过检查的 payload 时，运行 `--dry-run` 展示缺失输入计划，不要猜测字段。
- Nario 度量任务创建是异步操作。只创建一次，随后使用 report get/poll，不要重复创建任务。
- Nario 命令树有意不暴露 `feature list`、FTF 1.0 caseset、FTF translate 和已废弃的场景流量查询 API。
- 文档和测试使用 `example.psm`、`GetDemo`、`sample-*` 等示例值；示例中不得出现真实服务名或真实令牌。

## 快速开始

```bash
# 可选：用户确认需要复用后，将 Nario OpenAPI 令牌保存到本地。
bytedcli nario auth token set --authorization-token <token>

# 检查是否已配置可复用令牌。命令不会打印令牌值。
bytedcli nario auth token status

# 通过列出空间验证 CN OpenAPI 认证和路由。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario workspace list --env cn

# 列出模板。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template list \
  --env cn \
  --psm example.psm \
  --method GetDemo \
  --page 1 \
  --page-size 20

# 获取模板详情。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template get \
  --template-id 3000001

# 获取模板覆盖率统计。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template statistics get \
  --template-id 3000001

# 获取模板下未覆盖的场景 ID。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario scene list --uncovered \
  --template-id 3000001

# 使用经过检查的 payload 创建度量任务，然后轮询报告。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario measure task create \
  --payload-file ./measure_task.json \
  --dry-run
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report poll \
  --task-id 3000001

# 通过 FTF 任务 URL 或 ID 解析 Nario 度量报告。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report get \
  --url https://example.invalid/ftf/task/123456

# 调试已捕获流量是否命中 Nario 模板/场景，不写入打标结果。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging flow tag \
  --payload-file ./flow.json \
  --dry-run \
  --need-detail

# 列出已存储 PID 命中的模板/场景。默认依次尝试 flow_temporary 和 flow_tagged。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging flow hit \
  --psm example.psm \
  --pid sample-pid

# 规划单个目标场景调试；构建并检查调试 payload 后，使用 --payload-file 重新运行。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging scene-debug execute \
  --psm example.psm \
  --pid sample-pid \
  --template-id 3000001 \
  --scene-id 2200001 \
  --dry-run

# dry-run 原始模板创建 payload。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario template create \
  --payload-file ./template_create_payload.json \
  --psm example.psm \
  --method GetDemo \
  --dry-run

# 根据语义字段构建模板创建 payload，不执行写入。
bytedcli --json nario template payload create \
  --workspace-id 2 \
  --name sample-template \
  --psm example.psm \
  --method GetDemo

# 使用特征规则构建场景创建 payload。
bytedcli --json nario scene payload create \
  --template-id 3000001 \
  --workspace-id 2 \
  --name sample-scene \
  --rule '[{"feature_meta_id":6001,"attribute":"$compare_value","condition":"$eq","values":["main"]}]'

# 预览本地 CSV 导入；检查 dry-run 计划后才能使用 --yes。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario import file execute \
  --operation template-create \
  --file ./nario-template-create.csv \
  --dry-run

# 检查警告后刷新模板覆盖率统计。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario template coverage refresh \
  --template-id 3000001 \
  --dry-run

# 一键刷新模板下的推荐场景（会先清除该模板下的推荐场景）。先 dry-run 检查前置校验。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario template flush execute \
  --psm example.psm \
  --method GetDemo \
  --template-id 3000001 \
  --dry-run

# 查询刷新状态：idle 表示未刷新或已完成，running 表示进行中。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template flush status \
  --psm example.psm \
  --method GetDemo

# 编码规则 check_value_list 值。
bytedcli --json nario rule check-value encode \
  --type string \
  --value sample-a \
  --value sample-b

# 生成 default_value_list 需要的双重 stringify wire 字符串。
bytedcli nario rule check-value encode --type number --value 0 --wire

# 检查 payload 后执行。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario scene update \
  --payload-file ./scene_patch_payload.json \
  --yes
```

## 命令映射

| 目标                      | 命令                                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| 列出空间                  | `bytedcli nario workspace list --name sample-space`                                                                 |
| 获取空间                  | `bytedcli nario workspace get --workspace-id 2`                                                                     |
| 创建空间                  | `bytedcli nario workspace create --payload-file ./workspace.json --dry-run`                                         |
| 更新空间基础信息          | `bytedcli nario workspace update --workspace-id 2 --payload-file ./workspace.json --dry-run`                        |
| 列出模板                  | `bytedcli nario template list --psm example.psm --method GetDemo`                                                   |
| 获取模板                  | `bytedcli nario template get --template-id 3000001`                                                                 |
| 聚合模板规则              | `bytedcli nario template get-feature-aggregate --template-id 3000001 --feature-id 6001`                             |
| 获取模板统计              | `bytedcli nario template statistics get --template-id 3000001`                                                      |
| 刷新模板覆盖率            | `bytedcli nario template coverage refresh --template-id 3000001 --dry-run`                                          |
| 一键刷新模板下的场景      | `bytedcli nario template flush execute --psm example.psm --method GetDemo --template-id 3000001 --dry-run`          |
| 一键刷新接口下的场景      | `bytedcli nario template flush execute --psm example.psm --method GetDemo --dry-run`                                |
| 查询刷新状态              | `bytedcli nario template flush status --psm example.psm --method GetDemo`                                           |
| 创建模板                  | `bytedcli nario template create --payload-file ./template.json --psm example.psm --dry-run`                         |
| 构建模板 payload          | `bytedcli nario template payload create --workspace-id 2 --name sample-template --psm example.psm --method GetDemo` |
| 局部更新模板              | `bytedcli nario template update --payload-file ./template_patch.json --template-id 3000001 --dry-run`               |
| 删除模板                  | `bytedcli nario template delete --ids 3000001,3000002 --dry-run`                                                    |
| 列出规则枚举              | `bytedcli nario rule enum list`                                                                                     |
| 编码规则值                | `bytedcli nario rule check-value encode --type string --value sample-a`                                             |
| 列出场景                  | `bytedcli nario scene list --template-id 3000001`                                                                   |
| 获取场景                  | `bytedcli nario scene get --scene-id 2200001`                                                                       |
| 列出未覆盖场景            | `bytedcli nario scene list --uncovered --template-id 3000001`                                                       |
| 创建场景                  | `bytedcli nario scene create --payload-file ./scene.json --dry-run`                                                 |
| 构建场景 payload          | `bytedcli nario scene payload create --template-id 3000001 --workspace-id 2 --name sample-scene --rule '{...}'`     |
| 局部更新场景              | `bytedcli nario scene update --payload-file ./scene_patch.json --dry-run`                                           |
| 删除场景                  | `bytedcli nario scene delete --ids 2200001 --template-id 3000001 --dry-run`                                         |
| 从文件导入 Nario 建模信息 | `bytedcli nario import file execute --operation template-create --file ./rows.csv --dry-run`                        |
| 从表格导入 Nario 建模信息 | `bytedcli nario import sheet execute --operation scene-create --sheet-url <sheet-url> --dry-run`                    |
| 打印导入示例              | `bytedcli nario import example get --operation scene-create --format csv`                                           |
| 保存可复用令牌            | `bytedcli nario auth token set --authorization-token <token>`                                                       |
| 检查已保存令牌状态        | `bytedcli nario auth token status`                                                                                  |
| 清除已保存令牌            | `bytedcli nario auth token clear`                                                                                   |
| 创建度量任务              | `bytedcli nario measure task create --payload-file ./measure_task.json --dry-run`                                   |
| 轮询度量报告              | `bytedcli nario measure report poll --task-id 3000001`                                                              |
| 列出度量场景明细          | `bytedcli nario measure report scene-detail --task-id 3000001 --scene-id 2200001`                                   |
| dry-run 流量打标          | `bytedcli nario tagging flow tag --payload-file ./flow.json --dry-run --need-detail`                                |
| 按 PID 为流量打标         | `bytedcli nario tagging flow tag --psm example.psm --pid sample-pid --flow-collection flow_tagged --dry-run`        |
| 打标调试                  | `bytedcli nario tagging debug execute --kind scene-template --payload-file ./debug.json --dry-run`                  |

## 原始写入 payload 说明

- 用户提供语义字段而非经过检查的 OpenAPI payload 时，优先使用 `nario template payload create/update` 和 `nario scene payload create/update`。这些命令会应用 Nario 默认值、规范化常见别名并打印最终 payload，但不会写入。
- `nario template update` 遵循 OpenAPI 字段名，要求使用 `meta_id`；该端点不要使用 `id`。
- `nario scene update` 遵循 OpenAPI 字段名，要求使用 `psm_scene_id`；该端点不要使用 `id`。
- `nario scene create` 应指向已有匹配特征元数据的模板。空 `feature_rule_list` 或 `feature_meta_id` 不属于该模板的规则，可能被平台以通用创建失败拒绝。
- `attribute`、`conditions`、`check_value_list` 等场景规则值必须保持 OpenAPI wire format。先用 `--dry-run` 校验，检查 payload 后才能使用 `--yes`。
- `check_value_list`（场景规则）和 `default_value_list`（模板推荐配置）都遵循 Nario 后端 `TransMeasureCheckValueToFe`：先对每个实际值 `JSON.stringify`，再对字符串列表整体 `JSON.stringify`，两次缺一不可；`default_value_list` 在线路上是字符串而不是数组。典型对照：`0` → `"[\"0\"]"`，`success` → `"[\"\\\"success\\\"\"]"`，`true` → `"[\"true\"]"`，`false` → `"[\"false\"]"`。完整示例见 `references/nario-business-import.md` 的「规则值」一节。
- 使用 `nario rule enum list` 检查支持的规则枚举值；使用 `nario rule check-value encode` 生成一次编码后的 `check_value_list` 数组；加 `--wire` 可直接输出 `default_value_list` 用的双重 stringify 字符串（如 `0` → `"[\"0\"]"`），再放入 payload。
- 创建/更新模板时，可将 `--template-id`、`--workspace-id`、`--name`、`--psm`、`--method`、`--priority` 等常用字段写入经过检查的 JSON payload。如果参数与 payload 冲突，bytedcli 会在发送请求前拒绝该请求。

## Schema 驱动导入说明

- `nario import file execute` 读取本地 CSV/JSON 中的 Nario 建模信息。CSV 第一行作为表头；JSON 接受单个对象或对象数组。
- `nario import sheet execute` 通过 bytedcli 现有的飞书/Lark 认证读取飞书表格中的 Nario 建模信息。第一行应填写字段名。
- 支持的操作为 `template-create`、`template-update`、`scene-create` 和 `scene-update`。
- 导入与单行命令使用同一个 payload 构建器，因此中文表头、常见别名、默认值和 `check_value_list` 编码行为保持一致。
- 导入应先运行 `--dry-run`。检查逐行 payload 和错误后才能使用 `--yes`。
- 业务表格导入按 `操作ID` 分组；模板创建可能先执行创建阶段，再执行特征更新阶段。
- 模板和场景创建/更新行可省略 `创建人` / `更新人` / `user`。省略时，如果存在缓存的 bytedcli 登录用户名，bytedcli 使用其邮箱前缀；否则不填该字段。
- 已确认执行的导入默认没有硬性行数上限。仅当用户需要显式安全上限时使用 `--max-rows <n>`。
- 除非传入 `--force`，否则 `nario import example get --output <path>` 会拒绝覆盖现有文件。
- 表格优先的工作流请阅读 `references/nario-business-import.md`；基础 OpenAPI 端点和原始 payload 契约仍以 `references/nario-openapi.md` 为准。

## 历史 skill 映射

此前独立的 `nario-openapi` skill 包含 Python runner 和 Lark Sheet 模板。本次 bytedcli 集成优先将 OpenAPI 核心能力落入 CLI：

- 环境路由：面向用户的调用通过 `--env` 指向 CN online、BOE、Row、ZG（中国支付区）、GCP 或 TTP。`measure report get` 与 `tagging scene-debug execute` 的 `--ftf-env` 未显式传入时按 `--env` 推导（`cn`→`cn`、`boe`→`boe`、`row`→`i18n`、`zg`→`zg`）；其它命令（含 `template flush`）不暴露 `--ftf-env`，只按 `--env` 推导。
- 查询 API：空间、模板和场景的 list/get 命令。
- 写入 API：空间 create/update、模板 create/update/delete、场景 create/update/delete，支持 `--payload`/`--payload-file` 或语义构建字段。
- Schema 驱动导入：从飞书表格和本地 CSV/JSON 中的 Nario 建模信息创建/更新模板与场景。
- 安全辅助：规则枚举列表、`check_value_list` 编码和模板覆盖率刷新警告；白名单原始请求只作为没有专用命令时的兜底。
- 安全模型：令牌默认脱敏、显式本地持久化，以及 dry-run/yes 门禁。

飞书表格和本地 CSV/JSON 导入通过 `nario import ... execute` 提供。仅对 schema 驱动构建器尚未覆盖的复杂字段继续使用原始 payload 命令。度量与打标 API 在同一套 Nario 认证和环境模型下分别使用 Nario engine/consumer 服务。

## 参考资料

- `references/nario-openapi.md`
- `references/nario-business-import.md`
- `references/nario-measure.md`
- `references/nario-tagging.md`
- `references/nario-flush.md`
- `references/nario-case-measure-report-coverage.md`
- `references/nario-case-debug-flow-hit.md`
- `references/nario-case-debug-psm-scene.md`
- `references/nario-case-flow-collection-troubleshoot.md`
