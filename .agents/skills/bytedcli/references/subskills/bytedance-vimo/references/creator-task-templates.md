# CapCut overseas creator task templates

Use this reference for every `bytedcli --site i18n vimo creator task-template list` request. This leaf maps the
CapCut overseas Vimo “任务模板” list and is read-only. Dedicated create/copy/update/delete commands
are documented separately in [`creator-task-mutations.md`](creator-task-mutations.md).

## Contents

- [Scope](#scope)
- [Command and defaults](#command-and-defaults)
- [Filter matrix](#filter-matrix)
- [Examples](#examples)
- [Authentication](#authentication)
- [JSON output](#json-output)
- [Text output](#text-output)
- [Pagination](#pagination)
- [64-bit IDs and timestamps](#64-bit-ids-and-timestamps)
- [Errors](#errors)
- [Safety boundaries](#safety-boundaries)
- [Troubleshooting checklist](#troubleshooting-checklist)

## Scope

Use this command to:

- list task templates available to the CapCut overseas creator business;
- select one or more templates by exact template ID;
- fuzzy-match the upstream creator field;
- fuzzy-match the template title;
- combine all three filters;
- page through matching templates while preserving the raw nested task configuration.

Do not use this command for:

- solicitation-task records; use `--site i18n vimo creator task list`;
- Vimo material/template package lookup; use `--site cn vimo template get`;
- task-template create, edit, copy, or delete operations;
- CN Vimo or a business other than CapCut overseas.

## Command and defaults

```bash
bytedcli --site i18n --json vimo creator task-template list [options]
```

Defaults:

| Setting           | Value                | Meaning                                                 |
| ----------------- | -------------------- | ------------------------------------------------------- |
| business          | `capcut` | the only supported creator business                     |
| page              | `1`                  | one-based page number                                   |
| page size         | `20`                 | compatibility default for the shipped CLI               |
| maximum page size | `200`                | values above this fail before the request               |
| filters           | omitted              | list all task templates visible to the current identity |

Put the global `--json` option before `vimo`. Text mode is intended for quick inspection; JSON mode
is the stable form for agents and scripts.

## Filter matrix

| CLI option             | Input                                | Upstream meaning                                  | Combination                        |
| ---------------------- | ------------------------------------ | ------------------------------------------------- | ---------------------------------- |
| `--template-ids <ids>` | comma-separated positive decimal IDs | exact match against one or more task-template IDs | may combine with creator and title |
| `--creator <text>`     | one non-empty string                 | fuzzy match against the upstream creator field    | may combine with IDs and title     |
| `--title <text>`       | one non-empty string                 | fuzzy match against the template title            | may combine with IDs and creator   |
| `--page <n>`           | integer `1..1000000`                 | one-based BFF page                                | use with `--page-size`             |
| `--page-size <n>`      | integer `1..200`                     | page size                                         | use with `--page`                  |

`--template-ids` is the canonical multi-value option. The old singular `--template-id` is no
longer compatible; new commands and automation must use the plural form.

Template IDs are validated as decimal strings. Invalid examples include `0`, `-1`, `1.5`, `1e6`,
and `sample-id`. Duplicate IDs are removed before the request. The command never converts an ID to
a JavaScript number.

Creator and title filters are fuzzy, not exact. bytedcli trims them but does not otherwise normalize
the creator value: whether a username, email prefix, or another fragment matches is determined by
Vimo's creator field. A short fragment may match multiple templates. Add an exact template ID when
a single-record result is required.

When multiple filters are provided, bytedcli sends all of them in the same request and Vimo applies
them as an intersection (logical AND). The Cookie-mode integration test verifies that every returned
record satisfies the requested ID, creator, and title conditions.

## Examples

List the first page with the shipped CLI default page size:

```bash
bytedcli --site i18n --json vimo creator task-template list
```

Query one or more exact IDs:

```bash
TEMPLATE_ID_1='<template-id-1>'
TEMPLATE_ID_2='<template-id-2>'

bytedcli --site i18n --json vimo creator task-template list \
  --template-ids "${TEMPLATE_ID_1},${TEMPLATE_ID_2}"
```

Replace the sample decimal IDs with real template IDs. Do not paste angle-bracket placeholders
directly into a shell because unquoted `<` and `>` are shell redirection operators.

Fuzzy-match the creator:

```bash
bytedcli --site i18n --json vimo creator task-template list \
  --creator 'sample-creator-fragment'
```

Fuzzy-match the title:

```bash
bytedcli --site i18n --json vimo creator task-template list \
  --title 'sample-template-title-fragment'
```

Combine filters and request a larger page:

```bash
bytedcli --site i18n --json vimo creator task-template list \
  --template-ids "${TEMPLATE_ID_1},${TEMPLATE_ID_2}" \
  --creator 'sample-creator-fragment' \
  --title 'sample-template-title-fragment' \
  --page 1 \
  --page-size 200
```

Request the next page only after checking the previous result:

```bash
bytedcli --site i18n --json vimo creator task-template list --page 2 --page-size 10
```

## Authentication

### Managed sandbox or agent runtime

The runtime should inject a complete, current browser Cookie value into the command process through
`BYTEDCLI_VIMO_COOKIE`. Pass the Cookie value only; do not include the `Cookie:` header name.

Production-network sandboxes also select the production Vimo origin:

```bash
BYTEDCLI_NETWORK_PROFILE=prod \
  bytedcli --site i18n --json vimo creator task-template list --page-size 1
```

The production profile fails closed when no browser Cookie is injected. It does not fall back to a
different SSO identity and it does not send global PPE routing headers.

### Local one-shot Cookie test

Read the Cookie silently so it is not placed in shell history:

```bash
printf 'Vimo Cookie: '
IFS= read -rs BYTEDCLI_VIMO_COOKIE
printf '\n'
BYTEDCLI_VIMO_COOKIE="$BYTEDCLI_VIMO_COOKIE" \
  bytedcli --site i18n --json vimo creator task-template list --page-size 1
unset BYTEDCLI_VIMO_COOKIE
```

The shell variable remains unexported; the inline assignment exposes it only to this bytedcli child
process. If callers instead use `export`, every subsequently started child process can inherit it
until `unset` is run. bytedcli does not persist the injected value. Same-origin Cookie rotation stays
in the CLI process and does not update the browser, parent shell, environment variable, or persistent
cache. Start each new command process with a current browser Cookie snapshot. In a non-interactive
CI or sandbox, use the runtime's secret injection instead of `read -rs`.

### Office-network SSO fallback

When no browser Cookie is injected, office-network access may use the TikTok SSO/CAS session:

```bash
bytedcli --site i18n-tt auth login --session --auto --yes
bytedcli --site i18n --json vimo creator task-template list --page-size 1
```

`i18n-tt` is the global TikTok SSO site selector used by `auth login`; successful Vimo creator
responses use the normalized business site value `i18n`. These labels describe different layers of
the same overseas flow.

`BYTEDCLI_USER_CLOUD_JWT` is not a Vimo Web session and cannot replace the browser Cookie or
TikTok SSO/CAS flow.

## JSON output

A successful global JSON result has this shape:

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "page": 1,
    "page_size": 20,
    "total": 1,
    "templates": [
      {
        "template_id": "<template-id>",
        "template_name": "sample-template-title",
        "creator": "sample-creator",
        "create_time": "<unix-seconds>",
        "region": "sample-region",
        "updater": "sample-updater",
        "update_time": "<unix-seconds>",
        "task": {
          "id": "<task-id>",
          "title": "sample-task-title"
        }
      }
    ]
  },
  "error": null,
  "context": {}
}
```

Important output rules:

- `templates` contains the raw task-template records returned by Vimo.
- The nested `task` object is preserved; it is not flattened or summarized in JSON mode.
- `total` is the number of all templates matching the filters, not the current page length.
- `page` and `page_size` are added by bytedcli because the upstream result does not echo them.
- The upstream list is sorted by template `update_time` descending before BFF pagination.
- Unknown future fields remain available in each raw record.

Do not assume every optional field is present. In particular, creator, updater, region, and times
may be absent on older records.

## Text output

Text mode renders a compact table with:

- template ID;
- template name;
- creator and updater;
- region;
- create and update time in UTC;
- returned count, total, page, and page size.

Use JSON mode when the nested task configuration or unknown fields are needed.

## Pagination

The command uses one-based page pagination, not a cursor.

After each successful response, continue only when:

```text
data.page * data.page_size < data.total
```

Then request `--page <data.page + 1>` with the same filters and page size. Stop when the expression
is false. Do not use clue-list `next_cursor` values with this command.

The BFF fetches all templates matching the ID/creator/title filters, sorts them by update time
descending, and then slices the requested page. A template updated between page requests can shift
page boundaries; for a stable exact lookup, filter by template ID.

## 64-bit IDs and timestamps

Task-template IDs and nested task IDs are signed 64-bit values upstream. bytedcli parses large JSON
integers as strings and validates CLI IDs as decimal strings. Keep them quoted in JSON, shell
variables, JavaScript, and spreadsheets.

Correct JavaScript handling:

```javascript
const templateId = result.data.templates[0].template_id;
// Keep templateId as a string.
```

Do not use `Number(templateId)`: values above `Number.MAX_SAFE_INTEGER` lose precision.

`create_time` and `update_time` are Unix seconds represented as strings. Text mode formats them in
UTC. JSON mode preserves the upstream string values.

## Errors

| Error code               | Meaning                                                     | Action                                                            |
| ------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------- |
| `VIMO_INPUT_ERROR`       | invalid ID, pagination, business, or conflicting ID options | fix the command using the error hint                              |
| `VIMO_AUTH_REQUIRED`     | missing, rejected, or expired Vimo identity                 | inject a current Cookie or refresh the office-network SSO session |
| `VIMO_PERMISSION_DENIED` | identity is valid but lacks task-template read permission   | request the Vimo task-template read role                          |
| `VIMO_API_ERROR`         | Vimo returned another business error                        | inspect the message and narrow or correct filters                 |
| `VIMO_PARSE_ERROR`       | response shape or total is invalid                          | retry once, then report the sanitized response metadata           |
| HTTP `401`               | gateway rejected authentication                             | refresh the browser Cookie snapshot                               |
| HTTP `403`               | gateway or business permission denied                       | verify task-template read permission                              |

Always inspect the top-level `status` before reading `data`. On errors, consume `error.code`,
`error.status_code`, `error.message`, and the non-secret context. Never print environment values or
request Cookie headers while debugging.

## Safety boundaries

- This command performs only the list request.
- Never infer a mutation from this list reference; use only the dedicated semantic commands in
  [`creator-task-mutations.md`](creator-task-mutations.md).
- Never persist, log, echo, or return the browser Cookie, `X-Bytedance-User`, or other tokens.
- Never add PPE headers to a production-network Vimo request.
- Keep template and nested task IDs as strings.
- Use only the filters the user requested; an invalid explicit ID fails closed instead of becoming
  an unfiltered list.

## Troubleshooting checklist

1. Run `bytedcli --version` and inspect
   `bytedcli --site i18n vimo creator task-template list --help` for `--template-ids`, fuzzy creator/title
   filters, and page size `1..200`.
2. Confirm the command process receives `BYTEDCLI_VIMO_COOKIE` without printing its value.
3. In a production-network sandbox, confirm `BYTEDCLI_NETWORK_PROFILE=prod` is set.
4. Do not add `x-use-ppe`, `x-tt-env`, or `x-schedule-vdc` to production-network requests.
5. Start with `--page-size 1` and no filters to separate authentication from filter issues.
6. Test one exact `--template-ids` value, then creator, title, and combined filters.
7. Treat HTTP/business `401` as authentication and `403` as permission; do not retry permission
   failures as login failures.
8. If a browser Cookie snapshot is rejected, refresh Vimo in the browser and inject a new snapshot
   into a new CLI process.
