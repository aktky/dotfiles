#!/usr/bin/env python3
"""claude-sweep tests: temporary homes, real Git, stubbed lsof and launchctl."""
import datetime
import json
import os
import pathlib
import plistlib
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ACCOUNT = "5e078d4f-ac78-450c-88ce-3c3b4ffe868b"
ORG = "1c20df27-319e-4b33-a547-15f3bee1d852"
LABEL = "local.claude.sweep"


def encode(path):
    return "".join(c if c.isalnum() else "-" for c in str(path))


class ClaudeSweepTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-sweep-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name).resolve()
        self.repo = self.base / "repo with spaces"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.target = self.base / "target home"
        self.target.mkdir()
        self.tmp_root = self.base / "tmp root"
        self.tmp_root.mkdir()
        self.app = self.target / "Library/Application Support/Claude/claude-code-sessions" / ACCOUNT / ORG
        self.app.mkdir(parents=True)
        self.bindir = self.base / "bin"
        self.bindir.mkdir()
        self.log = self.base / "calls"
        (self.bindir / "launchctl").write_text(
            '#!/bin/bash\necho "launchctl $*" >> "$DOTFILES_TEST_LOG"\n'
            '[[ "$1" != print ]] || [[ -n "${TEST_LOADED:-}" ]]\n')
        # Reports the file in TEST_OPEN as held open by a process.
        (self.bindir / "lsof").write_text(
            '#!/bin/bash\n[[ -n "${TEST_OPEN:-}" && "${!#}" == "$TEST_OPEN" ]] && echo 123\n')
        for stub in self.bindir.iterdir():
            stub.chmod(0o755)
        gitconfig = self.base / "gitconfig"
        gitconfig.write_text("[init]\n\tdefaultBranch = master\n")
        self.env = dict(os.environ, PATH=str(self.bindir) + os.pathsep + os.environ["PATH"],
                        DOTFILES_TEST_LOG=str(self.log), HOME=str(self.target),
                        CLAUDE_SWEEP_TMP_ROOT=str(self.tmp_root), CLAUDE_SWEEP_RETRIES="0",
                        GIT_CONFIG_GLOBAL=str(gitconfig), GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        self.today = datetime.date.today().isoformat()
        self.trash = self.target / ".local/state/claude-sweep/trash"

    # --- helpers --------------------------------------------------------------

    def sweep(self, *args, **env):
        return subprocess.run([str(self.repo / "scripts/claude-sweep"), *args,
                               "--target-home", str(self.target)],
                              env=dict(self.env, **env), text=True, capture_output=True)

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], env=self.env, text=True,
                              capture_output=True, check=True).stdout.strip()

    def session(self, cli_id, cwd):
        """Everything a desktop session leaves behind; returns the paths."""
        enc = encode(cwd)
        project = self.target / ".claude/projects" / enc
        project.mkdir(parents=True, exist_ok=True)
        transcript = project / f"{cli_id}.jsonl"
        transcript.write_text(json.dumps({"type": "user", "cwd": str(cwd)}) + "\nnot json\n"
                              + json.dumps({"type": "image", "data": "aGk="}) + "\n")
        paths = [transcript, project / cli_id / "tool-results/out.txt",
                 self.tmp_root / enc / cli_id / "scratch.txt",
                 self.tmp_root / f"cache-break-state-{cli_id}.json",
                 self.target / ".claude/file-history" / cli_id / "v1",
                 self.target / ".claude/session-env" / cli_id / "env"]
        for path in paths[1:]:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x")
        return paths

    def delete_in_app(self, cli_id, local_id=None, age=120):
        stamp = str(int((time.time() - age) * 1000))
        for marker_id in filter(None, (cli_id, local_id)):
            (self.app / f"deleted_{marker_id}").write_text(stamp)

    def record(self, local_id, cli_id, **extra):
        data = dict(sessionId="local_" + local_id, cliSessionId=cli_id,
                    priorCliSessionIds=None, isArchived=False)
        data.update(extra)
        (self.app / f"local_{local_id}.json").write_text(json.dumps(data))

    def project(self):
        repo = self.base / "project"
        repo.mkdir()
        self.git(repo, "init", "-q")
        (repo / "README").write_text("hi\n")
        self.git(repo, "add", "README")
        self.git(repo, "commit", "-qm", "init")
        return repo

    def worktree(self, repo, name, detach=False):
        path = repo / ".claude/worktrees" / name
        self.git(repo, "worktree", "add", "-q", "-b", f"claude/{name}", str(path))
        if detach:
            self.git(path, "checkout", "-q", "--detach")
        return path

    def branches(self, repo):
        return self.git(repo, "branch", "--format=%(refname:short)").splitlines()

    def ledger(self):
        path = self.target / ".local/state/claude-sweep/done"
        return [line.split("\t")[0] for line in path.read_text().splitlines()] if path.exists() else []

    # --- sweeping -------------------------------------------------------------

    def test_preview_lists_and_changes_nothing(self):
        cli = "11111111-1111-4111-8111-111111111111"
        paths = self.session(cli, self.base / "somewhere")
        self.delete_in_app(cli, "aaaaaaaa-1111-4111-8111-111111111111")
        result = self.sweep()
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in paths:
            self.assertTrue(path.exists())
        self.assertIn(f"TRASH {cli}: {paths[0]}", result.stdout)
        self.assertIn("1 deleted session(s) have nothing left", result.stdout)
        self.assertIn("Preview only", result.stdout)
        self.assertFalse((self.target / ".local").exists())
        self.assertFalse((self.target / "Library/Logs").exists())

    def test_apply_moves_to_trash_once(self):
        cli = "22222222-2222-4222-8222-222222222222"
        paths = self.session(cli, self.base / "somewhere")
        self.delete_in_app(cli)
        result = self.sweep("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in paths:
            self.assertFalse(path.exists(), path)
        kept = self.trash / self.today / cli
        self.assertTrue((kept / "home" / paths[0].relative_to(self.target)).is_file())
        self.assertTrue((kept / "tmp" / paths[2].relative_to(self.tmp_root)).is_file())
        self.assertFalse(paths[0].parent.exists())  # Empty project folder removed.
        self.assertEqual(self.ledger(), [cli])
        self.assertIn("DONE " + cli, (self.target / "Library/Logs/claude-sweep.log").read_text())
        # Ledger: the ID is never processed again, even if a file reappears.
        paths[3].write_text("new")
        result = self.sweep("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(cli, result.stdout)
        self.assertTrue(paths[3].exists())
        self.assertEqual(self.ledger(), [cli])

    def test_recorded_sessions_are_untouched(self):
        archived = "33333333-3333-4333-8333-333333333333"
        prior = "44444444-4444-4444-8444-444444444444"
        paths = self.session(archived, self.base / "a") + self.session(prior, self.base / "b")
        self.record("bbbbbbbb-3333-4333-8333-333333333333", archived, isArchived=True)
        self.record("cccccccc-3333-4333-8333-333333333333", "55555555-5555-4555-8555-555555555555",
                    priorCliSessionIds=[prior])
        self.delete_in_app(archived)
        self.delete_in_app(prior)
        result = self.sweep()
        self.assertIn(f"KEEP {archived}", result.stdout)
        self.assertIn(f"KEEP {prior}", result.stdout)
        result = self.sweep("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in paths:
            self.assertTrue(path.exists(), path)
        self.assertEqual(self.ledger(), [])

    def test_busy_session_waits(self):
        cli = "66666666-6666-4666-8666-666666666666"
        paths = self.session(cli, self.base / "somewhere")
        self.delete_in_app(cli, age=0)
        result = self.sweep("--apply")
        self.assertIn(f"WAIT {cli}: deleted", result.stdout)
        result = self.sweep("--apply", CLAUDE_SWEEP_MIN_AGE="0", TEST_OPEN=str(paths[0]))
        self.assertIn(f"WAIT {cli}: transcript still open", result.stdout)
        for path in paths:
            self.assertTrue(path.exists(), path)
        self.assertEqual(self.ledger(), [])
        result = self.sweep("--apply", CLAUDE_SWEEP_MIN_AGE="0")
        self.assertEqual(self.ledger(), [cli], result.stdout)

    def test_unreadable_record_stops_the_run(self):
        cli = "77777777-7777-4777-8777-777777777777"
        paths = self.session(cli, self.base / "somewhere")
        self.delete_in_app(cli)
        (self.app / "local_dddddddd-7777-4777-8777-777777777777.json").write_text("{half")
        result = self.sweep("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(paths[0].exists())

    def test_clean_worktree_is_removed_with_branch(self):
        repo = self.project()
        for detach in (True, False):
            with self.subTest(detach=detach):
                name = "detached" if detach else "attached"
                cli = ("88888888-8888-4888-8888-88888888888" + ("1" if detach else "2"))
                path = self.worktree(repo, name, detach=detach)
                self.session(cli, path / "sub dir")
                self.delete_in_app(cli)
                result = self.sweep("--apply")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"REMOVE {cli}: worktree {path} and branch claude/{name}", result.stdout)
                self.assertFalse(path.exists())
                self.assertNotIn(f"claude/{name}", self.branches(repo))
                self.assertEqual(self.git(repo, "worktree", "list", "--porcelain").count("worktree "), 1)
                kept = self.trash / self.today / cli
                self.assertTrue((kept / ("other" + str(path))).is_dir())
                self.assertTrue((kept / "git-worktrees" / name).is_dir())
                self.assertEqual((repo / "README").read_text(), "hi\n")

    def test_dirty_worktree_is_held(self):
        repo = self.project()
        path = self.worktree(repo, "dirty", detach=True)
        (path / "notes.txt").write_text("unsaved")
        cli = "99999999-9999-4999-8999-999999999999"
        paths = self.session(cli, path)
        self.delete_in_app(cli)
        result = self.sweep("--apply")
        self.assertIn(f"HOLD {cli}: {path} has uncommitted or untracked changes", result.stdout)
        self.assertTrue((path / "notes.txt").exists())
        self.assertIn("claude/dirty", self.branches(repo))
        for p in paths:
            self.assertTrue(p.exists(), p)
        self.assertEqual(self.ledger(), [])
        doctor = self.sweep("doctor")
        self.assertIn(f"HOLD {cli}", doctor.stdout)

    def test_branch_with_unique_commits_is_held(self):
        repo = self.project()
        for detach in (False, True):
            with self.subTest(detach=detach):
                name = "work-detached" if detach else "work"
                path = self.worktree(repo, name)
                (path / "feature").write_text(name + "\n")  # Distinct commits per subtest.
                self.git(path, "add", "feature")
                self.git(path, "commit", "-qm", "feature")
                if detach:
                    self.git(path, "checkout", "-q", "--detach")
                cli = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa" + ("1" if detach else "2")
                self.session(cli, path)
                self.delete_in_app(cli)
                result = self.sweep("--apply")
                self.assertIn(f"HOLD {cli}: claude/{name} in {path} has 1 commit(s)", result.stdout)
                self.assertTrue(path.exists())
                self.assertIn(f"claude/{name}", self.branches(repo))
        # Once the commit is reachable elsewhere (merged), the next run cleans up.
        self.git(repo, "merge", "-q", "--ff-only", "claude/work")
        result = self.sweep("--apply")
        self.assertIn("REMOVE aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2", result.stdout)
        self.assertNotIn("claude/work", self.branches(repo))

    def squashed_branch(self, name):
        """A pushed worktree branch that master took as a squash commit, with a
        master-only fetch refspec so the branch has no remote-tracking ref."""
        repo = self.project()
        remote = self.base / "remote.git"
        self.git(self.base, "init", "-q", "--bare", str(remote))
        self.git(repo, "remote", "add", "origin", str(remote))
        self.git(repo, "config", "remote.origin.fetch", "+refs/heads/master:refs/remotes/origin/master")
        self.git(repo, "push", "-q", "origin", "master")
        path = self.worktree(repo, name)
        (path / "feature").write_text(name + "\n")
        self.git(path, "add", "feature")
        self.git(path, "commit", "-qm", "feature")
        self.git(path, "push", "-q", "origin", f"claude/{name}")
        self.git(repo, "merge", "-q", "--squash", f"claude/{name}")
        self.git(repo, "commit", "-qm", "feature (#1)")
        self.git(repo, "push", "-q", "origin", "master")
        self.assertEqual(self.git(repo, "for-each-ref", "refs/remotes/origin/claude"), "")
        return repo, path

    def test_squash_merged_branch_on_remote_is_removed(self):
        repo, path = self.squashed_branch("squashed")
        tip = self.git(path, "rev-parse", "HEAD")
        self.git(path, "checkout", "-q", "--detach")  # As the app leaves it.
        cli = "cccccccc-cccc-4ccc-8ccc-ccccccccccc1"
        self.session(cli, path)
        self.delete_in_app(cli)
        result = self.sweep("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"REMOVE {cli}: worktree {path} and branch claude/squashed "
                      f"(was {tip}; tip matches origin/claude/squashed)", result.stdout)
        self.assertFalse(path.exists())
        self.assertNotIn("claude/squashed", self.branches(repo))
        self.assertEqual(self.ledger(), [cli])

    def test_branch_ahead_of_remote_is_held(self):
        repo, path = self.squashed_branch("ahead")
        (path / "more").write_text("more\n")
        self.git(path, "add", "more")
        self.git(path, "commit", "-qm", "more")
        cli = "cccccccc-cccc-4ccc-8ccc-ccccccccccc2"
        self.session(cli, path)
        self.delete_in_app(cli)
        result = self.sweep("--apply")
        self.assertIn(f"HOLD {cli}: claude/ahead in {path} has 2 commit(s)", result.stdout)
        self.assertIn("origin/claude/ahead is at ", result.stdout)
        self.assertTrue(path.exists())
        self.assertIn("claude/ahead", self.branches(repo))
        self.assertEqual(self.ledger(), [])

    def test_unreachable_remote_holds(self):
        repo, path = self.squashed_branch("offline")
        cli = "cccccccc-cccc-4ccc-8ccc-ccccccccccc3"
        self.session(cli, path)
        self.delete_in_app(cli)
        for url, env in ((str(self.base / "gone.git"), {}),
                         # Hangs like a dead network; the timeout must cut it off.
                         ("example.invalid:repo.git", dict(GIT_SSH_COMMAND="sleep 5",
                                                           CLAUDE_SWEEP_REMOTE_TIMEOUT="1"))):
            with self.subTest(url=url):
                self.git(repo, "remote", "set-url", "origin", url)
                started = time.monotonic()
                result = self.sweep("--apply", **env)
                self.assertLess(time.monotonic() - started, 4)
                self.assertIn(f"HOLD {cli}: claude/offline in {path} has 1 commit(s)", result.stdout)
                self.assertIn("cannot reach origin", result.stdout)
                self.assertTrue(path.exists())
                self.assertIn("claude/offline", self.branches(repo))
        self.assertEqual(self.ledger(), [])

    def test_worktree_used_by_another_session_is_held(self):
        repo = self.project()
        path = self.worktree(repo, "shared")
        cli = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        self.session(cli, path)
        self.delete_in_app(cli)
        self.record("eeeeeeee-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "cccccccc-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                    worktreePath=str(path), cwd=str(path))
        result = self.sweep("--apply")
        self.assertIn(f"HOLD {cli}: {path} is still used by another session", result.stdout)
        self.assertTrue(path.exists())

    def test_trash_retention(self):
        old = self.trash / "2000-01-01/x"
        new = self.trash / self.today / "y"
        for path in (old, new):
            path.mkdir(parents=True)
        result = self.sweep()
        self.assertIn("PURGE trash/2000-01-01", result.stdout)
        self.assertTrue(old.exists())
        result = self.sweep("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(old.parent.exists())
        self.assertTrue(new.exists())

    # --- LaunchAgent ----------------------------------------------------------

    def plist(self):
        return self.target / "Library/LaunchAgents" / f"{LABEL}.plist"

    def test_install_doctor_uninstall(self):
        result = self.sweep("install")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.plist().exists())
        self.assertFalse(self.log.exists())
        for _ in range(2):
            result = self.sweep("install", "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
        text = self.plist().read_text()
        self.assertIn(f"<string>{self.app}</string>", text)
        self.assertIn(f"<string>{self.repo}/scripts/claude-sweep</string>", text)
        self.assertIn("<string>--quiet</string>", text)
        self.assertNotIn("@", text.replace("<?xml", ""))
        # launchd refuses a file that is not a single well-formed plist.
        parsed = plistlib.loads(text.encode())
        self.assertEqual(parsed["WatchPaths"], [str(self.app)])
        self.assertEqual(parsed["Label"], LABEL)
        self.assertEqual(self.log.read_text().count("launchctl bootstrap"), 2)
        result = self.sweep("doctor", TEST_LOADED="1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("No held-back sessions", result.stdout)
        # A new account/org folder is not watched until reinstalled.
        (self.app.parent / "fffffff0-0000-4000-8000-000000000000").mkdir()
        result = self.sweep("doctor", TEST_LOADED="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("UNWATCHED", result.stdout)
        result = self.sweep("install", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.plist().read_text(), text)
        result = self.sweep("uninstall", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.plist().exists())
        self.assertIn(f"launchctl bootout gui/{os.getuid()}/{LABEL}", self.log.read_text())

    def test_foreign_plist_is_never_overwritten_or_removed(self):
        self.plist().parent.mkdir(parents=True)
        self.plist().write_text("keep me")
        for command in ("install", "uninstall"):
            result = self.sweep(command, "--apply")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.plist().read_text(), "keep me")
        self.assertFalse(self.log.exists())

    def test_linked_command_finds_repo(self):
        link = self.base / "linked-claude-sweep"
        link.symlink_to(self.repo / "scripts/claude-sweep")
        result = subprocess.run([str(link), "--target-home", str(self.target)],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
