---
name: bytedance-d2c
description: "Figma 官方 D2C：支持直接获取 Figma 原始信息，并将 Figma 设计稿直接还原为 browser（H5 / desktop web）或 Lynx 页面代码。适用于首次获取 Figma 元信息，以及存量页面迭代时刷新最新 Figma 信息。Use when a user provides a Figma design link, wants Figma-to-code generation, or mentions D2C, figma2code, 视觉切分 / visual segmentation, 交互识别, D2C 精修 / refine, D2C 评测 / evaluation, render screenshot, Lynx build & capture, D2C context contract, graph / NodeID 查询, a D2C taskId's status or 产物下载, or a Figma node's curated semantic description. This skill is the single entry point for the whole D2C capability set and routes each intent to the appropriate guide under references/."
---

# Figma 官方 D2C

Figma 官方 D2C 可直接获取 Figma 原始信息，并将 Figma 设计稿直接还原为生产级 **browser**（H5 / desktop web）或 **Lynx** 页面代码。完整能力还包括视觉切分、交互识别、渲染、评测与有限精修循环。

`bytedance-d2c` is the single outward entry point for all of them. Capabilities live under `references/<capability>/SKILL.md`, keeping the upstream skill names 1:1. **Read the routing table, then load only the guides the task needs** — do not read every guide up front.

## Start here for any end-to-end D2C run

**If the task is "turn this Figma design into code" in any form, read the [aiden-d2c-skills](references/aiden-d2c-skills/GUIDE.md) flow guide first and follow it — before running any other capability.**

That guide owns the phase ordering every other capability assumes:

```
visual-segmentation → interaction-recognition → global assembly
  → deterministic validation → build/capture → evaluation → refine loop
```

The individual capability guides below document *one phase each*. They do not
restate the ordering, the artifact layout, or the prerequisites they depend on —
so starting from one of them skips setup steps that phase silently assumes
(most commonly: creating the interaction inventory before assembly). Entering
mid-flow is how a run ends up with plausible-looking code built on missing context.

Go straight to a single capability below only when the user asks for that one
thing in isolation — checking a task's status, reading one Figma node, scoring
an existing page. When in doubt, start at the flow guide.

## Route by intent

**✅ CLI** = a real SSO-authenticated `bytedcli ...` subcommand. **🧠 Reasoning** =
no executable step; read the guide and do the work yourself. Load only the guides
the task needs.

| Capability | For | Delivery |
|---|---|---|
| **[aiden-d2c-skills](references/aiden-d2c-skills/GUIDE.md)** | **Whole Figma → code flow — start here.** Sequences and names every phase guide (segmentation, interaction recognition, browser / Lynx generation, render, capture, evaluation, refine) — go there instead of entering a phase directly. | 🧠 Reasoning over ✅ CLI steps |
| [build-figma-index](references/build-figma-index/GUIDE.md) | 获取 Figma 元信息，或存量页面迭代时重新获取最新 Figma 信息（`bytedcli --json d2c figma get`，加 `--refresh` 绕过缓存） | ✅ CLI |
| [download-icon](references/download-icon/GUIDE.md) | 按节点 id 下载 Figma 图片 / 图标切图，出图层级由传入的节点 id 决定（`bytedcli d2c figma download-icon`，加 `--output-dir` 落盘） | ✅ CLI |
| [get-figma-graph](references/get-figma-graph/GUIDE.md) | 按 NodeID 查 Figma 信息及父子节点上下文 | ✅ CLI |
| [get-figma-design-description](references/get-figma-design-description/GUIDE.md) | 读单个 Figma 节点的人工语义描述 | ✅ CLI |
| [d2c-context-contract](references/d2c-context-contract/GUIDE.md) | `d2c.contract.json` 上下文标准化 | ✅ CLI validation + 🧠 Reasoning authoring |
| [deepwiki-skill](references/deepwiki-skill/GUIDE.md) | 生成过程中查组件 / 库文档 | ✅ CLI (`bytedcli deepwiki`) |

Rows 2 onward are standalone lookups — reach for one when the user asks for that
thing in isolation. The phase guides are not listed here on purpose: they are only
correct in the order the flow guide sets, so it owns routing to them. Task status
and 产物 download URLs live in the segmentation and render-screenshot guides
(`bytedcli d2c task get`).

Every networked command authenticates with your own ByteCloud + Codebase SSO session —
run `bytedcli auth login` once. None of them prompts for a credential.

## Agent Guidance

- **Do not call the D2C HTTP endpoints directly with the upstream scripts.** They send no credentials. The bytedcli commands cover the same endpoints and are SSO-authenticated.
- **If a capability looks missing, report the gap.** Everything D2C can do here is a bytedcli command or your own reasoning — do not route the user to an external marketplace to fill it.
- **Read `validation_coverage`, not just `passed`.** `d2c lynx-page validate` reports `component_selection_status`; when it is `skipped`, say only that deterministic validation found no render-blocking issue — never that component selection is correct.
- **Base flow decisions on `workflow_blocking` / `repairable` / `category`.** A `repairable: false` infrastructure issue means stop for an outer retry, not edit the code. A failing validation exits `0` with `passed: false` — read the field, not the exit code.
- **Geometry `insufficient-evidence` is degraded-but-valid.** Image evaluation stays usable; do not optimize against aggregate IoU / center / size values in that state.
- **Style-contract values already use the contract's `target.unit`.** Never convert or multiply them again.
- **Never paste a Figma token, cookie, or JWT where one is not asked for.** Tokens are resolved internally only where the backend requires one, and are never written to disk, logged, or echoed in output.
- **首次获取或普通读取 Figma 元信息时，`d2c figma get` 默认复用缓存；修改 / 迭代存量页面且需要新的、最新 Figma 信息时必须加 `--refresh`，避免命中旧缓存。** 默认返回 `origin_json`，只有明确不需要大体积原始树时才传 `--no-origin`。
- Task creation, Figma index build/refresh, rendering, build/capture, and image comparison create or update server-side work. The read-only and offline commands do not.
- `bytedcli design-space d2c ...` is a **different product** (Codin D2C: read-only Figma extraction and node recommendation). It is not part of this namespace and is not a substitute for it.

See [references/errors.md](references/errors.md) for the CLI error-code table, [references/examples.md](references/examples.md) for end-to-end CLI examples, and [references/capability-map.md](references/capability-map.md) for the authoritative upstream-skill → capability mapping with its pinned revision.
