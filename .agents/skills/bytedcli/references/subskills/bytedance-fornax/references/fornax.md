# Fornax via bytedcli

`bytedcli fornax` carries the full Fornax command surface. Use it as the default for Fornax operations.

## Command catalog

The top-level resource group list is generated from the Fornax runtime. Use this catalog to select a resource group, then run `bytedcli fornax <group> --help` or `bytedcli fornax <group> <action> --help` for version-specific flags.

### Identity, configuration, and platform resources

- Auth: use `bytedcli auth login|logout|status`; the hidden migration group does not expose Fornax-native `auth export|import|usttp-dev-login`
- Config: `config set|show|select-workspace`
- Workspace: `workspace list`
- User lookup: `user get` by Fornax IDs, SSO usernames, or Lark user IDs
- Application: `application get|register|sandbox-execution|update`
- Maintenance: `version`, `update`, and `completion bash|zsh|fish|powershell`

### Prompt, data, and evaluation resources

- Prompt: `prompt list|get-by-key|get-by-id|create|delete|draft|commit|release`
- Dataset: `dataset list|create|list-versions|create-version|list-items|get-item|add-items|update-item|delete-items|clear-items|export|import|get-job|cancel-job|append-schema-fields`
- Eval set: `eval-set create|get|list|update|delete|update-schema|create-version|list-versions|add-items|get-item-version|list-item-versions|list-items|update-items|delete-items|list-templates`
- Eval target: `eval-target list|async-debug|get-record|report-result`
- Evaluator: `evaluator list|get|create|update|update-draft|delete|submit-version|run|run-builtin|get-records|list-versions|get-version`
- Experiment: `experiment submit|list|list-by-group|detail|results|agg-results|retry|kill|update-run-conf|export|export-record`
- Experiment template: `experiment-template create|get|list|update-meta|update|submit-expt`
- Model: `model create|get|list|update`
- Synthesis: `synthesis create-and-run|list|terminate`
- Training dataset: `training-dataset create`
- Skill: `skill create|get|list|commit|list-commits|save-detail|batch-get-by-id|batch-get-by-key|release|list-releases|install`

### Trace, trajectory, and execution resources

- Trace: `trace get|list`
- Span: `span list`
- Trajectory: `trajectory` is a leaf command; it has no `get` subcommand
- Execution: `execution detail ...`, `execution task ...`, and `execution backflow ...`

### Labels and batch labeling

- Label definitions and values: `label create|get|list|update|bump-version|delete|list-tags|value ...`
- Computations: `label-computation create|get|list|update|bump-version|delete`
- Mappings: `label-mapping bind|get|list|unbind`
- Local computation: `compute-label run` is dry-run only and never writes label values
- Batch labeling: `label-job preview|create|get|list|list-details|set-priority|cancel`

### Analysis insights and warehouse

- Templates: `analysis-insight-template create|get|get-input-contract|list|update|publish|offline`
- Jobs: `analysis-insight-job create|get|list|update|terminate|regenerate|get-report|get-logs|report-progress|bind-report`
- Dashboards: `analysis-insight-dashboard create|get|list|update|refresh|delete`
- Read-only SQL: `warehouse query`

`analysis-insight-job report-progress` and `bind-report` are sandbox-internal callbacks that read platform-injected environment variables. Ordinary users should use job status/report commands instead of invoking these callbacks directly.

For mutating actions such as create, update, delete, publish, retry, terminate, bind, and cancel, inspect the exact action help before execution and follow the official CLI's confirmation or dry-run semantics. The bytedcli proxy forwards arguments and does not add a second confirmation layer.

## Important official constraints

- Trace lookup identifiers are mutually exclusive. Pass one of `--trace-id` or `--log-id`; trajectory accepts one of `--trace-id` or `--experiment-id`. Old traces often require an explicit `--last-n-minutes` or paired time range.
- Eval-set create schema is a JSON object, while `update-schema --columns/--columns-file` uses a JSON array. Locked template columns must remain present and unchanged. Shared item queries require `--shared`, `--source-space-id`, and an explicit version or version ID.
- Prompt evaluators must reference inputs with `{{variable_name}}`. A newly created evaluator has a draft version and cannot be used by experiments or templates until `evaluator submit-version` publishes a normal version.
- Experiment `--skip-target` is incompatible with target flags and target-derived evaluator mappings; `--skip-evaluator` is incompatible with evaluator flags and mappings. For `custom_agent`/`a2a_agent`, map the eval-set input to `builtin_user_query`; `custom_agent` also requires top-level `--env` and `--cluster`.
- Experiment `multi_set_config` and cross-space resources are available only to enabled workspaces. Enable the mode explicitly with `--eval-set-source-type multi_set_config`; do not combine its JSON configuration with single-set evaluator flags. SUA run-mode configuration applies only to `sandbox_agent` on that path.
- Experiment CSV export is asynchronous: call `experiment export`, poll `experiment export-record`, then use `--download`. Download fails with a non-zero exit code unless the record is `Success`, unexpired, and has a URL.
- Model create/update payloads may contain provider credentials in `accounts[*].authorization`. Generate a payload with `model create --template`, keep it in a protected file, preview with `--dry-run`, and never paste the payload or credentials into logs or chat. Prefer `series` over the legacy `family` field.
- Synthesis `--target-dataset-id` and `--target-dataset-category` are mutually exclusive. Skill releases accept `Online|BOE|PPE`; an Online release must use feature `prod`.

## Common setup

```bash
bytedcli auth login
bytedcli fornax config set workspace-id <workspace-id>
bytedcli auth status
```

AK/SK setup:

```bash
bytedcli fornax config set ak <ak>
bytedcli fornax config set sk <sk>
```

Help and completion:

```bash
bytedcli fornax prompt --help
bytedcli fornax completion zsh
```

## Prompt examples

```bash
bytedcli --json fornax prompt list --keyword demo --page-no 1 --page-size 20
bytedcli --json fornax prompt get-by-key --key demo_key
bytedcli --json fornax prompt get-by-id --prompt-id <prompt-id> --with-draft --with-commit
bytedcli --json fornax prompt draft save --prompt-id <prompt-id> --draft-file ./draft.json
bytedcli --json fornax prompt draft commit --prompt-id <prompt-id> --version 1.0.0
bytedcli --json fornax prompt release create --prompt-id <prompt-id> --commit-version 1.0.0 --env online --release-config @./release.json
```

## Trace examples

```bash
bytedcli --json fornax trace get --trace-id <trace-id> --last-n-minutes 30
bytedcli --json fornax trace get --log-id <log-id>
bytedcli --json fornax trace list --last-n-minutes 60 --page-size 10
bytedcli --json fornax span list --last-n-minutes 60 --span-filter-expr "span_type='model'"
bytedcli --json fornax trajectory --trace-id <trace-id>
```

## Dataset and evaluation examples

```bash
bytedcli --json fornax dataset list --name demo --limit 20
bytedcli --json fornax eval-set list --name demo --page-size 20
bytedcli --json fornax eval-target list --type sandbox_agent --name demo --page-size 20
bytedcli --json fornax evaluator list --name demo --with-version
bytedcli --json fornax experiment-template list --name demo --page-size 20
bytedcli --json fornax model list --name demo
bytedcli --json fornax synthesis list --search-words demo
```

For model writes, keep credentials out of argv and logs:

```bash
umask 077
bytedcli fornax model create --template > ./model.json
bytedcli fornax model create --data @./model.json --dry-run
```

## Experiment examples

```bash
bytedcli --json fornax experiment submit --name demo --eval-set-id <eval-set-id> --eval-set-version 1.0.0 --evaluator <evaluator-id>:<version> --target-type coze_loop_prompt --target-id <target-id>
bytedcli --json fornax experiment detail --experiment-id <experiment-id>
bytedcli --json fornax experiment results --experiment-id <experiment-id> --page-no 1 --page-size 20
bytedcli --json fornax experiment agg-results --experiment-id <experiment-id>
bytedcli --json fornax experiment retry --experiment-id <experiment-id> --retry-mode retry_all
bytedcli --json fornax experiment export --experiment-id <experiment-id> --export-type CSV --eval-set-fields input,expected_output
bytedcli --json fornax experiment export-record --experiment-id <experiment-id> --export-id <export-id>
bytedcli fornax experiment export-record --experiment-id <experiment-id> --export-id <export-id> --download ./out
```

## Skill examples

```bash
bytedcli --json fornax skill list --page-size 20
bytedcli --json fornax skill get --skill-id <skill-id>
bytedcli fornax skill install demo-skill --dir ~/.codex/skills
```

## Execution and label examples

```bash
bytedcli --json fornax execution detail get --detail-id '<task-id>|<detail-id>' --with-input
bytedcli --json fornax label list --search-keyword demo --limit 20
bytedcli --json fornax label-computation get --computation-id <computation-id>
bytedcli --json fornax label-mapping list --label-key demo-label
bytedcli --json fornax compute-label run --label-key demo-label --detail-id '<task-id>|<detail-id>'
bytedcli --json fornax label-job list --view-status failed,partial_failed --page-size 10
```

## Analysis and platform examples

```bash
bytedcli --json fornax analysis-insight-template list --statuses testing,available --page-size 10
bytedcli --json fornax analysis-insight-job list --status running,failed --page-size 10
bytedcli --json fornax analysis-insight-dashboard list --page-size 10
bytedcli --json fornax warehouse query --sql 'SELECT 1' --dry-run
bytedcli --json fornax application get --id <application-id>
bytedcli --json fornax user get --user-names demo.user
```

## Migration aliases

These aliases still run during migration and print deprecation guidance to stderr:

```bash
bytedcli fornax list-workspace
bytedcli fornax list-prompt --space-id <workspace-id>
bytedcli fornax get-prompt --space-id <workspace-id> --prompt-id <prompt-id>
bytedcli fornax create-prompt --space-id <workspace-id> --prompt-key team.demo.prompt --display-name "Demo Prompt"
bytedcli fornax update-prompt --space-id <workspace-id> --prompt-id <prompt-id> --message-list-file ./messages.json
bytedcli fornax publish-prompt --space-id <workspace-id> --prompt-id <prompt-id> --target online --version 1.0.1
bytedcli fornax experiment create --request-file ./experiment.json
bytedcli fornax experiment get --workspace-id <workspace-id> --experiment-id <experiment-id>
bytedcli fornax experiment aggr-results --workspace-id <workspace-id> --experiment-id <experiment-id>
bytedcli fornax trace --logid <logid>
bytedcli fornax trace-chain-diagnosis --trace-id <trace-id>
```

## Output contract

- Text mode appends `--format pretty` unless `--format` is already present.
- `bytedcli --json fornax ...` appends `--format raw`.
- Deprecation notices and installer logs use stderr.
- The Fornax runtime is set up automatically on first run; if a setup error occurs, retry the `bytedcli fornax` command.
