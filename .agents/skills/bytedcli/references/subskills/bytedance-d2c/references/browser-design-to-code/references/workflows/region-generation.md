# Region Generation Workflow

Use this mode for one coarse semantic browser region.

## Goal

Generate a local, conservative React browser region implementation from:

- one region crop image
- one region Figma JSON subtree
- caller-provided TSX/CSS/RFC output paths

The region is a building block, not the final page.

Follow `references/workflows/common-phases.md`. This workflow narrows those phases to a single coarse semantic region.

## Phase Additions

### Perceive

- Read the region crop before reading any structural source.
- List the visible content boundary for this crop.
- Read the region Figma JSON after the crop to recover text, assets, hierarchy, and repeated data.
- Treat image URLs in that region Figma JSON as the asset evidence for the region.
- Avoid pulling content from neighboring regions just because it exists in full-page sources.

### Decide

- When a business design system applies (`packageName`), identify the crop's component-worthy patterns (image, chip, input, tab row, repeated rows, overlay, banner, ...) and resolve each to a concrete library component and its usage **dynamically from DeepWiki** (per `../component-inventory-consumption.md`); record the component + evidence in the RFC. If nothing fits, say so in the RFC. This skill hardcodes no routing table or usage cards.
- Choose local HTML structure conservatively for everything not routed to a component.
- Use normal browser layout primitives: flex, grid, normal flow, padding, margin, percentages, and fixed pixel values where visual fidelity needs them.
- If the crop suggests a global pattern but lacks context, write it as uncertainty in the RFC.

### Generate

- Produce the region RFC first or alongside the code.
- Produce the region TSX and CSS at the caller-provided paths.
- Keep the root wrapper-friendly and avoid full-page layout.

### Verify

- Confirm TSX/CSS/RFC files exist.
- Confirm the output is scoped to the region crop.
- Confirm global uncertainties are documented instead of silently hard-coded.

## Region Contract

- Export the caller-provided component name as a named export.
- Import the caller-provided CSS file.
- Scope local class names with the caller-provided CSS prefix.
- Use browser JSX tags and CSS.
- Do not create a page root.
- Do not include whole-page absolute wrappers.
- Make the component root wrapper-friendly.
- If the crop suggests a cross-region relationship, record it in the RFC instead of forcing a page-level component locally.

## RFC Requirements

Keep it short. Include:

- visible content summary
- local structure decisions
- component routes taken (or "no route fits"), with the matching evidence
- layout and unit baseline
- assets used
- uncertainties or possible global relationships
