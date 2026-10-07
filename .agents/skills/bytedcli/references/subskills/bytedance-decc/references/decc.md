# DECC (Data Exchange & Cross-region Compute) CLI Reference

DECC provides cross-region data exchange capabilities. The CLI supports create/update OG tagging, creating HDFS channels, registering data (tables), and applying for permissions.
It also supports inspecting DECC/OG ticket list, detail, and comments, plus safely cancelling pending ticket versions.

Authentication: all DECC commands use a personal ByteCloud JWT from `--site i18n-tt`. USTTP/EUTTP are business regions, not authentication sites. The client derives the operator and headers from the same token for multi-step ticket and Gateway requests.

## Commands

### gateway service list

List or search DECC Gateway services(psm), typically to find the service entity ID for the psm that owns the api you want to tag.

```bash
bytedcli --site i18n-tt decc gateway service list [options]
```

**Options:**

- `--name <name>` — Filter by psm
- `--region <regions>` — Comma-separated compliance regions: `EU`, `US`, `EU,US`, or `US,EU`
- `--owners <owners>` — Comma-separated owner usernames; values are OR filters
- `--source-type <sourceType>` — Source type: `Web`, `Log`, `Metric`, or `CommonHeader`
- `--page <n>` — Page number, 1-based (default: `1`)
- `--page-size <n>` — Page size (default: `20`)

**Examples:**

```bash
# List services
bytedcli --site i18n-tt decc gateway service list

# Search by name
bytedcli --site i18n-tt decc gateway service list \
  --name demo.api_service

# Filter by region, owners, and source type
bytedcli --site i18n-tt decc gateway service list \
  --region EU,US \
  --owners demo.user,sample.user \
  --source-type CommonHeader
```

### gateway endpoint list

List the API endpoints under a DECC Gateway service entity (PSM).

```bash
bytedcli --site i18n-tt decc gateway endpoint list [options]
```

**Options:**

- `--entity-id <entityId>` (required) — DECC Gateway service entity ID
- `--stage <stage>` (required) — Endpoint stage: `approved` or `draft`
- `--path <path>` — Filter by HTTP path. DECC matches this filter as a prefix, so a path containing braces (DECC's `{{n}}` wildcard segments) never matches upstream. The CLI queries the longest static prefix — everything before the first brace — and matches the exact path locally, on the requested page only. Wrap such a path in single shell quotes.
- `--page <n>` — Page number, 1-based (default: `1`)
- `--page-size <n>` — Page size (default: `20`). The CLI does not cap it; DECC may honour a smaller page, and `page_size` in the result reports the size actually in effect.

**Examples:**

```bash
# List draft endpoints for a service entity by HTTP path
bytedcli --site i18n-tt decc gateway endpoint list \
  --entity-id demo-service-entity-id \
  --stage draft \
  --path /demo/api \
  --page 1 \
  --page-size 15

# Wildcard paths must be quoted; the CLI queries the static prefix and matches exactly
bytedcli --site i18n-tt --json decc gateway endpoint list \
  --entity-id demo-service-entity-id \
  --stage approved \
  --path '/demo/api/{{4}}/execute' \
  --page 1 \
  --page-size 100
```

**Output:** Text mode prints the endpoint table plus an explicit note whenever the response is not the complete result set. JSON mode adds `page`, `page_size` (the size actually in effect), `current_count`, `has_more`, `scanned_all`, and `truncated` next to the upstream `page_info`. Only `scanned_all: true` proves this one response holds every matching endpoint; it is false for any page after the first, because the pages before it were never read. Treat `truncated: true` as "this listing proves nothing about what is absent".

A braced `--path` additionally returns `path_filter` (`requested_path`, `templated`, `server_path_filter`, `match`, `scanned_count`, `matched_count`, and `prefix_total` when DECC returns a total). Under a braced path, `endpoints` holds only exact local matches while `page_info` still describes the wider static-prefix query, so read `path_filter.matched_count` for the match count and `path_filter.scanned_count` for the rows scanned. A braced path that matches no row on the requested page fails with `DECC_GATEWAY_ENDPOINT_NOT_FOUND` instead of an empty success; that error means "not on this page", not "does not exist". Its hint names the static-prefix listing to page through until `scanned_all` is true and the `gateway endpoint get --id <endpoint_id> --stage <stage>` read; a wildcard endpoint often exists in only one stage, so check both.

### gateway endpoint get

Optional target guards: `--entity-id`, `--version`, and the paired `--caller-vpc` / `--callee-vpc`. Entity guards assert the returned registration; they do not add an entity selector to the backend request.

Get a DECC Gateway API endpoint, including its ID, description, and tagged fields.

```bash
bytedcli --site i18n-tt decc gateway endpoint get [options]
```

**Options:**

- `--id <id>` (required) — DECC Gateway endpoint ID
- `--stage <stage>` (required) — Endpoint stage: `approved` or `draft`

**Examples:**

```bash
# Get a draft endpoint
bytedcli --site i18n-tt decc gateway endpoint get \
  --id demo-endpoint-id \
  --stage draft
```

### gateway tagging get

Audit the leaf-field compliance-tag coverage of exact Gateway endpoint paths in one target control plane. Do not use Chrome or another browser as supplementary or substitute evidence for a Gateway tagging verdict; if the CLI cannot prove the result, stop and report the error or `unverified` verdict.

```bash
bytedcli --site i18n-tt decc gateway tagging get [options]
```

**Options:**

- `--url <url>` — Trusted DECC `compliance_platform` service detail URL; mutually exclusive with `--entity-id`
- `--entity-id <entityId>` — DECC Gateway service entity ID; mutually exclusive with `--url`
- `--path <path>` (required, repeatable) — Exact HTTP path; 1–50 distinct paths per call
- `--method <method>` (required) — Exact HTTP method to audit
- `--stage <stage>` — `approved` (default) or `draft`
- `--region <region>` (required) — `US` or `EU`
- `--expect-field <path>` (repeatable) — Canonical leaf path from the authoritative IDL, HTTP binding, or runtime request; contract verification accepts exactly one `--path`

**Examples:**

```bash
# US/USTTP coverage uses tx_catalog_id or not_user_data=true
bytedcli --site i18n-tt decc gateway tagging get \
  --url https://decc.tiktok-row.net/compliance_platform/detail/demo-service-entity-id \
  --path /demo/api \
  --method POST \
  --stage approved \
  --region US \
  --expect-field query.page \
  --expect-field req.body.name

# Without contract inputs, only registered DECC fields are audited
bytedcli --site i18n-tt --json decc gateway tagging get \
  --entity-id demo-service-entity-id \
  --path /demo/first \
  --path /demo/second \
  --method POST \
  --region EU
```

For approved endpoints, the CLI selects the target region's endpoint-list row and passes its exact `version`, `caller_vpc`, and `callee_vpc` to the detail API. This is required when US and EU share an endpoint ID but use different approved versions. The response separates `registered_tag_verdict` from `contract_verdict`. Without `--expect-field`, contract coverage and the overall `verdict` are `unverified`, even when registered fields have missing tags. An empty schema also makes `registered_tag_verdict=unverified`, increments `unverified_endpoint_count`, and renders as `0/0 no registered fields`, never as complete. With contract inputs, the CLI compares every expected canonical leaf path against the selected DECC schema and reports `schema_contract.missing_fields`. An endpoint's `complete` requires both registered tag coverage and its schema contract: an expected field that DECC has not registered makes that endpoint `complete: false` even when every registered field carries a tag, and the endpoint is listed in the top-level `expected_fields_missing`. `incomplete_endpoint_count` counts both kinds of failure, so read each endpoint's `schema_contract` to tell a missing tag from a missing field. An endpoint with an empty schema is the exception: it stays in `unverified_endpoint_count` even when expected fields are missing from it, so `expected_fields_missing` is the field that answers which endpoints lack an expected field. Without `--expect-field`, `schema_contract.complete` is `null` and counts as unverified for that endpoint rather than complete or incomplete. JSON always includes the top-level `method`, `expected_fields`, `expected_fields_missing`, `warnings`, and each endpoint's `version` and `status`; unavailable selector values are `null`.

The query requires an exact method and fails closed when regional selectors are missing or ambiguous, a returned page size exceeds the requested size, pagination is inconsistent, list/detail identity or version differs, regional metadata conflicts, endpoint IDs are unsafe, business errors contain terminal controls, duplicate top-level/nested HTTP or tag representations conflict, or the schema/tag shape is malformed. `DECC_GATEWAY_REGION_MISMATCH` and `DECC_GATEWAY_REGION_AMBIGUOUS` can be raised while validating either the list or detail response; neither proves that a detail request was sent. Preserve the CLI evidence and stop: do not guess an assurance path, substitute another region, or use a browser result. The whole lookup shares bounded page, candidate/detail, regional-metadata, schema/tag/status, path-byte, actual decoded response-body byte, output-field, and 120-second budgets, plus per-response byte and structural limits. A request still honors the global HTTP timeout and GET retry configuration, while the overall deadline cancels an in-flight request without retrying after cancellation. On `DECC_GATEWAY_RESOURCE_LIMIT`, inspect `details.resource` and `details.phase`: narrow paths for cumulative list work, keep the required exact method for candidate/detail work, retry a duration timeout once and inspect its phase, and stop to report a single path or endpoint that exhausts its own limit.

### gateway endpoint submit

Preview a draft against the latest approved baseline for every selected exact caller/callee assurance path. The command is read-only by default and accepts explicit `--dry-run`. Prefer saving the complete reviewed state in a fail-closed plan file; a real submit can consume that exact plan with explicit `--yes`.

```bash
decc_plan_dir="$(mktemp -d)"
bytedcli --site i18n-tt decc gateway endpoint submit \
  --draft-id demo-endpoint-id \
  --caller-vpc demo-office-net \
  --callee-vpc US_demo-vpc \
  --dry-run \
  --plan-file "$decc_plan_dir/decc-submit-plan.json"

bytedcli --site i18n-tt decc gateway endpoint submit \
  --draft-id demo-endpoint-id \
  --caller-vpc demo-office-net \
  --callee-vpc US_demo-vpc \
  --plan-file "$decc_plan_dir/decc-submit-plan.json" \
  --yes

rm "$decc_plan_dir/decc-submit-plan.json"
rmdir "$decc_plan_dir"
```

Options:

- `--draft-id <draftId>` (required) — exact version-zero draft ID
- `--caller-vpc <vpc>` — exact caller selector; requires `--callee-vpc`
- `--callee-vpc <vpc>` — exact callee selector and target-region source
- `--dry-run` — explicitly request the read-only preflight; mutually exclusive with `--yes`
- `--plan-file <path>` — POSIX only. Use a private temporary directory outside the repository and remove the plan after the live result or failure recovery is complete, so a later `git add` cannot publish the full schema diff. Dry-run exclusively creates the plan; live consumes that exact plan. In either mode it cannot be combined with manual `--expect-field`, `--expect-snapshot`, or `--allow-unexpected-fields` guards. On Windows, use the manual expected-field and snapshot workflow.
- `--expect-field <path>` — intended changed field path; repeat for every expected path
- `--expect-snapshot <sha256>` — exact `snapshot_digest` from the reviewed dry-run; required for manual live submits and only valid alongside `--yes`. A live `--plan-file` supplies its own snapshot instead.
- `--yes` — perform the guarded submit; omitted by default
- `--allow-unexpected-fields` — live-submit-only risk override for changed paths not listed by `--expect-field`; requires `--yes`
- `--show-request` — include full submit request payloads during dry-run; cannot be combined with `--yes`

The JSON result is discriminated by `dry_run`. Both branches include `baseline_ticket_id`, `baseline_version`, `changed_fields`, `unexpected_fields`, `preflights`, `regional_baseline_drift`, `snapshot_digest`, and `review_plan_file`, which is the resolved plan path when `--plan-file` is used and `null` otherwise. When `--plan-file` is used, dry-run exclusively creates a mode-0600 regular file without following symlinks or overwriting an existing path. The plan binds the CLI version, draft, selector, assurance paths, every changed path, the complete field diff, and snapshot digest; live rejects a different CLI version or selector and uses the plan's complete changed-path set as the expected fields. The live branch has `dry_run: false` plus `submissions[]`, where every item contains its exact `assurance_path`, `ticket_id`, `ticket_version`, `ticket_url`, and `ticket_url_form`. A response that does not prove a complete versioned ticket is an unknown outcome rather than a successful result. Immediately before every POST it reloads the exact version-zero draft and exact pair's latest approved baseline; any change stops before that POST. Treat any ambiguous region, path, version, response shape, resource-budget, plan, or baseline identity error as fail-closed.

Before the first POST, a live submit walks the `ticket list` pages for the draft's entity and refuses when any ticket for the same endpoint is still open. DECC rejects such a submit anyway, and answers with a body the CLI cannot parse. The refusal is `DECC_GATEWAY_SUBMIT_PENDING_TICKET_EXISTS`, carries the open ticket's URL, and no flag bypasses it. Cancelling that version also discards a priority request approved on it, because a priority request belongs to one version and is not carried to the next. A dry run runs the same scan and reports the refusal in `warnings` instead of throwing, so the blocker is visible while the diff is being reviewed rather than only after `--yes`. Anything else the scan runs into on a dry run — no permission to list the entity's tickets, a list this build cannot read, a spent resource budget — also becomes a warning saying the check could not be made, because a dry run exists to show the diff and this gate must not take it away. A live submit still stops on every one of them.

Four properties of that scan matter when reading its result:

- The listing is requested **without** a region selector, so one pass covers every region this submit targets. Adding a selector switches DECC to the by-region ticket list, whose entity selector is the PSM id rather than the Gateway `entity_id` used here; a region-scoped request would return zero rows and turn the hard stop into a silent pass. The regions are matched locally instead. A ticket whose region DECC did not report, or reported as a value this build does not recognise, still blocks.
- "Open" means "not in a state known to be final". A ticket blocks unless its status is one of the recognised terminal ones (approved, finished, rejected, cancelled, canceled, closed), so a review state this build has not seen, or a status DECC did not report at all, blocks rather than passes.
- A ticket is matched either by `endpoint_id` (the draft id or an approved baseline id) or by its displayed identity carrying both the HTTP method and the route. That identity is upstream text: DECC has been observed rendering it as `<path> method:<METHOD>` and as `<METHOD> <path>`, path-parameter segments are compared with their placeholders collapsed, and case is folded. Every displayed identity key (`channel_name`, `endpoint_name`, `schema_name`, and `name`) is tried, not only the first one present. The ticket's `title` is deliberately not one of them: it is a human-readable description, and one that happens to name a method and a route would block a submit over a different endpoint's ticket. A ticket DECC labels in some other way is matched only by `endpoint_id`, and only when that id is one this submit already knows. An open ticket carrying neither a known `endpoint_id` nor a readable method-and-route label is counted in `unreadable_endpoint_identity_count`, and a non-zero count refuses the whole scan with `DECC_GATEWAY_SUBMIT_PENDING_TICKET_UNVERIFIED`, because a scan that matched nothing no longer proves the endpoint is free.
- The scan must be able to prove it saw the whole list, and only page markers the server actually returned count as evidence. It refuses with `DECC_GATEWAY_SUBMIT_PENDING_TICKET_UNVERIFIED`, and still sends no write, when the pages run out of budget, when the server answers a different page than requested, when it returns a page larger than the requested size, when it repeats a page it already returned, when it empties out before reaching its reported total, when the distinct tickets seen exceed that total, when a short page contradicts a total an earlier page reported, when it reports a page size of zero, or when it reports neither a total nor a page size of its own. A total, once reported, has to be satisfied: neither a later page reporting a smaller total nor a later page reporting none at all can end the walk early. Completion is counted in distinct tickets, not rows returned.

Tickets for other endpoints whose identity the scan could read, and tickets for a region DECC did report as a different one, never block a submit.

A business-reason refusal surfaces as `DECC_GATEWAY_API_ERROR` with `details.refused_by: "server"` and the redacted, length-capped upstream message; the message is read from `err_msg` first, because the envelope's `message` often still says "success" on a refusal. HTTP and business codes 408, 425, 429, and 5xx stay unknown outcomes, as does a response whose evidence contradicts itself, and as does a success that arrived beside a `data` field the CLI could not read. When a response cannot be parsed at all, `details.response_shape` reports the top-level keys and the JSON type of each value, never any value, with credential-shaped key names replaced by a numbered redaction marker.

Text mode prints only the compact field diff. Use `--show-request` only when the full dry-run payload is actually needed because it can be large. On success, live output includes the exact assurance path and normalized ticket ID/version/URL. A parse, timeout, redirect, network, retryable HTTP, incomplete-ticket, or contradictory ticket response is reported as an unknown mutation outcome; inspect the draft and ticket list before retrying. In a multi-path submit, completed paths are returned as partial-failure evidence and retry guidance never resubmits them blindly.

### gateway endpoint create

Preview or create a DECC Gateway endpoint draft. The command is a dry-run unless `--yes` is present. When `--owners` is omitted, the operator is used as the owner. A real create is read back at `version=0`; missing, extra, duplicate, or rewritten observable state is treated as an unverified outcome, so inspect before retrying.

```bash
bytedcli --site i18n-tt decc gateway endpoint create [options]
```

**Options:**

- `--entity-id <entityId>` (required) — DECC Gateway service entity ID
- `--path <path>` (required) — HTTP path
- `--method <method>` (required) — HTTP method
- `--description <description>` (required) — Endpoint description
- `--owners <owners>` — Comma-separated owner usernames; defaults to the operator
- `--dry-run` — Preview the exact URL and request body without writing (default)
- `--yes` — Create the draft and verify the complete observable request state by readback

**Examples:**

```bash
# Preview a draft endpoint owned by the current operator
bytedcli --site i18n-tt decc gateway endpoint create \
  --entity-id demo-service-entity-id \
  --path /demo/api \
  --method GET \
  --description "demo endpoint"

# Create and verify a draft endpoint with explicit owners
bytedcli --site i18n-tt decc gateway endpoint create \
  --entity-id demo-service-entity-id \
  --path /demo/api \
  --method POST \
  --description "demo endpoint" \
  --owners demo.user,sample.user \
  --yes
```

### gateway endpoint update

Optional target guards: `--entity-id` and paired `--caller-vpc` / `--callee-vpc`; field update supports the same options. Assurance-path create accepts only the entity guard because its VPC options describe the new path. Submit also accepts `--entity-id` and binds it into new review plans. Entity guards assert the returned registration; they do not add an entity selector to the backend request.

Preview or update a DECC Gateway endpoint draft while preserving its complete schema and assurance paths. The command is a dry-run unless `--yes` is present. Dry-run output contains a bounded complete-state diff, before/after fingerprints, and a confirmation token bound to the operator, draft, and exact diff without returning schema values.

```bash
bytedcli --site i18n-tt decc gateway endpoint update [options]
```

**Options:**

- `--draft-id <draftId>` (required) — DECC Gateway endpoint draft ID
- `--description <description>` — Endpoint description; defaults to the current draft detail description when omitted
- `--query-file <path>` — Query params field array file; mutually exclusive with `--http-schema-file`
- `--path-file <path>` — Path params field array file; mutually exclusive with `--http-schema-file`
- `--req-headers-file <path>` — Request headers field array file; mutually exclusive with `--http-schema-file`
- `--req-body-file <path>` — Request body field array file; mutually exclusive with `--http-schema-file`
- `--resp-headers-file <path>` — Response headers field array file; mutually exclusive with `--http-schema-file`
- `--resp-body-file <path>` — Response body field array file; mutually exclusive with `--http-schema-file`
- `--http-schema-file <path>` — Direct default-entry patch without the outer `""` key; deep-merged over the current entry and mutually exclusive with all section files
- `--allow-delete` — Permit live deletion only when every deleted path is shown by the same dry-run diff; a truncated deletion list always blocks the write
- `--dry-run` — Preview the complete-state diff without writing (default)
- `--yes` — Persist the complete draft state and verify it by readback
- `--confirmation-token <token>` — Exact token emitted by the reviewed dry-run; required together with `--yes`

The field-array files contain JSON arrays whose entries use `fieldName`, `type`, optional `description`, optional `compliance_tag`, and optional nested `children`. The CLI converts arrays to the map shape expected by DECC Gateway. All JSON inputs for one command share the 6 MiB schema budget; regular-file identity, size, bounded reads, and a final identity check are completed before parsing. A file that changes during the read is rejected.

The update API can round-trip only `caller_vpc` and `callee_vpc` in assurance paths. If a remote representation contains other path metadata, the CLI fails closed before diffing or POST. A live update that would delete values also fails unless `--allow-delete --yes` is explicit. If the bounded diff cannot capture every deletion, the dry-run returns a null confirmation token and live execution remains blocked. Raw HTTP schema patches apply the same classification-value safety rules as field updates: null, empty, invalid, or conflicting catalog/tag representations fail before POST.

**Examples:**

```bash
# Update draft description and request schema from local JSON files
bytedcli --site i18n-tt decc gateway endpoint update \
  --draft-id demo-endpoint-id \
  --description "updated demo endpoint" \
  --req-headers-file req_headers.json \
  --req-body-file req_body.json

# Update response schema from local JSON files
bytedcli --site i18n-tt decc gateway endpoint update \
  --draft-id demo-endpoint-id \
  --resp-headers-file resp_headers.json \
  --resp-body-file resp_body.json

# After reviewing that dry-run, rerun the exact same payload with its emitted token
bytedcli --site i18n-tt decc gateway endpoint update \
  --draft-id demo-endpoint-id \
  --resp-headers-file resp_headers.json \
  --resp-body-file resp_body.json \
  --yes \
  --confirmation-token '<token-from-the-dry-run>'

# Deep-merge a raw patch into the current default schema entry
bytedcli --site i18n-tt decc gateway endpoint update \
  --draft-id demo-endpoint-id \
  --http-schema-file schema_patch.json
```

Real writes require the exact confirmation token from the reviewed dry-run, read and recheck `version=0`, send the complete preserved state, and immediately verify the persisted schema, description, entity, and canonical assurance-path multiset. DECC exposes no modeled revision/CAS token: bytedcli serializes only mutations in the same process, so another CLI process or Web editor can still race and overwrite a full-state update. Use `--yes` only with an exclusive editing window; otherwise stop after dry-run. HTTP 408/425/429 and other ambiguous transport outcomes are not treated as definite rejections; they enter readback/outcome-unknown handling. On a verification or outcome-unknown error, follow the inspect hint and do not retry blindly.

### gateway field update

Update one existing draft field while preserving every other schema field. Unknown attributes are rejected before POST because DECC may silently discard them.

```bash
bytedcli --site i18n-tt decc gateway field update [options]
```

**Options:**

- `--draft-id <draftId>` (required) — Draft ID
- `--path <path>` (required) — Existing field path such as `query.name`, primitive root `req.body` / `resp.404.body`, nested `req.body.user.id`, structural `req.body.additionalProperties`, or `resp.404.body.error.code`. Dynamic segments containing `.`, brackets, quotes, backslashes, or a structural name use JSON bracket notation, for example `query["a.b"]`, `req.body["additionalProperties"]`, or `resp["2.00"].body["error.code"]`. Response status names `body` and `header` must also stay bracket-quoted (`resp["body"]` / `resp["header"]`) so they are not interpreted as the legacy status-200 forms. Wrap bracket paths in single shell quotes.
- `--description <description>` — Field description
- `--attributes <json>` / `--attributes-file <path>` — Safe attributes to merge
- `--tx-catalog-id <id>` / `--tt-catalog-id <id>` / `--byte-data-tag <tag>` — Semantic values normalized into `compliance_tag`
- `--not-user-data <true|false>` — Set `compliance_tag.not_user_data`
- `--dry-run` — Preview the diff (default)
- `--yes` — Persist and verify the field value by readback
- `--confirmation-token <token>` — Exact token emitted by the reviewed dry-run; required together with `--yes`

Compatible top-level `tx_catalog_id`, `tt_catalog_id`, `byte_data_tag`, and `not_user_data` keys in `--attributes` are also normalized into `compliance_tag`. Catalog/tag values must be non-empty strings, positive numbers, or non-empty arrays of those values; `not_user_data` must be boolean. `null` cannot clear a compliance tag because clearing classification requires an explicit deletion workflow. Conflicting values, structural edits, missing fields, and new unknown attributes fail before writing.

Paths emitted by `gateway tagging get` are reversible and can be passed directly to `field update`. Keep JSON bracket-quoted segments intact so a direct field named `a.b` is not confused with nested fields `a.b`, and a direct field named `additionalProperties` is not confused with the structural dynamic-value schema.

```bash
bytedcli --site i18n-tt decc gateway field update \
  --draft-id demo-endpoint-id \
  --path req.body.user.id \
  --description "Internal user identifier" \
  --tx-catalog-id demo-tx-catalog-id
```

### gateway assurance-path create

Idempotently append one assurance path while preserving the complete draft schema. The command is a dry-run unless `--yes` is present, and `--caller-vpc` defaults to `Office_Net`.

```bash
bytedcli --site i18n-tt decc gateway assurance-path create \
  --draft-id demo-endpoint-id \
  --caller-vpc Office_Net \
  --callee-vpc US_VPC1

# Rerun the exact same path with the token emitted above
bytedcli --site i18n-tt decc gateway assurance-path create \
  --draft-id demo-endpoint-id \
  --caller-vpc Office_Net \
  --callee-vpc US_VPC1 \
  --yes \
  --confirmation-token '<token-from-the-dry-run>'
```

Existing remote paths must contain only `caller_vpc` and `callee_vpc`; other metadata fails closed because the update contract cannot round-trip it. Existing exact paths return an idempotent no-change result without POST.

### hdfs-channel create

Create a new DECC HDFS channel (endpoint).

```bash
bytedcli --site i18n-tt decc hdfs-channel create [options]
```

**Options:**

- `--name <name>` (required) — Channel name (database name)
- `--description <description>` (required) — Channel description
- `--owners <owners>` (required) — Comma-separated owner usernames
- `--vgeo-list <vgeoList>` (required) — Comma-separated vGeo regions: `ROW-TT`, `NonTT`, `US`, `EU`, `CN`
- `--scenario <scenario>` — Comma-separated scenario types (default: `4` = CN_CROSS_BORDER)

**Examples:**

```bash
# Create a channel with CN vGeo
bytedcli --site i18n-tt decc hdfs-channel create \
  --name demo-database \
  --description "demo channel for cross-region exchange" \
  --owners demo.user \
  --vgeo-list CN \
  --scenario 4

# Create a channel with multiple vGeos
bytedcli --site i18n-tt decc hdfs-channel create \
  --name demo-multi-region \
  --description "multi-region channel" \
  --owners demo.user1,demo.user2 \
  --vgeo-list CN,US,EU \
  --scenario 3
```

### hdfs-data create

Register a new DECC HDFS data (table) under a channel.

```bash
bytedcli --site i18n-tt decc hdfs-data create [options]
```

**Options:**

- `--channel-id <channelId>` (required) — DECC channel/endpoint ID
- `--name <name>` (required) — Data name (table name)
- `--owners <owners>` (required) — Comma-separated owner usernames
- `--region <region>` (required) — Source DECC region
- `--scenario <scenario>` — Comma-separated scenario types (default: `3` = CLOVER)

**Supported regions:** `China-North`, `Singapore-Central`, `EU-TTP2`, `US-EastRed`, `EU-Compliance2`, `US-TTP`, `Asia-SouthEastBD`, `Asia_Saas`, `Singapore_Saas`, `Asia_CIS`

**Examples:**

```bash
# Register a table under a channel
bytedcli --site i18n-tt decc hdfs-data create \
  --channel-id demo-channel-id \
  --name demo_table_name \
  --owners demo.user \
  --region EU-TTP2

# Register with explicit scenario
bytedcli --site i18n-tt decc hdfs-data create \
  --channel-id demo-channel-id \
  --name demo_another_table \
  --owners demo.user1,demo.user2 \
  --region US-TTP \
  --scenario 2
```

### hdfs-data data-version

Change the schema of an existing DECC HDFS table. `hdfs-data create` only registers a table; adding or changing its fields goes through a data version: create a draft from the applied version, patch the draft, then submit it for approval.

A data version carries the schema twice and both copies must agree:

- `idl.content` — the Hive `CREATE TABLE` DDL
- `json_schema` — a flat per-column object whose `des` block holds the compliance category tag

`column create`, `column update`, and `column delete` each patch both carriers in one write, so the Hive DDL and the category tag never drift apart.

**Constraints:**

- DECC rejects any Chinese character in a data version with code `101002`. `column create` and `column update` validate `--column-name`, `--column-type`, `--description`, and `--tag` up front and name the offending flag.
- `data_version/update` is a full-record overwrite with no compare-and-set. A live `column create`, `column update`, or `column delete` therefore requires the `--confirmation-token` minted by the dry-run that read the exact draft you reviewed; if the draft changed in between, the token no longer matches and the write is refused. Tokens are also bound to the specific change they authorize, so a token minted for one column cannot be replayed against another.
- Only `list`, the scenario lookup, and `cancel` are served by the V3 BFF. Every other data-version call goes through the OpenAPI gateway (see the routing table at the end of this document).

**Scenario is per-channel, so leave `--scenario` off.** Every command reads the
data's own scenario from `data/detail` and prints it with its source, for
example `Scenario: 2=TEXAS (detected)`. Real channels are not filed under
ALL_SCENARIO: US-TTP channels use `2` = TEXAS and EU channels use `3` = CLOVER,
so a hardcoded `1` describes almost no real table. Pass `--scenario` only to
override, which prints `(explicit)`. The override takes the scenario name
(`--scenario TEXAS`) or the numeric code DECC uses in its payloads
(`--scenario 2`). If the lookup fails the call still proceeds under
ALL_SCENARIO and prints `(fallback)` plus a warning — treat that as a signal to
supply the value yourself.

**Category tags come from a live code table.** The `--tag` value (`6.1`,
`1.3.1`, `5.2`, …) is a data classification code. Read the current table with
`hdfs-data category list`, which also marks which codes are actually pickable —
roughly half are not. Do not work from a local copy: the live table has already
drifted from the hardcoded ones floating around. Which code to pick still comes
from the compliance requirement; to match what a table already does, read
neighbouring columns via `--json ... data-version get` and inspect
`json_schema.properties.<column>.des.tag`.

#### list / get

```bash
# All versions with their per-region state
bytedcli --site i18n-tt decc hdfs-data data-version list --data-id demo-data-id

# One version, summarized (column counts, states)
bytedcli --site i18n-tt decc hdfs-data data-version get --data-id demo-data-id --version 12

# Full record including the Hive DDL and json_schema
bytedcli --site i18n-tt --json decc hdfs-data data-version get --data-id demo-data-id
```

`--version` defaults to the newest version. `list` takes no `--scenario`: DECC
keys that route by data alone, so the scenario every other subcommand resolves
has nothing to select there.

Region states are named for the codes DECC documents — `Suspended`, `Applied`, `Pending`, `Draft`, `Pre-checked`, `Rejected`, `Canceled`, `Precheck Conditional Passed`. The platform emits more codes than that, especially while a submission is being processed: a real submission was observed moving `Draft` → `6` → `13` → `8` → `Suspended` within six minutes. Unnamed codes are printed verbatim as `code <n>`; they are not errors. Check the DECC console for the authoritative stage of an in-flight submission.

Note that `states` only lists the regions that the version's transfer directions actually cover (`extra.hdfs.list`), so a draft showing three regions can legitimately narrow to one after submission.

#### create

Create a draft from the newest **applied** version, which is the correct base for a schema change.

```bash
# Preview which version the draft would branch from
bytedcli --site i18n-tt decc hdfs-data data-version create --data-id demo-data-id

# Create it
bytedcli --site i18n-tt decc hdfs-data data-version create --data-id demo-data-id --yes

# Branch from a specific version instead
bytedcli --site i18n-tt decc hdfs-data data-version create \
  --data-id demo-data-id --upstream-version 11 --yes
```

**Options:** `--data-id` (required), `--upstream-version`, `--scenario` (auto-detected), `--dry-run` (default), `--yes`

#### column create

```bash
# 1. Review the IDL and schema diff; this prints the confirmation token
bytedcli --site i18n-tt decc hdfs-data data-version column create \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column \
  --column-type string \
  --description 'demo column' \
  --tag 6.1

# 2. Persist it with the token from that dry-run
bytedcli --site i18n-tt decc hdfs-data data-version column create \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column \
  --column-type string \
  --description 'demo column' \
  --tag 6.1 \
  --yes --confirmation-token <token-from-step-1>
```

**Options:**

- `--data-id <dataId>` (required) — DECC HDFS data (table) ID
- `--column-name <columnName>` (required) — Hive column name
- `--column-type <columnType>` (required) — Hive type, for example `string`, `bigint`, `map<string,string>`
- `--description <description>` (required) — Column comment; English only
- `--tag <tag>` (required) — DECC compliance category written to `des.tag`, for example `6.1`
- `--version <version>` — Draft version to patch (default: newest)
- `--sync <sync>` — `des.sync` value (default `YES`)
- `--scenario <scenario>` — auto-detected from the data; override only when the lookup fails
- `--dry-run` (default) / `--yes` / `--confirmation-token <token>`

The command is idempotent: if the column is already in both the IDL and `json_schema`, it reports `no_change` and writes nothing. After a live write it re-reads the version and fails with `DECC_HDFS_DATA_VERSION_READBACK_MISMATCH` if the column is not actually there.

#### column update

Change an existing column's Hive type, comment, or category tag. Retagging a column for a compliance requirement is the common case, and it does not require restating the type.

```bash
# 1. Review the before/after of just that column
bytedcli --site i18n-tt decc hdfs-data data-version column update \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column \
  --tag 1.3.1

# 2. Persist it with the token from that dry-run
bytedcli --site i18n-tt decc hdfs-data data-version column update \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column \
  --tag 1.3.1 \
  --yes --confirmation-token <token-from-step-1>
```

**Options:**

- `--data-id <dataId>` (required) — DECC HDFS data (table) ID
- `--column-name <columnName>` (required) — Existing Hive column to change
- `--column-type <columnType>` — New Hive type
- `--description <description>` — New column comment; English only
- `--tag <tag>` — New DECC compliance category written to `des.tag`
- `--sync <sync>` — New `des.sync` value
- `--version <version>` — Draft version to patch (default: newest)
- `--scenario <scenario>` — auto-detected from the data; override only when the lookup fails
- `--dry-run` (default) / `--yes` / `--confirmation-token <token>`

At least one of `--column-type`, `--description`, `--tag`, or `--sync` is required; only the fields you pass move. The schema node is merged field by field rather than rebuilt, because DECC attaches metadata of its own to a column once it has been through review (`asset_id`, `entity`, `reason`, `uneditable`) and rebuilding the node would silently drop it.

Changing the type updates both type vocabularies at once: `des.original_type` keeps the Hive type and `type` holds the JSON Schema type DECC derives from it. These do not coincide outside `string` — `bigint` becomes `integer`, `array<string>` becomes `array`, `decimal(10,2)` becomes `number` — so the mapping is applied explicitly. A live `--column-type bigint` was verified to land as `des.original_type: bigint` with `type: integer`.

If the draft already matches the patch, the command reports `no_change` and writes nothing.

#### column delete

Remove a column from a draft's Hive IDL and `json_schema`.

```bash
# 1. Review what would be removed, including the tag it carried
bytedcli --site i18n-tt decc hdfs-data data-version column delete \
  --data-id demo-data-id --version 13 --column-name demo_column

# 2. Remove it with the token from that dry-run
bytedcli --site i18n-tt decc hdfs-data data-version column delete \
  --data-id demo-data-id --version 13 --column-name demo_column \
  --yes --confirmation-token <token-from-step-1>
```

**Options:** `--data-id` (required), `--column-name` (required), `--version`, `--scenario` (auto-detected), `--dry-run` (default), `--yes`, `--confirmation-token`

The dry-run prints the declaration to be removed and the category tag it carried, so the change is recoverable from the reviewed output if the drop turns out to be wrong. If the column is in neither carrier, the command reports `no_change`.

**DECC accepts the removal on a draft, but that is not the same as the change being approvable.** Dropping a field that is already live in the applied version is a schema regression, and whether an approver passes it is a separate question this command cannot answer. Confirm the reviewers expect it before submitting.

#### submit

Submitting is what opens the DECC approval ticket.

```bash
# Preview
bytedcli --site i18n-tt decc hdfs-data data-version submit \
  --data-id demo-data-id --version 13 --reason 'add demo column'

# Submit for approval
bytedcli --site i18n-tt decc hdfs-data data-version submit \
  --data-id demo-data-id --version 13 --reason 'add demo column' --yes
```

**Options:** `--data-id` (required), `--version` (required), `--reason`, `--scenario`, `--dry-run` (default), `--yes`

#### cancel

Withdraw a version that is in review.

```bash
# Show the version's current states without touching it
bytedcli --site i18n-tt decc hdfs-data data-version cancel --data-id demo-data-id --version 13

# Withdraw it
bytedcli --site i18n-tt decc hdfs-data data-version cancel --data-id demo-data-id --version 13 --yes
```

**Options:** `--data-id` (required), `--version` (required), `--scenario` (auto-detected), `--dry-run` (default), `--yes`

**`cancel` only applies to a version that is in review.** DECC answers
`{"msg":"success"}` no matter what, including for a version that does not move:
cancelling a `Draft` or a `Suspended` version was verified to leave it exactly
as it was. The command therefore decides the outcome by reading the states back
rather than by trusting the response, and prints `cancel had no effect` with the
unchanged states when nothing moved. A version in review goes straight to
`Canceled` — an in-review version at `code 6` was observed becoming `Canceled`
on the readback in the same call.

There is no way to delete a `Draft` version through the API; `cancel` will not
do it. Drafts left behind by an aborted change stay in the version list.

Unlike every other write here, `cancel` has to go through the **V3 BFF**. The
OpenAPI gateway does carry the route — it is registered in BAM under
`tiktok.decc.openapiv3` — but answers 403 for a personal account, as it also
does for `data_version/list`.

#### End-to-end schema change

```bash
DATA_ID=demo-data-id

# 1. Find the applied version
bytedcli --site i18n-tt decc hdfs-data data-version list --data-id "$DATA_ID"

# 2. Create the draft (prints the new version number)
bytedcli --site i18n-tt decc hdfs-data data-version create --data-id "$DATA_ID" --yes

# 3. Add the column, twice: review, then commit with the token
bytedcli --site i18n-tt decc hdfs-data data-version column create \
  --data-id "$DATA_ID" --version 13 \
  --column-name demo_column --column-type string \
  --description 'demo column' --tag 6.1

# 4. Submit for approval
bytedcli --site i18n-tt decc hdfs-data data-version submit \
  --data-id "$DATA_ID" --version 13 --reason 'add demo column' --yes
```

### hdfs-data category list

List the compliance category codes that may go in a column's `des.tag`.

```bash
# The whole tree, with whether each code can be picked
bytedcli --site i18n-tt decc hdfs-data category list

# Just the codes you can actually write
bytedcli --site i18n-tt decc hdfs-data category list --fillable-only

# With DECC's own explanation of each code
bytedcli --site i18n-tt decc hdfs-data category list --data-id demo-data-id --with-descriptions
```

**Options:** `--data-id`, `--scenario`, `--fillable-only`, `--with-descriptions`

The code table comes from the same route the console's cascader uses,
`GET /decc-next-api/v3/schema/gateway/attributes`, which is the only source that
reports whether a code is actually selectable. A code is reported as pickable
when it is a leaf DECC has not greyed out, or a parent DECC marks
`allow_select`. `disabled` is inherited down the branch: DECC greys out a whole
subtree by marking its parent, so every deprecated `2.x` code is unpickable even
though only `2` carries the flag. At the time of writing 36 of 73 codes are
pickable.

`--with-descriptions` additionally reads `GET /openapi/catalog/details?catalog_type=1`
on the OpenAPI gateway, the only carrier of the per-code text. Descriptions are
worth reading before choosing: `1.1 Public Data`, for example, spells out that a
video's length and resolution count as public because they can be derived from
public data, while video id, user id and moderation status do not.

The tree is identical for `2=TEXAS` and `3=CLOVER`, and does not vary with the
transfer direction or channel. `1=ALL_SCENARIO` returns an empty tree, so a run
without `--data-id` deliberately reads the table under TEXAS rather than under
the `ALL_SCENARIO` fallback the data-version commands use.

Texas/Clover is one of at least seven catalogs DECC serves. The others
(Aggregated, Exemption, and the ROW variants) belong to other gateways and are
not what a DES-HDFS column is tagged with. Note that `catalog/list` reports only
four of them.

**Tag checking on writes.** `column create` and `column update` compare `--tag`
against this table and report the verdict, but never block on it:

- a pickable code is echoed with its name, e.g. `Category 6.1: Engineering Operational Data`
- a greyed-out code, a grouping node, or a code that is not in the table at all
  produces a `Warning:` plus the pickable codes nearest to it
- an unreachable code table produces `was not verified` and the change proceeds

This is advisory because `data_version/update` accepts any string: DECC does not
validate the tag on write, so a wrong one is only caught by a human reviewer
after submission. That is exactly why it is worth saying before the ticket
opens. It stays non-blocking so a read-only lookup being down cannot fail an
otherwise valid change.

### des-rpc annotation-plan get

Check BAM latest RPC IDL for a service and print the DECC Data Version requests needed to refresh DES-RPC annotations. This command does not write DECC by itself.

```bash
bytedcli --site i18n-tt decc des-rpc annotation-plan get [options]
```

**Options:**

- `--psm <psm>` (required) — BAM/PSM service name, e.g. `example.demo.service`
- `--rpc-method <rpcMethod>` — RPC method name to filter
- `--bam-version <version>` — BAM version to load, or `latest` (default: `latest`)
- `--cluster <cluster>` — BAM cluster (default: `default`)
- `--data-id <dataId>` — DECC Method/Data ID, if already known
- `--version <version>` — DECC Data Version number, if already known
- `--endpoint-limit <n>` — Maximum BAM RPC methods to show (default: `20`)

**Examples:**

```bash
# Verify example.demo.service is on the latest BAM IDL and inspect candidate RPC methods
bytedcli --site i18n-tt decc des-rpc annotation-plan get \
  --psm example.demo.service \
  --bam-version latest

# Print DECC load-idl / parse-idl requests for an existing draft Data Version
bytedcli --site i18n-tt decc des-rpc annotation-plan get \
  --psm example.demo.service \
  --rpc-method DemoMethod \
  --bam-version latest \
  --data-id demo-data-id \
  --version 12
```

### des-rpc direct call

Call DECC frontend/direct APIs with ByteCloud JWT. This is useful when DES-RPC data has been migrated to DECCv3 and the OpenAPI path is unavailable, or when validating IDL load/parse requests.

```bash
bytedcli --site i18n-tt decc des-rpc direct call [options]
```

**Options:**

- `--method <method>` — `GET` or `POST` (default: `GET`)
- `--path <path>` — DECC direct API path, for example `/api/v2/schema/idl/load`
- `--query <json>` / `--query-file <path>` — query params for GET-style APIs
- `--body <json>` / `--body-file <path>` — JSON request body for POST APIs
- `--timeout-ms <n>` — HTTP timeout in milliseconds
- `--dry-run` — print the direct API request without sending it

**Examples:**

```bash
bytedcli --site i18n-tt decc des-rpc direct call \
  --path /api/v2/schema/idl/load \
  --query '{"gateway":"RPC","endpoint_id":"demo-endpoint-id","data_name":"DemoMethod","is_serialized_data":false}'

bytedcli --site i18n-tt decc des-rpc direct call \
  --method POST \
  --path /api/v2/schema/idl/parse \
  --body-file ./decc-parse-body.json
```

### des-rpc channel create

Create a DECC DES-RPC Channel for a callee service. DES-RPC uses `gateway=2`.

```bash
bytedcli --site i18n-tt decc des-rpc channel create [options]
```

**Options:**

- `--name <name>` (required) — Callee service/channel name
- `--owners <owners>` (required) — Comma-separated owner usernames
- `--description <description>` — Channel description
- `--vgeo-list <vgeoList>` — Comma-separated vGeo regions; the legacy `--vgeos` alias remains accepted for compatibility
- `--domain-psm-list <psmList>` — Comma-separated `domain_psm_list` values; defaults to `--name`
- `--scenario <scenario>` — Comma-separated DECC scenario list (default: `4`)
- `--dry-run` — Print the OpenAPI request without sending it

### des-rpc data create

Create a DECC DES-RPC Data object for an RPC method under a DES-RPC Channel. Per DECC DES-RPC OpenAPI requirements, this command does not send `need_submit_data_version` or `data_version`.

```bash
bytedcli --site i18n-tt decc des-rpc data create [options]
```

**Options:**

- `--channel-id <channelId>` (required) — DECC DES-RPC Channel ID
- `--name <name>` (required) — RPC method name
- `--owners <owners>` (required) — Comma-separated owner usernames
- `--scenario <scenario>` — Comma-separated DECC scenario list (default: `4`)
- `--dry-run` — Print the OpenAPI request without sending it

### des-rpc data-version

Operate DES-RPC Data Version drafts. `create` resolves the latest Data Version whose state contains `applied` via OpenAPI detail first, falling back to DECC direct `id_list`, and uses that version as `upstream_version`. Pass `--applied-region US` or `--applied-region EU` when the base version must be selected from a specific region's applied state. Use `load-idl` to load BAM IDL, `parse-idl` to derive `json_schema`, `update` to write field annotations, and `submit` to send the version for approval. Add `submit --wait` to poll the workflow until review/apply nodes are ready and print generated ticket IDs and URLs; use `status` for later read-only checks without opening the browser.

```bash
bytedcli --site i18n-tt decc des-rpc data-version list --data-id demo-data-id
bytedcli --site i18n-tt decc des-rpc data-version get --data-id demo-data-id --version 12
bytedcli --site i18n-tt decc des-rpc data-version create --data-id demo-data-id --applied-region US
bytedcli --site i18n-tt decc des-rpc data-version load-idl --data-id demo-data-id
bytedcli --site i18n-tt decc des-rpc data-version parse-idl --data-id demo-data-id --upstream-version 12 --idl-file ./decc-idl.json
bytedcli --site i18n-tt decc des-rpc data-version update --data-id demo-data-id --version 12 --body-file ./decc-des-rpc-annotation.json
bytedcli --site i18n-tt decc des-rpc data-version update --data-id demo-data-id --version 12 --field-path _request.DemoOptions.SkipDemoField --tag demo-tag --entity demo-entity --sync YES --non-us-user-data-proof-field NO --description "Skip demo field" --reason "Refresh demo annotation"
bytedcli --site i18n-tt decc des-rpc data-version submit --data-id demo-data-id --version 12 --reason "update IDL annotation" --wait
bytedcli --site i18n-tt decc des-rpc data-version status --data-id demo-data-id --version 12
bytedcli --site i18n-tt decc des-rpc data-version set-direction --data-id demo-data-id --version 12 --scenario 9 --all --yes
bytedcli --site i18n-tt decc des-rpc data-version annotate --data-id demo-data-id --version 12 --scenario 9 --yes
```

Common options on Data Version operations:

- `--endpoint-path <path>` — Override the DECC OpenAPI path if the environment uses a different route
- `--timeout-ms <timeoutMs>` — HTTP timeout in milliseconds
- `--dry-run` — Print the OpenAPI request without sending it

`submit --wait` accepts `--wait-timeout-ms` (default `120000`) and `--poll-interval-ms` (default `3000`). A timeout returns the last observed workflow with `timed_out: true`; it does not resubmit the draft.

`set-direction --all --scenario <scenario>` merges every standard pair for that scenario while preserving existing pairs. Supported mappings are scenario `4` (CN ↔ ROW-TT), `5` (NonTT ↔ ROW-TT), and `9` (US/EU/ROW-TT/US-TTPBD directions). Like the single-pair form, it previews unless `--yes` is passed.

`annotate --scenario <scenario>` reads the correct scenario-specific Data Version; the update body matches the console contract and sends only `gateway` plus `data`.

`update --body-file` should contain the DECC Data Version fields for annotation updates, typically including `json_schema` and/or `field_infos`. The body may be either the data object itself or a full request object with a `data` object; the CLI sends a single `data-version update` request.

`data-version get/update --scenario <scenario>` accepts one positive scenario number. The DECC V3 detail and update contracts use a scalar enum, so comma-separated scenario lists are rejected before the request is sent.

Use `data-version update --field-path _request.<field>` or `--field-path _response.<field>` for targeted `json_schema` annotation patches. It reads the current Data Version with `GET /openapi/data_version/detail`, patches one schema field locally, then writes back with `POST /openapi/data_version/update`. For fields newly added by IDL parse but absent from the old schema, pass `--schema-node-file` with the DECC parse field node and `--field-path` where it should be inserted.

### des-rpc openapi call

Low-level fallback for DES-RPC OpenAPI operations that are not yet wrapped or whose path differs in the current environment.

```bash
bytedcli --site i18n-tt decc des-rpc openapi call \
  --method GET \
  --path /openapi/schema/idl/load \
  --query '{"gateway":2,"data_id":"demo-data-id"}' \
  --dry-run
```

### data-transfer-config create

Create a cross-region HDFS data transfer configuration (registers the transfer job metadata in DECC).

```bash
bytedcli --site i18n-tt decc data-transfer-config create [options]
```

**Options:**

- `--name <name>` (required) — Transfer configuration name
- `--owners <owners>` (required) — Comma-separated owner usernames
- `--data-id <dataId>` (required) — Source DECC data ID (from `dorado decc datas` or the DECC console)
- `--source-region <region>` (required) — Source DECC region
- `--source-data-name <name>` (required) — Source table name
- `--target-region <region>` (required) — Target DECC region
- `--target-channel-name <name>` (required) — Target DECC channel (database) name
- `--target-data-name <name>` (required) — Target table name
- `--dorado-project-id <id>` (required) — Dorado project ID for the transfer task
- `--dorado-project-name <name>` (required) — Dorado project display name
- `--dorado-folder-id <id>` (required) — Dorado folder ID for the transfer task
- `--dorado-folder-name <name>` (required) — Dorado folder display name
- `--partition-key <key>` — Partition key when `--partition-list` is omitted (default: `date`)
- `--partition-value <value>` — Partition value when `--partition-list` is omitted (default literal `${date}` Dorado schedule placeholder; pass as-is, not shell-expanded)
- `--partition-list <json>` — JSON array override for `partition_list`
- `--partition-list-file <path>` — JSON file with `partition_list` array
- `--task-type <taskType>` — `hdfs_extra.task_info.type` (default: `1`)
- `--gateway <gateway>` — DECC gateway type (default: `6` for HDFS)
- `--timeout-ms <timeoutMs>` — HTTP timeout in milliseconds (default: `120000`)
- `--dry-run` — Probe schema APIs and print readiness without creating the transfer config
- `--skip-hsql-column-sync` — Skip post-create patch of the target `global_hsql` task SQL
- `--source-channel-name <name>` — Source Hive database for schema comparison (defaults to DECC data channel name)
- `--channel-id <channelId>` — DECC channel/endpoint ID for schema lookup (defaults from DECC data detail)

**Regions (two lists):**

- **Dorado-mapped (required for `--source-region` / `--target-region` on this command):** `China-North`, `EU-Compliance2`, `EU-TTP2`, `Singapore-Central`, `US-East`, `US-EastRed`, `US-TTP` — used for HSQL tasks and Hive `fetch-columns`. Unmapped regions fail fast with `DECC_INPUT_ERROR`.
- **DECC registration only (`hdfs-data create`, etc.):** also includes `Asia-SouthEastBD`, `Asia_Saas`, `Singapore_Saas`, `Asia_CIS` — valid on the DECC console but not yet mapped to Dorado for transfer config.

**Examples:**

```bash
bytedcli --site i18n-tt decc data-transfer-config create \
  --name demo-transfer \
  --owners demo.user \
  --data-id 100001234 \
  --source-region EU-Compliance2 \
  --source-data-name demo_source_table \
  --target-region Singapore-Central \
  --target-channel-name demo_channel \
  --target-data-name demo_target_table \
  --dorado-project-id 12345001 \
  --dorado-project-name demo-project \
  --dorado-folder-id 12345678 \
  --dorado-folder-name demo-folder

bytedcli --site i18n-tt decc data-transfer-config create \
  --dry-run \
  --data-id 100001234 \
  --source-region EU-Compliance2 \
  --source-data-name demo_source_table \
  --target-region Singapore-Central

bytedcli --site i18n-tt --json decc data-transfer-config create \
  --name demo-transfer \
  --owners demo.user \
  --data-id 100001234 \
  --source-region EU-Compliance2 \
  --source-data-name demo_source_table \
  --target-region Singapore-Central \
  --target-channel-name demo_channel \
  --target-data-name demo_target_table \
  --dorado-project-id 12345001 \
  --dorado-project-name demo-project \
  --dorado-folder-id 12345678 \
  --dorado-folder-name demo-folder \
  --partition-list '[{"key":"date","value":"${date}"},{"key":"hour","value":"${hour}"}]'
```

**Output:** On success, JSON mode returns `id`, `data_transfer_config_id`, `transmission_task_id`, `hsql_task_id`, and `hsql_column_sync` when present. If create succeeds but post-create HSQL sync fails, the command still returns the created `id` / `hsql_task_id` with `hsql_column_sync.patched: false` and `hsql_column_sync.error` (avoid re-running create with the same `--name`). Text mode prints a warning in that case. With `--dry-run`, JSON mode returns `dry_run`, `ready`, `schema_source`, `column_count`, `steps`, and `verdict`; text mode prints the same probe summary.

**Agent Guidance:** Run `--dry-run` before create when validating a new table. It checks DECC data detail, OpenAPI field/list, Dorado DECC schema, and source Hive columns without calling `POST /openapi/data_transfer_config/create`. `--dry-run` only requires `--data-id`, `--source-region`, `--source-data-name`, and `--target-region` (plus optional partition and schema override flags); **both** `--source-region` and `--target-region` must be Dorado-mapped (see above) — unmapped values fail with `DECC_INPUT_ERROR` before create or probe. After create, the CLI patches the target `global_hsql` task `SELECT` list from the DECC-registered schema (`POST /openapi/data/field/list`). Partition keys from `--partition-list` are excluded from the `SELECT`. When the source Hive schema differs from the DECC schema, the CLI sets `bytequery.sql.global.query.direct.transfer.enabled = false`. If OpenAPI field/list is unauthorized, the CLI falls back to Dorado DECC schema and then source Hive columns; apply DECC OpenAPI permission for `/openapi/data/field/list` for the registered schema path.

**Note:** Uses the DECC OpenAPI gateway (`bc-maliva-gw.tiktok-row.net`), not the browser `decc-next-api` direct endpoint.

### apply

Apply for channel or data Owner permission. The role is inferred from `--object-type`: 1 → Channel Owner, 2 → Data Owner.

```bash
bytedcli --site i18n-tt decc apply [options]
```

**Options:**

- `--object-type <objectType>` (required) — Object type: `1` = channel, `2` = data
- `--object-key <objectKey>` (required) — Channel ID or Data ID
- `--users <users>` (required) — Comma-separated usernames to grant permission
- `--reason <reason>` (required) — Reason for the permission request

**Examples:**

```bash
# Apply for channel Owner
bytedcli --site i18n-tt decc apply \
  --object-type 1 \
  --object-key demo-channel-id \
  --users demo.user \
  --reason "Need channel access for data exchange"

# Apply for data Owner
bytedcli --site i18n-tt decc apply \
  --object-type 2 \
  --object-key demo-data-id \
  --users demo.user \
  --reason "Need data access for pipeline"

# Apply for multiple users
bytedcli --site i18n-tt decc apply \
  --object-type 1 \
  --object-key demo-channel-id \
  --users demo.user1,demo.user2 \
  --reason "Team needs channel access"
```

**Output:** On success, returns a permission ticket URL for tracking the approval process.

### ticket list

List historical DECC/OG tickets. Filters are optional; use narrow filters such as
ticket id, entity id, schema id, status, applicant, or region when available. On
the unified-v2 regional list, the CLI maps `--entity-id` to the upstream
`psm_id` selector and `--schema-id` to `endpoint_id`.

```bash
bytedcli --site i18n-tt decc ticket list [options]
```

**Options:**

- `--surface <surface>` — API surface: `unified-v2`, `unified-v1`, or `portal` (default: `unified-v2`)
- `--id <id>` — Ticket/object id filter
- `--entity-id <id>` — Entity id filter
- `--schema-id <id>` — Schema id filter
- `--type <type>` — Ticket type filter
- `--page <n>` — Page number, 1-based (default: `1`)
- `--page-size <n>` — Page size (default: `20`)
- `--status <status>` — Filter by ticket status
- `--applicant <applicant>` — Filter by applicant username
- `--region <region>` — Filter by ticket region

**Examples:**

```bash
bytedcli --site i18n-tt decc ticket list \
  --surface unified-v2 \
  --entity-id demo-entity-id \
  --region US \
  --page 1 \
  --page-size 20

bytedcli --site i18n-tt --json decc ticket list \
  --surface unified-v2 \
  --status pending \
  --region EU \
  --applicant demo.user
```

**Output:** Text mode prints a compact ticket table, including an `Interface` column with the reviewed endpoint (HTTP path plus method). JSON mode returns the parsed ticket list, pagination, surface, `current_count`, and raw response payload; each ticket carries `channel_name`, normalized from `channel_data.name`, so a ticket list does not need one `ticket get` per row to answer which endpoint a ticket belongs to. The column falls back to `endpoint_name` and is empty when DECC returns neither, so it never shows a service name in place of an interface. `total` is present only when DECC supplied an authoritative total; the CLI never substitutes the current page length for a missing total. An unrecognized collection shape is a structured parse error rather than an empty list.

`page_info` always answers with a `page_id` and `page_size`, filling in the requested values when DECC returned none, so `page_info_reported` says which of `page_id`, `page_size` and `total` actually came from the server. Anything that has to prove it walked a whole list must read `page_info_reported` first; the numbers alone cannot tell a server that honoured the request from one that ignored it.

### ticket get

Get DECC/OG ticket detail by ticket ID or DECC web URL. Exactly one of `--url` or `--ticket-id` is required.

```bash
bytedcli --site i18n-tt decc ticket get [options]
```

**Options:**

- `--url <url>` — Trusted DECC ticket detail URL ending in `/ticket/detail/<id>[/<version>]`. The CLI extracts the ticket ID and version. It is mutually exclusive with `--ticket-id`.
- `--surface <surface>` — API surface: `unified-v2`, `unified-v1`, or `portal`. When omitted, the CLI tries those surfaces in that order after explicit fallback-safe errors. Passing this option disables fallback.
- `--ticket-id <ticketId>` — DECC ticket ID (required unless `--url` is given; mutually exclusive with `--url`)
- `--version <version>` — Ticket version; overrides a version parsed from the selected URL. Short (non-numeric) ticket IDs usually require it: without a version every surface reports "not found", which does not prove the ticket is missing.

**Examples:**

```bash
bytedcli --site i18n-tt decc ticket get \
  --ticket-id demo-ticket-id \
  --version 3

bytedcli --site i18n-tt decc ticket get \
  --url '<decc-ticket-detail-url>'

bytedcli --site i18n-tt --json decc ticket get \
  --ticket-id demo-ticket-id \
  --version 3
```

**Output:** Text mode prints a compact ticket summary, including the reviewed `Interface`, available actions, current/total iterations, unresolved rejected fields, the top-level and current-iteration schema digests, `schema_consistent`, and `effective_schema_source`. In JSON, `actions` and `iteration_summary` remain top-level siblings; `schema_summary` contains the current iteration, rejected fields, schema digests, consistency, effective source, and inspection errors beside the normalized ticket detail and raw response payload. The top-level schema is the effective source when present because that is what the review page reads. A versioned query only succeeds when the returned ticket proves the requested version. On `unified-v2`, use `full_iteration_history[].review_comments[]` for complete field-level reject comments when the activity summary truncates paths as “and N more”.

`version_history` is a typed field: every entry carries a numeric `version_num`, and a status where DECC reported one. Entries the schema cannot read are dropped rather than failing the whole detail, and `version_history_unreadable_count` appears only when at least one was dropped. So an empty `version_history` with no count means DECC really returned no versions, while an empty one with a count means every entry was unreadable. When the whole field arrived as something other than a list, `version_history` is absent and only the count of 1 remains. The untouched list stays under `raw.version_history` in each case. `ticket iteration create` fails closed on both.

### ticket iteration create

Create a corrected iteration for one exact rejected unified-v2 endpoint ticket. The command is dry-run by default and builds the new `schema_snapshot` from the rejected ticket, copying only description-only changes explicitly listed with `--expect-field` from the selected version-zero draft. Unrelated owner, request-body, structure, tag, or metadata differences are not carried into the iteration.

What `create_iteration` does: it writes the new iteration's `schema_snapshot`. It does not rewrite top-level `ticket.schema`. The review page renders `ticket.schema` for the current iteration, so a reviewer sees the iteration's change only after switching the Base selector to iteration n-1. Cancelling a version does not carry that version's priority request to a new version.

**Options and constraints:**

- Exactly one of `--url` or `--ticket-id` is required.
- `--version` is required unless the selected ticket URL contains the version. A conflicting URL version and explicit `--version` are rejected.
- `--draft-id`, `--caller-vpc`, `--callee-vpc`, and `--reason` are required.
- `--expect-field <path>` is a repeatable selection set. Only selected description-only draft changes are copied; unlisted draft changes are ignored rather than treated as unexpected. Compare `rejected_fields` with the intended corrections and make sure every field required for this iteration is selected.
- `--dry-run` and `--yes` are mutually exclusive. Omitting both is equivalent to dry-run.
- `--expect-snapshot <sha256>` is accepted only with `--yes` and must match the reviewed dry-run.

```bash
bytedcli --site i18n-tt decc ticket iteration create \
  --url '<versioned-decc-ticket-url>' \
  --draft-id demo-draft-id \
  --caller-vpc demo-office-net \
  --callee-vpc EU_demo-vpc \
  --reason "Improve rejected field descriptions" \
  --expect-field resp.body.data.name \
  --dry-run

bytedcli --site i18n-tt decc ticket iteration create \
  --url '<versioned-decc-ticket-url>' \
  --draft-id demo-draft-id \
  --caller-vpc demo-office-net \
  --callee-vpc EU_demo-vpc \
  --reason "Improve rejected field descriptions" \
  --expect-field resp.body.data.name \
  --expect-snapshot 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --yes
```

The preflight verifies exact ticket/version, `rejected` status, `create_iteration` action, current iteration number, region, entity, method, path, and caller/callee assurance path. With no `--expect-field`, `changed_fields` lists the candidate draft changes and `would_create_iteration` is false. With selectors, `changed_fields` lists only the description corrections selected for the new snapshot; unlisted draft changes are deliberately omitted. `change_categories` re-keys the same changes by the kind of attribute each one touched. The diff is per-field, so the groups only ever describe schema fields: `description` for a field's description, `tag` for its compliance tags, `structure` for its type, value or key set as well as any added or removed path, and `metadata` for every other attribute the field snapshot carries. Endpoint-level changes such as owners or assurance paths are not part of this diff at all. It carries paths only, one path can land in more than one group, and the per-attribute detail stays in `changed_fields`, which remains the complete diff. The result also includes unresolved `rejected_fields`, a `would_create_iteration` verdict, and a `snapshot_digest`. If the original request did not explicitly authorize a live create, stop after dry-run and wait for affirmative user approval.

Two independent preflights run before any POST, each with its own error code, and neither sends a write:

- The requested version must equal the highest `version_history[].version_num`, reported back as `latest_version`. The server accepts `create_iteration` only on the newest version, and a newest version that is already cancelled still counts as newest. A version proven not to be the newest fails with `DECC_TICKET_ITERATION_NOT_LATEST`. Not being able to prove which version is newest is a different fact and has its own code, `DECC_TICKET_ITERATION_LATEST_UNVERIFIED`: it covers an absent history, an empty one, and one whose entries this build could not read, and a missing history is never read as "this is the newest version". A `--version` that is not a positive integer is the caller's own input error and fails earlier with `DECC_INPUT_ERROR`.
- A requested version whose own status is cancelled fails with `DECC_TICKET_ITERATION_CANCELLED`, because the server does not allow `create_iteration` on a cancelled ticket.

Both carry `details.refused_by: "cli"`, which distinguishes a CLI-local refusal from a server rejection (`refused_by: "server"`). A passing preflight never replaces server-side validation, and the live write still reads the result back.

A dry run refuses `DECC_TICKET_ITERATION_NOT_LATEST` and `DECC_TICKET_ITERATION_CANCELLED` the same way a live create does, because both are proven blockers. `DECC_TICKET_ITERATION_LATEST_UNVERIFIED` is different: it says the newest version could not be established, so a dry run reports it in `warnings` instead of throwing, and the reviewer still gets the diff. On that path `latest_version` is `"unverified"` rather than a number, so the field never echoes the requested version back as if it had been proven newest. A live create refuses on it, so a live result's `warnings` is always empty.

A live write re-reads the ticket and draft before POST, then reports five outcomes. Each is the record of a separate check, so do not infer any of them from another; in particular a persisted snapshot says nothing about what the review page renders:

- `iteration_snapshot_persisted` — the new iteration's `schema_snapshot` was read back and its canonical digest matched. It is the explicit record that this check ran; a live result only ever reports `true`, because a failed readback throws instead of returning.
- `main_schema_matches_snapshot` — whether top-level `ticket.schema` matches that snapshot: `true`, `false`, or `"unverified"` when one of the two schemas could not be read. It restates `schema_consistent` from the same readback rather than measuring the schema a second time, so the two never disagree.
- `status_after` — the ticket status after the write.
- `iteration_diff_entry_count` — how many entries `GET /unified_api/v2/ticket/diff` reports between iteration n-1 and n. It counts entries and does not inspect them, so it shows that the server sees a difference, not which one, and `0` does not mean the write failed. It is `"unverified"` when the endpoint gives no usable answer, which includes iteration 1; that never changes the digest-proven write result.
- `change_categories` — the changed paths grouped by attribute kind, as described above.

A dry run carries the same five fields with dry-run values: `iteration_snapshot_persisted` is `false` because no iteration was written, `iteration_diff_entry_count` is `"unverified"` because there is no new iteration to diff, and `main_schema_matches_snapshot` describes the ticket as it was read before the write.

Every result also carries `reviewer_visibility`, a fixed statement of what the review page shows, and `ticket_url_form`, which reports how the detail URL was derived: `versioned`, `id_only`, or `unverified` when neither the ticket's region nor its surface says which shape the detail page takes, including a versioned discriminator for which no version was returned. An `unverified` URL is the id-only form and may not open the exact version. `ticket cancel` and `gateway endpoint submit` report the same field and print the same warning.

The two discriminators are not independent. Both observations behind them moved region and surface together, so the region decides the shape and the surface only stands in for it when the region is unknown; reading them as separate votes would make a US unified-v2 ticket, which is what every US Gateway submit produces, look like a contradiction.

`DECC_TICKET_ITERATION_OUTCOME_UNKNOWN` means the write may have succeeded; do not retry blindly, and inspect the returned ticket URL first.

### ticket iteration submit

Reset one exact rejected unified-v2 ticket iteration to pending without changing its schema. This command is for resuming review only; it is not a schema correction mechanism.

```bash
bytedcli --site i18n-tt decc ticket iteration submit \
  --url '<versioned-decc-ticket-url>' \
  --reason "Resume review without changing schema" \
  --dry-run

bytedcli --site i18n-tt decc ticket iteration submit \
  --url '<versioned-decc-ticket-url>' \
  --reason "Resume review without changing schema" \
  --expect-snapshot 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --yes
```

For a rejected ticket, preflight requires the exact ticket/version and a `reset to pending` action. Live execution requires the reviewed snapshot, performs one operate request, then reads the ticket back and requires pending status for the same iteration. If the exact ticket is already pending and both schema digests match, `--yes` returns an idempotent no-op without requiring a snapshot or sending a POST. Every pending result compares the canonical digest of top-level `ticket.schema` with the current iteration's `schema_snapshot`; a mismatch, missing schema, or unparsable schema fails with `DECC_TICKET_SCHEMA_DIVERGENCE` and `details.refused_by: "cli"`. Because that one code covers both a real mismatch and a schema that could not be read, it says only that the two could not be proven equal, and it states no recovery action: pending status alone does not prove the reviewer-visible schema changed. `details.refused_by` is `"cli"` only on the preflight; the same check on the post-write readback reports `phase: "readback"` with `write_attempted: true` instead, because that path did send a write. The result carries the same `reviewer_visibility` statement and the same `ticket_url_form` as `ticket iteration create`. Do not retry the reset blindly.

### ticket priority get / request

Read priority for one exact ticket version, or create a BPM priority approval routed to the applicant's +1. Both commands accept `--url <ticket-detail-url>` or `--ticket-id <id> --version <version>`; `--surface` is optional and strict when supplied. An id-only URL (including US/portal links) also requires `--version <version>`. Conflicting URL and explicit versions are rejected.

```bash
bytedcli --site i18n-tt decc ticket priority get --ticket-id demo-ticket-id --version 3
bytedcli --site i18n-tt decc ticket priority request \
  --ticket-id demo-ticket-id --version 3 \
  --level urgent --reason "Demo release deadline" --dry-run
# After explicit user authorization, reuse the exact reviewed payload and token.
bytedcli --site i18n-tt decc ticket priority request \
  --ticket-id demo-ticket-id --version 3 \
  --level urgent --reason "Demo release deadline" \
  --confirmation-token '<reviewed-token>' --yes
```

`get` always reports `ticket_status` alongside `priority.status`, the BPM link and a version notice. A cancelled ticket can retain an Approved BPM record. That record does not transfer to a new ticket version. Approved priority is shown as Urgent (+1h) or Expedited (+2h), with Processing while the ticket remains pending; Rejected/Closed are shown separately and other nonempty statuses use the UI's Requested label.

`request` requires `--level urgent|expedited` and a nonempty `--reason`. It derives applicant, ticket link, gateway, geography, data version, entity id and the single-ticket count from the selected ticket context. It accepts explicit OG/AG metadata (including a unique schema compliance project for the ticket region); missing or contradictory metadata fails closed rather than guessing. The numeric request geography is US=1, EU=2, ROW=3; CLI callers use semantic levels. The ticket detail must explicitly provide `data_version`; an absent data version is not inferred from the ticket version. The preview shows the complete resolved `payload`, the existing `priority`, `warnings`, `would_request`, and `confirmation_token`.

A real request requires `--yes --confirmation-token <token>` from the same reviewed dry-run. The token binds the payload, operator, surface, ticket status, existing priority and duplicate decision. Only pending tickets can request priority. Existing Approved/Requested/processing priority makes `would_request: false` and live fails with `DECC_TICKET_PRIORITY_DUPLICATE` unless `--force-duplicate` was also included in the reviewed dry-run. Rejected/Closed records do not block a new request. The live response's `priority` remains the preflight observation; `bpm_ticket_link` identifies the newly created BPM approval, whose status can then be queried with `get`.

**Safety:** If the user's original request did not explicitly authorize this write, show the dry-run result and stop for affirmative user confirmation. An agent's own validation is not user authorization. The request creates an external BPM approval; generating a preview or a token does not grant authorization. A failed priority lookup is never treated as absence. Only `msg: success` with explicit `data: null` or an exact status-only `data: {"status":"Created"}` object represents no request; missing or malformed data fails closed. These BFF endpoints use `msg/data`, not unified_api `status_code/data`. An uncertain POST is not retried and raises `DECC_TICKET_PRIORITY_OUTCOME_UNKNOWN`; inspect the same version's priority and BPM before any retry.

### ticket cancel

Validate and cancel one exact pending DECC ticket version. The command is dry-run by default; a real write requires `--yes`.

```bash
bytedcli --site i18n-tt decc ticket cancel [options]
```

**Options:**

- `--url <url>` — Versioned DECC ticket detail URL; mutually exclusive with `--ticket-id`
- `--ticket-id <ticketId>` — DECC ticket ID; mutually exclusive with `--url`
- `--version <version>` — Exact ticket version (required unless present in `--url`)
- `--surface <surface>` — Strict API surface. When omitted, preflight tries `unified-v2`, `unified-v1`, then `portal` only after an explicit fallback-safe error.
- `--reason <reason>` (required) — Withdrawal reason
- `--dry-run` — Validate exact version, status, and available actions without writing
- `--yes` — Execute cancellation after validation
- `--discard-priority` — Explicitly accept losing this version's approved, requested or processing priority benefit; required for a live cancellation when the priority check warns

**Examples:**

```bash
bytedcli --site i18n-tt decc ticket cancel \
  --url '<decc-ticket-detail-url>' \
  --reason "Withdraw incorrect tagging" \
  --dry-run

bytedcli --site i18n-tt decc ticket cancel \
  --ticket-id demo-ticket-id \
  --version 3 \
  --reason "Withdraw incorrect tagging" \
  --yes
```

**Safety:** Preflight requires the exact version, `pending` status, and a `cancel` action. Both dry-run and live read the version's priority status first. Approved/Requested/processing priority produces `warnings` and `discard_priority_required: true`; live additionally requires `--discard-priority`. A failed lookup stops cancellation even with that flag. For `cancel --discard-priority`: If the user's original request did not explicitly authorize this write, show the dry-run result and stop for affirmative user confirmation. An agent's own validation is not user authorization. If the user's original request did not explicitly authorize a real cancellation, show the dry-run result and stop for affirmative user confirmation; only then may the exact same selector/version/reason be rerun with `--yes`. An agent's own validation is not user authorization. Already-cancelled versions return idempotently. After a write, the CLI reads the same version back. `DECC_TICKET_CANCEL_OUTCOME_UNKNOWN` means the request may have reached DECC but could not be verified; inspect the returned versioned URL before retrying.

### ticket comment list

List comments for a DECC ticket by ID or ticket detail URL. The DECC comment API can return a shared comment pool; the CLI only returns comments that can be correlated to the requested ticket.

```bash
bytedcli --site i18n-tt decc ticket comment list [options]
```

**Options:**

- `--ticket-id <ticketId>` — DECC ticket ID; required unless `--url` is given and mutually exclusive with it
- `--url <url>` — DECC ticket detail URL; extracts the ticket ID and is mutually exclusive with `--ticket-id`
- `--page <n>` — 1-based page within the safely correlated response pool (default: `1`)
- `--page-size <n>` — Comments per page after safe correlation (default: `20`)

**Examples:**

```bash
bytedcli --site i18n-tt decc ticket comment list \
  --ticket-id demo-ticket-id \
  --page 1 \
  --page-size 20

bytedcli --site i18n-tt decc ticket comment list \
  --url '<decc-ticket-detail-url>'

bytedcli --site i18n-tt --json decc ticket comment list \
  --ticket-id demo-ticket-id
```

**Output:** Text mode prints a compact comment table scoped to the ticket. JSON always includes the requested `page`, `page_size`, and returned `current_count`. Pagination is applied locally after safe ticket correlation because this upstream endpoint does not expose a verified ticket-scoped pagination contract; no `total` is reported. When upstream comments have no ticket-identifying field, the CLI withholds the shared pool and returns `comments: []`, `current_count: 0`, and `filtered: false`.

## Gateway tagging workflow and failure recovery

1. Keep authentication on `--site i18n-tt`; USTTP/EUTTP are business regions selected with `--region`, not authentication sites.
2. Scope every check by service entity, exact method/path, stage, and US/EU region. Never use a finished ticket or another region's latest version as proof of the requested region's current schema.
3. Use `gateway tagging get` for the verdict and never supplement or replace it with Chrome/browser evidence. If the CLI cannot prove the result, stop and report the error or `unverified` verdict. US requires `tx_catalog_id` (or `not_user_data=true`); EU requires `tt_catalog_id` (or `not_user_data=true`).
4. Before claiming completeness, derive the full leaf-field set from the authoritative IDL, HTTP binding, or observed runtime contract and repeat `--expect-field` for every canonical path. Run one exact `--path` per contract check. Without expected fields, `contract_verdict=unverified`; `0/0` only means DECC registered no leaf fields and cannot prove API contract completeness.
5. Treat missing collections/totals needed for pagination, malformed schemas, and list/detail mismatches as errors rather than zero matches or completed tagging.
6. Pass `{{n}}` wildcard paths exactly as DECC stores them, wrapped in single shell quotes. The upstream `--path` filter is a prefix match, so a complete wildcard path matches nothing server-side (percent-encoding does not help); the CLI therefore queries the longest static prefix — everything before the first brace — and matches the exact path locally. `gateway tagging get` pages through that prefix itself, so a wildcard path audits normally; `gateway endpoint list` only filters the page you asked for. A wildcard lookup that still matches nothing returns `DECC_GATEWAY_ENDPOINT_NOT_FOUND` with the static-prefix listing plus the `gateway endpoint get --id <endpoint_id> --stage <stage>` fallback — never an empty success — and from `endpoint list` it means "not on this page". Check both stages: a wildcard endpoint often exists only as approved or only as draft. Prefix queries widen the result set, so they consume more of the `pages`/`listed_rows` budget than an exact path; one audit paginates each distinct prefix once and reuses it across every `--path` that shares it.
7. If `DECC_GATEWAY_REGION_MISMATCH` or `DECC_GATEWAY_REGION_AMBIGUOUS` is returned, preserve the CLI evidence and stop. The list or detail response could not prove one target control plane; do not guess an assurance path, switch regions, or substitute Chrome. The error does not imply that a detail call was made.
8. If `DECC_GATEWAY_RESOURCE_LIMIT` is returned, do not use partial work as a verdict. When `details.phase` is `submit_pending_ticket_scan`, the limit was reached while listing the entity's tickets, which neither `--path` nor `--method` narrows: no submit was sent, so confirm with `decc ticket list --entity-id <id>` that no ticket for this endpoint is still open before retrying. Otherwise, for `pages` or `listed_rows`, narrow the path set; `--method` does not reduce endpoint-list pagination, so stop and report the path/resource if one path alone exceeds the limit. For `candidates` or `detail_requests`, narrow the path set and specify an exact method. For `duration_ms`, retry once and use `details.phase` to distinguish authentication from an upstream request timeout. For `metadata_units`, `audit_units`, `output_fields`, `path_bytes`, or `response_bytes`, retry smaller batches only when multiple endpoints contributed; if one endpoint exhausted the limit, stop and report its ID and resource.

## Gateway draft mutation workflow and failure recovery

1. Preview every create, endpoint update, field update, and assurance-path mutation first. Endpoint/field/assurance-path live writes require both explicit authorization and the exact `--confirmation-token` emitted by that same reviewed dry-run; never reuse a token after the draft or payload changes.
2. Prefer `gateway field update` for one existing field. Semantic catalog/tag options and compatible top-level keys are stored under `compliance_tag`; unknown attributes and null/invalid tag values are rejected before writing.
3. Use `gateway endpoint update` for intentional shape changes. Inspect the bounded complete-state diff, and do not use `--allow-delete --yes` unless every reported deletion is expected. Text mode always prints every captured deletion even when ordinary additions/changes are compacted.
4. Real mutations recheck and write `version=0`, then verify the persisted complete schema and exact assurance-path multiset. HTTP 408/425/429 are ambiguous rather than definite rejections. On a verification or outcome-unknown error, use the inspect command from the error and do not retry blindly.

## Ticket workflow and failure recovery

1. Prefer `ticket list/get` and `ticket comment list` over opening a browser. If a ticket URL is available, pass it directly with `--url`.
2. Omit `--surface` when automatic `unified-v2` → `unified-v1` → `portal` fallback is desired. An explicit surface is strict.
3. Treat a missing `total` as unknown, not zero or complete. Use `current_count` for the current page. Read `channel_name` (text column `Interface`) to see which endpoint each listed ticket belongs to instead of running one `ticket get` per row; an empty column means DECC returned no endpoint identity for that ticket.
4. A short (non-numeric) ticket ID usually needs `--version`. With `--surface` omitted, every surface on the fallback chain reports a missing version as "not found", so read the version with `decc ticket list --id <id>` and retry; only an empty ticket list proves the ticket does not exist. A numeric ticket ID resolves without a version, and its lookup failure is reported without version guidance.
5. Only `filtered: true` comments have been safely correlated to the requested ticket.
6. Preview cancellation first. Unless the original request explicitly authorized the write, display the preview and wait for affirmative user confirmation before using `--yes` with the same selector/version/reason. If verification is uncertain, inspect the ticket URL before any retry.
7. A ticket detail URL has two shapes and the CLI picks one from known discriminators only, never from the ticket-id shape. A `US` ticket, or one read from the `portal` surface when its region is unknown, uses `/ticket/detail/<id>`; appending a version segment makes that page report that it cannot find the item. An `EU` ticket, or a `unified-v2` one whose region is unknown, uses `/ticket/detail/<id>/<version>` and does not render without it. The region decides and the surface only stands in for it, because both observations behind these rules moved the two together. The region is read first and the surface only answers when the region says nothing, so an unlisted region on `portal` still gives the id-only shape. When neither says anything (an absent or `unified-v1` surface together with an absent or unlisted region, or a versioned discriminator with no version to render), the id-only shape is returned with `ticket_url_form: "unverified"`. The version is still reported in every result payload: as `version` on the ticket-workflow results, and as `ticket_version` on `gateway endpoint submit`'s `submissions[]`.
8. `details.refused_by` says who refused a write: `"cli"` for a local preflight that sent nothing, `"server"` for a rejection DECC returned. `"cli"` therefore proves nothing was sent, and `"server"` is only ever read out of a submit response, so on that one the write did go out. The field is absent whenever neither party refused, which is the case for an outcome that could not be determined. `write_attempted` is a separate marker, used where the same check runs on both sides of a write: `ticket iteration submit` reports `phase: "readback"` with `write_attempted: true` for its post-write schema check. It does not accompany a server refusal. A CLI refusal is not evidence about server state beyond what its details report.
9. Cancelling a ticket version discards the priority benefit on that version; its BPM record may remain Approved. `ticket priority get` reports both states. The record belongs to one version and is not carried to a new one. `cancel` checks priority before writing and requires `--discard-priority` when the record is approved, requested or processing.
10. `ticket priority request` previews the resolved payload and existing priority; a live request requires explicit authorization and the same preview's `--confirmation-token --yes`. Existing priority requires a deliberate `--force-duplicate` decision and a fresh preview. A lookup failure is not proof of absence.

## API Endpoints

| Command                                                                 | Gateway                                 | Endpoint                                                                                                                  |
| ----------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `gateway service list`                                                  | Direct unified API                      | `GET /unified_api/v2/services/list`                                                                                       |
| `gateway endpoint list`                                                 | Direct unified API                      | `GET /unified_api/v2/endpoints/list`                                                                                      |
| `gateway endpoint get`                                                  | Direct unified API                      | `GET /unified_api/v2/endpoints/detail`                                                                                    |
| `gateway tagging get`                                                   | Direct unified API                      | `GET /unified_api/v2/endpoints/list`, regional `GET /unified_api/v2/endpoints/detail`                                     |
| `gateway endpoint create`                                               | Direct unified API                      | `POST /unified_api/v2/endpoint/draft/create`, readback `GET /unified_api/v2/endpoints/detail?version=0`                   |
| `gateway endpoint update`                                               | Direct unified API                      | `GET /unified_api/v2/endpoints/detail?version=0`, `POST /unified_api/v2/endpoint/draft/update`, readback `GET ?version=0` |
| `gateway field update`                                                  | Direct unified API                      | `GET /unified_api/v2/endpoints/detail?version=0`, `POST /unified_api/v2/endpoint/draft/update`, readback `GET ?version=0` |
| `gateway assurance-path create`                                         | Direct unified API                      | `GET /unified_api/v2/endpoints/detail?version=0`, `POST /unified_api/v2/endpoint/draft/update`, readback `GET ?version=0` |
| `hdfs-channel create`                                                   | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/channel/create`                                                                                            |
| `hdfs-data create`                                                      | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/data/create`                                                                                               |
| `hdfs-data data-version list`                                           | Direct V3 (`decc.tiktok-row.net`)       | `GET /decc-next-api/v3/data_version/list`                                                                                 |
| `hdfs-data data-version *` scenario lookup                              | Direct V3 (`decc.tiktok-row.net`)       | `GET /decc-next-api/v3/data/detail`                                                                                       |
| `hdfs-data data-version get`                                            | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `GET /openapi/data_version/detail`                                                                                        |
| `hdfs-data data-version create`                                         | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/data_version/create`                                                                                       |
| `hdfs-data data-version column create`                                     | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `GET /openapi/data_version/detail`, `POST /openapi/data_version/update`, readback `GET /openapi/data_version/detail`      |
| `hdfs-data data-version column update`                                  | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `GET /openapi/data_version/detail`, `POST /openapi/data_version/update`, readback `GET /openapi/data_version/detail`      |
| `hdfs-data data-version column delete`                                    | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `GET /openapi/data_version/detail`, `POST /openapi/data_version/update`, readback `GET /openapi/data_version/detail`      |
| `hdfs-data data-version submit`                                         | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/data_version/submit`                                                                                       |
| `hdfs-data data-version cancel`                                         | Direct V3 (`decc.tiktok-row.net`)       | `POST /decc-next-api/v3/data_version/cancel`, readback `GET /decc-next-api/v3/data_version/list`                          |
| `hdfs-data category list`                                               | Direct V3 (`decc.tiktok-row.net`)       | `GET /decc-next-api/v3/schema/gateway/attributes`                                                                         |
| `hdfs-data category list --with-descriptions`                           | Both                                    | plus `GET /openapi/catalog/details?catalog_type=1` on `bc-maliva-gw.tiktok-row.net`                                       |
| `des-rpc channel create`                                                | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/channel/create`                                                                                            |
| `des-rpc data create`                                                   | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/data/create`                                                                                               |
| `des-rpc data-version list/get/create/load-idl/parse-idl/update/submit` | Direct V3 (`decc.tiktok-row.net`)       | `GET/POST /decc-next-api/v3/data_version/*`                                                                               |
| `des-rpc data-version status`, `submit --wait`                          | Direct V3 (`decc.tiktok-row.net`)       | `GET /decc-next-api/v3/state_machine/workflow/detail`                                                                     |
| `des-rpc direct call`                                                   | Direct (`decc.tiktok-row.net`)          | Caller-provided `GET`/`POST` path                                                                                         |
| `des-rpc openapi call`                                                  | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | Caller-provided `GET`/`POST` path                                                                                         |
| `data-transfer-config create`                                           | OpenAPI (`bc-maliva-gw.tiktok-row.net`) | `POST /openapi/data_transfer_config/create`, `POST /openapi/data/field/list` (schema sync)                                |
| `apply`                                                                 | Direct (`decc.tiktok-row.net`)          | `POST /decc-next-api/v3/auth/object_user_role/apply`                                                                      |
| `ticket list`                                                           | Direct unified/portal API               | `GET /unified_api/v2/tickets/list`                                                                                        |
| `ticket list --region`                                                  | Direct unified API                      | `GET /unified_api/v2/tickets/list_by_region`                                                                              |
| `ticket get`                                                            | Direct unified/portal API               | `GET /unified_api/v2/tickets/detail`                                                                                      |
| `ticket iteration create`                                               | Direct unified-v2 API                   | `POST /unified_api/v2/tickets/operate`, readback `GET /unified_api/v2/ticket/diff?diff_type=iteration`                     |
| `ticket iteration submit`                                               | Direct unified-v2 API                   | `POST /unified_api/v2/tickets/operate`                                                                                    |
| `ticket cancel`                                                         | Direct unified/portal API               | `POST /unified_api/v2/tickets/operate`                                                                                    |
| `ticket comment list`                                                   | Direct (`decc.tiktok-row.net`)          | `GET /api/v2/comment/list`                                                                                                |

## Scenario Reference

| Value | Name                    | Description               |
| ----- | ----------------------- | ------------------------- |
| 0     | UNKNOWN_SCENARIO        | Unknown                   |
| 1     | ALL_SCENARIO            | All scenarios             |
| 2     | TEXAS                   | Texas data sovereignty    |
| 3     | CLOVER                  | Clover data sovereignty   |
| 4     | CN_CROSS_BORDER         | CN cross-border transfer  |
| 5     | TT_NONTT                | TT & NonTT data isolation |
| 6     | EU_US_DIRECT_CONNECTION | EU-US direct connection   |
| 7     | ROW_HDFS_BOE            | row-hdfs/boe gateway      |
| 8     | ROW_HDFS_PRODUCTION     | row-hdfs/prod gateway     |
| 9     | RPC_TEXAS_CLOVER_MIXED  | RPC Texas/Clover mixed    |
| 10    | HDFS_TEXAS_CLOVER_MIXED | HDFS Texas/Clover mixed   |
