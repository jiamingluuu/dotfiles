---
name: bytedance-cloud-docs
description: "Use bytedcli Cloud Docs/字节云文档 to search/fetch by document ID, keywords, business ID or API-document filters; recall ByteCloud product/component articles with links, reasons and Markdown. Also use for natural-language ByteCloud architecture, principles, capabilities, usage, limitations or troubleshooting questions, even without explicit documentation intent."
---

# bytedcli Cloud Docs

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

- 根据用户的自然语言询问召回 ByteCloud 产品或组件相关文档
- 搜索/获取 Cloud Docs
- 查询业务域与 API 文档

## Routing

- 用户以自然语言询问 ByteCloud 产品或组件文档时，读取 [文档搜索与召回](references/recall-docs.md)。
- 用户已经给出明确 `doc_id`、只要求读取指定文档时，使用 `cloud-docs get`，并读取 [Cloud Docs CLI 命令](references/cloud-docs.md)。
- 用户明确要求执行 `search`、`list-business` 或 `list-docs` 命令时，读取 [Cloud Docs CLI 命令](references/cloud-docs.md)。

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
bytedcli cloud-docs search "keyword"
bytedcli cloud-docs get "doc_id"
bytedcli cloud-docs list-business
bytedcli cloud-docs list-docs "business_id" --api-doc "tce:v1"
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json cloud-docs search ...`）

## References

- [Cloud Docs CLI 命令](references/cloud-docs.md)
- [文档搜索与召回](references/recall-docs.md)
