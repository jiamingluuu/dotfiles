---
name: bytedance-lark-devops
description: "Operate Lark Devops via bytedcli — release platform reads (processes/spaces/apps/linked Bits pipelines on lark-devops.bytedance.net), guarded simple-release writes (create / audit add-app / apply-stage / set-window / submit), guarded dev-flow writes (BOE-only: create --flow dev / dev add-app / integrate / execute-pipeline / finish, strictly isolated from PRE/GRAY/ONLINE), FG (Feature Gate) OpenAPI (lookup by feature_key, rule / meta / ticket queries, rule CRUD), and Owl SLA read surface (feature tree / rule config / current value + previous-cycle / trend / low-points / alarm association / Grafana dashboards across CN + 6 I18N vRegions). Writes default dry-run; require --execute + --yes-i-know-this-is-live. Use for: release process/pipeline drill-down, creating a release (simple or dev), BOE publish, audit stage advancement, publish windows, feature gates (by feature_key) / FG tickets, Lark Scheduler (processor/job + launch-review), or SLA queries (功能树 / SLO / 当前 SLA / 趋势 / 低点 / 关联告警 + bosun 规则 / Grafana 大盘)."
---

# bytedcli Lark Devops

`bytedcli lark-devops` covers seven capabilities against `lark-devops.bytedance.net`:

1. **Release platform — read** (`process`, `space`, `app` subtrees) — release processes, spaces, apps, and their linked Bits pipeline runs.
2. **Release platform — guarded simple-release writes** (`release` subtree, `--flow simple`) — create / audit add-app / apply-stage / set-window / submit; targets PRE_RELEASE / GRAY_RELEASE / ONLINE for production release.
3. **Release platform — guarded dev-flow writes** (`release dev` subtree, `--flow dev`) — create / dev add-app / integrate / execute-pipeline / finish; targets DEV + INTEGRATION only, **strictly isolated** from production stages. Use for BOE feature-branch verification.
4. **FG (Feature Gate) OpenAPI** — feature search by feature_key, meta / rule queries (by feature_key or numeric ID), release ticket queries and grayscale rule CRUD (`fg` subtree).
5. **Lark Scheduler** (`scheduler` subtree) — processor/job 查询、执行历史、launch-review trigger。
6. **Owl SLA — read** (`sla` subtree) — feature tree / SLA rule config / current value + previous-cycle / trend / low-points / alarm association / Grafana dashboards across CN + 6 I18N vRegions.
7. **EEConf secret injection — guarded write** (`eeconf secret create` subtree) — submit EEConf encryption-key injection tickets (`EECONF_SECRET_*`) for TCE / Bernard; default dry-run, requires `--yes`.

Write flows (1-3) default to dry-run; real writes require `--execute --yes-i-know-this-is-live`. SLA (6) is read-only. EEConf (7) defaults to dry-run; real submit requires `--yes`.

Choose the subtree by capability:

- Release data (process/space/app) ⇒ `bytedcli lark-devops process|space|app …`
- Production release writes (simple flow) ⇒ `bytedcli lark-devops release create --flow simple …` + `audit …`
- Dev/BOE release writes ⇒ `bytedcli lark-devops release create --flow dev …` + `dev …`
- Feature gates ⇒ `bytedcli lark-devops fg …`
- Lark Scheduler ⇒ `bytedcli lark-devops scheduler …`
- SLA queries (功能树 / SLO / 数值 / 趋势 / 低点 / 告警关联 / 大盘) ⇒ `bytedcli lark-devops sla <resource> <verb>`
- EEConf 密钥注入提单 (TCE / Bernard) ⇒ `bytedcli lark-devops eeconf secret create --platform <tce|bernard> …`（详见 [EEConf secret injection](references/eeconf.md)）

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

所有子命令加 `-j` / `--json` 即输出结构化 JSON，供 Agent 下游消费。

---

## 1. Release platform (read-only)

### 1.1 When to use

- The user asks about a release process / 发布工单 / 发布单（已知 `process_id`）
- The user wants a summary of a release space（已知 `space_id`）
- The user wants to find all release processes in a space that reference an app name or a PSM entity
- The user wants to jump from a release process to its linked Bits pipeline runs, optionally by phase (pre / gray / online / audit / dev / integration) or unit (CN / SG_LARK / US / …)

### 1.2 Prerequisites

`lark-devops process|space|app` 子命令需要 `.lark-devops.bytedance.net` 的 `beops_session` cookie。按如下优先级获取：

1. **Chrome 本地 cookie**（首选）：只要用户在本机 Chrome 登录过 `https://lark-devops.bytedance.net`，CLI 会自动从 Chromium cookie 库抽出 `beops_session` 使用
2. **SSO session 兜底**：如果 Chrome 里没有，再尝试用 `bytedcli auth login --session` 缓存的 SSO session 去换

最可靠的做法是让用户在本机 Chrome 浏览器里登录一次 `https://lark-devops.bytedance.net`，然后再用 CLI。结果缓存在本地（TTL 6h）。清缓存：

```bash
bytedcli lark-devops auth logout
```

如果两种来源都失败，会抛 `LARK_DEVOPS_AUTH_REQUIRED`，并在 error message 里提示用户怎么办。

### 1.3 Commands

**Space 不是全局通用的，必须由用户显式提供 `--space-id`（数字）。**

```bash
# Release process（已知 process_id）
bytedcli lark-devops process summary --process-id 12340 -j

# 从 process 反查关联的 Bits pipeline runs（可选按 phase/unit 过滤）
bytedcli lark-devops process pipelines --process-id 12340 -j
bytedcli lark-devops process pipelines --process-id 12340 --phase gray -j
bytedcli lark-devops process pipelines --process-id 12340 --phase online --unit CN -j

# Space 内最近发布
bytedcli lark-devops space summary --space-id 67 --limit 3 -j

# 空间内按 app name 查工单
bytedcli lark-devops process search --mode app --space-id 67 --app-name example.app -j

# 空间内按 PSM entity 查工单
bytedcli lark-devops process search --mode psm --space-id 67 --psm-entity example.app_pre_release -j

# 应用搜索
bytedcli lark-devops app search --keyword example.app -j
bytedcli lark-devops app search --psm example.app.service --page-size 10 -j
```

### 1.4 Phase / Unit enums

- `--phase`：`dev | integration | pre | gray | online | audit`
  - 归一到 `DEV / INTEGRATION / PRE_RELEASE / GRAY_RELEASE / ONLINE / AUDIT`
- `--unit`：`CN | US | SG_LARK | SG_EA | JP | BOE | MY | OTHER | US_TTP3 | CN_NORTH6 | US_TTP4 | Undefined`
  - 支持别名 `cn/sg/sg-ea/us_ttp3/cn_north6/us_ttp4/…`，也可传数字 `0..11`

### 1.5 Pipeline run 详情

`bytedcli lark-devops process pipelines` 只返回流水线元信息（`run_id`、`bind_build_url`、`psm`、`unit`、`phase`）。查询流水线细节：

- 直接访问 `bind_build_url`（bits UI）查看完整 stage/job/log
- 或用现有 bits 子命令进一步下钻：`bytedcli bits pipeline --pipeline-id <pipelineId>`、`bytedcli bits job-run <job_run_id>`、`bytedcli bits step-logs <job_run_id> <step_name>`

### 1.6 Typical fields

从 `process summary` / `process pipelines` 结果里读取以下字段足以覆盖 90% 场景：

- `process_id`, `process_name`, `status`, `current_phase_index`
- `space_id`, `space_name`, `creator`, `operator`
- `phases[].phase_name` (`PRE_RELEASE / GRAY_RELEASE / ONLINE / …`), `phase_status`
- `phases[].apps[].app_name`, `env_items[].entity` (PSM), `env_items[].repos[].scm_branch / scm_version`
- `phases[].triggers[].task_executions[].bind_build_id` → run id，可送入 `bytedcli bits pipeline --pipeline-id <id>` 下钻
- `phases[].triggers[].task_executions[].bind_build_url` → 直接跳转 bits UI 看完整 stage/job/log

### 1.7 Fallback strategy for Agents

- User gives `process_id` → `process summary`
- User gives `space_id` → `space summary`
- User gives `space_id` + `app_name` → `process search --mode app`
- User gives `space_id` + `psm` → `process search --mode psm`
- User wants pipelines from a process → `process pipelines` (optionally `--phase` / `--unit`)
- User already has a `run_id` + `bind_build_url` → 直接访问 URL 或 `bytedcli bits pipeline --pipeline-id <pipelineId>`（按 pipeline 维度）

### 1.8 Constraints

- 读接口，不支持创建发布单、触发流水线、改状态
- `--space-id` 必传；不提供全局 seed
- `process search --mode app|psm` 扫描 `--limit` 条最近工单（默认 10），命中数受 `limit` 影响，可增大至 20~50 以提升召回
- 本地 session cookie 缓存 TTL 6h；取到旧值时执行 `bytedcli lark-devops auth logout` 后重试
- 认证失败会抛 `LARK_DEVOPS_AUTH_REQUIRED`，提示用户在本机 Chrome 登录 `https://lark-devops.bytedance.net`，或跑 `bytedcli auth login --session` 补一份 SSO session 兜底

---

## 2. Release write workflow (guarded)

### 2.1 When to use

- The user wants to **create** a new release process (currently only `--flow simple` is supported)
- The user wants to **advance a release audit** (add app → apply stage plans → set publish window → submit)
- The user wants to **inspect** audit-derived ids, unit/cluster/version candidates, or run pre-submit validation
- The user wants to **dry-run** any of the above to preview the exact HTTP payload without side effects

### 2.2 Prerequisites

Same auth model as Section 1 (Chrome `beops_session` primary, SSO fallback). **Writes additionally need a `_csrf_token` cookie from the same Chrome session** — CLI reads it automatically when present. If a write ever fails with a CSRF error, re-sign in to the site in Chrome and rerun.

### 2.3 Live-write guard (critical)

Every write subcommand follows the same pattern:

| Flags                                 | Behavior                                                                                 |
| ------------------------------------- | ---------------------------------------------------------------------------------------- |
| no `--execute`                        | **Dry-run**: returns `{mode:"dry_run", endpoint, payload}` — safe preview, no HTTP write |
| `--execute` only                      | **Rejected** with `LARK_DEVOPS_LIVE_WRITE_UNCONFIRMED`                                   |
| `--execute --yes-i-know-this-is-live` | **Live write** — actually sends the request                                              |

Always preview with dry-run, inspect the payload, **then** add both flags.

### 2.4 Strict sequence for `--flow simple`

```
1. release create
2. release audit add-app
2b. release audit seed-integrators        # 仅当 add-app 后顶层 integrators 仍为空时才补
3. release audit apply-stage --stage pre
4. release audit apply-stage --stage gray
5. release audit apply-stage --stage online
6. release audit set-window --confirm     # 推荐用 --from-platform --confirm
6b. release audit add/remove-work-item    # 可选：page ③ 需求/缺陷确认
6c. release audit confirm-apps --confirm true
7. release audit submit --process-id

# 便捷写法：submit --auto-confirm 会在前置未满足时自动补做 6 + 6c，再提审。
7b. release audit submit --process-id --auto-confirm
```

语义要点：

- `add-app` 是标准的 integrators 初始化路径；新工单按标准流程通常不需要额外处理。
- `seed-integrators` 是**专门 CLI**，只在预填 / 克隆 / 历史工单里顶层 `audit_user_status.integrators` 仍为空时使用；不要再通过“先乱跑一遍 apply-stage / set-apps 试试”这类绕路方式补 integrators。
- `seed-integrators --exclude-unit <id>` 会按 inspect 里的数字 `unit` 字段过滤，不依赖 `unit_name`；当平台返回 `unit_name: null` 但需要跳过特定 unit（例如 `--exclude-unit 9`）时使用。
- `submit` 本身只检查两个前置标志：应用已确认（`integrators[].viewed` 全 true）和窗口已确认（`audit_publish.status === "Done"`）；它不直接重跑规则1/2。
- `submit --auto-confirm` 是便捷开关：在前置未满足时自动跑 `confirm-apps` / `set-window --confirm`，不是另一条独立流程。

### 2.5 Commands

**Step 0 — 资源发现（必做，不能跳）**

```bash
# user 只给了 space 名 / app PSM？先解析 id（dev flow 也用同一套）
bytedcli lark-devops space search --name-like <keyword> -j    # → space_id
bytedcli lark-devops app search --psm <dot-form-psm> -j       # → app_id, app_name
```

**规则：** `--space-id` 和 `--app-id` 必须由 user 显式给数字、或 agent 通过上面两个只读接口解析。CLI 不提供全局默认。

```bash
# 1. Create (dry-run preview)
bytedcli lark-devops release create --space-id 67 --name "example release" --flow simple -j

# 1'. Create (live write)
bytedcli lark-devops release create --space-id 67 --name "example release" --flow simple \
  --execute --yes-i-know-this-is-live -j

# 2. Add app to audit scope
bytedcli lark-devops release audit add-app \
  --process-id 12345 --space-id 67 --app-id 1001 --app-name example.app \
  --execute --yes-i-know-this-is-live -j

# 2a. Discover unit names (need this to write plan.units section in step 3-5)
#     读 data.unit_drafts[].unit_name（字符串枚举：CN/US/SG_LARK/...）
bytedcli lark-devops release audit build-stage \
  --process-id 12345 --app-id 1001 --stage pre -j

# 3-5. Apply per-stage plan (PRE / GRAY / ONLINE)
bytedcli lark-devops release audit apply-stage \
  --process-id 12345 --space-id 67 --app-id 1001 --app-name example.app \
  --stage pre --file ./audit-stage-plan.json \
  --execute --yes-i-know-this-is-live -j

bytedcli lark-devops release audit apply-stage \
  --process-id 12345 --space-id 67 --app-id 1001 --app-name example.app \
  --stage online --file ./audit-stage-plan.json \
  --execute --yes-i-know-this-is-live -j

# 6. Publish window — 发布窗口是 space 级规范时间，由 /deploy/cd/audit/publish/get 权威返回
#    默认直接用平台返回的窗口重写回去（`--from-platform`），Agent 不应自行编造时间。
bytedcli lark-devops release audit set-window \
  --process-id 12345 --from-platform \
  --execute --yes-i-know-this-is-live -j

# 6a. 「确认」按钮：与设置时间同一端点；加 --confirm 才会把窗口状态置为 Done
bytedcli lark-devops release audit set-window \
  --process-id 12345 --from-platform --confirm \
  --execute --yes-i-know-this-is-live -j

# 仅当 space 管理员显式要求覆盖时，才使用 `--file ./publish-window.json`

# 6b. 需求/缺陷确认（可选）
bytedcli lark-devops release audit list-work-items --process-id 12345 -j
bytedcli lark-devops release audit search-work-items --process-id 12345 --type story -j
bytedcli lark-devops release audit add-work-item \
  --process-id 12345 --type story --work-item-key 9000000001 \
  --execute --yes-i-know-this-is-live -j

# 6c. 应用确认（强制规则1+2）
bytedcli lark-devops release audit confirm-apps --process-id 12345 --confirm true \
  --execute --yes-i-know-this-is-live -j

# 7. Submit（只检查前置标志，不自动确认）
bytedcli lark-devops release audit submit \
  --process-id 12345 \
  --execute --yes-i-know-this-is-live -j

# 7b. Submit --auto-confirm（一步到位）
bytedcli lark-devops release audit submit \
  --process-id 12345 --auto-confirm \
  --execute --yes-i-know-this-is-live -j

# 7c. Withdraw / Force-skip
bytedcli lark-devops release audit withdraw \
  --process-id 12345 \
  --execute --yes-i-know-this-is-live -j
bytedcli lark-devops release audit force-skip \
  --process-id 12345 \
  --execute --yes-i-know-this-is-live -j
```

### 2.6 Supporting inspect/debug commands

```bash
bytedcli lark-devops release audit inspect --process-id 12345 -j
bytedcli lark-devops release audit inspect-unit \
  --process-id 12345 --app-id 1001 --stage pre --unit SG_LARK -j
bytedcli lark-devops release audit build-stage \
  --process-id 12345 --app-id 1001 --stage pre -j
bytedcli lark-devops release audit materialize-stage \
  --process-id 12345 --app-id 1001 --stage pre --file plan.json -j
bytedcli lark-devops release audit get-window --process-id 12345 -j
bytedcli lark-devops release audit seed-integrators \
  --process-id 12345 --space-id 67 --app-id 1001 --app-name example.app \
  --execute --yes-i-know-this-is-live -j
bytedcli lark-devops release audit seed-integrators \
  --process-id 12345 --space-id 67 --app-id 1001 --app-name example.app \
  --exclude-unit 9 --execute --yes-i-know-this-is-live -j
bytedcli lark-devops release audit confirm-apps --process-id 12345 --confirm true \
  --execute --yes-i-know-this-is-live -j
bytedcli lark-devops release audit remove-app \
  --process-id 12345 --space-id 67 --app-id 1001 --app-name example.app \
  --execute --yes-i-know-this-is-live -j
bytedcli lark-devops space search --name-like demo-space -j   # 按名字查 space_id
bytedcli lark-devops release get --process-id 12345 -j

# 版本与集群对象无损精细编辑（unit/cluster 级单点增删，底层走 set-apps）
bytedcli lark-devops release audit unit add \
  --process-id 12345 --app-id 1001 --app-name example.app.service --stage pre --unit SG_LARK -j
bytedcli lark-devops release audit unit remove \
  --process-id 12345 --app-id 1001 --app-name example.app.service --stage pre --unit SG_LARK \
  --execute --yes-i-know-this-is-live -j
bytedcli lark-devops release audit cluster add \
  --process-id 12345 --app-id 1001 --app-name example.app.service --stage pre --unit SG_LARK \
  --clusters test --execute --yes-i-know-this-is-live -j
bytedcli lark-devops release audit cluster remove \
  --process-id 12345 --app-id 1001 --app-name example.app.service --stage pre --unit SG_LARK \
  --clusters test --execute --yes-i-know-this-is-live -j
```

### 2.7 Plan-file formats

#### 键名与 PSM 命名约定（必须严格遵守）

- `repo_versions` 的 **键永远是 slash-form** —— 例如 `example/app-service`、`sample/runtime-lib`、`demo/preview-sdk`。不要自行把 `/` 换成 `.` 或 `_`。
- `app_name` / PSM **永远是三段式 dot-form** —— 例如 `example.app.service`。create/add-app/apply-stage 命令的 `--app-name` 传这个值。
- 用户通常会一次性给一张 repo → 版本号的映射（slash-form 键）。Agent 可以直接把它复制进 `plan.repo_versions`，不需要再做键名归一化。

#### 版本预校验（dry-run 就能看到）

`apply-stage` 的结果里 **顶层 `preflight` 块** 是 Agent 判断安全写入与否的唯一信号：

```json
{
  "mode": "dry_run",
  "preflight": {
    "ok": false,
    "unknown_repo_versions": [
      {
        "unit": "CN",
        "repo_name": "sample/runtime-lib",
        "requested_version": "1.0.2.618",
        "available_versions": ["1.0.2.619", "1.0.2.620"]
      }
    ],
    "missing_repo_versions": [],
    "selected_units": ["CN"],
    "skipped_units": [],
    "hint": "plan.repo_versions references versions the platform does not list. ..."
  },
  "materialized": { "...": "..." }
}
```

- `preflight.ok=false` → 必须先修 `plan.repo_versions`（通常是版本号不在候选列表里），再重跑 dry-run，直到 `ok=true` 再 `--execute`。
- `preflight.ok=true` → 可以安全 `--execute`。
- 即便不看 `preflight`，`apply-stage --execute` 仍会在 `unknown_repo_versions` 非空时抛 `LARK_DEVOPS_PLAN_VERSION_NOT_FOUND` 强制拒绝写入，不会静默掉 repo。

**`preflight.ok=false` 时的 Agent 交互协议**：Agent 不应自行猜一个"接近的"版本号替换。正确流程是：

1. 从 `preflight.unknown_repo_versions[]` 取每一项的 `unit` / `repo_name` / `requested_version` / `available_versions`
2. 把失败原因和候选列表**原样回显给用户**，例如：

   > `sample/runtime-lib` 在 unit `CN` 的候选版本里没有 `1.0.2.618`。平台最近可用的版本：`1.0.2.619, 1.0.2.620, …`（共 N 个）。请指定一个新版本，或跳过这个 repo。

3. 等用户明确回复后再更新 `plan.repo_versions`，重跑 dry-run。
4. **不要批量自动改版本、不要去跑 inspect-unit 挑一个最新版自作主张。** 这类决策必须用户拍板。

查看完整候选版本列表时（`available_versions` 默认只返回前 10 条）：

```bash
bytedcli lark-devops release audit inspect-unit \
  --process-id <id> --app-id <id> --stage pre --unit CN --repo-limit 50 -j
# look at data.repo_candidates[].candidates[].version
```

#### 一份 plan 文件能否跨 PRE / GRAY / ONLINE 三阶段复用？

**默认推荐做法：复用同一份 plan**，把它依次传给 `--stage pre | gray | online`。行为：

- 平台对某个 stage 开放的 unit 才会走 `set-apps` 真正写入。
- 某 stage 在平台侧没有任何 `unit_iterms`（典型：关闭了灰度的 app 在 GRAY_RELEASE 阶段），`apply-stage` 会返回 `materialized.stage_auto_skipped=true`、`endpoints: []`、`results: []`。**视作成功不重试。**
- `repo_versions` 通常三阶段一致 —— 同一发布窗口里部署的是同一个 artifact 版本。

**分阶段拆 plan 的情况**（较少见）：

- PRE 只灰一小批 cluster，ONLINE 才对所有 cluster 放量 —— 按 stage 拆 `units` 字段。
- PRE 用 hotfix 版，ONLINE 用正式版 —— 按 stage 拆 `repo_versions`。

拆分时，为每个 stage 起单独文件：`plan-pre.json` / `plan-gray.json` / `plan-online.json`。

#### 默认部署策略：先 deploy-all，精细控制优先走专门 CLI

默认推荐仍是 deploy-all：先用 `build-stage` 看 unit 枚举，再在 plan 里把每个 unit 写成 `{ "is_deploy": true }`。

但这不等于“完全不支持局部开关”：

- **阶段级声明式控制**：`apply-stage` / `apply-release` 的 plan 里可以写 `is_deploy: false`、`cluster_ids`、`all_clusters`、`grayscale_on`、`online_deploy_type`
- **更安全的精细编辑**：如果用户只是想在现有阶段配置上做 unit / cluster 的单点增删，而且不想重新 pin 版本，优先用 `release audit unit add|remove` / `cluster add|remove`；这些命令底层走 `set-apps`，会保留其他 unit 的现有 `version_iterms`

Agent 默认策略：

1. 用户只说“按正常流程发” → deploy-all
2. 用户明确说“只发某几个 unit / 某几个 cluster” → 优先判断是否能用 `unit add|remove` / `cluster add|remove`
3. 用户给的是完整 manifest / plan，希望按声明整体覆盖 → 用 `apply-stage` / `apply-release`

#### Plan 文件示例

参考文件在 `references/release-plans/`。Copy one, edit, pass via `--file`。

**audit-stage-plan.example.json**（`apply-stage` / `materialize-stage` 共用，deploy-all 标准形态）：

```json
{
  "repo_versions": {
    "example/app-service": "1.0.0.6617",
    "sample/runtime-lib": "1.0.2.618",
    "demo/preview-sdk": "1.0.0.693"
  },
  "units": {
    "CN": { "is_deploy": true },
    "US": { "is_deploy": true },
    "SG_LARK": { "is_deploy": true }
  }
}
```

**publish-window.example.json**（仅当你需要覆盖 space 规范窗口时使用）：

```json
{
  "pre_time": { "start": 1776506082, "end": 1776507882 },
  "gray_time": { "start": 1776507882, "end": 1776637482 },
  "online_time": { "start": 1776637482, "end": 1776642882 },
  "desc": "",
  "status": "Done",
  "window_type": 1
}
```

> 正常流程用 `set-window --from-platform` 就够了 —— 平台会返回 space 级规范窗口，CLI 直接回写。**Agent 不应自行编造 start / end 时间戳**。

**dev-add-app-env-items.example.json**（array）与 **dev-update-app-env-item.example.json**（single object）覆盖 DEV-phase 路径。

### 2.8 Entity selection for Agents

- User says "create release" or "起一个发布单" → `release create` (dry-run first)
- User says "add app to release" → `release audit add-app`
- User says "set PRE / GRAY / ONLINE" → `release audit apply-stage --stage {pre|gray|online}`
- User says "set time window" → `release audit set-window --from-platform`（默认路径，不要问用户时间）
- User says "submit" / "提审" → `release audit submit --process-id`；如果用户明确想一步补齐未确认前置，再用 `--auto-confirm`
- User says "confirm-apps 报 not in integrators" / "按钮没出现" / "顶层 integrators 为空" → `release audit seed-integrators`
- User wants to inspect before writing → `release audit inspect` / `inspect-unit`
- User asks for the exact payload → any write subcommand without `--execute`

**Agent 决策默认值（未明确输入时）：**

- **Release 名称**：用户未提供时，默认按 `"<psm> simple release <YYYY-MM-DD>"` 生成（例如 `"example.app.service simple release 2026-04-19"`），在创建前向用户**一行确认**即可；用户沉默视为同意。
- **发布窗口**：永远用 `set-window --from-platform`，不问用户、不自行编造时间戳。
- **Units / Clusters**：默认 deploy-all；若用户明确要做局部增删，优先用 `unit add|remove` / `cluster add|remove`，避免重写整份 plan。
- **Repo 版本**：**simple flow 必须用户显式给版本清单**（SKILL 跟 dev flow 不对称，dev flow 可 default 最新，simple flow 不行）。用户没给时先问："要发的 repo 清单和版本号？"，拿到后才能写 plan.repo_versions。`preflight.ok=false` 时按 §2.7 "交互协议" 回显候选列表给用户，不自作主张换版本。

### 2.9 Behaviors to rely on

- **stage_auto_skipped** — if the platform exposes 0 `unit_iterms` for a stage (typical for GRAY_RELEASE on apps that disable gray), `apply-stage` returns `{materialized.stage_auto_skipped: true, auto_skip_reason, endpoints: [], results: []}` instead of attempting a no-op write. Treat this as **success without side effect** — do NOT retry.
- **preflight (dry-run)** — every `apply-stage` result carries a top-level `preflight` block with `ok`, `unknown_repo_versions`, `missing_repo_versions`, `selected_units`, `skipped_units`. Check `preflight.ok` before `--execute`. If `false`, fix `plan.repo_versions` using `available_versions` hints and re-dry-run.
- **unknown_repo_versions refusal** — live `apply-stage --execute` throws `LARK_DEVOPS_PLAN_VERSION_NOT_FOUND` (with `details.unknown_repo_versions` and available-candidate hint) if `preflight.ok=false`. Fix the plan first, then retry.
- **set-window --from-platform** — `set-window` adopts the space's canonical publish window by calling `/deploy/cd/audit/publish/get` and re-posting the same shape. Prefer this over `--file`; only supply `--file` when a space admin explicitly wants to override the canonical window.
- **submit post-verify** — after calling the submit endpoint, `submit` re-queries `audit/process/list` and checks `status=PENDING` + non-empty `detail_url`. If either fails, the result carries `error: "submit_did_not_start: …"` and `verification.verified=false`. The feishu approval URL is in `verification.detail_url` on success.
- **submit auto-confirm** — `submit --process-id --auto-confirm --execute` runs `confirm-apps` and `set-window --confirm` for the whole process when needed, then calls `audit/process/update/id`.
- **seed-integrators** — when top-level `audit_user_status.integrators` is still empty after the order already contains the app (common on pre-filled / cloned orders), use `release audit seed-integrators`. It re-submits the current app state through `app/update/v2` specifically to register the operator at the work-order level; do not invent `apply-stage` / `set-apps` workarounds for this.

### 2.10 Constraints

- Only `--flow simple` is supported (dev / full flows explicitly disabled)
- **Default deploy-all, but surgical edits exist**：常规流程默认 deploy-all；用户要精细控制时优先用 `unit add|remove` / `cluster add|remove`，其次才是底层 `set-apps`
- **Window is space-level canonical**：始终 `set-window --from-platform`；不问用户、不自行编造时间戳
- **Version mismatch requires user confirmation**：`preflight.ok=false` 时按 2.7 交互协议回显候选给用户，Agent 不自选版本
- `submit` rejects if confirm-apps / window-confirm preconditions are not met (use `release audit inspect`, `confirm-apps`, or `seed-integrators` to debug)
- Space search is read-only; it does NOT auto-resolve `--space-id` in `release create` — always pass numeric `--space-id` explicitly
- `release audit set-apps` is a lower-level escape hatch; prefer `apply-stage` for normal flow
- Real writes are logged on the platform — avoid running live writes against production processes that are already mid-audit

---

## 3. Dev flow (process_type=4, 开发流程发布)

### 3.1 When to use (dev flow vs simple flow 决策)

**选 dev flow（§3）当：**

- 用户明确说 "在 BOE 环境跑/发/测试 feature 分支" / "BOE feature" / "开发流程"
- 用户只想在 BOE 环境验证，**不需要上线** PRE_RELEASE / GRAY_RELEASE / ONLINE
- 用户提供了 BOE feature env tag 名（如 `boe_xxx_test`）

**选 simple flow（§2）当：**

- 用户说 "上线" / "灰度" / "提审" / "发布到生产" / "全量上线"
- 用户提到 `PRE_RELEASE` / `GRAY_RELEASE` / `ONLINE` 任一阶段
- 用户提到审批（audit submit / 提审）、发布窗口（set-window）

**拿不准时询问用户**（常见模糊词）：

| 用户说            | 问用户确认                                                  |
| ----------------- | ----------------------------------------------------------- |
| "测试环境"        | 是 BOE feature 测试（dev）还是 PRE_RELEASE 预发（simple）？ |
| "跑 feature 分支" | 是只在 BOE 验证（dev）还是走完整上线流程（simple）？        |
| "先发一下"        | 目的地是 BOE（dev）还是生产环境（simple）？                 |

两者 `release create` 参数只有 `--flow` 不同，但后续命令完全不共享（`release dev *` vs `release audit *`）。

### 3.2 ⚠️ 环境隔离强约束（必须牢记）

**dev flow 与线上发布流完全隔离。** 这是 dev flow 的第一性原则：

- `deploy_phases` 永远只是 `[1, 2]` = `[DEV, INTEGRATION]`
- CLI 组装 env_items 时，**只允许读取 `app_detail.stage_envs["1"]`（DEV）和 `stage_envs["2"]`（INTEGRATION）**；key `"3"`、`"4"`、`"5"` 对应的 PRE/GRAY/ONLINE 环境绝对不能被读取或写入
- service 层 `assertDevFlowIsolation` 守卫会在任何写路径前检查 payload，出现 `deploy_stage >= 3` / `phase_type >= 3` 的字段立刻抛 `LARK_DEVOPS_DEV_FLOW_LINE_CONTAMINATION` 拒绝写入
- 如果你（Agent）看到这个错误码，**不要重试**，告诉用户 CLI 内部出了一个 bug，不是用户的输入问题

### 3.3 Prerequisites

- **认证**：跟 2.2 一样，Chrome `beops_session` cookie 为主、SSO session 兜底；写操作还需要 `_csrf_token`
- **`--space-id` 必传**：dev flow 跟 simple flow 一样，space 不提供全局默认。User 只给空间名时 agent 通过 `space search --name-like` 解析；没给就问
- **`--app-id` 必传**：同理，通过 `app search --psm` 解析
- **`--boe-feature` 必须是已注册 tag**：先跑 `release dev list-boe-features --psm <psm>`（见 §3.5 step 0）；首次用一个新 tag 让用户去 UI 注册

### 3.4 Strict sequence for `--flow dev`

**六步顺序，不可颠倒**（顺序错 agent 会踩 TCE 锁 / 空 pipeline 等陷阱）：

```
1. release create --flow dev
2. release dev add-app                           # 单 app 走 flag，多 app 走 --file
3. release dev execute-pipeline --phase dev      # 部署 BOE feature 服务（必须先于 integrate）
4. release dev integrate                         # 建 MR，BOE feature → BOE prod
5. release dev execute-pipeline --phase integration  # 跑合并后的 pipeline
6. release dev finish                            # 手动收尾（平台不会自动 finish）
```

**关键顺序语义：**

- **Step 3（`--phase dev`）必须在 Step 4（integrate）之前**：DEV pipeline 负责把 feature 分支代码部署到 BOE feature 环境；没跑它直接 integrate 会基于未部署的代码建 MR，后续 integration pipeline 会失败
- **Step 5（`--phase integration`）必须在 Step 4（integrate）之后**：INTEGRATION phase 的 env_items 是 integrate 创建出来的；integrate 之前该 phase 没东西跑
- `execute-pipeline` 两次调用**必须显式指定 `--phase`**（CLI 不给默认值，避免歧义）

### 3.5 Commands

**Step 0 — 资源发现**

```bash
# user 只给空间名 / PSM？先解析 id
bytedcli lark-devops space search --name-like <keyword> -j   # → space_id
bytedcli lark-devops app search --psm <psm> -j               # → app_id

# 查这个 PSM 下已经在平台注册的 BOE feature tag 列表
bytedcli lark-devops release dev list-boe-features --psm <psm> -j
# 返回 data.features[]: [{env: "boe_xxx", service_id: N}]
# 用户给的 --boe-feature 必须在这个列表里；不在就让用户去 UI 注册
```

```bash
# 1. Create
bytedcli lark-devops release create --space-id 69 --name "demo-dev" --flow dev -j
bytedcli lark-devops release create --space-id 69 --name "demo-dev" --flow dev \
  --execute --yes-i-know-this-is-live -j

# 2a. Add app — single-app shortcut（最常用），--boe-feature 必填
bytedcli lark-devops release dev add-app \
  --process-id 12346 --app-id 1002 --branch feat/demo \
  --boe-feature boe_my_test_env -j

# 2b. Add app — declarative batch form（多 app）
bytedcli lark-devops release dev add-app --process-id 12346 --file apps.json -j

# 2c. Add app — live
bytedcli lark-devops release dev add-app \
  --process-id 12346 --app-id 1002 --branch feat/demo \
  --boe-feature boe_my_test_env \
  --execute --yes-i-know-this-is-live -j

# 3. DEV pipeline — 部署 BOE feature（必须先于 integrate）
bytedcli lark-devops release dev execute-pipeline \
  --process-id 12346 --phase dev --wait --timeout-ms 1800000 \
  --execute --yes-i-know-this-is-live -j

# 4. Integrate — 建 MR（BOE feature → BOE prod）
bytedcli lark-devops release dev integrate --process-id 12346 \
  --execute --yes-i-know-this-is-live -j

# 5. INTEGRATION pipeline — 跑合并后的代码（必须在 integrate 之后）
bytedcli lark-devops release dev execute-pipeline \
  --process-id 12346 --phase integration --wait --timeout-ms 1800000 \
  --execute --yes-i-know-this-is-live -j

# 6. Finish — 平台不会自动 close，必须手动调
bytedcli lark-devops release dev finish --process-id 12346 \
  --execute --yes-i-know-this-is-live -j
```

### 3.6 add-app 的两种入参形态

**形态 A：单 app flag 快捷形式**

```bash
--process-id <id> --app-id <id> --branch <feat/xxx> --boe-feature <tag> [--repo-versions-file file.json]
```

**形态 B：声明式批量 file（Agent 编程最友好）**

`apps.json`:

```json
{
  "apps": [
    { "app_id": 1002, "branch": "feat/foo", "boe_feature": "boe_my_test_env" },
    {
      "app_id": 1789,
      "branch": "feat/bar",
      "boe_feature": "boe_my_test_env",
      "repo_versions": { "ee/example/dep": "1.0.0.123" }
    }
  ]
}
```

**规则：**

- 两种形态**互斥**（类似 `set-window --file` vs `--from-platform`）
- `app_id` / `branch` / `boe_feature` 三者都是**必填**；`repo_versions` 可选
- `boe_feature` 是任意符合 `^boe_[a-zA-Z_0-9]{1,26}$` 的字符串（见 §3.10）；first-time tag 由 pipeline 懒创建，无需用户预先在 UI 注册。但 Agent 仍应跟用户确认 tag 名（避免 typo），不要自行随机生成
- `repo_versions` 未指定的依赖库自动取平台最新版本；键用 **slash-form**（`ee/example/dep`）
- 主仓库由 `--branch` 指定分支，不需要在 `repo_versions` 里列它

### 3.7 add-app 的 preflight

dry-run 返回的 `preflight` 块是 Agent 写前判断的唯一信号：

```json
{
  "mode": "dry_run",
  "process_id": 12346,
  "phase_id": 555,
  "preflight": {
    "ok": true,
    "resolved_apps": [ ... ],
    "unknown_branches": [],
    "unknown_repo_versions": [],
    "unknown_boe_features": [],
    "line_contamination_check": "pass"
  }
}
```

- `preflight.ok=true` → 可安全 `--execute`
- `preflight.ok=false` → 看以下两个 blocker 字段定位问题，**向用户回显** 候选信息让用户确认，**不要自行挑版本**
- 即便不看 preflight，`--execute` 会在 preflight 失败时直接抛 `LARK_DEVOPS_DEV_ADD_APP_PREFLIGHT_FAILED` 强制拒写

**两个 hard-blocker：**

1. **`unknown_repo_versions`** — 用户 `--repo-versions-file` pin 的版本不在 `scm/versions` 候选里。回显 `available_versions` 给用户选
2. **`line_contamination_check: fail`** — payload 出现 `deploy_stage >= 3`（严重 bug，不是用户错）

**soft warnings（不 block execute）：**

- `unknown_branches` — `search_branch` 探测失败，通常是误判，平台自己会在 execute 时验证
- `unknown_boe_features` — 用户的 `--boe-feature` 是个**全新标签**，还没在 `get_boe_tag_list` 出现过。**这不是错误**：pipeline 的 "Init BOE Env and deploy" 步骤会在 deploy 时**懒创建** TCE service，first-time tag 完全支持端到端。保留这个软提示主要用于 **typo 防护**——如果用户想用一个已存在的 tag 但拼错了，preflight 里的 `registered_features` 候选列表能帮用户立刻发现拼写差异

### 3.8 Agent 决策默认值

- **Release 名称**：未提供时默认 `"<psm> dev release <YYYY-MM-DD>"`（如 `"example.app.entity dev release 2026-04-19"`），提前向用户一行确认
- **主仓库分支**：必须用户指定，CLI 不自动挑。分支在 SCM 不存在时 preflight 失败
- **依赖库版本**：未指定 → 平台最新版；用户在 `repo_versions` 显式指定 → 锁定并校验
- **Units**：dev flow 无 unit 概念（固定 BOE），无需配置
- **发布窗口**：不适用（dev flow 无发布窗口）
- **finish 时机**：pipeline 跑完（`execute-pipeline --wait` 返回 `SUCCESS` 之类）后才调 `dev finish`

### 3.9 错误码

- `LARK_DEVOPS_DEV_FLOW_LINE_CONTAMINATION` — 线上环境污染（严重 bug，不是用户错）
- `LARK_DEVOPS_DEV_ADD_APP_PREFLIGHT_FAILED` — preflight 失败后仍 `--execute`（`unknown_repo_versions` 或 `line_contamination` 命中）
- `LARK_DEVOPS_INPUT_ERROR` — 普通参数校验失败（缺 `--branch`、`--file` 结构错等）

### 3.10 BOE feature 标签由 pipeline 懒创建

- `boe_feature` 是个**自由字符串字段**，写进 `env_item.attrs.boe_feature` 即可。平台不要求"预注册"
- `get_boe_tag_list` 返回的是**已部署过的 tag 历史**（每条对应一个 TCE service_id），不是必填白名单
- 首次用一个新 tag：**直接传**给 `dev add-app --boe-feature` 即可。Pipeline 的 "Init BOE Env and deploy" 步骤会在 deploy 时**懒创建** TCE service，下次再查 `get_boe_tag_list` 才会出现该 tag
- preflight 里 `unknown_boe_features[*].registered_features` 仍然列出"已部署历史"，用于 **typo 防护**——agent 应在 hint 里看到 `unknown_boe_features` 软警告时，先比对一下历史列表确认不是拼错；如果用户本意就是新 tag，直接 `--execute` 即可
- **格式约束**：tag 名必须匹配 `^boe_[a-zA-Z_0-9]{1,26}$`（总长 ≤ 30 字符，`boe_` 前缀 + 1~26 字符后缀）。超长或非法字符会在后端 PPE 原子工单阶段被拒，浪费一次 pipeline run

### 3.11 Constraints

- `--flow dev` 与 `--flow simple` 共享大部分 `release create` 参数；只有 `process_type` / `deploy_phases` 不同
- **不支持** dev flow 进阶到 AUDIT/PRE/GRAY/ONLINE —— 那是 simple flow 的链路；需要线上发布请另起一单 simple flow
- `release dev update-app` 是低层逃生口（传 raw JSON env_item），标准流程请用 `dev add-app`
- `dev finish` 必须手动调 —— pipeline 完成后工单不会自动 close
- `scm_type` 每个 repo 版本不同（主仓 `offline`；依赖从 `scm/versions.results[].type` 拿，通常 `online`，偶尔 `test`）。CLI 自动从平台取，不要硬编码。极端情况下平台响应没有 `type` 字段（历史数据），CLI fallback 为 `"online"` —— 如果 pipeline 因此在 i18n 挂，让用户改用 `--repo-versions-file` 精确 pin 一个新版本
- `boe_feature` 可以是任意符合 `^boe_[a-zA-Z_0-9]{1,26}$` 的字符串；first-time tag 由 pipeline 现创建，详见 §3.10

---

## 4. FG (Feature Gate)

### 4.1 When to use

- 按 feature_key 查 FG 在各地区 / 环境下的数字 ID、状态、管理员
- 按 feature_key 或数字 ID 查 FG meta / 灰度规则（rule）版本内容
- 新增 / 删除 FG 灰度规则（用户 ID、租户 ID、会话 ID、部门 ID、自定义规则等）
- 按发布工单 ID、FG 数字 ID 或 feature_key + 时间窗查询 FG 发布工单

### 4.2 Prerequisites

FG Open API 需要 app_id + app_secret 鉴权（应用身份，与 1.2 的 SSO session 无关）：

```bash
bytedcli lark-devops fg auth config --app-id <your-app-id> --app-secret <your-app-secret>
```

或环境变量：`BYTEDCLI_LARK_DEVOPS_FG_APP_ID`、`BYTEDCLI_LARK_DEVOPS_FG_APP_SECRET`；也可以在 fg 的查询 / 写命令（`feature search`、`meta get`、`rule get|create|delete`、`ticket list`）上临时传 `--app-id` / `--app-secret`（不落盘）。

### 4.3 Quick start

```bash
bytedcli lark-devops fg auth config --app-id example-app --app-secret example-secret
bytedcli lark-devops fg auth status

# 1) 按 feature_key 找数字 ID（每个 app x unit x env 一行；不带 --unit 列出全部地区）
bytedcli lark-devops fg feature search --feature-key example.key
bytedcli lark-devops fg feature search --feature-key example.key --unit cn --app Feishu
# 批量精确查多个 key（最多 99 个）；模糊搜索走 --keyword，用 --page/--page-size 翻页
bytedcli lark-devops fg feature search --feature-key example.a example.b --unit cn
bytedcli lark-devops fg feature search --keyword example --unit cn --page 1 --page-size 20

# 2) 查灰度规则 / meta：可直接用 feature_key + unit（内部自动解析 ID），或用数字 ID
bytedcli lark-devops fg rule get --feature-key example.key --unit cn --app Feishu
bytedcli lark-devops fg rule get --id 6910
bytedcli lark-devops fg rule get --id 6910 --versions 1 18
bytedcli lark-devops fg meta get --feature-key example.key --unit boecn

# 3) 写规则：用 feature_key + app + unit
bytedcli lark-devops fg rule create --feature-key example.key --app Feishu --unit cn \
  --user-id uid1 uid2 --comment 'Add test users'

bytedcli lark-devops fg rule create --feature-key example.key --app Feishu --unit cn \
  --entity-ids id1 id2 --comment 'Add custom entities'

bytedcli lark-devops fg rule delete --feature-key example.key --app Feishu --unit cn \
  --user-id uid1 --comment 'Remove test user'

# 4) 发布工单：--ticket-id 是工单 ID；--id 是 FG 数字 ID（先查 meta 拿 key 再搜）；按 key 查默认最近 180 天，可用 --start/--end 收窄
bytedcli lark-devops fg ticket list --ticket-id 123456
bytedcli lark-devops fg ticket list --id 6910
bytedcli lark-devops fg ticket list --feature-key example.key --unit cn
bytedcli lark-devops fg ticket list --feature-key example.key --start "30d ago" --publish-type rule --status published
```

### 4.4 FG Notes

- **按 feature_key 查灰度数据**：`fg rule get --feature-key <key> --unit <unit>` 是推荐入口。同一个 key 在 `Feishu` 与 `Lark` 两个 app 下各有一个 ID，若同时存在会报 `FG_FEATURE_AMBIGUOUS` 并列出候选，补 `--app Feishu` 或直接 `--id` 即可。
- **数字 ID 的语义**：FG 的 ID 按 app x unit x env 维度分配，`fg feature search --feature-key <key>` 不带 `--unit` 即列出该 key 在所有地区的 ID；`fg meta get` / `fg rule get` 走 `--id` 时 `--app/--unit/--env` 会被忽略。
- **`--versions`**：默认 `-1` 表示最新线上版本；多个版本用空格或逗号分隔（`--versions 1 18`）。
- **`fg feature search --status`** 取 FG 状态语义值：gray（灰度）、closed（关闭）、open（全量）、tob_gray、archived（已下线 / 归档）、new。响应里的 `rule.status` 数字含义相同：0 gray、1 closed、2 open、3 tob_gray、5 archived、6 new。
- **灰度比例是千分比**：`ratio: 800` 表示 80%。`conditions[].is_black=true` 是黑名单，黑名单优先于白名单。
- **工单查询**：`fg ticket list --ticket-id` 传的是**发布工单 ID**；`--id` 与 `meta get` / `rule get` 一样是 FG 数字 ID，CLI 会先查 meta 拿到 feature_key 与 app/unit/env 再搜工单（多一次请求，显式传的 `--app/--unit/--env` 优先）。按 `--id` / `--feature-key` 查时后端要求时间窗且不超过 180 天，CLI 默认取最近 180 天，可用 `--start "30d ago"` / `--end 2026-01-31` 收窄；`--fuzzy` 支持按 key 前缀模糊匹配。`--status` 取工单状态语义值：unpublished、pending_approval、rejected、approved、published、failed、cancelled、rolled_back、preparing；`--publish-type` 取 create、delete、meta、rule。`--start/--end/--page/--page-size` 只对 `--id` / `--feature-key` 查询生效。
- **app** 枚举值：Feishu, Lark, Docs, Smartable, Lark_Meetings, Meego, Miigo, EA, People（大小写敏感）
- **unit** 枚举值：cn, va, larksgaws, larkjpaws, larkmy, useast15a, uswest5a, eu_nc6（线上）; boecn, boeva（BOE）
- **env** 可选，不传时按 unit 自动映射：boecn/boeva → staging，其他 → online
- 条件规则与自定义规则互斥，每次请求只能传一类
- FG 发布工单串行：如有工单未到终态，写操作会被阻塞
- `--comment` 强烈建议填写变更原因
- 接口统一走 `https://lark-devops.bytedance.net`（含 BOE 数据）
- 文本模式下 `rule get` / `meta get` 先打印摘要，再原样输出版本列表 JSON；`-j` 模式的 `data` 为 `{ feature: { id, feature_key, app, unit, env }, total, list }`（走 `--id` 时 `feature` 里除 `id` 外为 `null`）。`ticket list` 的 `data` 为 `{ feature, total, page, page_size, started_at, finished_at, list }`（按工单 ID 查时 `feature` 内字段与这四个分页 / 时间窗字段为 `null`）。

---

## 5. Lark Scheduler（调度服务，processor / job 查询 + 触发审核工单）

lark-devops 平台「开发者工具」下的 Lark Scheduler 子应用，区别于通用 ByteCloud cronjob。命令前缀 `lark-devops scheduler`，认证复用 lark-devops 飞书登录。

### 5.1 When to use

- 查询 Lark Scheduler processor（处理器）配置列表，支持按 `--api-name` 过滤
- 列出某环境下的 job（定时任务）配置
- 获取单个 job 的配置详情
- 查看某个 job 的执行历史（instance 运行记录）
- 申请「立即触发」一个 job（走审核工单，需审核人 + 原因；默认 dry-run 预览，确认无误后再真正提交）

### 5.2 Commands

```bash
# 列出 processor 配置（支持 --api-name 客户端过滤，--unit / --region 选择环境）
bytedcli lark-devops scheduler processor list \
  --api-name "demo-processor" --page 1 --page-size 20 --unit cn --region online

# 列出 job 配置
bytedcli lark-devops scheduler job list \
  --page 1 --page-size 20 --unit cn --region online

# 获取单个 job 配置详情
bytedcli lark-devops scheduler job get \
  --id 1234567890 --unit cn --region online

# 查看某个 job 的执行历史（instance 运行记录）
bytedcli lark-devops scheduler job run list \
  --id 1234567890 --page 1 --page-size 20 --unit cn --region online

# 申请触发一个 job（走审核工单）—— 默认 dry-run，仅打印将提交的工单内容，不真正提交
# --reviewer / --reason 为提交所必填；reviewer 必须是该 job 的合法 operator 且不能是自己
bytedcli lark-devops scheduler job trigger \
  --id 1234567890 --reviewer demo-operator --reason "demo reason"

# 申请触发一个 job —— 确认无误后加 --yes 才真正提交审核工单
# 可选 --parameter 覆盖触发参数、--container 指定容器
bytedcli lark-devops scheduler job trigger \
  --id 1234567890 --reviewer demo-operator --reason "demo reason" \
  --parameter '{"key":"value"}' --yes

# 切换环境（unit + region）并以 JSON 输出（--json 是全局选项，放在子命令之前）
bytedcli --json lark-devops scheduler job list \
  --unit i18n --region online_staging
```

### 5.3 Notes

- `job trigger` 是写操作，语义是**申请「立即触发」审核工单**（不是直接执行）：提交后需审核人通过才会真正触发。**默认 dry-run**（仅打印将提交的工单内容，不实际提交）；确认无误后显式加 `--yes` 才真正提交。`--reviewer`（审核人 username）与 `--reason`（申请原因）为提交所必填，且 reviewer 必须是该 job 的合法 operator、不能是申请人自己；`--parameter` 可选，覆盖触发参数（多数 job 是纯命令字符串，部分是 JSON object，按该 job 实际格式传）；`--container` 可选，指定容器。注：本命令的确认 flag 是单 `--yes`，与本 skill 其他 lark-devops 写命令（发布 / 网关，用 `--execute --yes-i-know-this-is-live` 双 flag）不同——因为 trigger 只是**提交审核工单**（需审批人通过后才真正执行），风险量级低于那些直接真实执行的写操作
- **如何确定 `--reviewer`**：①用 `job get --id <jobID>` 查看 `operators` 字段（最直接）；②跑一次带合法 `--reviewer`/`--reason` 的 dry-run，输出含 `candidate_reviewers`。传入缺失/非法 reviewer 时（reviewer/reason 校验在 dry-run 之前），报错 hint 也会列出该 job 的候选审批人
- 多环境：`--unit` 选择控制面（`cn` / `i18n` / `boe` / `us-ttp`，默认 `cn`），`--region` 选择具体 region（默认 `online`，例如 `online_staging` / `cn6` 等）

---

## 6. Owl SLA (read-only)

### 6.1 When to use

任何与 Lark Owl SLA 平台相关的查询场景:

- 想看一个功能节点的 SLA 数值、SLO 阈值、规则配置、低点列表、关联告警状态/规则,或 Grafana 大盘地址
- 想看功能树结构(树 / 单节点元信息 / SLA 规则配置覆盖率)
- 想看一个节点的告警规则在不同 vRegion 是否都配齐
- 涉及 8 个 vRegion 的 SLA 查询(CN 区: `CHINA_NORTH` / `CHINA_NORTH6`,I18N 区: `SINGAPORE_COMMON` / `SINGAPORE_SAAS` / `ASIA_SAAS` / `ASIA_CIS` / `US_EE` / `US_TTP3`)
- 在 oncall / 复盘 / 巡检场景下,需要把"打开 Owl SLA 页面拷数据"替换成 CLI 一行

### 6.2 Prerequisites

跟其它 `lark-devops` 命令共用 `lark_devops_session.json` cookie 鉴权,不需要额外登录。第一次跑会自动引导 SSO。

### 6.3 vRegion 取值

接受以下任一形式(handler 内统一规范化为后端 canonical 值):

| Canonical          | 友好别名          | 含义                |
| ------------------ | ----------------- | ------------------- |
| `CHINA_NORTH`      | `cn` / `cn-north` | 中国北部(默认主区)  |
| `CHINA_NORTH6`     | `cn-north6`       | 中国北部六区        |
| `SINGAPORE_COMMON` | `sg-common`       | 新加坡教育通用      |
| `SINGAPORE_SAAS`   | `sg-saas`         | 新加坡 SaaS         |
| `ASIA_SAAS`        | `asia-saas`       | 亚洲 SaaS           |
| `ASIA_CIS`         | `cis` / `mycisb`  | 马来合规机房 MYCISB |
| `US_EE`            | `us-ee`           | 美国 EE             |
| `US_TTP3`          | `us-ttp3`         | 美国 TTP3           |

也接受 deploy-region 显示名(`China-North` / `Singapore-SaaS` 等)。不识别时抛带 `hint` 的结构化错误。

> 注:`sla` 子树用 `--vregion`,与 `lark-devops` 其他写命令的 `--region`(deploy unit)是**两个不同维度的概念**,不要混用。

### 6.4 Commands

```bash
# 元数据枚举
bytedcli lark-devops sla region list              # 8 个 vRegion
bytedcli lark-devops sla type list                # SLA 数据类型(后端/客户端/WEB端)
bytedcli lark-devops sla metric list              # 7 个结构化 SLA 指标类型
bytedcli lark-devops sla metric-tag list --type BYTE_TRACE_CLIENT_RATE

# 功能节点 / 子树 / SLA 规则覆盖率
bytedcli lark-devops sla feature get --node-id <id>
bytedcli lark-devops sla tree get --node-id <id> [--depth 3]
bytedcli lark-devops sla coverage get --node-id <id>

# SLA 规则配置(SLO + 算法 + 子节点权重 / 表达式)
bytedcli lark-devops sla rule get --node-id <id> --vregion cn \
    [--data-type backend|app|pc_web]

# SLA 数值 / 趋势 / 低点(时间窗默认 last-24h)
bytedcli lark-devops sla value get --node-id <id> --vregion cn \
    [--start "1h ago"] [--end "now"]
bytedcli lark-devops sla trend get --node-id <id> --vregion cn \
    [--start "12h ago"]
bytedcli lark-devops sla low-point list --node-id <id> --vregion cn \
    [--data-type backend] [--levels L0,L1] [--page-size 50]

# 告警关联(三态 status + 完整 bosun 规则)
bytedcli lark-devops sla alarm status --node-id <id> [--data-type backend]
bytedcli lark-devops sla alarm-rule list --node-id <id> \
    [--vregion cn]                  # 不传 --vregion = 跨所有 8 个区域一把拉
    [--raw]                          # 输出完整 bosun 表达式 + 通知/升级配置

# Grafana 大盘
bytedcli lark-devops sla dashboard list --node-id <id> --vregion cn
```

### 6.5 Notes

- `alarm-rule list` **默认跨区域** —— `infos` 接口一次返回该节点在所有 vRegion 的告警规则;传 `--vregion` 才本地过滤到单区域。这是 Owl 平台官方语义,不是 CLI 取巧
- 时间窗参数(`--start` / `--end`)接受 ISO-8601 / 毫秒时间戳 / 秒时间戳 / 相对时间(`1h ago` / `30m ago`),省略时默认 last-24h
- `--data-type` 接受 `backend` / `app` / `pc_web`,以及友好别名 `client`(→ app)/ `web`(→ pc_web)/ `pc-web`(→ pc_web)
- 三态告警关联 `status`:`ASSOCIATED_RULE`(已配)/ `UNASSOCIATED`(应配未配,UI 红 badge)/ `NO_ASSOCIATION_RULE_REQUIRED`(此节点无需告警,例如 sandbox / L3 待定节点)
- `feature get`(单节点元信息)与 `tree get`(子树)是两个独立接口,前者用于看单点,后者用于浏览/批量。`coverage get` 看的是"子树内已配 SLA 规则节点占比"
- 全量列表 / 低点表用 `-j` 输出 JSON 后用 `jq` 过滤更顺手,典型用法见 [Invocation](../../invocation.md)

---

## References

- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
- [Page to CLI Mapping](references/page-to-cli.md)
- [Release plan examples](references/release-plans/)
  - `audit-stage-plan.example.json`
  - `audit-set-apps.example.json`
  - `release-manifest.example.json`
  - `publish-window.example.json`
  - `dev-add-app-env-items.example.json`
  - `dev-update-app-env-item.example.json`
