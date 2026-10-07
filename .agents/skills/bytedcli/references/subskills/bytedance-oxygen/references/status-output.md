# Status Output Reference

This reference defines how the **agent** should present devtask status to the
user, built from the `data.summary` JSON (use `-j`). The CLI's own stdout text
mode prints plain `key: value` lines; agents should consume the JSON summary and
render the format below rather than parsing the text output.

## When Status Is Checked

- After every successful `devtask execute`, the CLI waits 1 minute then runs
  exactly **one** `check_devtask_status`.
- `devtask publish` includes the same delayed check as its final step.
- `devtask status` runs the check on demand.

Report the single snapshot by default. If the user explicitly requested waiting
for a terminal build or release, use bounded follow-up checks and stop on
terminal success or failure; do not repeatedly narrate unchanged snapshots.

## Version Identity Gate

Status is valid evidence only after the devtask name was proven absent before
init and the new task ID was read back before its first execute. Once this
fresh-task gate passes, no historical version-ID comparison is needed. After
`Stage=Published`, read the version IDs produced by that task, use those exact
IDs for production release, and read back each material's `releaseVersionID`.

## Status Format (agent response)

When `data.summary` exists, render the agent's user-facing reply in this format:

```
## Material Publish Status

**Devtask:** `<devtaskName>`
**ID:** `<devtaskId>` (or `-` if empty)
**Status:** `<pollState>`
**Unstable:** `<unstable>`

**Materials**

- **Material:** `<enName>`
  **Status:** `<statusLabel>`
  **Stage:** `<stageName>`
  **Reason:** `<compileFailReason>`

**Console**
`<consoleUrl>`
```

### Field Descriptions

| Field              | Source                          | Description                                                        |
| ------------------ | ------------------------------- | ------------------------------------------------------------------ |
| `devtaskName`      | `summary.devtaskName`           | The devtask name (resolved or explicit).                           |
| `devtaskId`        | `summary.devtaskId`             | The devtask ID; shown as `-` if empty.                             |
| `pollState`        | `summary.pollState`             | High-level state: `success`, `failure`, or `in_progress`.          |
| `unstable`         | `summary.unstable`              | `true` if any material is in a transitional or failed state.       |
| `enName`           | `row.enName`                    | Material uniqueId.                                                 |
| `statusLabel`      | `row.statusLabel`               | Human-readable status label for the material.                      |
| `stageName`        | `row.stageName`                 | Component publish stage name (see table below).                    |
| `compileFailReason`| `row.compileFailReason`         | Failure reason (empty if the material compiled successfully).      |
| `consoleUrl`       | `summary.consoleUrl`            | Oxygen console URL for the devtask.                                |

### Component Stage Names

The `stageName` is derived from the numeric `Stage` value returned by the
Oxygen backend:

| Stage | Name              |
| ----- | ----------------- |
| 0     | PrePublish        |
| 1     | Compiling         |
| 2     | Checking          |
| 3     | Cancel            |
| 4     | WaitApproval      |
| 5     | Published         |
| 7     | CompileFail       |
| 8     | CheckFail         |
| 9     | PublishFail       |
| 10    | PrePublishFail    |
| 11    | TTPCompiling      |
| 12    | TTPCompileFail    |
| 13    | CompileConfirm    |
| 14    | WaitingCodeSync   |

Stages 6, 15+ are not currently used by the backend.

### Poll State Classification

The `pollState` is derived from all material rows:

- **`success`** — all materials reached a terminal success stage (Published).
- **`failure`** — any material reached a terminal failure stage (CompileFail,
  CheckFail, PublishFail, PrePublishFail, TTPCompileFail, Cancel).
- **`in_progress`** — any material is still in a transitional stage
  (PrePublish, Compiling, Checking, WaitApproval, TTPCompiling,
  CompileConfirm, WaitingCodeSync).

The `unstable` flag is `true` when `pollState` is `failure` or `in_progress`.

## JSON Mode

In `--json` mode, the raw `check_devtask_status` result is returned:

```json
{
  "ok": true,
  "summary": {
    "pollState": "success",
    "unstable": false,
    "devtaskId": "12345",
    "devtaskName": "oxy-materials-demo-main-a1b2c3d4",
    "rows": [
      {
        "enName": "@demo/material-a",
        "statusLabel": "Published",
        "stageName": "Published",
        "compileFailReason": ""
      }
    ],
    "failedRows": [],
    "consoleUrl": "https://oxygen.tiktok-row.net/..."
  }
}
```

## Retry Behavior

`check_devtask_status` has an internal retry (up to 3 extra attempts) for
transient HTTP, parse, or request errors. This is transparent to the user —
only the final result is reported.
