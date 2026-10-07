---
name: bytedance-vimo
description: "Use for Vimo Web operations. Always route the request by deployment with the global `--site cn|i18n` option: CN covers JianYing account evidence, homepage configuration, template RID lookup/download, and commerce reads; i18n covers CapCut overseas Creator, User, Template, incentive, and controlled writes. Keep CN and overseas contracts, authentication, and references separate. Use vimocli only for Material OpenAPI workflows."
---

# ByteDance Vimo

Use one stable command shape and select the deployment globally:

```bash
bytedcli --site cn vimo <resource> <action> [options]
bytedcli --site i18n vimo <resource> <action> [options]
```

Put global options such as `--site`, `--json`, and HTTP routing headers before `vimo`.

## Route by site before loading details

Determine the business deployment from the user's object and intent, then read only the matching
site reference:

| User intent                                                           | Site   | Command family               | Read next                                                                                     |
| --------------------------------------------------------------------- | ------ | ---------------------------- | --------------------------------------------------------------------------------------------- |
| JianYing account evidence by UID                                      | `cn`   | `vimo user get`              | [`references/cn.md`](references/cn.md)                                                        |
| JianYing template RID, Vimo resource/share URL, signed ZIP            | `cn`   | `vimo template get/download` | [`references/cn.md`](references/cn.md)                                                        |
| JianYing commerce feature, benefit, or history                        | `cn`   | `vimo commerce ...`          | [`references/cn.md`](references/cn.md)                                                        |
| JianYing homepage tool, floor, priority, or relationship              | `cn`   | `vimo homepage ...`          | [`references/cn.md`](references/cn.md)                                                        |
| CapCut overseas creator, clue, task, permission, contract, punishment | `i18n` | `vimo creator ...`           | [`references/i18n.md`](references/i18n.md), then the matching creator reference               |
| CapCut UID/CapCut ID or basic-user contract-status query              | `i18n` | `vimo user list`             | [`references/i18n.md`](references/i18n.md), then [`references/users.md`](references/users.md) |
| CapCut overseas template-management list, Tab, or mutation            | `i18n` | `vimo template ...`          | [`references/i18n.md`](references/i18n.md), then the matching template reference              |
| CapCut overseas operation/incentive activity or recommended template  | `i18n` | `vimo incentive ...`         | [`references/i18n.md`](references/i18n.md)                                                    |

If the request only says “template ID” and does not identify RID/resource URL/ZIP versus overseas
template management, ask which object it is. The same noun does not imply the same backend contract.

## Domain boundaries

- Task details (任务说明、投稿、获奖名单) use `creator task get`, `creator task-submission list`,
  and `creator task-reward list`; reuse [creator-tasks.md](references/creator-tasks.md).
- `vimo creator` is the overseas 创作者管理 view. It owns creator lists, permissions, labels,
  clues, tasks, rewards, contracts, and punishments.
- `vimo user` is the overseas 用户查询/基础用户 view. It queries ordinary CapCut users by UID,
  CapCut ID, or contract status. Do not call this object a creator user or route it through
  `vimo creator`.
- `vimo template` under `--site cn` is RID lookup/download. Under `--site i18n`, it is overseas
  template management. Site selection is therefore part of the command contract.
- `vimo user` under `--site cn` is read-only JianYing account evidence by UID. Under `--site i18n`,
  it is the CapCut overseas basic-user query view.
- `vimo homepage` is the read-only JianYing homepage configuration graph. Tool IDs connect atomic
  definitions to primary/secondary orders; `relatedCategoryId` connects a primary list to one
  secondary collection. The priority view is a filtered online primary-list view, not a fourth entity.
  Runtime primary-list matching checks smaller priority values first and keeps only the first matched
  list per category type; confirm conflicts against the CN reference before treating a later row as
  effective.
  When `homepage graph get` returns `experiment_vids`, follow the mandatory VID-to-Libra procedure in
  the CN reference for every VID. This JianYing homepage workflow always queries Libra app `147`;
  Vimo's `appId=1775` is a separate namespace. A VID is a version ID and must never be used as a
  Flight ID.
- Homepage floors are a separate entity from the tool ordering graph. `homepage floor list` reads
  the configuration library, `homepage floor-priority list` is its published/online ordering view,
  and `homepage floor get` resolves item `toolId` references plus experiment VIDs. The runtime client
  consumes a server-resolved feed rather than the Vimo admin payload directly, and may insert a local
  album-to-video floor, so configured priority is not guaranteed to be the absolute on-screen order.
- Overseas `creator list`, `user list`, and `template list` accept optional `--biz capcut`.
  Omitting it defaults to CapCut. Historical `--biz 106` remains accepted for existing scripts;
  both forms resolve to numeric bid `106` in Vimo requests. New calls should use `capcut`.
  Regional selectors such as `--biz-ids` and `--region-biz-id` are separate concepts.

Use `vimocli` instead for Material CRUD, upload/publish, custom fields, service-account OpenAPI,
and cross-business material administration.

## Site policy

The CLI accepts flat commands without an explicit site for older callers and infers the deployment
from the selected capability. New commands, documentation, and automation must generate
`--site cn|i18n` with the flat `vimo` tree. `--site i18n-tt` is accepted as an overseas site alias,
but canonical Vimo commands use `--site i18n`.

An explicit site must agree with the selected capability. Do not retry a site mismatch by dropping
`--site`; correct the routing decision instead.

## Execution and safety

1. Verify the selected leaf and requested flags with `--help` when the installed version is
   uncertain. Do not substitute a nearby command when a flag is absent.
2. Keep every UID, template ID, task ID, benefit ID, and other 64-bit identifier as a decimal
   string. Never coerce it to a JavaScript number.
3. For reads, check top-level `status` before consuming `data`, and follow only the pagination
   fields documented by the matching reference.
4. Never print, persist, or put Cookie/JWT values in command arguments. Treat injected credentials
   as process-scoped secrets.
5. When a CN read fails with `VIMO_PERMISSION_DENIED`, read the CN permission guidance, show the
   returned Kani permission and dry-run command, then ask whether the user wants to request it. Do
   not submit an approval unless the user explicitly requested automatic application in the original
   prompt or confirms after seeing the denial.
6. For writes, read the matching mutation reference first. Preview without `--yes`, show the exact
   action/target/payload and effects, obtain explicit confirmation, then submit once. L3 submissions
   also require `--reason`; L4 submissions require `--reason` and `--ticket` and remain denied by
   default unless the caller is explicitly authorized. Never automatically retry an unknown
   mutation outcome. Vimo performs the final permission check for every read and write.

## Progressive references

Read the site reference first, then load only the leaf reference required by the request:

- CN routing, authentication, template inputs, and commerce tuple model:
  [`references/cn.md`](references/cn.md)
- Overseas routing, authentication, network profile, and domain selection:
  [`references/i18n.md`](references/i18n.md)
- Creator list: [`references/creator-list.md`](references/creator-list.md)
- User query: [`references/users.md`](references/users.md)
- Creator clues and clue plans: [`references/creator-clues.md`](references/creator-clues.md),
  [`references/creator-clue-plans.md`](references/creator-clue-plans.md)
- Creator tasks and task templates: [`references/creator-tasks.md`](references/creator-tasks.md),
  [`references/creator-task-templates.md`](references/creator-task-templates.md)
- Overseas template list and navigation Tab: [`references/templates.md`](references/templates.md)
- Creator mutations: [`references/creator-mutations.md`](references/creator-mutations.md)
- Clue/task mutations: [`references/creator-task-mutations.md`](references/creator-task-mutations.md)
- Overseas template mutations: [`references/template-mutations.md`](references/template-mutations.md)
- Shared invocation and troubleshooting: [`../../invocation.md`](../../invocation.md),
  [`../../troubleshooting.md`](../../troubleshooting.md)
