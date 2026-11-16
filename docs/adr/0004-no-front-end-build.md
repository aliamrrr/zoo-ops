# 4. No front-end build step

Date: 2026-11-16. Status: accepted.

## Context

The page is a canvas game of about 4,000 lines. Learners read it, and contributors tweak it.

## Decision

The front end is plain ES modules and CSS files served as they are. No bundler, no
framework, no `node_modules` to play. Files are split by responsibility (`world/`, `game/`,
`css/`) and kept under 600 lines. The server sends `Cache-Control: no-cache` with ETags, so a
saved file is picked up without cache-busting query strings. CI parses every module.

## Consequences

- "View source" shows exactly what runs, and the game starts with Python alone.
- No type checking of the JavaScript beyond syntax; the API contract test pins what the page
  reads from the server.
