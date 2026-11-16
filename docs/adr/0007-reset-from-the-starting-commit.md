# 7. `zoo reset` restores from the commit the learner started from

Date: 2026-11-16. Status: accepted. Replaces the `starter`, `hard-starter`, `hardpp-starter` tags.

## Context

`zoo reset` restored files from git tags. Two of the three tags were never published, and the
`starter` tag pointed at the first commit, so it would have restored files that no longer fit
the game after any change.

## Decision

`zoo reset` restores from `git merge-base HEAD origin/main` (then `main`, then the old
`starter` tag): the version of `main` the learner's work grew from.

## Consequences

- Nothing to tag or publish at each release; reset is always consistent with the game.
- It needs a git clone. A downloaded ZIP gets a clear message instead.
