# Bamboo invocation

## Prerequisite

Bamboo open APIs are unauthenticated. The runtime only needs ByteDance office-network access; do not run `auth login` or supply a browser Cookie/JWT. `list` and both detail commands are read-only. `create` and `update` default to a local request preview and send POST only with `--yes`.

## Commands

```bash
bytedcli bamboo hive-rule list --space-id demo-space-id
bytedcli bamboo hive-rule list --space-id demo-space-id --followed true --user-id 10001 --email demo.user
bytedcli bamboo hive-rule get --id 12345
bytedcli bamboo hive-rule create --payload-file ./demo-bamboo-rule-create.json
bytedcli bamboo hive-rule update --id 12345 --payload-file ./demo-bamboo-rule-update.json
bytedcli bamboo offline-result get --id 67890

# --json is a global option and must precede the domain
bytedcli --json bamboo hive-rule list --space-id demo-space-id --page 1 --page-size 20
bytedcli --json bamboo hive-rule get --id 12345
bytedcli --json bamboo hive-rule create --payload-file ./demo-bamboo-rule-create.json
bytedcli --json bamboo offline-result get --id 67890
```

Use a positive integer rule ID with `hive-rule get/update` and a positive integer check-result ID with `offline-result get`. `hive-rule list` requires `--space-id`; all other filters are optional.
The list filters `--alarm-level` and `--label` use semantic values: `critical|warning|notice` and `loss-risk|config-risk` respectively.
`--followed <true|false>` also requires `--user-id <employee-id>` and `--email <email-prefix>` because the unauthenticated API cannot infer the current user.

## Output

Text mode renders the complete normalized detail as formatted JSON. JSON mode uses the common bytedcli envelope:

```json
{
  "status": "success",
  "data": {
    "hive_rule": {
      "id": 12345
    }
  },
  "error": null,
  "context": {}
}
```

Offline results use `data.offline_result`. Response bodies are treated as sensitive, so HTTP debug and trace output omit SQL and abnormal data rows.

Hive-rule detail enum fields use semantic values compatible with write payloads. Their original numeric values are retained in `*Code` fields, while original Bamboo `是`/`否` text is retained in `*Text` fields next to normalized booleans.

List results use `data.hive_rules`, `data.page`, `data.page_size`, and `data.total`. The list response body is also treated as sensitive because each row may include SQL.

Mutation previews use `status: "dry_run"` and include the exact snake_case POST body under `data.request.body`. Live write request and response bodies are both excluded from HTTP debug and trace output. Read [`hive-rule-write-payloads.md`](hive-rule-write-payloads.md) before preparing a create or update payload.
