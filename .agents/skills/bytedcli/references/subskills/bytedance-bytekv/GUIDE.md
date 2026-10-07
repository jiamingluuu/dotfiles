---
name: bytedance-bytekv
description: "Read ByteKV namespace and table metadata, business auth configuration and one explicit key via bytedcli using a personal CN identity. Use for ByteKV whoami, owned namespaces, namespace PSM configuration, table metadata, and single-key reads."
---

# bytedcli ByteKV

ByteKV is a horizontally scalable, strongly consistent key-value database with distributed transactions.

## Commands

The complete command tree has seven operations. Use `info` for namespace/table metadata, `namespace auth-info` for business auth configuration, and `kv get` for key data. Square brackets below mean optional arguments; replace angle-bracket placeholders with literal values. Business selectors belong after the leaf command.

```text
bytedcli [global-options] bytekv whoami
bytedcli [global-options] bytekv namespace list [--page <n>] [--page-size <n>]
bytedcli [global-options] bytekv namespace info --name <namespace>
bytedcli [global-options] bytekv namespace auth-info --name <namespace> [--check-psm <psm>]
bytedcli [global-options] bytekv table list --namespace <namespace>
bytedcli [global-options] bytekv table info --namespace <namespace> --name <table>
bytedcli [global-options] bytekv kv get --namespace <namespace> --table <table> (--key <key> | --key-hex <hex>)
```

| Command          | Required options                  | Optional business options                                                         | Result                                                                         |
| ---------------- | --------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `whoami`         | None                              | None                                                                              | `name` recognized by ByteKV                                                    |
| `namespace list` | None                              | `--page`: integer 1–21474836, default 1; `--page-size`: integer 1–100, default 20 | `items`, `page`, `page_size`, `has_more`, `next_page`                             |
| `namespace info` | `--name`                          | None                                                                              | Namespace metadata, business description, console and Grafana links, or `null`                                 |
| `namespace auth-info` | `--name` | `--check-psm`: one exact PSM to compare locally | `namespace`, `enabled`, `disableReason`, `psms`, `psmCheck`, `documentationUrl`, `warnings`, or `null` |
| `table list`     | `--namespace`                     | None                                                                              | `items` containing table metadata, `capacityUnit`, `capacityNote`; empty `items` when absent           |
| `table info`     | `--namespace`, `--name`           | None                                                                              | Table metadata with `capacityUnit`, `capacityNote`, or `null`                                           |
| `kv get`         | `--namespace`, `--table`, exactly one of `--key` / `--key-hex` | None                                                                              | `namespace`, `table`, `key`, `keyEncoding`, `value`, `version`, `valueEncoding`, `itemStatus` |

Namespace metadata fields are `name`, `owners`, `cluster`, `deployedDc`, `forTest`, `tables`, `psm`. Only `namespace info` adds `grafanaUrl`, `consoleUrl` and `businessDescription` (null when not supplied). Table metadata fields are `name`, `sensitiveLevel`, `initialCapacity`, `expectedCapacity`.

Common global options:

- `--site cn`: select the supported platform. Specify it if your default site differs.
- `--as user`: explicitly use personal identity. Default `auto` also resolves a personal identity for ByteKV; `app` and `ai_auth` fail.
- `--json` / `-j`: standard `{status, data, error, context}` output; omit for human-readable tables. Global options can precede `bytekv`; `--json` also works after the leaf options.
- `--no-auto-upgrade`: use the current installed or locally built version without automatic upgrade.
- `--help` / `-h`: command help. `bytedcli --help --debug` lists the shared advanced global options; they are not additional ByteKV operations.

All names are exact, case-sensitive strings, with no wildcard or fuzzy matching. A resource name cannot be empty or whitespace-only. Business options accept both `--name value` and `--name=value`; their order after the leaf command does not matter. There are no positional resource arguments, short business flags, or hidden aliases. Supply each scalar option once; the shared parser keeps the last value if repeated, never treating repetition as a batch.

Examples covering the supported option combinations:

```bash
# Identity
bytedcli --site cn --as user bytekv whoami

# Namespace listing: defaults, page only, size only, both
bytedcli bytekv namespace list
bytedcli bytekv namespace list --page 2
bytedcli bytekv namespace list --page-size 100
bytedcli bytekv namespace list --page 1 --page-size 20

# Exact metadata lookup
bytedcli bytekv namespace info --name demo-ns
bytedcli bytekv table list --namespace demo-ns
bytedcli bytekv table info --namespace demo-ns --name demo-table

# Read auth configuration, optionally compare one business PSM
bytedcli bytekv namespace auth-info --name demo-ns
bytedcli bytekv namespace auth-info --name demo-ns --check-psm example.demo.service

# Single literal key; either JSON option placement is supported
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key demo-key --json
bytedcli --json bytekv kv get --key=demo-key --table=demo-table --namespace=demo-ns

# Binary key: bytes 00 ff 41; hex case does not change the bytes
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key-hex 00FF41 --json
bytedcli --json bytekv kv get --key-hex=00ff41 --table=demo-table --namespace=demo-ns

# Shell quoting preserves spaces, literal escapes, Unicode and leading hyphens
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key ' demo key '
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key 'demo\nkey'
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key '示例😀'
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key='--demo-key'

# Bash/zsh: an actual newline is different from the literal backslash-n above
bytedcli bytekv kv get --namespace demo-ns --table demo-table --key $'demo\nkey'
```

Every level supports help without authentication or business requests:

```bash
bytedcli bytekv --help
bytedcli bytekv whoami --help
bytedcli bytekv namespace --help
bytedcli bytekv namespace list --help
bytedcli bytekv namespace info --help
bytedcli bytekv namespace auth-info --help
bytedcli bytekv table --help
bytedcli bytekv table list --help
bytedcli bytekv table info --help
bytedcli bytekv kv --help
bytedcli bytekv kv get --help
bytedcli --json bytekv kv get --help
```

Invoking `bytekv`, `bytekv namespace`, `bytekv table` or `bytekv kv` without a child also prints help and exits successfully. Unknown children, unknown options, extra operands and missing required options fail. Shared `--all-help` provides the complete help tree.

## Semantics

- CN only. Uses the caller's personal ByteCloud login or request-scoped user identity. Application identities and machine-owner credentials are not used. Check `whoami` before a data read; platform permissions remain authoritative.
- `namespace list` includes only namespaces whose owner list contains the current user's exact name, including when that user is an administrator. Fetches one source page, default 20, allowed 1–100. Output has `page`, `page_size`, `has_more`, `next_page` and no global total. A filtered empty page can still have `next_page`; it does not mean the user owns no namespaces.
- `namespace info` uses an exact name and returns platform metadata with `businessDescription`, `consoleUrl` and `grafanaUrl`, or `null` when the namespace is absent. The platform link is requested with the same identity only after the exact namespace metadata is authorized. If the optional link is unavailable, namespace metadata is still returned with `grafanaUrl: null`; text mode prints a notice. Access failures are errors. The CLI does not open the URL or fetch metrics; Grafana access is checked separately when you open the link.
- `namespace auth-info` shows the specified namespace's service-PSM authorization configuration using the caller's existing personal platform identity. It is a read-only lookup, not a login or permission-grant operation. It returns `enabled`, `disableReason` and configured `psms`. Optional `--check-psm` adds `psmCheck: {psm, listed}` using exact, case-sensitive membership; otherwise `psmCheck` is null. The PSM is compared locally, never sent as caller identity. This does not modify authorization, probe the business service or verify its token, connectivity or effective access. A listed PSM does not prove access works; an empty list does not prove access is denied. A missing namespace returns null; permission and upstream failures remain errors.
- Auth results include `documentationUrl`: [ByteKV 存储鉴权修复方案](https://cloud.bytedance.net/docs/bytekv/docs/6412809fb08fc5022949da0b/66d8248d1d58ac032139658d). Configured PSMs containing characters outside ASCII letters, digits, hyphen (`-`), underscore (`_`) and period (`.`) produce a warning, including when authorization is disabled or `--check-psm` is omitted. Text mode prints warnings to stderr; JSON includes `warnings: [{code, psm, message}]`, with code `BYTEKV_PSM_UNEXPECTED_CHARACTERS`, or `[]` when none are found. The read still succeeds. Original entries and exact membership are preserved: `"example.demo.rd2,example.demo.rd3"` is one suspicious entry, so checking `example.demo.rd2` returns `listed: false`. Verify suspicious entries in the console; the CLI does not split or correct them. This character check does not validate whether a PSM exists or has effective access.
- `table list/info` return table metadata from the ByteKV platform, not live schema, current usage or measured QPS. `initialCapacity` and `expectedCapacity` are in GB and only reflect the amounts requested in the table-creation work order. These values are not currently enforced as write quotas. Do not expect or rely on this behavior; it may change. Text `table info` displays the GB suffix and this notice. JSON preserves both capacity fields as decimal strings and adds `capacityUnit: "GB"` and `capacityNote` to the result object; for `table list`, these fields apply to all `items`. An absent table returns `null`. `table list` makes one request for the specified namespace and has no pagination options.
- `kv get` makes one single-key read without automatic retries. Supply exactly one of `--key` or `--key-hex`; neither a key list nor both selectors are accepted. `--key` is a non-empty literal UTF-8 string: whitespace is preserved, and `\n` or `\x41` typed literally remain literal key characters. Unpaired Unicode surrogates are rejected before authentication. For arbitrary binary keys, use `--key-hex`: non-empty, even-length hexadecimal, accepting `0-9`, `a-f` and `A-F`, without spaces, separators or a `0x` prefix. Invalid hex is rejected before authentication, never truncated or repaired. Hex input preserves every byte, including NUL and invalid UTF-8. Do not pass raw binary through shell arguments: NUL cannot be passed and invalid UTF-8 may be replaced before the CLI receives it.
- Returned `keyEncoding` is `utf8` for `--key`, with the original text in `key`; it is `hex` for `--key-hex`, with lowercase hexadecimal in `key`. Both forms address the exact supplied bytes.
- HashClient is not supported. `kv get` does not add a hash prefix or convert a HashClient business key to its physical stored key. Passing that business key can address a different key; the result does not establish whether the HashClient record exists. Confirm the application's client mode before interpreting the response.
- Returned `valueEncoding` is `bytekv-escaped`: printable ASCII is unchanged, and other bytes are represented with `\n`, `\r`, `\t`, `\\` or `\xHH`. `version` is a decimal string to preserve uint64 precision.
- `itemStatus: "unavailable"` means the platform does not provide a separate per-key success status; `value` can contain a query error. Do not infer existence or success from `value`, an empty value, or version zero. CLI success means the platform envelope and response shape were accepted.
- The platform denies data reads by administrators. The CLI never changes roles or retries with another identity. Metadata access and data-read access are distinct.
- Responses larger than 8 MiB fail without partial output. HTTP diagnostics omit resource URLs and request/response bodies.
- A valid empty metadata result (`null` or empty `items`) is successful. Authentication failure, permission denial, transport failure and malformed responses are errors with a nonzero exit code. An unavailable optional Grafana URL is represented by `grafanaUrl: null` as described above.

## Agent Guidance

- Use only explicit user-requested resources and keys. Do not generate key lists, loops, parallel probes, scans or exports. This CLI's conservative request shape is not a server-enforced rate limit.
- No write, scan, multi-get, arbitrary HTTP, owner/PSM changes, tickets or role management commands are provided. Do not substitute another tool or edit the CLI to expand the task.
- For login failures, use the shared personal login flow (`bytedcli --site cn --as user auth login`). For access denial, check the same account's ByteKV console permissions; do not switch accounts or privileges automatically.
- Shared MCP discovers and runs these same commands; it does not add a separate data access path. Use named arguments (`name`, `namespace`, `table`, `key`, `keyHex`, `checkPsm`, `page`, `pageSize`) or an `args` array to preserve literal key characters. The shared MCP `args` string form has its own quoting and escape parsing; it is not the literal-key input form recommended here.
