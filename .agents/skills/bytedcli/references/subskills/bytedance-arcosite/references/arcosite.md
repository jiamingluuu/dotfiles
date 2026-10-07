# ArcoSite documents

## Internal document URL and read

Parse a URL locally before a workflow needs identifiers:

```bash
bytedcli --json arcosite document-url get --url '<arcosite-editor-url>'
```

Read the live editor document and obtain its Markdown projection and content hash:

```bash
bytedcli --json arcosite doc get --url '<arcosite-editor-url>'
```

An ArcoSite editor URL contains `app_id`, `business_id`, `doc_id`, language, and sometimes the business version. A ByteCloud document URL lacks `app_id`; when using one directly, pass an independently verified `--app-id` or switch to the complete editor URL.

## Update a draft

Prepare the entire desired body in a UTF-8 Markdown file. Preview first:

```bash
bytedcli --json arcosite doc update \
  --url '<arcosite-editor-url>' \
  --in-file ./draft.md
```

After the user confirms the same document, input file, title, and preview, apply it:

```bash
bytedcli --json arcosite doc update \
  --url '<arcosite-editor-url>' \
  --in-file ./draft.md \
  --yes
```

Optional flags:

- `--title <title>` updates the title with the body.
- `--edit-description <text>` records why an approved document is reopened.
- `--idempotency-key <key>` reuses a stable key after an ambiguous transport result. Do not retry an unverified write without reading the document first.
- `--app-id <id>` is only needed when the input is a ByteCloud document URL.

The command enforces these invariants:

- Empty Markdown is blocked.
- The existing rich-text layout envelope is retained to prevent a successful API response from rendering an empty document.
- A document under review is withdrawn before editing; an approved or published document uses `EditAfterApproval` before editing.
- The document is checked again before writing. A concurrent content or title change stops the write.
- Existing native internal document mentions survive the Markdown round trip.
- New legacy short links and ByteCloud document links are rejected because their targets cannot be uniquely verified from the URL alone. Use the target's full ArcoSite editor URL.
- The saved draft is read back and compared by content hash and title.

The command stops at a verified draft. It does not create or finish a task, submit review, approve, publish, delete, move, or create another language version.

## Public knowledge base

The existing `kb` commands use the public support knowledge base and its separate browser-session mechanism:

```bash
bytedcli arcosite kb list-sites
bytedcli arcosite kb search --query '<keyword>'
bytedcli arcosite kb get --doc-id '<doc-id>'
```

Do not use `kb get` as proof of the current internal editor draft; use `arcosite doc get` for that purpose.
