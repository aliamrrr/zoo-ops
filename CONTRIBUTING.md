# Contributing to Zoo Ops

Thanks for helping. New incidents, animals, clearer hints, translations, bug fixes and new
exercises are all welcome.

## Set up

```bash
git clone https://github.com/aliamrrr/zoo-ops.git
cd zoo-ops
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Check your change

```bash
ruff check . && ruff format --check .
mypy
pytest tests                       # about 40 s
pytest tests/starter -m slow       # the hard modes' suites, about 2 min
zoo play                           # and look at it
```

CI runs the same checks on Python 3.11 to 3.13, on Linux, macOS and Windows, and also starts
the game from the launchers and from the Docker image.

## Ground rules

- **Never commit a solution to `main`.** Level files keep their `NotImplementedError` TODOs and
  hard tickets stay red. `tests/starter` enforces it.
- **The JSON the page reads is a contract.** If you change a response on purpose, regenerate
  `tests/api/contract.json` with `ZOO_UPDATE_CONTRACT=1 pytest tests/api/test_contract.py`
  and explain why in the pull request.
- **Keep the game playable without infrastructure**: no new service the learner must run.
- Keep files focused and under about 600 lines; see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  for where things go, and [docs/authoring-levels.md](docs/authoring-levels.md) to add an
  exercise.

## Pull requests

One topic per pull request, a title that says what it changes for the player or the
contributor, and screenshots when the game looks different.
