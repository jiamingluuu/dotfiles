# AGW BFFv2 route troubleshooting

## Env current version differs from newly created config version

`agw config create` creates a new config version but does not by itself prove that an env's current config changed. Re-check the target env:

```bash
bytedcli --site cn --json agw config get --service-id <id> --env <env> --need-all-config
```

Use that `config.version` as the base version when the user says "current env config".

## Backend method not found

Use:

```bash
bytedcli --site cn --json agw bffv2 batch-route create --service-id <id> --base-version <version> --template <template> --route <thrift-backend-psm>:<METHOD>:<PATH>:<RPC_METHOD>
```

`batch-route create` currently validates thrift backends only. If the thrift method is absent, update global `bff_v2_backends_config` first with `backend-idl update --backend-idl thrift:<psm>:<version>`. Do not render against an ad hoc IDL version.

## Invalid backend API format

Use protocol-aware format:

```text
thrift:<psm>:<method>
http:<psm>:<method>
http-no-idl:<psm>:<method>
tcc:<psm>:<method>
rpc-http:<psm>:<method>
```

## TYPE_DSL section changed

`dsl-workspace export` fails if `TYPE_DSL` changed. Restore the readonly section or regenerate the workspace, then edit only `HANDLE_DSL`.

## Path/method already exists

Choose a different route path/method or inspect existing routes:

```bash
bytedcli --site cn agw bffv2 route list --service-id <id> --version <version>
```

## Client IDL method conflict

Leave `--frontend-idl-method-name` empty by default. If multiple routes use the same backend method and client IDL generation conflicts, set a unique frontend method name on one of the routes during `route create`.

## Publish order succeeded but traffic not changed

Check publish detail and pipeline status:

```bash
bytedcli --site cn --json agw publish order get --publish-id <publish-id>
```

For sidecar services, env deploy commands may not apply; publish config through AGW publish order/direct flow as appropriate.
