# Vimo CN routing

Read this reference only for JianYing CN Vimo requests. The CLI surface is flat, but CN remains a
separate implementation and authentication contract from overseas Vimo.

## Supported commands

```bash
bytedcli --site cn vimo template get --rid '<rid>'
bytedcli --site cn vimo template get --url '<vimo-or-share-url>'
bytedcli --site cn vimo template download --rid '<rid>' --output '<template.zip>'
bytedcli --site cn vimo template search --uid '<jianying-uid>'
bytedcli --site cn vimo template search --unique-id '<jianying-hao>'
bytedcli --site cn --json vimo template search --uid '<jianying-uid>' --status deleted
bytedcli --site cn --json vimo user get --uid '<jianying-uid>'
bytedcli --site cn --json vimo user get --uid '<jianying-uid>' --section subscription,orders
bytedcli --site cn vimo commerce resource-type list
bytedcli --site cn vimo commerce feature list --resource-type aigc
bytedcli --site cn vimo commerce benefit list --resource-type aigc --resource-id '<resource-id>'
bytedcli --site cn --json vimo homepage tool list --page 1 --page-size 20
bytedcli --site cn --json vimo homepage primary-list list
bytedcli --site cn --json vimo homepage secondary-list list
bytedcli --site cn --json vimo homepage primary-priority list
bytedcli --site cn --json vimo homepage graph get --tool-id sample_tool
bytedcli --site cn --json vimo homepage floor list --status online
bytedcli --site cn --json vimo homepage floor-priority list
bytedcli --site cn --json vimo homepage floor get --floor-id 1001
```

`homepage primary-priority list` defaults to `--page-size 999` because this page is an online,
published priority overview. Pass a smaller `--page-size` when you explicitly want paged output.
For every homepage list, `total` is `null` when Vimo omits a total; use `current_count` for the
number of rows returned on that page instead of treating it as a global total.

CN supports read-only account evidence by UID, homepage configuration, template RID lookup/download,
and commerce feature, benefit, and history queries.

## Authentication

All CN commands use a CN user ByteCloud JWT. They never consume an overseas Vimo browser Cookie or
overseas Vimo session.

```bash
bytedcli --site cn auth login
```

## Kani read permission after a 403

For mapped CN endpoints, `VIMO_PERMISSION_DENIED` includes `details.kani_permission` and a
`details.setup_commands` entry. The command is deliberately a Kani `approval create --dry-run`
preview with `<applicant>` and `<reason>` placeholders; it does not submit an approval.

Use this branch whenever a CN read returns 403:

1. Report the denied endpoint, permission key/name, mapping confidence, and dry-run command from the
   error. Never replace an unmapped permission with a broad permission such as `all`.
2. Ask whether the user wants to apply for that read permission. Stop before any Kani submission.
3. Only if the original prompt explicitly requested automatic permission application, or the user
   confirms after the denial, fill in the applicant and reason, run the dry-run, show its result, and
   follow the Kani approval confirmation policy before submitting. A request to run the Vimo read
   command alone is not consent to create an approval.

The current endpoint families map as follows:

| CN command family | Kani permission key | Name | Confidence |
| --- | --- | --- | --- |
| `vimo user get` sections | `user_info_operation` | 用户信息管理 | verified |
| `vimo homepage tool/primary-list/secondary-list/primary-priority` | `vco_homepagev3_tools_manage_read` | 剪映首页改版小工具管理-读 | verified |
| `vimo homepage floor/floor-priority` | `vco_homepagev3_floor_manage_read` | 剪映首页改版内容楼层管理-读 | verified |
| `vimo commerce feature/benefit/benefit-history` | `ai_commercialize_read` | AI转商可读权限 | verified |
| `vimo template get/search/download` | `template_operation` | 模板内容管理 | inferred |

`homepage floor get` reads both the selected floor and its referenced tool definitions. It can
therefore require both homepage read permissions; handle each reported denial separately. The
template mapping is inferred from the permission name and console route rather than verified server
metadata, so state that uncertainty before asking to apply.

These Kani permissions protect Vimo Console reads. They are distinct from Vimo Material OpenAPI
permission application through `vimocli`; do not route a Console 403 to the Material OpenAPI flow.

## Account evidence by UID

Start with `vimo user get --uid <jianying-uid>`. The default `basic` section includes profile
identifiers, creator level, online template/course counts, and enabled permissions. Add only the
evidence needed with `--section tags,certification,courses,subscription,orders,punishments`; use
`--section all` only when the complete account view is necessary.

Use `--page-size` for courses, orders, and punishments. Continue courses with the returned
`--cursor`, and orders or punishments with the returned `--offset`, only while the section reports
more data. Keep UIDs, order IDs, template RIDs, and cursors as strings.

Cite `data.evidence` and the matching `data.sections` fields. The response does not prove
account-binding conflicts, real-name verification failure causes, activity-task counts, user-owned
template lists, or template moderation results when those facts are absent.

## Homepage configuration graph

The four Vimo pages form three entities plus one filtered view:

1. `homepage tool list` returns atomic tool/collection definitions. `basicConfig.toolId` is the
   stable join key; `useConfigs` contains concrete icon, deeplink, description, label, and strategy.
2. `homepage primary-list list` returns first-screen ordering candidates. Its `order` references tool
   IDs, while `relatedCategoryId` references one secondary collection.
3. `homepage secondary-list list` returns category-Tab collections. Each collection has an `id`; its
   `categoryConfigs[].order` also references tool IDs.
4. `homepage primary-priority list` calls the primary-list endpoint with published/online filters and
   exposes candidate priority. It is not an independent configuration entity.

Prefer `homepage graph get --tool-id <id>` when answering where a tool is configured. It resolves
all three entity sets and reports missing references or a tool that appears in a primary list but not
in that primary list's related secondary collection. Do not infer relationships from names.

### Primary-list priority and runtime matching

For first-screen tool lists, priority is an ascending match order: smaller numeric `priority` values
are checked first. After strategy filtering, the runtime keeps only the first matched primary list
per category type, then sorts the selected categories by type. A later row with a larger priority
does not override an earlier matched row of the same type.

When diagnosing a homepage tool experiment:

1. Run `homepage primary-priority list` and inspect every online primary list that can match the same
   category type.
2. Treat all smaller-priority rows as blockers unless their strategies fail for the target device.
3. Resolve every strategy VID with the fixed Libra app flow below, and evaluate `ab_id_config`,
   `ab_id_black_config`, platform, channel, version, and client feature gates together.
4. If a tool is expected to appear only for one experiment, either give that experiment a smaller
   priority than competing same-type rows or add the experiment VID to the competing row's blacklist.

Runtime semantics observed in the homepage service:

- The service sorts primary-list configs with `config1.GetPriority() < config2.GetPriority()`.
- `RunStrategy` returns true only after platform/version, AB whitelist, AB blacklist, channel,
  feature, device form factor, and user-group checks pass.
- `ab_id_config.type=0` means any listed AB group may match; `type=1` means all listed groups must
  match. `ab_id_black_config` uses the same any/all rule, but a match rejects the config.
- For each category type, the selected map is populated only when that type is absent, so the first
  matched row wins.

If the runtime behavior is disputed, verify it from PSM instead of relying on the Vimo admin page
alone: find the API service for `/lv/v1/home/tool/get`, follow its RPC to the homepage core service,
then inspect the core implementation that loads the Vimo home config, sorts by priority, runs
strategy, and deduplicates by category type. If a Codebase permission request for a mapped repository
returns `CODEBASE_PERMISSION_RESOURCE_NOT_FOUND`, use the repository's project member page or a
dependency permission check/batch apply fallback; do not assume the PSM build repository name is the
requestable Codebase slug.

### Resolve every experiment VID

The graph response extracts the deduplicated `data.experiment_vids` from
`basicConfig.strategy` and every `useConfigs[].strategy`. Each reference records whether the VID came
from `ab_id_config` or `ab_id_black_config` and preserves its source path. These are Libra **version
IDs**, not Flight IDs. When the array is non-empty, continue with the `bytedance-libra` skill and
resolve every returned VID against JianYing app `147`:

```bash
bytedcli --site cn --json libra experiment list --app-id 147 \
  --keyword '<vid>' --search-type id
bytedcli --site cn --json libra experiment get --flight-id '<returned-flight-id>'
```

Do not pass `<vid>` to `--flight-id`. The list search is only a candidate mapping: accept it only when
the detail response's `versions[].id` contains the original VID. For each VID, report its source
field/path, Flight ID, experiment name, raw experiment status, matching version name/status, and
whether the mapping was verified. If the search returns zero or multiple candidates, detail lookup
fails, or no candidate contains the VID, report that VID as unresolved with the exact failure; do not
silently omit it or infer from `libra_url`. The homepage investigation is complete only when every
VID has either a verified status result or an explicit unresolved reason.

The IDs in this chain belong to different systems: Vimo homepage requests use Vimo `appId=1775`
and `businessId=1`, while experiment lookup is fixed to the JianYing mobile Libra app `147`. Do not
substitute one for the other, and do not ask the user for a Libra app ID for this homepage workflow.

The JianYing client consumes the resolved feed as `tools`, `categories`, and `home_categories`.
Homepage Tabs come from `home_categories`, the first screen uses `home_categories[0].tools`, and the
classified tool page groups flattened `categories[].tools`. Strategy matching, client feature/AB
filters, forced local entries, cache, and bundled fallback still affect final visibility, so a Vimo
record alone does not prove that every user sees the tool.

## Homepage content floors

`homepage floor list` reads the floor configuration library and accepts exact `--floor-id`, title, status,
and pagination filters. Status names map to the management states `draft`, `online`, and `offline`.
`homepage floor-priority list` calls the same endpoint with published/online filters and the Web
page's fixed `page=1,pageSize=999` query. The backend does not honor smaller page sizes for this
view, so the CLI intentionally does not expose pagination options. It is a filtered ordering view,
not a separate floor entity. Keep IDs and priority values as strings.

Prefer `homepage floor get --floor-id <id>` for investigation. It returns the complete floor record,
joins every item `toolId` to the homepage tool definitions, reports missing references, extracts the
floor and referenced-tool strategy VIDs, and provides the client semantics needed to interpret the
record:

- floor types: `1=tool`, `2=template`, `3=other`; the current renderer also recognizes `4=audio`;
- display ratios: `1=4:3`, `2=1:1`, `3=16:9`; `101` is reserved for a client-local single card;
- template sources: `0=common`, `1=recommend`, `2=topic`, `3=hot`, `4=search`;
- item click precedence is `tool_id`, then non-zero `template_id`, then `deeplink`;
- `more_url` opens HTTPS through the web container and other values through Deeplink routing.

The app does not consume the Vimo camelCase management payload directly. It posts Settings VIDs as
`abtest_group_ids` to `https://feed-api.capcutapi.com/lv/v1/home/content/get`; the service applies
strategy and sorting, then returns snake_case `content_floors`. With the new-floor experiment enabled,
the client adds `cursor`, `count=4`, and `enable_sort`. It can then insert a local album-to-video floor
with `floor_id=999` at an AB-controlled position. Therefore Vimo priority describes server-floor order,
not the final absolute order visible to every client.

Resolve every VID returned by `homepage floor get` with the same mandatory Libra app `147` procedure
above. Vimo `appId=1775` and Libra app `147` remain separate namespaces.

## Template selectors

Pass exactly one of `--rid` or `--url`. Supported URL forms include:

```text
https://vimo.bytedance.net/lv/content/template/resource?...&rid=<rid>
https://lv.ulikecam.com/activity/lv/sharevideo?template_id=<rid>&item_type=1
```

For a share link, `template_id` is the Vimo resource ID and `item_type` must be omitted or equal to
`1`. Keep the complete URL in one quoted shell argument.

### Template triage evidence

`template get` returns the fields needed to triage 剪同款 template reports without opening the Vimo
console:

- `status` / `status_text`: current resource state (`online`, `offline`, `deleted`, `banned`,
  `pre_review`). A deleted RID still returns its last metadata, including signed URLs.
- `biz_status`: per-app status rows (`app_id`, `biz_id`, `status_text`); `app_id=1775, biz_id=1` is
  JianYing. Use this to distinguish "deleted on JianYing" from a template that is only offline in
  another biz line.
- `is_ai_template` plus `aigc_algorithms`: the template's bound AI effect/algorithm tags
  (`name`, e.g. `high_aes_general_v41s`, `resource_type`, `resource_id`). A template can be
  `deleted` while still carrying AI algorithm tags; cite both fields instead of inferring AI status
  from the title or the user's entry point.
- `extra.aigc_fragments`: per-segment draft AIGC bindings parsed from the template `Extra`
  descriptor (`algorithm`, `algorithm_type`, `aigc_type` like `i2i`, `resource_id`,
  `resource_types`, and the authoring `prompt`). Non-AIGC segments are omitted.
- `functions`: console capability tags (e.g. `clipping`, `ai_painting_v2`, `motion_driven`).
- `author` (`uid`, `name`, `unique_id` / 剪映号) and `create_time`.

The command answers template-side state only. It does not show a user's publish-time binding,
export/publish events, or client-side AI labeling; for those use TEA/Matrix/ALog evidence.
Use `--include-raw --json` when a field is absent from the compact output.

### Search templates by user

`template search` lists templates published by one user, newest first. It maps the CN console
模板列表 "搜索方式 = 用户uid/剪映号" query; pass exactly one of:

- `--uid <jianying-uid>`: the numeric JianYing user ID (same identifier as `vimo user get --uid`).
- `--unique-id <jianying-hao>`: the public 剪映号.

```bash
bytedcli --site cn vimo template search --uid '<jianying-uid>'
bytedcli --site cn vimo template search --unique-id '<jianying-hao>' --status deleted
bytedcli --site cn --json vimo template search --uid '<jianying-uid>' --page-size 50
bytedcli --site cn --json vimo template search --uid '<jianying-uid>' --cursor '<next-cursor>'
```

- Pagination is cursor-based: omit `--cursor` for the first page, then pass the returned
  `next_cursor`. The endpoint returns no total; use `page_size`, `page_count`, `has_more`, and
  `next_cursor`.
- `--status` accepts `online|offline|deleted|banned|pre-review`, e.g. `--status deleted` to audit
  a user's deleted templates.
- `--page-size` is 1-100 (default 20).
- Each row carries the same triage fields as `template get` (`status_text`, `is_ai_template`,
  `aigc_algorithms`, `functions`, `biz_status`, `author`, `create_time`).
- This is a CN-only command; `vimo template list` (without `search`) is the separate CapCut
  overseas template-management list and only works under `--site i18n`.

## Commerce tuple model

Treat a commerce benefit as a hierarchy:

1. `resource_type` selects `aigc` or `normal-func`.
2. `resource_type + resource_id` selects one feature.
3. `resource_type + resource_id + benefit_type` selects one atom benefit.

The complete level-3 tuple is the stable business selector. A `benefit_type` may occur under more
than one feature, so never deduplicate by one field or select the first match. Prefer the complete
tuple for `benefit get` and `benefit-history`; use numeric `--benefit-id` only when copied from a
list/search result and still reject ambiguous matches.

### Online release change log

`commerce release list` answers "what changed the last time this benefit went online, and who
published it". It reconstructs the online releases (每一次上线，即 `getOperateLog` 中的 `publish` /
`publish-auto` 事件) newest-first, and for each release computes the normalized content diff against
the previous online release, so you get the actual changed fields—not just a version list.

```bash
bytedcli --site cn vimo commerce release list --benefit-id '<benefit-id>'
bytedcli --site cn --json vimo commerce release list \
  --resource-type aigc --resource-id '<resource-id>' --benefit-type '<benefit-type>'
bytedcli --site cn vimo commerce release list --benefit-id '<benefit-id>' --no-diff
```

- Each release row carries `published_at`, `version_id`, `operator` (发布人), `auto_publish`,
  `canary_publish_ratio`, and `change_count`; JSON additionally exposes `compared_to` and the full
  `changes[]` (`path` / `before` / `after`). The oldest online release compares against an empty
  baseline (`compared_to: "initial"`).
- Pass `--no-diff` for a fast metadata-only timeline (skips per-version draft loads and the diff).
- The diff compares benefit content only (pay strategies, pay guides, extra, names). Version
  metadata such as `version_id` / `status` is excluded, so two content-identical releases report
  `change_count: 0`.
- Use `--page` / `--page-size` to page the release list; each distinct version draft is fetched once
  and reused across adjacent comparisons. A version draft that cannot be loaded fails the command
  rather than being rendered as a full add/delete.
- `benefit-history list` still returns the raw per-version operation events (edit/submit/approve/
  publish); `release list` is the release-oriented "上线改动日志" view built on top of the same
  endpoint.
