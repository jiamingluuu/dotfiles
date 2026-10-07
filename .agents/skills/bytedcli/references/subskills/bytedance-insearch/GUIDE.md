---
name: bytedance-insearch
description: "搜索字节跳动内部知识、文档、服务和工具；也可通过 insearch get 对允许的内部 HTTP(S) URL 执行只读 GET。当用户提问涉及字节内部平台（如 TCC、TCE、Kitex、Hertz、ByteRPC、Neptune、Aeolus、BMQ、Hive、ES 等）、内部文档、内部流程，或给出需要登录态访问的内部 URL/API 时使用。Search ByteDance internal knowledge, docs, services and tools. Use when questions involve internal platforms, frameworks, documentation, deployment, oncall, ByteDance-specific topics, or authenticated internal URL reads."
---

# bytedcli insearch

Unified search and authenticated read-only URL fetch across ByteDance internal services. Use this skill when questions involve ByteDance internal knowledge, tools, services, documentation, or when the user provides an internal HTTP(S) URL/API that needs bytedcli-managed auth.

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- User asks about ByteDance internal tools (TCC, TCE, Kitex, Hertz, Neptune, Aeolus, etc.)
- User needs to find internal documentation
- User asks about internal processes (deployment, oncall, release, etc.)
- User asks "how to" questions about internal frameworks
- User wants to look up internal service configurations
- User needs answers about ByteDance-specific technology stack
- User provides a ByteDance internal HTTP(S) URL/API that needs login/auth, returns 401/403 without auth, or asks to GET/fetch/read it
- User needs content from an allowlisted internal URL; use `insearch get <url>`

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

### Search deterministic sources

```bash
bytedcli insearch query "kitex ppe环境"
bytedcli insearch query "TCC 配置发布"
```

### Search specific source

```bash
bytedcli insearch query "kitex ppe" --source feishu.cn
bytedcli insearch query "TCC SDK" --source cloud.bytedance.net
bytedcli insearch query "Openclaw" --source bytetech.info
bytedcli insearch query "对象存储 TOS" --source volcengine.com
```

### Ask Feishu independently

```bash
bytedcli insearch ask run --keyword "如何接入BMQ"
bytedcli insearch ask run "如何接入BMQ" --delete-history
```

### Get document/URL content

```bash
bytedcli insearch get https://bytedance.larkoffice.com/wiki/xxx
bytedcli insearch get https://cloud.bytedance.net/docs/tcc/wiki/xxx
bytedcli insearch get https://cloud.bytedance.net/docs/product/demo-product
bytedcli insearch get https://bytetech.info/articles/12345
bytedcli insearch get https://www.volcengine.com/docs/12345/678901
bytedcli insearch get https://docs.volcengine.com/docs/sample-product/sample-doc?lang=zh
bytedcli insearch get https://sample-service.bytedance.net/api/status
bytedcli insearch get https://code.byted.org/example/demo-project/tree/main/path/to/file.yaml
```

### Manage Ask Feishu Q&A history

```bash
bytedcli insearch ask list
bytedcli insearch ask delete --id 7361234567890
bytedcli insearch ask delete --id 7361234567890 --id 7361234567891
```

### Check auth status

```bash
bytedcli insearch status
bytedcli insearch login
```

## Available sources

| Source | Description | Auth |
|--------|-------------|------|
| feishu.cn | 飞书/Lark 文档、消息聚合别名 | lark-cli user session（`bytedcli lark login`） |
| ask.feishu.cn | 企业问答 / Feishu Ask；只通过 `insearch ask run` 独立执行 | Saved Feishu web session from `auth login --session --feishu` |
| cloud.bytedance.net | ByteCloud documentation | SSO JWT |
| bytedance.net | Internal portal (intranet) | SSO session |
| bitsai.bytedance.net | AI Q&A (BitsAI engineering navigator)；`insearch query` 默认不包含，推荐用 `bitsai ask` | SSO JWT |
| bytetech.info | ByteTech technical articles | SSO JWT |
| volcengine.com | 火山引擎（Volc Engine）公开产品文档；`insearch query` 默认不包含，显式 `--source volcengine.com` 检索，`insearch get <doc-url>` 取回 markdown | None (public) |

## Recommended workflow

1. Use `insearch query` for deterministic search: `bytedcli insearch query "your question"`.
2. Use `insearch get <url>` to fetch full document content from search results or read an allowlisted internal HTTP(S) URL.
3. Use `insearch ask run --keyword <question>` only when you explicitly want Ask Feishu Q&A. Use `bitsai ask --message <question>` when you explicitly want BitsAI.

## Notes

- `--json` is a **global flag** — place it before the subcommand: `bytedcli --json insearch query "xxx"`
- 飞书相关能力（`--source feishu.cn`、`insearch get <飞书文档 URL>`、`insearch get feishu://message/...`）由 `lark-cli` 提供，与其他 domain 共用同一份飞书身份。首次使用先跑 `bytedcli lark login`；`insearch status` 会显示当前 lark-cli 用户会话状态。
- `feishu.cn/drive/home` 的 `total` 是后端真实命中总数；`feishu.cn/messages` 的后端不返回总数，JSON 里不给 `total`，改用 `page_count` + `has_more` 表示当前页条数与是否还有更多，需要更多结果就调大 `--count`。
- `insearch query` does not include Ask Feishu. `ask.feishu.cn` creates a Q&A record, so run it explicitly with `insearch ask run`.
- `insearch query` default/all does not include BitsAI. Prefer `bitsai ask` for BitsAI; `--source bitsai.bytedance.net` remains an explicit compatibility path.
- Ask Feishu answers are saved to temp markdown files; `insearch ask run` returns the file path as `markdown_path` in JSON mode.
- `insearch ask run` creates a Q&A record in your Feishu Ask history; that record is **kept by default**. Pass `--delete-history` to remove it automatically once the answer is fetched.
- Clean up leftover Ask history with `insearch ask list` then `insearch ask delete --id <topicId>`. A topic is reported as deleted only when the server confirms it (`is_deleted=true`); unconfirmed ids are listed separately.
- ByteTech article fetch only supports article URLs; text mode prints full markdown body by default. Pass `--include-source-doc` only when the caller explicitly needs the source Feishu/Lark document link; in JSON mode this also includes `source_doc_token` and `source_doc_url`
- ByteCloud product URLs such as `https://cloud.bytedance.net/docs/product/demo-product` return product metadata plus related document URLs; fetch a related document URL for full document markdown.
- Volc Engine (火山引擎) public docs are public (no auth). `insearch query --source volcengine.com` searches across all product docs; `insearch get <doc-url>` returns the full doc as markdown (text mode prints `# Title` + metadata + body, `--json` keeps `markdown`). Both URL forms are supported: numeric-id URLs like `https://www.volcengine.com/docs/12345/678901` and slug URLs like `https://docs.volcengine.com/docs/sample-product/sample-doc` (the canonical `/docs/<LibraryCode>/doc/<DocumentCode>` form works too). Product landing URLs like `/docs/<libraryID>` are rejected.
- Codebase file URLs (`code.byted.org`/`code-tx.byted.org`) with `/tree/`, `/blob/`, or `/raw/` fetch file content via the Codebase API. For branches with slashes, use the `/-/` separator between revision and file path.
- Unsupported structured URLs fall back to a plain GET for allowlisted ByteDance internal HTTP(S) hosts; the fallback uses bytedcli-managed auth automatically.
- ⚠️ The plain-GET fallback can silently return an SSO **login page** instead of the target content when the target host rejects the current auth (no error is raised). If the fetched body contains `<title>ByteDance SSO</title>` or an SSO redirect form instead of the expected content, treat it as "not authenticated for this host" — do not parse it as real page data; re-run `bytedcli auth login` or fetch the data through the dedicated domain command (e.g. `aeolus` / `coral` subcommands) instead of raw GET.
- Auth errors include a hint on how to authenticate
- Use `insearch status` to check which sources are available
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json insearch query "xxx"`）

## References

- `references/search.md`
- `../../invocation.md`
- `../../troubleshooting.md`
