# series.md — `forge job wandb` / `forge job tensorboard`

Use this reference when the user wants to inspect Wandb or TensorBoard data emitted by one or more Forge jobs. `wandb` and `tensorboard` share the same command surface and response shape; only the source differs. For install / auth basics see [invocation.md](invocation.md).

Site selection is part of series lookup. For ordinary `us` / ROW jobs, pass `--site i18n`; do **not** use `--site us-ttp` unless the user explicitly says `us-ttp` / `usttp` / TTP, or the Forge/Reckon URL hostname is `reckon-ttp.tiktok-row.net`. In other words, `us` without `-ttp` maps to `i18n` for Wandb / TensorBoard queries, local plots, reports, metric analysis, and diagnosis.

For missing / partial / abnormal **Wandb or TensorBoard** data diagnosis, also read [series_diagnosis.md](series_diagnosis.md).

Do not use that diagnosis reference for generic job metrics or DeepInsight evaluation metrics unless the user has already explicitly identified Wandb or TensorBoard as the affected surface.

---

## Discover available paths

List the available paths for one job.

```bash
forge job wandb get-meta \
  --job-id 17728258 \
  --data-type scalar

forge job tensorboard get-meta \
  --job-id 17156012 \
  --data-type image
```

Notes:

- `--job-id` is required and takes a single job id.
- If you need multiple job ids, run multiple commands — one job per invocation.
- `--data-type` is required and must be `scalar`, `histogram`, or `image`.
- The output is scoped to the selected job.
- For most training tasks, Wandb and TensorBoard are alternative surfaces rather than two surfaces that must both be populated. If the expected data is clearly present in one surface, do not keep spending time proving why the other surface is empty.

---

## Query actual data

`wandb query` and `tensorboard query` handle the whole chain directly:

1. query the backend
2. normalize the response
3. write local files into one output directory
4. print a JSON summary to stdout

```bash
forge job wandb query \
  --job-id 17728258 \
  --data-type scalar \
  --paths framework/clip_norm/dense_clip_norm \
  --paths framework/clip_norm/dense_clip_scale

forge job wandb query \
  --job-id 17728258 \
  --data-type scalar \
  --paths train/loss \
  --step-min 23601 \
  --step-max 28801 \
  --output /tmp/codex-session-123/wandb-train-loss

forge job tensorboard query \
  --job-id 17156012 \
  --data-type image \
  --paths decoder_1/layer_0_1/cross_mha_1/attn_weights_head0/image/0 \
  --event-time-min 1715600000 \
  --event-time-max 1715603600
```

Operational rules:

- `--paths` is required for `query`. Each occurrence is one exact path; repeat `--paths` for multiple values. Paths may contain commas, parentheses, or other punctuation, so never split or join a path string on punctuation. If the paths are unknown, run `get-meta` first.
- One `query` invocation accepts at most 100 unique paths after deduplication.
- `--step-min`, `--step-max`, `--event-time-min`, `--event-time-max` are optional inclusive filters for narrowing the queried window.
- `event_time` uses the same Unix-second timestamps returned in `event_times[]`; reuse those values directly when narrowing a follow-up query.
- `wandb` and `tensorboard` share the same output layout; only `source` differs.
- Suffix-numbered path families such as `loss`, `loss_1`, `loss_2`, or `family/path`, `family/path_1` are common on both surfaces; do not treat that shape alone as an anomaly.
- For scalar diagnosis, inspect `step` together with `event_time`. If many points collapse onto a few `step` values while `event_time` remains evenly distributed, switch analysis to the time axis and follow the `global_step` precision-loss path in [series_diagnosis.md](series_diagnosis.md).
- Query one job at a time; for multi-job comparisons, run multiple queries.
- For a small explicit path set, a direct `query` is fine. For larger scalar analysis sets, prefer the helper's default 10-path batches even though the CLI accepts up to 100 paths per request.

### Batched queries (>10 scalar paths or no explicit path list)

If the user does not provide an explicit path list, or the relevant scalar set is larger than about 10 paths, use the helper script shipped with this skill at `<SKILL_DIR>/scripts/batch_query_series.py`. Resolve `<SKILL_DIR>` from the active skill itself; do not assume its local install name is `forge-cli`. The helper defaults to 10 paths per query batch and waits 1 second between successful query batches; keep those defaults for fidelity-oriented reports unless the user explicitly chooses a faster coarse scan.

Before running this helper or an agent-authored analysis script, inspect the script's imports and check the user's Python environment. Install only the missing dependencies with the same interpreter that will run the script (for example, `python3 -m pip install <package>`); do not add a virtual environment or unrelated setup steps.

```bash
python3 <SKILL_DIR>/scripts/batch_query_series.py \
  --source wandb \
  --job-id 17728258 \
  --data-type scalar \
  --output /tmp/codex-session-123/wandb-17728258
```

Filter discovered paths by substring before batching when the user gives a rough pattern:

```bash
python3 <SKILL_DIR>/scripts/batch_query_series.py \
  --source wandb \
  --job-id 17728258 \
  --data-type scalar \
  --path-contains loss \
  --path-contains grad \
  --output /tmp/codex-session-123/wandb-17728258
```

Or pass an explicit path file:

```bash
python3 <SKILL_DIR>/scripts/batch_query_series.py \
  --source tensorboard \
  --job-id 17156012 \
  --data-type image \
  --paths-file /tmp/codex-session-123/tensorboard-paths.txt \
  --output /tmp/codex-session-123/tensorboard-17156012
```

Rules for batched work:

- The helper script works on one job at a time; for two-job comparisons, run it once per job and compare the two consolidated output directories.
- If `--paths` / `--paths-file` is omitted, the helper runs `get-meta`, deduplicates the discovered paths, and splits them into 10-path batches by default. The CLI accepts up to 100 paths per request, but larger batches can reduce returned point density on wide scalar queries.
- The helper intentionally favors steady progress over peak QPS. It defaults to `--request-interval-seconds 1`, `--retry-count 3`, `--retry-base-delay-seconds 5`, and `--retry-max-delay-seconds 60`. Keep those defaults when the user cares about completing a large download without hitting backend rate limits.
- If the user did not give explicit paths, first use `get-meta` to estimate the scope before launching a long batched query.
- If the user only gave a vague pattern, inspect the discovered path set first; if the matching scope is still larger than about 10 scalar paths, treat it as a batched query case.
- The helper writes successful batches directly into the final output directory and updates `files/batch-manifest.json`, `files/series-paths.jsonl`, `files/query-meta.json`, and `summary.json` after each batch. If a run is interrupted or a batch fails after retries, rerun the same command with the same `--output`; completed batches are skipped and the failed or missing batch resumes.
- If a resumed run uses a different path filter, path order, `--batch-size`, data type, or time/step filter against the same output directory, treat the old output as a different artifact and choose a new `--output` directory.
- If `--output` is omitted, the helper uses the same default root as the CLI: `<temp>/forge/series/<source>-<data_type>-<job_id>` (where `<temp>` is `os.TempDir()` / `$TMPDIR`, e.g. `/tmp` on Linux).
- When another model is doing multi-step analysis in one session, usually pass an explicit session-scoped `--output /tmp/...` so artifacts land in a directory it already knows to revisit.
- Internally the helper stages one temporary raw CLI output per active batch, then copies the completed batch files into the consolidated `data/` tree before deleting the temporary staging directory.
- Do not point multiple raw `forge ... query` invocations at the same final output directory yourself; each CLI query rewrites that directory.
- Omit `--json` by default; only add it if the downstream consumer explicitly wants JSONL.

### Confirmation checkpoints

Pause and ask the user before continuing in these two cases.

Before a long batched query:

- Trigger when the user did not specify explicit `--paths`, or when a rough path hint still expands to a multi-batch query after `get-meta` or `files/series-paths.jsonl` inspection.
- Tell the user that this query needs to run in multiple batches and may take noticeably longer.
- Use a direct confirmation such as: `这次查询需要分批执行，耗时会比较长，是否仍然按这个条件继续查询？`.
- If yes, continue with the batched helper flow. If no, ask them to narrow the path scope or provide a clearer pattern.

Before local plotting:

- Trigger when the user asks to draw or render local plots from the queried data.
- Use a direct confirmation such as: `绘图耗时可能较长，是否继续执行？`.
- Only start the plotting step after the user confirms.
- If declined, stop at the prepared data files and ask whether they want a narrower plot scope or a different output format instead.

---

## Output contract

### Summary

- The console summary is always JSON.
- The locally saved `summary.json` is also always JSON.
- `--json` does **not** change the summary format — it only changes per-path data file format.
- Omit `--json` by default so per-path data files stay in CSV.

By default the CLI prints the same summary object it writes to `<output>/summary.json`.

### `--output`

`--output` is the output directory for this query.

- If omitted, the CLI uses a simple default directory:

  ```text
  <temp>/forge/series/<source>-<data_type>-<job_id>
  ```

- If explicitly set, the CLI writes the whole query result there instead.
- The CLI returns the canonical output path after resolving symlinked parent directories.
- On macOS, `/tmp/...` commonly comes back as `/private/tmp/...` in the returned summary.
- On Linux, `/tmp/...` usually stays `/tmp/...`, unless the chosen path itself traverses another symlinked parent.
- If the returned `output_dir` differs from the path you typed, trust the returned `output_dir` / `summary_path` / `query_meta_path`; do not reconstruct paths from the original flag value.

Recommended for another model / tool isolating artifacts for one session:

```bash
forge job wandb query \
  --job-id 17728258 \
  --data-type scalar \
  --paths train/loss \
  --output /tmp/codex-session-123/wandb-train-loss
```

For batched work, pass the final target directory to the helper script instead of reusing the same raw CLI `--output` across repeated queries.

### Local layout

Artifacts are written into one output directory.

Helper-driven example:

```text
/tmp/codex-session-123/wandb-train-loss/
  summary.json
  files/
    batch-manifest.json
    query-meta.json
    requested-paths.txt
    series-paths.jsonl
  data/
    scalar.000001.csv
    scalar.000002.csv
```

Guidelines:

- `summary.json` is the main human-readable + machine-consumable summary for this query.
- `files/query-meta.json` stores exact request metadata, filters, runtime info, and provenance.
- `files/series-paths.jsonl` is the `path_id -> path` index plus point counts and the final `data_file` path under `<output>/data/`; it should be directly consumable after the merge finishes.
- Local analysis and rendering must read each JSONL record's complete `path` value as an opaque label. Never split it on commas, parentheses, slashes, or other punctuation; use `path_id` / `data_file` for file routing.
- Direct single-query CLI runs only need `summary.json`, `files/query-meta.json`, `files/series-paths.jsonl`, and `data/`.
- `files/requested-paths.txt` is added by the helper when a large path set is discovered or expanded before splitting.
- `files/batch-manifest.json` is added by the helper to record how a batched query was partitioned and merged.
- `summary.json` intentionally does not inline per-path file entries; use `files/series-paths.jsonl` for the `path_id -> data_file` mapping.
- Treat this directory as disposable unless the user explicitly asks to keep it.

---

## Data file formats

The per-path data file extension depends on `--json`:

- Default: `.csv`
- `--json`: `.jsonl`

The `path_id` routing does not change; only the data file format does.

### Scalar

CSV columns:

```text
job_id,stage_id,step,event_time,instance_time,value
```

JSONL fields:

```json
{"job_id":17728258,"stage_id":11,"step":100,"event_time":1715600101,"instance_time":1715600001,"value":0.1}
```

### Histogram

CSV columns:

```text
job_id,stage_id,step,event_time,instance_time,bins,counts
```

`bins` and `counts` are JSON-encoded arrays inside the CSV cell.

JSONL fields:

```json
{"job_id":17728258,"stage_id":11,"step":100,"event_time":1715600101,"instance_time":1715600001,"bins":[0,1],"counts":[3]}
```

### Image

CSV columns:

```text
job_id,stage_id,step,event_time,instance_time,url
```

JSONL fields:

```json
{"job_id":17156012,"stage_id":31,"step":400,"event_time":1715600301,"instance_time":1715600201,"url":"data:image/png;base64,..."}
```

Notes:

- Render the returned `url` directly.
- Many TensorBoard image queries already return `data:image/...` URLs, which can be embedded into a local static HTML report without extra downloads.

---

## Range and sampling

- Do not assume Wandb / TensorBoard stores every raw write from every worker.
- For job-backed training tasks, under common Sail / Torch-style runtime behavior, Wandb / TensorBoard is usually fed by a sampled writer path rather than every worker writing the full stream independently.
- In practice this often means only one worker participates in the observed write stream for a given run; some TensorBoard task setups may therefore skip certain `step` values entirely even when training itself is still advancing.
- Narrower `step` / `event_time` windows can help the backend relax server-side downsampling.
- This does not always mean a dramatic increase in returned point count; on many jobs and paths the returned density still reflects the underlying write cadence or remaining backend sampling.
- Even when the total point-count increase is modest, narrowing the range can surface points that were effectively omitted in a full-range query.
- Trusted domain knowledge for one effective `(job, stage, data_type, path)` stream after write-side sampling:
  - `scalar`: keep the last point in each 30-second bucket
  - `histogram`: keep the last point in each 5-minute bucket
  - `image`: keep the last point in each 60-second bucket
- If the training side emits a path at a much smaller step/time interval than those retention buckets, many writes may be dropped simply because points arrived too quickly for this surface.
- Because wide queries may be downsampled, a good workflow is:
  1. Query a broad window once.
  2. Inspect returned local files.
  3. Rerun with a tighter range around the region of interest.

---

## Plotting stance

Keep plotting flexible and agent-owned.

Before reading downloaded files with an analysis script or rendering a local report, inspect that script's imports and check the user's environment. Prefer `pandas` and `matplotlib` when they are already available; if the chosen script needs a missing package, install only that package with the interpreter that will execute it (for example, `python3 -m pip install pandas matplotlib`). Fall back to Python standard-library tooling only when those plotting dependencies are unavailable.

- Do not hard-restrict the plotting artifact; follow the user's requested format when they have one.
- If the user did not specify a format, a local static HTML analysis report is a good default because it bundles narrative, charts, and image browsing into one shareable artifact.
- In user-facing report titles, headings, and prose, say `Wandb`, `TensorBoard`, or `TensorBoard & Wandb`; avoid the generic word `series` unless you are referring to actual script names or file names such as `series-paths.jsonl`.
- Check for `pandas` and `matplotlib` before plotting. When they are already installed, use them; otherwise install only the packages needed by the chosen rendering script.
- Prefer Python when the user wants iterative chart edits; `matplotlib` is the default when available.
- HTML / SVG is also fine when the user wants a portable local artifact, or as a standard-library fallback when Python plotting libraries are unavailable.
- Do not add new CLI plotting surfaces unless the user explicitly wants productized, stable rendering behavior.
- Ask for confirmation before starting local plotting work; iteration may take noticeably longer than querying alone.
- Unless the user explicitly asks for another language, write local reports and plot annotations in Chinese by default.
- Even in Chinese reports, do not translate fixed terms or identifiers that users may need to match exactly: keep `TensorBoard`, `Wandb`, `path`, `paths`, `step`, `event_time`, `relative_time`, `wall_time`, `job_id`, `stage_id`, `path_count`, `scalar`, `histogram`, `image`, and the literal `path` string itself unchanged.
- When Chinese prose and fixed terms appear together, keep the fixed term in its original form so users can directly grep, compare, or copy it back into a follow-up query.

### Multi-job comparison

- When comparing multiple jobs, first summarize the obvious context differences before charts: compared job ids, selected paths, visible runtime or event-time window, step span, and path_count or metric-surface size for each job.
- Keep this background section focused on directly observed comparison facts from the queried artifacts; do not try to enrich job attributes or infer a richer task-profile story unless another skill or explicit user input provides that context.
- When a chart or finding refers to a specific `path`, show the exact original `path` string instead of a translated alias.
- Prioritize overall trends and comparable windows over individual points. For running or streaming jobs, treat the latest observed point as only a current sample, not a final result.
- For scalar comparisons across multiple jobs, prefer `step` or `relative_time` as the x-axis.
- When job start times differ or the visible query windows are not aligned, prefer `relative_time`.
- Compute `relative_time` from the minimum `event_time` actually present in the plotted chart.
- When rendering a time-style comparison axis for multiple jobs, format it in a human-readable `X天X小时X分X秒` style when practical.
- Default report structure for multi-job comparisons: short findings first, then charts, then raw artifact links or supporting notes.
- Make comparison charts large enough that users can clearly read x-axis and y-axis values; avoid tiny thumbnails that hide scales or labels.
- In generated images, keep legend, subtitle, axis labels, and other chart annotations from overlapping each other; if space is tight, enlarge the canvas, wrap text, or move the legend / subtitle instead of letting them collide.
- If one job has a much shorter visible window or a very different path surface, call that out explicitly so readers do not over-interpret end-value differences.
- In multi-job comparison charts, keep the legend minimal: show only `job_id`.
- Do not stuff `event_time` ranges, step ranges, path counts, or other long metadata into the legend; put that information in the chart subtitle, chart body text, or surrounding report copy instead.

For scalar plotting:

- Use exactly one horizontal axis per chart.
- Default x-axis is `step`.
- For multi-job scalar comparisons, prefer `step` or `relative_time`.
- Use `event_time` when the user explicitly wants wall-clock comparison.
- Use `value` as the vertical axis unless the user explicitly asks for a derived transform instead.
- Default grouping is one chart per path, with all jobs for that path overlaid together.
- Do not merge unrelated paths into one scalar chart by default; multi-path overlays are usually not meaningful for comparison.
- If the user asks for a different grouping, follow the user's grouping.
- For multi-job scalar overlays, each legend entry should still be only the corresponding `job_id`.
- When switching the x-axis between `step`, `event_time`, and `relative_time`, sort each plotted line by the chosen x-axis before rendering; do not assume the returned order is already correct for the new axis.
- Do not downsample saved scalar points again by default; backend results may already be sampled. If rendering requires extra sampling for very large data, state it explicitly in the report.
- `relative_time` should be computed from the minimum `event_time` actually present in the plotted chart.
- `wall_time` is just a human-readable formatting of `event_time`.

For histogram plotting:

- Default grouping is one rendered panel per `job x path`.
- Prefer the current Forge / Wandb-style ridgeline stack instead of flattening each histogram into an unrelated scalar summary.
- Use `bins` as the histogram bucket edges on the horizontal axis and `counts` as the per-bucket heights; in practice `len(bins)` is typically `len(counts) + 1`, so derive each bucket span from adjacent edges.
- Do not try to squeeze multiple jobs for the same histogram path into one panel by default; only do that if the user explicitly asks for a composite layout.
- Use exactly one progression axis per figure: default `step`, or `event_time` when the user asks for wall-clock comparison.
- Render one filled ridge per `step` or `event_time`, ordered from older to newer so the training evolution reads top-to-bottom or back-to-front in one stack.
- Prefer semi-transparent area fills on a shared white background so overlapping ridges still show the overall shape evolution.
- Default to one path per histogram figure or card; do not merge unrelated histogram paths into one stack unless the user explicitly asks for it.
- Keep each histogram panel large enough that bucket structure and labels remain legible.
- If too many histograms make the figure unreadable, sample representative steps, add a step scrubber, or rerun `query` with a narrower window before plotting.

For image plotting:

- Render the returned `url` directly.
- If `url` already starts with `data:image/`, embed it directly in the HTML instead of downloading it again.
- Show the current `step` or `event_time` next to the image; the current Forge frontend surfaces both the frame metadata and the active preview together.
- For a single path, a browsable album, timeline, or slider-driven viewer is fine.
- Default grouping is one rendered panel per `job x path`.
- For multiple paths, prefer a grid of per-path cards with independent scrubbers or prev / next controls instead of interleaving every image into one long strip.
- Do not try to squeeze multiple jobs for the same image path into one panel by default; only do that if the user explicitly asks for a composite layout.
- When related paths belong to one family such as multiple attention heads, a card grid that keeps one large preview per path is usually easier to compare than a single shared carousel.
- Keep each image panel large enough that image content remains legible.

## Validated samples

Use these known-good samples when another model needs a quick plotting sanity check on `cn`.

- Wandb scalar: job `18175692`, paths `framework/clip_norm/dense_grad_norm` and `framework/clip_norm/global_grad_norm`.
- Wandb histogram: job `18175692`, path `c_output1/activation` for the current Forge frontend-style stacked ridge view.
- Wandb histogram: job `18175692`, paths `MLPMixer/resblock_0` and `all_concat/activation` as additional backend sanity samples.
- TensorBoard image: job `17156012`, path `decoder_1/layer_0_1/cross_mha_1/attn_weights_head0/image/0`.
- For `decoder_1/layer_0_1/cross_mha_1/attn_weights_head{0,1,2}/image/0`, `head0` showed the strongest observed frame variation in the 2026-04-22 validation pass.
- These samples were re-validated on `2026-04-22`.

For zooming and refinements:

- If the user wants to zoom in on a range, prefer re-querying with tighter `--step-*` or `--event-time-*` filters over cropping the existing plot.
- Wide queries may be downsampled; a smaller server-side window can surface points the broad query did not return.
- Use the saved local query files as a convenience, not as a source of truth. If the user asks for fresher or more detailed data, query again and overwrite or replace the output directory with a fresh query.

---

## Working pattern

1. Start with `get-meta` to discover candidate paths for the selected job.
2. Narrow to the paths the user cares about.
3. If the relevant scalar set is small (about ≤10 unique paths), one direct `query` is fine.
4. If the relevant scalar set is larger than about 10 paths, or the user only gave rough path guidance, use `scripts/batch_query_series.py` to discover / filter / split / query / merge into one output directory with its default 10-path batches.
5. Inspect `summary.json`, `files/query-meta.json`, `files/series-paths.jsonl`, and the per-path data files.
6. For multi-job comparisons, normalize the path set you will actually compare and note per-job window length, step span, and path_count before plotting.
7. For report-critical scalar paths, run a focused refinement query with only those paths when the broad query is visibly sparse; use the refined output as the preferred source for those paths in the report.
8. Plot outside the CLI using the tool that best matches the user's request. If the user did not specify a preferred artifact, a local static HTML report is a good default.
9. If the user wants a new axis, a zoomed range, or finer detail, rerun `query` or the helper script with a tighter window so the saved files reflect a fresher backend fetch.

## Current scope

- The CLI scope is intentionally limited to `get-meta` and `query`; plotting is handled outside the CLI.
- Saved local query data is temporary working state, not a durable cache contract.
- A saved query may be stale, incomplete, or downsampled relative to what a fresh narrower query could return.
- The CLI reuses the repo's existing auth, endpoint resolution, and Reckon API rate limiting.
