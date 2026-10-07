# Component Selection Routing — pick HOW a TYPE becomes a concrete component

The two inventory layers are fixed inputs: the **selection layer**
(`run-artifacts/component-inventory.json`, target-agnostic component TYPES,
produced upstream by visual segmentation) and the **behavior layer**
(`run-artifacts/interaction-inventory.json`, the runtime contract). What varies
per run is *how each selection-layer TYPE is resolved into a real library
component*. This document is the router that chooses that strategy. It never
overrides the behavior layer — whichever branch is taken, the
interaction-inventory contract still binds (no truncation, hidden tab/pager
peers generated, genuine interactivity).

## Input signal: business D2C context (`d2c_context/`)

Before routing, load the optional business context from the target repo's
working directory: the `d2c_context/` folder. Read **every** file
under it (recursively) and treat their concatenated contents as the business
context; if the folder is absent or empty, skip.
It is free-form markdown the business owner drops in to customize D2C for their
codebase, and typically declares any of:

- which component package(s) to target (e.g. `@ecom/auxo-mobile`) and reference paths;
- props / usage conventions specific to that library;
- whether the business has its **own** component-recognition capability the agent
  should call instead of resolving components itself, and how to invoke it.

Read it as evidence, not code. If the folder is absent or empty, route from the
ambient signals already in hand (`transformType`, `packageName`). Never print
sensitive paths from it verbatim in logs or chat.

## Route (first match wins)

### 1. Business self-built component recognition — when the context declares one

If `d2c_context/` declares that the business has its own component
recognition / selection capability (a command, service, or mapping the business
maintains), **defer to it**: invoke it as the context describes, and consume the
component mapping it returns in place of doing your own TYPE→component
resolution. The agent's job then is to honor that mapping while still satisfying
the behavior layer.

> Interface not yet standardized. This is a documented hook: follow whatever
> invocation the business context specifies. If the declared capability cannot be
> invoked or returns nothing usable, fall through to branch 2 (do not silently
> hardcode) and record the fallthrough in the composition plan.

### 2. DeepWiki dynamic resolution — the default for a business library (browser)

When the target is a business component library named by `packageName` (or by
`d2c_context/`) and there is no self-built recognition, resolve each
selection-layer TYPE to a concrete component **at runtime from DeepWiki**, per
`references/component-inventory-consumption.md`: `get_collection` for the
package, `search` each TYPE by meaning, distill the result into an
`import` + props + minimal JSX card recorded in the composition plan, apply the
allowlist brake. This skill hardcodes no routing table or usage cards — new
components and new libraries need zero skill changes. Any hints in
`d2c_context/` (preferred package, reference paths, props conventions)
sharpen the DeepWiki queries but do not replace them.

### 3. Fixed interaction→lynx-ui mapping + componentSelection gate — Lynx single-library

When the target is Lynx with no business-library requirement, selection folds
into the interaction→lynx-ui mapping owned by `lynx-design-to-code` (lynx-ui is
Lynx's single known library), gated by its `componentSelection` deterministic
check. No DeepWiki hop is needed. If a Lynx run *does* name a package beyond
lynx-ui (via `packageName` / `d2c_context/`), it adopts branch 2's dynamic
path for those components — the branches are symmetric, Lynx is just the common
case where selection collapses into one fixed library.

## Invariants across all branches

- The behavior layer (`interaction-inventory.json`) is never weakened by the
  chosen branch; its high-confidence entries are required.
- A missing/invalid/empty inventory degrades to best-effort and is reported as a
  validation weakness, never a block, and never a reason to emit inert static
  markup for visible tab/list/input/action/overlay patterns.
- Whatever branch resolves a component, the composition plan must record the
  concrete component + its source (self-built mapping / DeepWiki card / lynx-ui
  mapping) next to the region and its TYPE, so Verify can confirm every routed
  choice appears in the final code.
