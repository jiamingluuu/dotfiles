# 工作流程检查项

每次执行 `bytedance-mango` 工作流程前必须读取本文件。每个 Step 的检查项必须全部通过后才能进入下一步；任一项不满足时，停下补齐信息或等待用户确认。

## Step 0: 明确操作范围

- [ ] 操作类型已明确。
- [ ] 涉及 `method list/add/update/delete` 时，已读取 [method.md](method.md)。
- [ ] 已区分只读查询和写操作。
- [ ] 写操作的目标对象已明确到任务、菜单、接口或流水线。

## Step 1: 确认登录态和用户身份

- [ ] 当前操作者已确认。

## Step 2: 确认空间 / 应用 / Module / AGW PSM

- [ ] `--space-id` 已确认。
- [ ] 已确认唯一 Mango 应用 / `--module`
- [ ] 接口录入时，AGW PSM 已确认。

## Step 3: 确认泳道下的芒果任务

- [ ] BOE/PPE 泳道已确认。
- [ ] 已在确认的 `--space-id` 和 `--module` 下用 `task list --env <boe-or-ppe>` 按 BOE/PPE 查询芒果任务。
- [ ] 若根据 BOE/PPE 未查询到可用任务，已直接创建任务。
- [ ] 已获得唯一 `task-id`。

## Step 4: 菜单与资源门禁

- [ ] 已查询任务菜单。
- [ ] 若已查询任务菜单，菜单候选非空，且已确认平台可默认使用唯一菜单/资源，或用户已明确选择具体菜单/资源。
- [ ] 若已查询任务菜单且候选多于 1 个，已展示候选并获得用户确认。
- [ ] 若未显式选择菜单，JSON 未出现 `task_menu_bound=false`、`can_use_default_menu=false`、`default_method_menu_item=null`。
- [ ] 若已显式选择菜单，已校验该菜单来自当前任务 `menus[].method_menu_item`。
- [ ] 若已查询任务菜单且 `requires_method_resources=true`，已有默认资源、`menu resource` 返回 `needs_selection=false` 且 `default_method_resources` 非空，或用户已明确选择资源。
- [ ] 若需要显式菜单/资源，已记录用户确认的 `MenuItems` / `MethodResources`。
- [ ] 未根据接口路径、前端路由、业务名称、历史任务、PRD/RFC、service group、PSM 或相似接口自动匹配菜单/资源。

## Step 5: 汇总信息并等待用户确认

- [ ] 操作类型已明确：录入接口、修改接口、删除接口、触发流水线或组合操作。
- [ ] 已查询现有接口并确认目标唯一。
- [ ] 已汇总 space、module、AGW PSM、task ID、泳道。
- [ ] 已汇总 method 名称、请求方式、说明和 `--methods` JSON 摘要；若 HTTP 路由由平台生成，已标明新增后回查最终路由。
- [ ] 已展示“将要执行的写操作”，并等待用户确认。

## Step 6: 执行操作并触发流水线

- [ ] Step 5 已获得用户明确确认。
- [ ] Step 3 已获得唯一 `task-id`。
- [ ] Step 4 菜单与资源门禁已通过。
- [ ] 写命令与操作目标一致。
