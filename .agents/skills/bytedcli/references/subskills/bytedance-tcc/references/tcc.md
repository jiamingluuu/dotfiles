# TCC

```bash
bytedcli tcc site list
bytedcli --site cn tcc namespace list --page 1 --size 50
bytedcli --site cn tcc namespace search "keyword" --scope all --page 1 --size 50
bytedcli --site cn tcc namespace get "namespace"
bytedcli --site boe tcc namespace psm-dependency list "namespace" --env boe

bytedcli tcc config list "namespace" --region CN --keyword "demo" --dir-path "/default"
bytedcli tcc config list "namespace" --region CN --keyword "queue-id" --search-field value --dir-path "/default"
bytedcli tcc config get "namespace" "config_name" --region CN --dir "/default"
bytedcli tcc config get "namespace" "config_name" --region CN --dir "/encrypt" --decrypt
bytedcli tcc config version list "namespace" "config_name" --region CN --dir "/default"
bytedcli tcc config version get "namespace" "config_name" --ver 3 --region CN --dir "/default"
bytedcli tcc config version diff "namespace" "config_name" --from-version 2 --to-version 3 --region CN --dir "/default"
bytedcli --site i18n-bd tcc config dir list "namespace" --env ppe_xxx
bytedcli --site i18n-bd tcc config meta list --env ppe_xxx

bytedcli --site cn tcc config create "namespace" "config_name" --env ppe --region CN --dir "/default" --description "demo config" --data-type yaml --encrypted true --value "a: b"
bytedcli --site cn tcc config update "namespace" "config_name" --env ppe --region CN --encrypted false --value "a: b"
# Only update the explicitly requested region; do not expand same-key sync-group peers
bytedcli --site cn tcc config update "namespace" "config_name" --env ppe --region CN --no-sync-group --value "a: b"
# When the config belongs to a synced region group (for example CN + China-East),
# config update automatically expands extend_regions and update_base_version to all existing copies in that group.
bytedcli --site i18n-bd tcc config import "namespace" --config-ids "123,456" --target-env ppe_xxx
# If --target-env reports NO_ACTIVE_ENV_FOUND, the PPE lane env does not exist yet; create it first
bytedcli --site i18n-bd tcc env create "namespace" --env ppe_xxx --regions "Singapore-Central"
# tcc env create resolves the namespace's ns_id, calls env/create, then reads back
# via tcc env list to confirm the new env appears; it returns a warning (not a
# silent success) if the env is not yet visible in the read-back.
# tcc env delete is destructive and cannot be undone. Without --dry-run/--yes it
# prompts for confirmation on an interactive terminal, and requires --yes on a
# non-interactive one. --dry-run only resolves ns_id and prints the delete
# request without submitting it. After deleting, it reads back via tcc env list
# and returns a warning (not a silent success) if the env still appears.
bytedcli --site i18n-bd tcc env delete "namespace" --env ppe_xxx --dry-run
bytedcli --site i18n-bd tcc env delete "namespace" --env ppe_xxx --yes

# config create requires a non-empty --description and automatically falls back
# to the V2 service_id create API for former_tcc / tcc_v2 namespaces.
# For ppe / ppe_* envs whose TCC service is not active yet, config create
# automatically creates that ENV TCC service and binds it to the requested
# --region. If the requested region is not available in ENV TCC conf spaces,
# the command fails with available regions instead of binding to another region.
# config create's --data-type defaults to yaml and is NOT auto-detected from
# --value / --file. Always infer the data type from the actual content before
# calling config create and pass it explicitly:
#   - JSON.parse-able object/array (e.g. {...} / [...])         -> --data-type json
#   - YAML document (key: value, indented lists, --- markers)   -> --data-type yaml
#   - Plain text that is neither valid JSON nor YAML structure  -> --data-type string
#   - When using --file, prefer the file extension first
#     (.json -> json, .yaml/.yml -> yaml, otherwise fall back to content-based rules)
#   - When uncertain, prefer --data-type string to avoid TCC mis-parsing the value as YAML.
# TCC v2: explicitly control CDN; omitted --enable-cdn defaults to false, including updates.
bytedcli --site cn tcc config update "demo.namespace" "demo_config" --env ppe --region CN --enable-cdn true --value '{"enabled":true}'
# Web V1 rejects --enable-cdn (both true and false).
# config create/config update accept --encrypted true|false for Web V1 namespaces.
# config update also falls back to the V2 service_id upsert API for
# former_tcc / tcc_v2 namespaces, using the requested --region and --dir.
# config version diff compares two explicit version numbers and outputs a unified diff.
# JSON config data is formatted before diffing; use --context-lines to tune context.
# former_tcc / tcc_v2 namespaces do not support --encrypted; the CLI fails fast
# instead of silently ignoring the flag.
# deployment deploy switches former_tcc / tcc_v2 prod namespaces to the TCC AG V2
# activity path: config/upsert_deploy/v2 + deployment/list/base_info/step_info/operate.
# For ppe/ppe_* and other non-prod envs it uses the TCC OpenAPI instead:
#   - --publish-mode manual     -> /api/v2/open/config/modify_only (modify, do not publish)
#   - --publish-mode auto/force-auto -> /api/v2/open/config/modify (modify and publish)
# Non-prod V2 calls require a service token. Prefer exporting TCC_OPENAPI_TOKEN;
# this CLI environment variable maps to the API request body's token field.
# --token is also accepted but may enter shell history. This is a TCC platform
# OpenAPI service token, not an SSO/JWT token.
# The OpenAPI combines modification and publication, so the CLI reads and
# resubmits the latest value with latest_version as the default from_version.
# One explicit --region is required; --region all is not supported.
# --strategy-id and --region-parallel are unsupported. Omit --from-version;
# if supplied, it must equal the current latest_version used for the CAS check.
# Add --dry-run first to send tcc-openapi-mock: 1. Success validates only and
# never modifies or publishes; deployment_id may therefore be null. Remove
# --dry-run after validation to submit the real request. Token and value are
# redacted from JSON output.
# --dry-run is rejected on Web V1/v3 and V2 prod rather than being silently ignored.
# app_name stays empty unless TCC assigned one. operator is optional and defaults
# to the current bytedcli login username when available; it is shown in version history.
# For unpublished former_tcc configs, V2 deploy expects the target latest version in region_confspace_version[].from_version, and remark should be written to config_data.note.
# In auto mode it reads the live current step before each operation and keeps
# advancing with the allowed forward action (for example start, next_batch,
# finish) when no review is required; otherwise it returns the current review
# deployment for follow-up approval.
# When a deploy stage sets force_rolling=true, the web deploy payload also turns
# on enable_rolling=true for that stage.
# Feature strategy env validation: when strategy_type=feature, --env must be
# ppe/ppe_* or boe/boe_* (e.g. ppe_demo, boe_demo).

# Deploy config (default: --publish-mode auto, auto start + finish when no review needed)
export TCC_OPENAPI_TOKEN="service-token"
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe_demo --region CN --dir-path "/default" --dry-run
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe_demo --region CN --dir-path "/default"
# Web V1 only: deploy one region without expanding same-key sync-group peers
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe --region CN --dir-path "/default" --no-sync-group
# Web V1: without --to-version/--from-version each target region (sync group or --region all) deploys
# its own online -> latest versions; with several target regions an explicit version is refused
# unless it matches every region's online_version (--from-version) / latest_version (--to-version)
# deployment deploy supports --dir-path to pin a same-name config inside a specific directory.
# When the config belongs to a synced region group (for example CN + China-East),
# deployment deploy automatically expands config_changes/check_review conf_ids to all existing copies in that group.
# Add --region-parallel when you need parallel rollout across regions.

# Merge several configs of one namespace into a single deployment ticket: pass config_name
# as a comma-separated list. Each config keeps its own per-region pending versions; regions
# with no pending change are skipped. Legacy web namespaces only — TCC v2 (AgV2) namespaces
# reject multiple names (deploy each config separately there). --from/--to-version cannot be
# combined with multiple names.
bytedcli --site cn tcc deployment deploy "namespace" "conf_a,conf_b" --env prod --region all --publish-mode manual

# TCC v2 non-prod manual mode modifies without publishing (modify_only)
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env ppe_demo --region CN --dir-path "/default" --publish-mode manual

# Deploy with review support (auto mode): returns review info when review is needed
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env prod --region CN --dir-path "/default" --publish-mode auto

# TCC v2 prod: select one or more PSMs for the small-traffic stage
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env prod --region CN --gray-psm "example.service" --publish-mode manual

# Force auto-publish regardless of review requirement
bytedcli --site cn tcc deployment deploy "namespace" "config_name" --env prod --region CN --dir-path "/default" --publish-mode force-auto

# Query publish details by deployment ID or control-panel URL
bytedcli --site cn tcc deployment get "1234567890" --env prod
bytedcli tcc deployment get "https://example.com/tcc/namespace/demo.namespace/publish-details/1234567890??x-resource-account=demo&x-bc-region-id=example" --env prod
# Query deployment metadata, config_changes, and get_step only; skip config version diffs
bytedcli --site cn tcc deployment get "1234567890" --env prod --no-diff

# Operate deployment or approve/reject current review step
bytedcli tcc deployment operate "1234567890" --operation start --env prod
bytedcli tcc deployment approve "https://example.com/tcc/namespace/demo.namespace/publish-details/1234567890??x-resource-account=demo&x-bc-region-id=example" --env prod
bytedcli tcc deployment reject "1234567890" --env prod

# Multi-region consistency whitelist. Create accepts one exact directory and
# config only; wildcard scope and raw payload overrides are intentionally blocked.
bytedcli --site us-ttp tcc region-consistency whitelist list --namespace "demo.namespace"
bytedcli --site us-ttp tcc region-consistency whitelist create --namespace "demo.namespace" --dir-path "/default" --config-name "demo_config" --reason "Region-specific business config" --expected-regions "US-TTP,US-TTP2" --dry-run
bytedcli --site us-ttp tcc region-consistency whitelist create --namespace "demo.namespace" --dir-path "/default" --config-name "demo_config" --reason "Region-specific business config" --expected-regions "US-TTP,US-TTP2" --yes
```

`region-consistency whitelist create` reads the effective policy first and requires
`--expected-regions` to equal the complete region union. The whitelist API itself
has no region field, so this prevents a caller from silently overlooking a wider
blast radius. The command scans for an existing exact entry, sends at most one
create POST, and never retries an ambiguous write. A returned `bpm_url` means
approval is pending. A list read-back only proves `listed`; the API exposes no
activation status, so validate effectiveness by rerunning the original release
precheck.
