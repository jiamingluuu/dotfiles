# FTF 流量回放执行

目录：[触发与目标](#触发与目标) · [上下文](#执行前收集上下文) · [接入门禁](#psm-接入门禁) · [执行](#按环境执行) · [核验](#结果核验)

## 触发与目标

当用户说“执行FTF流量回放”“跑一下FTF流量回放”“执行FTF”“执行FTF回放”“执行流量回放”
或“执行FTF回归”时，直接执行本流程。该意图已经授权触发回放，不要再次询问是否执行，
也不要把“执行FTF”降级为帮助、计划或只读查询。

优先复用已开启 CI 的测试计划；某个环境类型零命中时，仅为该环境回退创建独立任务。全程使用 bytedcli/API，不打开 FTF 页面。
执行前冻结站点；下列示例固定为 cn，zg 使用 `--site cn --vregion China-Pay`。由提交结果
返回的 task ID 必须继续复用同一站点，裸 ID 未附站点时不得猜测。

## 执行前收集上下文

从当前会话、开发任务和部署结果中收集并核对：

- 当前 PSM；
- 用户的回放意图：全量回归，或变更影响接口回归；
- 本次变更涉及的接口（如有）；
- 每个已部署实例的实际泳道名及对应集群。

先按用户意图区分参数：

- 用户明确要求全量回归、全部接口回归或等价意图时，省略 `--method-list`，即使上下文存在变更接口也不得缩小范围。
- 用户明确要求变更影响接口回归时，从上下文提取变更接口；用户未明确全量时，默认按变更影响接口回归处理，以保持既有行为。
- 变更影响接口回归存在接口时，必须按上游 `UniversalMethod` 的输出格式传入：协议或 HTTP 动词大写，
  随后一个英文空格，再跟方法名或路径。例如 `GET /flow/list`、`POST /caseset/add-flow`、
  `THRIFT GetTaskDetail`、`RMQ EventConsumer`。多个接口使用英文逗号连接成同一个
  `--method-list` 参数，不要只传裸方法名。上下文没有变更接口时，省略 `--method-list` 并继续执行，
  不得猜测接口，也不得把接口信息作为执行前置条件。

区分环境类型与实际泳道：

| 实际泳道 | 环境类型 | 计划筛选参数   |
| -------- | -------- | -------------- |
| `boe_*`  | `boe`    | `--env boe`    |
| `ppe_*`  | `online` | `--env online` |

`boe`、`online` 不是泳道名。必须把实际泳道传给 `--replay-env`，把该泳道对应的集群传给
`--replay-cluster`。缺少 PSM、泳道或集群时，先从上下文和部署结果补齐；不要猜值。

## PSM 接入门禁

收集到 PSM 后，先执行以下命令确认该 PSM 是否已接入 FTF。这必须是整个回放流程的第一个业务动作，
并且必须早于任何 `plan list`、`plan execute` 或 `task create`：

```bash
bytedcli --json --site cn ftf psm get --psm <psm>
```

只有命令返回该 PSM 的记录，并且记录中的 `is_register_bytecopy` 或 `is_register_sdk` 至少一个等于
`1` 时，才视为已接入 FTF，并继续执行后续计划筛选。两者满足其一即可，不要求同时为 `1`。

命令成功但未返回记录，或返回记录中的两个注册标记均不等于 `1` 时，立即停止整个回放流程。不得查询
测试计划、不得执行计划，也不得走零命中 `task create` 回退。向用户说明：

> 该 PSM 暂未接入 FTF，无法发起流量回放测试，请参考
> [FTF2.0 Quick Start](https://bytedance.larkoffice.com/wiki/Gq0pwkub2iuEx1kgqWAcgOCznXc) 接入。

若命令自身报错，同样停止且不执行任何后续回放动作，并如实报告命令错误；不要把鉴权、网络或服务端
错误误报为“未接入”。同一次回放涉及 BOE 和 PPE 时，对同一个 PSM 只需完成一次接入检查，通过后再
分别按环境执行。

## 按环境执行

对每个已部署的环境独立执行以下步骤。若 BOE 与 PPE 都已部署，两侧都要执行，不能共用一侧的
计划列表、泳道或集群。

### 1. 筛选已开启 CI 的计划

BOE：

```bash
bytedcli --json --site cn ftf plan list --psm <psm> --env boe --ci
```

PPE：

```bash
bytedcli --json --site cn ftf plan list --psm <psm> --env online --ci
```

读取全部分页结果。只使用本次查询返回、且确认 `enable_ci=1` 的计划。

### 2. 按空间确定执行范围

读取完当前环境的全部命中计划后，按每条计划返回的 `space_id` 分组，再决定执行范围：

- 零个空间：进入“零命中回退”。
- 一个空间：直接执行该空间内全部命中计划，不询问用户。
- 多个空间：先按空间分组展示全部命中计划，然后询问用户选择一个或多个空间。每组至少展示
  `space_id`，以及组内每个计划的 `parent_plan_id` 和名称；不要把不同空间的计划混成一张无分组列表。
  建议展示为 `空间 <space_id>（<count> 个计划）`，下一行列出 `parent_plan_id · name`，让选择项与
  即将触发的计划一一可核对。

多空间时优先使用当前运行时可用的结构化用户输入工具，以复选框提供空间选项；每个选项标签应能
唯一识别空间，说明中列出该空间的计划数量和计划摘要。若当前运行时没有结构化多选能力，要求用户
回复一个或多个以英文逗号分隔的 `space_id`。只接受本次查询结果中出现的空间，不接受计划 ID 代替
空间 ID。

这次询问只用于选择**执行范围**，不是再次确认是否执行 FTF。用户选择后，直接逐计划执行所选空间
中的全部计划，不再询问执行确认。用户取消或未选择任何空间时，将当前环境记录为“未执行：未选择
空间”并停止该环境；这不属于零命中，禁止因此创建回退任务。BOE 与 PPE 分别完成自己的分组和选择，
不能用一侧的空间选择过滤另一侧。

### 3. 逐计划触发

对命中的每个计划分别执行一次，不要把多个计划合成一次调用：

```bash
bytedcli --site cn ftf plan execute \
  --parent-plan-id <parent_plan_id> \
  --replay-env <actual_lane> \
  --replay-cluster <actual_cluster> \
  --yes
```

变更影响接口回归且上下文存在变更接口时，在上述命令中追加
`--method-list "<comma-separated UniversalMethod>"`；全量回归或没有变更接口时不追加。传入后会合并到计划每个 PSM 的 `psm_trigger_params`；显式
`--psm-trigger-params` 中同一 PSM 的字段仍具有更高优先级。这里使用列表返回的
`parent_plan_id`，并把当前环境对应的实际泳道和集群传入。

### 4. 零命中回退

若某个环境类型没有命中计划，只为该环境创建一个独立任务。`--case-filter-mode` 使用 CLI
对外公开的字符串语义值 `non-realtime`；不要传后端数字枚举。以下默认值按固定值传入。创建前，从当前 bytedcli 全局配置或当前命令上下文读取
`site` 与 `vregion`，严格解析 `--space-id`：`cn + China-North -> 762`、`cn + China-Pay -> 8`、
`i18n + Singapore-Central -> 8`。

这些是全局路由信息，不能用业务环境参数 `--env boe|online` 推断。命中表中组合时直接使用固定值，
不得询问用户空间 ID。若当前 `site + vregion` 不在表中，停止当前环境的零命中回退，说明该路由尚无
FTF 回退空间映射；不得询问、猜测或省略 `--space-id` 创建任务。

BOE：

```bash
bytedcli --site cn ftf task create \
  --space-id <resolved_space_id> \
  --psm <psm> \
  --env boe \
  --case-filter-mode non-realtime \
  --task-run-time 10 \
  --noflow-abort-duration 300 \
  --method-replay-count 100 \
  --replay-mode normal \
  --replay-env <boe_lane> \
  --replay-cluster <boe_cluster>
```

PPE：

```bash
bytedcli --site cn ftf task create \
  --space-id <resolved_space_id> \
  --psm <psm> \
  --env online \
  --case-filter-mode non-realtime \
  --task-run-time 10 \
  --noflow-abort-duration 300 \
  --method-replay-count 100 \
  --replay-mode diffy \
  --replay-env <ppe_lane> \
  --replay-cluster <ppe_cluster> \
  --base-replay-env prod \
  --base-replay-cluster default \
  --yes
```

两类回退均遵循相同的条件参数规则：变更影响接口回归且上下文存在变更接口时追加
`--method-list "<comma-separated UniversalMethod>"`；全量回归或不存在变更接口时省略。PPE 回退必须使用实际 `ppe_*`
泳道，不得误传 BOE 泳道。BOE 创建沿用命令自身的非 online
直接执行行为；PPE 已由用户的执行意图授权，因此携带 `--yes` 直接提交。两类回退都必须携带按上述映射
解析出的 `--space-id`；已定义组合直接使用固定值，不询问用户。

## 结果核验

记录每个环境的计划筛选条件、命中计划、触发返回的任务 ID，以及零命中时实际使用的回退参数。
对每个返回的任务 ID 执行 `bytedcli --json --site cn ftf task get --id <task_id>`，核对 PSM、环境、
实际泳道、集群和任务状态。若提交结果未知，不得重复提交；先按任务 ID 或计划记录读取状态。

最终区分：已按计划触发、已回退创建、未执行及其原因。任何缺失上下文、权限错误或版本缺口都要
明确记录，不得伪造成功。
