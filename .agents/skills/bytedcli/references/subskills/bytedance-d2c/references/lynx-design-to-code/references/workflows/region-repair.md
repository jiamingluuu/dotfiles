# Region Repair Workflow

Use this mode to repair one generated coarse semantic region in place.

## Goal

Repair an existing ReactLynx region implementation from:

- the stable local region target image
- the current rendered or aligned rendered evidence
- optional diff evidence
- the current region TSX/CSS/RFC
- the region Figma JSON subtree
- caller-provided repaired TSX/CSS/RFC output paths

The repair output remains a region building block. It must not become a page implementation.

Follow `references/workflows/common-phases.md`. This workflow narrows those phases to image-driven repair of one region.

## Phase Additions

### Perceive

- Read the target region image first. Treat it as the stable local target viewport.
- Read rendered and diff evidence only after the target image. If raw rendered evidence includes a preview-service canvas, ignore unrelated canvas area and compare the local component content.
- Read current TSX/CSS/RFC and region Figma JSON after visual comparison.
- Follow `d2c_context/d2c.contract.json` `target.unit`. Values in the selected region Figma JSON are already final: `px` comes from raw `origin.json`, while `rpx` comes from normalized `origin.rpx.json`. Do not convert them again or copy target/rendered pixel numbers as CSS.
- Classify the failure before editing:
  - spacing, padding, margin, or target blank-space loss
  - wrong asset, missing asset, wrong asset scale, or wrong aspect ratio
  - typography, color, radius, shadow, or border mismatch
  - missing, repeated, clipped, or wrongly ordered content
  - wrong component route or structure
  - unreliable preview/evaluation evidence
- Use region Figma JSON to audit text, asset URLs, node dimensions, and repeated structures.
- For each visible bitmap/card, choose the image URL from the Figma node whose absolute bbox overlaps that visible bitmap/card. Same-subtree URLs are not interchangeable.
- If rendered evidence height is shorter than the target region image, classify the failure as collapsed owned viewport height before fine visual differences.
- If target/render evidence contains mocked device chrome such as a status bar or home indicator, exclude it from owned product content. Do not add chrome to improve the visual score.
- If the target region image begins with product UI at y=0, y=0 is the owned product top edge. Any rendered top offset before that row is a spacing/layout failure, not safe-area content to preserve.

### Decide

- Prefer CSS-only repair for spacing, color, typography, radius, border, and simple sizing issues.
- Change TSX only when the structure prevents the visual fix, when a component route is wrong, or when content/assets are missing.
- Use `references/component-overview.md` before changing component structure or choosing a stronger component route.
- If a routed component has a bundled guide/API/example, read it before editing that component.
- Preserve the current component boundary unless the target image and Figma JSON prove that the current internal structure is wrong.
- Do not make global assembly decisions here. Cross-region relationships belong in the RFC as notes for global assembly.

### Generate

- Edit from the current region implementation. Do not rewrite from scratch unless the current structure cannot represent the target.
- Preserve the named export, CSS import, CSS prefix, and caller-provided output paths.
- Preserve target-space blank areas that are visible in the target image, including side insets, card outer margins, vertical gaps, background exposure, bottom padding, and divider/rule spacing.
- Repair collapsed owned viewport height with min-height, content sizing, padding, margins, or vertical gaps so the isolated render naturally covers the region target height.
- Preserve only product background/safe-area spacing near device chrome; do not render status icons or the home indicator pill.
- Do not add a top spacer for absent status chrome. If the stable target has product navigation/title/search at the top edge, render that content at the region root top edge.
- Preserve major Figma asset geometry. A large hero image or background asset should not be decomposed into tiny decorative pieces unless the Figma JSON proves that structure.
- Preserve normalized Figma `rpx` strings for typography, radius, border, asset dimensions, and major spacing when present. Convert raw numeric Figma values before writing CSS. Do not multiply an existing `rpx` value again.
- For repeated visual groups, repair the DOM model when needed:
  - waterfall/masonry target: independent stacks when items have unequal heights or staggered vertical starts;
  - row-aligned grid target: row grid or flex-wrap is acceptable;
  - unequal item heights plus `flex-wrap` is a strong failure signal because subsequent items are vertically misplaced;
  - explicit Figma sibling groups with unique image assets: preserve each source group and its child order. Do not repair by flattening all items and splitting with odd/even index logic such as `i % 2`.
- Use only image URLs that exist in the region evidence or explicit allowlist.
- Keep the region root wrapper-friendly: no page root, no fixed page footer, no cross-region absolute positioning, and no neighboring-region content.

### Verify

- Confirm repaired TSX/CSS/RFC files exist at the requested output paths.
- Confirm the named export, CSS import, and CSS prefix are unchanged.
- Confirm all visible target text and required assets are represented or explicitly marked as missing source evidence in the RFC.
- Confirm root spacing matches the target region viewport rather than trimming to content.
- Confirm the rendered region does not collapse shorter than the target viewport.
- Confirm no preview-service canvas artifact was implemented as product UI.

## Source Priority

1. Target region image: visual truth for this local viewport.
2. Region Figma JSON: text, assets, hierarchy, repeated content, and dimensions.
3. Rendered/aligned/diff evidence: evidence of current failures.
4. Current TSX/CSS/RFC: repair substrate.
5. Validation score and issue labels: weak signals that need visual confirmation.

## RFC Requirements

Keep it short. Include:

- failure classification
- changes made
- component decisions or changed routes
- asset decisions
- unresolved evidence problems
- global assembly notes, if any
