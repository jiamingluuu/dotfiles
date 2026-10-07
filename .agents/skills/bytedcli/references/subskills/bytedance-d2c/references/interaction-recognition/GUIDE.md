---
name: interaction-recognition
description: Target-agnostic interaction inventory recognition and target mapping references shared by Lynx and browser D2C workflows.
allowed-tools: Read, Write, Edit, Grep
---
# Interaction Recognition

Use this skill when a D2C workflow needs to infer, review, or consume `interactionInventory` for Figma designs.

## Required Reads

Always read:

- `references/interaction-recognition-playbook.md`
- `references/interaction-target-mapping.md`

## Scope

- The playbook is the source of truth for target-agnostic interaction recognition.
- The target mapping is the source of truth for how recognized `Interaction` classes should influence Lynx and browser generation.
- Do not add Lynx-only or browser-only recognition rules to the playbook. Put target-specific consumption guidance in the target mapping.

## Output Artifact

When the caller asks you to create an interaction inventory, always write a JSON file at the caller-provided path, normally:

`<figma2codeDir>/run-artifacts/interaction-inventory.json`

Use this artifact shape:

```json
{
  "schemaVersion": 1,
  "figmaUrl": "<figmaUrl>",
  "source": "inferred",
  "interactions": []
}
```

If no supported interaction is visible, keep `interactions` as an empty array. If recognition cannot be completed because required evidence is unreadable, write the empty artifact and report the reason to the caller.

Do not implement target-specific components here. This skill only classifies target-agnostic page interactions. Lynx/browser assembly consumes the artifact in `global-assembly`. The region-level component inventory (`run-artifacts/component-inventory.json`) is produced upstream by visual segmentation, not by this skill; the target skill maps its component TYPES to concrete library components.
