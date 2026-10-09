# Dotfiles

Run `~/dotfiles/install.sh` to install everything. The script uses fixed paths
under `~/dotfiles`, `~/.config`, `~/.codex`, `~/.claude` and `~/.agents`;
pass `--agents-only` to install only Codex, Claude and shared agent configs.
Existing targets are renamed to `.backup`, `.backup.1`, etc. Codex skill backups
go under `~/.codex/dotfiles-backups/skills/` to avoid duplicate skill discovery.
Already-correct symlinks are left alone, so repeated runs make no changes.
Each source is checked before its target is replaced.

## Agent configuration

| Repository source | Installed location |
| --- | --- |
| `.agents/AGENTS.md` | `~/.agents/AGENTS.md` |
| `.agents/skills/` | `~/.agents/skills`, `~/.claude/skills` |
| `codex/.codex/AGENTS.md` | `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md` |
| `codex/.codex/config.toml` | `~/.codex/config.toml` |
| `codex/.codex/keybindings.json` | `~/.codex/keybindings.json` |
| `codex/.codex/agents`, `hooks`, `hooks.json`, `rules` | Corresponding paths in `~/.codex/` |
| `codex/.codex/browser/config.toml` | `~/.codex/browser/config.toml` |
| Each directory in `codex/.codex/skills/` | Corresponding skill in `~/.codex/skills/` |
| `claude/.claude/settings.json` | `~/.claude/settings.json` |

The legacy `codex/.agents/skills` path links to `.agents/skills` in this repo.
The latter is authoritative; it includes the newer OKR skill and the five
older engineering skills. Existing Codex-specific skill copies are kept
separate because their versions may differ. Codex's managed `.system` skills
are left in place. Claude shares the complete shared skill collection.

The live Codex configuration was imported on 2026-10-08, replacing the older
machine's snapshot. Its currently empty `AGENTS.md` is preserved as-is;
`.agents/AGENTS.md` remains a separate instruction file. Settings, model names,
and permissions were not changed during migration. Existing agent definitions
and hooks remain available; migration does not enable them in the config.

`config.toml` contains machine-specific paths, project trust entries and app
integration settings. Review these on another machine before installing.
Applications may rewrite their own configuration or replace a symlink; inspect
`git diff` and rerun the installer when needed. Keep secrets in the tools'
local credential stores, not in tracked configuration or skills.

Credentials, history, sessions, databases, plugin caches, computer-use app
binaries and scheduled automation state remain under the original home
directories. Home `.agents/.skill-lock.json` is also left local; the existing
repository lockfile is only a snapshot. Never replace the entire `.codex` or
`.claude` directory with a symlink.

## Other configuration

The installer also links zsh, Vim, Zed, WezTerm, Neovim, tmux, Alacritty and
`jj/config.toml`. The iTerm2 entries are an application-support link and runtime
sockets; Raycast and NVIDIA runtime directories are not migrated. Existing
VS Code exports remain available in `vscode/` for manual import.

## Restore a previous config

Remove only the installed symlink, then rename its adjacent `.backup` (or the
appropriate numbered backup) to the original name. For Codex skills, restore
from `~/.codex/dotfiles-backups/skills/` instead. Backups are retained and
ignored by Git. No credentials or runtime directories need to be restored.
