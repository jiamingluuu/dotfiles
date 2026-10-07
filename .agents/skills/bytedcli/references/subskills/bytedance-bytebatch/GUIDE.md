---
name: bytedance-bytebatch
description: Use when the user mentions ByteBatch, 批处理平台, 刷库, 刷标签, 批量任务, batch job, job type, bytebatch 任务, or asks to list/create/rerun ByteBatch jobs, inspect batch-processing services and deploy regions, or upload/download ByteBatch job files through the CLI.
---

# ByteBatch CLI

Use `bytedcli bytebatch <subcommand>` for ByteBatch batch-processing (刷库 / 刷标签 / 批量任务) workflows.

## Workflow

1. Find the service: `bytebatch service list` → note the PSM and its default region/cluster.
2. Find the deploy region and cluster: `bytebatch region list` (`--region` / `--cluster` must be a valid pair).
3. Find the job type: `bytebatch job-type list --psm <psm> --region <region>`; job types are registered in the service's own code, they are not free text.
4. Query or operate jobs with `bytebatch job list` / `job create` / `job execute`.
5. Prefer `-j/--json` for automation. The structured schema is `{status, data, error, context}`.
6. Treat `job create` and `job execute` as dry-run by default. They only print the payload they would POST; pass `--yes` **after explicit user approval** to submit.

## Commands

| Command                    | Purpose                                                                      |
| -------------------------- | ---------------------------------------------------------------------------- |
| `whoami`                   | Show which ByteBatch user the current login maps to (auth check)             |
| `region list`              | Deploy regions and their clusters                                            |
| `service list` / `get`     | Batch-processing services, owner, default region/cluster, permissions        |
| `job-type list`            | Job types registered for a service in one deploy region                      |
| `job list`                 | Jobs with filters (type/status/id/biz-key/creator)                           |
| `job create`               | Create a job (immediate or scheduled); dry-run without `--yes`               |
| `job execute`              | cancel / run / terminate / continue / retry / rerun; dry-run without `--yes` |
| `file upload` / `download` | Upload a job input file, download input/success/fail result files            |

## References

Read on demand — do not load these up front:

- `references/bytebatch.md` — every command with its flags, enum values, file-URI shapes and error-code table. Read it before composing any concrete `bytedcli bytebatch` invocation.
- `../../invocation.md` — how to install and invoke `bytedcli`, global flags, JSON output contract. Read it when the CLI is missing or a global flag is unclear.
- `../../troubleshooting.md` — generic bytedcli failures (auth, proxy, network). Read it when an error is not in the ByteBatch error-code table.

## Site selection

ByteBatch has its own site set, exposed as `--bytebatch-site` (default `cn`), independent of the global `--site` flag:

| `--bytebatch-site` | Host                              |
| ------------------ | --------------------------------- |
| `cn`               | `music-batch.bytedance.net`       |
| `i18n`             | `music-batch.tiktok-row.net`      |
| `boe`              | `bytebatch-boe.bytedance.net`     |
| `boe-i18n`         | `bytebatch-boei18n.bytedance.net` |

## Auth

Authentication first reuses the normal bytedcli ByteCloud user login and sends it as a Bearer JWT. The selected `--bytebatch-site` automatically chooses the matching credential partition (`cn`, `i18n-tt`, `boe`, or `boe + boei18n`). Formal requests do not use PPE headers. Older ByteBatch deployments automatically fall back to the legacy CAS site session.

For JWT authentication errors, log in to the matching partition and verify with `whoami`, for example:

```bash
bytedcli --site cn auth login
bytedcli bytebatch whoami
```

Only if an older deployment falls back to CAS and reports `BYTEBATCH_SSO_SESSION_REQUIRED` or `BYTEBATCH_SESSION_BOOTSTRAP_FAILED`, refresh its browser session. Use `--site i18n-tt` for the formal `i18n` ByteBatch site; the existing `*.bytedance.net` sites use `--site cn` for CAS.

Do not hand-write cookies or JWTs for ByteBatch commands.

## Agent Guidance

- A successful `bytedcli auth status` does **not** prove the selected ByteBatch backend accepts the JWT or that the caller has ByteBatch RBAC. Run `bytedcli bytebatch whoami --bytebatch-site <site>` once before a batch of calls.
- Job types are per service **and** per deploy region. Always list them for the exact `--psm` + `--region` pair before creating a job; a typo silently becomes an unknown type instead of a helpful error.
- `--region` and `--cluster` must match: `China-North` clusters differ from `SG1` clusters. Read them from `bytebatch region list` or from the service's default cluster in `service get`.
- Creating a job usually needs an input file first: `bytebatch file upload --psm <psm> --region <region> --file ./input.csv` prints a **File URI** (a bare key) — that is what `job create --input-file-uri` expects, not the full download URL.
- File identifiers come in two shapes: `file upload` returns a bare key, `job list` returns full URLs. `file download --uri` accepts either. Bare keys and same-origin URLs use ByteBatch auth; recognized ByteBatch public-file URLs are downloaded without JWTs, cookies, command-level headers, or redirects. Other origins and paths outside `/api/files/` are rejected.
- Allowed job operations depend on the job's current state; `job list --json` reports each job's `allowedOperations`. Do not attempt `rerun` on a running job.
- Job status semantics: `initial`, `scheduled`, `cancelled`, `starting_cron`, `processing`, `terminating`, `success`, `fail`, `terminated`. `success` means the job finished, not that every row succeeded — compare `countTotal` / `countFinished` / `countSuccess` and download the fail file when they differ.
- ByteBatch does not always report a total count. When it does not, JSON reports `total: null` plus `current_count` / `has_more`, and the text summary says `This page` — never read `current_count` as a total.
