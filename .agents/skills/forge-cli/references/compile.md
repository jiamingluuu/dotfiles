# compile.md — `forge code compile create` / `forge code compile get` / `forge code compile-artifact get`

Use this reference for Forge model/norbert compilation, local compilation, local validation, build status polling, Sail/Sail Dev/Zouwu compile parameters, compile log snapshots, and model compile artifact downloads. For install/auth/runtime basics see [invocation.md](invocation.md). Compile is a Forge workflow, not a native Git commit/push workflow.

## Intent Guard

- Forge compile/build intent -> use `forge code compile create`.
- Local compile intent (本地编译) -> use `forge code compile create --compile-mode local`. This flow creates a commit/build, runs compilation locally, uploads compile artifacts, and produces a handle for later `job create`. When the user asks for "本地编译", always use this real flow.
- Local compile with system/framework environment (系统环境 / framework Python) -> still use `forge code compile create --compile-mode local`; on official images pass `--use-venv`, while non-official `forge_dev` images select it automatically.
- Local compile with user/current environment (用户环境 / 当前python环境 / host Python) -> still use `forge code compile create --compile-mode local`; this is available on official images with `--use-venv` omitted. Do NOT use local validation for this.
- Local validation intent (本地验证) -> use `forge code compile create --compile-mode local-verify`; the CLI selects `fd build --local-verify` or `forge_dev build --local-verify` from `FORGE_COMPILER_VERSION`. This only runs model or Norbert code locally to check logic/output; it does not create a Forge commit/build, does not upload compile artifacts, and cannot be used for later training submission.
- Local Run intent -> not a compile task. Local Run pulls remote data, runs the model locally, and produces real outputs. Do not translate Local Run into local compile or local validation.
- Native Git intent (`git commit`, `push 代码`, `提交到远端分支`) -> use native Git commands; do not call Forge commit/compile.

## Workspace Rules

- Context-driven compile commands read `.forge/forge_meta.json` from cwd or nearby parent directories; `code compile create/get` does not accept `--dir` or `--output-dir`.
- Before context-driven compile, `cd` into the actual workspace root returned by `code fetch`, not its parent/wrapper directory, and say: `当前工作区是 <workspace>，version <version_id>，继续执行 compile。`
- If the user gives a path, verify that path has `.forge/forge_meta.json`. If multiple candidate workspaces are found, ask the user to choose; do not deduplicate by `version_id`, `project_name`, framework, or layout.
- If the current directory is an unrelated repo with no `.forge/forge_meta.json`, stop broad searching. Ask the user to run `forge code fetch --version-id <id>`, provide a precise workspace path, or pass explicit `--commit-id`.
- Explicit `--commit-id` can run without workspace context. Model compile reads framework from `get_commit`; norbert compile submits only the commit id. For local explicit-commit compile, if the current directory is inside a Forge workspace and the commit `version_id` differs from the workspace `version_id`, ask the user to confirm whether to continue; confirmed mismatch runs must not update the current workspace `.forge/forge_meta.json`.

### Explicit Commit Local Workspace Guard

Before `forge code compile create --compile-mode local --commit-id <id>` from inside a Forge workspace:

- Read the current `.forge/forge_meta.json`; record `workspace.version_id`, `workspace.framework`, `workspace.framework_version`, `workspace.source_type`, and the target commit artifact for `model` or `norbert` when present.
- Use read-only commit metadata for `<id>` as the source of truth. If commit metadata cannot be obtained, refuse instead of running local compile.
- If commit `version_id` differs from workspace `version_id`, tell the user both concrete values and ask whether to continue. If confirmed, rerun/continue the local compile; the CLI must not bind or persist compile context to the mismatched workspace, and `forge_dev` uses a per-build temporary output directory unless the user supplies `--local-output-path`.
- If commit `version_id` matches the workspace `version_id`, the CLI may use the workspace and persist the compile artifact for later `compile get` / `job create`.
- For git-managed workspaces that are used as the compile workspace, also require a clean worktree and current `git rev-parse HEAD` equal to the commit `git_commit_sha` or the matching `.forge` commit artifact `git_head`.
- Use this confirmation wording: `指定 commit <id> 属于 version <commit_version_id>，当前工作区 <workspace> 属于 version <workspace_version_id>，两者不匹配。是否仍然执行本地编译？确认后不会写入当前工作区 .forge/forge_meta.json。`

## Target Selection

- On `forge_dev`, local compile and model local validation default to `model` and infer Sail/Torch from workspace metadata; do not add `--code-type` or `--compile-type` unless the user is overriding a derived value. Norbert local validation still uses `--code-type norbert`.
- If the user explicitly says `model` or `norbert`, compile only that target.
- For remote compile, if the user asks to compile/build a workspace or fetched version and does not name a target, compile both `model` and `norbert`. This includes requests like `拉取 version 618896，然后编译时实时展示日志`. Local compile keeps the preceding `forge_dev` model-only default because Norbert local compile is unsupported.
- Run model and norbert as separate compile submissions and separate polling streams. Do not merge their statuses.
- Before compiling a workspace target, ensure that target has a Forge commit record. If missing, run `forge code commit create --code-type <model|norbert> --description "auto commit for compile"` for that target, then compile it.
- If the user provides a commit ID and does not name a target, do not default to both. Use the explicit-commit path: `forge code compile create --commit-id <commit_id>`. The CLI calls `get_commit`, infers `code_type`, and compiles the matching target. If metadata cannot infer `code_type`, ask the user whether it is `model` or `norbert`.

## Sail / Zouwu Parameters

Use these choice rules when Sail/Sail Dev/Zouwu parameters cannot be derived, such as remote compile, compatibility `fd`, or non-official Sail TensorFlow selection. `forge_dev` local defaults are described below.

- Ask exactly one form before running the command when values are missing.
- Form title: `Sail 编译参数` for Sail/Sail Dev, `Zouwu 编译参数` for Zouwu.
- Form fields: exactly TensorFlow version and GPU Graphs. Keep target, wait behavior, timeout, workspace, and commit id out of the form.
- TensorFlow: only pass `--tensorflow-version` after user selection; do not default to `1.15` or `2.5.0`.
- GPU Graphs: `training,serving` are required and always submitted. Optional closed-list extras are `gpu_training`, `gpu_training_dandelion_v3`, `gpu_training_dandelion_v3_streaming`, `gpu_training_jaguar`.
- Submit `--compile-graphs training,serving[,<extra graph>]`. If no optional graph is selected, submit `training,serving`.
- Display framework names as `Sail` / `zouwu`, not raw framework paths. Prefer submit label `开始编译` when the host supports it.

## Create Compilation

```bash
forge code compile create --code-type model
forge code compile create --code-type model --tensorflow-version <user-selected> --compile-graphs <user-selected-graphs>
forge code compile create --code-type norbert
forge code compile create --commit-id 123456
forge code compile create --code-type model --dry-run
```

Key flags:

| Flag | Notes |
|---|---|
| `--code-type` | `model` or `norbert`; optional when `--commit-id` is enough to infer `get_commit.code_type` |
| `--commit-id` | Explicit Forge commit id; skips workspace requirement and can infer code type |
| `--compile-mode` | `remote`, `local`, or `local-verify`; defaults to `remote` |
| `--compile-type` | Local-only override; `forge_dev` normally infers `torch` or `sail` from workspace metadata |
| `--tensorflow-version` | Sail/Sail Dev/Zouwu model compile; `forge_dev` derives official local Sail and prompts for non-official local Sail |
| `--compile-graphs` | Sail/Sail Dev/Zouwu graph set; `forge_dev` local modes and Torch default to `training,serving` |
| `--local-output-path` | Local compile/validation artifact directory; `forge_dev` defaults under the workspace |
| `--wait` | Blocking backend status wait with NDJSON; optional for synchronous `forge_dev` local compile |
| `--dry-run` | Validate without submitting |

Output rules:

- After plain remote `compile create` without `--wait`, tell the user only the `commit_id` and that compile was submitted. Do not expose `build_id` or local log paths unless explicitly asked for internals.
- Use `commit_id` as the user-facing handle for follow-up status/log work.

## Local Compilation

Local compile is a real Forge compile flow: it creates/submits a Forge build, starts the selected local compiler command, uploads artifacts on success, and is not local validation or Local Run. `FORGE_COMPILER_VERSION < 1.0.0.1940` selects the compatibility `fd` path unchanged; `>= 1.0.0.1940` selects `forge_dev` and enables the new CLI defaults and conflict checks.

### Agent session lifetime (MANDATORY)

- Agents must run local compile and local validation in the foreground and remain in the current session until the underlying `fd` or `forge_dev` command has fully exited. Do not end the turn, close the tool session, or report completion while it is still running.
- Do not background or detach these commands. Do not use `&`, `nohup`, `setsid`, `disown`, double-fork helpers, detached subprocesses, or any other attempt to bypass agent session cleanup.
- On `forge_dev`, omit `--wait` unless backend status events are specifically needed: the CLI still stays in the foreground until `forge_dev` exits and then returns final JSON. On compatibility `fd`, agent-run local compile must include `--wait`, because its no-wait path returns immediately after starting `fd`.
- Local validation is synchronous. Keep the foreground `forge code compile create --compile-mode local-verify ...` command open until it exits and returns its final result.
- If the agent cannot remain available for the full foreground wait, do not start local compile or local validation. Never start the task and then leave it with an unknown state.

`forge_dev` commands (`FORGE_COMPILER_VERSION >= 1.0.0.1940`):

```bash
forge code compile create --compile-mode local
forge code compile create --compile-mode local --local-output-path ./artifacts
forge code compile create --compile-mode local --use-venv  # official image: request framework Python
forge code compile create --compile-mode local --commit-id 123456
```

Compatibility `fd` command (`FORGE_COMPILER_VERSION < 1.0.0.1940`):

```bash
forge code compile create --compile-mode local --code-type model --compile-type torch --device cuda --use-venv --wait
forge code compile create --compile-mode local --code-type model --compile-type torch --device mlu --use-venv --wait
forge code compile create --compile-mode local --code-type model --compile-type sail --tensorflow-version <user-selected> --compile-graphs training,serving --use-venv --wait
forge code compile create --compile-mode local --code-type model --commit-id 123456 --device cuda --use-venv --wait
forge code compile create --compile-mode local --code-type model --wait  # omit --use-venv for current/user python
```

Hard stops:

- Runtime preflight: `--site us-ttp` and `--site eu-ttp` are unsupported; `FORGE_REGION` must match the target code region (`cn` for `--site cn`, `us` for `--site i18n`); `FORGE_IDE=1`, `FORGE_COMPILER_VERSION`, and the selected `fd`/`forge_dev` command in `PATH` are required.
- Compiler capability gate: before local compile or local validation, probe `FORGE_COMPILER_VERSION`, identify the requested capability from compile mode / framework / device, and check the capability rows below. Treat each row as a minimum compiler version; version X supports rows whose threshold is <= X, and overlapping rows use the highest matching threshold.
- If the current compiler does not support the requested capability, but a listed target version does, choose the lowest explicit supporting version and ask: `当前 FORGE_COMPILER_VERSION=<current> 不支持 <capability>，需要 <target_version>。是否升级本地 forge_compiler 环境？确认后我会执行：bvc clone data/reckon/forge_compiler /opt/tiger/forge_compiler --version <target_version> -f && export FORGE_COMPILER_VERSION=<target_version>`
- If the user confirms the upgrade, run `bvc clone data/reckon/forge_compiler /opt/tiger/forge_compiler --version <target_version> -f && export FORGE_COMPILER_VERSION=<target_version>`, then continue the local compile or validation with that `FORGE_COMPILER_VERSION` in the shell/session that runs the command. If the user declines, do not run the local workflow.
- Capability `>= 1.0.0.1821` and `< 1.0.0.1891`: torch model local compile on GPU only (`cuda`/`mlu`).
- Capability `>= 1.0.0.1891`: torch model local compile on `cpu` / `cuda` / `mlu`; Sail/Sail Dev model local compile; torch/Sail local validation. Compatibility `fd` still requires explicit Sail TensorFlow/graphs.
- Capability `>= 1.0.0.1940`: Norbert local validation with compiler-managed system/framework venv.
- Unsupported by listed compilers: Zouwu local compile, norbert local compile, torch `ascend`, TTP local compile.
- For torch local compile, `--device` may be omitted or set to `cpu`, `cuda`, or `mlu`; omitted probes cuda then mlu, and only uses CPU on compiler versions that support CPU.
- Without `--commit-id`, torch local compile requires a torch-dev Forge workspace (`aml/lagrange_admin/torch_dev`); Sail/Sail Dev local compile requires a matching workspace and supporting compiler. On `forge_dev`, code type and compile type come from workspace metadata, graphs default to `training,serving`, and missing Sail TensorFlow is derived from an official installation record or prompted for a non-official image. Zouwu and norbert local compile are unsupported. The CLI creates a fresh commit and build. Do not reuse a previous successful workspace commit unless the user explicitly asks for it.
- With `--commit-id`, workspace context is optional; from inside a workspace, apply the Explicit Commit Local Workspace Guard.
- If commit `build_status` is `SUBMITTED`, `PREPARING`, or `RUNNING`, refuse because it is already compiling.

Behavior/output:

- On the compatibility `fd` path, agents should pass `--use-venv` by default and omit it only when the user asks for user/host Python. On the `forge_dev` path, omit it unless an official-image user explicitly requests the framework environment, so the CLI can apply the image-type default.
- On the `forge_dev` path, official images default local compile to user Python; non-official images default to the compiler-managed system venv. The compatibility `fd` path keeps the user's existing `--use-venv` behavior.
- Torch local compile sends `compile_site=local`, torch defaults, `use_venv`, and `computation_platform`, then starts the selected local compiler command. Every option dispatched to `forge_dev` uses its canonical long name (`--compile-type`, `--build-id`, `--use-venv`, `--device`, `--local-output-path`, and `--local-code-path` where applicable); do not generate short aliases for `forge_dev`. The compatibility `fd` invocation remains unchanged.
- Sail local compile sends `compile_site=local`, `tensorflow_version`, normalized `compile_graphs`, `is_parallel=true`, and `use_venv`. After the build is created, `forge_dev build --build-id` does not repeat TensorFlow, graphs, or parallel fields; the compatibility `fd` invocation is unchanged.
- On the `forge_dev` path, `--local-output-path` selects the artifact directory for local compile and local validation. Relative explicit paths resolve under the Forge workspace; defaults stay outside it at `<os temp>/forge/local-compile/build-<build_id>` and `<os temp>/forge/local-verify`. An explicit output directory must be absent or empty because the compiler replaces it.
- On `forge_dev`, the default no-`--wait` invocation stays synchronous and returns final JSON after artifact upload. The compiler's stdout and stderr are redacted and written to CLI stderr so stdout stays machine-readable; a non-zero exit also points to `forge code compile get --code-type <type> --commit-id <id>`. `--wait` is optional and switches output to backend NDJSON status events. Compatibility `fd` still needs `--wait` for agent-driven foreground completion.
- With `--wait`, use the same NDJSON wait flow as remote compile. Local compile succeeds only when Forge reaches a successful terminal build status and the selected local compiler command exits successfully; any Forge failure, non-zero local compiler exit, timeout, or interruption returns failure.
- User-facing summaries should use `commit_id`, local compile type, device, Python environment, compiler version, and final artifact-upload status only after success.

## Local Validation

Local validation is local-only execution for checking model or Norbert logic/output. It maps to `--compile-mode local-verify` and the version-selected `fd build --local-verify` / `forge_dev build --local-verify` implementation, but conceptually it is not local compile and not Local Run.

`forge_dev` commands (`FORGE_COMPILER_VERSION >= 1.0.0.1940`):

```bash
forge code compile create --compile-mode local-verify
forge code compile create --compile-mode local-verify --local-output-path ./validation-output
forge code compile create --compile-mode local-verify --code-type norbert
```

Compatibility `fd` command (`FORGE_COMPILER_VERSION < 1.0.0.1940`):

```bash
forge code compile create --compile-mode local-verify --compile-type torch --local-code-path /workspace/demo/models
forge code compile create --compile-mode local-verify --compile-type sail --local-code-path /workspace/demo/models --compile-graphs serving
```

Use local validation only when the user asks to validate logic/output locally or explicitly asks for `local-verify`. It has no Forge side effects, needs no Forge commit, does not upload artifacts, and cannot be followed by `job create`.

Local validation through the CLI requires a compiler version that supports local validation. On `forge_dev`, model compile type is inferred from workspace metadata. Official Torch supports `cpu`, `cuda`, and `mlu`; an omitted device probes CUDA, then MLU, then CPU. Non-official Torch is intentionally unavailable in the CLI. Sail graphs default to `training,serving`. Official Sail rejects a user-supplied TensorFlow version and reads it from the image installation record; non-official Sail prompts for `1.15` or `2.5.0` in an interactive terminal and requires the flag in non-interactive use.

Norbert local validation requires `FORGE_COMPILER_VERSION >= 1.0.0.1940` and a Forge workspace whose metadata contains both `framework` and `framework_version`. The CLI uses `<workspace>/norbert`, fixes the internal compile type to `norbert`, and always invokes the compiler-managed system/framework venv with `--use-venv true`; `--use-venv` is not a user-selectable switch. Sail frameworks select py37. Torch frameworks select py311 and honor `--device`; images that only contain py37 do not support Torch-framework Norbert validation. The result has `code_type=norbert`, `compile_type=norbert`, and `python_environment=system`, without creating a commit/build or uploading artifacts.

`local-verify` runs synchronously. For this mode only, the CLI routes the selected local compiler's stdout and stderr to CLI stderr through the same sensitive-text redaction used for compile logs, then prints the normal JSON result on stdout when validation succeeds. This preserves the CLI contract that stdout stays machine-readable for strict JSON consumers, while stderr carries human-readable logs and warnings without leaking token / jwt / secret / cookie / authorization-like values. On validation failure, compiler output has already been shown in redacted form and the command returns a `local_verify_compile_failed` error. Sail local validation passes `--is-parallel false` only to the internal compiler invocation; `forge code compile create` does not expose an `--is-parallel` flag.

Do not use local validation for:

- "本地编译" / "local compile" / "fd build" when the user expects compile artifacts for training.
- "当前 python 编译" / user environment compile; that is local compile with `--use-venv` omitted.
- Local Run; Local Run pulls remote data and produces real model outputs, which is a separate workflow.

## Live Progress / Logs

When the user asks for `实时展示日志`, `边编译边看日志`, `follow compile logs`, or visible progress:

This submit-then-poll flow applies to remote compile only. For local compile and local validation, follow **Agent session lifetime (MANDATORY)** above and keep the foreground command open until the selected local compiler and enclosing `forge` command finish.

1. Determine targets using Target Selection, then submit each target without `--wait`.

   ```bash
   forge code compile create --code-type <model|norbert>
   forge code compile create --commit-id <commit_id>
   ```

2. Parse `code_type` and `commit_id` from each submit result.
3. CRITICAL: poll exactly one short command per tool call.

   Do not use Bash loops. Do not chain commands with `sleep`, `&&`, `;`, or pipelines for polling. Do not run multiple `compile get` commands in one Bash/tool call. Each poll must be exactly one `compile get` command:

   ```bash
   forge code compile get --code-type <model|norbert> --commit-id <commit_id>
   ```

4. MANDATORY: immediately after each poll completes, output a text message to the user before making any other tool call. Do not run any extra command to read the local log file between `compile get` and this message. Use this exact shape:

   ```text
   Status: <status>
   Summary: <message or short newest log excerpt>
   ```

   Build Summary from the `compile get` response only: prefer its message or newest log excerpt from that response. Do not invent log paths when a response omits build metadata.
5. If the status is `SUBMITTED` for 1 minute across repeated polls, stop polling and report that the compile submission appears stuck.
6. If the status is not terminal, wait 10 seconds before the next poll, then repeat step 3. Use a separate sleep/wait action such as `sleep 10`. Never combine the pause and next poll in the same Bash/tool call.
7. Stop at terminal status: `SUCCESS`, `SUCCEEDED`, `FAILED`, `FAIL`, `CANCELED`, `CANCELLED`, `ABORTED`, `KILLED`, `TIMEOUT`.

Do not use `compile create --wait --wait-timeout 30m` as the default for live-log requests; it blocks the agent tool call and can look stuck.

## Check Status

```bash
forge code compile get --code-type model
forge code compile get --code-type model --commit-id 123456
forge code compile get --code-type model --wait --wait-timeout 10m
```

- Without `--commit-id`, `compile get` reads the target-specific compile handle from the current workspace.
- With `--commit-id`, it resolves the latest build without workspace context.
- `--wait` is for CI/E2E or explicit wait-only requests. It emits NDJSON events (`started`, `log_file`, `status`, `summary`) and does not stream full logs. Local and remote compile keep the same wait event shape. It fails if status stays `SUBMITTED` for 1 minute.

## Download Compile Artifact

Use `forge code compile-artifact get` when the user asks for the UI action **Download Model Meta**, “下载模型编译产物”, “Forge 平台模型编译产物下载”, `compiled_new`, or `get_model_meta`.

```bash
forge code compile-artifact get --commit-id 5820082 --site cn
forge code compile-artifact get --commit-id 2144154 --site i18n
forge code compile-artifact get --commit-id 936867 --site us-ttp
forge code compile-artifact get --commit-id 936867 --site eu-ttp
forge code compile-artifact get --commit-id 5820082 --output ./compiled_code_5820082.tar.gz
```

- The command downloads the raw archive returned by the backend and does not extract it.
- `--commit-id` is optional in a Forge workspace; when omitted, it infers the model artifact from model compile context first, then model commit context.
- When workspace compile context records a model `build_id`, the CLI checks that staged build directly and downloads using the context's model `commit_id`; explicit `--commit-id` and commit-only context fall back to the commit's latest model compile build. A fork commit may reuse a source commit's build, so the selected build's `commit_id` does not need to equal the requested commit id.
- Before downloading, the CLI proceeds only when the selected build status is successful (`SUCCESS` / `SUCCEEDED`).
- `--output` is a file path, not a directory. When omitted, the CLI uses the server attachment filename in the current directory. Pass `--force` to overwrite an existing output file.
- Do not use `code commit get` for this: `code commit get` restores source code, while `code compile-artifact get` downloads model compile artifacts.
- The CLI chooses the backend from `--site`: cn/i18n use their site Reckon download host; eu-ttp/us-ttp use global `get_model_meta` with the correct region parameter. TTP downloads require i18n scoped auth; if auth fails, tell the user to run `forge --site i18n auth login --begin` / `--complete`. Do not ask users to pass a region flag.

## Log Snapshots

- Plain `compile create` does not fetch backend logs or create/update `<temp>/forge/compile-logs/...`; a missing local log file right after submit is expected.
- Local `compile create --compile-mode local` follows the same log snapshot rules as remote compile: `fd build` stdout/stderr is not written under `<temp>/forge/compile-logs/...`, and backend logs are written only through `compile create --wait` or `compile get` when Reckon returns them.
- `compile get` fetches current state and any available backend logs. When logs are returned, the CLI writes redacted snapshots under `<temp>/forge/compile-logs/...`.
- For live-progress requests, do not read the snapshot file in a separate tool call. Use the `compile get` response as the only source for the summary.
- For one-shot summaries, use `compile get` output and omit internal paths unless useful. The snapshot file path is for user navigation/debugging, not an extra polling step.
- Logs are redacted for token/jwt/secret/cookie/authorization-like keys; do not disable redaction.

## Behavior Notes

- Torch model compile defaults `torch_version=2.4` and `compile_graphs=training,serving` unless explicitly overridden.
- Norbert compile submits only `commit_id`; framework-specific fields are cleared.
- Git-managed workspaces may auto-create a Forge commit record before compile. That means `code update` -> `code commit create` -> compile. This does not create a native Git commit; dirty worktrees are rejected.
- For `--site us-ttp`, compile keeps the same CLI surface. Any auto-created commit uses the TTP bridge inherited from `code commit create`.
- Missing workspace metadata should be handled before starting any long compile flow: refetch/select the workspace, or switch to explicit `--commit-id`.
