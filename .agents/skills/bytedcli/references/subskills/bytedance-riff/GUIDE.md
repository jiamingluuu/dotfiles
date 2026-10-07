---
name: bytedance-riff
description: "Operate the Riff agent task platform via bytedcli: create tasks from templates or prompts, wait for or watch task output, follow up or re-run a thread, cancel tasks, list result files and download artifacts, and browse templates. Use when tasks mention Riff, riff.bytedance.net task or template links, delegating work to a Riff sandbox agent, or reading a Riff task result."
---

# bytedcli Riff

Use this skill when the task mentions Riff / riff.bytedance.net, wants to delegate work to a Riff sandbox agent, or needs the status, output or result files of a Riff task.

Riff is the ByteDance agent task platform: a task runs an agent (codex / claude) inside a cloud sandbox with a repo, skills and credentials injected, and produces output, result files and optional Feishu docs. Templates package a reusable task configuration.

- What Riff is and how to use it (Feishu doc): https://bytedance.larkoffice.com/wiki/NFiBwXU93iuJS0kg63OcVyKpnSe
- Full OpenAPI reference (every endpoint, parameter and error code behind these commands): https://riff.bytedance.net/openapi — Markdown for agents: fetch https://riff.bytedance.net/api/openapi?format=md (always the latest version)

## How To Call

Use `bytedcli` directly. Put `-j` before the domain for machine-readable output:

```bash
bytedcli -j riff <resource> <command> [options]
```

When parameters are unclear, inspect help instead of guessing:

```bash
bytedcli riff --help
bytedcli riff task --help
bytedcli riff task create --help
```

## Usage Principles

- Always go through `bytedcli riff`; do not hand-write curl against `/api/task-execute` or other Riff endpoints.
- Template first: find a template with `riff template list`, then `riff task create --template-id <id> --prompt "..."`. The prompt becomes the template `userPrompt`; never paste template content into the prompt and never override template settings (`--agent`, `--model`, `--skill`, `--env-var`, `--lark-doc`) unless the user asked for it.
- Riff creates `${TASK_OUTPUT_DIR}/result.md` by default. Plain answers and analysis are read from the task output (`task get` / `task watch`); file artifacts are read with `task result` and `task download`. Do not rewrite the prompt just to force a `result.md`.
- If the user wants a merge request, write "create a draft MR / merge request" into the task prompt; there is no MR field on the command.
- Task artifacts belong to `TASK_OUTPUT_DIR` inside the sandbox; never ask the task to write results back into the business repository as its deliverable.
- `--lark-doc` is off by default (the Riff OpenAPI default); pass it only when the user wants a Feishu doc.

## When To Use

- Find a template with `riff template list --keyword <keyword>` and read it with `riff template get --id <templateId>`.
- Create a task from a template with `riff task create --template-id <id> --prompt "..."`.
- Create a plain task with `--repo <group/repo> --branch <ref> --prompt-file ./prompt.md` when no template fits.
- Wait for a result in one call with `--wait`, or attach later with `riff task watch --id <taskId>`.
- Read status and the output tail with `riff task get --id <taskId>`; use `--output-tail-bytes 0` for the full output.
- List result files with `riff task result --id <taskId>` and fetch one with `riff task download --id <taskId> --path <file.path>`.
- Continue a thread with `riff task follow-up --parent-id <latestTaskId> --prompt "..."`, or re-issue a failed/cancelled/timeout task with `riff task rerun --id <taskId>`.
- Stop a task with `riff task cancel --id <taskId>`.

## Auth

- Every request sends the **cn-site ByteCloud JWT** as `x-jwt-token`; run `bytedcli auth status` first and `bytedcli auth login` if it is not authenticated.
- Riff is served on the default `--site cn` (`https://riff.bytedance.net`) only.
- Inside a Riff sandbox the injected ByteCloud JWT already authenticates bytedcli, so a running task can spawn sub-tasks with the same commands.

## Quick Start

```bash
bytedcli -j riff template list --keyword demo
bytedcli -j riff task create --template-id demo-template-id --prompt "分析最近一次 CI 失败原因" --wait
bytedcli -j riff task get --id demo-task-id
bytedcli -j riff task result --id demo-task-id
bytedcli -j riff task download --id demo-task-id --path result.md --output-dir ./riff-output
bytedcli -j riff task follow-up --parent-id demo-task-id --prompt "把修复方案写成 MR 描述" --wait
```

## Featured E2E Templates

Riff runs full end-to-end (E2E) test and delivery flows smoothly through templates — real devices, in-app debugging, UI automation and visual assertions inside one task. Start from these public templates with `riff task create --template-id <id> --prompt "..."`:

| Template | Template id | What it does |
|---|---|---|
| [Lynx Sandbox 模板](https://riff.bytedance.net/app/413f7482-22e2-4824-8c16-0eda0a12dbb2/dashboard) | `413f7482-22e2-4824-8c16-0eda0a12dbb2` | Lynx / Relax / Web development with Lynx Sandbox and Lynx DevTool |
| [webinfra-e2e](https://riff.bytedance.net/app/b6f2a2ae-39b7-46a8-af65-2ab1721c403f/dashboard) | `b6f2a2ae-39b7-46a8-af65-2ab1721c403f` | Cross-platform AI-native E2E testing: consumes natural-language test cases and closes the loop of device occupation, in-app debugging, UI automation and visual assertions |
| [豆包小程序开发](https://riff.bytedance.net/app/b631cdfd-c08f-4013-8bb5-867ed078a020/dashboard) | `b631cdfd-c08f-4013-8bb5-867ed078a020` | Develops Doubao mini-programs from requirements or an existing dbx project and finishes E2E acceptance on real Android / iOS devices |

```bash
bytedcli -j riff task create --template-id b6f2a2ae-39b7-46a8-af65-2ab1721c403f \
  --prompt "用例：打开设置页，切换深色模式，断言页面主题变化" --wait
```

## Output Conventions

- Text mode: agent output chunks go to stdout verbatim; status transitions (`pending` → `queued` → `creating_session` → `running` → terminal) go to stderr; the final summary table (status, exit code, duration, URL, preview, published docs) goes to stdout.
- `-j`: `create/follow-up/rerun --wait` print one terminal JSON envelope (`task_id`, `status`, `exit_code`, `duration_sec`, `result_output`, `artifact_publications`, `waited_via`); `watch` prints one NDJSON line per stream event (`init`, `status`, `output`, `log`, `done`, ... unknown events pass through as `event: "unknown"`) followed by the final envelope; other commands print a single JSON envelope.
- No output ever contains the JWT, signed download URLs or `--env-var` values; `task get` lists only `env_keys`.
- Task status values: `pending`, `queued`, `creating_session`, `running`, then `completed` / `failed` / `cancelled` / `timeout`.

## Agent Guidance

- `--sandbox-cluster` defaults to `boe` (same as the Riff OpenAPI default); pass `--sandbox-cluster cn` for the prod sandbox pool.
- `--skill` takes `<source>#<skill>[@<version>]`, e.g. `code.byted.org/demo-group/demo-repo#demo-skill`; `--skills-file` accepts a JSON array of `{ "source", "skill", "versionPolicy"? }`.
- `--env-var KEY=VALUE` sets task environment variables. Do not put secrets in prompts.
- `task result` is the artifact interface; `status: empty` or `unavailable` means no result files, not a failed task.
- `task download` only works for files marked `downloadable` (they have an archive copy).

## Failure Handling

- `AUTH_REQUIRED` / HTTP 401: run `bytedcli auth status`, then `bytedcli auth login`, and retry with the same arguments. `RIFF_FORBIDDEN`: only the task or template owner can access it.
- `RIFF_TASK_WAIT_TIMEOUT` (default 30 minutes): the task keeps running; check later with `riff task get --id <taskId>` or `riff task watch --id <taskId>`.
- `RIFF_TASK_INTERACTION_REQUIRED`: the agent asked a runtime question; the task is still running and must be answered on the Riff task page before waiting again.
- Stream interruptions are handled automatically: `watch` / `--wait` fall back to polling task detail and report the terminal status.
- Riff error codes are kept in `details.riff_code` — for example `UNSUPPORTED_AGENT_MODEL` (with `supportedModels`), `WEEKLY_COST_QUOTA_EXCEEDED`, `AGENTBUDDY_AUTH_REQUIRED` (complete the authorization from `hint`, then retry). Follow the `hint` before retrying; do not change the task arguments to work around an authorization error.
- `task-result` `empty`: the task produced no files; read the answer from `task get --output-tail-bytes 0`.

## References

- Read [Invocation and global options](../../invocation.md) before installing/updating bytedcli, choosing global `--site`/`--json` placement, or diagnosing ByteCloud authentication.
- Fetch `https://riff.bytedance.net/api/openapi?format=md` (e.g. with curl; no auth required, always the latest version) when a task needs an endpoint, request field or error code that the CLI commands do not cover (triggers, runtime-interaction answers, template management).
- Read [Troubleshooting](../../troubleshooting.md) when a `riff` command is missing or fails because of authentication, network, permissions, or CLI version drift.
