---
name: bytedance-reimbursement
description: "Use bytedcli reimbursement commands for Hi Travel workflows: inspect forms and invoices, create or update ChatGPT, Claude, DeepSeek, or Kimi AI product drafts, resolve expense cities, guard draft-expense merges, detect, explicitly delete or submit, verify mutations, and troubleshoot authentication. Trigger for Hi Travel, 报销 or reimbursement, invoice or receipt attachments, AI product claims, and requests to merge reimbursement drafts."
---

# bytedance-reimbursement

## Commands

```bash
# List and inspect reimbursement forms
bytedcli --json reimbursement list --page 1 --page-size 10
bytedcli --json reimbursement get --id <reimbursement_union_id>

# List and inspect the current user's generic Hi Travel invoice records (发票)
bytedcli --json reimbursement invoice list --page 1 --page-size 10
bytedcli --json reimbursement invoice get --id <invoice_id>

# Run pre-submit detection
bytedcli --json reimbursement detect --id <reimbursement_union_id>

# Delete or close a draft after the user explicitly confirms the live action
bytedcli --json reimbursement delete --id <reimbursement_union_id> --yes

# Prepare an AI product reimbursement draft from a receipt plus payment proof
# (defaults: --product chatgpt, --city 北京, --claim-currency CNY)
bytedcli --json reimbursement ai-subscription create \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png \
  --date 2026-05-07 \
  --invoice-amount 200 \
  --claim-ratio 0.5

# DeepSeek API/Token top-up: --product deepseek selects the matching product and purchase type.
bytedcli --json reimbursement ai-subscription create \
  --receipt ./deepseek-invoice.pdf \
  --attachment ./deepseek-payment-proof.png \
  --date 2026-05-07 \
  --invoice-amount 100 \
  --currency CNY \
  --claim-currency CNY \
  --product deepseek

# Kimi subscription in Shanghai: both Kimi and Shanghai use built-in mappings.
bytedcli --json reimbursement ai-subscription create \
  --receipt ./kimi-invoice.pdf \
  --date 2026-05-07 \
  --invoice-amount 99 \
  --currency CNY \
  --claim-currency CNY \
  --product kimi \
  --city 上海

# Non-CN-settled employee paying in a local currency (e.g. SGD-settled, Claude): pick the product
# and set --claim-currency to the settlement currency so no CNY conversion is applied.
bytedcli --site i18n-tt --json reimbursement ai-subscription create \
  --receipt ./sample-receipt.png \
  --date 2026-05-25 \
  --invoice-amount 300 \
  --currency SGD \
  --claim-currency SGD \
  --product claude \
  --claim-ratio 0.5

# Preview merging one single-expense source draft into a master draft.
# This is an authenticated online read, but does not mutate either draft without --yes.
bytedcli --json reimbursement merge \
  --master-id <master_reimbursement_union_id> \
  --source-id <source_reimbursement_union_id> \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png

# Merge only after the user explicitly confirms the live action
bytedcli --json reimbursement merge \
  --master-id <master_reimbursement_union_id> \
  --source-id <source_reimbursement_union_id> \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png \
  --yes

# Submit an already verified and detected form only after explicit confirmation
bytedcli --json reimbursement submit \
  --id <reimbursement_union_id> \
  --yes
```

## Safe workflow

1. Read the product, expense city, paid date, receipt currency, full paid amount, and receipt number from each receipt. Never infer currency or city from the filename.
2. Before creating a draft, use `list` and `get` to check draft and submitted forms for the same product, date, receipt currency, full invoice amount, and receipt filename. Stop and report the existing form when these match.
3. Run `ai-subscription create --dry-run` before the live create. This validates local input, including the built-in Beijing/Shanghai/Shenzhen city selection; it does not check server duplicates, validate a template, fetch a cross-currency exchange rate, or mutate Travel.
4. Select `--template-reimbursement-id` dynamically from a recent successfully audited form owned by the current user, and verify that it contains the same AI product. Omit the option when no valid template exists.
5. After every create, update, merge, or submit, run `reimbursement get` and verify the server state. Do not trust command prose, initialization payloads, or a successful HTTP response alone.
6. Run `detect` after all attachments and merges are complete. Submit only when no blocking tag remains and the user explicitly requested submission.
7. If a mutation fails or times out, inspect the affected reimbursement before retrying. Preserve every returned reimbursement, attachment, invoice, and expense ID.
8. For merge failures, preserve `details.stage` when present, plus `master_id`, `source_id`, `uploaded_attachment_ids`, `invoice_id`, and `appended_expense_id`; an empty attachment list or `null` ID means that artifact had not been created when the command stopped.

For the full duplicate, template, merge, acceptance, and recovery procedure, read [references/reimbursement.md](references/reimbursement.md).

## Guidance

- Authentication resolves the Travel session in this order:
  1. bytedcli's local cache (refreshed within the past 6 hours).
  2. Chrome's persistent cookie store. When stdin/stdout are a TTY, bytedcli reads `TRAVEL_SESSION` for `travel.bytedance.com` from Chrome's local cookie SQLite store, decrypting via macOS Keychain `Chrome Safe Storage`. On first use the OS shows one Keychain prompt — click "Always Allow" once and the cookie is reused thereafter. Set `BYTEDCLI_DISABLE_CHROME_COOKIE_STORE=1` to skip this path.
  3. Chrome CDP. If a Chromium-based browser is running with `--remote-debugging-port` open (defaults probed: `9222`, `19825`; override via `BYTEDCLI_REIMBURSEMENT_CDP_PORT`), bytedcli reads the existing `TRAVEL_SESSION` over CDP without launching Chrome or touching Keychain. This path is the recommended primary in agent / CI / non-TTY environments and runs automatically when the cookie-store path is skipped.
  4. SSO redirect chain backed by `bytedcli auth login --session`. Kept as a last resort; the upstream Travel site is now a single-page app, so this path is rarely able to mint a fresh `TRAVEL_SESSION` by itself.
- Onboarding: open `https://travel.bytedance.com` in Chrome once a year and complete the Travel/Reimbursement login flow so Chrome refreshes `TRAVEL_SESSION` for `travel.bytedance.com`. bytedcli reads it from there on subsequent runs.
- `ai-subscription create` defaults to preparing a draft/update and running detection; it does not submit unless both `--submit` and `--yes` are present.
- `reimbursement invoice list/get` queries the generic Hi Travel invoice store. It is useful for tracing the manual invoice created by `ai-subscription create`, but it can also return non-AI invoices. Do not classify a row as AI-related from the invoice response alone; follow its `reimbursementUnionId` with `reimbursement get` and inspect the linked expense product.
- `--receipt` accepts exactly one primary receipt or invoice. Repeat `--attachment <path>` for payment proof, subscription details, or other supplemental files. The receipt alone creates the manual invoice snapshot; the expense attachment list contains the receipt followed by all supplemental files in CLI input order. Do not merge these materials into one file.
- `reimbursement merge` accepts only unchanged `SNAPSHOT` / `UN_SUBMIT` drafts whose expenses have the strict supported manual AI structure. It prints a read-only plan unless `--yes` is present. A live merge uploads the files and creates a manual invoice, rereads both drafts immediately before append to reject concurrent changes, then rereads the master after append and any title update. Successful verification binds the appended expense to the exact attachment and invoice IDs created by that invocation. Merge never runs detection, submits either draft, or deletes the source.
- For merge, pass the source expense's primary receipt through `--receipt` and repeat `--attachment` for every supplemental file in the exact server attachment order. Every local file must be non-empty, and each basename and byte size must match the corresponding source attachment. Do not run concurrent merges against the same master because the upstream append endpoint has no exposed compare-and-swap token.
- `reimbursement delete` also has the `close` alias and requires `--yes`; use it only for drafts that should be removed.
- Use `--template-reimbursement-id` only after validating the prior successful form and same-product AI expense with `get`.
- Use `--reimbursement-id` to keep multiple AI products in one draft: the requested product updates its existing row, while a product not yet present appends a new row. It never appends a second row for the same recognized product. Use `reimbursement merge` only to combine expenses that already live in separate drafts.
- `--invoice-amount` is the full receipt amount. The expense claim uses `--claim-ratio` and is expressed in `--claim-currency`.
- `--product` selects the AI product and its purchase type on the expense row (`chatgpt` default, `claude`, `deepseek`, or `kimi`). ChatGPT, Claude, and Kimi use built-in `软件（订阅制）` mappings; DeepSeek uses the built-in `API/Token充值` mapping. The default title is derived from the product (e.g. `Kimi 订阅报销` or `DeepSeek API/Token 充值报销`); pass `--title` to override. Reporting the wrong product or purchase type is a common cause of `单据校验失败` on detect.
- `--city` selects a built-in expense city (`北京` default, `上海`, or `深圳`); the English names `Beijing`, `Shanghai`, and `Shenzhen` are also accepted (case-insensitive). These cities use fixed Travel city IDs, so city selection does not make a lookup request. Other values fail locally before any draft or attachment is created. An explicit `--city` overrides all expense city fields copied from `--template-reimbursement-id` or an existing draft. Without `--city`, a new expense cloned from a template keeps that template city only when all required city fields are present; incomplete template city data falls back to Beijing. If `--reimbursement-id` already contains the requested product, that current expense wins over any template and its city fields reset to Beijing for backward compatibility. A fresh expense without a template also defaults to Beijing.
- `--claim-currency` is the settlement currency the claim is paid in (`CNY` default). When it equals `--currency`, no FX conversion is applied (rate = 1) and the claim stays in that currency; otherwise the Travel exchange-rate API converts the consumption currency into `--claim-currency`. Employees settled outside CNY (e.g. an SGD-settled TikTok/i18n employee) should pass `--claim-currency` matching their settlement currency, and usually run with `--site i18n-tt` so the command authenticates against the right SSO environment.
