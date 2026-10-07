---
name: bytedance-oxygen
description: Use when users ask to create Oxygen materials, initialize/update/execute fresh material devtasks, verify new material versions, check publish status, or release an exact version. Also use when workflows need the materials aggregate endpoint, uniqueId resolution, or prod confirmation gates. Do not use for rollback requests or pure code-reading questions.
---

# Oxygen Material

## Overview

This skill is for Oxygen material (物料) publish workflows. Oxygen is a TikTok
material publish platform at `oxygen.tiktok-row.net`.

The CLI wraps the Oxygen aggregate endpoint through `bytedcli oxygen` commands.
Keep the workflow focused on user intent, confirmation gates, aggregate action
selection, and the single delayed status check after `execute`.

In publish flows, distinguish `devtaskName` from material names. A devtask is a
single material-version batch, not a reusable release channel. Publishing a new
code revision requires a uniquely named fresh devtask and new version IDs;
existing devtasks may be read for history or updated only before their first
execute.

## Required Workflow

1. Use `bytedcli oxygen config get` to read local `.oxygen.json` state.
2. Keep `.oxygen.json` minimal with product identity: `{ "productKey": "..." }`.
3. Treat `.oxygen.local.json` as a local runtime override for `oxygen_env` only.
   The skill must not read it directly or rely on it for workflow decisions.
4. Never persist login state, SSO tokens, cookies, or operator identity in
   `.oxygen.json` or `.oxygen.local.json`.
5. Always execute commands with the business-project root as `cwd`. If the user
   already provided the target business-project root/path explicitly, use it
   directly; otherwise, if the active working directory is not already the target
   material project, stop and ask which business-project root to use.
6. If the user explicitly provides `devtaskName`, use it for the current
   conversation only and pass it through via `--devtask-name`. Never write it
   into `.oxygen.local.json`.
7. For every new code release, generate an explicit unique devtask name. Do not
   use the CLI's deterministic default: it can resolve to an executed historical
   devtask on later commits of the same branch.
8. Prefer granular `devtask init` then `devtask execute` for production so the
   fresh-task boundary is visible. `devtask publish` is safe only with an
   explicit unique name that does not resolve to an executed devtask.
9. Interpret publish intent carefully before choosing the aggregate action:
   - `发布物料 <name>` or `发布这个物料 <name>` means `<name>` is a material name.
   - `在当前 devtask 上发布物料 <name>` is valid only when that devtask has not
     executed yet and is still being assembled for the same batch. If it has
     executed, create a fresh devtask instead.
   - Only treat user input as `devtaskName` when the user explicitly says
     `devtask`, or otherwise clearly identifies a devtask instead of a material.
10. Confirmation via dry-run: write commands (`material create`, `devtask init`,
    `devtask update`, `devtask execute`, `devtask publish`) default to a dry-run
    preview and require `--yes` to actually submit.
    - For prod-targeted writes, first run without `--yes`, show the dry-run
      preview to the user, get explicit confirmation, then re-run with `--yes`.
    - For PPE-targeted writes you may pass `--yes` directly.
    - Never pass `--yes` for a prod write without explicit user confirmation.
11. For auth-sensitive calls such as the first `devtask get`, prefer a short
    initial command timeout around 15-30 seconds. If that call times out before
    producing a structured auth response, tell the user it is likely blocked in
    login bootstrap and retry once with a modestly longer timeout only when needed.
12. Before init, run `devtask get` for the chosen unique name and require it to
    be missing. If it exists, choose another name. After init, read back a new,
    not-yet-executed devtask ID. This fresh-task gate replaces any historical
    version-ID baseline.
13. Use `devtask update` only to assemble material scope before the fresh
    devtask's first execute. Never update and re-execute a completed devtask for
    a later code revision.
14. Treat default `materials` as a CLI-owned concern. If the user does not provide
    `materials`, let the CLI resolve them; if default resolution or later
    validation fails, ask the user to provide `materials` manually.
15. Do not silently create missing materials during publish-like flows. If a
    material is missing, stop and ask whether to run `material create` first.
16. After every successful `devtask execute`, read the version IDs produced by
    that fresh task, then wait 1 minute, run `devtask status`, and report that
    snapshot. Continue monitoring only when the user requested a terminal
    outcome.
17. A production release must use each batch's exact new `--version-id`; after
    mark-release, read back `releaseVersionID` and require equality.

## Commands

```bash
# Config
bytedcli oxygen config get
bytedcli oxygen config set --product-key <key>

# Material
bytedcli oxygen material create --product-key <key> --material-name <uniqueId>

# Devtask
bytedcli oxygen devtask init --product-key <key> --env <env> --devtask-name <unique-name>
bytedcli oxygen devtask get --product-key <key> --devtask-name <unique-name>
bytedcli oxygen devtask update --product-key <key> --devtask-name <unique-name> --materials <uniqueIds>
bytedcli oxygen devtask execute --product-key <key> --devtask-name <unique-name>
bytedcli oxygen devtask status --product-key <key> --devtask-name <unique-name>
bytedcli oxygen devtask materials --product-key <key> --devtask-name <unique-name>
bytedcli oxygen material mark-release --product-key <key> --material-name <enName> --version-id <new-id>
```

## Reference Guide

- Read `references/workflow.md` when choosing between `material create`,
  `devtask init`, `devtask get`, `devtask update`, `devtask execute`,
  `devtask status`, or `devtask materials`.
- Read `references/materials-input.md` when `materials` is omitted, when default
  uniqueId resolution matters, or when the user must manually provide `materials`
  after CLI default resolution fails.
- Read `references/status-output.md` when replying after `devtask execute`,
  formatting `devtask status`, or applying the delayed-check requirement.
- Read `../../troubleshooting.md` for common errors and how to handle them.
- Read `../../invocation.md` for the generic `bytedcli` invocation prefix and
  site switching (examples below write `bytedcli` directly).

## Hard Rules

- Never read `.oxygen.local.json` directly in the skill.
- skipTTP vs prod: a prod (`envType: online`) publish built with
  `skipTTPBuild: true` cannot be activated as the online release version. To skip
  TTP, publish to PPE only; a prod publish must run the full TTP build. The CLI
  enforces this — `devtask execute`/`publish` force `skipTTPBuild: false` for prod
  (PPE stays skip by default). ROW pulls the latest PPE+skipTTP deploy fine.
- Never silently create missing materials during publish-like flows.
- Never execute an already executed/completed devtask for a new code revision.
- Never claim a new build from a devtask that was not proven fresh before init.
  Once the fresh-task gate passes, no historical version-ID baseline is needed.
- Never omit `--version-id` when marking a production release.
- Never skip the single delayed `devtask status` after `devtask execute`.
- Render user-facing `devtask status` responses with the required status format
  whenever `data.summary` exists.
- Keep tokens runtime-only and keep the aggregate flow as the only supported
  execution path.

## Common Mistakes

- Treating `.oxygen.local.json` as skill-readable workflow state.
- Defaulting to a long first-call timeout that hides auth bootstrap failures as
  generic hangs.
- Treating `发布物料 <name>` as if `<name>` were a `devtaskName`.
- Letting the deterministic default devtask name resolve to a historical task.
- Treating `Stage=Published` on a reused or unverified devtask as proof that
  the current code produced a version.
- Releasing implicit latest instead of the exact version IDs produced by the
  fresh devtask.
- Updating or executing an old devtask instead of creating a fresh batch.
- Dumping raw command JSON or ad-hoc status formatting when the status-output
  reference already defines the response contract.
