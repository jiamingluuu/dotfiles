# CodeVision troubleshooting

## Command or flag is missing

Inspect the runtime help instead of guessing names:

```bash
bytedcli codevision evidence --help
bytedcli codevision evidence repository search --help
bytedcli codevision evidence graph query --help
bytedcli codevision evidence file multi-get --help
```

Normal requests use visible business flags. `--input-json` and `--input-file` are advanced escape hatches and cannot be combined with those flags.

## Authentication fails

CodeVision uses the current user's ByteCloud JWT:

```bash
bytedcli auth login
bytedcli --json auth status
```

`CODEVISION_USERNAME` is attribution metadata only and cannot fix an expired or missing JWT.

## Request target or input is rejected

- `CODEVISION_AUTH_TARGET_ERROR`: custom endpoints or credential-bearing URLs are not allowed. Remove endpoint, token, header, and `requestOptions` overrides.
- `CODEVISION_INPUT_ERROR`: follow the error's `hint`, use the command's visible flags, and check repeatable limits. Requests accept at most 50 repositories, 20 files, and concurrency from 1 through 8.
- Put global `--json` before `codevision`, for example `bytedcli --json codevision evidence scope get`.

## Graph or ranking results are incomplete

`pending`, `error`, `issues`, and truncation metadata are valid partial-result states. Preserve successful repository results, report unresolved items, then narrow the authorized scope or keywords before retrying. Do not treat Top-K order as proof.

Custom graph SQL must be one read-only `SELECT` or `WITH ... SELECT` statement and must end with a top-level `LIMIT` from 1 through 1000. The unbounded `repository-keyword-evidence` SDK template is not exposed by bytedcli; use `files-by-keyword` for bounded repository file evidence.

## File download returns an error event

`file download` returns one `ready` or `error` event per unique file. A cache validation failure for one file does not discard the other events. Check the event's `file`, `issue.code`, and `issue.message`; retry only the affected file after confirming its repository-relative path and size.

`CODEVISION_CACHE_ERROR` means the SDK path failed the private-cache boundary, symlink, file-type, mode, size, or integrity check. Do not manually trust or consume the rejected path.

## Network or timeout failure

- Confirm internal network access and a valid login.
- Increase the command-local `--timeout-ms` only when the query is expected to be slow.
- Use global `--http-debug`, `--socks5-proxy`, or `--http-proxy` when transport diagnosis is needed; do not add custom CodeVision endpoints.
