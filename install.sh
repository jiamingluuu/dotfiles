#!/bin/sh

set -eu

DOTFILES_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

link_path() {
    source=$1
    target=$2

    mkdir -p "$(dirname -- "$target")"

    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        return
    fi

    if [ -e "$target" ] || [ -L "$target" ]; then
        backup="${target}.backup"
        suffix=1

        while [ -e "$backup" ] || [ -L "$backup" ]; do
            backup="${target}.backup.${suffix}"
            suffix=$((suffix + 1))
        done

        mv "$target" "$backup"
        printf 'Backed up %s to %s\n' "$target" "$backup"
    fi

    ln -s "$source" "$target"
    printf 'Linked %s -> %s\n' "$target" "$source"
}

link_path "$DOTFILES_DIR/.zshrc" "$HOME/.zshrc"
link_path "$DOTFILES_DIR/.vimrc" "$HOME/.vimrc"

link_path "$DOTFILES_DIR/zed" "$HOME/.config/zed"
link_path "$DOTFILES_DIR/wezterm" "$HOME/.config/wezterm"
link_path "$DOTFILES_DIR/nvim" "$HOME/.config/nvim"
link_path "$DOTFILES_DIR/tmux" "$HOME/.config/tmux"
link_path "$DOTFILES_DIR/alacritty" "$HOME/.config/alacritty"

# Install only tracked Codex configuration, preserving Codex's runtime data.
link_path "$DOTFILES_DIR/codex/.codex/AGENTS.md" "$HOME/.codex/AGENTS.md"
link_path "$DOTFILES_DIR/codex/.codex/config.toml" "$HOME/.codex/config.toml"
link_path "$DOTFILES_DIR/codex/.codex/hooks" "$HOME/.codex/hooks"
link_path "$DOTFILES_DIR/codex/.codex/hooks.json" "$HOME/.codex/hooks.json"
link_path "$DOTFILES_DIR/codex/.codex/rules" "$HOME/.codex/rules"

# Codex and Claude Code share the same instructions and user skills.
link_path "$DOTFILES_DIR/codex/.agents/skills" "$HOME/.agents/skills"
link_path "$HOME/.codex/AGENTS.md" "$HOME/.claude/CLAUDE.md"
link_path "$HOME/.agents/skills" "$HOME/.claude/skills"
