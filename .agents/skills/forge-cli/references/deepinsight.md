# deepinsight — `forge job deepinsight` CLI Reference

Three commands: `get-meta` → `query` → `diagnose`.

**Rule: always `get-meta` first** unless user already knows exact metric, head, and time range.
**Rule: use `AskUserQuestion` for any missing required flag. Never guess values.**
**Rule: `get-meta` is the preferred discovery source, not a completeness proof.** If
the user explicitly provides a head that is absent from metadata, preserve that
head and run the query instead of substituting another discovered head or
declaring it invalid.

---

## Key Concepts

| Term | Meaning |
|---|---|
| Instance time | Sample creation timestamp — the time axis for all queries |
| Training time | Wall-clock period the model trained on |
| Server time | When a sample was written to ClickHouse (may lag training time) |
| Storage L1 (RDS) | Permanent cache of previous query results |
| Storage L2 (ClickHouse) | Raw samples; queried on cache miss/stale |

---

## `get-meta` — discover metadata

```bash
forge job deepinsight get-meta --job-id 17728258
forge job deepinsight get-meta --job-id 17728258 --verbose  # adds databus, clickhouse_*
```

- **Required**: `--job-id`
- Response is JSON with `model_name`, `train_start_time`, `train_end_time`,
  `head_mapping`, `instance_start_time`, and `instance_end_time`.
- `head_mapping` keys are user-facing head names → prefer them as `--head` values.
- Rarely, DeepInsight has queryable heads that are not present in `head_mapping`.
  Absence from metadata is not enough to conclude the user-provided head is invalid.
- `instance_*_time` defines the valid query time range.

---

## `query` — fetch metric data

```bash
forge job deepinsight query --job-id 17728258 --metric auc --head cvr_head \
  --start-time 2026-04-01 --end-time 2026-04-07 --json
```

**Required**: `--job-id`, `--metric`, `--head`, `--start-time`, `--end-time`
**Optional**: `--time-type {day|hour|minute}`, `--sql-filters <json-array>`, `--json`, `--output <file>`

### Output

| Mode | Behavior |
|---|---|
| Default (no flags) | CSV to stdout: `date,model_name,count,value,origin,valid`; when available, stderr prints `forge2 link: <url>` |
| `--json` | JSON with `status`, `message` (contains log id), `data`, and optional `links.forge2` |
| `--output <f>` | Writes formatted result to file; stdout prints only `wrote output to <f>`; when available, stderr prints `forge2 link: <url>` |
| `--json --output <f>` | File is JSON with optional `links.forge2`; stdout still only prints path; when available, stderr prints `forge2 link: <url>` |

**Agent default: always add `--json`** unless user explicitly wants CSV/table.

`links.forge2` is the canonical Forge2 DeepInsight metric page for the executed query. Treat `links.*` values as opaque command output: use the returned link and do not hand-build a URL from job id, model name, head, metric, time range, or idc. The link may be omitted if Forge2 web endpoint resolution is unavailable; the query data remains valid.

Forge2 job-page links use `/forge2/jobs/<job-id>/deepinsight2?query=...`, a valid
format distinct from `/forge2/deepinsight/metric`. In
`query=__train:train_head__...`, the leading empty segment is expected, not a
missing metric; use any metric stated by the user. Diagnose no data from
`query` and `diagnose` results, not the URL shape.

### Empty result → run `diagnose`

If `data` is empty, run `forge job deepinsight diagnose` with the same flags. If
the user-provided head was absent from metadata, diagnose that same raw head;
do not switch to the only discovered head unless the user asks for it. See
[deepinsight_diagnose.md](deepinsight_diagnose.md).

### Time rules

Formats accepted: `YYYY-MM-DD` | `YYYY-MM-DD HH:MM` | `YYYY-MM-DD HH:MM:SS` | RFC3339 | Unix seconds.

- Omitted `--time-type` defaults to `day`.
- `day` → request uses `YYYY-MM-DD`; `hour`/`minute` → `YYYY-MM-DD HH:MM:SS`.
- `--end-time` ≥ `--start-time`.
- `site=cn` → UTC+8; other sites → UTC.
- Time range is **instance time**.

### Head resolution

Users pass a human-facing head name (e.g. `cvr_head`), not the backend `head_N` index. The CLI auto-resolves:

1. Exact match preferred.
2. Suffix match allowed (e.g. `head_a` matches `prefix_x:head_a`).
3. Ambiguous suffix → error → ask user to pick a more specific head from `get-meta` `head_mapping`.
4. No match → the CLI preserves the raw `--head` value and lets DeepInsight
   answer the query. Treat this as an unlisted-head query; report that the head
   was not found in metadata, but do not call it invalid unless the backend
   query or diagnosis proves that.

### Metric selection

`get-meta` does not enumerate available metrics. Match user intent:

| Intent | Metrics |
|---|---|
| Binary ranking quality | `auc`, `debias_auc` |
| Bias-corrected ranking | `debias_auc`, `debias_weighted_auc` |
| User-level ranking | `uauc`, `uauc_v2`, `uauc_avg` |
| Query/request grouped ranking | `qauc`, `qauc_v2`, `req_auc`, `gauc_req`, `gauc_cost` |
| Calibration / avg prediction | `pred_avg`, `label_avg`, `bias`, `calibration` |
| Probabilistic loss | `log_loss`, `rig`, `squared_loss`, `mape` |
| Graded-relevance ranking | `ndcg`, `ndcg_strict`, `label_ndcg`, `rerank_ndcg` |
| Monetization ranking | `ecpm_auc`, `ecpm_uauc`, `ecpm_ri` |
| Instance counts | `count`, `user_count` |
| Regression ranking | `regression_auc`, `reg_auc`, `reg_auc2` |
| Label-flip corrected | `flipauc`, `flipped_label_avg` |

If unsure, ask the user which intent above matches, then map to 1-2 candidates.

<details><summary>Full metric catalog</summary>

| Metric | Description |
|---|---|
| `auc` | Binary AUC (fast bucketing) |
| `debias_auc` | AUC corrected for sampling/exposure bias |
| `debias_weighted_auc` | Debiased AUC with per-sample weights |
| `uauc` | User-level AUC, sample-count weighted |
| `uauc_v2` | User-level AUC, more exact per-user calc |
| `uauc_avg` | User-level AUC, unweighted average |
| `qauc` | Query-level AUC, sample-count weighted |
| `qauc_v2` | Query-level AUC, unweighted average |
| `req_auc` | Request-level AUC, sample-count weighted |
| `gauc_req` | Group AUC by sample count |
| `gauc_cost` | Group AUC by cost/spend |
| `ndcg` | NDCG per request, averaged |
| `ndcg_strict` | Stricter NDCG variant |
| `label_ndcg` | Label-derived NDCG |
| `rerank_ndcg` | Reranking-stage NDCG |
| `ecpm_auc` | eCPM AUC |
| `ecpm_uauc` | eCPM user-level AUC |
| `ecpm_ri` | eCPM relative improvement |
| `count` | Total samples/rows |
| `user_count` | Distinct users |
| `label_avg` | Mean label |
| `pred_avg` | Mean prediction |
| `bias` | Mean(pred) − Mean(label) |
| `calibration` | Relative difference mean(pred)/mean(label) |
| `log_loss` | Binary cross-entropy (clipped) |
| `squared_loss` | 0.5 × MSE |
| `rig` | Relative information gain vs constant baseline |
| `mape` | Mean absolute % error (positive labels) |
| `regression_auc` | Correctly ordered label-pair fraction |
| `reg_auc` | Regression ranking (tie handling v1) |
| `reg_auc2` | Regression ranking (tie handling v2) |
| `flipauc` | AUC corrected for label-flip noise |
| `flipped_label_avg` | Mean label after label-flip correction |

</details>

### SQL filters

```bash
--sql-filters '[{"key":"stage_id","type":"int","op":">","value":"100"}]'
```

Each filter object requires:

| Field | Values |
|---|---|
| `key` | Field name |
| `type` | `int` \| `float` \| `str` \| `int_array` \| `float_array` \| `str_array` |
| `op` | Array types: `ArrayHas` \| `NotArrayHas` \| `IsNullOrNotArrayHas`; scalars: `>`, `<`, `=`, compounds like `% 1000 >` |
| `value` | Filter value as string |

Invalid JSON or missing fields → immediate validation error. Empty/omitted → no filters.

---

## `diagnose` — debug empty query results

Runs automated pipeline diagnosis. Only for empty results, not unexpected/partial data or explicit query error.

```bash
forge job deepinsight diagnose --job-id 17728258 --metric auc --head cvr_head \
  --start-time 2026-04-01 --end-time 2026-04-07
```

**Required**: `--job-id`, `--metric`, `--head`, `--start-time`, `--end-time`
**Optional**: `--time-type`, `--sql-filters`, `--output <file>`

**Output**: JSON with `status`, `message`, and optional `evidence` to stdout (or file via `--output`).
**Interpretation**: see [deepinsight_diagnose.md](deepinsight_diagnose.md).

---

## Agent rules

- Never invent metric names or heads. Discover candidates from `get-meta` or
  error messages, but if the user explicitly names a head that metadata does not
  expose, query that exact head once before concluding it is invalid.
- Default `query` to `--json`.
- When returning a DeepInsight page link, use `links.forge2` from JSON output, or the stderr `forge2 link: <url>` line from CSV/`--output` mode. Do not synthesize the URL.
- Treat DeepInsight as read-only: discover → query → diagnose.
- On "no data" reports, run `diagnose` first, then interpret with `deepinsight_diagnose.md`.
