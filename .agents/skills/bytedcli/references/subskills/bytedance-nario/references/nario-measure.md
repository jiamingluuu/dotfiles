# Nario 度量参考

当用户询问 Nario 场景覆盖率、命中统计、度量任务或度量报告时，使用本参考资料。度量 API 为异步接口：创建一次任务后，查询或轮询报告。

## 路由顺序

1. 用户提供 FTF task URL/ID 时，先运行 `report get --url ...` 或 `--ftf-task-id ...`，由 CLI 解析关联的 Nario 度量任务 ID。
2. 用户直接提供 Nario 度量任务 ID 时，运行 `report get --task-id ...`。
3. 从 `report get` 的 `resolvedTask.taskId` 取得真实 Nario 任务 ID，再用于 `poll` 和 `scene-detail`。
4. 需要定位低覆盖分布和未命中样例时，运行 `scene-detail --summary`。
5. 需要完整精确未命中场景清单时，分页运行非汇总 `scene-detail`，读取全部页面后筛选 `flow_distinct_hit_count`（兼容响应中的 `hit_flow_count`）数值为 `0` 的场景行。
6. 已有关联度量任务时不要重新创建任务，也不要改用 raw OpenAPI 猜测任务级覆盖接口。

## 命令映射

| 目标                       | 命令                                                                                                                                        |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 创建度量任务               | `bytedcli nario measure task create --payload-file ./measure_task.json --dry-run`                                                           |
| 获取报告基础信息           | `bytedcli --json nario measure report get --task-id 3000001`                                                                                |
| 通过 FTF 任务获取报告      | `bytedcli --json nario measure report get --url https://example.invalid/ftf/task/123456`                                                    |
| 通过 FTF 任务 ID 获取报告  | `bytedcli --json nario measure report get --ftf-task-id 123456 --ftf-env cn`                                                                |
| 轮询至报告进入终态         | `bytedcli --json nario measure report poll --task-id 3000001 --interval-ms 5000 --poll-timeout-ms 120000`                                   |
| 列出报告中的场景级明细     | `bytedcli --json nario measure report scene-detail --task-id 3000001 --page 1 --page-size 20`                                               |
| 按 method/模板汇总低覆盖率 | `bytedcli --json nario measure report scene-detail --summary --task-id 3000001 --page-size 100 --max-pages 200 --top 5`                     |
| 筛选场景级明细             | `bytedcli --json nario measure report scene-detail --task-id 3000001 --scene-id 2200001 --psm example.psm --method GetDemo`                 |

## 安全与执行

- 创建任务会启动后端异步工作，因此必须使用 `--dry-run` 或 `--yes`。
- 不要为同一个问题重复创建任务。首次创建任务后，优先使用 `report get` 或 `report poll`。
- `report get`、`report poll`、`scene-detail` 和 `scene-detail --summary` 都是读操作。
- `report get --url` 和 `report get --ftf-task-id` 会先通过现有 FTF 模块读取 FTF 任务详情并使用其中的 `narioTaskId`；不要将 FTF 任务 ID 本身当作 Nario 度量任务 ID。
- 报告汇总分析应使用 Nario 报告场景明细。除非用户明确要求 FTF 重放报告数据，否则不要依赖 FTF 报告聚合。
- `template statistics get` 和 `scene list --uncovered` 描述模板当前统计，不等于某次度量任务的场景 hit/miss。
- `template coverage refresh` 会异步刷新模板统计，是受 `--dry-run` / `--yes` 保护的写操作，不是度量报告查询。
- `raw execute` 不提供 measure/coverage 的任务路由。不要猜测 `query/task`、`coverage_detail` 等路径，也不要用场景元数据的全局流量字段推断本次任务结果。
- 当其他 Agent 或脚本需要解析状态、覆盖率或场景明细时，使用 `--json`。

## 任务创建 payload

确切的任务 payload 取决于平台所有者选择的度量场景。将其保存在经过检查的 JSON 文件中，并通过 `--payload-file` 传入。

经过检查的 payload 中可能出现的常见字段：

| 字段                                   | 含义                                                       |
| -------------------------------------- | ---------------------------------------------------------- |
| `task_name` / `name`                   | 人类可读的度量任务名称。                                   |
| `psm`                                  | 目标服务 PSM。                                             |
| `method`                               | 目标接口或 method。                                        |
| `business_workspace_id` / `work_space` | Nario 空间 ID。                                            |
| `scene_meta_id` / `meta_id`            | 任务面向单个模板时的模板 ID。                              |
| `psm_scene_id_list`                    | 任务面向指定场景时的场景 ID。                              |
| 时间范围字段                           | 开始/结束时间或流量窗口应使用经过检查的 API 文档中的表述。 |

如果用户无法提供经过检查的 payload，先帮助其确定度量目标、时间范围、空间/模板/场景范围，以及需要模板级还是场景级覆盖率。随后起草 payload 并运行 `--dry-run`。

## 报告字段

当 report get 通过 FTF 解析时，输出还包含 `resolvedTask`：

| 字段        | 含义                                         |
| ----------- | -------------------------------------------- |
| `taskId`    | 实际查询的 Nario 度量任务 ID。               |
| `source`    | 直接输入为 `nario-task`，桥接为 `ftf-task`。 |
| `ftfTaskId` | 可用时用于桥接的 FTF 任务 ID。               |

CLI 会汇总响应中存在的常见报告字段：

| 汇总字段                     | 后端字段示例                               |
| ---------------------------- | ------------------------------------------ |
| `taskId`                     | `id`, `task_id`                            |
| `status`                     | `status`, `task_status`, `coverage_status` |
| `workspaceId`                | `business_workspace_id`                    |
| `workspaceName`              | `business_workspace_name`                  |
| `flowTotal`                  | `flow_total`                               |
| `sceneHitCount`              | `scene_hit_count`                          |
| `sceneNotHitCount`           | `scene_not_hit_count`                      |
| `sceneHitCoverageStr`        | `scene_hit_coverage_str`                   |
| `flowDistinctHitCoverageStr` | `flow_distinct_hit_coverage_str`           |
| `feUrl`                      | `fe_url`                                   |

轮询识别的终态包括数字 `2`、`3`、`4`、`5`，以及字符串 `success`、`failed`、`done`。

## 场景明细筛选

- `--task-id` 为必填参数。
- `--scene-id` 可重复传入。CLI 会向后端发送 `psm_scene_list_str` 筛选条件。
- `--hit-options` 原样透传后端命中筛选条件，只能使用经过检查的后端枚举值。
- `--template-id` 映射到后端 `scene_meta_id`。
- 分页默认为 `--page 1 --page-size 20`。
- `scene-detail --summary` 扫描 Nario 场景明细分页，并按 `method`、method+模板聚合低覆盖率。结果按覆盖率影响排序，每类默认只返回前 5 个分组，且每组的 `sampleUncoveredSceneIds` 最多保留 5 个未覆盖场景 ID。
- 汇总结果的 `truncated=true` 表示场景分页未扫描完整；即使 `truncated=false`，`byMethod` / `byTemplate` 仍受 `--top` 截断，`sampleUncoveredSceneIds` 也仍是样例，不能拼成完整未命中清单。
- 仓库只确认 `--hit-options` 会原样透传，未定义哪个取值代表“未命中”。不要猜测该枚举；读取非汇总场景明细并按命中流量计数字段数值为 `0` 判断。
- 要输出“完整精确未命中场景清单”，必须分页读取到全部场景明细，确认累计读取数量达到响应 `total`（或最后一页条数小于 `page_size`），再筛选 `flow_distinct_hit_count`（兼容 `hit_flow_count`）数值为 `0` 的行。未读完时只能输出样例和证据缺口。
- 覆盖率影响是当前全局覆盖率减去移除该 method/模板分组后的覆盖率。负值表示该分组拉低全局覆盖率。

## 报告口径

最终回答应明确区分：

- 总体覆盖：报告状态、`sceneHitCount`、`sceneNotHitCount`、`sceneHitCoverageStr` 和 `flowTotal`。
- 低覆盖分布：`scene-detail --summary` 返回的 method、模板、覆盖率影响和未覆盖场景 ID 样例；同时报告 `truncated`，不要将样例描述为完整清单。
- 精确未命中场景：来自已完整分页读取的非汇总 Nario 场景明细，并以命中流量计数为 `0` 判定；不能根据 method 流量条数、场景创建时间、规则形态、全局 `is_flow_cover` / `flow_count` 或未经验证的 `--hit-options` 取值猜测。
- 证据缺口：报告未终态时继续轮询；无法读取场景明细时，明确说明当前只能得到聚合数据。

如果仅因缺少 `NARIO_OPENAPI_AUTHORIZATION_TOKEN` 无法调用 Nario measure，可在用户要求继续时，将 FTF task 配置的目标场景 ID 与各 flow detail 的 `scene_ids` 做集合差。该结果必须标记为“FTF 数据降级计算”，不能表述为 Nario 原生度量报告；除此之外不要退回启发式猜测。
