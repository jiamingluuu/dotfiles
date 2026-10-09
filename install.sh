#!/bin/sh
set -eu
case "$#:${1-}" in
    0:|1:--agents-only) ;;
    *) printf 'Usage: %s [--agents-only]\n' "$0" >&2; exit 1 ;;
esac
cd "$HOME/dotfiles"

link_path() {
    source="$PWD/$1"
    target="$HOME/$2"
    [ -e "$source" ] || { printf 'Missing source: %s\n' "$source" >&2; exit 1; }
    if [ -L "$target" ] && [ "$target" -ef "$source" ]; then
        return
    fi
    mkdir -p "$(dirname "$target")"
    if [ -e "$target" ] || [ -L "$target" ]; then
        backup_base="$HOME/${3:-$2.backup}"
        backup=$backup_base
        suffix=1
        while [ -e "$backup" ] || [ -L "$backup" ]; do
            backup="$backup_base.$suffix"
            suffix=$((suffix + 1))
        done
        mkdir -p "$(dirname "$backup")"
        mv "$target" "$backup"
        printf 'Backed up %s to %s\n' "$target" "$backup"
    fi
    ln -s "$source" "$target"
    printf 'Linked %s -> %s\n' "$target" "$source"
}

if [ "${1-}" != --agents-only ]; then
    link_path .zshrc .zshrc
    link_path .vimrc .vimrc
    for config in zed wezterm nvim tmux alacritty; do
        link_path "$config" ".config/$config"
    done
    link_path jj/config.toml .config/jj/config.toml
fi

# Link configuration only; leave credentials, sessions and caches in place.
for config in AGENTS.md config.toml keybindings.json agents hooks hooks.json rules; do
    link_path "codex/.codex/$config" ".codex/$config"
done
link_path codex/.codex/browser/config.toml .codex/browser/config.toml

# Preserve managed .system skills and keep backups outside skill discovery.
for skill in codex/.codex/skills/*; do
    name=${skill##*/}
    link_path "$skill" ".codex/skills/$name" ".codex/dotfiles-backups/skills/$name"
done
link_path .agents/AGENTS.md .agents/AGENTS.md
link_path .agents/skills .agents/skills
link_path claude/.claude/settings.json .claude/settings.json
link_path codex/.codex/AGENTS.md .claude/CLAUDE.md
link_path .agents/skills .claude/skills
