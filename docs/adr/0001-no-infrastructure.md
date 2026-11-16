# 1. No infrastructure to install

Date: 2026-11-16. Status: accepted.

## Context

The audience is learners on their own laptop, on Windows, macOS or Linux. Asking them to run
Redis, Postgres and an LLM API key before they can see anything loses most of them.

## Decision

Everything the patterns need is simulated in process: `fakeredis` for Redis, SQLite for the
database, fake LLM providers (the Owl and the Parrot) with realistic latency and failures, and
a controllable clock for incidents. The Hard service is still written against real interfaces
(`redis.Redis`, SQL migrations) so the code transfers to production.

## Consequences

- One command installs and plays. CI needs no services.
- Some production behaviors cannot be shown (real network partitions, real Postgres locking).
  Hard++ covers distributed behaviors with a deterministic simulation instead.
