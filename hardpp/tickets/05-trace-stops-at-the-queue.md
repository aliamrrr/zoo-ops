# PLANET-205 The trace that stops at the queue

**Area:** `zoo_planet.tracing`
**Pattern:** Distributed tracing: W3C context propagation and tail-based sampling
**Asked at:** Google (Dapper), Uber (Jaeger), Datadog

> A feeding took 40 seconds. The trace shows the API call and then nothing: the worker
> starts a brand-new trace. We also keep a random 10% of traces decided at the start, so the
> slow and failing ones we need are usually gone, while we pay to store boring ones.

## Requirements

1. **Propagation.** An incoming `traceparent` header (W3C format `00-<32 hex trace id>-<16 hex span id>-<flags>`) is continued by the API. The context travels with the job through the queue, so the worker's `feed` span is a child of the `queue.publish` span, in the same trace.
2. **Tail-based sampling.** Decide per trace once it is complete: **2 seconds** (tracer clock) after its last span ended with no span still open. `Tracer.flush()` makes the decisions that are due.
3. Keep every trace with an error, every trace longer than **0.5 s** (first start to last end), and 5% of the others: those whose `int(trace_id[:8], 16) % 100 < 5`.
4. A trace is exported whole or not at all. Nothing is exported before its decision.

## Done when

`python -m zoo test --mode hardpp 5` is green.

## Read before you start

- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Dapper, a large-scale distributed systems tracing infrastructure](https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/)
- [Tail sampling processor, OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/tailsamplingprocessor/README.md)
