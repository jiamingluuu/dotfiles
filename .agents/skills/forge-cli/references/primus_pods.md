# Primus training pods — executor attempts, lifecycle, and regional routing

Use this reference whenever a request involves training pod discovery, executor
state, executor attempt/version selection, entering a training container, or a
pod/process-level kill operation. This routing decision comes before any
Forge webshell command.

## Contents

- [Source of Truth](#source-of-truth)
- [Logical executor versus concrete attempt](#logical-executor-versus-concrete-attempt)
- [Regional default paths](#regional-default-paths)
- [Capability boundary and handoff](#capability-boundary-and-handoff)
- [Investigation flow](#investigation-flow)
- [Hard stops for agents](#hard-stops-for-agents)

## Source of Truth

**Primus History is the Source of Truth** for:

- the set of AM and executor pods belonging to a training application;
- the mapping from a logical executor to its concrete attempts/versions;
- lifecycle state such as `STARTING`, `RUNNING`, or released/terminal states;
- selecting the concrete live pod for diagnosis or an operation.

The read-only commands `forge job primus-app get`, `forge job primus-role list`,
and `forge job primus-pod list/get` expose a current Primus metadata snapshot.
Results normally report `source: "standalone_primus_cli"`; a job-derived
successful empty result may fall back to the selected stage's legacy
`newStatus.json` URL and then reports `source: "legacy_primus_new_status"`. Their role/pod output explicitly reports
`lifecycle_authority: "primus_history"`. Use them only when that snapshot or an
exact metadata row is the requested artifact; do not substitute them for the
History workflow below when reconstructing pod inventory, expanding attempts,
judging lifecycle state, or selecting a live target.

The two sources do not carry identical per-pod fields. Under
`source: "standalone_primus_cli"` the per-pod stdout / stderr / syslog /
SysProbe link fields and the `streaming_info`, `hdfs_latency`, `throughput`,
and `busy` fields are not supplied and are omitted from the output; the legacy
`newStatus.json` fallback still populates them. No Vela link is supplied
either, but office runtimes still synthesize `links.vela` from `pod.host_name`
as described below, so use it when it is present. Treat all of
these as optional: key off their presence rather than expecting them, and read
`source` before comparing two results field by field. For streaming throughput
figures, use the training metrics commands instead of the pod snapshot.

The pod commands adapt their explicit `links` for navigation from the caller's
runtime: on `network=office`, production hostname suffixes are rewritten to the
selected i18n/EU-TTP/US-TTP office suffix while URL ports, paths, queries, and
fragments are preserved. This is display-only. The Primus request endpoint and
the job-derived top-level `primus_history_url` remain original metadata, so the
History authority and audit handoff below are unchanged.

When the source row has no Vela URL and has a non-empty `host_name`, office
runtime results synthesize a direct Vela one-machine navigation link for all
four sites: `vela.byted.org` for CN, `vela.tiktok-row.net` for i18n,
`vela-ttp-eu.tiktok-row.net` for EU-TTP, and
`vela-ttp-us.tiktok-row.net` for US-TTP. Production runtime results do not
synthesize this link.

Use the Primus History URL returned by the selected stage's metadata or
supplied by the user. Keep the target `stage_id` attached to every subsequent
lookup, log query, handoff, and operation; a retry stage is a different
execution instance even when the `job_id` is unchanged.

```bash
# A specific historical or retry stage
forge job meta get --job-id <id> --stage-id <stage-id> --site <site>

# The latest stage, only when no specific stage is intended
forge job meta get --job-id <id> --site <site>
```

The output field is named `latest_stage` in both forms. When `--stage-id` was
passed, verify that `latest_stage.stage_id` equals the requested value; do not
silently continue with the job's latest stage. Use
`latest_stage.links.primus_history_original` as the **original History URL**
for audit and handoff, and use `latest_stage.links.primus_history_access` for
navigation. Treat both paths and queries as opaque and never synthesize a
History URL from a job ID or a general hostname table. On an older binary that
does not return `latest_stage.links`, preserve
`latest_stage.primus_history_url` as the original and derive the access URL
with the compatibility rule below.

Derive the **access History URL** with this site-aware rule:

- For `--site us-ttp`, when the original URL hostname contains
  `tiktok-usts.net`, replace only that host substring with `tiktok-us.net`.
  Preserve the scheme, port, path, and query. The original US-TTP hostname is
  known to be unreachable from the corporate network; this is the same
  resolver rule used by Forge's Primus log and webshell integrations.
- For every other site or hostname, the access URL is the original URL
  unchanged. Do not invent another rewrite.

`latest_stage.links.primus_bdee` and `latest_stage.links.dorado_bdee`, when
present, are service-provided BDEE jump targets. Surface the matching link when
the requested compliant operation belongs there. Do not infer or synthesize a
missing BDEE URL.

Then use the Primus History access path already available in the current
environment:

1. Open/query the access History URL and select the relevant role.
2. Inspect all lifecycle states to enumerate every attempt/version.
3. Filter to `RUNNING` when selecting the current live attempt.

If the current environment cannot read Primus History, report that limitation
and surface the selected `stage_id`, original History URL, and derived access
History URL for the user. Do not introduce another CLI dependency or substitute
`forge job webshell list`. Webshell target discovery is a convenience for an
explicitly requested Forge webshell flow; it is not authoritative pod inventory
and cannot establish which attempt is current.

## Logical executor versus concrete attempt

A logical executor name does not identify one immutable pod. For example:

```text
logical executor: executor_stream_395
attempts:         executor_stream_395_0
                  executor_stream_395_1
                  executor_stream_395_2
```

The suffix represents a concrete attempt/version. Retries and replacements can
leave older attempts visible after a newer one starts. Apply all of these rules:

1. Inspect all lifecycle states when reconstructing history or investigating
   restarts.
2. Expand every row sharing the logical executor prefix; do not collapse them
   into one `executor_stream_395` row.
3. Filter to `RUNNING` before a live diagnosis or operation.
4. Target the concrete `RUNNING` attempt and its exact pod identity. Do not
   choose by largest suffix, first/last list position, launch timestamp alone,
   or a webshell-list row.
5. If no attempt is `RUNNING`, report that there is no current live target; do
   not fall back to a released attempt.
6. If multiple attempts unexpectedly appear `RUNNING`, report the ambiguity
   and stop before any mutating action until Primus state or the intended target
   is clarified.

## Regional default paths

| Target control plane | Default diagnosis and operation path |
|---|---|
| RoW / i18n (`--site i18n`) | Locate the concrete attempt in Primus History and use Primus logs for read-only diagnosis. Native `forge job sdp exec` runs one compliant command in the exact pod, including current Primus-on-Godel (`nj-*`) jobs; it needs the CN browser SSO session plus an i18n ByteCloud user JWT. |
| EU/TTP (`--site eu-ttp` / `--site us-ttp`) | Default to **Primus History** and `forge job log query --log-type primus`. On the office network, the command can use the **Footprint-backed read path** with the CN browser SSO session. Do not default to Forge webshell for pod discovery, state judgment, or container execution. |
| cn (`--site cn`) | Primus History remains authoritative for pod/attempt/lifecycle facts. Prefer normal Primus log paths for read-only diagnosis; Forge webshell remains an explicit, confirmed supplemental path only. |

## Capability boundary and handoff

The `forge` CLI exposes job/stage metadata, Primus log queries, native RoW SDP
one-shot execution, and the explicit Forge webshell commands documented in
[webshell.md](webshell.md). TTP office Primus content queries and downloads may
use Footprint internally; there is no separate public Footprint command, and
Footprint is not an inventory or lifecycle source. EU/TTP and CN container
entry or pod/process mutation remain regional operational handoffs.

For RoW Primus containers (including current Primus-on-Godel `nj-*` jobs),
`forge job sdp exec` creates the SDP session by following that pod's
service-provided webshellauth URL with `type=sdp` appended: webshellauth
resolves the pod host IP and container id server-side and builds the compliant
`T_GENERAL` SDP session, then redirects to the gpcp detail page. The caller
supplies Forge/stage context and one explicit target selector; Forge derives
only the exact pod's webshellauth URL from the selected stage's Primus History
data and never constructs an IP, container id, or URL itself.

The values written as `<...>` below are placeholders, not verified live jobs:

```bash
# Exact RUNNING executor attempt from the latest stage
forge --site i18n job sdp exec \
  --job-id <forge-job-id> \
  --role <role> \
  --executor-id <exact-running-executor-id> \
  --command "tail -n 200 <approved-log-path>"

# Selected stage and AM target
forge --site i18n job sdp exec \
  --job-id <forge-job-id> --stage-id <stage-id> \
  --am \
  --command-file <single-line-command-file>
```

SDP needs two credentials: the CN browser SSO session (webshellauth delegates
OAuth2 to `sso.bytedance.com` for every region — a human terminal can use
`forge auth login --session --site cn`, an agent the non-blocking `--begin --session` / `--complete` flow; an account whose QR scan Lark rejects with "Login method isn't allowed" uses `--session-method interactive-browser` instead) to create the session, and an i18n
ByteCloud **user** JWT for the SDP WebSocket. AK/SK application identity is
rejected, and an injected JWT must explicitly identify a human-user credential
type. The container OS user is server-determined by webshellauth; there is no
`--user`, `--region`, or IP/container flag. Use only a non-interactive,
bounded, single-line command. Pipes are supported, while newlines, `;`, `&&`,
`||`, and background `&` are rejected. SDP's server whitelist remains
authoritative. The result's `completed` field is authoritative; `exit_code` is
always null because the SDP protocol does not report the remote process exit
status. Preserve the returned `sdp_job_id` and `sdp_detail_url` when execution
is incomplete or needs audit.

If the target is not i18n, the selected stage has no authoritative History URL,
the exact pod has no service-provided webshellauth URL, no exact executor
attempt is `RUNNING`, or multiple matching attempts are `RUNNING`, stop before
session creation and use this handoff:

1. Complete the supported read-only steps first: resolve the selected
   job/stage metadata, preserve the returned
   `latest_stage.links.primus_history_original` and
   `latest_stage.links.primus_history_access` (or the older raw-field
   compatibility projection), and query available Primus logs through
   `forge job log` with the same `stage_id` when useful.
2. Stop before container entry or any mutating action. State explicitly that
   the requested target/region is unsupported or unresolved; do not invent an
   SDP target or Primus command and do not fall back to Forge webshell.
3. Hand the user or regional operator the exact continuation context that is
   known: `site`, `job_id`, `stage_id`, original and access History URLs, role,
   logical executor, concrete `RUNNING` attempt/pod, requested command or kill
   scope, and the relevant log evidence. Mark any unresolved field as
   unresolved rather than guessing it.
4. For an unresolved RoW target (no exact `RUNNING` attempt, no
   service-provided webshellauth URL, or an OG/BPM deny), do not blindly retry
   `forge job sdp exec`; confirm the Primus History target first, then continue
   through `latest_stage.links` if it stays unresolved.
   For EU/TTP/CN, continue through the established regional operation path or
   the supported `forge job log query` workflow. If Primus History itself is not
   reachable, surface the selected stage plus both History URL forms as the
   first handoff items.

Use this handoff wording:

```text
Current agent environment has no supported <SDP / Primus>
entrypoint for this action. Continue in the established <region> workflow
using:
site=<site>
job_id=<job-id>
stage_id=<stage-id-or-unresolved>
primus_history_url_original=<metadata-or-user-supplied-url>
primus_history_url_access=<site-resolved-url>
role=<role-or-unresolved>
logical_executor=<logical-id-or-unresolved>
running_attempt=<concrete-attempt-or-unresolved>
requested_action=<diagnosis-or-kill-scope>
```

`forge job kill` is a separate job-level lifecycle command. Do not confuse an
explicit request to stop the whole Forge job with a pod/process-level kill
inside one executor. Conversely, do not turn a request about one bad attempt
into a whole-job kill.

## Investigation flow

1. Resolve the target site and stage. If a `stage_id` is specified or selected,
   pass it to
   `forge job meta get --job-id <id> --stage-id <stage-id> --site <site>` and
   verify the returned `latest_stage.stage_id`; otherwise intentionally use the
   latest stage.
2. Preserve `latest_stage.links.primus_history_original` and navigate with
   `latest_stage.links.primus_history_access`. Only on an older binary without
   these fields, derive the access URL with the single approved US-TTP host
   rewrite above; leave every other URL unchanged.
3. Open/query the access URL through the current environment's existing Primus
   History access path, select the relevant role, and inspect all lifecycle
   states.
4. Group concrete attempts by logical executor and identify the current
   `RUNNING` attempt.
5. For logs, use Primus log with the same `stage_id` or the region's supported
   Footprint-backed log chain before considering container entry.
6. If a live container operation is necessary, follow the regional route only:
   RoW uses native `forge job sdp exec` on the exact History-resolved AM or
   `RUNNING` executor attempt (including current `nj-*` jobs). EU/TTP/CN targets
   stay on their supported metadata-link/Primus/log or operational handoff path.
   If no supported exact target or entrypoint is available, use the capability
   handoff above.
7. Consider [webshell.md](webshell.md) only if the user explicitly requests
   Forge webshell and confirms that the environment and access path are usable.

## Hard stops for agents

- Do not run `forge job webshell list` merely because the user said pod,
  executor, container, attempt, lifecycle, status, diagnose, or kill.
- Do not drop an explicitly supplied or selected `stage_id` and silently use
  the job's latest stage.
- Do not replace the original History URL in audit or handoff context. For
  US-TTP access, apply only the recognized `tiktok-usts.net` ->
  `tiktok-us.net` hostname rewrite and preserve every other URL component.
- Do not infer executor health from a logical executor name without expanding
  its attempts.
- Do not operate on a terminal/released attempt when there is a different
  `RUNNING` attempt.
- Do not bootstrap a cn webshell browser session as part of ordinary pod
  discovery or log diagnosis.
- Do not invoke or require `bytedcli` for Forge SDP execution.
- Do not invent SDP, Primus exec/kill, or Footprint commands when the current
  environment exposes no supported entrypoint; use the explicit handoff.
- Do not accept a caller-supplied SDP IP, container id, or webshellauth URL, or
  infer them from a Forge job ID, pod name, hostname, or DNS. Forge derives only
  the exact pod's webshellauth URL from the selected stage's service-provided
  Primus History data; webshellauth resolves the IP and container id and picks
  the OS user server-side.
- Do not form an automatic `forge job webshell list -> forge job webshell exec`
  workflow.
