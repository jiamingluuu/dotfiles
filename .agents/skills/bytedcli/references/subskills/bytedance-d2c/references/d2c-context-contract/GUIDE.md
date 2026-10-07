---
name: d2c-context-contract
description: Create, validate, or consume reusable Design-to-Code context contracts for Figma-to-Lynx/browser workflows. Use when a user asks to standardize d2c_context, generate d2c.contract.json, define business-generated D2C constraints, enforce component mapping/token/data protocol rules, validate D2C contract folders, or turn ad hoc D2C execution notes into a reusable skill/context package.
---

# D2C Context Contract

Use this skill to make D2C context explicit, portable, and business-generated. The contract replaces ad hoc agent notes with files that can be validated before code generation.

## Expected Folder

Prefer this shape:

```text
d2c_context/
  d2c.contract.json
  figma.protocol.json
  AGENT_GUIDE.md
  <business-authored-rule-files>.md
  schema/
    d2c-context.schema.json
```

`d2c.contract.json` is the task-specific contract instance. `schema/d2c-context.schema.json` validates that instance. `figma.protocol.json` stores design evidence. `AGENT_GUIDE.md` is a short human-readable guide generated from the contract. Business-authored markdown rule files may live at any relative path inside `d2c_context/`; list them explicitly in `agentRuleFiles`.

## Workflow

0. If explaining how a business should integrate this contract, read `references/business-integration.md` and answer from that user-facing onboarding flow.
1. If creating a contract, read `references/contract-spec.md` and generate `d2c.contract.json`, `figma.protocol.json` if design evidence exists, `AGENT_GUIDE.md`, and optional business rule markdown files referenced by `agentRuleFiles`.
2. If validating a contract, run `bytedcli --json d2c contract validate --contract <path-to-d2c_context-or-d2c.contract.json>`.
3. If consuming a contract for D2C implementation, read `d2c.contract.json` first, then read `AGENT_GUIDE.md`, then read any files listed in `agentRuleFiles`, then only read referenced protocol files needed for the selected component or page.
4. Enforce hard policies before implementation:
   - The contract and referenced protocol files are the source of truth for package names, versions, variants, props, node structure, styles, assets, token mappings, and runtime data states.
   - For a selected component/page, resolve by `nodeId` or `componentName` before implementation, then read the matching mapping and design node evidence.
   - Mapped components must be tried before primitive fallback.
   - Missing mapped packages must be installed as `packageName@targetVersion`.
   - Registry/404/private package failures must be retried using the contract's configured registry fallback before primitive fallback.
   - Theme token mappings must be applied before hardcoded fallback colors.
   - Runtime visual states must come from `dataProtocolMappings` when design evidence requires component state.
   - Version changes marked for design review must not be changed during implementation without explicit user approval.
   - Fallback is allowed only after install/import/runtime evidence fails, and the evidence must be recorded.
5. Treat missing required contract fields as a blocker for generation quality, not as permission to guess.

## Key Distinctions

- `d2c.contract.json`: business-generated constraints and policies for one D2C task.
- `d2c-context.schema.json`: reusable JSON Schema that validates the contract.
- `figma.protocol.json`: evidence extracted from Figma/component planner.
- `AGENT_GUIDE.md`: concise instructions for agents, derived from the contract.
- `agentRuleFiles`: business-authored markdown files for coding standards, component usage notes, naming/style rules, and framework-specific constraints.

## Resources

- Read `references/business-integration.md` when a user asks how their business or infrastructure should integrate this skill.
- Read `references/contract-spec.md` when generating or editing contract content.
- Use `references/d2c-context.schema.json` as the baseline schema when the project does not already provide one.
- Run `bytedcli --json d2c contract validate --contract <path-to-d2c_context-or-d2c.contract.json>` to check JSON syntax and required D2C fields.
