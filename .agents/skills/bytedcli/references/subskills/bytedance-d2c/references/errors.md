# D2C error codes

Every failure is a structured error carrying `code` and an actionable `hint`.

| Code | Cause | What to do |
|------|-------|-----------|
| `D2C_INPUT_ERROR` | Bad argument: empty / malformed `--task-id`, unknown `--kind`, non-URL `--figma-page-url`, invalid `BYTEDCLI_D2C_HOST` | Fix the argument. The `hint` lists the allowed values or expected form. |
| `D2C_AUTH_ERROR` | No usable ByteCloud or Codebase credential | Run `bytedcli auth login`, then retry. Raised before any request is sent. |
| `D2C_FORBIDDEN` | HTTP 403 — authenticated, but not authorized for this task or page | Ask the owner for access. Re-authenticating does **not** help. |
| `D2C_NOT_FOUND` | HTTP 404 — no such task for this `--kind` | Verify the id, and try the other `--kind`. |
| `D2C_API_ERROR` | Backend reported a semantic failure in an otherwise successful response | Read `message`; usually a task-level failure rather than a client mistake. |
| `D2C_PARSE_ERROR` | Response did not match the expected schema | Likely a backend change; report it. The error carries a short payload preview. |

## Authentication model

Requests carry two JWTs obtained from your existing SSO session — a ByteCloud JWT and a Codebase JWT — plus `x-client-type: bytedcli`. The **server** derives the calling user from those credentials.

Consequences worth knowing:

- There is no `--token` / `--cookie` / `--jwt` flag, and none will be added. Credentials come only from your SSO session.
- Nothing prompts interactively and no browser is opened, so these commands are safe in CI and other headless contexts. Without a valid cached session they fail fast with `D2C_AUTH_ERROR`.
- On an HTTP 401 the credentials are force-refreshed and the request is retried exactly once, which covers a locally cached JWT that the server has already revoked.
- Authorization is enforced server-side per user. A 403 is a real access decision, not a client bug.

## Host override

`BYTEDCLI_D2C_HOST` redirects requests, e.g. to a staging gateway. Because every request carries your credentials, the override must be an `https://` URL on a `*.bytedance.net` host; anything else — including plain `http://` on a bytedance host, which would put the JWTs on the wire in cleartext — is refused with `D2C_INPUT_ERROR`. `BYTEDCLI_D2C_HOST_UNSAFE=1` lifts the restriction and will send your credentials to whatever host you configure — use it only against a local mock.
