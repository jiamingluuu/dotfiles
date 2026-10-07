---
name: bytedance-devbox
description: "Manage development machines (Devbox) via bytedcli: list/get instances, purchase catalog browsing, instance creation (with xflow approval tracking), power management (start/stop/reboot), SSH access and remote command execution, SCP file transfer, IDE remote connection (VSCode/Cursor/Trae), Grafana monitor and Web Terminal links, snapshot management (list/create/rollback/delete), volume list/extend, and Computer Use sandbox management (list/terminal/create/delete/run)."
---

# bytedcli Devbox

## How to invoke bytedcli

Pick one invocation method. All examples below use `bytedcli` directly.

```bash
# Option 1: run latest via npx
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]

# Option 2: global install then call bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

## When to use

- List and inspect Devbox instances
- Browse the purchase catalog (flavors/images/volume types) and create a new Devbox
- Power management: start/stop/reboot/rebuild/delete/resize (require `--yes`)
- Track xflow approval jobs (e.g. GPU creation requests)
- SSH into a Devbox — interactive login or remote command execution (`--cmd`)
- SCP file transfer to/from a Devbox instance
- Open remote IDE session (VSCode, Cursor, Trae), Grafana monitor, or Web Terminal
- Manage snapshots: list, create, rollback, delete
- List volumes and extend a volume to a larger size
- Manage Computer Use sandboxes and run GUI-agent tasks on them

## Prerequisites

- ByteDance SSO authentication: `bytedcli auth login`
- 跨 site / vregion 操作（如 SG-BOE：`--site boe --vregion sg`）请先按 `../../invocation.md` 完成对应站点登录

## Quick start

All instance-specific commands auto-detect `--vmid` when you only have one Devbox.

```bash
# List all my devbox instances
bytedcli devbox list

# Get instance details
bytedcli devbox get

# SSH — interactive login
bytedcli devbox ssh

# SSH — remote command execution
bytedcli devbox ssh --cmd "hostname && uptime"
bytedcli devbox ssh --cmd "cd /project && make build && make run"

# SSH — remote command with custom timeout (seconds)
bytedcli devbox ssh --cmd "make build" --timeout 300

# Open IDE
bytedcli devbox ide
bytedcli devbox ide --type cursor

# Power management (require --yes)
bytedcli devbox stop --yes
bytedcli devbox reboot --yes
bytedcli devbox rebuild --yes
bytedcli devbox delete --yes
bytedcli devbox resize --flavor ecs.g3i.2xlarge --yes
bytedcli devbox start --yes

# Browse the catalog, then create a devbox (dry-run first)
bytedcli devbox catalog
bytedcli devbox catalog --type GPU
bytedcli devbox catalog --flavor devbox_v.c1.4xlarge.v6
bytedcli devbox create --flavor devbox_v.c1.4xlarge.v6 \
  --image devbox_v-velinux-lyra-5.15.default \
  --data-volume-size 500 \
  --software "go=1.24.4,python=3.13.5" --dry-run
bytedcli devbox create --flavor devbox_v.c1.4xlarge.v6 --yes

# GPU flavors need approval — track xflow jobs
bytedcli devbox xflow list

# Monitor & web terminal (add --open to launch the browser)
bytedcli devbox monitor
bytedcli devbox web-terminal --open

# Snapshots
bytedcli devbox snapshot list
bytedcli devbox snapshot create --name "before-upgrade"
bytedcli devbox snapshot rollback --id <snapshotGroupId> --dry-run
bytedcli devbox snapshot delete --id <snapshotGroupId> --yes

# Volumes
bytedcli devbox volume list
bytedcli devbox volume extend --volume-id bytevol... --size 600 --dry-run

# Computer Use sandbox (GUI agent)
bytedcli devbox sandbox list
bytedcli devbox sandbox create --os linux --yes
bytedcli devbox sandbox terminal --open
bytedcli devbox sandbox run --task "打开浏览器搜索 ByteDance"
```

## SSH access

```bash
# Interactive login (auto-detects instance)
bytedcli devbox ssh

# With explicit vmid
bytedcli devbox ssh --vmid sample-vm-001

# Remote command execution — returns stdout/stderr and exit code
bytedcli devbox ssh --cmd "systemctl status my-service"
bytedcli devbox ssh --cmd "docker compose up -d"

# Custom timeout for long-running commands (default: 60s)
bytedcli devbox ssh --cmd "make build" --timeout 300

# JSON mode — get connection info without spawning SSH
bytedcli --json devbox ssh

# JSON mode — get structured output from remote command
bytedcli --json devbox ssh --cmd "df -h"
```

If SSH fails with "Permission denied", the CLI automatically runs `kinit` to refresh Kerberos credentials and retries once.

## SCP file transfer

```bash
# Upload local file/directory to remote
bytedcli devbox scp ./local/path /remote/path

# Download from remote to local
bytedcli devbox scp --download /remote/path ./local/path

# With explicit vmid
bytedcli devbox scp --vmid sample-vm-001 ./data /home/user/data

# JSON mode — get connection info without spawning SCP
bytedcli --json devbox scp ./local/path /remote/path
```

If SCP fails with auth error (exit code 255), the CLI automatically runs `kinit` and retries once. The `-r` flag is always passed so directories are transferred recursively.

## IDE access

```bash
# Open VSCode (default)
bytedcli devbox ide

# Open Cursor or Trae
bytedcli devbox ide --type cursor
bytedcli devbox ide --type trae

# JSON mode — get URI without opening
bytedcli --json devbox ide --type vscode
```

## Snapshot management

```bash
bytedcli devbox snapshot list
bytedcli devbox snapshot create
bytedcli devbox snapshot create --name "before-upgrade"
```

## Volume info

```bash
bytedcli devbox volume list
```

## Dangerous operations

These commands require `--yes` to execute:

| Command | Effect |
|---------|--------|
| `devbox stop --yes` | Shut down the instance |
| `devbox reboot --yes` | Restart the instance |
| `devbox rebuild --yes` | Reset system disk (data disk preserved) |
| `devbox rebuild --full --yes` | Wipe all disks |
| `devbox delete --yes` | Permanently delete the instance |
| `devbox resize --flavor <f> --yes` | Change machine type |

## Notes

- `--vmid` is optional — auto-detected when only one instance exists
- `--json` (global option, before subcommand) for structured output: `bytedcli --json devbox list`
- SSH remote exit code is propagated to the CLI process
- IDE `--type` defaults to `vscode`

## References

- `references/devbox-commands.md`
- `../../invocation.md`
- `../../troubleshooting.md`
