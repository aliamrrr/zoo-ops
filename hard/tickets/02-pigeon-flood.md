# ZOO-102 A pigeon flood took the kiosk down

**Reporter:** On-call keeper, after the Saturday incident
**Pattern:** Rate limiting + API gateway

> A misconfigured bot (the "pigeons") sent 500 questions in ten seconds with one token.
> The model provider throttled our whole account, so every visitor got errors for twenty
> minutes. Someone also pasted an entire book into the question box.

## Acceptance criteria

- Each caller (the `sub` of their credentials) gets at most **60 questions per minute** on the Owl, with bursts allowed up to that number and a steady refill of one per second.
- Each caller also gets at most **6,000 model tokens per minute**. Count a question as `ceil(len(question) / 4)` tokens.
- A refused request answers `429` with a JSON body `{"error": "rate_limited", "limit": "requests" | "tokens", ...}` and a `Retry-After` header in whole seconds, rounded up.
- A refused request consumes nothing from either budget.
- One caller's budget never affects another caller.
- The budget is shared by every replica: 30 questions on one replica and 30 on another use the same 60.
- Every key the service writes to Redis expires.

## Notes

The edge proxy will get its own limit later (see `levels/l02_rate_limit/nginx.conf` in the Classic mode for the idea). This ticket is about the service itself.

## Done when

`python -m zoo test --mode hard 2` is green and the unit tests still pass.

## Read before you start

- [Scaling your API with rate limiters, Stripe](https://stripe.com/blog/rate-limiters)
- [Redis transactions: WATCH, MULTI, EXEC](https://redis.io/docs/latest/develop/interact/transactions/)
