---
name: bytedance-iconbox
description: "Use when the user needs to inspect an IconBox library URL, list its groups or icons, upload local SVG icons, or export React/Vue packages, CDN URLs, or font files from IconBox."
---

# ByteDance IconBox

Use `bytedcli iconbox` for IconBox library inspection, SVG uploads, and exports.

## Authentication

IconBox reuses the ByteDance SSO browser session and exchanges it for a short-lived IconBox OAuth cookie in memory. If authentication fails, run:

```bash
bytedcli auth login --session --auto --yes
```

Do not copy browser cookies into commands, files, logs, or prompts.

## Inspect a library

Prefer the original library URL when the user provides one:

```bash
bytedcli --json iconbox library get --library-url 'https://arco.bytedance.net/iconbox/mime/lib/123/0'
bytedcli --json iconbox icon list --library-url 'https://arco.bytedance.net/iconbox/mime/lib/123/0' --page-size 50
bytedcli --json iconbox icon list --library-id 123 --keyword sample
```

`library get` returns the library name, owner, writable status, icon count, and group IDs/names.

## Upload SVG icons

Uploads are dry-run by default. First review the resolved destination:

```bash
bytedcli --json iconbox icon upload --library-url 'https://arco.bytedance.net/iconbox/mime/lib/123/0' --file ./sample-icon.svg --group-name Default
```

Then repeat with `--yes`:

```bash
bytedcli --json iconbox icon upload --library-url 'https://arco.bytedance.net/iconbox/mime/lib/123/0' --file ./sample-icon.svg --group-name Default --yes
```

For batch upload, repeat `--file`; each SVG basename becomes the icon name:

```bash
bytedcli --json iconbox icon upload --library-id 123 --file ./add.svg --file ./close.svg --group-id 456 --yes
```

Use `--name` and `--name-cn` only with a single file. Icon names allow letters, numbers, underscores, and hyphens.

IconBox fade mode is enabled by default, matching the web UI. Add `--preserve-color` when the SVG's original colors must be kept.

## Export packages and URLs

React and Vue exports publish NPM packages. They are dry-run by default, so inspect the resolved package name, next version, and SVG attribute settings before adding `--yes`:

```bash
bytedcli --json iconbox package export --language react --library-id 123
bytedcli --json iconbox package export --language react --library-id 123 --version 1.2.3 --yes
bytedcli --json iconbox package export --language vue --library-id 123 --keep-color true
```

When the settings are omitted, bytedcli inherits the latest package settings for that language. A first release defaults to keeping `fill="none"` and default fill attributes while not preserving original colors.

CDN export returns the CSS, Less, and JS URLs without publishing a new package:

```bash
bytedcli --json iconbox cdn export --library-id 123
bytedcli --json iconbox cdn export --library-id 123 --icon-id 456 --icon-id 789
```

Font export downloads a ZIP file. Existing files are not overwritten unless `--force` is present:

```bash
bytedcli --json iconbox font download --library-id 123 --output ./iconbox-font.zip
bytedcli --json iconbox font download --library-id 123 --icon-id 456 --output ./selected-font.zip --force
```

Omitting `--icon-id` exports the whole library. Repeat `--icon-id` to export a selected subset for CDN or font output.

If IconBox reports that package settings changed, inspect the server message before repeating the publish with both `--yes` and `--confirm-setting-change`. Do not add the confirmation flag preemptively.
