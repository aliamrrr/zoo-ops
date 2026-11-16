# 6. `main` ships the exercises, never the solutions

Date: 2026-11-16. Status: accepted.

## Context

The level and ticket tests are red on purpose, so a green CI cannot tell an untouched
exercise from one whose solution was committed by mistake.

## Decision

`tests/starter` fails when a Classic TODO no longer raises `NotImplementedError` (except the
documented `naive` ones that work slowly on purpose) and, in a slower CI job, when any Hard or
Hard++ ticket passes all its acceptance tests on `main`. The pre-commit hook runs the fast
part whenever a level changes.

## Consequences

- A solution cannot reach `main` unnoticed.
- Solutions live on the learner's own branch.
