# Coral permission workflow

Use this when directly granting, applying, answering, submitting, withdrawing, or debugging Coral Hive permissions.

## Direct grant (owner, immediate write)

`permission grant` adds a table recipient without approval. It is dry-run by default and prints the endpoint plus complete payload without sending HTTP. Review that preview with the user; only after explicit confirmation rerun with `--yes`. If both `--dry-run` and `--yes` are present, dry-run wins.

```bash
# Preview first
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --auth-object demo-group --auth-type user_group --permission read --ttl 180

# Preview a column-level grant; repeat --column or comma-separate values
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --column sample_col --column sample_date --auth-object demo-user --auth-type person \
  --permission read --ttl 180

# Submit only after explicit confirmation
bytedcli --json coral permission grant --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --auth-type person --permission read --ttl 180 --yes
```

`user_group` is the default receiver type; `person` grants to an individual. The default reason is `日常业务需求`. Direct grant supports both table-level and column-level resources. Pass repeatable or comma-separated `--column` values for column grants; each column is submitted as a separate resource object.

## Modify an existing permission TTL

`permission modify-ttl` identifies the existing grant by its resource and authorization fields; it does not accept an application id. It previews by default and POSTs to `/api/v1/privileges/modifyTTL` only with `--yes`; `--dry-run` wins over `--yes`.

```bash
# Table (resource_type=1, name=db/table)
bytedcli --json coral permission modify-ttl --region cn --resource-type table \
  --name example_db/example_table --auth-type person \
  --auth-object demo-user --permission read --ttl 180 --reason "Extend table access"

# Database (resource_type=2, name=db)
bytedcli --json coral permission modify-ttl --region cn --resource-type database \
  --name example_db --auth-type psm --auth-object demo.psm \
  --permission read --ttl 90 --reason "Extend database access"

# Column (resource_type=3, name=db/table/column); submit only after preview approval
bytedcli --json coral permission modify-ttl --region cn --resource-type column \
  --name example_db/example_table/sample_col --auth-type person --auth-object demo-user \
  --permission read --ttl 30 --reason "Extend column access" --yes
```

For batch jobs, repeat `--object '<json>'`, or pass `--objects-file` containing a JSON array. Every object must contain `data_source`, `resource_type`, `name`, `auth_type`, `auth_object`, `permission`, and a positive-integer `ttl`. The CLI rejects resource types outside 1/2/3 and names whose slash-separated depth does not match the resource type.

## Apply

```bash
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --auth-object demo-user --permission read --ttl 365 \
  --reason "Need read access for analysis." > /tmp/coral-permission-draft.json

# Disable automatic partition column merging when applying for specific columns only
bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --no-auto-partition --auth-object demo-user --permission read --ttl 365 \
  --reason "Need read access for analysis." > /tmp/coral-permission-draft.json

bytedcli --json coral permission apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --auth-object demo-user --permission read --ttl 365 \
  --reason "Need partition-scoped read access." > /tmp/coral-row-filter-draft.json
```

- Omit `--column` for table-level permission.
- Repeat `--column` or comma-separate values for column-level permission. When `--column` is provided,
  the command automatically queries table metadata and auto-fills partition columns (e.g. `date`, `p_date`)
  to prevent WHERE filter 403 errors in query engines. Pass `--no-auto-partition` to disable.
- Repeat `--row-filter column=value` for exact row/partition values. Repeated values for the same
  column are merged; values are not parsed as SQL or split on commas.
- `--column app` means column-level access to the `app` field. It does not replace
  `--row-filter app=sample-app`.
- Use `--auth-type psm` only when granting to a service identity.
- Use `--cluster <cluster>` only as an advanced Coral group override; CN permission apply defaults to Coral group `default`.
- For Dorado `NoPrivilegeException` logs, apply for every `User ... does not have privileges` subject in the exception. Use `--auth-type person` for human users and `--auth-type psm` for project/service identities.
- If Coral returns `CORAL_PERMISSION_RESOURCE_CLOSED`, stop: no draft or application was created for that resource. Report the table URL/resource details from the error instead of continuing to `permission create`.

## If result is `status: draft`

1. Read the draft JSON from `/tmp`.
2. Ask the user only the visible questions from the draft/API output.
3. Fill one question at a time:

```bash
bytedcli --json coral permission answer --draft-file /tmp/coral-permission-draft.json \
  --question-id <question_id> --answer <user_answer> > /tmp/coral-permission-answered.json
```

4. Chain subsequent answers from the latest answered draft file.
5. Submit only after all required visible questions are answered:

```bash
bytedcli --json coral permission create --region sg --draft-file /tmp/coral-permission-answered.json
```

## Questionnaire rules

- Resource questions come from `relation[*].resource_questions_answers`.
- Cross-region questions come from `crossRegionQuestions` in the draft. They use option ids/names from Coral and are submitted as `cross_region_questions_answers[*].selections` by the CLI.
- Legal questions come from `trigger_legal_rule.customized_question.question_items`.
- Legal answers need both display `answers` and API-derived `answer_ids`.
- Conditional legal questions use `show_condition`; compare prior `answer_ids`, not display text.
- Ask hidden conditional branches only if they become visible after prior answers.
- Do not hardcode question ids or option ids from old examples.

For cross-region multi-select questions, repeat `--answer` with the selected option ids or exact option names from the draft:

```bash
bytedcli --json coral permission answer --draft-file /tmp/coral-permission-draft.json \
  --question-id 1 --answer 4 --answer 1 --answer 2 > /tmp/coral-permission-answered-q1.json
```

For options that require an explanation, pass both the selected option and the free-text explanation:

```bash
bytedcli --json coral permission answer --draft-file /tmp/coral-permission-answered-q1.json \
  --question-id 2 --answer 5 --answer "Need access for approved dashboard validation." \
  > /tmp/coral-permission-answered-q2.json
```

## Create result handling

- `submitted`: new ticket confirmed; expect `groupId` and/or `applicationUrl`.
- `existing`: Coral returned `existed_application_id`; report it as an existing blocking ticket.
- `unknown`: Coral returned no new id/URL and no existing id; do not claim ticket creation.

Withdraw only when the user asked for it, or when cleaning up an explicitly authorized test ticket:

```bash
bytedcli --json coral permission withdraw --region sg --id <application_id> --description "Withdraw test application"
```

## Cross-region/legal gotcha

Do not hand-edit `cross_region_questions_answers`. Use `permission answer`; it maps selected Coral options to the Triton-compatible `selections` payload. If an option label contains commas, prefer the numeric option id from the draft to avoid shell/CLI splitting ambiguity.
