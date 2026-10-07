# localrun_lgtf.md - `forge localrun` for LGTF local debugging

Use this reference when the user wants ForgeIDE local model debugging for LGTF / LagrangeTF projects in Sail containers, especially Norbert stages with `train_mode` `lgtf` or `base_gpu`. For common localrun tool setup, workspace layout, and discovery-first behavior, follow [localrun.md](localrun.md). This file only records LGTF-specific differences.

## Contents

- [When to use this reference](#when-to-use-this-reference)
- [Capability selection](#capability-selection)
- [Command flow](#command-flow)
- [`init`](#init), [`compile`](#compile), [`data-dump`](#data-dump), [`data-process`](#data-process), and [`run`](#run)
- [Weight loading and replay](#weight-loading-and-replay)
  - [Discover and collect online replay artifacts](#discover-and-collect-online-replay-artifacts)
  - [Sync Jaguar checkpoint](#sync-jaguar-checkpoint)
  - [Async Dandelion online PS](#async-dandelion-online-ps)
  - [Request and topology rules](#request-and-topology-rules)
  - [Replay limitations and interpretation](#replay-limitations-and-interpretation)
  - [Replay acceptance](#replay-acceptance)
- [Profiling](#profiling)
  - [TensorFlow Profiler and advanced artifacts](#tensorflow-profiler-and-advanced-artifacts)
  - [Nsight Systems](#nsight-systems)
  - [Graph-hook tensor and summary dumps](#graph-hook-tensor-and-summary-dumps)
- [Diagnosis focus](#diagnosis-focus)
- [Response rules for agents](#response-rules-for-agents)

## When to use this reference

Read this reference only after [localrun.md](localrun.md#routing-workflow) identifies the project as LGTF / LagrangeTF from explicit framework wording or project evidence. Strong evidence includes an LGTF-selected template, Norbert `train_mode` `lgtf`, or a Sail project whose `base_gpu` stage is paired with LGTF config/runtime dependencies such as `producer` plus `runner_local_run`. `base_gpu` by itself is not sufficient because it can occur in non-LGTF training contexts.

Do not enter this reference merely because a request contains `checkpoint`, `dense-checkpoint-path`, weight loading, online PS, `nsys`, profiling, timeline/trace, memory snapshot, or graph-hook wording. Those describe a capability, not the framework. In particular, keep an explicitly LagrangeTorch/Torch localrun request in [localrun_lgtorch.md](localrun_lgtorch.md), even when it also mentions checkpoint or profiling.

LGTF and Sailor can both run inside ForgeIDE framework `Sail`. The installed localrun dispatcher distinguishes them from `.forge/localrun/training/localrun.yaml`: LGTF configs include `cmd.data-process` plus SCM dependencies such as `producer` and `runner_local_run`; Sailor configs use the shorter Sailor chain and `sailor_localrun.yaml`.

## Capability selection

After LGTF is confirmed, select the LGTF mode from intent and the current `localrun.yaml` / live help:

| LGTF intent | Guidance |
|---|---|
| Ordinary local execution with fresh/unloaded weights | Follow [Command flow](#command-flow), ending at [`run`](#run). |
| Load a retained Sync Jaguar checkpoint | Follow [Sync Jaguar checkpoint](#sync-jaguar-checkpoint). |
| Read weights from an Async Dandelion online PS | Follow [Async Dandelion online PS](#async-dandelion-online-ps). |
| Collect performance or graph diagnostics | Apply [Profiling](#profiling) to a short LGTF `run`. |

The first three rows are mutually exclusive weight modes for one run. Profiling is an optional overlay, subject to its rank/window constraints and the Async online-PS graph-hook restriction. Treat replay and profiling as LGTF `run` capabilities, not standalone localrun subcommands.

## Command flow

LGTF localrun uses the five-step chain:

```text
init -> compile -> data-dump -> data-process -> run
```

Do not route LGTF to Sailor `eval`. LGTF replay and profiling are modes of the normal `run` command, not separate subcommands.

Default command selection rules:

- Full LGTF localrun: `init -> compile -> data-dump -> data-process -> run`.
- Data-only / producer-only: `init -> compile -> data-dump -> data-process`.
- Runner-only: run `run`; if it fails because compile output or MiniBatchRequest input is missing, backfill the upstream stages.
- Weight loading/replay: prepare a graph-compatible MiniBatchRequest, then select exactly one weight source under [Weight loading and replay](#weight-loading-and-replay).
- Profiling: add the controls under [Profiling](#profiling) to a short `run`; do not create a separate profiling workflow.
- Stepwise requests: run one command at a time, report its output/log paths and result, then wait for confirmation before continuing.

## init

```bash
forge localrun init --job-config <job_config_var> --stage-name <stage_name>
```

Effects:

- Selects the LGTF template for Sail Norbert train modes `lgtf` and `base_gpu`.
- Writes `.forge/localrun/training/localrun.yaml` when missing.
- Installs LGTF dependencies, including producer, driver, base runner, Sail, and runner_local_run SCM deps.
- Creates `training/data_process/` in addition to init / compile / data_dump / run directories.

If init reports an unsupported Sail train mode, inspect the selected Norbert stage before changing localrun config. Sailor modes such as `common`, `catchup_batch`, and `catchup_stream` should use [localrun_sailor.md](localrun_sailor.md).

## compile

```bash
forge localrun compile
forge localrun compile --gflag base_gpu_mode=dandelion_v3
forge localrun compile --gflag training_graph_key=training/gpu_dandelion_v3
```

LGTF compile follows Norbert coordinator configuration and runs the Sail make.py-style compile path plus LGTF postprocessing. It no longer uses the Sailor-style `--commit-id` download or `reuse` model-meta path.

Use `cmd.compile.gflags` in `localrun.yaml` for reusable overrides, or CLI `--gflag key=value` for one-off compile overrides. Useful override keys include `base_gpu_mode`, `compile_option`, `training_graph_key`, `runner2ps_in_cpu_concat`, `pilot_is_eval`, and `extra_bvc_lib`.

Compile output is under `.forge/localrun/training/compile/<runid>/output`, with `summary.json` carrying the resolved graph, model root, and runtime dependency information for downstream data-process/run.

## data-dump

```bash
forge localrun data-dump --count <records_or_batches> --preview-count <n>
```

This stage uses the shared TF-family Primus data-dump implementation. It reads Norbert / Fountain data source config, writes binary Primus cache under `.forge/localrun/training/data_dump/<runid>/output/binary`, and optionally writes preview samples under `output/preview/sample.jsonl`.

Use this stage for physical data reachability, date range, FeatureStore selection, HDFS/Hadoop config, and raw data preview checks.

Choose `--count` from the Fountain batch size, not as a fixed magic number. Because Fountain may filter samples before producing MiniBatchRequest input, dump more than one Fountain batch's worth of records so downstream `data-process` has output after filtering.

## data-process

```bash
forge localrun data-process
forge localrun data-process --primus-cache-path <data_dump_output>
```

LGTF data-process converts dumped Primus cache into `MiniBatchRequest` files for runner_local_run. It reads the latest compile output and latest data-dump output by default.

The command auto-infers runner sharding / shard count where possible from local GPUs and Norbert stage configuration. If the input sample count is too small for the inferred sharding or batch semantics, increase data-dump count carefully or reduce local batch/sharding settings for the localrun config.

Important artifacts:

- `.forge/localrun/training/data_process/<runid>/output/summary.json`
- `.forge/localrun/training/data_process/<runid>/output/MiniBatchRequest*`

## run

```bash
forge localrun run
forge localrun run --build-path <compile_output> --binary-data-path <MiniBatchRequest_file_or_dir>
forge localrun run --gflag train_step_limits=1
forge localrun run -- --train_step_limits=1
```

LGTF run invokes `runner_local_run` with the compile output and MiniBatchRequest input. Use it to answer whether the LGTF local chain runs through with local data. It is a local runner execution path, not a Sailor online-PS eval path.

Runner gflags and envs are imported from Norbert only through a small allowlist, so the local runner receives much less than the online runner role configuration. This is intentional because LGTF local runner topology often differs from online topology: local ports, process wiring, GPU visibility, sharding, graph-hook dumps, and test-only step limits are local concerns. Require users to configure runner-specific gflags/envs explicitly through `cmd.run.gflags` / `cmd.run.envs` in `localrun.yaml`, or through one-off CLI/raw gflag overrides when live help supports them.

The Norbert runner import is mainly for graph identity / runner behavior and debug knobs, such as `enable_new_runner`, `training_graph_key`, compression method gflags, `runner_graph_hook`, `RUNNER_LOCAL_RUN_DUMP_*`, XLA, and GLOG settings. Do not assume other online runner gflags/envs are present locally just because they exist in Norbert.

Key configuration:

- `cmd.run.args.gpu-num` and `visible-devices`: local GPU count / CUDA visibility; defaults are inferred with `nvidia-smi` where possible.
- `cmd.run.args.runner-type`: `dandelion` or `jaguar`; inferred from Norbert stage roles when unset.
- `cmd.run.gflags.train_step_limits`: local training step limit; template default is `1`.
- `cmd.run.gflags.shard_num`: auto-filled for common Jaguar / Dandelion cases when possible.
- `cmd.run.envs.RUNNER_LOCAL_RUN_DUMP_*`: graph-hook summary/tensor dump controls.

Gflag precedence for run is:

```text
Norbert runner allowlist < localrun.yaml cmd.run.gflags < CLI --gflag / raw gflags
```

Env precedence for run follows the same source policy: Norbert runner allowlist first, then explicit `localrun.yaml cmd.run.envs` and intentionally provided local execution env. Online Norbert role envs outside the allowlist are not automatically available in LGTF localrun; if they matter, translate them deliberately for the local topology instead of copying the online environment wholesale.

## Weight loading and replay

Replay is the normal five-step LGTF flow with a recorded request and one explicit weight source. Keep the compile output, MiniBatchRequest, graph key, feature contract, runner type, and weight topology from the same model/stage. Hash the selected request and record the exact run directory and dependency versions before comparing outputs.

There are two supported user-facing modes. Do not combine them.

### Discover and collect online replay artifacts

Start from the exact source job and stage; do not infer provenance from a path, timestamp, or latest-stage default. All commands below are read-only. Add the correct global `--site` for the source job when it is not in the configured default cell.

1. List stages, select the stage that produced the target behavior, then pin that stage in metadata and log queries:

   ```bash
   forge job stage list --job-id <source_job_id> --page-size 50
   forge job meta get --job-id <source_job_id> --stage-id <source_stage_id>
   forge job log get-meta --job-id <source_job_id> --stage-id <source_stage_id> --with-roles
   ```

2. List the job's checkpoints and select by the target logical time, status, and provenance rather than simply taking the newest row:

   ```bash
   forge job checkpoint list --job-id <source_job_id> --page-size 100
   ```

   Record `checkpoint_id`, `checkpoint_time`, `training_instance_time`, `hdfs_path`, size, and status. Treat `hdfs_path` as the complete checkpoint root to stage and verify that its dense and sparse contents belong to one logical snapshot. `checkpoint save` changes retention state; run it only when the user explicitly asks to retain the selected checkpoint.

3. Discover the actual Runner/Base Runner role name from log metadata, list that role's files on the exact stage and executor, and download the service-listed MiniBatchRequest candidates:

   ```bash
   forge job log query \
     --job-id <source_job_id> --stage-id <source_stage_id> \
     --log-type primus --role <discovered_runner_role> --index <executor_index> \
     --list-files

   forge job log query \
     --job-id <source_job_id> --stage-id <source_stage_id> \
     --log-type primus --role <discovered_runner_role> --index <executor_index> \
     --log-file <listed_MiniBatchRequest_path> \
     --download --output <local_candidate_file>
   ```

   If no suitable request dump exists, the source Runner must be configured to dump multiple request candidates around the target step before rerunning it; do not mutate the source job unless the user explicitly requests that operation. `forge job log query --download` downloads files exposed by the selected Primus log manifest. When a log instead prints an HDFS/TOS/object-store artifact path, preserve that exact path and use the environment's authorized storage client; do not guess a path or treat log download as a generic object-store copier.

4. Build a local manifest before replay. Record source job/stage/site, role/executor/log path, remote size, local SHA256, request rank/count, selected checkpoint metadata, model commit, compile artifact/graph key, Runner/Base Runner/Driver/Sail/Toolbox versions, device type, and intended graph target. Verify downloaded size before renaming a temporary file into the candidate set.

Collect more than one request per online rank when strict parity matters. `countN` records receiver arrival order and is not a stable graph-batch identity. Decode the candidates and match them to the online target by an identity multiset such as `(uid, req_time, req_id, sample_id)` plus labels; never use prediction values to choose the request. Only after each rank has one unique match should the selected rank-specific files be passed to localrun.

### Sync Jaguar checkpoint

Use a complete Jaguar checkpoint root containing both sparse manifests/shards and the dense checkpoint, not only the `.jaguar_dense` file:

```bash
forge localrun run \
  --build-path <compile_output> \
  --minibatch-request-path <request_file_or_ranked_directory> \
  --runner-type jaguar \
  --gpu-num <local_rank_count> \
  --visible-devices <device_list> \
  --dense-checkpoint-path <complete_checkpoint_root> \
  --jaguar-checkpoint-staging-strategy hardlink \
  --gflag train_step_limits=1
```

Toolbox creates an isolated sparse checkpoint view per local rank and shares the resolved dense file read-only. `hardlink` avoids copying but requires the checkpoint and localrun workspace to be on the same filesystem. Use `copy` explicitly across filesystems; there is no silent fallback.

### Async Dandelion online PS

Use the exact online PS model with exactly one discovery source:

```bash
forge localrun run \
  --build-path <compile_output> \
  --minibatch-request-path <request_file_or_directory> \
  --runner-type dandelion \
  --gpu-num <local_rank_count> \
  --visible-devices <device_list> \
  --ps-zk-path <online_ps_zk_path> \
  --ps-model-name <exact_online_ps_model> \
  --gflag train_step_limits=1 \
  --shard-num <online_ps_shard_count>
```

Replace `--ps-zk-path` with `--ps-route-file <ordered_route_json>` when using an explicit route file; the two are mutually exclusive. Do not supply `--dense-checkpoint-path`: after the replay graph and checkpoint graph pass the fail-closed audit, Erdos materializes dense state locally from that same PS and reads sparse values from it during forward execution. The mode is Dandelion-only and forward-only. It rejects caller-owned `eval`, DeepInsight, runner-to-PS, optimizer, checkpoint-dump, summary, and external runner-hook controls. Profiling controls remain independent and may be used when their windows and ranks are valid.

An online PS replay is not a frozen atomic snapshot: dense materialization happens before sparse lookup, so a changing PS can expose time skew. Use a retained complete checkpoint for durable, offline, same-state reproduction.

### Request and topology rules

- Treat local runner count and sparse/PS shard count as separate dimensions. `runner_sharding` controls local request distribution and normally follows local `gpu-num`; producer/runtime `shard_num` describes the serialized sparse/PS topology. They do not need to be equal: eight local ranks with `shard_num=20` is valid when the matching request/PS topology has 20 shards.
- For Async PS, generate the MiniBatchRequest with the online PS shard count during `data-process`, for example `forge localrun data-process --flag runner_sharding=8 --flag shard_num=20`. Preserve that `shard_num` for `run`. Changing only the run gflag cannot reshape an already serialized request whose fetch-input width is wrong; regenerate it.
- Ordinary `MiniBatchRequest*` files use the shared-directory behavior. To preserve an online multi-rank assignment, provide a directory containing only rank-specific names with both a MiniBatchRequest marker and `rank<N>`, such as `MiniBatchReq.rank0.count0`. The rank set must be exactly `0..gpu_num-1`; mixed shared/ranked files or a missing rank fail before startup.
- A request-dump `countN` can reflect RPC arrival order before the runner barrier, not graph consumption order. For strict online parity, capture multiple candidates per rank, match candidates by `(uid, req_time, req_id, sample_id)` plus labels, select one request per rank, and rerun a fresh single step so candidate discovery does not change RNG position. Here `req_time` is part of the request identity; do not select candidates by prediction values or by unrelated log/execution timestamps.
- Use enough input to satisfy Fountain filtering and batching. An empty data-process output from a tiny dump is not evidence of a replay bug.

### Replay limitations and interpretation

Loading a checkpoint is a proxy for one part of online execution, not a promise to reproduce online behavior bit for bit. A result depends on the complete execution state: weights; graph/model code and dependencies; per-rank sample set, batch composition, row order, and shape; graph target and side effects; random-op identity, call order, and RNG state; and device, kernel, runtime, and parallel scheduling. A checkpoint restores only the weight portion, and even that requires dense and sparse state from the same logical time.

Keep these two goals separate:

| Goal | Required interpretation |
|---|---|
| Exact-batch replay | Reuse the same rank-specific batch, row order, shape, graph target, and random-op call trajectory. This is the supported general target, subject to runtime/kernel numeric tolerance. |
| Sample-invariant replay | Expect one sample to produce the same value after moving to another rank, row, or batch shape. Stateful batch RNG does not provide this guarantee; it requires an explicit model/op-level stateless per-sample RNG contract and is not a generic localrun capability. |

Account for the following boundaries when interpreting a result:

- Reprocessing the same raw sample set through Primus/Fountain can change shuffle order, batch boundaries, rank assignment, row positions, tail-batch handling, and therefore RNG invocation history. Replay captured MiniBatchRequest files for exact-batch claims.
- A complete Jaguar checkpoint must include matching dense and sparse state. A missing sparse key can take an initialization path with its own randomness.
- Async online-PS replay is especially approximate: it is not an atomic snapshot, and dense materialization can occur at a different time from sparse reads while the PS is changing.
- A forward-only local replay intentionally suppresses optimizer, statistics, embedding, and checkpoint side effects. It can validate the selected forward path, but it does not reproduce an entire online training step when those effects matter.
- Fixed scalar seeds do not bind random values to sample identity. A changed batch shape, row, graph rewrite, fetch/target, or op call count can advance stateful RNG differently. Any graph rewrite used for comparison must also be applied to an online oracle with the same semantics and disclosed explicitly.
- Different framework/compiler versions, devices, kernels, reductions, atomics, or execution schedules can cause numeric differences after input and weights match. Define tolerances before examining the result; require identical devices and runtime paths before claiming bitwise equivalence.

Accordingly, a successful checkpoint/PS load proves that localrun exercised the selected weight source and graph path. It does not by itself prove online parity, causality, or sample-invariant determinism.

### Replay acceptance

For every replay, verify both `.forge/localrun/training/run/<runid>/summary.json` and its `toolbox_summary_path` under the run output. Require `status=SUCCESS`, the intended runner type/rank count, the expected checkpoint or PS fields, and one successful runner result per rank.

For Sync Jaguar, require every rank to report successful sparse import and dense load. For Async PS, require the graph-verification and forward-only preflight markers, `online_ps_read_only_eval=true`, one `forward_results_rank<N>.jsonl` per rank, no extra training step, and no PS-write/training side-effect marker. A successful process exit without the expected rank outputs is not a successful replay.

Use layered acceptance and stop at the first failed layer:

1. **Input identity:** verify sample count and identity multiset first, then rank/batch/row mapping, shape, and labels. Candidate selection must not use predictions.
2. **Restored execution state:** verify checkpoint root/step/completeness or exact PS identity, graph key and target, model/compile/runtime versions, random-op call conditions, device, and forward-only semantics.
3. **Output comparison:** report compared-row coverage, exact-match count, and max/mean absolute differences against tolerances chosen before looking at the output. A mismatch at this layer is interpretable only after the first two layers pass.

## Profiling

Profiling is configured on `run`; localrun owns all output paths and places artifacts under the current run's `output/`. Never copy online absolute paths such as `tf_profile_dir`, `trace_path`, `tf_trace_dir`, or `tf_memory_profile_dump_dir` into `localrun.yaml`. Norbert sampling switches may be imported, but online destinations are deliberately discarded.

### TensorFlow Profiler and advanced artifacts

Configure both endpoints together; either endpoint alone is invalid:

```bash
forge localrun run \
  --tf-profile-rank 0 \
  --gflag tf_profile_start_step=0 \
  --gflag tf_profile_end_step=1 \
  --gflag train_step_limits=2
```

The window must satisfy `0 <= start <= end`, and the selected rank must be in `[0, gpu_num)`. If no rank is specified, localrun selects rank `0`, or rank `1` when `nsys` is also enabled on a multi-GPU run. `model-source-dir` defaults to `/workspace/<project>/models` when TF Profiler is enabled and supplies source locations for heat-map postprocessing; an explicit path must exist.

Expected or optional outputs include:

- `output/tf_profile/<rank>/` — TensorFlow Profiler data; compatible stacks also emit `*_per_node.csv`, `*_per_op.csv`, `*_flame.json`, and `*_model_code_with_heat_map.json`;
- `output/tf_memory_profile_dump/<rank>/` — GPU memory snapshots when `tf_mem_profile_sync_period` enables collection;
- `output/tf_trace/<rank>/` — Dandelion/Jaguar timeline or trace data.

Dandelion timeline sampling uses `timeline_interval` / `timeline_on_init`; Jaguar uses `tf_trace_interval` / `tf_trace_time_interval`. TensorFlow Profiler and timeline collection both open a TensorFlow profiling session, so schedule them on different steps. An overlap fails with `AlreadyExistsError: Another profiling session active`. For example, profile steps 0-1 and start a Dandelion timeline at step 3:

```bash
forge localrun run \
  --gflag train_step_limits=3 \
  --gflag tf_profile_start_step=0 \
  --gflag tf_profile_end_step=1 \
  --gflag timeline_interval=3
```

If an inherited Norbert profile window points outside a short local run and profiling is not wanted, explicitly set both `tf_profile_start_step=-1` and `tf_profile_end_step=-1`, and do not set `tf-profile-rank`.

### Nsight Systems

`nsys` is NVIDIA-GPU-only and captures one local rank:

```bash
forge localrun run --nsys --nsys-rank 0
```

Use `--nsys-binary <path>` only when automatic lookup from `PATH` and standard CUDA/Nsight locations cannot find it. Output is written to `output/nsys/<rank>/*.nsys-rep`.

The CUDA profiler start/stop hooks must both be present and satisfy `0 <= start < stop`. When omitted, localrun leaves one warmup step before collection and supplies runner-specific defaults: Dandelion `2/3`, Jaguar `1/2`. It raises `train_step_limits` when necessary so TF Profiler and nsys stop steps are reachable.

Do not capture TF Profiler and nsys on the same rank. On one GPU, run two short commands. On multiple GPUs, assign different ranks; the default combined layout is nsys rank `0` and TF Profiler rank `1`.

### Graph-hook tensor and summary dumps

Graph-hook dumps are adjacent diagnostics, not a TensorFlow profiling session. Enable `runner_graph_hook=insert_summary_and_identity_ops`, then narrow collection with `RUNNER_LOCAL_RUN_DUMP_SUMMARY_LIST`, `RUNNER_LOCAL_RUN_DUMP_SUMMARY_OPS`, `RUNNER_LOCAL_RUN_DUMP_TENSOR_LIST`, or `RUNNER_LOCAL_RUN_DUMP_TENSOR_OPS` under `cmd.run.envs`. Raw tensor dumping and real-time printing can create large outputs and memory pressure; start with summaries and a narrow tensor/op list.

Do not enable an external runner graph hook in Async online-PS replay: the forward-only safety boundary owns and rejects it. Use TF Profiler, timeline, memory, or nsys controls instead.

After a profiling run, inspect the localrun summary's `artifacts` list and recursively check `output/`. Treat a missing expected rank directory, an empty `.nsys-rep`, an unreachable stop step, or an overlapping-session error as a failed capture even if the model itself completed.

## Diagnosis focus

- Wrong template / unsupported mode: confirm Norbert `train_mode` is `lgtf` or `base_gpu`.
- Compile failure: inspect coordinator gflags, `base_gpu_mode`, `training_graph_key`, driver/base_runner versions, and compile `summary.json`.
- Data-dump failure: inspect data source config, HDFS/Hadoop env, and data-dump `summary.json`.
- Data-process failure: inspect latest compile output, latest data-dump binary cache, inferred sharding, and generated `MiniBatchRequest*`.
- Replay failure: verify graph/request/weight provenance first, then rank coverage, local `runner_sharding`, serialized/PS `shard_num`, checkpoint completeness or PS identity, and the replay preflight markers.
- Profiling failure: inspect selected ranks, paired step bounds, reachable stop steps, TF Profiler/timeline overlap, nsys availability, and run-scoped artifact paths.
- Run failure: inspect runner type, local GPU visibility, MiniBatchRequest path, `train_step_limits`, graph-hook envs, and runner_local_run logs.
- Output interpretation: no-weight `run` proves local execution; checkpoint/PS replay additionally proves the selected weight path. Neither proves online parity without the same requests and a same-state oracle comparison.

## Response rules for agents

- Prefer `forge localrun ...` over raw `localrun ...`.
- Keep CLI/YAML keys in kebab-case where localrun exposes kebab-case, for example `data-process`, `primus-cache-path`, `binary-data-path`, `train-step-limits` only if live help exposes it; LGTF gflags themselves often use underscore names because they pass through to runner/coordinator.
- Before relying on a flag or behavior, inspect `forge localrun -h`, `forge localrun <command> -h`, or installed source under `/release/forge_ide_ci/localrun/`.
- For ambiguous Sail-container requests, distinguish LGTF from Sailor by `train_mode` and the generated `localrun.yaml`, then read only the matching reference.
