---
name: bytedance-lynx
description: >-
  Comprehensive Lynx Skill for app development, debugging, performance, recording, memory, fixtures, devices, and LynxExample workflows. Use for Lynx DevTool/CDP/App/connector debugging; DOM/CSS/ReactLynx inspection or mutation; runtime/console/network logs, screenshots, JSB, reload/open; performance trace capture/export/validation; Recorder interaction capture and replay diagnosis; JS heap snapshot capture/comparison and leak analysis; global Lynx memory status; Recorder/TestBench fixture inspection or editing; Sandbox Android lease/release, ADB, recording, preview, or debug; and LynxExample artifact metadata, downloads, or Android/iOS app start and page open. Routes tasks to the live agent-lynx Skills and command surface without copying upstream Skill contents.
---

# Lynx

Use this Skill for end-to-end Lynx development and diagnosis: inspect or control apps with DevTool/CDP, acquire Sandbox devices, capture traces or runtime recordings, inspect heap or live memory evidence, edit Recorder fixtures, and operate LynxExample.

## How Lynx work is organized

- This Skill understands the task, selects the relevant Lynx capability, and organizes the steps.
- The agent-lynx command surface operates live clients, sessions, devices, and generated artifacts.
- Published task instructions come from Agent Lynx Skills loaded on demand; this routing Skill does not copy their contents.
- A live device/session is not an artifact; performance traces, Sandbox video evidence, Recorder replay JSON, and heap snapshots have different purposes.

## Standard execution method

Before any non-LynxExample task, list the available Lynx Skills and load the best match:

```bash
bytedcli lynx skills list
bytedcli lynx skills get <name>
```

These commands invoke `agent-lynx skills list` and `agent-lynx skills get <name>` through bytedcli.
In returned instructions, execute `agent-lynx ...` examples as `bytedcli lynx ...`; do not use their direct `npx @byted/agent-lynx` fallback because bytedcli owns this runtime.

1. Run `skills list` and read the current descriptions.
2. Select the single most specific published Skill from the map below.
3. Run `skills get <name>` and follow the returned instructions.
4. Load a second Skill only when the task crosses capabilities; stop when the task goal is met.
5. Track loaded Skill names and load each only once unless the available set changed.

| User intent                                                                                        | Load                             |
| -------------------------------------------------------------------------------------------------- | -------------------------------- |
| Live app/client/session debugging with DevTool, CDP, DOM/CSS, logs, screenshots, JSB, or ReactLynx | `lynx-devtool`                   |
| Current process-wide Lynx memory status and high-memory triage                                     | `lynx-global-memory-status`      |
| Capture, inspect, or compare JS heap snapshots and diagnose retainers or leaks                     | `lynx-js-heap-snapshot-analysis` |
| Record page interactions into replay JSON or diagnose a recording                                  | `lynx-recorder`                  |
| Inspect, decode, edit, encode, or upload a Recorder/TestBench fixture                              | `lynx-recorder-fixture`          |
| Lease/release Sandbox Android devices, use ADB/BOE, preview, or record Sandbox evidence            | `lynx-sandbox`                   |
| Analyze an existing Lynx performance trace or compare trace regressions                            | `lynx-trace-analysis`            |
| Record, download, and validate a Lynx performance trace                                            | `lynx-trace-record`              |

Agent Lynx 0.14.13 publishes these eight Skills. Live `skills list` descriptions take priority over this summary; request only names returned by the current list.

## Common workflow decisions

- Load the most specific Skill for the requested artifact or live workflow. Add another only when the task crosses capabilities; for example, acquire/connect with `lynx-sandbox`, then debug with `lynx-devtool`.
- Use `lynx-trace-record` for trace collection, `lynx-trace-analysis` for diagnosis of an existing trace, `lynx-global-memory-status` for live aggregate memory, and `lynx-js-heap-snapshot-analysis` for snapshot-based leak diagnosis.
- Use `lynx-recorder` to create or diagnose a recording and `lynx-recorder-fixture` when the fixture itself must be inspected or edited.
- Sandbox recording is synchronized video + DevTool evidence; Recorder output is runtime replay JSON. Do not confuse them.

## Current command surface

Do not guess agent-lynx subcommands or flags. Inspect the current command tree:

```bash
bytedcli lynx --help
```

## LynxExample

LynxExample workflows are documented directly in this Skill; do not create or suggest a separate LynxExample Skill.

| Task                      | Command                                                                      |
| ------------------------- | ---------------------------------------------------------------------------- |
| Resolve artifact metadata | `bytedcli lynx example get`                                                  |
| Download an artifact      | `bytedcli lynx example download`                                             |
| Start/open Android app    | `bytedcli lynx example android start` / `bytedcli lynx example android open` |
| Start/open iOS app        | `bytedcli lynx example ios start` / `bytedcli lynx example ios open`         |

Use group or leaf help for current parameters:

```bash
bytedcli lynx example --help
bytedcli lynx example <group> <action> --help
```

See `references/lynx.md` for the concise execution guide.
