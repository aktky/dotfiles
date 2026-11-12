#!/bin/bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
target_home="$HOME"
links() {
  printf '%s\n' 'config/zsh/zprofile|.zprofile' 'config/zsh/zshrc|.zshrc' \
    'config/git/config|.gitconfig' 'config/git/ignore|.config/git/ignore' \
    'config/tmux/tmux.conf|.tmux.conf' 'config/vim/vimrc|.vimrc' \
    'scripts/codex-switch|.local/bin/codex-switch'
}
find_brew() {
  brew_bin="$(command -v brew || true)"
  if [[ -z "$brew_bin" ]]; then
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      if [[ -x "$candidate" ]]; then brew_bin="$candidate"; break; fi
    done
  fi
  [[ -n "$brew_bin" ]]
}
normalize_target() {
  [[ -d "$target_home" ]] || { echo 'Target home must already exist.' >&2; exit 2; }
  target_home="$(cd "$target_home" && pwd -P)"
  [[ "$target_home" != / ]] || exit 2
}
check_parent() {
  local parent
  parent="$(dirname "$1")"
  while [[ "$parent" != "$target_home" && "$parent" != / ]]; do
    if [[ -L "$parent" || ( -e "$parent" && ! -d "$parent" ) ]]; then
      printf 'CONFLICT parent: %s\n' "$parent" >&2
      return 1
    fi
    parent="$(dirname "$parent")"
  done
}

# Updates the caller's status; strict also fails on unmanaged packages.
check_packages() {
  if find_brew; then
    if ! HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" bundle check --no-upgrade --file="$repo_root/Brewfile"; then
      echo 'Missing declared packages. Review bootstrap, then apply.'; status=1
    fi
    expected_brews="$(HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" bundle list --brews --file="$repo_root/Brewfile")" || exit 1
    expected_casks="$(HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" bundle list --casks --file="$repo_root/Brewfile")" || exit 1
    actual_brews="$(HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" leaves)" || exit 1
    actual_casks="$(HOMEBREW_NO_AUTO_UPDATE=1 "$brew_bin" list --cask)" || exit 1
    extras="$(LC_ALL=C comm -23 <(printf '%s\n' "$actual_brews" | LC_ALL=C sort -u) <(printf '%s\n' "$expected_brews" | LC_ALL=C sort -u)
  LC_ALL=C comm -23 <(printf '%s\n' "$actual_casks" | LC_ALL=C sort -u) <(printf '%s\n' "$expected_casks" | LC_ALL=C sort -u))"
    if [[ -n "$extras" ]]; then
      printf 'UNMANAGED Homebrew leaves/casks (review only):\n%s\n' "$extras"
      if $strict; then status=1; fi
    fi
  else
    echo 'MISSING Homebrew'; status=1
  fi
}
