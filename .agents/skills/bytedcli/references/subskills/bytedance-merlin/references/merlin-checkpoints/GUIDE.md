---
name: merlin-checkpoints
description: 查询和管理 HDFS Checkpoint 目录、目录组与 checkpoint 条目。当需要获取训练 Checkpoint 详情、枚举 Titan 上的 checkpoint 目录/目录组、刷新目录或查询权限时使用。支持用户直接提供 HDFS 路径，通过 checkpoint-dirs get --path / list 解析目录与 checkpoint 的 SID。
---

# Checkpoint 查询与管理

## 适用场景

- 获取训练 Checkpoint 卡片详情（命令：`training checkpoint-dirs get`）
- 按 job_run_id 查询某步的 checkpoint 信息（命令：`training checkpoints list`）
- 按条件分页查询 HDFS checkpoint 目录（命令：`training checkpoint-dirs list`）
- 分页查询 checkpoint 目录组（命令：`training checkpoint-dir-groups list`）
- 获取单个 checkpoint 目录详情（命令：`training checkpoint-dirs get`）
- 查询单个训练 checkpoint 关联的 checkpoint（命令：`training checkpoints list`）
- 查询单个 checkpoint 目录下的训练 checkpoint （命令：`training checkpoints list`）
- 刷新 checkpoint 目录（命令：`training checkpoint-dirs scan`）
- 查询用于回溯评估的训练 checkpoint（命令：`training checkpoints list`）
- 查询 checkpoint 目录权限（命令：`training checkpoint-dir-perms get`）
- 获取目录组信息（命令：`training checkpoint-dir-groups get`）

## 核心概念

### ID 体系（v4 SID 模型）

v4 命令通过 SID 定位 checkpoint 目录与单个 checkpoint，不再传 `dir_hash` / `ckpt_hash`：

| 概念 | 标识符 | 来源 | 说明 |
|------|--------|------|------|
| Checkpoint 目录 | directory sid | `checkpoint-dirs get --path` / `checkpoint-dirs list` | 训练 checkpoint 保存目录的唯一标识 |
| 单个 Checkpoint | checkpoint sid | `checkpoints list --filter '{"directory_sid":"<sid>"}'` | 目录下单个 checkpoint 的唯一标识 |

- 用户提供 HDFS 目录路径时，直接 `checkpoint-dirs get --path "hdfs://..."`，从返回结果取 directory sid。
- 需要单个 checkpoint 的 sid 时，用 directory sid 调 `checkpoints list --filter '{"directory_sid":"<sid>"}'`，从返回结果取目标 checkpoint sid。
- 目录与 checkpoint 的 SID 直接跨 region 稳定，无需在客户端做路径归一化或换算。

> 兼容说明：更早的 / 遗留接口曾用路径 hash（`dir_hash` / `ckpt_hash`）定位目录与 checkpoint；v4 命令一律改用 `--path` / `--sid`，无需再手工计算 hash。

## 路径 → SID 解析（AI 指令）

v4 命令用 SID 定位目录与 checkpoint，AI 无需再计算路径 hash。

**AI 必须遵循以下规则**：

1. **用户提供 `hdfs://` 目录路径时** → 直接查目录卡片拿 directory sid，再调用后续命令：
   ```bash
   bytedcli merlin training checkpoint-dirs get --path "hdfs://example-source/home/sample/models/my-llm"
   # → 从返回结果取 directory sid

   # 需要单个 checkpoint sid 时，用 directory sid 列出该目录 checkpoint
   bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'
   # → 从返回结果取目标 checkpoint sid
   ```
2. **用户直接提供 sid 时** → 单个 ckpt 直接作为 `--sid`；目录 sid 用 `checkpoints list --filter '{"directory_sid":...}'` 列出目录 checkpoint
3. **用户提供模糊信息（名称/关键字）时** → 先通过 `checkpoint-dirs list --filter '<json>'` 搜索，从返回结果获取 sid

> 遗留说明：本 Skill 仍保留 `hash_ckpt_path.py`（历史 / 遗留接口的路径 hash 计算）。v4 的 `checkpoint-dirs` / `checkpoints` 命令不需要它——按上面的 `--path` / `--sid` 走即可。

## 前置条件

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

如果出现认证错误（401/403），运行 `bytedcli auth login`。

---

## 1. 查询 Checkpoint 卡片

获取 HDFS Checkpoint 卡片的详细信息。v4 通过轮询等待卡片创建完成。

```bash
bytedcli merlin training checkpoint-dirs get --path hdfs://path/to/checkpoint

# v4 已移除 --wait-until-creation：若卡片尚未创建完成，重复执行上面的命令轮询直到返回结果
bytedcli merlin training checkpoint-dirs get --path hdfs://path/to/checkpoint
```

返回包含：`path`、`name`、`owners`、`stage`、`ckpt_count`、`min_step`/`max_step`、`jobs`、`source_sync`/`target_syncs` 等。

如果返回 `should_retry: true`，说明卡片尚未创建完成，需要再次调用（轮询）。

---

## 2. 按 Step 查询 Checkpoint

```bash
bytedcli merlin training checkpoints list --filter '{"merlin_job_ids":["<merlin_job_id>"],"step":<step>}'
```

---

## 3. 查询 Checkpoint 目录列表

分页查询 HDFS checkpoint 目录，支持按名称、路径、owner、训练任务等筛选。

```bash
bytedcli merlin training checkpoint-dirs list --page-size 20

# 按关键字和 owner 筛选（v4 过滤统一走 --filter '<json>'）
bytedcli merlin training checkpoint-dirs list --filter '<json>' --page-size 10

# 按 Merlin 任务 ID 筛选（merlin_job_id 作为 --filter 字段传入）
bytedcli merlin training checkpoint-dirs list --filter '<json>' --page-size 20
```

分页参数：`--page-size`、`--page-token`、`--skip`；过滤统一走 `--filter '<json>'`，可用字段如 `name_keyword`、`path_keyword`、`path_exact`、`owner`、`stage`、`modal`、`repo`、`merlin_job_id`、`arnold_trial_id`、`keyword`、`like`、`hdfs_ckpt_dir_group_sid`、`external_region`；精确结构见 `--schema`。

---

## 4. 查询 Checkpoint 目录组

```bash
bytedcli merlin training checkpoint-dir-groups list --page-size 20

# 只看自己创建的（my_created 作为 --filter 字段传入）
bytedcli merlin training checkpoint-dir-groups list --filter '<json>'
```

分页参数：`--page-size`、`--page-token`、`--skip`；过滤统一走 `--filter '<json>'`，可用字段如 `name_keyword`、`my_created`、`like`、`external_region`；精确结构见 `--schema`。

---

## 5. 获取目录详情与目录组信息

```bash
# v4 直接接受 HDFS 路径，无需计算 hash：
bytedcli merlin training checkpoint-dirs get --path "hdfs://<ckpt_dir_path>"

# 若确实需要 directory sid，可先用 checkpoint-dirs list 获取，再用 --sid 调用：
bytedcli merlin training checkpoint-dirs get --sid '<directory_sid>'

# 获取目录组信息
bytedcli merlin training checkpoint-dir-groups get --sid '<group_sid>'
```

---

## 6. 查询单个训练 checkpoint 关联的 checkpoint

```bash
# v4 top-level 无 --train-ckpt-hash：先用 --filter '{"directory_sid":...}' 列出目录 checkpoint，再在 filter 里加 step 等字段按单个 ckpt 过滤
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'
```

---

## 7. 查询单个 checkpoint 目录下的训练 checkpoint

查询 HDFS 训练 checkpoint 列表，支持按 step 范围、转换标签、任务 ID 等筛选。

```bash
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'

# 按 step 范围筛选
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>","step_from":1000,"step_to":5000}'
```

**从 HDFS 路径出发的完整示例**：

```bash
# Step 1: 从 HDFS 路径拿到 directory sid（也可用 checkpoint-dirs list 搜索）
bytedcli merlin training checkpoint-dirs get --path "hdfs://<ckpt_dir_path>"
# → 从返回结果取 directory sid

# Step 2: 查询训练 checkpoint 列表
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>","step_from":1000,"step_to":5000}'
```

---

## 8. 刷新 Checkpoint 目录

重新扫描 checkpoint 目录，更新目录下的 checkpoint 列表。v4 通过目录 sid 触发扫描（可先用 `training checkpoint-dirs list` 拿到 directory sid）。

```bash
bytedcli merlin training checkpoint-dirs scan --directory-sid '<directory_sid>'
```

---

## 9. 查询回溯评估用 Checkpoint

查询可用于回溯评估的训练 checkpoint 列表，支持按 step/token 范围和转换标签筛选。

```bash
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'

# 按 step 范围筛选
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>","step_from":1000,"step_to":5000}'
```

---

## 10. 查询目录权限

```bash
bytedcli merlin training checkpoint-dir-perms get --sid '<dir_sid>'
```

---

## 端到端工作流示例

### 场景：从 HDFS 路径查询目录详情和训练 checkpoint

```bash
# 1. 用户提供 HDFS 目录路径，直接获取目录详情（v4 接受 HDFS 路径，无需计算 hash）
bytedcli merlin training checkpoint-dirs get --path "hdfs://example-source/home/sample/models/my-llm"
# → 从返回结果取 directory sid

# 2. 列出该目录下的训练 checkpoint
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>"}'

# 3. 如需按单个 ckpt 过滤：v4 top-level 无 --train-ckpt-hash，按目录列出后用 --filter '<json>'
bytedcli merlin training checkpoints list --filter '{"directory_sid":"<directory_sid>","step":<step>}'
```

---

## 常见问题

| 现象 | 原因和处理 |
|------|-----------|
| `bytedcli: command not found` | 先安装 bytedcli |
| 401 / 403 认证错误 | 运行 `bytedcli auth login` 重新登录 |
| 轮询超时 | 稍后重试，或再次执行 `training checkpoint-dirs get` 轮询卡片状态 |
| 不知道 directory sid | 用 `checkpoint-dirs get --path` 或 `checkpoint-dirs list` 获取 directory sid |
| NonTT / 跨 region 路径查不到目录 | v4 用 `checkpoint-dirs get --path` 直接按路径解析 directory sid；跨 region 目录可在 `checkpoint-dirs list --filter '<json>'` 里带 `external_region` 过滤 |

## 关联技能

- `merlin-companion-eval`：伴生评估管理（依赖 checkpoint 信息）
- `merlin-model-card`：模型卡片管理
