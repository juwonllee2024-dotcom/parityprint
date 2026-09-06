import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_cli(
        self, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env is not None:
            merged_env.update(env)
        return subprocess.run(
            [sys.executable, "-m", "parityprint", *args],
            text=True,
            capture_output=True,
            env=merged_env,
            check=False,
        )

    def test_snapshot_and_check_json_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env_file = root / ".env.example"
            snapshot = root / "parity.json"
            env_file.write_text("API_URL=\nOPTIONAL=\n", encoding="utf-8")

            created = self.run_cli(
                "snapshot",
                str(snapshot),
                "--env-file",
                str(env_file),
                "--json",
                env={"API_URL": "https://example.test", "OPTIONAL": "enabled"},
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertEqual(json.loads(created.stdout)["tracked_keys"], 2)

            checked = self.run_cli(
                "check",
                str(snapshot),
                "--json",
                env={"API_URL": "https://example.test", "OPTIONAL": "enabled"},
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["status"], "match")

    def test_check_returns_one_for_drift_and_never_prints_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env_file = root / ".env.example"
            snapshot = root / "parity.json"
            env_file.write_text("API_TOKEN=\n", encoding="utf-8")
            created = self.run_cli(
                "snapshot",
                str(snapshot),
                "--env-file",
                str(env_file),
                env={"API_TOKEN": "original-secret"},
            )
            self.assertEqual(created.returncode, 0, created.stderr)

            checked = self.run_cli(
                "check",
                str(snapshot),
                "--json",
                env={"API_TOKEN": "different-secret"},
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            payload = json.loads(checked.stdout)
            self.assertEqual(payload["status"], "match")
            self.assertNotIn("secret", checked.stdout.lower())


if __name__ == "__main__":
    unittest.main()
