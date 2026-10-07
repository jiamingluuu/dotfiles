# Global Assembly Workflow

Use this mode after region generation.

## Goal

Use full-page vision and all region artifacts to generate final ReactLynx page code. Region output is source material. Preserve it when compatible, but merge, wrap, or rewrite regions when full-page structure proves a better Lynx component relationship.

Follow `references/workflows/common-phases.md`. This workflow applies those phases to full-page composition after region generation.

## Inputs

- full screenshot
- region bboxes/tree
- region TSX/CSS/RFC
- region crops or region Figma JSON when available
- root/full Figma JSON or skeleton when available
- `run-artifacts/interaction-inventory.json`
- `../interaction-recognition/references/interaction-target-mapping.md`
- final TSX/CSS output paths

## Phase Additions

### Perceive

- Read the full screenshot first.
- Read all region RFC/meta/code and compare region-local decisions against the full screenshot.
- Use region crops and region Figma JSON when a local region needs clarification.
- Identify cross-region patterns, including tab/title rows paired with content panes, search controls paired with result lists, sticky headers, overlays, and mocked system chrome.
- Treat the full screenshot as the aligned product viewport. If status chrome has been cropped away and the screenshot starts with product UI at y=0, final layout must start product UI at y=0. Do not keep a region-local safe-area spacer from the uncropped Figma coordinate system.

### Decide

- Read `references/component-overview.md` before global component decisions.
- Read `interaction-inventory.json` before the composition plan, then read `../interaction-recognition/references/interaction-target-mapping.md`. Treat high-confidence entries as required component-selection constraints and low-confidence entries as soft routing hints.
- If the inventory file is missing or invalid, report that the orchestration step failed and proceed only as a best-effort fallback. Do not use missing inventory as a reason to choose inert static markup for visible tab/list/input/action/overlay patterns.
- When `component-overview.md` selects a route with a follow-up component skill, read that component guide/API/examples before writing final TSX. The final code must use the component's real runtime API, not just a matching tag name.
- Build a compact composition plan before writing final code.
- The composition plan should list:
  - preserved regions
  - merged regions
  - rewritten regions
  - global components such as `Tabs + ViewPager`, `List`, `FeedList`, `FoldView`, overlays, or inputs
  - interaction-driven component choices, including which `Interaction` entry each choice satisfies
  - layout mode: flow by default for semantic regions, absolute only for real overlap/layering
- Region-local output is source material. It is not an untouchable final contract.
- Preserve asset grounding when merging or rewriting regions: final semi.design image URLs must come from supplied Figma/contract evidence, and missing hero artwork must be reported rather than invented.
- Preserve explicit repeated-structure grouping when merging or rewriting regions. If a region Figma JSON or source artifact has sibling repeated containers with unique visible image assets, keep one data array or component subtree per source group and preserve each group's child order. Do not flatten all items into a single array and derive groups with odd/even index splitting (`i % 2`) unless the source evidence is truly one row-major list with no meaningful sibling groups.
- When creating `Tabs` + `ViewPager` from a static screenshot, every inferred peer page must contain visible content. If only the active pane is available, duplicate the active pane content into hidden peer pages instead of leaving them empty or opacity-hidden.
- Do not satisfy `interaction-inventory.json` by adding hidden, unreachable, or visually unrelated components. The selected component or target intrinsic structure must be visible in the assembled page region that the interaction describes.
- Hidden validator-only text, transparent fake components, and opacity-hidden components that are not part of the visible design are forbidden.

### Generate

- Generate final TSX/CSS from the composition plan.
- Generate ReactLynx TSX. Lynx intrinsic tags are lowercase JSX tags and are not imported as JavaScript symbols.
- Do not import `react`, `react-dom`, or `@lynx-js/react` in the final page artifact.
- The final TSX must default export one page component.
- The final TSX must be self-contained with region code inlined or rewritten; remote evaluation submits only `figma2code.tsx` and `figma2code.css`.
- Preserve region code when compatible.
- Merge or rewrite regions when the full screenshot shows a better global component relationship.
- Prefer flow layout for coarse semantic regions.
- Preserve rpx-normalized source units. Do not convert rpx values again during global assembly.
- Remove synthetic top spacers during assembly. A region whose bbox begins at y=0 should not be pushed down by page-header padding, status-bar placeholders, or vertically centered navigation inside an oversized invisible top area.

### Verify

- Confirm final TSX/CSS files exist.
- Confirm every region is either preserved, merged, or intentionally rewritten.
- Confirm global component relationships are represented in the final code.
- Confirm selected routed components follow their follow-up skill APIs.
- Confirm every high-confidence interaction inventory entry is represented by a real visible Lynx component, target intrinsic, or documented target limitation in the composition plan.
- Confirm missing/invalid/empty interaction inventory is reported as a validation weakness and not as component correctness.
- Confirm each `Tabs` + `ViewPager` tab has a non-empty peer page, including pages inferred from static screenshots.
- Confirm semantic wrappers are not mechanically bbox-sized absolute wrappers unless a true layered case is documented.
- Confirm final TSX default exports the page component and has no unsupported runtime imports.
- Confirm final CSS follows `d2c_context/d2c.contract.json` `target.unit`; use raw `origin.json` px evidence for `px`, and normalized `origin.rpx.json` evidence for `rpx`.

## Global Decisions

- Prefer flow layout for coarse semantic regions.
- Use absolute positioning only for true overlays, floating affordances, masks, badges, or layered media.
- Revisit region-local choices when the full screenshot shows a cross-region pattern.
- A tab title region plus a content region below should usually become one `Tabs + ViewPager` relationship.
- A repeated content pane under tabs can be a `List` inside the active pane.
- Large repeated collections should use `List` or `FeedList`; plain `scroll-view` + manual `map()` is only valid for small or mixed scroll containers and must be justified in the composition plan.
- Static screenshots may only expose one active tab pane. Preserve grounded active-pane content when scaffolding inferred peer pages for page behavior.
- Search/input controls should remain semantically connected to their result/content region when visible.
- For top navigation/search/header sections, align the top product row to the screenshot top edge when the screenshot top edge is product content. Added safe-area padding is only valid when the target image visibly contains that blank product-owned area.

## Output Contract

- Produce final `figma2code.tsx`.
- Produce final `figma2code.css`.
- Produce a composition plan JSON when an output path is provided.
- In the final response, report which regions were preserved, merged, or rewritten.
