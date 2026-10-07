---
name: bytedance-ida
description: "Use bytedcli iDA for professional data analysis, metric attribution, anomaly analysis, natural-language data queries, iDA Deep Research, sessions, agents, skills, or MCP servers. Also use it to download the CSV, script, or chart files a Deep Research run produced. Trigger when tasks mention IDA, iDA, Deep Research, Aeolus/Tea/Libra/Hive/Dorado analysis, iDA agent, iDA skill market, or iDA MCP."
---

# bytedcli iDA

## How to call bytedcli

Recommended: install once, then call `bytedcli` directly.

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback only when global install is unavailable.
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

Use `bytedcli --json ida ...` for machine-readable output. The global `--json` flag must appear before `ida`.

## When to use

- Ask iDA to analyze metrics, explain changes, trace attribution, investigate anomalies, or produce a data-analysis report.
- Use natural language to work across internal data platforms such as Aeolus, Tea, Libra, Hive, and Dorado.
- Ask iDA Deep Research and wait for the final answer.
- Submit a Deep Research run without waiting, then collect the answer later — for runs that outlast a tool timeout.
- Download the files a Deep Research run produced — generated CSVs, scripts, charts.
- Continue an existing Deep Research session.
- List or inspect iDA agents, Deep Research models, sessions, messages, MCP servers, and iDA skill market entries.
- Use raw iDA chatCompletion, session, message, or feedback APIs when the user explicitly needs the web-style iDA agent flow.

## Do not use

- Do not use for AIME sessions or models; use `aime`.
- Do not use for Tika AI knowledge platform conversations; use `tika`.
- Do not use for BitsAI engineering asset Q&A; use `bitsai`.
- Do not use raw iDA chat commands when Deep Research is enough.

## Prerequisites

- Run `bytedcli auth login` if the current bytedcli session is missing or expired.
- Default region is `cn`. Use `bytedcli ida --region sg ...` for the SG iDA site.
- Need current command details or newly added options: run `bytedcli ida --help` or `bytedcli ida <resource> --help`.

## Data Analysis Strengths

iDA is strongest when the task is data analysis, not generic chat. It can connect ByteDance data products, Lark knowledge, internal knowledge bases, Meego views, group messages, and engineering context in one analysis path.

Use iDA first when the answer depends on professional data-platform context:

- Permission-aware analysis: iDA can inherit the user's data permissions, including row and column controls in products such as Aeolus.
- Higher data accuracy and attribution quality: iDA is backed by official data-platform capabilities and understands metric queries, attribution, and anomaly-analysis workflows.
- Broader data range: besides query results, iDA can reason over metadata, asset lists, lineage, dashboards, and dependency relationships.
- Better explanations: ask not only "what changed", but also what the metric means, why it changed, which assets are related, and how dependencies connect.
- Data-analysis outputs: iDA can create natural-language data queries, attribution analysis, documents, web reports, and dynamic charts linked with Aeolus-native dashboard components.

## Deep Research Workflow

Start with Deep Research for data analysis, attribution, anomaly investigation, synthesis, comparison, and other investigation tasks.

```bash
bytedcli ida model list
bytedcli ida agent get
bytedcli ida deep-research create --content "Analyze why the demo conversion metric changed this week"
bytedcli ida deep-research create --session-id <session_id> --content "Continue with attribution and related dashboard assets"
bytedcli --json ida deep-research create --content "Create a data-analysis report for the sample metric anomaly" --no-web-search
```

Deep Research creates a session automatically when `--session-id` is omitted. It waits for the stream to finish and returns a compact final answer.

### Long runs: submit now, collect later

A Deep Research run takes minutes, which outlasts most agent tool timeouts. `--no-wait` returns as soon as iDA accepts the task; the run continues server-side.

```bash
bytedcli ida deep-research create --agent-id <agent_id> --content "<question>" --no-wait
# → session_id and task_id, plus the exact command to collect the answer

bytedcli ida deep-research get --session-id <session_id> --task-id <task_id>
```

`get` reads exactly one turn and takes both ids; there is no default turn. The `task_id` that `create --no-wait` printed is the one to pass, and `terminal_status` in the output is that turn's own.

**One submission, more than one task.** Measured on live sessions: every `create` that ran past about a minute — with or without `--no-wait` — ended up with a second task in the session, started by iDA some 40–60 seconds after the first, and both ran to completion. The id `create` returns is real and finishes; it is just not the only one. So:

- a task's own `terminal_status` is the only thing that says whether _that_ run ended;
- before submitting the same question again, list the session — a second submission on top of a run still going means a third and fourth task;
- a prompt with side effects (writing a document, building a dashboard) must tolerate being executed twice.

**Deciding whether to poll again.** Poll on this turn's own output:

1. **`answer` or `artifacts` is non-empty** → that is this turn's own output. Stop. This is the same test `deep-research create` stops on.
2. **`terminal_status` is one of** `success` `succeeded` `completed` `failed` `failure` `error` `cancelled` `canceled` `killed` `timeout` (compare case-insensitively) → the turn ended. Stop.
3. **Anything else, including `terminal_status: null`** → poll again.

Treat an unrecognized `terminal_status` as still running, never as finished: guessing the other way ends the wait mid-write and reports an empty run.

**An empty read does not mean there is no task.** iDA rewrites its messages while a run progresses, and for part of that window the turn comes back with no answer, no artifacts and `terminal_status: null`. This is normal mid-run and is exactly when to keep polling. It is also why an unreadable turn is never reported as an error — a mistyped `--task-id` and a turn between rewrites are indistinguishable, so `get` returns the same empty shape for both and echoes the id you asked for. If a wait runs past its budget while `terminal_status` is still null, that is not evidence the run failed — list the session before concluding anything.

**To see a session — every turn it holds and how far each has got — list it.** This is the session-scoped read; `get` has no session mode.

```bash
bytedcli ida deep-research list --session-id <session_id>
# → one row per turn: task_id, terminal_status, finished_at, step_count, artifact_count
#   plus latest_task_status, iDA's own status for the session as a whole
```

`latest_task_status` there is the session's, not any one turn's. Measured live, it reads `error` while both tasks of a submission are still running — it tracks iDA's own placeholder message, which times out — and `completed` once they finish. It is context beside the rows, never a verdict on a turn; the rows carry those.

Read the list before assuming a submitted turn was lost, and before waiting on one: a session can hold a turn you did not submit — the sibling task above, or one iDA spawns when a run stops to ask a question — and a turn that never finishes on its own looks, in `get`, exactly like one still running. The list will not tell you a turn is waiting for input; iDA exposes no such signal, and a turn stopped on a question reports `success` like any other. What it will tell you is that the turn exists, so you can read its answer and see the question. A turn still being written may be absent until iDA persists it; that is not evidence it was lost.

`session get` returns the whole payload — megabytes on a long session — and is for reading raw messages, not for finding out where a run is.

**Poll across turns, not inside one.** Submitting returns in seconds and the answer is minutes away, so a loop that waits out that gap holds your turn — and your host's interface — hostage for the whole run, which is the cost `--no-wait` exists to avoid.

Concretely, after submitting: do not call `sleep`, do not write a shell loop, and do not repeat `get` for the sole purpose of keeping the current turn open. Those are the three shapes this goes wrong in, and an agent has been observed doing all three while its host's interface stayed frozen.

Pick how to collect in this order:

1. Your host offers a background mechanism you are allowed to use → hand collection to it and carry on.
2. Collecting would need a host subagent, and spawning one needs authorization you do not have → do not spawn it.
3. Otherwise → report the `session_id` and `task_id`, **end the turn**, and read again when you are next invoked.

Wait in-band only when the user asked to watch the run, or when your host can genuinely move the wait off the turn.

**A run can stop and ask for access you cannot grant from here.** The remote agent reaches data platforms under its own connector identity, and a successful `bytedcli auth login` says nothing about whether that identity is bound. When a run answers with an authentication or binding URL, return the URL as given, keep the `session_id`, and continue in that same session once the user confirms — the pending work and its context live there. Do not start a new session, and do not route around it with other tools. Which connectors a given agent needs is that agent's own documentation to state.

On that basis the budget is ~30s between reads and ~30 minutes before giving up — a budget spread over turns, not the parameters of one loop. Running the budget out leaves two readings that the output cannot separate, a turn still being written and an id that was mistyped, so list the session rather than reporting either one.

You do not have to wait out the budget to catch a typo. After a few empty reads, run `ida deep-research list --session-id <session_id>` and check that the id you are polling appears among the turns. That is a lookup, not a stopping condition: finding the turn means keep waiting, and not finding it means the id is wrong — or that iDA has not persisted the turn yet.

**When the list is also empty.** `session get` runs the same parser, so `messages[].task_result` is missing there too. What it adds is the payload that parser could not normalize: `--json` keeps `messages[].deep_research_content` verbatim — raw iDA keys, so the turn id there is `taskId`, not `task_id`. Read it before concluding the run produced nothing: the answer is usually still inside, and it is also where you confirm the turn id you asked for exists. If `deep_research_content` is itself absent, that message really is empty.

If the raw payload holds an answer that `task_result` did not, that is the bug worth reporting — capture it with `bytedcli --debug ida deep-research get --session-id <session_id> --task-id <task_id>`, which reports what could not be read: the first few dropped entries in detail, then a count. A payload that is genuinely empty logs nothing, because nothing failed to parse.

**A turn that ended is not necessarily a turn that answered.** It can end by asking you to confirm an action, to approve a permission request, or to clarify the question — all of which still report a finished status. Read `answer` and decide whether to reply in the same session with `--session-id`. What a given agent asks for, and how to answer it, belongs to that agent's own documentation, not here.

Two more things before parsing:

- **`get` returns the answer, the turn's `terminal_status` and an artifact summary; `--full` adds the execution trace and the artifact contents.** The trace and the bodies run to six figures of tokens on a real investigation and the answer is a low single-digit percentage of it, so they are opt-in. `step_count` is reported either way, and is `null` when the turn could not be read at all.
- **`--no-wait` reports only `session_id`, `task_id` and `created_session`.** It omits `answer`, `artifacts`, `steps` and `terminal_status` — iDA has not produced them yet, and emitting empty ones would read as a finished, empty result. Only `get` returns those fields.
- **`--timeout-ms` does not apply to `--no-wait`**, which never waits.

### Collecting the files a run produced

A turn's deliverables — CSVs, generated scripts, charts — come back as artifacts. `get` summarizes them by default: identity, file names and sizes, a `table_count` and a `has_text` flag. Add `--full` to read the tables and text themselves; a file still has to be fetched.

```bash
bytedcli --json ida deep-research artifact list --session-id <session_id> --task-id <task_id>
bytedcli ida deep-research artifact download --session-id <session_id> --task-id <task_id> --artifact-id <artifact_id>
# without --task-id: every turn in the session — each row names its task_id
bytedcli --json ida deep-research artifact list --session-id <session_id>
```

Without `--task-id` both commands cover the whole session: `list` returns every turn's artifacts with a `task_id` on each, and `download` finds the artifact wherever it lives and reports the turn it came from. Sibling tasks of one submission produce same-named artifacts, so pick by `task_id`, not by name.

`download` writes to a private temp file and prints the path; pass `--output <path>` to choose one. An existing path is left alone unless you add `--force`.

An artifact whose `files` are empty carries only tables or text — read it with `get --full` rather than downloading it. `table_count` and `has_text` tell you it is there; they are not the content. An empty artifact list means the same thing an empty turn does: the run may still be mid-rewrite, so re-read before concluding it produced nothing.

The download is authenticated as you, so bytedcli only sends it to known iDA hosts and refuses to follow redirects. `IDA_ARTIFACT_URL_UNTRUSTED` means iDA served a file from a host this build does not know — report it rather than working around it.

Useful options:

- `--agent-id <id>`: use a specific Deep Research-capable agent when creating a session.
- `--model <name>`: model value from `ida model list`.
- `--no-search`, `--no-web-search`, `--lark-qa`, `--no-knowledge-qa`: control search sources.
- `--no-wait`: return as soon as iDA accepts the task, then collect with `ida deep-research get`.
- `--timeout-ms <milliseconds>`: increase when the answer takes longer than the default wait window.

## Session and Message Reads

Use these when the user asks to inspect, resume, audit, or fetch prior iDA context.

```bash
bytedcli ida session list
bytedcli ida session get --session-id <session_id>
bytedcli ida message list --session-id <session_id>
bytedcli ida session update --session-id <session_id> --name "Demo research"
```

`session get` is the Deep Research session detail path. `session info`, `session raw list`, and `message list` operate on raw iDA sessions.

## iDA Agent, Skill, and MCP Discovery

Use these for capability discovery before choosing a specific iDA agent, skill, or MCP server.

```bash
bytedcli ida user get
bytedcli ida agent get --agent-id <agent_id>
bytedcli ida skill scene list
bytedcli ida skill list --keyword "demo"
bytedcli ida skill get --skill-id <skill_id>
bytedcli ida mcp list --agent-id <agent_id> --with-tools
```

For skill detail, pass either `--skill-id <id>` or both `--source <source> --identifier <identifier>`.

## Raw iDA Chat Workflow

Use raw chat only when the user needs an existing web-style iDA agent/session flow, not a Deep Research answer.

```bash
bytedcli ida chat completion create --session-id <session_id> --query "Continue the analysis"
bytedcli ida chat completion close --session-id <session_id>
bytedcli ida chat repl execute --session-id <session_id>
bytedcli ida message create --session-id <session_id> --content "Append this note"
bytedcli ida message feedback create --session-id <session_id> --message-id <message_id> --thumb up
```

`message create` appends a non-streaming message and does not ask the model for a response. Use `chat completion create` when a model response is needed.

## Output Rules

- Prefer text output for final user-facing answers.
- Add `--json` when another agent or script will parse the result.
- Do not expose Titan tokens, cookies, internal request headers, or raw SSE implementation details in the final user answer.

## Deep Research Result Shape

A finished run carries four things: the text conclusion, the deliverables, the execution trace and the task's terminal state.

- `answer`: the text conclusion.
- `artifacts`: deliverables. Each carries `files` (with a `uri` to fetch) and, when read in full, `tables` (`columns` / `rows`) and `text`, so a generated CSV can be read as structured data without downloading it. `deep-research get` summarizes these by default and needs `--full` for the contents; `create`, `session get` and `artifact list` return them whole.
- `steps`: the execution trace — `type`, `tool_name`, any executed `code`, `finished_at` (ISO) and, on a step another step spawned, `parent_step_id`. Use it to judge whether an answer came from real queries or from the model alone, and to see where a run spent its time: iDA reports when each step finished but never when it started, so durations come from the gaps between `finished_at` values — a parent step finishes after the steps under it, so group by `parent_step_id` before diffing. `deep-research get` reports `step_count` by default and returns the trace itself only with `--full`.
- `terminal_status`: terminal state of that task, for example `success`.

**The two commands expose them at different places.** `deep-research create` reports one run, so the fields sit at the top level alongside `session_id`, `task_id` and `created_session`:

```bash
bytedcli --json ida deep-research create --content "..." | jq '.data.answer, .data.artifacts'
```

`session get` reports a whole session, so each turn keeps its own copy under `messages[].task_result`, next to that message's `text`:

```bash
bytedcli --json ida session get --session-id <session_id> \
  | jq '.data.messages[] | select(.task_result) | .task_result.answer'
```

`task_result` additionally carries `task_id`, `finished_at` and `schema_version`. It is absent on messages that hold no run — a user question, or the placeholder created with the session.

Two differences worth knowing before parsing:

- **A missing answer is a missing key, not an empty string.** `deep-research create` always reports `answer` (`""` when the run produced only artifacts), but inside `task_result` the key is simply absent. Read it as optional.
- **Only `deep-research create` prints an artifact summary in text mode.** `session get` renders a message table whose `Text` column holds the answer; to see deliverables from a session read, use `--json`.

A run that delivers only artifacts and no prose is still a success.

## References

- `../../invocation.md`
