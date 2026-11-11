# 08 Async processing: The Anthill

**In the game.** The ant colony carries 30 seeds (background jobs). Two rotten leaves are poison jobs that always fail, and one clumsy ant drops seed-7 twice. The Owl desk on the game page streams its answers live through your `sse_event()`.

## The pattern

- **Queue and workers**: slow work leaves the request path. The API enqueues a job and answers right away, workers process it later. Celery with Redis or RabbitMQ, SQS, or Kafka consumers.
- **Ack after success**: a job is removed only once it is done. A crash means it comes back.
- **Retries with backoff**: failed jobs return to the queue after a growing delay (SQS visibility timeout, Celery `retry(countdown=...)`).
- **Dead-letter queue**: after N attempts a job moves to a DLQ with its last error, so one poison message never blocks the queue or loops forever. Someone inspects and redrives it.
- **Streaming with SSE**: an LLM answer takes seconds. Server-Sent Events stream tokens over a plain HTTP response (`text/event-stream`), with automatic reconnection in the browser.

## What you write

In [async_jobs.py](async_jobs.py): `Worker.run_once`, `sse_event`. The queue and the browser-side `parse_sse` are provided.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| Poison job retried forever | The colony is stuck, the queue never drains |
| No retry | seed-7 is lost after its first drop |
| No DLQ | Rotten leaves vanish without a trace |
| Wrong SSE framing | The Owl's bubble stays empty or garbled on the game page |

## Learn it

- [Server-sent events (WHATWG HTML spec)](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Amazon SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
- [Celery tasks: retries, acks_late](https://docs.celeryq.dev/en/stable/userguide/tasks.html)

## Hints

- Catch `Exception` around the handler, record `f"{type(exc).__name__}: {exc}"`.
- Delay of attempt n: `retry_delay * 2 ** (attempts - 1)`.
- SSE: `data.split("\n")`, one `data: ` line each, and end with an empty line.

```
python -m zoo test 8
python -m zoo scene 8
```
