# PLANET-207 The half-finished adoption

**Area:** `zoo_planet.adoption`
**Pattern:** Saga (orchestration) with compensations and crash recovery
**Asked at:** Uber (Cadence), Amazon (Step Functions), Airbnb

> An international adoption touches three services owned by three teams: the shelter
> reserves the kitten, payments charges the family, transport books the van. When the van
> is refused, the kitten stays reserved and the family stays charged. When the orchestrator
> restarts in the middle, nobody knows where it was.

## Requirements

1. `run(adoption)` returns `"completed"` when every step succeeds.
2. Transient failures (`TransientError`) are retried, up to 3 attempts per step or compensation.
3. When a step fails permanently, already completed steps are compensated in reverse order (`cancel`, `refund`, `release`) and `run` returns `"compensated"`.
4. The workflow state lives in the `SagaStore`, which survives crashes. A new `AdoptionWorkflow` on the same store finishes or compensates every unfinished adoption in `resume()`, which returns `{adoption_id: final_status}`. A step that completed is never run again.
5. Crash points: keep `saga.after_reserve` and `saga.after_charge`, and call `saga.compensating` right before the first compensation.
6. `status(adoption_id)` returns the current status from any process.

## Constraints

- The three services are idempotent per adoption id. Do not change them.

## Done when

`python -m zoo test --mode hardpp 7` is green.

## Read before you start

- [Sagas, Garcia-Molina and Salem](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf)
- [Pattern: Saga, microservices.io](https://microservices.io/patterns/data/saga.html)
