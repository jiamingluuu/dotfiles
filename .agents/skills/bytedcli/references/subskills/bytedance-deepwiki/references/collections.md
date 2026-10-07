# Collection mapping

When searching company infra / shared libraries, pass `--collection-name` so DeepWiki searches that knowledge base instead of the current repo. This table is the source of truth for the most common collections.

| Infra / library | `--collection-name` | Notes |
|-----------------|---------------------|-------|
| Semi Design | `DouyinFE_semi_design` | Design system & UI library |
| EdenX | `webinfra_edenx` | Modern.js-based full-stack framework |
| Pia | `pia_pia` | Progressive instant-app framework |
| Gulux | `nodejs_gulux` | Node.js service framework |
| Garfish | `pgcfe_garfish` | Micro-frontend platform |
| @byted/hooks | `toutiao_fe_hooks` | Base React hooks library |
| Noah | `ife_noah` | Mid/back-office base library (incl. `@webcast/standard-components`) |
| Ace | `ife_dayu` | Base library: `@byted-ace/form`, `@byted-ace/request`, `@byted-ace/hook`, `AceSemiForm` ... |
| Ufra | `ies_ufra` | C-side flow management: `@ufra/*`, `ufra.meta.json` |
| Pace | `ies_pace` | PC SSR rendering framework |
| Emo | `web_solutions_emo` | Monorepo management tool |
| @safe-fe/ui | `ies_safe_devlib` | `@safe-fe/ui`, `@safe-fe/admin-ui` |
| Lynx | `lynx` | Cross-platform stack: ReactLynx, TTML, Lepus, rspeedy, x-element |
| Hybrid | `hybrid` | Cross-end container & resource delivery: AnnieX, Gecko, Forest, GFC, JSB/JSBridge |
| Slardar Hybrid monitor | `hybrid_performance` | Cross-end perf/stability/alert monitoring |
| Any OSS library | `external` | Non-company OSS (ahooks, ant-design ...); the query MUST include the npm package name |
| Company base platforms | `internal` | Fallback for internal platform docs / knowledge |

## If the mapping is unknown

Resolve a collection name from a repo or package, then search with it:

```bash
bytedcli --json deepwiki get-collection --repo-name owner/repo
bytedcli --json deepwiki search --query "Button 组件属性与事件" --collection-name <resolved-name>
```

> `get-collection` can be slow and may require additional backend authorization. Prefer the table above when the infra is listed.
