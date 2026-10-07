# Materials Input Reference

This reference describes how Oxygen materials are identified, how default
materials are resolved, and how to pass `--materials` to `bytedcli oxygen`
commands.

## Material uniqueId Convention

Every material is identified by its **uniqueId** (also called `EnName`), which
always starts with `@`:

```
@demo/material-a
@tiktok/some-material
```

Do **not** pass the material's display name or enName. The CLI validates that
each material value starts with `@` and rejects input that does not.

## Passing Materials Explicitly

Use the `--materials` option with comma-separated uniqueIds:

```bash
bytedcli oxygen devtask init \
  --product-key demo-product \
  --env ppe_test1 \
  --devtask-name oxy-materials-demo-20260903-a1b2c3 \
  --materials @demo/material-a,@demo/material-b

bytedcli oxygen devtask update \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3 \
  --materials @demo/material-a
```

The CLI parses the comma-separated string into an array, trims whitespace, and
filters empty entries.

## Default Materials Resolution

When `--materials` is omitted, the CLI resolves default materials from the
business-project root:

1. **`configs/editor.json`** — if it exists and contains a `uniqueId` field
   (or array of `uniqueId` values), those are used.
2. **`package.json`** — if `configs/editor.json` does not resolve materials, the
   `name` field is used, but only if it starts with `@`.

If neither source resolves to valid uniqueIds, the command fails and asks the
user to provide `--materials` manually.

## Materials in the Publish Workflow

In `oxygen devtask publish`:

- If `--materials` is passed, it is used as the target scope.
- If a fresh, not-yet-executed devtask exists with different materials,
  `update_devtask` can align the scope before its first execute.
- If the resolved devtask was already executed, do not update/re-execute it for
  a new code revision; choose a unique name and initialize a fresh devtask.
- If `--materials` is omitted, default resolution runs at init time.

## Creating a Missing Material

If a referenced material does not exist on Oxygen, the publish flow stops rather
than silently creating it. To create a material:

```bash
bytedcli oxygen material create \
  --product-key demo-product \
  --material-name @demo/new-material
```

This always requires explicit user confirmation.

## Listing Current Devtask Materials

```bash
bytedcli oxygen devtask materials \
  --product-key demo-product \
  --devtask-name oxy-materials-demo-20260903-a1b2c3
```

Returns the list of material uniqueIds currently configured in the devtask.
