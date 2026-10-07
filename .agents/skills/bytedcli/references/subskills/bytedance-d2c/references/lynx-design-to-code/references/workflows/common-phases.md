# Common D2C Phases

All `lynx-design-to-code` modes follow these four phases. The selected workflow may narrow the scope, but should not skip the phase order.

Before each phase, say exactly one short sentence describing what you are doing next. Only announce these four phase transitions: `Perceive`, `Decide`, `Generate`, and `Verify`.

## 1. Perceive

- Analyze the provided screenshot or crop first.
- If a full-page screenshot is available, use it to infer hierarchy, reading order, major sections, region prominence, cross-region relationships, and mocked system chrome.
- If only a region crop is available, use it to define the local visual boundary and avoid page-level assumptions.
- Use Figma JSON, region Figma JSON, IR, JSX, skeleton, or image maps after visual perception to recover:
  - exact structure and hierarchy
  - text content
  - image URLs and asset types
  - repeated regions
  - hidden details the visual input cannot reveal
- Identify scrolling, repeated content, overlays, badges, media, inputs, tab/title-control patterns, fixed-vs-fluid dimensions, and any system UI chrome that should be excluded.

## 2. Decide

- Choose components and layout after perception, not before.
- Use `references/component-overview.md` before finalizing important page-level, scrolling, repeated, carousel, overlay, media, or interactive component decisions.
- Prefer specialized Lynx components when the visible structure clearly matches their signatures.
- Prefer conservative local choices when working on a region crop that lacks full-page context.
- Revisit local region choices during global assembly when the full screenshot shows a better cross-region relationship.
- Consider user-land components when `packageName` is present and they match the design without harming fidelity.
- Record the reason for meaningful component choices in the RFC or composition summary.

Hard decision rules:

- Use `List` or `FeedList` for large repeated collections.
- Use `Tabs` + `ViewPager` together when visible tab titles control peer content panes.
- Use `scroll-view` for small or mixed scrollable containers.
- Use `x-input-ng` for real editable single-line fields.
- Use `svg` for SVG content or SVG URLs.
- Use image/video/media elements according to the actual visible asset and behavior.
- Ignore mocked OS/system chrome such as status bars unless the product UI explicitly owns that region. Let screenshot alignment account for non-product top offsets instead of generating placeholder space.
- If the provided screenshot/crop has already removed mocked status chrome, its y=0 is the product target y=0. Do not add safe-area/status-bar placeholder padding before the first product row unless that blank area is visibly present in the target image.
- Avoid absolute positioning unless the UI is genuinely layered.

## 3. Generate

- Generate complete, compilable ReactLynx for the selected mode's output contract.
- Produce artifacts at caller-provided paths when paths are provided.
- Prefer CSS files over inline styles unless inline styles are clearly necessary.
- Use wrapper-friendly roots for generated components/regions.
- Include all visible content required by the selected scope.
- Keep file structure minimal. Extract subcomponents only when repetition or readability clearly benefits.
- In region mode, generate local source material and record uncertainty instead of forcing global structures.
- In global assembly mode, preserve region output when compatible, but merge or rewrite when full-page structure proves a better component relationship.

## 4. Verify

- Check that all required output files were written.
- Check important visible content is represented.
- Check component choices match visible patterns and the selected mode's scope.
- Check Lynx output has no React DOM imports and no HTML tags.
- Check primitive tag names are not imported from `@byted-lynx/react`.
- Check roots/wrappers are layout-appropriate for the mode.
- Check no large repeated list is faked inside a generic container when a list component is required.
- Check no real editable input is implemented as `view` + `text`.
- Check no tabbed peer-content pattern is implemented without a `Tabs` + `ViewPager` relationship.
- If local validation or preview tooling is available in the host workflow, use it. If it cannot run, report the concrete blocker.

## RFC Shape

When the mode requires an RFC or analysis, keep it compact and use these headings unless the caller provides a stricter contract:

- `## Visual Summary`
- `## Component Decisions`
- `## Layout Decisions`
- `## Styling Decisions`
- `## Generation Constraints`
- `## File Plan`
