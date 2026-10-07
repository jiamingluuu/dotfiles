# Examples & best practices

## Query tips

- Keep each query focused on one page, module, or feature, e.g. `"表单页 校验规则用法"`.
- Avoid long compound queries; split complex questions into several simple searches.

## Tool selection

- **Default**: `deepwiki search` (summary) — fast answer + referenced files.
- **Need raw doc text**: `deepwiki search --format snippets`, then `deepwiki get-content --doc-id <id>`.
- **Need source-located depth**: `deepwiki analyze` (slower; needs a pre-built index).
- **Unknown collection**: check [collections.md](collections.md), else `deepwiki get-collection`.

## Scenario 1 — company infra docs (Semi Design)

```bash
bytedcli --json deepwiki search --query "表单页 Checkbox 组件用法" --collection-name DouyinFE_semi_design --limit 15
```

## Scenario 2 — understand a module in a repo

```bash
# Scope package search to a repo when several repos contain the same package name
bytedcli --json deepwiki search --query "组件生命周期" \
  --repo-name owner/repo --package-name demo-package

bytedcli --json deepwiki analyze --query "话题页 发布模块 位置与功能" \
  --repo-name owner/repo --repo-url https://code.byted.org/owner/repo.git

# Package names can be used alone or together with a repo
bytedcli --json deepwiki analyze --query "组件模块架构" \
  --package-name demo-a,demo-b
bytedcli --json deepwiki analyze --query "组件接入流程" \
  --repo-name owner/repo --package-name demo-a
```

## Scenario 3 — find where a feature lives across repos

```bash
bytedcli --json deepwiki business-graph search --query "用户登录 认证模块" --no-repo
```

## Scenario 4 — changes for a specific requirement / MR

```bash
bytedcli --json deepwiki business-graph search --query "结算页 功能变更" \
  --repo-name owner/repo --meego-id 12345 --mr-number 456
```

## Scenario 5 — repo not indexed yet

`deepwiki analyze` auto-triggers a build and returns immediately when the repo has no index. To trigger explicitly and watch progress:

```bash
bytedcli --json deepwiki index create --repo-url https://code.byted.org/owner/repo.git --repo-path owner/repo
bytedcli --json deepwiki index list --status running
```

## Source verification

DeepWiki indexes can lag. After `search` / `business-graph` return file paths, verify with local `Read` / `Grep` before relying on them. `analyze` reads source live and is more reliable, but still spot-check critical code.
