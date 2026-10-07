# ps.md — `forge ps get`, `forge ps fid list`, `forge ps fid query`

Use these commands for read-only Training Parameter Server data inspection.

They do not manage OnlinePS lifecycle. Continue to use:

```bash
forge serving online-ps start ...
forge serving online-ps stop ...
```

## Target selection

Every PS command requires exactly one target selector:

```bash
--job-id <training-job-id>
--model-name <model-name>
```

Prefer `--job-id` when the user names a training job. The CLI forwards the
selector to Forge, and the Forge PS API resolves the authoritative training
model and concrete Training PS. Do not ask users for a PS cluster name or ZK
path.

If Forge cannot resolve the training job or model, stop instead of guessing. A
direct `--model-name` is passed to Forge as supplied.

Pass the target `--site` explicitly when it is known.

## Current Training PS information

```bash
forge ps get --job-id 18871067 --site cn
forge ps get --model-name demo_model --site cn
```

The result contains:

- `target`: Forge-resolved `source`, nullable `job_id`, `model_name`, and
  `ps_name`
- `model_info`: aggregate feature, vector-feature, memory, and shard counts
- `slots`: per-slot counts, dimension, banned count, and estimated memory
- `shards`: per-shard health, host, feature counts, memory, and timestamps
- `query_time`: the backend observation time

`query_time` is the observation time returned by Forge. Treat the result as the
latest Training PS information available to this request.

## List FIDs by slot

```bash
forge ps fid list \
  --job-id 18871067 \
  --slot 100 \
  --shard 3 \
  --site cn

forge ps fid list \
  --job-id 18871067 \
  --slot 100 \
  --limit 50 \
  --bias-index 20 \
  --vec-index 20 \
  --shard 3 \
  --site cn
```

Flags:

| Flag | Meaning |
|---|---|
| `--slot` | Required Training PS slot ID; slot `0` is valid |
| `--limit` | Maximum bias FIDs and vector FIDs returned independently; default `20` |
| `--bias-index` | Bias cursor returned by the previous response; default `0` |
| `--vec-index` | Vector cursor returned by the previous response; default `0` |
| `--shard` | Required exact Training PS shard; shard `0` is valid |

The response keeps bias and vector FIDs separate for the requested shard and
returns `next_bias_index` plus `next_vec_index`. Use those exact values with the
same `--shard` for the next page; do not derive the next cursor from result
length or reuse it for another shard.

Per-shard errors use `err_code` and `err_msg`.

## Query values and embeddings by FID

```bash
forge ps fid query \
  --job-id 18871067 \
  --fid 10001 \
  --fid 10002 \
  --site cn

forge ps fid query \
  --model-name demo_model \
  --fid 10001,10002 \
  --shard 3 \
  --site cn
```

`--fid` is required and accepts repeated flags or comma-separated values. FIDs
are unsigned decimal strings. The CLI removes duplicates while preserving
first-seen order. One request accepts at most 6000 unique FIDs, and their
comma-separated serialization must not exceed 120000 bytes.

Each `results` row may contain:

- `fid`
- scalar fields `val` and `bias`
- `vec_w` and `vec_dim` for the embedding
- optional `shard_id`, `ip`, and `port`
- `err_code` and `err_msg`

`vec_w` is the raw embedding returned by the Training PS weight-only fetch
path. Forge returns one row for each requested FID, including an all-zero
placeholder when no non-zero value was parsed. The brief output cannot
distinguish a missing FID from a legitimate all-zero value, so do not infer or
report a `hit` state.

Use `forge ps` for these inspections; do not bypass the CLI with local PS
tools or hand-built backend requests. Forge owns target resolution,
authorization, and request boundaries, while the CLI validates stable
user-facing limits for earlier feedback.

## Current scope

- Training PS only.
- No snapshot-list command yet.
- No OnlinePS FID query yet.
- No raw debug output or infrastructure-selector flags.

Future OnlinePS support belongs under the same `ps` read-only data resource only
when the backend can resolve an OnlinePS target and return a direct raw FID
value with stable release/version provenance.
