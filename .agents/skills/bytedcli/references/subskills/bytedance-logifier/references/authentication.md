# Authentication

Logifier uses the current bytedcli CN ByteCloud user identity. The credential is obtained per request and sent only in the Logifier request header. It is not an argument, output field, or local Logifier token cache.

```bash
bytedcli --site cn --json auth status
bytedcli --site cn auth login
```

Do not ask the user to copy a JWT, Cookie, browser session, or long-lived token. If `LOGIFIER_AUTH_REQUIRED` remains after a fresh login, preserve the request ID from the structured error and ask the Logifier platform to confirm the user's batch permission.
