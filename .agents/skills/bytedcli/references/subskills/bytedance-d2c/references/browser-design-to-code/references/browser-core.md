# Browser Core D2C Rules

This file is shared knowledge for all `browser-design-to-code` modes.

## Syntax And Imports

- Use standard React for browser rendering.
- Import React from `react`.
- Use standard HTML JSX tags such as `<div>`, `<span>`, `<img>`, `<p>`, `<button>`, `<section>`, and `<article>`.
- Keep region components as named exports.
- Import the caller-provided CSS file from the TSX file.
- Prefer semantic local component names and stable local arrays for repeated content.

## Browser Layout Policy

- A generated component or region root should be wrapper-friendly: `width: 100%`, `height: 100%` when the caller provides a fixed wrapper, `box-sizing: border-box`, and normal flow or `position: relative`.
- Keep page-level absolute positioning outside region components. Region components may use absolute positioning for internal overlays, badges, masks, anchored controls, or layered media.
- Use flex/grid/normal flow for cards, lists, rows, and text layout.
- Prefer CSS files over inline styles for layout, color, typography, and backgrounds.
- Keep class names scoped with the caller-provided prefix.

## Figma Auto-Layout (`figmaLayout`)

Some Figma / `origin.json` nodes carry a `figmaLayout` namespace describing the design's auto-layout intent. Treat it as a **supporting signal** for flow structure and fixed-vs-fluid sizing — it complements, and does not override, the visual evidence, `style` values, and the Browser Layout Policy above. It is absent on many nodes; absence just means fall back to visual + `style`. For the full field → flex mapping (container/child fields, `HUG`/`FILL` sizing, unit handling) see `../d2c-visual-segmentation/references/figma-layout.md`.

## Units

- Use browser CSS units: `px`, `%`, `rem`, `em`, `vw`, and `vh`.
- In unified browser workflows, mobile (H5) design output is assembled on a 375px browser baseline unless the caller states another baseline; for desktop web, follow the design's own width.
- Use `width: 100%` and `height: 100%` for full-container layers instead of fixed full-canvas values.
- Explain the chosen unit family and baseline in RFC output.

## Assets

- Use image URLs present in the supplied Figma/asset evidence.
- Use `<img src="..." />` for extracted raster assets.
- If essential visible artwork has no extracted URL, record missing source evidence in the RFC and recreate only the visible, reliable parts with text, CSS, or inline SVG.

## Verification

Before finalizing, check:

- Output files were written.
- Important visible content is represented.
- The TSX is standard React/browser JSX.
- The component root is wrapper-friendly.
- CSS selectors are scoped with the caller-provided prefix.
- Assets are grounded in supplied evidence.
