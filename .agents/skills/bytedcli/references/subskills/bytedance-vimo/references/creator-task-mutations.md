# Overseas Vimo clue and task mutations

This reference covers clue creation/dispatch, clue delivery plans, solicitation tasks, task pins,
submissions, rewards, and Creator task templates. Also read the corresponding read references and
the parent Skill's mutation workflow.

## JSON files and dry-run review

All writes are dry-runs until explicitly confirmed. JSON options must point to an existing readable
file containing one business object. Review `data.action` and `data.payload`, then rerun with
`--yes` only after explicit confirmation. L3 live submissions also require a non-empty `--reason`;
L4 live submissions require both `--reason` and `--ticket` and are denied by default unless the
caller is explicitly authorized. The CLI rejects control or credential keys; never include endpoint,
raw action, `yes`, Cookie, authorization, JWT, token, secret, or request headers. IDs remain strings.

Create/update objects receive bounded structural validation, but the Vimo business object is not a
generic patch. Obtain a complete current object from a trusted export or API response, remove fields
as documented below, preview the exact payload, then confirm. If the file changes, preview again.

## AI clue and dispatch

```bash
bytedcli --site i18n --json vimo creator clue create-ai \
  --clue-id '<eligible-source-id>' --area '<vimo-area>' --grade A
bytedcli --site i18n --json vimo creator clue dispatch \
  --clue-id '<clue-id>' --main-type '<main-type-id>' \
  --subscription-id '<plan-id>'
```

- `create-ai` accepts grade `S|A|B|C` and may cause multiple downstream side effects.
- Discover main types with `clue-type list`. Main type `1` omits `--subscription-id`; other types
  require the matching plan ID.
- Dispatch creates a solicitation task. Verify it with `task list` by clue source.
- Clue-type mutation and legacy clue deletion are not supported.

## Clue delivery plans

```bash
bytedcli --site i18n --json vimo creator clue-plan create --plan-file '<plan.json>'
bytedcli --site i18n --json vimo creator clue-plan copy --plan-file '<source-plan.json>'
bytedcli --site i18n --json vimo creator clue-plan update \
  --plan-id '<plan-id>' --plan-file '<complete-plan.json>'
bytedcli --site i18n --json vimo creator clue-plan enable --plan-id '<plan-id>'
bytedcli --site i18n --json vimo creator clue-plan disable --plan-id '<plan-id>'
bytedcli --site i18n --json vimo creator clue-plan delete --plan-id '<plan-id>'
```

- Create omits `id`; copy removes the source `id`; update injects or verifies `--plan-id`.
- If `schedule` exists, it must contain exactly one of `cron_expr` or `interval_seconds`.
- Enable/disable/delete only after an exact `clue-plan list` state check.

## Solicitation-task lifecycle

```bash
bytedcli --site i18n --json vimo creator task create --task-file '<task.json>'
bytedcli --site i18n --json vimo creator task create \
  --task-file '<task.json>' --from-clue-id '<clue-id>'
bytedcli --site i18n --json vimo creator task copy --task-file '<source-task.json>'
bytedcli --site i18n --json vimo creator task update \
  --task-id '<task-id>' --task-file '<complete-task.json>'
bytedcli --site i18n --json vimo creator task end --task-id '<task-id>'
bytedcli --site i18n --json vimo creator task delete --task-id '<task-id>'
```

- Create omits `id`. Copy strips record/approval identity, removes clue attribution, and creates an
  operator-source task.
- Update submits a complete task object. It never exposes or sends privileged `skipApproval`.
- End/delete only in states where the Vimo page permits the operation. Verify by exact task ID.

## Task pins and submissions

```bash
bytedcli --site i18n --json vimo creator task-pin update \
  --task-id '<task-id>' --enable-biz-ids '<region-biz-id>'
bytedcli --site i18n --json vimo creator task-pin update \
  --task-id '<task-id>' --disable-biz-ids '<region-biz-id>'
bytedcli --site i18n --json vimo creator task-submission add \
  --task-id '<task-id>' --item-id '<item-id>'
```

Pin dry-run reads the current full pin map, applies the patch, and displays the complete merged
`pin_map` write payload. A later `--yes` submission reads the then-current map again and applies the
requested patch to that current state before writing, so inspect the live result after submission.
Both rounds require the normal overseas Vimo Cookie or office-network SSO credential. A region must
already exist in the current map. Submission adds one item; it does not review or reward it.

## Rewards

```bash
bytedcli --site i18n --json vimo creator task-reward recalculate --task-id '<task-id>'
bytedcli --site i18n --json vimo creator task-reward insert \
  --task-id '<task-id>' --item-ids '<item-id>' \
  --task-rule-id '<rule-id>' --reason '<reason>'
bytedcli --site i18n --json vimo creator task-reward remove \
  --task-id '<task-id>' --reward-id '<reward-id>'
bytedcli --site i18n --json vimo creator task-reward clear --task-id '<task-id>'
bytedcli --site i18n --json vimo creator task-reward publish --task-id '<task-id>'
```

- Insert selects exactly one of `--item-ids` or `--user-ids`; `--task-rule-id` is a positive
  signed-i64 decimal string, and reason is at most 50 characters. Optional `--reward-file`
  supplies a user-provided reward object.
- Remove deletes one reward; clear removes all unconfirmed candidates; publish releases confirmed
  rewards. These are separate writes requiring separate previews and confirmations.
- Publish is complete only when `data.result.outcome=published` and
  `data.result.hasFailures=false`. `outcome=rejected` means the list was not published; report
  `invalidUserIds` and `invalidTemplateIds`, remove or correct those entries through a separately
  reviewed operation, and do not replay the publish automatically.

## Creator task templates

```bash
bytedcli --site i18n --json vimo creator task-template create --template-file '<template.json>'
bytedcli --site i18n --json vimo creator task-template copy --template-file '<source-template.json>'
bytedcli --site i18n --json vimo creator task-template update \
  --template-id '<template-id>' --template-file '<complete-template.json>'
bytedcli --site i18n --json vimo creator task-template delete --template-id '<template-id>'
```

Create omits `template_id`; copy removes it; update injects or verifies `--template-id` and keeps the
complete nested Task definition. This resource is not `--site i18n vimo template`, the video-template manager.

## Unsupported writes

Do not mutate clue-type catalogs, use legacy clue delete, skip task approval, send a raw task
status, reorder rewards, call arbitrary endpoint/body, or use internal/debug/batch page actions.
