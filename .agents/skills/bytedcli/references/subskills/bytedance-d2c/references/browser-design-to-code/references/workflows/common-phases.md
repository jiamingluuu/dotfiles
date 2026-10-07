# Common Browser D2C Phases

All `browser-design-to-code` modes follow these four phases. The selected workflow may narrow the scope, but should not skip the phase order.

Before each phase, say exactly one short sentence describing what you are doing next. Only announce these four phase transitions: `Perceive`, `Decide`, `Generate`, and `Verify`.

## 1. Perceive

- Analyze the provided screenshot or crop first.
- If only a region crop is available, use it to define the local visual boundary and avoid page-level assumptions.
- Use Figma JSON, region Figma JSON, IR, JSX, skeleton, or image maps after visual perception to recover exact structure, text content, image URLs, repeated regions, and hidden details the visual input cannot reveal.
- Identify repeated content, overlays, badges, media, inputs, fixed-vs-fluid dimensions, and any mocked system UI chrome that should be excluded.

## 2. Decide

- Choose browser-native HTML structure and CSS layout after perception.
- Prefer conservative local choices when working on a region crop that lacks full-page context.
- Record meaningful layout and asset decisions in the RFC.
- Ignore mocked OS/system chrome unless the product UI explicitly owns that region.
- Prefer flex/grid/normal flow for structured UI and reserve absolute positioning for internal overlays.

## 3. Generate

- Generate complete, compilable browser React for the selected mode's output contract.
- Produce artifacts at caller-provided paths when paths are provided.
- Prefer CSS files over inline styles.
- Use wrapper-friendly roots for generated components/regions.
- Include all visible content required by the selected scope.
- Keep file structure minimal. Extract subcomponents only when repetition or readability clearly benefits.

## 4. Verify

- Check that all required output files were written.
- Check important visible content is represented.
- Check output uses React/browser JSX and browser CSS.
- Check roots/wrappers are layout-appropriate for the mode.
- Check scoped CSS class names use the caller-provided prefix.
- If local validation or preview tooling is available in the host workflow, use it. If it cannot run, report the concrete blocker.

## RFC Shape

When the mode requires an RFC or analysis, keep it compact and use these headings unless the caller provides a stricter contract:

- `## Visual Summary`
- `## Component Decisions`
- `## Layout Decisions`
- `## Styling Decisions`
- `## Generation Constraints`
- `## File Plan`
