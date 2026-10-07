---
name: bytedance-mango
description: "通过 bytedcli 操作芒果平台任务与接口录入能力，包含通用工作流、CLI 命令和 references。用户提到 Mango、芒果、芒果任务查询、任务创建、接口查询、接口录入、接口修改、接口删除、空间、应用、菜单、资源、GraphQL 规则时使用。"
---

# bytedcli 芒果平台

使用 `bytedcli mango` 管理芒果平台任务和任务下的接口。

## 平台层级

芒果平台先区分空间（Space）；每个空间下有多个芒果应用（Module）；每个 Module 下有多个任务（Task）；每个任务下可以管理接口（Method）。

## 命令速查

需要稳定结构化输出时，把全局参数 `--json` 放在 `mango` 前面。

| 分类   | 命令                                       | 用途                                           |
| ------ | ------------------------------------------ | ---------------------------------------------- |
| 登录态 | `--site cn auth login --session --auto`    | 准备 Mango/open-admin 请求需要的 SSO browser session。 |
| 空间   | `mango space list`                         | 查看可用空间 ID，用于后续 `--space-id`。       |
| 应用   | `mango app list --space-id <id>`           | 查看空间下应用，获取 `Module` 和 AGW PSM。     |
| 模块   | `mango module graphql-rule list`           | 查看指定模块默认会注入的 GraphQL 规则。        |
| 任务   | `mango task list/create/trigger-pipeline`  | 查询、创建任务，或触发任务流水线重跑。         |
| 菜单   | `mango task menu list`                     | 查询任务可选菜单和默认资源状态。               |
| 接口   | `mango task method list/add/update/delete` | 查询、录入、修改或删除任务下的接口。           |

## 使用规则

- `--space-id` 来自 `mango space list`。
- `--module` 来自 `mango app list --space-id <id>` 输出中的 `Module`。
- 所有任务 ID 都使用 `--task-id <task-id>`。
- 录入接口时，必须传 `--agw-psm <psm>`，agw psm 来自 `mango app list --space-id <id>` 输出中的 `AGW PSM`。
- 命令报未知参数时，先用 `bytedcli mango ... --help` 复核当前 CLI 参数；以当前 CLI help 为准更新执行方式。

## 工作流程

```text
- [ ] Step 0: 明确操作范围
- [ ] Step 1: 确认登录态和用户身份
- [ ] Step 2: 确认空间 / 应用 / Module / AGW PSM
- [ ] Step 3: 确认泳道下的芒果任务
- [ ] Step 4: 菜单与资源门禁
- [ ] Step 5: 汇总信息并等待用户确认
- [ ] Step 6: 执行操作并触发流水线
```

每次执行工作流程前，必须读取 [workflow-checklist.md](references/workflow-checklist.md)。每个 Step 必须按该 checklist 全部通过后才能进入下一步；检查项未通过时，停下补齐信息或等待用户确认。

如果另一个业务 skill（如 `mango-task-manager`）提供固定上下文或对步骤、顺序、检查项有修改，以业务 skill 为准；未覆盖部分继续按本工作流和 [workflow-checklist.md](references/workflow-checklist.md) 执行。

### Step 0: 明确操作范围

1. 确认用户要执行的是只读查询还是写操作。
2. 涉及 `method list/add/update/delete` 时，先读取 [method.md](references/method.md) 准备命令字段。
3. 确认目标是任务、菜单、接口、流水线还是组合操作。
4. 只读查询可停在查询结果；接口录入、修改、删除和触发流水线必须走到 Step 5 等待用户确认。Step 3 中按 BOE/PPE 查不到任务时，直接创建任务。

### Step 1: 确认登录态和用户身份

1. 检查 `bytedcli` 的登录状态。
2. 获取当前操作人信息。

```bash
# 登录并刷新 cn 站点 session。
bytedcli --site cn auth login --session --auto

# 查看当前 bytedcli 操作人信息。
bytedcli auth userinfo
```

### Step 2: 确认空间 / 应用 / Module / AGW PSM

1. 确认后续命令使用的 `--space-id`、Mango 应用、`--module` 和 AGW PSM。
2. 必须确认唯一 Mango 应用 / `--module`；如果不确定，停下展示候选并让用户确认一个。
3. 若用户或业务 skill 明确指定 space/app/module，则使用指定值并校验一致性。
4. 如果用户只提供 BOE/PPE 泳道且业务 skill 定义了候选 module，可先按泳道只读查询候选 module；只有唯一 module 命中同一泳道任务时，才可把该 module 作为已确认上下文，并在 Step 5 披露该推断。零命中或多命中时必须让用户确认。

```bash
# 查询可用 Mango 空间，确认后续命令使用的 space ID。
bytedcli mango space list

# 查询指定空间下的应用，确认唯一 Mango 应用、module 和 AGW PSM。
bytedcli mango app list --space-id <space-id>
```

### Step 3: 确认泳道下的芒果任务

1. 必须在 Step 2 已确认的 `--module` 下查询或创建任务。
2. 按 BOE/PPE 泳道查询芒果任务。
3. 若根据 BOE/PPE 没有查询到可用任务，直接创建任务。
4. 创建成功并拿到 `task-id` 后，再进入菜单与资源门禁；门禁通过后才创建接口。
5. 所有任务接口命令都要显式传 `--task-id`。

```bash
# 在 Step 2 确认的 module 下，按任务名和环境过滤查询芒果任务。
bytedcli mango task list --space-id <space-id> --module <module> --name <task-name> --env <boe-or-ppe>

# 在 Step 2 确认的 module 下，按 BOE/PPE 泳道过滤查询芒果任务；task list 使用 --env，不使用 --boe/--ppe。
bytedcli mango task list --space-id <space-id> --module <module> --env <boe-or-ppe>

# 在 Step 2 确认的 module 下，BOE/PPE 未查询到可用任务时直接创建芒果任务。
bytedcli mango task create --space-id <space-id> --module <module> --name <task-name> --boe <boe> --ppe <ppe>
```

### Step 4: 菜单与资源门禁

1. `method add/update` 前查询任务菜单。
2. 确认是否已有唯一可默认使用的菜单/资源；否则必须让用户选择。
3. 若用户或业务 skill 明确指定菜单，则使用指定菜单并校验它来自当前任务菜单候选。
4. 菜单输出很大时，先按 service group 聚合，再展示与用户上下文相关的少量候选；不得把关键词命中当成自动选择。
5. 用户确认菜单后，如果平台需要资源，调用 `mango task menu resource` 解析资源；`needs_selection=false` 且有 `default_method_resources` 时可使用默认资源，否则展示资源候选并等待用户确认。
6. 禁止在菜单与资源门禁通过前创建接口。

```bash
# 查询当前任务下的菜单和默认资源状态。
bytedcli mango task menu list --space-id <space-id> --module <module> --task-id <task-id>

# 按 service group 过滤当前任务下的菜单候选。
bytedcli mango task menu list --space-id <space-id> --module <module> --task-id <task-id> --service-group <service-group>
```

禁止：不得根据接口路径、前端路由、业务名称、历史任务、PRD/RFC、service group、PSM 或相似接口自动匹配菜单/资源；不得只确认 service group 就继续写接口。

### Step 5: 汇总信息并等待用户确认

1. 准备所有待执行信息。
2. 新增接口前只能汇总用户显式传入或平台可解析的预期 HTTP 路由；若 HTTP 路由由平台生成，必须标明新增后会回查最终路由。
3. 一次性展示给用户确认。
4. 用户未明确确认前，禁止进入 Step 6。

### Step 6: 执行操作并触发流水线

1. 通过 [workflow-checklist.md](references/workflow-checklist.md) 中 Step 6 检查后再执行写操作。
2. 门禁通过后，才执行接口创建/修改/删除；若门禁需要用户选择，必须停下展示候选并等待确认。
3. 接口配置变更成功后触发流水线。
4. `method add` 成功后必须回查 `method list`，记录方法 ID、最终 HTTP 路由、菜单和资源；不要只依赖 add 返回的 `method_count`。
5. 接口 `method list/add/update/delete` 的具体命令和字段格式以 [method.md](references/method.md) 为准。

```bash
# 接口配置变更成功后，触发任务流水线重跑。
bytedcli mango task trigger-pipeline --space-id <space-id> --module <module> --task-id <task-id>
```

## References

| 任务场景                                           | 参考文件                                            |
| -------------------------------------------------- | --------------------------------------------------- |
| 工作流程检查项，执行流程前必须读取                 | [workflow-checklist.md](references/workflow-checklist.md) |
| 通用执行、JSON 输出、HTTP 调试                     | [invocation.md](../../invocation.md)           |
| 登录态与显式上下文                                 | [auth-state.md](references/auth-state.md)           |
| 模块 GraphQL 默认规则                              | [module.md](references/module.md)                   |
| 任务查询、创建、流水线                             | [task.md](references/task.md)                       |
| 任务接口查询、录入、修改、删除、接口类型和字段说明 | [method.md](references/method.md)                   |
| 常见错误与处理                                     | [troubleshooting.md](../../troubleshooting.md) |
