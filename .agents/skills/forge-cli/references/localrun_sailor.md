# localrun_sailor.md - `forge localrun` for Sailor local debugging

Use this reference when the user wants ForgeIDE local model debugging through `forge localrun` for Sail / Sailor projects, especially Norbert stages with `train_mode` `common`, `catchup_batch`, or `catchup_stream`. This workflow is distinct from `forge code compile create --compile-mode local`: localrun is a local debug chain, while local compile is a real Forge build submission.

## Shared localrun setup

Follow [localrun.md](localrun.md#tool-model-and-discovery-first-rule) for the proxy model, live-help discovery, installation checks, and workspace layout. This file only records Sailor-specific command flow and diagnosis details.

Useful Sailor installed source entry points:

- `/release/forge_ide_ci/localrun/localrun` — command dispatcher and framework routing.
- `/release/forge_ide_ci/localrun/sailor/init.py` — Sailor / LGTF init and template selection.
- `/release/forge_ide_ci/localrun/sailor/compile.py` — Sailor local debug compile and optional remote model-meta download.
- `/release/forge_ide_ci/localrun/sailor/data_dump.py` — Sailor Primus data dump wrapper.
- `/release/forge_ide_ci/localrun/sailor/entry.py` — Sailor run / eval entrypoint and gflag merge behavior.
- `/release/forge_ide_ci/localrun/sailor/localrun_sailor_template.yaml` — default Sailor config template.
- `/release/forge_ide_ci/localrun/tf_utils/data_dump.py` — shared TF-family data-dump implementation used by Sailor.

Framework note: this reference focuses on Sailor under ForgeIDE framework `Sail`. LGTF also runs in `Sail` containers but has a different command chain (`data-process` exists) and template. LagrangeTorch has its own five-step chain. Do not blindly apply the lgtorch or LGTF workflow to Sailor.

## Command flow

Sailor localrun exposes a shorter training chain than LagrangeTorch:

```text
init -> compile -> data-dump -> run
```

`data-process` is not part of the Sailor chain. Sailor `run` generates the needed `fountain.dump` from Norbert and consumes data-dump binary cache directly.

Sailor also supports `eval` for PS-based offline inference. Treat it as a separate explicit workflow from the default training debug chain: run it when the user asks for Sailor eval/inference, and confirm flags with live help/source in the current environment.

Run commands from inside `/workspace/<project>` or a child path. Prefer explicit Norbert config selection during init when the project provides a local-run job config.

Default command selection rules for agents:

- If the user asks to run Sailor localrun and does not narrow the scope, run the Sailor training chain: `init -> compile -> data-dump -> run`.
- If the user asks only to pull / preview raw samples (`拉原始样本`, `预览样本`, `只看数据`, similar wording), run through raw sample dump only: `init -> compile -> data-dump`.
- If the user asks to run end to end (`端到端跑一遍`, `跑通链路`, `跑一下 localrun`, similar wording), run the full chain: `init -> compile -> data-dump -> run`. Sailor does not split producer and runner as separate user-facing workflows; data ingestion and model execution are both owned by Sailor.
- Before running `compile`, determine the build source. If the user did not say whether to reuse an already-compiled online build by `commit-id` or compile the current local code, ask them to choose; do not guess.
- If the user explicitly asks to stop after every command, run exactly one command at a time; after each command, print the result including output/log paths and any code changes, then wait for confirmation before continuing.
- Otherwise, continue autonomously through the selected command range, diagnosing the earliest failing stage before running dependent later stages.

### 1. init — initialize or repair the environment

```bash
cd /workspace/<project>
forge localrun init --job-config <job_config_var> --stage-name <stage_name>
```

Treat `--job-config` and `--stage-name` as observed localrun flags, not hardcoded forge flags. Confirm with `forge localrun init -h` when using a new localrun version.

Effects:

- Detects ForgeIDE framework and Norbert stage.
- For Sailor, supports Norbert train modes `common`, `catchup_batch`, and `catchup_stream`.
- Creates `.forge/localrun/training/localrun.yaml` from `localrun_sailor_template.yaml` when missing.
- Creates localrun directory structure.
- Installs dependencies from `localrun.yaml`, including Sailor SCM dependencies and required Python packages.
- Can be rerun as an environment repair command.

For a typical Sailor project:

```bash
forge localrun init --job-config local_run_job_config --stage-name train
```

### 2. compile — generate or download Sailor model meta

```bash
forge localrun compile
forge localrun compile --commit-id <commit_id>
forge localrun compile --compile-graphs training,serving --tensorflow-version <version>
```

Treat `--commit-id`, `--compile-graphs`, `--tensorflow-version`, `--is-parallel`, and `--framework-version` as observed localrun flags. Confirm with `forge localrun compile -h` before relying on them in an unfamiliar environment.

Compile has two user-facing modes:

- Existing online build: use `forge localrun compile --commit-id <commit_id>` to download already-compiled model meta/build output.
- Current local code: use `forge localrun compile` to compile the workspace code in the current ForgeIDE environment.

When the user asks for an end-to-end Sailor localrun and has not specified which mode they want, ask this before compile. The choice affects whether localrun validates the user's current code changes or replays data/run behavior against an existing online build.

Effects:

- Default mode runs Sail local debug compile through the local Forge compiler path.
- `--commit-id` downloads an existing remote build output for local debugging.
- The first compile graph, usually `training`, is used to sync Sailor model meta into the local runtime model directory.
- Output is under `.forge/localrun/training/compile/<runid>/output`.
- The command writes a `summary.json` containing the compile source, output path, graph, `sail_output` path, and synced model-meta location.

Use this stage first to catch model-code import errors, Sail graph/meta generation problems, incompatible TensorFlow/framework version choices, missing compiler dependencies, and malformed build output layout.

### 3. data-dump — download Primus cache from physical data sources

```bash
forge localrun data-dump --count <records_or_batches> --preview-count <n>
forge localrun data-dump --model-meta-path <compiled_meta_dir> --build-graph training
```

Treat `--count`, `--preview-count`, `--model-meta-path`, and `--build-graph` as observed localrun flags. Confirm with `forge localrun data-dump -h` before relying on them.

Effects:

- Reads Norbert / Fountain data source config.
- Uses compile model meta when FeatureStore selection is needed.
- Writes binary Primus cache under `.forge/localrun/training/data_dump/<runid>/output/binary`.
- Writes optional preview under `.forge/localrun/training/data_dump/<runid>/output/preview/sample.jsonl`.
- Writes output summary under `.forge/localrun/training/data_dump/<runid>/output/summary.json`.

Use this stage to validate data source reachability, date ranges, FeatureStore selection, HDFS/Hadoop config, and whether raw data is parseable without obvious garbling, missing fields, or schema mismatch.

Choose `--count` from the Fountain batch size, not as a fixed magic number. Because Fountain may filter samples before producing local input, dump more than one Fountain batch's worth of records so downstream `run` has output after filtering.

### 4. run — execute Sailor local training debug

```bash
forge localrun run
forge localrun run --build-path <compiled_output_or_sail_output> --binary-data-path <data_dump_binary_dir>
forge localrun run --gflag mini_batch_size=1
forge localrun run -- --mini_batch_size=1
```

Treat `--build-path`, `--binary-data-path`, `--quiet`, and `--gflag key=value` as observed Sailor localrun flags. Confirm with `forge localrun run -h` before relying on them.

Effects:

- Reads latest compile output by default.
- Reads latest data-dump output by default.
- Generates Sailor `fountain.dump` from the selected Norbert stage before invoking the toolbox run.
- Writes a per-run toolbox config named `sailor_localrun.yaml` under `.forge/localrun/training/run/<runid>/`.
- Starts Sailor local training using the resolved build output, binary data cache, dependencies, environment overrides, and gflags.

Use `run` to answer whether model compile output, data dump, Fountain generation, Sailor dependencies, and model code can connect end to end on a small local sample. Its result is primarily "did the local chain run through?" The local PS used by `run` has freshly initialized weights, so do not treat `run` outputs as the online model's meaningful prediction for a sample.

Sailor gflag precedence should match online semantics:

```text
localrun.yaml cmd.run.gflags + CLI --gflag / raw gflags > Norbert defaults > model code defaults
```

For user custom logic, prefer setting `cmd.run.gflags` in `.forge/localrun/training/localrun.yaml` when the override should be reused. Prefer CLI `--gflag key=value` or raw gflags after `--` for one-off experiments.

### eval — online-weight offline inference

Sailor `eval` connects to an online training PS and runs offline inference with the already-trained weights held there:

```bash
forge localrun eval --ps-cluster <zk_ps_path> --model-name <model_name>
```

Use `eval` to answer what the online trained model really predicts for a sample. This is the right surface for reproducing online issues that require trained weights, for example score/output mismatches that a local fresh-weight `run` cannot explain. Keep eval separate from the normal local training debug chain. When the user asks for Sailor eval/offline inference, run this path directly after confirming flags with `forge localrun eval -h` or installed source.

Before eval, determine whether the current container is a compliance container using the exact environment contract:

```bash
if [ "${IS_COMPLIANCE_MODE:-}" = "true" ]; then
  echo "compliance Sailor eval"
else
  echo "standard Sailor eval"
fi
```

Only the exact value `true` selects the compliance path. In a compliance container, Sailor eval currently requires all of the following as one compatibility set:

- Sailor SCM: `data/aml/sailor_bin_test@2.0.2.721`
- `enable_archon_ttheader=true`
- `archon_codec_type=zstd`
- `ps_client_enable_rpc_compliance=true`
- `haven_enable_rpc_compliance=true`

Persist the compatibility set in `.forge/localrun/training/localrun.yaml` under the eval command and Sailor dependency, not under `cmd.run`:

```yaml
cmd:
  eval:
    gflags:
      enable_archon_ttheader: true
      archon_codec_type: zstd
      ps_client_enable_rpc_compliance: true
      haven_enable_rpc_compliance: true

dependencies:
  scm:
    sailor:
      name: data/aml/sailor_bin_test
      version: "2.0.2.721"
      install_path: /opt/tiger/sailor_bin
```

After changing the dependency, rerun the same `forge localrun init ...` command used for the workspace. Init compares `current_revision` with the requested SCM and reinstalls the Sailor dependency when they differ. Before eval, inspect the installed dependency rather than assuming that changing YAML changed the files used by the runtime:

```bash
cat /opt/tiger/sailor_bin/current_revision
```

Verify that the recorded repository and version match `data/aml/sailor_bin_test@2.0.2.721`. If the file is missing, init failed, or the installed revision differs, stop and repair init; do not run compliance eval with an inferred or stale Sailor binary. Eval uses the configured absolute install path and does not repair a stale dependency on its own.

For a one-off invocation, the four runtime switches can also be passed explicitly after the required Sailor SCM has been installed and verified:

```bash
forge localrun eval \
  --ps-cluster <zk_ps_path> \
  --model-name <model_name> \
  --gflag enable_archon_ttheader=true \
  --gflag archon_codec_type=zstd \
  --gflag ps_client_enable_rpc_compliance=true \
  --gflag haven_enable_rpc_compliance=true
```

CLI gflags do not select or install the Sailor SCM, so they are not a substitute for updating `dependencies.scm.sailor`, rerunning init, and checking `current_revision`. In a non-compliance container, retain the ordinary Sailor version resolved from Norbert/YAML and the ordinary eval gflags; do not force version `2.0.2.721` or inject the four compliance switches.

## `localrun.yaml` configuration model

Sailor init creates:

```text
/workspace/<project>/.forge/localrun/training/localrun.yaml
```

Important sections:

- `common.norbert.job-config` — Norbert job config variable name.
- `common.norbert.stage-config` — selected Norbert stage.
- `cmd.compile.python_bin` — Python used by Sail local compile wrapper, normally the managed Python 3.11 path in current templates.
- `cmd.compile.args` — compile arguments such as `commit-id`, `compile-graphs`, `tensorflow-version`, `is-parallel`, and `framework-version`.
- `cmd.data-dump.python_bin` — Python used for Primus data dump dependencies.
- `cmd.data-dump.args` — data-dump arguments such as `count`, `preview-count`, `model-meta-path`, and `build-graph`.
- `cmd.run.python_bin` — Python used to invoke Sailor localrun tooling.
- `cmd.run.args` — run arguments such as `build-path` and `binary-data-path`.
- `cmd.run.gflags` — Sailor gflags passed through to runtime.
- `cmd.run.envs` — environment overrides for the run process.
- `cmd.eval.gflags` — Sailor eval-only gflags. Put the four RPC compliance switches here only when `IS_COMPLIANCE_MODE=true`; do not place them under `cmd.run.gflags`.
- `dependencies.pip` — Python packages installed by init.
- `dependencies.scm.sailor` — Sailor binary SCM dependency inferred from Norbert when possible. Compliance eval overrides it with `data/aml/sailor_bin_test@2.0.2.721` and requires init plus installed-revision verification.

Use kebab-case keys in YAML and CLI flags (`commit-id`, `compile-graphs`, `data-dump`, `binary-data-path`). Do not introduce snake_case or camelCase fallbacks when editing current schema unless live source requires them.

Do not treat templates alone as source of truth. If YAML behavior is unclear, inspect the installed parser/source in `/release/forge_ide_ci/localrun/` and then the current project's `.forge/localrun/training/localrun.yaml`.

## Known-good Sailor skeleton flow

Use live help/source before running this in an unfamiliar environment:

```bash
cd /workspace/<project>
forge localrun init --job-config local_run_job_config --stage-name train
forge localrun compile
forge localrun data-dump --count 20 --preview-count 1
forge localrun run --gflag mini_batch_size=1
```

Observed successful artifacts:

- localrun config: `.forge/localrun/training/localrun.yaml`
- init log: `.forge/localrun/training/init/<runid>/log/init.log`
- compile output: `.forge/localrun/training/compile/<runid>/output`
- data-dump binary cache: `.forge/localrun/training/data_dump/<runid>/output/binary`
- data-dump preview: `.forge/localrun/training/data_dump/<runid>/output/preview/sample.jsonl`
- data-dump summary: `.forge/localrun/training/data_dump/<runid>/output/summary.json`
- run workspace: `.forge/localrun/training/run/<runid>/`
- generated run config: `.forge/localrun/training/run/<runid>/sailor_localrun.yaml`

## Diagnosis playbook

Always diagnose the earliest failing stage first. Later commands depend on previous outputs. The standard Sailor localrun workflow is: init to select the correct Norbert/Sailor template and install dependencies; compile to validate local Sail model-meta generation or download remote build output; data-dump to validate Norbert / Fountain datasource definitions and raw Primus data quality; run to debug Sailor training behavior with local binary cache.

Typical localrun goals are pre-launch model debugging: validate data-source definitions, Fountain graph generation, whether local dumped data matches expectations, and whether Sailor training code can run with local binary data. Model code usually lives under `models/`; Norbert scheduling, training config, and Fountain graph definitions usually live under `norbert/`.

### General checks

1. Confirm current path is under `/workspace/<project>`, not bare `/workspace`.
2. Confirm `models/` and `norbert/` exist.
3. Confirm `forge localrun --help` works.
4. Confirm the detected framework is `Sail` and the Norbert `train_mode` is a Sailor-supported mode (`common`, `catchup_batch`, `catchup_stream`).
5. Confirm `.forge/localrun/training/localrun.yaml` exists after init.
6. Inspect the latest `<command>/<runid>/log/` and `<command>/<runid>/output/` directories.

### init failures

- Non-ForgeIDE or wrong framework: check ForgeIDE container detection and `/release/forge_ide_ci/localrun/common.py`.
- Unsupported train mode: inspect the selected Norbert stage; current Sailor localrun supports `common`, `catchup_batch`, and `catchup_stream`.
- Wrong Norbert config variable or stage name: inspect `norbert/main.py` and stage names in `job_config["stage_config"]`.
- Dependency install failure: inspect `training/init/<runid>/log/init.log` and `dependencies` in `localrun.yaml`.
- Python bootstrap failures: inspect which Python the command re-execed into and whether the configured Python has PyYAML / required packages.

### compile failures

- Import/module errors usually point to `models/` code or missing dependencies.
- Compile graph errors usually point to Sail graph declarations, model-meta generation, or TensorFlow/framework version mismatch.
- Invalid local output layout: ensure the compile output contains a `sail_output/<graph>/<model_name>/model_meta.spec` layout, or exactly one nested `*/sail_output/<graph>`.
- Remote build download failure with `--commit-id`: check whether optional download dependencies are installed in the same Python used by compile, then inspect TOS/model-meta download errors.
- If multiple model candidates exist under the graph output, make the build output or graph selection unambiguous before retrying.

### data-dump failures

- Data source unavailable or wrong date range: inspect Norbert / Fountain data-source config and permissions.
- FeatureStore selection problems: ensure compile succeeded and model meta can be read; pass `--model-meta-path` and `--build-graph` only when live help/source supports them.
- HDFS / staging / Hadoop config problems: inspect generated logs and environment values such as `HADOOP_CONF_DIR` and `PRIMUS_FRAMEWORK_STAGING_DIR`.
- Primus cache writer failures: inspect command logs and `training/data_dump/<runid>/output/summary.json`.
- Validate `output/preview/sample.jsonl` when present to detect garbled or missing fields early.

### run failures

- Missing build output: run `compile` first or pass explicit `--build-path`.
- Missing binary data: run `data-dump` first or pass explicit `--binary-data-path`.
- `fountain.dump` generation failure: inspect selected Norbert stage, data source config, `FORGE_MODEL_DIR`, and `FORGE_MODEL_NAME` inferred from compile output.
- Sailor dependency mismatch: inspect `dependencies.scm.sailor` in `localrun.yaml` and the actual BVC installation under `/opt/tiger/sailor_bin` or the configured install path.
- Gflag problems: check both `cmd.run.gflags` and CLI `--gflag` / raw gflags after `--`; final runtime gflags should reflect user overrides above Norbert/model defaults.
- Model runtime errors: inspect the Sailor toolbox run logs and the generated `sailor_localrun.yaml`; failures here usually point to model training logic, feature declarations, or runtime dependency mismatch.

### eval failures

- First check whether `IS_COMPLIANCE_MODE` is exactly `true`; do not infer compliance mode from site, cluster, or an RPC error message.
- In compliance mode, check the actual Sailor installation's `current_revision`, not just `localrun.yaml`. It must match `data/aml/sailor_bin_test@2.0.2.721`; rerun init if it does not.
- Inspect the generated eval/toolbox config or final process arguments and verify that all four required gflags reached the runtime. A YAML edit alone is insufficient evidence.
- Treat missing TTHeader, zstd codec, PS-client compliance, and Haven compliance settings as one configuration error; enabling only a subset is unsupported.
- After the compliance preflight passes, diagnose ordinary PS path, model name, network/permission, model-meta, and inference errors through eval logs. Do not mask them by changing the training `run` workflow.

## Response rules for agents

- Prefer `forge localrun ...` over raw `localrun ...` so forge remains the unified entrypoint.
- Keep localrun arguments in kebab-case exactly as the tool exposes them, for example `data-dump`, `--build-path`, `--binary-data-path`, `--gflag`.
- Before relying on any localrun subcommand, flag, or behavior, inspect `forge localrun -h`, `forge localrun <command> -h`, or `/release/forge_ide_ci/localrun/` source; templates are useful but not authoritative.
- Do not run `data-process` for Sailor unless live source has changed and explicitly supports it for the detected framework.
- Treat `eval` as a supported Sailor offline inference workflow, separate from the default training debug chain.
- For Sailor eval, branch on the exact `IS_COMPLIANCE_MODE=true` contract. Fail closed when a compliance container does not have the required SCM revision and all four eval gflags; do not silently fall back to standard RPC behavior.
- Keep compliance-only Sailor settings scoped to eval. Do not apply them to `run`, non-compliance containers, LGTF, or LagrangeTorch.
- Do not run broad destructive cleanup under `.forge/localrun`; old run directories are useful for diagnosis.
- When a command fails, quote the concrete log path and summarize the root cause from logs before editing code.
- If code is changed, final output must include changed file locations, what changed, and why, so the user can review whether to accept the fix.
