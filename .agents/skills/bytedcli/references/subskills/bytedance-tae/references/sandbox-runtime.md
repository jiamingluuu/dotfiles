# Sandbox sessions and runtime

`bytedcli tae sandbox` natively implements controlplane and sandboxd operations. No external taecli installation is required. `sandbox list/search/get` continue to query platform resources; `sandbox session ...` operates runtime sessions.

## Authentication and routing

Use bytedcli ByteCloud authentication. Runtime commands default to `--region cn`; region determines the credential partition, independently of the platform resource `--site` option. Use `--auth-site` only to override the credential partition for a custom route. `--region i18n` and `i18n_office` use `i18n-tt`; `i18n_bd`, `i18n_bd_volc`, and `asia_cis` use `i18n-bd`; BOE endpoints use `boe`; TTP endpoints use `us-ttp` or `eu-ttp`.

`region list` lists the built-in mappings. Supported regions: `sandbox`, `boe`, `cn`, `i18n`, `boe_i18n`, `usttp`, `euttp`, `local`, `cn_north`, `cn_east`, `i18n_office`, `chinasinf_north`, `boesinf_north`, `i18n_bd`, `i18n_bd_volc`, `asia_cis`, `boe_sandbox`, `china_north6`. `i18n_office` uses its production endpoint when `BYTEDCLI_NETWORK_PROFILE=prod`; use this instead of taecli's `i18n_prod` region.

Controlplane operations require `--psm` or `--sandbox-id`. Providing the ID skips PSM discovery; `resolve --sandbox-id` returns the supplied identity without fetching metadata. Sandboxd operations need only `--session-id`.

Use `--control-plane-url` or `--sandboxd-url` for custom endpoints; the latter supports `{session_id}` substitution. The `local` region skips automatic authentication. Explicit ZTI authentication uses `BYTEDCLI_TAE_ZTI_TOKEN` (or `--zti-token`). JWT overrides use the existing bytedcli authentication facilities, including `--bytecloud-user-jwt-file`. Do not place credentials in examples or prompts. `TAECLI_*` variables and taecli's separate login storage are not read.

## Region mismatch

If the API returns `InvalidParameter.RegionMismatch`, use the region named in the error instead of retrying the default endpoint. For example, a sandbox deployed in `cn-east` requires `--region cn_east` on both controlplane and sandboxd commands. Check `bytedcli tae sandbox region list` for supported CLI names.

## Commands

```bash
bytedcli auth login --site cn
bytedcli tae sandbox region list
bytedcli tae sandbox resolve --psm example.sandbox
bytedcli tae sandbox session create --psm example.sandbox --ttl 3600 --env DEMO=true --metadata TASK=demo
bytedcli tae sandbox session list --psm example.sandbox --page 1 --page-size 20 --ids-only
bytedcli tae sandbox session get --psm example.sandbox --session-id demo-session --query-usage
bytedcli tae sandbox session update --psm example.sandbox --session-id demo-session --ttl 7200
bytedcli tae sandbox session search --psm example.sandbox --body '{"metadata":{"TASK":"demo"}}'
bytedcli tae sandbox session list --archived --psm example.sandbox --body @history.json
bytedcli tae sandbox bash --session-id demo-session --command 'pwd'
bytedcli --http-timeout-ms 300000 tae sandbox bash --session-id demo-session --timeout-ms 60000 --command 'echo demo' --stream
bytedcli tae sandbox exec --session-id demo-session
bytedcli tae sandbox process start --session-id demo-session --executable /bin/echo --arg demo
bytedcli tae sandbox process list --session-id demo-session
bytedcli tae sandbox process connect --session-id demo-session --pid 123
bytedcli tae sandbox process stdin --session-id demo-session --pid 123 --data $'demo\n'
bytedcli tae sandbox process signal --session-id demo-session --pid 123 --signal SIGTERM
bytedcli tae sandbox port expose --session-id demo-session --port 8080
bytedcli tae sandbox port list --session-id demo-session --no-debug-port-set
bytedcli tae sandbox port unexpose --session-id demo-session --port 8080
bytedcli tae sandbox fs stat --session-id demo-session --path /workspace/demo.txt
bytedcli tae sandbox fs list --session-id demo-session --path /workspace --depth 2
bytedcli tae sandbox fs mkdir --session-id demo-session --path /workspace/demo
bytedcli tae sandbox fs upload --session-id demo-session --file ./input.json --destination /workspace/input.json
bytedcli tae sandbox fs download --session-id demo-session --path /workspace/result.bin --output ./result.bin
bytedcli tae sandbox fs move --session-id demo-session --source /workspace/input.json --destination /workspace/demo/input.json
bytedcli tae sandbox fs remove --session-id demo-session --path /workspace/demo/input.json
bytedcli tae sandbox request --target controlplane --psm example.sandbox --method POST --path sessions/search --body '{}'
bytedcli tae sandbox request --target sandboxd --session-id demo-session --method POST --path /api/process/list
bytedcli tae sandbox session delete --psm example.sandbox --session-id demo-session
bytedcli tae sandbox session batch-delete --psm example.sandbox --session-ids demo-session-a demo-session-b
```

`session create --body JSON|@file` accepts a base object with forward-compatible fields. Explicit options override matching fields. Repeated `--env` and `--metadata` replace their respective maps; `--expose-port` and `--debug-port` replace their respective port arrays. Supported creation options also include `--image`, `--cpu-milli`, `--memory-mb`, `--command`, `--prestop-command`, `--revision-id`, `--resumable` / `--no-resumable`, and repeatable `--tos-mount`, `--fuse-mount`, `--patch-mount` JSON objects or files. Omitting both resumable flags preserves the body value; `--resumable` sets true and `--no-resumable` sets false. Mount objects use the SDK wire fields; credentials inside mount files must be treated as secrets.

`session list` supports `--order-create`, `--order-expire`, `--order-scheduled-eviction` (`asc` or `desc`), `--query-usage`, `--is-evicting`, `--pre-eviction-reason`, and `--has-scheduled-eviction`. JSON returns `items`, `page`, `page_size`, `current_count`, and `has_more`. For active `session list`, `total` is `null`; a full page returns `has_more: null` (unknown), and a shorter page returns `false`. `--ids-only` applies only to active sessions and projects JSON items to `{session_id}` objects and prints one ID per line in text mode. `session list --body` requires `--archived`. `session search` and `session list --archived` accept complete query objects through `--body`; explicit `--page` / `--page-size` override body pagination, with defaults of 1 / 20 when neither is supplied. Their JSON output includes `total` and computes `has_more` from that total. Archived items preserve the history record and its termination/archive details.

`bash` and `process start` support `--cwd`, repeated `--env`/`--unset-env`, `--target-user`, `--target-group`, `--stdin`, `--close-stdin`, and `--stream`. `process signal --signal` accepts POSIX names such as `SIGTERM` / `SIGKILL` and numeric signals. Port commands use `--debug-port-set` / `--no-debug-port-set` without a value to select debug / normal ports. All fs operations support `--target-user` and `--target-group`. Upload without `--destination` uses each local file's basename; with `--destination`, exactly one file is required. Uploads are buffered in memory; downloads stream to the destination.

Raw `request` supports repeated `--query KEY=VALUE`, `--header NAME=VALUE`, arbitrary JSON via `--body`, and binary `--output`. Controlplane `/api/` paths are used within the configured host; other paths are relative to `/api/v1/sandboxes/{sandbox_id}/`. Sandboxd paths are relative to the session gateway. Absolute URLs are rejected; choose the endpoint using the URL override options.

## Output and execution

- Ordinary commands default to text; `--json` uses the bytedcli result envelope.
- Bash text mode forwards stdout/stderr unchanged and uses the remote exit code. JSON mode returns the process result and preserves that exit code.
- Streaming process commands emit NDJSON in JSON mode. If a stream closes before a final process result, the command fails; inspect `process list` before retrying.
- `exec` requires interactive stdin/stdout TTYs and rejects JSON. It opens a new Bash PTY, forwards resize and control keys, and restores the local terminal on exit or failure.
- `--http-timeout-ms` is the shared transport deadline, including response consumption. Process `--timeout-ms` controls remote execution and the sandbox gateway call timeout. An explicit `--header x-sandbox-call-timeout-ms=...` overrides the gateway timeout. The HTTP timeout remains independent; set a larger `--http-timeout-ms` for long commands.
- Binary `--output -` writes raw bytes and rejects JSON. File output reports the destination after successful completion.
- Writes execute directly, including session deletion and file removal. Non-idempotent operations are not automatically replayed. After an ambiguous transport failure, inspect state before repeating a write.
- These commands cover controlplane/sandboxd, not AIO, browser, code interpreter, or legacy bash-server APIs.

## taecli migration and parity

The native protocol baseline is taecli 1.1.0. Positional inputs become explicit options.

| taecli | bytedcli tae sandbox | Contract |
| --- | --- | --- |
| `auth ...` | `bytedcli auth ...` | Unified credentials and login |
| `sandbox get` | `resolve --psm ...` | Same PSM discovery/ID bypass |
| `ls` | `session list --ids-only` | IDs with pagination context |
| `session create/get/update/delete/list/search/batch-delete`, `session history` | Session actions with options; history becomes `session list --archived` | Same lifecycle paths and payload fields |
| `bash <session> -- <command>` | `bash --session-id ... --command ...` | Same process/start request and exit semantics |
| `exec <session>` | `exec --session-id ...` | Same shell WebSocket protocol |
| `process ...` | `process ... --session-id ...` | Same start/connect/signal/stdin APIs |
| `port ... --debug` | `port ... --debug-port-set` | Same debug-port wire field |
| `fs ...` | `fs ... --session-id ... --path ...` | Same filesystem API and identity fields |
| `request ...` | `request --target ... --method ... --path ...` | Raw paths, query, body and downloads |
| `regions` | `region list` | Regional routes with bytedcli network profile |
