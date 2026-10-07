# commit.md — `forge code commit create|get|list|diff`

Use this reference for Forge commit records. For install/auth/runtime basics see [invocation.md](invocation.md). This is not native Git commit/push.

## Intent Guard

- Native Git intent (`git commit`, `提交 git`, `push 代码`, `提交到远端分支`) -> use native Git commands only.
- Forge commit intent (`Forge commit record`, `code commit create`, compile/job needs a Forge commit) -> use `forge code commit create`.
- Forge commit inspection intent (list recent records, compare a record to another record or current workspace) -> use `forge code commit list` / `forge code commit diff`.
- Questions like `612844 这个 version 提交了哪些 commit`, `某个 version 的 commit 列表`, or `最近几次成功的 model 变动` are Forge commit-record queries. Do not ask for a Git repo; run `forge code commit list --version-id <id>` and add `--build-status SUCCEEDED` only when the user explicitly says successful.

## Workspace Rules

- `code commit create` requires a fetched workspace and reads `.forge/forge_meta.json` from cwd or nearby parent directories.
- It does not accept `--dir` or `--output-dir` and does not search all local workspaces by version id.
- Before running it, `cd` into the actual workspace root returned by `code fetch`, not its parent/wrapper directory, and say: `当前工作区是 <workspace>，version <version_id>，继续执行 commit。`
- If the user gives a path/version/project, verify the selected workspace by reading `.forge/forge_meta.json`.
- If the current directory is an unrelated repo with no `.forge/forge_meta.json`, stop. Do not keep broad-searching. Ask the user to run `forge code fetch --version-id <id>` or provide the fetched workspace path.
- `code commit create` has no no-workspace flag path.

## Create Commit

```bash
forge code commit create --code-type model --description "fix feature extraction"
forge code commit create --code-type norbert --description "refresh norbert workflow"
forge code commit create --code-type model --dry-run
```

Key flags:

| Flag | Notes |
|---|---|
| `--code-type` | Required: `model` or `norbert` |
| `--description` | Required for real submit; optional for `--dry-run` |
| `--dry-run` | Validate context/request without creating a commit |

Rules that matter:

- `code commit create` first runs `code update`, then calls Forge `create_commit`.
- Forge-managed `model` serializes `models/`; Forge-managed `norbert` serializes `norbert/`.
- Git-managed workspaces use Git metadata instead of serializing directories. The command may push a clean HEAD through `code update`, but it never creates a native Git commit. If the worktree is dirty, use the normal Git workflow first.
- On success, the commit artifact is stored in `.forge/forge_meta.json` for later compile/job stages.
- Success also returns `links.forge2`, the Forge2 commit-detail page. Show it as the commit link when useful. Treat `links.*` as opaque command output — do not hand-build a commit URL from `commit_id`, and do not add a tracing/workspace variant: none exists for commits (verified live; the route 404s).

## Get Commit

```bash
forge code commit get --commit-id 123456
forge code commit get --commit-id 123456 --output-dir ./other-dir
```

`code commit get` restores commit code to disk and does not require workspace context. Its output includes the exact commit record's `framework` and `framework_version`; use those fields, not compile/job logs or paginated `commit list` results, when resolving framework source for diagnosis. For `--site us-ttp --network prod`, it reads the commit's metadata without requesting code, then downloads exactly one archive through the default US-TTP production Reckon gateway: model uses `code_dir=models&node_name=models`, while Norbert uses `code_dir=norbert&node_name=norbert`. The response may be a plain or gzip-wrapped tar and must contain exactly the selected workspace root. A pre-existing empty `--output-dir` keeps its inode and metadata. `--site us-ttp --network office` retains `get_commit` and the global code fallback; other sites keep using the commit's `code_snippet`. Output also includes `links.forge2`, the Forge2 commit-detail page for this commit. Treat `links.*` as opaque command output — do not hand-build a commit URL from `commit_id`; no tracing/workspace variant exists for commits (verified live; the route 404s).

## List Commits

```bash
forge code commit list --version-id 612844 --code-type model
forge code commit list --version-id 612844
forge code commit list --version-id 612844 --build-status SUCCEEDED
```

Key flags:

| Flag | Notes |
|---|---|
| `--version-id` | Forge version id; inferred from the current workspace when omitted |
| `--code-type` | Optional: `model` or `norbert`; omitted queries both types and returns a merged recent list |
| `--limit` | Defaults to 5 |
| `--offset` | Defaults to 0 |
| `--build-status` | Optional; omit unless the user explicitly asks for a status such as `SUCCEEDED` |

Each item in `commits[]` also carries `links.forge2` for that commit. Treat `links.*` as opaque command output — do not hand-build a commit URL from `commit_id`; no tracing/workspace variant exists for commits (verified live; the route 404s).

## Diff Commit

```bash
forge code commit diff --commit-id 5762444 --base-commit-id 5760630
forge code commit diff --commit-id 5762444
forge code commit diff --commit-id 5762444 --base-commit-id 5760630 --context-lines 0
```

`code commit diff` is read-only. It compares a target commit to another Forge commit when
`--base-commit-id` is provided. Otherwise it resolves the current Forge workspace from cwd
or parent directories and compares current workspace -> target commit. If no workspace is
found, cd into a fetched workspace or pass `--base-commit-id`.
The patch direction is always source -> target. JSON output includes the patch in the
`patch` field. `--context-lines` controls the unchanged lines around each diff hunk,
defaults to 3, and accepts any non-negative integer including 0. The JSON result echoes
the effective value in `context_lines`. If `get_commit` does not return `code_snippet`, non-TTP commits fail.
For `--site us-ttp` commits with `global_id`, the CLI falls back to
`global_site/get_commit_code`; it never falls back to Git metadata.
`code commit diff` output has no `links` field — the diff is a locally-generated patch with no corresponding web page. Don't add one.
