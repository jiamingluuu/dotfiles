---
name: bytedance-gecko
description: "Use bytedcli gecko commands to query Gecko CN resources (diagnostics, apps, projects, deployments, channels, channel overview enrichments, offline rule trees, offline packages, workflows, tags, scans, stats, files, logs, patches), create PPE offline packages from SCM builds, enable or disable their env lanes, and manage SP&T per-app-version builtin/ODR settings, including create, update, enable, disable and resource generation workflows."
---

# bytedcli Gecko CN

## Invocation

```bash
bytedcli --site cn gecko <resource> <action> [options]
```

## Quick start

```bash
bytedcli --site cn gecko diagnostics get --include-root-users --include-dependency
bytedcli --site cn gecko app list --query demo-app
bytedcli --site cn gecko project list --query demo-project --include-subscription
bytedcli --site cn gecko project get --project-id sample-project-id --include-deployments
bytedcli --site cn gecko project admins --project-id sample-project-id
bytedcli --site cn gecko project apps --project-id sample-project-id
bytedcli --site cn gecko channel list --query demo-channel --include-projects
bytedcli --site cn gecko channel get --channel-id sample-channel-id --include-config --include-groups --include-admins
bytedcli --site cn gecko channel get --channel-id sample-channel-id --include-optional-config
bytedcli --site cn gecko channel resolve --access-key redacted-access-key --channel-name demo-channel
bytedcli --site cn gecko channel groups --channel-id sample-channel-id
bytedcli --site cn gecko channel admins --channel-id sample-channel-id
bytedcli --site cn gecko channel patrol --channel-id sample-channel-id --status TO_BE_FIX
bytedcli --site cn gecko channel traffic-switch --channel-id sample-channel-id
bytedcli --site cn gecko deployment get --access-key redacted-access-key
bytedcli --site cn gecko offline tree --channel-id sample-channel-id --include-packages --include-package-details
bytedcli --site cn gecko offline tree --access-key redacted-access-key --channel-name demo-channel --include-workflows
bytedcli --site cn gecko offline package list --channel-id sample-channel-id --page 1 --page-size 10
bytedcli --site cn gecko offline package list --access-key redacted-access-key --channel-name demo-channel --status 6 --include-rule-path
bytedcli --site cn gecko offline package get --package-id sample-package-id --include-files --include-logs --include-patches
bytedcli --site cn gecko offline package files --package-id sample-package-id
bytedcli --site cn gecko offline package logs --package-id sample-package-id
bytedcli --site cn gecko offline package patches --package-id sample-package-id
bytedcli --site cn gecko offline package scan --package-id sample-package-id
bytedcli --site cn gecko offline package tags --package-id sample-package-id
bytedcli --site cn gecko offline package rule-path --package-id sample-package-id
bytedcli --site cn gecko offline package workflows --package-id sample-package-id
bytedcli --site cn gecko offline package tickets --package-id sample-package-id
bytedcli --site cn gecko offline package stats --package-id sample-package-id --access-key redacted-access-key
bytedcli --site cn gecko spt config get --app-id 10000000
bytedcli --site cn gecko spt setting list --app-id 10000000 --app-version 1.0.0
bytedcli --site cn gecko spt setting list --app-id 10000000 --limit 100
bytedcli --site cn gecko spt setting get --setting-id sample-spt-setting-id
bytedcli --site cn gecko spt tag-usage get --app-id 10000000 --app-version 1.0.0 --type GECKO
```

## PPE offline package writes

Every write is preview-first: pass exactly one of `--dry-run` / `--yes`. Always inspect the preview before submitting the same command with `--yes`. These commands are PPE-only and do not publish an ONLINE/production package.

Creation accepts either `--channel-id` or `--access-key` + `--channel-name`. With the name selector, dry-run performs a read-only channel lookup so the preview contains the exact channel ID; it never requests an SCM artifact token or creates a package. Live execution then exchanges the SCM build for an artifact token and creates the offline package with one or more required PPE env lanes.

```bash
bytedcli --site cn gecko offline package create --channel-id sample-channel-id --leaf-id sample-leaf-id --repo-name sample-project/sample-repo --scm-version 1.0.0.1 --top-folder dist --env-lane sample-ppe-lane --description 'Android acceptance' --dry-run
bytedcli --site cn gecko offline package create --channel-id sample-channel-id --leaf-id sample-leaf-id --repo-name sample-project/sample-repo --scm-version 1.0.0.1 --top-folder dist --env-lane sample-ppe-lane --description 'Android acceptance' --yes
bytedcli --site cn gecko offline package enable --package-id sample-package-id --dry-run
bytedcli --site cn gecko offline package enable --package-id sample-package-id --yes
bytedcli --site cn gecko offline package disable --package-id sample-package-id --description 'Acceptance complete' --dry-run
bytedcli --site cn gecko offline package disable --package-id sample-package-id --description 'Acceptance complete' --yes
```

## SP&T writes

Every write leaf is preview-first: exactly one of `--dry-run` / `--yes` is required. Preview first, then re-run the same command with `--yes`.

```bash
bytedcli --site cn gecko spt setting create --app-id 10000000 --app-version 1.0.0 --version-identifier '*' --dry-run
bytedcli --site cn gecko spt setting create --app-id 10000000 --app-version 1.0.0 --version-identifier '*' --app-channel 'App Store' --yes
bytedcli --site cn gecko spt setting update --setting-id sample-spt-setting-id --version-identifier '*' --app-channel 'App Store' --yes
bytedcli --site cn gecko spt setting disable --setting-id sample-spt-setting-id --yes
bytedcli --site cn gecko spt setting enable --setting-id sample-spt-setting-id --yes
bytedcli --site cn gecko spt resource generate --app-id 10000000 --app-version 1.0.0 --description 'sample reason' --dry-run
```

## Notes

- Every command is read-only except the PPE offline package and `spt` write leaves listed above.
- Auth uses ByteCloud JWT with `x-jwt-token`; run `bytedcli --site cn auth login` if auth is missing or expired.
- Commands that mirror URL-style Gecko pages generally accept either `--channel-id` or `--access-key` + `--channel-name`.
- `offline package create` requires at least one `--env-lane`; an empty lane set can imply full release and is intentionally rejected. Its dry-run output shows both OpenAPI requests and uses a placeholder for the artifact token produced by step 1.
- `offline package enable` and `disable` submit Gecko's env-lane release and rollback workflows respectively. They do not call the generic release-policy or ONLINE publishing APIs.
- Expensive page enrichments are explicit: use project `--include-subscription` / `--include-deployments`, channel list `--include-subscription` / `--include-projects`, and channel get `--include-config` / `--include-deployment` / `--include-groups` / `--include-admins` only when those fields are needed.
- Offline package `--status` accepts comma-separated numeric codes or Chinese labels: `1=处理中`, `2=处理失败`, `3=待发布`, `4=实验中`, `5=灰度中`, `6=全量`, `7=已关闭`, `8=部分清理`, `9=全量清理`.
- `offline package stats` calls the monitor usage-stats endpoint and can be slow; keep it explicit instead of using it in default package detail reads.
- SP&T (`spt`) covers app-version builtin/ODR resource settings: `spt config get` returns the app-level global config, `spt setting list` / `spt setting get` return per-app-version settings. `spt setting` status maps to `enabled` (`isEnable`), `disabled` (`isDisable`), or `pending` when neither flag is set; `isResourceReady` tells whether the generated artifacts are available.
- The SP&T search endpoint has no server-side pagination and returns every setting ID for an app. `spt setting list` therefore truncates client side at `--limit` (default 50, max 500) and reports `truncated` in JSON plus a hint in text output. Prefer `--app-version` for an exact-version lookup; raise `--limit` only when the full list is genuinely needed.
- `spt config get` masks offline resource group access keys in text output; use `--json` when the raw access key is required.
- The App-level SP&T global config is read-only by design. It is a whole-document write guarded by an optimistic lock and one change affects every version of the app, so apply it manually in the Gecko console instead of asking for a CLI write path.
- `spt setting create` is irreversible: the backend has no delete endpoint, so a created setting stays in the list permanently. Always `--dry-run` first.
- `spt setting update` reads the current setting first: `--version-identifier` is required, and omitting `--app-channel` / `--device-id` carries the current lists over unchanged. Pass an explicit value to replace a list.
- `spt setting enable` requires workflow approval on the Gecko side; the command only submits the request.
- `spt resource generate` runs on the Gecko control-plane OpenAPI host, takes 30min-1h, and cannot be cancelled from the CLI.
- `spt tag-usage get --type` accepts only `MINI_APP` or `GECKO`.
- Text output avoids access keys, TOS URLs, package schemas, and patch download URLs by default. Use `--json` when raw fields are required for automation.
