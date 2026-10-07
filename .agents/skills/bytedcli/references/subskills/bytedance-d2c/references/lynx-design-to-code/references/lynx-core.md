# Lynx Core D2C Rules

This file is shared knowledge for all `lynx-design-to-code` modes.

## Syntax And Imports

- Use ReactLynx, not React DOM.
- Do not import `react`, `react-dom`, or browser-only routing/runtime packages.
- Use lowercase Lynx primitive tags such as `<view>`, `<text>`, `<image>`, `<svg>`, `<scroll-view>`, and x-elements directly as JSX tags.
- Primitive tags are platform/intrinsic elements, not JavaScript exports. Do not import primitive tag names from `@byted-lynx/react`.
- Import only real JavaScript exports from `@byted-lynx/react`, such as `Component`, `root`, `useState`, `useRef`, `useEffect`, or types when needed.
- Use capitalized names for imported/custom components.
- Text content must live inside `<text>` or a component that explicitly supports text children.
- Do not use HTML tags such as `<div>`, `<span>`, `<img>`, `<p>`, or `<button>`.

## Component Routing

- Read `references/component-overview.md` before important page-level, scrolling, repeated, carousel, overlay, media, or interactive component decisions.
- Prefer specialized components when the visible structure clearly matches them.
- Use `List` or `FeedList` for large repeated lists/feeds. Do not fake a large repeated list with `.map()` inside a plain generic container.
- Use `Tabs` + `ViewPager` together when visible tab titles control peer content panes. In a static screenshot, one active pane below a convincing tab title row is enough evidence to infer hidden peer panes.
- When only the active tab pane is available in static evidence, every inferred `ViewPager` peer page must still render real content. Reuse the active pane content for hidden peers instead of generating empty, opacity-hidden, or placeholder-only pages.
- Use `scroll-view` for small or mixed scrolling regions. Prefer `List`/`FeedList` when the pane is mostly repeated rows/cards.
- Use `x-input-ng` for real editable single-line inputs. Do not fake editable input with `view` + `text`.
- Use `svg` for SVG content or SVG URLs. Do not render SVG assets with `image`.
- Use image/video/media elements according to asset type and visible behavior; do not reduce media playback or vector content to bitmap placeholders unless no better source exists.
- Use only image URLs present in the supplied Figma/asset evidence. Do not invent or autocomplete CDN asset filenames; if essential visible artwork has no extracted URL, record the missing source evidence instead of rendering an ungrounded image.

## Layout Policy

- Lynx elements default to `display: linear`, whose default `linear-direction: column` stacks children vertically. Do not assume the Web's default block layout.
- Use `display: flex` for generated layout containers unless the design or target repo specifically requires linear or grid layout. Flex layout follows the Web default: `flex-direction: row`, so children flow horizontally unless `flex-direction: column` is set explicitly.
- Prefer flex, normal flow, padding, margin, percentages, and `aspectRatio`.
- A generated component or region root should be wrapper-friendly: `width: 100%`, normal flow or `position: relative`, and content-driven height when practical.
- Do not copy a Figma bbox into a component root as `width: Npx` / `height: Npx`.
- Do not put `position: absolute` on a component or region root. Reserve absolute positioning for true internal overlays, badges, masks, anchored controls, layered media, or explicit floating UI.
- Preserve fixed values only when they are important for visual fidelity and not simply canvas/bbox dimensions.
- Avoid `max-width` and `max-height` unless clearly required.
- Prefer symmetric spacing and semantic centering over one-sided offset hacks.

## Figma Auto-Layout (`figmaLayout`)

Some Figma / `origin.json` nodes carry a `figmaLayout` namespace describing the design's auto-layout intent. Treat it as a **supporting signal** for flow structure and fixed-vs-fluid sizing — it complements, and does not override, the visual evidence, `style` values, and the layout rules above. It is absent on many nodes; absence just means fall back to visual + `style`. For the full field → flex mapping see `../d2c-visual-segmentation/references/figma-layout.md`; convert its raw-px spacing (`itemSpacing`, `counterAxisSpacing`, `padding*`) to `rpx` per the Units rules below.

## Units

- Follow the target repo's established unit convention first.
- If no convention is available, use a real conversion baseline from the Figma/screenshot width.
- Use `rpx` when the project expects Lynx responsive pixels or the caller requests it.
- In the unified Lynx D2C workflow, source artifacts may contain either normalized `rpx` strings or raw numeric Figma px values. Preserve explicit `rpx` strings, but convert raw numbers/`px` strings before writing Lynx CSS.
- Region target screenshots are scaled visual evidence. Do not treat screenshot/crop pixel dimensions such as `240px` as CSS `rpx` values.
- When conversion to `rpx` is required, use `rpx = figmaPx * 750 / designWidth`.
  - For a 375px-wide Figma design, `1px = 2rpx`, `10px = 20rpx`, `18px = 36rpx`.
  - Do not copy a Figma px number and only change the suffix to `rpx`.
- Use `px` only for APIs that require it, hairlines, or physically stable tiny values.
- Prefer `width: 100%` / `height: 100%` for full-container layers instead of fixed full-canvas values.
- Explain the chosen unit family and baseline in RFC output.

## Verification

Before finalizing, check:

- Output files were written.
- Important visible content is represented.
- Component choices match visible global patterns.
- No React DOM imports or HTML tags appear in Lynx output.
- Primitive tag names are not imported from `@byted-lynx/react`.
- Root layout is wrapper-friendly unless an exception is explicitly justified.
