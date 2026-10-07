# ByteFlow Workflow Syntax

ByteFlow workflow definitions are ASL-compatible JSON documents.

## Top-Level Shape

Required:

```json
{
  "StartAt": "FirstState",
  "States": {}
}
```

Optional fields seen in docs:

- `Comment`
- `TimeoutSeconds`
- `Version`
- `ContextMergeStrategy`

## State Types

| Type | Purpose | Common fields |
| --- | --- | --- |
| `Task` | Invoke a resource/action | `Resource`, `Parameters`, `Retry`, `Catch`, `TimeoutSeconds`, `OutputPath`, `Next`, `End` |
| `Choice` | Branch based on input | `Choices`, `Default` |
| `Succeed` | Successful terminal state | `Type` |
| `Fail` | Failed terminal state | `Cause`, `Error` |
| `Pass` | Pass-through or transform | `Parameters`, `Result`, `ResultPath`, `Next`, `End` |
| `Wait` | Delay | `Seconds`, `Timestamp`, `SecondsPath`, `TimestampPath`, `Next` |
| `Parallel` | Run branches in parallel | `Branches`, `Retry`, `Catch`, `Next`, `End` |
| `Map` | Iterate over items | `ItemsPath`, `Iterator`, `MaxConcurrency`, `Next`, `End` |

## Task Resource BRN

Start latest revision:

```text
brn:byteflow:::{AppName}/stateMachine/{StateMachineName}:startExecution.{action-mode}
```

Start a specific revision:

```text
brn:byteflow:::{AppName}/stateMachine/{StateMachineName}/{RevisionNumber}:startExecution.{action-mode}
```

Known action modes:

- `requestResponse`
- `sync`

## Standard vs Express

Standard:

- Persistent, auditable, recoverable.
- Better for long-running workflows and business processes.
- Exactly-once oriented semantics.

Express:

- Short-running, high-throughput.
- At-least-once oriented semantics.
- Tasks should be idempotent.

## Local Validation Checklist

Before proposing an update, run:

```bash
bytedcli byteflow workflow validate --file workflow.json
```

The fixed checks are:

1. `WF001_JSON_OBJECT`: JSON parses and the workflow root is an object.
2. `WF002_REQUIRED_TOP_LEVEL`: `StartAt` is a non-empty string and `States` is a non-empty object.
3. `WF003_STARTAT_TARGET`: `StartAt` names an existing state.
4. `WF004_STATE_OBJECT_AND_TYPE`: every state is an object with a supported `Type`.
5. `WF005_TRANSITION_TARGETS`: `Next`, `Default`, `Choices[].Next`, and `Catch[].Next` targets exist.
6. `WF006_TERMINATION`: non-terminal states use `Next` or `End: true`; `Choice` and terminal states follow their own semantics.
7. `WF007_CHOICE_SHAPE`: `Choice` states define `Choices` or `Default`, and choice branches have `Next` plus condition-like fields.
8. `WF008_TASK_RESOURCE`: `Task.Resource` is a non-empty string; unknown BRN shapes are warnings.
9. `WF009_WAIT_SHAPE`: `Wait` states define exactly one of `Seconds`, `Timestamp`, `SecondsPath`, or `TimestampPath`.
10. `WF010_RETRY_CATCH_SHAPE`: `Retry` and `Catch` are arrays when present; catchers define `Next`.
11. `WF011_PARALLEL_SHAPE`: `Parallel.Branches` is a non-empty array, and nested branch workflows pass validation.
12. `WF012_MAP_SHAPE`: `Map.Iterator` or `Map.ItemProcessor` is a nested workflow object and passes validation.
13. `WF013_REACHABILITY`: states are reachable from `StartAt`.
14. `WF014_TERMINAL_REACHABILITY`: at least one terminal state is reachable from `StartAt`.

If the script is unavailable, manually check the same `WFxxx` items and say that validation was manual.

## Common Mistakes

- Creating a revision without first updating the statemachine definition. In classic ByteFlow, revision create snapshots the current definition.
- Treating Express workflows as exactly-once. Design task actions to be idempotent.
- Printing app tokens or `sa_secret` fields when debugging API responses.
- Touching an existing online workflow before validating JSON locally and getting explicit confirmation.
