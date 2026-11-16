# 2. Acceptance tests run in a subprocess, cached by fingerprint

Date: 2026-11-16. Status: accepted.

## Context

In the hard modes the learner edits a whole project. The game must know which tickets pass,
without importing stale modules, without freezing when a test hangs, and without rerunning
two minutes of tests on every page refresh.

## Decision

`zoo/checks.py` runs one `pytest` subprocess for all tickets of a mode, with a small plugin
(`zoo/pytest_report.py`) that writes each outcome to JSON. Results are cached in
`.zoo/status-<mode>.json` under a fingerprint of the project's source files (path, size,
mtime). The `StatusBoard` answers at once with the last results and refreshes in the
background when the fingerprint changes. `--continue-on-collection-errors` keeps one broken
ticket from hiding the others.

## Consequences

- The learner's code is always imported fresh, and a hang is cut at 300 s.
- The game shows "checking" for a few seconds after each save in a hard mode.
