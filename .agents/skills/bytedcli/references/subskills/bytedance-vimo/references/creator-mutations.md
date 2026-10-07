# Overseas Vimo creator mutations

This reference covers bounded writes to the CapCut overseas Creator BFF: permissions, labels,
related UID, creator source/type, application review, contracts, and punishment. Also read
[`users.md`](users.md), [`creator-list.md`](creator-list.md), and the parent Skill's
Auth section before executing a command.

## Mandatory preview and confirmation

Every command below is a pure dry-run unless `--yes` is present. A dry-run validates the inputs and
returns the exact `data.action`, `data.target`, and `data.payload` without acquiring a Vimo session
or sending a write. Show that payload and its effects to the user. Only after explicit confirmation
may the otherwise identical command be repeated once with `--yes`.

Permission grant/revoke, application approval, contract invitation, creator punishment, and other
L3 submissions require a non-empty `--reason` together with `--yes`. Account punishment is L4: a
live submission also requires `--ticket` and remains denied by default unless the local risk policy
explicitly authorizes the operator. Supplying a ticket does not bypass that default denial.

Never retry a submitted mutation automatically. If a batch stops, report `completed_uids`,
`attempted_uid`, `attempted_outcome`, `unattempted_uids`, and `partial_success`. An
`attempted_outcome` of `unknown` does **not** mean that UID failed: query its current state before
deciding whether any manual retry is safe, and never submit the untouched remainder implicitly.

## Permissions and labels

Discover dynamic values first:

```bash
bytedcli --site i18n --json vimo creator permission list
bytedcli --site i18n --json vimo creator label list
```

Use only returned `permissions[].key` and `labels[].id` values:

```bash
bytedcli --site i18n --json vimo creator permission grant \
  --uids '<capcut-uid>' --permissions '<permission-key>'
bytedcli --site i18n --json vimo creator permission revoke \
  --uids '<capcut-uid>' --permissions '<permission-key>'
bytedcli --site i18n --json vimo creator label add \
  --uids '<capcut-uid>' --labels '<label-id>'
bytedcli --site i18n --json vimo creator label remove \
  --uids '<capcut-uid>' --labels '<label-id>'
```

- `--uids` accepts at most 100 unique signed-i64 decimal strings.
- These commands add/remove incrementally; they do not replace a complete collection.
- A confirmed write re-reads the dynamic catalog before sending. If it changed, query and preview
  again.
- Revoking a publishing permission can clear creator level or trigger other Vimo side effects.
- These are not `vimocli material admin user grant|revoke`; that separate operator workflow uses
  numeric Material OpenAPI permissions and a different identity.

## Creator fields

```bash
bytedcli --site i18n --json vimo creator related-uid set \
  --uid '<capcut-uid>' --related-uid '<jianying-uid>'
bytedcli --site i18n --json vimo creator source set --uid '<capcut-uid>' --source operation
bytedcli --site i18n --json vimo creator business-type set --uids '<capcut-uid>' --type producer
bytedcli --site i18n --json vimo creator image-type set --uid '<capcut-uid>' --type producer
```

| Option                     | Values                                                                                                                                  |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `source set --source`      | `agency`, `model`, `operation`, `white-apply`, `tt-anchor`, `creativity`                                                                |
| `business-type set --type` | `normal`, `producer`                                                                                                                    |
| `image-type set --type`    | `producer`, `in-house`, `non-cn`, `cn`, `robot`, `cn-in-house`, `cn-robot`, `cn-producer`, `test`, `cn-test`, `cover-template-producer` |

`source set --force` selects Vimo's explicit force-update route; it is not a general validation
bypass. Source/type changes do not grant publishing permission. Preview and confirm each separate
change independently.

## Application review

UID plus exact `create_time` identifies an application:

```bash
bytedcli --site i18n --json vimo creator audit approve \
  --uid '<capcut-uid>' --create-time '<exact-create-time>'
bytedcli --site i18n --json vimo creator audit reject \
  --uid '<capcut-uid>' --create-time '<exact-create-time>' \
  --reason 'editing_unqualified'
```

Reject reasons may be comma-separated but must come from:
`link_not_working`, `editing_unqualified`, `material_unqualified`, `incorrect_language`,
`watermark_material`, `low_age_material`, `style_underage_eu_us`, `nonlocalized_us`.

Review always uses strict mode. Approval can grant publishing permissions and update creator
source. Never retry an uncertain review.

## Contracts

```bash
bytedcli --site i18n --json vimo creator contract invite --uid '<capcut-uid>' --type image
bytedcli --site i18n --json vimo creator contract terminate --uid '<capcut-uid>' --type image
```

- New invitations support only `image`.
- Termination supports `video|image` and is only for a current pending/unsigned contract state.
- Query the corresponding contract mode with `user list` first. Contract writes do not
  automatically mutate creator permissions or image creator type.

## Creator and account punishment

```bash
bytedcli --site i18n --json vimo creator punish apply \
  --uid '<capcut-uid>' --duration 7d --reason '<reason>'
bytedcli --site i18n --json vimo creator punish cancel --uid '<capcut-uid>' --reason '<reason>'
bytedcli --site i18n --json vimo creator account-punish apply --uid '<capcut-uid>' --reason '<reason>'
bytedcli --site i18n --json vimo creator account-punish cancel --uid '<capcut-uid>' --reason '<reason>'
```

Creator punishment accepts `3d|7d|14d|30d|forever` and affects C-side publishing/sharing.
Account punishment is a separate indefinite account action. Reasons must be 1..500 readable
characters without control characters. Account-punishment dry-runs do not require a ticket; any
authorized live submission requires both `--reason` and `--ticket`. Query current punishment fields
before and after.

## Unsupported writes

Do not expose raw `updateUser`, user create/delete, direct contract repair, score changes, copyright
reset, age-gate changes, batch auto-review, arbitrary endpoint/body, or an unmapped page button.
