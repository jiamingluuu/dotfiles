---
name: python-readable
description: "Write, edit, refactor, and review Python for readability and simplicity. Apply when implementing Python code or simplifying existing Python, especially to avoid unexplained numeric literals, trivial helper functions, passed lambdas, and speculative abstractions. Keep changes within the requested scope."
---

# Readable Python

Write Python that a reader can follow from top to bottom with few jumps between definitions. Optimize for understanding the actual task, not for the smallest line count or the largest number of reusable components.

## Start with the direct implementation

- Read the surrounding code and relevant project instructions. Respect existing public interfaces and supported Python versions.
- Implement the behavior requested now. Prefer ordinary functions, explicit arguments, familiar data structures, and existing library features.
- Keep related steps together. Use descriptive local variables and blank lines to separate stages before extracting helpers.
- Do not add a class, factory, registry, decorator, generic pipeline, configuration layer, or dependency solely for hypothetical future use. Introduce one only when a present requirement benefits from it.
- A little duplication is acceptable when the alternative couples unrelated behavior. Extract shared logic when it represents the same concept and should change together.
- Apply these preferences to code being written or changed. Do not turn a focused task into a repository-wide style rewrite.

## Give numbers meaning

- Name numeric values that encode policy, limits, timeouts, thresholds, protocol details, or non-obvious conversions. Reuse an existing named constant or library enum when available.
- Put units in names: `timeout_seconds`, `max_payload_bytes`, `distance_meters`. Explain the reason or source of a surprising value when known.
- Keep names near their use. Use a local variable for a local calculation and a module constant for a fixed shared policy. Do not introduce a settings object or user-facing option just to name a number.
- Keep obvious literals such as a zero initial count, a one-step increment, or a first-element index when their meaning is already clear. Naming every `0` and `1` makes code harder to read.
- Preserve existing values and units during cleanup. Do not invent a policy or guess what an unexplained value means; inspect its context first.

For an existing fifteen-minute idle timeout:

```python
# Before
if idle_seconds >= 900:
    disconnect()

# After
IDLE_TIMEOUT_SECONDS = 15 * 60

if idle_seconds >= IDLE_TIMEOUT_SECONDS:
    disconnect()
```

## Keep useful functions; remove trivial indirection

- Treat a function with fewer than five meaningful body lines as a review signal. Ignore comments, docstrings, blank lines, and formatting-only line breaks. This is a heuristic, not a minimum length requirement.
- Usually inline a private helper used once that merely forwards arguments, reads a field, wraps an obvious expression, or splits one continuous operation into fragments. Also consider whether an existing built-in already expresses the operation.
- Keep a short function when it names a non-obvious domain rule, centralizes a rule used in several places, provides a required callback or protocol method, or preserves a public interface. Its name or boundary should add understanding beyond its body.
- Do not create a helper solely to make its caller shorter or to unit-test a trivial expression. Test observable behavior at a useful boundary.
- Never pad a function, add redundant variables, or merge unrelated operations to reach five lines.
- Do not preserve a giant function just to avoid small helpers. Extract coherent responsibilities when doing so reduces nesting, separates side effects from substantial calculations, or makes a complex operation understandable.

## Prefer explicit flow over passed lambdas

- Avoid introducing lambdas as arguments or assigning them to variables. For ordinary transformation and filtering, prefer a simple comprehension or a direct loop over `map`/`filter` chains and callback pipelines.
- Use a comprehension for one straightforward transformation with an optional simple filter. Use a loop when there are several stages, branches, side effects, or error handling.
- When an API expects a callable, pass an existing function or method when it expresses the operation. For a simple field sort, standard helpers such as `operator.itemgetter` or `operator.attrgetter` can suffice.
- If the callback contains domain logic, use a meaningfully named `def`. A short callback is acceptable when the API needs it; do not build an adapter class or elaborate workaround to avoid a lambda.
- Do not introduce a higher-order API, closure, or callable parameter when a direct call would handle the current requirement.

For records whose `active` flag and `email` field are required:

```python
# Before: tiny helpers and callbacks obscure a single operation.
def is_active(user):
    return user["active"]


def clean_email(user):
    return user["email"].strip().lower()


def active_emails(users):
    return list(map(lambda user: clean_email(user), filter(is_active, users)))
```

```python
# After: selection, normalization, and collection are visible together.
def active_emails(users):
    emails = []
    for user in users:
        if not user["active"]:
            continue
        email = user["email"].strip().lower()
        emails.append(email)
    return emails
```

## Make the remaining code easy to follow

- Prefer domain names such as `pending_orders` over vague names such as `data`, `obj`, or `result` when a more specific meaning is known.
- Use early returns or `continue` to reduce nesting when the flow stays clear. Expand nested conditional expressions and dense comprehensions into ordinary statements.
- Keep state and dependencies explicit. Avoid hidden mutation, unnecessary mutable globals, reflection, and dynamic dispatch for a fixed set of straightforward cases.
- Add type annotations where they clarify inputs, outputs, or a confusing data shape, following project conventions. Avoid elaborate generics or protocols for a single concrete implementation.
- Comments should explain intent, constraints, or surprising behavior. Do not narrate obvious statements or require a docstring for every tiny private function.
- Validate at real input boundaries and catch exceptions where recovery or useful context is possible. Avoid broad catch-and-continue blocks, silent fallback values, and speculative defensive checks that hide errors.
- Preserve return types, ordering, laziness, exceptions, side effects, and distinctions such as `None` versus an empty value when simplifying existing code. A shorter implementation is not an improvement if it changes the contract accidentally.

## Review before finishing

Read the changed code as a maintainer would. Resolve these questions without producing a separate report unless requested:

- Can the main path be followed without jumping through trivial helpers?
- Does each short function, callback, class, and abstraction have a concrete purpose now?
- Are meaningful numeric values named, with units clear, while obvious literals remain readable?
- Could a direct statement, existing function, or loop replace a passed lambda or unnecessary layer?
- Did the cleanup preserve behavior and stay within scope?

Run the relevant project checks for the change. For a refactor, use existing tests and add focused coverage only for a meaningful uncovered behavior; do not create tests that enforce line counts or mirror private helpers. Do not add lint plugins or automated bans for these preferences unless requested.
