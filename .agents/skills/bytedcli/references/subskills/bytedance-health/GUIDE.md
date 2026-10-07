---
name: bytedance-health
description: "Use when users ask about ByteHealth or 字节健康 massage availability, therapist schedules, massage booking, or subscribing to a full slot's release reminder. Uses bytedcli health massage commands, supports a local per-user therapist preference, and requires explicit confirmation before mutations."
---

# ByteHealth massage booking

Use `bytedcli health massage` to inspect massage schedules, book an available slot, or subscribe to a full slot's release reminder.

## Safety rules

- Always run `health massage locations` first. If multiple locations are returned, require an explicit `--location`; never guess one.
- When the user does not select a therapist, prioritize one who can perform the requested action. Apply a locally configured therapist preference only among equally eligible therapists.
- Before any booking, subscription, reminder cancellation, or order cancellation, show the exact target and obtain explicit user confirmation.
- `subscribe`, `unsubscribe`, `book`, and `cancel` are dry-run by default. Add `--yes` only after that confirmation.
- Never expose or ask the user to paste ByteHealth cookies. The CLI reuses the browser session and caches it privately.
- Booking additionally requires the user to have reviewed the agreement, a valid phone number, and an unambiguous base massage product. Show its exact name and price before confirmation. Paid bookings return an Alipay payment URL/QR after the order is created.
- Never retry order creation after an ambiguous network failure. First verify order status in ByteHealth to avoid duplicate pending orders.

## Workflow

```bash
# 1. Discover exact locations
bytedcli health massage locations

# 2. Optionally store this user's preference locally (example only)
bytedcli health massage preference set --therapist 12

# 3. Inspect slots; omission prefers availability, then the local preference
bytedcli health massage slots \
  --location sample-location \
  --date 2026-09-01

# 4. Preview a release reminder subscription
bytedcli health massage subscribe \
  --location sample-location \
  --date 2026-09-01 \
  --therapist 12 \
  --time 16:00-16:30

# 5. Submit only after the user confirms the exact selection
bytedcli health massage subscribe \
  --location sample-location \
  --date 2026-09-01 \
  --therapist 12 \
  --time 16:00-16:30 \
  --yes
```

Slot states are `available`, `subscribable`, `subscribed`, `booked`, and `off_schedule`. Book only `available` slots, subscribe only `subscribable` slots, and cancel a reminder only for `subscribed` slots.

Every slot includes `orderId` (number or `null`), `paymentStatus`, and `paymentTime` (strings or `null`). Missing values are returned as `null`, not omitted; pending-payment orders also have the `booked` state.

## Booking

Preview first. The phone number is accepted as sensitive input and is never printed.

```bash
bytedcli health massage book \
  --location sample-location \
  --date 2026-09-01 \
  --therapist 12 \
  --time 16:00-16:30 \
  --phone 13800000000 \
  --accept-agreement
```

The default non-limited base product is selected automatically. Use `--goods-id` only to override it. After explicit confirmation, rerun the same command with `--yes`; paid orders print a payment URL and terminal QR, while `--qr-image [path]` saves a PNG. If the slot becomes unavailable, refresh `slots`; do not automatically choose another time.

If payment generation fails after the order is created, do not run `book` again. Resume payment for the existing order instead:

```bash
bytedcli health massage pay --order-id 123456 --qr-image ./payment.png
```

Cancel an existing order with a preview first, then repeat with `--yes` after confirmation:

```bash
bytedcli health massage cancel --order-id 123456
bytedcli health massage cancel --order-id 123456 --yes
```

## Authentication

Commands first verify the private Ryan/ByteHealth cache, then reuse the CN SSO session managed by `bytedcli auth` when possible. If no reusable session exists, they open ByteHealth in the system default browser; finish sign-in there while the CLI waits and securely caches the verified Ryan session. Slot queries, bookings, and release-reminder subscriptions remain direct CLI API operations.

## References

- Read `../../invocation.md` for installation, global options, and JSON invocation rules.
- Read `../../troubleshooting.md` when authentication, network access, or command execution fails.
