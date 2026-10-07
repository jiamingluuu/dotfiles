# Reimbursement Commands

Reimbursement commands are grouped under `reimbursement` and backed by Hi Travel APIs.
Authentication resolves automatically through the cached Travel session, Chrome's persistent cookie store, Chrome CDP, and finally the SSO session created by `bytedcli auth login --session`. Keep the SSO redirect path as a last resort. Never print, copy, or persist `TRAVEL_SESSION`, SSO cookies, or exported authentication data.

## Contents

- [Receipt facts and duplicate checks](#receipt-facts-and-duplicate-checks)
- [Invoice lookup](#invoice-lookup)
- [Template selection](#template-selection)
- [Create or update a draft](#create-or-update-a-draft)
- [Merge multiple drafts](#merge-multiple-drafts)
- [Detect, submit, and verify](#detect-submit-and-verify)
- [Key options and multi-currency claims](#key-options-and-multi-currency-claims)
- [Failure handling](#failure-handling)

```bash
# Inspect the installed command surface before relying on newer options
bytedcli --version
bytedcli reimbursement --help
bytedcli reimbursement merge --help

# Last-resort SSO session bootstrap
bytedcli auth login --session

# Clear only a stale cached Travel session before retrying automatic resolution
bytedcli reimbursement auth logout

# Read existing forms
bytedcli --json reimbursement list --page 1 --page-size 10
bytedcli --json reimbursement get --id <reimbursement_union_id>

# Read the current user's generic Hi Travel invoice records
bytedcli --json reimbursement invoice list --page 1 --page-size 10
bytedcli --json reimbursement invoice get --id <invoice_id>

# Detect, explicitly submit, or explicitly delete a draft
bytedcli --json reimbursement detect --id <reimbursement_union_id>
bytedcli --json reimbursement delete --id <reimbursement_union_id> --yes
bytedcli --json reimbursement submit --id <reimbursement_union_id> --yes

# Validate local AI subscription inputs without calling Travel APIs
bytedcli --json reimbursement ai-subscription create \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png \
  --date 2026-05-07 \
  --invoice-amount 200 \
  --claim-ratio 0.5 \
  --dry-run

# Create one live draft expense; this does not submit
bytedcli --json reimbursement ai-subscription create \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png \
  --attachment ./sample-subscription-detail.pdf \
  --date 2026-05-07 \
  --invoice-amount 200 \
  --claim-ratio 0.5

# Preview an authenticated, read-only merge
bytedcli --json reimbursement merge \
  --master-id <master_reimbursement_union_id> \
  --source-id <source_reimbursement_union_id> \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png \
  --title "AI 订阅报销"

# Perform the same merge only after explicit confirmation
bytedcli --json reimbursement merge \
  --master-id <master_reimbursement_union_id> \
  --source-id <source_reimbursement_union_id> \
  --receipt ./sample-receipt.pdf \
  --attachment ./sample-payment-proof.png \
  --title "AI 订阅报销" \
  --yes
```

## Invoice lookup

The invoice subcommands query the current user's generic Hi Travel invoice store. They are useful
for tracing the manual invoice created by an AI product reimbursement, but the result can also
contain non-AI invoices. To confirm an AI relationship, follow the returned
`reimbursementUnionId` with `reimbursement get` and inspect the linked expense product.

## Receipt facts and duplicate checks

Read these values from every receipt before invoking a mutation:

- Product: `chatgpt`, `claude`, `deepseek`, or `kimi`.
- Expense city, using the built-in Beijing, Shanghai, or Shenzhen value in Chinese or English.
- Paid date in `YYYY-MM-DD`.
- Receipt currency and full paid amount before applying the reimbursement ratio.
- Receipt or invoice number when present.
- Primary receipt filename and every supplemental attachment filename.

Never infer currency or city from a filename or reuse values from a different receipt. Use `list` across enough pages to cover the receipt date, then inspect plausible AI reimbursement candidates with `get`. Check every expense in drafts and submitted forms. Treat a matching product, date, receipt currency, full invoice amount, and primary receipt filename as a duplicate; use the receipt or invoice number as additional confirmation when available. Stop and report the existing reimbursement ID and status instead of creating another draft.

## Template selection

Choose a template dynamically rather than hardcoding an ID:

1. Find recent successfully audited or completed AI reimbursements in the current user's `list` results.
2. Inspect each candidate with `get`.
3. Verify that it belongs to the current user, is not a draft, uses the AI learning expense type, and contains the same `productName` as the new receipt.
4. Pass the verified union ID through `--template-reimbursement-id`.

Omit the option when no valid candidate exists. Do not substitute another user's form, another product, an unrelated expense type, or an unsubmitted draft.

## Create or update a draft

Run `ai-subscription create --dry-run` first. It validates the date, amount, ratio, supported product key, built-in Beijing/Shanghai/Shenzhen city, file existence, and duplicate local file identities without making network requests. For cross-currency claims it cannot provide the final settlement amount because the live Travel exchange-rate request has not run; it also does not check server-side duplicates or validate a template.

The live command creates a draft when `--reimbursement-id` is absent. With `--reimbursement-id`, it updates the row for the requested product when that product already exists, or appends a new row when the draft contains only other AI products. It does not append a second row for the same recognized product. Use `reimbursement merge` when the expenses already live in separate drafts. After the mutation, capture the returned IDs and call:

```bash
bytedcli --json reimbursement get --id <reimbursement_union_id>
```

Verify all of the following before continuing:

- The draft is still unsubmitted, normally `status=SNAPSHOT` and `comboStatus=UN_SUBMIT`.
- The expected expense exists and an update did not change the expense count unexpectedly.
- Product, expense city, date, receipt currency, full invoice amount, claim ratio, and settlement amount match the receipt and Travel exchange rate.
- The primary receipt is first, followed by all supplemental attachments in CLI input order.
- Title and settlement total are correct in `--claim-currency`.

## Merge multiple drafts

Use one master reimbursement with multiple AI expenses when the receipts belong to the same reimbursement batch. Create the first receipt as the master and each additional receipt as a temporary one-expense draft. Do not use `--reimbursement-id` to append.

`reimbursement merge` enforces these preconditions:

- Master and source IDs differ.
- Both forms are `SNAPSHOT` plus `UN_SUBMIT` drafts with the same owner and reimbursement document.
- The master has at least one expense and the source has exactly one.
- Every master expense and the source expense uses the canonical AI-learning expense type ID or the exact case-insensitive name `AI学习研究`. Date, product, currency, positive invoice and settlement amounts, and at least one attachment must be present; every attachment must have an ID, basename, and positive byte size.
- Every expense has exactly one invoice. That invoice has an ID, type `BIZ_UNIT_RECEIPT_ELECTRIC`, source `MANUAL`, and both `snapshot` and the single `multiInvoiceSnapshot` value bound to the primary attachment ID.
- `--receipt` is the source expense's primary receipt. Repeated `--attachment` values reproduce every supplemental source attachment in exact server order. Every local file must be non-empty, and each basename and byte size must match the corresponding source attachment.
- The master does not already contain the source expense signature based on date, product, receipt currency, full invoice amount, and the complete ordered attachment filename list.

Without `--yes`, merge performs authenticated server reads and local file validation, then returns a non-mutating plan. Review `masterId`, `sourceId`, `files`, `sourceExpense`, `masterExpenseCount`, `predictedExpenseCount`, and `predictedTotal`.

Use `--yes` only after the user explicitly confirms the merge. The live command uploads the supplied files and creates a new manual invoice, then rereads both master and source before append. It compares status, combo status, owner, document, title, version, amount, payable amount, and expense IDs/signatures with the initially validated drafts. Any change stops the workflow before expense append with stage `pre_append_recheck`; uploaded attachments and an invoice may already exist.

After the append call, merge rereads the master even when the append response failed or timed out. It accepts an ambiguous append only when readback proves exactly one matching expense, preserves every pre-existing expense, verifies totals and draft identity, and proves that the matching expense references the exact artifacts created by this invocation. A requested title update is followed by another readback. Merge never runs detection, submits either form, or deletes the source. Review `appendedExpenseId`, `receiptAttachmentId`, `additionalAttachmentIds`, `invoiceId`, `expenseCount`, `amount`, `payableAmount`, and `expenses`, then independently run `get` on the master and verify:

- Expense count increased by exactly one.
- Exactly one expense matches the source signature, including all attachment basenames in order.
- Its attachment IDs equal the `uploaded_attachment_ids` created by this invocation in order.
- It has exactly one invoice. That invoice ID equals the `invoice_id` created by this invocation, has type `BIZ_UNIT_RECEIPT_ELECTRIC` and source `MANUAL`, and binds the receipt attachment ID created by this invocation through `snapshot` and the single `multiInvoiceSnapshot` value.
- `appendedExpenseId` comes from the verified readback when the append response was ambiguous.
- `amount` and `payableAmount` equal the sum of the settlement amounts.
- Title matches `--title` when supplied.

Do not run concurrent merges against the same master. The command performs a second change check immediately before append and rejects ambiguous readbacks, but the upstream append endpoint exposes no atomic compare-and-swap token. If another writer races after that check, verification fails and the master must be inspected manually before any retry.

Delete a temporary source only after this readback succeeds, only when it was created for the current task, and only after the user explicitly confirms deletion. Verify afterward that it no longer appears in `list` or `get`.

## Detect, submit, and verify

Run detection after all attachment uploads and merges are complete:

```bash
bytedcli --json reimbursement detect --id <reimbursement_union_id>
```

Inspect the full detection response rather than assuming tags always live at one fixed JSON path. Stop when a tag level or code contains `STRONG`, `BLOCK`, `FATAL`, or `ERROR`. Report `WEAK` and `TIP` warnings instead of suppressing them. If attachment recognition is still in progress, wait and rerun detection before claiming that the form is ready.

The standalone `submit` command does not replace this acceptance step. Submit only when the user explicitly requested it, the final draft readback matches every receipt, and no blocking detection tag remains:

```bash
bytedcli --json reimbursement submit --id <reimbursement_union_id> --yes
bytedcli --json reimbursement get --id <reimbursement_union_id>
```

Require a non-empty `serialNo`, a submitted state rather than `SNAPSHOT` plus `UN_SUBMIT`, the expected title and expense count, and matching product, date, receipt currency, full invoice amount, settlement amount, and attachments for every receipt. Validate totals in the settlement currency selected by `--claim-currency`, not by assuming CNY. Report the serial number, settlement total, per-receipt settlement amounts, and current approval state.

## Key options and multi-currency claims

- `--receipt <path>`: exactly one primary receipt/invoice used to create the manual invoice snapshot.
- `--attachment <path>`: supplemental expense attachment such as payment proof. Repeat the flag for multiple files; files remain in CLI input order and are not registered as extra invoices.
- `--product <chatgpt|claude|deepseek|kimi>`: AI product on the expense row (default `chatgpt`). It drives both the default title and purchase type. ChatGPT/Claude/Kimi use built-in `软件（订阅制）` mappings; DeepSeek uses the built-in `API/Token充值` mapping.
- `--city <name>`: built-in expense city `北京`, `上海`, or `深圳` (default `北京`); `Beijing`, `Shanghai`, and `Shenzhen` are also accepted (case-insensitive). The CLI uses fixed Travel city IDs and rejects other values locally. Explicit `--city` overrides city fields from a template or existing draft. Without `--city`, a new expense cloned from a template keeps that template city only when all required city fields are present; incomplete template city data falls back to Beijing. If `--reimbursement-id` already contains the requested product, that current expense wins over any template and its city fields reset to Beijing for backward compatibility. A fresh expense without a template also defaults to Beijing.
- `--currency <code>`: receipt/consumption currency (default `USD`).
- `--claim-currency <code>`: settlement currency the claim is paid in (default `CNY`). When it equals `--currency`, no FX conversion is applied (rate = 1).
- `--claim-ratio <ratio>`: reimbursed share, e.g. `0.5`.

DeepSeek API/Token top-up:

```bash
bytedcli --json reimbursement ai-subscription create \
  --receipt ./deepseek-invoice.pdf \
  --attachment ./deepseek-payment-proof.png \
  --date 2026-05-07 \
  --invoice-amount 100 \
  --currency CNY \
  --claim-currency CNY \
  --product deepseek
```

Kimi subscription in Shanghai:

```bash
bytedcli --json reimbursement ai-subscription create \
  --receipt ./kimi-invoice.pdf \
  --date 2026-05-07 \
  --invoice-amount 99 \
  --currency CNY \
  --claim-currency CNY \
  --product kimi \
  --city 上海
```

Non-CN-settled employees (e.g. SGD-settled TikTok/i18n) should pass `--claim-currency` matching their settlement currency and usually run with `--site i18n-tt`:

```bash
bytedcli --site i18n-tt --json reimbursement ai-subscription create \
  --receipt ./sample-receipt.png \
  --date 2026-05-25 \
  --invoice-amount 300 \
  --currency SGD \
  --claim-currency SGD \
  --product claude \
  --claim-ratio 0.5
```

## Failure handling

- If create initializes a draft but a later upload or write fails, preserve and report every returned ID. `TRAVEL_ATTACHMENT_UPLOAD_FAILED` details can include `reimbursement_id`, `failed_file`, and `uploaded_attachment_ids`. Inspect the draft with `get` before retrying; do not silently create another one.
- `TRAVEL_INPUT_ERROR` means local arguments or files failed validation. Fix the input before making a live call.
- `TRAVEL_MERGE_BLOCKED` occurs before attachment upload or invoice creation. Inspect `details.reason`, the two drafts, and local attachment order rather than forcing the write; no merge artifacts were created.
- Merge-time `TRAVEL_ATTACHMENT_UPLOAD_FAILED` details always include `master_id`, `source_id`, `uploaded_attachment_ids`, `invoice_id`, `appended_expense_id`, and `failed_file`. IDs not yet created are `null`, and the attachment list contains only uploads completed before the failure.
- `TRAVEL_MERGE_VERIFICATION_FAILED` means a live merge could not safely continue or prove its final state. It can occur after uploads, after invoice creation but before append, during ambiguous append reconciliation, or during final or title readback. Its details always include `stage`, `master_id`, `source_id`, `uploaded_attachment_ids`, `invoice_id`, and `appended_expense_id`; artifacts not yet created appear as `[]` or `null`. `cause_error`, `write_error`, and stage-specific evidence may also be present. Preserve the source and inspect the master before any retry.
- Interpret `create_invoice*` as attachments possibly uploaded but no expense appended; `pre_append_*` as attachments and invoice created but no expense appended; `append_readback` or `readback_*` as an append that may already have taken effect; and `title_readback` as a verified expense with an uncertain title update.
- Upload and verification failures never trigger an automatic second write.
- If detection blocks submission, report the tags and stop. Do not delete drafts or alter unrelated Travel data to work around validation.
- If submit times out or returns an ambiguous error, run `get` before retrying. A non-empty `serialNo` or submitted state means Travel may already have accepted it.
- For `TRAVEL_AUTH_REQUIRED` or Travel HTTP 401, update bytedcli, open `https://travel.bytedance.com` in Chrome to refresh the Travel login, clear only the cached Travel session with `reimbursement auth logout`, and retry automatic cookie-store/CDP recovery. Do not clear all browser or ByteCloud authentication, and keep `auth login --session` as the last resort.
