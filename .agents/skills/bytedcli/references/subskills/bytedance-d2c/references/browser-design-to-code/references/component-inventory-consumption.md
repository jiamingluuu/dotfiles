# Component Selection & Usage (browser) — dynamic, DeepWiki-driven

This skill hardcodes **no** component list, routing table, or usage cards. Which library component realizes a pattern, and how to use it, is resolved **at runtime from DeepWiki** for whatever `packageName` the task targets. New components and new libraries need zero skill changes.

Component selection is specified by two orthogonal, binding layers:

- **Selection layer — `run-artifacts/component-inventory.json`** (produced upstream by visual segmentation): each region attributed to render-target-agnostic component **TYPES** (`TABLE, LIST, TABS, INPUT, SELECT, IMAGE, CAROUSEL, OVERLAY, TOOLTIP, CHECKBOX, RADIO, SWITCH, SLIDER, DATE_PICKER, FOLD, DESCRIPTIONS, BUTTON, TAG, STATIC`). This says WHICH kind of component, not which library component.
- **Behavior layer — `run-artifacts/interaction-inventory.json`** (+ `../interaction-recognition/references/interaction-target-mapping.md`): the runtime/completeness contract — repeated/`minRepeat` groups not truncated, tab/paged peers generated, real interactivity. Not a second selector.

They compose: `component=LIST` + `interaction=SCROLL/repeated/minRepeat 5` → use the library's list component AND render ≥5 data-driven rows, never 3 static ones.

## Resolving a TYPE to a concrete component (DeepWiki, at runtime)

For each region's `high` component-inventory TYPE, resolve the concrete component from the target `packageName` via `bytedcli deepwiki`:

```bash
# once per task: resolve + cache the collection for the target package
bytedcli --json deepwiki get-collection --package-name "<packageName>"
# per TYPE: find the component that realizes it, and its usage
bytedcli --json deepwiki search \
  --collection-name "<collection>" \
  --query "<TYPE 的自然语言描述，如 数据表格 / 可滚动列表 / 选项下拉 / 底部弹层> 组件 import props 用法 JSX 示例" \
  --limit 5
```

**Query by the TYPE's meaning, not a guessed component name** (e.g. TYPE=TABLE → query "数据表格/明细网格 组件"; TYPE=OVERLAY → "弹层/对话框/底部抽屉 组件"). Let DeepWiki return the package's actual component(s).

**Consume discipline**: DeepWiki results are evidence, not code. Distill each result into a usage-card shape — exact `import` statement, the props you will actually use, one minimal JSX sketch — and record it in the composition plan next to the region + its TYPE. A result with no usable import + props contract counts as a failed lookup.

**Budget**: at most 2 queries per TYPE and 8 per page; cache and reuse — do not re-query a TYPE already resolved.

**Missing-component reality**: if DeepWiki shows the package has no component for a TYPE (e.g. no dedicated table), pick the closest documented alternative it returns (a description/grid or list component) and record the substitution + reason in the composition plan.

**Fallback**: only when DeepWiki genuinely returns nothing usable for a TYPE — implement the nearest native browser semantic (scroll container, tablist+panel, input/textarea, button, overlay/dialog) and record it as a limitation. Never hand-roll a styled `div` in place of a component DeepWiki does surface.

## Enforcement (binding)

- **Selection**: every region `high` TYPE must be realized with a real library component resolved from DeepWiki (or a recorded substitution/limitation), referenced in the composition plan. `low` TYPEs are soft hints.
- **Allowlist brake** (the over-generation fix): a library component whose TYPE is not attributed to any region needs on-screen evidence recorded in the composition plan before you import it — this is what stops `Image`/`List` from being spammed into regions with no picture/rows.
- **Behavior**: each `high` interaction entry's runtime contract must hold — full repeated count (no truncation), hidden tab/pager peers generated, genuine interactivity.
- A missing/empty inventory degrades to best-effort and is reported as a validation weakness, never a block.

> Generalization: both inventories are target-agnostic, reusable layers, and selection+usage is fully dynamic. Browser uses this DeepWiki-driven path for any business library. Lynx today folds selection into its interaction→lynx-ui mapping because lynx-ui is its single known library; when Lynx needs packages beyond lynx-ui, it adopts this same dynamic selection path.
