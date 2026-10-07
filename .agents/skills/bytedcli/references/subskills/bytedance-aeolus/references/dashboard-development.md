# Dashboard change workflow

Router: this skill's SKILL.md (named GUIDE.md in the bytedcli mirror). This file is the process for changing an existing dashboard: re-anchor the live object, pick the smallest change, then verify the same component. Command flags live in the command branches. Do not treat [aeolus.md](aeolus.md) as command body.

Command branches:

- sheet / filter / layout / card title / publish: [dashboard.md](dashboard.md)
- chart type / axis title / legend / number format / query fields: [report-chart.md](report-chart.md)
- computed fields / Join / SQL / sync: [dataset.md](dataset.md)

## Definitions

- **Dashboard**: the whole artifact (`dashboardId`)
- **Sheet**: one tab (`sheetId`)
- **Component**: a visible card, usually `chart_<reportId>`
- **Report**: a saved chart/query (`reportId`)
- **Dataset**: the field model behind a report (`datasetId`)

These are not interchangeable. Most mistakes come from editing a saved report that is not on the tab the user is looking at.

## Workflow

### 1. Re-anchor on the live URL

Parse `appId`, `dashboardId`, and `sheetId` from the user URL. If `sheetId` is missing, inspect the dashboard or ask which tab they mean.

Fetch the live sheet before changing anything. Command: [dashboard.md](dashboard.md) `dashboard sheet get`.

Map visible components to `componentId` / name / `reportId` / layout.

When changing an existing card, confirm its current `reportId` in the live sheet component tree. Configure and validate a new report before attaching it to the sheet.

### 2. Pick the smallest change, then its command branches

| User ask | Change | Then read |
|---|---|---|
| 卡片标题 | sheet `component.props.title.text`，`dashboard update` | [dashboard.md](dashboard.md) |
| 图例、轴标题、颜色、小数位、单位 | `report style` only | [report-chart.md](report-chart.md) |
| 字段加到表格、TopN、趋势分组、已有字段改查询 | that report's query | [report-chart.md](report-chart.md) |
| 筛选项、联动、布局、tab | sheet payload | [dashboard.md](dashboard.md) |
| 新计算字段、Join、口径、回刷 | dataset | [dataset.md](dataset.md) |

Read only the command references needed for the current step, including [dashboard.md](dashboard.md) for sheet re-anchoring and verification.

Display-only: `chart get` then `report style` dry-run, then `--yes`. If `chart get` already has dimMet / `display.conf`, do not `report resolve`.

Query change: inspect the dataset's existing fields and their meanings before choosing changes to the report, dataset, or upstream data source. Reuse a field when its semantics satisfy the request.

If a saved report is reused and the change is not universally safe, create a new report and rewire only this sheet component. Add the new `reportId` to the applicable public-filter `chartIDs`. Remove the old ID only when no component in this sheet still references it. Verify with `dashboard query` on the new report and any unchanged cards using the old report. Commands in [report-chart.md](report-chart.md) / [dashboard.md](dashboard.md).

`report update` rebuilds the query from the flags you pass. Do not use it to patch style. Do not follow it with a raw PUT unless `report resolve` then proves the saved config is broken.

### 3. Verify the same thing the user sees

Use the live `sheetId` and the target `reportId`:

1. Re-fetch the live sheet; the component still points at that `reportId`.
2. For query changes: `report query --format sql` for the intended field in SQL; `report query --format data` for returned columns. Do not use `chart get` or `--include-sql` as query evidence — they do not return `columns`/`rows`.
3. For axis/legend/number format: `report style get` shows the patched `display.conf` / field format. For card title: live sheet `component.props.title.text`.
4. For filter/layout: sheet linkage matches `chartIDs`; `dashboard query` on the target report still works.

CLI preview is not the browser filter pipeline. Visual "it still looks wrong" needs page/screenshot inspection.

Writes: dry-run first, then submit the same payload after the user confirms. `report style` commits with `--yes`. `dashboard update` has no `--yes`; drop `--dry-run` to submit. Success HTTP is not acceptance.

## Common failure modes

- Editing a report from local cache instead of the live sheet
- Treating the visible card title as `report style` instead of sheet `component.props.title.text`
- Assuming a report name is unique
- Rewiring a card to a new `reportId` without migrating public-filter `chartIDs`
- Changing a saved report that is not the component on the tab
- Losing display aliases by rebuilding report config too broadly
- Treating `report update` / `dashboard update` success as enough without re-read

## User interaction

Short corrective feedback means re-anchor on live evidence. State what was wrong, which live object is in play, and what changes next.

When reporting completion, include dashboard/sheet/report IDs, the visible field or chart behavior after the change, and any unconfirmed browser-cache risk.
