---
name: bytedance-cis-master-data
description: "Query CIS主数据 with bytedcli. Trigger when users say 主数据, CIS主数据 or CIS 主数据, or EA主数据 or EA 主数据. Supports the documented organization, finance, workplace, property, geography, locale, calendar, and reference models; do not use for generic master-data design or another named platform."
---

# CIS Master Data

Use `bytedcli cis-master-data` for read-only CIS master-data lookup. Route the natural-language
expressions `主数据`, `CIS主数据` / `CIS 主数据`, and `EA主数据` / `EA 主数据` to this same CLI. The
CLI supports the models linked below within the domain. Prefer global `--json` so the result remains
structured for downstream reasoning. The command always uses the selected site's personal ByteCloud
identity; `--as app` does not change this domain's authentication mode.

## Identity and Troubleshooting

Use the default invocation for ordinary queries:

```bash
bytedcli --json cis-master-data ref-country get --field code --value demo-country-code
```

- The service accepts personal JWTs whose `region` is `cn`, `i18n`, or `i18nbd`.
  A supported region still requires a valid, unexpired token with an employee identity and the
  caller's existing data permissions.
- Global `--site` selects the identity provider; it does not switch the master-data business
  environment. CLI site `i18n` is an alias of `i18n-bd`, not the JWT region `i18n`.
  The global site choices are not a master-data JWT support list. Explicitly supplied credentials
  are checked by the service using the actual token region.
- If the service reports `getKeyLookupFunc: not support region:`, check the selected identity
  provider or explicitly supplied JWT against the supported regions. Do not retry the same token
  or automatically switch sites.
- If the error explicitly reports expiration, renew the credential through its existing source.
  For other identity errors, preserve the original error and request ID for diagnosis; do not
  assume that logging in again will fix them. Never print or ask the user to share a JWT.
- Authentication and data permissions are separate. On permission denial, use only the application
  link returned by the CLI; do not invent a link or change identity to bypass the denial.

## Permission-limited Results

A successful query may include `permission_warning` and `permission_apply_urls`.
Explain the warning: the result covers only records or fields the caller may view, and must not be
presented as an unrestricted complete result. Only claim that matching records were actually omitted
when the warning explicitly says so; a restricted authorization scope alone does not prove omissions.
Do not infer hidden records, missing field values, or that an absent field has no data.
Judge task completion against the records and fields the user actually requested. If those are returned,
answer the request directly; a permission warning or application URL alone does not mean the task is
incomplete or that the user needs more permissions. Do not label a successful answer as a failure.
Keep any scope caveat proportional to its effect on the answer. Do not repeat a generic warning as an
unmet user requirement or proactively recommend applying for more access when the request is satisfied.
If the user needs complete coverage, or a requested record or field cannot be supplied, explain the
remaining uncertainty without assuming permissions caused every absence. Offer a returned application
URL only when additional access is relevant to that unmet need or the user asks about permissions.
Use only the application URLs returned by the CLI, without rewriting or inventing them. The returned
page may request a data range or a role; the user must select the appropriate scope there. A link does
not automatically identify or grant the permissions missing from this query. If no link is returned,
explain the limitation without guessing an application path. Do not automatically retry or switch identity.

## Reference Summaries

Successful queries may include optional `references[sourceField][sourceCode]` alongside the original
result. Each summary contains `mdm_code` and either `name` or language-specific keys such as
`name.zh-CN` and `name.en-US`; all values remain strings. Use the original reference field's value
to find its summary. For an array reference, parse the original array value and match each code.
Original record fields are unchanged. No extra command option is required.

These are one-level names for interpreting returned records, not full target details or permission
to list the target model. An independent query for the target’s full details still checks the target model’s permissions. Absence of a summary does not establish that the target is missing or
inaccessible. Do not infer names, languages, or permissions from absence. If
`reference_summary_warning` is present, the main query succeeded but the summaries are incomplete;
report that limitation without treating missing names as data facts. Do not automatically retry.

### Enum names in query results

Successful queries may include optional `enum_labels[recordMdmCode][field][rawCode]`.
Match the result record's `mdm_code`, field, and original enum code to read its name.
Names are scoped to each record: identical codes in different ledgers need not have the same meaning.
Keep using the original code for subsequent calls; do not replace request values with names.
For an array-valued field, parse its original array and match each code separately.
These labels explain only values in the visible query results, not all available options,
and do not add any supported filters. Use only filters documented for the selected command.
If labels are absent, keep the original code and do not guess its meaning.
`enum_labels_warning` means the main query succeeded but enum explanations are incomplete.
No extra command or switch is required. Enum labels and reference summaries are separate annotations.

## Method Selection

| Need                                       | Command     | Selection rule                                              |
| ------------------------------------------ | ----------- | ----------------------------------------------------------- |
| One known exact lookup value               | `get`       | Use a documented get field; returns one matching record     |
| Several independent exact criteria         | `batch-get` | Use only for independent criteria; maximum 128 per call     |
| Many values of the same exact lookup field | `multi-get` | Prefer over `batch-get`; repeat `--value`; maximum 128      |
| Exact bounded collection lookup            | `query`     | Criteria must match a documented model field set            |
| Fuzzy lookup across model fields           | `search`    | Pass only `--keyword`; search fields are fixed by the model |
| General filtered scan                      | `list`      | Use only if the model exposes it and other methods do not fit  |

Do not guess field names for `--field`, `--criterion`, `--filter`, `--sort`, or `--return-field`.
Read the model reference before constructing an exact or bounded lookup:

| User model name    | Command group                        | Model reference                                                                      |
| ------------------ | ------------------------------------ | ------------------------------------------------------------------------------------ |
| 会计子目类型 | `md-sub-account-subject-type` | [Subsubject types](references/md-sub-account-subject-type.md) |
| 多账套会计科目COA | `md-inter-account-subject-area` | [Accounting areas](references/md-inter-account-subject-area.md) |
| 部门               | `md-department`                      | [Department: fuzzy name search only](references/md-department.md)                                            |
| 法人主体           | `md-legal-entity`                    | [Legal entity](references/md-legal-entity.md)                                        |
| 主体账户           | `biz-legal-entity-account`           | [Legal-entity account](references/biz-legal-entity-account.md)                       |
| 金融分支机构       | `md-bank`                            | [Financial-institution branch](references/md-bank.md)                                |
| 汇率               | `biz-exchange-rate`                  | [Exchange rate](references/biz-exchange-rate.md)                                     |
| 利率               | `biz-interest-rate`                  | [Interest rate](references/biz-interest-rate.md)                                     |
| 币种               | `ref-currency`                       | [Currency](references/ref-currency.md)                                               |
| 银行总行           | `md-head-bank`                       | [Head bank](references/md-head-bank.md)                                              |
| 国家/地区          | `ref-country`                        | [Country/region](references/ref-country.md)                                          |
| 省/州              | `ref-state`                          | [State/province](references/ref-state.md)                                            |
| 城市               | `ref-city`                           | [City](references/ref-city.md)                                                       |
| 区/县              | `ref-county`                         | [County/district](references/ref-county.md)                                          |
| 国籍               | `ref-nationality`                    | [Nationality](references/ref-nationality.md)                                         |
| 自定义区域         | `biz-custom-region`                  | [Custom region](references/biz-custom-region.md)                                     |
| 时区               | `ref-time-zone`                      | [Time zone](references/ref-time-zone.md)                                             |
| 公共假期           | `md-public-holiday`                  | [Public holiday](references/md-public-holiday.md)                                    |
| 语言               | `ref-language`                       | [Language](references/ref-language.md)                                               |
| 证件类型           | `md-card-type`                       | [Identity-document type](references/md-card-type.md)                                 |
| 源系统标识         | `biz-source-system`                  | [Source-system identifier](references/biz-source-system.md)                          |
| CIS业务线          | `md-cis-business-line`               | [CIS business line](references/md-cis-business-line.md)                              |
| 虚拟主体           | `biz-virtual-entity`                 | [Virtual entity](references/biz-virtual-entity.md)                                   |
| 人员序列           | `md-sequence`                        | [Personnel sequence](references/md-sequence.md)                                      |
| 职场               | `md-workplace`                       | [Workplace](references/md-workplace.md)                                              |
| 楼宇               | `md-building`                        | [Building](references/md-building.md)                                                |
| 楼层               | `md-building-layer`                  | [Building floor](references/md-building-layer.md)                                    |
| 地产项目           | `md-real-estate-project`             | [Real-estate project](references/md-real-estate-project.md)                          |
| IT库房位置         | `md-warehouse-location`              | [IT warehouse location](references/md-warehouse-location.md)                         |
| 收单地址           | `biz-acquiring-address`              | [Acquiring address](references/biz-acquiring-address.md)                             |
| 商户号             | `biz-merchant`                       | [Merchant number](references/biz-merchant.md)                                        |
| 预算科目           | `md-budgetary-account`               | [Budgetary Account](references/md-budgetary-account.md)                              |
| 预算科目扩展       | `biz-budgetary-account`              | [Budgetary Account Extension](references/biz-budgetary-account.md)                   |
| 会计科目           | `md-accounting-subject`              | [Accounting Subject](references/md-accounting-subject.md)                            |
| 会计科目扩展       | `biz-accounting-subject`             | [Accounting Subject Extension](references/biz-accounting-subject.md)                 |
| 会计子目           | `md-sub-account-subject`             | [Accounting Subsubject](references/md-sub-account-subject.md)                        |
| 会计子目扩展       | `biz-sub-account-subject`            | [Accounting Subsubject Extension](references/biz-sub-account-subject.md)             |
| 多账套会计科目     | `md-inter-account-subject`           | [Multi-Ledger Accounting Subject](references/md-inter-account-subject.md)            |
| 多账套会计科目扩展 | `biz-inter-account-subject`          | [Multi-Ledger Accounting Subject Extension](references/biz-inter-account-subject.md) |
| 财务区域           | `md-finance-region`                  | [Finance Region](references/md-finance-region.md)                                    |
| 核算区域           | `md-gl-region`                       | [Accounting Region](references/md-gl-region.md)                                      |
| 付款类型           | `md-payment-type`                    | [Payment Type](references/md-payment-type.md)                                        |
| 支出类型           | `md-expense-type`                    | [Expense Type](references/md-expense-type.md)                                        |
| 支出类型Mapping    | `biz-expense-mapping`                | [Expense Type Mapping](references/biz-expense-mapping.md)                            |
| 采购品类           | `md-supplier-category`               | [Procurement Category](references/md-supplier-category.md)                           |
| 中台属性           | `biz-mid-plat-property`              | [Middle-Platform Property](references/biz-mid-plat-property.md)                      |
| 业务线             | `md-product`                         | [Business Line](references/md-product.md)                                            |
| 业务线扩展         | `biz-product`                        | [Business Line Extension](references/biz-product.md)                                 |
| 业务线星云关系     | `biz-nebula-app-info`                | [Business Line Nebula Relationship](references/biz-nebula-app-info.md)               |
| 总账侧业务线       | `biz-financial-report-business-line` | [General-Ledger Business Line](references/biz-financial-report-business-line.md)     |
| 往来               | `md-internal-segment`                | [Internal Segment](references/md-internal-segment.md)                                |

## Shared Syntax

```bash
# Exact criterion
bytedcli --json cis-master-data <model> get --field <field> --value <value>

# Independent criteria; one result lookup per --criterion
bytedcli --json cis-master-data <model> batch-get \
  --criterion 'mdm_code=<code-1>' \
  --criterion 'mdm_code=<code-2>'

# Same exact lookup field, multiple values
bytedcli --json cis-master-data <model> multi-get \
  --field mdm_code --value <code-1> --value <code-2>

# Bounded query; repeat --criterion for every field in a documented field set
bytedcli --json cis-master-data <model> query \
  --criterion 'first_field=<value>' \
  --criterion 'second_field=<value>'

# Fuzzy search; do not pass a field
bytedcli --json cis-master-data <model> search --keyword <keyword>

# Paged list, only when the selected model reference explicitly exposes list
bytedcli --json cis-master-data <model> list --page-size 32
```

Filters use `field=operator:value`. Operators are `equal`, `gt`, `lt`, `gte`, `lte`, `contain`,
`starts-with`, `not-equal`, and `in`. For `in`, place comma-separated values after the colon.

Sorting uses `field:asc` or `field:desc`. Search optionally accepts
`--language zh-CN|en-US|ja-JP`. Use `--page-token` only with the continuation token returned by the
previous response; do not combine it with `--page`. Page size is limited to 512 records.

## Agent Guidance

### Entity model selection

`法人主体` identifies companies or organizations; `虚拟主体` includes trust plans, funds,
consolidation adjustments, and consolidation entities. These descriptions help interpret the
request; a company-like or fund-like name alone does not prove the record's model.

- Follow an explicitly named model or the model already established in the conversation.
- For bare `主体`, `公司`, or `组织` with no established model, ask whether the user wants legal
  entities, virtual entities, or both. Generic wording such as `查公司` does not explicitly select
  `法人主体`. A name, `mdm_code`, EBS code, or financial context alone does not settle this.
  Do not infer the model from code prefixes, numeric ranges, or historical example values.
- When the user explicitly requests both models, use their documented commands separately and
  label each result with its model. Preserve the requested matching semantics; legal entities only
  expose `search`, so do not promise exact lookup across both models or invent a unified command.
- Do not merge same-name records across models. Distinguish each model's no-match result from a
  failed or permission-denied query; partial success is not a complete two-model result. Do not
  switch models after an empty result or error unless that other model was requested.
- A request for a subject's bank account belongs to the legal-entity-account model; read its
  reference instead of treating every occurrence of `主体` as a choice between the two entities.

### Finance and business-line model selection

预算科目、会计科目、会计子目、多账套会计科目、业务线 each have basic and extended information entries.
Each pair shares the business object query permission and uses the same `mdm_code`. Locate basic information
first when the user supplies its name, then use the returned code to read the extension. Do not guess codes.
支出类型 and 支出类型Mapping are separately queried and separately permissioned objects.
业务线 (`md-product`), 业务线扩展 (`biz-product`), 业务线星云关系 (`biz-nebula-app-info`),
总账侧业务线 (`biz-financial-report-business-line`), and CIS业务线 (`md-cis-business-line`)
are distinct entries; follow the requested name and ask when it is ambiguous.
财务区域 and 核算区域 also have separate entries.

The five basic/extended pairs above share the corresponding business object's detail query permission
with 主数据平台 (Master Data Platform). Name search for 会计子目 and 多账套会计科目 returns discovery summaries
containing `mdm_code` and `name` (including available language variants) without requiring the model
query permission. Search success does not authorize detail access. Read details using the returned code.
For their detail queries and extensions, results contain only the rows and fields visible to the signed-in
account; each extension shares its corresponding basic record's data range. A successful detail response
does not promise every record or every field. Do not reconstruct omitted fields or retry another entry
to work around a permission restriction. An empty result alone does not establish that a record is
missing globally or that permission was denied.

多账套会计科目扩展 and 支出类型Mapping do not expose `search`; use their documented exact criteria.
业务线扩展 searches its business introduction (`explanation`), not mission or vision. When the user
knows the business-line name, search the basic business-line entry first and reuse its returned code.

### Command and result discipline

1. In user-facing replies, use `CIS主数据` for the domain. Use the input expressions only for
   routing; do not explain or annotate how the user's wording relates to the domain name.
2. Select the command group from the model table instead of translating or guessing from its code.
   `银行总行` selects `md-head-bank`; `金融分支机构`, `银行分行`, or `银行支行` selects `md-bank`
   only when the user is asking about master data. Do not route bare `银行` or consumer-facing
   `银行网点` requests without enough master-data context. Keep `国家/地区` separate from `自定义区域`,
   and from the person's `国籍`; keep `法人主体` separate from `主体账户`. Respect the stated
   administrative level when choosing `省/州`, `城市`, or `区/县`. Use `币种` for a currency
   definition, not for `汇率` or `利率` data. Ask which model the user means when the wording does
   not establish one. Keep `虚拟主体` separate from `法人主体` and `主体账户`;
   `人员序列` describes sequences, not employees. Distinguish `职场`, `楼宇`, and `楼层` by the
   requested level; `地产项目`, `IT库房位置`, and `收单地址` are separate models. `商户号`
   lookup does not provide account balances or transactions.
3. Use `search` to discover a stable identifier when the user only supplies a name fragment and the
   selected model exposes `search`.
4. For models that expose exact lookup, use `get` with a field explicitly listed for it in the selected model reference.
   Prefer `mdm_code` for a specific record; business-key lookups may have multiple matches.
   When the user supplies several values of the same exact
   lookup field, prefer `multi-get` over `batch-get`. Use `batch-get` only when the user asks for
   independent exact criteria. Follow model-specific history or status guidance before assuming one
   row per value.
5. Use `query` only with a field set listed in the selected model reference.
   For `get`, `batch-get`, `multi-get`, and `query`, pass exact string values unchanged, including
   leading and trailing spaces; use safe shell quoting, for example `--criterion 'name= sample name '`.
6. Confirm every verb in the selected model group's `Commands` list before constructing it. A
   parent help page is not evidence that an unlisted leaf command exists.
   On an unsupported command, option, field, or criterion combination, read the error and the
   corresponding model or command `--help`. Correct the call only when the supported operation
   preserves the requested meaning. Do not automatically replace an exact lookup with keyword search.
   If no supported operation expresses all conditions, explain the limitation and ask for a supported
   lookup value or a change of scope. Do not drop conditions, substitute fields, enumerate records
   to bypass an unavailable method, or present a locally filtered page as the complete result.
7. Use `list` only when the selected model reference explicitly exposes it and `get`, `batch-get`,
   `multi-get`, `query`, and `search` cannot express the requested lookup. Use only documented
   filters and pagination, use a bounded page size, and avoid broad unfiltered scans unless the user
   explicitly requests one. A small page does not make an unavailable command supported.
8. Use optional `--filter`, `--sort`, or `--return-field` only when the model reference or command
   help explicitly documents that field for the operation; otherwise omit the option. A returned
   field does not by itself prove that it can be reused for filtering, sorting, or field selection.
9. Treat an empty record set as a valid no-match result. On permission denial, surface only
   application links returned by the CLI. Do not construct, rewrite, or supplement application
   links from model codes or role identifiers; when the CLI returns no link, report the denial
   without inventing one. Surface validation errors without changing the requested model or
   widening the query.
