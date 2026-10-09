---
name: code-refactoring
description: |
    Refactor small, messy source code (1-4 classes/files, up to ~400 lines each, in .py/.cpp/.rs) into clean, readable code — primarily by flattening nested if-else and for statements, clarifying conditions, and improving names. Use this skill whenever the user asks to refactor, clean up, simplify, untangle, de-nest, or improve the readability of code, or describes code as messy / deeply nested / hard to follow / full of duplicated conditions or unclear names, even if they never say the word "refactor". This skill is strongly biased toward simple, local, in-place transformations and AGAINST over-engineering\: do NOT introduce helper functions, dataclasses, structs, classes, traits, or type aliases unless they are genuinely warranted.
---

# Code Refactoring

Turn tangled code into code a person can read top-to-bottom and understand without jumping around. Scope is intentionally small — usually 1–4 classes or files, each up to ~400 lines. Cleanliness here means **reader locality and flatness**, not abstraction count.

## The rule that overrides everything else

A reader should understand each function by reading it straight down, without chasing definitions elsewhere. Every helper function, dataclass, struct, trait, or type alias you add is a place the reader must navigate *to* — a tax. Only pay that tax when it clearly buys more than it costs.

So the default move is **flatten the code where it sits**, not extract it. When two solutions are equally readable, pick the one with fewer named things and fewer locations involved. Before reaching for a new abstraction, ask: "Can a guard clause, a named local variable, or a `continue` get me there instead?" Usually it can. A refactor that replaces deep nesting with a swarm of one-line helpers has failed.

**Prefer:** fewer nesting levels · clearer names · simpler control flow · local variables that explain intent · obvious data flow · small, behavior-preserving edits.
**Avoid:** unnecessary abstraction · excessive helpers · new types without strong need · type aliases that hide simple types · premature generalization · large rewrites when local reshaping is enough.

## Operating rules (the contract)

1. Preserve behavior exactly unless the user explicitly asks for changes.
2. Keep scope local to the requested files/classes/functions. Don't refactor unrelated nearby code "for consistency."
3. Don't change public APIs, or rename stable public symbols, unless explicitly requested.
4. Don't introduce new frameworks, design patterns, or architectural layers.
5. Don't aggressively extract helpers, and don't create dataclasses/structs/classes/traits/interfaces/type aliases unless they materially simplify the code.
6. Keep any necessary helpers near their call sites, in the same file/class.
7. Prefer readable names over comments that explain unclear names.
8. Preserve existing error handling, logging, metrics, tracing, ownership, concurrency, and resource-lifetime behavior unless explicitly asked to improve them.
9. Refactor incrementally; validate after each meaningful change. Keep the diff small and reviewable.
10. Never silently delete an edge case.

## Workflow

**1. Understand current behavior first.** Read the whole region before editing. Note: responsibility, inputs/outputs, mutable state, side effects, error paths, early returns, loop invariants, logging/metrics, ownership/lifetime, and any concurrency/async. For complex code, briefly summarize the behavior before changing it.

**2. Pick the smallest useful target.** Common problems: deep nested `if/else`; loop bodies doing too much; unclear names; duplicated conditions; ambiguous boolean flags; long multi-phase functions; mixed validation/transformation/side-effects; magic constants; hidden mutation; murky error handling.

**3. Apply the ladder below**, climbing only as far as you need.

**4. Verify behavior is unchanged** (see "Finishing").

## The refactoring ladder

Each rung is more invasive than the last. Most messy code is fixed entirely by rungs 1–4.

### 1. Guard clauses / early exit — the primary tool

Replace nested `if`/`else` with early `return`, `continue`, or `break`. Invert the condition, bail out, and keep the happy path at the lowest indentation. Remove the `else` after any `return`/`continue`/`break`/`throw`.

```cpp
// Before — nested, happy path buried
if (user) {
  if (user->active()) {
    process(*user);
  } else {
    return Error("inactive user");
  }
} else {
  return Error("missing user");
}

// After — flat, reads as a checklist
if (!user)            return Error("missing user");
if (!user->active())  return Error("inactive user");
process(*user);
```

Same idea inside loops, using `continue`:

```cpp
for (const auto& item : items) {
  if (!item.enabled())            continue;
  if (item.score() < min_score)   continue;
  results.push_back(BuildResult(item));
}
```

### 2. Name a complex condition with a local variable

When a condition is hard to read, assign it to a well-named local. This documents intent and stays completely local — no jumping required. Prefer this over a one-line helper.

```python
has_valid_score   = score is not None and score >= min_score
is_allowed_region = region in allowed_regions
if not has_valid_score or not is_allowed_region:
    return None
```

### 3. Simplify boolean logic and consolidate branches

Apply De Morgan's laws, drop double negatives, and remove dead/unreachable branches. Lift code that is identical across `if` and `else` out of the conditional, keeping only the real difference explicit:

```python
# Before
if mode == "fast":
    connect(); run(timeout=1);  cleanup()
else:
    connect(); run(timeout=10); cleanup()
# After
timeout = 1 if mode == "fast" else 10
connect()
run(timeout=timeout)
cleanup()
```

### 4. Replace a long if-else chain with a clean dispatch

When an `if/elif/else` chain is really a mapping from value to result, use `match`/`switch` or a literal lookup. Only when the mapping is genuinely flat and uniform — don't force it.

```rust
// Before: nested if-let
fn lookup(map: &HashMap<String, i32>, key: &str) ->[118;1:3u i32 {
    if let Some(v) = map.get(key) {
        if *v > 0 { *v } else { 0 }
    } else { 0 }
}
// After
fn lookup(map: &HashMap<String, i32>, key: &str) -> i32 {
    match map.get(key) {
        Some(v) if *v > 0 => *v,
        _ => 0,
    }
}
```

### 5. Use a language iteration idiom — only when it shortens *and* clarifies

A `for`-append loop often becomes a single comprehension / iterator chain. Do it when the result is plainly clearer; keep the loop when it isn't.

```python
result = [x.name for x in data if x.enabled]   # was: empty list + for + if + append
```

Stop there. Nested comprehensions, comprehensions with side effects, or long iterator chains are *harder* to read than the loop — and harder to debug. If branching or named intermediate values would help, keep the explicit loop. If you can't read it aloud in one breath, it's gone too far.

### 6. Extract a helper function — last resort, high bar

See the next section. Reaching this rung should be rare.

## When a helper / new type is justified

**Extract a function** only when at least one is clearly true: the same logic is repeated; the block has a clear, nameable responsibility that hides the main flow; or it is long enough (rough threshold: well over ~15–20 cohesive lines) that naming it improves comprehension. Even then, keep it in the same file/class, adjacent to its caller, with a name that states intent (`IsEligibleForRanking`, not `CheckItem`).

**Do NOT extract** when: the body is one or two obvious lines; the name would just restate the code; the reader must jump away to follow essential local logic; it takes many parameters; or it's used once and doesn't simplify the caller. A vague name that hides important business rules (`if (CanProcess(x))`) is worse than the inline checks it replaces.

**Introduce a struct/dataclass/enum/type alias** only when the same group of fields travels together repeatedly, forms a real domain concept, or the current loose tuples/parallel arrays cause bugs. Bad reasons: "clean architecture," making code look formal, wrapping two variables used once, or aliasing a primitive to avoid passing two parameters.

```rust
// Fine — used once, just read the values
let min_score = config.min_score;
let max_count = config.max_count;
// Over-engineered unless RankingLimits is a reused, real concept
```

## Function length

Don't blindly minimize length. A linear, easy-to-scan, locally-understandable function with clear phases is fine even at 60–70 lines — better than a 25-line function that delegates to six unclear helpers. Consider splitting only when a function holds several *independently* understandable phases (validate → prepare → process → emit), and even then prefer blank lines and a short comment per phase before extracting.

## Naming

Improve names aggressively when they obscure intent. A good name answers: what is this value, why does it exist, what decision/domain concept does it encode. Replace vague names (`flag`, `tmp`, `data`, `res`, `val`, `obj`, `check`, `process`, `handle`) with intent-revealing ones (`should_skip_user`, `normalized_score`, `eligible_items`). Do not rename stable public symbols without explicit permission.

## Comments

Prefer self-explanatory code. Keep comments that explain the non-obvious: business rules, surprising edge cases, performance choices, concurrency/ownership constraints, compatibility behavior, or why something intentionally looks unusual. Delete comments that merely restate the code (`// increment i`).

## Error handling

Preserve the existing style. Do not convert return codes ↔ exceptions, nullable ↔ `Result`, or logging-only errors ↔ hard failures unless asked. When cleaning it up: make error paths visible, keep messages specific, don't swallow errors, and don't change retry/fallback, logging, or metrics behavior.

## Language-specific notes

**Python** — *Prefer:* early returns; named local booleans; `any()`/`all()`; `enumerate`/`zip` over index juggling; `dict.get(k, default)`; single-level comprehensions when readable; explicit loops when logic branches. *Avoid:* unnecessary dataclasses; excessive decorators; clever one-liners; deeply nested comprehensions; dynamic tricks; broad module restructuring.

**Rust** — *Prefer:* the `?` operator and `let ... else { return }` / `if let` to flatten `Option`/error handling; `match` (with guards) over `if/else if` chains; short, linear iterator adapters (`filter`/`map`/`find`); clear borrowing. *Avoid:* new traits or generics for local cleanup; overusing type aliases; changing ownership to satisfy a refactor; cloning to dodge the borrow checker without justification.

**C++** — *Prefer:* guard clauses; `const` locals; references over needless copies; range-based `for`; structured bindings (`auto [k, v] : map`); a single `std::any_of` / `std::ranges::find_if` when clearly shorter; RAII-preserving edits. *Avoid:* template abstractions for local cleanup; unnecessary type aliases; clever iterator chains; macro-based refactoring; any hidden change to ownership or lifetimes.

## Anti-patterns — do NOT do these

- **Tiny-helper explosion:** several single-use one-liner helpers (`is_valid_user`, `has_valid_score`, …) when inline reads fine.
- **Premature domain modeling:** a `ProcessingContext` dataclass/struct for values used in one short function.
- **Abstracting before understanding:** introducing a strategy/visitor/builder/factory/registry/"engine" to clean a small function.
- **Hiding important logic** behind a vague helper name the reader needs to see.
- **Overusing functional style:** `list(map(transform, filter(lambda x: ..., items)))` when an explicit loop with named intermediates is clearer and debuggable.
- **Cosmetic churn:** reformatting or renaming things that were fine, bloating the diff.
- **Refactoring across boundaries** the user didn't ask about.

## Finishing

- **Verify behavior is unchanged.** Run existing tests if any exist. If none exist, walk through edge cases yourself: empty/single/duplicate/invalid input, `None`/null/optional-missing values, boundary values, and every branch you collapsed. Add focused tests only if the refactor exposes an untested edge case and that's in scope.
- **Watch guard-clause ordering.** Reordering early-return checks can change behavior when a condition has side effects or when one check must precede another (a null check must come before any field access; short-circuit order matters). Preserve the original evaluation order and semantics.
- **Confirm preserved side effects:** logging, metrics, counters, retries, and performance-sensitive loops not made obviously worse.
- Re-read the result top-to-bottom. If you still must scroll or jump to definitions to follow the main path, keep flattening — and if you added an abstraction you can't justify by the bar above, remove it.

## Review checklist

Behavior preserved? · Main flow easier to read? · Nesting reduced? · Names clearer? · Helpers necessary and well-named? · No unjustified new types? · No broad architectural changes? · Understandable mostly in one place? · Edge cases still handled? · Logs/metrics/side effects intact? · Diff small and reviewable?

## Codex prompt template

```text
Refactor the selected code for readability while preserving behavior.

Scope:
- Only modify the selected file/function/class unless a tiny adjacent change is necessary.
- Do not change public APIs.
- Do not introduce new classes, structs, dataclasses, traits, interfaces, or type aliases unless strongly justified.
- Do not aggressively extract helper functions.
- Prefer local control-flow cleanup, guard clauses, clearer names, and reduced nesting.
- Keep important business logic close to where it is used.
- Preserve logging, metrics, error handling, side effects, ownership, and concurrency.

Goals:
- Reduce nested if/else and loop complexity; make the happy path obvious.
- Name complex conditions with local variables; remove redundant else after return/continue/break/throw.
- Optimize for reader locality — understandable in one pass.

Before editing: briefly summarize current behavior, name the main readability problems, and state the minimal plan.
After editing: summarize what changed, explain why behavior is preserved, and note tests/checks to run.
```

When in doubt, choose the refactor that makes the code easiest to read in one pass. Optimize for local clarity, stable behavior, and reviewable diffs — never for cleverness, abstraction, or minimal line count.
