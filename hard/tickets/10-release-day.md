# ZOO-110 Release day

**Reporter:** Platform team
**Pattern:** Deployment + scaling

> Every deploy drops a few visitor questions, because Kubernetes kills the pod while it is
> still serving them. Last month a new model version (`owl-large-v2`) went to everybody at
> once and answered nonsense for an hour.

## Acceptance criteria

**Graceful shutdown**
- `POST /internal/lifecycle/drain` (sent by the pod's preStop hook) answers `202`. From then on `GET /readyz` answers `503` while `GET /healthz` stays `200`.
- While draining, new `/v1/*` requests answer `503` with a `Retry-After` header. Requests already in flight finish normally.
- `GET /internal/lifecycle` returns `{"draining": bool, "in_flight": int}`, where `in_flight` counts `/v1/*` requests being served.

**Canary release**
- Owl answers carry an `X-Release: stable | canary` header. The canary serves `Settings.canary_owl_model`, the stable release serves `Settings.owl_model`.
- A caller is on the canary when `int(sha256(sub).hexdigest()[:16], 16) % 100 < Settings.canary_percent`. That keeps every caller on the same side, across replicas and restarts.
- `POST /internal/releases/evaluate` returns `{"verdict": "wait" | "rollback" | "promote"}`:
  - `wait` while the canary has served fewer than 25 Owl questions;
  - `rollback` when the canary's error rate (5xx) is more than 1 point above the stable one. After a rollback everybody is served by the stable release;
  - `promote` otherwise.

## Done when

`python -m zoo test --mode hard 10` is green and the unit tests still pass.

## Read before you start

- [Liveness, readiness and startup probes, Kubernetes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [CanaryRelease, Martin Fowler](https://martinfowler.com/bliki/CanaryRelease.html)
