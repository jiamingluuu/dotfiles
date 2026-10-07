# Region Generation Workflow

Use this mode for one coarse semantic region.

## Goal

Generate a local, conservative ReactLynx region implementation from:

- one owned target image for the complete local viewport
- one region crop image
- one region Figma JSON subtree
- caller-provided TSX/CSS/RFC output paths

The region is a building block, not the final page.
Generation is image-first: the owned target image is the authority for layout, row count, placement, spacing, clipping, visual hierarchy, and ownership. The Figma JSON is supporting evidence for exact text, assets, style values, and hierarchy for content that is visible in the target image.

Follow `references/workflows/common-phases.md`. This workflow narrows those phases to a single coarse semantic region.

## Phase Additions

### Perceive

- Read the owned target image before reading any structural source.
- Treat the owned target image as the complete local viewport for this region. Its blank space, side insets, outer card margins, vertical gaps, exposed background, bottom padding, captions, and divider/rule spacing are part of the visual contract.
- Read the context crop after the owned target image. Use it only to understand neighboring spacing and cross-region uncertainty.
- List the owned visible content boundary and the owned blank-space boundary separately.
- Read the region Figma JSON after the crop to recover exact text, assets, hierarchy, repeated data, typography, colors, and normalized dimensions for visible target-image content.
- Do not replace the target-image layout with a generic or standard component pattern. If the image shows centered content, unusual padding, clipped rows, nonstandard alignment, or partial visibility, implement the image.
- If the Figma JSON geometry or a component convention conflicts with the owned target image, follow the owned target image and record the conflict in the RFC.
- Follow `d2c_context/d2c.contract.json` `target.unit`. Values in the selected region Figma JSON are already final: `px` comes from raw `origin.json`, while `rpx` comes from normalized `origin.rpx.json`. Do not convert them again or copy crop pixel numbers as CSS.
- Treat image URLs in that region Figma JSON as an allowlist. A visible asset absent from the JSON is missing source evidence, not permission to guess a CDN URL.
- Select image URLs by spatial overlap: for each visible card/bitmap in the target crop, use the Figma image node whose absolute bbox overlaps that card/bitmap. Do not swap in another URL only because it appears elsewhere in the same superset subtree.
- Do not pull content from neighboring regions just because it exists in full-page sources.
- Do not implement mocked device chrome. If the target crop reaches a status bar, signal/battery area, or home indicator pill, treat that chrome as non-product alignment evidence. Preserve only product background/safe-area spacing when it affects the region edge.
- If the target crop begins with product UI at y=0, y=0 is the owned product edge. Do not reserve removed status-bar/safe-area height before the first row.

### Decide

- Choose local components conservatively.
- Choose component behavior only after the target image layout is established. Component defaults must not override visible image geometry.
- Do not assume cross-region relationships unless they are visible inside the crop.
- If the crop suggests a global pattern but lacks context, write it as uncertainty in the RFC. Example: `This tab-title region may control a content region below; global assembly should revisit Tabs + ViewPager`.
- Read `references/component-overview.md` before any non-trivial local component choice.

### Generate

- Produce the region RFC first or alongside the code.
- Produce the region TSX and CSS at the caller-provided paths.
- Keep the root wrapper-friendly and avoid full-page layout.
- Make the root cover the complete owned target viewport without becoming a page wrapper.
- If a region bbox height is provided, the isolated render must naturally cover that owned viewport height. Use min-height, padding, margins, vertical gaps, or content sizing; do not collapse to only the non-blank image/text content.
- Preserve visible target-space blank areas using root padding, child margins, explicit vertical gaps, background exposure, or bottom padding. Do not trim the implementation down to only text/image content.
- If a card or button has visible page background around it in the target, do not make it edge-to-edge just because the region root is width 100%.
- Do not justify a visual mismatch by saying a standard header/list/input/tab normally uses different alignment or spacing. Generic conventions are only fallback when both the target image and Figma JSON are ambiguous.
- Do not draw status bars, battery/signal icons, or home indicator pills, even when they are visible in the crop or Figma subtree.
- Do not add a top spacer for absent status chrome. A region bbox y=0 or a crop whose first row is product navigation/title should render that product row at the region root top edge.
- Preserve normalized Figma `rpx` strings for typography, radius, border, asset dimensions, and major spacing when present. Convert raw numeric Figma values before writing CSS. Do not multiply an existing `rpx` value again.
- For repeated visual groups such as lists, grids, carousels, or masonry feeds, classify the layout before coding:
  - Preserve explicit sibling repeated groups from the region Figma JSON when those groups contain unique visible image assets.
  - Use independent stacks for waterfall/masonry targets where items have unequal heights or staggered vertical starts.
  - Use row grid/flex-wrap only when every row aligns in the target.
  - Never use flex-wrap rows for a masonry target; it pushes the next row below the tallest item and changes the visible order.
  - Do not flatten source groups and rebuild them with odd/even index logic such as `i % 2` unless the source evidence is one row-major list.

### Verify

- Confirm TSX/CSS/RFC files exist.
- Confirm the output is scoped to the region crop.
- Confirm the root spacing contract matches the owned target image.
- Confirm rendered height coverage matches the owned target viewport; a short render means lost region spacing or collapsed content.
- Confirm global uncertainties are documented instead of silently hard-coded.

## Region Contract

- Export the caller-provided component name as a named export.
- Import the caller-provided CSS file.
- Scope local class names with the caller-provided CSS prefix.
- Do not create a page root.
- Do not include whole-page absolute wrappers.
- Make the component root wrapper-friendly.
- If the crop suggests a cross-region relationship, record it in the RFC instead of forcing a page-level component locally.

## RFC Requirements

Keep it short, but use these headings:

- `## Visual Summary`
- `## Owned Viewport Contract`
- `## Root Spacing Contract`
- `## Text And Data Coverage`
- `## Component Decisions`
- `## Layout Decisions`
- `## Asset Decisions`
- `## Generation Constraints`
- `## File Plan`

The root spacing contract must say which visible blank areas are represented by root padding, child margins, vertical gaps, background exposure, or bottom padding.
The layout decisions must explicitly state the image-first visual contract and note any Figma/style conflicts that were resolved in favor of the target image.

Record uncertainties or possible global relationships, such as `may pair with tab content below`, without forcing a page-level component inside the region.
