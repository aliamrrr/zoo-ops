# ZOO-108 The robot crew is stuck, and the Owl goes silent

**Reporter:** Operations, and the kiosk UX team
**Pattern:** Async processing

> When one robot is broken, the cleaning queue retries its job in a tight loop and the
> other pens stay dirty. Nobody knows which jobs gave up. Separately, visitors stare at
> a blank kiosk for two seconds before the whole answer appears at once.

## Acceptance criteria

**Background jobs**
- A failed job is retried later, not immediately: after **1 second**, then **2 seconds** (platform clock).
- A job is attempted at most **3 times**. Then it moves to a dead-letter queue and is never run again.
- `GET /internal/dead-letters` lists them: `[{"id", "kind", "attempts", "last_error"}]`.
- A failing job never blocks the jobs behind it. `POST /internal/worker/drain` only runs jobs that are due now.

**Streaming**
- `GET /v1/owl/stream?question=...` answers `text/event-stream` (Server-Sent Events).
- The answer arrives as several `token` events whose data, concatenated, is exactly the answer, multi-line answers included. The stream ends with a `done` event.

## Done when

`python -m zoo test --mode hard 8` is green and the unit tests still pass.

## Read before you start

- [Server-sent events, WHATWG HTML spec](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Amazon SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
