import json
import tempfile
import unittest
from pathlib import Path

from parityprint.core import (
    SnapshotError,
    build_snapshot,
    compare_snapshot,
    parse_env_keys,
    read_snapshot,
    write_snapshot,
)


class CoreTests(unittest.TestCase):
    def test_parse_env_keys_ignores_values_and_comments(self) -> None:
        keys = parse_env_keys(
            "# public contract\nexport API_URL=https://example.test\nTOKEN=secret\nEMPTY\n"
        )
        self.assertEqual(keys, ["API_URL", "EMPTY", "TOKEN"])

    def test_snapshot_stores_states_but_never_values(self) -> None:
        snapshot = build_snapshot(
            {"API_TOKEN": "super-secret-value", "EMPTY": ""},
            tracked_keys=["API_TOKEN", "EMPTY", "MISSING"],
            platform_name="test-os",
            python_version="3.13.0",
        )

        encoded = json.dumps(snapshot, sort_keys=True)
        self.assertNotIn("super-secret-value", encoded)
        self.assertEqual(
            snapshot["environment"],
            {"API_TOKEN": "set", "EMPTY": "empty", "MISSING": "missing"},
        )
        self.assertEqual(
            snapshot["identity"], {"platform": "test-os", "python": "3.13.0"}
        )

    def test_compare_reports_drift_without_revealing_values(self) -> None:
        snapshot = build_snapshot(
            {"API_TOKEN": "old-secret", "PORT": "3000"},
            tracked_keys=["API_TOKEN", "PORT"],
            platform_name="windows",
            python_version="3.13.0",
        )

        result = compare_snapshot(
            snapshot,
            {"API_TOKEN": "new-secret", "PORT": ""},
            platform_name="linux",
            python_version="3.12.0",
        )

        self.assertEqual(result["status"], "drift")
        self.assertEqual(
            result["changes"],
            [{"key": "PORT", "before": "set", "now": "empty"}],
        )
        self.assertEqual(
            result["identity_changes"],
            {
                "platform": {"before": "windows", "now": "linux"},
                "python": {"before": "3.13.0", "now": "3.12.0"},
            },
        )
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("old-secret", encoded)
        self.assertNotIn("new-secret", encoded)

    def test_snapshot_round_trip_is_atomic_json(self) -> None:
        snapshot = build_snapshot(
            {"MODE": "test"},
            tracked_keys=["MODE"],
            platform_name="test-os",
            python_version="3.13.0",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "parity.json"
            write_snapshot(path, snapshot)
            self.assertEqual(read_snapshot(path), snapshot)
            self.assertFalse((path.parent / ".parity.json.tmp").exists())

    def test_malformed_snapshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema": 99}', encoding="utf-8")
            with self.assertRaises(SnapshotError):
                read_snapshot(path)


if __name__ == "__main__":
    unittest.main()
