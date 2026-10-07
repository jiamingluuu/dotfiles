---
name: bytedance-fornax
description: "Operate the Fornax platform through bytedcli, including prompts, traces and trajectories, execution/backflow, datasets and evaluation, labels and batch labeling, analysis insights, warehouse queries, applications, users, models, skills, and experiments. Use when tasks mention Fornax, AgentOps evaluation or analysis, or any Fornax resource command."
---

# bytedcli Fornax

## How to call bytedcli

```bash
# Run latest bytedcli directly
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]

# Or install bytedcli globally first
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

Use `bytedcli --json fornax ...` for machine-readable output. The global `--json` flag must appear before `fornax`.

## When to use

- Configure Fornax: `config set`, `config show`; auth uses `bytedcli auth login`
- List workspaces and set a default workspace
- Manage prompts, prompt drafts, commits, and releases
- Query traces, spans, trajectories, execution details/tasks, and backflow state
- Manage datasets, eval sets/targets, evaluators, experiments/templates, models, skills, synthesis, and training datasets
- Manage labels, computations, mappings, values, dry-run computation, and batch labeling jobs
- Manage analysis insight templates/jobs/dashboards and query the read-only analysis warehouse
- Inspect applications and resolve Fornax users to SSO or Lark identities
- Install Fornax skills into local agent skill directories
- Inspect Fornax command help and generate shell completion

## Command model

`bytedcli fornax` carries the full Fornax command surface. The runtime is set up automatically on first run; no manual installation is needed.

The proxy group list is generated from the installed official CLI. Read `references/fornax.md` for the command catalog, and run `bytedcli fornax <group> --help` for the exact flags supported by the installed version. Do not infer flags from a different resource group.

Recommended commands follow the Fornax command surface:

```bash
bytedcli auth login
bytedcli fornax config set workspace-id <workspace-id>
bytedcli --json fornax workspace list
bytedcli --json fornax prompt list --keyword demo --page-no 1 --page-size 20
bytedcli --json fornax prompt get-by-id --prompt-id <prompt-id> --with-draft
bytedcli --json fornax trace get --trace-id <trace-id> --last-n-minutes 30
bytedcli --json fornax trace list --last-n-minutes 60 --page-size 10
bytedcli --json fornax trajectory --trace-id <trace-id>
bytedcli --json fornax execution detail get --detail-id '<task-id>|<detail-id>' --with-input
bytedcli --json fornax experiment submit --name demo --eval-set-id <eval-set-id> --eval-set-version 1.0.0 --evaluator <evaluator-id>:<version> --target-type coze_loop_prompt --target-id <target-id>
bytedcli --json fornax experiment results --experiment-id <experiment-id> --page-no 1 --page-size 20
bytedcli --json fornax label list --search-keyword demo --limit 20
bytedcli --json fornax analysis-insight-job list --status running,failed --page-size 10
bytedcli --json fornax warehouse query --sql 'SELECT 1' --dry-run
bytedcli fornax skill install demo-skill --dir ~/.codex/skills
bytedcli fornax prompt --help
bytedcli fornax completion zsh
```

## Auth and config

Fornax uses bytedcli's unified authentication. Run `bytedcli auth login` to log in, then configure your workspace:

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

Migration aliases:

```bash
bytedcli fornax auth config --access-key <ak> --secret-key <sk>
bytedcli fornax auth config --jwt-token <token>
```

`auth config --access-key/--secret-key` stores `ak` and `sk` in the Fornax runtime config. `auth config --jwt-token` keeps the legacy bytedcli credential store for migration compatibility.

## Prompt flow

```bash
bytedcli --json fornax prompt list --keyword demo --page-no 1 --page-size 20
bytedcli --json fornax prompt get-by-key --key demo_key
bytedcli --json fornax prompt get-by-id --prompt-id <prompt-id> --with-draft
bytedcli --json fornax prompt draft save --prompt-id <prompt-id> --draft-file ./draft.json
bytedcli --json fornax prompt draft commit --prompt-id <prompt-id> --version 1.0.0
bytedcli --json fornax prompt release create --prompt-id <prompt-id> --commit-version 1.0.0 --env online --release-config @./release.json
```

Migration aliases still run and print deprecation guidance to stderr:

```bash
bytedcli fornax list-workspace
bytedcli fornax list-prompt --space-id <workspace-id>
bytedcli fornax get-prompt --space-id <workspace-id> --prompt-id <prompt-id> --personal-draft
bytedcli fornax create-prompt --space-id <workspace-id> --prompt-key team.demo.prompt --display-name "Demo Prompt"
bytedcli fornax update-prompt --space-id <workspace-id> --prompt-id <prompt-id> --message-list-file ./messages.json
bytedcli fornax publish-prompt --space-id <workspace-id> --prompt-id <prompt-id> --target online --version 1.0.1
```

## Experiment flow

```bash
bytedcli --json fornax experiment submit --name demo --eval-set-id <eval-set-id> --eval-set-version 1.0.0 --evaluator <evaluator-id>:<version> --target-type coze_loop_prompt --target-id <target-id>
bytedcli --json fornax experiment detail --experiment-id <experiment-id>
bytedcli --json fornax experiment results --experiment-id <experiment-id> --page-no 1 --page-size 20
bytedcli --json fornax experiment agg-results --experiment-id <experiment-id>
bytedcli --json fornax experiment retry --experiment-id <experiment-id> --retry-mode retry_all
```

Migration aliases:

```bash
bytedcli fornax experiment create --request-file ./experiment.json
bytedcli fornax experiment get --workspace-id <workspace-id> --experiment-id <experiment-id>
bytedcli fornax experiment aggr-results --workspace-id <workspace-id> --experiment-id <experiment-id>
```

## Trace flow

Recommended trace commands:

```bash
bytedcli --json fornax trace get --trace-id <trace-id> --last-n-minutes 30
bytedcli --json fornax trace get --log-id <log-id>
bytedcli --json fornax trace list --last-n-minutes 60 --page-size 10
```

Legacy diagnosis remains available:

```bash
bytedcli fornax trace --logid <logid>
bytedcli fornax trace-chain-diagnosis --trace-id <trace-id>
```

## Output rules

- Text mode appends `--format pretty` unless the user passes `--format`.
- `bytedcli --json fornax ...` appends `--format raw`.
- Deprecation notices and installer logs go to stderr, keeping JSON stdout parseable.
- Interactive commands such as `config select-workspace` and `skill install` without `--dir` run with inherited stdio.

## References

- `references/fornax.md`
