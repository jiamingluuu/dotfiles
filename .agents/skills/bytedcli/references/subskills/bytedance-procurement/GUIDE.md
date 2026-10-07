---
name: bytedance-procurement
description: "Use for Procurement 采购 workflows and Supplier Management 供应商管理 resources. Supports supplier detail lookup by Supplier V code (供应商 V 码) and third-party supplier lookup by company name or unified social credit code. Not for general Supplier Management name search."
---

# Procurement 采购

Use `bytedcli procurement` for Procurement operations. The `supplier` subcommand gets supplier
details by Supplier V code and searches third-party supplier sources. It does not support general
Supplier Management name search.

## Auth

Supplier Management is a CN Web console. API requests use a same-origin site cookie plus an
LGW CSRF token (`x-lgw-csrf-token`). ByteCloud JWT from `auth login` is only a Titan bootstrap
fallback input — it is not sent as the request credential.

Preferred recovery order:

1. Open the Supplier Management console once in Chrome and ensure you are logged in:
   `https://procurement.bytedance.net/supplier-manage/query/supplier?source=home`
2. If Chrome has no usable site session, mint CN SSO/Titan identity, then retry:

```bash
bytedcli auth login --session --auto --yes
```

The CLI prefers a Chromium session for the Supplier Management site after a lightweight session probe (only 401/403 or SSO login redirects reject the jar; a 404 from `/lgw/csrf_token` is ignored because that path can 404 on a still-valid browser session). If none is available or the probe fails, it derives a fresh site session from the current bytedcli CN SSO/Titan identity and obtains a CSRF token before sending the API request. Verified sessions stay sticky in memory across retries. It retries once after refreshing authentication when the backend reports an expired login. Permission failures are returned directly.

Never ask the user to paste browser cookies, CSRF tokens, JWTs, or captured `Cookie` headers. Do not loop on `auth login` alone when the error says the procurement site session or CSRF is unavailable — open Chrome first.

## Supplier Management

```bash
# Get supplier detail by Supplier V code (BU defaults to BU99)
bytedcli procurement supplier get --supplier-v-code demo-v-code

# Select a business unit
bytedcli procurement supplier get --supplier-v-code demo-v-code --bu BU88

# Search third-party suppliers by supplier name
bytedcli procurement supplier third-party search --keyword demo-supplier

# Search third-party suppliers by unified social credit code
bytedcli procurement supplier third-party search --keyword 91110000EXAMPLE001 --country CN

# Structured detail output
bytedcli --json procurement supplier get --supplier-v-code demo-v-code

# Structured third-party search output
bytedcli --json procurement supplier third-party search --keyword demo-supplier
```

`supplier get` requires `--supplier-v-code`; `--bu` defaults to `BU99`.

For third-party search, `--country` is a two-letter country code and defaults to `CN`.

## Output

`supplier get` JSON output includes:

- `supplier`: the upstream detail record.

`supplier third-party search` JSON output includes:

- `suppliers`: normalized supplier records.
- `current_count`: number of records returned by this request; the upstream API does not provide a total.
- `timed_out`: whether the upstream fuzzy search timed out.
- `trace_id`: upstream request trace identifier for troubleshooting.

Key supplier fields include `supplierName`, `voucherCode`, `voucherTypeName`, `country`, registration flags, and data source.

## References

- Read `../../invocation.md` for installation, global options, and JSON invocation rules.
- Read `../../troubleshooting.md` when authentication, network access, or command execution fails.
