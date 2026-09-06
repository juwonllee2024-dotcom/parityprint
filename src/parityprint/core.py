"""Privacy-preserving environment shape snapshots and comparisons."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Literal, TypedDict, cast

SCHEMA_VERSION = 1
EnvironmentState = Literal["set", "empty", "missing"]
_ENVIRONMENT_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SnapshotError(ValueError):
    """Raised when a snapshot or its inputs cannot be trusted."""


class Identity(TypedDict):
    platform: str
    python: str


class Snapshot(TypedDict):
    schema: int
    identity: Identity
    declared_keys: list[str]
    environment: dict[str, EnvironmentState]


class StateChange(TypedDict):
    key: str
    before: EnvironmentState
    now: EnvironmentState


class IdentityChange(TypedDict):
    before: str
    now: str


class CompareResult(TypedDict):
    status: Literal["match", "drift"]
    changes: list[StateChange]
    identity_changes: dict[str, IdentityChange]
    tracked_keys: int


def normalize_platform(value: str | None = None) -> str:
    """Return a small, stable platform label without host-specific details."""

    raw = (value or sys.platform).lower()
    if raw.startswith("win"):
        return "windows"
    if raw == "darwin" or raw.startswith("mac"):
        return "macos"
    if raw.startswith("linux"):
        return "linux"
    if raw.startswith("freebsd"):
        return "freebsd"
    return raw or "unknown"


def runtime_version(value: str | None = None) -> str:
    """Return only the Python major/minor/patch version."""

    if value is not None:
        return value
    info = sys.version_info
    return f"{info.major}.{info.minor}.{info.micro}"


def parse_env_keys(text: str) -> list[str]:
    """Parse dotenv-like key declarations without reading or returning values."""

    keys: set[str] = set()
    for line_number, raw_line in enumerate(text.lstrip("\ufeff").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key = line.split("=", 1)[0].strip()
        if not _ENVIRONMENT_KEY.fullmatch(key):
            raise SnapshotError(f"invalid environment key on line {line_number}: {key}")
        keys.add(key)
    return sorted(keys)


def _environment_state(environment: Mapping[str, str], key: str) -> EnvironmentState:
    if key not in environment:
        return "missing"
    return "empty" if environment[key] == "" else "set"


def build_snapshot(
    environment: Mapping[str, str],
    *,
    tracked_keys: Iterable[str] | None = None,
    declared_keys: Iterable[str] | None = None,
    platform_name: str | None = None,
    python_version: str | None = None,
) -> Snapshot:
    """Build a snapshot containing states and identity, never environment values."""

    declared = set(declared_keys or ())
    selected = set(tracked_keys) if tracked_keys is not None else set(environment)
    selected.update(declared)
    selected = {key for key in selected if key}
    if not selected:
        raise SnapshotError("no environment keys selected")
    invalid = sorted(key for key in selected if not _ENVIRONMENT_KEY.fullmatch(key))
    if invalid:
        raise SnapshotError("invalid environment key: " + ", ".join(invalid))
    declared = {key for key in declared if key in selected}
    return {
        "schema": SCHEMA_VERSION,
        "identity": {
            "platform": normalize_platform(platform_name),
            "python": runtime_version(python_version),
        },
        "declared_keys": sorted(declared),
        "environment": {
            key: _environment_state(environment, key) for key in sorted(selected)
        },
    }


def _validate_snapshot(value: object) -> Snapshot:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA_VERSION:
        raise SnapshotError(f"unsupported snapshot schema; expected {SCHEMA_VERSION}")

    identity = value.get("identity")
    if not isinstance(identity, dict):
        raise SnapshotError("snapshot identity is missing")
    platform_name = identity.get("platform")
    python_version = identity.get("python")
    if not isinstance(platform_name, str) or not isinstance(python_version, str):
        raise SnapshotError("snapshot identity is malformed")

    declared = value.get("declared_keys")
    if not isinstance(declared, list) or not all(
        isinstance(key, str) and _ENVIRONMENT_KEY.fullmatch(key) for key in declared
    ):
        raise SnapshotError("snapshot declared_keys is malformed")

    environment = value.get("environment")
    allowed_states = {"set", "empty", "missing"}
    if not isinstance(environment, dict):
        raise SnapshotError("snapshot environment is missing")
    if any(
        not isinstance(key, str)
        or not _ENVIRONMENT_KEY.fullmatch(key)
        or state not in allowed_states
        for key, state in environment.items()
    ):
        raise SnapshotError("snapshot environment contains an invalid key or state")
    if not environment:
        raise SnapshotError("snapshot tracks no environment keys")

    return {
        "schema": SCHEMA_VERSION,
        "identity": {"platform": platform_name, "python": python_version},
        "declared_keys": list(declared),
        "environment": cast(dict[str, EnvironmentState], dict(environment)),
    }


def write_snapshot(path: str | Path, snapshot: Snapshot) -> None:
    """Write snapshot atomically, leaving no temporary file after success."""

    validated = _validate_snapshot(snapshot)
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(validated, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def read_snapshot(path: str | Path) -> Snapshot:
    """Read and validate a snapshot before it participates in a comparison."""

    source = Path(path).expanduser().resolve()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"could not read snapshot: {source}") from exc
    return _validate_snapshot(raw)


def compare_snapshot(
    snapshot: Snapshot,
    environment: Mapping[str, str],
    *,
    platform_name: str | None = None,
    python_version: str | None = None,
) -> CompareResult:
    """Compare tracked states and coarse runtime identity without exposing values."""

    validated = _validate_snapshot(snapshot)
    current_identity = {
        "platform": normalize_platform(platform_name),
        "python": runtime_version(python_version),
    }
    identity_changes: dict[str, IdentityChange] = {}
    for field in ("platform", "python"):
        before = validated["identity"][field]
        now = current_identity[field]
        if before != now:
            identity_changes[field] = {"before": before, "now": now}

    changes: list[StateChange] = []
    for key, before in validated["environment"].items():
        now = _environment_state(environment, key)
        if before != now:
            changes.append({"key": key, "before": before, "now": now})

    return {
        "status": "match" if not changes and not identity_changes else "drift",
        "changes": changes,
        "identity_changes": identity_changes,
        "tracked_keys": len(validated["environment"]),
    }
