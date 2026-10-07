---
name: bytedance-ray
description: "Query CN Ray Dashboard jobs, Serve, cluster, actors, streaming, metrics and logs; manage OpenStudio project Ray services with mandatory human confirmation for changes. Use for Ray runtime or OpenStudio service management; not TCE provisioning."
---

# Ray Dashboard and OpenStudio Services

## OpenStudio Service Management

Use `bytedcli ray service` for OpenStudio **服务管理 → Ray 服务**.
Read [OpenStudio service management](references/openstudio.md) for project lists
(mine/subscribed/all), name search, details, version history and configuration
previews. Update/restart/stop/rollback default to preview only. Before submission,
show the exact target, configuration diff and high-risk restart/interruption warning.
An explicit human reply confirming that operation in chat is valid approval.
After that approval, an agent may run `--interactive` in a PTY and enter the exact
confirmation phrase on the user's behalf. Compare the fresh terminal preview with
the approved operation before entering the phrase; ask again if the action, target,
configuration, current/rollback version, status or restart mode changed. Never infer approval from
silence, a general task request or an unrelated earlier confirmation.
For file-based edits, record the exact input file bytes or SHA-256 before the
approved preview and verify them again before starting `--interactive` and before
entering the confirmation phrase. Changed
file contents require a new preview and approval, even when masked previews look
identical; never compare redacted values as evidence that secrets are unchanged.
These commands use CN ByteCloud JWT authentication; the Dashboard commands below
use a separate credential-free transport.

## Dependencies and Setup

Use the built-in `bytedcli ray` commands. No Python Ray installation or browser
automation is needed. Install bytedcli if missing, then discover the command help:

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli ray --help
bytedcli ray log get --help
```

Require network access to the user-provided CN Dashboard. Pass the root URL or
original hash-route URL to every command. `--url` selects the target independently
of global `--site`. Only `*.ray-dashboard-cn.bytedance.net` root URLs over HTTP(S)
are supported. Do not paste browser cookies or JWTs: the verified gateway uses
direct reads without credentials. Browser-session gateways, redirects, proxy
paths, query strings, non-default ports and other regions are unsupported.

## Commands

Use global `--json` before `ray` for scripts and agents. Lists default to page 1,
20 items; `--page-size` accepts 1-1000. Dashboard commands below are read-only snapshots.

| Command                  | Selection and result                                                                                                        |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `ray job list`           | Jobs; optional `--id`, `--submission-id`, `--user`, `--keyword` entrypoint substrings and exact `--status`                  |
| `ray job get --id`       | Job or submission details                                                                                                   |
| `ray serve list`         | Applications; `--keyword` name substring, exact `--status`                                                                  |
| `ray serve get --name`   | Exact application with deployments and replicas                                                                             |
| `ray serve status`       | Applications, controller and proxies                                                                                        |
| `ray cluster get`        | Version, metadata and scheduler resource status                                                                             |
| `ray node list`          | Nodes and resource snapshots; exact `--state`, hostname `--keyword`                                                         |
| `ray node get --id`      | Node details                                                                                                                |
| `ray actor list`         | Server-side pagination and aggregate filter counts; `--id`, `--job-id`, `--namespace`, `--state`, `--keyword` class filters |
| `ray actor get --id`     | Actor details and available process statistics                                                                              |
| `ray streaming list`     | Datasets and operators; `--job-id`, exact `--state`, dataset `--keyword`                                                    |
| `ray streaming get --id` | Exact dataset; narrow with `--job-id` when ambiguous                                                                        |
| `ray cluster metrics`    | Live node resource snapshots and configured Grafana links, not historical curves                                            |
| `ray log list --node-id` | Log filenames grouped by type; optional `--glob`                                                                            |
| `ray log get`            | Exactly one source: `--job-id`, `--actor-id`, `--task-id`, or `--node-id` plus `--filename`                                 |

Streaming list/get accept `--mode streaming|batch|blocked_streaming|oneshot_streaming|all`;
the default is `streaming`. Actor pagination is server-side; other lists filter
and paginate the retrieved snapshot locally. Read `total`, `current_count`,
`page`, `page_size` and `has_more`; do not infer completeness from one page.
Actor `aggregated` contains the Dashboard's filter counts; `has_more` is only a
pagination signal, not a collection-completeness guarantee.

## Inspection Workflow

```bash
URL='http://demo.example.service.ray-dashboard-cn.bytedance.net/#/jobs'
bytedcli --json ray cluster get --url "$URL"
bytedcli --json ray job list --url "$URL"
bytedcli --json ray job get --url "$URL" --id demo-job
bytedcli --json ray node list --url "$URL" --state ALIVE
bytedcli --json ray node get --url "$URL" --id demo-node
bytedcli --json ray actor list --url "$URL" --job-id demo-job
bytedcli --json ray actor get --url "$URL" --id demo-actor
bytedcli --json ray serve status --url "$URL"
bytedcli --json ray serve list --url "$URL"
bytedcli --json ray serve get --url "$URL" --name demo-app
bytedcli --json ray streaming list --url "$URL" --job-id demo-job
bytedcli --json ray streaming get --url "$URL" --job-id demo-job --id demo-data
bytedcli --json ray cluster metrics --url "$URL"
bytedcli ray log get --url "$URL" --job-id demo-job --lines 200
bytedcli ray log get --url "$URL" --actor-id demo-actor --suffix err --lines 200
bytedcli ray log get --url "$URL" --task-id demo-task --lines 200
bytedcli --json ray log list --url "$URL" --node-id demo-node --glob '*.log'
bytedcli ray log get --url "$URL" --node-id demo-node --filename demo.log --keyword ERROR
```

## Agent Guidance

- Start with the URL and a resource list. Copy exact IDs from returned objects.
  Job IDs and submission IDs differ; driver-only jobs may lack submission IDs.
- `RUNNING` does not prove business health. Correlate actor states, node
  resources, scheduler status and logs before drawing a conclusion.
- Empty Serve applications or datasets are successful empty results, not evidence
  of an outage. Report unsupported endpoint errors separately from empty results.
- Log reads default to 1000 tail lines, maximum 50000, with a 20 MiB response cap.
  `--keyword` matches literally within that tail, not the whole log. Check
  `possibly_truncated`, `returned_lines` and `matched_lines`.
- Use `--suffix out|err` only with actor/task sources. Job logs resolve the driver
  node and submission log filename; if coordinates are unavailable, list node
  files and select a filename explicitly. Do not guess a submission filename.
- Sensitive configuration/environment fields and recognizable credential strings
  are masked. Arbitrary application log text may still contain private data;
  inspect before sharing. Do not store raw production output in tests or docs.
- No job submission/stopping, Serve deployment, actor killing, profiling,
  environment dumps, continuous tailing or Grafana historical queries are exposed.
- On `RAY_HTTP_ERROR`, verify network access and the same URL in the Dashboard.
  On `RAY_SCHEMA_ERROR`, report a version/response mismatch instead of treating
  missing data as zero. On response-cap errors, reduce `--lines` for log content
  or use `--glob` for log filenames; reduce Actor `--page-size`; use Dataset
  `--job-id`/`--mode` before a job-scoped request. Local filters and pagination
  cannot shrink upstream Jobs/Nodes/Serve or job-scoped Dataset snapshots.

## References

- Read [invocation](../../invocation.md) for installation, global option
  placement, and HTTP tracing.
- Read [troubleshooting](../../troubleshooting.md) for generic
  authentication, network, and skill mirror sync failures.
