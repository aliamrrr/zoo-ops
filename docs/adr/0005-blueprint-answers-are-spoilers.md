# 5. Blueprint answers are spoilers, not secrets

Date: 2026-11-16. Status: accepted.

## Context

The hard modes check a learner's architecture design against an expected answer.

## Decision

Answers live in `architecture/blueprint.json` next to each project, and the server only ever
sends the public part (components, slots, blocks) to the page. A placement is checked on the
server, which answers with a verdict and a hint.

## Consequences

- The browser's network tab never reveals the answer.
- Anyone who opens the JSON file can read it. That is acceptable for a learning game, and the
  documentation says so instead of calling it a secret.
