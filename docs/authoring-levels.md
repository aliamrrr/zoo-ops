# Writing a level or a ticket

Every mode is a folder with a `zoo-mode.json` manifest. The game reads everything it shows
from there, so adding or changing an exercise rarely touches `zoo/`.

## A Classic level

A level is a folder in `levels/` with four files:

| File | Role |
| --- | --- |
| `README.md` | The pattern in a few lines, the bugs it prevents, their symptoms, hints. Shown in the game's station drawer. |
| `<name>.py` | The file the learner edits. Each function to write has a docstring that is its spec and a body that is exactly `raise NotImplementedError("<Name>")`. |
| `test_<name>.py` | The contract. Tests call the learner's functions directly, never mocks of them. |
| `scene.py` | `play(scene: zoo.kit.Scene)`: a short story that runs the learner's code and reports with `scene.info`, `scene.good`, `scene.bad`, `scene.check` and `scene.metric`. Any `bad` line marks the station as broken. |

Then add the level to `levels/zoo-mode.json`:

```json
{"id": "11", "label": "Search", "pattern": "Full-text search", "title": "The Library",
 "test": "l11_search",
 "without": "What the zoo suffers while the pattern is missing.",
 "with": "What the keeper does once the pattern is built.",
 "exercise": {"file": "search.py", "todos": ["build_index", "query"]}}
```

- `todos` lists every name raised by a `NotImplementedError` in the file, in order.
- A TODO that already works the slow way in the starter (an N+1 query) is listed in `naive`
  too: the starter guard then expects it not to raise.
- The keeper of each pattern number is in `zoo/cast.py`; the world draws it from
  `zoo/static/js/world/motion.js`.

If the level should change the live game (like 01, 03, 04 and 08 do), hook it in
`zoo/game.py`: every hook must fall back to the naive behavior when the learner's function
raises `NotImplementedError`, and turn any other exception into a game note, never a crash.

## A Hard or Hard++ ticket

1. Write the ticket in `tickets/NN-name.md`: who reports it, what users see, acceptance
   criteria, and what is out of scope. It describes a symptom, never the solution or the file
   to change.
2. Write its acceptance tests in `tests/acceptance/test_*_NN_*.py`. They go through the public
   API of the project (HTTP routes, service entry points), so any reasonable design passes.
3. Add its block to `architecture/blueprint.json`: a `blocks` entry (label and blurb shown to
   the learner) and an `answers` entry (accepted `slots`, the component `links`, and a `hint`
   that points at the right area without naming it).
4. Add the level to the mode's `zoo-mode.json` with its `ticket` and `test` paths.

## Before you open the pull request

```bash
pip install -e ".[dev]"
pytest tests                    # the game shell, the API contract, the starter guards
pytest tests/starter -m slow    # no hard ticket passes on main
ruff check . && ruff format --check . && mypy
```

- Solve your new exercise on a branch to prove it can be solved, but **commit only the
  starter** to `main`. The starter guards fail otherwise.
- Play it: `zoo play`, then check the station, the callouts and the journal.
