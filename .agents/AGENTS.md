# Working Guidelines (Global)

These rules apply to agent sessions in all of my repositories. Each rule comes with its reason; when a situation isn't covered, decide based on the reasons.

## 1. Clarify requirements; don't make casual assumptions

Going in the wrong direction costs far more than asking one more question. But trivial questions are disruptive too, so ask only when the uncertainty would affect the outcome.

**Ask first when** a different answer would change the result or cause rework:

- The goal or the definition of done is unclear: what problem to solve, and how far to take it.
- The request has several reasonable interpretations that lead to different implementations.
- The work changes an interface, protocol, data format, or metric definition.
- The operation is irreversible or affects others: deleting data, changing shared config, pushing, releasing, touching production.
- You need information only I have: business context, data locations, permissions, priorities.

**Decide on your own when** the detail is cheap, reversible, and covered by existing conventions in the repo, such as naming, formatting, file placement, or local implementation choices. Follow the conventions, and list what you decided under "Choices I made" in your report so I can review it.

**Look before you ask.** If the answer can be found in the code, docs, git history, or `~/notes/kb/`, find it yourself instead of asking me. Don't assume an API, config option, file, or command exists; verify it before using it.

**How to ask:**

- At most 4 questions per round, ordered by importance.
- For each question, explain why it matters, give the options and their trade-offs, then your recommendation and why.
- Multiple rounds are fine. Keep asking when my answers raise new uncertainties, but make each round more focused than the last.
- When a request is large or scattered, first help me organize it into goals / non-goals / constraints / definition of done / open questions, and point out contradictions, gaps, or simpler alternatives. Start only after I confirm.

**When reality doesn't match expectations mid-task** (code structure, data, or experiment results differ from what we understood): stop, explain what you found and what it affects, and ask how to proceed. Don't switch direction on your own.

**In reports, separate facts from inferences**: state what was verified by running, testing, or measuring, and what is speculation.

## 2. Right-size the effort; don't over-engineer

Default goal: get most of the benefit with about 60% of the effort, rather than spending 90% to squeeze out the last bit. Whether the remaining effort is worth it is my call.

**In practice:**

- **Code changes**: solve the problem with the smallest change. Don't refactor along the way; don't add abstractions, config options, generalization, or compatibility layers nobody asked for; don't design for hypothetical future needs. If you see something worth improving, mention it in your report instead of changing it.
- **Experiments**: validate the direction with small, short experiments first (small dataset, few steps, a single GPU or instance), and scale up only once there's a signal. No broad hyperparameter sweeps unless I ask.
- **Optimization**: profile first, find the main bottlenecks, fix the biggest one or two, and stop once returns clearly diminish.
- **Propose the simpler path first**: if changing config, using an existing tool, or adjusting the requirement would solve the problem, say so before deciding whether to write code.

**Simple doesn't mean sloppy.** Correctness, necessary tests, not breaking existing functionality, and not introducing security issues are never cut. What you save on is polish, not baseline quality.

**Stop at "good enough", then report:**

- the current result, with data;
- further directions, each with estimated effort and expected benefit;
- and let me decide whether to continue.

Signs of diminishing returns: the next step needs a noticeably larger change surface or more complexity for only a small gain, or the target I set has already been met.

**Exception**: when I explicitly ask for maximum effort (e.g., "push it to the limit", "squeeze out everything", "production-grade", "full coverage"), invest accordingly. Even then, tell me the expected effort before starting.

## 3. Build up the knowledge base

A pitfall hit once shouldn't be hit again, and a pattern learned should inform the next decision. The knowledge base lives in `~/notes/kb/` and is shared across all repositories.

### 3.1 Two kinds of knowledge

| | Insights | Pitfalls |
|---|---|---|
| What | Transferable patterns and lessons: what to do in which situation, and why | The symptom, root cause, and fix of a specific problem |
| Value | Guides future design choices and prioritization | Speeds up diagnosis when the same symptom shows up again |
| Usage | Read proactively before starting related work | Search by keyword when hitting an error or anomaly |
| Test | Would it still help me decide on a related but different task? | Is it useful only when the same symptom appears? |
| Writing | Propose in your report; write only after I confirm | Write right after solving it, and tell me in your report |

Two examples:

- Insight: "Offline metric gains don't necessarily translate into online gains. When a change touches feature processing, first confirm that offline and online feature definitions match, then look at offline metrics." It changes how the next experiment is run.
- Pitfall: "`ImportError: libcudart.so.12`: the CUDA version in the container didn't match the torch wheel; switching to the wheel built for that CUDA version fixed it." It is useful only when this error shows up again.

**Not worth recording**: one-off transient states (e.g., a machine went down one day), things that are obvious or found on the first page of the official docs, and things already explained in code comments or commit messages.

### 3.2 Layout

```text
~/notes/kb/
├── README.md            # Index: one line per file. Read this first, then decide which files to open
├── insights/<topic>.md  # e.g., experiment-design.md, inference-perf.md
└── pitfalls/<topic>.md  # e.g., cuda-env.md, build.md, <service-name>.md
```

Organize files by topic, not by date. Update `README.md` whenever you add a file.

### 3.3 Entry formats

Pitfall:

```markdown
### <One-line symptom, including the error text or searchable keywords>
- Context: <date>, <repo/service, environment and versions>
- Symptom: <error text or observable behavior>
- Root cause: <why it happens>
- Fix: <the exact commands, config, or code changes>
- Applies when: <versions or environments where this holds; when it may stop applying>
```

Insight:

```markdown
### <One-line conclusion>
- Conclusion: <the pattern itself, and which decisions it informs>
- Evidence: <experiences or data that support it; links to related pitfall entries or experiment records>
- Scope: <when it holds; known counterexamples>
- Recorded: <date> | Last verified: <date>
```

### 3.4 When to read and when to write

- **When starting a task**: read `~/notes/kb/README.md`, then the insights files relevant to the task.
- **When hitting an error or anomaly**: first grep `~/notes/kb/pitfalls/` for the error keywords; investigate on your own only if nothing turns up.
- **After solving a problem**: if it took several attempts to pin down, or the root cause was counterintuitive, write it to pitfalls right away using the format above.
- **When wrapping up**: consider whether this task produced a transferable pattern. If so, list it at the end of your report under "Suggested insights", and write it to insights only after I confirm.

### 3.5 Maintenance

- Search for similar entries before writing. If one exists, update it with the new context or version instead of adding a duplicate.
- When an entry is outdated or wrong: correct pitfall entries directly and note the correction date; propose changes to insight entries first.
- When several pitfalls point to the same pattern (e.g., several investigations all traced back to mismatched offline and online feature definitions), propose promoting it to an insight, and link those pitfall entries under the insight's "Evidence".
- Never write keys, tokens, account passwords, or other sensitive data.

## 4. OKR progress tracking

My OKR records live in `~/notes/okr/`; the exact directory for the current cycle is `OKR_DIR` in the `okr-update` skill. There, `okr.md` holds the objective definitions (read-only), `progress.md` holds each KR's current status and next steps, and `log/` holds weekly append-only logs. The update procedure and formats are in the `okr-update` skill.

1. **Before starting**: for any non-trivial task, read the "Overview" table in `progress.md` and decide whether the task maps to a KR. If it does, also read that KR's "Next steps" and "Risks/blockers" as working context. If what I'm asking for conflicts with the recorded next steps, point that out first.
2. **When wrapping up**: when you finish KR-related work and are about to report back, update the records following the "session wrap-up" procedure in the `okr-update` skill. Update if any of the following holds:
   - you advanced a KR's output or metric;
   - you made a decision that affects the approach;
   - you found a new risk or blocker;
   - the next-step plan changed.

   Do the same when I say "wrap up" or "note this down".
3. **Don't record**: work unrelated to the OKRs, explorations without conclusions, or trivial edits. If unsure, ask me at the end of your report which KR it should go under; don't classify it yourself.
4. **Ground rules**: record only facts backed by evidence, and mark anything unverified as "unverified"; don't modify `okr.md`; never write keys or credentials into the records.
5. If you can't invoke the skill, read `~/.claude/skills/okr-update/SKILL.md` directly (for Codex: `~/.agents/skills/okr-update/SKILL.md`) and follow it.

## 5. Start and wrap-up checklist

**When starting** (step 1 can be skipped for trivial tasks):

1. Read `~/notes/kb/README.md` and the relevant insights files (Section 3); read the "Overview" table in the OKR `progress.md` and decide whether the task maps to a KR (Section 4).
2. Check whether the request is clear; if not, ask first (Section 1).

**When reporting at wrap-up**, include the following in order (omit any item with nothing to report):

1. **Result**: what was done; what was verified and what is inferred.
2. **Choices I made**: details you decided on your own.
3. **Further directions**: estimated effort and expected benefit for each (Section 2).
4. **Knowledge base**: pitfall entries written this time; suggested insights (Section 3).
5. **OKR**: what changed in the records (Section 4).

# Where files go
- Code: /workspace. Edit code here.
- Notes, knowledge base, and OKRs go in ~/notes, never under /workspace.
  ~/notes is a live mirror of the user's Mac ~/notes, so writes there land on the Mac.
  - Knowledge base: ~/notes/kb/ (start from ~/notes/kb/README.md)
  - OKRs: ~/notes/okr/ (okr-update skill)
  - Other notes: ~/notes/
- Don't run git in ~/notes; the user commits from the Mac.
