# ByteFlow Classic API Reference

This reference is based on read-only console inspection, frontend bundle analysis, and live read-only API checks on 2026-05-26 and 2026-06-03.

## Console URLs

| Site | URL |
| --- | --- |
| CN | `https://cloud.bytedance.net/byteflow` |
| BOE | `https://cloud-boe.bytedance.net/byteflow` |
| I18N | `https://cloud-i18n.bytedance.net/byteflow` |
| I18N-TT / ROW console | `https://cloud.tiktok-row.net/byteflow` |
| EU | `https://cloud-eu.tiktok-row.net/byteflow` |
| US-TTP | `https://cloud.tiktok-usts.net/byteflow` |

## API Base

Classic ByteFlow CN:

```text
https://cloud.bytedance.net/api/v1/byteflow/api/v1
```

TikTok ROW ByteFlow console is `https://cloud.tiktok-row.net/byteflow`, but the API base is `https://bc-sg-gw.tiktok-row.net/api/v1/byteflow/api/v1`.
Use helper site `--site i18n-tt` for that console; `row` and `tiktok-row` are accepted aliases.

Observed frontend bundle:

```text
https://lf-goofy-east.bytegoofy.com/obj/goofy-tjdt/gftar/toutiao/cloud/byteflow/1.0.0.829/resource/cloud_garr/byteflow/byteflow.js
```

## Auth

App APIs:

```text
x-jwt-token: <bytecloud jwt>
```

App-scoped statemachine/revision/execution/activity/DAG APIs:

```text
x-jwt-token: <bytecloud jwt>
Authorization: Bearer <app token>
Bf-Cluster: default
```

Get app token:

```http
GET /apps/{appName}
```

Do not print app token. Redact `token`, `sa_secret`, `Authorization`, cookies, and secrets from output.

## Verified Read Endpoints

List apps:

```http
GET /apps?page_no=1&page_size=20&subscribed_only=true&name=
```

Get app:

```http
GET /apps/{appName}
```

List statemachines for the token's app:

```http
GET /statemachines?page_no=1&page_size=20
```

Get statemachine:

```http
GET /statemachines/{stateMachineId}
```

List revisions:

```http
GET /statemachines/{stateMachineId}/revisions?page_no=1&page_size=10
```

List executions for an app:

```http
GET /executions?page_no=1&page_size=20
```

List executions for a statemachine:

```http
GET /statemachines/{stateMachineId}/executions?page_no=1&page_size=20
```

Get execution detail:

```http
GET /executions/{executionId}
```

List execution events:

```http
GET /executions/{executionId}/events?page_no=1&page_size=9999
```

To answer "which node is this flow currently running", fetch both execution detail and events. Pair `*StateEntered` events with later `*StateExited` / `*StateFailed` events of the same `state_name`; remaining entered states are the current active states. Parallel workflows can have multiple active states.

List express executions:

```http
GET /express?page_no=1&page_size=20
```

List express execution events:

```http
GET /express/{executionId}/events?page_no=1&page_size=9999
```

List activities:

```http
GET /activities?page_no=1&page_size=20&name={activityName}
```

Get activity:

```http
GET /activities/{activityName}?name={activityName}
```

List DAG definitions:

```http
GET /dags?page_no=1&page_size=20&name={dagName}
```

Get DAG definition:

```http
GET /dags/{dagId}
```

List DAG executions:

```http
GET /dagexecutions?page_no=1&page_size=20
```

Get DAG execution:

```http
GET /dagexecutions/{dagExecutionId}
```

List DAG execution events:

```http
GET /dagexecutions/{dagExecutionId}/events?page_no=1&page_size=9999
```

DAG responses can include large `definition` payloads and embedded business parameters. Helper output omits large definition fields by default and only prints them when `--include-definition` is passed.

## Write Endpoints Observed From Frontend Bundle

These endpoints were discovered from frontend code. Live verification should use helper `--dry-run`; do not execute a write request without human confirmation.

All helper write commands require a per-operation confirmation phrase:

1. Run the command with `--dry-run`.
2. Show the target app/object, endpoint, payload summary, and online-risk note to the user.
3. Execute only after the user confirms that exact operation.
4. Pass both `--yes` and the dry-run `required_confirm_write` value as `--confirm-write`.

Do not reuse confirmation phrases across operations.
For helper commands that take `--payload-file`, the dry-run output includes a short SHA-256 digest as `payload_sha256`, and the `required_confirm_write` phrase includes that digest.
For workflow definition writes (`statemachine-create` and `statemachine-update`), the dry-run output includes `workflow_sha256`, and the `required_confirm_write` phrase includes that digest.

Subscribe or unsubscribe from an app:

```http
POST /apps/{appName}/subscribe
POST /apps/{appName}/unsubscribe
```

Create statemachine:

```http
POST /statemachines
Content-Type: application/json

{
  "name": "...",
  "type": "standard",
  "sa_secret": "...",
  "definition_str": "{...workflow JSON string...}"
}
```

Update statemachine definition:

```http
PUT /statemachines/{stateMachineId}
Content-Type: application/json

{
  "name": "...",
  "type": "standard",
  "sa_secret": "...",
  "definition_str": "{...workflow JSON string...}"
}
```

The helper uses a read-merge-write shape for update: first `GET /statemachines/{id}`, preserve current `name`, `type`, and `sa_secret` when present, replace only `definition_str`, then dry-run or `PUT`.

Delete statemachine:

```http
DELETE /statemachines/{stateMachineId}
```

Create revision snapshot:

```http
POST /statemachines/{stateMachineId}/revisions
Content-Type: application/json

{
  "revision_name": "...",
  "description": "..."
}
```

Keep `revision_name` short. A 33-character name was rejected by the server's max-length validation during MVP testing; the helper uses a conservative 30-character local guard.

Before updating a statemachine or creating a revision, query:

```http
GET /statemachines/{stateMachineId}/revisions?page_no=1&page_size=1
```

If the online revision count is 0, stop and require explicit user consent. The message should clearly state that updating the definition or creating the first revision may introduce online risk or change how production executions/releases resolve the workflow. The helper enforces this with `--allow-first-revision-risk`.

Delete revision:

```http
DELETE /statemachines/{stateMachineId}/revisions?revision_number={number}
```

Start a standard execution:

```http
POST /executions
Content-Type: application/json

{...payload from --payload-file...}
```

Execution retry, stop, and delete:

```http
POST /executions/{executionId}/retry
POST /executions/{executionId}/stop
DELETE /executions/{executionId}
```

The helper reads execution detail before status-sensitive writes. `execution-retry` expects `Failed` or `Cancelled`; `execution-stop` expects `Running`; `execution-delete` expects a terminal state. If status does not match, live execution is blocked unless the user explicitly accepts the risk and reruns with `--allow-status-risk`.

Start an express execution:

```http
POST /express
Content-Type: application/json

{...payload from --payload-file...}
```

Create, update, or delete an activity:

```http
POST /activities/{activityName}
PUT /activities/{activityName}
DELETE /activities/{activityName}
```

Create and update use the JSON body from `--payload-file`.

Create, update, or delete a DAG:

```http
POST /dags
PUT /dags/{dagId}
DELETE /dags/{dagId}
```

Create and update use the JSON body from `--payload-file`. DAG payloads may include secrets or large definitions; helper output redacts sensitive keys and omits large definitions unless `--include-definition` is passed.

Start or stop a DAG execution:

```http
POST /dagexecutions
POST /dagexecutions/{dagExecutionId}/stop
```

`dag-execution-start` uses the JSON body from `--payload-file`. `dag-execution-stop` reads current detail first and expects `Running`; mismatches require explicit user consent plus `--allow-status-risk`.

## Confirmed Read Example

Read-only validation succeeded for:

- App: `example_app`
- StateMachine ID: `12345`
- StateMachine name: `demo_state_machine`
- Type: `standard`
- Latest revision: `3`
- Revision list row count: `3`
