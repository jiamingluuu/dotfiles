# Errors

- `LOGIFIER_INPUT_ERROR`: The batch ID, device ID, business line, time window, DSL, page index, limit, or API base URL is invalid. Follow the error hint. The base URL must be an HTTPS Logifier endpoint.
- `LOGIFIER_AUTH_REQUIRED`: The current CN user login was rejected. Run `bytedcli --site cn auth login`, then retry the same command.
- `LOGIFIER_API_ERROR`: Logifier returned an explicit failure envelope. Check batch permission and retain the request ID; do not retry by changing or exposing credentials.
- `LOGIFIER_RESPONSE_INVALID`: The response did not match the batch/query contract. Upgrade bytedcli and retry; if it persists, report the request ID without copying log contents or credentials.
- `LOGIFIER_RETRIEVAL_FAILED`: The retrieval task ended unsuccessfully. Inspect its task status in Logifier before starting another retrieval.
- `LOGIFIER_RETRIEVAL_TIMEOUT`: The task is still pending when the wait deadline elapsed. Continue later with `bytedcli logifier retrieval wait --task-id <id>`.
- `LOGIFIER_BATCH_NOT_READY`: A newly finished retrieval batch is still being indexed. Wait briefly, then rerun `bytedcli logifier batch query --batch-id <id>`.
