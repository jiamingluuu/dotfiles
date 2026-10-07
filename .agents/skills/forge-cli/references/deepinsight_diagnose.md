# deepinsight_diagnose — Diagnose Response Interpretation

Interpret the JSON output of `forge job deepinsight diagnose`. Output goes to stdout by default, or to `--output <file>`.

---

## Pipeline

```
Training Job → SDK (client) → Databus → Server → ClickHouse → Query API
     │              │              │           │
     ▼              ▼              ▼           ▼
 throughput    sdk.ok/err     databus    server.succ/err
```

`deepinsight_sdk_*` = client-side metrics. **Instance time** = sample creation timestamp. **Server time** = ClickHouse write timestamp.

---

## Response Structure

```json
{
  "status": 0,
  "message": "ok",
  "evidence": {
    "model_name": "model_a",
    "job_id": 17728258,
    "query_is_empty": true,
    "query_error": "",
    "total_instance_time_range": { "start_time": 1711929600, "end_time": 1712016000 },
    "actual_instance_time_range": { "start_time": 1711929600, "end_time": 1712016000 },
    "actual_instance_time_range_note": "",
    "metrics_search_range": { "start_time": 1711929600, "end_time": 1712016000 },
    "clickhouse": {
      "read": { "cluster": "c1", "database": "d1", "table": "t1" },
      "write": { "cluster": "c1", "database": "d1", "table": "t1" }
    },
    "metrics": {
      "training_throughput":         { "empty": false, "series": [...] },
      "deepinsight_sdk_throughput":  { "empty": true,  "series": [] },
      "deepinsight_sdk_err_throughput":   { "empty": false, "series": [...] },
      "deepinsight_server_throughput":    { "empty": false, "series": [...] },
      "deepinsight_server_err_throughput":{ "empty": false, "series": [...] }
    }
  }
}
```

Each metric has: `empty` (bool), `series[].tags` (`databus`, `why`, `model`, `dc`), `series[].dps[].y_value` (throughput), `series[].points`.

---

## TTL Check — First After an Empty Query

DeepInsight raw ClickHouse TTL varies by data; **90 days applies only to the
longest-retained data**. Use 90 days only as the conservative cutoff for a
definite expiration conclusion.
Always run `forge job deepinsight query` first so a permanently stored cached
result can still be returned. Only after that query returns empty, use the job's
training end time as the operational TTL reference before interpreting pipeline
metrics:

1. Read `train_end_time` from `forge job deepinsight get-meta --job-id <id>`.
2. Compute the cutoff as diagnosis time minus 90 days.
3. If `train_end_time` is older than the cutoff, report that TTL varies, only
   the longest-retained data reaches 90 days, and this data is beyond even that
   retention; use this as the unique primary cause and stop.
4. If `train_end_time` is empty or within the last 90 days, continue the
   pipeline checks because a shorter TTL may apply.

Apply this TTL check before and with higher priority than any `diagnose` status.
If step 3 matches, do not report a pipeline cause such as `wrong_databus_channel`.

---

## Quick Decision Table

Read `evidence.metrics` top-to-bottom following the pipeline. First matching row wins.

| Status | Trigger | Action |
|---|---|---|
| `no_training_throughput` | `training_throughput.empty: true` | Verify job running (`forge job meta get`); if running → Training Oncall |
| `sdk_send_errors` | `sdk_throughput.empty: true` + `sdk_err_throughput.empty: false` | Check `why` tag → see table below |
| `check_deepinsight_configuration` | `training_throughput: not empty` + `sdk_throughput.empty: true` + `sdk_err_throughput.empty: true` | SDK disabled, sample rate 0, or all samples filtered |
| `wrong_databus_channel` | `sdk_throughput: not empty` + `server_throughput.empty: true` + `server_err_throughput.empty: true` + wrong `databus` tag | Remove custom `deep_insight_v2_kafka_dbus_name` gflag |
| `server_receive_errors` | `sdk_throughput: not empty` + `server_throughput.empty: true` + `server_err_throughput.empty: false` | Check `why` tag → see table below |
| `miss_matched_clickhouse` | `clickhouse.read` ≠ `clickhouse.write` | Fix query config in Forge2 UI; if still wrong → DeepInsight Oncall |
| `query_range_out_of_bounds` | User range outside `total_instance_time_range` or `actual_instance_time_range` | Re-query within valid range; data outside `actual` but inside `total` = expired (permanently unavailable) |
| `diagnose_inconclusive` | All checks pass but query still empty | Remove `--sql-filters` and retry; if persists → DeepInsight Oncall |

---

## Top-Level Checks

| Condition | Meaning |
|---|---|
| `evidence` is null | Diagnosis could not run — check `message` |
| `query_is_empty: false` | Query has data — no problem to diagnose |
| `query_error` non-empty | DeepInsight returned explicit error — analyze the message |

## Time Range Checks

- `total_instance_time_range` — theoretical full instance time range that's possible for this job, derived from model metadata. Use it to detect obvious out-of-range queries. **If this field is `null`, the backend service is failing to compute it — Escalate to DeepInsight Oncall.**
- `actual_instance_time_range` — actual data in ClickHouse (may be shorter due to TTL)
- Check `actual_instance_time_range_note` for TTL expiration notice

---

## Tag Reference

### `databus` tag (in `sdk_throughput`)

| Value | Status |
|---|---|
| `deep_insight_kafka_v2` | Correct (default) |
| `deep_insight_kafka_v3` | Wrong if `dc=dy` + site=cn (v3 not deployed there) |
| Contains `ldp` (e.g. `pacs_ldp_deep_insight_channel`) | Correct — dedicated channel for Local Differential Privacy models |
| Any other custom (`deep_insight_xxx_model`) | Wrong — server not listening |

Wrong databus diagnosis: `sdk_throughput: not empty` + `server_throughput.empty: true` + `databus` is not `deep_insight_kafka_v2`, not an `ldp` channel, and not `deep_insight_kafka_v3` in a supported dc.

### `why` tag — client errors (in `sdk_err_throughput`)

| `why` | Resolution |
|---|---|
| `dbus_send` | Escalate to DeepInsight Oncall |
| `illegal_req_time` | Fix `req_time` in training code (add fountain ops with `fix_zero_req_time`) |
| `too_much_head` | Reduce heads per sample (max 100) |
| `uid_illegal` | Fix `uid` or set `-deep_insight_check_uid=false` |

### `why` tag — server errors (in `server_err_throughput`)

| `why` | Resolution |
|---|---|
| `json_parse_err` | See `json_parse_err` follow-up diagnosis below |
| `no_match_head` | Escalate to DeepInsight Oncall |
| `databus_write_err` | Escalate to DeepInsight Oncall |

#### `json_parse_err` follow-up diagnosis

When `server_err_throughput` shows `why=json_parse_err`, check the following common causes in order:

1. **Predict produces NaN**: In some training frameworks using older versions of the `cpputil/json` dependency, json serialization of a sample with a NaN predict value produces a truncated json, which then fails DeepInsight deserialization (`cpputil/json` truncates on INF/NAN). Check whether predict in the training code may output NaN/INF.
2. **Dumped LineId field contains illegal characters**: LineId fields dumped via the `deep_insight_dump_extra_fields` gflag may contain content that cannot be deserialized (e.g., un-escaped nested json strings). Inspect the LineId fields referenced by `deep_insight_dump_extra_fields` and ensure the content of the specified field is properly escaped.

If both causes are ruled out, Escalate to DeepInsight Oncall.

### `dc` tag (in `training_throughput`)

Data center identifier (`dy`, `hl`, `lf`, …). Used to check `deep_insight_kafka_v3` compatibility (v3 not deployed in `dy` at cn).

---

## `check_deepinsight_configuration` Details

SDK completely silent (no sends, no errors). Possible causes:

1. SDK disabled in training config
2. Sample rate = 0 (`-deep_insight_sample_ratio`)
3. All samples filtered out (invalid uid or inf/nan labels)

SDK sampling rule: `uid % 1000 < sample_ratio * 1000`. Samples with inf/nan labels are dropped before SDK.

---

## Escalation Checklist

When escalating to DeepInsight Oncall, provide:

- Full diagnose JSON (`--output` to save)
- Job ID and model name
- Query parameters (`--metric`, `--head`, `--start-time`, `--end-time`, `--sql-filters`)
- `total_instance_time_range` and `actual_instance_time_range`
- ClickHouse read/write config
- `why` tag values (if errors present)
- `databus` tag values (if relevant)
- Whether this worked before (if known)
