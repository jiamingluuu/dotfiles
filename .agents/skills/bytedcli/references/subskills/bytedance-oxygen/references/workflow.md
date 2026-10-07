# Oxygen Workflow Reference

This reference maps Oxygen material publish workflows to `bytedcli oxygen`
commands. All workflows target the single aggregate endpoint at
`oxygen.tiktok-row.net/oxyapi/materials/aggregate`.

## Command-to-Action Mapping

| Command                              | Aggregate action         |
| ------------------------------------ | ------------------------ |
| `oxygen material create`             | `create_material`        |
| `oxygen devtask init`                | `init_devtask`           |
| `oxygen devtask get`                 | `get_devtask`            |
| `oxygen devtask update`              | `update_devtask`         |
| `oxygen devtask execute`             | `execute_devtask`        |
| `oxygen devtask status`              | `check_devtask_status`   |
| `oxygen devtask materials`           | `list_devtask_materials` |
| `oxygen devtask publish`             | init/update + execute + status |

## Product Identity Resolution

1. `--product-key` / `--product-id` passed on the command line take precedence.
2. If neither is passed, the CLI reads `.oxygen.json` for `productKey` /
   `productID`.
3. If still unresolved, the command fails with a hint to set one.

Keep `.oxygen.json` minimal:

```json
{ "productKey": "demo-product" }
```

`.oxygen.local.json` is a local runtime override (only `oxygen_env` is honored);
it is not read for skill workflow decisions.

## Env Mapping

The CLI `--env` value is normalized into the Oxygen `envType` + `effectedEnv`
format:

| CLI `--env`   | `envType`   | `effectedEnv`     |
| ------------- | ----------- | ----------------- |
| `prod`        | `online`    | `["prod"]`        |
| `ppe_test1`   | `test`      | `["ppe_test1"]`   |
| `ppe_<name>`  | `test`      | `["ppe_<name>"]`  |

`prod` is the only non-PPE value. Any other value must start with `ppe_`.

## Devtask Name Resolution

- If `--devtask-name` is passed, it is used directly (conversation-only; never
  written to `.oxygen.local.json`).
- Otherwise the CLI generates a deterministic name:
  `oxy-materials-<repo>-<branch>-<sha1>`, where `sha1` is derived from the repo
  remote URL, current branch, first commit, target branch, and productKey.

The generated name can remain stable across later commits on the same branch.
That makes it unsuitable as the identity of repeated production code releases.

## Version Identity Invariant

- A devtask is one material-version batch, not a reusable release channel.
- Re-executing an already executed/completed devtask can rebuild its previously
  bound versions without creating new version IDs.
- For every new code release, pass a unique `--devtask-name`, confirm it does
  not resolve to a historical devtask, and initialize a fresh devtask.
- Before init, query the chosen unique devtask name and require it to be absent.
  After init, read back a new, not-yet-executed devtask ID. If the name already
  exists, choose another one. No historical material-version baseline is needed
  once this fresh-task gate passes.
- Release only with the exact new `--version-id`; never rely on the implicit
  latest version in a production workflow.
- On a devtask that passed the fresh-task gate, `Stage=Published` proves that
  this release batch built successfully. Never apply that conclusion to a
  reused or unverified devtask.

## Workflow: Create a Material

```bash
bytedcli oxygen material create --product-key demo-product --material-name @demo/material
```

- Always requires explicit user confirmation before creation.
- `--material-name` must be a uniqueId starting with `@`.
- Optional `--scm-name` is passed through as `extra.scmBasicInfo.scmName`.

## Workflow: Publish to a Fresh Devtask (PPE)

```bash
bytedcli oxygen devtask publish \
  --product-key demo-product \
  --env ppe_test1 \
  --devtask-name oxy-materials-demo-20260903-a1b2c3
```

This runs the full aggregate workflow:

1. Choose a unique devtask name for this release batch.
2. `get_devtask` — the unique name must be missing; if it exists, choose
   another name.
3. `init_devtask` with env, materials (auto-resolved if omitted),
   and git branch.
4. `execute_devtask` — trigger this fresh batch.
5. Read and capture the version IDs produced by this fresh devtask.
6. Check status for the fresh devtask and report the snapshot.

If step 2 finds an executed/completed devtask, choose a new name instead of
continuing. `publish` does not itself guarantee creation of a new version when
it resolves an existing task.

Write commands default to a dry-run preview; pass `--yes` to submit. PPE-targeted
writes may pass `--yes` directly.

## Workflow: Publish to Prod

```bash
# 1. preview (dry-run)
bytedcli oxygen devtask publish \
  --product-key demo-product \
  --env prod \
  --devtask-name oxy-materials-demo-20260903-a1b2c3
# 2. after the user confirms the preview, submit
bytedcli oxygen devtask publish \
  --product-key demo-product \
  --env prod \
  --devtask-name oxy-materials-demo-20260903-a1b2c3 \
  --yes
```

Same flow as PPE, but for prod always show the dry-run preview and get explicit
user confirmation before re-running with `--yes`. Prod also forces the full TTP
build (`skipTTPBuild: false`) so the version can be activated.

## Workflow: Publish a Specific Material

When the user says "发布物料 @demo/material" (publish material @demo/material):

1. Create a fresh, uniquely named devtask for this release batch.
2. Add `@demo/material` during init. Multiple materials in the same batch may
   be assembled with `update_devtask` only before the first execute.
3. Execute the fresh devtask.
4. Read and capture the material version ID produced by this fresh devtask.
5. Check the fresh devtask status.

Do not add a new code revision to an already executed devtask. Create another
devtask instead.

Do not silently create a missing material. If the material does not exist, stop
and ask whether to run `material create` first.

## Workflow: Granular Control

Use individual subcommands instead of `publish` when you need step-by-step
control:

```bash
# Initialize a uniquely named fresh devtask
bytedcli oxygen devtask init \
  --product-key demo-product \
  --env ppe_test1 \
  --devtask-name oxy-materials-demo-20260903-a1b2c3

# Check current state
bytedcli oxygen devtask get \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3
bytedcli oxygen devtask materials \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3

# Update scope only before this devtask's first execute
bytedcli oxygen devtask update \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3 \
  --materials @demo/material-a,@demo/material-b

# Execute
bytedcli oxygen devtask execute \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3

# Status (after execute, the CLI runs this once automatically)
bytedcli oxygen devtask status \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3
```

## Auth-Sensitive Calls

The first `devtask get` in a flow may block on login bootstrap. Use a short
initial timeout (15-30 seconds). If it times out before producing a structured
auth response, tell the user it is likely blocked in login bootstrap and retry
once with a modestly longer timeout.

## PPE Environment Headers

When `--oxygen-env <env>` is set (or read from `.oxygen.local.json`), the CLI
sends `x-use-ppe: 1` and `x-tt-env: <oxygenEnv>` headers.
