#!/usr/bin/env python3
"""llmctl tests: temporary homes and stubbed tools, never real installs or downloads."""
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class LlmctlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-llm-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name).resolve()
        self.repo = self.base / "repo with spaces"
        shutil.copytree(ROOT, self.repo, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.target = self.base / "target home"
        self.target.mkdir()
        self.bindir = self.base / "bin"
        self.bindir.mkdir()
        self.log = self.base / "calls"
        for name in ("hf", "brew", "launchctl", "tmutil", "llama-bench"):
            stub = self.bindir / name
            stub.write_text('#!/bin/bash\necho "%s $*" >> "$DOTFILES_TEST_LOG"\n' % name)
            stub.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bindir) + os.pathsep + os.defpath,
                        DOTFILES_TEST_LOG=str(self.log),
                        LLM_HOME=str(self.target / ".local/share/llm"))

    def llmctl(self, *args, home=True):
        extra = ["--links-only", "--target-home", str(self.target)] if home else []
        return subprocess.run([str(self.repo / "scripts/llmctl"), *args, *extra],
                              env=self.env, text=True, capture_output=True)

    def plist(self):
        return self.target / "Library/LaunchAgents/local.llm.llama-swap.plist"

    def test_install_preview_never_writes(self):
        result = self.llmctl("install")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertFalse(self.log.exists())

    def test_install_is_idempotent_and_diagnosable(self):
        for _ in range(2):
            result = self.llmctl("install", "--apply")
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.llmctl("doctor")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((self.target / ".config/llama-swap/config.yaml").resolve(),
                         self.repo / "config/llm/llama-swap.yaml")
        text = self.plist().read_text()
        self.assertIn(str(self.target) + "/.config/llama-swap/config.yaml", text)
        self.assertIn("127.0.0.1:8080", text)
        self.assertNotIn("@", text.replace("<?xml", ""))
        for sub in ("models", "hf", "bench"):
            self.assertTrue((self.target / ".local/share/llm" / sub).is_dir())
        self.assertFalse(self.log.exists())  # --links-only: no brew, no tmutil.
        linked = self.target / ".local/bin/llmctl"
        result = subprocess.run([str(linked), "--help"], env=self.env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_changed_launch_agent_blocks_install(self):
        self.plist().parent.mkdir(parents=True)
        self.plist().write_text("keep me")
        result = self.llmctl("install", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.plist().read_text(), "keep me")
        self.assertFalse((self.target / ".config").exists())

    def test_existing_config_blocks_install(self):
        conflict = self.target / ".config/llama-swap/config.yaml"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("keep me")
        result = self.llmctl("install", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(conflict.read_text(), "keep me")
        self.assertFalse(self.plist().exists())

    def test_doctor_reports_manifest_drift(self):
        self.assertEqual(self.llmctl("install", "--apply").returncode, 0)
        with open(self.repo / "config/llm/models.tsv", "a") as manifest:
            manifest.write("orphan\torg/repo\t*.gguf\t1\tgguf\n")
            manifest.write("odd\torg/odd\t*\t1\tsafetensors\n")
        yaml = self.repo / "config/llm/llama-swap.yaml"
        yaml.write_text(yaml.read_text() + "  stray-model:\n    cmd: echo\n")
        result = self.llmctl("doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NOT ROUTED: orphan", result.stdout)
        self.assertIn("BAD FORMAT: odd", result.stdout)
        self.assertIn("NOT IN MANIFEST: stray-model", result.stdout)
        # Nested keys such as capacities: or the routing block are not model IDs.
        self.assertNotIn("capacities", result.stdout)
        self.assertNotIn("routing", result.stdout)

    def test_shipped_manifest_and_routes_match(self):
        self.assertEqual(self.llmctl("install", "--apply").returncode, 0)
        result = self.llmctl("doctor")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("NOT ", result.stdout)

    def test_pull_previews_and_validates_names(self):
        result = self.llmctl("pull", home=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("qwen3.8-flash-next", result.stdout)
        self.assertFalse(self.log.exists())
        result = self.llmctl("pull", "--apply", "qwen3.8-27b", "unknown", home=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())
        result = self.llmctl("pull", "--apply", "qwen3.8-27b", home=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), [
            "hf download unsloth/Qwen3.8-27B-GGUF --include Qwen3.8-27B-UD-Q4_K_XL.gguf "
            "--local-dir " + str(self.target / ".local/share/llm/models/qwen3.8-27b")])
        self.log.unlink()
        result = self.llmctl("pull", "--apply", "gemma-4-26b-a4b", home=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.log.read_text().splitlines(), [
            "hf download mlx-community/gemma-4-26b-a4b-it-8bit --include * "
            "--local-dir " + str(self.target / ".local/share/llm/mlx/gemma-4-26b-a4b")])

    def test_bench_needs_download_and_previews(self):
        result = self.llmctl("bench", "qwen3.8-27b", home=False)
        self.assertNotEqual(result.returncode, 0)
        model = self.target / ".local/share/llm/models/qwen3.8-27b"
        model.mkdir(parents=True)
        (model / "mmproj-F16.gguf").write_text("")
        (model / "Qwen3.8-27B-UD-Q4_K_XL.gguf").write_text("")
        result = self.llmctl("bench", "qwen3.8-27b", home=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Qwen3.8-27B-UD-Q4_K_XL.gguf", result.stdout)
        (self.target / ".local/share/llm/mlx/gemma-4-26b-a4b").mkdir(parents=True)
        result = self.llmctl("bench", "--apply", "gemma-4-26b-a4b", home=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("MLX", result.stderr)
        self.assertFalse(self.log.exists())

    def tailscale_stub(self, serving):
        stub = self.bindir / "tailscale"
        status = "|-- / proxy http://127.0.0.1:8080" if serving else "No serve config"
        stub.write_text('#!/bin/bash\necho "tailscale $*" >> "$DOTFILES_TEST_LOG"\n'
                        '[[ "$1 $2" == "serve status" ]] && echo "%s"\ntrue\n' % status)
        stub.chmod(0o755)

    def test_server_profile_links_server_config_and_is_detected(self):
        result = self.llmctl("install", "--profile", "server", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.target / ".config/llama-swap/config.yaml").resolve(),
                         self.repo / "config/llm/llama-swap.server.yaml")
        result = self.llmctl("install")  # No --profile: keeps the installed one.
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PROFILE: server", result.stdout)
        result = self.llmctl("doctor")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PROFILE: server", result.stdout)

    def test_switching_profile_needs_explicit_relink(self):
        self.assertEqual(self.llmctl("install", "--apply").returncode, 0)
        result = self.llmctl("install", "--profile", "server", "--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.target / ".config/llama-swap/config.yaml").resolve(),
                         self.repo / "config/llm/llama-swap.yaml")
        self.assertEqual(self.llmctl("install", "--profile", "nope").returncode, 2)

    def test_doctor_reports_server_route_missing_from_manifest(self):
        self.assertEqual(self.llmctl("install", "--profile", "server", "--apply").returncode, 0)
        with open(self.repo / "config/llm/llama-swap.server.yaml", "a") as config:
            config.write("  ghost:\n    cmd: llama-server --model ${models}/ghost/x.gguf\n")
        result = self.llmctl("doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NOT IN MANIFEST: ghost is routed by llama-swap.server.yaml", result.stdout)

    def test_pull_without_names_follows_installed_profile(self):
        self.assertEqual(self.llmctl("install", "--profile", "server", "--apply").returncode, 0)
        env = dict(self.env, HOME=str(self.target))
        result = subprocess.run([str(self.repo / "scripts/llmctl"), "pull"], env=env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PULL qwen3.8-27b", result.stdout)
        self.assertNotIn("flash-next", result.stdout)

    def test_serve_requires_server_profile_and_previews(self):
        self.tailscale_stub(serving=False)
        env = dict(self.env, HOME=str(self.target))
        serve = lambda *a: subprocess.run([str(self.repo / "scripts/llmctl"), "serve", *a],
                                          env=env, text=True, capture_output=True)
        self.assertEqual(serve("--apply").returncode, 1)  # Not installed.
        self.assertEqual(self.llmctl("install", "--profile", "server", "--apply").returncode, 0)
        result = serve()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tailscale serve --bg --https=443 http://127.0.0.1:8080", result.stdout)
        self.assertFalse(self.log.exists())
        self.assertEqual(serve("--apply").returncode, 0)
        self.assertEqual(serve("--off", "--apply").returncode, 0)
        self.assertEqual(self.log.read_text().splitlines(), [
            "tailscale serve --bg --https=443 http://127.0.0.1:8080",
            "tailscale serve status",
            "tailscale serve --https=443 off",
            "tailscale serve status"])

    def test_package_check_includes_llm_brewfile_once_enabled(self):
        stub = self.base / "brew-stub"
        stub.write_text("""#!/bin/bash
printf '%s\\n' "$*" >> "$DOTFILES_TEST_LOG"
case "$1 $2" in
  'bundle check') exit 0 ;;
  'bundle list') case "$*" in *config/llm/Brewfile) [[ "$3" == --brews ]] && echo llama.cpp ;; *) [[ "$3" == --brews ]] && echo git ;; esac; true ;;
  'leaves ') printf 'git\\nllama.cpp\\n' ;;
  'list --cask') : ;;
  *) exit 90 ;;
esac
""")
        stub.chmod(0o755)
        command = ["/bin/bash", "-c", r'''source "$1"
target_home="$3"
test_brew="$2"
find_brew() { brew_bin="$test_brew"; }
status=0
strict=true
check_packages
exit "$status"
''', "test", str(self.repo / "scripts/common.sh"), str(stub), str(self.target)]
        result = subprocess.run(command, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("llama.cpp", result.stdout)
        self.assertEqual(self.llmctl("install", "--apply").returncode, 0)
        result = subprocess.run(command, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("install", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
