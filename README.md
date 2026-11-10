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
- AI CLIs: use the vendor's installer/updater; bootstrap does not install these yet.
- Project runtimes and dependencies: keep declarations and lockfiles in that project.

Apply uses `brew bundle install --no-upgrade`; explicit updates use
`brew bundle upgrade --file=./Brewfile`. Removing entries does not uninstall packages.
Brewfile does not pin versions. Doctor reports unmanaged Homebrew leaves/casks,
not every installed tool; `--strict` makes those findings fail the check.

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

## Check changes

```sh
python3 tests/test_bootstrap.py
bash -n scripts/common.sh scripts/bootstrap scripts/doctor scripts/check-1password
zsh -n config/zsh/zprofile config/zsh/zshrc
```
