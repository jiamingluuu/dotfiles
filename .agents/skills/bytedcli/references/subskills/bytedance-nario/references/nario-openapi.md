# Nario OpenAPI 参考

本文件用于说明 Nario manager 资源端点和 payload 契约。场景覆盖率、度量报告、任务级 hit/miss 和低覆盖分布应使用 `nario measure report ...`，不要从本文件的原始端点推测任务级 coverage API。

## 环境

- `cn`：Nario manager 中国在线环境。
- `boe`：Nario manager BOE 环境。
- `row`：Nario manager Row 办公网环境。
- `zg`：Nario manager 中国支付区环境。
- `gcp`：Nario manager GCP 生产网络环境。
- `ttp`：Nario manager TTP 生产网络环境。

## 核心端点

| 能力             | 端点                                               | CLI                                                                         | 状态                                       |
| ---------------- | -------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------ |
| 空间列表         | `GET /workspace/query/list`                        | `nario workspace list`                                                      | 已集成，支持名称、服务树、类型和 self view 过滤 |
| 空间详情         | `GET /workspace/query/detail`                      | `nario workspace get`                                                       | 已集成                                     |
| 创建空间         | `POST /workspace/add`                              | `nario workspace create`                                                    | 已集成，带 dry-run/yes 门禁                |
| 更新空间         | `POST /workspace/update/basic`                     | `nario workspace update`                                                    | 已集成，带 dry-run/yes 门禁                |
| 模板详情         | `GET /openapi/v2/query/sceneMeta?meta_id=<id>`     | `nario template get`                                                        | 已集成                                     |
| 模板列表         | `GET /openapi/v2/query/sceneMeta/list`             | `nario template list`                                                       | 已集成                                     |
| 模板聚合         | `GET /openapi/v2/aggregate/feature`                | `nario template get-feature-aggregate`                                      | 已集成                                     |
| 模板统计         | `GET /openapi/v2/sceneMeta/statistics`             | `nario template statistics get`                                             | 已集成                                     |
| 刷新模板覆盖率   | `POST /openapi/v2/sceneMeta/fresh/flow_statistics` | `nario template coverage refresh`                                           | 已集成，带强 dry-run/yes 警告              |
| 一键刷新推荐场景 | `POST /openapi/v2/scene/psm_scene/flush`           | `nario template flush execute`                                              | 已集成，带 dry-run/yes 门禁与 preflight    |
| 查询刷新状态     | `POST /openapi/v2/scene/psm_scene/flush/status`    | `nario template flush status`                                               | 已集成，单次查询不轮询                     |
| 创建模板         | `POST /openapi/v2/scene_meta/create`               | `nario template create`                                                     | 已集成，带 dry-run/yes 门禁                |
| 局部更新模板     | `POST /openapi/v2/scene_meta/update_patch`         | `nario template update`                                                     | 已集成，带 dry-run/yes 门禁                |
| 删除模板         | `POST /openapi/v2/scene_meta/batch/delete`         | `nario template delete`                                                     | 已集成，带 dry-run/yes 门禁                |
| 场景详情         | `GET /openapi/v2/query/scene?id=<id>`              | `nario scene get`                                                           | 已集成                                     |
| 场景列表         | `POST /openapi/v2/query/scene/list`                | `nario scene list`                                                          | 已集成                                     |
| 未覆盖场景 ID    | `GET /openapi/v2/query/not_cover/sceneIDs`         | `nario scene list --uncovered`                                              | 已集成                                     |
| 创建场景         | `POST /openapi/v2/psm_scene/add`                   | `nario scene create`                                                        | 已集成，带 dry-run/yes 门禁                |
| 局部更新场景     | `POST /openapi/v2/psm_scene/update_patch`          | `nario scene update`                                                        | 已集成，带 dry-run/yes 门禁                |
| 删除场景         | `POST /openapi/v2/psm_scene/batch/delete`          | `nario scene delete`                                                        | 已集成，带 dry-run/yes 门禁                |
| 白名单原始请求   | 指定的 manager OpenAPI 路径                        | `nario raw execute`                                                         | 仅在没有专用命令时兜底；写入要求 dry-run/yes |
| 规则枚举         | 本地辅助工具                                       | `nario rule enum list`                                                      | 已集成                                     |
| check_value_list | 本地辅助工具                                       | `nario rule check-value encode`                                             | 已集成                                     |
| payload 构建器   | 本地 schema 辅助工具                               | `nario template payload create/update`, `nario scene payload create/update` | 已集成；不发送写请求                       |
| 表格/文件导入    | 本地 schema 辅助工具 + 现有写入 API                | `nario import sheet execute`, `nario import file execute`                   | 已集成，带 dry-run/yes 门禁                |

## 原始写入 payload 契约

- 模板局部更新使用 `meta_id` 作为模板 ID 字段。仅包含 `id` 的 payload 会在发送请求前被拒绝。
- 场景局部更新使用 `psm_scene_id` 作为场景 ID 字段。仅包含 `id` 的 payload 会在发送请求前被拒绝。
- 创建场景依赖目标模板的特征元数据。优先根据现有模板详情/列表响应构建 `feature_rule_list`；空规则列表或 `feature_meta_id` 与模板无关的规则可能被平台拒绝。
- 在部分 OpenAPI payload 上下文中，`check_value_list` 是字符串化的 JSON 数组。其序列化遵循 `TransMeasureCheckValueToFe`：先对每个实际值 `JSON.stringify`，再对字符串列表整体 `JSON.stringify`（两次 stringify 缺一不可）。模板推荐配置中的 `default_value_list` 在线路上同样是走双重 stringify 后的字符串，而不是数组。`nario rule check-value encode` 默认输出一次编码后的 `check_value_list` 数组；加 `--wire` 可直接输出双重 stringify 后的 wire 字符串，用于 `default_value_list`（如 `0` → `"[\"0\"]"`，`success` → `"[\"\\\"success\\\"\"]"`，`true` → `"[\"true\"]"`）。
- 模板创建/更新支持常用补丁参数（`--template-id`、`--workspace-id`、`--name`、`--psm`、`--method`、`--priority`），复杂规则结构仍通过 `--payload` / `--payload-file` 传入。
- 模板覆盖率刷新是异步、高影响操作。必须使用 `--dry-run` 或 `--yes`，并会输出长时间刷新和重复调用相关警告。
- 模板/场景 `payload create/update` 命令会应用 schema 默认值并规范化语义字段，但不发送写请求。
- 导入命令支持从飞书表格或本地 CSV/JSON 中的 Nario 建模信息执行 `template-create`、`template-update`、`scene-create` 和 `scene-update`。它们与单行命令复用同一个构建器；用户需要显式安全上限时可选用 `--max-rows <n>`。

## Raw 请求边界

- 只在没有 workspace/template/scene/import/measure/tagging 等专用命令，且目标 manager 路径已在 allowlist 中时使用 `nario raw execute`。
- 不要用 raw 请求替代 `nario measure report get/poll/scene-detail`，也不要试探未登记的 task、coverage 或 report 路径。
- 不要用 `query/scene` 返回的场景元数据推断某次 FTF/Nario 度量任务的 hit/miss。
- 查询和写入都优先使用专用命令；raw 写请求仍必须先 `--dry-run`，确认后才能 `--yes`。

## 有意排除的端点

| 能力            | 端点                                                                                              | 原因                                        |
| --------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 特征列表        | `GET /openapi/v2/query/featureMeta/list`                                                          | 推迟到设计更通用的特征 API 后实现。         |
| FTF 1.0 caseset | `/new_case_set/*`                                                                                 | 属于 FTF/Teslax，而不是 Nario CLI。         |
| FTF translate   | `/biz/open_api/translate/json_data`                                                               | 属于通用 FTF 能力，不是 Nario domain 命令。 |
| 已废弃流量查询  | `/openapi/v2/query/sceneFlow/*`, `/openapi/v2/query/flow/detail`, `/openapi/v2/query/origin/flow` | Nario OpenAPI 文档已将其标记为废弃。        |

## 删除请求体结构

删除模板会发送由数字 ID 组成的原始 JSON 数组，例如：

```json
[3000001, 3000002]
```

删除场景会发送对象请求体，例如：

```json
{
  "psm_scene_id_list": [2200001],
  "scene_meta_id": 3000001
}
```

## 后续范围

当前 schema 驱动构建器/导入已覆盖模板和场景的核心创建/更新流程。平台所有者确认字段语义后，后续迭代可将 schema 注册表扩展到特征列表、高级表达式模式、度量任务和更复杂的流量打标 API。
