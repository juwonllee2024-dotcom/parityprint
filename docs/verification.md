# Verification record

Status: published v0.1.0. The package artifacts below were built from the
release target commit and checked locally before publication.

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

- Commit: `d16b539a6e59db9d61226fd256ff743dc3ab47ca`
- CI: [12-job matrix run](https://github.com/juwonllee2024-dotcom/parityprint/actions/runs/34049291774)
- Release: [v0.1.0](https://github.com/juwonllee2024-dotcom/parityprint/releases/tag/v0.1.0)
- Package SHA-256, computed from the exact uploaded assets:
  - `parityprint-0.1.0-py3-none-any.whl`: `59fab3c780217628ebc8f0d4670b4535c09498be2b6d4971b0a962e9823f863b`
  - `parityprint-0.1.0.tar.gz`: `63d87d05fe5c54ada51fa28089fb7c8ab32c64fdd8cae2b45760d758483dc4f1`
