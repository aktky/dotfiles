#!/usr/bin/env python3
"""Exercise account switching with fake credentials/clients in temporary homes."""
import base64
import json
import os
import pathlib
import shutil
import signal
import stat
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts/codex-switch"


def credentials(name):
    payload = json.dumps({
        "email": name + "@example.test",
        "https://api.openai.com/auth": {"chatgpt_plan_type": "test"},
    }).encode()
    token = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    return json.dumps({"auth_mode": "chatgpt", "tokens": {
        "id_token": "header." + token + ".signature",
        "access_token": "fake-access-" + name,
        "refresh_token": "fake-refresh-" + name,
    }}) + "\n"


class CodexSwitchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-switch-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.home = self.base / "temporary home"
        self.home.mkdir()
        self.codex_home = self.home / ".codex"
        self.bindir = self.base / "fake bin"
        self.bindir.mkdir()
        jq = shutil.which("jq")
        self.assertIsNotNone(jq, "jq is required; install the Brewfile packages before testing")
        (self.bindir / "jq").symlink_to(jq)
        self.log = self.base / "calls"
        self.fixture = self.base / "login.json"
        self.fixture.write_text(credentials("fresh"))
        self.env = dict(os.environ, HOME=str(self.home),
                        CODEX_HOME=str(self.codex_home),
                        PATH=str(self.bindir) + os.pathsep + os.defpath,
                        SWITCH_TEST_LOG=str(self.log),
                        SWITCH_TEST_LOGIN_FILE=str(self.fixture))
        for key in ("BASH_ENV", "ENV", "OPENAI_API_KEY", "CODEX_API_KEY"):
            self.env.pop(key, None)
        self.make_stub("pgrep", r'''printf 'pgrep %s\n' "$*" >> "$SWITCH_TEST_LOG"
if [[ -n "${SWITCH_TEST_PRIOR_SWITCH:-}" && ! -e "$SWITCH_TEST_PRIOR_SWITCH" ]]; then
  cp "$SWITCH_TEST_LOGIN_FILE" "$CODEX_HOME/auth.json"
  printf 'b\n' > "$CODEX_HOME/accounts/.current"
  touch "$SWITCH_TEST_PRIOR_SWITCH"
fi
exit "${SWITCH_TEST_CLIENT_STATUS:-1}"
''')
        self.make_stub("codex", r'''printf 'codex %s\n' "$*" >> "$SWITCH_TEST_LOG"
[[ "${!#}" == login ]] || exit 90
[[ ! -e "$CODEX_HOME/auth.json" ]] || exit 91
cp "$SWITCH_TEST_LOGIN_FILE" "$CODEX_HOME/auth.json"
if [[ "${SWITCH_TEST_SIGNAL:-}" == TERM ]]; then kill -TERM "$PPID"; fi
exit "${SWITCH_TEST_LOGIN_STATUS:-0}"
''')
        for forbidden in ("pkill", "killall", "osascript"):
            self.make_stub(forbidden, 'echo FORBIDDEN >> "$SWITCH_TEST_LOG"; exit 95\n')

    @property
    def accounts(self):
        return self.codex_home / "accounts"

    @property
    def auth(self):
        return self.codex_home / "auth.json"

    @property
    def marker(self):
        return self.accounts / ".current"

    def make_stub(self, name, body):
        path = self.bindir / name
        path.write_text("#!/bin/bash\nset -eu\n" + body)
        path.chmod(0o755)

    def write_account(self, name, value=None):
        self.accounts.mkdir(parents=True, exist_ok=True)
        path = self.accounts / (name + ".json")
        path.write_text(value or credentials(name))
        return path

    def active(self, name="a", value=None):
        self.write_account(name)
        self.auth.write_text(value or credentials(name))
        self.marker.write_text(name + "\n")

    def run_switch(self, *args, command=COMMAND):
        result = subprocess.run([str(command), *args], env=self.env,
                                capture_output=True, text=True, timeout=15)
        self.assertNotIn("fake-access-", result.stdout + result.stderr)
        self.assertNotIn("fake-refresh-", result.stdout + result.stderr)
        if self.log.exists():
            self.assertNotIn("FORBIDDEN", self.log.read_text())
            self.assertNotIn("logout", self.log.read_text())
        return result

    def snapshot(self):
        return {str(path.relative_to(self.codex_home)): path.read_bytes()
                for path in self.codex_home.rglob("*") if path.is_file()}

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_help_status_and_invalid_arguments_do_not_create_state(self):
        for args in [(), ("--help",), ("../bad",), ("a", "--unknown"),
                     ("a", "--relogin", "extra"), ("--relogin",), ("",)]:
            result = self.run_switch(*args)
            self.assertEqual(result.returncode, 0 if args in [(), ("--help",)] else 2)
            self.assertFalse(self.codex_home.exists())
            self.assertFalse(self.log.exists())

    def test_status_describes_slots_without_writes_or_clients(self):
        self.active("a")
        self.write_account("b")
        before = self.snapshot()
        result = self.run_switch()
        self.assert_success(result)
        self.assertIn("current: a (a@example.test, plan=test)", result.stdout)
        self.assertIn("b@example.test", result.stdout)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.log.exists())

    def test_round_trip_saves_rotated_tokens_and_private_permissions(self):
        rotated = credentials("a-rotated")
        self.active("a", rotated)
        self.write_account("b")
        self.assert_success(self.run_switch("b"))
        self.assertEqual((self.accounts / "a.json").read_text(), rotated)
        self.assertEqual(self.auth.read_text(), credentials("b"))
        self.assert_success(self.run_switch("a"))
        self.assertEqual(self.auth.read_text(), rotated)
        self.assertEqual(self.marker.read_text(), "a\n")
        self.assertNotIn("codex ", self.log.read_text())
        self.assertEqual(stat.S_IMODE(self.accounts.stat().st_mode), 0o700)
        for path in [self.auth, self.marker, self.accounts / "a.json", self.accounts / "b.json"]:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertFalse((self.accounts / ".switch.lock").exists())

    def test_first_login_uses_file_backend_and_saves_slot(self):
        self.assert_success(self.run_switch("a"))
        self.assertEqual(self.auth.read_text(), self.fixture.read_text())
        self.assertEqual((self.accounts / "a.json").read_text(), self.fixture.read_text())
        self.assertEqual(self.marker.read_text(), "a\n")
        self.assertIn('codex -c cli_auth_credentials_store="file" login', self.log.read_text())

    def test_switch_to_new_account_keeps_current_rotated_tokens(self):
        self.active("a", credentials("rotated"))
        self.assert_success(self.run_switch("b"))
        self.assertEqual((self.accounts / "a.json").read_text(), credentials("rotated"))
        self.assertEqual((self.accounts / "b.json").read_text(), self.fixture.read_text())

    def test_login_failure_restores_unlabelled_existing_auth(self):
        self.codex_home.mkdir()
        self.auth.write_text(credentials("unlabelled"))
        before = self.snapshot()
        self.env["SWITCH_TEST_LOGIN_STATUS"] = "1"
        result = self.run_switch("a")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_failed_first_login_leaves_no_credentials_or_marker(self):
        self.env["SWITCH_TEST_LOGIN_STATUS"] = "1"
        result = self.run_switch("a")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.auth.exists())
        self.assertEqual(list(self.accounts.iterdir()), [])

    def test_relogin_failure_and_invalid_output_restore_all_files(self):
        self.active("a", credentials("rotated"))
        self.write_account("b")
        before = self.snapshot()
        for slot in ("a", "b"):
            for status, fixture in [("1", credentials("failed")), ("0", "{}\n"),
                                    ("0", "not json\n")]:
                self.env["SWITCH_TEST_LOGIN_STATUS"] = status
                self.fixture.write_text(fixture)
                result = self.run_switch(slot, "--relogin")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.snapshot(), before)

    def test_interrupted_relogin_restores_auth_slot_and_marker(self):
        self.active("a", credentials("rotated"))
        before = self.snapshot()
        self.env["SWITCH_TEST_SIGNAL"] = "TERM"
        result = self.run_switch("a", "--relogin")
        self.assertEqual(result.returncode, 128 + signal.SIGTERM)
        self.assertEqual(self.snapshot(), before)

    def test_relogin_success_replaces_active_and_saved_credentials(self):
        self.active("a")
        self.assert_success(self.run_switch("a", "--relogin"))
        self.assertEqual(self.auth.read_text(), self.fixture.read_text())
        self.assertEqual((self.accounts / "a.json").read_text(), self.fixture.read_text())

    def test_running_clients_refuse_without_changes(self):
        self.active("a")
        self.write_account("b")
        before = self.snapshot()
        self.env["SWITCH_TEST_CLIENT_STATUS"] = "0"
        result = self.run_switch("b")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("close Codex/ChatGPT", result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("codex ", self.log.read_text())

    def test_failed_process_check_refuses_without_changes(self):
        self.active("a")
        self.write_account("b")
        before = self.snapshot()
        self.env["SWITCH_TEST_CLIENT_STATUS"] = "2"
        result = self.run_switch("b")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not check running clients", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_switch_rechecks_active_slot_after_acquiring_lock(self):
        self.active("a")
        self.write_account("b")
        self.write_account("c")
        self.fixture.write_text(credentials("b-rotated"))
        self.env["SWITCH_TEST_PRIOR_SWITCH"] = str(self.base / "prior-switch-done")
        self.assert_success(self.run_switch("c"))
        self.assertEqual((self.accounts / "a.json").read_text(), credentials("a"))
        self.assertEqual((self.accounts / "b.json").read_text(), credentials("b-rotated"))
        self.assertEqual(self.auth.read_text(), credentials("c"))
        self.assertEqual(self.marker.read_text(), "c\n")

    def test_invalid_saved_auth_or_marker_refuse_without_changes(self):
        self.active("a")
        self.write_account("b", "{}\n")
        before = self.snapshot()
        self.assertNotEqual(self.run_switch("b").returncode, 0)
        self.assertEqual(self.snapshot(), before)
        self.marker.write_text("../outside\n")
        before = self.snapshot()
        self.assertNotEqual(self.run_switch("b", "--relogin").returncode, 0)
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("codex ", self.log.read_text())

    def test_same_slot_is_read_only_but_missing_auth_can_be_restored(self):
        self.active("a")
        before = self.snapshot()
        self.assert_success(self.run_switch("a"))
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("codex ", self.log.read_text())
        self.auth.unlink()
        self.assert_success(self.run_switch("a"))
        self.assertEqual(self.auth.read_text(), credentials("a"))

    def test_custom_codex_home_workspace_and_symlink_invocation(self):
        self.codex_home = self.base / "custom codex home"
        self.env["CODEX_HOME"] = str(self.codex_home)
        self.accounts.mkdir(parents=True)
        (self.accounts / "a.workspace").write_text("workspace-id\n")
        link = self.bindir / "codex-switch"
        link.symlink_to(COMMAND)
        self.assert_success(self.run_switch("a", command=link))
        self.assertTrue((self.accounts / "a.json").is_file())
        self.assertFalse((self.home / ".codex").exists())
        self.assertIn('-c forced_chatgpt_workspace_id="workspace-id"', self.log.read_text())

    def test_symlinked_auth_and_concurrent_switch_do_not_overwrite_files(self):
        self.active("a")
        self.write_account("b")
        outside = self.base / "outside.json"
        outside.write_text(credentials("outside"))
        self.auth.unlink()
        self.auth.symlink_to(outside)
        self.assertNotEqual(self.run_switch("b").returncode, 0)
        self.assertTrue(self.auth.is_symlink())
        self.assertEqual(outside.read_text(), credentials("outside"))
        self.auth.unlink()
        self.auth.write_text(credentials("a"))
        (self.accounts / ".switch.lock").mkdir()
        before = self.snapshot()
        self.assertNotEqual(self.run_switch("b").returncode, 0)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue((self.accounts / ".switch.lock").exists())


if __name__ == "__main__":
    unittest.main()
