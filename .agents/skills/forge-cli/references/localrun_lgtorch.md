# localrun_lgtorch.md — `forge localrun` for LagrangeTorch local debugging

Use this reference when the user wants ForgeIDE local model debugging through `forge localrun`, especially for LagrangeTorch / lgtorch projects. This workflow is distinct from `forge code compile create --compile-mode local`: localrun is a local debug chain, while local compile is a real Forge build submission.

## Shared localrun setup

Follow [localrun.md](localrun.md#tool-model-and-discovery-first-rule) for the proxy model, live-help discovery, installation checks, and workspace layout. This file only records LagrangeTorch-specific command flow and diagnosis details.

Useful LagrangeTorch installed source entry points:

- `/release/forge_ide_ci/localrun/localrun` — command dispatcher.
- `/release/forge_ide_ci/localrun/lg_torch/init.py` — LagrangeTorch init.
- `/release/forge_ide_ci/localrun/lg_torch/compile.py` — LagrangeTorch model meta compile / reuse / download.
- `/release/forge_ide_ci/localrun/lg_torch/data_dump.py` — Primus data dump.
- `/release/forge_ide_ci/localrun/lg_torch/data_process.py` — Fountain data processing.
- `/release/forge_ide_ci/localrun/lg_torch/run.py` — local training run.
- `/release/forge_ide_ci/localrun/localrun_torch_template.yaml` or the corresponding `lg_torch` template path in the installed version — default LagrangeTorch config template.
- `/release/forge_ide_ci/localrun/localrun_sailor_template.yaml` — Sailor / lgtf-style template when debugging non-lgtorch localrun.

Framework note: this reference focuses on LagrangeTorch. Sailor uses a shorter chain without `data-process` and may expose `eval`; LGTF keeps a five-step chain but produces MiniBatchRequest input for runner_local_run. Do not blindly apply the lgtorch workflow to those frameworks.

## Command flow

LagrangeTorch has historically exposed this strict training chain, but verify exact command names and flags with `forge localrun -h` and `forge localrun <cmd> -h` before running:

```text
init -> compile -> data-dump -> data-process -> run
```

Run commands from inside `/workspace/<project>` or a child path. Prefer explicit Norbert config selection during init when the project provides a local-run job config.

Default command selection rules for agents:

- If the user asks to run localrun and does not narrow the scope, run the full lgtorch chain: `init -> compile -> data-dump -> data-process -> run`.
- If the user says to run only data / producer (`只跑数据`, `producer`, similar wording), run through data production only: `init -> compile -> data-dump -> data-process`.
- If the user says to run only model / runner (`只跑模型`, `只跑 runner`, `只跑 run`, similar wording), run only `run` by default. If `run` fails because the local Fountain input is missing (for example no latest `data.pt`), help the user run the data-production chain `init -> compile -> data-dump -> data-process` first, then retry `run`.
- If the user explicitly asks to stop after every command, run exactly one command at a time; after each command, print the result including output/log paths and any code changes, then wait for confirmation before continuing.
- Otherwise, continue autonomously through the selected command range, diagnosing the earliest failing stage before running dependent later stages.

### 1. init — initialize or repair the environment

```bash
cd /workspace/<project>
forge localrun init --job-config <job_config_var> --stage-name <stage_name>
```

Treat `--job-config` and `--stage-name` as observed LagrangeTorch flags, not hardcoded forge flags. Confirm with `forge localrun init -h` when using a new localrun version.

Effects:

- Creates `.forge/localrun/training/localrun.yaml` from the LagrangeTorch template when missing.
- Creates localrun directory structure.
- Installs dependencies from `localrun.yaml`.
- Can be rerun as an environment repair command.

For a typical lgtorch demo with `local_run_job_config` and `history_stage`:

```bash
forge localrun init --job-config local_run_job_config --stage-name history_stage
```

### 2. compile — generate or reuse model meta

```bash
forge localrun compile
forge localrun compile --reuse true --model-meta-path <compiled_meta_dir>
forge localrun compile --commit-id <commit_id>
```

Treat `--reuse`, `--model-meta-path`, and `--commit-id` as observed localrun flags. Confirm with `forge localrun compile -h` before relying on them in an unfamiliar environment.

Effects:

- Default mode runs model meta generation, usually through `python3 models/main_model.py --mode=meta_gen.MetaGenerator`.
- Output is under `.forge/localrun/training/compile/<runid>/output`.
- The compile artifact is also prepared under `/opt/tiger/pilot_gpu_service` for downstream Primus / Fountain / lgtorch runtime consumption.

Use this stage first to catch model-code import errors, feature declaration problems, invalid graph/meta generation, and missing dependencies.

### 3. data-dump — download Primus cache from physical data sources

```bash
forge localrun data-dump --count <records_or_batches> --preview-count <n>
```

Treat `--count` and `--preview-count` as observed localrun flags. Confirm with `forge localrun data-dump -h` before relying on them.

Effects:

- Reads Norbert / Fountain data source config.
- Uses compile model meta when FeatureStore selection is needed.
- Writes binary Primus cache under `.forge/localrun/training/data_dump/<runid>/output/binary`.
- Writes optional preview under `.forge/localrun/training/data_dump/<runid>/output/preview/sample.jsonl`.
- Writes output summary under `.forge/localrun/training/data_dump/<runid>/output/summary.json`.
- The binary dump follows Primus / Matrix data contracts; use Matrix IDL, Primus IO source, or the internal data-format doc for low-level interpretation.

Use this stage to validate data source reachability, date ranges, feature-store availability, and whether raw data is parseable without obvious garbling, missing fields, or schema mismatch.

### 4. data-process — run Fountain and produce local training cache

```bash
forge localrun data-process --dump-batch-num <num>
```

Treat `--dump-batch-num` as an observed localrun flag. Confirm with `forge localrun data-process -h` before relying on it.

Effects:

- Reads latest data-dump output by default.
- Reads latest compile output by default.
- Runs Fountain / producer logic from the Norbert config.
- Writes local training cache to `.forge/localrun/training/data_process/<runid>/output/data.pt`.

Use this stage to debug Fountain graph logic, dataflow names, fetch outputs, batch size, and transformations. The local-run batch size often needs to be much smaller than online training, otherwise there may not be enough dumped data to produce `data.pt`.

### 5. run — execute local training debug

```bash
forge localrun run --train-step-limits <steps>
```

Treat `--train-step-limits` as an observed localrun flag. Confirm with `forge localrun run -h` before relying on it.

Effects:

- Reads latest compile output and latest data-process output by default.
- If the fountain cache path is a directory, localrun reads `<dir>/data.pt`.
- Starts a single-node local `torchrun` training run.

Use this stage to debug actual model forward / loss / optimizer / training-code problems with local data. For runner-only requests, start here; if the failure is only missing local input, backfill the upstream data flow and retry rather than stopping at the missing-input error.

## Known-good LagrangeTorch demo flow

The following flow was validated in a ForgeIDE LagrangeTorch container for `/workspace/lagrange_torch_demo`:

```bash
cd /workspace/lagrange_torch_demo
forge localrun init --job-config local_run_job_config --stage-name history_stage
forge localrun compile
forge localrun data-dump --count 20 --preview-count 1
forge localrun data-process --dump-batch-num 1
forge localrun run --train-step-limits 2
```

Observed successful artifacts:

- compile output: `.forge/localrun/training/compile/<runid>/output`
- data-dump binary cache: `.forge/localrun/training/data_dump/<runid>/output/binary`
- data-dump preview: `.forge/localrun/training/data_dump/<runid>/output/preview/sample.jsonl`
- data-process cache: `.forge/localrun/training/data_process/<runid>/output/data.pt`
- run log: `.forge/localrun/training/run/<runid>/log/run.log`

## Diagnosis playbook

Always diagnose the earliest failing stage first. Later commands depend on previous outputs. The standard user workflow is: first compile the model to validate model code and meta generation; then data-dump to validate Norbert / Fountain datasource definitions and raw Primus data quality; then often repeat data-process to debug Fountain graph logic and produced tensors; finally run with the local Fountain cache to debug model runtime behavior.

Typical localrun goals are pre-launch model debugging: validate data-source definitions, Fountain graph correctness, whether local dumped data matches expectations, and whether model training code can run with local Fountain cache. Model code usually lives under `models/`; Norbert scheduling, training config, and Fountain graph definitions usually live under `norbert/`.

### General checks

1. Confirm current path is under `/workspace/<project>`, not bare `/workspace`.
2. Confirm `models/` and `norbert/` exist.
3. Confirm `forge localrun --help` works.
4. Confirm `.forge/localrun/training/localrun.yaml` exists after init.
5. Inspect the latest `<command>/<runid>/log/` and `<command>/<runid>/output/` directories.

### init failures

- Non-ForgeIDE or wrong framework: check `FORGE_IDE`, container framework detection, and `/release/forge_ide_ci/localrun/common.py`.
- Dependency install failure: inspect `training/init/<runid>/log/init.log` and `dependencies` in `localrun.yaml`.
- Wrong Norbert config variable or stage name: inspect `norbert/main.py` and stage names in `job_config["stage_config"]`.

### compile failures

- Import/module errors usually point to `models/` code or missing dependencies.
- Meta generation errors usually point to feature column definitions, graph declarations, or `@LG.train` dataflow bindings.
- If reusing a compiled artifact, ensure `--reuse true --model-meta-path <dir>` points to a directory with the expected LagrangeTorch model meta layout.

### data-dump failures

- Data source unavailable or wrong date range: inspect `norbert/fountain_config.py`, FeatureStorage settings, and data-source permissions.
- FeatureStore selection problems: ensure compile succeeded and model meta can be read.
- Primus cache writer failures: inspect `training/data_dump/<runid>/log/primus_cache_write.log` and related Primus IO logs.
- Validate `output/preview/sample.jsonl` when present to detect garbled or missing fields early.
- For schema, alignment, garbling, missing fields, or raw cache decoding questions, inspect the data-dump `summary.json`, Matrix / IDL proto definitions, Primus IO code, and the internal data-format doc before changing model code.

### data-process failures

- Missing input: ensure latest data-dump output has `binary/` and latest compile output exists, or pass explicit paths.
- No `data.pt`: local-run batch size may be too large for the dumped sample count. Reduce the batch size in local-run Norbert/Fountain config or increase data-dump count cautiously.
- Fountain graph or runstep binding errors: inspect `norbert/fountain_config.py` and the expected fetch name. If model code uses `@LG.train(..., dataflow="my_data")`, the Fountain config must expose the same name, preferably as `config.add_fetch(name="my_data", data_flow=instance)`. Treat mismatched names such as model `dataflow="test"` plus Fountain `add_fetch("my_data", ...)` as a real bug even if a stale compiled artifact lets one local run appear to pass.

### run failures

- Missing `data.pt`: rerun data-process and confirm `.forge/localrun/training/data_process/<runid>/output/data.pt` exists.
- Model runtime errors: inspect `training/run/<runid>/log/run.log`; failures here usually point to model forward/loss/optimizer code under `models/`.
- If localrun consumes all available batches before `--train-step-limits`, that is still a successful local debug run when the command exits cleanly.

## Response rules for agents

- Prefer `forge localrun ...` over raw `localrun ...` so forge remains the unified entrypoint.
- Keep localrun arguments in kebab-case exactly as the tool exposes them, for example `data-dump`, `data-process`, `--train-step-limits`.
- Before relying on any localrun subcommand, flag, or behavior, inspect `forge localrun -h`, `forge localrun <command> -h`, or `/release/forge_ide_ci/localrun/` source; templates are useful but not authoritative.
- Do not run broad destructive cleanup under `.forge/localrun`; old run directories are useful for diagnosis.
- When a command fails, quote the concrete log path and summarize the root cause from logs before editing code.
- If code is changed, final output must include changed file locations, what changed, and why, so the user can review whether to accept the fix.
