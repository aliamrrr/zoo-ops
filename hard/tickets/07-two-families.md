# ZOO-107 Two families, one kitten

**Reporter:** Adoption office
**Pattern:** Data integrity

> Two families were told they adopted Pixel. Same afternoon, the north pantry showed 12 kg
> more food than was ever delivered, and a transfer to a mistyped pantry made 10 kg vanish.
> Separately, the website team needs a URL slug for every kitten, and there are a lot of
> kittens in production.

## Acceptance criteria

**Adoptions**
- `GET /v1/kittens/{id}` returns an `ETag` header that changes whenever the kitten changes. The adoption response returns the new one.
- `POST /v1/kittens/{id}/adoption` requires `If-Match`: missing answers `428`, stale answers `412`.
- When several families adopt at the same moment with the same `ETag`, exactly one succeeds and every other one gets `412`.

**Food transfers**
- A transfer is all or nothing. An unknown pantry answers `404` and changes nothing. Not enough food answers `409` and changes nothing.
- Concurrent transfers never create or lose food and never leave a pantry negative.

**Kitten slugs**
- Every kitten has a `slug`: its name lowercased with runs of spaces turned into single dashes (`"Tofu The Brave"` becomes `tofu-the-brave`). It is returned by the API.
- The migration must not lock the table on a big production database: existing rows are backfilled in batches of **at most 500 rows per statement**.

## Done when

`python -m zoo test --mode hard 7` is green and the unit tests still pass.

## Read before you start

- [HTTP conditional requests, MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Conditional_requests)
- [SQLite transactions, BEGIN IMMEDIATE](https://www.sqlite.org/lang_transaction.html)
- [ParallelChange (expand and contract), Martin Fowler](https://martinfowler.com/bliki/ParallelChange.html)
