---
name: bytedance-sar
description: Use SAR Creator Arcade through bytedcli for local Codex project initialization, exact Skills version management, local project upload, and uploaded Arcade Thread management.
---

# SAR Creator Arcade

Use the built-in `bytedcli sar` command. Prefer `--json` for agent calls. Develop with Codex in a
local initialized project, then upload and manage the result through Arcade.

## Initialize and manage Skills

Initialize the thread-root directory and install an exact published Skills release:

```bash
bytedcli --json sar init --project-dir ./demo
bytedcli --json sar init --version 0.1.19 --project-dir ./demo
bytedcli --site boe --json sar init --thread-id sample-thread-id --project-dir ./demo
```

Manage the project-local Skills after initialization:

```bash
bytedcli --site boe --json sar skills sync --project-dir ./demo
bytedcli --json sar skills sync --project-dir ./demo
bytedcli --json sar skills sync --version 0.1.19 --project-dir ./demo
bytedcli --json sar skills status --project-dir ./demo
bytedcli --site boe --json sar skills check-update --project-dir ./demo
```

The global site selects both the Arcade environment and its published Skills release: `cn` maps to
the production release and `boe` maps to the BOE release. Pass `--version` to install an explicit
exact version instead. The project persists only the resolved `skills.version` in
`sar-local/project.json`.

`init` creates the local thread-root layout: `workspace`, `.codex-data`, `outputs`, `uploads`,
and `tmp`. It installs Skills into `.agents/skills` and writes a managed local-execution block to
the root `AGENTS.md`. The game project lives in `workspace`; the root represents all files that
may correspond to an online Thread. Initialization requires a missing or empty target directory
and does not create or bind an online Thread.

With `--thread-id`, `init` first verifies that the current Arcade identity owns the Thread, then
initializes the same local runtime and checks out the latest downloadable online `workspace`. It
does not download online messages, Runs, uploads, outputs, or `.codex-data`. Rebuild the project
locally before uploading it again.

`--project-dir` must identify the complete local project directory. If the user provides only a
parent directory for a checkout, inspect its sibling naming convention and ask the user for the
leaf directory name before running `init`. Never use the Thread ID as the directory name by
default, and never infer a name that would collide with an existing project. For a checkout, run
the command from the parent directory and pass that leaf path explicitly; checkout does not replace
the shell's current working directory.

`skills sync` replaces only SAR-managed Skills and preserves unrelated local Skills. Repeating a
healthy exact version is idempotent. `skills check-update` is read-only.

## Upload and manage Arcade Threads

A local project is uploadable after it has
`workspace/game/.settings/project.json` and `outputs/dist/web/index.html`.

Create a new online Thread:

```bash
bytedcli --site boe --json sar arcade create --project-dir ./demo
```

Every `arcade create` creates a new Thread. It returns `projectId`, `sessionUrl`, and
`previewUrl`, but does not bind that Thread to the local project. By default no game title is
inferred from the package or directory name; Arcade keeps it empty until game identity generation
completes. Pass `--game-title` only when the user explicitly supplied a title.

Replace the current version of an existing owned Thread:

```bash
bytedcli --site boe --json sar arcade update \
  --project-dir ./demo \
  --thread-id sample-thread-id \
  --yes
```

`arcade update` checks ownership server-side and rejects an active Thread. Without `--yes`, it
returns `SAR_ARCADE_CONFIRMATION_REQUIRED` and stops before uploading.

List and delete uploaded Threads:

```bash
bytedcli --site boe --json sar arcade list --page 1 --page-size 20
bytedcli --site boe --json sar arcade delete --thread-id sample-thread-id --yes
```

Treat the returned `projectId`, Session ID, and Thread ID as the same identifier. At the CLI
boundary, management mutations accept `--thread-id`.

## Upload contract

The upload includes `workspace`, `outputs`, `uploads`, and the selected root Codex task's raw
rollout files under `codex`. The CLI does not materialize or upload `.codex-data`; creator-server
converts raw rollout data into platform-authoritative messages, Runs, Usage, Cost time, and trace.
Local Skills, `sar-local`, `AGENTS.md`, `.codex-data`, and `tmp` are excluded.

The archive is built from a temporary copy. In UTF-8 text files, the exact local thread-root prefix
is rewritten to `/mnt/user-data`; binary files and the original local project remain unchanged.

Before `arcade create` or `arcade update`, the CLI must locate the Codex root task that developed
the project. If the project is not backed by Codex, stop with
`当前仅支持 codex，如有其他 Agent 适配需求可联系 @longzhou`.

For local creator-server integration against BOE-backed data, add the loopback-only
`--api-base-url http://127.0.0.1:3000/arcade/api/cli/sar-creator-arcade`. The global
`--site boe` still selects BOE authentication and the BOE session URL.

## Identity and environment

Resolve the current CLI identity with:

```bash
bytedcli --json sar user status
```

Arcade maps the email verified by the ByteCloud JWT to the Arcade Feishu app's `open_id`. If CLI
authentication is missing, run `bytedcli --site <cn-or-boe> auth login`. Do not invent or fall back
to another identity mapping.

Use global `--site boe` only when targeting BOE; `--site cn` selects production. The same site
selects the corresponding published Skills release unless `init` or `skills sync` receives an
explicit `--version`.

## Rules

- Local initialization and Skills management never create or bind an online Thread.
- `arcade create` always creates a new online Thread.
- `arcade update` changes only the explicitly authorized Thread and never persists a binding.
- `arcade delete` requires the exact `--thread-id` and `--yes`.
- Return the URLs supplied by Arcade; never construct a CDN URL locally.
- Authentication errors may include `hint` and `auth_command`; execute or relay them instead of
  guessing identity mappings.
