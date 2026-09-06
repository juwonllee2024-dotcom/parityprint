# Security policy

## Scope

ParityPrint is a local, read-only environment-shape reporter. Its core safety
promise is narrow: it stores selected variable names and state labels, never
their values.

The command does not use a shell, spawn a process, make a network request, read
hostnames or usernames, or install tools. It reads a dotenv-like file only to
parse key names when the user explicitly supplies `--env-file`.

## Important limitations

- Variable names can themselves reveal service or project information. Do not
  commit a snapshot if its names are confidential.
- A `set` label does not prove a value is correct, reachable, or safe.
- A snapshot is a comparison contract, not a secret manager or sandbox.
- A hostile hand-edited snapshot is untrusted input; ParityPrint validates its
  schema before comparing it.

## Reporting a vulnerability

Do not open a public issue for a secret or an exploitable security report. Use
GitHub's private vulnerability reporting for this repository when available.
If it is unavailable, contact the repository owner through GitHub with only a
minimal description and no credentials or private data.

## Safe contribution rules

Never add telemetry, network calls, subprocess execution, secret-value output,
or automatic mutation without a separate security review and explicit product
decision. New behavior must retain tests proving values are absent from output.
