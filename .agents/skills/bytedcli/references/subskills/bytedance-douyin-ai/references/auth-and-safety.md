# Authentication and mutation safety

Douyin AI is an internal CN-only domain. Outside chat_server, it exchanges the SSO browser session persisted by:

```bash
bytedcli --site cn auth login --session
```

for the MPSSO Cookie accepted by the fixed Douyin AI HTTPS origin, probes `/api/getUserInfo`, caches the derived Cookie, and performs at most one forced exchange/retry after an authentication failure. The Cookie is never returned in command output.

Inside chat_server, bytedcli first reads the injected `SECURE_SHARE_SESSION_ID`, with `SECURE_SHARE_SESSION` as a compatibility source. The value is used only in memory, only for the fixed Douyin AI HTTPS origin, and is never persisted or printed. If the injection is missing, the command returns `AUTH_REQUIRED` immediately. If the injected session is rejected, the command retries once with the same injected identity and then returns `AUTH_REQUIRED`; it does not fall back to a local session or JWT and does not start interactive login.

If a local command returns `AUTH_REQUIRED`, rerun the login command above. Before repeating a mutation, inspect its outcome and read back; an error after submission does not prove no write occurred. In chat_server, recreate the conversation or fix the `SECURE-SHARE-SESSION` injection instead. A ByteCloud JWT is never used as the Douyin AI Cookie.

Remote mutations return a deterministic dry-run plan unless `--yes` is present. Dry-run never creates a Workflow, uploads a package, changes permissions, takes a Workflow lock, creates a conversation, or sends a debug message. It may issue read-only requests to compute the current-to-target difference.

Workflow import additionally requires `--force` to acknowledge replacing the server draft. `--force` is not a substitute for `--yes`.

Ordinary Agent update/deploy have no `--force`. Get, export and previews never call the edit-status endpoint: despite its read-like name, it initializes/refreshes leases. Only explicit execution acquires the Agent editor lease, rereads under the lock, checks the baseline, sends at most one business write, verifies by readback and cleans up its own lease. Client locking/digests are not server-side atomic CAS. Unknown ownership or cleanup acknowledgement becomes a warning; it never authorizes releasing someone else's lock or replaying a write.

To bind an Agent deploy preview to execution, save it with `--plan-out <file>` and pass the same file back with `--plan <file> --yes`. The exclusive private file contains only target/draft identity and versioned configuration/mapping-input hashes. The original baseline is checked before no-op and again under the lease; a changed or missing draft rejects. `--plan-out` cannot accompany `--yes` or `--plan`. Direct `--yes` remains supported without a cross-invocation expectation. Baseline checks do not freeze resource runtime state or eliminate the final server-side race.

Agent writes disable request and auth-failure retries. The `preservation_scope=api_visible_config` boundary covers the existing read API, not invisible stored fields; server save/publish transformations are unchanged. A mismatch is `verification_failed`, an unverified submission is `submitted_unverified`, and uncertain transport is `outcome_unknown`. Each uses an error envelope and exit 1 while retaining the sanitized receipt in `data.result`. Confirmed business success with lease warnings uses `partial_success`/exit 1. Read back before considering another operation; never blindly retry or automatically roll back.

Agent ordinary output and HTTP traces omit Prompt, variable values and full config/resource snapshots; export writes sensitive configuration only to its explicit local file. Traces with sensitive body/URL flags also withhold error-message detail, retaining method, redacted URL, attempt and duration. Keep exported/input files protected and out of version control. Deploy publishes the whole current publishable draft, including web edits; `test_run_validated=false` explicitly means no automatic test run or trial Trace. Platform permission/safety checks still apply.
