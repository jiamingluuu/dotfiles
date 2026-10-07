---
name: bytedance-arcosite
description: "Read internal ArcoSite editor documents as Markdown and safely update their drafts with bytedcli; also search the public ArcoSite knowledge base. Use when a request includes an arcosite.bytedance.net editor URL, asks to inspect or edit an ArcoSite draft, or explicitly asks for ArcoSite knowledge-base search."
---

# bytedcli ArcoSite

Use this skill for internal ArcoSite document reading and draft editing. Keep Cloud Docs search and published-document retrieval in `bytedance-cloud-docs`.

## Routing

- For an internal editor URL, document content, draft state, or Markdown update, read [ArcoSite documents](references/arcosite.md).
- For the public support knowledge base, use `bytedcli arcosite kb ...` as described in [ArcoSite documents](references/arcosite.md).
- For authentication setup or CLI invocation, read [invocation](../../invocation.md).
- For authentication, permission, or safety errors, read [troubleshooting](../../troubleshooting.md).

## Safety contract

- Read the current document before proposing an edit.
- `doc update` consumes a complete Markdown file and is dry-run by default. Show the preview before adding `--yes`.
- Never pass or request raw JWTs, cookies, AK, or SK. Use `bytedcli auth login`.
- Never infer that a draft update also authorizes task creation, review submission, approval, publication, deletion, or language-version creation. Those actions are outside this command surface.
- If a live write is reported as unverified, read the document before deciding whether any retry is safe.
