# dotfiles

Personal Mac setup. Requires Command Line Tools and [Homebrew](https://brew.sh).

```sh
./scripts/bootstrap          # Preview
./scripts/bootstrap --apply  # Install Brewfile packages and symlink config
./scripts/doctor             # Check packages and links
```

Back up and move conflicting files before applying; bootstrap never overwrites them.
Keep Git identity and signing settings in `~/.config/git/config.local`
(see the SSH setup below).
After applying, edits to this clone affect live settings through symlinks; use a
separate worktree for review. To undo, remove only this repo's links and restore backups.

## Tools

- Shared tools: edit `Brewfile`, preview, apply, then run doctor.
- AI CLIs: `./scripts/install-ai` previews; `./scripts/install-ai --apply` installs
  Claude, Codex, Grok and Cursor through their official installers. Pass names to
  select a subset. Sign in through each CLI; credentials stay outside this repo.
- Updates: `claude update`, `grok update`, `cursor-agent update`; for Codex,
  rerun `./scripts/install-ai --apply codex`. Keep vendor auto-updates enabled.
  Use `grok` and `cursor-agent`, not the ambiguous `agent` command.
- Project runtimes and dependencies: keep declarations and lockfiles in that project.
  For Python, `uv` is managed in `Brewfile`. Use `uv python install <version>`
  for the runtime specified by the project, then sync its committed lockfile.

Apply uses `brew bundle install --no-upgrade`; explicit updates use
`brew bundle upgrade --file=./Brewfile`. Removing entries does not uninstall packages.
Brewfile does not pin versions. Doctor reports unmanaged Homebrew leaves/casks,
not every installed tool; `--strict` makes those findings fail the check.

## Codex account switching

On the new Mac, apply bootstrap as shown above, then install Codex and open a new
login shell:

```sh
./scripts/install-ai --apply codex
exec zsh -l
```

Bootstrap links `codex-switch` into `~/.local/bin`; `jq` is already in `Brewfile`.
Create `~/.codex/config.toml` if needed and set this key at the top level, before
any `[section]`. Update an existing key instead of adding a duplicate:

```toml
cli_auth_credentials_store = "file"
```

Quit the Codex/ChatGPT desktop app and all Codex CLI/app-server processes before
switching. The command refuses to switch while clients are running; it does not
close them for you. Sign in to each account once on the new Mac:

```sh
codex-switch a            # First use: browser login for account a
codex-switch b            # First use: browser login for account b
codex-switch a            # Switch to the saved account
codex-switch              # Show the current account and saved slots
codex-switch b --relogin  # Replace an expired login
```

Reopen the app or CLI after switching. Config, history and plugins stay shared;
only `auth.json` changes. Credentials and saved slots stay in `~/.codex`, outside
this repository. If `CODEX_HOME` is set, use that directory for both configuration
and credentials. Sign in afresh on each Mac rather than copying token files, and
do not run `codex logout` between switches.

## 1Password and GitHub

In 1Password Settings → Developer, enable CLI integration and the SSH Agent.
Reuse your authentication and signing keys; export only their **public** keys as
`~/.ssh/github-auth.pub` and `~/.ssh/github-signing.pub`. Register them on GitHub
as Authentication and Signing keys if not already registered.

On a new Mac, after bootstrap:

```sh
mkdir -p ~/.ssh ~/.config/git
chmod 700 ~/.ssh
test -e ~/.ssh/config || test -L ~/.ssh/config || install -m 600 config/ssh/config.example ~/.ssh/config
test -e ~/.config/git/config.local || test -L ~/.config/git/config.local || install -m 600 config/git/config.local.example ~/.config/git/config.local
```

Fill in your name/email in `~/.config/git/config.local`. If these files already
exist, merge the templates instead. With the public keys in place:

```sh
printf '%s %s\n' "$(git config user.email)" "$(cat ~/.ssh/github-signing.pub)" >> ~/.ssh/allowed_signers
./scripts/check-1password --authenticate
ssh -T git@github.com
```

Verify a new GitHub host fingerprint against [GitHub's published keys](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints).
GitHub's successful SSH greeting exits with status 1. Use SSH remotes
(`git@github.com:OWNER/REPO.git`); subsequent commits are signed automatically.
Check a signed commit with `git verify-commit HEAD`.

For secrets, use `op signin` and `op run --env-file=.env.1password.local -- <command>`
in the same shell; the ignored env file contains `op://` references.
Desktop integration uses your account permissions, not per-project restrictions.

## Local LLM stack (opt-in)

For Macs with enough unified memory. `llama-swap` serves every local model from one
OpenAI-compatible endpoint at `http://127.0.0.1:8080` and starts `llama-server`
(llama.cpp) for the requested model on demand. Shared `bootstrap` never installs it.

```sh
./scripts/llmctl install            # Preview
brew trust --formula mostlygeek/llama-swap/llama-swap  # Third-party tap; once per Mac
./scripts/llmctl install --apply    # config/llm/Brewfile, links, LaunchAgent
exec zsh -l                         # Loads ~/.config/llm/env (LLM_HOME, HF_HOME)
llmctl pull qwen3.8-27b             # Preview the download and its size
llmctl pull --apply qwen3.8-27b
llmctl start                        # Then open http://127.0.0.1:8080/ui
llmctl doctor
```

- Declarations live here: `config/llm/models.tsv` (what to download) and
  `config/llm/llama-swap.yaml` (how to serve it). Keep model names the same in
  both; `llmctl doctor` reports drift. Requests never trigger downloads.
- State stays outside the repo in `~/.local/share/llm` (`models/`, `hf/`,
  `bench/`, excluded from Time Machine) and `~/Library/Logs/llm`.
- `install` writes `~/Library/LaunchAgents/local.llm.llama-swap.plist`, which starts
  llama-swap at login. llama-swap reloads its config when the linked file changes.
  To change the template, run `llmctl stop`, move the old plist away, and reinstall.
- The large MoE needs more GPU memory than the macOS default (about 75% of RAM).
  `llmctl doctor` prints the `sudo sysctl iogpu.wired_limit_mb=...` command;
  the setting resets on reboot and is left to you.
- `llmctl bench --apply NAME` records `llama-bench` results with the llama.cpp
  version under `~/.local/share/llm/bench`. Stop llama-swap first.
- The server listens on localhost only and has no API key. Add keys through
  1Password before exposing it to other devices.

## Check changes

```sh
python3 -m unittest discover -s tests
for script in scripts/*; do bash -n "$script"; done
for config in config/zsh/*; do zsh -n "$config"; done
```

Tests use temporary homes and stubbed login/process checks; they do not install
packages, use real credentials or switch the current Mac's account.
