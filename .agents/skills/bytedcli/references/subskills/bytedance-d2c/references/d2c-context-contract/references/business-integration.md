# Business Integration Guide

Use this guide when explaining how a business team should integrate `d2c-context-contract` with its own design-to-code infrastructure.

## What This Skill Provides

`d2c-context-contract` defines a portable contract format for D2C context. It lets a business team expose its own component library, token system, runtime data protocol, design evidence, and coding rules to an agent without hardcoding those rules into the global skill.

The skill is not a business component library and does not prescribe package names, theme systems, registry URLs, rule file paths, or framework-specific conventions. The business owns those details in the generated `d2c_context/` package.

## Integration Model

The business integration should generate a `d2c_context/` directory for each D2C task, page, or component set.

Required files:

```text
d2c_context/
  d2c.contract.json
  AGENT_GUIDE.md
```

Common optional files:

```text
d2c_context/
  figma.protocol.json
  schema/d2c-context.schema.json
  <any-business-rule-file>.md
```

Business rule markdown files can use any names and any folder structure. The only requirement is that `d2c.contract.json` lists every rule file the agent must read in `agentRuleFiles`.

```json
{
  "agentRuleFiles": [
    "rules.md",
    "platform/lynx.md",
    "team/style-guide.md"
  ]
}
```

Paths are relative to `d2c_context/`. Agents must read these files after `AGENT_GUIDE.md` and before implementation.

## Business Responsibilities

The business infrastructure should translate business knowledge into contract files:

- Component recognition and component library routing go into `componentMappings[]`.
- Theme variables, style tokens, generated token modules, or raw token fallbacks go into `tokenMappings[]`.
- Visual states that depend on runtime data go into `dataProtocolMappings[]`.
- Dependency and fallback policy goes into `dependencyPolicy`.
- Validation expectations go into `validation`.
- Human-authored coding rules go into markdown files referenced by `agentRuleFiles`.
- Figma or planner evidence goes into `figma.protocol.json` or another protocol file referenced by the contract.

## Recommended Onboarding Steps

1. Install the skill for the target agent.
2. Add a generator in the business D2C pipeline that emits `d2c_context/`.
3. Emit `d2c.contract.json` with target, dependency policy, mappings, data protocol, validation, and `agentRuleFiles`.
4. Emit `AGENT_GUIDE.md` from the contract. Keep it short and procedural.
5. Emit any business-authored markdown rule files needed for code style, component usage, platform behavior, mock data, naming, or validation.
6. Run `bytedcli --json d2c contract validate --contract ./d2c_context` in local checks or CI.
7. Pass the generated `d2c_context/` to the D2C agent along with the design task.

## Minimal Contract Shape

```json
{
  "schemaVersion": "d2c-context/v1",
  "target": {
    "platform": "lynx-ttml",
    "styleLanguage": "less",
    "unit": "rpx"
  },
  "dependencyPolicy": {
    "componentMappingFirst": true,
    "installMissingMappedPackages": true,
    "registryFallback": ["https://registry.example.com"],
    "fallbackRequiresEvidence": true
  },
  "componentMappings": [],
  "tokenMappings": [],
  "dataProtocolMappings": [],
  "agentRuleFiles": [],
  "validation": {}
}
```

Replace `registryFallback` with the registry or registries required by the business environment. If no fallback registry exists, use an empty array only when the business accepts that registry failures may block component installation.

## Component Mappings

Use `componentMappings[]` to tell the agent which real business component should implement a design node.

```json
{
  "nodeId": "<figma-node-id>",
  "nodeName": "<figma-node-name>",
  "packageName": "<component-package-name>",
  "componentName": "<component-export-or-tag-name>",
  "targetVersion": "<package-version-or-range>",
  "variantProperties": {},
  "props": {},
  "propsPatch": {},
  "tokenMappingIds": [],
  "decisionStatus": "ready"
}
```

The agent should attempt `packageName@targetVersion` before primitive fallback. If fallback is used, the agent must record installation, import, registration, runtime, or platform-entry evidence.

## Token Mappings

Use `tokenMappings[]` to map design tokens or variables to the target project token system.

```json
{
  "id": "<token-mapping-id>",
  "designToken": "<figma-variable-or-style-name>",
  "rawValue": "<resolved-design-value>",
  "codeToken": "<project-token-reference>",
  "codeUsage": {
    "language": "<css|less|scss|js|ts>",
    "import": "<optional-project-token-import>",
    "snippet": "<optional-usage-snippet>"
  },
  "usages": []
}
```

`codeUsage` is intentionally open. A business may use CSS custom properties, Less variables, Sass variables, generated token modules, JS theme objects, or raw values.

## Runtime Data Protocol

Use `dataProtocolMappings[]` when a visual state cannot be restored by styles alone.

```json
{
  "id": "<data-protocol-mapping-id>",
  "targetComponent": "<component-package-or-name>",
  "figmaEvidence": {
    "nodeId": "<figma-node-id>",
    "nodeName": "<figma-node-name>"
  },
  "requiredState": [
    {
      "dataPath": "<runtime-data-path>",
      "valueKind": "<value-kind>",
      "value": "<optional-required-value>",
      "reason": "<why-this-state-is-required>"
    }
  ]
}
```

Use this for badges, disabled states, follow states, live states, experiment variants, remote image variants, or any component visual controlled by business data.

## Business Rule Markdown

Use markdown files referenced by `agentRuleFiles` for rules that are too textual, contextual, or business-specific for JSON.

Good content for rule files:

- component usage dos and don'ts
- code style and naming conventions
- wrappers that must be used for images, links, analytics, logging, or navigation
- platform constraints
- data mocking conventions
- validation commands
- small examples that are specific to the business integration

Avoid putting large design evidence in these files. Design evidence belongs in protocol files, and machine-readable mappings belong in `d2c.contract.json`.

If a markdown rule conflicts with `d2c.contract.json`, the contract wins unless the user explicitly asks to change the contract.

## Validation

Run the validator against the generated context:

```bash
bytedcli --json d2c contract validate --contract ./d2c_context
```

The command checks required contract fields, mapping shapes, `AGENT_GUIDE.md`, and whether every `agentRuleFiles[]` entry points to an existing markdown file.

## Agent Consumption Order

Agents should consume a generated context in this order:

1. Read `d2c.contract.json`.
2. Read `AGENT_GUIDE.md`.
3. Read every markdown file listed in `agentRuleFiles`, in order.
4. Read only the protocol evidence needed for the selected page or component.
5. Implement using mapped components and mapped tokens before fallback.
6. Provide runtime data states required by `dataProtocolMappings[]`.
7. Run the validations required by the contract.

## Mental Model

The business integration owns the facts. The skill owns the protocol for delivering those facts to agents.

Do not fork the skill for each business. Generate richer `d2c_context/` packages instead.
