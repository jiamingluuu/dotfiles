---
name: "d2c-evaluation-workflow"
description: "Evaluate a rendered D2C page against its Figma reference. Always produces aligned images, pixel diff, and score for Lynx or H5; for Lynx, additionally consumes the usable captured UI Tree, maps Figma/runtime nodes, and emits geometry metrics and a geometry report for refine."
allowed-tools: Bash, Read
---

# Role

Act as the single public evaluation facade between capture and refine:

- Always run remote image alignment, diff, and scoring via `bytedcli d2c screenshot compare`.
- For Lynx, additionally run deterministic UI-tree geometry evaluation via `bytedcli d2c geometry evaluate` when a usable captured tree exists.
- Point both commands at the same `--output-dir` so downstream refine reads one evaluation directory.

Do not build or capture here. Use `lynx-build-and-capture` for Lynx and `d2c-render-screenshot` for H5/browser first.

# Input contract

`d2c screenshot compare` — required for every target:

- `--reference-image <path>` — original comparison PNG. Use `input_image.png`, never `screenshot.raw.png`.
- `--output-dir <dir>` — evaluation output directory.
- One rendered candidate:
  - `--candidate-image <path>`, or
  - Lynx `--capture-output-dir <dir>`, which defaults the candidate to `<dir>/device-screenshot.png`.

Common optional flags:

- `--project-root <dir>` — base for relative paths.
- `--compare-options <json>` / `--align-options <json>` — forwarded to the comparison service.
- `--timeout-ms <ms>` — per-request timeout.

`d2c geometry evaluate` — Lynx only, all three required:

- `--figma-json <path>` — Figma node JSON, or layout-only `origin.json`.
- `--runtime-tree <path>` — the captured `lynx-ui-tree.json` from the Lynx capture step.
- `--output-dir <dir>` — directory to write the geometry report into.

Geometry optional flags:

- `--figma-node-id <id>` — explicit Figma root node.
- `--previous-report <path>` — previous round's `geometry-report.json`, enabling the stable Figma ID + runtime path trend.
- `--top-k <n>` — worst-node count, default 10.

Geometry runs entirely offline against local files; it needs no Figma credential and performs no raw-node fetch. Never print or persist a token.

# Output contract

`d2c screenshot compare` writes the image artifacts into `--output-dir`:

- `figma.png`, `device.png`
- `aligned.figma.png`, `aligned.device.png`
- `diff_result.png`
- `evaluation-result.json`
- `response.json`

Prior artifacts in `--output-dir` are discarded first, so a failed round cannot silently report the previous round's output.

Evidence states, read from the two commands' results rather than from a manifest file:

- Image evidence is usable when `evaluation-result.json` carries a score and both aligned images plus the diff exist.
- H5/browser: geometry is **not-applicable** — `d2c geometry evaluate` is Lynx-only and simply is not run. This is a normal state, not a failure.
- Lynx without a usable tree or without Figma geometry: geometry reports **insufficient-evidence** with a reason; image evaluation remains valid.
- Lynx with sufficient evidence: geometry reports **usable**, with metrics, Top-K, and report paths.

When geometry runs, it also writes:

- `geometry/geometry-report.json` — matches, IoU, center deviation, size error, coverage, Top-K, and stable-pair trend.
- `geometry/geometry-report.md` — concise readable summary.

# Workflow

Before each phase, state in exactly one short sentence what happens next.

## 1. Preparation

- Confirm the reference PNG exists and is non-empty.
- Confirm the explicit candidate exists, or Lynx capture contains `device-screenshot.png`.
- For Lynx, also confirm the capture directory holds a usable `lynx-ui-tree.json` and that `origin.json` (or raw Figma node JSON) is available for geometry.
- Do not start a local devtool/browser or rebuild the page.

## 2. Execution

For H5/browser, run image evaluation only:

```bash
bytedcli --json d2c screenshot compare \
  --reference-image "<figma2codeDir>/input_image.png" \
  --candidate-image "<browserCapturePath>" \
  --output-dir "<evaluationOutputDir>"
```

For Lynx, run image evaluation against the capture directory, then geometry against the captured UI tree:

```bash
bytedcli --json d2c screenshot compare \
  --reference-image "<figma2codeDir>/input_image.png" \
  --capture-output-dir "<captureOutputDir>" \
  --output-dir "<evaluationOutputDir>"

bytedcli --json d2c geometry evaluate \
  --figma-json "<figma2codeDir>/origin.json" \
  --runtime-tree "<captureOutputDir>/lynx-ui-tree.json" \
  --output-dir "<evaluationOutputDir>/geometry"
```

From round 2 onward, add to the geometry call:

```bash
  --previous-report "<previousEvaluationOutputDir>/geometry/geometry-report.json"
```

## 3. Monitor

- Treat image-compare HTTP failure as evaluation failure.
- Before reusing an output directory, discard its prior image-evaluation response, result, aligned images, and diff. `d2c screenshot compare` does this for you.
- Treat a non-object or incomplete image-compare response as evaluation failure. Require both aligned images, the diff image, and the score; never call image evidence usable from partial evidence.
- Treat geometry failure as `insufficient-evidence`; do not discard successful image artifacts.
- Never claim node-level metrics unless a geometry report was actually generated.

## 4. Verify and hand off

- Confirm `evaluation-result.json` and the image diff artifacts exist, plus `geometry/geometry-report.json` when geometry ran.
- Read both the image evidence state and the geometry state.
- For usable geometry, inspect coverage, primary metrics, worst nodes, and stable-pair trend—not only averages.
- Pass the absolute `evaluation-result.json` path, and `geometry/geometry-report.json` when present, to `d2c-refine-workflow` via `sourceEvidencePaths`.
