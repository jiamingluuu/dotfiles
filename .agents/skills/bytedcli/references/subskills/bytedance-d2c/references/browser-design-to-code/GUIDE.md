---
name: browser-design-to-code
description: Mode-based Figma-to-browser React design-to-code guidance for region generation and full-page generation. Covers both mobile (H5) and desktop web output.
allowed-tools: Bash, Read, Grep
---
# browser-design-to-code

Use this skill when a browser (H5 / desktop web) D2C agent needs React/browser syntax, layout guidance, or a concrete generation workflow.

## Select A Mode

The caller should state one mode. If no mode is stated, use `full-page-generation`. If the caller is working from visual-segmentation/region artifacts, use `global-assembly`; do not use `full-page-generation` after a region pipeline.

- `region-generation`: generate one coarse semantic region from a region crop and region Figma JSON.
- `global-assembly`: revisit all region artifacts with full-page vision, merge or rewrite cross-region structures, and generate final page code.
- `full-page-generation`: generate a complete page directly from a full screenshot and Figma JSON/IR.

## Required Reads

Always read:

- `references/browser-core.md`
- `references/workflows/common-phases.md`
- `references/component-selection-routing.md` (the three-branch router that picks HOW each selection-layer TYPE becomes a concrete component: business self-built recognition / DeepWiki dynamic / lynx-ui fixed mapping, keyed on `d2c_context/`)
- `references/component-inventory-consumption.md` (how the two inventory layers select components and how usage is resolved dynamically from DeepWiki — this skill hardcodes no component list)

Then read exactly one workflow:

- `references/workflows/region-generation.md`
- `references/workflows/global-assembly.md`

## Component selection & usage: dynamic, no hardcoded list

This skill carries **no** hardcoded component routing table or usage cards. A region's component TYPE comes from `run-artifacts/component-inventory.json` (target-agnostic, produced upstream by visual segmentation); the concrete library component and its `import` + props + JSX are resolved **at runtime from DeepWiki** for the target `packageName`, via the `deepwiki-skill` scripts. The exact protocol — query a TYPE by meaning, budget, consume discipline (distill results into an import + props + minimal JSX card recorded in the composition plan), missing-component substitution, and the allowlist brake — lives in `references/component-inventory-consumption.md`. Read it before selecting any component.

When running `global-assembly`, read `<figma2codeDir>/run-artifacts/interaction-inventory.json` and `<figma2codeDir>/run-artifacts/component-inventory.json` together as the two binding layers (selection + behavior), per `references/component-inventory-consumption.md`. When consuming `interactionInventory`, also read:

- `../interaction-recognition/references/interaction-target-mapping.md`

## Optional: Node Semantic Descriptions

Before generating, enrich the nodes you are about to build with human-curated semantic descriptions via the `get-figma-design-description` skill (it calls `getFigmaDescription` with `figmaPageUrl` + node ids and returns a short `Role / Intent / Data / Implementation / Unknowns` contract or structured JSON per node). Use any returned `figmaDescription` as extra semantic context that the design can't reveal (data binding, intended interaction, implementation constraints). If the result contains `semanticJson` or `rootConfig`, read those structured fields directly. Apply every recognized `rootConfig` root-level style, layout, or runtime value to the page's outermost root element style/class instead of putting it on an inner node or ignoring it; leave unknown fields as notes rather than inventing behavior. A `found: false` node simply has no description yet — proceed normally. Rank these descriptions per Source Priority below (above visual guessing, below screenshot and Figma structure).

## Source Priority

1. Screenshot or region crop: visual truth.
2. Figma JSON / region Figma JSON / IR: structure, text, assets, repeated data.
3. Node semantic descriptions from `get-figma-design-description`: human-curated intent and implementation constraints.
4. Component selection & usage (`references/component-inventory-consumption.md`): the inventory TYPE plus the DeepWiki-resolved library component and its real API. It decides implementation, never overrides what the screenshot shows.
5. Region RFC/meta/code: source material for assembly, not an untouchable final contract.
6. Browser and React references in this skill: implementation constraints.

## Output Discipline

Produce the requested artifacts at the caller-provided paths. Do not treat a chat code block as a substitute for required artifacts.
