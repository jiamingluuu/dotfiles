---
name: bytedance-primus
description: "Always use this skill for read-only Primus inspection, diagnosis, and log retrieval. A prompt is in scope when it asks to inspect, query, or debug and includes at least one Primus signal: the word Primus; a primus-ui or primushistory URL; a /jobhistory/app/ or redirect_log.html path; an application id commonly ending in -pj; a Primus-derived mljob-log-proxy URL accompanied by application, History, role, or pod context; or a Forge/Reckon request explicitly targeting Primus. Within that context, use it for exit -137/OOM/SIGKILL, application and AM summaries, Conf, Job, Data, environment, roles, pods, tasks, Doctor, Timeline, TaskBuild, Streaming, Flow, CRDs, lifecycle, and dispatcher/launcher/executor/stdout/stderr logs. It maps Primus UI resources to read-only bytedcli commands, preserves Forge-provided TTP History routing, and uses authenticated browser evidence when a TTP frontend resource must be checked."
---

# Primus

Run the matching `bytedcli primus ...` command directly. Start an application investigation with `primus app get`; use `primus app list` when the application id is unknown. These commands expose the Primus UI concepts as stable, named query resources, so an agent can move from application → role → pod/log without reconstructing frontend requests.

For Primus logs, start from the exact History/UI URL or app id, identify the role with `primus role list`, list the role pods with `primus pod list`, then use `primus log list --resolve-files` for bounded concrete-file metadata or `primus log get --pod-name <pod>` for matched file content. This application → role → pod → log sequence is the primary diagnostic path.

All commands are read-only. Pass a copied Primus UI URL directly with `--url`; bytedcli derives the corresponding region, History host, and application id. Otherwise pass `--vdc` and `--app-id`. Use `--attempt-id <n>` to select the same application attempt in the regional resource API and retained History queries; copied History view URLs such as `/jobhistory/app/<app-id>/<attempt-id>/` are also accepted and keep the selected attempt. CloudNative app ids are normalized with `-pj` automatically. Yarn `application_...` ids require `--host` or `--url`.

For host-specific routing, gzip handling, and log-resolution notes, read `references/primus.md`.

## TTP History Routing

Treat the Forge/Reckon Primus links as resource-specific evidence; a host that works for one resource does not become a global alias for every request.

- EU-TTP app payloads such as `newStatus.json?from=page` stay on the Forge-provided `primushistoryuseast2a-k8s.tiktok-eu.org` host. US-TTP app payloads stay on `primushistoryuseast5-k8s.tiktok-us.net`; normalize a copied `primushistoryuseast5-k8s.tiktok-usts.net` input to that resolvable host. Do not rewrite either app route to a BDEE/office gateway. When the exact retained payload is required, create a mode-0600 temporary file, store its path in `primus_payload_file`, and register an `EXIT` cleanup trap before issuing one read-only `curl --compressed --fail --silent --show-error --output "$primus_payload_file" '<direct-history>/jobhistory/app/<app-id>[/<attempt>]/newStatus.json?from=page'` request. Before inspecting requested keys, require `jq -e 'type == "object"' "$primus_payload_file" >/dev/null` to succeed. Treat an HTTP redirect, login/error page, invalid JSON, or non-object JSON as transport/auth/format unavailable or unverified, never as empty data; do not switch hosts or guess another endpoint. Never allow the raw response body to reach stdout, a tool transcript, or the final response, and do not pass the URL through a client that rewrites its host.
- AM environment is a separate retained resource. EU-TTP uses `primus-history-euttp.byted.org`; US-TTP uses `primus-history-usttp.tiktok-row.org`.
- Do not query EU-TTP or US-TTP Timeline/TaskBuild as an agent data source. Their History pages load `timeline.html` and `taskbuild.html`, which issue same-origin relative requests to `doctor/timeline.json` and `doctor/taskbuild.json`; live authenticated browser checks currently fail (`Failed to fetch` on EU-TTP and invalid response format on US-TTP). If the user explicitly asks about these pages, use `chrome:control-chrome` once to inspect the exact Forge-linked page. Report the frontend resource as unavailable when it fails; do not change hosts, hand-build another API URL, or reinterpret the failure as an empty event list.
- CN and ROW Timeline/TaskBuild remain normal `bytedcli primus timeline list` / `task-build list` queries. Preserve an explicit attempt segment from the copied History URL or `--attempt-id`.

## Quick Start

```bash
bytedcli --json primus app list --vdc GL --keyword demo-job --limit 200
bytedcli --json primus app get --vdc GL --app-id demo-app-pj
bytedcli --json primus app get --url 'https://primushistory.example/jobhistory/app/demo-app-pj/'
bytedcli --json primus app get --url 'https://primushistory.example/jobhistory/app/demo-app-pj/' --attempt-id 2
bytedcli --json primus app get --url 'https://primushistory.example/jobhistory/app/demo-app-pj/2/'
bytedcli --json primus app get --url 'https://primushistory.example/jobhistory/app/demo-app-pj/' --expect-job-id demo-job --expect-stage-id demo-stage
bytedcli --json primus app get --url 'https://primushistory.example/jobhistory/app/demo-app-pj/' --no-env
bytedcli --json primus app get --url 'https://primushistory.example/jobhistory/app/demo-app-pj/' --raw

bytedcli --json primus am get --vdc GL --app-id demo-app-pj
bytedcli --json primus config get --vdc GL --app-id demo-app-pj
bytedcli --json primus job get --vdc GL --app-id demo-app-pj
bytedcli --json primus data get --vdc GL --app-id demo-app-pj
bytedcli --json primus env get --vdc GL --app-id demo-app-pj --prefix PRIMUS_
bytedcli --json primus env get --vdc GL --app-id demo-app-pj --key JOB_ID --key STAGE_ID
bytedcli --json primus role list --vdc GL --app-id demo-app-pj
bytedcli --json primus cluster get --vdc GL --app-id demo-app-pj

bytedcli primus pod list --vdc GL --app-id demo-app-pj --role dispatcher --state ALL
bytedcli primus pod list --vdc GL --app-id demo-app-pj --role dispatcher --state ALL --search demo-pod
bytedcli primus log list --vdc GL --app-id demo-app-pj --role dispatcher --state ALL --resolve-files --max-pages 1 --resolve-limit 5
bytedcli primus log get --vdc GL --app-id demo-app-pj --role dispatcher --state ALL --pod-name demo-pod --max-row-attempts 3 --file-pattern '_dispatcher\.log|stderr\.log|syslog\.log'
bytedcli primus log get --vdc GL --app-id demo-app-pj --role NorbertDriver --state ALL --file-pattern 'stdout\.log'
bytedcli primus log get --vdc GL --app-id demo-app-pj --role stream --state ALL --file-pattern 'dataio.*\.log\.INFO' --start '0-200000'
bytedcli primus log get --vdc GL --app-id demo-app-pj --role stream --state ALL --file-pattern 'dataio.*\.log\.INFO' --output-dir /tmp/primus-logs --download-full
bytedcli --json primus log get --vdc GL --app-id demo-app-pj --role stream --state ALL --file-pattern 'dataio.*\.log\.INFO' --no-cache

bytedcli primus task list --vdc GL --app-id demo-app-pj
bytedcli primus task-build list --vdc GL --app-id demo-app-pj --page-size 100
bytedcli primus timeline list --vdc GL --app-id demo-app-pj --page-size 100
bytedcli primus doctor get --vdc GL --app-id demo-app-pj
bytedcli primus streaming get --vdc GL --app-id demo-app-pj
bytedcli primus flow get --vdc GL --app-id demo-app-pj
bytedcli primus devops crd list --vdc GL --app-id demo-app-pj
bytedcli primus devops pod list --vdc GL --app-id demo-app-pj
bytedcli primus devops pod list --vdc GL --app-id demo-app-pj --table-mode search --search demo-pod
bytedcli primus devops pod list --vdc GL --app-id demo-app-pj --table-mode missing
bytedcli primus devops lifecycle get --vdc GL --app-id demo-app-pj --pod-name demo-pod
bytedcli primus devops pod-status get --vdc GL --app-id demo-app-pj --pod-name demo-pod

bytedcli primus export --vdc GL --app-id demo-app-pj --output-dir /tmp/primus-dump
bytedcli primus export --vdc GL --app-id demo-app-pj --output-dir /tmp/primus-dump --fetch-logs

bytedcli primus url get --kind overview --vdc GL --app-id demo-app-pj
bytedcli primus url get --kind pods --vdc GL --app-id demo-app-pj --role dispatcher --state ALL
bytedcli primus raw get --kind pod-status --vdc GL --app-id demo-app-pj --pod-name demo-pod
```

## Command Selection

- Use `app list` to discover recent applications from a History host. Filter with `--keyword`, `--user`, `--queue`, or `--state`; check `truncated` before assuming the returned set is complete.
- Use `app get` first when the application id or URL is known. It returns normalized application and AM facts, role counts, related applications, Data stream status, Streaming sources, gang-scheduler queue entries, actual `overviewSections`, relative `queryableResources` command paths, application `features`, safe component versions, and structured `endpointErrors`. A resource can remain queryable even when its overview section is absent; prepend `bytedcli primus` to a returned path and reuse the current `--url` or `--vdc` / `--app-id` selector to determine whether records are empty. `app get` does not expose the full AM environment. Add `--raw` only when the exact env/overview/status payloads are required. Use `--no-env` when the AM env host is unavailable and job/stage validation is not required.
- When a Forge job or stage is known, pass `--expect-job-id` and/or `--expect-stage-id`. A mismatch raises `PRIMUS_CONTEXT_MISMATCH`; an unavailable env endpoint raises `PRIMUS_CONTEXT_UNVERIFIED`. Never reuse a job's latest-stage application for an older stage without this validation.
- Use the UI resource commands for focused queries: `am get`, `config get`, `job get`, `data get`, `env get`, `role list`, `cluster get`, `doctor get`, `streaming get`, and `flow get`. Use `timeline list` and `task-build list` for CN/ROW; apply the TTP frontend limitation above for EU-TTP/US-TTP.
- `env get` and the Doctor environment section redact secret-like values by default. Narrow environment queries with repeated `env get --key` or one `--prefix`; use `env get --show-sensitive` or `doctor get --show-sensitive` only when the exact value is required and the output remains local.
- Use `role list` to identify role names and counts, then `pod list --role <role>` for executor rows. When the pod name is known, narrow the row directly with `pod list --role <role> --search <pod-name>`; use `devops pod-status get --pod-name <pod-name>` for its UI status and `log get --role <role> --pod-name <pod-name>` for its concrete logs. This is the standard application → role → pod/status/log path.
- Use `export` for handoff or wider debugging. It writes normalized `summary.json`, raw `env.json`, `overview.json`, `status.json`, retained History role row files, `tasks.json`, `crds.json`, `cluster.json`, and a History-backed `logs-index.json`; use focused `pod list` / `log list` / `log get` for the region-specific live query path.
- Use `task list` for task rows. On CN/ROW, use `task-build list` for TaskBuild statistics and `timeline list` for chronological Primus events. Do not silently substitute these resources on EU-TTP/US-TTP.
- Use `devops pod list`, `devops crd list`, `devops lifecycle get`, and `devops pod-status get` for DevOps-side diagnostics. Select the UI pod table with `devops pod list --table-mode normal|search|missing`.
- Use `pod list` for regional role rows and `log list` when you need normalized log records. Add `log list --resolve-files` only when concrete file metadata is needed across a bounded set of rows; it defaults to one page and five resolution attempts and prioritizes abnormal exits. All four sites try rows with usable pod/host coordinates through the regional file API, expand a validated pod landing when necessary, then retry serially through retained History only when regional discovery fails or produces no concrete files. Check `truncated`, `resolution_truncated`, `attempted_rows`, `concrete_file_rows`, `landing_only_rows`, `no_files_rows`, `failed_rows`, `skipped_rows`, `without_log_url_rows`, `without_log_coordinates_rows`, and each row's status before drawing conclusions. Log commands return `cache.status` (`hit`, `miss`, `mixed`, or `bypass`) and per-lookup `stored_at`, `age_ms`, `expires_at`, and `ttl_ms`; ordinary `log list` caches its pod discovery while explicit `pod list` remains live. Pass `--no-cache` only when a fresh control-plane read is required. Increase `--max-pages` or `--resolve-limit` deliberately; for one pod or actual file content, use `log get`.
- Use `log get` when you need actual file content such as `stderr.log`, `syslog.log`, `stdout.log`, dataio logs, or role-specific logs under `/var/log/tiger`. It prioritizes abnormal rows and automatically tries up to three candidates when a row is empty or unavailable; within one row, one concrete file failure does not stop the remaining matched files. Inspect `rowAttempts`, `scan`, top-level `cache`, per-file `cache`, `empty`, `fetchError`, `fetchErrorCode`, `fetchErrorHint`, and `fetchErrorAuthCommand`; authentication or gateway recovery guidance must not be discarded. `--no-cache` bypasses both regional pod/file discovery caches and EU/US plugin metadata caches, but never changes log-body freshness because log bodies are not cached. Narrow with `--pod-name` or `--row-index`, and increase `--max-row-attempts` only when needed. `primus log get` owns the complete region-specific path: all four sites use regional pod/file discovery first, including validated landing expansion, then use retained History only as a serial fallback when no readable concrete file is produced. US-TTP/EU-TTP select the content transport internally after concrete-file discovery. Keep using the same Primus command throughout, and do not hand a discovered concrete URL to another log command. Use `--start <range>` when fetching the beginning or middle of a concrete file: direct CN/ROW reads support `-N` and `A-B`, while US/EU reads also accept `0` and `A-`. Use `--output-dir <dir>` when matched content should be written to files instead of printed; add `--download-full` for US/EU files or direct CN/ROW files whose discovery metadata includes a positive file size. `logResolutionStatus: "no-files"` means the applicable discovery path completed without concrete files. `logResolutionStatus: "fetch-error"` means discovery failed and is not evidence that files are absent. Use the recorded attempt error and retry guidance directly.
- Use `raw get --kind <kind>` only as an escape hatch for an exact History JSON endpoint.
- Use `url get --kind <kind>` to generate the exact History or UI URL without fetching it.

## Important Options

- Common selectors: `--url`, `--vdc`, `--app-id`, `--attempt-id`, `--host`, `--row`; `--attempt-id` selects the same application attempt in both the resource API and retained History queries, and is rejected by `primus url get --kind ui`.
- HTTP controls: `--header 'Name: value'`, `--timeout-ms <ms>`.
- Application discovery: `app list --limit`, `--keyword`, `--user`, `--queue`, `--state`.
- Application safety: `app get --no-env`, `--raw`, `--expect-job-id`, `--expect-stage-id`. Do not combine `--no-env` with either expectation option.
- Sensitive environment access: repeated `env get --key`, `env get --prefix`, and explicit `env get --show-sensitive` / `doctor get --show-sensitive`.
- Role rows: `--role`, `--state`, `--page-size`, `--page`, `--search`, `--sort-order`.
- Collection commands: `--max-pages`, `--log-limit-bytes`; `log list --resolve-files` also supports `--resolve-limit`. `log list/get --no-cache` bypasses all discovery/plugin metadata caches for one invocation.
- Log files: `--pod-name`, `--row-index`, `--max-row-attempts`, `--file-pattern`, `--max-files`, `--start`, `--output-dir`, `--download-full`.
- DevOps endpoints: `--devops-app-id`, `--no-include-doctor`; pod tables use `--table-mode normal|search|missing`.

## Notes

- `app get` is the canonical agent-facing overview, while focused UI resources use their named `get` or `list` commands.
- `env get` and `doctor get` redact secret-like environment values by default. `app get --raw`, either command with `--show-sensitive`, and `primus export` may contain sensitive values; share summarized findings rather than raw env dumps.
- Focused application/AM summary, role, pod, Data, and log commands use the Primus CLI resource API on CN, ROW, US-TTP, and EU-TTP. Focused logs retry serially through retained History when regional discovery cannot produce readable concrete files. History remains the source for application discovery, UI-only resources, and `primus export`; US/EU empty Data responses fall back to retained History Data.
- `config get` and `job get` parse JSON strings embedded in `newStatus.json?from=page`. `data get` removes one transport-level `#<JSON>#` wrapper when present and preserves whether the resulting Data documents parsed successfully.
- `doctor get` uses the deployment's diagnostic route. Timeline/TaskBuild are agent-queryable on CN/ROW; EU-TTP/US-TTP frontend failures are reported as unavailable under the TTP routing rule instead of being retried on a guessed host.
- `pod list` uses normalized rows from the regional Primus CLI API. `log list` and `log get` use regional pod/file discovery first on all four sites, including validated landing expansion, with a serial retained-History fallback.
- `--url` and `--host` accept only known Primus History/UI host forms; use `--vdc` and `--app-id` for generated hosts.
- `0` and `-1000` exit codes are usually normal. `137`, `-137`, `9`, and `-9` usually indicate OOM or kill unless the diagnosis field says otherwise.
- Use `log list --resolve-files` for bounded concrete-file metadata and `log get` for content. Treat `no-files` as authoritative only after the applicable regional or History discovery path completes; treat `fetch-error` as a failed discovery that still requires recovery.
- `primus log get` uses regional file discovery first on all four sites, retained History as the serial discovery fallback, and selects the US/EU content transport internally; callers keep the same Primus command across regions.
- Primus History retention is an external boundary for regional log fallbacks, History-only resources, and `primus export`. Retry the exact older application/attempt from `applications` or the original stage metadata; never silently substitute a newer stage's application.
- The client retries transient HTTP/application-level rate limits and returns `PRIMUS_RATE_LIMITED` with a recovery hint after exhaustion. Do not immediately widen `--max-pages`, `--resolve-limit`, or `--max-row-attempts` after this error.
