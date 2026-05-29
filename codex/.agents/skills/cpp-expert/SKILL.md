---
name: modern-cpp
description: Write, review, refactor, or modernize C++ code (C++17 and later) to be clean, readable, idiomatic, and maintainable. Use this skill whenever the task involves writing new C++, reviewing or cleaning up existing C++, porting older C++98/03/11 code forward, designing C++ APIs or module boundaries, choosing between language/library features, applying a code-review checklist, or answering "what's the idiomatic way to do X in C++". Trigger it even when the user doesn't say "best practices" explicitly — any time C++ source is being produced or judged, prefer these conventions. Optimizes for clarity and correctness first; performance is welcome but never at the cost of readability unless the user asks.
---

# Modern C++ (C++17)

A guide for writing C++ that is explicit, safe, readable, and easy to maintain. The target standard is **C++17**, so every feature below is available without C++20/23. Where a C++20 feature would be the "real" answer, this guide gives the best C++17 substitute and says so. Where a type is library-specific rather than standard (e.g. `Status`/`StatusOr`), that is called out.

## Core principles

Optimize in this order: **correct → clear → fast**. Code is read far more often than it is written, so the most expressive, hardest-to-misuse version is the best version. Prefer simple designs over clever abstractions. Performance matters, but reach for a hand-tuned optimization only when a profiler — not intuition — says the code is on a hot path.

Good C++17 code:

- Makes ownership explicit and uses **RAII** for every resource (memory, file, lock, socket).
- Prefers **value semantics**: types that behave like values, with no hidden sharing.
- **Expresses intent in the type system** — `std::optional<T>` says "maybe absent," `std::unique_ptr<T>` says "I own this," `std::string_view` says "I observe but don't own." Let types carry meaning so the reader doesn't reconstruct it.
- Keeps APIs small and intention-revealing, and makes invalid states hard to represent.
- Separates business logic from infrastructure, and validates external input at the boundary.
- Uses standard-library facilities before custom utilities.
- Optimizes only when profiling or a clear constraint justifies it.

> **Project convention — prefer references to pointers.** When a function observes an argument it does not own, take it by reference (`T&` / `const T&`), never by raw pointer. A reference cannot be null and cannot be accidentally rebound, so it is the safer, more honest default. Reach for a pointer only when you need something a reference genuinely cannot provide — rebinding to a different object over time, or representing "no object at all" — and even for absence, prefer `std::optional` (or `std::optional<std::reference_wrapper<T>>`) over a raw pointer. Owning raw pointers are never the right tool (see §3).

---

# Patterns — idioms to reach for

## 1. RAII for resource management

Resources are acquired and released by object lifetime. Cleanup becomes automatic and exception-safe, and callers never have to remember to call `close()`, `release()`, `unlock()`, or `cleanup()`.

```cpp
std::lock_guard<std::mutex> lock(mu);             // unlocks on scope exit
std::unique_ptr<Foo> foo = std::make_unique<Foo>();
std::ifstream input(path);                         // closes on scope exit
```

Wrap your own resources the same way — acquire in the constructor, release in the destructor:

```cpp
class Timer {
public:
    explicit Timer(std::string name) : name_(std::move(name)) {}
    ~Timer() { /* record elapsed time */ }
private:
    std::string name_;
};
```

## 2. Value semantics and explicit ownership

Use ordinary values when ownership is simple — they copy, compare, and clean up correctly with no indirection to reason about.

```cpp
struct UserProfile {            // good — owns its data, value semantics
    std::string user_id;
    int age = 0;
    std::vector<std::string> tags;
};
```

Make ownership legible at a glance:

```cpp
Foo value;                    // owned directly
std::unique_ptr<Foo> foo;     // exclusive ownership
std::shared_ptr<Foo> foo;     // shared ownership — use sparingly
const Foo& foo;               // read-only, non-owning, non-null borrow
Foo& foo;                     // mutable, non-owning, non-null borrow
Foo* foo;                     // ONLY when rebinding or null is genuinely required (see convention above)
```

## 3. Smart pointers — pick the weakest tool that works

- `std::unique_ptr<T>` — the default for owning a heap object. One owner, zero overhead, movable not copyable.
- `std::shared_ptr<T>` — only when ownership is genuinely *shared* with no clear dominant owner. It has real costs (atomic refcount, larger size). Don't reach for it just because lifetime feels hard.
- `std::weak_ptr<T>` — breaks `shared_ptr` cycles; expresses "I observe this, I don't keep it alive."

Prefer `std::make_unique` / `std::make_shared` over `new`: exception-safe, and `make_shared` does a single allocation. **Never write naked `new`/`delete`** — manual memory management is the largest single source of leaks and use-after-free.

## 4. Special member functions: Rule of Zero, then Rule of Five

If your members are themselves RAII types (`std::string`, `std::vector`, smart pointers), declare **no** destructor, copy, or move operations — the compiler-generated ones are correct. This **Rule of Zero** is the default.

```cpp
class Config {                       // copy/move/destroy all correct, for free
    std::string name_;
    std::vector<int> values_;
    std::unique_ptr<Backend> backend_;  // makes Config move-only, which is correct here
};
```

Only when you must manage a resource by hand do you follow the **Rule of Five** — declare all five, and define them deliberately with `= default` / `= delete`:

```cpp
class NonCopyable {
public:
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;            // say exactly what you mean
    NonCopyable& operator=(const NonCopyable&) = delete;
    NonCopyable(NonCopyable&&) noexcept = default;       // movable
    NonCopyable& operator=(NonCopyable&&) noexcept = default;
};
```

Mark move operations `noexcept` when they can't throw — standard containers fall back to copying during reallocation if a move can throw.

## 5. Pass parameters by intent and cost

| Intent | How to pass |
|---|---|
| Read only, cheap to copy (`int`, small structs, `std::string_view`) | by value |
| Read only, expensive to copy | by `const T&` |
| Read-only string the function won't store | `std::string_view` |
| Mutate the caller's object | by `T&` |
| Take ownership ("sink") | by value, then `std::move` into place |
| May be absent | `std::optional<T>` (return) / overloads — **not** a raw pointer (see convention) |

```cpp
void readLarge(const std::vector<int>& xs);   // borrowed, read-only
void mutate(User& user);                       // borrowed, mutable
void takeOwnership(std::unique_ptr<Foo> foo);  // sink, owning

class User {                                    // setter/ctor that stores a copy:
public:
    void setName(std::string name) { name_ = std::move(name); }  // pass by value, move in
private:
    std::string name_;
};
```

**Return by value.** Guaranteed copy elision (C++17) and move semantics make it cheap. Don't return `const` values (it blocks moves), and never return a reference or pointer to a local.

## 6. `const` and `constexpr` correctness

Make things `const` by default; relax only when mutation is needed. `const` documents intent, prevents accidental writes, and enables optimization. Mark member functions `const` whenever they don't change observable state.

```cpp
void processUser(const User& user);
class Cache {
public:
    std::size_t size() const { return data_.size(); }
private:
    std::unordered_map<std::string, Value> data_;
};
```

Use `constexpr` for values and functions computable at compile time — it replaces `#define` constants and `enum` hacks with type-safe, scoped alternatives. Use `const` for ordinary runtime immutability.

```cpp
constexpr int kDefaultTimeoutMs = 100;
constexpr int square(int x) { return x * x; }  // usable at compile and run time
```

## 7. `auto` and structured bindings

`auto` is a readability tool, not a religion. Use it when it removes noise or prevents a subtle type mismatch; avoid it when the explicit type is the point of the line.

```cpp
auto it = users.find(id);                     // good — exact iterator type is noise
auto user = std::make_unique<User>("Ada");    // good — type is already on the right
FeatureValue value = getValue();              // better than auto when the type matters

for (const auto& [key, value] : my_map) { }   // structured bindings: clear and concise
auto [iter, inserted] = my_set.insert(x);     // unpack without .first/.second
```

Mind the qualifiers: `auto` strips `const` and `&`. Use `const auto&` to observe without copying, `auto&` to modify in place.

## 8. Vocabulary types: `optional`, `variant`, `string_view`

**`std::optional<T>`** for a value that may be absent — replaces magic sentinels (`-1`, empty string) and out-param-plus-bool.

```cpp
std::optional<User> findUser(std::string_view id);
if (auto user = findUser(id)) { greet(*user); }            // contextual bool, then deref
auto name = findUser("x").value_or(User{"guest"}).name;    // supply a default
```

**`std::variant<Ts...>`** for a closed set of alternatives — a type-safe tagged union that beats stringly-typed data or raw unions.

```cpp
using FeatureValue = std::variant<int64_t, double, std::string, std::vector<float>>;
std::visit([](const auto& v) { process(v); }, value);      // dispatch on the active type
```

**`std::string_view`** for read-only string parameters — accepts `std::string`, string literals, and substrings with zero allocation.

```cpp
bool hasPrefix(std::string_view text, std::string_view prefix);
```

**Lifetime caveat:** a view does not own its data. Never return one pointing at a local, and don't store one whose backing buffer may die first:

```cpp
class Foo {
public:
    explicit Foo(std::string_view name) : name_(name) {}  // BAD — may dangle
private:
    std::string_view name_;
};
// Safer: store a std::string and std::move into it.
```

## 9. C++17 language features worth using

- **`if`/`switch` with initializer** — scope a variable to the condition that uses it:
  ```cpp
  if (auto it = m.find(key); it != m.end()) { use(it->second); }
  ```
- **`if constexpr`** — compile-time branching that replaces tag dispatch and most SFINAE:
  ```cpp
  template <typename T>
  auto deref(T t) {
      if constexpr (std::is_pointer_v<T>) return *t;
      else return t;
  }
  ```
- **Class template argument deduction (CTAD)** — drop redundant template args: `std::lock_guard lock(m);`, `std::pair p{1, "x"};`.
- **Fold expressions** — collapse variadic packs cleanly: `return (args + ...);`.
- **Attributes** — `[[nodiscard]]` where ignoring the result is a bug (e.g. `empty()`, error codes), plus `[[maybe_unused]]` and `[[fallthrough]]`.
- **`std::filesystem`** — portable path/file operations; stop using platform APIs for this.

## 10. Standard algorithms and containers

Prefer named algorithms over hand-written loops *when the algorithm states intent more clearly* — but don't force one when a plain loop reads better.

```cpp
auto it = std::find(users.begin(), users.end(), target);
std::sort(items.begin(), items.end(),
          [](const Item& a, const Item& b) { return a.score > b.score; });

for (const auto& item : items) {                 // a clear loop is fine
    if (item.enabled && item.score > threshold) result.push_back(item.id);
}
```

- Iterate with **range-based for** unless you need the index.
- **Container defaults:** `std::vector` for almost everything; `std::array` for fixed size; `std::unordered_map`/`set` for hash lookup; ordered `map`/`set` when ordering matters. `std::vector` usually beats `std::list` on real hardware (cache locality).
- Prefer **`std::array<float, 128>`** over a C array `float[128]` — safer, and works with algorithms.
- Use `'\n'` rather than `std::endl` in loops; `std::endl` flushes every time.
- Use `std::size_t` for container sizes/indices, and avoid mixing signed/unsigned carelessly. If negative values are meaningful, use a signed type.

## 11. Model your data — strong types over loose primitives

**Group related fields into a struct** instead of parallel vectors sharing an index:

```cpp
struct UserRecord { std::string name; int age = 0; double score = 0.0; };
std::vector<UserRecord> users;                   // not three parallel vectors
```

**Give important concepts their own types** to kill parameter-order bugs and self-document:

```cpp
struct RetryPolicy { int timeout_ms = 100; int max_retries = 3; };
void update(UserId id, RetryPolicy policy, bool enabled);   // not (int, int, int, bool)
```

**Convert strings to typed representations at the boundary** rather than branching on raw strings everywhere:

```cpp
enum class FeatureType { FloatList, Int64List, String };
FeatureType type = parseFeatureType(raw_type);   // normalize once, then use the enum
```

## 12. Initialization

Prefer brace initialization (it forbids narrowing) and initialize at declaration. Use constructor initializer lists rather than assigning in the body. Know the one trap:

```cpp
std::vector<int> a(3);   // three elements, all 0
std::vector<int> b{3};   // ONE element with value 3 — initializer_list wins

class Foo {
public:
    Foo(std::string name, int count) : name_(std::move(name)), count_(count) {}  // init list
private:
    std::string name_;
    int count_ = 0;
};
```

## 13. Use `std::move` intentionally

Move only when you are deliberately giving up the current value. Don't `std::move` a local you're returning (it defeats copy elision), and don't read a moved-from object except to reassign or destroy it.

```cpp
auto name2 = std::move(name);
std::cout << name;   // BAD — moved-from, usually wrong
```

## 14. Lambdas

```cpp
auto byName = [](const auto& a, const auto& b) { return a.name < b.name; };  // generic lambda
```

Prefer **explicit captures** over `[=]`/`[&]` so lifetime and intent are visible. Capturing by reference into a lambda that outlives the captured object is a dangling-reference bug — watch lambdas stored in members, passed to async work, or returned.

## 15. Concurrency basics

Protect shared mutable state with an RAII lock — **`std::scoped_lock`** (C++17) locks one or several mutexes deadlock-free:

```cpp
std::mutex m;
{
    std::scoped_lock lock(m);   // released even on exception
    // critical section
}
```

Prefer higher-level tools (`std::async`, futures, a task queue) over hand-managed `std::thread`. The cleanest concurrent code shares as little mutable state as possible — pass data by value or through queues instead of sharing and locking.

---

# Design and architecture

## 16. Small, intention-revealing functions

A function should do one thing, have a name that says what, and usually fit on one screen. Split large functions by responsibility — not mechanically into meaningless helpers.

```cpp
bool isEligibleForRanking(const User& user, const RequestContext& ctx);  // good
void handle();  void process();  void doStuff();                         // vague — avoid
```

Keep the happy path flat with **guard clauses** instead of deep nesting:

```cpp
if (!a) return;
if (!b) return;
if (!c) return;
doWork();
```

## 17. Composition over inheritance

Use inheritance for stable runtime polymorphism behind an interface — not to reuse code. Prefer composing collaborators:

```cpp
class FeatureService {
public:
    FeatureService(FeatureComputer computer, FeatureCache cache)
        : computer_(std::move(computer)), cache_(std::move(cache)) {}
private:
    FeatureComputer computer_;
    FeatureCache cache_;
};
```

A polymorphic base needs a **virtual destructor**; mark overrides `override` (catches signature mismatches) and `final` where further overriding is wrong. Keep data members `private`; avoid `protected` data.

```cpp
class Operator {
public:
    virtual ~Operator() = default;
    virtual Status run(Context& ctx) = 0;
};
class MyOperator : public Operator {
public:
    Status run(Context& ctx) override;
};
```

## 18. Make constructors `explicit`

Single-argument constructors should usually be `explicit` to prevent surprising implicit conversions:

```cpp
class UserId {
public:
    explicit UserId(std::string value) : value_(std::move(value)) {}
private:
    std::string value_;
};
```

## 19. Design APIs around invariants

A good API makes invalid states hard to represent, so callers stop re-checking the same conditions:

```cpp
class NonEmptyString {
public:
    static std::optional<NonEmptyString> create(std::string value) {
        if (value.empty()) return std::nullopt;
        return NonEmptyString(std::move(value));
    }
    const std::string& value() const { return value_; }
private:
    explicit NonEmptyString(std::string value) : value_(std::move(value)) {}
    std::string value_;
};
```

Replace ambiguous boolean parameters with an options struct (designated initializers are C++20; in C++17, name the fields):

```cpp
struct RunOptions { bool enable_cache = true; bool dry_run = false; };
RunOptions options; options.enable_cache = true;
runJob(options);                 // not runJob(true, false);
```

## 20. Validate at boundaries; separate parse / validate / execute

Validate external input (config, requests, files, env vars, RPC, user IDs) near the system boundary. Afterward, internal code operates on typed, trusted objects instead of re-checking raw input. Keep the stages distinct so failures are easy to locate and test:

```cpp
StatusOr<RawConfig> parseConfig(std::string_view text);   // Status/StatusOr are library
StatusOr<Config>    validateConfig(const RawConfig& raw); // types (e.g. Abseil), not std
Status              execute(const Config& config);
```

## 21. Clean module boundaries and header hygiene

Expose a small public interface; keep implementation in `.cc` files. Use forward declarations and include the real header only in the source file — this cuts build time and coupling. Don't rely on transitive includes: if a file uses a type, include its header directly. Group code in domain namespaces rather than the global namespace.

```cpp
// foo.h
class Bar;                       // forward declaration
namespace project::feature {
class Foo {
public:
    void useBar(const Bar& bar);
};
}  // namespace project::feature
```

## 22. Inject dependencies; avoid global mutable state and hidden side effects

Pass collaborators in rather than reaching for globals — this makes code testable, deterministic, and concurrency-friendly. A function should not silently mutate unrelated state.

```cpp
// Hard to test — hidden global + clock dependency:
Feature computeFeature();
// Testable — dependencies explicit:
Feature computeFeature(const RequestContext& ctx, const Config& config,
                       std::chrono::system_clock::time_point now);

// Hidden side effect (BAD): mutates a global cache as a surprise.
// Prefer making it explicit:
Feature getOrComputeFeature(const Request& req, FeatureCache& cache);
```

## 23. Avoid premature abstraction and god classes

Write the concrete code first; introduce templates, inheritance hierarchies, or factories only when multiple real use cases share stable structure. Watch for "god class" smells: too many unrelated fields/methods, vague names (`Manager`, `Handler`, `Processor`, `Helper`), tests that need heavy setup, and small changes that keep touching the same big class. Split by responsibility.

---

# Error handling

Pick **one dominant error style per module** and don't mix many in one layer:

- `std::optional<T>` — absence is expected and simple.
- An error-code/`Status` enum — operation succeeded or failed. *(`Status`/`StatusOr<T>` are library types, e.g. Abseil — not standard C++17.)*
- Exceptions — for failures a caller usually can't handle locally and shouldn't check on every call. Throw by value, **catch by `const&`** (catching by value slices), and never let an exception escape a destructor.

Handle known failures explicitly — never swallow errors with an empty `catch (...)`:

```cpp
try {
    doWork();
} catch (const ConfigError& e) {       // specific, logged, mapped to a result
    logError(e.what());
    return Status::InvalidConfig;
}
```

Mark functions `noexcept` only when they truly cannot throw (especially moves and `swap`).

---

# Anti-pattern quick reference

Replace the left with the right:

| Anti-pattern | Use instead |
|---|---|
| `new` / `delete`, owning raw pointers | `unique_ptr` / `make_unique`, RAII |
| Raw pointer for non-owning, non-null argument | a reference (`T&` / `const T&`) |
| `shared_ptr` as the default pointer | `unique_ptr` by default; share only when truly shared |
| `using namespace std;` in a header or global scope | qualify (`std::`), or a narrow `using` inside a function |
| C-style cast `(T)x` | `static_cast` / `const_cast` / `reinterpret_cast` (named, searchable) |
| `NULL` or `0` for pointers | `nullptr` |
| `typedef` | `using` (reads left-to-right, works with templates) |
| `#define` constants / function-like macros | `constexpr`, `inline` functions, templates |
| Plain `enum` | `enum class` |
| C arrays / raw buffers | `std::array`, `std::vector`, `std::string` |
| Out-parameters to return data | return by value (struct / `optional` / `tuple`) |
| `-1` / empty / sentinel "no value" | `std::optional` |
| Stringly-typed logic (`if (type == "float_list")`) | `enum class`, parsed at the boundary |
| Parallel vectors sharing an index | one `struct`, one `vector` |
| Boolean-parameter soup (`runJob(true, false)`) | an options struct with named fields |
| Deep nested `if`s | guard clauses / early returns |
| `catch (...) {}` swallowing errors | catch specific types; log and propagate |
| Global mutable state / gratuitous singletons | inject dependencies explicitly |
| Returning a reference/pointer to a local | return by value (RVO + move) |
| `std::endl` in a loop | `'\n'` |
| Premature abstraction / god classes | concrete code first; split by responsibility |

---

# Performance, kept in proportion

Prefer clear code by default; optimize only where the code is proven hot or a constraint is obvious — and **document why**:

```cpp
// On the request hot path: avoid extra allocations here.
std::string serializeFeatureVector(const std::vector<float>& values);
```

High-value, low-cost habits: pass expensive objects by `const&` (or `string_view`); `reserve()` a `vector` when the final size is known; lean on move semantics and copy elision (don't fight them); avoid repeated hash lookups; prefer contiguous storage; avoid heap allocation in tight loops. Don't reach for `shared_ptr`, `std::function`, or virtual dispatch when a simpler value type or template will do.

```cpp
std::vector<Result> results;
results.reserve(inputs.size());                 // intent + fewer reallocations
for (const auto& input : inputs) results.push_back(process(input));
```

**Measure before optimizing.** Clear code a profiler later flags is easy to speed up; clever code written on a hunch is hard to read and often isn't faster. When in doubt, choose the version a teammate will understand at 2 a.m.

---

# Style and project conventions

## Naming

Consistency matters more than the specific scheme. A workable convention:

- Types: `PascalCase` — `FeatureComputer`, `RetryPolicy`
- Functions: `camelCase` — `computeFeature()`, `isEnabled()`
- Variables: `snake_case` — `retry_count`, `user_id`
- Private members: trailing underscore — `cache_`
- Constants: `kCamelCase` — `kMaxRetryCount`
- Enum values: `PascalCase` — `Status::InvalidInput`

## File organization and includes

Header exposes the interface; source holds the implementation. Use `#pragma once`, wrap in a domain namespace, and order includes: the matching header first, then standard library, then project/third-party — each group sorted.

```cpp
#include "feature_computer.h"   // 1. matching header

#include <memory>               // 2. standard library
#include <string>
#include <vector>

#include "project/foo.h"        // 3. project / third-party
```

## Comments

Comments explain **why**, not **what** — capture the rationale, the invariant, or the gotcha:

```cpp
// Some upstream configs still emit empty feature names. Keep this guard until
// the migration to typed configs lands.
if (feature_name.empty()) return Status::InvalidArgument("empty feature name");
```

## Logging

Logs should say what happened, where, and include key identifiers — without flooding tight loops or leaking sensitive data:

```cpp
LOG(INFO) << "Loaded feature graph node_count=" << graph.nodeCount()
          << " edge_count=" << graph.edgeCount();
```

---

# Testing

Write tests for normal, boundary, invalid, empty, and large inputs; for ownership/lifetime-sensitive behavior; and as regressions for fixed bugs. Prefer small unit tests for pure logic and integration tests at module boundaries. Name tests after the behavior they pin down:

```cpp
TEST(FeatureParserTest, RejectsEmptyFeatureName)
TEST(FeatureComputerTest, ReturnsEmptyVectorWhenNoOperatorsAr[27;1:3ueEnabled)
```

Deterministic, dependency-injected code (see §22) is what makes these tests simple and reliable.

---

# Code review checklist

Before submitting, check:

- Is ownership clear, and are lifetimes safe?
- Are names specific and intention-revealing?
- Are functions small enough to understand at a glance?
- Are errors handled explicitly (no silent `catch (...)`)?
- Is external input validated at the boundary, then trusted internally?
- Are unnecessary copies avoided; references preferred over pointers?
- Are headers minimal (forward declarations, direct includes)?
- Are abstractions justified by real, repeated use?
- Are tests added for meaningful behavior and regressions?
- Are logs useful but not noisy, and free of sensitive data?
- Is any performance optimization necessary, local, and documented?
- Could a simpler design solve the same problem?

---

# Summary

Prefer clear, typed, RAII-based C++17. Make ownership explicit (values first, `unique_ptr` next, `shared_ptr` rarely), prefer references over pointers, and let the type system carry intent with `optional`, `variant`, `string_view`, and strong types. Keep functions and APIs small, validate at boundaries, inject dependencies, and keep modules and headers clean. Avoid global mutable state, manual memory management, hidden side effects, stringly-typed logic, and speculative abstraction. Optimize only where it matters — and keep that code localized, documented, and tested.

