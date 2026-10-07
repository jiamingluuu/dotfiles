# BFFv2 DSL workspace

`dsl-workspace import` converts a rendered `BFFV2RouteConfig` JSON object into TypeScript files that are easier for users and agents to review.

## File layout

```text
bffv2-dsl/
├── README.md
├── bff-config.meta.json
├── tsconfig.json
├── response.dsl.ts
├── backend-0.dsl.ts
└── backend-1.dsl.ts
```

Each `*.dsl.ts` file combines generated `type_dsl` and editable `handle_dsl`:

```ts
// @bytedcli-bffv2:begin-type-dsl readonly sha256=<hash>
// generated type_dsl, readonly
// @bytedcli-bffv2:end-type-dsl

// @bytedcli-bffv2:begin-handle-dsl editable
// generated handle_dsl, edit this section only
// @bytedcli-bffv2:end-handle-dsl
```

## Review rule

Edit only `HANDLE_DSL` sections.

The `TYPE_DSL` section is generated from request/backend IDL and render output. It provides local TypeScript types, syntax highlighting, and jump-to-definition. `dsl-workspace export` re-hashes the type section and fails if it changed.

## Pack rule

```bash
bytedcli --site cn --json agw bffv2 dsl-workspace export \
  --workspace ./bffv2-dsl \
  --output-file reviewed-bff-config.json
```

`dsl-workspace export`:

1. Reads `bff-config.meta.json`.
2. Splits each `*.dsl.ts` by bytedcli markers.
3. Verifies `TYPE_DSL` hash.
4. Writes only `HANDLE_DSL` edits back into the BFFv2 config.
5. Produces `reviewed-bff-config.json` for `route create`.

When `dsl-workspace import` receives a BFF config that contains `req_parser.idl`, it also writes `request.idl.thrift` and `bff-config.rendered.json` into the workspace. For artifact workspaces, keep editing that single `request.idl.thrift` file; do not create a second workspace such as `dsl-workspace-reviewed`.

## Refresh-types workflow

Request IDL and backend IDL are coupled with `TYPE_DSL`. Whenever either IDL config changes, rerun `agw bffv2 dsl create` with the latest IDL before creating a workspace, packing edits, or generating a route plan. This refresh updates `type_dsl` only; `handle_dsl` is user-maintained and should stay unchanged.

Use the latest render result as the source of truth for `TYPE_DSL`. Preserve user-edited `HANDLE_DSL` sections unchanged unless the user explicitly asks to adapt handle logic. Run TypeScript checking if possible to catch handle code broken by IDL changes.

In an artifact workspace, refresh by running `agw bffv2 dsl create` from the artifact/workspace. Do not rerun `agw bffv2 dsl-workspace import --output-dir ...` against the existing workspace; that command is for creating a new workspace from a BFF config and refuses to overwrite non-empty directories.
