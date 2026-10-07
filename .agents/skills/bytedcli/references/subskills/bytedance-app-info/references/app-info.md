# AppInfo command guide

| Command | Purpose |
| --- | --- |
| `bytedcli app-info search` | List applications without a filter. Pagination defaults to page 1 with 20 items per page. |
| `bytedcli app-info search --keyword <value>` | Automatically identify an input across App ID, code, package names, then Chinese name or alias. |
| `bytedcli app-info search --keyword <value> --by <dimension>` | Search one explicit dimension. |
| `bytedcli app-info get --app-id <app-id>` | Get one application by its unique App ID. |
| `bytedcli app-info batch-get --app-id <app-id>...` | Batch get applications by App ID. Repeat `--app-id` or pass comma-separated IDs. |

## Examples

```bash
bytedcli app-info search
bytedcli app-info search --page 2 --page-size 50
bytedcli app-info search --keyword 13
bytedcli app-info search --keyword funny_gallery --by code
bytedcli app-info search --keyword 今日头条 --by cn-name
bytedcli app-info get --app-id 13
bytedcli app-info batch-get --app-id 13 --app-id 322880
```

## Search modes

- Omit both `--keyword` and `--by` to list applications. Only `current` and `pageSize` are sent upstream.
- Pass `--keyword` without `--by` for automatic identification. A positive integer is tried as an App ID first and returns immediately when matched. Otherwise the input is tried as a code and Android/iPhone/iPad package; Chinese name or alias is the final fallback.
- Pass both `--keyword` and `--by` to query one explicit dimension.
- Passing `--by` without `--keyword` is invalid.
- `--page` defaults to `1`; `--page-size` defaults to `20`.

## Search dimensions

| `--by` value | Meaning | Upstream query parameter |
| --- | --- | --- |
| `app-id` | Unique application ID | `appId` |
| `code` | Application identifier | `name` |
| `cn-name` | Chinese application name or alias | `appNameOrAliasName` |
| `account-group-id` | Account group ID | `accountGroupId` |
| `product-line-id` | Product line ID | `productId` |
| `android-package` | Android package name | `androidPackage` |
| `iphone-package` | iPhone package name | `iphonePackage` |
| `ipad-package` | iPad package name | `ipadPackage` |

## Output shape

- `search` returns `keyword`, `by`, `page`, `page_size`, `total`, and `items`. For automatic identification, `by` is `auto`; for an unfiltered list, `keyword` and `by` are empty strings.
- `get` returns one AppInfo summary.
- `batch-get` returns `count` and per-input `items`.
- Each `batch-get` item contains only `input`, `ok`, `item`, and `error`.

## Returned app fields

`search` items, the `get` result, and successful `batch-get` items use the same AppInfo summary shape. Returned fields include:

- identity fields: `app_id`, `app_name`, `en_name`, `app_alias`, `name`, `tt_app_key`
- product and account fields: `product_id`, `product_name`, `product_cn_name`, `account_group_id`, `account_group_name`, `account_group_cn_name`
- app classification fields: `app_type`, `app_type_v2`, `is_external`, `app_status`, `status`
- package fields: `android_package`, `iphone_package`, `ipad_package`, `harmony_package`, `macos_package`, `vision_package`, `windows_package`, `winphone_package`
- member and audit fields: `android_member_id`, `iphone_member_id`, `ipad_member_id`, `create_time`, `modify_time`

Example JSON for one item:

```json
{
  "app_id": 322880,
  "app_name": "演示应用",
  "name": "demo-app",
  "tt_app_key": "demo_key",
  "product_id": 100,
  "product_name": "demo_product",
  "android_package": "com.example.android",
  "iphone_package": "com.example.ios",
  "ipad_package": "com.example.ipad"
}
```

The human-readable table uses query-aligned headers: `APP ID`, `CODE`, `CN NAME`, `ACCOUNT GROUP ID`, `PRODUCT LINE ID`, `ANDROID PACKAGE`, `IPHONE PACKAGE`, and `IPAD PACKAGE`. `CODE` displays the response `name`; `CN NAME` displays `appName` (`app_name` in JSON).

## Current boundaries

- `get` and `batch-get` accept only positive 32-bit App IDs through `--app-id`.
- `batch-get` uses independent `/app/info?appId=<id>` lookups with a concurrency limit of 10; `search` uses `/app/list`.
- AppInfo routes are site-specific: use `--site boe`, `--site i18n-bd`, or `--site i18n-tt` for those environments. The i18n-tt API is available through its standard site gateway, so callers do not need to pass `--vregion`. `--site i18n` is an i18n-bd routing alias, not i18n-tt.
- JSON output should be preferred for automation or Skill consumption.
