---
name: bytedance-it
description: "Use bytedcli IT commands for IT Service personal asset lists, asset model search, and indicative purchase prices. Trigger when users mention IT asset application, my/personal IT assets, it.bytedance.com hardware apply, iPhone/Mac/device model lookup, or want to query an IT asset reference/procurement price."
---

# bytedance-it

Use `bytedcli it` to list personal IT assets and search IT Service asset models with indicative prices. Keep the two concepts separate: `asset search` returns asset models available for application or purchase, while `asset list` returns asset instances under the current user's account.

## Auth

IT Service uses same-origin browser cookies plus a Tanna authorization token stored in the IT site cookie. The CLI reads the current Chromium session for `it.bytedance.com` and sends the extracted token as `Authorization: Bearer ...`. Titan Passport is only a fallback cookie source.

Preferred recovery order:

1. Open `https://it.bytedance.com/itam2/hardware/apply` in Chrome and ensure the page is logged in.
2. If there is no reusable SSO session, run:

```bash
bytedcli auth login --session --auto --yes
```

Never ask the user to paste browser cookies, authorization tokens, or captured `Cookie` headers.

## My Assets

```bash
# List personal IT assets
bytedcli it asset list

# Filter personal IT assets by keyword
bytedcli it asset list --keyword "MacBook"

# Structured output
bytedcli --json it asset list --keyword "MacBook"
```

`asset list` reads the IT homepage personal asset list. JSON output includes `items`, `total`, `page`, `page_size`, and `raw_item_count`. Each item is a concrete asset instance and includes asset code, localized name/model/specification, SN, status/sub-status, purpose, timestamps, and OU information.

## Asset Search

```bash
# Search a model and show indicative price
bytedcli it asset search --keyword "iPhone 17 512G"

# Structured output
bytedcli --json it asset search --keyword "iPhone 17 512G"

# Increase backend page size
bytedcli it asset search --keyword "iPhone 17" --page-size 100
```

`asset search` first queries the backend with the full keyword. If the backend returns no raw rows and the keyword contains capacity tokens such as `512G` or `1T`, it retries with a broader keyword and filters locally. This matches the IT web flow where the search may use `iPhone 17` while the user visually selects the `512G` model. Returned rows are asset models/SKUs available for application or purchase, not assets already assigned to the user.

## Output

JSON output includes:

- `items`: matched asset models.
- `total`: upstream total for the backend query.
- `page`, `page_size`: page context.
- `raw_item_count`: number of raw rows before local keyword filtering.

Each item includes model, specification, asset type, PR self-service flag, and `price.amount` / `price.currencyCode`.
