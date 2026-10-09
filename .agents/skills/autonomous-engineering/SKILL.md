---
name: autonomous-engineering
description: Use for difficult implementation, debugging, integration, migration, or refactoring tasks that require autonomous investigation and verification.
---

# Autonomous Engineering Workflow

The parent agent is the orchestrator.

## Phase 1: Establish the problem

Determine:
- requested outcome;
- existing behavior;
- constraints;
- definition of done.

Do not start editing before understanding the relevant execution path.

## Phase 2: Investigation

Delegate uncertain technical questions to the investigator.

For independent questions, use multiple investigators in parallel.

Require evidence rather than unsupported conclusions.

When appropriate:
- reproduce;
- inspect logs;
- trace code;
- search external documentation;
- state hypotheses;
- run falsifying experiments.

## Phase 3: Architecture

If the change crosses architectural boundaries, delegate to the architect.

Require an impact map before implementation.

Create or update an ExecPlan following PLANS.md.

## Phase 4: Implementation

Delegate source-code modifications to exactly one implementer.

Pass it:
- task contract;
- investigation conclusions;
- architecture decision;
- ExecPlan;
- relevant constraints.

Do not send raw exploratory noise when a concise evidence summary is sufficient.

## Phase 5: Verification

After implementation, spawn verifier and reviewer independently.

Run them in parallel when practical.

The verifier tests observable correctness.
The reviewer evaluates the design and diff.

## Phase 6: Repair

If either returns substantive failures:
- consolidate findings;
- send concrete evidence to the implementer;
- make a focused correction;
- rerun verification.

Do not blindly revert or retry.

If a hypothesis was falsified, update the diagnosis before making another patch.

## Phase 7: Completion

Finish only when:
- requested behavior is demonstrated;
- verification passes;
- no high-severity review finding remains;
- obsolete code is removed or explicitly justified;
- the working tree is coherent.

Return a concise evidence-based report.

