---
name: bytedance-canteen
description: "Use when users ask what food is available at ByteDance canteens, including today's breakfast, lunch, or dinner menu for one or more office buildings, or mention ByteCanteen, 字节食堂, 今天吃什么, 楼栋菜单, 早餐, 午餐, or 晚餐. Queries ByteCanteen in real time through bytedcli and reuses the saved Feishu Web session."
---

# ByteCanteen menus

Use `bytedcli canteen menu get` for real-time ByteDance canteen menus. For a first query or an abbreviated building name, search with a broad city or campus keyword first, then copy the complete returned building name verbatim into `--building`. Do not guess, shorten the returned name, or silently select among multiple candidates.

## Auth

The command reuses the Feishu Web session saved by bytedcli. If it reports `CANTEEN_FEISHU_SESSION_REQUIRED`, run:

```bash
bytedcli auth login --session --feishu
```

Never ask the user to paste a Feishu cookie, session, mina code, or ByteCanteen token. The CLI derives the ByteCanteen token internally and keeps it in memory only.

## Commands

```bash
# Discover candidates with a broad city or campus keyword
bytedcli canteen building search --keyword demo-city
bytedcli --json canteen building search --keyword demo-city

# Copy the complete returned building name, including city, campus, and phase
bytedcli canteen menu get --building demo-city-demo-campus-phase-2-building-c

# Query multiple buildings and one meal
bytedcli canteen menu get \
  --building demo-city-demo-campus-phase-2-building-c \
  --building demo-city-demo-campus-phase-2-building-d \
  --meal lunch

# Query a specific date and multiple meals
bytedcli canteen menu get \
  --building demo-city-demo-campus-phase-2-building-c \
  --date 2026-08-14 \
  --meal breakfast,dinner

# Structured output
bytedcli --json canteen menu get \
  --building demo-city-demo-campus-phase-2-building-c
```

`--building` and `--meal` are repeatable and also accept comma-separated values. The date defaults to today in `Asia/Shanghai`; omitting `--meal` queries breakfast, lunch, and dinner.

## Result handling

- For a first query or a shorthand building name, use `canteen building search` with a broad city or campus keyword. A shortened building name may return no candidates even when the building exists.
- Copy the displayed complete building name, or JSON `buildings[].name`, verbatim into `--building`; keep city, campus, phase, and building markers, and do not use the bracketed building ID.
- An exact normalized building-name match wins. If no exact match exists, the CLI accepts the result only when the search returns one candidate.
- Ambiguous building searches return candidates and do not silently select one.
- Multiple buildings are independent: successful menus are preserved, failures are reported, and the command exits nonzero on partial success.
- `hidingReason` is represented as an unavailable menu result. Do not invent dishes or recommendations.
- Text output follows building → meal → stall → dish category. Use `--json` for automation.

## References

- Read `../../invocation.md` for installation, global options, and JSON invocation rules.
- Read `../../troubleshooting.md` when authentication, network access, or command execution fails.
