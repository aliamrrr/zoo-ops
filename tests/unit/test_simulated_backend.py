"""The live hooks of the hard modes play what the shipped tickets do."""

from __future__ import annotations

from zoo.game import MEAL_GRAMS, SimulatedBackend


def test_the_simulated_kiosk_follows_the_shipped_tickets() -> None:
    backend = SimulatedBackend()
    question = "Why do otters hold hands?"
    assert backend.ask(question, storm=False).provider == "owl"
    assert backend.ask(question, storm=False).provider == "owl"
    assert backend.ask(question, storm=True).failed

    backend.online = frozenset({"01", "03"})
    backend.reset()
    backend.ask(question, storm=False)
    assert backend.ask(question, storm=False).cache_hit
    assert backend.ask("How strong is an ant?", storm=True).provider == "parrot"


def test_simulated_meals_are_served_once_with_idempotency() -> None:
    backend = SimulatedBackend()
    backend.online = frozenset({"04"})
    for _ in range(20):
        assert backend.feed("lion").delivered_grams == MEAL_GRAMS
    backend.online = frozenset()
    meals = {backend.feed("lion").delivered_grams for _ in range(40)}
    assert max(meals) > MEAL_GRAMS
