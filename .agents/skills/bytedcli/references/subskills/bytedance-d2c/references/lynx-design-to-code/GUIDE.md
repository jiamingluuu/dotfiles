---
name: lynx-design-to-code
description: Lynx generation and repair guidance for a D2C stage that already has prepared design evidence. Use only when the caller explicitly requests region generation, region repair, global assembly, full-page generation, component routing, or deterministic validation and provides screenshots, Figma JSON / IR, region artifacts, or diff evidence. Do not use as the entrypoint for a Figma link or an end-to-end design-to-code request.
allowed-tools: Bash, Read, Grep
---
# lynx-design-to-code

Use this skill when a Lynx D2C agent needs component routing, Lynx syntax/layout guidance, or a concrete generation/repair workflow.

## Select A Mode

The caller should state one mode. If no mode is stated, use `full-page-generation`. If the caller is working from visual-segmentation/region artifacts, use `global-assembly`; do not use `full-page-generation` after a region pipeline.

- `region-generation`: generate one coarse semantic region from a region crop and region Figma JSON.
- `region-repair`: repair one generated coarse semantic region from target/render/diff evidence and region Figma JSON.
- `global-assembly`: revisit all region artifacts with full-page vision, merge or rewrite cross-region structures, and generate final page code.
- `full-page-generation`: generate a complete page directly from a full screenshot and Figma JSON/IR.

## Required Reads

Always read:

- `references/lynx-core.md`
- `references/workflows/common-phases.md`

Then read exactly one workflow:

- `references/workflows/region-generation.md`
- `references/workflows/region-repair.md`
- `references/workflows/global-assembly.md`
- `references/workflows/full-page-generation.md`

When selecting important components, also read:

- `references/component-overview.md`

When running `global-assembly`, read `<figma2codeDir>/run-artifacts/interaction-inventory.json`. When consuming `interactionInventory`, also read:

- `../interaction-recognition/references/interaction-target-mapping.md`

If `component-overview.md` points to a local component guide/API/example and that file is available, read it before writing code. If a referenced file is not bundled in this marketplace, continue from `references/lynx-core.md` and record the missing reference in the RFC instead of guessing unsupported APIs.

## Optional: Node Semantic Descriptions

Before generating, enrich the nodes you are about to build with human-curated semantic descriptions via the `get-figma-design-description` skill (it calls `getFigmaDescription` with `figmaPageUrl` + node ids and returns a short `Role / Intent / Data / Implementation / Unknowns` contract or structured JSON per node). Use any returned `figmaDescription` as extra semantic context that the design can't reveal (data binding, intended interaction, implementation constraints). If the result contains `semanticJson` or `rootConfig`, read those structured fields directly. Apply every recognized `rootConfig` root-level style, layout, or runtime value to the page's outermost root `<view>` style/class instead of putting it on an inner node or ignoring it; leave unknown fields as notes rather than inventing behavior. A `found: false` node simply has no description yet — proceed normally. Rank these descriptions per Source Priority below (above visual guessing, below screenshot and Figma structure).

## Source Priority

1. Screenshot or region crop: visual truth.
2. Figma JSON / region Figma JSON / IR: structure, text, assets, repeated data.
3. Node semantic descriptions from `get-figma-design-description`: human-curated intent and implementation constraints.
4. Region RFC/meta/code: source material for global assembly, not an untouchable final contract.
5. Component and platform references: implementation constraints.

## Output Discipline

Produce the requested artifacts at the caller-provided paths. Do not treat a chat code block as a substitute for required artifacts.

## Page Validation Command

When the selected mode is `global-assembly` and the caller provides an assembled page candidate, run deterministic validation before screenshot evaluation or visual refine:

```bash
bytedcli --json d2c lynx-page validate --figma2code-dir "<figma2codeDir>" --project-root "<projectRoot>"
```

The command reads the default assembled artifacts under `<figma2codeDir>`:

- `figma2code.tsx`
- `figma2code.css`
- `composition-plan.json`
- `regions-visual/region-artifacts.json`
- `run-artifacts/section-contracts.json`
- `run-artifacts/figma-facts.json`
- `run-artifacts/interaction-inventory.json`

It reads `<projectRoot>/d2c_context/d2c.contract.json` and enforces the selected unit: a `px` contract permits Lynx CSS `px`, while an `rpx` contract continues to reject raw `px`.

It writes `<figma2codeDir>/validation-report.json`. Every issue carries `workflowBlocking`, `repairable`, and `category`. Any `workflowBlocking=true` issue must be resolved before build/capture/evaluation/refine: high-confidence component-selection mismatches, render-blocking component-usage violations, artifact/syntax errors are `repairable=true` and should be repaired (see repair loop below); render service or validator execution failures are `category=infrastructure`, `repairable=false`, and must stop the current run for outer-loop retry instead of editing code. Low-confidence mismatches, quality component violations, and other `workflowBlocking=false` issues are reported but do not block later steps. The report no longer persists `componentGatePassed`; derive the component gate on demand from `category=component && workflowBlocking=true` issues, and always base flow decisions on `workflowBlocking`/`repairable`/`category` directly. If component-selection validation is skipped because the interaction inventory is missing, invalid, or empty, do not present `passed: true` as proof that component selection was validated.

If `validation-report.json.passed` is false, everything needed to repair is already in that report — there is no separate repair-context step. Alongside the per-issue `workflowBlocking` / `repairable` / `category` / `sectionId` fields, the report carries a top-level `repairTargets` array (the affected sections, or `global`) and a `guidance` array.

Read `<figma2codeDir>/validation-report.json`, repair only the `workflowBlocking && repairable` issues, then rerun the validator. Use `repairTargets` to decide whether the repair is global or section-specific. Repair and rerun up to 2 attempts; if any `workflowBlocking=true` issue remains, stop before build/capture/evaluation/refine and report the remaining blocking issues (component or otherwise). If a blocking issue is `category=infrastructure` and `repairable=false`, stop and escalate for outer-loop retry instead of editing code. `workflowBlocking=false` findings remain advisory for this workflow. Do not use this command for pure visual tuning; screenshot differences belong to build/capture, evaluation, and refine.
