# ZOO-105 We are flying blind

**Reporter:** Site reliability, after a post-mortem
**Pattern:** Observability

> During the last incident nobody could tell which log lines belonged to which visitor,
> the dashboards only showed averages, and the pager rang 40 times for a 2 minute blip
> while the real outage the next morning paged nobody.

## Acceptance criteria

**Logs**
- Every line the service writes is one JSON object with at least `ts`, `level`, `logger`, `message` and `request_id`.
- A request keeps the `X-Request-ID` it came with, or gets a new unique one. The id is echoed in the response header `X-Request-ID` and carried by **every** log line written while serving that request, including the services' own lines.

**Metrics**
- `GET /internal/metrics` returns `{"routes": {"<METHOD> <route template>": {"count": int, "errors": int, "p95_ms": float}}}`. For example the key `POST /v1/owl/answers`.
- `p95_ms` is the nearest-rank 95th percentile of the request durations measured with the platform clock. `errors` counts 5xx responses.

**Alerting**
- Our SLO: 99.9% of `/v1/*` requests do not end in a 5xx.
- `GET /internal/alerts` returns `{"page": bool, "burn_rate_short": float, "burn_rate_long": float}` with burn rates over the last 5 minutes and the last hour.
- Page only when **both** burn rates exceed 14.4.

## Done when

`python -m zoo test --mode hard 5` is green and the unit tests still pass.

## Read before you start

- [Alerting on SLOs, Google SRE Workbook](https://sre.google/workbook/alerting-on-slos/)
- [contextvars](https://docs.python.org/3/library/contextvars.html)
