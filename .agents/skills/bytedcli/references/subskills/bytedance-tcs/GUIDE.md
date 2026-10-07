# TCS / Rock

Use this route for TCS labeling or audit onboarding, Business, Scene, Jimu templates, Content Schema, Workflow, Queue, Rock cross-queue sampling, and Rock appeal configuration. TCS is unrelated to TCC and TCE; do not route configuration-center or deployment requests here.

The complete Skill is maintained with the official plugin:
https://code.byted.org/tiktok-tns-eng/bytedcli-plugin-tcs/blob/main/skills/bytedance-tcs/SKILL.md

## Bootstrap

1. Install and validate the official plugin if `bytedcli tcs` is unavailable:

```bash
bytedcli self plugin install --name tcs
bytedcli self plugin doctor --name tcs
```

The official package is `@bytedance-dev/bytedcli-plugin-tcs` and requires bytedcli `>=0.155.0`, Node.js `>=18`, and Python `>=3.9`.

2. Restart the Agent or MCP session after installation so the plugin Skill and command catalog are refreshed.
3. Load the installed `bytedance-tcs` Skill before constructing specs or selecting commands.
4. TCS uses SG MPSSO rather than ByteCloud JWT. Check or start login through the plugin:

```bash
bytedcli --json tcs auth status
bytedcli --json tcs auth login --region sg
```

5. Read runtime help before execution. Writes are dry-run by default and require an explicit repeat with `--yes` after the user confirms the same payload:

```bash
bytedcli tcs --help
bytedcli tcs <resource> --help
bytedcli --json tcs <resource> <operation> --spec-file ./spec.json --dry-run
```
