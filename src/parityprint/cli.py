"""Command-line interface for ParityPrint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .core import (
    SnapshotError,
    build_snapshot,
    compare_snapshot,
    parse_env_keys,
    read_snapshot,
    write_snapshot,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parityprint",
        description="Prove environment parity without recording secret values.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    snapshot = commands.add_parser(
        "snapshot", help="capture environment shape into a local JSON file"
    )
    snapshot.add_argument("output", type=Path, help="snapshot JSON destination")
    snapshot.add_argument(
        "--env-file",
        type=Path,
        help="dotenv-like file whose key names define the tracked contract",
    )
    snapshot.add_argument(
        "--key",
        action="append",
        default=[],
        metavar="NAME",
        help="track one environment key; repeat for multiple keys",
    )
    snapshot.add_argument(
        "--json", action="store_true", help="print a machine-readable summary"
    )

    check = commands.add_parser(
        "check", help="compare current environment to a snapshot"
    )
    check.add_argument("snapshot", type=Path, help="snapshot JSON to compare")
    check.add_argument("--json", action="store_true", help="print JSON results")
    return parser


def _read_declared(path: Path | None) -> list[str]:
    if path is None:
        return []
    try:
        return parse_env_keys(path.expanduser().read_text(encoding="utf-8"))
    except OSError as exc:
        raise SnapshotError(f"could not read env file: {path}") from exc


def _snapshot_command(args: argparse.Namespace) -> int:
    declared = _read_declared(args.env_file)
    tracked = set(args.key)
    if args.env_file is None and not tracked:
        tracked.update(os.environ)
    tracked.update(declared)
    snapshot = build_snapshot(
        os.environ,
        tracked_keys=tracked,
        declared_keys=declared,
    )
    write_snapshot(args.output, snapshot)
    summary = {
        "status": "captured",
        "snapshot": str(args.output.expanduser().resolve()),
        "tracked_keys": len(snapshot["environment"]),
        "declared_keys": len(snapshot["declared_keys"]),
        "values_stored": False,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print("ParityPrint snapshot captured.")
        print(f"Tracked keys: {summary['tracked_keys']}")
        print(f"Declared contract keys: {summary['declared_keys']}")
        print("Values stored: no")
    return 0


def _check_command(args: argparse.Namespace) -> int:
    snapshot = read_snapshot(args.snapshot)
    result = compare_snapshot(snapshot, os.environ)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["status"] == "match":
        tracked_keys = result["tracked_keys"]
        print(f"PARITY MATCH ({tracked_keys} tracked keys; values never compared)")
    else:
        print(f"PARITY DRIFT ({result['tracked_keys']} tracked keys)")
        for change in result["changes"]:
            print(f"- {change['key']}: {change['before']} -> {change['now']}")
        for field, identity_change in result["identity_changes"].items():
            before = identity_change["before"]
            now = identity_change["now"]
            print(f"- {field}: {before} -> {now}")
    return 0 if result["status"] == "match" else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            return _snapshot_command(args)
        if args.command == "check":
            return _check_command(args)
    except (OSError, SnapshotError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2
