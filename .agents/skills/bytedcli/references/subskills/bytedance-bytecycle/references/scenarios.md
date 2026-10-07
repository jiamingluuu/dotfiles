# Scenarios

Pick a scenario first, then jump to the matching reference. Commands shown here are entry points; see each reference for the full flag list and dry-run / `--yes` behavior.

## Scenario 1: Drive a release train end-to-end

Reference: `train.md` + `pipeline.md` (for MR and pipeline steps).

Lifecycle:

```text
train create / hotfix-create
  -> train to-integrating
  -> ticket create OR ticket wip create       # requires a full payload file
  -> ticket wip board
  -> ticket approve / reject
  -> train to-code-freeze
  -> mr train create / merge
  -> train pipeline create-and-build
  -> pipeline trigger-train
  -> train to-deploying
  -> train merge-back
  -> train complete
```

Read-only context:

```bash
bytedcli bytecycle train get --train-id <id>
bytedcli bytecycle train list --workspace-id <id> --status integrating
bytedcli bytecycle train vars get --train-id <id>
bytedcli bytecycle train pipeline list --train-id <id> --region cn
bytedcli bytecycle train operation list --train-id <id>
bytedcli bytecycle mr train get --train-id <id>
```

## Scenario 2: Ticket board / edit / off-board

Reference: `ticket.md`.

```bash
bytedcli bytecycle ticket get --ticket-id <id>
bytedcli bytecycle ticket list --workspace-id <id> --status wip --creator <username>
bytedcli bytecycle ticket warning get --ticket-id <id>

bytedcli bytecycle ticket create --payload-file ticket-create.json
bytedcli bytecycle ticket wip create --payload-file wip-ticket-create.json

bytedcli bytecycle ticket update --ticket-id <id> \
  --template-var-key context.params.example \
  --template-var-value new-value
bytedcli bytecycle ticket vars update --ticket-id <id> --payload-file tv.json

bytedcli bytecycle ticket wip board --wip-ticket-id <id> --train-id <id>
bytedcli bytecycle ticket approve   --ticket-id <id>
bytedcli bytecycle ticket reject --ticket-id <id> --note "..."

bytedcli bytecycle ticket revert request --ticket-id <id>
bytedcli bytecycle ticket revert approve --ticket-id <id>
bytedcli bytecycle ticket remerge --train-id <id> --ticket-id <id>

bytedcli bytecycle ticket pipeline create-and-build --ticket-id <id> --region cn
```

The ticket-side reads / create / lifecycle / vars / revert / remerge are wrapped. Ticket create commands require a full payload file because payloads depend on team-level conventions.

## Scenario 3: Execution

Reference: `execution.md`.

```bash
bytedcli bytecycle execution get --execution-id <uuid>
bytedcli bytecycle execution list --mine --status pending --workspace-id <id>
```

Submit / approve / reject / complete / rollback / MR creation / pipeline trigger are not wrapped yet. Do not expose private request details to agents; wait for wrapped command support.

## Scenario 4: Config delivery

Reference: `config.md`.

Nothing wrapped yet. Do not use unwrapped config delivery operations from agent workflows.
