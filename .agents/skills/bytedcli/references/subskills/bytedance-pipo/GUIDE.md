---
name: bytedance-pipo
description: "Use when users ask about PIPO, PIPO orders, PIPO KYB, merchant KYC cases, or KYB certificate file download. Look up PIPO orders by id, search PIPO security compliance KYB cases, and download attachments through bytedcli instead of opening the console."
---

# PIPO

Use `bytedcli pipo order get` to look up a PIPO order by id on the MIS order query page. `--region` is required (`my` or `my4a`). Pass `--channel-info` and/or `--payment-info` to select which slices to return. Use `bytedcli pipo security compliance kyb` to search PIPO KYB / KYC cases by client id. Use `--raw` to include `CaseJsonParam` and file ids, then `bytedcli pipo security compliance download --file-id` to download an attachment.

## Auth

Order get always uses `mis.tiktok-row.net` and ignores global `--site`. It reuses Chromium cookies for that host, including `mis2_sid`. Open the MIS order query page in Chrome once, then retry the CLI. KYB / download use ByteCloud JWT for `pipo-security-sea.tiktok-row.net` and reuse Chromium cookies for that host when present.

```bash
bytedcli auth login
```

Operator email for KYB is taken from the logged-in user. Override with `--user-email` only when needed.

## Commands

```bash
bytedcli pipo order get --order-id demo-order-id --region my --channel-info
bytedcli --json pipo order get --order-id demo-order-id --region my4a --payment-info
bytedcli --json pipo order get --order-id demo-order-id --region my --channel-info --payment-info
bytedcli pipo security compliance kyb --client-id 1234567890
bytedcli --json pipo security compliance kyb --client-id 1234567890 --page 1 --page-size 10
bytedcli --json pipo security compliance kyb --client-id 1234567890 --raw
bytedcli pipo security compliance download --file-id demo-file-id --output ./cert.pdf
```

`--tenant` defaults to `ukyc_ttop_merchant`. `--region` for order get has no default: `my` and `my4a` select different MIS `groupId` values. Order get requires at least one of `--channel-info` or `--payment-info`.

## Result handling

- `order get` JSON includes `order_id`, `idc`, `group_id`, plus selected `channel_info` and/or `payment_info`. It does not return the full MIS payload. Text mode prints those ids plus the selected slices.
- KYB JSON includes `items`, `total`, `page`, `page_size`, and `truncated`. Each item is a whitelist of `caseId`, `clientId`, `clientName`, `status`, `treatmentId`, `treatmentStatus`, `caseMainStatus`, `businessLine`, `caseRegion`, `caseSource`, `caseTag`, `scenarioCode`, `pipoEntity`, `kycType`, `assignee`, `latestReviewer`, `createdAt`, and `updatedAt`.
- `--raw` adds `raw` (backend case, with `CaseJsonParam` parsed) and `files` (`fileId`, `fileName`, `kind`). The first enterprise cert is usually `files[0]` / `enterprise_info.certificate_list[0].cert_file_id_list[0]`. Text mode prints a files table only when `files` is non-empty.
- Text mode shows Case ID / Client ID / Client Name / Status / Business Line / Region / Created. If `truncated` is true, raise `--page-size` or change `--page`.
- `download` writes the raw file bytes from `GET /api/aml_platform/preview?file_id=` (platform endpoint name; CLI verb is download). Successful responses are written to `--output` (or `./<file-id>.<ext>`). Re-run with `--force` to overwrite. Typical content types are `application/pdf` and `image/jpeg`.
- Use placeholder order ids such as `demo-order-id`, client ids such as `1234567890`, and file ids such as `demo-file-id` in examples; do not copy real cookies or JWTs from browser curls.

## Agent Guidance

- Always pass `--region my` or `--region my4a` with `pipo order get`. Do not guess a default region. Do not add `--site i18n-tt` for this command. Always pass `--channel-info` and/or `--payment-info`; do not request the full order payload.
- To download the first cert: run `kyb --client-id ... --raw`, take `items[0].files[0].fileId` (or `raw.CaseJsonParam.enterprise_info.certificate_list[0].cert_file_id_list[0]`), then `download --file-id <id> --output ./cert.pdf`.
- Do not open the console preview URL in a browser without the same JWT/cookie session; use the CLI `download` command.

## References

- Read `../../invocation.md` for installation, global options, and JSON invocation rules.
- Read `../../troubleshooting.md` when authentication, network access, or command execution fails.
