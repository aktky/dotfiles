#!/usr/bin/env python3
"""Integration tests: only temporary target homes, never real package installs."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name).resolve()
        self.repo = self.base / "repo with spaces"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.target = self.base / "target home"
        self.target.mkdir()

    def run_script(self, name, *args):
        return subprocess.run(
            [str(self.repo / "scripts" / name), "--links-only",
             "--target-home", str(self.target), *args],
            text=True, capture_output=True,
        )

    def test_preview_never_writes(self):
        result = self.run_script("bootstrap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_apply_is_idempotent_and_diagnosable(self):
        for _ in range(2):
            result = self.run_script("bootstrap", "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_script("doctor")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((self.target / ".gitconfig").resolve(),
                         self.repo / "config/git/config")
        self.assertFalse((self.target / ".config/git/config.local").exists())

    def test_conflict_stops_before_any_links(self):
        conflict = self.target / ".vimrc"  # Last entry: preflight must cover all.
        conflict.write_text("keep me")
        result = self.run_script("bootstrap", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(conflict.read_text(), "keep me")
        self.assertEqual(list(self.target.iterdir()), [conflict])

    def test_dangling_link_is_a_conflict(self):
        (self.target / ".gitconfig").symlink_to(self.base / "missing")
        result = self.run_script("bootstrap", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.target / ".zshrc").exists())

    def test_symlinked_parent_cannot_redirect_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.target / ".config").symlink_to(outside, target_is_directory=True)
        result = self.run_script("bootstrap", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.target / ".zshrc").exists())

    def test_missing_source_is_reported_by_doctor(self):
        self.assertEqual(self.run_script("bootstrap", "--apply").returncode, 0)
        (self.repo / "config/zsh/zshrc").unlink()
        self.assertNotEqual(self.run_script("doctor").returncode, 0)

    def test_missing_source_blocks_apply(self):
        (self.repo / "config/vim/vimrc").unlink()
        result = self.run_script("bootstrap", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_package_queries_detect_drift_without_installing(self):
        stub = self.base / "brew-stub"
        log = self.base / "brew-calls"
        stub.write_text("""#!/bin/bash
printf '%s\\n' "$*" >> "$DOTFILES_TEST_LOG"
case "$1 $2 $3" in
  'bundle check --no-upgrade') exit "${DOTFILES_TEST_MISSING:-0}" ;;
  'bundle list --brews') printf 'git\\ntmux\\nripgrep\\njq\\n' ;;
  'bundle list --casks') : ;;
  'leaves  ') printf 'git\\ntmux\\nripgrep\\njq\\nextra-tool\\n' ;;
  'list --cask ') : ;;
  *) echo 'Unexpected Homebrew operation' >&2; exit 90 ;;
esac
""")
        stub.chmod(0o755)
        env = dict(os.environ, DOTFILES_TEST_LOG=str(log))
        command = ["/bin/bash", "-c", r'''source "$1"
test_brew="$2"
find_brew() { brew_bin="$test_brew"; }
status=0
strict="$3"
check_packages
exit "$status"
''', "test", str(self.repo / "scripts/common.sh"), str(stub)]
        for strict, missing, expected in [("false", "0", 0), ("true", "0", 1), ("false", "1", 1)]:
            env["DOTFILES_TEST_MISSING"] = missing
            result = subprocess.run(command + [strict], env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertIn("extra-tool", result.stdout)
        calls = log.read_text()
        self.assertIn("--file=" + str(self.repo / "Brewfile"), calls)
        self.assertNotIn("install", calls)
        self.assertNotIn("cleanup", calls)

    def test_1password_check_is_opt_in_and_hides_account_output(self):
        bindir = self.base / "bin"
        bindir.mkdir()
        log = self.base / "op-calls"
        stub = bindir / "op"
        stub.write_text("""#!/bin/bash
printf '%s\\n' "$*" >> "$DOTFILES_TEST_LOG"
case "$1" in
  --version) echo '2.test' ;;
  signin) echo 'PRIVATE_SESSION'; exit "${DOTFILES_TEST_AUTH_FAILURE:-0}" ;;
  whoami) echo 'PRIVATE_ACCOUNT_METADATA'; echo 'PRIVATE_ERROR' >&2; exit "${DOTFILES_TEST_AUTH_FAILURE:-0}" ;;
  *) exit 90 ;;
esac
""")
        stub.chmod(0o755)
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.defpath,
                   DOTFILES_TEST_LOG=str(log))
        for key in ("OP_SERVICE_ACCOUNT_TOKEN", "OP_CONNECT_HOST", "OP_CONNECT_TOKEN"):
            env.pop(key, None)
        command = [str(self.repo / "scripts/check-1password")]
        result = subprocess.run(command, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(log.read_text().splitlines(), ["--version"])
        for failure in ("0", "1"):
            log.write_text("")
            env["DOTFILES_TEST_AUTH_FAILURE"] = failure
            result = subprocess.run(command + ["--authenticate"], env=env,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, int(failure))
            self.assertNotIn("PRIVATE_", result.stdout + result.stderr)
            self.assertEqual(log.read_text().splitlines(),
                             ["--version", "signin", "whoami"] if failure == "0"
                             else ["--version", "signin"])
        log.write_text("")
        env["OP_SERVICE_ACCOUNT_TOKEN"] = "test-placeholder"
        result = subprocess.run(command + ["--authenticate"], env=env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("whoami", log.read_text())
        self.assertNotIn("signin", log.read_text())
        self.assertNotIn("test-placeholder", result.stdout + result.stderr)

    def test_custom_home_cannot_install_packages(self):
        result = subprocess.run(
            [str(self.repo / "scripts/bootstrap"), "--apply",
             "--target-home", str(self.target)], capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.target.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
