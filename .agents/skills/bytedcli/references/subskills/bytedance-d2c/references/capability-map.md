# Upstream skill → bytedcli capability map

Authoritative mapping from the upstream plugin's skills to this namespace's capability guides. **Every upstream skill must appear exactly once**, so a new upstream skill cannot be silently dropped.

Enforced by `test/skills/bytedance-d2c-namespace.test.ts`, which fails when an entry is missing, unmapped, or points at a guide that does not exist.

## Provenance

This namespace was ported from the upstream Aiden D2C Agent plugin. Every capability
here is a `bytedcli` subcommand or your own reasoning, so there is nothing to install.
The pin below exists to keep the port auditable and upgradeable.

| | |
|---|---|
| Source of truth | `aidenD2C` monorepo, `packages/plugin_source/skills/` (readable, unminified) |
| Built artifact | https://code.byted.org/bytedance/aiden-d2c-plugin-codex |
| Plugin | `aiden-d2c` **1.1.0** |
| Pinned revision | `4bcbc425f0aed0e5f8283899e3c845bb180a30e1` (the repository publishes no tags, so the revision is the precise anchor) |
| Skills in `plugin_source` | 17 |
| Distributed downstream at the pinned revision | 13 |
| Mirrored in this namespace | **12** |

The version and revision are asserted by `test/skills/bytedance-d2c-namespace.test.ts`,
so they cannot drift silently. To refresh against a newer upstream: diff the upstream
skills at the new revision, port any behavioural change into the corresponding bytedcli
command and guide, then update this file and the test's pinned constants together.

### Credentials

- The ported commands authenticate with your own ByteCloud + Codebase SSO session — run `bytedcli auth login` once. There is no token flag for D2C REST access.
- The upstream scripts called the D2C endpoints **without any credentials**. The bytedcli commands are SSO-authenticated, so they are the safer route as well as the only supported one.
- Figma tokens are handled only where the backend genuinely requires one (segmentation task creation). A token is never written to disk, never logged, and never included in command output.
- The FaaS build/capture and image-compare host is deliberately served by a separate client that sends **no** ByteCloud or Codebase JWT, because that host does not need them.

## Mapping

This table records provenance only — it names each capability's directory rather
than linking its guide file. The namespace root guide is the single entry point
that routes to the guides; a reader arrives here from there. Naming the directory
also keeps this table correct in the generated `skills/bytedcli/` mirror, where
every `SKILL.md` is renamed to `GUIDE.md` but directory names are unchanged.

| Upstream skill | Capability directory | Delivery |
|---|---|---|
| `aiden-d2c-skills` | `aiden-d2c-skills/` | 🧠 Reasoning over ✅ CLI steps |
| `d2c-visual-segmentation` | `d2c-visual-segmentation/` | ✅ CLI |
| `interaction-recognition` | `interaction-recognition/` | 🧠 Reasoning (upstream ships no scripts) |
| `browser-design-to-code` | `browser-design-to-code/` | 🧠 Reasoning (upstream ships no scripts) |
| `lynx-design-to-code` | `lynx-design-to-code/` | 🧠 Reasoning + ✅ CLI validation |
| `d2c-render-screenshot` | `d2c-render-screenshot/` | ✅ CLI |
| `lynx-build-and-capture` | `lynx-build-and-capture/` | ✅ CLI |
| `d2c-evaluation-workflow` | `d2c-evaluation-workflow/` | ✅ CLI |
| `d2c-refine-workflow` | `d2c-refine-workflow/` | ✅ CLI guard + 🧠 Reasoning edits |
| `d2c-context-contract` | `d2c-context-contract/` | ✅ CLI validation + 🧠 Reasoning authoring |
| `get-figma-design-description` | `get-figma-design-description/` | ✅ CLI |
| `deepwiki-skill` | `deepwiki-skill/` | ✅ CLI via `bytedcli deepwiki` |

### ByteCLI-native Figma capabilities

The following capabilities wrap existing D2C APIs directly. They are not
additional upstream plugin skills, so they do not change the pinned 12-skill
provenance count above.

| Source API | Capability directory | Delivery |
|---|---|---|
| `buildFigmaIndex` | `build-figma-index/` | ✅ CLI |
| `searchFigmaGraph` | `get-figma-graph/` | ✅ CLI |
| `downloadIcon` | `download-icon/` | ✅ CLI |

Directory names and `SKILL.md` filenames are kept **1:1 with upstream**, and the
guidance prose is carried verbatim. Three kinds of edit are applied on top:

1. **Execution blocks** — upstream invokes bundled scripts, this namespace invokes
   the equivalent `bytedcli` command.
2. **Security and auth notes** — the upstream `settings.json` token-persistence
   mandate does not exist on the bytedcli route, so it is replaced by how tokens
   are actually resolved (see Credentials above). A few of these carry a short
   English restatement alongside the Chinese, so the repo's security guards in
   `test/skills/bytedance-d2c-namespace.test.ts` can assert them.
3. **Dead references** — links to upstream paths that were never distributed
   (e.g. a `tmp/` scratch doc) are dropped rather than mirrored as 404s.

Of the 17 skills in `plugin_source`, 4 are never distributed downstream at all
(`d2c-bench-artifacts`, `d2c-quality-diagnoser`, `d2c-trace-analyzer`,
`codex-trace-debugger`). They are upstream-internal tooling — Bench artifact
retrieval and evaluation-trace analysis — and are out of scope here.

### Deliberately excluded: `d2c-debug`

Upstream **does** distribute `d2c-debug` at the pinned revision, so the 13 → 12 gap is a
choice, not an oversight. It is excluded because its entire payload is two upstream
scripts (`retrieve_remote_artifacts`, `collect_local_artifacts`) that assemble a debug
bundle, and bytedcli has no equivalent command for either. Mirroring the guide without
them would document a capability that cannot actually run — the one thing this namespace
must never do.

The artifacts that guide collected are already reachable: `d2c task get` returns the task
status and download URL, `d2c segment create --wait --output-dir` downloads and unpacks
the products, and the validation, geometry, and evaluation reports are written to disk by
their own commands. What is missing is only the bundling step. If bundling turns out to be
worth a command, add it as one and mirror the guide then.

### Status polling is not a separate capability

Upstream bundles a `get_status.mjs` inside both `d2c-visual-segmentation` and
`d2c-render-screenshot`. In bytedcli both collapse into one
`bytedcli d2c task get --task-id <id> --kind <kind>` command, so the shared read
path is documented inside each of those two mirrored skills rather than split into
a separate directory — keeping the 1:1 mapping with upstream intact.

## Endpoint coverage

Which upstream HTTP calls bytedcli wraps today:

| Endpoint | Method | bytedcli command | Covered |
|---|---|---|---|
| `/api/D2C/getFigmaDescription` | POST | `d2c figma get-description` | ✅ |
| `/api/D2C/buildFigmaIndex` | POST | `d2c figma get` | ✅ |
| `/api/D2C/searchFigmaGraph` | POST | `d2c figma-graph get` | ✅ |
| `/api/D2C/visualSegmentation/{taskId}` | GET | `d2c task get --kind visual-segmentation` | ✅ |
| `/api/D2C/renderScreenshot/{taskId}` | GET | `d2c task get --kind render-screenshot` | ✅ |
| `/api/D2C/visualSegmentation` | POST | `d2c segment create` | ✅ |
| `/api/D2C/renderScreenshot` | POST | `d2c render create` | ✅ |
| `/api/D2C/getFigmaToken` | POST | (internal to `d2c segment create`) | ✅ resolution only — never exposed as a command, and the value is never printed or persisted |
| FaaS `pack-demo-builder`, `screenshot-capture` | POST | `d2c lynx-capture create` | ✅ separate host, no SSO credential sent |
| FaaS `image-compare` | POST | `d2c screenshot compare` | ✅ separate host, no SSO credential sent |
| `/api/D2C/reportEvaluationInvoke` | POST | — | ✗ plugin telemetry; deliberately not ported |
| `/api/D2C/reportRefineInvoke` | POST | — | ✗ plugin telemetry; deliberately not ported |
| `api.figma.com/v1/files/{key}/nodes` | GET | — | ✗ public Figma API, needs a user Figma token |

The read-only lookups share the D2C host with DeepWiki (`aiden-deepwiki.bytedance.net`) and reuse the same ByteCloud + Codebase JWT pair. The FaaS endpoints are served by a **separate client that sends no credentials at all**, because that host neither needs nor should receive the user's SSO tokens.

Job-creating commands (`segment create`, `render create`, `lynx-capture create`, `screenshot compare`) consume compute; the read-only and offline commands do not.

The upstream scripts also shipped several purely local validators and scorers with no HTTP at all. Those are ported as offline commands: `d2c lynx-page validate`, `d2c contract validate`, `d2c geometry evaluate`, `d2c refine-loop diagnose`, and `d2c style-contract create`.

## Deliberately not copied

The upstream tree carries ~7 MB of bundled scripts and ~530 KB of vendored component documentation. Neither is reproduced here:

- **Bundled build artifacts.** The plugin repository ships minified bundles (~3.5 MB each, embedding a whole TypeScript compiler). Those are not copied. The **readable sources** behind them live in the upstream monorepo under `packages/plugin_source/skills`, and it is those that were ported into `src/services/d2c/` — so the logic here is reviewable, diffable, and patchable.
- **The TSX AST component linter** is the one validator sub-check not ported: it needs the TypeScript compiler API at runtime, which would put a compiler in the bytedcli bundle for a single check. `d2c lynx-page validate` therefore reports `component_selection_status: "skipped"` while every other check runs normally — see the `lynx-design-to-code/` capability guide.
- **Vendored per-component documentation is now mirrored in full** (`lynx-design-to-code/references/components/**`, 49 files across 17 components, matching upstream exactly — note `button` ships `guide.md` only, with no `api.md` or `examples.md`). Earlier revisions of this map claimed the set was a stale snapshot and excluded it; that was inaccurate — spot checks show real content (`input/api.md` 244 lines, `dialog/examples.md` 757 lines). Four `examples.md` files are near-empty upstream (`input`, `image`, `view`, `text`), and several files embed internal CDN screenshot/video URLs and internal wiki links (`view-pager`, `video-engine`, `popup`, `tabs`, `fold-view`, `feed-list`, `svg`); those are carried verbatim to stay 1:1, so the assets stay reachable only from inside the corporate network. **One exception to the verbatim rule:** upstream's `video-engine/examples.md` carried a `videoModel` blob holding a live TOS-signed media URL (`x-tos-authkey` / `x-tos-signature`, expiry set to ~2060). Signing material is never mirrored — that blob is replaced with a placeholder, and `test/skills/bytedance-d2c-namespace.test.ts` now fails on any `x-tos-authkey` / `x-tos-signature` / `x-signature` / `key_seed` query parameter, so a future refresh cannot reintroduce one. DeepWiki remains the runtime fallback for anything not covered.
- **Invocation telemetry** (`reportEvaluationInvoke`, `reportRefineInvoke`) is deliberately dropped: per-invocation probes do not belong in a bytedcli request path.

This is a documented boundary, not an omission. Every capability is either a bytedcli command or explicitly model reasoning, so every route a caller can take is one they can run today.

## Adding a new upstream skill

1. Mirror the upstream skill directory verbatim as `references/<upstream-name>/SKILL.md` (keep the upstream `name` frontmatter).
2. Add its row to the mapping table above and to the `bytedance-d2c` root routing table.
3. Update the pinned revision in the Provenance table above.
4. Add the upstream skill name to `UPSTREAM_SKILLS` in `test/skills/bytedance-d2c-namespace.test.ts`.
5. Run `npm run build:assets` to regenerate the mirror under `skills/bytedcli/references/subskills/bytedance-d2c/`. **Never hand-edit the mirror.**

Step 4 is what makes the gate meaningful: the test cross-checks the upstream list against this table and the guides on disk, so skipping steps 1–3 fails the build rather than passing quietly.
