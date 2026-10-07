# Devbox Command Reference

> All `--vmid` options auto-detect the instance when only one exists.
> Dangerous operations require `--yes` to execute.

## Instance management

### devbox list

List all Devbox instances.

```bash
bytedcli devbox list
bytedcli devbox list --status active
bytedcli --json devbox list
```

| Option | Description |
|--------|-------------|
| `--status <status>` | Filter by status (e.g., active, stopped) |
| `--flavor <flavor>` | Filter by flavor |

### devbox get

Get detailed information about a Devbox instance.

```bash
bytedcli devbox get
bytedcli devbox get --vmid <vmid>
```

| Option | Description |
|--------|-------------|
| `--vmid <vmid>` | Instance ID (optional, auto-detected) |

## Catalog & create

### devbox catalog

List purchasable flavors (with images/software/volume types) — the same dataset as the console's 创建开发机 page.

```bash
bytedcli devbox catalog
bytedcli devbox catalog --type GPU
bytedcli devbox catalog --flavor devbox_v.c1.4xlarge.v6
bytedcli devbox catalog --stock
```

| Option | Description |
|--------|-------------|
| `--type <type>` | Filter by flavor type, e.g. `通用型`, `GPU`, `云桌面` |
| `--flavor <id>` | Show one flavor's details (images, software_install versions, data volume types) |
| `--stock` | Include stock information (mirrors the UI's `get_stock=true`) |

### devbox create

Create a new devbox. **Dry-run by default**: preview the exact payload with `--dry-run`, then submit with `--yes`. GPU flavors with `need_apply` go through an xflow approval — track with `devbox xflow list`.

```bash
bytedcli devbox create --flavor devbox_v.c1.4xlarge.v6 \
  --image devbox_v-velinux-lyra-5.15.default \
  --data-volume-size 500 \
  --software "go=1.24.4,python=3.13.5" --dry-run
bytedcli devbox create --flavor devbox_v.c1.4xlarge.v6 --yes
# 云桌面 / Computer Use flavors require a password (username defaults to the JWT username)
bytedcli devbox create --flavor devbox_v.c1.4xlarge.gui --password-file ~/.secret/devbox-pw --yes
```

| Option | Required | Description |
|--------|----------|-------------|
| `--flavor <id>` | Yes | Flavor ID from `devbox catalog` |
| `--image <image>` | No | OS image ID (defaults to the flavor's default image) |
| `--data-volume-type <type>` | No | Data volume type ID (e.g. `bytedrive`) |
| `--data-volume-size <gb>` | No | Data volume size in GB (positive integer) |
| `--software <list>` | No | `"go=1.24.4,python=3.13.5"`; bare `id` picks the image's first offered version |
| `--username <username>` | No | Login username (defaults to the JWT username) |
| `--password-file <path>` | No* | File containing the password (* required for password flavors) |
| `--dry-run` | one of the two | Preview payload without submitting |
| `--yes` | one of the two | Submit for real |

## SSH & remote execution

### devbox ssh

Interactive SSH login or remote command execution.

```bash
# Interactive login
bytedcli devbox ssh

# Remote command execution
bytedcli devbox ssh --cmd "hostname && uptime"
bytedcli devbox ssh --cmd "cd /project && make build"

# JSON mode — connection info (no --cmd) or structured output (with --cmd)
bytedcli --json devbox ssh
bytedcli --json devbox ssh --cmd "docker ps"
```

| Option | Description |
|--------|-------------|
| `--vmid <vmid>` | Instance ID (optional, auto-detected) |
| `--cmd <command>` | Execute command remotely instead of interactive login |
| `--extra-args <args>` | Extra arguments passed to ssh |
| `--timeout <seconds>` | Timeout in seconds for `--cmd` mode (default: 60) |

**Behavior**:
- Without `--cmd`: spawns interactive `ssh user@ip` with terminal pass-through
- With `--cmd`: runs `ssh user@ip '<command>'`, captures stdout/stderr, propagates exit code
- If SSH fails with Permission denied, auto-runs `kinit` and retries once

### devbox scp

Copy files to/from a Devbox instance. Uploads by default; use `--download` for reverse.

```bash
# Upload local to remote
bytedcli devbox scp ./local/path /remote/path

# Download remote to local
bytedcli devbox scp --download /remote/path ./local/path

# JSON mode — connection info without spawning SCP
bytedcli --json devbox scp ./local/path /remote/path
```

| Option | Description |
|--------|-------------|
| `--vmid <vmid>` | Instance ID (optional, auto-detected) |
| `--download` | Download from remote to local (default is upload) |

**Behavior**:
- Always passes `-r` for recursive directory transfer
- If SCP fails with exit code 255 (auth failure), auto-runs `kinit` and retries once

### devbox ide

Open a remote IDE connection.

```bash
bytedcli devbox ide
bytedcli devbox ide --type cursor
bytedcli devbox ide --type trae
bytedcli --json devbox ide
```

| Option | Default | Description |
|--------|---------|-------------|
| `--vmid <vmid>` | auto | Instance ID |
| `--type <type>` | `vscode` | IDE type: `vscode`, `cursor`, `trae` |

## Monitor & Web Terminal

### devbox monitor

Print the Grafana monitor link(s) for an instance. `--open` launches the browser.

```bash
bytedcli devbox monitor
bytedcli devbox monitor --open
```

### devbox web-terminal

Get the Web Terminal (远程连接) console URL. Requires the instance to be initialized (`initcode == success`).

```bash
bytedcli devbox web-terminal
bytedcli devbox web-terminal --open
```

## Xflow approval jobs

### devbox xflow list

List pending approval jobs (e.g. GPU devbox creation). The console polls this only for China-BOE / SANDBOX / Singapore-BOE.

```bash
bytedcli devbox xflow list
```

## Dangerous operations (require `--yes`)

### devbox start

```bash
bytedcli devbox start --yes
```

### devbox stop

```bash
bytedcli devbox stop --yes
```

### devbox reboot

```bash
bytedcli devbox reboot --yes
```

### devbox rebuild

Reset system disk. With `--full`, wipes all disks.

```bash
bytedcli devbox rebuild --yes
bytedcli devbox rebuild --full --yes
```

| Option | Description |
|--------|-------------|
| `--full` | Wipe system + data disks (default: system only) |

### devbox delete

Permanently delete the instance.

```bash
bytedcli devbox delete --yes
bytedcli devbox delete --vmid <vmid> --yes
```

### devbox resize

Change machine type.

```bash
bytedcli devbox resize --flavor ecs.g3i.2xlarge --yes
```

| Option | Required | Description |
|--------|----------|-------------|
| `--flavor <flavor>` | Yes | Target flavor |

## Snapshot management

### devbox snapshot list / create

```bash
bytedcli devbox snapshot list
bytedcli devbox snapshot create --name "before-upgrade" --description "pre-upgrade state"
```

### devbox snapshot rollback / delete

Both are destructive and **dry-run by default** (`--dry-run` to preview, `--yes` to submit). Rollback clears all data written after the snapshot point and auto-starts the instance afterwards.

```bash
bytedcli devbox snapshot rollback --id <snapshotGroupId> --dry-run
bytedcli devbox snapshot rollback --id <snapshotGroupId> --yes
bytedcli devbox snapshot delete --id <snapshotGroupId> --yes
```

| Option | Required | Description |
|--------|----------|-------------|
| `--vmid <vmid>` | No | Instance ID (auto-detected) |
| `--id <snapshotGroupId>` | Yes | Snapshot group ID from `snapshot list` |

## Volumes

### devbox volume list

Lists the real cloud disks (system + data) with size, expansion limit and zone.

```bash
bytedcli devbox volume list
```

### devbox volume extend

Extend a volume to a new absolute size in GB. **Dry-run by default**; afterwards expand the partition inside the instance per the console guide.

```bash
bytedcli devbox volume extend --volume-id bytevol... --size 600 --dry-run
bytedcli devbox volume extend --volume-id bytevol... --size 600 --yes
```

| Option | Required | Description |
|--------|----------|-------------|
| `--vmid <vmid>` | No | Instance ID (auto-detected) |
| `--volume-id <id>` | Yes | Volume ID (`bytevol...`) from `volume list` |
| `--size <gb>` | Yes | Absolute target size in GB (must be > current, ≤ limit) |

## Computer Use sandbox

GUI-agent sandboxes (the console's Computer Use tab). `--sandbox-id` auto-detects when only one sandbox exists.

```bash
bytedcli devbox sandbox list
bytedcli devbox sandbox create --os linux --dry-run
bytedcli devbox sandbox create --os linux --yes
bytedcli devbox sandbox terminal --open
bytedcli devbox sandbox run --task "打开浏览器搜索 ByteDance" --timeout 300
bytedcli devbox sandbox delete --sandbox-id <id> --yes
```

| Command | Notes |
|---------|-------|
| `sandbox list` | `{SandboxId, OsType, Status, Eip, PrimaryIp}` |
| `sandbox create --os windows\|linux` | dry-run by default |
| `sandbox terminal [--open]` | Assembles the noVNC console URL from the sandbox token |
| `sandbox delete` | dry-run by default; contents are emptied |
| `sandbox run --task <text>` | Streams planner events; `--model`, `--system-prompt(-file)`, `--timeout <sec>`; JSON mode emits one NDJSON event per line |
