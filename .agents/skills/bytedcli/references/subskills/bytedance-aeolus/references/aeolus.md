# Aeolus CLI Reference (index)

Do not treat this file as command body. Read the matching branch, then stop.

Router and load rules: this skill's SKILL.md (named GUIDE.md in the bytedcli route mirror). The route mirror keeps this file at the same relative path (`references/aeolus.md`) as the domain index.

Examples using `$AEOLUS_REPORT_URL` or `$AEOLUS_DASHBOARD_URL` expect the caller to export the actual user-provided URL. Fabricated hosts are intentionally not used because URL parsing rejects unknown Aeolus hosts. Do not commit real resource IDs into docs.

## Branch files

| Branch | File |
|---|---|
| change an existing dashboard (re-anchor, smallest change, verify) | [dashboard-development.md](dashboard-development.md) |
| report / chart / style / dimMet / report-side filters | [report-chart.md](report-chart.md) |
| dashboard query / filters / diff / download / folder / sheet update | [dashboard.md](dashboard.md) |
| dataset fields / model / Join / sync / SQL / viz-query | [dataset.md](dataset.md) |
| Query Editor folders / files / templates / tmp-table / tasks | [query-editor.md](query-editor.md) |
| Shuttle / TTP / DECC | [shuttle.md](shuttle.md) |
| invocation / `--json` / prod network | `invocation.md` |
| troubleshooting | `troubleshooting.md` |

`invocation.md` and `troubleshooting.md` are shared helpers maintained by the bytedcli route skill. The subskills mirror excludes them via the sync tool's `EXCLUDED_REFERENCE_BASENAMES`, and links in the mirrored GUIDE are rewritten to `../../invocation.md` / `../../troubleshooting.md`.

## Commands by branch

- [report-chart.md](report-chart.md): `resolve-report`, `report resolve`, `report query`, `report download`, `report create`, `report update`, `report style`, `chart get`, `chart query`, `report filters`, `filter options`
- [dashboard.md](dashboard.md): `list-authorized`, `resource recent`, `resource search`, `dashboard query`, `dashboard filters`, `dashboard diff`, `dashboard download`, `dashboard create`, `dashboard build`, `dashboard update`, `dashboard version list`, `dashboard sheet get`, `dashboard folder`, `dashboard move`
- [dataset.md](dataset.md): `dataset-fields`, `dataset-dim-met-map`, `dataset-fields-download`, `dataset-fields-upload`, `dataset-model-info`, `dataset-create`, `dataset-update-sql`, `dataset-update-fields`, `dataset-add-source-table`, `dataset-add-fields`, `dataset-remove-fields`, `dataset-draft`, `dataset-sync`, `dataset-delete`, `dataset-restore`, `dataset-folder`, `dataset-move`, `query`, `viz-query`, `save-viz-query`
- [query-editor.md](query-editor.md): `query-editor folder`, `file`, `template`, `tmp-table`, `query`, `task`, `login`, `whoami`, `queues`, `datasources`
- [shuttle.md](shuttle.md): `shuttle project`, `template`, `queue`, `folder`, `task`

## What not to do

- Do not reopen this file looking for flags, option tables, or examples.
- Do not preload every branch. If `chart get` already has dimMet or style, skip `report resolve`.
- Read [dataset.md](dataset.md) or filter metadata when needed for field discovery, query construction, or validation; skip calls when existing results suffice.
- Shuttle compliance rules stay in [shuttle.md](shuttle.md). Do not reconstruct them from this index.

## JSON output

`--json` is a global option and must appear before `aeolus`. See `invocation.md`.

## Regions and auth

Region host table and serial-call rules stay in this skill's SKILL.md (named GUIDE.md in the bytedcli mirror). Dataset ClientID / Open API token stay in [dataset.md](dataset.md). Query Editor EU/US-TTP login tables stay in [query-editor.md](query-editor.md).
