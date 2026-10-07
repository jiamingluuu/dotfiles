---
name: bytedance-warlock
description: "Read Warlock shared network captures through bytedcli. Use whenever a user provides a warlock.byteintl.net/share URL or Warlock share key, asks to inspect captured API request/response bodies or response headers, wants the captured x-tt-logid, or needs a safe read-only summary of Warlock network records."
---

# bytedcli Warlock

Use `bytedcli warlock share get` to turn a Warlock share URL into structured network records. The command reads the share data directly and parses nested JSON response bodies and headers; do not use `insearch get` on the page HTML or manually construct the hidden storage URL.

## Commands

```bash
# Read a Warlock share URL in human-readable form.
bytedcli warlock share get --url '<warlock-share-url>'

# Stable JSON for agents and scripts. Global --json goes before the domain.
bytedcli --json warlock share get --url '<warlock-share-url>'

# A share key can be used when the full URL is unavailable.
bytedcli --json warlock share get --key <share-key>

# Include captured request headers. Sensitive values remain redacted.
bytedcli --json warlock share get --url '<warlock-share-url>' --include-request-headers

# Override the request timeout for a slow share lookup.
bytedcli --json warlock share get --url '<warlock-share-url>' --timeout-ms 30000
```

## Output

JSON output is under `data` and contains:

- `shareType`, `sharedAt`, and `count` for the share.
- `items[]` for captured network records.
- `items[].request.method` and `items[].request.url` for request identity.
- `items[].response.body` for the recursively parsed API response.
- `items[].response.headers` for response headers such as `x-tt-logid`.
- `items[].request.headers` only when `--include-request-headers` is passed.

When the user asks for the API response, return `items[].name` together with `items[].response.body`. When the user asks for response headers or a LogID, read `items[].response.headers`; do not confuse the share-storage request headers with the captured business API headers.

## Safety

- The command is read-only and accepts only the Warlock HTTPS share page or a validated share key.
- Request header values matching Cookie, Authorization, token, secret, or credential names stay redacted even when request headers are included.
- Sensitive response headers such as `set-cookie` are also redacted.
- Treat the share URL/key as access-bearing input: do not copy it into logs, tickets, or unrelated documents.
- Warlock mock import, capture mutation, and other write operations are outside this command's scope.

## Agent Guidance

- `WARLOCK_SHARE_INPUT_ERROR`: pass the full HTTPS Warlock `/share?key=...` URL or a valid share key.
- `WARLOCK_SHARE_HTTP_ERROR`: confirm office-network access and that the share still opens. The reported endpoint intentionally replaces the access-bearing key with `<share-key>`.
- `WARLOCK_SHARE_API_ERROR`: the key was rejected, expired, or removed; ask the owner to generate a new share.
- `WARLOCK_SHARE_INVALID_RESPONSE` / `WARLOCK_SHARE_SCHEMA_ERROR`: upgrade bytedcli and retry. If it persists, report the share type without pasting request cookies or authorization headers.
- An empty `items` array is a valid empty capture, not an HTTP failure.

## References

- `../../invocation.md`
- `../../troubleshooting.md`
