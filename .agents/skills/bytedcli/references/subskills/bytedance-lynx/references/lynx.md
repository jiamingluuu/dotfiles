# Lynx execution guide

Use the current agent-lynx instructions and command surface for Lynx development, debugging, performance traces, runtime recordings, heap snapshots, live memory, Sandbox devices, and LynxExample tasks.

## Select task instructions

For every non-LynxExample task:

```bash
bytedcli lynx skills list
bytedcli lynx skills get <name>
```

Agent Lynx 0.14.13 publishes these Skills:

| Task                                                    | Load                             |
| ------------------------------------------------------- | -------------------------------- |
| Live DevTool/CDP/app/session debugging                  | `lynx-devtool`                   |
| Current process-wide Lynx memory status                 | `lynx-global-memory-status`      |
| JS heap snapshot capture, comparison, or leak analysis  | `lynx-js-heap-snapshot-analysis` |
| Recorder capture or recording diagnosis                 | `lynx-recorder`                  |
| Recorder/TestBench fixture inspection or editing        | `lynx-recorder-fixture`          |
| Sandbox device, ADB/BOE, preview, recording, or cleanup | `lynx-sandbox`                   |
| Existing performance trace analysis or comparison       | `lynx-trace-analysis`            |
| Performance trace recording, download, or validation    | `lynx-trace-record`              |

Run `skills get <name>` for the selected live instructions; bytedcli does not embed their contents. Live `skills list` descriptions take priority over this summary, and only names returned by the current list should be requested. Load each Skill at most once unless the available set changes, and combine Skills only when the task crosses capabilities.
Treat `agent-lynx ...` commands in returned instructions as `bytedcli lynx ...` and ignore their direct `npx @byted/agent-lynx` fallback; bytedcli manages the pinned runtime.

## Inspect current commands

```bash
# Complete Lynx command tree
bytedcli lynx --help

# LynxExample commands and parameters
bytedcli lynx example --help
```

Use the selected Skill and live help for current commands, parameters, defaults, and troubleshooting.
