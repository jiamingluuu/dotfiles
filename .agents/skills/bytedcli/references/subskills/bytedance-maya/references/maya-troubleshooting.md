# Maya troubleshooting

## Authentication required

If Maya reports `MAYA_AUTH_REQUIRED`, refresh the ByteDance browser session and retry:

```bash
bytedcli --site cn auth login --session
```

Do not log in through `i18n-tt`; Maya exchanges the ByteDance session for its application cookie.

## Group or chart not found

Run `maya dashboard get` without a group filter and rediscover the live chart, group, and metric IDs. Dashboard configuration is mutable, so do not reuse IDs copied from an old analysis.

## Country filter not found

`--country` fails closed when the saved chart has no recognized country filter. Query the saved dashboard configuration or choose a chart with an explicit country dimension; do not treat the unfiltered result as country-scoped.

## Date override rejected

Pass both `--start` and `--end` as valid `YYYY-MM-DD` values. A selected-day chart requires the same date for both flags because the saved chart derives its trend windows from that day.

## Empty result

An empty result does not prove that the metric or country has no data. Check `applied_filters`, confirm the live group and chart IDs, and retry a known populated day before drawing a business conclusion.
