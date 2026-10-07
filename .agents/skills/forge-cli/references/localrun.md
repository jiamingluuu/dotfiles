# localrun.md - route ForgeIDE localrun requests

Use this reference first for `forge localrun` / `localrun` requests. Localrun is a local debug/run workflow; do not confuse it with `forge code compile create --compile-mode local`, which submits a real Forge local compile.

## Contents

- [Routing workflow](#routing-workflow)
- [Tool model and discovery-first rule](#tool-model-and-discovery-first-rule)
- [Workspace layout](#workspace-layout)

## Routing workflow

Route in this order: **localrun intent -> framework -> capability**. Choose exactly one framework reference before interpreting framework-specific flags or procedures. Use existing localrun evidence first, and let the installed `localrun` entrypoint decide the framework only when the user is asking to execute or initialize the localrun workflow.

Capability terms are not framework evidence. `checkpoint`, `dense-checkpoint-path`, weight loading/replay, online PS, `ps-zk-path`, `nsys`, TensorFlow Profiler, timeline/trace, memory snapshot, and graph-hook dumps can appear in requests for more than one framework or may be unsupported by the selected framework. Never use one of these terms alone to route directly to LGTF. A request such as "Torch localrun 加载 checkpoint" must route to LagrangeTorch first; a request that only says "localrun 加载 checkpoint" remains framework-unknown until project evidence identifies it.

Before running a mutating localrun command, classify the user's intent:

- Diagnostic intent: the user asks to diagnose an error, inspect logs, explain an existing result, find artifacts, or understand why a previous localrun command failed.
- Execution intent: the user asks to initialize, repair/setup the environment, generate localrun config, or run one or more localrun stages.

For diagnostic intent, start with read-only checks only. Inspect existing `.forge/localrun/training/localrun.yaml`, existing `.forge/localrun/training/<command>/<runid>/{log,output}` directories, summary files, live help (`/usr/local/bin/localrun -h`, `forge localrun -h`, and command-specific `-h`), and installed source under `/release/forge_ide_ci/localrun/` when needed. Do not run `forge localrun init` as a generic discovery step during diagnosis, because it writes `localrun.yaml`, creates directories, and can install dependencies. Run `init` during diagnosis only if the user explicitly asks to initialize, regenerate config, or repair/bootstrap the environment.

In a localrun context, when the user says `线上 commit id` / `按 commit 下载`, treat that specific intent as framework-specific localrun compile/download behavior, not as a request to check out source code with Git. Identify the framework first from explicit user wording or existing config/init evidence before mapping it to a command:

- LagrangeTorch / lgtorch: after checking `forge localrun compile -h`, use the observed `forge localrun compile --commit-id <id>` form when supported.
- Sailor: after checking `forge localrun compile -h`, use the observed `forge localrun compile --commit-id <id>` form when supported.
- LGTF / LagrangeTF: do not route non-empty commit ids to `compile --commit-id`. The installed LGTF implementation rejects non-empty `commit_id`; tell the user LGTF localrun supports coordinator-aligned local compile, then use the LGTF compile flow from [localrun_lgtf.md](localrun_lgtf.md) if they want to execute it.
- Unknown framework: do not guess. For diagnostic intent, continue read-only discovery from existing files/logs/help. For execution intent, run `init` only when the user has asked to initialize/bootstrap or proceed with localrun setup.

Framework routing workflow:

1. If the user explicitly names a framework (`LagrangeTorch` / `lgtorch` / `Torch localrun`, `LGTF` / `LagrangeTF`, `Sailor`) or asks for that framework's documentation, select that framework reference. For execution, if existing config clearly contradicts the requested framework, surface the mismatch before running instead of mixing their commands.
2. Otherwise, inspect existing `.forge/localrun/training/localrun.yaml`, the latest init output/log if it exists, command output summaries, and live help to infer the framework without modifying the workspace.
3. If the user has execution intent and no existing evidence identifies the framework, run `forge localrun init` first, or inspect the latest init result if it already exists. `init` is the framework discovery and bootstrap point; it selects the template and writes `.forge/localrun/training/localrun.yaml`.
4. Read the existing or newly generated init console output and latest `.forge/localrun/training/init/<runid>/log/init.log` when available. Use the detected framework / selected template / generated yaml shape reported there.
5. Then load exactly one detailed reference:

   | Framework | Sufficient evidence | Reference |
   |---|---|---|
   | LagrangeTorch | Explicit `LagrangeTorch` / `lgtorch` / `Torch localrun`, or dispatcher/init selects the LagrangeTorch template/framework | [localrun_lgtorch.md](localrun_lgtorch.md) |
   | LGTF | Explicit `LGTF` / `LagrangeTF`, or Sail framework plus LGTF template/config evidence such as `train_mode` `lgtf`; for `base_gpu`, also require the Sail/LGTF template or dependencies such as `producer` plus `runner_local_run` | [localrun_lgtf.md](localrun_lgtf.md) |
   | Sailor | Explicit `Sailor`, or Sail framework plus Sailor template/config evidence such as `train_mode` `common`, `catchup_batch`, or `catchup_stream` and the Sailor command shape | [localrun_sailor.md](localrun_sailor.md) |

Do not use `cmd.data-process` alone to distinguish LGTF from LagrangeTorch; both can expose that stage. Do not use generic `TensorFlow`, `Torch`, `base_gpu`, checkpoint, PS, or profiling wording without the localrun/framework context required above.

If `init` fails before framework/template selection, diagnose the init failure from live help/source and logs before choosing a framework reference. Useful entry points are `/usr/local/bin/localrun -h`, `forge localrun -h`, and `/release/forge_ide_ci/localrun/localrun`.

After framework routing, load only the selected detailed reference unless the user asks for a cross-framework comparison. Inside that reference, select the framework's ordinary-run, weight-loading/replay, eval, or profiling guidance. If that reference does not document the requested capability, inspect the selected framework's live help and installed source and report the actual support boundary; do not borrow flags or behavior from another framework.

## Tool model and discovery-first rule

The complete tool is the ForgeIDE `localrun` CLI, normally available on `PATH` and commonly installed at `/usr/local/bin/localrun`. `forge localrun` is a transparent proxy: `forge localrun <args>` forwards `<args>` verbatim to `localrun <args>` and passes stdout/stderr/exit code straight back. forge adds no localrun business logic of its own; `localrun` owns all subcommands, flags, help text, framework detection, and exit semantics.

Do not add Forge runtime flags such as `--site` or `--network` to `forge localrun` commands. localrun is local-only and does not understand those flags. If a user-provided command contains them, forge strips those flags before invoking the localrun binary.

Consequence for agents: discover the current command surface before relying on a subcommand or flag. Do not treat framework references as a permanent schema. Run help from inside the ForgeIDE project/container and trust live help / installed source if it differs from this reference:

```bash
forge version
/usr/local/bin/localrun -h
localrun -h                 # or: forge localrun -h
localrun <cmd> -h           # or: forge localrun <cmd> -h
```

If installation is in doubt, check `/usr/local/bin/localrun -h` before the `PATH` entrypoint. Older or adjacent tooling may expose framework-specific commands such as `lg_torch`; use them only if the environment's help/source confirms they are the intended localrun entrypoint.

### Tooling and installation checks

Correct localrun execution requires both dependencies to be available: the ForgeIDE `localrun` tool and `forge-cli` itself. Check and repair them in this order.

Check the fixed localrun path first, then the `PATH` entrypoint, and only then use the `forge localrun` proxy:

```bash
/usr/local/bin/localrun -h
localrun -h
forge localrun -h
```

If `/usr/local/bin/localrun` is missing or stale in a ForgeIDE container, install or update the ForgeIDE CI package to the version requested by the user or environment owner, then run its installer:

```bash
bvc clone toutiao/reckon/forge_ide_ci /release/forge_ide_ci/ --version <version>
/release/forge_ide_ci/localrun/install_localrun.sh
```

If this is the first localrun in the current ForgeIDE environment and `/release/forge_ide_ci` already exists, update that checkout before running localrun:

```bash
cd /release/forge_ide_ci
bvc pull
```

The `/release/forge_ide_ci/` clone is also the place to inspect source and templates when diagnosing command behavior. After installation, re-run `/usr/local/bin/localrun -h` and `forge localrun -h` before continuing.

Check `forge-cli` through the public `forge` command:

```bash
forge version
```

If `forge` is missing or stale, clone `forge-cli` under `/workspace` and install / update it using the repo's normal build or install flow:

```bash
git clone git@code.byted.org:reckon/forge-cli.git /workspace/forge-cli
cd /workspace/forge-cli
# install or update forge-cli using the repo's normal install / build flow
```

Do not diagnose localrun command behavior until these two entrypoints (`/usr/local/bin/localrun` and `forge`) are both available, unless the user's task is specifically to repair installation.

Useful installed source entry points:

- `/release/forge_ide_ci/localrun/localrun` - command dispatcher and framework routing.
- `/release/forge_ide_ci/localrun/install_localrun.sh` - localrun installer.
- `/release/forge_ide_ci/localrun/` - framework command implementations, templates, and shared helpers. Framework-specific references list the most relevant files for each chain.
- `/release/forge_ide_ci/localrun/localrun_torch_template.yaml`, `/release/forge_ide_ci/localrun/localrun_sailor_template.yaml`, and framework-local template paths in the installed version - default config templates. Templates are useful, but live help and installed source are authoritative.

Useful AML repositories for deeper diagnosis:

| Area | Repo |
|---|---|
| AML components / Norbert scheduling / Sail API / Sailor implementation / LGTF implementation | `https://code.byted.org/lagrange/erdos` / `git@code.byted.org:lagrange/erdos.git` |
| Fountain framework | `https://code.byted.org/euclid/fountain` / `git@code.byted.org:euclid/fountain.git` |
| LagrangeTorch framework | `https://code.byted.org/lagrange/torch` / `git@code.byted.org:lagrange/torch.git` |
| Matrix / IDL proto definitions | `https://code.byted.org/idl/matrix/tree/master/proto?ref_type=heads` / `git@code.byted.org:idl/matrix.git` |
| Primus IO | `https://code.byted.org/inf/primus_io` / `git@code.byted.org:inf/primus_io.git` |

Useful data-format reference: Primus data dump has strict structures; when raw dump interpretation is needed, consult the internal doc `https://bytedance.larkoffice.com/docx/HpnJdg9bFooUWexq1zTcFIiXnWd` or inspect Matrix / Primus IO source directly.

## Workspace layout

Localrun assumes projects live under `/workspace/<project>`. A valid training project usually has:

```text
/workspace/<project>/
  models/                 # model code
  norbert/                # Norbert scheduling / training / Fountain config
  .forge/
    localrun/
      training/
        localrun.yaml     # global localrun config for training commands
        init/<runid>/{log,output}/
        compile/<runid>/{log,output}/
        data_dump/<runid>/{log,output}/
        data_process/<runid>/{log,output}/   # frameworks that expose data-process
        run/<runid>/{log,output}/
        eval/<runid>/                        # Sailor offline inference when supported
      serving/
      data/
```

`runid` is generated per command execution, usually in `yyyymmdd_hhmmss` format. Command-specific `summary.json` files can appear under command output directories, for example data-dump writes `training/data_dump/<runid>/output/summary.json`. Filesystem directory names use underscores (`data_dump`, `data_process`), while CLI commands use kebab-case (`data-dump`, `data-process`).
