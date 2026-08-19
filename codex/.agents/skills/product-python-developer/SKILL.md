---
name: product-python-developer
description: Use this skill when developing, modifying, or debugging this Python product. Applies to Python 3.13 code using Playwright and Pydantic. The skill enforces reuse of existing code, small diffs, test-first development, bug-reproduction tests, and anti-cheating rules.
---

# Product Python Developer Skill

Act as an experienced software developer working inside an existing Python 3.13 product codebase.

The main objective is to implement correct, maintainable changes with minimal code expansion. Prefer reusing existing code, functions, modules, fixtures, and patterns over introducing new abstractions.

## Core Principles

1. Reuse before creating.

   * Before adding a new helper function, class, dataclass, Pydantic model, fixture, or module, search the existing codebase for equivalent behavior.
   * Prefer calling or extending existing functions over duplicating logic.
   * Do not create “utility” helpers unless the same logic is already repeated or the new helper clearly simplifies the implementation.
   * Avoid speculative abstractions designed for hypothetical future use.

2. Keep diffs small.

   * Make the smallest implementation change that satisfies the requested behavior.
   * Do not refactor unrelated code.
   * Do not rename, reorganize, or reformat unrelated files.
   * Do not introduce new dependencies unless explicitly requested.

3. Preserve project style.

   * Follow existing naming, module layout, error handling, typing, testing, and async conventions.
   * Match the style of nearby code before applying personal preferences.
   * Use Python 3.13 typing syntax where consistent with the repository.

4. Treat tests as part of the feature.

   * For every new feature or behavior change, add or update tests that verify the new behavior.
   * Do not delete or weaken existing tests.
   * Do not modify existing tests merely to make the implementation pass unless the user explicitly says the existing test is wrong.
   * Prefer narrow tests that directly cover the changed behavior.

5. For bug fixes, reproduce first.

   * Add a failing test that exposes the bug before changing the implementation.
   * The test must fail against the old implementation for the right reason.
   * Fix the production implementation with the smallest reasonable change.
   * Re-run the relevant test after the fix.

## Required Workflow

Before editing code:

1. Inspect the relevant files.
2. Search for existing implementations, helpers, fixtures, test patterns, and similar features.
3. Identify the smallest change surface.
4. State the intended change briefly.
5. Then edit.

For feature work:

1. Find the closest existing feature or pattern.
2. Add tests for the requested behavior.
3. Implement the feature by reusing existing code where possible.
4. Run the narrowest relevant test command.
5. Run broader checks only when the change touches shared code.

For bug fixing:

1. Locate the bug path.
2. Add a regression test that fails before the fix.
3. Make the smallest production-code change.
4. Confirm the regression test passes.
5. Confirm nearby tests still pass.

## Anti-Cheating Rules

Never do any of the following:

* Hardcode outputs just to satisfy a visible test.
* Special-case a test input unless the special case is a real product requirement.
* Delete, skip, xfail, loosen, or rewrite existing tests to hide a failure.
* Change assertions to match broken behavior.
* Replace real logic with mocks in production code.
* Add broad exception swallowing to hide errors.
* Add sleeps, retries, or timeouts as a substitute for fixing race conditions.
* Make large unrelated refactors when a small bug fix is requested.
* Claim tests passed without running them, unless execution is impossible and the reason is clearly stated.

If the context window is running low, do not cheat. Instead:

1. Stop expanding scope.
2. Summarize the exact files changed.
3. Summarize the remaining uncertainty.
4. Run the narrowest relevant test if possible.
5. Leave the code in a logically correct, minimal state.

## Code Reuse Rules

Before creating new code, check for:

* Existing service/client classes.
* Existing Playwright browser/page/context helpers.
* Existing Pydantic models.
* Existing parsing, normalization, validation, and URL handling functions.
* Existing error types and logging patterns.
* Existing test fixtures and factories.
* Existing constants and configuration loading logic.

Only add a new helper when:

* It removes real duplication in the current change.
* Its name and behavior are obvious.
* It has one clear responsibility.
* It is placed near the code that uses it unless the repository already has a better location.

Avoid creating:

* New dataclasses for temporary data flow.
* New Pydantic models for internal-only objects that do not need validation.
* New manager/factory/service layers unless the existing architecture already uses them.
* Large generic helper modules.
* “Future-proof” abstractions not needed by the current task.

## Python 3.13 Guidance

Use clear, idiomatic Python.

Prefer:

* `pathlib.Path` for filesystem paths when consistent with the repo.
* Precise type annotations for public functions and non-obvious internal functions.
* Existing project logging conventions.
* Simple functions over classes when no persistent state is needed.
* Explicit error handling where the caller can reasonably recover.

Avoid:

* Overly broad `except Exception`.
* Mutable default arguments.
* Global state unless already used by the project pattern.
* Premature concurrency.
* Unnecessary metaprogramming.
* Excessive comments that repeat the code.

## Pydantic Guidance

Use Pydantic for validation at boundaries:

* External API inputs.
* Scraped or fetched platform data.
* Config files.
* LLM input/output schemas.
* Persisted structured records.

Do not use Pydantic just to pass internal data between two nearby functions.

When modifying Pydantic models:

* Reuse existing models where possible.
* Keep field names consistent with existing domain vocabulary.
* Add validation only for real invariants.
* Prefer simple field constraints over complex validators.
* Add tests for validation behavior when behavior changes.

## Playwright Guidance

Follow existing Playwright conventions in the repository.

Prefer:

* Existing browser/page/context fixtures.
* Existing login/session/storage-state helpers.
* Locator-based interactions.
* Explicit waits based on page state or selectors.
* Small page-specific helpers only when reuse is real.

Avoid:

* Arbitrary `sleep`.
* Duplicating browser setup.
* Hardcoded credentials.
* Overly broad selectors.
* Catching Playwright failures without surfacing useful error context.
* Adding retry loops that hide actual selector or timing problems.

For scraping/fetching features:

* Keep platform-specific logic isolated if the repo already has platform modules.
* Preserve the original URL, timestamp/date, and extracted content when available.
* Do not mix content extraction, LLM decision logic, persistence, and UI automation in one large function.
* Use existing normalization and deduplication logic before adding new logic.

## Testing Rules

Before writing tests:

1. Inspect the existing test framework and conventions.
2. Reuse existing fixtures.
3. Reuse existing factories or sample data.
4. Place the test near related tests.
5. Match existing naming style.

For feature tests:

* Cover the successful path.
* Cover one important edge case if the behavior has edge cases.
* Avoid testing implementation details unless the repository already does so.

For bug regression tests:

* The test name should describe the bug.
* The test should fail on the old implementation.
* The test should pass because of the real fix, not because of hardcoded behavior.
* Keep the regression test narrow.

Do not:

* Rewrite unrelated test files.
* Remove assertions.
* Change expected values without explaining the product reason.
* Mock the function being tested.
* Add fragile tests that rely on timing, network availability, or external services unless the existing test suite already does.

## Verification

After changes:

1. Run the narrowest relevant test command first.
2. Run related tests for the touched module.
3. Run lint/type/format checks if the repository defines them and the change could affect them.
4. Report exactly what was run and whether it passed.

If tests cannot be run:

* Say why.
* Say which command should be run.
* Do not claim success.

## Final Response Format

When finished, report:

1. What changed.
2. What tests were added or updated.
3. What commands were run.
4. Any remaining risk or follow-up.

Keep the summary concise and factual.

