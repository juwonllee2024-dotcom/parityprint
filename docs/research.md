# ParityPrint research note

Research date: 2026-09-06. This is a product hypothesis record, not proof of
market demand.

## Problem

Developers repeatedly encounter “works on my machine” failures caused by
differences that are invisible in the code: missing environment keys, empty
configuration, runtime versions, and machine-specific setup. A developer
onboarding discussion describes first-time setup taking almost a day because
of a wrong Node version, missing `.env` keys, and stale README instructions:
[developersIndia discussion](https://www.reddit.com/r/developersIndia/comments/1olvm3l/).
The pain is real, but this source is anecdotal and not a market-size estimate.

The current developer-tool signal also favors terminal-first workflows: a
recent CLI ecosystem report observed mature CLI tools sustaining attention
across multiple days and sources, while GitHub's own [Trending page](https://github.com/trending)
is the direct place to recheck current movement. This supports distribution
through a tiny CLI, not demand by itself.

## Existing substitutes and gap

- [mise](https://mise.en.dev/dev-tools/) manages and installs tool versions,
  activates them per project, and can manage environment setup.
- [Dev Container specification](https://containers.dev/implementors/json_reference/)
  models environment variables inside container lifecycles.
- [dotenvx](https://dotenvx.com/docs/quickstart/encryption/) encrypts `.env`
  values and injects them at runtime.
- Docker, Nix, lockfiles, and shell scripts can reproduce larger portions of a
  machine, but add setup or require sharing more configuration.

**Gap hypothesis:** a developer sometimes needs a 30-second, read-only answer
to “is the small configuration contract present here?” before adopting a
container, changing a version manager, or sharing any secret. Existing tools
solve enforcement or secret transport; ParityPrint tests shape only.

## Four independent innovation questions

Each candidate was scored 1–5 on pain, novelty, buildability today, organic
shareability, and open-source fit.

1. **ParityPrint — 23/25, selected.** Fact: setup discussions repeatedly name
   wrong versions, missing keys, and stale instructions. Hypothesis: a redacted
   `snapshot → check` report makes the invisible difference obvious. Difference:
   it stores states, never values, and does not install or enforce anything.
   Seven-day experiment: ask ten developers to compare local and CI snapshots;
   continue if eight understand the report and no secret value appears.
2. **PortLease — 21/25, rejected.** Fact: local dev servers often collide on
   ports; the current trend includes named-local-URL tooling. Hypothesis: a
   named lease could prevent `EADDRINUSE`. Difference: reservation instead of
   killing a process. Seven-day experiment: observe ten projects starting two
   services. Rejected today because existing portless/port managers reduce
   novelty and the network/process boundary is higher risk.
3. **UnicodeVeil — 20/25, rejected.** Fact: copied text can contain invisible
   or confusable characters. Hypothesis: a reviewable scan/clean report would
   prevent confusing failures. Difference: show exact code points before any
   rewrite. Seven-day experiment: collect ten real paste failures. Rejected
   today because it overlaps LinePatch and existing Unicode security tooling.
4. **DeskDrift — 18/25, rejected.** Fact: users report accumulating random files
   and messy folders. Hypothesis: a before/after folder growth report could
   reduce cleanup anxiety. Difference: explain change without deleting anything.
   Seven-day experiment: compare Downloads snapshots with ten users. Rejected
   today because organize, FileID, and duplicate tools already occupy the
   space.

## Business wedge

- **First user:** solo developer or small team member debugging a local/CI
  mismatch.
- **First ten users:** personal GitHub network, small developer communities,
  and targeted issue discussions; no paid ads or mass messages.
- **Smallest offer:** one command to create a safe contract and one command to
  check it.
- **Retention hypothesis:** teams keep a snapshot check in CI because drift is
  cheaper to catch before a handoff or bug report.
- **Revenue hypothesis:** MIT core remains free; future signed binaries,
  team policy packs, or support may be paid. No revenue is proven.
- **Cost target:** 0 USD for first 30 days; standard library runtime and GitHub
  Actions only.

## Risks and decision

The product can create false confidence if users mistake `set` for “correct.”
README and SECURITY explicitly state this limit. Package versions, services,
and secrets remain out of scope. Build the small experiment before adding any
enforcement or integrations.
