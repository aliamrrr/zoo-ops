# ZOO-109 A raccoon read our data

**Reporter:** Security, high priority
**Pattern:** Auth + security

> The Lyon shelter runs on the same platform as Paris. A Lyon volunteer (the "raccoon")
> listed every Paris animal and their meal history. The pen test also found that we accept
> tokens nobody signed. The feeder bots still share one password in a config file.

## Acceptance criteria

**Tokens**
- Bearer tokens are JWTs signed with HS256 using `Settings.jwt_secret`. Refuse with `401`: unsigned tokens, tokens signed with any other key or algorithm, expired tokens, and tokens without `exp`, `sub` or `tenant`.

**Bots**
- Bots send `X-Api-Key: zk_<key_id>_<secret>` (the secret may contain underscores). The `api_keys` table stores the SHA-256 hex digest of the **whole** key, never the key. Its `scopes` column is space separated.
- An unknown or wrong key answers `401`. Comparing digests must not leak timing information.

**Tenants and scopes**
- A caller only ever sees and changes data of their own tenant. Anything belonging to another tenant answers `404`, as if it did not exist.
- Placing meal orders needs the `kitchen:write` scope, otherwise `403`.

## Done when

`python -m zoo test --mode hard 9` is green and the unit tests still pass.

## Read before you start

- [JSON Web Token Best Current Practices, RFC 8725](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authorization cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
