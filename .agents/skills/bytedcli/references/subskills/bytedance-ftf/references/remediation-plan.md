# FTF 噪音修复计划预览

当用户需要审核 DIFF 噪音修复建议，但尚未授权执行平台配置、代码修改、部署、流量录制或回放变更时，
使用此工作流。

## Use Cases

- 当需要从一个 FTF 任务生成可审阅、不可执行的噪音修复建议时使用。
- 不用于直接写入噪音规则、修改代码、部署或触发回放。

## Inputs

- 必填：可信 FTF 任务 URL，或顶层任务 ID 加明确站点。
- 可选：PSM、method、annotation 类型、最大聚类数和每个聚类的样本数。
- 输出文件路径必须尚不存在；调用方负责选择可写目录。

## Workflow

### 1. 生成计划

```bash
bytedcli --json ftf remediation plan create \
  --url "<ftf-task-url>" \
  --max-clusters 20 \
  --sample-size 5 \
  --output-markdown ./repair-plan.md \
  --output-json ./repair-plan.json
```

任务 URL 会固定站点和任务身份。仅提供任务 ID 时，必须按照 FTF 主 Skill 的约定显式指定全局站点或区域。

### 2. 检查计划契约

- 默认分析范围是未标注的入向 DIFF 聚类。
- 命令从前 `--max-clusters` 个聚类中分别抽取最多 `--sample-size` 条记录；
  `--max-clusters` 最大为 500，超限请求会在访问后端前被拒绝。
- 仅当字段路径具有链路追踪或请求身份标识语义，且至少三个样本的录制值和回放值均完全不同时，才会提升为候选动作。
- 不会仅根据值差异将业务 ID、状态、金额、库存、权限、实验或配置字段提升为候选动作。
- 数组路径保持 `needs_human`，直到数组对齐检查证明稳定键等价，并由业务负责人确认顺序没有业务语义。
- 每个建议动作都包含 `approval=required`、`execution_available=false`、精确的 PSM/方法/路径范围、回滚意图、回读要求和回放验证。
- `task.evidence_hash` 绑定本次实际分析的聚类与样本证据；`plan_hash` 包含该哈希但不包含展示时间，因此相同证据重新渲染时确认身份稳定，证据变化时确认身份失效。
- 不覆盖已有输出文件。

### 3. 审核结果

JSON 是事实来源，Markdown 是固定渲染结果。请求确认前检查：
`--output-json` 的调用方使用
[`repair-plan.schema.json`](../assets/schemas/repair-plan.schema.json) 校验计划结构后再读取字段。

1. `scope.truncated=false`；否则需明确说明计划仅覆盖已展示的前缀范围。
2. 每个可执行结论都有精确的 Flow 链接，或明确说明链接不可用。
3. 每个动作都限定到具体方法和路径；拒绝全局忽略建议。
4. 每个 `needs_human` 结论都有一项具体的后续取证动作。
5. 用户明确知晓该命令未执行任何变更。

不得在同一轮执行任何建议动作。当前 CLI 不提供从该计划直接执行动作的入口；
`ftf remediation schema update` 和 `ftf remediation array-match update` 是独立的预览/写入工作流，
不能视为对计划中 `plan_hash` 或动作 ID 的确认。

## Structured Output

- JSON 必须通过 [`repair-plan.schema.json`](../assets/schemas/repair-plan.schema.json) 校验。
- `findings` 保存全部分类结论，`actions` 仅保存达到候选门槛且仍需审批的动作。
- `execution_enabled` 和每个 action 的 `execution_available` 固定为 `false`。
- Markdown 只用于人工阅读，不替代 JSON 契约。

## Results

- 成功：输出 schema-valid JSON 和对应 Markdown；如指定文件路径，则以新文件写入且不覆盖旧文件。
- 部分完成：`scope.truncated=true` 时只覆盖已分析的聚类前缀，必须明确剩余范围。
- 失败：任务身份、证据字段或输出路径不满足契约时停止，不生成可供确认的计划。
