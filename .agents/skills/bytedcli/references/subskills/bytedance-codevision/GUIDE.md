---
name: bytedance-codevision
description: "Use CodeVision evidence through bytedcli to discover authorized repositories, query CodeGraph, rank relevant files, read bounded source excerpts, and download full source files. Use when an agent needs auditable cross-repository code evidence, needs to find where code lives before inspecting it, or must connect repository, symbol, file, and source evidence without guessing a repo first."
---

# CodeVision Evidence (bytedcli)

CodeVision provides a staged, read-only evidence workflow for locating code across the repositories visible to the current user. Its rankings narrow the search space; they are evidence, not proof that a repository or file is correct.

## Invocation

```bash
bytedcli --json codevision evidence <resource> <action> [options]
```

Authenticate first when needed:

```bash
bytedcli auth login
```

The command uses the current user's ByteCloud JWT. Do not put tokens, headers, `requestOptions`, or endpoint overrides in input JSON. Network requests are restricted to the built-in CodeVision HTTPS endpoints. `CODEVISION_AGENT_SESSION_ID`, when already set by the caller, is forwarded as request metadata; otherwise bytedcli generates an isolated session ID. Local source files remain in a private session-scoped system temporary cache.

The SDK uses `CODEVISION_USERNAME`, then `USERNAME`, then `USER` as non-secret request attribution metadata. Set `CODEVISION_USERNAME` only when the automatic username is unavailable or incorrect; it does not replace authentication:

```bash
export CODEVISION_USERNAME=demo-user
```

## Choose the right code tool

- Use `codevision evidence` when the repository is unknown, several authorized repositories may be relevant, or you need a reproducible chain from repository ranking to CodeGraph rows and source lines.
- Use `codebase` when the repository or MR is already known and you need exact repository files, diffs, commits, or review metadata.
- Use `deepwiki` for semantic knowledge answers and indexed documentation. Verify important conclusions against source evidence afterward.
- Use local code search first when the target repository is already checked out and current.

## Evidence workflow

1. Run `scope get` and select the smallest relevant authorized space or repository set. The command returns one complete authorized-scope snapshot rather than a paginated collection; space metadata describes authorization context, not relevance.
2. Run `repository search` with a few strong code clues such as identifiers, API names, routes, config keys, or domain phrases.
3. Run `graph list`, then query the selected repositories for symbols, files, or relationships. Establish the primary symbol or call chain before broadening the search.
4. Run `file search` with repository references plus graph results, keywords, or file hints.
5. Run `file multi-get` on function-sized line ranges. Expand only when adjacent context is necessary.
6. Use `file download` only when a full local file is required.
7. Inspect `issues`, pending/error states, truncation metadata, score breakdowns, and path policies before drawing a conclusion.

## Commands and flags

| Command                                 | Normal flags                                                                                                                                                                                                                                                                             |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `codevision evidence scope get`         | `--space-id`, `--repo`, `--concurrency`                                                                                                                                                                                                                                                  |
| `codevision evidence repository search` | Required repeatable `--keyword`; optional `--space-id`, `--repo`, `--repo-branch <repo=branch>`, `--match-mode`, `--limit`, `--concurrency`                                                                                                                                              |
| `codevision evidence graph list`        | No input; lists the bounded templates exposed by bytedcli                                                                                                                                                                                                                                |
| `codevision evidence graph query`       | Required repeatable `--repo`, one `--branch`, and exactly one of `--template` or `--sql`; keyword templates accept repeatable `--keyword`, `--match-mode`, `--limit`; `schema` accepts `--limit`; custom SQL must be one `SELECT` or `WITH ... SELECT` statement ending with a top-level `LIMIT` of at most 1000; optional `--concurrency` |
| `codevision evidence file search`       | Required repeatable `--repo` and one `--branch`; add at least one of repeatable `--keyword`, `--file-hint`, or `--query-result-json`; optional `--match-mode`, `--limit`, `--per-repository-limit`, `--concurrency`                                                                      |
| `codevision evidence file multi-get`    | One `--repo`, one `--branch`, repeatable `--file`; optional `--repo-id`, `--repo-name`, `--start-line`, `--end-line`, `--max-lines`, `--max-bytes`, `--concurrency`                                                                                                                      |
| `codevision evidence file download`     | One `--repo`, one `--branch`, repeatable `--file`; optional `--repo-id`, `--repo-name`, `--concurrency`                                                                                                                                                                                  |

Use visible flags for normal requests. Use exactly one of `--input-json <json>` or `--input-file <path>` only for deeply nested evidence structures, such as different branches per repository, complete `queryResults`, or files from multiple repositories. Do not combine raw input with normal business flags.

All remote commands accept `--timeout-ms <ms>` from 1 through 600000. Raw input is field-validated against bytedcli's supported CodeVision request schemas. Unknown fields, including `requestOptions`, are rejected; only the CLI timeout is forwarded. A request may contain at most 50 repositories or 20 files, and `--concurrency` must be from 1 through 8.

## Examples

```bash
# 1. Inspect all authorized scope, or restrict it with optional input.
bytedcli --json codevision evidence scope get
bytedcli --json codevision evidence scope get \
  --space-id sample-space

# 2. Rank repositories. Reuse data.projection.repositories in later requests.
bytedcli --json codevision evidence repository search \
  --keyword OrderHandler \
  --keyword CreateOrder \
  --match-mode token \
  --limit 5

# 3. Inspect graph templates, then query selected repositories.
bytedcli --json codevision evidence graph list
bytedcli --json codevision evidence graph query \
  --repo example-org/example-repo \
  --branch main \
  --template symbols-by-keyword \
  --keyword OrderHandler \
  --limit 20

# 4. Rank files. Reuse data.projection.files for source retrieval.
bytedcli --json codevision evidence file search \
  --repo example-org/example-repo \
  --branch main \
  --keyword OrderHandler \
  --file-hint src/order \
  --limit 10

# 5. Read a bounded source range with line numbers and truncation metadata.
bytedcli --json codevision evidence file multi-get \
  --repo example-org/example-repo \
  --branch main \
  --file src/order/handler.ts \
  --start-line 40 \
  --end-line 120

# 6. Materialize a full file in the SDK cache when a local path is needed.
bytedcli --json codevision evidence file download \
  --repo example-org/example-repo \
  --branch main \
  --file src/order/handler.ts
```

For heterogeneous repository branches or other advanced structures, put one complete evidence request object in a file:

```bash
bytedcli --json codevision evidence graph query \
  --input-file ./codevision-query.json \
  --timeout-ms 120000
```

## Reading results

- `repository search` returns ranking metadata, `scoreBreakdown`, `pathPolicies`, and `data.projection.repositories`.
- `graph query` returns one `complete`, `pending`, or `error` result per repository. Preserve partial successes and report unresolved repositories.
- `file search` returns ranking metadata and `data.projection.files`. Generated-file matches remain visible with a disclosed penalty; configured excluded paths are filtered only during ranking.
- `file multi-get` returns line-numbered excerpts, SHA-256 digests, byte counts, and truncation reasons. Omitted limits default to 200 lines and 65536 excerpt bytes per file.
- `file download` returns all ready/error events together in `data.events`; one file's cache-validation failure does not discard other file events. Ready events include a private session cache path. Each complete source file is limited to 8388608 bytes. On later client startup, bytedcli best-effort scans a bounded set of session directories and removes some entries older than 24 hours; this is not a guaranteed deletion deadline.

## Agent guidance

- Start narrow. A small authorized scope and a few discriminative identifiers produce stronger evidence than broad business nouns.
- Treat Top-K order as a retrieval signal. Confirm candidates with graph relationships and source lines before claiming ownership or behavior.
- Query primary symbols and call chains separately from secondary concerns, then connect them only when returned evidence supports the relationship.
- Prefer `file multi-get` over `file download` for reasoning. Bounded excerpts keep evidence reviewable and reduce irrelevant context.
- If a result is truncated, pending, or carries issues, state that limitation and narrow, retry, or inspect the affected repository separately.

## References

- Read [Invocation](../../invocation.md) when installation, global option placement, site selection, JSON output, or HTTP diagnostics are unclear.
- Read [Troubleshooting](references/codevision-troubleshooting.md) when a CodeVision command, authentication, query, download, or cache operation fails.
