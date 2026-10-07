# Full Page Generation Workflow

Use this mode for one-shot page generation when no region pipeline is involved.

## Goal

Generate a complete ReactLynx page from a full screenshot and Figma JSON/IR.

Follow `references/workflows/common-phases.md`. This workflow applies those phases to one-shot full-page generation.

## Phase Additions

### Perceive

- Read the full screenshot first.
- Read Figma JSON/IR after visual perception to recover structure, text, assets, and repeated data.
- Identify page-level hierarchy, global components, scrolling regions, overlays, and mocked system chrome.

### Decide

- Read `references/component-overview.md` before important component decisions.
- Decide page-level components and layout from the full-page view.
- Choose between static fidelity and interactive component behavior conservatively when the product intent is unclear.

### Generate

- Produce a compact RFC/analysis if the caller requested one.
- Produce final TSX/CSS at the caller-provided paths.
- If no paths are provided, emit generic `figma2code.tsx` and `figma2code.css`.

### Verify

- Confirm final output files or emitted artifacts are complete.
- Confirm page-level component relationships are represented.
- Confirm the output obeys `references/lynx-core.md`.

## Output Contract

- Use the caller-provided paths.
- If no paths are provided, emit `figma2code.tsx` and `figma2code.css`.
- Keep the final chat response brief after writing files.
