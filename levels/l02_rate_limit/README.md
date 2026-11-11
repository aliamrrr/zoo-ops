# 02 Rate limiting + API gateway: The Gate

**In the game.** Gus the goose guards the gate in front of the Owl. A pigeon flock sends 50 requests per second, a hedgehog sends one, and a python sends a 50 000 token prompt.

## The pattern

- **Token bucket**: a bucket of `capacity` tokens refilled at a constant rate. Each request pays tokens. It allows short bursts and caps the long-run rate.
- **Per key**: each API key has its own buckets, so one abusive client never starves the others.
- **Requests and tokens**: LLM traffic needs two budgets. 60 requests per minute means nothing if one request carries a book.
- **No partial charge**: check both budgets, then charge both. A refused request costs nothing.
- **Retry-After**: a 429 tells the client exactly when to come back.
- **Gateway**: auth, limits and routing live in front of the services, in Nginx, Kong or a LiteLLM proxy. See [nginx.conf](nginx.conf) and [litellm_config.yaml](litellm_config.yaml).

## What you write

In [rate_limit.py](rate_limit.py): `TokenBucket._refill`, `TokenBucket.try_consume`, `TokenBucket.retry_after`, `RateLimiter.check`. The `Gateway` around them is provided.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| No refill cap | The flock saves up tokens and floods the Owl |
| Shared budget | The hedgehog gets 429s because of the pigeons |
| No token budget | The python's giant prompt reaches the Owl |
| Partial charge | The refused giant prompt still burns the python's request budget |

## Learn it

- [Scaling your API with rate limiters (Stripe)](https://stripe.com/blog/rate-limiters)
- [Nginx limit_req module](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- [LiteLLM virtual keys, rpm and tpm limits](https://docs.litellm.ai/docs/proxy/virtual_keys)

## Hints

- Refill is `elapsed * rate`, capped with `min(capacity, ...)`. Move `_updated_at` every time.
- `retry_after(n)` is `(n - tokens) / rate` when tokens are missing.
- In production the bucket lives in Redis and is updated by a Lua script, so all gateway replicas share it atomically.

```
python -m zoo test 2
python -m zoo scene 2
```
