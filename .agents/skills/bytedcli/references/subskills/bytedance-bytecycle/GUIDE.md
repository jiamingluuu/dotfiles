---
name: bytedance-bytecycle
description: Use when the user mentions ByteCycle, Canal Delivery, 发布火车, 火车, 车票, WIP 车票, 上车, release train, train MR, train pipeline, trigger ticket pipeline, or asks to operate ByteCycle through CLI.
---

# ByteCycle CLI

Use `bytedcli bytecycle <subcommand>` for ByteCycle / Canal Delivery workflows.

## Workflow

1. Identify the scenario first (see `references/scenarios.md`).
2. Read the matching reference in `references/` to find the exact command.
3. Prefer `--json` for automation. The structured schema is `{status, data, error, context}`.
4. Treat every write command as dry-run unless the user explicitly approves execution.
5. Pass `--yes` only after explicit user approval. Without `--yes`, write commands only print a dry-run payload or action summary.

## Top-level commands

| Family      | Purpose                                                           | Reference                  |
| ----------- | ----------------------------------------------------------------- | -------------------------- |
| `train`     | Release train lifecycle (get/list + write actions)                | `references/train.md`      |
| `ticket`    | Ticket create / boarding / WIP / edit / list                      | `references/ticket.md`     |
| `mr`        | Train MR query / create / merge                                   | `references/pipeline.md`   |
| `pipeline`  | Pipeline creation-status + build/job/manual-checkpoint operations | `references/pipeline.md`   |
| `execution` | Execution (pipeline node-level) get + list --mine                 | `references/execution.md`  |
| Auth/config | Login reuse and advanced troubleshooting overrides                | `references/auth.md`       |

## Auth & config

Use the normal `bytedcli auth` login state. Do not hand-write JWT, Cookie, domain, or API base URL values for routine agent workflows; see `references/auth.md` only for troubleshooting.

## Coverage scope

- **Train (fully wrapped)**: get / list / vars get / pipeline list / pipeline create-and-build / create / hotfix-create / quick-create / edit / to-integrating / to-code-freeze / to-deploying / merge-back / complete / cancel / rollback / complete-rollback / operation list.
- **Ticket (fully wrapped)**: get / list / create / pipeline list / pipeline create-and-build / wip create / wip board / approve / reject / update / vars update / warning get / revert request / revert approve / revert reject / remerge. Ticket create commands require a full payload file because payload fields are project-specific.
- **MR**: train get / create / merge.
- **Pipeline**: ticket status / train status / train jobs / train approve / trigger-ticket / trigger-train / build get / build list / build vars / build start / build rerun / job pending / job approve / job reject / job approve-build.
- **Execution (read only)**: get / list --mine.
- Not yet wrapped: full `execution` write side (submit / approve / reject / complete / rollback / mr / pipeline), the whole `config_delivery` scenario, monorepo flows, callbacks, lark-group / scm-list / branch-diff helpers. Use wrapped commands where available; do not expose private request details to agents. See `references/execution.md` and `references/config.md` for boundaries.
