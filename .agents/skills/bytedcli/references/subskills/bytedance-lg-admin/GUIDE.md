---
name: bytedance-lg-admin
description: "Use when tasks involve LG Admin MaaS, Prifly, or PilotBench queries and batch-size throughput updates; LG Admin Torch package releases, release meta, or discards; Torch image builds; build-history form submission; cpu/cuda/mlu Torch version selection; serving/monitoring lookup; live-inspecting a pilot/snapshot pod; or LTS bugfix backport workflow (create Meego defect + Bits develop task + cherry-pick to LTS integration branch) through bytedcli lg-admin."
---

# LG Admin

Use `bytedcli lg-admin` for LG Admin operations. The command surface covers MaaS / Prifly / PilotBench queries plus the `pilotbench result update` batch-size throughput write, and the lg-admin Torch release page. Do not use this skill for general ICM release, history, repo, or build queries. Names containing lagrange, torch, cpu, cuda, or mlu may be repo/package identifiers; they are not enough to route to LG Admin. Do not use or describe `lagrange torch`. Use `bytedcli lg-admin torch` only when the user asks to submit a Torch package/image release, query or discard a known LG Admin package release version, or query a known LG Admin image task/build version.

## MaaS Queries and Batch-Size Updates

Use `lg-admin maas` to inspect MaaS / Prifly BU configuration, model metadata, and PilotBench perf records. Queries are read-only; the only write is `pilotbench result update`, which submits a new Throughput value for one batch_size back to Prifly.

Authentication reuses the bytedcli ByteCloud personal JWT. Complete `bytedcli auth login` before the first request.

```bash
bytedcli lg-admin maas meta get
bytedcli lg-admin maas bu list
bytedcli lg-admin maas bu get --bu demo-bu
bytedcli lg-admin maas model list --bu demo-bu --status online,offline
bytedcli lg-admin maas model get --bu demo-bu --model-name demo-model
bytedcli lg-admin maas pilotbench list --bu demo-bu --model-name demo-model --page 1 --page-size 20
bytedcli lg-admin maas pilotbench status get --record-id demo-record-id
bytedcli lg-admin maas pilotbench result get --record-id demo-record-id
bytedcli --json lg-admin maas model list --bu demo-bu
```

Command groups:

- `lg-admin maas meta get`: get global MaaS packages, business types, supported DCs, and region.
- `lg-admin maas bu list|get`: list Prifly BUs or read one BU's traffic configuration.
- `lg-admin maas model list|get`: list one BU's models or read one model's Prifly / Model Hub metadata.
- `lg-admin maas pilotbench list|status get|result get`: inspect profile records, perf task status, and detailed benchmark results.
- `lg-admin maas pilotbench result update`: write a new Throughput (QPS) for one `batch_size` back to Prifly (the only write command in this group).

Agent guidance:

- Put global `--json` before `lg-admin`: `bytedcli --json lg-admin maas pilotbench list --bu demo-bu --model-name demo-model`.
- `model list --status` accepts only comma-separated `online` and `offline`; both are queried by default.
- `pilotbench list` uses a 1-based `--page` and defaults to `--page 1 --page-size 20`.
- `pilotbench status get --record-id` and `pilotbench result get --record-id` both use the profile record's `recordId` / `record_id`.
- The Prifly result endpoint calls its backend selector `job_id`; the CLI maps `--record-id` internally, so do not expose `--job-id`.
- `pilotbench result update` submits directly (no dry-run) and only updates; it does not re-fetch state to verify. Required flags: `--bu`, `--record-id`, `--model-name`, `--package`, `--max-batch-size`, `--gpu-share-ratio`, `--num-cuda-ctx`, `--pilot-ipc-worker-cnt`, `--batch-timeout-ms`, `--batch-size`, `--throughput`, `--operator`. Ranges are validated before submitting: `--gpu-share-ratio` must be `1..100`, `--num-cuda-ctx` `1..64`, and `--max-batch-size` strictly larger than `--batch-size`. To verify the update took effect, run `pilotbench list` afterward.
- For a model investigation, first resolve the BU and model name from Forge / Serving information, then run `lg-admin maas model get`, followed by the PilotBench list, status, and result commands.
- See [`references/maas-perf.md`](references/maas-perf.md) for Perf task states, common stalls, and the capacity water-level formula.

## Torch Releases

Package release, matching the build history form:

```bash
bytedcli lg-admin torch release package build \
  --branch demo-branch \
  --platform cpu=2.7 \
  --platform cuda=2.10 \
  --platform mlu=2.10 \
  --comment dev
```

Submit with `--yes`; without it the command fetches meta and permission, then renders a dry-run summary. For agent-driven releases, submit with `--yes --wait` so the command does not report success until framework metadata and every requested platform are registered.

Useful package release flags:

- `--release-type DEV|LTS`
- `--pub-base branch|tag|commit`, plus `--branch`, `--git-tag`, or `--git-commit`
- `--regions cn,va`. A package intended for ForgeFE must include `cn`, because that release path registers `version_meta`; for ROW use `cn,va`, never `va` alone.
- `--platform cpu=2.10`, repeatable for `cpu`, `cuda`, `mlu`, or other supported platforms
- `--use-cache` / `--no-use-cache`
- `--skip-arm`, `--skip-arch <arch>`
- `--image-mode default|rebuild|custom|custom-cmd`
- `--image platform=namespace/image:tag` for `--image-mode custom`
- `--cmd-option platform=cmd` for `--image-mode custom-cmd`
- `--skip-permission`
- `--wait`, plus optional `--wait-timeout-ms` and `--poll-interval-ms`, to verify the asynchronous release through framework-metadata registration

Get the meta for a package release:

```bash
bytedcli lg-admin torch release package get \
  --release-version demo-release-version \
  --require-complete
```

The text output summarizes the release, supported platform artifacts, third-party artifacts, and an explicit `integrity` classification. Use `--json` when the complete meta payload is needed. Builds still in progress may return `version_meta: null` and `third_party_meta: null`. A terminal `status: success` with `version_meta: null`, an empty `supported_platforms`, or a missing requested platform is an incomplete release, not a ForgeFE-usable success.

Release acceptance rules for agents:

- Do not report a submitted package as successful from the build task's top-level `status` alone.
- For ForgeFE-selectable ROW builds, use `--regions cn,va`; copying a historical VA-only package's region list can reproduce a terminal release with no framework metadata.
- Prefer `package build ... --yes --wait`. If the submission was made without `--wait`, poll `package get`, then run `package get --require-complete` before handing the version to a user.
- Verify that `integrity.status` is `complete` and that `version_meta.supported_platforms` contains every requested platform. `third_party_meta` may legitimately be an empty array; the framework platform mapping is the required ForgeFE contract.
- If the release ends with null framework metadata, do not reuse that version. Re-submit the same commit with `--regions` including `cn` (ROW: `cn,va`) and `--use-cache`, then verify the replacement.

Discard a package release by its release version:

```bash
bytedcli lg-admin torch release package discard \
  --release-version demo-release-version
```

Add `--yes` to perform the discard. Without it, the command only renders a dry-run summary. The backend validates whether the current release status can be discarded.

Image release, matching the ICM build history form:

```bash
bytedcli lg-admin torch release image build \
  --branch demo-branch \
  --compute-platforms cpu,cuda,mlu \
  --regions cn \
  --comment dev
```

Query an image release task:

```bash
bytedcli lg-admin torch release image get --task-id 821
```

Useful image release flags:

- `--release-type DEV|LTS`
- `--pub-base branch|tag|commit`, plus `--branch`, `--git-tag`, or `--git-commit`
- `--regions cn,va`
- `--compute-platforms cpu,cuda,mlu`
- `--build-describe <text>`
- `--yes`

Routing hints for agents:

- User asks for ICM release/history/repo/build queries, including ICM prod, recent releases, build commit, build repository, or repo/build metadata: do not use this skill; use the top-level `icm` command/skill. Repo/package names containing lagrange, torch, cpu, cuda, or mlu do not change this routing.
- User asks to 发 LG 镜像 / 发布 LG 镜像 / LG Torch 镜像 / LG Admin 镜像 / build LG image / LG image release: use `lg-admin torch release image build`; use `lg-admin torch release image get` only when querying a known LG Admin image task id or build version.
- User asks to 发版 / 发版本 / 发布版本 / package release / Torch 版本发版: use `lg-admin torch release package build`.
- User asks to inspect / query / 拉取 the meta for a known LG Admin Torch package release version: use `lg-admin torch release package get --release-version <version>`.
- User asks to discard / disable / 废弃 / 下线 a known LG Admin Torch package release version: use `lg-admin torch release package discard --release-version <version>`; add `--yes` only after the user confirms the write.

## Serving Lookup

Get a Torch job's online serving deployments and monitoring pages by its Forge job id:

```bash
bytedcli lg-admin torch serving get --job-id 12345678
```

The command returns:

- the Forge job page URL (`https://reckon.bytedance.net/forge2/jobs/<job-id>`);
- the Forge serving **prifly** monitoring page(s) for this job (`https://reckon.bytedance.net/forge2/prifly/<prifly-id>`), auto-resolved from the Reckon serving API;
- the two Merlin serving PSM detail pages for this job — `snapshot.<biz>.model_<job-id>` and `pilot_gpu.<biz>.model_<job-id>` — under `https://ml.bytedance.net/deployment/serviceList/psm/detail/<psm>`;
- with `--include-instances` (default on), each deployment's per-region instance hosts (IPs).

Useful serving flags:

- `--origin <url>` Merlin origin for lookup/auth, default `https://ml.bytedance.net`
- `--reckon-base-url <url>` Forge (Reckon) UI/API base, default `https://reckon.bytedance.net`
- `--include-instances` / `--no-include-instances` (use `--no-include-instances` to only return page URLs without extra deployment calls)

Notes:

- The prifly page id is the Forge serving service id, resolved from `GET /api/v1/model_serving/services?keyword=model_<job-id>`; if that lookup fails the command still returns the other pages and reports `prifly_error`.
- Use `--json` to get the full structured result (`forge_job_url`, `prifly[].prifly_url`, `merlin_origin`, `services[].psm_detail_url`, and `services[].deployments[].instances[]`).

Routing hint for agents:

- User asks 某个模型/部署的 serving 页面 / prifly 监控页 / snapshot 与 pilot 的 merlin 页面 / 监控链接 / 各地域实例 IP by a Forge job id: use `lg-admin torch serving get --job-id <job-id>`.
- User wants to 进容器排查 / 看 pilot 或 snapshot pod 的日志与缓存文件 / 定位容器进程 / 授权 root 后登机器 by a Forge job id: use `lg-admin torch serving inspect --job-id <job-id>`.

## Serving Inspect

Live-debug a deployed Torch job's pilot / snapshot pod. `serving get` reads metadata and IPs; `serving inspect` packages the manual "grant host root → ssh to the host → locate the container → read-only" sequence:

```bash
bytedcli lg-admin torch serving inspect --job-id 12345678 --target snapshot
bytedcli lg-admin torch serving inspect --job-id 12345678 --instance 10.0.0.1 --exec 'ls -l /opt/tiger/inductor'
bytedcli --json lg-admin torch serving inspect --job-id 12345678 --all-instances --yes
```

What it does per selected instance:

1. resolves the job's pilot (`pilot_gpu`) and snapshot instances (reusing `serving get`'s resolver), tagged by `idc`;
2. grants host root via orthrus (default on);
3. waits for the grant to propagate, then `bgo ssh root@<ip>` onto the **host**;
4. locates the container by process signature (`manhattan_worker` / `pilot_main` / `lgt_pilot_main` for pilot, `snapshot_model_optimizer` for snapshot), narrowed by `model_<job-id>` / `r<job-id>`, and reports the PID, `/proc/<pid>/root`, CRI id, and a ready-to-paste `nsenter` enter line;
5. with `--exec`, runs one read-only command inside the container namespace and captures its output.

Useful flags:

- `--target pilot|snapshot|both` (default `both`) — which machine type to inspect.
- `--idc <name>` — filter discovered instances to one data center (e.g. `cn`, `useast2a`); errors listing discovered idcs on no match.
- `--instance <ip>` — pin one instance, skipping selection. `--all-instances` — fan out to every discovered instance.
- `--grant` / `--no-grant` — grant host root before ssh (default on); `--no-grant` for ssh-only when the host is already owned.
- `--yes` — apply the grant in `--json` / non-TTY mode (otherwise it dry-runs and prints the grant that _would_ be issued).
- `--site cn|i18n|ttp` + `--account <user>` — required for non-cn instances (cn self-serves for the logged-in user).
- `--role root` (default), `--grant-timeout <1..24>` hours, `--grant-wait-ms <ms>` ssh-propagation deadline.
- `--exec '<cmd>'` read-only command; `--exec-max-bytes <n>` output cap; `--exec-timeout-ms <ms>` exec deadline.
- `--locate-timeout-ms <ms>` (default 60000) — host-side container-locate deadline; raise for slow hosts.

Agent guidance:

- Grant defaults on but only auto-applies in an interactive terminal. In `--json` / automation it dry-runs unless you pass `--yes` — pass `--yes` to actually grant root.
- `--exec` is read-only by convention (`cat` / `ls` / `grep` / `tail`); the command never writes to the pod. The located block never dumps `/proc/<pid>/environ` (secrets).
- After a grant, sshd propagation takes ~3-10 min. For automation, lower `--grant-wait-ms` to fail fast, or raise it for slow propagation.
- Prefer `--json` and pass `--instance <ip>` or `--all-instances` to avoid the interactive selection prompt; when a target has >1 instance and nothing is pinned, `--json` returns `selection_required` with the candidates instead of hanging.
- If the deployment is stopped, Merlin returns no live instance, so `inspect` finds nothing to inspect — it still surfaces the job's `serving_pages` (Forge prifly page + state) so you can confirm the pod is stopped rather than the job missing.
- Slow socket-hybrid hosts can take >30s just to open the `bgo ssh` connection; if the located block reports "locate probe timed out", raise `--locate-timeout-ms` (default 60000). Instance hosts may be bare IPv6 addresses (e.g. `fdbd:...`), which are supported.
- Container artifact paths worth reading via `--exec`: `/var/log/tiger/data.manhattan.log*` (serving log, "warmup model success" = ready), `/var/log/tiger/lgtorch_launch.log`, `/var/log/tiger/worker_<rank>_<n>.stderr` (recompile reasons), `/opt/tiger/inductor/{write_done,inductor.lock}` (extraction sentinel + lock).
- Container location is by process signature. The pilot compute process is `manhattan_worker` (its cmdline carries `--model_name=...r<job-id>_0`); `pilot_main` is only the launcher. `inspect` matches `manhattan_worker` first and narrows by both `model_<job-id>` and `r<job-id>` forms — necessary because one host commonly co-locates several models' containers, so matching on `pilot_main` alone (or the wrong job) lands in the wrong container.
- `bgo ssh` requires a pty (it puts the terminal in raw mode and crashes without one); `inspect` allocates one internally, so you do not need to. If you run `bgo ssh` by hand in a script/pipe it will `SIGSEGV` — wrap it with `script -q /dev/null bgo ssh ...`.

Healthy-pilot check recipe (does the model load the precompiled `inductor.zip` and come up without recompiling?):

```bash
bytedcli --json lg-admin torch serving inspect --job-id <job-id> --target pilot --instance <ip> --no-grant \
  --exec 'ls /opt/tiger/inductor/write_done; grep -c "warmup model success" /var/log/tiger/data.manhattan.log; grep -ciE "recompil|guard fail" /var/log/tiger/worker_*.stderr'
```

Healthy = `write_done` exists (inductor.zip extracted) + `warmup model success` present + recompile count 0. Missing `write_done` or a non-zero recompile count means the pod cold-compiled / is recompiling per request batch size.

## LTS Bugfix Cherry-Pick

For LTS bugfixes, the goal is to bring **only the target commit's changes** onto the LTS integration branch — never the whole `master`.

### Commands

```bash
# Create a Meego defect + Bits bugfix develop task bound to the latest LTS release
bytedcli lg-admin torch lts create-meego-bits \
  --meego-space <meego-space> \
  --psm <service.psm> \
  --bits-space-id <bits-space-id> \
  --description "<what the fix does>" \
  --mr <mr-url-or-iid>

# Or specify explicit commit SHAs instead of an MR
bytedcli lg-admin torch lts create-meego-bits \
  --meego-space <meego-space> \
  --psm <service.psm> \
  --bits-space-id <bits-space-id> \
  --description "<what the fix does>" \
  --commit <sha1>,<sha2>

# Specify LTS version prefix (default: 1.8)
bytedcli lg-admin torch lts create-meego-bits \
  --meego-space <meego-space> --psm <service.psm> --bits-space-id <bits-space-id> \
  --description "<what the fix does>" --lts-version 1.9 --commit <sha>
```

### Prerequisites and auth (do this first, before starting the flow)

`create-meego-bits` chains three back-ends, each with its own login. Interactive logins (Meego device-code, Feishu QR) expire in ~10 minutes, so authenticate **all of them upfront** rather than discovering each gap mid-flow:

1. **ByteCloud** (codebase MR lookup, lg-admin): `bytedcli auth status` → `Authenticated: Yes`.
2. **Meego** (defect creation): `bytedcli meego status` → `Authenticated: Yes`. If not, `bytedcli meego login` (device-code — approve within 10 min).
3. **Meego GoAPI / Feishu web session** (required to set a defect's **role** fields such as 经办人): `bytedcli meego status` → `GoAPI: ready`. If `missing`, run `bytedcli auth login --session --feishu` (QR scan; also ~10-min expiry).
4. **bitscli JWT** (Bits develop task): `bitscli` fetches its own JWT via `agentbuddy get-jwt`. If that fails with `could not determine executable to run`, export a ByteCloud JWT instead:
   `JWT=$(bytedcli auth get-bytecloud-jwt-token); USER_CLOUD_JWT="$JWT" AIME_USER_CLOUD_JWT="$JWT" bitscli devops dev-task create ...`

**Meego defect creation caveats (why the automated create can fail):**

- **Required role fields are not settable via the MCP `create_workitem` path.** If the space's defect template makes 经办人 (assignee) required, the default (auto-chat) MCP create fails with `ErrFieldRequired ... (role_<space>_<type>_role_<id>) 必填` — roles are not part of the `create_workitem` `fields` schema. Set them only through the GoAPI path: `bytedcli meego workitem create --no-auto-chat ... --role-owner '经办人:<username>'` (needs the Feishu session from step 3, and does **not** pull a sync group). Resolve the role via `bytedcli meego workitem config role list --project-key <space> --work-item-type issue`.
- **`tree-multi-select` fields** (e.g. 业务 / 组件名称) are rejected by MCP `create_workitem` in every encoding (`[{option_id}]`, bare id, `[{key}]`). Templates that make these required cannot be created through MCP — use the GoAPI/web path. Look up their keys and option ids via `bytedcli meego workitem config field list --project-key <space> --work-item-type issue`.
- **GoAPI create returning `code=-214034` with an empty message** is a pre-commit web-form/permission rejection (no stray ticket is created). It persists even for a minimal name+template body, so it is not a field-encoding problem. When it blocks you, fall back to filling the **新建缺陷** form on the Meego web page (resolve template, assignee, priority, and required tree-selects there), then continue the Bits/cherry-pick steps with the created work-item URL.
- Verify you did not leave probe/duplicate tickets after failed attempts:
  `bytedcli meego workitem list --project-key <space> --mql "SELECT work_item_id, name FROM <simpleName>.issue WHERE name LIKE '%<keyword>%'"` (note: MQL uses the space **simpleName**, `work_item_id` not `id`).

### Cherry-pick rules (keep the diff minimal)

1. **Branch from the LTS integration branch**, not from `master`.
   - The LTS integration branch name follows the pattern `integration_lts<ver>_<timestamp>_<ticket-id>` (e.g. `integration_lts1.8.9_2026-09-02_<ticket-id>`).
   - To find the exact integration branch for your LTS release, run `bytedcli bits develop inspect-changes --dev-id <bits-dev-id>` and read the `target_branch` of the bound change card.
   - The `create-meego-bits` command generates a working branch name `lts-bugfix-<meego-work-item-id>` and passes it as the change card's `source_branch`. Bits creates this branch from the LTS integration branch automatically. If the integration branch cannot be resolved from the release ticket, the command throws `LG_ADMIN_TORCH_LTS_INTEGRATION_BRANCH_UNRESOLVABLE` (no silent fallback to `master`).

2. **Cherry-pick the MR's original commit(s), not the merge commit.**
   - Resolve the MR's `source_commit` (from `Versions[].SourceCommitId`), not the `merge_commit`.
   - `git cherry-pick <source_commit>` — for multi-commit MRs, pass each commit in order.
   - Do **not** `git cherry-pick -m 1 <merge_commit>`: for squash-merged MRs the merge commit's parent-1 diff includes all of `master` since the branch point, not just the MR's changes.

3. **Resolve conflicts by keeping only the target commit's intent.**
   - For version-bump conflicts (e.g. `libtorch*.version`), take the incoming (MR) version.
   - For unrelated conflicts, prefer the LTS branch's content unless the commit explicitly changes that file.
   - **`modify/delete` conflict = the file does not exist on the LTS line.** Some modules are master-only (introduced after the LTS branch point, e.g. `context/manhattan_manager.py`). `git cherry-pick` reports these as `CONFLICT (modify/delete): <path> deleted in HEAD and modified in <commit>`. Before resolving, confirm with `git ls-tree -r --name-only <integration-branch> | grep <path>` and `git grep -l <symbol> <integration-branch>`. If the module genuinely does not exist on the LTS line, that part of the fix is **not applicable** — `git rm <path>` to drop it, keep the parts that do apply, and **state the exclusion in the amended commit message** (e.g. "the ManhattanManager pickle fix is N/A on release-1.8: module absent"). Do not fabricate the file onto the LTS branch. If dropping a part changes what the backport delivers, surface that to the user before pushing rather than silently shipping a partial pick.

4. **Verify the diff is minimal before pushing.**
   - `git diff --stat <integration-branch>...HEAD` should show only the files the MR touched.
   - If the diff includes unrelated files, the cherry-pick picked up extra changes — abort and redo from the integration branch.

5. **Push to the Bits task's working branch.**
   - The Bits develop task auto-creates a working branch (the change card's `source_branch`). Find it via `bytedcli bits develop inspect-changes --dev-id <bits-dev-id>`.
   - `git push origin HEAD:<working-branch>`
   - The Bits task auto-creates the MR targeting the LTS integration branch.
   - If you need to update the change card's source branch manually:
     `bytedcli bits develop change create --dev-id <bits-dev-id> --psm <psm> --type CUSTOM --branch <working-branch> --target-branch <integration-branch> --yes`
   - Confirm the MR has the expected commit count and file count.

### Common pitfalls

- **Shallow clone + cherry-pick** produces spurious `add/add` conflicts across the whole tree because git can't find the merge base. Use a full clone (`git fetch --unshallow`) before cherry-picking.
- **Picking the merge commit** (`-m 1`) for squash-merged MRs includes all of `master` since the branch point. Always pick the original source commit(s).
- **Source branch = master** on the Bits change card means the MR is `master → integration`, which is never what you want for an LTS backport.
- **Master-only module in the pick** shows up as a `modify/delete` conflict; it means that half of the fix does not apply to the LTS line. Drop it, keep the applicable half, and record the exclusion in the commit message (see Cherry-pick rule 3) — don't recreate the file on the LTS branch.
- **Interactive login expiry is the biggest time sink.** Meego device-code and Feishu QR both expire in ~10 min. Complete every login in the Prerequisites list before starting, not lazily when each command fails.

## Torch Auth And Headers

The native commands use the ByteCloud personal JWT flow and send lg-admin headers:

- `X-Jwt-Token`
- `X-Lgx-Admin-Control-Plane`, default `cn`
- `X-Lgx-Admin-Region`, default `cn`
- `X-Lgx-Admin-Domain-Id`, default `online`

Override API or header values with `--host`, `--control-plane`, `--admin-region`, and `--domain-id`.
