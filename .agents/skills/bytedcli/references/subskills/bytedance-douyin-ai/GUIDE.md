---
name: bytedance-douyin-ai
description: Use when the user asks about Douyin AI workspaces, agents, knowledge-base metadata lookup or knowledge-base data rows (listing, adding, or deleting one row), project deployment to the short-drama creative platform, operation data, traces, Workflow creation or DSL export/import/deployment, internal Skills, Skill permissions, or Plugin packaging, publishing, validation, and debugging through bytedcli.
---

# Douyin AI CLI

Use `bytedcli douyin-ai <resource> <action>` for the internal Douyin AI platform.

## Before invoking

1. This domain only supports the global `--site cn` profile.
2. In chat_server, authentication automatically uses the injected shared session; do not run interactive login. Outside chat_server, reuse the browser session created by `bytedcli --site cn auth login --session`. Never request or hand-write a Cookie.
3. Prefer `bytedcli --json douyin-ai ...` for automation. The output schema is `{status,data,error,context}`.
4. Read `references/commands.md` before composing a concrete invocation.
5. Treat every remote write as dry-run by default. Pass `--yes` only after the user has reviewed and approved the plan.

## Capability map

| Resource          | Actions                                                                           |
| ----------------- | --------------------------------------------------------------------------------- |
| Workspace/project | `space list`, `project list`, `project deploy`                                    |
| Ordinary Agent    | `agent get`, `agent export`, `agent update`, `agent deploy`                       |
| Knowledge base    | `knowledge-base list`, `knowledge-base get`, `knowledge-base data list`, `knowledge-base data create`, `knowledge-base data delete` |
| Observability     | `operation-data get`, `trace get`, `trace list`                                   |
| Workflow          | `workflow create`, `workflow export`, `workflow import`, `workflow deploy`        |
| Skill             | `skill upload`, `skill download`                                                  |
| Skill permission  | `skill permission list`, `update`, `delete`                                       |
| Plugin            | `plugin create`, `upload`, `deploy`, `get`, `validation execute`, `debug execute` |

## Safety

- `agent update`, `agent deploy`, `project deploy`, `knowledge-base data create`, `knowledge-base data delete`, `workflow create`, `workflow import`, `workflow deploy`, Skill upload and permission changes, and Plugin upload/deploy/validation/debug do not write remotely without `--yes`.
- Ordinary Agent (`appMode=0`) is a main-repository capability, not a plugin. Use the Agent commands for native rich-text Prompt, seven model fields, tool/dataset bindings and custom inputs. Read the Agent section in `references/commands.md` before preparing a patch: arrays replace the final editable list, and `[]` clears it.
- `knowledge-base list` and `knowledge-base get` are read-only and workspace-scoped. Return name-search candidates and pagination information; confirm the ID before composing an Agent binding, without automatically selecting a duplicate name or editing its Prompt.
- `knowledge-base data create` and `knowledge-base data delete` change one row each. Field names are validated against the knowledge base schema before a request body is built, and `--knowledge-base-key` only asserts the key resolved from `--knowledge-base-id` instead of overriding it. `data delete` needs a knowledge id and its owning document id; take both from `data list`, which reports them per row, instead of guessing or copying them from a browser capture. Deleting cannot be undone from the CLI, and rows are only readable page by page, so a success means the platform accepted the write rather than that the row content was verified.
- Agent preservation/readback covers only `preservation_scope=api_visible_config`; existing server transformations remain unchanged. `agent update` saves a draft; `agent deploy` publishes the whole current publishable draft, including web edits, with `test_run_validated=false` and no trial Trace.
- For Agent deploy automation, preview with `--plan-out <file>`, review the plan, then execute with `--plan <file> --yes` and the same target. The private baseline contains identity and versioned hashes only; it constrains the current draft and is never replacement configuration. Drift or a disappeared draft rejects before no-op and is checked again under the lease. Direct `--yes` remains supported but does not bind an earlier preview.
- On a nonzero exit after Agent submission, inspect the receipt in `data.result` and read back before any new command. `outcome_unknown`, `submitted_unverified`, and `verification_failed` are not proof of no write. Successful writes with lease warnings are `partial_success`. Never blindly retry or roll back.
- `project deploy` currently supports only `--channel playlet-creative` and always targets the fixed `douyin_series` workspace.
- `--force` only confirms a local overwrite or Workflow draft replacement. It never authorizes a remote write.
- `trace list` requires a workspace boundary and defaults to at most 100 deduplicated Trace candidates. Pass `--all` only when the user explicitly accepts an unbounded result set; partial detail failures use `partial_success` and exit code 1.

## References

- `references/commands.md` — complete command and flag surface.
- `references/auth-and-safety.md` — session reuse, CN restriction, dry-run behavior, and troubleshooting.
- `../../invocation.md` — shared bytedcli installation and invocation conventions.
- `../../troubleshooting.md` — shared bytedcli troubleshooting guidance.
