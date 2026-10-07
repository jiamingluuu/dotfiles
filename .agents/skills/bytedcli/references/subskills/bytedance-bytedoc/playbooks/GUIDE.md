# ByteDoc 场景编排 Playbooks

本目录承载跨原子能力的一站式业务流程。`slow-query/`、`index-governance/`、`access-workflows/` 等目录描述单个能力怎么用；本目录描述什么时候从一个能力进入下一个能力，以及每个阶段必须停下来让用户做什么决策。

新增一站式流程时优先放在这里，再从相关原子能力 guide 链接回来。不要把跨阶段决策散落到多个原子能力文档里，否则后续扩展新的治理场景时很难保证 Agent 走同一套门禁。

## 慢查到索引治理

适用场景：

- 用户要求分析 ByteDoc 慢查询，并且结果显示可能与缺索引、索引顺序不合理、扫描量过大、排序无法利用索引等问题相关。
- 用户明确说“优化慢查”“治理慢查”“看看要不要建索引”“从慢查推进建索引”等。

不适用场景：

- 用户直接要求执行某个原子能力，例如“查索引列表”“创建索引 dry-run”“查询建索引状态”“运行 slow-query index-recommend --apply-index-dry-run”。这类请求按对应原子 guide 执行，不需要额外套本 playbook 的阶段门禁。

### 阶段 1：慢查证据摘要

1. 先加载 `../slow-query/GUIDE.md`，解析目标库的 `site`、`backend`、`vregion`、service/db。
2. 运行 `slow-query overview`；需要具体 query shape 时再运行 `slow-query detail`。
3. 只基于慢查证据给用户做 3-6 条摘要：时间窗、阈值、backend/vregion、collection/query shape、耗时、扫描量、返回量、调用方、是否采样或截断。
4. 如果证据不足，不要进入索引治理；先说明缺什么证据，必要时询问是否调整时间窗、阈值或使用 `--fetch-all`。

阶段 1 的输出只能是分析结论和下一步建议。即使看起来明显需要索引，也不要直接运行 `bytedoc index create` dry-run。

### 阶段门禁 A：是否进入索引治理

慢查分析后，除非用户在本轮已经明确要求“准备建索引工单 / 生成建索引 dry-run / 一站式治理到建索引”，否则必须先问用户是否需要继续进入索引治理阶段。

推荐问法：

```text
这类慢查可能需要通过索引治理处理。需要我继续帮你生成候选索引并准备建索引 dry-run 吗？
```

用户没有确认前，禁止由 Agent 主动执行：

- `bytedoc slow-query index-recommend --apply-index-dry-run`
- `bytedoc index create ...`
- 任何带 `--execute` 的建索引命令

用户如果只想要分析结论或治理建议，就停在阶段 1，不要替用户推进到工单。

### 阶段 2：候选索引与风险确认

用户确认进入索引治理阶段后：

1. 对 classic / cloud-native 可运行 `slow-query index-recommend` 获取推荐结果；Volc 返回 unsupported 时，说明当前没有 index-recommend 能力，不要切 backend 猜。
2. 对 classic，如需要后续创建工单，可以运行 `slow-query index-recommend --apply-index-dry-run` 生成 `indexCreateDryRuns[]`，但这仍然只是候选 dry-run 命令，不是已经执行 `index create` dry-run。
3. 建议同时用 `../index-governance/GUIDE.md` 的 `index list` 查看目标 collection 现有索引，避免推荐重复索引或明显冲突。
4. 向用户展示候选索引、对应 collection、命中的慢查 shape、预期收益、潜在风险（写入放大、唯一性、TTL、partialFilterExpression/collation 是否需要补充）。

### 阶段门禁 B：是否为候选索引生成 create dry-run

在运行具体的 `bytedoc index create ...` dry-run 前，必须再次确认用户要为哪个候选索引准备创建工单 dry-run。这个门禁不能被 `indexCreateDryRuns[]` 里的命令存在本身替代。

推荐问法：

```text
我建议先为 collection=<collection> 的 keys=<keys> 准备创建索引 dry-run。是否继续？
```

用户确认后，才运行不带 `--execute` 的 `bytedoc index create` 命令。dry-run 成功后展示 payload、workflow、collection、keys、unique、TTL、partialFilterExpression、collation、confirmation 和 nextActions。

### 阶段 3：真实建索引工单

只有在用户看过 `index create` dry-run payload 并明确确认后，才允许追加 `--execute --yes-i-know-this-is-live` 提交 BPM 工单。

live 成功后必须继续：

1. 返回 `ticket.ticketId` 和 `ticket.url`。
2. 用 `bytedoc index task get` 或 `bytedoc index task list --operation create --status doing|finished` 跟踪状态。
3. 不要把“工单已提交”描述成“索引已创建完成”，除非状态接口确认完成。

## 演进约定

- 原子能力新增命令时，先更新对应原子 guide；只有当多个原子能力形成稳定业务路径时，才新增或扩展本 playbook。
- Playbook 只描述跨阶段编排、用户决策门禁和成功口径，不重复每个命令的完整参数语义。
- 所有真实写入、工单、权限申请都必须保留 dry-run / 用户确认 / live 执行 / 状态跟踪四段式结构。
