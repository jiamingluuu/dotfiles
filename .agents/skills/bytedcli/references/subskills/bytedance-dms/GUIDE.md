---
name: bytedance-dms
description: "Use bytedcli DMS commands when the user explicitly mentions DMS, a DMS console, a DMS db-id, or non-ByteDoc MySQL / Redis / DMS unified database querying: list accessible databases, look up a database's engine/dc/psm, and execute a SQL / Mongo shell / Redis command by --db-id. In ByteDance context, generic Mongo/MongoDB database tasks should use bytedance-bytedoc unless the user explicitly asks for DMS."
---

# bytedcli DMS

Use this skill when the task mentions DMS, the DMS console (dms-i18n.byteintl.net), a DMS `db-id`, querying a MySQL / Redis database through DMS, or explicitly running a SQL / Mongo shell / Redis command against an accessible DMS database.

If the user only says `mongo`, `MongoDB`, Mongo 库、集合、文档、慢查询、索引、连接、SDK 或权限 in ByteDance context, route to `bytedance-bytedoc` first. ByteDoc is the default MongoDB-facing platform unless the user explicitly names DMS or provides a DMS database id.

## Invocation

```bash
bytedcli --json dms <command> [options]
```

In this repo, local testing uses:

```bash
node dist/bytedcli.js --json dms <command> [options]
```

If options are unclear, run `dms --help`, `dms execute --help`, `dms db get --help`, or `dms db list --help` instead of guessing.

## Quick commands

```bash
# List the databases the current user can access (ids + engine type)
bytedcli --json dms db list

# Look up a database's engine / dc / psm / cluster by id (positional)
bytedcli --json dms db get 1001

# Execute a query (query is the positional arg) — engine auto-resolved from the target
bytedcli --json dms execute "select 1" --db-id 1001                         # MySQL by id
bytedcli --json dms execute "db.getCollectionNames();" --db-name demo_db     # MongoDB by name
bytedcli --json dms execute "get some_key" --db-id 1003                     # Redis by id (auto cluster)

# Redis: a db can front many clusters — list them, then target one by name or id
bytedcli --json dms db get 1003                                             # lists Redis clusters
bytedcli --json dms execute "get some_key" --db-id 1003 --cluster demo_redis_cluster
```

## How the unified interface works

- One `dms execute "<query>"` command covers all three engines. Pass the query as the positional argument; select the target with `--db-id` or `--db-name`.
- `--db-name` is resolved to an id via `dms db list` (the databases you can access); if the name is ambiguous the CLI errors and lists the candidate ids, so pass `--db-id` instead. `dms db list` currently returns the complete accessible list from the backend in one response; it has no pagination flags.
- The engine is auto-resolved from the target database's backend `type`:
  - `type 1` → MongoDB (Mongo shell query, e.g. `db.coll.find().limit(10)`)
  - `type 2` → MySQL (SQL query, e.g. `select * from t limit 10`)
  - `type 3` → Redis (Redis command, e.g. `get key`, `hgetall h`)
- For Redis, the CLI fetches the database's redis service detail and auto-picks the online cluster (clusterId / clusterName / idc) before executing. A Redis db can front MANY clusters (different `idc` + `redis`/`alchemy` module); run `dms db get <id>` to list them, then target a specific one with `--cluster <name|id>`.
- DMS Redis only proxies key-data commands (`get`, `hgetall`, ...); admin commands like `ping` / `info` / `dbsize` are not supported and the backend returns `Not found.`.
- `--engine mysql|mongo|redis` is only an override; normally omit it.
- `--site` defaults to `i18n-tt`. Other sites: `i18n-bd`, `cn`, `cn-boe`, `eu` (aliases: `row`, `bd`, `boe`, `prod`, `gcp`).

## Result shape

- Tabular results (MySQL, Mongo `find`) return `columns` + `rows` + `row_count`.
- Line-oriented results (Redis, Mongo command output like collection names) return `lines`.
- Only successful executions return data; engine-side errors surface as a structured `DMS_API_ERROR`.

## Rules that matter

- Get ids/names from `dms db list`; the listed `id` is the value for `--db-id` (and `db get <id>`), the `name` is the value for `--db-name`.
- Use bytedcli auth/session (ByteCloud JWT exchanged via SSO). Do not reuse `x-jwt-token` from browser curl examples.
- Use `/tmp` for any scratch files; do not write into the repo.
- Mongo queries can be slow; if a query times out, retry with `--http-timeout-ms 45000`.

## References

- 通用调用方式：`../../invocation.md`
- 排障说明：`../../troubleshooting.md`
