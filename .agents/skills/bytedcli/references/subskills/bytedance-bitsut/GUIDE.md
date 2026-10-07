---
name: bytedance-bitsut
description: "Use when tasks mention BitsUT or Bits 单测基建能力，包含单测 CI 执行和单测智能生成相关功能; includes unit-test CI execution, AI unit-test generation, coverage detail, case lists, issue troubleshooting, task_group_id, and ai_gen_task_id."
---

# bytedcli BitsUT

Use `bytedcli bitsut` for Bits 单测基建能力，包含单测 CI 执行和单测智能生成相关功能。

## How To Call

Use global JSON mode for stable machine-readable output:

```bash
bytedcli --json bitsut <domain> <resource> <action> [options]
```

Inspect help instead of guessing arguments:

```bash
bytedcli bitsut --help
bytedcli bitsut gen --help
bytedcli bitsut ci --help
bytedcli bitsut repo --help
```

## Domains

- `bitsut gen`: 单测智能生成相关功能。IDs are `ai_gen_task_id` / `gen_task_id`.
- `bitsut ci`: 单测 CI 执行相关功能。Use `--task-group-id` for task-group scoped drill-down commands; backend fields may still be named `task_id`.
- `bitsut repo`: Repository and CI discovery shared by generation and execution workflows.

Do not mix generation task ids with execution task ids.

## Common Commands

```bash
# Latest task groups for an MR, grouped by pipeline/job.
bytedcli --json bitsut ci result-summary --mr-id 123456789

# Latest task groups for a repo branch or commit, grouped by pipeline/job.
bytedcli --json bitsut ci result-summary --repo-name example/repo --branch feature/demo

# Search execution task history by time range and filters.
bytedcli --json bitsut ci history --start 2026-08-01 --end 2026-08-02 --codebase-mr-id 123456

# OneSite execution task group detail.
bytedcli --json bitsut ci task --task-group-id 123456

# Execution logs and artifact files by task group id.
bytedcli --json bitsut ci artifact --task-group-id 123456

# BitsUT internal execution stages and step details.
bytedcli --json bitsut ci step --task-group-id 123456

# Execution case list.
bytedcli --json bitsut ci case --task-group-id 123456 --page 1 --page-size 20

# Execution coverage files. Mode is semantic, not backend numeric code.
bytedcli --json bitsut ci coverage --view list --task-group-id 123456 --type diff --mode line

# Generation task list.
bytedcli --json bitsut gen history --repo example/repo --page 1 --page-size 20

# Generation task detail.
bytedcli --json bitsut gen task --gen-task-id 123456

# Generation workflow step detail.
bytedcli --json bitsut gen workflow --view step --gen-task-id 123456 --step-id step-demo --latest-event-timestamp 0

# CI yaml config by revision and yaml path.
bytedcli --json bitsut repo ci-yaml --mode config --repo example/repo --revision abc123 --yaml-path .codebase/pipelines/ci.yaml

# Recommended CI yaml path for a source/target branch.
bytedcli --json bitsut repo ci-yaml --mode recommend --repo example/repo --source-branch feature/demo --target-branch master

# Codecov-related CI yaml paths for a branch.
bytedcli --json bitsut repo ci-yaml --mode codecov --repo example/repo --source-branch feature/demo --target-branch master

# Subprojects and associated ci_yaml values for a revision.
bytedcli --json bitsut repo ci-yaml --mode subprojects --repo example/repo --revision feature/demo --language 2 --target-revision master
```

## Authentication

All requests send ByteCloud JWT in the `x-jwt-token` header through bytedcli auth. If authentication fails, run:

```bash
bytedcli auth login
```

The command supports `--ut-env online|boe` for UT service routing. Default is `online`.

## Agent Guidance

- Prefer `--json` for all agent calls.
- Use `bitsut ci result-summary --mr-id` or `--repo-name` with `--branch`/`--commit-id` to discover the latest task groups grouped by pipeline/job.
- Use `bitsut ci history --start --end` plus filters such as `--codebase-mr-id`, `--commit`, `--repo-id`, or `--branch` to discover task groups from history; this command does not require a OneSite id.
- Use `bitsut ci task --task-group-id` for OneSite task-group detail, then keep using `--task-group-id` with `case`, `coverage --view list|tree|file|rules`, or `issue` for deeper troubleshooting.
- Use `bitsut ci artifact --task-group-id` when logs or artifact files are needed for one task group.
- Use `bitsut ci step --task-group-id` for BitsUT internal stages and step details; use `bits step-logs` for BITS CI job step logs.
- Use `bitsut gen history` to discover `ai_gen_task_id`, then `bitsut gen task --gen-task-id` for generation details.
- Use `bitsut repo ci-yaml --mode config|recommend|codecov|subprojects` for repository CI discovery. The former `gen repo` commands are not part of the public command surface.
- Coverage options use semantic values: `--type diff|full`, `--mode line|condition|branch|statement`.
- Current scope is read-only. Do not use this skill for replay run, artifact apply, or other write operations.
