# Component Overview Routing Guide

This skill is the routing layer for component selection.

Use it to do three things only:

1. Choose the best Lynx component or element for a region.
2. Match that choice against the identification signatures below.
3. Open the documented follow-up skill before generating code.

Do not treat this file as the full API reference for every component. Once a route is selected, the follow-up skill becomes the source of truth.

## Component Selection Guide

Apply these rules in order:

1. Prefer specialized containers before primitives.
   - `FeedList` / `List` / `ScrollView` / `Swiper` / `ViewPager` / `Tabs` / `FoldView` / `Dialog` / `Popup`
2. Use media-specific routes before generic rendering.
   - `VideoEngine`, `image`, `svg`
3. Use dedicated interactive elements before generic primitives.
   - `input`
4. Use `view` only when the region is structural and does not imply a stronger interaction model.
5. Use `text` for all textual leaf nodes.
6. If no signature fits, fall back to the nearest dedicated Lynx skill and record the assumption in the RFC.

## Routing Rules

- Always record the evidence that matched the chosen route.
- If a route has a `Next skill`, open it before implementation.
- A selected route is valid only when the generated TSX follows the follow-up skill's runtime API. Do not treat a component name in TSX as sufficient evidence.
- Only expose routes that have a dedicated follow-up skill.
- If a UI pattern has no dedicated skill, do not surface it as a top-level route here; instead route to the nearest dedicated skill(s) and note the assumption in the RFC.
- Never map SVG assets to `image`.
- If a repeating scrollable region can grow large, or a scrollable pane is primarily repeated cards/rows, prefer `List` or `FeedList` over `ScrollView`.
- If the UI indicates a real tabbed layout with a title row and an associated peer content area, route the title row to `Tabs` and the content area to `ViewPager`. Treat it as a `Tabs` + `ViewPager` pair, not a plain `view` shell, and do not require all peer panes to be simultaneously visible before using this route; when a convincing tab-title row and one active pane are visible in a static screenshot, assume the sibling panes are hidden peers.
- For inferred `Tabs` + `ViewPager` peers, every tab must map to a non-empty page. If only the active pane is visible in Figma, reuse the active pane content for hidden pages rather than emitting empty or opacity-hidden pages.
- Stage, status, or schedule labels still route to `Tabs` + `ViewPager` when the row has an active indicator and switches a peer content pane. Use a normal `view` row only when the row is passive metadata with no tab behavior.
- If a bottom action is fixed at the page/container bottom, keep it outside scroll containers. Do not satisfy a page-level bottom action with a Button inside `List` or `FeedList` item content.
- If the UI shows a real editable single-line text field, route to `input` and implement it with `x-input-ng`, not `view` + `text`.

## Quick Routing Map

- Full-page horizontal pages: `ViewPager`
- Tab titles controlling peer views: `Tabs` + `ViewPager`
- Passive status or schedule rows with no tab behavior: `view`
- Small mixed-content overflow area: `ScrollView`
- Large repeated data: `List`
- Feed with refresh/load-more semantics: `FeedList`
- Horizontal card or image carousel: `Swiper`
- Sticky toolbar plus collapsible header: `FoldView`
- Blocking centered modal: `Dialog`
- Bottom sheet or sliding panel: `Popup`
- Explicit action target: `Button`
- Single-line editable field: `input`
- Standard media playback: `VideoEngine`
- Deferred heavy subtree: `LazyComponent`
- Generic structure: `view`
- Text leaf: `text`
- Raster asset: `image`
- SVG asset or inline vector: `svg`

## Routed Entries With Dedicated Skills

### `<List>`
- Choose when: A scrollable region renders repeated items and the count can be large.
- Avoid when: The content is small, fixed, or structurally mixed; use `ScrollView` instead.
- Identification Signatures: Repeated card rows, `.map()` item render loops, virtualized feed/grid intent, large uniform datasets.
- Implementation guard: give the `List` itself an explicit height, do not use `z-index` / `zIndex` inside list item descendants, and keep fixed page-level bottom actions outside the `List`.
- Next skill: `./components/list/guide.md`

### `<FeedList>`
- Choose when: The page is a feed stream with pagination, pull-to-refresh, or load-more behavior.
- Avoid when: It is only a static or finite repeated list; use `List`.
- Identification Signatures: News/video/feed stream, append-on-scroll behavior, refresh header, load-more footer, waterfall/feed semantics.
- Implementation guard: give the `FeedList` itself an explicit height, do not use `z-index` / `zIndex` inside list item descendants, and keep fixed page-level bottom actions outside the `FeedList`.
- Next skill: `./components/feed-list/guide.md`

### `<ScrollView>`
- Choose when: A bounded region needs scrolling but its children are heterogeneous or few.
- Avoid when: The content is a large repeated dataset, or the scrollable pane is mostly repeated cards/rows; use `List` or `FeedList`.
- Identification Signatures: Overflowing mixed layout, small number of children, horizontal or vertical content tray without virtualization, mostly static content sections.
- Next skill: `./components/scroll-view/guide.md`

### `<Swiper>`
- Choose when: A compact horizontal carousel shows cards, banners, or images page by page.
- Avoid when: Each page is a full independent screen; use `ViewPager`.
- Identification Signatures: Horizontal slides, paging dots, hero banner rotation, card/image carousel.
- Next skill: `./components/swiper/guide.md`

### `<ViewPager>`
- Choose when: The user swipes between full pages or peer content panes.
- Avoid when: The region is only a carousel or banner; use `Swiper`.
- Identification Signatures: Full-page horizontal views, one page visible at a time, peer screens like category pages or top-level tabs, a single active pane shown beneath a visible tab bar in a static screenshot where the sibling panes are implied hidden peers.
- Implementation guard: each page must contain valid visible content. When static evidence only provides the active pane, reuse that pane's grounded content for inferred peer pages instead of generating empty or opacity-hidden pages.
- Next skill: `./components/view-pager/guide.md`

### `<Tabs>`
- Choose when: A title bar or segmented control switches peer content views.
- Avoid when: The design is only a page-swiping container with no visible tab-title pattern, or the row is passive stage/status/schedule metadata with no active indicator or peer pane.
- Identification Signatures: Tab titles, active indicator, segmented control, a selected title row directly above a primary content pane, paired with peer content panes even when only the active pane is visible and the other panes are implied hidden peers.
- Pairing Rule: A real tabbed content pattern should be implemented as `Tabs` + `ViewPager`, including static screenshots where only the active pane is visible and the sibling panes are implied. Set a literal `viewpagerId` on `Tabs`; use the same explicit id on `ViewPager` except for a single default `ViewPager` paired with `Tabs viewpagerId='viewpager'`. Do not replace the content panes with ad-hoc `view` switching, keep the native `linkBar` for active indicators, place `Tabs` in a width-bounded container, use `tabSpacing` / margin / padding instead of fake large equal tab widths, and ensure every tab has a non-empty peer page.
- Next skill: `./components/tabs/guide.md`
- Required paired skill: `./components/view-pager/guide.md`

### `<FoldView>`
- Choose when: A collapsible header, sticky toolbar, and scrollable content slot move together.
- Avoid when: It is only an accordion section; do not confuse page-level fold behavior with simple hide/show.
- Identification Signatures: Header collapses on scroll, toolbar pins, nested scrolling coordination.
- Next skill: `./components/fold-view/guide.md`

### `<Dialog>`
- Choose when: The UI interrupts the flow and requires focused confirmation or acknowledgment.
- Avoid when: The content is a bottom sheet or lightweight hint; use `Popup` or `Toast`.
- Identification Signatures: Centered modal, backdrop, confirm/cancel actions, alert or blocking prompt.
- Next skill: `./components/dialog/guide.md`

### `<Popup>`
- Choose when: Secondary content or actions slide up from the bottom or appear as an interactive panel.
- Avoid when: The interaction is a blocking alert; use `Dialog`.
- Identification Signatures: Bottom sheet, draggable panel, staged height stops, action sheet, partial-screen overlay.
- Implementation guard: use the guide's ref + render-prop API; no `visible` / `placement` or direct primitive body. If the Popup contains `List`, `ScrollView`, or `FoldView`, pass popupOptions into the content component, bind `main-thread:gesture` to the nested scroll container, and set `scrollContainerId` to the nested `listId` / `scrollviewId`.
- Next skill: `./components/popup/guide.md`

### `<Button>`
- Choose when: The region is an explicit tap target whose primary job is to trigger an action.
- Avoid when: The node is only text, only layout, or just a passive label.
- Identification Signatures: Tappable control with pressed/disabled states, label plus optional icon, strong action affordance.
- Next skill: `./components/button/guide.md`

### `input` route (`x-input-ng`)
- Choose when: The region is a real editable single-line text field.
- Avoid when: The node is only a static label, or the field is multi-line.
- Identification Signatures: Search bars, login/account fields, OTP/code entry, single-line editable text boxes, visible placeholder/caret/focus affordance.
- Next skill: `./components/input/guide.md`

### `<VideoEngine>`
- Choose when: The region is standard audio/video playback or a media player area.
- Avoid when: The media is a live stream, or the region is only a poster image.
- Identification Signatures: Video player surface, poster, play/pause controls, scrub/progress UI, embedded media playback.
- Next skill: `./components/video-engine/guide.md`

### `<LazyComponent>`
- Choose when: A heavy subtree should mount only after it approaches or enters the viewport.
- Avoid when: The region is tiny, always visible, or business-critical above the fold.
- Identification Signatures: Expensive off-screen modules in long scrolling pages, explicit exposure-driven rendering, estimated size available.
- Next skill: `./components/lazy-component/guide.md`

### `<view>`
- Choose when: The node is a generic structural wrapper for layout, spacing, background, border, or grouping.
- Avoid when: The region clearly matches a stronger route such as `List`, `ScrollView`, `Dialog`, `Popup`, or `Swiper`.
- Identification Signatures: Plain container, flex row/column, decorative wrapper, layout grouping with no specialized interaction semantics.
- Next skill: `./components/view/guide.md`

### `<text>`
- Choose when: The node's primary payload is visible text.
- Avoid when: The node is actually a container, bitmap, or vector.
- Identification Signatures: Headings, labels, paragraphs, captions, counters, button labels, inline text spans.
- Next skill: `./components/text/guide.md`

### `<image>`
- Choose when: The asset is raster-based such as PNG, JPG, JPEG, WebP, or GIF.
- Avoid when: The source is SVG or inline vector markup.
- Identification Signatures: Photo, avatar, poster, bitmap URL, `<img>`-like content, raster background asset.
- Next skill: `./components/image/guide.md`

### `<svg>`
- Choose when: The region is vector markup, an `.svg` asset, or a vector icon/illustration that must stay scalable.
- Avoid when: The asset is a bitmap photo or poster.
- Identification Signatures: Inline SVG markup, SVG XML string, `.svg` URL, vector path icon, shape-based illustration.
- Next skill: `./components/svg/guide.md`

## Final Routing Reminder

For each major region:

1. Pick the best route from this file.
2. Quote the evidence that matched its identification signatures.
3. Open the documented next skill when one exists.
4. Only fall back to `view` after ruling out the specialized routes above.
