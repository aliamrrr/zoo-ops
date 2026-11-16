# 3. One manifest and one runtime interface for every mode

Date: 2026-11-16. Status: accepted. Supersedes the special-cased Classic mode.

## Context

Hard and Hard++ were described by a `zoo-mode.json` manifest, but Classic was hard-coded in
Python, and 17 `is_classic` checks spread over the server, the CLI and the modes.

## Decision

Every mode, Classic included, is a folder with a `zoo-mode.json` validated by pydantic at
load. The manifest's `runtime` picks a `ModeRuntime` implementation (`ClassicRuntime` or
`AcceptanceRuntime`); the server and the CLI only call that interface.

## Consequences

- No caller asks which mode it is in. A new mode is a new folder.
- A malformed manifest fails at start-up with a precise message, never mid-shift.
- The cast of keepers (`zoo/cast.py`) is shared by all modes: pattern 04 is always Miso.
