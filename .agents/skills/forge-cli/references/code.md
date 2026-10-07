# code.md — `forge code fetch` / `forge code update` / `forge code meta` / `forge code version create`

Use this reference for fetching Forge code into a local workspace, updating code from that workspace, inspecting or switching a version's framework metadata, and creating a new version by forking an existing version or commit. For install/auth/runtime basics see [invocation.md](invocation.md).

## Intent Guard

- `forge code update` is a Forge workflow refresh/publish step.
- Do not use it for native Git requests such as `git commit`, `提交 git`, `push 代码`, or `提交到远端分支`; use normal Git commands instead.

## Workspace Rules

- `code fetch` creates the workspace and returns `output_dir`; that returned path is the workspace root.
- `--output-dir` is a parent directory where the workspace will be created, not the final workspace root.
- Forge-managed workspaces contain `.forge/forge_meta.json`, `models/`, and `norbert/`; Git-managed workspaces are normal git clones with `.forge/forge_meta.json` at repo root.
- Context-driven commands (`code update`, `code commit create`, `code compile create`, `job create`) must run from the real workspace root or a nearby child directory.
- Before running a later workflow command, `cd` into the actual workspace root returned by fetch and say: `当前工作区是 <workspace>，version <version_id>，继续执行 <action>。`
- If the current directory is an unrelated repo with no `.forge/forge_meta.json`, stop broad searching. Ask the user to run `forge code fetch --version-id <id>` or provide a precise workspace path. `code update` and `code commit create` have no no-workspace mode; `code compile create` can use `--commit-id`; `job create` needs both model and norbert commit IDs outside a workspace.

Agent workspace selection priority:

1. Explicit user path, after verifying `.forge/forge_meta.json`.
2. Current workspace if metadata matches the requested version/project.
3. `output_dir` returned by the latest `code fetch` in this conversation.
4. Bounded local search only when the user asks for a known version/project and no workspace is selected.
5. If zero or multiple matches remain, ask the user to clarify or run `code fetch`.

## Fetch Code

CRITICAL: before every `forge code fetch`, ask the user to confirm the control plane. Do this even when the version id is known, because fetch creates a workspace bound to that control plane.

- Use one prompt named `控制面` when forms are available; otherwise ask one concise question.
- Show all four choices: `CN (--site cn)`, `I18N / ROW / US (--site i18n)`, `EU-TTP (--site eu-ttp)`, `US-TTP (--site us-ttp)`.
- Default/preselect `CN`, but do not run fetch until the user confirms.
- Pass the confirmed `--site` explicitly. Before a non-default site, make sure that site is logged in or run `forge auth login --site <site>`.
- Keep `--network office` unless the user explicitly asks for `prod`, auto-detection resolves `prod`, or a pinned config (`forge config set`) requires otherwise.

```bash
forge code fetch --version-id <VERSION_ID> --network office --site <CONFIRMED_SITE>
```

### FORGE_IDE Git Auth

When `FORGE_IDE=1`, Git-managed fetch MUST use HTTPS + existing Code token as the default path. The CLI clones `https://code.byted.org/<repo>.git`; SSH is not the `FORGE_IDE=1` default.

- Before fetch, MUST read Code URL rewrites only; MUST NOT edit `~/.gitconfig`:

```bash
git config --global --get-regexp '^url\..*code\.byted\.org.*\.insteadOf$' || true
```

- Good pattern: `url.https://<user>:<token>@code.byted.org/.insteadOf=https://code.byted.org/`. MUST use it directly.
- Bad `FORGE_IDE=1` pattern: `url.git@code.byted.org:.insteadOf=https://code.byted.org/`. It rewrites HTTPS clone to SSH and often fails with `Permission denied (publickey,gssapi-with-mic)`; MUST NOT rely on it when `FORGE_IDE=1`.
- If a global HTTPS-to-SSH rewrite would hijack fetch but an HTTPS token base is available, MUST run fetch with process-scoped config instead of changing global config:

```bash
GIT_CONFIG_GLOBAL=/dev/null \
GIT_CONFIG_COUNT=1 \
GIT_CONFIG_KEY_0='url.<authenticated-https-base>.insteadOf' \
GIT_CONFIG_VALUE_0='https://code.byted.org/' \
forge code fetch --version-id <VERSION_ID> --network office --site <CONFIRMED_SITE>
```

- MUST NOT use SSH, `git ls-remote`, branch scans, or `forge auth login` as Git auth workarounds unless the user explicitly asks.
- MUST handle the exact `forge code fetch` error once.
- MUST use `--branch` only when the user explicitly provides a branch.

Target conflict rules:

- Do not create wrapper directories such as `forge_fetch_<version>` unless the user explicitly asks for that parent directory.
- Do not invent fallback names such as `<workspace>_<version>` or `<workspace>_v<version>`.
- Do not inspect, diff, summarize, or preflight an existing target directory. Run `code fetch` and let the CLI show the conflict prompt.
- Pass `--force` only after the user explicitly chooses overwrite. Git-managed fetch does not reuse matching existing workspaces.

Key flags:

| Flag | Notes |
|---|---|
| `--version-id` | Required Forge version ID |
| `--output-dir` | Optional parent directory |
| `--force` | Overwrite target after explicit user confirmation |
| `--branch` | Git-managed only |
| `--network`, `--site` | Runtime control plane |

Output fields: `ok`, `output_dir`, `source_type`, `context_path`. Metadata is persisted to `.forge/forge_meta.json`.
For `--site us-ttp` Forge-managed fetches, the CLI also resolves code through
global `get_version_code` and persists the returned `code_version_id` plus
project/global metadata needed by later commit, compile, and job steps.

## Update Code

Run from the selected workspace:

```bash
forge code update --version-id <VERSION_ID>
forge code update --version-id <VERSION_ID> --dry-run
```

- `--version-id` is an optional safety check and must match the current workspace.
- Forge-managed update serializes the workspace and excludes `.forge/`.
- If two files in the same directory differ only by letter case (e.g. `models/din.py` and `models/DIN.py`), update/commit still succeed but the JSON result carries a `warnings` entry: consumers on case-insensitive filesystems (macOS/Windows) cannot fetch both. See [troubleshooting.md](troubleshooting.md#code-fetch--commit-get-fails-with-case-insensitive-name-collision).
- Git-managed update checks repo binding, rejects dirty worktrees, and pushes a clean HEAD when needed; `--dry-run` never pushes.
- Forge workflow commands may call `code update`; native Git requests must stay on native Git commands.
- If `.forge/forge_meta.json` is missing, stop and ask the user to run `code fetch` or `cd` into the fetched workspace before retrying.

## Version Metadata

Use `code meta` to read or switch the framework metadata returned by `get_version`: `framework` and `framework_version`.

```bash
forge code meta get --version-id <VERSION_ID> --network office --site <SITE>
forge code meta update --version-id <VERSION_ID> --framework <FRAMEWORK> --framework-version <FRAMEWORK_VERSION> --network office --site <SITE>
```

In a Forge workspace, `--version-id` can be omitted and is inferred from `.forge/forge_meta.json`. `code meta update` mutates remote version metadata; for temporary validation, always save the original value, switch, verify with `code meta get`, then immediately restore and verify again before running `code fetch`, `code commit create`, `code compile create`, or `job create`.

Key flags: `--version-id` (required outside a workspace), `--framework`, `--framework-version`, `--dry-run`, `--network`, `--site`.

Both commands also return `links.forge2`, the Forge2 version-workspace page for that `version_id`. Show it as the version link when useful. Treat `links.*` as opaque command output — do not hand-build a version URL from `version_id`, and do not add a tracing/workspace variant: none exists for versions.

## Create Version From Fork

Use `code version create` to create a new Forge version through the backend `fork_version` API. It can fork a source version HEAD, or fork one/two source commits into a target model/project.

CRITICAL: `code version create` is mutating and region-sensitive. Before running it, resolve the intended control plane and pass `--site` explicitly. If the user gives only bare commit/version IDs, ask which site owns those IDs; do not default to `cn`. If the user gives a Forge2 URL, infer `--site` from the hostname using [invocation.md](invocation.md#site-inference-before-command-assembly).

```bash
forge code version create --from-version-id <SOURCE_VERSION_ID> --target-model-id <TARGET_MODEL_ID> --network office --site <SITE>
forge code version create --from-version-id <SOURCE_VERSION_ID> --target-model-name <TARGET_MODEL_NAME> --network office --site <SITE>
forge code version create --from-model-commit-id <MODEL_COMMIT_ID> --target-model-id <TARGET_MODEL_ID> --network office --site <SITE>
forge code version create --from-model-commit-id <MODEL_COMMIT_ID> --from-norbert-commit-id <NORBERT_COMMIT_ID> --target-model-id <TARGET_MODEL_ID> --network office --site <SITE>
```

- `--from-version-id` is the source version. In a Forge workspace it can be omitted and is inferred from `.forge/forge_meta.json` when no source commit is provided.
- `--from-model-commit-id` and `--from-norbert-commit-id` each accept one source commit. The CLI calls `get_commit` on the same `--site`, verifies the commit `code_type`, infers the source version, and requires all commits to belong to one version.
- Exactly one of `--target-model-id` or `--target-model-name` is required. Do not infer the target from the current workspace.
- `--target-model-name` resolves the exact model/project name through `list_models` on the same `--site`; if no exact match or multiple exact matches are returned, stop and ask for a more precise name or the numeric `--target-model-id`.
- `--owner` defaults to the current authenticated user; pass it explicitly for automation when the username cannot be inferred.
- `--dry-run` prints the `fork_version` request and does not create a version.

The command uses the normal runtime endpoint resolver for `list_models`, `get_commit`, and `fork_version`; it does not mix regions in one invocation. If `list_models`, `get_commit`, or `fork_version` cannot find the id/name, first check that `--site` matches the source commit/version and target model's control plane.

Output includes `version_id`, version metadata, and `links.forge2` for the new version. The command does not rewrite the current workspace's `.forge/forge_meta.json`; fetch the new version explicitly before continuing work:

```bash
forge code fetch --version-id <NEW_VERSION_ID> --network office --site <SITE>
```
