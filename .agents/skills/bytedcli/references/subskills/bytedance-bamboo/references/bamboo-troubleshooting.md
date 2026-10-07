# Bamboo troubleshooting

## Command or option is missing

Check the available resource groups and keep the required ID in `--id`:

```bash
bytedcli bamboo --help
bytedcli bamboo hive-rule list --help
bytedcli bamboo hive-rule get --help
bytedcli bamboo hive-rule create --help
bytedcli bamboo hive-rule update --help
bytedcli bamboo offline-result get --help
```

The rule/result ID must be a positive integer. Hive rule IDs and offline result IDs are different resource types. Rule listing also requires a non-empty `--space-id`.

## Invalid mutation payload

`BAMBOO_INPUT_ERROR` means the normalized JSON payload is missing a required field, contains an unknown field, violates an enum/range, has a Cron expression inconsistent with `runFrequency`, or fails another conditional rule. It also reports `hive-rule list --followed` calls missing `--user-id` or `--email`. Use exactly one of `--payload` and `--payload-file`, then compare write JSON with [`hive-rule-write-payloads.md`](hive-rule-write-payloads.md).

Do not add `--yes` while fixing validation. A valid command without `--yes` prints the exact POST body and performs no write.

## Resource not found

- `BAMBOO_HIVE_RULE_NOT_FOUND`: verify that `--id` is a Hive rule ID.
- `BAMBOO_OFFLINE_RESULT_NOT_FOUND`: verify that `--id` is an offline check result ID.

Do not retry one ID across both commands unless its resource type is genuinely unknown.

## Network failure

These endpoints require access to the ByteDance office network. Confirm network reachability and retry the same read-only command or dry-run.

The endpoints are unauthenticated. Do not run `auth login`, copy browser cookies, or add JWT environment variables to fix Bamboo network or not-found errors.

If a live create/update with `--yes` times out or disconnects, the write outcome is uncertain. Query by unique rule name or rule ID before retrying.

## Unexpected response

`BAMBOO_API_RESPONSE_PARSE_ERROR`, `BAMBOO_HIVE_RULE_LIST_RESPONSE_PARSE_ERROR`, `BAMBOO_HIVE_RULE_RESPONSE_PARSE_ERROR`, `BAMBOO_HIVE_RULE_CREATE_RESPONSE_PARSE_ERROR`, and `BAMBOO_OFFLINE_RESULT_RESPONSE_PARSE_ERROR` indicate that Bamboo returned a shape outside the documented contract. Preserve the error code and endpoint context when reporting the issue; do not print or attach raw response bodies because they may contain SQL and abnormal data rows.
