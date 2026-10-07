---
name: bytedance-deepwiki
description: "Search Aiden DeepWiki via bytedcli: RAG knowledge search over indexed repos (summarized answer, raw snippets, or deep source-located analysis), resolve collection names, fetch full docs, run business-graph (semantic graph) search over code-change records (by Meego/MR/commit), look up a repo's service meta — PSM, RPC/HTTP interfaces, IDL location and upstream/downstream call topology — and build or refresh a repo's index. Use when tasks mention DeepWiki, 知识库搜索 / 文档搜索, company infra docs (Semi Design, EdenX, Lynx, Hybrid, Garfish ...), API usage lookup, cross-repo knowledge, finding where a feature lives across repos, a service's PSM / IDL / interfaces / upstream-downstream dependencies / call topology, changes for a Meego/MR/commit, or building/updating a repo index."
---

# bytedcli DeepWiki

Aiden DeepWiki builds a code knowledge base offline from repository source and answers questions over that index. Retrieval is semantic rather than a live exact-code search, so focused page/module/feature keywords recall better than broad multi-topic prompts. Use this skill to search that knowledge, trace code-change history via a semantic graph, and trigger index builds.

## Invocation

```bash
bytedcli --json deepwiki <command> [options]
```

## Command overview

| Command | Use it for | Latency |
|---------|-----------|---------|
| `deepwiki search` | **Primary.** Summarized answer + referenced files (`--format summary`), or raw doc snippets (`--format snippets`) | ~10–30s |
| `deepwiki analyze` | Deep analysis with source location; needs a pre-built index | ~75s |
| `deepwiki get-collection` | Resolve the collection name for a repo / package | slow |
| `deepwiki get-content` | Fetch a full document by `--doc-id` (from a snippets result) | ~10s |
| `deepwiki get-service-meta` | **Upstream/downstream call topology** of a repo's services (+ PSMs, method URLs, IDL, TCC dependencies); chain into `search` | ~10s |
| `deepwiki business-graph search` | Fast business-graph (semantic graph) search over code-change records | ~10s |
| `deepwiki business-graph analyze` | Deep async business-graph search (creates a task and polls) | minutes |
| `deepwiki index create` | Build / incrementally update a repo's index | async |
| `deepwiki index list` | List index build tasks | fast |

## Knowledge search

### Write focused semantic queries

DeepWiki recall works best when each query describes one concrete target using page, module, and feature keywords. Name the business surface and intent directly, for example:

- `"结算页 优惠券模块 校验逻辑"`
- `"个人主页 头像上传功能"`
- `"订单模块 退款状态映射"`

Keep unrelated targets in separate calls. For example, if a task asks about `"结算页优惠券流程"`、`"个人主页头像上传"`、`"订单退款状态"`, run three searches and combine the verified results afterward. Do not send one broad query containing all three topics: unrelated semantic intents compete during recall and reduce result quality.

### ⚠️ Decide the search target first

| Target | When | Required flag |
|--------|------|---------------|
| Current repo | Query the current project's code/modules/APIs | none (defaults to the cwd git repo) |
| Another repo | Query a specific repo | `--repo-name owner/repo` |
| Package in a specific repo | Disambiguate same-named packages across repos | `--repo-name owner/repo --package-name demo-package` |
| Company infra (Semi Design, EdenX, Lynx, Hybrid, Garfish ...) | Query a shared component library / framework | **`--collection-name`** (see [references/collections.md](references/collections.md)) |

Common mistake: searching Semi Design docs without `--collection-name` only searches the current repo. Always pass the correct collection name from [references/collections.md](references/collections.md).

```bash
# Summarized answer for company infra (must pass --collection-name)
bytedcli --json deepwiki search --query "表单页 校验规则用法" --collection-name DouyinFE_semi_design

# Raw snippets for a specific repo, then fetch a full doc by id
bytedcli --json deepwiki search --query "话题页 发布模块" --repo-name owner/repo --format snippets
bytedcli --json deepwiki get-content --doc-id <doc_id_from_snippets> --repo-name owner/repo

# Package search scoped to a repo; use this when multiple repos contain the same package name
bytedcli --json deepwiki search --query "组件生命周期" --repo-name owner/repo --package-name demo-package

# Deep, source-located analysis for a repo (slower; needs a pre-built index)
bytedcli --json deepwiki analyze --query "表单页 校验模块架构" --repo-name owner/repo --repo-url https://code.byted.org/owner/repo.git

# Package-scoped analysis; --package-name accepts comma-separated names
bytedcli --json deepwiki analyze --query "组件模块架构" --package-name demo-a,demo-b

# Repo and package scopes can be combined
bytedcli --json deepwiki analyze --query "组件接入流程" --repo-name owner/repo --package-name demo-a
```

## Service meta + call topology (primary: who a repo's services call, and who calls them)

`deepwiki get-service-meta` resolves a **git repo** to the back-end services it deploys and — most importantly — their **upstream / downstream call topology**. The recommended use is to map a repo's service dependencies, then feed those facts into `deepwiki search` / `deepwiki business-graph search` to find the actual implementation or change history.

For each PSM it returns:

- `deploymentType` — `tce` or `faas`; the deployment's own `serviceId` / `serviceName` / `runtime` / `category` / `envName` / `revisionId` follow alongside
- `methodUrls` — exposed RPC/HTTP methods (`method` / `url` / `http_method`)
- `idlRepo` + `mainIDLFilePath` — where the IDL lives
- `downstreams` — services this PSM **calls** (each edge's `callee` is the downstream PSM)
- `upstreams` — services that **call** this PSM (each edge's `callee` is the upstream PSM)
- `tccDependencies` — TCC config services this deployment reads, with `serviceName` / `serviceId` and the `regions` / `confspaces` / `clusters` / `dcs` / `sdkLanguages` / `sdkVersions` it uses

Each SCM also carries `faasServiceCount` and `faasServicesTruncated` for the FaaS services found under it.

```bash
# Defaults to the current git repo
bytedcli --json deepwiki get-service-meta

# Explicit git repo name
bytedcli --json deepwiki get-service-meta --repo-name owner/repo
```

### ⚠️ Git repo name vs SCM name (don't mix them up when chaining)

- `repo_name` (the input, and the output `repo_name` field) is the **git repo path** (e.g. `owner/repo`). **This is the name `deepwiki search` / `business-graph search` understand** — reuse it as their `--repo-name`.
- `scms[].name` is the **Argos SCM registration name** (e.g. `sample-org/sample-scm`). It is usually **not** the git path and must **not** be passed as `--repo-name`.

### Recommended workflow: facts → implementation

`get-service-meta` is best at **facts** (PSM, IDL, methods, topology); `deepwiki search` / `business-graph search` are best at **explanation / implementation / history**. Use the facts as precise inputs to narrow recall:

```bash
# 1. Get the topology + methods for a repo (note its repo_name = git path)
bytedcli --json deepwiki get-service-meta --repo-name owner/repo

# 2a. Find a method's implementation — reuse the SAME git repo name as --repo-name
bytedcli --json deepwiki search --query "GetFoo 方法实现" --repo-name owner/repo

# 2b. Understand a downstream/upstream dependency (PSM taken from the topology)
bytedcli --json deepwiki search --query "调用 demo.example.downstream 的链路" --repo-name owner/repo

# 2c. Trace how a method changed over time
bytedcli --json deepwiki business-graph search --query "GetFoo 接口变更" --repo-name owner/repo
```

To inspect a **downstream/upstream service's own repo**, re-run `get-service-meta` with that service's candidate git repo name (a PSM is not directly a git path), then chain its topology again.

### Caveats

- **TCE + FaaS, not Goofy.** Both TCE and FaaS deployments are returned, each tagged with `deploymentType`; Goofy services are not covered. A repo deployed only on Goofy comes back with `scms` populated but `psmList: []` / `psms: []` — empty PSMs ≠ "no service". FaaS lookups are best-effort and can come back empty (the backend needs its own upstream credentials), so `faasServiceCount` / `faasServicesTruncated` on the SCM are the counts to trust.
- `scm_count: 0` usually means the repo name doesn't match an SCM registration, or it's a pure frontend / tooling repo.
- Service meta aggregates several gateways and can be slow; raise `--timeout-ms` if a query times out.
- Text mode caps each method / topology list at 20 rows; use `--json` for the full set.

## Business-graph search (semantic graph over change records)

Finds the code and business nodes touched by changes. Two scopes:

- **Cross-repo** (`--no-repo`): locate which repos/nodes relate to a description when the repo is unknown.
- **Scoped**: pass `--repo-name` and optionally `--meego-id` / `--mr-number` / `--base-commit` to pin a specific change.

```bash
# Cross-repo: which repos implement this?
bytedcli --json deepwiki business-graph search --query "用户登录 认证模块" --no-repo

# Scoped to a repo + Meego requirement
bytedcli --json deepwiki business-graph search --query "购物车功能变更" --repo-name owner/repo --meego-id 12345

# Deep async analysis (minutes; creates a task and polls)
bytedcli --json deepwiki business-graph analyze --query "支付模块重构" --repo-name owner/repo --max-polls 120
```

Returns `codeRelated` nodes (classes, functions, API endpoints, DB tables, UI components) and `nonCodeRelated` nodes (pages, business features, rules). Each node carries `source_details` (`repo_name`, `mr_number`, `meego_id`, `base_commit_sha`, `file_path`).

## Index management

If `deepwiki analyze` reports the repo has no index, it **automatically triggers a build and returns immediately** (building takes minutes — it does not wait). Re-run `analyze` later. You can also trigger/inspect builds directly:

```bash
# Build or incrementally update an index (defaults to the current git repo)
bytedcli --json deepwiki index create --repo-url https://code.byted.org/owner/repo.git --repo-path owner/repo

# Check build progress
bytedcli --json deepwiki index list --status running
```

## Agent Guidance

- **Verify before relying.** Except for `analyze` (which reads source live), `search`/`business-graph` results may be stale. After getting referenced files (`files[].filePath` / `file_path`), confirm with local `Read`/`Grep` before drawing conclusions.
- **One semantic intent per query.** Use concrete page/module/feature keywords. Split different features or modules into separate `deepwiki search` calls, then synthesize only after checking the recalled files.
- **Pick the lightest tool.** Start with `deepwiki search` (summary). Use `--format snippets` + `get-content` when you need the raw doc text; escalate to `analyze` only when you need source-located depth.
- **Request timeouts.** `search --format summary` (`fast_summary`) defaults to 600000 ms; `analyze` and `get-collection` default to 300000 ms; other DeepWiki requests, including `search --format snippets`, default to 120000 ms. `search`, `analyze`, and `get-service-meta` accept `--timeout-ms` for slower queries.
- **Index builds are slow and asynchronous.** Never block waiting on a fresh index — trigger it and move on, then re-run later.
- **Auth (required for every command).** All DeepWiki requests go to the REST API and must carry a ByteCloud JWT (`x-jwt-token`) + a Codebase JWT (`x-codebase-jwt-token`) + `x-client-type: bytedcli`. If either credential is missing the command fails with `DEEPWIKI_AUTH_ERROR`. DeepWiki always uses the **`cn`** ByteCloud login regardless of `--site` / `BYTEDCLI_CLOUD_SITE`, so on `DEEPWIKI_AUTH_ERROR` log in to `cn` specifically: `BYTEDCLI_CLOUD_SITE=cn bytedcli auth login` (logging into `i18n-*` does not help).
- **Host** is overridable via `BYTEDCLI_DEEPWIKI_HOST`, but restricted to `*.bytedance.net` (requests carry your JWTs). Set `BYTEDCLI_DEEPWIKI_HOST_UNSAFE=1` to allow a non-bytedance host (e.g. a local mock) — credentials will then be sent there.

See [references/examples.md](references/examples.md) for more scenarios and [references/collections.md](references/collections.md) for the infra → collection-name mapping.
