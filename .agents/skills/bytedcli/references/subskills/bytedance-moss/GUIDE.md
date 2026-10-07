---
name: bytedance-moss
description: MOSS test material management platform queries via bytedcli. Use when checking MOSS review test tags, listing owned test accounts, or listing virtual identity credentials.
---

# MOSS

Use this skill for the MOSS test material management platform, including test account and virtual credential lookup.

## Authentication

MOSS APIs use ByteCloud SSO JWT. Log in before running the commands:

```bash
bytedcli auth login
```

## Commands

```bash
# Check whether a test account has the review test tag.
bytedcli moss test-account has-tag --user-id 1000000000000000 --app-id 1000

# List test accounts under the fixed MOSS account pool, with optional local filters.
bytedcli moss test-account list --app-id 1000 --user-id 1000000000000000 --mobile 10000000000

# List virtual credentials for an app.
bytedcli moss test-credential list --app-id 1000

# Machine-readable output.
bytedcli --json moss test-account has-tag --user-id 1000000000000000 --app-id 1000
bytedcli --json moss test-account list --app-id 1000 --user-id 1000000000000000 --mobile 10000000000
bytedcli --json moss test-credential list --app-id 1000
```

## Output Notes

- `test-account has-tag` text output returns only `hasTag`; JSON output keeps `appId`, `userId`, `reviewTestTag`, and `hasTag`.
- `test-account list` uses the fixed MOSS `space_id` required by the platform. `--app-id`, `--user-id`, and `--mobile` are local filters after fetching the account pool.
- `test-account list` emits the account expiry field as `expireTime`.
- Large numeric IDs are emitted as strings in JSON output to avoid precision loss.
- API fields are normalized to camelCase, for example `user_id` becomes `userId`.
- `test-credential list` returns credential `bindUsers`, omits the raw per-credential `status`, labels the text authorization column as `Authorized Users`, and labels the text expiry column as `Expire Date`.
- Virtual credential text fields are decoded to readable Chinese when the API returns Unicode escape sequences.
