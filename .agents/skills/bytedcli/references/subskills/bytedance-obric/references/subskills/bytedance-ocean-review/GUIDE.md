---
name: bytedance-ocean-review
description: "Use bytedcli obric ocean-review commands to inspect Ocean Review / Gerrit changes from ocean-review.byted.org, publish comments, apply review label votes, update change topics, and create cherry-picks. Invoke when tasks mention Gerrit, Ocean Review, review comments, changed files, approvals, topics, cherry-picks, a /c/<project>/+/<number> URL, or a Gerrit change number."
---

# bytedance-ocean-review

Use this skill when the user wants to inspect or update a code review on
`https://ocean-review.byted.org/`.

## Commands

```bash
bytedcli obric ocean-review get --change '<ocean-review-change-url>'
bytedcli --json obric ocean-review get --change '<ocean-review-change-url>'

bytedcli obric ocean-review search --query 'owner:demo-user@example.com status:open'
bytedcli --json obric ocean-review search --query 'status:open' --page 2 --page-size 20

bytedcli obric ocean-review file list --change '<ocean-review-change-url>'
bytedcli --json obric ocean-review file list --change 12345 --project demo-project

bytedcli obric ocean-review comment list --change '<ocean-review-change-url>'
bytedcli --json obric ocean-review comment list --change '<ocean-review-change-url>'

bytedcli obric ocean-review diff get --change '<ocean-review-change-url>' --file <path>
bytedcli --json obric ocean-review diff get --change 12345 --project demo-project --file <path>

bytedcli obric ocean-review comment create --change '<ocean-review-change-url>' --file <path> --line 12 --message 'nit: ...'

bytedcli obric ocean-review review update --change '<ocean-review-change-url>' --score +1
bytedcli --json obric ocean-review review update --change 12345 --project demo-project --label Code-Review --score +2 --yes

bytedcli obric ocean-review topic update --change '<ocean-review-change-url>' --topic <topic>
bytedcli --json obric ocean-review topic update --change 12345 --project demo-project --topic <topic> --yes

bytedcli obric ocean-review cherry-pick create --change '<ocean-review-change-url>' --branch <target-branch>
bytedcli --json obric ocean-review cherry-pick create --change 12345 --project demo-project --branch <target-branch> --yes
```

## Notes

- Prefer passing the original Ocean Review URL directly; the CLI extracts project path and change number.
- Authentication reuses `bytedcli auth login --session` SSO cookies and follows the Gerrit OAuth login chain.
- JSON mode returns structured change/file/comment/diff data and strips Gerrit's XSSI prefix automatically.
- `ocean-review comment create` is dry-run by default. Show the preview and wait for explicit user
  confirmation before rerunning with `--yes`.
- `ocean-review review update` defaults to the `Code-Review` label and accepts any integer score.
  Gerrit validates the configured range and permissions. The command is dry-run by default; show the
  preview and wait for explicit user confirmation before rerunning with `--yes`.
- `ocean-review topic update` is dry-run by default. Show the preview and wait for explicit user
  confirmation before rerunning with `--yes`.
- `ocean-review cherry-pick create` is dry-run by default. Show the preview and wait for explicit user
  confirmation before rerunning with `--yes`.
- The hidden compatibility path is `bytedcli obric gerrit ...`; there is no top-level `bytedcli gerrit`.
- Do not use this skill for submit, abandon, or reviewer mutation.
