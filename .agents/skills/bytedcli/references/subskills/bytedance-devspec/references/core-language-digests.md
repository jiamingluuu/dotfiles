# Core Language DevSpec Digests

This file is a compact bootstrap and fallback reference for agents. It is not a
full copy of DevSpec. Prefer installed cache data from `bytedcli --json devspec
...`; use this digest only when cache/auth/network is unavailable or when a fast
first-pass review needs conservative defaults.

Recommended refresh path:

```bash
bytedcli --json devspec install --language Go JavaScript
bytedcli --json devspec guideline get --name bytedance_go --locale en --summary
bytedcli --json devspec guideline get --name bytedance_javascript --locale en --summary
bytedcli --json devspec scan-rule list --language Go
bytedcli --json devspec scan-rule list --language JavaScript
```

## How Agents Should Use This

- Treat REQUIRED/required rules as blocking findings.
- Treat RECOMMENDED/suggested rules as warnings unless local code ownership says otherwise.
- Treat OPTIONAL/optional rules as contextual guidance.
- Prefer the repository's existing formatter, linter, framework, and test patterns.
- When this digest and the installed DevSpec cache disagree, the cache wins.
- When the cache and `--original` disagree, the `--original` DevSpec response wins.

## Language Routing

| User input | Canonical scan-rule language | Guideline name candidates |
|------------|------------------------------|---------------------------|
| `go`, `golang`, `golnag` | `Go` | `bytedance_go` |
| `js`, `javascript`, `javascrpt`, `node`, `nodejs`, `ecmascript` | `JavaScript` | `bytedance_javascript` |
| `ts`, `typescript`, `type-script`, `tsx` | `JavaScript` or `TypeScript` scan rules if listed by `devspec language list` | `bytedance_javascript` first, then discovered TypeScript guideline if available |

Use `bytedcli --json devspec language list` to confirm the current scan-rule language list before assuming TypeScript has a separate rule bucket.

## Go Digest

Source guideline: `bytedance_go`.

First verified rule from the DevSpec page:

- `byted_s_package_name_same_with_dir` is required: package names should match directory names, be short, and be meaningful. Test code may use a `_test` package.

Conservative review checklist:

- Package and file organization: package names should be concise, lowercase, and aligned with directory names; keep public APIs in obvious files and avoid utility dumping grounds.
- Naming: exported identifiers need clear names and comments when they are part of the package API; avoid obscure abbreviations outside common Go idioms such as `ctx`, `req`, `resp`, `cfg`, and `err`.
- Formatting: generated code should still be `gofmt`/`goimports` clean; imports should be grouped and unused imports removed.
- Errors: return errors instead of panicking in library or request-path code; wrap errors with useful context; do not discard errors with `_` unless there is a clear reason.
- Context: pass `context.Context` through request, RPC, storage, and long-running operations; do not store contexts in structs for normal request flow.
- Concurrency: protect shared mutable state, avoid goroutine leaks, handle channel close ownership carefully, and make cancellation paths explicit.
- Nil and zero values: check nil pointers, nil maps/slices, and optional response fields before dereference; design structs so useful zero values are safe where possible.
- Logging: include actionable context without leaking secrets, tokens, cookies, raw credentials, or private user data.
- Tests: table-driven tests are preferred for branching logic; cover error paths and edge cases around nil, empty, timeout, and malformed inputs.
- Generated/IDL code: do not hand-edit generated artifacts unless the repository explicitly owns them; update the source IDL/schema instead.

Go scan-rule workflow:

```bash
bytedcli --json devspec scan-rule list --language Go
bytedcli --json devspec scan-rule list --language golang --severity critical major
```

## JavaScript And TypeScript Digest

Source guideline candidate: `bytedance_javascript`. Use `devspec guideline list --language JavaScript --summary` to discover current names.

Conservative review checklist:

- Types first: prefer TypeScript types/interfaces or well-supported runtime schemas for structured data; avoid implicit `any` and unvalidated external payloads.
- Module boundaries: keep side effects isolated, exports intentional, and shared helpers small; avoid large catch-all utility modules.
- Async behavior: always await promises that must complete, handle rejections, avoid floating promises unless deliberately detached, and preserve cancellation/timeouts where the local stack supports them.
- Errors: surface actionable errors with context; do not swallow exceptions in empty `catch` blocks; avoid throwing strings or unstructured values.
- Equality and coercion: prefer strict equality and explicit conversions; avoid relying on truthiness for values where `0`, `""`, or `false` are valid inputs.
- Nullability: distinguish missing, null, empty array/object, and false; use optional chaining carefully and keep fallback defaults explicit.
- Security: never log or commit tokens, cookies, AK/SK pairs, JWTs, or private user data; sanitize data before HTML/SQL/shell/URL interpolation.
- Frontend state: keep state ownership clear, avoid derived-state drift, clean up timers/subscriptions/listeners, and handle loading, empty, error, and permission states.
- Node/process code: avoid shell injection, prefer structured APIs over string commands, validate file paths and URLs, and keep network timeouts explicit.
- Tests: cover async failure paths, serialization/parsing boundaries, UI states, and alias/normalization logic where user input is accepted.

JavaScript/TypeScript scan-rule workflow:

```bash
bytedcli --json devspec scan-rule list --language JavaScript
bytedcli --json devspec scan-rule list --language js --severity critical major
bytedcli --json devspec scan-rule list --language TypeScript --severity critical major
```

If `TypeScript` is not returned by `devspec language list`, use the JavaScript scan-rule bucket and the TypeScript-specific checklist above.

## Cache Commands For Core Languages

Install the current remote data into the local cache:

```bash
bytedcli --json devspec install --language Go JavaScript
```

Refresh only when freshness matters:

```bash
bytedcli --json devspec guideline list --language Go --update --summary
bytedcli --json devspec guideline list --language JavaScript --update --summary
bytedcli --json devspec scan-rule list --language Go --update
bytedcli --json devspec scan-rule list --language JavaScript --update
```

Bypass cache for source-of-truth troubleshooting:

```bash
bytedcli --json devspec guideline get --name bytedance_go --original
bytedcli --json devspec guideline get --name bytedance_javascript --original
```
