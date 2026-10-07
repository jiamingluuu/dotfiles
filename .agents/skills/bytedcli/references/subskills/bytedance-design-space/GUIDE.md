---
name: bytedance-design-space
description: "Use when tasks mention Design Space, Codin D2C, design-to-code, Figma to code, Figma DSL/XML, D2C icon download, D2C code verification, or selecting an appropriate Figma node before D2C generation."
---

# Design Space / Codin D2C

Design Space D2C converts Figma designs into implementation material for agents and code generation. The official entry is:

```bash
https://design-space.bytedance.net/d2c
```

Use bytedcli for agent-friendly command execution:

```bash
bytedcli design-space d2c --help
```

## Credential Boundary

bytedcli does not store or manage Design Space credentials. Provide them via the `CODIN_D2C_TOKEN` and `FIGMA_ACCESS_TOKEN` environment variables.

Before the first workflow, check credential status:

```bash
bytedcli design-space d2c auth status
```

If credentials are missing, configure the upstream D2C tokens:

```bash
export CODIN_D2C_TOKEN=<your-d2c-token>
export FIGMA_ACCESS_TOKEN=<your-figma-token>
bytedcli design-space d2c auth verify
```

Token values may already be present in the local user cache from a previous setup. Do not ask users to paste token values into chat.

## Figma Node Selection

When the user gives a Figma URL that points at a canvas, page, or large section, do not call `get-figma-data` directly. First suggest page-sized Figma nodes:

```bash
bytedcli --json design-space d2c node suggest \
  --url "https://www.figma.com/design/ABC123/Demo?node-id=1-2" \
  --limit 20
```

Use one returned Page Frame Candidate URL for D2C generation:

```bash
bytedcli design-space d2c get-figma-data \
  --url "https://www.figma.com/design/ABC123/Demo?node-id=3-4" \
  --directory "/absolute/project/path" \
  --platform web
```

Default node selection semantics:

- Page Frame Candidates are the recommended generation units.
- Section Groups organize related candidates and help choose a variant.
- Section Groups are not default generation units.
- If no candidates are found, ask the user to select a smaller Figma frame or confirm a different target.

## Supported D2C Commands

The bytedcli surface intentionally whitelists stable D2C commands:

```bash
bytedcli design-space d2c get-figma-data ...
bytedcli design-space d2c download-icons ...
bytedcli design-space d2c verify-code ...
bytedcli design-space d2c query-ui-rules ...
bytedcli design-space d2c cleanup-temp ...
bytedcli design-space d2c auth status
bytedcli design-space d2c auth verify
bytedcli design-space d2c commands
bytedcli design-space d2c schema --command get-figma-data
```

Runtime Design Review commands are not part of the supported bytedcli whitelist yet. Do not route ordinary D2C work through the hidden raw escape hatch unless debugging a missing upstream command.

## Standard Workflow

1. Detect the target project platform from the repository.
2. Verify credentials with `design-space d2c auth status` or `auth verify`.
3. If the Figma URL is broad, run `design-space d2c node suggest`.
4. Run `get-figma-data` with one candidate URL.
5. Read the XML/preview or generated H5 result according to the upstream D2C output.
6. Download icons only when needed.
7. Generate or adapt code in the target project.
8. Run `verify-code` once for non-H5 platforms.
9. Run `cleanup-temp` after the workflow is complete.
