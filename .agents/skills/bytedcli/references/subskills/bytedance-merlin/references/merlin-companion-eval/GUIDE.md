---
name: merlin-companion-eval
description: 管理和监控 merlin, seed 训练任务的伴生评估（Companion Evaluation）：查询/更新/回溯伴生任务、复制伴生任务、从零创建伴生评估（绑定 Checkpoint）、获取评估结果并创建 Insight 分析。当用户说"伴生评估/companion job/查看伴生任务/创建伴生评估/复制伴生任务/Checkpoint 评估结果/Auto Evaluation/sequence job/序列任务/回溯评估"时使用。
---

# 伴生评估（Companion）管理

管理 Merlin 训练任务的伴生评估（Companion Evaluation），覆盖查询、更新、复制、回溯、从零创建、监控结果与 Insight 分析。

## 业务概念全景

> **v4 运行单元说明**：当前 v4 的实际运行单元是 CompanionJob 的 run / instance；SequenceJob / SequenceJobNode 是不再在 v4 对外暴露的遗留内部概念（见 §6），此处保留仅用于解释历史结构，AI 不应把 SequenceJob 当作当前可管理 / 可直接操作的运行时。

### 实体层级

```
HdfsCkptDir  ── 标识: directory sid（来自 checkpoint-dirs get --path / list）
├── HdfsTrainCkpt [1..N]  ── 标识: checkpoint sid（来自 checkpoints list --filter '{"directory_sid":...}'）
│   └── SequenceJob [0..N]  ── CompanionJob 触发后产生的运行实例，不可直接管理（见 §6）
│       ├── SequenceJobNode [1..N]  (按依赖顺序执行)
│       │   └── 产物: HdfsTransformCkpt (可传递给下游 Node)
│       └── status: RUNNING / DONE / FAILED
└── CompanionJob [0..N]  ── 绑定: checkpoint 目录（directory sid）
    ├── 自动触发: 新 ckpt 产出时按 step/token 间隔、正则条件自动触发
    ├── 手动回溯 (Backfill): 对已有 ckpt 手动触发
    └── 触发产生 → SequenceJob 运行实例
```

### 关键概念

| 概念 | 说明 |
|------|------|
| CompanionJob | 伴生任务：绑定到某个 checkpoint 目录的触发配置 + 运行配置（运行配置即 SequenceJobConfig，见 `companion-jobs create --config`） |
| SequenceJob | CompanionJob 触发后产生的运行实例（针对单个 checkpoint，由多个 Node 组成）；v4 不再提供独立管理命令，见 §6 |
| SequenceJobNode | SequenceJob 内的执行节点（模型转换、评估等），有依赖顺序 |
| 自动触发 | CompanionJob 监听目录，新 checkpoint 产出时自动触发 SequenceJob |
| 手动回溯 (Backfill) | 对已有 checkpoint 手动触发 SequenceJob 执行 |

### Node 执行链示例

SequenceJob 内 Node 按依赖顺序执行，上游产物自动传递给下游：

| 顺序 | Node 类型 | 输入 | 产物 |
|------|----------|------|------|
| 1 | Safetensors 模型转换 | HdfsTrainCkpt (原始) | HdfsTransformCkpt (safetensors) |
| 2 | Quantize 量化 | 上游 Node 1 产物 | HdfsTransformCkpt (量化格式) |
| 3 | 自动评估 | 上游 Node 2 产物 | 评估结果 |

### ID 体系与路径解析（v4 SID 模型）

v4 命令用 SID 定位目录与 checkpoint，不再传 `dir_hash` / `ckpt_hash`，AI 无需计算路径 hash。

**AI 必须遵循以下规则**：

1. **用户提供 `hdfs://` 目录路径时** → 查目录卡片拿 directory sid，需要单个 checkpoint 时再列出该目录：
   ```bash
   bytedcli merlin training checkpoint-dirs get --path "hdfs://..."
   # → 从返回结果取 directory sid

   bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'
   # → 从返回结果取目标 checkpoint sid
   ```
2. **用户直接提供 sid 时** → 目录 sid 用 `checkpoints list --filter '{"directory_sid":...}'` 列目录，单个 checkpoint sid 作为 `--checkpoint-sid` 使用
3. **用户提供模糊信息时** → 先通过 `checkpoint-dirs list --filter '<json>'`（merlin-checkpoints Skill）搜索

## 前置条件

- `bytedcli merlin` 可用
- 知道训练任务的 `job_run_id` 或伴生任务的 sid

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

如果出现认证错误（401/403），运行 `bytedcli auth login`。

---

## 1. 查询伴生评估任务

获取训练任务关联的伴生评估列表：

```bash
# v4 companion-jobs list 无 job_run_id / 训练任务 sid 过滤字段；先由训练任务解析出 checkpoint sid，再按 checkpoint_sid_any 过滤
bytedcli merlin training checkpoints list --filter '{"merlin_job_ids":["<merlin_job_id>"]}'
# → 从返回结果取 checkpoint sid

bytedcli merlin training companion-jobs list --filter '{"checkpoint_sid_any":["<checkpoint_sid>"]}'
```

（v4 按伴生任务 sid 查单个任务用 `bytedcli merlin training companion-jobs get --sid '<companion_job_sid>'`。companion-jobs 列表过滤没有 job_run_id / 训练任务 sid 字段：要列出某训练任务下的伴生任务，须按上面的两步流程——先用 checkpoints list 由训练任务解析出 checkpoint sid，再按 checkpoint_sid_any 过滤；已知伴生配置 sid 时可按 companion_config_sid 过滤。精确字段见列表命令的 schema 输出。）

返回包含：`step`（Checkpoint 步数）、`evaluation_sid`、`collection_sids`、`status`（DONE/FAILED 等）。

如果需要通过条件（如关键字、类型、模式、创建者等）筛选伴生评估任务列表，可以使用：

```bash
bytedcli merlin training companion-jobs list --filter '{"name_contains":"<关键字>"}'
```

（v4 list 过滤统一走 `--filter '<json>'`；精确字段见 `--schema`。）

按 checkpoint 目录筛选（v4 用 directory sid，先查目录卡片拿到 sid）：

```bash
# 用户提供 HDFS 路径时，先查目录卡片拿到 directory sid
bytedcli merlin training checkpoint-dirs get --path "hdfs://example-cluster/home/sample/models/my-llm"
# → 从返回结果取 directory sid

# v4 companion-jobs list 无 directory 过滤字段；先列出该目录的 checkpoint 拿到 sid，再按 checkpoint_sid_any 过滤
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'
# → 从返回结果取 checkpoint sid

bytedcli merlin training companion-jobs list --filter '{"checkpoint_sid_any":["<checkpoint_sid>"]}'
```

---

## 2. 更新伴生评估任务

更新伴生配置的名称、描述、类型、模式等（v4 的编辑落在 companion-configs 上，`--sid` 为伴生配置 sid，启用/停用用 `--is-enabled` / `--no-is-enabled`）：

```bash
bytedcli merlin training companion-configs update --sid '<companion_config_sid>' --name updated-name --is-enabled
```

---

## 3. 复制伴生评估任务

基于现有伴生任务复制到新 HDFS 目录：

```bash
bytedcli merlin training companion-configs fork --checkpoint-directory-sid <target_dir_sid> --sources '<json array>'
```

**注意**：`--checkpoint-directory-sid` 为目标 checkpoint 目录的 sid（目录须已存在）；`--sources` 为 JSON 数组，精确结构见 `--schema`。

---

## 4. 回溯执行伴生评估

基于伴生配置在指定 checkpoint 上回溯执行。有两种方式：

### 方式 A：按 checkpoint sid 回溯

适用于用户提供完整 checkpoint 路径的场景（v4 用 checkpoint sid，先解析出 sid 再批量创建回溯实例）：

```bash
# Step 1: 查目录卡片拿到 directory sid，再列出目标 checkpoint 拿到 checkpoint sid
bytedcli merlin training checkpoint-dirs get --path "hdfs://example-cluster/home/sample/models/my-llm"
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'
# → 从返回结果取目标 checkpoint 的 sid

# Step 2: 基于伴生配置批量创建（回溯）
bytedcli merlin training companion-jobs batch-create --companion-config-sid '<companion_config_sid>' --checkpoint-sids '["<checkpoint_sid>"]' --type '<type>'
```

### 方式 B：按 path + step 回溯

v4 没有按 step 一步回溯的命令；先按目录 + step 解析出 checkpoint sid，再复用方式 A 的 `batch-create` 回溯：

```bash
# Step 1: 按目录 + step 解析出 checkpoint sid
bytedcli merlin training checkpoint-dirs get --path "hdfs://example-cluster/home/sample/models/my-llm"
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>","step":1000}'
# → 从返回结果取该 step 的 checkpoint sid

# Step 2: 批量创建（回溯）
bytedcli merlin training companion-jobs batch-create --companion-config-sid '<companion_config_sid>' --checkpoint-sids '["<checkpoint_sid>"]' --type '<type>'
```

### AI 引导逻辑

| 用户输入 | 推荐方式 |
|---------|---------|
| "回溯评估 hdfs://xxx step 1000" | 方式 B — 按 step 解析 checkpoint sid 后 `companion-jobs batch-create` |
| "回溯 hdfs://xxx/step-1000" | 方式 A — 解析 checkpoint sid 后 `companion-jobs batch-create` |
| 直接提供 checkpoint sid | 直接 `companion-jobs batch-create --checkpoint-sids` |

---

## 5. 从零创建伴生评估

当基于基线任务派生新训练任务后，需要为新任务创建伴生评估。典型流程：

1. 先用 `bytedcli merlin training checkpoints list --filter '{"merlin_job_ids":["<基线 merlin_job_id>"]}'` 拿到基线训练任务产出的 checkpoint sid，再用 `bytedcli merlin training companion-jobs list --filter '{"checkpoint_sid_any":[...]}'` 获取基线训练任务的伴生评估配置（沿用返回里的 `companion_config_sid`）
2. 通过 `bytedcli merlin training checkpoint-dirs get --path <hdfs_ckpt_dir_path>` 查询新训练任务的 HDFS checkpoint 目录卡片（v4 无 `--wait-until-creation`；若卡片尚未生成，轮询该命令直至返回）
3. 从目录卡片取 directory sid，再 `checkpoints list --filter '{"directory_sid":"<directory_sid>"}'` 拿到目标 checkpoint 的 sid（对应 `--checkpoint-sid`）
4. 创建伴生评估：

```bash
bytedcli merlin training companion-jobs create \
  --checkpoint-sid <ckpt_sid> \
  --config '<json>' \
  --name <name> \
  --type <type>
```

创建前建议调用 `merlin-job-resource` 技能选择合适的集群与队列。

---

## 6. 序列任务（Sequence Job）：当前版本已不再暴露

SequenceJob 能力在当前 Merlin 版本中已不再暴露，没有对应的替代命令（原 `create-sequence-job` / `list-sequence-job` / `get-sequence-job` / `stop-sequence-job` / `retry-sequence-job` 均已下线）。如需周期性 / 重复触发的伴生评估，请改用伴生配置与伴生任务（`training companion-configs` / `training companion-jobs`）。

---

## 7. 监控评估结果与 Insight 分析

获取评估完成的 Checkpoint 结果并创建 Insight 进行深度分析。

### 获取评估结果

```bash
# v4 companion-jobs list 无 job_run_id / 训练任务 sid 过滤字段；先由训练任务解析出 checkpoint sid，再按 checkpoint_sid_any 过滤
bytedcli merlin training checkpoints list --filter '{"merlin_job_ids":["<merlin_job_id>"]}'
# → 从返回结果取 checkpoint sid

bytedcli merlin training companion-jobs list --filter '{"checkpoint_sid_any":["<checkpoint_sid>"]}'
```

从返回中筛选 `status=DONE` 的条目，提取 `evaluation_sid` 和 `collection_sids`。

### 创建 Insight

```bash
bytedcli merlin insight create --name 'Job_<job_id>_Step<step>_Analysis' \
  --job-refs '[{"arena_job_sid":"<evaluation_sid>","region":"cn"}]' \
  --config '{"collection_refs":[{"collection_sid":"<col_sid>","collection_version_sid":"<ver_sid>"}]}'
```

`--job-refs` 用评估返回的 `evaluation_sid` 作为 `arena_job_sid`（每项必填 `arena_job_sid` + `region`）；`--config.collection_refs` 用返回的 `collection_sid` / `collection_version_sid`。完整嵌套结构（`config` 的权重 / display、cross-collection 等）以 `bytedcli merlin insight create --schema` 为准。

region 选择：国内用 `cn`，海外用 `sg`（`job_refs` 每项的 `region` 与顶层 `--region` 同理）。

### 调用 merlin-insight 技能分析

创建 Insight 后，调用 `merlin-insight` 技能进行能力分析和显著性对比。

---

## 端到端工作流示例

### 场景：从 HDFS 路径到触发回溯评估

```bash
# 1. 用户提供目录路径，查目录卡片拿到 directory sid
bytedcli merlin training checkpoint-dirs get --path "hdfs://example-source/home/sample/models/my-llm"
# → 从返回结果取 directory sid

# 2. 列出该目录的 checkpoint 拿到 checkpoint sid（v4 companion-jobs list 无 directory 过滤字段）
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'
# → 从返回结果取 checkpoint sid

# 3. 按 checkpoint_sid_any 查询该目录绑定的伴生任务
bytedcli merlin training companion-jobs list --filter '{"checkpoint_sid_any":["<checkpoint_sid>"]}'
# → 获取 companion_config_sid

# 4a. 按 checkpoint sid 回溯（从上一步返回结果取目标 checkpoint 的 sid）
bytedcli merlin training companion-jobs batch-create --companion-config-sid '<companion_config_sid>' --checkpoint-sids '["<checkpoint_sid>"]' --type '<type>'

# 4b. 按 step 回溯：先按 step 解析 checkpoint sid，再复用 4a 的 batch-create
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>","step":1000}'
```

---

## 注意事项

- `evaluation_sid` 和 `collection_sids` 来自伴生评估列表的返回结果
- 创建 Insight 时 `job_refs` 中的 `region` 需匹配环境（cn 或 sg）
- 同一 step 的评估已处理过则跳过（去重）
- 必须先 `insight create` 获取 `insight sid`，再调用 `merlin-insight` 技能分析
- 需要目录 / checkpoint 的 sid 时，用 `checkpoint-dirs get --path` / `list` 拿 directory sid，再用 `checkpoints list --filter '{"directory_sid":...}'` 拿 checkpoint sid

---

## 关联技能

- `merlin-insight`：Insight 深度分析（能力分析、显著性、案例查询）
- `merlin-job-launch`：创建并启动训练任务
- `merlin-job-resource`：选择合适的资源配置
- `merlin-checkpoints`：查询 Checkpoint 卡片、目录信息与目录/checkpoint sid
