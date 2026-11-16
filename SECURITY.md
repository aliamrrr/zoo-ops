# Security

Zoo Ops is a local learning game: it binds to `127.0.0.1` by default and stores nothing
outside its own folder. The Docker image runs as a non-root user.

If you find a vulnerability (for example a way for the page or a manifest to run code outside
the learner's own files), please report it privately through
[GitHub's private vulnerability reporting](https://github.com/aliamrrr/zoo-ops/security/advisories/new)
rather than in a public issue. You will get an answer within a week.

The Blueprint answers in `hard/architecture/` and `hardpp/architecture/` are spoilers, not
secrets: reading them is not a vulnerability.
