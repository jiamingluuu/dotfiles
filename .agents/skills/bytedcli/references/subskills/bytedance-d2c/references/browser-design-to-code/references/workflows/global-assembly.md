# Global Assembly Workflow

Use this mode after browser region generation.

## Goal

Use full-page vision and all region artifacts to generate final browser React page code. Region output is source material. Preserve it when compatible, but merge, wrap, or rewrite regions when full-page structure proves a better browser layout relationship.

Follow `references/workflows/common-phases.md`. This workflow applies those phases to full-page composition after region generation.

## Inputs

- full screenshot
- region bboxes/tree
- region TSX/CSS/RFC
- region crops or region Figma JSON when available
- root/full Figma JSON or skeleton when available
- `run-artifacts/interaction-inventory.json`
- `run-artifacts/component-inventory.json` (region-level component attribution: target-agnostic component TYPES, high/low per region; produced upstream by visual segmentation)
- `references/component-inventory-consumption.md` (dynamic DeepWiki resolution of TYPE → library component + usage, and enforcement)
- `../interaction-recognition/references/interaction-target-mapping.md`
- final TSX/CSS output paths

## Phase Additions

### Perceive

- Read the full screenshot first.
- Read region RFC/meta/code selectively and compare region-local decisions against the full screenshot.
- Use region crops and region Figma JSON when a local region needs clarification.
- Identify cross-region patterns, including tab/segment rows paired with content panes, search controls paired with result lists, sticky headers, overlays, repeated cards, and mocked system chrome.

### Decide

- For each region, resolve its component-inventory TYPE to a concrete library component by the strategy the router picks (per `../component-selection-routing.md`, keyed on `d2c_context/`): a business self-built recognition capability when the context declares one, otherwise **dynamically from DeepWiki** (per `../component-inventory-consumption.md`) — query the TYPE by meaning, distill the result into an import + props + minimal JSX card, and record it in the composition plan. This skill hardcodes no routing table or usage cards.
- **Two inventory layers, both binding.** A region's component is fully specified by two orthogonal layers — resolve both and satisfy both in the composition plan:
  - **Selection layer — `run-artifacts/component-inventory.json` (WHICH component).** Region-anchored, target-agnostic component TYPES; map each type to a concrete library component per `references/component-inventory-consumption.md`. A region's `high` type must be realized with the mapped component (or recorded substitution) and referenced in the plan; `low` types are soft hints. **Allowlist brake**: a library component whose type is absent from every region entry needs on-screen evidence recorded in the plan before import.
  - **Behavior layer — `run-artifacts/interaction-inventory.json` (HOW it must behave).** Read it with `../interaction-recognition/references/interaction-target-mapping.md`. It is not a second selector — it is the runtime/completeness contract the selected component must honor: repeated/`minRepeat` groups must not be truncated (generate the full count, not a static subset), tab/paged patterns must generate their hidden peer panes, inputs/actions/overlays must stay genuinely interactive. High-confidence entries are required; low-confidence are soft hints.
  - The two layers compose: e.g. selection says "auxo `List`", behavior says "SCROLL, repeated, minRepeat 5" → use `List` AND render ≥5 data-driven rows, never 3 static ones.
- If either inventory is missing or invalid, report the orchestration weakness and proceed best-effort. Do not use a missing inventory as a reason to choose inert static markup for visible tab/list/input/action/overlay patterns.
- Build a compact composition plan before writing final code.
- The composition plan should list:
  - preserved regions
  - merged regions
  - rewritten regions
  - global browser components or relationships such as tabs, lists, sticky/floating layers, overlays, forms, or repeated card groups
  - interaction-driven component choices, including which `Interaction` entry each choice satisfies
  - layout mode: flow by default for semantic regions, absolute only for true overlap/layering or when preserving exact Figma placement is required
- Region-local output is source material. It is not an untouchable final contract.
- Preserve asset grounding when merging or rewriting regions: final semi.design image URLs must come from supplied Figma/contract evidence, and missing hero artwork must be reported rather than invented.

### Generate

- Generate final TSX/CSS from the composition plan.
- Use the DeepWiki-resolved library component for every region TYPE the composition plan selected, and browser React JSX with HTML tags (`div`, `span`, `p`, etc.) for structural containers and text leaves. Do not downgrade a selected component to styled native markup.
- The final TSX must default export one page component.
- The final TSX should import React and `./figma2code.css`; do not leave imports to region-local files.
- Do not import `react-dom` or Lynx runtime packages in the final page artifact.
- Preserve region code when compatible.
- Merge or rewrite regions when the full screenshot shows a better global browser relationship.
- Prefer flow layout for coarse semantic regions. Use absolute positioning for real overlays, floating affordances, masks, badges, or when exact Figma geometry is the most reliable browser representation.
- Use browser-compatible CSS units. Convert incompatible source units to px-compatible CSS.

### Verify

- Confirm final TSX/CSS files exist.
- Confirm every region is either preserved, merged, or intentionally rewritten.
- Confirm global component relationships are represented in the final code.
- Confirm every component route recorded in the composition plan appears in the final code as a real import + rendered JSX (or carries a documented missing-component substitution). A routed pattern silently re-implemented as styled `div`s fails this check.
- Selection layer: confirm every `high` component-inventory type is realized via its mapped library component (or documented substitution), and every imported library component is justified by an inventory type or recorded on-screen evidence. Unjustified `Image`/`List` imports fail this check.
- Behavior layer: confirm each `high` interaction-inventory entry's runtime contract holds in the final code — repeated/`minRepeat` groups render the full count (not a truncated static subset), tab/paged patterns emit their hidden peer panes, and inputs/actions/overlays are genuinely interactive, not styled static markup.
- Confirm every high-confidence interaction inventory entry is represented by a real visible browser semantic structure or documented target limitation in the composition plan.
- Confirm missing/invalid/empty interaction inventory is reported as a validation weakness and not as component correctness.
- Confirm the page root size/background matches rootInfo.
- Confirm final code is self-contained for the browser demo builder.

## Global Decisions

- Prefer normal browser flow for semantic sections.
- Use exact absolute geometry only when it improves fidelity or preserves a known region contract.
- Revisit region-local choices when the full screenshot shows a cross-region pattern.
- A tab title region plus a content region below should usually become one tabbed content relationship.
- Repeated content panes should usually become a data-driven list or repeated card group.
- Search/input controls should remain semantically connected to their result/content region when visible.
- Do not satisfy `interaction-inventory.json` by adding hidden, unreachable, or visually unrelated components. Use visible browser semantics such as scroll containers, tablist + panel, input/textarea, button, overlay/dialog, or documented target limitations.
- Hidden validator-only text, transparent fake components, and opacity-hidden components that are not part of the visible design are forbidden.

## Output Contract

- Produce final `figma2code.tsx`.
- Produce final `figma2code.css`.
- Produce a composition plan JSON when an output path is provided.
- In the final response, report which regions were preserved, merged, or rewritten.
