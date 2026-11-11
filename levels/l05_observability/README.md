# 05 Observability: The Lookout

**In the game.** Mika the meerkat watches one hour of zoo traffic. The sloth exhibit is slow, and in the last five minutes the enclosure database starts failing.

## The pattern

- **Structured logs**: one JSON object per line, so a backend (Loki, Datadog, CloudWatch) can filter on any field.
- **Request id**: generated at the edge (or read from `X-Request-ID`), stored in a `ContextVar`, attached to every log line. Filtering on it shows the whole story of one request. Pass it to downstream calls and it becomes a trace id.
- **Tracing**: spans with durations, parent and child ids. OpenTelemetry exports them to Jaeger or Tempo, Langfuse does it for LLM calls (prompts, tokens, cost).
- **Percentiles**: the average hides the slow tail. p95 and p99 show what real users feel.
- **SLO alerts**: alert on how fast the error budget burns, using a long and a short window together. The long one proves it matters, the short one proves it is still happening.

## What you write

In [observability.py](observability.py): `request_context`, `JsonFormatter.format`, `percentile`, `burn_rate`, `should_page`. The `span` helper is provided.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| Request id missing or leaking | Mika cannot rebuild the story of the failing request |
| Wrong percentile | p95 hides the sloth path |
| Single-window alert | A tiny blip pages the keeper at 3 am |
| No burn-rate alert | The database is down and nobody is paged |

## Learn it

- [Alerting on SLOs (Google SRE Workbook)](https://sre.google/workbook/alerting-on-slos/)
- [contextvars (Python docs)](https://docs.python.org/3/library/contextvars.html)
- [Traces (OpenTelemetry)](https://opentelemetry.io/docs/concepts/signals/traces/) and [Langfuse docs](https://langfuse.com/docs)

## Hints

- `token = var.set(value)` then `var.reset(token)` in a `finally`.
- Nearest-rank: sort, then index `ceil(p / 100 * n) - 1`.
- Burn rate 14.4 over one hour spends 2% of a 30 day budget.

```
python -m zoo test 5
python -m zoo scene 5
```
