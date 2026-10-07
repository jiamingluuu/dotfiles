---
name: bytedance-devspec
description: "Fetch and apply ByteDance DevSpec coding guidelines via bytedcli. Use when tasks mention DevSpec, ByteDance code specifications, language or business code guidelines, bytedance_go/bytedance_python/bytedance_javascript, coding protocol, REQUIRED/RECOMMENDED/OPTIONAL rules, or internal code style compliance."
---

# bytedcli DevSpec

## How to invoke bytedcli

Choose one invocation style. Examples below use `bytedcli` directly.

```bash
# Run latest without installing globally
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]

# Or install globally first
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

## When to use

- Need ByteDance DevSpec / code specification content.
- Need the ByteDance code specifications for any available DevSpec language or business guideline.
- Reviewing code against ByteDance internal normative levels.
- Need machine-readable DevSpec data for an agent.
- Need scan rules by language from the DevSpec scan-rule hub.
- Need an optional industry reference such as Google, Airbnb JavaScript, or Uber Go.

## Prerequisites

- For DevSpec pages behind SSO, run `bytedcli auth login --session` first.
- DevSpec currently uses the CN SSO/session environment.
- Use `--json` for structured agent-readable output.
- Run `bytedcli --json devspec install` once to install DevSpec content into the local cache. Agents should read from this cache by default.
- For Go and JavaScript/TypeScript, this skill also bundles a compact offline digest in `references/core-language-digests.md` as bootstrap/fallback guidance. Treat the installed cache or `--original` DevSpec response as the source of truth when available.
- Industry guides are bundled metadata and original principle summaries. They are never selected automatically and require an explicit `industry-guide list --id ...`.
- Read `../../invocation.md` when choosing between a global installation and the `npx` fallback, or when global options such as `--json` and `--site` are unclear.
- Read `../../troubleshooting.md` when installation, authentication, version, network, or command invocation fails.

## Quick start

```bash
bytedcli --json devspec install
bytedcli --json devspec guideline list --summary
bytedcli --json devspec guideline list --language Python --update
bytedcli --json devspec guideline get --name bytedance_go --locale en
bytedcli --json devspec guideline get --name bytedance_go --locale zh
bytedcli --json devspec guideline get --name bytedance_python --locale en --summary
bytedcli --json devspec guideline get --name bytedance_javascript --locale en --summary
bytedcli --json devspec guideline get --name bytedance_go --locale en --summary
bytedcli --json devspec scan-rule list --language Go
bytedcli --json devspec scan-rule list --language golang
bytedcli --json devspec scan-rule list --language py
bytedcli --json devspec scan-rule list --language js
bytedcli --json devspec scan-rule list --language TypeScript --severity critical major
bytedcli --json devspec language list
bytedcli --json devspec scan-rule list --language py --update
bytedcli --json devspec guideline get --name bytedance_go --original
bytedcli --json devspec industry-guide list
bytedcli --json devspec industry-guide list --language JavaScript
bytedcli --json devspec industry-guide list --id airbnb-javascript-style-guide
bytedcli --json devspec industry-guide list --id effective-go uber-go-style-guide
bytedcli --json devspec industry-guide list --id google-typescript-style-guide
bytedcli --json devspec industry-guide list --id jetbrains-go-modern-guidelines
```

## Notes

- Default `guideline list`, `guideline get`, `scan-rule list`, and `language list` reads use the local cache. If the cache is missing, run `bytedcli --json devspec install`.
- DevSpec reads require an SSO browser session, which a ByteCloud Auth login does not provide. Run `bytedcli auth login --session` first; without it, `devspec install` and every remote read fail with `DEVSPEC_AUTH_REQUIRED`. `industry-guide list` is offline and works without any login.
- Use `--update` to refresh the matching cache entry before reading; use `--original` to bypass the cache and read DevSpec directly without updating it.
- Agent read order: first read installed cache through `bytedcli --json devspec ...`; when cache/auth/network is unavailable and the language is Go or JavaScript/TypeScript, use `references/core-language-digests.md` as a conservative baseline; refresh later with `--update` when possible.
- Apply inputs in this order: repository-local instructions and formatter/linter/test configuration, current internal DevSpec, explicitly selected industry guides, then generic fallback guidance.
- Use `industry-guide list` without `--id` to browse the catalog. Add `--id <id...>` to explicitly select one or more external guides and return their principles for a task. Do not combine `--id` with `--language`.
- If selected industry guides conflict at the same priority, report the conflict instead of silently combining incompatible rules.
- The built-in industry catalog is offline and includes source URLs, license metadata, status, themes, limitations, and original principle summaries. Follow source URLs when exact normative wording is required.
- The catalog includes Google Go, Google TypeScript, Google Python, Airbnb JavaScript, Uber Go, Effective Go, Go Code Review Comments, and JetBrains Go Modern Guidelines. Google JavaScript remains discoverable for legacy projects but is marked deprecated with `google-typescript-style-guide` as its replacement.
- `jetbrains-go-modern-guidelines` covers choosing current Go language and standard-library features instead of older equivalents. Select it for Go work when modern-API adoption matters, and read the target Go version from `go.mod` or `go.work` first so only available features are applied.
- `devspec install` discovers and installs all available DevSpec guidelines in `en` and `zh` by default, scan-rule languages `Go`, `Python`, and `JavaScript`, plus the scan-rule language list. Use `--guideline <name...>` to install only specific guidelines.
- `devspec guideline list` reads the DevSpec guideline hub and recursively flattens inherited child guidelines, so language and business-specific specifications are discoverable by `u_name`.
- `REQUIRED` / `required` rules are blocking/error-level requirements.
- `RECOMMENDED` / `suggested` rules are warning-level best practices.
- `OPTIONAL` / `optional` rules are contextual best practices.
- The verified DevSpec page is `https://devspec.bytedance.net/codespecs/bytedance_go`.
- The verified guideline list API is `/guideline/api/v1/inherit_guidelines`.
- The verified scan-rule page is `https://devspec.bytedance.net/rules`; its API uses `/guideline/api/v3/rules` and `/guideline/api/v3/languages`.
- Scan-rule language input is normalized for common aliases and typos: Go/golang, Python/py, JavaScript/js/node/ecmascript, plus close misspellings.
- The verified guideline title is `ByteDance Golang Code Specification`, version `1.0.1`, with `66` items.
- The first verified rule is `byted_s_package_name_same_with_dir`: package name should match directory name; test packages may use `_test`.

## References

- `../../invocation.md` — read when selecting an installation/invocation mode or using global options.
- `../../troubleshooting.md` — read when installation, authentication, version, network, or command execution fails.
- `references/go-codespec.md`
- `references/core-language-digests.md`
