# 09 Auth + security: The Kennel

**In the game.** Rex the guard dog checks badges for two shelters, Paris and Lyon. A raccoon who is admin in Lyon tries to read the Paris animals, forges an unsigned token, replays an expired one and guesses an API key.

## The pattern

- **JWT verification**: check the signature with an algorithm list pinned by the server, never the one in the token header (the `alg: none` attack). Require `exp`, reject expired tokens.
- **API keys**: high entropy, shown once, stored as a hash. A short public `key_id` makes the lookup fast, a constant-time compare avoids timing leaks.
- **Tenant isolation**: every resource belongs to a tenant, and every access checks it first. Admin of tenant A is nobody in tenant B.
- **Scopes**: least privilege, a token only carries the permissions it needs.
- **Secrets**: never in code or git, read from the environment or a mounted file (Docker and Kubernetes secrets, Vault), no default value, masked in logs.

## What you write

In [auth.py](auth.py): `verify_token`, `ApiKeyStore.authenticate`, `authorize`. Token issuing, key creation, `Secret` and `load_secret` are provided.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| No tenant check | The raccoon's Lyon token opens the Paris registry |
| Algorithm read from the token | An unsigned `alg: none` token is accepted |
| No `exp` requirement | A token stolen yesterday still works |
| `==` on raw keys | Works, but leaks timing and stores usable keys |

## Learn it

- [JSON Web Token Best Current Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [PyJWT usage](https://pyjwt.readthedocs.io/en/stable/usage.html)
- [OWASP Authorization cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)

## Hints

- `jwt.decode(token, secret, algorithms=[...], options={"require": [...]})`, and catch `jwt.PyJWTError`.
- `presented.split("_", 2)` keeps underscores inside the secret part.
- Check the tenant before the scopes.

```
python -m zoo test 9
python -m zoo scene 9
```
