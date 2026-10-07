# TAE / AI PaaS workflow

Prefer first-class `bytedcli tae` commands for Agent, Sandbox, MCP Server, and MCP Tool operations. Use raw API passthrough only when a capability is not covered by the command surface and the user has authorized the action.

## Safety and scope

- Deleting tools, updating MCP servers/tools, and releasing revisions are externally visible; confirm user authorization first.
- Store scratch JSON, generated schemas, and reports under `/tmp/`, not in a source workspace.
- Do not send internal payloads or IDL content to external services.

## Site selection

Use the default `--site` unless the user gives a TAE page from another ByteCloud site or explicitly asks for one.

```bash
bytedcli tae mcp server search --keyword demo-server
bytedcli --site i18n-tt tae mcp server search --keyword demo-server
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli tae mcp server search --keyword demo-server
```

If authentication fails after switching sites, run `bytedcli auth login --site <site>`.

## Sandbox runtime

Native `bytedcli tae sandbox session`, `bash`, `exec`, `process`, `fs`, `port`, `request`, and `region list` cover controlplane/sandboxd. Use the bytedance-tae skill reference `references/sandbox-runtime.md` for authentication, command options, streaming and migration. Platform `sandbox list/search/get` retain their resource-query semantics.

## First-class CLI commands

Use search commands for keyword lookup. Use list commands for unfiltered or explicitly filtered collections.

```bash
bytedcli tae mcp server search --keyword demo-server
bytedcli tae mcp server list --limit 20
bytedcli tae mcp server get --server-id demo-server-id
bytedcli tae mcp server create --payload '{"name":"demo-server"}'
bytedcli tae mcp server update --server-id demo-server-id --payload '{"name":"demo-server"}'
bytedcli tae mcp server release --server-id demo-server-id

bytedcli tae agent search --keyword demo-agent
bytedcli tae agent list --limit 20
bytedcli tae agent get --agent-id demo-agent-id

bytedcli tae sandbox search --keyword demo-sandbox
bytedcli tae sandbox list --limit 20
bytedcli tae sandbox get --sandbox-id demo-sandbox-id

bytedcli tae mcp tool list --server-id demo-server-id
bytedcli tae mcp tool get --server-id demo-server-id --tool-id demo-tool-id
bytedcli tae mcp tool create --server-id demo-server-id --payload '{"tool_name":"demo_tool"}'
bytedcli tae mcp tool update --server-id demo-server-id --tool-id demo-tool-id --payload '{"tool_input_schema":"{}"}'
bytedcli tae mcp tool delete --server-id demo-server-id --tool-id demo-tool-id

# Discover valid BAM versions and RPC method names before importing.
bytedcli bam version list --psm example.service.api --cluster default
bytedcli bam method list --psm example.service.api --cluster default --version 1.0.0 --ep-type rpc

# BAM RPC import defaults to dry-run and returns every final create payload.
bytedcli tae mcp tool import-bam \
  --server-id demo-server-id \
  --psm example.service.api \
  --version 1.0.0 \
  --methods GetDemo,CreateDemo \
  --descriptions-json '{"GetDemo":"Get one demo record by id.","CreateDemo":"Create one demo record."}'

# Create selected tools after reviewing the preview.
bytedcli tae mcp tool import-bam \
  --server-id demo-server-id \
  --psm example.service.api \
  --version 1.0.0 \
  --methods GetDemo,CreateDemo \
  --descriptions-json '{"GetDemo":"Get one demo record by id.","CreateDemo":"Create one demo record."}' \
  --yes

# Create all selected tools, then release only when every create succeeds.
bytedcli tae mcp tool import-bam \
  --server-id demo-server-id \
  --psm example.service.api \
  --version 1.0.0 \
  --methods GetDemo,CreateDemo \
  --descriptions-json '{"GetDemo":"Get one demo record by id.","CreateDemo":"Create one demo record."}' \
  --yes --release

bytedcli tae mcp schema generate --idl-file /tmp/service.thrift --method GetSomething --output /tmp/schema.json
bytedcli tae mcp schema update --server-id demo-server-id --dry-run --report /tmp/schema_report.json
bytedcli tae mcp schema update --server-id demo-server-id --report /tmp/schema_report.json --release
```

Common CLI options: `--env prod`, `--region-id bytedance`, and global `--json` / `--site <site>`.

`sandbox list/search` return only your own sandboxes by default; add `--all` for every sandbox, or `--search-type own|subscribe|all` to choose explicitly. For these commands `--env` filters the sandbox environment (default `prod`), and `--limit` defaults to 20 (10 for search). JSON `data` is the sandbox array.

`import-bam --methods` accepts repeatable or comma-separated method names. Select `--version` from `bam version list`, and select method names from `bam method list --ep-type rpc`; the import command revalidates that the version exists before querying API details. The command uses the same TAE BAM proxy and payload defaults as the web workflow. The web form requires a non-empty model-facing description, so every method submitted with `--yes` must also have a non-empty entry in `--descriptions-json`; dry-run does not require descriptions. A partial create failure prevents release and returns `TAE_MCP_BAM_PARTIAL_FAILURE` with per-method results; do not blindly retry methods already reported as `created`.

When using bytedcli through MCP `--all-tools`, pass known options as structured tool fields instead of embedding them in `args`. For example, call `tae_api_post` with `site`, `path`, `payload`, `env`, and `regionId` fields. `site` is a bytedcli global option; do not put `--site` inside leaf `args` after `tae api post`.

## Connector access policy (domain allowlist)

A TAE Sandbox Connector egresses through an access policy that whitelists domains (and, optionally, ant-style paths). Changes are **two-stage**: a write only updates a server-side **draft**, and the draft activates only after a **release ticket is approved in BPM**. These commands call the Connector auth BFF (`/api/v1/tae/ai/auth`) with the bytedcli ByteCloud JWT and an `x-resource-account: public` header; no hand-rolled auth is needed.

The tenant owns one **dedicated (custom) policy group** (key `tae:custom:tenant:*`, scenario `tae.intranet.limit`). Platform **system groups** (`system.inner.limit`, `system.out.limit`) are shared and read-only; writes that resolve to a system group (including an explicit `--group-id` pointing at one) are rejected.

Related but different surfaces — do not confuse them:

- `bytedcli tae connector ...` (this section) manages the **tenant-level Connector** network allowlist (`--connector-id`). It is shared by many sandboxes, and changes go through a draft → BPM release ticket.
- `bytedcli tae sandbox ...` drives a **single running sandbox instance** (`--session-id`, controlplane/sandboxd + ZTI): shell, processes, files, ports. It does not configure egress domains.
- `bytedcli aiosandbox instance policy list --sandbox-id <id>` is a **read-only** view of the policy groups that apply to one sandbox instance (FaaS/sandbox-instance control plane). It cannot list domains/paths or edit the allowlist; use `tae connector domain list` for that.

```bash
# List the tenant-dedicated group's whitelisted domains and their allowed paths.
bytedcli tae connector domain list --connector-id connector-demo0001
# Add --all to also include the shared system groups (read-only context).
bytedcli tae connector domain list --connector-id connector-demo0001 --all

# Add a domain to the draft. Default path '/**' + method '*' allows the WHOLE domain.
# Writes default to dry-run and print the final payload; add --yes to commit the draft.
bytedcli tae connector domain add --connector-id connector-demo0001 --domain demo.example.com
bytedcli tae connector domain add --connector-id connector-demo0001 --domain demo.example.com --yes

# Allow only a path prefix on an existing domain (adds an action instead of a new policy).
bytedcli tae connector domain add \
  --connector-id connector-demo0001 \
  --domain demo.example.com \
  --path '/api/demo/**' \
  --method '*' \
  --name-cn 'demo api' \
  --yes

# Preview the release diff (added policies/actions, releasable, requires_approval).
bytedcli tae connector release preview --connector-id connector-demo0001

# Submit the release ticket. Defaults to dry-run; --yes submits and returns the BPM approval link.
bytedcli tae connector release create --connector-id connector-demo0001 --reason 'allow demo.example.com for sandbox egress' --yes

# Check a ticket's status and its BPM approval link.
bytedcli tae connector ticket get --ticket-id 123456
```

Rules and safety:

- `domain add` is idempotent per `(domain, method, path)`; an identical rule returns `already_exists` instead of creating a duplicate. Domains are normalized to lowercase before matching.
- Adding a domain already in the dedicated group appends a path **action**; a brand-new domain creates a **policy** that carries the action.
- `--path '/**'` allows **every** path and method on the domain. Prefer a narrow prefix (for example `/api/demo/**`) unless the whole domain is intended; this materially widens the sandbox egress surface.
- A draft commit does **not** affect running sandboxes. Run `release create` and wait for BPM approval; the command returns the ticket id and `bpm_link` for the approver.
- v1 intentionally does not remove rules (the draft delete endpoints are not wrapped). To roll back, use the TAE web console.
- Common options on every leaf: `--region-id bytedance` (default) and global `--json` / `--site <site>`. There is no `--env` on these commands — switch regions with the global `--site`. `domain add` also accepts `--name-cn` and `--description-cn`, and `release create` accepts `--publish-note`.

## Raw API passthrough

Use raw passthrough only after checking `bytedcli tae --help` and confirming there is no first-class command.

```bash
bytedcli tae api get --path /agents
bytedcli tae api update --path /agents/demo-agent-id --payload '{"name":"demo-agent"}'
```

Raw passthrough reuses bytedcli authentication and TAE request headers internally; agents should not hand-roll JWT header examples in normal workflows.

## Schema generation workflow

For RPC tools, prefer generating input schema from Thrift IDL:

1. Run `tae mcp schema generate` for one method or `tae mcp schema update --dry-run` for live tools.
2. Review the report under `/tmp/`.
3. Run `tae mcp schema update --server-id ... --release` only when the user authorizes writing and publishing.
4. Verify live tools after release.

Schema compatibility rule: do not emit empty `format` values.

## Troubleshooting

- `401/403`: check `--site`, refresh login with `bytedcli auth login --site <site>`, then retry.
- Missing resource id: use the corresponding `--server-id`, `--tool-id`, `--agent-id`, or `--sandbox-id` option.
- Empty schema after creation: run schema generation/update from the live tool configuration when IDL is available.
