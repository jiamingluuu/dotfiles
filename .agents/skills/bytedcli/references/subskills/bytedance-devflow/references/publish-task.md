# DevFlow 任务发布

本引用文档用于检查 DevFlow 任务是否满足合码发布条件、发起任务或单服务合码发布，以及查询任务或发布单的实时发布状态。

对应底层命令：

- `publish qualitycheck`
- `publish start`
- `publish info`

## 何时使用

根据用户意图选择一个动作：

- 用户询问“能否合码”“能否发布”“发布前有什么阻塞”时，使用 `publish qualitycheck`。
- 用户明确要求对已有 DevFlow 任务执行整体合码上线、单服务合码上线或仅合码时，使用 `publish start`。
- 用户询问任务、服务或发布单的发布状态、发布流水线、当前执行原子、原子状态或报错信息时，使用 `publish info`。

以下场景不使用本能力：

- 根据仓库、SCM、集群等完整发布参数创建 TCE 服务发布单时，使用 `references/publish-service.md`。
- 只需要根据 `task_id + psm` 返回发布流水线 ID 时，使用 `references/query-publish_pipeline.md`。
- 用户表达的是部署、泳道部署或重试部署，而不是合码发布时，使用对应部署引用文档。

## 动作选择

| 用户意图 | 命令 | 读写属性 |
| --- | --- | --- |
| 检查能否合码或发布 | `publish qualitycheck` | 只读 |
| 对已有任务执行合码或发布 | `publish start` | 写操作 |
| 查询发布状态、流水线、当前原子或错误 | `publish info` | 只读 |

## 接口映射与超时

| Resource/Action | Method | Path | 参数位置 |
| --- | --- | --- | --- |
| `publish` / `qualitycheck` | GET | `/openapi/mcp/task/publish/qualitycheck` | `task_id`、`repo_name`、`branch` 均为 query 参数 |
| `publish` / `start` | POST | `/openapi/mcp/task/publish/start` | `action`、`task_id`、`psm`、`provider` 均为 JSON body 参数；`provider` 可选，用于同一 PSM 下区分资源类型 |
| `publish` / `info` | GET | `/openapi/mcp/task/publish/info` | `task_id`、`order_id`、`psm` 均为 query 参数 |

`publish start` 会同步执行合码、创建发布单并启动流水线，多服务任务耗时可能超过通用 HTTP 超时，因此该动作单独使用 2 分钟超时，不影响其他请求。

`publish start` 是非幂等写操作。请求超过专用超时后必须提示“发布结果待确认”，引导调用 `publish info` 查询，禁止自动重试。

### 发布前检查

用户只是询问是否具备发布条件，尚未明确要求执行合码或发布时，只调用：

```bash
bytedcli devflow publish qualitycheck [--task_id="<task_id>"] [--repo_name="<repo_name>"] [--branch="<branch>"] --bytedcli-skill-dir="<skill所在目录>"
```

参数优先级：

1. 用户明确提供的 `task_id`
2. 用户明确提供的 `repo_name + branch`
3. CLI 根据当前 Git 仓库自动推断的 `repo_name + branch`

不要因为用户询问“能否发布”就直接调用 `publish start`。

### 发起合码发布

`publish start` 是写操作。只有用户明确要求执行合码、发布或上线时才调用。

发布范围必须来自用户的明确表达，不能根据 `qualitycheck` 返回的“可发服务”自动缩小：

- 用户明确提供目标服务 PSM 时，才允许选择 `service_merge_and_publish` 或 `service_merge`。
- 用户明确表达“整个任务”“全部服务”“整体发布”或同类任务级范围时，才允许选择 `task_merge_and_publish`，且禁止传 `psm`。
- 用户未明确提供 PSM，只说“发布这个服务”“现在帮我发布”或同类表述时，如果任务包含多个服务，必须先向用户澄清要发布的具体 PSM 或确认是否整体发布，禁止默认发起任务整体合码上线。
- 多服务任务的整体检查只要存在任一阻塞服务，就必须停止并告知当前任务不能整体合码上线及具体原因；即使其他服务显示可发布，也禁止自动选择其中一个服务发起服务级发布。
- 因部分服务阻塞而停止后，只有用户后续明确指定 PSM，才能针对该服务重新检查并发起服务级动作。

动作映射：

- 整个任务合码并发布：`task_merge_and_publish`，禁止传 `psm`
- 单个服务合码并发布：`service_merge_and_publish`，必须传 `psm`
- 单个服务仅合码：`service_merge`，必须传 `psm`

调用方式：

```bash
bytedcli devflow publish start --action="task_merge_and_publish" --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

```bash
bytedcli devflow publish start --action="service_merge_and_publish" --task_id="<task_id>" --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

```bash
bytedcli devflow publish start --action="service_merge" --task_id="<task_id>" --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

当用户只说“看看能不能发布”或“检查一下发布条件”时，不得推断为上述写操作。

### 查询发布状态

按任务查询全部服务：

```bash
bytedcli devflow publish info --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

按任务查询指定服务：

```bash
bytedcli devflow publish info --task_id="<task_id>" --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

按发布单查询：

```bash
bytedcli devflow publish info --order_id="<order_id>" --bytedcli-skill-dir="<skill所在目录>"
```

参数约束：

- `task_id` 和 `order_id` 必须且只能提供一个。
- `psm` 只能与 `task_id` 一起使用。
- 查询服务发布状态、当前流水线、当前执行原子或原子错误时，优先使用 `publish info`，不要退回 `service info`。

## 推荐流程

用户明确要求执行合码发布时：

1. 当前对话中没有可信的最新检查结果时，先调用 `publish qualitycheck`。
2. 先按用户是否明确提供 PSM 确定范围；不得用检查结果中的“可发服务”替用户选择目标服务。
3. 原样展示检查结果；任务级范围存在任一阻塞服务或返回 `pending` 时停止，不调用 `publish start`。
4. 检查通过且用户的执行意图明确时，根据任务级或服务级范围选择 `publish start` action。
5. `publish start` 成功后，可调用 `publish info` 查询最新状态和流水线。
6. `publish start` 会同步执行合码、创建发布单和启动流水线，CLI 为该动作单独等待最多 2 分钟。若仍然超时，结果属于未知状态，必须先调用 `publish info` 确认，禁止自动重试写操作。

用户只要求查看状态时，直接调用 `publish info`，不需要先执行 `qualitycheck`。

## 与旧能力的边界

- `service publish`：没有 DevFlow 任务或仅需要根据完整 TCE 发布参数创建服务发布单时使用。
- `publish start`：对已有 DevFlow 任务执行合码或启动发布。
- `publish info`：查询任务、指定服务或发布单的完整发布状态，包括流水线和当前原子。
- `publish_pipeline query`：兼容旧场景，只查询流水线 ID。

用户使用“发布”但无法判断是在创建 TCE 发布单，还是对已有任务执行合码上线时，必须先澄清；不得默认选择写操作。

## 输出处理

- 优先原样展示 CLI 输出，保留状态文案和 HTTPS 链接。
- 调用 `publish info` 后，必须向用户展示返回的 DevFlow 任务链接，且链接应定位到任务的“合码上线”页面；无论按 `task_id`、`task_id + psm` 还是 `order_id` 查询，都不得省略该链接。
- 调用 `publish info` 后，汇总输出至少包含：服务名、发布状态、流水线状态、当前执行原子、当前原子状态、流水线链接、任务链接、智能发布提示。
- `publish info` 返回中如果包含“智能发布提示”，最终回复必须展示该提示；多服务场景下每个服务返回的提示都要保留，不能因摘要化省略。
- 返回 `pending` 时，必须先原样展示提示，再补参、处理阻塞或请求用户确认。
- `publish info` 和 `publish qualitycheck` 是只读操作，不得将查询结果解释为已经发起发布。
- `publish start` 返回失败时，保留失败前缀、服务名称和具体错误，不得描述为发布成功。
- `publish start` 请求超时时，原样展示“发布结果待确认”提示，并先查询发布状态；不得把客户端超时直接解释为发布失败。
- `publish info` 中 `publish_status` 表示发布动作是否成功发起，`pipeline.status` 表示流水线执行状态。发布成功但流水线原子失败时，应表述为“发布成功，流水线原子执行失败”，不得改写为“发布失败”。
