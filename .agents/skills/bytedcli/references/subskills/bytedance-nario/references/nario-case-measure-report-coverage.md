# Nario 案例：度量报告覆盖率

当用户提供 FTF task URL/ID 或 Nario 度量任务 ID，并询问任务场景覆盖率、低覆盖分布、哪些场景没有命中或如何解读度量报告时，使用本案例。仅查询模板当前统计时，使用 `template statistics get` / `scene list --uncovered`，不要混入本任务级报告流程。

## 工作流

1. 如果用户提供 FTF 任务 URL/ID，先运行 `nario measure report get --url ...` 或 `--ftf-task-id ...`；CLI 会从 FTF 任务详情中解析关联的 Nario 度量任务 ID。
2. 如果用户直接提供 Nario 度量任务 ID，运行 `nario measure report get --task-id <id>` 或 `poll`。
3. 通过 FTF 路由时，读取 `report get` 输出的 `resolvedTask.taskId`；不要把 FTF task ID 直接用于 `poll` 或 `scene-detail`。
4. 如果报告尚未进入终态，使用真实 Nario 任务 ID 运行 `poll`，不要创建另一个任务。
5. 如果尚无任务且用户有经过检查的度量任务 payload，先运行 `nario measure task create --dry-run`。用户批准真实执行后，仅运行一次 `--yes`，并记录返回的 Nario 任务 ID。
6. 使用 `nario measure report scene-detail --summary --task-id <id>`，根据 Nario 场景明细按接口和模板聚合低覆盖率，并记录 `truncated`；这里的未覆盖 ID 只是每组最多 5 个样例。
7. 用户需要完整精确未命中清单时，分页运行非汇总 `nario measure report scene-detail --task-id <id>`，读取全部页面后筛选命中流量计数为 `0` 的场景行。
8. 汇总覆盖率、终态状态、可用的报告链接、低覆盖率 method/模板、精确未命中场景 ID 和证据缺口。

## 命令

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario measure task create \
  --payload-file ./measure_task.json \
  --dry-run

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario measure task create \
  --payload-file ./measure_task.json \
  --yes

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report poll \
  --task-id 3000001 \
  --interval-ms 5000 \
  --poll-timeout-ms 120000

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report get \
  --url https://example.invalid/ftf/task/123456

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report scene-detail \
  --task-id 3000001 \
  --page 1 \
  --page-size 20

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report scene-detail --summary \
  --task-id 3000001 \
  --page-size 100 \
  --max-pages 200 \
  --top 20
```

## 解读检查清单

- 如果报告状态尚未进入终态，继续轮询，不要创建另一个任务。
- 如果用户提供 FTF 任务 ID，绝不能直接将其作为 `--task-id`；先解析 `resolvedTask.taskId`。
- 如果 `sceneHitCount` 偏低，先运行场景明细汇总，识别导致未命中的 method/模板，再按需列出聚焦场景明细。
- `sceneHitCoverageStr` 是任务总体场景覆盖率；method 流量条数和 FTF report 聚合只能解释流量分布，不能直接判定哪个场景未命中。
- `scene-detail --summary` 的 `byMethod` / `byTemplate` 受 `--top` 限制，每组 `sampleUncoveredSceneIds` 最多 5 个；即使 `truncated=false`，这些 ID 仍只是样例。
- 精确未命中场景必须来自完整分页读取的非汇总 Nario `scene-detail`，按 `flow_distinct_hit_count`（兼容 `hit_flow_count`）数值为 `0` 判定。仓库没有定义 `--hit-options` 的未命中枚举，不要猜测其取值。
- 不要根据场景创建时间、规则形态或场景元数据中的全局 `is_flow_cover` / `flow_count` 做启发式认定。
- `template statistics get` / `scene list --uncovered` 是模板当前统计，`template coverage refresh` 是异步写操作；三者均不能替代当前任务的 measure 场景明细。
- 如果 `flowTotal` 为零，修改场景前先进入流量采集/打标排障路径。
- 如果某个特定场景未命中，使用代表性流量执行打标调试案例。

## 认证受阻时的降级

`nario measure` 需要 `NARIO_OPENAPI_AUTHORIZATION_TOKEN`。如果只因缺少该令牌无法读取报告：

1. 先明确说明 Nario 原生度量报告被认证阻塞，不要改用 raw OpenAPI 猜测任务级 endpoint。
2. 用户要求继续时，可从 FTF task 元数据取得目标场景 ID，再收集各 flow detail 的 `scene_ids`，用目标集合减去已命中集合。
3. 将结果标记为“FTF 数据降级计算”，同时说明它不是 Nario `measure report scene-detail` 的原生输出。
4. 没有集合差证据时停止在已确认的聚合数据，不猜测具体未命中场景。

## 输出结构

1. 任务映射：FTF task ID（如有）、`resolvedTask.taskId`、报告状态和链接。
2. 总体覆盖：hit、miss、总场景数、覆盖率和流量总数。
3. 低覆盖分布：method、模板、覆盖率影响、`truncated` 和未覆盖场景样例。
4. 未命中场景：仅在非汇总明细已完整分页读取后列出精确场景 ID；注明来自 Nario 明细或 FTF 数据降级计算。
5. 证据边界与下一步：未终态、认证阻塞、分页未完成、明细不可用或需要打标调试。
