"""The Owl: a fake LLM with canned answers, streamed token by token."""

from __future__ import annotations

import re

ANSWERS = {
    "otter": "Sea otters hold hands while they sleep.\nThat way they never drift apart.",
    "lion": "Lions sleep up to 20 hours a day.\nHunting is exhausting work.",
    "penguin": "Penguins propose with a pebble.\nThe smoothest pebble wins.",
    "cat": "Cats spend about 70% of their lives asleep.\nMiso is aiming for 90%.",
    "fox": "A fox can hear a watch ticking 40 meters away.\nRusty hears your bugs too.",
    "mole": "A mole can dig 20 meters of tunnel in a single day.\nDigby prefers one index.",
    "ant": "Some ants can carry 50 times their own weight.\nJobs are lighter than seeds.",
    "canary": "Miners carried canaries to detect gas early.\nPip detects bad releases.",
}
FALLBACK = "Hoot. Ask me about otters, lions, penguins, cats, foxes, moles, ants or canaries."

QUESTIONS = {
    "otter": "Why do otters hold hands?",
    "lion": "How long do lions sleep?",
    "penguin": "How do penguins propose?",
    "cat": "Do cats really sleep that much?",
    "fox": "How well can a fox hear?",
    "mole": "How fast can a mole dig?",
    "ant": "How strong is an ant?",
    "canary": "Why did miners carry canaries?",
}


def answer_for(question: str) -> str:
    lowered = question.lower()
    for topic, answer in ANSWERS.items():
        if topic in lowered:
            return answer
    return FALLBACK


def tokens(text: str) -> list[str]:
    """Words with their trailing whitespace, so joining the tokens rebuilds the text."""
    return re.findall(r"\S+\s*", text)
