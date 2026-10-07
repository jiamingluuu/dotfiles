# Figma Auto-Layout (`figmaLayout`) → Flex Mapping

Shared reference for interpreting the `figmaLayout` namespace when writing or refining
D2C code (`browser-design-to-code`, `lynx-design-to-code`, `d2c-refine-workflow`, …).
Target-neutral: the field → flex mapping is the same for browser CSS and Lynx; only the
unit family differs (see *Unit handling* below).

## What it is and how much to trust it

Some Figma JSON / `origin.json` nodes carry a `figmaLayout` namespace that records the
design's auto-layout intent (`style` is already flattened CSS and no longer exposes it).

Treat `figmaLayout` as a **supporting signal** for flow structure and fixed-vs-fluid
sizing intent. It does **not** raise its own priority above the evidence the target skill
already ranks first — the rendered/visual evidence, the `style` values, and that skill's
existing layout policy and priority order stay authoritative. Use `figmaLayout` to
disambiguate structure and sizing when it agrees with that evidence, not to override it.

`figmaLayout` is intentionally absent on many nodes (the DSL trims hidden/merged nodes).
Absence just means fall back to visual + `style` — it does not mean "no layout".

## Container node → the flex container it becomes

- `layoutMode`: `HORIZONTAL` → `display: flex; flex-direction: row`; `VERTICAL` →
  `column`; `NONE`/absent → not an auto-layout container (children may be absolutely
  positioned via `constraints`).
- `primaryAxisAlignItems` → `justify-content` (`MIN`→`flex-start`, `CENTER`→`center`,
  `MAX`→`flex-end`, `SPACE_BETWEEN`→`space-between`).
- `counterAxisAlignItems` → `align-items` (`MIN`→`flex-start`, `CENTER`→`center`,
  `MAX`→`flex-end`, `BASELINE`→`baseline`).
- `itemSpacing` → main-axis `gap`; `counterAxisSpacing` → cross-axis gap when wrapping.
- `layoutWrap: WRAP` → `flex-wrap: wrap`.
- `paddingTop/Right/Bottom/Left` → `padding`.

## Child node → how it sizes/positions inside its parent's auto-layout

- `layoutSizingHorizontal` / `layoutSizingVertical`: `FIXED` → keep an explicit size;
  `HUG` → size to content (do **not** hardcode a bbox width; let content drive, e.g.
  `fit-content`); `FILL` → fill the parent along that axis (main axis: `flex: 1`; cross
  axis: `align-self: stretch` or `width: 100%`).
- `layoutGrow: 1` → `flex-grow: 1`.
- `layoutAlign`: `STRETCH` → `align-self: stretch`; `MIN`/`CENTER`/`MAX` →
  `align-self: flex-start`/`center`/`flex-end`.
- `layoutPositioning: ABSOLUTE` → this child is out of the auto-layout flow →
  `position: absolute`, anchored by `constraints` (`{ vertical, horizontal }`) against the
  positioned parent.

## How it relates to `style`

`style` remains the source for color, typography, and exact spacing/size values;
`figmaLayout` only informs flex structure and the fixed-vs-fluid distinction. When a
node's sizing is `HUG`/`FILL`, express it with flex and do not freeze it with a bbox
`width`/`height` copied from `style`.

## Unit handling

`itemSpacing`, `counterAxisSpacing`, and `padding*` are **raw Figma px**. Convert them per
the target skill's unit convention before writing (browser: `px`/`%`/`rem`; Lynx: `rpx` on
the design baseline) — never paste the raw number blindly. The sizing keywords
(`HUG`/`FILL`) are intent, not px values — express them with flex, never fixed sizes.
