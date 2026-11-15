# ZOO-101 The Owl bill exploded

**Reporter:** Finance, via the platform channel
**Pattern:** Cache

> Our model provider invoice tripled this month. The kiosk logs show the same twenty
> questions asked thousands of times a day, and every single one goes to the model.
> Visitors also wait almost a second for answers we already gave five minutes earlier.

## Acceptance criteria

- A deterministic question (`temperature` 0) that was already answered is served without calling the model.
- Wording differences that do not change the meaning are the same question: case and surrounding or repeated whitespace.
- Sampled answers (`temperature` above 0) are never reused.
- All replicas of the service share what they learned. Production runs four of them behind the gateway.
- Nothing is kept longer than 10 minutes, and every key the service writes to Redis expires.
- When a keeper updates a fact (`PUT /v1/owl/facts/{topic}`), visitors get the new fact on their very next question.
- A failed call is never remembered as an answer.

## Out of scope

Embeddings, and caching anything other than Owl answers.

## Done when

`python -m zoo test --mode hard 1` is green and the unit tests still pass.

## Read before you start

- [Caching patterns, AWS whitepaper](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html)
- [Redis `SET` with `EX`](https://redis.io/docs/latest/commands/set/)
