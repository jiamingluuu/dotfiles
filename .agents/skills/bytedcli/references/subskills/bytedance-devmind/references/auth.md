# DevMind Auth

DevMind uses two request headers:

- `x-jwt-token`: a ByteCloud JWT for `bits.bytedance.net`, obtained from bytedcli SSO.
- `Auth-Code`: a six-digit minute HOTP derived from the current username.

Do not print or log either value.

The Auth-Code algorithm is:

```text
timestamp_seconds = round(unix_ms / 1000)
day_suffix = int(UTC date YYYY-MM-DD last digit) + 1
key = username repeated day_suffix times
counter = floor(timestamp_seconds / 60)
HMAC-SHA1(key, counter as 8-byte big-endian)
dynamic truncate -> 6 digit string (zero-padded)
```

Boundary notes:

- Codes are stable within the same UTC minute (`counter` does not change).
- Codes rotate at the next UTC minute boundary.
- `day_suffix` follows the UTC calendar date last digit, so values can change across UTC midnight even when the local timezone date has not flipped.
- Username is trimmed before key derivation; empty usernames are rejected.

Use `bytedcli -j devmind doctor` to verify auth health. It reports only non-sensitive status such as username, JWT presence, and Auth-Code digit count.
