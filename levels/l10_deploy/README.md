# 10 Deployment + scaling: The Nest

**In the game.** Pip the canary sings every new release first. Song v2 is broken and must roll back, song v3 is fine and must ship, and when the pod gets SIGTERM five visitors are mid-song.

## The pattern

- **Stateless apps**: no session or cache in process memory, everything in Redis or the database. Any instance can die, be cloned or be moved, which is what autoscaling needs.
- **Docker and CI/CD**: one immutable image per commit, built and tested in CI, promoted through environments. See the root [Dockerfile](../../Dockerfile) and [ci.yml](../../.github/workflows/ci.yml).
- **Canary releases**: send a small, sticky share of users to the new version, compare its error rate and latency with the baseline, then promote or roll back automatically.
- **Health checks**: liveness ("restart me if I am stuck") is not readiness ("send me traffic"). A draining pod is alive but not ready.
- **Graceful shutdown**: on SIGTERM, fail readiness, refuse new requests, finish in-flight ones, then exit before the grace period ends.
- **Autoscaling**: an HPA adds pods on CPU or queue depth. See [k8s.yaml](k8s.yaml).

## What you write

In [deploy.py](deploy.py): `in_canary`, `judge_canary`, `Lifecycle.ready`, `Lifecycle.track_request`, `Lifecycle.begin_shutdown`, `Lifecycle.wait_until_drained`.

## How it breaks in the game

| Bug | What you see |
| --- | --- |
| `hash()` instead of sha256 | Users flip between versions on every restart |
| No error comparison | The broken song v2 reaches the whole flock |
| Ready during shutdown | New traffic keeps arriving at a dying pod |
| No drain | Songs are cut in the middle |

## Learn it

- [CanaryRelease (Martin Fowler)](https://martinfowler.com/bliki/CanaryRelease.html)
- [Liveness, readiness and startup probes (Kubernetes)](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [The Twelve-Factor App: processes and disposability](https://12factor.net/disposability)

## Hints

- `int.from_bytes(digest[:8], "big") % 100`.
- `threading.Condition` is a lock plus `wait_for(predicate, timeout)` and `notify_all()`.
- Raise `ShuttingDown` before incrementing the counter.

```
python -m zoo test 10
python -m zoo scene 10
```
