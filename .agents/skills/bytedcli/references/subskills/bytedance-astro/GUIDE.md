---
name: bytedance-astro
description: >-
  Astro platform general online materials search. Use when the user wants to
  search or browse TikTok Shop / e-commerce search materials on the Astro
  platform, including general search, mall search, suggestion search, guide
  search, without-cart video search, and search badcase data across ROW, US, and
  EU regions. Also use when the user asks to discover available material sources,
  custom field enums, or display fields on Astro.
---

# bytedcli astro

Astro platform commands for querying general online materials across multiple
e-commerce search verticals and regions.

## Authentication

Uses ByteCloud JWT for the `i18n` site. Run `bytedcli auth login` first.

## Commands

### Search materials

```bash
# Basic search (ROW region, default)
bytedcli astro materials search --source generalSearch

# Search with region and pagination
bytedcli astro materials search --source generalSearch --country ID --page 1 --page-size 20

# Search in US region
bytedcli astro materials search --source mallSearch --astro-region us --country US

# Search in EU region
bytedcli astro materials search --source generalSearch --astro-region eu --country UK

# Filter by document type (shop card)
bytedcli astro materials search --source generalSearch --doc-type 10008_94

# Extra custom field filter
bytedcli astro materials search --source generalSearch --custom-field is_living_shop_card=1

# JSON output
bytedcli --json astro materials search --source generalSearch --country ID
```

### Discover available fields

```bash
# List all sources and their fields
bytedcli astro materials list-fields

# Show fields for a specific source
bytedcli astro materials list-fields --source generalSearch

# JSON output
bytedcli --json astro materials list-fields
```

### List supported sites and regions

```bash
bytedcli astro list-sites
```

## Supported sources

| Source | Description |
|--------|-------------|
| `generalSearch` | General e-commerce search (shop card, product card, live card, etc.) |
| `mallSearch` | Mall/shop search (creator card, shop card) |
| `sugSearch` | Suggestion search (normal sug, creator rich sug, shop rich sug) |
| `guideSearch` | Guide/recommendation search (creator, shop, product, normal) |
| `withoutCartVideoSearch` | Video search without cart |
| `searchBadcase` | Search badcase data (filter badcase, filter schema, query badcase) |

## Supported regions

| Region | Countries |
|--------|-----------|
| `row` (default) | ID, TH, MY, PH, VN, SG, SA, MX, BR, JP |
| `us` | US |
| `eu` | UK, DE, ES, FR, IE |
