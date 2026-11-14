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
  Claude, Codex, Grok, Cursor and Antigravity (`agy`) through their official
  installers. Pass names to select a subset. Sign in through each CLI;
  credentials stay outside this repo.
- Updates: `claude update`, `grok update`, `cursor-agent update`; `agy`
  self-updates; for Codex, rerun `./scripts/install-ai --apply codex`. Keep
  vendor auto-updates enabled.
  Use `grok` and `cursor-agent`, not the ambiguous `agent` command.
- The Antigravity installer runs `agy install` to configure the shell. `~/.zshrc`
  and `~/.zprofile` link into this repo, so `install-ai` warns if any installer
  changes tracked files; review and revert unwanted edits.
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

## Claude desktop cleanup

Deleting a Claude Code session in the desktop app removes only the app's record;
the transcript, tool results, scratchpad, edit history and worktree stay behind.
Bootstrap links `claude-sweep` into `~/.local/bin`; the LaunchAgent is opt-in:

```sh
claude-sweep                    # Preview what would be cleaned and what is held back
claude-sweep --apply            # Clean now
claude-sweep install --apply    # LaunchAgent: run on every deletion, and daily
claude-sweep doctor             # LaunchAgent state, recent log, held-back sessions
claude-sweep uninstall --apply
```

- Only sessions with the app's `deleted_<id>` marker and no remaining record are
  swept; archived sessions are never touched. A session whose transcript is still
  open, or that was deleted under 30 seconds ago, waits for the next pass.
- A worktree under `.claude/worktrees/` is removed with its `claude/*` branch only
  when it has no uncommitted or untracked changes and no commits that another
  branch, tag or remote lacks. Otherwise it is held back and listed by doctor.
- Everything is moved to `~/.local/state/claude-sweep/trash/<date>/<id>/` and
  purged after 7 days; a removed branch's last commit is in
  `~/Library/Logs/claude-sweep.log`. Each ID is processed once (`done` ledger).
- `install` watches the account folders that exist at the time. When doctor reports
  `UNWATCHED` (a new account), run `uninstall --apply`, then `install --apply`.

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
OpenAI-compatible endpoint at `http://127.0.0.1:8080` and starts the requested
model on demand: `llama-server` (llama.cpp) for GGUF, one `omlx serve` process per
MLX model. Shared `bootstrap` never installs it.

```sh
./scripts/llmctl install            # Preview
brew trust --formula mostlygeek/llama-swap/llama-swap  # Third-party taps; once per Mac
brew tap jundot/omlx https://github.com/jundot/omlx && brew trust --formula jundot/omlx/omlx
xcodebuild -downloadComponent MetalToolchain  # oMLX custom kernels need full Xcode + this
./scripts/llmctl install --apply    # config/llm/Brewfile, links, LaunchAgent
exec zsh -l                         # Loads ~/.config/llm/env (LLM_HOME, HF_HOME)
llmctl pull qwen3.8-27b             # Preview the download and its size
llmctl pull --apply qwen3.8-27b
llmctl start                        # Then open http://127.0.0.1:8080/ui
llmctl stop
llmctl smoke                        # Start, ask qwen3.8-27b one question, stop again
llmctl doctor
```

On the workstation llama-swap runs only between `llmctl start` and `llmctl stop`,
never at login: it is a backup for the inference server and a place for
experiments, not a resident service. Register it in clients as its own endpoint
(`http://127.0.0.1:8080/v1`) next to the server's URL; model IDs match the
server's, so the same names work on either. Run `llmctl smoke` after upgrading
llama.cpp, or now and then, so the backup is known to work before it is needed.

- Declarations live here: `config/llm/models.tsv` (what to download, with
  space-separated include patterns for extra files such as a vision projector,
  and whether it is `gguf` or `mlx`) and `config/llm/llama-swap.yaml` (how to serve it). Use
  the same names in both; `llmctl doctor` reports drift. Requests never trigger
  downloads. `config/llm/templates` (linked to `~/.config/llm/templates`) holds
  chat templates that replace outdated ones embedded in a GGUF; after pulling a
  change that adds this link, rerun `llmctl install --apply`.
- llama-swap alone decides what stays loaded. Each model declares the GPU memory
  it needs (`capacities.gpu`, GB) against a 96 GB pool, and llama-swap unloads
  others until the requested model fits. oMLX runs one model per process, each
  with its own base path, so its own multi-model eviction never comes into play.
- State stays outside the repo in `~/.local/share/llm` (`models/` GGUF, `mlx/`,
  `omlx/` per-model oMLX settings and SSD KV cache, `hf/`, `bench/`; excluded from
  Time Machine) and `~/Library/Logs/llm`.
- `install` writes the LaunchAgent plist. The workstation keeps it at
  `~/.local/share/llm/launchd/local.llm.llama-swap.plist`, which launchd never loads
  on its own; `llmctl start` loads it and restarts llama-swap if it crashes until
  `llmctl stop`. The server profile writes it to `~/Library/LaunchAgents` to start at
  login. Reinstalling a workstation removes the login copy earlier versions wrote.
  llama-swap reloads its config when the linked file changes. To change the
  template, run `llmctl stop`, move the old plist away, and reinstall.
- The large MoE needs more GPU memory than the macOS default (Metal's recommended
  working set, about 107 GB on a 128 GB Mac).
  `llmctl doctor` prints the `sudo sysctl iogpu.wired_limit_mb=...` command;
  the setting resets on reboot and is left to you.
- `llmctl bench --apply NAME` records `llama-bench` results for GGUF models with
  the llama.cpp version under `~/.local/share/llm/bench`. Stop llama-swap first.
- The server listens on localhost only and has no API key. Add keys through
  1Password before exposing it beyond your own tailnet.

### Inference server profile

A second Mac can run the daily model for every device on the tailnet, while the
workstation keeps the large MoE and research. The server profile links
`config/llm/llama-swap.server.yaml` instead: the daily model, preloaded at
startup, plus GGUF models that fit a 48 GB Mac alone. llama-swap runs one at a
time there, so requesting another model unloads the current one until the daily
model is requested again. Any model idle for a week unloads (`globalTTL`). Later `llmctl` commands detect the profile from that
link, and `pull` without names fetches only the models the profile serves.
Apply the shared `bootstrap` on the server too. `config/llm/Brewfile` is shared,
so run the tap trust and Metal Toolchain steps above before installing.

```sh
./scripts/llmctl install --profile server           # Preview
./scripts/llmctl install --profile server --apply
exec zsh -l
llmctl pull --apply                                 # Only the server's models
llmctl start
llmctl serve                                        # Preview Tailscale Serve
llmctl serve --apply                                # https://<host>.<tailnet>.ts.net
llmctl doctor
```

- `serve` keeps llama-swap on `127.0.0.1:8080` and lets Tailscale Serve proxy HTTPS
  from the tailnet only; enable HTTPS certificates in the Tailscale admin console
  first. Every device on the tailnet can call it, since there is no API key.
  `llmctl serve --off --apply` withdraws it. Clients use
  `https://<host>.<tailnet>.ts.net/v1` as an OpenAI-compatible base URL.
- To switch a Mac between profiles, run `llmctl stop`, remove the
  `~/.config/llama-swap/config.yaml` link, and install with the other profile.

Set these on the server by hand, once:

- Energy: `sudo pmset -c sleep 0 disksleep 0 womp 1 autorestart 1`. A MacBook
  still sleeps when its lid closes without an external display, so leave the lid
  open. MacBooks ignore `autorestart` (it is missing from `pmset -g cap`); their
  battery rides out short outages instead.
- Automatic login for the server's user: the LaunchAgent starts only in a logged-in
  session. That requires FileVault off. If you keep FileVault on, use
  `sudo fdesetup authrestart` for planned restarts and unlock by hand after a
  power loss; the model is down until then.
- Battery: limit charging (Optimized Battery Charging or a charge-limit tool),
  since the server stays plugged in.
- Software Update: keep security updates, but turn off automatic installs that
  restart the Mac unattended.
- Remote Login (System Settings → General → Sharing) for SSH over the tailnet.

## Check changes

```sh
python3 -m unittest discover -s tests
for script in scripts/*; do bash -n "$script"; done
for config in config/zsh/*; do zsh -n "$config"; done
```

Tests use temporary homes and stubbed login/process checks; they do not install
packages, use real credentials or switch the current Mac's account.
