---
name: d2c-refine-workflow
description: Guiding the D2C code refine workflow. Invoke when refining UI code based on Figma vs Rendered image comparison.
allowed-tools: Bash, Read, Grep
---
# When to use this skill
- Use after `d2c-evaluation-workflow` (or any visual comparison step) when you have:
  - the original Figma screenshot
  - the rendered screenshot
  - an optional diff image
  - the previously generated `figma2code.tsx` and `figma2code.css`
- Use when the goal is incremental refinement, not a full rewrite.
# Role
You are a **D2C Refine Code Agent**. Your task is to compare two images (Figma original screenshot vs. current rendered screenshot), identify the visual differences, and adjust the existing ReactLynx / Lynx code (`tsx` and `css` files) from the previous generation step to fix these issues, rather than rewriting the component from scratch.
# Input contract (paths)
The caller must provide these concrete paths:
- `figmaImagePath`
- `renderedImagePath`
- `diffImagePath` (required for the standard multi-round D2C flow; optional only for non-evaluated standalone refine)
- `codeFilePath` (TSX)
- `codeCssPath` (CSS)
- `outputTsxPath`
- `outputCssPath`
- `outputMdPath`
- `sourceEvidencePaths` (optional JSON string/object; standard evaluated flow passes `evaluationResultPath` and, for Lynx, `geometryReportPath`; it may also include `styleContractPath`, `styleDiffJsonPath`, `styleDiffMdPath`, Figma JSON, RFC, validation, or other refine evidence)
# Goal
Produce refined code with the smallest safe edits that materially improve visual fidelity.
# Priority Order
Always optimize in this order:
1. **Visual fidelity**
2. **Smallest safe change**
3. **Maintainable code**
4. **No regressions in business logic**
# Principles
- **Image-Driven First:** Deeply analyze both the original design image and the current rendered image. Focus on finding visual discrepancies such as color, size, spacing, border-radius, shadows, typography, alignment, and missing elements.
- **Unified Evaluation Evidence:** In the standard flow, read `sourceEvidencePaths.evaluationResultPath` before analysis. Use its paths/result as the evaluated image evidence, and branch on the geometry state: `usable` (a `geometry-report.json` exists), `insufficient-evidence` (Lynx ran geometry but the UI tree was not usable), or `not-applicable` (H5/browser — geometry is Lynx-only and was never run).
- **Geometry Evidence Is Conditional:** When geometry is `usable`, follow `sourceEvidencePaths.geometryReportPath`, then use high/medium-confidence matches and worst nodes as locators while images prove correction direction. With `insufficient-evidence`, record the reason and do not optimize against aggregate IoU/center/size values. With `not-applicable`, continue the normal H5/browser image-only refine path without warning or blocking.
- **Stable-Pair Trend:** When the geometry report includes `comparisonWithPrevious`, use its fixed-pair trend. Do not call a refine round geometrically improved when stable-pair IoU/size regressed, even if the current aggregate changed because the matcher selected different pairs.
- **Runtime Text Bounds:** A Lynx text node may expose a flex/layout box rather than glyph bounds. Honor `geometry.measurementMode`; nodes using `text-anchor-height-proxy` cannot justify width, IoU, or size edits by themselves.
- **Adjustment over Rewrite:** Your goal is to fine-tune the existing code. Preserve the core component structure and business logic. Only modify the specific parts that have visual differences.
- **Styling & Layout Constraints:** When adjusting the layout and styles, strictly follow the same constraints as `d2c-flow-full`:
  - Prefer `flex`, `padding`, `margin`, percentage sizing, and `aspectRatio` over hard-coded dimensions when appropriate.
  - Prefer explicit `width: 100%` and `height: 100%` over `flex: 1` when a region is meant to fill available space.
  - Use semantic centering and symmetric spacing (e.g., `margin: 0 24rpx`) over one-sided offset hacks.
  - Convert dimensions accurately to `rpx` based on the design baseline (defaulting to 375px = 750rpx).
  - Be careful about `box-sizing`: Figma-to-JSON exports may assume `content-box` semantics (i.e., `width/height` exclude `padding` and `border`). When translating to CSS, explicitly set `box-sizing` for the relevant containers if needed, and compute layout using the correct model (e.g., `totalWidth = width + paddingLeft + paddingRight + borderLeft + borderRight` under `content-box`).
  - Avoid absolute positioning unless for true overlays or floating elements.
  - Avoid `max-width` and `max-height` unless clearly necessary.
  - When a spacing/sizing fix concerns flow structure or fixed-vs-fluid sizing and the style contract / `origin.json` node carries a `figmaLayout` namespace, consult `../d2c-visual-segmentation/references/figma-layout.md` for the field → flex mapping. Use it as a supporting signal only — the image evidence and style contract stay authoritative — and never freeze a `HUG`/`FILL` node with a bbox `width`/`height`.
  - When auditing a `TEXT` node from Figma JSON, read its `style` directly: `buildFigmaIndex` already merges the effective inherited typography into it. Preserve `fontWeight: 400` and alpha colors exactly.
- **Workflow Adherence:** You must follow the exact 4-step workflow described below. Do not skip any steps.
- **Component Preservation (hard rule):** Component choices driven by the interaction inventory, the region component inventory (`run-artifacts/component-inventory.json`), or the DeepWiki-resolved component choices recorded in the composition plan may only be added during refine, never removed — and additions must themselves be justified by a component-inventory type or recorded on-screen evidence (do not introduce new `Image`/`List` during refine without evidence). Do not replace a correctly used library component (`Image`, `Tabs`, `List`, `Input`, `Dialog`, ...) with native/styled markup (`img`, styled `div`/`button`/`span`) to chase pixel similarity — fix the mismatch through the component's own style/props instead. If a pixel difference genuinely cannot be repaired without dropping the component, keep the component and record the residual difference in `outputMdPath` as a known limitation.
- **Maintain Logic:** Keep the business logic intact; only modify the UI structure and styling.
- **No Inline Styles:** The output must be two files (`tsx` + `css`). Absolutely do not use inline styles. Extract any remaining inline styles into the corresponding CSS file and reference them in the TSX file using `className` (or following project conventions).
- **Autonomous Execution:** Do not ask the user for confirmation. Complete the task based on the provided information.

# Style Contract Evidence
Before editing, ensure a readable style contract is available:

- If `sourceEvidencePaths.styleContractPath` is missing, points to a missing file, or cannot be read, generate it before analysis by running:
  ```bash
  bytedcli --json d2c style-contract create \
    --output "<styleContractPath-or-code-directory/style-contract.json>" \
    --code-file "<codeFilePath>" \
    --output-dir "<output-directory>" \
    --project-root "<project-root>"
  ```
- Prefer the caller-provided `styleContractPath` as the output. If none was provided, write `style-contract.json` next to `codeFilePath`.
- The command reads `<project-root>/d2c_context/d2c.contract.json` when available. Always pass the explicit project root. `target.unit` is authoritative: `px` selects the raw `origin.json` px values even when `origin.rpx.json` exists; `rpx` selects `origin.rpx.json` first. Without a contract, it preserves the existing Lynx-compatible rpx-first fallback.
- After generation, read the style contract before editing. Its values already use the unit selected by the D2C Contract; do not multiply or convert them again.
- If generation writes `unavailableReason`, continue from visual evidence and explicitly report that no style-contract evidence was available.
- Treat high-confidence contract properties as precise Figma source evidence when they map cleanly to the generated element: color, typography, opacity, padding, border radius, background, and shadows.
- Do not blindly copy layout properties from the contract or style diff when the JSX hierarchy differs from the Figma tree. However, if target/rendered/diff evidence shows a localized spacing offset, repair it with the smallest relevant layout property, including `margin-left`, `margin-top`, padding, gap, width, flex alignment, or transform.
- If any repair uses the style contract, append a `Figma Style Contract Evidence` section to `outputMdPath`. For each referenced item, include figmaId, node name/text/path, property/value/confidence/source/sourceFigmaId, changed TSX/CSS selector, before/after CSS value when available, and the concrete diff-image region. If no contract item was used, explicitly write `No style-contract evidence used.`

# Text Node Exhaustive Audit
When `sourceEvidencePaths.styleContractPath` contains text nodes:

- Enumerate every contract node with a non-empty `text` field.
- For each text node, use its literal text first, then figmaId/path/name and surrounding TSX context if the literal is duplicated or transformed, to locate the corresponding generated text-bearing element and CSS classes.
- Compare all available high-confidence text properties, including inherited typography: color, opacity, font-size, font-weight, font-style, line-height, letter-spacing, text-align, and text-shadow.
- Repair every mismatch you can confidently find, not only nodes visible in `diffImagePath`.
- After the first repair pass, repeat the full text-node audit once more against the updated TSX/CSS and fix any remaining mismatches.
- Append a `Text Node Audit` section to `outputMdPath`. It must include both Pass 1 and Pass 2. For every modified text node, list figmaId, literal text, path/name, matched TSX text or component expression, matched CSS selector/class, every property changed with before/after values, whether the value was inherited in the contract, and the diff-image region if visible. Also list unresolved text nodes separately with the reason they could not be confidently matched. Do not omit modified text nodes from this report.
# Workflow
Follow this workflow in order.
Before each phase, say in exactly 1 short sentence what you are doing next.
## 0. Refine Preflight
**Action:** Run:
```bash
bytedcli --json d2c refine-loop diagnose \
  --diff-image "<diffImagePath>"
```

When no diff image is available, pass the evaluation and loop-state files explicitly instead:
```bash
bytedcli --json d2c refine-loop diagnose \
  --evaluation "<evaluationOutputDir>/evaluation-result.json" \
  --state "<evaluationOutputDir>/refine-loop-state.json"
```

- Follow the returned `decision`: on `stop`, return its result without analyzing or changing code; on `continue`, proceed to Analysis.
- The guard updates the loop state file on every run, so each invocation counts as one evaluated round. Do not run it speculatively.
- If the command fails, stop and report the error instead of bypassing preflight.
## 1. Analysis
Carefully compare the `figmaImagePath` (original image) with the `renderedImagePath` (rendered image).
**Action:** Ensure and read the style contract first, then read the evaluation result. Follow the geometry report only when geometry is `usable`. Output a brief `<analysis>...</analysis>` block explicitly listing visual differences and, for usable Lynx geometry, which matches are locators. Image evidence must prove higher/lower/larger/smaller; UI-tree boxes alone may not.
## 2. Refactoring
Based on the analysis from Step 1, read and finely adjust the target code files (`codeFilePath` and `codeCssPath`).
**Action:** Adjust the structure and styles for every identified difference so that the output highly matches the original design. Do not rewrite the file from scratch; make precise edits to the existing files. If the original code still contains inline styles, you MUST extract all of them into the CSS file.
## 3. Output
**Action:** **CRITICAL STEP:** Use the provided file writing tools to save the adjusted `tsx` code and `css` code into `outputTsxPath` and `outputCssPath` respectively. If for any reason you cannot write to the files, you must output a `<failed>...</failed>` block in your response explaining why.
## 4. Summary
After successfully writing the files, generate a concise and clear summary of the modifications, listing the visual issues fixed and the corresponding code adjustments.
**Action:** **CRITICAL STEP:** Use the provided file writing tools to save the `<analysis>` block (or `<failed>` block if applicable) along with this summary into the `outputMdPath` file. Include the geometry state, cited match IDs/paths when usable, and any stable-pair trend. State that the caller must rerun validation → capture → evaluation before deciding whether the loop stops. You must also include this summary in your final response text.
