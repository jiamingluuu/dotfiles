# Douyin AI commands

All resource identifiers are named flags; positional IDs are not supported.

```bash
bytedcli douyin-ai space list [--keyword <text>]
bytedcli douyin-ai project list --workspace-id <id> [--page <n>] [--page-size <n>] [--keyword <text>] [--only-mine] [--sort <created|updated>]
bytedcli douyin-ai project deploy --channel playlet-creative (--url <project-url>|--project-id <id>) [--yes]
bytedcli douyin-ai operation-data get --workspace-id <id> --agent-id <id> [--channel <channel>] [--scene <text>] [--start <ISO8601>] [--end <ISO8601>] [--stat-key <key>...] [--group-by <field>...] [--stats-config <json>] [--query-param <json>]
bytedcli douyin-ai trace get --workspace-id <id> --agent-id <id> --trace-id <id> [--event-time <ISO8601>] [--ai-cluster <name>]
bytedcli douyin-ai trace list --workspace-id <id> --log-id <id> [--agent-id <id>] [--ai-cluster <name>] [--all]
```

Use `trace get` when one Trace ID and its Agent ID are already known. Use `trace list` when one LogID may correspond to a main Agent plus child Agents or child Workflows:

```bash
bytedcli -j douyin-ai trace list --workspace-id demo-space --log-id demo-log
bytedcli -j douyin-ai trace list --workspace-id demo-space --log-id demo-log --agent-id demo-agent
bytedcli -j douyin-ai trace list --workspace-id demo-space --log-id demo-log --all
```

`--workspace-id` selects the tenant boundary in which the LogID is queried; a LogID is not a global authorization or routing key. `--agent-id` is optional and narrows the result to one Agent or Workflow. Without it, the command follows every QueryTrace page, deduplicates candidates, and preserves backend order in a flat `traces[]` array.

The default safety limit is 100 deduplicated candidates. If discovery observes more than 100, the command fails with `DOUYIN_AI_TRACE_LIMIT_EXCEEDED` before fetching any detail and the hint recommends `--all`; it never returns a silently truncated success result. `--all` removes only this count limit. Full-detail requests still use concurrency four.

Text mode prints every candidate summary. JSON mode returns every successful full trace plus safe structured errors for failed details. When some details fail, the top-level status is `partial_success`, `error` remains `null`, and the process exits with code 1. If every detail fails for authentication, the command preserves `AUTH_REQUIRED`; other all-detail-failed results use `DOUYIN_AI_TRACE_DETAIL_ERROR`. No candidates use `DOUYIN_AI_TRACE_NOT_FOUND`.

Deploy a project to the short-drama creative platform:

```bash
bytedcli douyin-ai project deploy --channel playlet-creative --project-id <id>
bytedcli douyin-ai project deploy --channel playlet-creative --url 'https://douyin-ai.bytedance.net/project/<id>?space=%22douyin_series%22' --yes
```

`playlet-creative` is currently the only supported deployment channel. The workspace is fixed to `douyin_series`, so this command does not accept `--workspace-id`. Without `--yes`, it reads the project and channel state and prints the deployment plan without sending the write. After a successful write it performs one channel readback; a failed or unconfirmed readback is reported as a warning and is not retried.

## Ordinary Agent

Find knowledge-base candidates before binding an ID (read-only; same-name matches remain separate):

```bash
bytedcli --no-auto-upgrade --json douyin-ai knowledge-base list --workspace-id demo-space --keyword 'Demo knowledge'
bytedcli --no-auto-upgrade --json douyin-ai knowledge-base get --workspace-id demo-space --knowledge-base-id demo-dataset
```

List supports `--scope all|personal|team|standard|douyin`, `--page` (1) and `--page-size` (20). Results are platform-visible within the requested workspace, not a global uniqueness guarantee. Keyword search does not auto-select, bind or edit Prompt; paginate when `has_more` is true. Default discovery includes Space type 4. Detail returns metadata/schema/version summaries, not document contents.

`knowledge-base data list` is read-only and reports the row ids that `data delete` needs:

```bash
bytedcli --no-auto-upgrade --json douyin-ai knowledge-base data list --workspace-id demo-space --knowledge-base-id demo-dataset --page-size 50
```

Each row carries a `knowledge_id` and the owning `document_id`, alongside the knowledge base's schema columns. This is the only way to discover those two ids: a row created by `data create` is otherwise known only from that command's own receipt, and a row created in the platform UI has no CLI source at all. `--document-id` defaults to `0`, which lists rows across every document in the knowledge base; pass an owning document id to narrow the listing. Rows are paged with `--page` and `--page-size`, and `page_count` means the rows returned in this page. A row whose owning document the platform does not report shows `document_id` as null (text mode: `(not reported)`) with a warning naming it, because such a row cannot be targeted by `data delete`. A column whose value the gateway did not stringify is kept and flagged `unverified` rather than presented as an exact value.

`knowledge-base data create` and `knowledge-base data delete` change one row per invocation; batch input is not supported:

```bash
bytedcli --no-auto-upgrade --json douyin-ai knowledge-base data create --workspace-id demo-space --knowledge-base-id demo-dataset --table-content '{"demo_field":"demo value"}'
bytedcli --no-auto-upgrade --json douyin-ai knowledge-base data create --workspace-id demo-space --knowledge-base-id demo-dataset --table-content '{"demo_field":"demo value"}' --yes
bytedcli --no-auto-upgrade --json douyin-ai knowledge-base data delete --workspace-id demo-space --knowledge-base-id demo-dataset --document-id 1000000000000000001 --knowledge-id 1000000000000000002 --yes
```

Without `--yes`, the schema is read and the validated request is printed without sending a write. The write key is resolved from `--knowledge-base-id`; `--knowledge-base-key` only asserts that resolved value and never overrides it, so a mismatch fails before any request. Every `--table-content` field must exist in the knowledge base schema, values must be strings, and content is sent exactly as given. A knowledge base that reports no field schema is refused rather than written to blind. Take both `data delete` ids from `data list`: it reports each row's `knowledge_id` and owning `document_id` together. `data create` reports the row id the platform echoes back, and creates the row under the document sentinel `0`, so a row this CLI just created can also be removed with `--document-id 0`. Deleting is not reversible from the CLI, and deleting a row that no longer exists is rejected with `business_code -1`. Rows are only readable page by page: success means the platform accepted the write, not that the row content was verified. A failed session is never retried automatically for a write.

Main-repository commands for ordinary Agent (`appMode=0`), separate from Workflow and plugin commands:

```bash
bytedcli --no-auto-upgrade --json douyin-ai agent get --workspace-id demo-space --agent-id app_demo
bytedcli --no-auto-upgrade douyin-ai agent export --workspace-id demo-space --agent-id app_demo --output agent.json
bytedcli --no-auto-upgrade --json douyin-ai agent update --workspace-id demo-space --agent-id app_demo --file agent.patch.json
bytedcli --no-auto-upgrade --json douyin-ai agent update --workspace-id demo-space --agent-id app_demo --file agent.patch.json --yes
bytedcli --no-auto-upgrade --json douyin-ai agent deploy --workspace-id demo-space --agent-id app_demo
bytedcli --no-auto-upgrade --json douyin-ai agent deploy --workspace-id demo-space --agent-id app_demo --yes
# Bind reviewed preview to execution
bytedcli --no-auto-upgrade --json douyin-ai agent deploy --workspace-id demo-space --agent-id app_demo --plan-out agent.deploy.plan.json
bytedcli --no-auto-upgrade --json douyin-ai agent deploy --workspace-id demo-space --agent-id app_demo --plan agent.deploy.plan.json --yes
```

All four accept `--url <agent-url>` instead of both target flags; do not combine them. Update requires exactly one of `--file <path>` or `--stdin`. Export requires `--output`, never overwrites an existing file, and prints only file metadata. No `--force`, format selector, inline Prompt, historical version or deploy patch is supported. Get reports `lock_status=not_checked`, not an unlocked guarantee.

Deploy `--plan-out <file>` is preview-only and mutually exclusive with `--plan` and `--yes`; it creates an exclusive 0600 file after validation. `--plan <file>` constrains another preview or `--yes` execution, with the target still supplied explicitly. Direct `--yes` remains supported. The strict 64 KiB baseline contains schema_version=1, fingerprint_version=agent-deploy-v1, workspace_id, agent_id, graph_instance_id, graph_instance_key, draft_version, content_sha256 and publish_input_sha256. The latter hashes all ModelConfig mapping inputs including the resolved app.name fallback, not wire JSON bytes; its fingerprint version is coupled to the mapper/comparison rules. Both hashes retain only the documented WSOS signature normalization. Unknown/duplicate fields and invalid schema/hash versions reject; do not hand-write or modify baseline values. The baseline is not a patch or an instruction to publish a historical draft. Identity/content/name drift or disappearance rejects before no-op and is checked again after acquiring the lease. Resource/reference validation still runs; these checks are not atomic server CAS. Preview output includes confirmation_baseline and, when saved, plan_output file metadata under plan.changes.

Input is `{ "schema_version": 1, "base"?: { "workspace_id": string, "agent_id": string, "draft_version": number, "content_sha256": string }, "patch": { ... } }`. Use actual export base values, never invented hashes; stale target/version/hash fails. Export is directly accepted as update input. Only the following patch groups are allowed:

| Group | Writable input |
| --- | --- |
| `prompt` | `{doc: nativeRichTextDoc}`; no string doc, text or Markdown; `prompt_text` is derived |
| `model` | `id/key/tenant` together for identity changes; `temperature` [0,1], nonnegative safe-integer `token_limit/context_round_limit`, `thinking_type` empty/enabled/disabled/auto |
| `tools` | `{bindings: [{tool_id: string, enabled?: boolean}]}`; details come from checked resources |
| `knowledge` | `datasets?: [{id, top_k?: decimalString, score?: number, params?: object\|null\|"", multi_channel_query_params?: object\|object[]\|null\|"", rank_config?: object\|null\|""}]`, `force_recall_qa_record?: boolean\|null` |
| `inputs` | `params?: Record<string,string>\|null`, `forms?: [{variable, type: 1\|2\|3\|4, description?, label?, default?: string, required?: boolean}]\|null` |

Omitted fields remain unchanged; declared objects merge by property. Arrays replace the entire editable list, and `[]` explicitly clears it. Omitted writable properties inside replacement array items are removed, not inherited. Forms replace custom definitions only; built-ins remain. Params merge by key; null clears the map. Only explicitly nullable fields accept null. Native rich-text documents replace as a whole; mention `attrs.raw` uses current editor fields, while obsolete aliases are inert preserved extras. Unknown/forbidden business fields reject the whole input. Final references/resources are checked, permitting Prompt + bindings + variables in one patch; metadata and system forms are not writable.

Dataset JSON configuration fields preserve the platform's exact empty-string sentinel on export/update. Only multi_channel_query_params also accepts arrays of JSON objects for structured retrieval channels. Empty string, null, empty object and empty array remain distinct; nonempty JSON text strings and whitespace-only strings are not accepted as public input.

Dataset `top_k` uses decimal text publicly (0 through 9223372036854775807) and JSON integers on new writes, with lossless projection of platform numbers. Unchanged values retain their API-visible representation; existing settings inside `params` are not updated implicitly. Only newly added IDs receive type/capability-based initialization and proven protocol defaults. Supplying any explicit retrieval field, including null and empty strings, bypasses automatic retrieval initialization as a group. Space may legitimately have an empty embedding key; unavailable initialization evidence fails closed. Relative-date defaults depending on browser timezone require explicit retrieval configuration.

Knowledge mentions require consistent dataset.id/detail.id and a detail.key matching the resolved resource. A refVariable must be retrievable and not excluded by the final binding's Fixed FilterFieldList. Names are not identities and a binding does not require a Prompt mention.

An exact empty input-form default string is the platform's unset-default representation and remains unchanged, not converted to zero or false. Nonempty defaults must match the variable type; whitespace-only numeric/boolean defaults are invalid.

Plans/results expose `preservation_scope=api_visible_config`: only existing API-visible configuration is preserved and checked; server save/publish transformations are unchanged. Comparison hashes normalize only refreshed expire/timeStamp/sign values on strictly recognized signed relative WSOS icon URLs, retaining the full path/OID, parameter presence/count, other parameters and fragment. Unknown formats compare unchanged; the original content and submitted icon value are never rewritten. Every other mismatch remains an error. The repository guide `docs/domains/douyin-ai/agent-config.md` contains executable per-group and combined examples, the full forbidden-field table and acceptance evidence index.

Update only saves a draft. Deploy publishes the whole current publishable draft, including prior web edits, with `test_run_validated=false`, no automatic trial and no trial Trace. Default previews do not acquire or refresh locks. Execution uses a lease and locked reread, not atomic server CAS. Nonzero exits after submission retain uncertain/mismatched receipts in `data.result`; successful writes with lock warnings use `partial_success`. Inspect and read back; never blindly replay update/deploy.

Deploy previews compare current online content with the draft, label first publication explicitly, and mark unavailable comparisons rather than inventing an empty diff. Write receipts separate `submission_acknowledged` from `verification.status` (matched/mismatch/unconfirmed). Diagnostics include read attempts, matching identity evidence and at most 20 safe difference paths plus counts; values and dynamic keys are withheld. Acknowledgement alone never proves saved/published content, and an uncertain response does not authorize replay.

An unacknowledged submission may retain submission_diagnostic with a sanitized stage/code, optional status_code and bounded schema issue paths/codes/input types. It never includes messages, response bodies or field values. A matched publication can remain success with submission_acknowledged=false and this diagnostic; the diagnostic alone does not trigger partial_success or authorize retry.

## Workflow

Create a draft Workflow from the built-in input-to-output template:

```bash
bytedcli douyin-ai workflow create --workspace-id <id> --name <name> [--description <text>] [--yes]
```

Without `--yes`, `workflow create` only prints the draft plan and sends no remote request. `--workspace-id` is a workspace identifier returned by `bytedcli douyin-ai space list`; it is not a fixed enum. The name is required and limited to 20 Unicode code points; the optional description is limited to 140 Unicode code points.

Workflow export, import, and deploy accept either `--url`, or both `--workspace-id` and `--workflow-id`:

```bash
bytedcli douyin-ai workflow export --workspace-id <id> --workflow-id <id> [--output <path>] [--force]
bytedcli douyin-ai workflow import --workspace-id <id> --workflow-id <id> (--file <path>|--stdin) --force [--yes]
bytedcli douyin-ai workflow deploy --workspace-id <id> --workflow-id <id> [--yes]
```

`workflow deploy` reads and plans the latest publishable draft by default. Pass `--yes` to acquire the edit lock and publish it. The command does not send a test-run Trace, so it reports `test_run_validated=false` and does not validate a recent successful test run.

Skill:

```bash
bytedcli douyin-ai skill upload --workspace-id <id> [--skill-id <id>] --zip <path> [--publish] [--publish-channel <channel>...] [--detail-visibility <visibility>] [--can-download|--no-can-download] [--display-name <text>] [--description <text>] [--yes]
bytedcli douyin-ai skill download --workspace-id <id> --skill-id <id> [--status <draft|published>|--version <version>] [--output <path>]
bytedcli douyin-ai skill permission list --workspace-id <id> --skill-id <id>
bytedcli douyin-ai skill permission update --workspace-id <id> --skill-id <id> --email <address>... [--role <user|editor|admin>] [--applicant <email>] [--yes]
bytedcli douyin-ai skill permission delete --workspace-id <id> --skill-id <id> --email <address>... [--applicant <email>] [--yes]
```

Plugin:

```bash
bytedcli douyin-ai plugin create [--dir <path>] [--name <name>] [--display-name <text>] [--description <text>] [--force]
bytedcli douyin-ai plugin upload --workspace-id <id> [--plugin-id <id>] (--dir <path>|--zip <path>) [--display-name <text>] [--description <text>] [--package-display <mode>] [--can-download|--no-can-download] [--ai-cluster <name>] [--yes]
bytedcli douyin-ai plugin deploy --workspace-id <id> --plugin-id <id> [--change-note <text>] [--ai-cluster <name>] [--yes]
bytedcli douyin-ai plugin get --workspace-id <id> --plugin-id <id> [--ai-cluster <name>]
bytedcli douyin-ai plugin validation execute --workspace-id <id> (--dir <path>|--zip <path>) [--publish] [--ai-cluster <name>] [--yes]
bytedcli douyin-ai plugin debug execute --workspace-id <id> [--plugin-id <id>] --message <text> [--upload] [--dir <path>|--zip <path>] [--model-name <name>] [--conversation-id <id>|--new-conversation] [--output-dir <path>] [--timeout-ms <ms>] [--poll-interval-ms <ms>] [--display-name <text>] [--description <text>] [--package-display <mode>] [--can-download|--no-can-download] [--ai-cluster <name>] [--yes]
```

`plugin debug execute --output-dir` writes returned inline or downloadable artifacts below the selected directory. Artifact paths are sanitized before local writes.

No command, flag, or value aliases are supported. Semantic values are:

- Project sort: `created`, `updated`.
- Operation channel: `dybno`, `agent-center`, `agent-square`, `internal-debug`, `governance`, `openapi`, `lark-bot`, `hive`, `basic-platform`, `web`, `h5`, `group-chat`, `square-online`, `avatar`, `skill-agent`.
- Skill publish channel: `space`, `flower-search`, `flower-bottom-bar`, `flower-comment`, `flower-im`.
- Skill detail visibility: `all`, `skill-md`, `hidden`.
- Plugin package display: `full-directory`, `readme-only`, `hidden`.
- Skill role: `user`, `editor`, `admin`.

Time flags require ISO8601 values with an explicit timezone, for example `2026-08-02T12:00:00+08:00`.
