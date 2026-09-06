# ParityPrint example

This example uses `.env.example` as a public key contract. The file contains
placeholder names only.

```bash
parityprint snapshot parity.json --env-file .env.example --json
parityprint check parity.json --json
```

The generated `parity.json` is intentionally ignored by the repository. If you
choose to commit a snapshot in your own project, inspect variable names first.
