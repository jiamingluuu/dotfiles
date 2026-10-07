# Overseas Vimo video-template mutations

These commands mutate Template Management > CapCut video templates. They are not Creator task
templates or incentive templates. Read
[`templates.md`](templates.md) and the parent Skill's mutation workflow first.

Commands require the page region's `--region-biz-id`, not the top-level CapCut bid. Global offline
(`--scope global`) defaults to `--region-biz-id 1` when omitted and preserves an explicit value. Query the
exact template in the same region before previewing. Scalar writes are dry-runs until the identical
reviewed command is repeated once with `--yes`; any target, business, or region change requires a
new preview.

Metadata, hashtag, tag-add, and originality writes are L2. Regional online/offline, copy, and full
tag replacement are L3, so live submission requires a non-empty `--reason` with `--yes`. Global
online is L4: it additionally requires `--ticket` and remains denied by default unless the local
risk policy explicitly authorizes the operator. A dry-run needs neither `--reason` nor `--ticket`.

## Metadata

```bash
bytedcli --site i18n --json vimo template metadata update \
  --region-biz-id '<region-biz-id>' --template-id '<template-id>' \
  --field title --title '<short-title>' --description '<description>'
bytedcli --site i18n --json vimo template metadata update \
  --region-biz-id '<region-biz-id>' --template-id '<template-id>' \
  --field grade --value high
```

| `--field`                                  | Required values                                     |
| ------------------------------------------ | --------------------------------------------------- |
| `title`                                    | `--title` and/or `--description`                    |
| `cover`, `ab-list-cover`                   | `--uri`, `--width`, `--height`                      |
| `ai-cover`, `list-cover`                   | `--uri`                                             |
| `default-open-mode`                        | `--value cut \| shoot`                              |
| `corner-tag`                               | `--value 0 \| 1 \| 2 \| 3 \| 4`                     |
| `ccweb-available`                          | `--value true \| false`                             |
| `segment-template-collection`, `item-type` | `--value <safe-integer>`                            |
| `grade`                                    | `--value unrated \| high \| basic \| low`           |
| `manual-review`                            | `--value not-reviewed \| reviewed \| content-error` |
| `visibility`                               | `--value feed \| profile`                           |
| `clear-music-link`                         | no `--value`                                        |

Each command updates one allowlisted field. Raw update actions and arbitrary bodies are rejected.

## Lifecycle and copy

```bash
bytedcli --site i18n --json vimo template online \
  --region-biz-id '<region-biz-id>' --template-ids '<template-id-1>,<template-id-2>' --scope region
bytedcli --site i18n --json vimo template offline \
  --region-biz-id '<region-biz-id>' --template-ids '<template-id-1>,<template-id-2>' --scope region
bytedcli --site i18n --json vimo template copy \
  --region-biz-id '<region-biz-id>' --template-id '<template-id>' \
  --target-uid '<capcut-uid>'
```

- Scope defaults to `region`; `global` is an L4 operation and remains denied by default for live
  submission even when `--reason` and `--ticket` are present.
- All L3 live submissions require `--reason`. Offline accepts the semantic reason
  `music-copyright`; online and copy accept a readable audit reason.
- There is no general permanent template-delete command. Use offline.
- Online and offline require a comma/space-separated `--template-ids` value, including when
  changing one template. Batch submissions run concurrently and return per-template outcomes;
  failures are not retried automatically.
- Copy creates a new template under the target creator. Verify target publishing eligibility and
  read the new ID from the result/list.

## Hashtags, tags, originality

```bash
bytedcli --site i18n --json vimo template hashtag add \
  --region-biz-id '<region-biz-id>' --template-ids '<template-id>' \
  --topic-ids '<topic-id>'
bytedcli --site i18n --json vimo template hashtag remove \
  --region-biz-id '<region-biz-id>' --template-ids '<template-id>' \
  --topic-ids '<topic-id>'
bytedcli --site i18n --json vimo template tag add \
  --region-biz-id '<region-biz-id>' --template-id '<template-id>' \
  --tag-ids '<v4-tag-id>'
bytedcli --site i18n --json vimo template tag replace \
  --region-biz-id '<region-biz-id>' --template-id '<template-id>' \
  --tag-ids '<complete-operation-tag-set>'
bytedcli --site i18n --json vimo template originality set \
  --region-biz-id '<region-biz-id>' --template-id '<template-id>' \
  --originality-type original
```

Hashtag operations can return per-template failures; do not replay them. Always inspect
`data.outcome` (`success`, `partial_success`, or `failed`) and `data.has_failures`, even when the
top-level CLI `status` is `success`. Failure details are normalized under
`data.add_failures`/`data.remove_failures` with string IDs and typed `err_code`/`err_reason` fields.
`tag add` appends V4 tags, while `tag replace` replaces the complete operation-channel set.
Originality values are `original`, `same-author-processed`, `different-author-processed`,
`multiple-submissions`, and `copied`.

## Unsupported writes

Do not use general template hard delete, raw update actions, unauthenticated/fire-and-forget
endpoints, internal sync/traffic/TCC/debug operations, cross-region batch sync, or unmapped page
buttons/rules.
