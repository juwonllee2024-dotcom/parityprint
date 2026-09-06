# Verification record

Status: local release candidate; remote commit, CI, and release identity are
filled after publication.

## TDD

- RED: tests were written first and failed with
  `ModuleNotFoundError: No module named 'parityprint'`.
- GREEN: snapshot privacy, dotenv parsing, atomic round-trip, schema rejection,
  match, drift, and CLI flows pass after implementation.

## Fresh commands

```text
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
mypy
python -m compileall -q src tests
python -m build
pip-audit --local
git diff --check
```

## Real input

```text
parityprint snapshot examples/parity.json --env-file examples/.env.example --json
parityprint check examples/parity.json --json
```

Expected behavior: snapshot contains key states only; changing a secret value
without changing its `set` state remains a match, while missing/empty state or
Python/platform identity drift returns status `drift` and exit code `1`.

## Security evidence

Local static scans check for shell execution, process control, network clients,
sockets, and common secret assignments. A dedicated protected security scan is
recorded as unavailable if the connector is not exposed; unavailable is never
reported as a successful scan.

## Release identity

- Commit: recorded after all checks pass.
- CI: recorded after public push and matrix success.
- Release: recorded after `v0.1.0` is published.
- Package SHA-256: recorded from exact release assets.
