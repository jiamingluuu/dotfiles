# insearch command reference

## insearch query [keyword]

Search deterministic ByteDance internal sources.

Options:
- `--keyword <kw>` — search keyword (alternative to positional arg)
- `--source <sources>` — comma-separated: feishu.cn, feishu.cn/drive/home, feishu.cn/messages, cloud.bytedance.net, bytedance.net, bytetech.info, bitsai.bytedance.net, volcengine.com. `all` is the default and excludes Ask Feishu, BitsAI and Volc Engine docs. `feishu.cn` expands to docs + messages.
- `--count <n>` — results per source (default: 10)
- `--offset <n>` — result offset (default: 0)

Ask Feishu is intentionally not a `query` source because it creates a Q&A record. Run `insearch ask run` when you explicitly want Ask Feishu Q&A. BitsAI is also excluded from the default `all` source set; prefer `bitsai ask` for BitsAI Q&A, or explicitly pass `--source bitsai.bytedance.net` for compatibility. Volc Engine (火山引擎) public docs are likewise excluded from `all`; pass `--source volcengine.com` to search them (public, no auth).

The `feishu.cn/*` sources are served by `lark-cli`, sharing the same Feishu identity as other bytedcli domains — run `bytedcli lark login` once. `feishu.cn/drive/home` reports a real backend match total; `feishu.cn/messages` has no backend total, so JSON omits `total` and returns `page_count` + `has_more` instead — raise `--count` for more.

Examples:

```bash
# Search deterministic sources
bytedcli insearch query "kitex ppe环境"

# Search specific sources
bytedcli insearch query "TCC 配置发布" --source feishu.cn,cloud.bytedance.net

# Explicit compatibility path for BitsAI direct answers
bytedcli insearch query "如何接入BMQ" --source bitsai.bytedance.net

# Search ByteTech technical articles
bytedcli insearch query "Openclaw" --source bytetech.info

# Search Volc Engine (火山引擎) public docs
bytedcli insearch query "对象存储 TOS" --source volcengine.com

# JSON output
bytedcli --json insearch query "kitex ppe环境"
```

## insearch get [target]

Get content by URL.

Options:
- `--target <target>` — URL (alternative to positional arg)

GET fallback safety boundaries:
- Only GET is supported.
- bytedcli-managed auth is selected automatically and only sent to the maintained ByteDance internal/TTP host allowlist.
- URLs with username/password are rejected.
- POST, PUT, PATCH, DELETE, arbitrary auth headers, and user-provided tokens are not supported.

Supported URL patterns:
- `*.larkoffice.com/wiki/*` — Feishu wiki doc → markdown
- `*.larkoffice.com/docx/*` — Feishu docx → markdown
- `*.feishu.cn/wiki/*` — Feishu wiki doc → markdown
- `*.feishu.cn/docx/*` — Feishu docx → markdown
- `cloud.bytedance.net/docs/*/wiki/*` — Cloud docs (wiki) → markdown
- `*.bytedance.net/docs/*/wiki/*` — Cloud docs (wiki) → markdown
- `cloud.bytedance.net/docs/product/*` — ByteCloud product docs entry → product metadata and related document URLs
- `bytetech.info/articles/*` — ByteTech article URL → full markdown in text mode; structured detail in `--json`
- `*.volcengine.com/docs/<library>/<document>` — Volc Engine public doc → full markdown in text mode; structured detail (incl. `markdown`) in `--json`. Both numeric-id URLs (`/docs/12345/678901`) and slug URLs (`/docs/<LibraryCode>/<DocumentCode>`, incl. the `/docs/<LibraryCode>/doc/<DocumentCode>` canonical form) are supported; product landing URLs like `/docs/<libraryID>` are rejected.
- Other allowlisted ByteDance internal HTTP(S) URLs — plain GET fallback with bytedcli-managed auth

Examples:

```bash
# Fetch Feishu wiki doc
bytedcli insearch get https://bytedance.larkoffice.com/wiki/xxx

# Fetch Cloud doc
bytedcli insearch get https://cloud.bytedance.net/docs/tcc/wiki/xxx

# Fetch ByteCloud product docs entry and related document URLs
bytedcli insearch get https://cloud.bytedance.net/docs/product/demo-product

# Fetch ByteTech article by URL
bytedcli insearch get https://bytetech.info/articles/12345

# Fetch Volc Engine public doc as markdown (numeric-id or slug URL)
bytedcli insearch get https://www.volcengine.com/docs/12345/678901
bytedcli insearch get https://docs.volcengine.com/docs/sample-product/sample-doc?lang=zh

# Fetch file from Codebase repository
bytedcli insearch get https://code.byted.org/example/demo-project/tree/main/path/to/file.yaml

# GET fallback for internal URL/API
bytedcli insearch get https://sample-service.bytedance.net/api/status

# JSON output
bytedcli --json insearch get https://bytedance.larkoffice.com/wiki/xxx
```

## insearch ask

Run Ask Feishu independently and manage `ask.feishu.cn` Q&A history.

### insearch ask run

Ask `ask.feishu.cn` a question. This creates a Q&A record in your Feishu Ask history; by default that record is kept.

Options:
- `--keyword <kw>` — question text (alternative to positional arg)
- `--delete-history` — delete the Q&A record after the answer is fetched (default: kept)

```bash
bytedcli insearch ask run --keyword "如何接入BMQ"
bytedcli insearch ask run "如何接入BMQ" --delete-history
bytedcli --json insearch ask run --keyword "如何接入BMQ"
```

### insearch ask list

List the current user's recent Ask Feishu Q&A topics.

Options:
- `--page-size <n>` — maximum number of topics to list (default: 20)

```bash
bytedcli insearch ask list
bytedcli --json insearch ask list --page-size 20
```

### insearch ask delete

Delete Ask Feishu Q&A topics by id.

Options:
- `--id <id>` — topic id to delete (repeatable, or comma-separated)

A topic is reported as deleted only when the server confirms it (`is_deleted=true`); unconfirmed ids are returned separately in `failed`.

```bash
bytedcli insearch ask delete --id 7361234567890
bytedcli insearch ask delete --id 7361234567890 --id 7361234567891
```

## insearch login

Authenticate all search services (SSO session + service sessions).

Triggers SSO login flow and sets up sessions for all supported search backends. If specific services fail, the command reports which services are available and which need additional setup.

The `feishu.cn/*` sources are served by `lark-cli`; if its user session is missing, run `bytedcli lark login` and re-run.

```bash
bytedcli insearch login
```

## insearch status

Check authentication status of all search services.

Returns a table showing each service's auth state (ok / expired / not_configured) and instructions for missing credentials. The `Feishu via lark-cli` row reports the current lark-cli user session; it only probes an already-installed lark-cli and never installs one.

```bash
bytedcli insearch status
bytedcli --json insearch status
```
