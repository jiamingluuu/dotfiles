# ByteDog Authentication

ByteDog API requires a ByteCloud JWT token for authentication. The `bytedcli bytedog` commands handle JWT acquisition and injection automatically via the global `--site` option.

## URL host to auth site

When the user provides a ByteDog page or console URL, choose the `bytedcli --site` value from the URL host.

| ByteDog URL host                | `bytedcli --site` | SSO/auth area            | Auth check                                   | Login command                        |
| ------------------------------- | ----------------- | ------------------------ | -------------------------------------------- | ------------------------------------ |
| `bytedog.bytedance.net`         | `cn`              | ByteDance SSO / CN       | `bytedcli --site cn --json auth status`      | `bytedcli --site cn auth login`      |
| `bytedog-sinf.bytedance.net`    | `sinf-cn`         | ByteDance SSO / CN       | `bytedcli --site sinf-cn --json auth status` | `bytedcli --site sinf-cn auth login` |
| `bytedog-boe.bytedance.net`     | `boe`             | BOE test SSO             | `bytedcli --site boe --json auth status`     | `bytedcli --site boe auth login`     |
| `bytedog.byteintl.net`          | `i18n-bd`         | ByteDance SSO / ByteIntl | `bytedcli --site i18n-bd --json auth status` | `bytedcli --site i18n-bd auth login` |
| `bytedog-i18n.bytedance.net`    | `i18n-tt`         | TikTok SSO / ROW         | `bytedcli --site i18n-tt --json auth status` | `bytedcli --site i18n-tt auth login` |
| `bytedog-ttp-us.tiktok-row.net` | `us-ttp`          | TikTok SSO / US TTP      | `bytedcli --site us-ttp --json auth status`  | `bytedcli --site us-ttp auth login`  |
| `bytedog-ttp-eu.tiktok-row.net` | `eu-ttp`          | TikTok SSO / EU TTP      | `bytedcli --site eu-ttp --json auth status`  | `bytedcli --site eu-ttp auth login`  |

## Authentication sequence

ByteDog uses the same check-before-login order as the general auth guidance. First select the exact site from the ByteDog URL host, then inspect that site's effective ByteCloud JWT state:

```bash
bytedcli --site <site> --json auth status
```

Use `data.authenticated` to decide whether the ByteCloud JWT path is available for ByteDog:

- `data.authenticated=true`: run the requested ByteDog command. Do not log in again merely because `data.bytecloud_auth.status` is `need_login`; ENV JWT, JWT override, or session JWT may be the active source.
- `data.authenticated=false`: start ByteCloud Auth login for that same site, complete it, then run the requested ByteDog command.

```bash
# Human / blocking
bytedcli --site <site> auth login

# Agent / non-blocking, only after data.authenticated=false
bytedcli --site <site> --json auth login --begin
bytedcli --site <site> --json auth login --complete <token>
```

`auth login --begin` creates a new authorization challenge, so run it only after the status check reports `data.authenticated=false`. Do not substitute another authenticated site for the URL-derived target site, because `--site` also selects the ByteDog backend.

## Network profile

ByteDance 生产网络设置 `BYTEDCLI_NETWORK_PROFILE=prod`，办公网络保持该变量未设置。该值区分大小写，不使用 `PROD`；出现连接错误时先确认网络配置，避免反复切换环境。
