---
name: forge-cli
description: "通过 forge 操作 ByteDance Forge 平台时使用 —— 涵盖代码、编译、训练任务、任务观测/诊断、推理部署。code fetch/update（Forge/Git workspace）、code meta get/update（查看/切换 framework 版本）、code commit create/get/list/diff、code compile create/get（model/norbert 编译、本地编译、本地验证、compile graphs/GPU Graphs、compile logs、wait/poll build）、code compile-artifact get（下载模型编译产物）、forge localrun（ForgeIDE 调试）、job list/create/kill/owner transfer/priority update（含共享权重 only-register 任务）、job norbert-commit list/update、job primus-crd get/list/diff/update（primus 热更）、job sdp exec（RoW 合规容器单命令）；job 观测：stage get/list、checkpoint list/save/delete、meta（含共享权重子任务）、event、log、metrics、utilization（CPU/GPU）、deepinsight（AUC/UAUC/NDCG、校准、bias）、wandb/tensorboard get-meta+query；PS状态/FID/embedding查询、serving/MaaS部署、Dense Snapshot 查询/pin/unpin与Haven版本、quota 资源组/结算单元/任务/配额变更记录/配置变更与配额申请/释放/转移/出让/回收/迁移、job webshell list/exec。Triggers: 编译异常、localrun、共享权重子任务、Primus CRD/热更/查询、Vela指标、训练日志/指标、转移 owner、更改任务资源组、Norbert commit 更新/热更、wandb/tensorboard 打点异常或丢点、资源巡检/巡检白名单、SDP/合规容器操作、webshell 进 pod。"
version: v0.20.0
---

# forge-cli

Use this skill for any task that touches the Bytedance Forge workflow through `forge`. It covers the full chain from fetching code to submitting jobs and observing them.

## Workflow chain

```text
code fetch  ->  edit locally  ->  code commit create  ->  code compile create / get  ->  job create  ->  job priority update / job observe (stage get|list / profiling-timeline list / memory-snapshot list / checkpoint list / primus-app get / primus-role list / primus-pod list|get / meta / event / log / metrics / utilization / deepinsight / wandb / tensorboard) / job checkpoint save|delete / job primus-crd config / job kill
```

Each fetched version is a Forge workspace with `.forge/forge_meta.json`; later stages read that workspace metadata from the current directory or its parents so users rarely repeat derived flags. Keep using the same workspace through one workflow.

## Control-plane preflight (MUST before any `forge` command)

Before assembling a `forge` command, extract the target `--site` from the user's text. If a site is found, pass it explicitly on every `forge` command in the workflow; never rely on the default site. Treat the site as sticky across follow-up commands for the same job/version/workspace. If user-provided signals imply conflicting sites, stop and ask before running, especially before mutating commands.

Exception: `forge localrun` is a local-only proxy to the ForgeIDE `localrun` binary. Do **not** add `--site` / `--network` to `forge localrun` commands; localrun does not understand Forge runtime flags. If a user already includes those global flags, forge strips them before launching localrun.

Control-plane words map as follows: `cn` -> `--site cn`; `i18n`, `row`, or explicit `us 控制面` / US control-plane wording -> `--site i18n`; `euttp` / `eu-ttp` -> `--site eu-ttp`; `usttp` / `us-ttp` -> `--site us-ttp`. Only treat `us` as i18n when it is clearly a site/control-plane signal, not any unrelated occurrence of the word. Bare `ttp` / `TTP 区域` is ambiguous between `eu-ttp` and `us-ttp`; do not default it to either site. The single biggest trap: `us 控制面` is i18n/row, not us-ttp.

## URL site inference

Before assembling any `forge` command from a Forge2/Reckon URL, infer the target `--site` from the URL hostname and pass it explicitly on every command in the same workflow. Do not fall back to the default site after extracting a job id, stage id, or version id from a URL. If URL-derived site and user text disagree, stop and ask before running, especially before mutating commands.

Hostnames map as follows: `reckon.bytedance.net` -> `--site cn`; `reckon-us.tiktok-row.net` -> `--site i18n`; `reckon-eu.tiktok-row.net` -> `--site eu-ttp`; `reckon-ttp.tiktok-row.net` -> `--site us-ttp`.

Auxiliary auth never changes the target site. A `--site us-ttp` code workflow stays `--site us-ttp` even if the bridge asks the user to refresh i18n and us-ttp login; an i18n job webshell command stays `--site i18n` even if session repair uses `forge auth login --begin --session --site cn`.

## Control-plane confirmation

Before the first site-relevant `forge` command in a workflow, including any prerequisite `forge auth status --site <site>` check, resolve the intended site. If neither the user's text nor any URL yields a site and no `--site` is already sticky in the conversation, first check the ForgeIDE signal: when the ForgeIDE precondition holds and `FORGE_IDE_DEPLOY_REGION` maps to `cn` or `i18n`, use that deployment environment as the sticky site and skip the question. Otherwise, run `forge config show` and read `runtime_source.site`.

If `forge config show` output has no `runtime_source` key, the binary predates this field: run `forge upgrade`; if upgrading is not possible, treat it as `default`.

- `flag` or `pinned`: use `runtime.site` as the sticky site for the conversation without asking.
- `default`: stop and ask which control plane to use, offering exactly `cn` (CN control plane), `i18n` (RoW / "us control plane"), `eu-ttp` (EU-TTP), and `us-ttp` (US-TTP). In the same question, ask whether to persist it with `forge config set --site <site>` so future conversations skip the question; run that command only after an explicit yes. Ask only when a person can answer in an interactive conversation. In a non-interactive or unattended run (a scheduled or cron-triggered routine, batch or CI execution, no user present, or the agent was told not to ask), do not ask: proceed with `runtime.site` as before, and state in the output that the site was not specified and `<site>` was used, together with the fix (`--site <site>` in the prompt, or `forge config set --site <site>` on that machine).
- Never infer candidates from `auth`; Global accounts commonly populate all four sites, so that inventory does not identify the user's control plane.

Ask at most once per conversation. After the user chooses, keep the site sticky and pass `--site <site>` explicitly on every site-relevant command. Do not ask when the user already named a site, when a site is already sticky, or for `forge localrun`, `forge config`, `forge version`, or `forge upgrade`, where the site is irrelevant. `forge auth` is site-scoped and is not on this list; the explicit fixed-site exception is browser-session repair with `forge auth login --begin --session --site cn`.

## Framework source provenance guard (MUST)

Before fetching, checking out, or reading framework source for any compile, job, localrun, serving, or series diagnosis:

1. Resolve the exact executing Forge commit: use the selected build's `commit_id` for compile diagnosis; use the selected stage's model `commit_id` for model/framework failures and its `norbert_commit_id` for Norbert-specific failures.
2. On the same Forge site, run `forge code commit get --commit-id <id> --output-dir <empty-dir> --site <site>` for that exact commit.
3. Use only the command's `framework` and `framework_version` fields as the framework source coordinates.

Never infer, replace, or override these fields from compile logs, job or Primus logs, `code commit list`, version/workspace metadata, an installed environment, or a latest/default version. If the exact commit cannot be resolved, `commit get` fails, or either field is empty, stop and report that framework source provenance is unavailable; do not fall back. This guard applies to agent-side framework source inspection, not to the CLI's normal workspace-driven compile request assembly.

## Training pod / executor routing guard (MUST)

Before locating a training pod, judging an executor's state, or choosing a container-operation path, read [references/primus_pods.md](references/primus_pods.md) in full and follow these rules:

- **Primus History is the Source of Truth** for training pod inventory, executor attempt/version expansion, and pod lifecycle state. Keep the target stage explicit: when the user supplies or selects a `stage_id`, run `forge job meta get --job-id <id> --stage-id <stage-id> --site <site>` and verify the returned `latest_stage.stage_id`; omit `--stage-id` only when the latest stage is intentionally the target. Use `latest_stage.links.primus_history_original` for audit/handoff and `latest_stage.links.primus_history_access` for navigation. With an older CLI that lacks `latest_stage.links`, preserve `latest_stage.primus_history_url` and apply only the documented US-TTP host rewrite. Then inspect the relevant role's pod rows: use all lifecycle states to reconstruct attempts and `RUNNING` rows to select current live attempts.
- Treat `latest_stage.links.primus_bdee` and `latest_stage.links.dorado_bdee` as opaque, service-provided BDEE jump targets. Surface them when the requested compliant operation belongs there; never synthesize a BDEE URL from a job, stage, or hostname table.
- A logical executor such as `executor_stream_395` is not one concrete pod. Expand all attempt/version rows such as `executor_stream_395_0`, `_1`, `_2`, and use the current `RUNNING` attempt as the diagnosis or operation target. Never infer the active attempt from suffix order, the first row, or `forge job webshell list`.
- `forge job webshell list` is **not** a Source of Truth for Primus pod inventory, attempt identity, or lifecycle state. When explicitly requested, it may run without a pre-resolved target and return non-authoritative webshell candidates. Resolve a concrete `RUNNING` attempt from Primus History before executor exec or any lifecycle conclusion.
- `forge job webshell exec` is **not** the default container-operation entrypoint. For RoW (`--site i18n`), read-only diagnosis starts with Primus History/logs. Native SDP execution runs one compliant command in the exact pod, including current Primus-on-Godel (`nj-*`) jobs. For EU/TTP (`--site eu-ttp` / `--site us-ttp`), default to Primus History and `forge job log query --log-type primus`; on the office network that command can use the Footprint-backed read path after Primus resolves the executor/file URL.
- For an explicit RoW container operation, use native `forge --site i18n job sdp exec` after the user has supplied or selected one exact AM or concrete executor target. Forge binds the selected/latest stage, revalidates a unique `RUNNING` executor attempt, then creates the SDP session by following that pod's service-provided webshellauth URL with `type=sdp` appended (webshellauth resolves the pod IP/container id and picks the OS user server-side, building the `T_GENERAL` session). It needs the CN browser SSO session (acquire it through the non-blocking step-4 flow below — never the bare blocking `forge auth login`, except the rejected-QR fallback in step 4) plus an i18n ByteCloud user JWT. Keep the command single-line and bounded, and rely on SDP's server whitelist. Do not invoke or require `bytedcli`. For EU/TTP/CN or missing authoritative metadata, use the explicit handoff in `references/primus_pods.md`.
- Use Forge webshell only when the user explicitly asks for `forge job webshell` and the target environment/access path has already been confirmed usable. Do not create an automatic `webshell list -> webshell exec` loop.

## Prerequisites (read [invocation.md](references/invocation.md) for details)

Complete [Control-plane confirmation](#control-plane-confirmation) before step 2: `forge auth status --site <site>` is site-relevant and must not run until `<site>` is resolved.

1. **Install**: `forge version` — if missing, install via the shipped install.sh (see `invocation.md`).
2. **Auth**: run `forge auth status --site <site>`. Default/`auto` identity is injected JWT → user login only; configuring AK/SK never makes Forge silently switch principals. For headless application identity, configure AK/SK **and** `BYTECLOUD_AUTH_AS=app`, then run the same status command. `BYTECLOUD_AUTH_AS=user|app` is strict after the injected-JWT seam. Before proposing any login, check for a pre-provisioned shared credential store: if `BYTECLOUD_CLI_CONFIG_DIR` is set (or the site-less summary reports that redirect), run the per-site status and treat a valid `"auth_source": "bytecloud-sdk"` result as authenticated. If status is invalid and no application identity is intended, run `forge auth login --begin --site <site>`. The command returns immediately without polling and emits a JSON envelope carrying `user_action` plus a `complete_token`. Pass `user_action.prompt_body` to the user-facing surface **verbatim** (plain text, no fenced code block, no markdown decoration); the cmd has already substituted every load-bearing field, including URL / QR alternatives and session Feishu PC AppLink when present — surfacing only one alternative or wrapping it in a code block both break the flow. End your turn after surfacing the prompt; once the user signals they've scanned / clicked, call `forge auth login --complete <token>` **once** (one-shot, no polling loop). On `success` → continue. On `pending` → wait 3–5 seconds and call `--complete` once more (the server may lag the user's confirmation). On `expired` → restart with `--begin`. Never invoke the bare `forge auth login` from inside an agent — it is a blocking command that deadlocks synchronous bash tools. When `FORGE_IDE_DEPLOY_REGION` is not set, a dial / TLS / lookup timeout from `auth login --begin` or any Reckon command on a non-`cn` site must first be retried once with `--network office` before offering any other explanation; inside ForgeIDE the ForgeIDE STOP rules under "Quick rules" take precedence and no office retry applies. See [Auth login from an agent](references/invocation.md#auth-login-from-an-agent) and [Shared credential store](references/invocation.md#shared-credential-store-bytecloud_cli_config_dir).
3. **Runtime flags**: `--network office|prod` and `--site cn|i18n|eu-ttp|us-ttp` as needed. Inside an AIME agent sandbox (non-blank `AIME_CURRENT_USER`), Forge defaults to `--network office` for every site. If `forge config show` still reports `runtime.network=prod` without a user pin inside that sandbox, the binary predates this behavior: run `forge upgrade` or pass `--network office` explicitly on every command, including `forge auth login --begin`. Credentials are keyed by site in the ByteCloud auth SDK. A Global **user-login application** may populate target-compatible user credentials for multiple sites from one login; an AK/SK **application identity** is a separate application/service-account principal and needs its own API/resource permissions. AK/SK plus a username never becomes a user JWT. Git-managed US-TTP `code commit create` is user-only and fails before update/push under application identity; use `BYTECLOUD_AUTH_AS=user` with the same user logged in to `us-ttp` and `i18n`, or pass an existing `--commit-id` when a compile can skip auto-commit. Forge-managed US-TTP application flows require the same SDK-reported AccessKeyID on `us-ttp` and `i18n` and fail closed before update when they differ. `job sdp exec` is i18n user-only because it represents a person entering a container; it needs the CN browser SSO session (to create the SDP session through webshellauth) plus an i18n ByteCloud user JWT (for the SDP WebSocket), AK/SK is rejected, and an injected JWT must carry an explicit human-user credential type. The container OS user is server-determined. `job webshell exec` likewise requires the CN browser SSO session; AK/SK alone does not enable it. `cn` uses a ByteDance identity; the three TikTok sites (`i18n` / `eu-ttp` / `us-ttp`) use a TikTok identity. Control-plane口语 names map to `--site` 1:1 except that `--site i18n` has three aliases (`i18n` / `row` / `us` 控制面 — all the same site, **not** the same as `us-ttp`). See [`invocation.md` → Authentication](references/invocation.md#authentication), [`invocation.md` → Multi-site login](references/invocation.md#multi-site-login), and [`invocation.md` → Control planes](references/invocation.md#control-planes).
4. **Browser SSO session (conditional only)**: do not check or acquire this session for ordinary Forge commands, pod discovery, Primus file listing, lifecycle checks, or `webshell list`. Enter this prerequisite only for an explicit `webshell exec` or `job sdp exec` (both delegate to sso.bytedance.com; `job sdp exec` uses the cn session to create its SDP session through webshellauth), an office-network US-TTP Primus content query/download that will try Footprint first, or an office-network EU-TTP content query/download after direct log access has failed and a Footprint retry is needed. Then run `forge auth session status --site cn`; if `validated=false`, run `forge auth login --begin --session --site cn`, pass `user_action.prompt_body` verbatim to the user, end your turn until they signal done, then call `--complete <token>` **once** (no polling loop — same flow as item 2). If the user reports that Lark rejected the scan ("Login method isn't allowed" / "blocked"), stop the QR flow — no further `--complete` and no new `--begin --session`, even on `expired` — and run `user_action.fallback_command` (or `recovery.fallback_command`): the one sanctioned blocking login, which opens a local Chrome window for password or passkey sign-in and saves the session only on the machine that runs it; on a remote host without a display, ask the user to run it and the target command on their own desktop instead. See [QR scan rejected](references/invocation.md#qr-scan-rejected-login-method-isnt-allowed). Footprint search/download also requires a valid i18n-office ByteCloud credential from item 2/3; the JWT is scoped to the Footprint host and is not sent through SSO redirects. Apart from that fallback, the plain blocking form is only for human terminals.

### Execution environment

Corp-internal Forge / Tracing / Primus observation commands — `forge job meta|event|log|metrics|profiling-timeline|memory-snapshot|deepinsight|wandb|tensorboard ...`, `forge ps ...`, `forge job webshell ...`, and direct Primus / Primus History / Reckon Tracing probes — depend on internal DNS that often does not resolve inside the sandbox even when auth is valid. Prefer running these outside sandbox by default. On `no such host` / `Could not resolve host` / `127.0.0.1:53` / `::1` resolver errors, see [Sandbox DNS / resolver failures](references/troubleshooting.md#sandbox-dns--resolver-failures) — this is an environment artifact, not a service incident.

## Route by task

Route by task first. When a request matches one task row or any keyword coverage row, read the linked reference file in full before answering or running commands. If multiple tasks are required, read each matched reference file in full. Do not read references unrelated to the current task.

| Task | Reference |
|---|---|
| Fetch a Forge version into a workspace; update or publish code from the current workspace; inspect or switch a version's framework metadata; create a new version by forking a version or commit | [references/code.md](references/code.md) |
| Create/list/diff Forge commit records; restore commit code to disk; answer "version 提交了哪些 commit" | [references/commit.md](references/commit.md) |
| Trigger or inspect model / norbert compilation; local compile; Torch/Sail/Zouwu compile parameters; poll build status; inspect compile logs; download model compile artifacts / Download Model Meta | [references/compile.md](references/compile.md) |
| List training jobs (including a whole resource group's jobs across all owners and statuses, or filtered by owner / status / job-id), submit, or kill training jobs, including shared-weights only-register jobs; inspect/create/pin Training Haven versions; transfer job owner; change Personal or Group Priority; list job stages, profiling timeline files, or GPU memory snapshots; list/save/delete model checkpoints; inspect standalone Primus application/role/pod snapshots; view/list/diff/update Primus CRD config; list model-type catalog; read job metadata, events, logs, training metrics, Vela host-machine metrics, CPU/GPU/DeepInsight-server utilization | [references/job.md](references/job.md) |
| Inspect current Training PS model/slot/shard state; list FIDs by slot; fetch raw values or embeddings by FID | [references/ps.md](references/ps.md) |
| Inspect serving deployments, dense snapshots, and Serving Haven versions for one model; list deployments by BU or PSM; inspect one concrete deployment; create/get/update/start/stop ModelHub or MaaS serving deployments; pin/unpin dense snapshots; enable or edit MaaS runtime config; start/stop OnlinePS; check instance health and MaaS progress | [references/serving.md](references/serving.md) |
| Diagnose serving distribution failure, rollout-readiness blockers, or status discrepancy between summary and deployment health | [references/serving_diagnosis.md](references/serving_diagnosis.md) |
| Create / list / update / delete / execute / enable / disable resource-inspection tasks (inspection rules), browse the inspection-rule catalog, and pick which rule a task runs | [references/inspection.md](references/inspection.md) |
| Create, list, approve, reject, renew, or revoke resource-inspection kill whitelist (强杀白名单) entries for jobs or users | [references/inspection_whitelist.md](references/inspection_whitelist.md) |
| List or update resource groups and pick one for `job create`; `job create` can also prompt for the current user's resource group when omitted; check rigid/elastic/allocated/available quota per `(dc, training_type, resource_type, resource_annotation, product_type)` dimension; list **only** the running / queued (quota-occupancy) tasks in a resource group — for a group's full job list across all statuses use [job.md](references/job.md) instead | [references/quota.md](references/quota.md) |
| Discover DeepInsight head mapping; query evaluation metrics (AUC / UAUC / NDCG / calibration / bias) | [references/deepinsight.md](references/deepinsight.md) |
| Discover and query Wandb or TensorBoard series paths (scalar / histogram / image); batch helper for larger scalar path sets (default 10-path batches; CLI maximum 100); plot outside the CLI | [references/series.md](references/series.md) |
| Diagnose missing / partial / abnormal Wandb or TensorBoard series data, but only after the user explicitly identifies Wandb or TensorBoard as the affected surface | [references/series_diagnosis.md](references/series_diagnosis.md) |
| Global flags, JSON output, `--network` / `--site` rules, install / upgrade, auth | [references/invocation.md](references/invocation.md) |
| Shared / pre-provisioned ByteCloud credential store: `BYTECLOUD_CLI_CONFIG_DIR`, credentials injected by a managed container or CI, "是否还要重新登录 / 需不需要 login", which store or `auth_source` answered a per-site status check | [`invocation.md` → Shared credential store](references/invocation.md#shared-credential-store-bytecloud_cli_config_dir) |
| Locate training pods; expand logical executors into concrete attempt/version rows; judge pod / executor lifecycle state; run `forge job sdp exec` for an exact RoW target (incl. Primus-on-Godel `nj-*`); hand off EU/TTP operations | [references/primus_pods.md](references/primus_pods.md) |
| Use `forge job webshell list/exec` only when the user explicitly requests Forge webshell and the environment is confirmed usable; configure `forge auth login --session` for that explicit fallback | [references/webshell.md](references/webshell.md) |
| Auth failures, workspace metadata missing/stale artifacts, cross-region prod network errors, common errors | [references/troubleshooting.md](references/troubleshooting.md) |
| Run or diagnose ForgeIDE localrun | Start with [references/localrun.md](references/localrun.md). After it identifies exactly one framework, read only the matching [LagrangeTorch](references/localrun_lgtorch.md), [LGTF](references/localrun_lgtf.md), or [Sailor](references/localrun_sailor.md) reference. |

## Code keyword coverage

Use [references/code.md](references/code.md) whenever the request matches any code-stage wording below. This preserves the old `forge-code` trigger surface through the main Forge skill.

| User wording / keywords | Specific reference |
|---|---|
| `forge code fetch`, `forge fetch`, `fetch code`, `download code`, `get version code`, `拉代码`, `下载代码`, `获取版本代码` | [Fetch Code](references/code.md#fetch-code) |
| `forge code update`, `code update`, `update code`, `publish code`, `更新代码`, `上传代码`, `发布代码` | [Update Code](references/code.md#update-code) |
| `forge code meta get`, `forge code meta update`, `version meta`, `framework_version`, `framework version`, `切换版本`, `切换 framework`, `切换 framework_version`, `切换代码版本` | [Version Metadata](references/code.md#version-metadata) |
| `forge code version create`, `fork version`, `version fork`, `从 version fork`, `从 commit fork`, `fork commit`, `fork 新版本`, `复制 version`, `复制 commit 到新 version` | [Create Version From Fork](references/code.md#create-version-from-fork) |
| `workspace`, `workdir`, `.forge/forge_meta.json`, `output_dir`, `--output-dir`, `--force`, target exists, overwrite, fetch conflict, existing workspace | [Workspace Context](references/code.md#workspace-context) and [Fetch Code](references/code.md#fetch-code) |
| Git-managed code, Forge-managed code, repo clone, branch, `--branch`, clean worktree, auto-push, `--dry-run` | [Workspace Context](references/code.md#workspace-context) and [Update Code](references/code.md#update-code) |
| `git commit`, `git push`, `提交 git`, `提交到远端分支` in a non-Forge request | [Intent Guard](references/code.md#intent-guard) |

## Commit keyword coverage

Use [references/commit.md](references/commit.md) whenever the request matches any Forge commit-record wording below. A Forge `version_id` alone is enough for list queries; do not ask for a Git repo id/path just because the user says `commit`.

| User wording / keywords | Specific reference |
|---|---|
| `<version_id> 这个 version 提交了哪些 commit`, `version 提交了哪些 commit`, `version 的 commit 列表`, `最近 commit`, `最近几次成功的 model 变动`, `list commits` | [List Commits](references/commit.md#list-commits) |
| `Forge commit record`, `code commit create`, `提交 Forge commit`, `创建 commit record`, `commit record` for compile/job | [Create Commit](references/commit.md#create-commit) |
| `code commit get`, `恢复 commit 代码`, `restore commit`, `get commit` with Forge record id | [Get Commit](references/commit.md#get-commit) |
| `code commit diff`, `看看 commit 改了什么`, `和当前工作区对比`, `和另一个 commit 对比`, `输出 patch` | [Diff Commit](references/commit.md#diff-commit) |

## Compile keyword coverage

Use [references/compile.md](references/compile.md) whenever the request matches any compile-stage wording below. This keeps compile, Sail, Zouwu, and Torch triggering strong after the standalone compile skill was folded into this main skill.

Do not confuse Local Run with local compile or local validation. Local Run pulls remote data and runs the model locally for real outputs; it is not a compile workflow.

| User wording / keywords | Specific reference |
|---|---|
| `forge code compile create`, `compile create`, `trigger compilation`, `build model`, `model compile`, `创建编译`, `编译`, `构建模型` | [Create Compilation](references/compile.md#create-compilation) |
| `本地编译`, `local compile`, `fd build`, `当前环境`, `current environment`, `系统环境`, `当前python环境`, `当前 python 环境`, `不使用 venv`, `FORGE_COMPILER_VERSION`, `compile_site=local`, `use_venv` | [Local Compilation](references/compile.md#local-compilation) |
| `本地验证`, `local validation`, `--compile-mode local-verify`, `local-verify`, `只在本地运行模型代码`, `只在本地运行 Norbert 代码`, `检查逻辑`, `检查输出`, `不上传编译产物`, `不产生 commit` | [Local Validation](references/compile.md#local-validation) |
| `Local Run`, `local run`, `拉取远端数据`, `本地运行模型得到真实输出`, `真实输出` | Not a compile task: do not use local compile or local validation. Use the Local Run workflow if available; otherwise ask for the intended Local Run entrypoint. |
| `forge code compile get`, `compile get`, `build status`, `check compile`, `compile status`, `编译状态`, `查看编译` | [Check Build Status](references/compile.md#check-build-status) |
| `Torch`, `torch compile`, `Torch 编译`, `torch_version`, `torch_version=2.4`, Torch model compile defaults | [Normalization Rules](references/compile.md#normalization-rules) |
| `Sail`, `Sail Dev`, `Zouwu`, `zouwu`, `Sail 编译`, `zouwu 编译`, `tensorflow-version`, `TensorFlow version`, `1.15`, `2.5.0`, `compile graphs`, `GPU Graphs`, `training,serving`, `gpu_training`, `gpu_training_dandelion_v3`, `gpu_training_dandelion_v3_streaming`, `gpu_training_jaguar` | [Sail User Choice Guard](references/compile.md#sail-user-choice-guard) and [Create Compilation](references/compile.md#create-compilation) |
| `--code-type model`, `--code-type norbert`, `norbert compile`, `--commit-id`, explicit commit compile, workspace compile | [Workspace Context](references/compile.md#workspace-context) and [Context And Waiting Behavior](references/compile.md#context-and-waiting-behavior) |
| `compile logs`, `build_log`, `tail compile log`, `less compile log`, `forge/compile-logs`, redacted logs | [Compile Logs](references/compile.md#compile-logs) |
| `forge code compile-artifact get`, `compile-artifact`, `Download Model Meta`, `下载模型编译产物`, `模型编译产物下载`, `compiled_new`, `get_model_meta`, `model meta archive` | [Download Compile Artifact](references/compile.md#download-compile-artifact) |
| `--wait`, `--wait-timeout`, `--wait-interval`, poll compile, wait for build | [Context And Waiting Behavior](references/compile.md#context-and-waiting-behavior) |

## Localrun keyword coverage

Use [references/localrun.md](references/localrun.md) whenever the request matches any ForgeIDE local debugging wording below. It routes to exactly one framework-specific reference. Localrun is a local debug/run workflow; do not confuse it with `code compile create --compile-mode local`, which submits a real Forge local compile.

| User wording / keywords | Specific reference |
|---|---|
| `forge localrun`, `localrun`, `本地调试`, `本地跑一下`, `local debug`, `LagrangeTorch localrun`, `lgtorch localrun`, `lg_torchrun`, `LGTF`, `LagrangeTF`, `tensorflow localrun`, `TF localrun`, `Sailor localrun`, `Sail localrun` | [references/localrun.md](references/localrun.md) |
| `localrun init`, `localrun compile`, `localrun data-dump`, `localrun data-process`, `localrun run`, `localrun eval`, `data_dump`, `data_process`, `producer`, `只跑数据`, `runner`, `只跑模型`, `只跑 run`, `完整 localrun 流程`, `每跑一步停一下` | [references/localrun.md](references/localrun.md) |
| `.forge/localrun`, `localrun.yaml`, `summary.json`, `runid`, `产物目录`, `日志目录`, `primus cache`, `fountain cache`, `sailor_localrun.yaml` | [references/localrun.md](references/localrun.md) |
| localrun 报错、模型本地运行失败、fountain 图失败、data dump 失败、数据错位/乱码/缺省、模型代码 debug、Sailor eval、offline inference、线上 PS、trained weights | [references/localrun.md](references/localrun.md) |

## Job keyword coverage

Use [references/job.md](references/job.md) whenever the request matches any job-stage wording below.

| User wording / keywords | Specific reference |
|---|---|
| `forge job list`, `job list`, `列出训练任务`, `查看任务列表`, `任务列表`, `我的任务`, `我自己的任务`, `--mine`, `资源组所有任务`, `资源组的任务`, `资源组下的任务`, `某资源组有哪些任务`, `某人/owner 的任务`, 按 `--status` (`running` / `streaming` / `success` / `failed` / `killing` / `killed`) 查任务, 按 `job-id` 查任务 | [List jobs](references/job.md#list-jobs) |
| `forge job create`, `job create`, `提交训练任务`, `创建训练任务`, `shared weights`, `share-weights`, `only-register`, `no-train` | [Create a job](references/job.md#create-a-job) |
| `forge job kill`, `job kill`, `停止训练任务`, `kill job`, `停止 job` | [Kill a job](references/job.md#kill-a-job) |
| `forge job owner transfer`, `job owner transfer`, `转移 owner`, `transfer owner` | [Transfer job owner](references/job.md#transfer-job-owner) |
| `forge job resource-group update`, `更改任务资源组`, `修改 job 资源组`, `change job resource group` | [Change job resource group](references/job.md#change-job-resource-group) |
| `forge job priority update`, `修改任务优先级`, `修改个人优先级`, `修改组优先级`, `Personal Priority`, `Group Priority` | [Change job priority](references/job.md#change-job-priority) |
| `forge job primus-crd get`, `forge job primus-crd list`, `forge job primus-crd diff`, `forge job primus-crd update`, `Primus CRD config`, `Update Primus CRD`, `更新 Primus CRD`, `Primus 热更`, `Primus热更`, `Update Primus`, `修改 Primus CRD 配置`, `Primus CRD 配置 diff`, `Primus CRD 历史` | [Primus CRD config](references/job.md#primus-crd-config) |
| `forge job primus-app get`, `forge job primus-role list`, `forge job primus-pod list`, `forge job primus-pod get`, standalone Primus application / role / pod snapshot, legacy newStatus fallback, Primus 应用摘要, Primus role 列表, Primus pod 快照 | [Direct Primus application, role, and pod snapshots](references/job.md#direct-primus-application-role-and-pod-snapshots) and [references/primus_pods.md](references/primus_pods.md) |
| `热更`, `热更新`, `任务热更`, `任务 热更`, `job 热更`, `更新任务配置` without an explicit `Primus` / `CRD` / `Norbert commit` target | [Hot update intent guard](references/job.md#hot-update-intent-guard) |
| `forge job stage get`, `job stage get`, only a `stage_id`, `stage 属于哪个 job`, `stage 对应的 job_id`, `根据 stage 查 job` | [Get a job stage by ID](references/job.md#get-a-job-stage-by-id) |
| `forge job stage list`, `job stage list`, `stage list`, `stage 列表`, `列出 stage`, `有哪些 stage`, `stage_id 列表`, `历史 stage`, `跨 stage 查日志`, `多个 stage 的日志` | [List job stages](references/job.md#list-job-stages) |
| `forge job profiling-timeline list`, `forge job memory-snapshot list`, `profiling timeline files`, `性能分析时间线`, `tf_profile`, `GPU memory snapshot`, `显存快照`, `显存快照文件` | [Profiling timeline and GPU memory snapshot artifacts](references/job.md#profiling-timeline-and-gpu-memory-snapshot-artifacts) |
| `forge job checkpoint list`, `forge job checkpoint save`, `forge job checkpoint delete`, `checkpoint list/save/delete`, `checkpoint 保留`, `checkpoint 删除`, `模型 checkpoint`, `训练 checkpoint`, `backup_id`, `hdfs_path` | [Job checkpoints](references/job.md#job-checkpoints) |
| `forge job haven-version`, `Training Haven`, `训练 Haven 版本`, `训练图版本`, `训练图改图`, model-scoped `Haven pin/unpin` | [Training Haven versions](references/job.md#training-haven-versions) |
| `forge job meta get`, `job meta`, `job status`, `stage status`, `sub_stages`, `共享权重子任务`, `share_weights_to`, `Forge2 job link` | [Get job metadata](references/job.md#get-job-metadata) |
| `forge job event get-meta`, `forge job event query`, `job event`, `error event`, `事件` | [Job events](references/job.md#job-events) |
| `forge job log get-meta`, `forge job log query`, `job log`, `Primus log`, `训练日志`, `stderr.log`, `stdout.log`, `train_path`, `训练路径`, `日志里的 date`, `从日志提取路径`, `从 Primus 日志找路径` | [Job logs](references/job.md#job-logs) |
| `forge job metrics get-meta`, `forge job metrics query`, `训练指标`, `吞吐`, `cpu_util`, `gpu_util`, `metrics/sailor/read_instance` | [Training metrics](references/job.md#training-metrics) |
| `forge job sdp exec`, `SDP`, `训练 pod`, `pod 列表`, `pod 状态`, `executor 状态`, `executor attempt`, `executor version`, `RUNNING attempt`, `Primus History`, `进入容器`, `容器诊断`, `kill pod`, `kill process` | [references/primus_pods.md](references/primus_pods.md) |
| User explicitly says `forge job webshell`, `Forge webshell`, or asks to use an already-confirmed Forge webshell URL | [references/webshell.md](references/webshell.md) |

## Inspection keyword coverage

Use [references/inspection.md](references/inspection.md) for inspection-task / rule wording, and [references/inspection_whitelist.md](references/inspection_whitelist.md) for kill-whitelist (强杀白名单) wording — match the specific row below and read only the file it points to (the two surfaces are independent). Inspection tasks and whitelists are **per control plane**, so a query reflects only one `--site`; when the user names no site, still say which site you queried (default `cn`) and that other control planes hold separate data — never treat one site's result as the whole picture.

| User wording / keywords | Specific reference |
|---|---|
| `forge inspection task create`, `巡检规则`, `巡检任务`, `新建巡检`, `创建巡检规则`, `添加巡检任务`, `inspection task`, `inspection rule`, `create inspection task` | [Create inspection task](references/inspection.md#create-inspection-task) |
| `forge inspection task list`, `巡检规则列表`, `查巡检任务`, `有哪些巡检`, `我的巡检任务`, `查我创建的巡检`, `--mine`, `list inspection tasks`, `inspection rules` | [List inspection tasks](references/inspection.md#list-inspection-tasks) |
| `forge inspection task update`, `改巡检规则`, `修改巡检任务`, `update inspection task` | [Update inspection task](references/inspection.md#update-inspection-task) |
| `forge inspection task enable / disable`, `启用巡检`, `停用巡检`, `暂停巡检`, `恢复巡检`, `enable/disable inspection task` | [Enable / disable inspection task](references/inspection.md#enable--disable-inspection-task-启用--停用) |
| `forge inspection rule list`, `有哪些巡检规则`, `可配置的巡检规则`, `巡检规则有哪些`, `选哪个巡检规则`, `配置巡检规则`, `inspection_job_type`, `which inspection rules`, `list inspection rules` | [Which inspection rule](references/inspection.md#which-inspection-rule-does-a-task-run-配置巡检规则) |
| `巡检指标`, `巡检条件`, `利用率百分数`, `利用率阈值`, `部署率百分数`, `除去启动`, `有效时长`, `向前检测`, `符合以下条件`, `inspection conditions`, `utilization threshold`, `filters`, `is_or` | [Inspection conditions](references/inspection.md#inspection-conditions-巡检指标) |
| `巡检排除 failover`, `failover 时间排除`, `除去 failover 前后`, `remove_failover_before_minute`, `remove_failover_after_minute`, `failover exclusion` | [Exclude failover time](references/inspection.md#exclude-failover-time-from-utilization) |
| `forge inspection task delete`, `删除巡检规则`, `删掉巡检任务`, `delete inspection task` | [Delete inspection task](references/inspection.md#delete-inspection-task) |
| `forge inspection task execute`, `立即执行巡检`, `手动跑一次巡检`, `触发巡检`, `run inspection now`, `execute inspection task` | [Execute inspection task](references/inspection.md#execute-inspection-task) |
| `forge inspection hit-item list`, `forge inspection hit-item get`, `巡检命中明细`, `为什么被巡检杀了`, `为什么命中但没杀`, `豁免原因`, `inspection_item_id` | [Hit evidence and action outcomes](references/inspection.md#hit-evidence-and-action-outcomes-hit-item-listget) |
| `forge inspection scheduler-job list`, `巡检执行记录`, `巡检结果`, `巡检跑了什么`, `执行历史`, `schedule jobs`, `inspection run history`, `job_result` | [Run history](references/inspection.md#run-history-scheduler-job-list-执行记录) |
| `告警配置`, `通知配置`, `通知接受人`, `通知群`, `强杀阈值`, `kill_threshold`, `alert config`, `task_alert_config`, `model_alert_config` | [Alert config](references/inspection.md#alert-config-task_config-alert-blocks) |
| `forge inspection target list`, `巡检目标下拉`, `巡检 target 有哪些`, `有哪些psm`, `psm 列表`, `bu 列表`, `online ps 列表`, `inspection target list`, `list targets` (inspection-target value discovery only; for listing billing units or resource groups use the quota commands below) | [Discovering valid values](references/inspection.md#discovering-valid-values-targets-roles-gpu-types) |
| `forge inspection role list`, `forge inspection gpu-type list`, `role 下拉`, `有哪些 role`, `卡型列表`, `gpu 卡型`, `list roles`, `list gpu types` | [Discovering valid values](references/inspection.md#discovering-valid-values-targets-roles-gpu-types) |
| `forge inspection kill-whitelist create`, `巡检白名单`, `强杀白名单`, `加白`, `加到白名单`, `豁免巡检`, `不要杀这个任务`, `加白多久`, `白名单有效期`, `加白时长`, `inspection whitelist`, `kill whitelist`, `exempt from inspection kill` | [Create whitelist entry](references/inspection_whitelist.md#create-kill-whitelist-entry) |
| `forge inspection kill-whitelist list`, `查白名单`, `白名单列表`, `我申请的白名单`, `--mine`, `pending approval`, `待我审批`, `pending-my-approval`, `查看加白状态` | [List whitelist entries](references/inspection_whitelist.md#list-kill-whitelist-entries) |
| `forge inspection kill-whitelist update`, `approve whitelist`, `reject whitelist`, `renew whitelist`, `revoke whitelist`, `审批白名单`, `拒绝加白`, `续期白名单`, `撤销白名单` | [Update whitelist entry](references/inspection_whitelist.md#update-kill-whitelist-entry) |

## Quota keyword coverage

Use [references/quota.md](references/quota.md) whenever the request matches any quota-stage wording below.

| User wording / keywords | Specific reference |
|---|---|
| `forge quota resource-group list`, `resource-group list`, `list resource groups`, `资源组`, `资源组列表`, `有哪些资源组`, `列出资源组`, `查询某结算单元的资源组`, `一个结算单元下有哪些资源组`, `我的资源组`, `我自己的组`, `--mine`, `--name`, `--payoff-unit`, `--user`, `--all-users` | [Identity-only](references/quota.md#identity-only-default) |
| `forge quota resource-group update`, `resource-group update`, `修改资源组`, `更新资源组`, `资源组管理员`, `资源组成员`, `资源组优先级`, `--description`, `--admin`, `--member`, `--priority`, `--config` | [Update a resource group](references/quota.md#update-a-resource-group) |
| `--with-quota`, `quota check`, `查 quota`, `配额查询`, `资源组余量`, `available quota`, `--has-available` | [With quota](references/quota.md) |
| `--resource-type`, `--resource-annotation`, `--product-type`, `--dc`, `--training-type`, `g02`, `h20`, `hwj590`, `guarantee`, `pbd`, `batch`, `realtime` | [Quota-level filter flags](references/quota.md) |
| `rigid`, `elastic`, `allocated`, `available`, `total`, `null` / unlimited quota, overallocated, quota dimensions `(dc, training_type, resource_type, resource_annotation, product_type)` | [Output contract](references/quota.md#output-contract) |
| Pick a resource group before `forge job create`; 资源组选型; saturated pool; `--resource-group` | [Working patterns](references/quota.md#working-patterns) |
| `forge quota task list`, `quota task list`, `running tasks`, `queued tasks`, `排队任务`, `排队中的任务`, `正在运行的任务`, `我的运行中任务`, `我的排队任务`, `--mine`, `已分配的任务`, `占用配额的任务`, `为什么在排队` | [Task list](references/quota.md#task-list-running--queued-tasks) |
| `forge quota payoff-unit list`, `payoff-unit list`, `list payoff units`, `结算单元`, `结算单元列表`, `查询结算单元`, `有哪些结算单元`, `列出结算单元`, `有多少结算单元`, `我的结算单元`, `我管理的结算单元`, `业务线列表`, `--mine`, `--admin` | [Payoff units](references/quota.md#payoff-units-forge-quota-payoff-unit-list) |
| `forge quota payoff-unit update`, `payoff-unit update`, `修改结算单元`, `更新结算单元`, `结算单元管理员`, `结算单元优先级`, `结算单元标签`, `--babi-source-name`, `--apply-quota-check`, `--pilot-galaxy-node`, `--tag` | [Update a payoff unit](references/quota.md#update-a-payoff-unit) |
| `forge quota quota-change list`, `quota 变更记录`, `配额变更记录`, `配额流水`, `quota history`, `转移记录`, `Job 配额占用变化` | [Quota change history](references/quota.md#quota-change-history) |
| `forge quota request create`, `quota 申请`, `申请配额`, `释放配额`, `转移 quota`, `跨结算单元转移`, `迁移资源组`, `quota apply/release/transfer`, `出让 quota`, `回收已出让 quota`, `资源组整体迁移` | [Quota requests](references/quota.md#quota-requests-apply-release-transfer-and-migration) |
| `forge quota config-change list`, `config-change list`, `配置变更`, `配置变更记录`, `我做的配置变更`, `--mine`, `config modification records`, `--config-type`, `--change-kind` | [Config change records](references/quota.md#config-change-records-forge-quota-config-change-list-配置变更) |

Disambiguation — "结算单元" / "资源组" listing: **any** request to list or enumerate billing units — "有哪些结算单元 / 结算单元列表 / 查询结算单元 / 有多少结算单元 / list payoff units" — goes to `forge quota payoff-unit list` (the purpose-built command; returns id, admins, priority, galaxy node, …). Likewise "有哪些资源组 / 资源组列表" → `forge quota resource-group list`. "我管理的结算单元 / 我名下的结算单元 / 我自己的结算单元" → `forge quota payoff-unit list --mine` directly (matches the unit's own `admins` field); do **not** derive it by running `resource-group list --mine` and reading each item's `payoff_unit_name` — that answers a different, unasked question (which units happen to contain a group you administer) and re-implements a filter the command already has built in. Do **not** answer these with `forge inspection target list --task-type payoff-unit|resource`; that command exists only to fill an inspection task's `--inspection-target` argument (reached from the inspection-task-creation flow) and returns bare deduped names, so it is the wrong tool for a general "有哪些…" question. "配置变更记录 / config modification records" → `forge quota config-change list`. "quota / 配额变更记录" → `forge quota quota-change list`; do not substitute config-change for quota history.

Disambiguation — "资源组任务" routing: a bare "查看某资源组所有任务 / 任务列表 / 有哪些任务" means **all jobs in the group** (every owner, every status) → use `forge job list --resource-group <name>` ([job.md](references/job.md#list-jobs)). Only route to `forge quota task list` when the user explicitly scopes to running / 已分配 / queued / 排队 tasks (the quota-occupancy view). `quota task list` returns only `running` + `queued` tasks, never finished / failed / killed ones, so it is the wrong tool for "所有任务".

## Parameter Server keyword coverage

Use [references/ps.md](references/ps.md) whenever the request matches any Training PS data-inspection wording below. `serving online-ps start/stop` remains the OnlinePS lifecycle surface.

| User wording / keywords | Specific reference |
|---|---|
| `forge ps get`, `PS 状态`, `PS 信息`, `slot 信息`, `shard 信息`, `feature 数`, `PS 内存` | [Current Training PS information](references/ps.md#current-training-ps-information) |
| `forge ps fid list`, `根据 slot 查 fid`, `slot 有哪些 fid`, `bias fid`, `vector fid`, `vec fid` | [List FIDs by slot](references/ps.md#list-fids-by-slot) |
| `forge ps fid query`, `根据 fid 查 embedding`, `fid value`, `查权重`, `查 embedding`, `vec_w` | [Query values and embeddings by FID](references/ps.md#query-values-and-embeddings-by-fid) |

## Serving keyword coverage

Use the serving references below whenever the request matches any serving-deployment wording below.

| User wording / keywords | Specific reference |
|---|---|
| `forge serving model get`, `serving model get`, `serving 部署`, `模型部署`, `查看部署状态`, `列一下有哪些 PSM`, `有哪些 serving`, `有没有 serving 部署` | [What this command is for](references/serving.md#what-this-command-is-for) and [Query strategy for agents](references/serving.md#query-strategy-for-agents) |
| `forge serving dense-snapshot`, `dense snapshot`, `dense pin/unpin`, `按时间 pin dense`, `pinned_dense_snapshots` | [Dense snapshot pinning](references/serving.md#dense-snapshot-pinning) |
| `forge serving deployment create`, `deployment create`, `创建 serving 部署`, `创建模型部署`, `部署到 PSM`, `创建 MaaS`, `--job-id --psm`, `--biz-unit`, `--region`, `--start` | [Deployment commands](references/serving.md#deployment-commands) |
| `forge serving deployment update`, `deployment update`, `修改 deployment 配置`, `ModelHub snapshot config`, `修改 MaaS 配置`, `MaaS 套餐开关`, `MaaS runtime 配置`, `开启 runtime`, `use_runtime`, `runtime template`, `pass_config`, `extra_config`, `extra_context`, `SCM repo 增删改`, `替换 SCM repo`, `--runtime-scm-remove`, `Byted TF Opt`, `byted_tf_opt_snapshot_config`, `snapshot_psm`, `--use-runtime`, `--runtime-env-id`, `--runtime-package` | [Update a deployment](references/serving.md#update-a-deployment) |
| `forge serving deployment list`, `forge serving deployment get`, `forge serving deployment start`, `forge serving deployment stop`, `按 BU 查部署`, `按 PSM 查部署`, `启动 serving 部署`, `停止 serving 部署`, `MaaS 上线`, `MaaS 下线`, `MaaS 进度`, `--deployment-id`, `--maas-job-id` | [Deployment commands](references/serving.md#deployment-commands) |
| `forge serving online-ps start`, `forge serving online-ps stop`, `OnlinePS 上线`, `OnlinePS 下线`, `PS Push Online`, `push online`, `release OnlinePS`, `unrelease OnlinePS`, `PerModel 集群组`, `指定目标集群`, `--target-cluster`, `--dump-path`, `--compress`, `--clean-job` | [OnlinePS lifecycle commands](references/serving.md#onlineps-lifecycle-commands) |
| `forge serving haven-version`, `Serving Haven`, `在线图版本`, `Serving 改图`, `Serving Haven pin/unpin` | [Serving Haven versions](references/serving.md#serving-haven-versions) |
| `forge serving profiling-artifact list`, `Serving profile`, `serving profiling`, `推理性能采集`, `推理 profile 产物` | [Serving profiling artifacts](references/serving.md#serving-profiling-artifacts) |
| `PSM`, `看这个 PSM`, `某个部署详情`, `deployment detail`, `serving detail`, `实例是不是有坏的`, `实例健康` | [Query strategy for agents](references/serving.md#query-strategy-for-agents) and [Response-shaping rules for agents](references/serving.md#response-shaping-rules-for-agents) |
| `OnlinePS` diagnosis/status questions, `开实验`, `放量`, `首发上线`, `首次上线`, `分发失败`, `热更新`, `lag`, `分发 lag`, `共享权重上线`, `shared-weight serving readiness`, parent OnlinePS, `批训练`, `流训练`, `train_mode` | [references/serving_diagnosis.md](references/serving_diagnosis.md) |
| `MaaS`, `是不是 MaaS`, `from_maas`, `maas_job_id`, `maas_job_status`, `biz_unit`, `MaaS 状态解释`, `MaaS 状态差异`, `上线预检`, `上线进度` | [references/serving.md](references/serving.md). 当前没有独立只读的 MaaS 上线预检命令；用户仅要求查看/运行预检时不得调用 `deployment start`，只有用户明确要求上线时才可执行 start。 |
| MaaS PSM 实例健康, MaaS serving summary/detail 差异, MaaS deployment health | [references/serving_diagnosis.md](references/serving_diagnosis.md) |
| `serving deployment not found`, `未找到对应的 serving 部署`, 空实例、无实例 | [Failure handling rules for agents](references/serving.md#failure-handling-rules-for-agents) |

## Quick rules that apply across references

- ForgeIDE precondition (MUST): the next four ForgeIDE guard / STOP rules apply **only** when `FORGE_IDE_DEPLOY_REGION` is set. An AIME agent sandbox is not ForgeIDE.
- ForgeIDE guard (MUST, when the precondition holds): before explaining any ForgeIDE control-plane/JWT/TLS/OG/Segregator failure, read `FORGE_IDE_DEPLOY_REGION` and treat it as the authoritative deployment environment (`cn` or `i18n`), not the requested `--site`.
- ForgeIDE access (MUST, when the precondition holds): `cn` env can access `cn` only; `i18n` env can access `i18n` only.
- ForgeIDE cn/i18n mismatch (STOP, when the precondition holds): do not continue auth troubleshooting or suggest re-login, `auth status`, whitelisting, jumpboxes, changing `--site`, or office-network fallback. Tell the user to switch to the matching ForgeIDE and rerun the same command.
- ForgeIDE TTP target (STOP, when the precondition holds): `eu-ttp`/`us-ttp` have no ForgeIDE env. Before auth checks or parameter questions, say ForgeIDE cannot run this request; do not suggest login/status/retry or ask AskUserQuestion. Tell the user to run from an office-network environment.
- ForgeIDE-only preferred wording: `Current ForgeIDE is deployed in <env>, so it can access <allowed-site> only. This request targets <target-site/domain>; this is production network isolation, not a ForgeIDE product limit or auth problem. For cn/i18n, switch to the matching ForgeIDE and rerun the same command. For eu-ttp/us-ttp, ForgeIDE cannot run this request; use an office-network environment.`
- Auth-class errors — `not logged in`, `<ENV> is set for site=X but ignored for target site=Y`, or `resolved ByteCloud credential ... is not compatible with target site` — always use the `forge auth login --begin --site <site>` flow. Never answer them with network-isolation / "use an office-network environment" wording.
- Public commands follow `forge <resource> <action>` or `forge <resource> <domain> <action>` (e.g., `code commit create`, `job metrics query`). There is **no** top-level `commit` / `compile` alias.
- Action verbs are fixed: `create`, `get`, `get-meta`, `query`, `list`, `diff`, `diagnose`, `update`; lifecycle verbs `start` / `stop` are allowed for explicit runtime lifecycle resources such as `serving deployment` and `serving online-ps`. `get-meta` returns available metadata/dimensions; `query` returns actual data.
- CLI flags use kebab-case (`--job-id`, `--data-type`, `--step-min`).
- Most commands already emit JSON on stdout by default and have **no** `--json` flag — passing `--json` to them fails with `unknown flag`, so do not add it reflexively. The only commands that define a `--json` flag are `job deepinsight query` (default CSV → JSON) and `job wandb|tensorboard query` (per-path data files CSV → JSONL; the summary stays JSON regardless), plus `version`, `auth status`, and `auth jwt`. Separately, `job deepinsight query` and `job wandb|tensorboard query` also accept `--output` to write results to disk.
- `--dry-run` (where supported) validates local request assembly or local prechecks without mutating. It is not a live backend acceptance guarantee unless the command reference says so; prefer it before `create` / `update` in anything shared.
- After plain `code compile create`, expose `commit_id` as the user-facing handle; do not repeat `build_id`, derived compile log paths, or tail commands to the user.
- `code compile create/get --wait` emits NDJSON status events until terminal status; consume stdout line by line and use the final `summary` plus exit code.
- `code compile get` automatically redacts token / jwt / secret / cookie / authorization-like keys from build logs — do not disable this.

## Agent stance

- Prefer workspace metadata resolution over re-asking the user for derived flags. If a derived flag is missing, trace back to the earliest missing stage (e.g., missing framework → run `code fetch` again) rather than asking the user to supply it manually.
- Treat job observation commands (`job stage get/list`, `job profiling-timeline list`, `job memory-snapshot list`, `job checkpoint list`, `job primus-app get`, `job primus-role list`, `job primus-pod list/get`, `job meta`, `event`, `log`, `metrics`, `utilization`, `deepinsight`, `wandb`, `tensorboard`), `serving profiling-artifact list`, `serving dense-snapshot list`, `haven-version list/get`, and every `ps` command as read-only; never mutate during investigation. Treat `serving dense-snapshot update`, `haven-version create/update`, and `job checkpoint save/delete` as mutating commands: run them only on explicit user intent and never as part of read-only diagnosis.
- For plotting or follow-up analysis, capture results with `--json` / `--output` and analyze locally outside the CLI. Do not add CLI plotting surfaces.
- Do not invent metric names, head names, or flag names beyond what the relevant reference lists; confirm discovered values with `get-meta` first. DeepInsight has a rare unlisted-head exception: if the user explicitly names a head that metadata does not expose, preserve that head and follow [references/deepinsight.md](references/deepinsight.md)'s raw-head query flow before concluding it is invalid.
- Never use `forge job webshell list` as evidence for training pod inventory, executor attempt identity, or lifecycle state. Resolve those facts from Primus History first. For an explicit RoW operation, use `forge job sdp exec` with an exact History-resolved AM or `RUNNING` executor target (incl. Primus-on-Godel `nj-*`); it creates the SDP session via webshellauth `type=sdp`. Never default container diagnosis or kill operations to `forge job webshell exec`. Follow the region-specific route in [references/primus_pods.md](references/primus_pods.md).
- Catalog / enumeration questions ("有哪些巡检规则", "有哪些卡型", "能选哪些 model type", "有哪些日志类型", "巡检目标有哪些", …) must be answered by actually running the matching list / get-meta command (`inspection rule list`, `inspection gpu-type list`, `inspection target list`, `job model-type list`, `job log get-meta`, …) and reading its real output. Do not answer from this skill's documentation alone, and do not present a command you did not run as if it were the answer.
- On HTTP 429 / rate-limit errors, back off a few seconds and retry the same command 2–3 times before drawing any conclusion. If it still fails, report that the API is rate-limited and the data was **not** retrieved — never turn a 429 into a "no data" / "not found" conclusion, and never switch to guessing in place of the blocked query.

## Related local assets

- `scripts/batch_query_series.py` — helper shipped alongside this skill to split larger `job wandb|tensorboard query` path sets into default 10-path batches (≤100 exact paths per CLI request), pass every path as a separate `--paths` flag, and merge them into one consolidated output directory. Used from `references/series.md`.
